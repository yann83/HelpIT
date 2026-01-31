# HelpIT

A Windows remote administration tool built with Python and Tkinter.

HelpIT provides IT administrators with a graphical interface to manage remote Windows machines, including process management, service control, file transfer, and remote script execution.

## Features

- **Remote Machine Discovery**: Ping and validate remote machines by IP or hostname
- **Process Management**: View and kill running processes on remote machines
- **Service Management**: Start, stop, and restart Windows services
- **File Explorer**: Dual-pane file browser for transferring files between local and remote machines
- **Remote Script Execution**: Execute PowerShell (.ps1) and Batch (.bat, .cmd) scripts remotely
- **Wake-on-LAN**: Send magic packets to wake up machines
- **Remote Desktop**: Quick launch RDP sessions
- **Remote Assistance**: Launch Microsoft Remote Assistance
- **Computer Management**: Open MMC snap-in for remote machines
- **Remote CMD**: Open command prompt on remote machines via PsExec

## Requirements

### System Requirements

- Windows 10/11
- Python 3.8 or higher
- Administrator privileges (for PsExec operations)
- Network access to target machines

### Dependencies

```
ping3>=4.0.4
pywin32>=306
cryptography>=41.0.0
wakeonlan>=3.0.0
```

### External Tools

HelpIT requires PsTools from Microsoft Sysinternals. Download from:
https://docs.microsoft.com/en-us/sysinternals/downloads/pstools

Required executables (place in `bin/` folder):
- `PsExec64.exe`
- `pskill64.exe`
- `pslist64.exe`
- `PsService64.exe`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/HelpIT.git
cd HelpIT
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Download PsTools and extract the required executables to the `bin/` folder.

4. Create the configuration file `config.json`:
```json
{
    "default_path": "C:\\temp",
    "ping_threshold": 75
}
```

## Usage

### Running the Application

```bash
python main.py
```

### Basic Workflow

1. Enter the IP address or hostname of the target machine
2. Click "Check" or press Enter to validate the connection
3. Use the action buttons to manage the remote machine

### Configuration

Edit `config.json` to customize:

| Setting | Description | Default |
|---------|-------------|---------|
| `default_path` | Default local path for file explorer | `C:\temp` |
| `ping_threshold` | Ping threshold in ms (orange warning if exceeded) | `75` |

### Remote Scripts

Place your scripts in the `scripts/` folder. Supported formats:
- PowerShell scripts (`.ps1`)
- Batch files (`.bat`, `.cmd`)

Scripts are copied to the remote machine's `C:\Windows\Temp\` folder before execution.

## Project Structure

```
HelpIT/
├── bin/                    # PsTools executables
│   ├── PsExec64.exe
│   ├── pskill64.exe
│   ├── pslist64.exe
│   └── PsService64.exe
├── scripts/                # Scripts for remote execution
├── tmp/                    # Temporary files and session logs
├── main.py                 # Main application entry point
├── psexec.py              # PsExec wrapper class
├── explorer.py            # Dual-pane file explorer
├── process.py             # Process manager GUI
├── service.py             # Service manager GUI
├── script_manager.py      # Script execution GUI
├── wolmanager.py          # Wake-on-LAN database manager
├── config.json            # Application configuration
├── config.sqlite          # MAC address database
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Security Considerations

- HelpIT uses PsExec which requires administrator credentials
- Credentials are handled by Windows authentication (no storage in the app)
- MAC addresses are stored locally in an SQLite database
- Ensure proper network security policies are in place

## Troubleshooting

### Common Issues

**"PsExec64 missing" error**
- Ensure PsTools executables are in the `bin/` folder

**"No ping" response**
- Check network connectivity
- Verify firewall allows ICMP
- Confirm the target machine is online

**"Could not retrieve Product Name"**
- PsExec may not have sufficient permissions
- Ensure you're running as administrator
- Check that remote registry service is running on target

**Services/Processes list is empty**
- Verify PsExec can connect to the target
- Check Windows Firewall settings on target machine

## Building Executable

To create a standalone executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "bin;bin" --add-data "config.json;." main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [PsTools](https://docs.microsoft.com/en-us/sysinternals/downloads/pstools) by Mark Russinovich
- [Tkinter](https://docs.python.org/3/library/tkinter.html) for the GUI framework
- [ping3](https://github.com/kyan001/ping3) for ICMP ping functionality
- [wakeonlan](https://github.com/remcohaszing/pywakeonlan) for Wake-on-LAN support

## Changelog

### Version 1.0.0
- Initial release
- Process and service management
- File explorer with copy progress
- Remote script execution
- Wake-on-LAN support
