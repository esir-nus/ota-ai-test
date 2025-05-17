#!/bin/bash
# Setup script for OTA daemon test environment on Raspberry Pi
# This script sets up the necessary directories and dependencies for testing

set -e

echo "Setting up OTA daemon test environment on Raspberry Pi..."

# Create required directories
echo "Creating required directories..."
sudo mkdir -p /var/lib/robot-ai-ota/downloads
sudo mkdir -p /var/lib/robot-ai/notifications
sudo mkdir -p /backups
sudo mkdir -p /opt/robot-ai
sudo mkdir -p /etc/robot-ai

# Set proper permissions for the test environment
echo "Setting directory permissions..."
sudo chmod 755 /var/lib/robot-ai-ota
sudo chmod 755 /var/lib/robot-ai
sudo chmod 755 /backups
sudo chmod 755 /opt/robot-ai

# Create test device ID
echo "Creating test device ID..."
echo "TEST-DEVICE-123" | sudo tee /etc/device_id > /dev/null

# Create test OTA config
echo "Creating test OTA configuration..."
cat << EOF | sudo tee /etc/ota_config.json > /dev/null
{
    "version": "1.0.0",
    "device_id": "TEST-DEVICE-123",
    "product_type": "robot-a",
    "update_server": "http://localhost:8000/api/update",
    "update_check_times": ["03:00", "04:00", "05:00"],
    "backup_retention_count": 2
}
EOF

# Install test dependencies
echo "Installing test dependencies..."
pip install pytest pytest-cov coverage mock

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo "Test environment setup completed successfully."
    echo "You can now run the tests using:"
    echo "  cd OTA && python -m tests.run_tests"
else
    echo "Error: Test environment setup failed."
    exit 1
fi 