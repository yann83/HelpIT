"""
Example usage of the ServiceManager module

This file demonstrates how to use the ServiceManager class
independently or integrated with the main application.
"""

import tkinter as tk
from pathlib import Path
from service import ServiceManager
from psexec import PsExecManager


def standalone_example():
    """
    Example of using ServiceManager as a standalone application
    """
    # Configuration
    SCRIPT_DIR = Path(__file__).parent
    REMOTE_IP = "55.156.6.51"
    REMOTE_HOSTNAME = "s118301-121-900"
    PSEXEC_PATH = SCRIPT_DIR / "bin" / 'PsExec64.exe'
    LOG_PATH = SCRIPT_DIR / "tmp"
    CSV_FILE = SCRIPT_DIR / "tmp"/ "S118301-121-900_services.csv"

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

        # Generate service list CSV
        print("Generating service list...")
        # psexec_manager.get_services_to_csv()

        # Check if CSV was created
        if Path(CSV_FILE).exists():
            print(f"Service list created: {CSV_FILE}")

            # Create and show ServiceManager
            service_manager = ServiceManager(
                csv_filename=CSV_FILE,
                psexec_manager=psexec_manager,
                current_ip=REMOTE_IP,
                current_hostname=REMOTE_HOSTNAME,
                psexec_path=PSEXEC_PATH,
                log_path=LOG_PATH
            )

            # Note: The ServiceManager window will handle its own event loop
            # as it uses Toplevel, so we need to keep the root window alive
            root.mainloop()

        else:
            print("Error: CSV file was not created")

    except Exception as e:
        print(f"Error: {e}")


def integrated_example():
    """
    Example showing how ServiceManager is integrated in the main application
    
    This is a simplified version of what happens in main.py
    """
    
    class SimpleApp:
        """Simplified version of HelpITGUI class"""
        
        def __init__(self):
            # Main application window
            self.root = tk.Tk()
            self.root.title("HelpIT - Service Manager Example")
            self.root.geometry("300x200")
            
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
            
            # Button to open service manager
            btn_services = tk.Button(
                self.root,
                text="Show Services",
                command=self.open_services,
                bg="#2196F3",
                fg="white",
                font=('Arial', 10, 'bold'),
                width=15,
                height=2
            )
            btn_services.pack(pady=10)
        
        def open_services(self):
            """Open the service manager window"""
            try:
                # Generate service list
                self.psexec.get_services_to_csv()
                csv_filename = Path(self.log_path) / f"{self.current_hostname}_services.csv"
                
                if csv_filename.exists():
                    # Create ServiceManager window
                    service_manager = ServiceManager(
                        csv_filename=csv_filename,
                        psexec_manager=self.psexec,
                        current_ip=self.current_ip,
                        current_hostname=self.current_hostname,
                        psexec_path=self.psexec_path,
                        log_path=self.log_path
                    )
                else:
                    print("Error: Could not generate service list")
            
            except Exception as e:
                print(f"Error opening service manager: {e}")
        
        def run(self):
            """Run the application"""
            self.root.mainloop()
    
    # Create and run the application
    app = SimpleApp()
    app.run()


def test_service_operations():
    """
    Example of testing individual service operations
    """
    # Configuration
    REMOTE_IP = "192.168.1.100"
    REMOTE_HOSTNAME = "WORKSTATION-01"
    PSEXEC_PATH = "C:/Tools/PsExec64.exe"
    LOG_PATH = "C:/Logs"
    
    try:
        # Initialize PsExecManager
        psexec = PsExecManager(
            ip_address=REMOTE_IP,
            netbios=REMOTE_HOSTNAME,
            psexec_path=PSEXEC_PATH,
            tmp_dir=LOG_PATH
        )
        
        # Test service: Print Spooler (safe to test with)
        test_service = "Spooler"
        
        print(f"\nTesting service operations on '{test_service}'...\n")
        
        # 1. Check initial status
        print("1. Checking initial status...")
        status = psexec.get_service_status(test_service)
        print(f"   Status: {'RUNNING' if status == 1 else 'STOPPED'}")
        
        # 2. Stop the service if running
        if status == 1:
            print("\n2. Stopping service...")
            result = psexec.stop_service(test_service)
            print(f"   Result: {'Success' if result else 'Failed'}")
            
            # Check new status
            new_status = psexec.get_service_status(test_service)
            print(f"   New status: {'RUNNING' if new_status == 1 else 'STOPPED'}")
        
        # 3. Start the service
        print("\n3. Starting service...")
        result = psexec.start_service(test_service)
        print(f"   Result: {'Success' if result else 'Failed'}")
        
        # Check new status
        new_status = psexec.get_service_status(test_service)
        print(f"   New status: {'RUNNING' if new_status == 1 else 'STOPPED'}")
        
        # 4. Restart the service
        print("\n4. Restarting service...")
        result = psexec.restart_service(test_service)
        print(f"   Result: {'Success' if result else 'Failed'}")
        
        # Check final status
        final_status = psexec.get_service_status(test_service)
        print(f"   Final status: {'RUNNING' if final_status == 1 else 'STOPPED'}")
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")


def demo_csv_structure():
    """
    Demonstrate the CSV file structure for services
    """
    print("\n" + "="*60)
    print("SERVICE CSV FILE STRUCTURE")
    print("="*60)
    print("\nThe CSV file uses semicolon (;) as delimiter:")
    print("\nFormat:")
    print("  id;name;etat")
    print("\nExample rows:")
    print("  Audiosrv;Audio Windows;RUNNING")
    print("  Spooler;Print Spooler;STOPPED")
    print("  WAPTService;WAPT Service;RUNNING")
    print("\nColumns:")
    print("  - id:   Service short name (used for commands)")
    print("  - name: Service display name (shown to user)")
    print("  - etat: Service state (RUNNING, STOPPED, etc.)")
    print("\nImportant:")
    print("  ⚠️  Commands MUST use the 'id' column, not 'name'")
    print("  ✓  Correct:   stop_service('Audiosrv')")
    print("  ✗  Wrong:     stop_service('Audio Windows')")
    print("\n" + "="*60)


if __name__ == "__main__":
    standalone_example()

