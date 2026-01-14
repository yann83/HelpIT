import tkinter as tk
from tkinter import ttk, messagebox
import csv
import logging
from pathlib import Path


class ServiceManager:
    """
    Class to manage and display services in a GUI window
    Allows starting, stopping, and restarting services on a remote machine using PsExec
    """

    def __init__(self, csv_filename, psexec_manager, current_ip, current_hostname, psexec_path, log_path):
        """
        Initialize the ServiceManager

        Args:
            csv_filename (str or Path): Path to the CSV file containing service list
            psexec_manager (PsExecManager): Instance of PsExecManager to execute commands
            current_ip (str): IP address of the remote machine
            current_hostname (str): Hostname of the remote machine
            psexec_path (str): Path to PsExec64.exe
            log_path (str): Path to the log directory
        """
        self.csv_filename = Path(csv_filename)
        self.psexec_manager = psexec_manager
        self.current_ip = current_ip
        self.current_hostname = current_hostname
        self.psexec_path = psexec_path
        self.log_path = log_path

        # Dictionary to store widget references for each service
        # Key: service_id, Value: dict with 'status_label', 'stop_btn', 'run_btn', 'restart_btn'
        self.service_widgets = {}

        # State color mapping for visual feedback
        self.state_colors = {
            'RUNNING': '#4CAF50',      # Green
            'STOPPED': '#F44336',      # Red
            'START_PENDING': '#FF9800', # Orange
            'STOP_PENDING': '#FF9800',  # Orange
            'CONTINUE_PENDING': '#FF9800', # Orange
            'PAUSE_PENDING': '#FF9800', # Orange
            'PAUSED': '#FFC107'        # Amber
        }

        # Create the main window
        self.window = tk.Toplevel()
        self.window.title(f"Service Manager - {self.current_hostname} ({self.current_ip})")
        self.window.geometry("750x600")

        # Create the interface
        self._create_widgets()

        # Load services from CSV
        self._load_services()

    def _create_widgets(self):
        """
        Create all GUI widgets for the service manager window
        """
        # Title label
        title_label = ttk.Label(
            self.window,
            text=f"Services on {self.current_hostname}",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=10)

        # Create a frame for the scrollable list
        list_frame = ttk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        
        # Create a frame inside the canvas to hold the service list
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure the scrollable region
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create window in canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add mouse wheel scrolling support
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Create bottom frame for buttons
        bottom_frame = ttk.Frame(self.window)
        bottom_frame.pack(pady=10)

        # Refresh button to reload the service list
        refresh_btn = ttk.Button(
            bottom_frame,
            text="Refresh List",
            command=self._refresh_service_list
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Close button
        close_btn = ttk.Button(
            bottom_frame,
            text="Close",
            command=self.window.destroy
        )
        close_btn.pack(side=tk.LEFT, padx=5)

    def _on_mousewheel(self, event):
        """
        Handle mouse wheel scrolling

        Args:
            event: Mouse wheel event
        """
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _load_services(self):
        """
        Load services from CSV file and display them in the GUI
        """
        # Check if CSV file exists
        if not self.csv_filename.exists():
            messagebox.showerror("Error", f"CSV file not found: {self.csv_filename}")
            logging.error(f"CSV file not found: {self.csv_filename}")
            return

        try:
            # Read the CSV file (delimiter is semicolon)
            with open(self.csv_filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')

                # Convert to a list and sort by 'name' (ascending order)
                services = list(reader)
                services_sorted = sorted(services, key=lambda x: x.get('name', '').strip().lower())

                # Counter for row positioning
                row_index = 0

                # Iterate through each service in the CSV
                for row in services_sorted:
                    service_id = row.get('id', '').strip()
                    service_name = row.get('name', '').strip()
                    service_state = row.get('etat', '').strip()

                    # Skip empty entries
                    if not service_id:
                        continue

                    # Create a frame for each service row
                    service_frame = ttk.Frame(self.scrollable_frame)
                    service_frame.grid(row=row_index, column=0, sticky="ew", pady=2, padx=5)

                    # Configure column weights for proper expansion
                    service_frame.columnconfigure(0, weight=1)  # ID column
                    service_frame.columnconfigure(1, weight=2)  # Name column (wider)
                    service_frame.columnconfigure(2, weight=1)  # Status column
                    service_frame.columnconfigure(3, weight=1)  # Buttons column

                    # Create ID label
                    id_label = ttk.Label(
                        service_frame,
                        text=service_id,
                        font=('Arial', 9),
                        width=12,
                        anchor='w'
                    )
                    id_label.grid(row=0, column=0, sticky="w", padx=2)

                    # Create Name label
                    name_label = ttk.Label(
                        service_frame,
                        text=service_name,
                        font=('Arial', 9),
                        width=40,
                        anchor='w'
                    )
                    name_label.grid(row=0, column=1, sticky="w", padx=2)

                    # Create status label with colored background
                    status_label = tk.Label(
                        service_frame,
                        text=service_state,
                        font=('Arial', 9, 'bold'),
                        bg=self.state_colors.get(service_state, '#9E9E9E'),
                        fg="white",
                        width=10,
                        relief=tk.RAISED
                    )
                    status_label.grid(row=0, column=2, padx=5)

                    # Create Stop button
                    stop_btn = tk.Button(
                        service_frame,
                        text="Stop",
                        bg="#F44336",  # Red color
                        fg="white",
                        width=6,
                        command=lambda sid=service_id: self._stop_service(sid)
                    )
                    stop_btn.grid(row=0, column=3, padx=1)

                    # Create Run button
                    run_btn = tk.Button(
                        service_frame,
                        text="Run",
                        bg="#4CAF50",  # Green color
                        fg="white",
                        width=6,
                        command=lambda sid=service_id: self._start_service(sid)
                    )
                    run_btn.grid(row=0, column=4, padx=1)

                    # Create Restart button
                    restart_btn = tk.Button(
                        service_frame,
                        text="Restart",
                        bg="#2196F3",  # Blue color
                        fg="white",
                        width=7,
                        command=lambda sid=service_id: self._restart_service(sid)
                    )
                    restart_btn.grid(row=0, column=5, padx=2)

                    # Store widget references for later updates
                    self.service_widgets[service_id] = {
                        'status_label': status_label,
                        'stop_btn': stop_btn,
                        'run_btn': run_btn,
                        'restart_btn': restart_btn
                    }

                    row_index += 1

                logging.info(f"Loaded {row_index} services from {self.csv_filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Error reading CSV file: {e}")
            logging.error(f"Error reading CSV file {self.csv_filename}: {e}")

    def _update_service_status(self, service_id):
        """
        Update the status display for a specific service

        Args:
            service_id (str): ID of the service to update
        """
        try:
            # Get the current status from PsExec
            status = self.psexec_manager.get_service_status(service_id)
            
            # Map status code to text
            if status == 1:
                status_text = "RUNNING"
            else:
                status_text = "STOPPED"
            
            # Update the status label
            widgets = self.service_widgets.get(service_id)
            if widgets:
                status_label = widgets['status_label']
                status_label.config(
                    text=status_text,
                    bg=self.state_colors.get(status_text, '#9E9E9E')
                )
            
            logging.info(f"Service status updated: {service_id} is {status_text}")

        except Exception as e:
            logging.error(f"Error updating status for service {service_id}: {e}")

    def _stop_service(self, service_id):
        """
        Stop a service on the remote machine

        Args:
            service_id (str): ID of the service to stop
        """
        # Confirm action with user
        response = messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to stop service '{service_id}'?"
        )

        if not response:
            return

        try:
            # Call the stop_service method from PsExecManager
            result = self.psexec_manager.stop_service(service_id)

            if result:
                # Success: update the status
                self._update_service_status(service_id)
                messagebox.showinfo("Success", f"Service '{service_id}' stopped successfully!")
                logging.info(f"Service '{service_id}' stopped on {self.current_hostname}")
            else:
                # Failure: show error message
                messagebox.showerror(
                    "Error",
                    f"Failed to stop service '{service_id}'"
                )
                logging.error(f"Failed to stop service '{service_id}' on {self.current_hostname}")

        except Exception as e:
            messagebox.showerror("Error", f"Error stopping service: {e}")
            logging.error(f"Error stopping service '{service_id}': {e}")

    def _start_service(self, service_id):
        """
        Start a service on the remote machine

        Args:
            service_id (str): ID of the service to start
        """
        # Confirm action with user
        response = messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to start service '{service_id}'?"
        )

        if not response:
            return

        try:
            # Call the start_service method from PsExecManager
            result = self.psexec_manager.start_service(service_id)

            if result:
                # Success: update the status
                self._update_service_status(service_id)
                messagebox.showinfo("Success", f"Service '{service_id}' started successfully!")
                logging.info(f"Service '{service_id}' started on {self.current_hostname}")
            else:
                # Failure: show error message
                messagebox.showerror(
                    "Error",
                    f"Failed to start service '{service_id}'"
                )
                logging.error(f"Failed to start service '{service_id}' on {self.current_hostname}")

        except Exception as e:
            messagebox.showerror("Error", f"Error starting service: {e}")
            logging.error(f"Error starting service '{service_id}': {e}")

    def _restart_service(self, service_id):
        """
        Restart a service on the remote machine

        Args:
            service_id (str): ID of the service to restart
        """
        # Confirm action with user
        response = messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to restart service '{service_id}'?"
        )

        if not response:
            return

        try:
            # Call the restart_service method from PsExecManager
            result = self.psexec_manager.restart_service(service_id)

            if result:
                # Success: update the status
                self._update_service_status(service_id)
                messagebox.showinfo("Success", f"Service '{service_id}' restarted successfully!")
                logging.info(f"Service '{service_id}' restarted on {self.current_hostname}")
            else:
                # Failure: show error message
                messagebox.showerror(
                    "Error",
                    f"Failed to restart service '{service_id}'"
                )
                logging.error(f"Failed to restart service '{service_id}' on {self.current_hostname}")

        except Exception as e:
            messagebox.showerror("Error", f"Error restarting service: {e}")
            logging.error(f"Error restarting service '{service_id}': {e}")

    def _refresh_service_list(self):
        """
        Refresh the service list by regenerating the CSV and reloading the display
        """
        try:
            # Clear existing widgets in scrollable frame
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            # Clear widget references
            self.service_widgets.clear()

            # Regenerate the service list CSV
            self.psexec_manager.get_services_to_csv()

            # Reload services from the updated CSV
            self._load_services()

            messagebox.showinfo("Success", "Service list refreshed successfully!")
            logging.info(f"Service list refreshed for {self.current_hostname}")

        except Exception as e:
            messagebox.showerror("Error", f"Error refreshing service list: {e}")
            logging.error(f"Error refreshing service list for {self.current_hostname}: {e}")

    def show(self):
        """
        Show the service manager window
        """
        self.window.mainloop()
