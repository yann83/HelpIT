# test_double_windows.py
"""
Dual-pane file explorer for Windows with network file transfer capabilities.

This application provides a side-by-side file browser interface for copying
files between a local machine and a remote Windows share (via UNC paths).

Features:
    - Dual-pane navigation (local and network)
    - Multi-file selection and batch copy
    - Progress bar for large file transfers
    - Threaded operations to keep UI responsive
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
from pathlib import Path
import threading
from datetime import datetime


class ProgressWindow:
    """
    A modal progress window for displaying file copy operations.

    This window shows the current file being copied, overall progress
    across multiple files, and provides a cancel button.

    Attributes:
        parent: The parent tkinter window.
        window: The Toplevel window instance.
        cancelled: Flag indicating if the operation was cancelled.
        current_file_var: StringVar for current filename display.
        file_progress_var: StringVar for file count progress.
        progress_bar: The ttk.Progressbar widget.
    """

    def __init__(self, parent, title="Copy in progress..."):
        """
        Initialize the progress window.

        Args:
            parent: The parent tkinter window.
            title: The window title. Defaults to "Copy in progress...".
        """
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("450x180")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        # Flag to track cancellation
        self.cancelled = False

        self._setup_ui()

        # Center the window on parent
        self._center_on_parent()

    def _setup_ui(self):
        """Build the progress window UI components."""
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Current file label
        self.current_file_var = tk.StringVar(value="Preparing...")
        ttk.Label(
            main_frame,
            textvariable=self.current_file_var,
            wraplength=400
        ).pack(anchor=tk.W, pady=(0, 5))

        # File count progress (e.g., "File 2/5")
        self.file_progress_var = tk.StringVar(value="")
        ttk.Label(
            main_frame,
            textvariable=self.file_progress_var
        ).pack(anchor=tk.W, pady=(0, 5))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            main_frame,
            orient=tk.HORIZONTAL,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=10)

        # Percentage label
        self.percent_var = tk.StringVar(value="0%")
        ttk.Label(
            main_frame,
            textvariable=self.percent_var
        ).pack()

        # Cancel button
        ttk.Button(
            main_frame,
            text="Cancel",
            command=self._on_cancel
        ).pack(pady=(10, 0))

    def _center_on_parent(self):
        """Center the progress window on its parent window."""
        self.window.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        self.window.geometry(f"+{x}+{y}")

    def _on_cancel(self):
        """Handle the cancel button click."""
        self.cancelled = True
        self.current_file_var.set("Cancelling...")

    def update_progress(self, current_bytes, total_bytes, current_file,
                        file_index, total_files):
        """
        Update the progress display.

        Args:
            current_bytes: Number of bytes copied so far for current file.
            total_bytes: Total bytes of current file.
            current_file: Name of the file currently being copied.
            file_index: Index of current file (1-based).
            total_files: Total number of files to copy.
        """
        # Calculate percentage
        if total_bytes > 0:
            percent = (current_bytes / total_bytes) * 100
        else:
            percent = 100

        # Update UI elements
        self.current_file_var.set(f"Copying: {current_file}")
        self.file_progress_var.set(f"File {file_index}/{total_files}")
        self.progress_bar['value'] = percent
        self.percent_var.set(f"{percent:.1f}%")

        # Force UI update
        self.window.update()

    def close(self):
        """Close and destroy the progress window."""
        self.window.grab_release()
        self.window.destroy()


class DualFileExplorer:
    """
    A dual-pane file explorer for local and network file management.

    This class creates a GUI application with two side-by-side file browsers,
    allowing users to navigate directories and copy files between local
    storage and network shares.

    Attributes:
        root: The main tkinter window.
        left_path: Current path displayed in the left (local) pane.
        right_path: Current path displayed in the right (network) pane.
        left_tree: Treeview widget for the left pane.
        right_tree: Treeview widget for the right pane.
    """

    # Buffer size for file copy operations (64 KB)
    COPY_BUFFER_SIZE = 64 * 1024

    def __init__(self, root):
        """
        Initialize the dual file explorer.

        Args:
            root: The main tkinter window instance.
        """
        self.root = root
        self.root.title("File Manager - Dual Pane")
        self.root.geometry("1200x700")

        # Initial paths
        self.left_path = r"C:\temp"
        self.right_path = r"\\cinema\VIDEOS"  # Adjust as needed

        self._setup_ui()
        self.refresh_both()

    def _setup_ui(self):
        """Build the main application UI."""
        self._create_toolbar()
        self._create_main_panels()
        self._create_status_bar()

    def _create_toolbar(self):
        """Create the top toolbar with connection controls."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Label(toolbar, text="Remote IP:").pack(side=tk.LEFT, padx=5)

        self.ip_entry = ttk.Entry(toolbar, width=15)
        self.ip_entry.insert(0, "192.168.1.50")
        self.ip_entry.pack(side=tk.LEFT)

        ttk.Button(
            toolbar,
            text="Connect",
            command=self._connect_remote
        ).pack(side=tk.LEFT, padx=5)

        # Help label for multi-selection
        ttk.Label(
            toolbar,
            text="(Ctrl+Click or Shift+Click for multi-selection)",
            foreground="gray"
        ).pack(side=tk.RIGHT, padx=10)

    def _create_main_panels(self):
        """Create the main three-panel layout (left, center, right)."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel (Local)
        self._create_left_panel(main_frame)

        # Center panel (Action buttons)
        self._create_center_panel(main_frame)

        # Right panel (Network)
        self._create_right_panel(main_frame)

    def _create_left_panel(self, parent):
        """
        Create the left (local) file browser panel.

        Args:
            parent: The parent frame to contain this panel.
        """
        left_frame = ttk.LabelFrame(parent, text="📁 Local", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Address bar
        self.left_path_var = tk.StringVar(value=self.left_path)
        left_addr = ttk.Entry(left_frame, textvariable=self.left_path_var)
        left_addr.pack(fill=tk.X, pady=(0, 5))
        left_addr.bind('<Return>', lambda e: self._refresh_left())

        # Treeview with scrollbar
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # IMPORTANT: selectmode='extended' enables multi-selection
        self.left_tree = ttk.Treeview(
            tree_frame,
            columns=('size', 'modified'),
            yscrollcommand=scrollbar.set,
            selectmode='extended'  # Enable Ctrl+Click and Shift+Click
        )
        self.left_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.left_tree.yview)

        # Configure columns
        self.left_tree.heading('#0', text='Name')
        self.left_tree.heading('size', text='Size')
        self.left_tree.heading('modified', text='Modified')
        self.left_tree.column('size', width=100)
        self.left_tree.column('modified', width=150)

        # Double-click to navigate
        self.left_tree.bind(
            '<Double-1>',
            lambda e: self._on_double_click('left')
        )

    def _create_center_panel(self, parent):
        """
        Create the center panel with action buttons.

        Args:
            parent: The parent frame to contain this panel.
        """
        middle_frame = ttk.Frame(parent, width=100)
        middle_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        middle_frame.pack_propagate(False)

        ttk.Label(
            middle_frame,
            text="Actions",
            font=('Arial', 10, 'bold')
        ).pack(pady=10)

        ttk.Button(
            middle_frame,
            text="→ Copy →",
            command=self._copy_left_to_right,
            width=14
        ).pack(pady=5)

        ttk.Button(
            middle_frame,
            text="← Copy ←",
            command=self._copy_right_to_left,
            width=14
        ).pack(pady=5)

        ttk.Separator(middle_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Button(
            middle_frame,
            text="🗑️ Delete",
            command=self._delete_selected,
            width=14
        ).pack(pady=5)

        ttk.Button(
            middle_frame,
            text="🔄 Refresh",
            command=self.refresh_both,
            width=14
        ).pack(pady=5)

    def _create_right_panel(self, parent):
        """
        Create the right (network) file browser panel.

        Args:
            parent: The parent frame to contain this panel.
        """
        right_frame = ttk.LabelFrame(parent, text="🌐 Network", padding=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Address bar
        self.right_path_var = tk.StringVar(value=self.right_path)
        right_addr = ttk.Entry(right_frame, textvariable=self.right_path_var)
        right_addr.pack(fill=tk.X, pady=(0, 5))
        right_addr.bind('<Return>', lambda e: self._refresh_right())

        # Treeview with scrollbar
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # IMPORTANT: selectmode='extended' enables multi-selection
        self.right_tree = ttk.Treeview(
            tree_frame,
            columns=('size', 'modified'),
            yscrollcommand=scrollbar.set,
            selectmode='extended'  # Enable Ctrl+Click and Shift+Click
        )
        self.right_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.right_tree.yview)

        # Configure columns
        self.right_tree.heading('#0', text='Name')
        self.right_tree.heading('size', text='Size')
        self.right_tree.heading('modified', text='Modified')
        self.right_tree.column('size', width=100)
        self.right_tree.column('modified', width=150)

        # Double-click to navigate
        self.right_tree.bind(
            '<Double-1>',
            lambda e: self._on_double_click('right')
        )

    def _create_status_bar(self):
        """Create the bottom status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _connect_remote(self):
        """Connect to a remote network share using the entered IP."""
        ip = self.ip_entry.get()
        self.right_path = f"\\\\{ip}\\c$"
        self.right_path_var.set(self.right_path)
        self._refresh_right()

    def _list_directory(self, path):
        """
        List the contents of a directory.

        Args:
            path: The directory path to list.

        Returns:
            A list of dictionaries containing file/folder information.
            Each dict has keys: name, path, is_dir, size, modified.
        """
        try:
            items = []

            # Add ".." entry for parent navigation (if not at root)
            if path != os.path.dirname(path):
                items.append({
                    'name': '..',
                    'path': os.path.dirname(path),
                    'is_dir': True,
                    'size': '',
                    'modified': ''
                })

            # List files and folders
            for entry in os.scandir(path):
                try:
                    stat_info = entry.stat()
                    items.append({
                        'name': entry.name,
                        'path': entry.path,
                        'is_dir': entry.is_dir(),
                        'size': (
                            self._format_size(stat_info.st_size)
                            if not entry.is_dir()
                            else '<DIR>'
                        ),
                        'modified': self._format_time(stat_info.st_mtime)
                    })
                except (PermissionError, OSError):
                    # Skip inaccessible files
                    continue

            # Sort: directories first, then by name
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            return items

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Unable to read {path}\n{str(e)}"
            )
            return []

    def _populate_tree(self, tree, items):
        """
        Fill a Treeview widget with file/folder items.

        Args:
            tree: The Treeview widget to populate.
            items: List of item dictionaries from _list_directory().
        """
        # Clear the tree
        tree.delete(*tree.get_children())

        # Add each item
        for item in items:
            icon = '📁' if item['is_dir'] else '📄'

            tree.insert(
                '',
                tk.END,
                text=f"{icon} {item['name']}",
                values=(item['size'], item['modified']),
                tags=(item['path'], 'dir' if item['is_dir'] else 'file')
            )

    def _refresh_left(self):
        """Refresh the left (local) panel."""
        path = self.left_path_var.get()
        if os.path.exists(path):
            self.left_path = path
            items = self._list_directory(path)
            self._populate_tree(self.left_tree, items)
            self.status_var.set(f"Local: {len(items)} items")

    def _refresh_right(self):
        """Refresh the right (network) panel."""
        path = self.right_path_var.get()
        if os.path.exists(path):
            self.right_path = path
            items = self._list_directory(path)
            self._populate_tree(self.right_tree, items)
            self.status_var.set(f"Network: {len(items)} items")

    def refresh_both(self):
        """Refresh both panels."""
        self._refresh_left()
        self._refresh_right()

    def _on_double_click(self, side):
        """
        Handle double-click for directory navigation.

        Args:
            side: 'left' or 'right' indicating which panel was clicked.
        """
        tree = self.left_tree if side == 'left' else self.right_tree
        selection = tree.selection()

        if not selection:
            return

        # Only navigate using the first selected item
        item = selection[0]
        tags = tree.item(item, 'tags')

        if len(tags) > 0:
            path = tags[0]
            is_dir = 'dir' in tags

            if is_dir:
                if side == 'left':
                    self.left_path = path
                    self.left_path_var.set(path)
                    self._refresh_left()
                else:
                    self.right_path = path
                    self.right_path_var.set(path)
                    self._refresh_right()

    def _get_selected_paths(self, tree):
        """
        Get paths of all selected items in a Treeview.

        Args:
            tree: The Treeview widget to get selections from.

        Returns:
            A list of tuples (path, is_dir) for each selected item.
        """
        selection = tree.selection()
        if not selection:
            return []

        paths = []
        for item in selection:
            tags = tree.item(item, 'tags')
            if tags:
                path = tags[0]
                is_dir = 'dir' in tags
                # Exclude ".." navigation entry
                if os.path.basename(path) != '..':
                    paths.append((path, is_dir))

        return paths

    def _copy_left_to_right(self):
        """Copy selected files from left (local) to right (network) panel."""
        selected = self._get_selected_paths(self.left_tree)

        if not selected:
            messagebox.showwarning(
                "Warning",
                "Select one or more files on the left"
            )
            return

        # Filter out directories (folder copy not implemented yet)
        files_to_copy = [(path, is_dir) for path, is_dir in selected
                         if not is_dir]
        dirs_skipped = len(selected) - len(files_to_copy)

        if dirs_skipped > 0:
            messagebox.showinfo(
                "Info",
                f"{dirs_skipped} folder(s) skipped.\n"
                "Folder copy is not yet implemented."
            )

        if not files_to_copy:
            return

        # Prepare source/destination pairs
        copy_pairs = []
        for src_path, _ in files_to_copy:
            dst_path = os.path.join(self.right_path, os.path.basename(src_path))
            copy_pairs.append((src_path, dst_path))

        self._copy_files_with_progress(copy_pairs, 'right')

    def _copy_right_to_left(self):
        """Copy selected files from right (network) to left (local) panel."""
        selected = self._get_selected_paths(self.right_tree)

        if not selected:
            messagebox.showwarning(
                "Warning",
                "Select one or more files on the right"
            )
            return

        # Filter out directories
        files_to_copy = [(path, is_dir) for path, is_dir in selected
                         if not is_dir]
        dirs_skipped = len(selected) - len(files_to_copy)

        if dirs_skipped > 0:
            messagebox.showinfo(
                "Info",
                f"{dirs_skipped} folder(s) skipped.\n"
                "Folder copy is not yet implemented."
            )

        if not files_to_copy:
            return

        # Prepare source/destination pairs
        copy_pairs = []
        for src_path, _ in files_to_copy:
            dst_path = os.path.join(self.left_path, os.path.basename(src_path))
            copy_pairs.append((src_path, dst_path))

        self._copy_files_with_progress(copy_pairs, 'left')

    def _copy_files_with_progress(self, copy_pairs, refresh_side):
        """
        Copy multiple files with a progress dialog.

        This method copies files in a background thread while displaying
        a progress window. Each file's progress is tracked and displayed.

        Args:
            copy_pairs: List of (source_path, destination_path) tuples.
            refresh_side: 'left' or 'right' - which panel to refresh after copy.
        """
        # Create progress window
        progress = ProgressWindow(self.root)
        total_files = len(copy_pairs)

        def do_copy():
            """Background thread function to perform the copy."""
            copied_count = 0
            failed_files = []

            for index, (src, dst) in enumerate(copy_pairs, start=1):
                # Check for cancellation
                if progress.cancelled:
                    break

                filename = os.path.basename(src)

                try:
                    # Get file size
                    file_size = os.path.getsize(src)

                    # Copy with progress tracking
                    self._copy_single_file_with_progress(
                        src, dst, file_size,
                        progress, index, total_files
                    )
                    copied_count += 1

                except Exception as e:
                    failed_files.append((filename, str(e)))

            # Update UI on main thread
            def finish():
                progress.close()

                # Show summary
                if progress.cancelled:
                    self.status_var.set(
                        f"Cancelled. {copied_count}/{total_files} files copied."
                    )
                elif failed_files:
                    error_msg = "\n".join(
                        [f"- {name}: {err}" for name, err in failed_files]
                    )
                    messagebox.showerror(
                        "Copy errors",
                        f"Errors on {len(failed_files)} file(s):\n{error_msg}"
                    )
                    self.status_var.set(
                        f"✅ {copied_count}/{total_files} files copied "
                        f"({len(failed_files)} errors)"
                    )
                else:
                    self.status_var.set(
                        f"✅ {copied_count} file(s) copied successfully"
                    )

                # Refresh the destination panel
                if refresh_side == 'left':
                    self._refresh_left()
                else:
                    self._refresh_right()

            self.root.after(0, finish)

        # Start copy in background thread
        thread = threading.Thread(target=do_copy, daemon=True)
        thread.start()

    def _copy_single_file_with_progress(self, src, dst, file_size,
                                         progress, file_index, total_files):
        """
        Copy a single file while updating progress.

        Uses buffered reading/writing to track copy progress for large files.

        Args:
            src: Source file path.
            dst: Destination file path.
            file_size: Size of the source file in bytes.
            progress: ProgressWindow instance to update.
            file_index: Current file number (1-based).
            total_files: Total number of files being copied.

        Raises:
            Exception: If the copy operation fails or is cancelled.
        """
        filename = os.path.basename(src)
        bytes_copied = 0

        with open(src, 'rb') as src_file, open(dst, 'wb') as dst_file:
            while True:
                # Check for cancellation
                if progress.cancelled:
                    # Clean up partial file
                    dst_file.close()
                    try:
                        os.remove(dst)
                    except OSError:
                        pass
                    raise Exception("Operation cancelled")

                # Read and write a chunk
                chunk = src_file.read(self.COPY_BUFFER_SIZE)
                if not chunk:
                    break

                dst_file.write(chunk)
                bytes_copied += len(chunk)

                # Update progress (use after() to update from main thread)
                self.root.after(
                    0,
                    lambda b=bytes_copied, s=file_size, f=filename, i=file_index, t=total_files:
                        progress.update_progress(b, s, f, i, t)
                )

        # Preserve file metadata (timestamps, permissions)
        shutil.copystat(src, dst)

    def _delete_selected(self):
        """Delete selected files/folders from the focused panel."""
        # Determine which panel has focus
        if self.left_tree.focus():
            tree = self.left_tree
            side = 'left'
        elif self.right_tree.focus():
            tree = self.right_tree
            side = 'right'
        else:
            messagebox.showwarning("Warning", "Select a file to delete")
            return

        selected = self._get_selected_paths(tree)
        if not selected:
            return

        # Build confirmation message
        if len(selected) == 1:
            confirm_msg = f"Permanently delete:\n{selected[0][0]}?"
        else:
            confirm_msg = f"Permanently delete {len(selected)} items?"

        if not messagebox.askyesno("Confirmation", confirm_msg):
            return

        deleted_count = 0
        errors = []

        for path, is_dir in selected:
            try:
                if is_dir:
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                deleted_count += 1
            except Exception as e:
                errors.append((os.path.basename(path), str(e)))

        # Update status
        if errors:
            error_msg = "\n".join([f"- {name}: {err}" for name, err in errors])
            messagebox.showerror(
                "Deletion errors",
                f"Could not delete {len(errors)} item(s):\n{error_msg}"
            )

        self.status_var.set(f"✅ Deleted: {deleted_count} item(s)")

        # Refresh the panel
        if side == 'left':
            self._refresh_left()
        else:
            self._refresh_right()

    @staticmethod
    def _format_size(size):
        """
        Format a file size in human-readable units.

        Args:
            size: File size in bytes.

        Returns:
            A formatted string like "1.5 MB" or "256 KB".
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @staticmethod
    def _format_time(timestamp):
        """
        Format a Unix timestamp as a readable date/time string.

        Args:
            timestamp: Unix timestamp (seconds since epoch).

        Returns:
            A formatted string like "2024-01-15 14:30".
        """
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')


def main():
    """Application entry point."""
    root = tk.Tk()
    app = DualFileExplorer(root)
    root.mainloop()


if __name__ == "__main__":
    main()