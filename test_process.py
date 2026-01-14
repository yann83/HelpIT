"""
Example usage of the ProcessManager module

This file demonstrates how to use the ProcessManager class
independently or integrated with the main application.
"""

import tkinter as tk
from pathlib import Path
from process import ProcessManager
from psexec import PsExecManager


def standalone_example():
    """
    Example of using ProcessManager as a standalone application
    """
    # Configuration
    REMOTE_IP = "192.168.1.100"
    REMOTE_HOSTNAME = "WORKSTATION-01"
    PSEXEC_PATH = r"D:\DOCUMENTS\PROGRAMMATION\Python\Projets\HelpIT\bin\PsExec64.exe"
    LOG_PATH = r"D:\DOCUMENTS\PROGRAMMATION\Python\Projets\HelpIT\tmp"
    CSV_FILE = r"D:\DOCUMENTS\PROGRAMMATION\Python\Projets\HelpIT\tmp\S118301-121-900_processus.csv"

    # Create main window (required for Toplevel)
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    try:
        # Initialize PsExecManager
        psexec_manager = PsExecManager(
            ip_address=REMOTE_IP,
            netbios=REMOTE_HOSTNAME,
            psexec_path=PSEXEC_PATH,
            tmp_dir=LOG_PATH
        )

        # Generate process list CSV
        print("Generating process list...")
        psexec_manager.get_processes_to_csv()

        # Check if CSV was created
        if Path(CSV_FILE).exists():
            print(f"Process list created: {CSV_FILE}")

            # Create and show ProcessManager
            process_manager = ProcessManager(
                csv_filename=CSV_FILE,
                psexec_manager=psexec_manager,
                current_ip=REMOTE_IP,
                current_hostname=REMOTE_HOSTNAME,
                psexec_path=PSEXEC_PATH,
                log_path=LOG_PATH
            )

            # Note: The ProcessManager window will handle its own event loop
            # as it uses Toplevel, so we need to keep the root window alive
            root.mainloop()

        else:
            print("Error: CSV file was not created")

    except Exception as e:
        print(f"Error: {e}")


def integrated_example():
    """
    Example showing how ProcessManager is integrated in the main application
    
    This is a simplified version of what happens in main.py
    """
    
    class SimpleApp:
        """Simplified version of HelpITGUI class"""
        
        def __init__(self):
            # Main application window
            self.root = tk.Tk()
            self.root.title("HelpIT - Simplified Example")
            self.root.geometry("300x150")
            
            # Configuration (these would come from your actual config)
            self.current_ip = "192.168.1.100"
            self.current_hostname = "WORKSTATION-01"
            self.psexec_path = "C:/Tools/PsExec64.exe"
            self.log_path = "C:/Logs"
            
            # Initialize PsExecManager
            self.psexec = PsExecManager(
                ip_address=self.current_ip,
                netbios=self.current_hostname,
                psexec_path=self.psexec_path,
                tmp_dir=self.log_path
            )
            
            # Create UI
            self.create_widgets()
        
        def create_widgets(self):
            """Create UI widgets"""
            label = tk.Label(
                self.root,
                text=f"Connected to:\n{self.current_hostname}\n({self.current_ip})",
                font=('Arial', 10)
            )
            label.pack(pady=20)
            
            # Button to open process manager
            btn_processes = tk.Button(
                self.root,
                text="Show Processes",
                command=self.show_processes,
                bg="#4CAF50",
                fg="white",
                font=('Arial', 10, 'bold'),
                width=15,
                height=2
            )
            btn_processes.pack(pady=10)
        
        def show_processes(self):
            """Open the process manager window"""
            try:
                # Generate process list
                self.psexec.get_processes_to_csv()
                csv_filename = Path(self.log_path) / f"{self.current_hostname}_processus.csv"
                
                if csv_filename.exists():
                    # Create ProcessManager window
                    process_manager = ProcessManager(
                        csv_filename=csv_filename,
                        psexec_manager=self.psexec,
                        current_ip=self.current_ip,
                        current_hostname=self.current_hostname,
                        psexec_path=self.psexec_path,
                        log_path=self.log_path
                    )
                else:
                    print("Error: Could not generate process list")
            
            except Exception as e:
                print(f"Error opening process manager: {e}")
        
        def run(self):
            """Run the application"""
            self.root.mainloop()
    
    # Create and run the application
    app = SimpleApp()
    app.run()


if __name__ == "__main__":
    print("ProcessManager Module - Example Usage")
    print("=" * 50)
    print()
    print("Choose an example:")
    print("1. Standalone usage (opens only ProcessManager)")
    print("2. Integrated usage (simulates main application)")
    print()
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\nRunning standalone example...")
        standalone_example()
    elif choice == "2":
        print("\nRunning integrated example...")
        integrated_example()
    else:
        print("Invalid choice. Please run again and select 1 or 2.")
