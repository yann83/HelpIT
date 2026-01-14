import subprocess
import re
import csv
import sys
from pathlib import Path


# Begin --- Display print function when not compiled
def is_compiled():
    """Detects if the application is compiled with PyInstaller"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def debug_print(*args, **kwargs):
    """Print only if the application is not compiled"""
    if not is_compiled():
        print(*args, **kwargs)


# End --- Display print function when not compiled


class PsExecManager:
    """
    Class for managing PsExec commands on remote machines
    Handles all subprocess calls with proper console window hiding for compiled versions
    """

    def __init__(self, ip_address, netbios, psexec_path, tmp_dir):
        """
        Initializes the PsExec handler

        Args:
            ip_address (str): IP address of the remote machine
            netbios (str): NetBIOS name of the remote machine
            psexec_path (str): Path to PsExec64.exe
            tmp_dir (str): Temporary directory path
        """
        self.ip_address = ip_address
        self.netbios = netbios
        self.psexec_path = psexec_path
        self.tmp_dir = tmp_dir

        # Ps exe
        self.psexec = psexec_path + '\\PsExec64.exe'
        self.pskill = psexec_path + '\\pskill64.exe'
        self.pslist = psexec_path + '\\pslist64.exe'
        self.psservice = psexec_path + '\\PsService64.exe'

        test_paths = [self.psexec, self.pskill, self.pslist, self.psservice]

        # Create tmp dir if not exist
        Path(self.tmp_dir).mkdir(parents=True, exist_ok=True)

        # Check if Psexec exist
        for test_path in test_paths:
            if not Path(test_path).exists():
                raise FileNotFoundError(f"{test_path} not found.")

    def _get_base_command(self, ps_exe):
        """
        Returns the basic PsExec command

        Returns:
            list: List of basic arguments
        """
        return [ps_exe, "-accepteula", f"\\\\{self.ip_address}"]

    def _get_subprocess_flags(self, hide_window=True):
        """
        Returns the appropriate subprocess flags for Windows to hide console windows

        Args:
            hide_window (bool): If True, hide the console window. If False, show it.

        Returns:
            tuple: (startupinfo, creationflags) for subprocess calls
        """
        startupinfo = None
        creationflags = 0

        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()

            if hide_window:
                # Hide the console window
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                # CREATE_NO_WINDOW prevents console window creation
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                # Show the console window in a new console
                creationflags = subprocess.CREATE_NEW_CONSOLE

        return startupinfo, creationflags

    def _execute_command(self, ps_exe, command_args, timeout=30):
        """
        Executes a PsExec command with hidden console window

        Args:
            command_args (list): Additional arguments for the command
            timeout (int): Timeout in seconds

        Returns:
            subprocess.CompletedProcess: Execution result or None if error
        """
        full_command = self._get_base_command(ps_exe) + command_args

        try:
            # Get flags to hide console window
            startupinfo, creationflags = self._get_subprocess_flags(hide_window=True)

            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                encoding='cp850',
                errors='ignore',
                timeout=timeout,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            return result
        except subprocess.TimeoutExpired:
            debug_print(f"Timeout on {self.ip_address}")
            return None
        except Exception as e:
            debug_print(f"Error running command: {e}")
            return None

    def open_terminal(self):
        """
        Open a command prompt (cmd) on the remote machine.
        Note: This command is interactive and blocks execution.
        This method SHOWS the window because user interaction is needed.
        """
        command = self._get_base_command(self.psexec) + ["cmd.exe"]

        # Get flags to SHOW the console window (user needs to interact)
        startupinfo, creationflags = self._get_subprocess_flags(hide_window=False)

        subprocess.Popen(
            ['start', 'cmd', '/k'] + command,
            shell=True,
            startupinfo=startupinfo,
            creationflags=creationflags
        )

    def get_distinguished_name(self):
        """
        Retrieves the machine's Distinguished Name from Active Directory
        Uses 3 different methods to ensure compatibility with admin privileges

        Returns:
            str: Distinguished Name or None in case of error
        """
        # Method 1: Query with -s (system account) flag - Standard approach
        command_args = [
            "-s", "reg", "query",
            r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Group Policy\State\Machine",
            "/v", "Distinguished-Name"
        ]

        result = self._execute_command(self.psexec, command_args, timeout=15)

        if result and result.returncode == 0:
            match = re.search(r'Distinguished-Name\s+REG_SZ\s+(.+)', result.stdout)
            if match:
                dn = match.group(1).strip()
                if dn:
                    debug_print(f"Distinguished Name retrieved : {dn}")
                    return dn

        debug_print("Could not retrieve Distinguished Name")
        return None

    def get_product_name(self):
        """
        Retrieves the Windows product name
        Uses fallback methods to ensure compatibility

        Returns:
            str: Product name or None in case of error
        """
        # Method 1: Standard approach with -s flag
        command_args = [
            "-s", "reg", "query",
            r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion",
            "/v", "ProductName"
        ]

        result = self._execute_command(self.psexec, command_args)

        if result and result.returncode == 0:
            match = re.search(r'ProductName\s+REG_SZ\s+(.+)', result.stdout)
            if match:
                pn = match.group(1).strip()
                if pn:
                    debug_print(f"Product Name retrieved : {pn}")
                    return pn

        debug_print("Could not retrieve Product Name")
        return None


    def get_display_version(self):
        """
        Retrieves the Windows display version
        Uses fallback methods to ensure compatibility

        Returns:
            str: Display version or None in case of error
        """
        # Method 1: Standard approach with -s flag
        command_args = [
            "-s", "reg", "query",
            r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion",
            "/v", "displayversion"
        ]

        result = self._execute_command(self.psexec, command_args)

        if result and result.returncode == 0:
            match = re.search(r'displayversion\s+REG_SZ\s+(.+)', result.stdout)
            if match:
                dv = match.group(1).strip()
                if dv:
                    debug_print(f"Display Version retrieved : {dv}")
                    return dv

        debug_print("Could not retrieve Display Version")
        return None

    def get_active_user(self):
        """
        Retrieves the active user on the machine

        Returns:
            str: Active username or None in case of error
        """
        command_args = ["quser"]

        result = self._execute_command(self.psexec, command_args)

        if result and result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Actif' in line or 'Active' in line:
                    # Extract username (first column)
                    parts = line.split()
                    if parts:
                        debug_print(f"Active user retrieved : {parts}")
                        return parts[0].strip()

        debug_print("Could not retrieve Active user")
        return None

    def get_processes_to_csv(self):
        """
        Retrieves the list of processes and saves it as a CSV file.

        Returns:
            str: Path to the created CSV file or None in case of error
        """
        command_args = [
            "powershell",
            "Get-Process | Where-Object { $_.Name -notin @('System','svchost','wininit','lsass','services','csrss','smss','winlogon') } | Select-Object Name,Id"
        ]

        result = self._execute_command(self.psexec, command_args, timeout=60)

        if result and result.returncode == 0:
            # Parse the output
            lines = result.stdout.split('\n')
            processes = set()  # Use a set to have unique values

            # Find where the list of processes begins (after "Name" and "----")
            start_parsing = False
            for line in lines:
                if '----' in line:
                    start_parsing = True
                    continue

                if start_parsing and line.strip():
                    # Extract process name (first column)
                    parts = line.split()
                    if parts and not parts[0].startswith('PsExec') and parts[0] not in ['powershell', 'exited', 'on']:
                        process_name = parts[0].strip()
                        if process_name and not process_name.isdigit():
                            processes.add(process_name)

            # Create CSV file
            csv_filename = Path(self.tmp_dir) / f"{self.netbios}_processus.csv"

            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['name'])
                for process in sorted(processes):
                    writer.writerow([process])

            debug_print(f"CSV file created: {csv_filename} ({len(processes)} unique processes)")
            return csv_filename

        return None

    def kill_process(self, process_name):
        """
        Kills a process by name

        Args:
            process_name (str): Process name (with or without .exe)

        Returns:
            int: 1 if at least one operation was successful, 0 otherwise
        """
        # Add .exe if necessary
        if not process_name.endswith('.exe'):
            process_name += '.exe'

        command_args = ["taskkill", "/IM", process_name, "/F"]

        result = self._execute_command(self.psexec, command_args)

        if result:
            # Check if "Operation successful" appears in the output
            if "Opération réussie" in result.stdout or "SUCCESS" in result.stdout:
                return 1

        return 0

    def get_services_to_csv(self):
        """
        Retrieves the list of services and saves it as a CSV file.

        Returns:
            str: Path to the created CSV file or None in case of error
        """
        command_args = ["sc", "query", "state=", "all"]

        result = self._execute_command(self.psexec, command_args, timeout=60)

        if result and result.returncode == 0:
            # Dictionary for mapping status codes (not used but kept for reference)
            state_map = {
                '1': 'STOPPED',
                '2': 'START_PENDING',
                '3': 'STOP_PENDING',
                '4': 'RUNNING',
                '5': 'CONTINUE_PENDING',
                '6': 'PAUSE_PENDING',
                '7': 'PAUSED'
            }

            services = []
            current_service = {}

            lines = result.stdout.split('\n')

            for line in lines:
                line = line.strip()

                if line.startswith('SERVICE_NAME:'):
                    # If we already have a service running, we save it
                    if current_service:
                        services.append(current_service)
                    # New service
                    service_name = line.split(':', 1)[1].strip()
                    current_service = {'id': service_name, 'name': '', 'etat': ''}

                elif line.startswith('DISPLAY_NAME:') and current_service:
                    display_name = line.split(':', 1)[1].strip()
                    current_service['name'] = display_name

                elif line.startswith('STATE') and current_service:
                    # Extract status code
                    match = re.search(r'STATE\s*:\s*(\d+)\s+(\w+)', line)
                    if match:
                        state_code = match.group(1)
                        state_name = match.group(2)
                        current_service['etat'] = state_name

            # Add last service
            if current_service:
                services.append(current_service)

            # Create CSV file
            csv_filename = Path(self.tmp_dir) / f"{self.netbios}_services.csv"

            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(['id', 'name', 'etat'])
                for service in services:
                    writer.writerow([service['id'], service['name'], service['etat']])

            debug_print(f"CSV file created: {csv_filename} ({len(services)} services)")
            return csv_filename

        return None

    def get_service_status(self, service_name):
        """
        Checks if a service is running

        Args:
            service_name (str): Name of the service

        Returns:
            int: 1 if RUNNING, 0 otherwise
        """
        command_args = ["sc", "query", service_name]

        result = self._execute_command(self.psexec, command_args)

        if result and result.returncode == 0:
            match = re.search(r'STATE\s*:\s*\d+\s+(\w+)', result.stdout)
            if match:
                state = match.group(1).strip()
                if state == 'RUNNING':
                    return 1

        return 0

    def start_service(self, service_name):
        """
        Starts a service

        Args:
            service_name (str): Name of the service

        Returns:
            bool: True if successful, False otherwise
        """
        command_args = ["sc", "start", service_name]

        result = self._execute_command(self.psexec, command_args)

        if result and result.returncode == 0:
            return True

        return False

    def stop_service(self, service_name):
        """
        Stops a service

        Args:
            service_name (str): Name of the service

        Returns:
            bool: True if successful, False otherwise
        """
        command_args = ["sc", "stop", service_name]

        result = self._execute_command(self.psexec, command_args)

        if result and result.returncode == 0:
            return True

        return False

    def restart_service(self, service_name):
        """
        Restarts a service

        Args:
            service_name (str): Service name

        Returns:
            bool: True if successful, False otherwise
        """
        command_args = ["cmd", "/c", f"sc stop {service_name} && sc start {service_name}"]

        result = self._execute_command(self.psexec, command_args, timeout=60)

        if result and result.returncode == 0:
            return True

        return False

    def run_script(self, script_file):
        #powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%DOSSIER_DISTANT%\%SCRIPT_NAME%"
        script_path = f"C:\\windows\\temp\\{script_file}"
        command_args = ["powershell.exe", "-ExecutionPolicy", "Bypass","-NoProfile","-File",  f'"{script_path}"']

        result = self._execute_command(self.psexec, command_args, timeout=60)

        if result and result.returncode == 0:
            return True

        return False


if __name__ == "__main__":
    # Replace with your hostname / IP
    ip = "55.184.25.84"

    try:
        psexec = PsExecManager(ip, "P118301-076-033", r"C:\CONFIDENTIEL\PROJETS\HelpIT\bin", "tmp")



        # Retrieve system information
        debug_print(f"Distinguished Name: {psexec.get_distinguished_name()}")
        debug_print(f"Active User: {psexec.get_active_user()}")
        """
        debug_print(f"Product Name: {psexec.get_product_name()}")
        debug_print(f"Display Version: {psexec.get_display_version()}")
        debug_print(f"Active User: {psexec.get_active_user()}")

        # Recover the processes
        debug_print("\nRecover the processes...")
        psexec.get_processes_to_csv()

        # Kill a process
        debug_print("\nStop firefox...")
        res = psexec.kill_process("firefox")
        debug_print(f"Result: {'Success' if res == 1 else 'Fail'}")

        # Recover services
        debug_print("\nRecover services...")
        psexec.get_services_to_csv()

        # Check a service
        debug_print("\nCheck service...")
        is_running = psexec.get_service_status("")
        debug_print(f"Service RUNNING: {'Yes' if is_running == 1 else 'No'}")
        """

    except FileNotFoundError as e:
        debug_print(f"Error: {e}")
    except Exception as e:
        debug_print(f"Unexpected error: {e}")