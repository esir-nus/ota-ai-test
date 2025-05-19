# Robot-AI OTA System

An over-the-air (OTA) update system for Robot-AI devices, providing secure and reliable software updates with rollback capabilities.

## Features

- Automated update checking and installation
- Secure communication with update server (HTTPS)
- Package integrity verification
- System backup and restore
- Voice command integration
- GUI interface for update management
- Multi-product support
- Rollback capability
- Progress monitoring and notifications

## Prerequisites

- Python 3.8 or higher
- Raspberry Pi (tested on Raspberry Pi 4)
- systemd-based Linux system
- Network connectivity

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/esir-nus/ota-ai-test.git
   cd ota-ai-test
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the OTA daemon service:
   ```bash
   sudo ./daemon/install_service.sh
   ```

## Configuration

1. Create the configuration file at `/etc/ota_config.json`:
   ```json
   {
     "product_type": "robot_ai",
     "version": "1.0.0",
     "update_server": "https://updates.robot-ai.example.com",
     "update_check_times": ["03:00", "04:00", "05:00"],
     "backup_retention_count": 2
   }
   ```

2. Configure update server URL in the configuration file.

3. Set up device identification:
   - The system will automatically generate a device ID based on the MAC address
   - The ID is stored in `/etc/device_id`

## Usage

### GUI Interface

The system provides a Tkinter-based GUI for:
- Checking update status
- Triggering manual updates
- Monitoring update progress
- Viewing version information

### Voice Commands

Supported voice commands:
- "Install update tonight"
- "Install update now"
- "Roll back update"
- "Cancel update"

### Manual Operation

1. Check for updates:
   ```bash
   sudo systemctl start robot-ai-ota.service
   ```

2. View status:
   ```bash
   sudo systemctl status robot-ai-ota.service
   ```

3. View logs:
   ```bash
   sudo journalctl -u robot-ai-ota.service
   ```

## Development

### Project Structure

```
OTA/
├── daemon/           # Main daemon implementation
│   ├── core/        # Core functionality
│   ├── gui/         # GUI interface
│   ├── network/     # Network communication
│   ├── update/      # Update management
│   └── voice/       # Voice command processing
├── tests/           # Test suite
└── TASKS.md         # Implementation tasks
```

### Running Tests

```bash
python -m pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Security

- All communication with the update server is over HTTPS
- Update packages are verified using checksums
- System backups are created before updates
- Rollback capability for failed updates

## License

[Add your license here]

## Support

For support, please [create an issue](https://github.com/your-username/robot-ai-ota/issues) on GitHub. 
