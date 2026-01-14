# Service Manager Module

## Overview

The `service.py` module provides a graphical interface to display and manage Windows services on remote machines using PsExec. It complements the ProcessManager module with service-specific functionality.

## Features

- **Display Service List**: Shows all services from a CSV file with 3 columns (ID, Name, State)
- **Control Services**: Three action buttons per service:
  - **Stop** (Red): Stops a running service
  - **Run** (Green): Starts a stopped service
  - **Restart** (Blue): Restarts a service (stop then start)
- **Visual Status Feedback**: Color-coded status labels:
  - Green: RUNNING
  - Red: STOPPED
  - Orange: PENDING states
  - Amber: PAUSED
- **Automatic Status Update**: Status refreshes after each action
- **Refresh Function**: Reload the service list to see changes
- **Scrollable Interface**: Handle large service lists with mouse wheel support

## Architecture

### ServiceManager Class

The `ServiceManager` class is a complete, standalone module that handles:
- Reading service data from CSV files (semicolon-delimited)
- Creating a Tkinter GUI with scrollable list
- Executing service control commands via PsExec
- Updating service status dynamically
- Providing visual feedback with color-coded states

### Key Methods

```python
class ServiceManager:
    def __init__(self, csv_filename, psexec_manager, current_ip, 
                 current_hostname, psexec_path, log_path)
    def _create_widgets(self)              # Creates the GUI
    def _load_services(self)               # Loads services from CSV
    def _update_service_status(service_id) # Updates status display
    def _stop_service(service_id)          # Stops a service
    def _start_service(service_id)         # Starts a service
    def _restart_service(service_id)       # Restarts a service
    def _refresh_service_list(self)        # Refreshes the list
    def show(self)                         # Shows the window
```

## CSV File Format

The CSV file must have the following format with semicolon (`;`) as delimiter:

```csv
id;name;etat
AdobeARMservice;Adobe Acrobat Update Service;STOPPED
Audiosrv;Audio Windows;RUNNING
BFE;Moteur de filtrage de base;RUNNING
```

### Columns:
- **id**: Service identifier (used for commands)
- **name**: Service display name
- **etat**: Service state (RUNNING, STOPPED, etc.)

## Service States

The module recognizes the following service states from PsExec:

| State | Code | Color | Description |
|-------|------|-------|-------------|
| RUNNING | 4 | Green | Service is running |
| STOPPED | 1 | Red | Service is stopped |
| START_PENDING | 2 | Orange | Service is starting |
| STOP_PENDING | 3 | Orange | Service is stopping |
| CONTINUE_PENDING | 5 | Orange | Service is resuming |
| PAUSE_PENDING | 6 | Orange | Service is pausing |
| PAUSED | 7 | Amber | Service is paused |

## Usage

### From the Main Application

1. Select a target machine (validate an IP or hostname)
2. Click on the "Services" button or menu
3. The Service Manager window will open automatically
4. Use the action buttons:
   - **Stop**: Click red button to stop a running service
   - **Run**: Click green button to start a stopped service
   - **Restart**: Click blue button to restart a service
5. The status label updates automatically after each action
6. Use "Refresh List" to reload the service list

### Integration Example

```python
# In main.py
from service import ServiceManager

def open_services(self):
    # Get services list using PsExec
    self.psexec.get_services_to_csv()
    csv_filename = Path(LOG_PATH / f"{self.current_hostname}_services.csv")
    
    if csv_filename.exists():
        # Create and show ServiceManager
        service_manager = ServiceManager(
            csv_filename=csv_filename,
            psexec_manager=self.psexec,
            current_ip=self.current_ip,
            current_hostname=self.current_hostname,
            psexec_path=self.psexec_path,
            log_path=str(LOG_PATH)
        )
```

## PsExec Methods Used

The ServiceManager uses the following methods from PsExecManager:

### get_service_status(service_id)
```python
# Returns: 1 if RUNNING, 0 otherwise
status = psexec_manager.get_service_status("Audiosrv")
if status == 1:
    print("Service is running")
```

### stop_service(service_id)
```python
# Returns: True if success, False otherwise
result = psexec_manager.stop_service("Audiosrv")
```

### start_service(service_id)
```python
# Returns: True if success, False otherwise
result = psexec_manager.start_service("Audiosrv")
```

### restart_service(service_id)
```python
# Returns: True if success, False otherwise
result = psexec_manager.restart_service("Audiosrv")
```

## GUI Layout

```
┌────────────────────────────────────────────────────────────────┐
│              Services on HOSTNAME (192.168.1.100)              │
├────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ [Stop] [Run] [Restart]  Service Name              STATUS │  │
│ │ [Stop] [Run] [Restart]  Adobe Update Service     STOPPED│  │
│ │ [Stop] [Run] [Restart]  Audio Windows            RUNNING│  │
│ │ [Stop] [Run] [Restart]  Base Filtering Engine    RUNNING│  │
│ │ ...                                                       │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                │
│              [Refresh List]  [Close]                           │
└────────────────────────────────────────────────────────────────┘
```

## Button Colors

- **Stop Button**: Red (#F44336) - Danger/Stop action
- **Run Button**: Green (#4CAF50) - Success/Start action
- **Restart Button**: Blue (#2196F3) - Info/Restart action

## Requirements

- Python 3.6+
- tkinter (usually included with Python)
- PsExec64.exe (SysInternals Suite)
- Windows environment (services are Windows-specific)
- Administrator rights on remote machine

## Error Handling

The module includes comprehensive error handling:
- File not found errors for CSV files
- Network errors when executing remote commands
- User confirmation before performing actions
- Logging of all operations and errors
- Graceful handling of service control failures

## Code Comments

All code comments are in English for better maintainability and international collaboration. The code follows Python best practices with:
- Clear docstrings for classes and methods
- Inline comments explaining complex logic
- Type hints in docstrings for parameters

## Differences from ProcessManager

| Feature | ProcessManager | ServiceManager |
|---------|----------------|----------------|
| Columns | 1 (name) | 3 (id, name, state) |
| Buttons per row | 1 (Kill) | 3 (Stop, Run, Restart) |
| CSV Delimiter | Comma | Semicolon |
| Button behavior | Disabled on success | Always enabled |
| Status update | N/A | Automatic after action |
| Color coding | Button only | Status label |

## Technical Notes

### Why Use Service ID?

Service commands must use the service ID (short name) rather than the display name:
- **Correct**: `stop_service("Audiosrv")`
- **Incorrect**: `stop_service("Audio Windows")`

The CSV provides both ID and name, but commands use the ID column.

### Status Update Flow

1. User clicks action button (Stop/Run/Restart)
2. Confirmation dialog appears
3. PsExec command is executed
4. `_update_service_status()` is called
5. `get_service_status()` queries current state
6. Status label updates with new state and color

### Color Mapping

Colors are stored in `self.state_colors` dictionary for easy customization:

```python
self.state_colors = {
    'RUNNING': '#4CAF50',      # Green
    'STOPPED': '#F44336',      # Red
    'START_PENDING': '#FF9800', # Orange
    # ... etc
}
```

## Future Enhancements

Potential improvements:
- Filter services by state (show only running, stopped, etc.)
- Search functionality to find specific services
- Service dependency information
- Startup type management (Auto, Manual, Disabled)
- Bulk operations (stop/start multiple services)
- Service description tooltip on hover

## Troubleshooting

**Problem**: Service won't start
- Check if service is disabled in startup type
- Verify dependencies are running
- Check Windows Event Logs on remote machine

**Problem**: "Access Denied" error
- Run application as administrator
- Verify account has admin rights on remote machine
- Check that Remote Registry service is running

**Problem**: Status doesn't update
- Check network connectivity
- Verify PsExec can connect to remote machine
- Check firewall rules

## License

This module is part of the HelpIT application.
