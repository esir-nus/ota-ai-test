# Robot-AI OTA Daemon

A Python-based OTA (Over-The-Air) update daemon for the Robot-AI project on Raspberry Pi.

## Overview

This daemon runs continuously in the background on the Raspberry Pi while the device is powered on. It handles checking for updates, notifying users, scheduling updates, performing backups, and applying updates to the Robot-AI system.

## Features

- Scheduled update checks at 3 AM, 4 AM, and 5 AM daily
- Network quality validation before update operations
- User notifications with severity classification
- Voice command processing for update decisions
- System backup with retention policy
- Safe update application with integrity verification
- Automatic and user-triggered rollback mechanisms
- Multi-product support

## Architecture

The daemon consists of the following key components:

1. **Core Service** - The main daemon process that manages the update lifecycle
2. **Network Module** - Handles communication with the OTA server
3. **Scheduler** - Manages the timing of update checks and installations
4. **Backup System** - Creates and manages system backups
5. **Notification System** - Integrates with the Robot-AI projector for user notifications
6. **Voice Command Processor** - Processes user voice commands related to updates
7. **Update Manager** - Handles the download and installation of updates
8. **Rollback System** - Manages system restoration when needed

## Configuration

The daemon uses a configuration file located at `/etc/ota_config.json` with the following structure:

```json
{
  "product_type": "robot_ai",
  "version": "1.0.0",
  "update_server": "https://updates.robot-ai.example.com",
  "update_check_times": ["03:00", "04:00", "05:00"],
  "backup_retention_count": 2,
  "device_id": "A1B2-C3D4"
}
```

## File Structure

```
OTA/daemon/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── daemon_service.py
│   └── config_manager.py
├── network/
│   ├── __init__.py
│   └── ota_client.py
├── scheduler/
│   ├── __init__.py
│   └── task_scheduler.py
├── backup/
│   ├── __init__.py
│   └── system_backup.py
├── notification/
│   ├── __init__.py
│   └── user_notification.py
├── voice/
│   ├── __init__.py
│   └── command_processor.py
├── update/
│   ├── __init__.py
│   └── update_manager.py
├── rollback/
│   ├── __init__.py
│   └── recovery_system.py
└── utils/
    ├── __init__.py
    └── device_identifier.py
```

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure the system service: `sudo ./install_service.sh`
4. Start the service: `sudo systemctl start robot-ai-ota.service`

## Development

See the `TASKS.md` file in the OTA directory for the current development tasks and progress. 