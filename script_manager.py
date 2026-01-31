# script_manager.py
"""
Script Manager GUI for HelpIT application.

This module provides a graphical interface to browse and execute scripts
on remote machines using PsExec.

Features:
    - List available scripts (.ps1, .bat, .cmd) from a specified directory
    - Select and launch scripts on remote machines
    - Visual feedback for script execution status
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
from constants import *


class ScriptManager:
    """
    A GUI window to manage and execute scripts on remote machines.

    This class creates a Toplevel window that displays available scripts
    from a specified directory and allows the user to execute them on
    a remote machine via PsExec.

    Attributes:
        scripts_path (Path): Directory containing the scripts.
        psexec_manager (PsExecManager): Instance to execute remote commands.
        current_ip (str): IP address of the target machine.
        current_hostname (str): Hostname of the target machine.
        window (tk.Toplevel): The main window for the script manager.
        script_listbox (tk.Listbox): Widget displaying available scripts.
        launch_button (tk.Button): Button to execute the selected script.
    """

    # Supported script extensions
    SUPPORTED_EXTENSIONS = ['.ps1', '.bat', '.cmd']

    def __init__(self, scripts_path, psexec_manager, current_ip, current_hostname):
        """
        Initialize the ScriptManager window.

        Args:
            scripts_path (str or Path): Path to the directory containing scripts.
            psexec_manager (PsExecManager): Instance of PsExecManager for remote execution.
            current_ip (str): IP address of the remote machine.
            current_hostname (str): Hostname of the remote machine.
        """
        self.scripts_path = Path(scripts_path)
        self.psexec_manager = psexec_manager
        self.current_ip = current_ip
        self.current_hostname = current_hostname

        # List to store script file paths
        self.script_files = []

        # Create the main window
        self.window = tk.Toplevel()
        self.window.title(f"Script Manager - {self.current_hostname} ({self.current_ip})")
        self.window.geometry(SCRIPT_MANAGER_SIZE)
        self.window.resizable(True, True)

        # Keep window on top
        self.window.attributes('-topmost', True)

        # Create the interface
        self._create_widgets()

        # Load scripts from the directory
        self._load_scripts()

        # Update the launch button state based on selection
        self._update_launch_button_state()

    def _create_widgets(self):
        """
        Create all GUI widgets for the script manager window.

        This method builds the complete user interface including:
        - Title label
        - Scrollable list of scripts
        - Launch and Close buttons
        """
        # Main frame with padding
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        title_label = ttk.Label(
            main_frame,
            text=f"Available Scripts",
            font=('Arial', 12, 'bold')
        )
        title_label.pack(pady=(0, 10))

        # Info label showing the scripts directory
        info_label = ttk.Label(
            main_frame,
            text=f"Directory: {self.scripts_path}",
            font=('Arial', 8),
            foreground='gray'
        )
        info_label.pack(pady=(0, 5))

        # Frame for the listbox and scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Scrollbar for the listbox
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox to display scripts
        self.script_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            font=('Arial', 10),
            height=10
        )
        self.script_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbar
        scrollbar.config(command=self.script_listbox.yview)

        # Bind selection event to update button state
        self.script_listbox.bind('<<ListboxSelect>>', self._on_selection_change)

        # Bind double-click to launch script
        self.script_listbox.bind('<Double-1>', lambda e: self._launch_script())

        # Frame for buttons at the bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Launch button (initially disabled)
        self.launch_button = tk.Button(
            button_frame,
            text="Launch",
            bg="#4CAF50",  # Green color
            fg="white",
            width=12,
            font=('Arial', 10, 'bold'),
            command=self._launch_script,
            state=tk.DISABLED  # Disabled by default
        )
        self.launch_button.pack(side=tk.LEFT, padx=5)

        # Refresh button
        refresh_button = ttk.Button(
            button_frame,
            text="Refresh",
            width=10,
            command=self._refresh_scripts
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        # Close button
        close_button = ttk.Button(
            button_frame,
            text="Close",
            width=10,
            command=self.close
        )
        close_button.pack(side=tk.RIGHT, padx=5)

        # Status label at the bottom
        self.status_var = tk.StringVar(value="Select a script to launch")
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Arial', 9),
            foreground='gray'
        )
        status_label.pack(pady=(5, 0))

    def _load_scripts(self):
        """
        Load script files from the scripts directory.

        This method scans the scripts_path directory for files with
        supported extensions (.ps1, .bat, .cmd) and populates the listbox.
        """
        # Clear the current list
        self.script_listbox.delete(0, tk.END)
        self.script_files.clear()

        # Check if the scripts directory exists
        if not self.scripts_path.exists():
            logging.warning(f"Scripts directory does not exist: {self.scripts_path}")
            self.status_var.set("Scripts directory not found")
            return

        # Find all script files with supported extensions
        try:
            for extension in self.SUPPORTED_EXTENSIONS:
                # Use glob to find files with the current extension
                for script_file in self.scripts_path.glob(f"*{extension}"):
                    if script_file.is_file():
                        self.script_files.append(script_file)

            # Sort scripts alphabetically by name
            self.script_files.sort(key=lambda x: x.name.lower())

            # Populate the listbox
            for script_file in self.script_files:
                # Display the filename with its extension
                self.script_listbox.insert(tk.END, script_file.name)

            # Update status based on number of scripts found
            script_count = len(self.script_files)
            if script_count == 0:
                self.status_var.set("No scripts found in directory")
                logging.info(f"No scripts found in {self.scripts_path}")
            else:
                self.status_var.set(f"{script_count} script(s) available")
                logging.info(f"Loaded {script_count} scripts from {self.scripts_path}")

        except Exception as e:
            logging.error(f"Error loading scripts: {e}")
            self.status_var.set(f"Error loading scripts")
            messagebox.showerror("Error", f"Failed to load scripts: {e}")

    def _on_selection_change(self, event=None):
        """
        Handle listbox selection change event.

        Args:
            event: The selection change event (optional).
        """
        self._update_launch_button_state()

    def _update_launch_button_state(self):
        """
        Update the Launch button state based on current selection.

        The button is enabled only when a script is selected in the listbox.
        """
        # Get current selection
        selection = self.script_listbox.curselection()

        if selection and len(self.script_files) > 0:
            # A script is selected - enable the button
            self.launch_button.config(state=tk.NORMAL)
        else:
            # No selection - disable the button
            self.launch_button.config(state=tk.DISABLED)

    def _launch_script(self):
        """
        Launch the selected script on the remote machine.

        This method gets the selected script from the listbox and uses
        PsExecManager to execute it on the remote machine.
        """
        # Get the current selection
        selection = self.script_listbox.curselection()

        if not selection:
            messagebox.showwarning("Warning", "Please select a script to launch.")
            return

        # Get the selected script index
        selected_index = selection[0]

        # Get the corresponding script file path
        script_file = self.script_files[selected_index]

        # Confirm execution with the user
        confirm = messagebox.askyesno(
            "Confirm Execution",
            f"Are you sure you want to execute:\n\n"
            f"{script_file.name}\n\n"
            f"on {self.current_hostname} ({self.current_ip})?"
        )

        if not confirm:
            return

        # Update status to show execution in progress
        self.status_var.set(f"Executing {script_file.name}...")
        self.launch_button.config(state=tk.DISABLED)
        self.window.update()

        try:
            # Execute the script using PsExecManager
            result = self.psexec_manager.run_script(script_file)

            if result:
                # Script executed successfully
                self.status_var.set(f"Script executed successfully")
                messagebox.showinfo(
                    "Success",
                    f"Script '{script_file.name}' executed successfully on {self.current_hostname}."
                )
                logging.info(f"Script {script_file.name} executed on {self.current_hostname}")
            else:
                # Script execution failed
                self.status_var.set(f"Script execution failed")
                messagebox.showerror(
                    "Error",
                    f"Failed to execute script '{script_file.name}' on {self.current_hostname}."
                )
                logging.error(f"Failed to execute {script_file.name} on {self.current_hostname}")

        except FileNotFoundError as e:
            self.status_var.set("Script file not found")
            messagebox.showerror("Error", f"Script file not found: {e}")
            logging.error(f"Script file not found: {e}")

        except ValueError as e:
            self.status_var.set("Unsupported script type")
            messagebox.showerror("Error", f"Unsupported script type: {e}")
            logging.error(f"Unsupported script type: {e}")

        except Exception as e:
            self.status_var.set("Error during execution")
            messagebox.showerror("Error", f"Error executing script: {e}")
            logging.error(f"Error executing script {script_file.name}: {e}")

        finally:
            # Re-enable the launch button
            self._update_launch_button_state()

    def _refresh_scripts(self):
        """
        Refresh the list of available scripts.

        This method reloads the scripts from the directory and updates
        the listbox display.
        """
        self._load_scripts()
        self._update_launch_button_state()
        logging.info("Script list refreshed")

    def close(self):
        """
        Close the script manager window.
        """
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            logging.info("ScriptManager window closed")

    def show(self):
        """
        Show the script manager window and start its event loop.

        Note: As a Toplevel window, it shares the mainloop with the parent.
        """
        self.window.focus_set()
