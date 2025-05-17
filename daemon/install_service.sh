#!/bin/bash
# Installation script for the Robot-AI OTA daemon service

# Ensure script is run as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Variables
SERVICE_NAME="robot-ai-ota"
SERVICE_FILE="${SCRIPT_DIR}/robot-ai-ota.service"
SYSTEMD_DIR="/etc/systemd/system"
CONFIG_FILE="/etc/ota_config.json"

echo "Installing Robot-AI OTA daemon service..."

# Create configuration file if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating default configuration file at $CONFIG_FILE"
    python3 -c "
import json
config = {
    'product_type': 'robot_ai',
    'version': '1.0.0',
    'update_server': 'https://updates.robot-ai.example.com',
    'update_check_times': ['03:00', '04:00', '05:00'],
    'backup_retention_count': 2,
    'device_id': None
}
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
    chmod 644 "$CONFIG_FILE"
fi

# Copy service file to systemd directory
echo "Copying service file to $SYSTEMD_DIR/$SERVICE_NAME.service"
cp "$SERVICE_FILE" "$SYSTEMD_DIR/$SERVICE_NAME.service"
chmod 644 "$SYSTEMD_DIR/$SERVICE_NAME.service"

# Create log directory if it doesn't exist
if [ ! -d "/var/log/robot-ai" ]; then
    echo "Creating log directory at /var/log/robot-ai"
    mkdir -p "/var/log/robot-ai"
fi

# Reload systemd daemon
echo "Reloading systemd daemon"
systemctl daemon-reload

# Enable the service to start on boot
echo "Enabling service to start on boot"
systemctl enable "$SERVICE_NAME"

echo "Installation complete."
echo "To start the service now, run: sudo systemctl start $SERVICE_NAME"
echo "To check status: sudo systemctl status $SERVICE_NAME" 