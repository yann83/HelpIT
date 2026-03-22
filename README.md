# HelpIT

A Windows remote administration tool built with Python and Tkinter.

HelpIT provides IT administrators with a graphical interface to manage remote Windows machines, including process management, service control, file transfer, and remote script execution.

**Why two versions ?**

| Criterion                            | PsExec                                                                                                                               | WinRM / PowerShell Remoting                                                                                                                                |
|--------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Client‑side configuration level      | Very low: administrative shares (`admin$`), admin rights, no dedicated role to install.                                             | Higher: WinRM must be enabled, `Enable‑PSRemoting`, firewall rules, GPO restrictions, etc.                                                                |
| OS availability                      | Works on very old versions of Windows (no PowerShell remoting required).                                                            | Requires PowerShell and WinRM (Windows 7+ / recent servers).                                                                                               |
| Security / hardening                 | Frequently exploited by attackers (lateral movement), no native encryption, difficult to restrict finely.                           | Native, supports encryption (HTTPS), Kerberos/NTLM authentication, possible to filter by IP/GPO.                                                          |
| Traceability / logging               | Very low: runs via `PSEXESVC`, no dedicated network logs, often hidden.                                                           | Very good: WinRM and PowerShell logs, correlation and audit capabilities.                                                                                  |
| Ease of one‑off usage                | Very simple for a single command or an interactive CMD session (`psexec \\pc cmd`).                                                 | Requires a bit more CLI (e.g., `Enter‑PSSession`, `Invoke‑Command`) but is more consistent and robust.                                                     |
| Interoperability / scripts           | Good for launching executables or scripts over SMB, but not “native” PowerShell.                                                   | Integrated with PowerShell: scripts, DSC, pipelines, etc., very well suited for automation.                                                               |
| Deployment / fleet administration    | Poorly suited for large‑scale or standardized deployment.                                                                           | Very suitable: GPO, Ansible, third‑party tools, centralized script‑based execution.                                                                        |
| Network / firewall interoperability  | Uses SMB (port 445) + RPC, often already open but very exposed.                                                                    | Dedicated ports (5985/5986), easier to filter and secure.                                                                                                  |
| Support “operating mode”             | Ideal as a “swiss‑army knife” fallback tool on machines that no longer respond to PowerShell or WinRM.                              | Ideal for day‑to‑day support, in a standardized and secure way within an Active Directory environment.                                                     |

**In concrete terms for an IT domain:**  
- **PsExec** = “Swiss‑army knife” easy to set up, but less secure and less traceable, usually reserved for emergency troubleshooting or legacy estates.  
- **WinRM / PowerShell Remoting** = modern standard solution for remote support, more secure, more automatable, and better suited to an active environment.



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
- Administrator privileges
- Network access to target machines
- WinRm for winrm version

### Dependencies

```
ping3
pywin32
cryptography
wakeonlan

# for psexec
pypsexec
smbprotocol

# for winrm
pywinrm
requests-ntlm
ntlm-auth
```

### External Tools

HelpIT requires PsTools from Microsoft Sysinternals. Download from:
https://docs.microsoft.com/en-us/sysinternals/downloads/pstools

Required executables (place in `bin/` folder):
- `PsExec64.exe`

## Installation

1. Download PsTools and extract the required executable to the `bin/` folder.

2. Create the configuration file `config.json`:
```json
{
    "default_path": "C:\\temp",
    "ping_threshold": 75
}
```

## Usage

The application is available in two versions: one with full psexec support and the other with winrm support. For the latter, winrm must be active on the domain.

### Running the Application

Run `HelpIT.exe`

### Basic Workflow

1. Enter the IP address or hostname of the target machine
2. Click "Check" or press Enter to validate the connection
3. Use the action buttons to manage the remote machine

For the winrm version, after step 3 you will need to enter your admin credential once again.

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

## Security Considerations

- HelpIT uses PsExec or WinRM which requires administrator credentials
- Credentials are handled by Windows authentication except for WinRM version with the `credentials.dat` file (see DPAPI below)
- MAC addresses are stored locally in an SQLite database
- Ensure proper network security policies are in place

## Troubleshooting

### Common Issues

Check your administrator rights: access to administrative shares, running programs as administrator, RDP access, and MSRA.

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

**Connection/execution error on with WinRM**
- Check tcp rules in GPO for winrm

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [PsTools](https://learn.microsoft.com/en-us/sysinternals/downloads/pstools) by Mark Russinovich
- [Tkinter](https://docs.python.org/3/library/tkinter.html) for the GUI framework
- [ping3](https://github.com/kyan001/ping3) for ICMP ping functionality
- [wakeonlan](https://github.com/remcohaszing/pywakeonlan) for Wake-on-LAN support
- [pypsexec](https://github.com/jborean93/pypsexec) by Jordan Borean
 - [pywinrm](https://github.com/diyan/pywinrm) by diyan

## Changelog

### Version 1.0.0
- Initial release
- Process and service management
- File explorer with copy progress
- Remote script execution
- Wake-on-LAN support
- WinRM support


## About Credentials Storage (DPAPI)

HelpIT can save WinRM credentials between sessions using the **Windows 
Data Protection API (DPAPI)**.

DPAPI is a built-in Windows encryption mechanism that ties the encryption 
key to the **current Windows user account**. This means:

- Credentials are stored encrypted in a local `credentials.dat` file
- The file is **unreadable on any other machine** or under any other 
  Windows account, even if copied
- No master password is required - Windows manages the key transparently
- Requires `pywin32` (`pip install pywin32`)

To save credentials: check **"Remember my credentials"** in the login 
dialog on first launch.  
To update or clear them: click the **⚙ Creds** button in the status bar.

## WinRM Configuration (Group Policy)

WinRM (Windows Remote Management) must be enabled and properly configured
on all target machines. In a domain environment, this is best done via
**Group Policy Objects (GPO)**.

### Required GPO Settings

All settings below are located in:
`Computer Configuration > Policies > Windows Settings > Security Settings`
or
`Computer Configuration > Policies > Administrative Templates`

---

#### 1. Enable the WinRM Service

**Path:**
`Computer Configuration > Preferences > Control Panel Settings > Services`

| Setting | Value |
|---|---|
| Service name | `WinRM` |
| Startup type | `Automatic` |
| Service action | `Start service` |

---

#### 2. Allow WinRM through Windows Firewall

**Path:**
`Computer Configuration > Policies > Windows Settings > Security Settings > Windows Firewall with Advanced Security > Inbound Rules`

Create a new inbound rule:

| Setting | Value |
|---|---|
| Rule type | `Predefined` |
| Predefined rule | `Windows Remote Management` |
| Profile | `Domain` (at minimum) |
| Action | `Allow the connection` |

> **Note:** This opens TCP port **5985** (HTTP). If you use HTTPS, also open port **5986**.

---

#### 3. Configure the WinRM Listener

**Path:**
`Computer Configuration > Policies > Administrative Templates > Windows Components > Windows Remote Management (WinRM) > WinRM Service`

| Policy | Value |
|---|---|
| `Allow remote server management through WinRM` | `Enabled` |
| IPv4 filter | `*` (or restrict to your admin subnet, e.g. `192.168.1.0/24`) |
| IPv6 filter | `*` or leave empty |

---

#### 4. Set WinRM Authentication (NTLM / Negotiate)

**Path:**
`Computer Configuration > Policies > Administrative Templates > Windows Components > Windows Remote Management (WinRM) > WinRM Service`

| Policy | Value |
|---|---|
| `Allow Basic authentication` | `Disabled` (not needed, less secure) |
| `Allow CredSSP authentication` | `Disabled` (unless needed) |
| `Allow Negotiate authentication` | `Enabled` ✅ |

HelpIT uses **NTLM via Negotiate**, which is the default for domain accounts.
No extra configuration is required if Negotiate is enabled.

---

#### 5. (Optional) Increase Shell Memory / Timeout Limits

**Path:**
`Computer Configuration > Policies > Administrative Templates > Windows Components > Windows Remote Management (WinRM) > WinRM Service`

| Policy | Recommended value |
|---|---|
| `Specify maximum amount of memory in MB per Shell` | `1024` |
| `Specify maximum number of processes per Shell` | `15` |
| `Specify Shell Timeout` | `60000` (ms) |

---

### Verify WinRM is Active on a Target Machine

Run this command **on the target machine** (as administrator) to confirm
WinRM is listening:
```powershell
winrm enumerate winrm/config/listener
```

Expected output should show a listener on `Transport = HTTP` and `Port = 5985`.

To manually enable WinRM on a single machine (without GPO):
```powershell
winrm quickconfig -quiet
```

---

### Quick Diagnostic from the HelpIT Machine

To test connectivity to a target before using HelpIT, run this from
your admin workstation:
```powershell
Test-WSMan -ComputerName <IP_or_hostname>
```

A successful response confirms WinRM is reachable and responding.