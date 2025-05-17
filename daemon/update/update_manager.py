"""
Update Manager for the OTA daemon.

This module handles applying updates, including download management,
verification, and installation.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("ota-daemon.update")

class UpdateManager:
    """Manages update operations for the OTA daemon."""
    
    def __init__(self, network_client=None, backup_manager=None):
        """Initialize the update manager.
        
        Args:
            network_client: The OTA network client for downloading updates.
            backup_manager: The backup manager for creating backups.
        """
        self.network_client = network_client
        self.backup_manager = backup_manager
        
        # Temporary directory for downloads
        self.temp_dir = Path("/var/lib/robot-ai-ota/downloads")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def apply_updates(self, files: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Apply downloaded updates to the system.
        
        Args:
            files: List of downloaded file information.
        
        Returns:
            A tuple of (success, message).
        """
        try:
            for file_info in files:
                source_path = file_info["source_path"]
                destination = Path(file_info["destination"])
                executable = file_info.get("executable", False)
                
                # Create destination directory if it doesn't exist
                destination.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy the file to its destination
                shutil.copy2(source_path, destination)
                
                # Set executable permission if needed
                if executable:
                    os.chmod(destination, 0o755)
                
                logger.info(f"Applied update: {source_path} -> {destination}")
            
            return (True, "Updates applied successfully")
        except Exception as e:
            error_msg = f"Error applying updates: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
    
    def restart_services(self, services: List[str]) -> Tuple[bool, str]:
        """Restart system services.
        
        Args:
            services: List of service names to restart.
        
        Returns:
            A tuple of (success, message).
        """
        try:
            for service in services:
                logger.info(f"Restarting service: {service}")
                result = subprocess.run(
                    ["systemctl", "restart", service],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    error_msg = f"Failed to restart service {service}: {result.stderr}"
                    logger.error(error_msg)
                    return (False, error_msg)
            
            return (True, "Services restarted successfully")
        except Exception as e:
            error_msg = f"Error restarting services: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary download files."""
        try:
            for file in self.temp_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            
            logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {str(e)}")
            
    def reboot_system(self) -> None:
        """Reboot the system to apply updates."""
        try:
            logger.info("Rebooting system")
            subprocess.run(["reboot"], check=True)
        except Exception as e:
            logger.error(f"Failed to reboot system: {str(e)}") 