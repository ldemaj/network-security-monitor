# Network Device Monitor

A Python-based network monitoring tool that scans your local network for connected devices, identifies their types, and alerts you when new devices join the network.

## Features

- **Real-time Network Scanning**: Uses ARP scanning to discover all devices on your local network
- **Device Type Detection**: Identifies device types (phones, computers, TVs, etc.) using:
  - MAC address vendor information
  - Port scanning
  - TTL analysis
- **New Device Alerts**: Sends email notifications when new devices are detected
- **Persistent Storage**: Stores device information in SQLite database
- **Web Interface**: Clean, modern UI showing:
  - All discovered devices
  - Device types
  - First and last seen timestamps
  - New device alerts
- **Device History**: Tracks when devices were first and last seen on the network

## How It Works

1. **Network Scanning**:
   - Uses Scapy for ARP scanning
   - Scans the local network
   - Collects IP and MAC addresses

2. **Device Type Detection**:
   - Analyzes MAC address vendor information
   - Performs port scanning for device signatures
   - Uses TTL values for basic OS detection
   - Checks for common device ports (e.g., RTSP for cameras, 9100 for printers)

3. **Database Storage**:
   - SQLite database for persistent storage
   - Tracks device history
   - Stores first and last seen timestamps
   - Maintains device type information

4. **Alert System**:
   - Email notifications for new devices
   - Configurable alert thresholds
   - Detailed device information in alerts

## Requirements

- Python 3.7+
- Nmap (for device type detection)
- Administrator/root privileges (for network scanning)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ldemaj/network-security-monitor.git
   cd network-security-monitor
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Nmap:
   - Windows: Download and install from [nmap.org](https://nmap.org/download.html)
   - Linux: `sudo apt-get install nmap`
   - macOS: `brew install nmap`

5. Set up environment variables for email notifications (optional):
   ```
   EMAIL_SENDER=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   EMAIL_RECEIVER=receiver-email@example.com
   ```

   Note: For Gmail, you'll need to use an App Password. See [Google's documentation](https://support.google.com/accounts/answer/185833) for details.

## Usage

1. Run the application:
   ```bash
   # Make sure you're in the project directory and virtual environment is activated
   python app.py
   ```

2. Access the web interface:
   - Open your browser
   - Navigate to `http://localhost:5000`

3. The interface will show:
   - All discovered devices
   - Device types
   - Connection history
   - New device alerts

## Running as a Service

### Windows
1. Create a batch file (start_monitor.bat):
   ```batch
   @echo off
   cd /d %~dp0
   call venv\Scripts\activate
   python app.py
   ```

2. Create a Windows Service using NSSM or Task Scheduler

### Linux
1. Create a systemd service file:
   ```ini
   [Unit]
   Description=Network Monitor Service
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/path/to/network-security-monitor
   Environment=PATH=/path/to/network-security-monitor/venv/bin
   ExecStart=/path/to/network-security-monitor/venv/bin/python app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. Enable and start the service:
   ```bash
   sudo systemctl enable network-security-monitor
   sudo systemctl start network-security-monitor
   ```

## Security Considerations

- The application requires administrator/root privileges for network scanning
- Email credentials should be stored securely
- The database file contains network device information and should be protected
- Consider using a firewall to restrict access to the web interface

## Troubleshooting

1. **Scanning Issues**:
   - Ensure you're running with administrator/root privileges
   - Check if your firewall is blocking the scans
   - Verify Nmap is installed correctly

2. **Email Notifications**:
   - Verify environment variables are set correctly
   - For Gmail, ensure you're using an App Password
   - Check your spam folder for notifications

3. **Device Type Detection**:
   - Some devices might show as "Unknown Device"
   - This is normal for devices that don't respond to scans
   - Consider adjusting scan parameters in scanner.py

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
