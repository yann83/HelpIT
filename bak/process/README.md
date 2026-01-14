# Process Manager Module

## Overview

The `process.py` module provides a graphical interface to display and manage processes on remote Windows machines using PsExec.

## Features

- **Display Process List**: Shows all processes from a CSV file in a scrollable window
- **Kill Process**: Each process has a green "Kill" button to terminate it remotely
- **Visual Feedback**: Button turns red and becomes inactive after successfully killing a process
- **Refresh Function**: Reload the process list to see updated processes
- **Scrollable Interface**: Handle large process lists with mouse wheel support

## Architecture

### ProcessManager Class

The `ProcessManager` class is a complete, standalone module that handles:
- Reading process data from CSV files
- Creating a Tkinter GUI with scrollable list
- Executing kill commands via PsExec
- Providing visual feedback on operation success/failure

### Integration with Main Application

The `main.py` file has been updated to:
1. Import the `ProcessManager` class
2. Call it from the `show_processes()` method
3. Pass all required parameters (IP, hostname, PsExec path, log path)

## Usage

### From the Main Application

1. Select a target machine (validate an IP or hostname)
2. Click on the "Processes" button or menu
3. The Process Manager window will open automatically
4. Click the green "Kill" button next to any process to terminate it
5. The button will turn red if the operation succeeds
6. Use "Refresh List" to update the process list

### Parameters

When creating a `ProcessManager` instance, you need to provide:

```python
process_manager = ProcessManager(
    csv_filename=csv_filename,           # Path to CSV file with process list
    psexec_manager=self.psexec,          # PsExecManager instance
    current_ip=self.current_ip,          # Remote machine IP address
    current_hostname=self.current_hostname,  # Remote machine hostname
    psexec_path=self.psexec_path,        # Path to PsExec64.exe
    log_path=str(LOG_PATH)               # Path to log directory
)
```

## CSV File Format

The CSV file must have the following format:

```csv
name
AggregatorHost
firefox
chrome
...
```

- Header row: `name`
- One process name per line
- No additional columns required

## Code Comments

All code comments are in English for better maintainability and international collaboration. The code follows Python best practices with:
- Clear docstrings for classes and methods
- Inline comments explaining complex logic
- Type hints in docstrings for parameters

## Requirements

- Python 3.6+
- tkinter (usually included with Python)
- PsExec64.exe (SysInternals Suite)
- Windows 11 environment (as specified by user preferences)

## Error Handling

The module includes comprehensive error handling:
- File not found errors for CSV files
- Network errors when executing remote commands
- User confirmation before killing processes
- Logging of all operations and errors

## Future Enhancements

Potential improvements:
- Add process filtering/search functionality
- Display additional process information (PID, memory usage)
- Batch process termination
- Export filtered process lists
- Process priority management

## Technical Notes

### Why Toplevel Window?

The `ProcessManager` uses `tk.Toplevel()` instead of `tk.Tk()` because:
- It's a secondary window to the main application
- Allows multiple process manager windows simultaneously
- Doesn't interfere with the main application's mainloop
- Properly integrated with the parent window's lifecycle

### Button State Management

The buttons are stored in a dictionary (`self.process_buttons`) to:
- Enable updating button states after operations
- Provide visual feedback without reloading the entire list
- Maintain references for future operations

## License

This module is part of the HelpIT application.
