import sys
import json
import configparser
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import ping3
import logging
import ipaddress
from datetime import datetime
from pathlib import Path
from wakeonlan import send_magic_packet

# local class
from psexec import PsExecManager
from process import ProcessManager
from service import ServiceManager
from wolmanager import WolManager
from explorer import DualFileExplorer


# Begin --- Display print function when not compiled
def is_compiled():
    """Detects if the application is compiled with PyInstaller"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def debug_print(*args, **kwargs):
    """Print only if the application is not compiled"""
    if not is_compiled():
        print(*args, **kwargs)
# End --- Display print function when not compiled

# Get local paths , needed for compilation use
def get_application_path():
    """Returns the application path (PyInstaller compatible)"""
    if getattr(sys, 'frozen', False):
        # If the application is compiled with PyInstaller
        return Path(sys.executable).parent
    else:
        # If the application runs normally
        return Path(__file__).parent

SCRIPT_DIR = get_application_path()
CONFIG_JSON = SCRIPT_DIR / "config.json"
LOG_PATH = SCRIPT_DIR / "tmp"
MAIN_LOG = SCRIPT_DIR / "HelpIT.log"
BIN_PATH = SCRIPT_DIR / "bin"

# Creating the necessary folders
BIN_PATH.mkdir(exist_ok=True)
LOG_PATH.mkdir(exist_ok=True)

# logging config
logging.basicConfig(
    filename=MAIN_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

debug_print(f"log dir {str(LOG_PATH)}")
debug_print(f"config.json path {CONFIG_JSON}")

class ToolTip:
    """Create a tooltip for a widget"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Arial", 9, "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def update_text(self, new_text):
        """Update tooltip text"""
        self.text = new_text

class HelpITGUI:
    """GUI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HelpIT")
        self.root.geometry("440x255")

        # Component Initialization
        self.config = configparser.ConfigParser()

        # Variables
        self.default_local_path = ""
        self.ping_threshold = ""
        self.current_target = ""
        self.current_ip = ""
        self.current_hostname = ""
        self.current_os_name = ""
        self.current_os_version = ""
        self.logged_user = ""
        self.fqdn = ""

        # PsExecManager instance (will be initialized upon target validation)
        self.psexec = None
        self.psexec_path = str(BIN_PATH / "PsExec64.exe")

        # References to open manager windows (Process and Service managers)
        self.process_manager = None
        self.service_manager = None
        self.open_explorer = None

        # Loading config
        self._load_config()

        # Create user interface
        self._create_widgets()

        # Starting log
        logging.info(f"Start HelpIT")

    def create_default_config(self, file_path: Path) -> None:
        """
        Create a default configuration file if it does not exist.

        Args:
            file_path (Path): The path to the configuration file.
        """
        default_config = {
              "default_path": "C:\\temp",
              "ping_threshold" : 75
        }

        with open(file_path, "w") as file:
            json.dump(default_config, file, indent=4)


    def _load_config(self):
        """Load config"""
        if not CONFIG_JSON.exists():
            logging.error(f"WARNING: config.json is missing in  {CONFIG_JSON}")
            debug_print(f"WARNING: config.json is missing in  {CONFIG_JSON}")
            self.create_default_config(CONFIG_JSON)

        if CONFIG_JSON.exists():
            try:
                with open(str(CONFIG_JSON), "r") as file:
                    self.data = json.load(file)
            except Exception as e:
                logging.error(f"ERROR loading config: {e}")
                messagebox.showerror("ERROR", "ERROR loading config")
                sys.exit(1)

        else:
            messagebox.showerror("ERROR",  "Config file missing.")
            sys.exit(1)

        self.ping_threshold = self.data["ping_threshold"]
        self.default_local_path = self.data["default_path"]

        if not Path(self.psexec_path).exists():
            messagebox.showerror("ERROR", "PsExec64 missing.")
            sys.exit(1)

    def get_mac_address(self, ip_address):
        """
        Retrieve the MAC address for a given IP address using ARP table.
        Works on Windows by executing 'arp -a' command.

        Args:
            ip_address: The IP address to look up

        Returns:
            str: The MAC address in format XX-XX-XX-XX-XX-XX, or None if not found
        """
        try:
            # Execute arp -a command to get ARP table
            result = subprocess.run(
                ['arp', '-a', ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse the output to find MAC address
                # Windows ARP output format: Internet Address      Physical Address      Type
                #                           192.168.1.100          6c-02-e0-00-8d-39     dynamic
                lines_output = result.stdout.splitlines()

                for line in lines_output:
                    if ip_address in line:
                        # Split the line and look for MAC address pattern
                        parts = line.split()
                        for part in parts:
                            # Check if this part matches MAC address pattern (xx-xx-xx-xx-xx-xx)
                            if '-' in part and len(part) == 17:
                                # Validate it's a proper MAC address
                                mac_parts = part.split('-')
                                if len(mac_parts) == 6 and all(len(p) == 2 for p in mac_parts):
                                    # Convert to uppercase for consistency
                                    mac_address = part.upper()
                                    logging.info(f"MAC address found for {ip_address}: {mac_address}")
                                    return mac_address

                logging.warning(f"MAC address not found in ARP table for {ip_address}")
                return None
            else:
                logging.error(f"Failed to execute arp command: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logging.error(f"Timeout while retrieving MAC address for {ip_address}")
            return None
        except Exception as e:
            logging.error(f"Error retrieving MAC address for {ip_address}: {e}")
            return None

    def _create_widgets(self):
        """GUI widgets"""
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Edit zone
        ttk.Label(main_frame, text="Name / IP", font=('Arial', 12, 'bold'),
                  foreground='#3B99FE').grid(row=0, column=1, pady=5)

        self.input_target = ttk.Entry(main_frame, width=20)
        self.input_target.grid(row=1, column=1, padx=5, sticky=(tk.W, tk.E))
        self.input_target.bind('<Return>', lambda e: self.validate_target())

        self.input_target.focus_set()

        ttk.Button(main_frame, text="Check", command=self.validate_target).grid(row=1, column=2, sticky=tk.W)

        # Progress bar : begin to column 1 like input
        self.progressbar = ttk.Progressbar(main_frame, mode='determinate', length=200)
        self.progressbar.grid(row=2, column=1, columnspan=2, pady=5, padx=5, sticky=(tk.W, tk.E))

        # Information labels
        self.label_ping = ttk.Label(main_frame, text="", foreground='blue')
        self.label_ping.grid(row=3, column=1, padx=5)

        self.label_ip = ttk.Label(main_frame, text="IP/Name address : ")
        self.label_ip.grid(row=4, column=1, columnspan=3, sticky=tk.W)

        self.label_os = ttk.Label(main_frame, text="OS Version : ")
        self.label_os.grid(row=5, column=1, columnspan=3, sticky=tk.W)

        self.label_user = ttk.Label(main_frame, text="Session : ")
        self.label_user.grid(row=6, column=1, columnspan=3, sticky=tk.W)

        self.label_fqdn = ttk.Label(main_frame, text="AD Path : ")
        self.label_fqdn.grid(row=7, column=1, columnspan=3, sticky=tk.W)

        self.fqdn_tooltip = ToolTip(self.label_fqdn, "")

        # Actions frames
        action_frame = ttk.LabelFrame(main_frame, text="Actions", padding="5")
        action_frame.grid(row=1, column=0, rowspan=6, padx=5, sticky=(tk.N, tk.S))

        # Column 1 (buttons) : begin to row=0 to be aligned with input target (which is in row=1)
        ttk.Button(action_frame, text="Process", command=self.show_processes).grid(row=0, column=0, pady=2, padx=2,
                                                                                     sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Manage", command=self.open_computer_management).grid(row=1, column=0, pady=2,
                                                                                             padx=2, sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Services", command=self.open_services).grid(row=2, column=0, pady=2, padx=2,
                                                                                   sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="WOL", command=self.wake_on_lan).grid(row=3, column=0, pady=2, padx=2,
                                                                            sticky=tk.W + tk.E)
        # Column 2 (buttons)
        ttk.Button(action_frame, text="Assist", command=self.remote_assistance).grid(row=0, column=1, pady=2,
                                                                                         padx=2, sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="RDP", command=self.remote_desktop).grid(row=1, column=1, pady=2, padx=2,
                                                                                  sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Drive C", command=lambda: self.open_drive('C')).grid(row=2, column=1, pady=2,
                                                                                           padx=2, sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="CMD", command=self.open_remote_cmd).grid(row=3, column=1, pady=2, padx=2,
                                                                            sticky=tk.W + tk.E)

        # Statut bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=9, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        #ttk.Button(status_frame, text="⚙", width=3, command=self.change_password).pack(side=tk.LEFT, padx=2)
        ttk.Button(status_frame, text="Logs", width=5, command=self.open_logs).pack(side=tk.LEFT, padx=2)

    def _extract_first_ou(self, fqdn):
        """
        Extracts the first OU of a Distinguished Name

        Args:
        fqdn(str): The complete Distinguished Name

        Returns:
        str: The first OU found, or "?" if not found
        """
        if not fqdn or fqdn == "?":
            return "?"

        try:
            # Search for fist OU= in string chain
            import re
            match = re.search(r'OU=([^,]+)', fqdn)
            if match:
                return match.group(1)
            return "?"
        except Exception as e:
            logging.error(f"Error OU extraction : {e}")
            return "?"

    def _truncate_text(self, text, max_length=40):
        """
        Truncates text if it is too long

        Args:
            text(str): The text to truncate
            max_length(int): Maximum length

        Returns:
            str: The truncated text with "..." if necessary
        """
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text

    def _close_manager_windows(self):
        """
        Close any open Process or Service manager windows
        Called when validating a new target
        """
        # Close ProcessManager window if it exists
        if self.process_manager:
            try:
                self.process_manager.close()
                logging.info("ProcessManager window closed due to new target validation")
            except Exception as e:
                logging.error(f"Error closing ProcessManager window: {e}")
            finally:
                self.process_manager = None

        # Close ServiceManager window if it exists
        if self.service_manager:
            try:
                self.service_manager.close()
                logging.info("ServiceManager window closed due to new target validation")
            except Exception as e:
                logging.error(f"Error closing ServiceManager window: {e}")
            finally:
                self.service_manager = None


    def validate_target(self):
        # Close any open manager windows when validating a new targetp
        self._close_manager_windows()

        """Validates and retrieves the target's information"""
        target = self.input_target.get().strip()
        if not target:
            messagebox.showwarning("Warning", "Please enter an IP address or hostname.")
            return

        # Ping threshold in milliseconds (adjustable)
        ping_limit = int(self.ping_threshold)

        # Test if it's an IP address and validate
        is_valid_ip = False

        # Check if it looks like an IP address (contains periods and numbers)
        if '.' in target and any(c.isdigit() for c in target):
            try:
                ipaddress.ip_address(target)
                is_valid_ip = True
                logging.info(f"Valid IP address : {target}")
            except ValueError:
                messagebox.showerror("Error", f"Invalid IP address : {target}")
                logging.warning(f"Invalid IP address : {target}")
                return
        else:
            # This is not an IP address, it's a hostname.
            logging.info(f"Hostname detected : {target}")

        self.current_target = target
        self.progressbar['value'] = 0

        # Test ping
        try:
            ping_time = ping3.ping(target, timeout=2)
            if ping_time is None or ping_time is False or ping_time <= 0:
                self.label_ping.config(text="No ping", foreground='red')
                logging.warning(f"Error no response for {target}")
                return

            ping_ms = int(ping_time * 1000)

            # Determine the color based on the response time
            if ping_ms >= ping_limit:
                color = 'orange'
                logging.warning(f"Slow ping with {target}: {ping_ms}ms (threshold : {str(ping_limit)}ms)")
            else:
                color = 'green'
                logging.info(f"Ping to {target}: {ping_ms}ms")

            self.label_ping.config(text=f"Ping: {ping_ms}ms", foreground=color)
            logging.info(f"Ping to {target}: {ping_ms}ms")

        except Exception as e:
            self.label_ping.config(text="Error ping", foreground='red')
            logging.error(f"Error ping vers {target}: {e}")
            return

        self.progressbar['value'] = 10

        # Solve Name / IP
        try:
            if is_valid_ip:
                self.current_ip = target
                self.current_hostname = socket.gethostbyaddr(target)[0]
            else:
                self.current_hostname = target
                self.current_ip = socket.gethostbyname(target)

            self.label_ip.config(text=f"Name : {self.current_hostname} | IP: {self.current_ip}")

        except Exception as e:
            logging.error(f"Error solving {target}: {e}")
            self.label_ip.config(text=f"Address : {target}")

        self.progressbar['value'] = 20

        # Retrieve MAC address and store it in the database
        try:
            # Get MAC address from ARP table
            mac_address = self.get_mac_address(self.current_ip)

            if mac_address:
                # Initialize WolManager and store the MAC address
                wol_manager = WolManager("config.sqlite")
                row_id = wol_manager.update_mac_address(mac_address, self.current_hostname)
                logging.info(
                    f"MAC address stored in database: {mac_address} for {self.current_hostname} (ID: {row_id})")
            else:
                logging.warning(f"Could not retrieve MAC address for {self.current_ip}")
        except Exception as e:
            # Don't stop the validation process if MAC retrieval fails
            logging.error(f"Error storing MAC address in database: {e}")

        self.progressbar['value'] = 40

        self.psexec = PsExecManager(self.current_ip,netbios=self.current_hostname ,psexec_path=self.psexec_path,tmp_dir=str(LOG_PATH))

        self.progressbar['value'] = 50

        self.current_os_name = self.psexec.get_product_name()
        if not self.current_os_name: self.current_os_name = "?"

        self.progressbar['value'] = 60

        self.current_os_version = self.psexec.get_display_version()
        if not self.current_os_version: self.current_os_version = "?"

        self.progressbar['value'] = 60

        self.label_os.config(text=f"OS Version : {self.current_os_name} {self.current_os_version}")

        self.progressbar['value'] = 80

        self.logged_user = self.psexec.get_active_user()
        if not self.logged_user: self.logged_user = "?"
        self.label_user.config(text=f"Session : {self.logged_user}")

        self.progressbar['value'] = 90

        self.fqdn = self.psexec.get_distinguished_name()
        if not self.fqdn:
            self.fqdn = "?"
            first_ou = "?"
        else:
            first_ou = self._extract_first_ou(self.fqdn)

        # Truncate if string chain to long
        display_text = f"AD path : {first_ou}"
        truncated_text = self._truncate_text(display_text, 40)

        self.label_fqdn.config(text=truncated_text)

        # Update Tooltip with complete path
        self.fqdn_tooltip.update_text(self.fqdn)

        self.progressbar['value'] = 100

        # Session log
        log_file = LOG_PATH / f"{self.current_hostname}.log"
        with open(log_file, 'a') as f:
            f.write(f"\n{'=' * 50}\n")
            f.write(f"Session run : {datetime.now()}\n")
            f.write(f"Name : {self.current_hostname} | IP: {self.current_ip}\n")
            f.write(f"User : {self.logged_user}\n")
            f.write(f"OS : {self.current_os_name} {self.current_os_version}\n")
            f.write(f"Ping : {ping_ms}ms\n")
            f.write(f"{'=' * 50}\n")

        logging.info(f"Session running for {self.current_hostname} ({self.current_ip})")

    def show_processes(self):
        if not self.current_ip:
            messagebox.showwarning("Warning", "Select a valid target first.")
            return

        try:
            self.psexec.get_processes_to_csv()
            csv_filename = Path(LOG_PATH / f"{self.current_hostname}_processus.csv")

            # Check if CSV file was created successfully
            if csv_filename.exists():
                # Create and show the ProcessManager window
                self.process_manager = ProcessManager(
                    csv_filename=csv_filename,
                    psexec_manager=self.psexec,
                    current_ip=self.current_ip,
                    current_hostname=self.current_hostname,
                    psexec_path=self.psexec_path,
                    log_path=str(LOG_PATH)
                )
                # Note: ProcessManager window will handle its own mainloop as a Toplevel window

        except Exception as e:
            logging.error(f"Error with process manager : {e}")
            messagebox.showerror("Error", "Process manager issue.")

    def open_computer_management(self):
        """Open the computer management console"""
        if not self.current_ip:
            messagebox.showwarning("Warning", "Select a valid target first.")
            return

        try:
            subprocess.Popen(f'compmgmt.msc /computer={self.current_ip}', shell=True)
        except Exception as e:
            logging.error(f"Error can't open computer management : {e}")
            messagebox.showerror("Error", "Can't open computer management console")

    def open_services(self):
        if not self.current_ip:
            messagebox.showwarning("Warning", "Select a valid target first.")
            return
        try:
            # PsExec is mandatory
            self.psexec.get_services_to_csv()
            csv_filename = Path(LOG_PATH / f"{self.current_hostname}_services.csv")
            # Check if CSV file was created successfully
            if csv_filename.exists():
                # Create and show the ServiceManager window
                self.service_manager = ServiceManager(
                    csv_filename=csv_filename,
                    psexec_manager=self.psexec,
                    current_ip=self.current_ip,
                    current_hostname=self.current_hostname,
                    psexec_path=self.psexec_path,
                    log_path=str(LOG_PATH)
                )
                # Note: ServiceManager window will handle its own mainloop as a Toplevel window

        except Exception as e:
            logging.error(f"Error can't open services management : {e}")
            messagebox.showerror("Error", "Can't open services management console")

    def remote_assistance(self):
        """Microsoft assist"""
        if not self.current_ip:
            messagebox.showwarning("Warning", "Select a valid target first.")
            return
        command_string = f'msra.exe /offerra {self.current_ip}'
        subprocess.run(command_string, shell=True, check=True, capture_output=True, text=True)

    def remote_desktop(self):
        """Microsoft RDP"""
        if not self.current_ip:
            messagebox.showwarning("Warning", "Select a valid target first.")
            return
        try:
            if sys.platform == 'win32':
                subprocess.Popen(f'mstsc /v:{self.current_ip}')
                logging.info(f"RDP to {self.current_ip}")
            else:
                # Pour Linux, utiliser rdesktop ou xfreerdp
                subprocess.Popen(f'xfreerdp /v:{self.current_ip}')
        except Exception as e:
            logging.error(f"Error remote desktop : {e}")
            messagebox.showerror("Error", "Remote desktop issue.")

    def open_drive(self, drive_letter):
        if not self.current_ip:
            messagebox.showwarning("Warning", "Select a valid target first.")
            return
        self.open_explorer = DualFileExplorer(left_dir=self.default_local_path ,ip=self.current_ip)

    def wake_on_lan(self):
        """Send a Wake-on-LAN magic packet to all MAC addresses associated with the current hostname"""
        # Check if a target hostname has been validated
        if not self.current_hostname:
            messagebox.showwarning("Warning", "Select a valid target first.")
            return

        try:
            # Initialize the WolManager to access the database
            wol_manager = WolManager("config.sqlite")

            # Retrieve all MAC addresses associated with the current hostname
            mac_addresses = wol_manager.read_mac_address(self.current_hostname)

            # Check if any MAC addresses were found
            if not mac_addresses:
                messagebox.showwarning("Warning",
                                       f"No mac adress for {self.current_hostname}")
                logging.warning(f"No mac adress for {self.current_hostname}")
                return

            # Counter for successful packets sent
            success_count = 0
            failed_macs = []

            # Iterate through all MAC addresses and send magic packet to each
            for mac_address in mac_addresses:
                try:
                    # Send the Wake-on-LAN magic packet
                    send_magic_packet(mac_address)
                    success_count += 1
                    logging.info(f"WOL packet sent to {self.current_hostname} ({mac_address})")
                except Exception as e:
                    # Log individual failures but continue with other MAC addresses
                    failed_macs.append(mac_address)
                    logging.error(f"Failed to send WOL to {mac_address}: {e}")

            # Display result message to user
            if success_count > 0:
                if failed_macs:
                    # Partial success
                    messagebox.showinfo("Success",
                                        f"WOL packet successfully send : {success_count}/{len(mac_addresses)}\n"
                                        f"Failed MAC: {', '.join(failed_macs)}")
                else:
                    # Complete success
                    messagebox.showinfo("Success",
                                        f"WOL packet successfully send to {success_count} MAC adress\n"
                                        f"Target : {self.current_hostname}")
            else:
                # All packets failed
                messagebox.showerror("Error",
                                     f"Failed to send WOL packet to {self.current_hostname}")

        except Exception as e:
            # Handle any unexpected errors
            logging.error(f"Error in wake_on_lan: {e}")
            messagebox.showerror("Error", f"Error sending WOL packet: {e}")

    def open_remote_cmd(self):
        # Open a distant command terminal
        if not self.current_ip:
            messagebox.showwarning("Warning", "Select a valid target first.")
            return

        try:
            if sys.platform == 'win32':
                # PsExec ismandatory
                self.psexec.open_terminal()

        except Exception as e:
            logging.error(f"Error opening terminal: {e}")
            messagebox.showerror("Error", "Couldn't open terminal")

    def open_logs(self):
        """Open log folder"""
        try:
            if sys.platform == 'win32':
                os.startfile(LOG_PATH)
            else:
                subprocess.Popen(['xdg-open', LOG_PATH])
        except Exception as e:
            logging.error(f"Error opening logs : {e}")

    def run(self):
        """Launch app"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Manage closing app"""
        logging.info(f"HelpIT close")
        self.root.destroy()

def main():
    app = HelpITGUI()
    app.run()


if __name__ == "__main__":
    main()