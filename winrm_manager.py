# winrm_manager.py
"""
Remote command execution manager for HelpIT application.

This module uses WinRM (Windows Remote Management) via the pywinrm library
to execute commands on remote Windows machines and capture their output.

WinRM is a native Microsoft protocol (WS-Management / SOAP over HTTP),
built into every Windows machine since Vista. It does not rely on SMB,
impacket, or any third-party binary, which makes it fully compatible
with antivirus software.

Prerequisites on the REMOTE machine (run once as admin):
    winrm quickconfig -quiet

On a domain-joined machine, WinRM is usually already enabled via GPO.

Dependencies:
    pip install pywinrm requests-ntlm
"""

import re
import csv
import sys
import logging
import shutil
import subprocess
from pathlib import Path

import winrm

from utils import debug_print
from constants import DEFAULT_PSEXEC_TIMEOUT, DEFAULT_SCRIPT_TIMEOUT


class WinRM:
    """
    Manages remote command execution on Windows machines using WinRM.

    WinRM (Windows Remote Management) is a Microsoft-native protocol that
    runs commands remotely over HTTP and captures their output reliably.
    It replaces pypsexec/impacket which triggered antivirus false positives.

    The WinRM session is created lazily on each _run() call so the
    __init__ never blocks the Tkinter main thread.

    Attributes:
        ip_address (str): IP address of the remote machine.
        netbios (str): NetBIOS/hostname of the remote machine.
        tmp_dir (str): Local temporary directory for CSV files.
        psexec_path (str): Path to the bin folder (kept for open_terminal).
        psexec_bin (str): Full path to PsExec64.exe for interactive sessions.
    """

    def __init__(self, ip_address: str, netbios: str, psexec_path: str, tmp_dir: str,
             username: str = "", password: str = "") -> None:
        """
        Initializes the PsExecManager.

        No network connection is made here - the WinRM session is created
        lazily on the first command call, so this constructor never blocks.

        Args:
            ip_address (str): IP address of the remote machine.
            netbios (str): NetBIOS name of the remote machine.
            psexec_path (str): Path to the bin folder (used for open_terminal only).
            tmp_dir (str): Local temporary directory path for CSV output files.
        """
        self.ip_address = ip_address
        self.netbios = netbios
        self.psexec_path = psexec_path
        self.tmp_dir = tmp_dir
        self.username = username
        self.password = password

        # Path to PsExec64.exe - kept only for open_terminal (interactive session)
        self.psexec_bin = str(Path(psexec_path) / "PsExec64.exe")

        # Create the local tmp directory if it does not exist
        Path(self.tmp_dir).mkdir(parents=True, exist_ok=True)

        # No WinRM session created here - done lazily in _get_session()
        # This prevents blocking the Tkinter main thread during __init__
        logging.debug(f"[WINRM] PsExecManager initialized for {ip_address} ({netbios})")

    def _get_session(self, timeout: int = DEFAULT_PSEXEC_TIMEOUT) -> winrm.Session:
        """
        Creates and returns a fresh WinRM session for the target machine.

        A new session is created on every call to avoid stale connection state
        between successive commands. NTLM transport uses the current Windows
        user credentials automatically - no username/password needed in code.

        Args:
            timeout (int): Timeout in seconds for this session.

        Returns:
            winrm.Session: A configured WinRM session ready to run commands.
        """
        return winrm.Session(
            target=self.ip_address,
            auth=(self.username, self.password),  # NTLM credentials (domain\user + password)
            transport="ntlm",                # NTLM = Windows integrated auth, no plaintext pwd
            server_cert_validation="ignore", # Ignore self-signed cert warnings on HTTP
            read_timeout_sec=timeout + 5,
            operation_timeout_sec=timeout,
        )

    def _run(self, executable: str, arguments: str = "",
             use_system: bool = True,
             timeout: int = DEFAULT_PSEXEC_TIMEOUT) -> tuple:
        """
        Executes a command on the remote machine via WinRM.

        Sends a cmd-style command over WinRM and returns stdout, stderr and
        the return code with the same signature as the old pypsexec version.

        The 'use_system' parameter is kept for API compatibility but has no
        effect under WinRM - commands always run as the authenticated user
        (which must be a local admin on the remote machine).

        Args:
            executable (str): Remote executable (e.g. "cmd.exe", "sc", "taskkill").
            arguments (str): Command-line arguments string.
            use_system (bool): Ignored - kept for API compatibility only.
            timeout (int): Timeout in seconds.

        Returns:
            tuple[str, str, int]: (stdout, stderr, return_code).
            tuple[None, None, None]: If the connection or execution failed.
        """
        logging.debug(f"[WINRM] Run: {executable} {arguments} on {self.ip_address}")

        try:
            session = self._get_session(timeout)

            # run_cmd sends the command exactly like typing in a CMD window.
            # arguments is passed as a single-element list so WinRM forwards
            # it verbatim to the remote shell without re-parsing.
            if arguments:
                response = session.run_cmd(executable, [arguments])
            else:
                response = session.run_cmd(executable)

            stdout = self._decode(response.std_out)
            stderr = self._decode(response.std_err)
            rc = response.status_code

            logging.debug(
                f"[WINRM] RC={rc} | "
                f"stdout={stdout.strip()[:200]} | "
                f"stderr={stderr.strip()[:200]}"
            )

            return stdout, stderr, rc

        except Exception as e:
            logging.error(f"[WINRM] Connection/execution error on {self.ip_address}: {e}")
            return None, None, None

    def _run_ps(self, ps_script: str, timeout: int = DEFAULT_PSEXEC_TIMEOUT) -> tuple:
        """
        Executes a PowerShell script block on the remote machine via WinRM.

        Uses run_ps() which Base64-encodes the script before sending,
        avoiding all quoting issues with complex PowerShell commands.

        Args:
            ps_script (str): PowerShell script content to execute remotely.
            timeout (int): Timeout in seconds.

        Returns:
            tuple[str, str, int]: (stdout, stderr, return_code).
            tuple[None, None, None]: If the connection or execution failed.
        """
        logging.debug(f"[WINRM] RunPS on {self.ip_address}: {ps_script[:100]}")

        try:
            session = self._get_session(timeout)

            # run_ps() Base64-encodes the script to avoid quoting/escaping issues
            response = session.run_ps(ps_script)

            stdout = self._decode(response.std_out)
            stderr = self._decode(response.std_err)
            rc = response.status_code

            logging.debug(
                f"[WINRM] RC={rc} | "
                f"stdout={stdout.strip()[:200]} | "
                f"stderr={stderr.strip()[:200]}"
            )

            return stdout, stderr, rc

        except Exception as e:
            logging.error(f"[WINRM] PowerShell execution error on {self.ip_address}: {e}")
            return None, None, None

    @staticmethod
    def _decode(raw: bytes) -> str:
        """
        Decodes bytes output from WinRM into a string.

        Tries UTF-8 first (modern Windows), then falls back to cp850
        which is the default code page for Windows CMD consoles.

        Args:
            raw (bytes): Raw bytes from WinRM stdout or stderr.

        Returns:
            str: Decoded string, empty string if raw is None or empty.
        """
        if not raw:
            return ""
        try:
            return raw.decode("utf-8", errors="replace")
        except Exception:
            return raw.decode("cp850", errors="replace")

    # ------------------------------------------------------------------
    # Public interface - identical signatures to the old pypsexec version
    # ------------------------------------------------------------------

    def open_terminal(self) -> None:
        """
        Opens an interactive CMD prompt on the remote machine.

        Uses PsExec64.exe directly because WinRM does not support
        interactive sessions. The console window is shown so the
        user can type commands.
        """
        if not Path(self.psexec_bin).exists():
            logging.error(f"[WINRM] PsExec64.exe not found at {self.psexec_bin}")
            return

        command = [
            self.psexec_bin, "-accepteula",
            f"\\\\{self.ip_address}",
            "cmd.exe"
        ]

        # CREATE_NEW_CONSOLE makes the window visible and interactive
        creationflags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0

        subprocess.Popen(
            ["start", "cmd", "/k"] + command,
            shell=True,
            creationflags=creationflags
        )

        logging.info(f"[WINRM] Interactive terminal opened for {self.ip_address}")

    def get_product_name(self) -> str | None:
        """
        Retrieves the Windows product name from the remote registry.

        Queries HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion /v CurrentBuild
        and maps the build number to a Windows version string.

        Returns:
            str: Windows version string (e.g. "Windows 10") or None if not found.
        """
        os_base = "Windows ancien"

        stdout, stderr, rc = self._run(
            "cmd.exe",
            arguments=(
                r'/c reg query '
                r'"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" '
                r'/v CurrentBuild'
            )
        )

        if stdout:
            match = re.search(r'CurrentBuild\s+REG_SZ\s+(.+)', stdout)
            if match:
                pn = match.group(1).strip()
                if pn:
                    # Map build number to Windows version name
                    build = int(pn)
                    if build >= 22000:
                        os_base = "Windows 11"
                    elif build >= 10000:
                        os_base = "Windows 10"
                    elif build >= 9600:
                        os_base = "Windows 8.1"
                    elif build >= 9200:
                        os_base = "Windows 8"
                    elif build >= 7600:
                        os_base = "Windows 7"
                    else:
                        os_base = "Windows"

                    debug_print(f"Product Name retrieved: {os_base}")
                    logging.info(f"[WINRM] ProductName={os_base}")
                    return os_base

        logging.warning(f"[WINRM] Could not retrieve ProductName (rc={rc})")
        return None


    def get_pc_infos(self) -> str | None:
        """
        Retrieves BIOS information from the remote machine via WinRM.

        Runs Get-CimInstance Win32_BIOS remotely to collect manufacturer,
        BIOS name, SMBIOS version, version string, and serial number.

        Returns:
            str: Formatted multi-line string with each BIOS field on its own
                 line, or None if the command failed or returned no output.
        """
        ps_script = (
            "Get-CimInstance -ClassName Win32_BIOS | "
            "Select-Object Manufacturer, Name, SMBIOSBIOSVersion, Version, SerialNumber | "
            "Format-List"
        )

        stdout, stderr, rc = self._run_ps(ps_script)

        output = (stdout or "").strip() or (stderr or "").strip()

        if not output:
            logging.warning("[WINRM] get_pc_infos: empty output")
            return None

        fields = ["Manufacturer", "Name", "SMBIOSBIOSVersion", "Version", "SerialNumber"]

        # Parse "Key : Value" lines from PowerShell Format-List output
        parsed: dict = {}
        for line in output.splitlines():
            line = line.strip()
            if " : " in line:
                key, _, value = line.partition(" : ")
                key = key.strip()
                if key in fields:
                    parsed[key] = value.strip()

        if not parsed:
            logging.warning("[WINRM] get_pc_infos: no fields parsed from output")
            return None

        # Build formatted result - align values by padding keys
        max_key_len = max(len(k) for k in fields)
        lines = [f"{field:<{max_key_len}} : {parsed.get(field, 'N/A')}" for field in fields]
        result = "\n".join(lines)

        debug_print(f"PC infos retrieved:\n{result}")
        logging.info(f"[WINRM] get_pc_infos OK for {self.ip_address}")
        return result


    def get_display_version(self) -> str | None:
        """
        Retrieves the Windows display version from the remote registry.

        Queries HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion /v DisplayVersion.

        Returns:
            str: Display version string (e.g. "23H2") or None if not found.
        """
        stdout, stderr, rc = self._run(
            "cmd.exe",
            arguments=(
                r'/c reg query '
                r'"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" '
                r'/v DisplayVersion'
            )
        )

        if stdout:
            match = re.search(r'DisplayVersion\s+REG_SZ\s+(.+)', stdout, re.IGNORECASE)
            if match:
                dv = match.group(1).strip()
                if dv:
                    debug_print(f"Display Version retrieved: {dv}")
                    logging.info(f"[WINRM] DisplayVersion={dv}")
                    return dv

        logging.warning(f"[WINRM] Could not retrieve DisplayVersion (rc={rc})")
        return None

    def get_distinguished_name(self) -> str | None:
        """
        Retrieves the Active Directory Distinguished Name of the remote machine.

        Queries the Group Policy state registry key which is populated after
        the machine has received GPOs from the domain controller.

        Returns:
            str: Distinguished Name (e.g. "CN=PC2,OU=Workstations,DC=...") or None.
        """
        stdout, stderr, rc = self._run(
            "cmd.exe",
            arguments=(
                r'/c reg query '
                r'"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Group Policy\State\Machine" '
                r'/v Distinguished-Name'
            )
        )

        if stdout:
            match = re.search(r'Distinguished-Name\s+REG_SZ\s+(.+)', stdout)
            if match:
                dn = match.group(1).strip()
                if dn:
                    debug_print(f"Distinguished Name retrieved: {dn}")
                    logging.info(f"[WINRM] DN={dn}")
                    return dn

        logging.warning(f"[WINRM] Could not retrieve Distinguished Name (rc={rc})")
        return None

    def get_active_user(self) -> str | None:
        """
        Retrieves the currently active (logged-in) user on the remote machine.

        Runs 'quser' and looks for the Active/Actif session line.

        Returns:
            str: Username of the active session, or None if no active session.
        """
        stdout, stderr, rc = self._run("quser", arguments="")

        # quser output may appear in stdout or stderr depending on the environment
        output = (stdout or "") + (stderr or "")

        for line in output.split("\n"):
            if "Active" in line or "Actif" in line:
                parts = line.split()
                if parts:
                    username = parts[0].strip().lstrip(">")
                    debug_print(f"Active user retrieved: {username}")
                    logging.info(f"[WINRM] Active user={username}")
                    return username

        logging.warning(f"[WINRM] Could not retrieve active user (rc={rc})")
        return None

    def get_processes_to_csv(self) -> Path | None:
        """
        Retrieves the list of running processes and saves them to a CSV file.

        Runs PowerShell Get-Process on the remote machine, filters system
        processes, and saves the result locally as a CSV file.

        Returns:
            Path: Path to the created CSV file, or None on failure.
        """
        ps_script = (
            "Get-Process | "
            "Where-Object { $_.Name -notin @('System','svchost','wininit','lsass',"
            "'services','csrss','smss','winlogon') } | "
            "Select-Object Name,Id | Format-Table -AutoSize"
        )

        # Use _run_ps to avoid quoting issues with PowerShell commands
        stdout, stderr, rc = self._run_ps(ps_script, timeout=60)

        output = (stdout or "") + (stderr or "")

        if not output.strip():
            logging.warning("[WINRM] get_processes_to_csv: empty output")
            return None

        # Parse output - skip header and separator lines
        processes = set()
        start_parsing = False

        for line in output.split("\n"):
            if "----" in line:
                # Dashes mark the start of actual data rows
                start_parsing = True
                continue
            if start_parsing and line.strip():
                parts = line.split()
                if parts:
                    process_name = parts[0].strip()
                    # Filter out non-process lines and artifacts
                    if (process_name
                            and not process_name.isdigit()
                            and process_name not in ("Name", "exited", "on")):
                        processes.add(process_name)

        # Write CSV file locally
        csv_filename = Path(self.tmp_dir) / f"{self.netbios}_processus.csv"

        if csv_filename.exists():
            csv_filename.unlink()

        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["name"])
            for process in sorted(processes):
                writer.writerow([process])

        debug_print(f"CSV created: {csv_filename} ({len(processes)} processes)")
        logging.info(f"[WINRM] Processes CSV: {csv_filename} ({len(processes)} entries)")
        return csv_filename

    def kill_process(self, process_name: str) -> int:
        """
        Kills a process by name on the remote machine.

        Args:
            process_name (str): Process name with or without the .exe extension.

        Returns:
            int: 1 if the process was killed successfully, 0 otherwise.
        """
        # Ensure .exe extension is present
        if not process_name.lower().endswith(".exe"):
            process_name += ".exe"

        stdout, stderr, rc = self._run(
            "taskkill",
            arguments=f"/IM {process_name} /F"
        )

        output = (stdout or "") + (stderr or "")

        if rc == 0 or "SUCCESS" in output or "Opération réussie" in output:
            logging.info(f"[WINRM] Process killed: {process_name}")
            return 1

        logging.warning(f"[WINRM] Failed to kill {process_name} (rc={rc})")
        return 0

    def get_services_to_csv(self) -> Path | None:
        """
        Retrieves all Windows services and saves them to a CSV file.

        Runs 'sc query state= all' on the remote machine and parses the
        SERVICE_NAME, DISPLAY_NAME and STATE fields.

        Returns:
            Path: Path to the created CSV file, or None on failure.
        """
        stdout, stderr, rc = self._run(
            "sc",
            arguments="query state= all",
            timeout=60
        )

        output = (stdout or "") + (stderr or "")

        if not output.strip():
            logging.warning("[WINRM] get_services_to_csv: empty output")
            return None

        services = []
        current_service: dict = {}

        for line in output.split("\n"):
            line = line.strip()

            if line.startswith("SERVICE_NAME:"):
                # Save previous service before starting a new entry
                if current_service:
                    services.append(current_service)
                service_id = line.split(":", 1)[1].strip()
                current_service = {"id": service_id, "name": "", "etat": ""}

            elif line.startswith("DISPLAY_NAME:") and current_service:
                current_service["name"] = line.split(":", 1)[1].strip()

            elif line.startswith("STATE") and current_service:
                match = re.search(r"STATE\s*:\s*\d+\s+(\w+)", line)
                if match:
                    current_service["etat"] = match.group(1)

        # Don't forget the last service in the output
        if current_service:
            services.append(current_service)

        # Write CSV file locally
        csv_filename = Path(self.tmp_dir) / f"{self.netbios}_services.csv"

        if csv_filename.exists():
            csv_filename.unlink()

        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter=";")
            writer.writerow(["id", "name", "etat"])
            for svc in services:
                writer.writerow([svc["id"], svc["name"], svc["etat"]])

        debug_print(f"CSV created: {csv_filename} ({len(services)} services)")
        logging.info(f"[WINRM] Services CSV: {csv_filename} ({len(services)} entries)")
        return csv_filename

    def get_service_status(self, service_name: str) -> int:
        """
        Checks whether a specific service is running on the remote machine.

        Args:
            service_name (str): The service name (short name, not display name).

        Returns:
            int: 1 if the service is RUNNING, 0 otherwise.
        """
        stdout, stderr, rc = self._run("sc", arguments=f"query {service_name}")

        output = (stdout or "") + (stderr or "")
        match = re.search(r"STATE\s*:\s*\d+\s+(\w+)", output)

        if match and match.group(1).strip() == "RUNNING":
            logging.info(f"[WINRM] Service {service_name} is RUNNING")
            return 1

        logging.info(f"[WINRM] Service {service_name} is NOT running")
        return 0

    def start_service(self, service_name: str) -> bool:
        """
        Starts a service on the remote machine.

        Args:
            service_name (str): The service name (short name).

        Returns:
            bool: True if the command succeeded (rc=0), False otherwise.
        """
        stdout, stderr, rc = self._run("sc", arguments=f"start {service_name}")

        if rc == 0:
            logging.info(f"[WINRM] Service started: {service_name}")
            return True

        logging.warning(f"[WINRM] Failed to start {service_name} (rc={rc})")
        return False

    def stop_service(self, service_name: str) -> bool:
        """
        Stops a service on the remote machine.

        Args:
            service_name (str): The service name (short name).

        Returns:
            bool: True if the command succeeded (rc=0), False otherwise.
        """
        stdout, stderr, rc = self._run("sc", arguments=f"stop {service_name}")

        if rc == 0:
            logging.info(f"[WINRM] Service stopped: {service_name}")
            return True

        logging.warning(f"[WINRM] Failed to stop {service_name} (rc={rc})")
        return False

    def restart_service(self, service_name: str) -> bool:
        """
        Restarts a service on the remote machine by stopping then starting it.

        Uses a single cmd /c call with && to chain stop and start atomically.

        Args:
            service_name (str): The service name (short name).

        Returns:
            bool: True if both stop and start succeeded, False otherwise.
        """
        stdout, stderr, rc = self._run(
            "cmd.exe",
            arguments=f"/c sc stop {service_name} && sc start {service_name}",
            timeout=60
        )

        if rc == 0:
            logging.info(f"[WINRM] Service restarted: {service_name}")
            return True

        logging.warning(f"[WINRM] Failed to restart {service_name} (rc={rc})")
        return False

    def run_script(self, script_file: Path, timeout: int = DEFAULT_SCRIPT_TIMEOUT) -> bool:
        """
        Copies a script to the remote machine and executes it via WinRM.

        The script is copied via the administrative share (\\\\IP\\c$\\windows\\temp),
        then executed remotely. Supported formats: .ps1, .bat, .cmd.
        The temporary file is removed from the remote machine after execution.

        Args:
            script_file (Path): Path to the local script file.
            timeout (int): Execution timeout in seconds.

        Returns:
            bool: True if the script was copied and executed successfully.

        Raises:
            FileNotFoundError: If the local script file does not exist.
            ValueError: If the file extension is not supported.
        """
        script_file = Path(script_file)

        if not script_file.exists():
            raise FileNotFoundError(f"Script file not found: {script_file}")

        extension = script_file.suffix.lower()
        supported = [".ps1", ".bat", ".cmd"]

        if extension not in supported:
            raise ValueError(
                f"Unsupported extension: {extension}. "
                f"Supported: {', '.join(supported)}"
            )

        # Copy script to remote machine via administrative network share
        remote_share = f"\\\\{self.ip_address}\\c$\\windows\\temp\\"
        remote_exec_path = f"C:\\windows\\temp\\{script_file.name}"

        try:
            shutil.copy2(script_file, remote_share)
            logging.info(f"[WINRM] Script copied to {remote_share}{script_file.name}")
        except Exception as e:
            logging.error(f"[WINRM] Failed to copy script: {e}")
            return False

        # Execute remotely depending on the script type
        try:
            if extension == ".ps1":
                # _run_ps Base64-encodes the command - avoids all quoting issues
                ps_script = (
                    f"Set-ExecutionPolicy Bypass -Scope Process -Force; "
                    f"& '{remote_exec_path}'"
                )
                stdout, stderr, rc = self._run_ps(ps_script, timeout=timeout)
            else:
                # .bat or .cmd - run via cmd.exe
                stdout, stderr, rc = self._run(
                    "cmd.exe",
                    arguments=f"/c \"{remote_exec_path}\"",
                    timeout=timeout
                )

            if rc == 0:
                logging.info(f"[WINRM] Script executed successfully: {script_file.name}")
                return True

            logging.warning(f"[WINRM] Script failed (rc={rc}): {script_file.name}")
            return False

        finally:
            # Always clean up the remote script file after execution
            try:
                remote_file = Path(
                    f"\\\\{self.ip_address}\\c$\\windows\\temp\\{script_file.name}"
                )
                if remote_file.exists():
                    remote_file.unlink()
                    logging.info(f"[WINRM] Remote script cleaned up: {remote_file}")
            except Exception as e:
                logging.warning(f"[WINRM] Could not clean up remote script: {e}")


if __name__ == "__main__":
    # Quick test - replace with a real IP and hostname
    ip = "192.168.1.1"
    hostname = "PC-TEST"

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    try:
        mgr = PsExecManager(ip, hostname, r"bin", "tmp")

        print(f"Product Name   : {mgr.get_product_name()}")
        print(f"Display Version: {mgr.get_display_version()}")
        print(f"Active User    : {mgr.get_active_user()}")
        print(f"DN             : {mgr.get_distinguished_name()}")

    except Exception as e:
        print(f"Error: {e}")