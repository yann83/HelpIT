import tkinter as tk
from tkinter import ttk, messagebox
import csv
import logging
from pathlib import Path


class ProcessManager:
    """
    Class to manage and display processes in a GUI window
    Allows killing processes on a remote machine using PsExec
    """

    def __init__(self, csv_filename, psexec_manager, current_ip, current_hostname, psexec_path, log_path):
        """
        Initialize the ProcessManager

        Args:
            csv_filename (str or Path): Path to the CSV file containing process list
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

        # Dictionary to store button references for each process
        # Key: process name, Value: button widget
        self.process_buttons = {}

        # Create the main window
        self.window = tk.Toplevel()
        self.window.title(f"Process Manager - {self.current_hostname} ({self.current_ip})")
        self.window.geometry("600x500")

        # Create the interface
        self._create_widgets()

        # Load processes from CSV
        self._load_processes()

    def _create_widgets(self):
        """
        Create all GUI widgets for the process manager window
        """
        # Title label
        title_label = ttk.Label(
            self.window,
            text=f"Processes on {self.current_hostname}",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=10)

        # Create a frame for the scrollable list
        list_frame = ttk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)

        # Create a frame inside the canvas to hold the process list
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

        # Refresh button to reload the process list
        refresh_btn = ttk.Button(
            bottom_frame,
            text="Refresh List",
            command=self._refresh_process_list
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

    def _load_processes(self):
        """
        Load processes from CSV file and display them in the GUI
        """
        # Check if CSV file exists
        if not self.csv_filename.exists():
            messagebox.showerror("Error", f"CSV file not found: {self.csv_filename}")
            logging.error(f"CSV file not found: {self.csv_filename}")
            return

        try:
            # Read the CSV file
            with open(self.csv_filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                # Lire toutes les lignes dans une liste
                processes = list(reader)

                # Trier la liste par la colonne 'name' (ordre ascendant)
                processes.sort(key=lambda row: row.get('name', '').strip().lower())

                # Counter for row positioning
                row_index = 0

                # Iterate through each process in the CSV
                for row in processes:
                    process_name = row.get('name', '').strip()

                    # Skip empty names
                    if not process_name:
                        continue

                    # Create a frame for each process row
                    process_frame = ttk.Frame(self.scrollable_frame)
                    process_frame.grid(row=row_index, column=0, sticky="ew", pady=2, padx=5)

                    # Configure column weight for proper expansion
                    process_frame.columnconfigure(1, weight=1)

                    # Create kill button (initially green)
                    kill_btn = tk.Button(
                        process_frame,
                        text="Kill",
                        bg="#4CAF50",  # Green color
                        fg="white",
                        width=8,
                        command=lambda pname=process_name: self._kill_process(pname)
                    )
                    kill_btn.grid(row=0, column=0, padx=5)

                    # Store button reference for later updates
                    self.process_buttons[process_name] = kill_btn

                    # Create label with process name
                    process_label = ttk.Label(
                        process_frame,
                        text=process_name,
                        font=('Arial', 10)
                    )
                    process_label.grid(row=0, column=1, sticky="w", padx=5)

                    row_index += 1

                logging.info(f"Loaded {row_index} processes from {self.csv_filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Error reading CSV file: {e}")
            logging.error(f"Error reading CSV file {self.csv_filename}: {e}")

    def _kill_process(self, process_name):
        """
        Kill a process on the remote machine

        Args:
            process_name (str): Name of the process to kill
        """
        # Confirm action with user
        response = messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to kill process '{process_name}'?"
        )

        if not response:
            return

        try:
            # Call the kill_process method from PsExecManager
            result = self.psexec_manager.kill_process(process_name)

            # Get the button for this process
            button = self.process_buttons.get(process_name)

            if result == 1:
                # Success: change button to red and disable it
                if button:
                    button.config(bg="#F44336", state="disabled")  # Red color

                messagebox.showinfo("Success", f"Process '{process_name}' killed successfully!")
                logging.info(f"Process '{process_name}' killed on {self.current_hostname}")

            else:
                # Failure: show error message
                messagebox.showerror(
                    "Error",
                    f"Failed to kill process '{process_name}'"
                )
                logging.error(f"Failed to kill process '{process_name}' on {self.current_hostname}")

        except Exception as e:
            messagebox.showerror("Error", f"Error killing process: {e}")
            logging.error(f"Error killing process '{process_name}': {e}")

    def _refresh_process_list(self):
        """
        Refresh the process list by regenerating the CSV and reloading the display
        """
        try:
            # Clear existing widgets in scrollable frame
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            # Clear button references
            self.process_buttons.clear()

            # Regenerate the process list CSV
            self.psexec_manager.get_processes_to_csv()

            # Reload processes from the updated CSV
            self._load_processes()

            messagebox.showinfo("Success", "Process list refreshed successfully!")
            logging.info(f"Process list refreshed for {self.current_hostname}")

        except Exception as e:
            messagebox.showerror("Error", f"Error refreshing process list: {e}")
            logging.error(f"Error refreshing process list for {self.current_hostname}: {e}")

    def show(self):
        """
        Show the process manager window
        """
        self.window.mainloop()
