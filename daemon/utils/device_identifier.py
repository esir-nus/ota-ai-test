"""
Device Identifier utility for the OTA daemon.

This module handles generating and retrieving the unique device ID
based on hardware identifiers (MAC address).
"""

import hashlib
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("ota-daemon.device-id")

DEVICE_ID_PATH = Path("/etc/device_id")


def get_mac_address() -> Optional[str]:
    """Get the MAC address of the primary network interface.
    
    Returns:
        MAC address as string or None if not found.
    """
    try:
        # On Raspberry Pi (Linux), we can get the MAC address from /sys/class/net
        if os.path.exists("/sys/class/net"):
            # Look for common network interfaces
            for interface in ["eth0", "wlan0"]:
                mac_path = f"/sys/class/net/{interface}/address"
                if os.path.exists(mac_path):
                    with open(mac_path, "r") as f:
                        mac = f.read().strip()
                        if mac:
                            logger.debug(f"Found MAC address {mac} from {mac_path}")
                            return mac
        
        # Try using ip command
        output = subprocess.check_output(["ip", "link"], universal_newlines=True)
        for line in output.split("\n"):
            if "link/ether" in line:
                match = re.search(r"link/ether ([0-9a-f:]+)", line)
                if match:
                    mac = match.group(1)
                    logger.debug(f"Found MAC address {mac} from ip command")
                    return mac
        
        logger.warning("Could not find MAC address")
        return None
    except Exception as e:
        logger.error(f"Error getting MAC address: {str(e)}")
        return None


def generate_device_id() -> str:
    """Generate a unique device ID based on the MAC address.
    
    Returns:
        A unique device ID as a string.
    """
    mac_address = get_mac_address()
    
    if not mac_address:
        # Fallback to a random ID if MAC address is not available
        mac_address = os.urandom(6).hex()
        logger.warning("Using random value for device ID as MAC address is not available")
    
    # Generate SHA256 hash of the MAC address
    device_hash = hashlib.sha256(mac_address.encode()).hexdigest()
    
    # Use the first 8 characters with a dash in the middle for readability
    device_id = f"{device_hash[:4]}-{device_hash[4:8]}".upper()
    
    logger.info(f"Generated device ID: {device_id}")
    return device_id


def get_device_id() -> str:
    """Get the device ID, generating and saving if it doesn't exist.
    
    Returns:
        The device ID as a string.
    """
    if DEVICE_ID_PATH.exists():
        # Read existing device ID
        try:
            with open(DEVICE_ID_PATH, "r") as f:
                device_id = f.read().strip()
                logger.debug(f"Read device ID from {DEVICE_ID_PATH}: {device_id}")
                return device_id
        except Exception as e:
            logger.error(f"Error reading device ID: {str(e)}")
    
    # Generate new device ID
    device_id = generate_device_id()
    
    # Save the device ID
    try:
        # Ensure the directory exists
        DEVICE_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(DEVICE_ID_PATH, "w") as f:
            f.write(device_id)
        logger.info(f"Saved device ID to {DEVICE_ID_PATH}")
    except Exception as e:
        logger.error(f"Error saving device ID: {str(e)}")
    
    return device_id


if __name__ == "__main__":
    # Enable stdout logging for testing
    logging.basicConfig(level=logging.DEBUG)
    print(f"Device ID: {get_device_id()}") 