"""
User Notification System for the OTA daemon.

This module handles displaying notifications to users about OTA updates,
including update availability, installation scheduling, and results.
"""

import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional
import socket
import datetime

logger = logging.getLogger("ota-daemon.notification")

# Constants for notification files
NOTIFICATION_DIR = Path("/var/lib/robot-ai/notifications")
UPDATE_NOTIFICATION_FLAG = NOTIFICATION_DIR / "update_available.json"
UPDATE_PROGRESS_FLAG = NOTIFICATION_DIR / "update_progress.json"
UPDATE_RESULT_FLAG = NOTIFICATION_DIR / "update_result.json"
RELEASE_NOTES_FILE = Path("/release_notes.txt")

class NotificationType(Enum):
    """Types of notifications that can be displayed."""
    UPDATE_AVAILABLE = "update_available"
    UPDATE_SCHEDULED = "update_scheduled"
    UPDATE_IN_PROGRESS = "update_in_progress"
    UPDATE_COMPLETED = "update_completed"
    UPDATE_FAILED = "update_failed"
    ROLLBACK_AVAILABLE = "rollback_available"
    ROLLBACK_COMPLETED = "rollback_completed"

class UpdateSeverity(Enum):
    """Severity levels for updates."""
    CRITICAL = "critical"
    SECURITY = "security"
    REGULAR = "regular"
    FEATURE = "feature"

class NotificationSystem:
    """Handles user notifications for the OTA daemon."""
    
    def __init__(self, gui_socket_path: str = "/tmp/robot-ai-gui.sock"):
        """Initialize the notification system.
        
        Args:
            gui_socket_path: Path to the Unix socket for communicating with the GUI.
        """
        self.gui_socket_path = gui_socket_path
        
        # Ensure notification directory exists
        NOTIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    
    def notify_update_available(self, 
                               version: str,
                               severity: UpdateSeverity,
                               features: str,
                               release_notes: str,
                               size_mb: float) -> bool:
        """Notify the user about an available update.
        
        Args:
            version: The version of the available update.
            severity: The severity level of the update.
            features: A short description of the main features in the update.
            release_notes: The full release notes for the update.
            size_mb: The size of the update in megabytes.
        
        Returns:
            True if the notification was created successfully, False otherwise.
        """
        try:
            # Save release notes to file
            with open(RELEASE_NOTES_FILE, "w") as f:
                f.write(release_notes)
            
            # Create notification data
            notification_data = {
                "type": NotificationType.UPDATE_AVAILABLE.value,
                "version": version,
                "severity": severity.value,
                "features": features,
                "size_mb": size_mb,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Save notification data to flag file
            with open(UPDATE_NOTIFICATION_FLAG, "w") as f:
                json.dump(notification_data, f, indent=2)
            
            logger.info(f"Created update notification for version {version}")
            
            # Try to send notification to GUI via socket
            self._send_notification_to_gui(notification_data)
            
            return True
        except Exception as e:
            logger.error(f"Error creating update notification: {str(e)}")
            return False
    
    def notify_update_scheduled(self, version: str, scheduled_time: str) -> bool:
        """Notify the user that an update has been scheduled.
        
        Args:
            version: The version of the scheduled update.
            scheduled_time: The time the update is scheduled for, in 24-hour format (HH:MM).
        
        Returns:
            True if the notification was created successfully, False otherwise.
        """
        try:
            # Create notification data
            notification_data = {
                "type": NotificationType.UPDATE_SCHEDULED.value,
                "version": version,
                "scheduled_time": scheduled_time,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Save notification data to flag file
            with open(UPDATE_PROGRESS_FLAG, "w") as f:
                json.dump(notification_data, f, indent=2)
            
            logger.info(f"Created update scheduled notification for version {version} at {scheduled_time}")
            
            # Try to send notification to GUI via socket
            self._send_notification_to_gui(notification_data)
            
            return True
        except Exception as e:
            logger.error(f"Error creating update scheduled notification: {str(e)}")
            return False
    
    def notify_update_in_progress(self, version: str, progress: float) -> bool:
        """Notify the user that an update is in progress.
        
        Args:
            version: The version being updated to.
            progress: The progress of the update, as a percentage (0-100).
        
        Returns:
            True if the notification was created successfully, False otherwise.
        """
        try:
            # Create notification data
            notification_data = {
                "type": NotificationType.UPDATE_IN_PROGRESS.value,
                "version": version,
                "progress": progress,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Save notification data to flag file
            with open(UPDATE_PROGRESS_FLAG, "w") as f:
                json.dump(notification_data, f, indent=2)
            
            logger.debug(f"Created update in progress notification for version {version} ({progress}%)")
            
            # Try to send notification to GUI via socket
            self._send_notification_to_gui(notification_data)
            
            return True
        except Exception as e:
            logger.error(f"Error creating update in progress notification: {str(e)}")
            return False
    
    def notify_update_result(self, version: str, success: bool, message: str) -> bool:
        """Notify the user about the result of an update.
        
        Args:
            version: The version that was updated to.
            success: Whether the update was successful.
            message: A message describing the result.
        
        Returns:
            True if the notification was created successfully, False otherwise.
        """
        try:
            # Create notification data
            notification_data = {
                "type": NotificationType.UPDATE_COMPLETED.value if success else NotificationType.UPDATE_FAILED.value,
                "version": version,
                "success": success,
                "message": message,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Save notification data to flag file
            with open(UPDATE_RESULT_FLAG, "w") as f:
                json.dump(notification_data, f, indent=2)
            
            logger.info(f"Created update result notification for version {version} (success: {success})")
            
            # Try to send notification to GUI via socket
            self._send_notification_to_gui(notification_data)
            
            return True
        except Exception as e:
            logger.error(f"Error creating update result notification: {str(e)}")
            return False
    
    def notify_rollback_available(self, from_version: str, to_version: str) -> bool:
        """Notify the user that a rollback is available.
        
        Args:
            from_version: The current version.
            to_version: The version to roll back to.
        
        Returns:
            True if the notification was created successfully, False otherwise.
        """
        try:
            # Create notification data
            notification_data = {
                "type": NotificationType.ROLLBACK_AVAILABLE.value,
                "from_version": from_version,
                "to_version": to_version,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Save notification data to a rollback flag file
            rollback_flag_file = NOTIFICATION_DIR / "rollback_available.json"
            with open(rollback_flag_file, "w") as f:
                json.dump(notification_data, f, indent=2)
            
            logger.info(f"Created rollback available notification from {from_version} to {to_version}")
            
            # Try to send notification to GUI via socket
            self._send_notification_to_gui(notification_data)
            
            return True
        except Exception as e:
            logger.error(f"Error creating rollback available notification: {str(e)}")
            return False
    
    def clear_notifications(self, notification_type: Optional[NotificationType] = None) -> None:
        """Clear notifications of the specified type.
        
        Args:
            notification_type: The type of notifications to clear. If None, clear all notifications.
        """
        try:
            if notification_type is None:
                # Clear all notification files
                for file in NOTIFICATION_DIR.glob("*.json"):
                    file.unlink(missing_ok=True)
                logger.info("Cleared all notifications")
            else:
                # Clear specific notification type
                if notification_type == NotificationType.UPDATE_AVAILABLE:
                    UPDATE_NOTIFICATION_FLAG.unlink(missing_ok=True)
                elif notification_type in [NotificationType.UPDATE_SCHEDULED, NotificationType.UPDATE_IN_PROGRESS]:
                    UPDATE_PROGRESS_FLAG.unlink(missing_ok=True)
                elif notification_type in [NotificationType.UPDATE_COMPLETED, NotificationType.UPDATE_FAILED]:
                    UPDATE_RESULT_FLAG.unlink(missing_ok=True)
                elif notification_type == NotificationType.ROLLBACK_AVAILABLE:
                    rollback_flag_file = NOTIFICATION_DIR / "rollback_available.json"
                    rollback_flag_file.unlink(missing_ok=True)
                
                logger.info(f"Cleared {notification_type.value} notifications")
        except Exception as e:
            logger.error(f"Error clearing notifications: {str(e)}")
    
    def _send_notification_to_gui(self, notification_data: Dict[str, Any]) -> bool:
        """Send a notification to the GUI through a socket.
        
        Args:
            notification_data: The notification data to send.
        
        Returns:
            True if the notification was sent successfully, False otherwise.
        """
        if not os.path.exists(self.gui_socket_path):
            logger.debug(f"GUI socket {self.gui_socket_path} not found, skipping direct notification")
            return False
        
        try:
            # Create a Unix socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            
            # Connect to the GUI socket
            sock.connect(self.gui_socket_path)
            
            # Send the notification data
            message = json.dumps({"notification": notification_data}).encode("utf-8")
            sock.sendall(message)
            
            # Close the socket
            sock.close()
            
            logger.debug(f"Sent notification to GUI: {notification_data['type']}")
            return True
        except Exception as e:
            logger.debug(f"Error sending notification to GUI: {str(e)}")
            return False
    
    def check_for_voice_command(self) -> Optional[str]:
        """Check if there's a voice command flag file with a command for OTA.
        
        Returns:
            The voice command as a string, or None if no command found.
        """
        voice_command_file = NOTIFICATION_DIR / "ota_voice_command.txt"
        
        if not voice_command_file.exists():
            return None
        
        try:
            # Read the voice command
            with open(voice_command_file, "r") as f:
                command = f.read().strip()
            
            # Delete the file after reading
            voice_command_file.unlink()
            
            logger.info(f"Received voice command: {command}")
            return command
        except Exception as e:
            logger.error(f"Error reading voice command: {str(e)}")
            return None 