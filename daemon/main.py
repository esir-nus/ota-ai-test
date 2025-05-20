#!/usr/bin/env python3
"""
Robot-AI OTA Daemon - Main Service

This is the main entry point for the OTA daemon that manages the update lifecycle
for the Robot-AI system on Raspberry Pi.
"""

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any
import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("robot-ai-ota.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ota-daemon")

# Import OTA daemon modules
from core.config_manager import ConfigManager
from utils.device_identifier import get_device_id
from network.ota_client import OTAClient
from scheduler.task_scheduler import TaskScheduler, Task
from backup.system_backup import BackupManager
from notification.user_notification import NotificationSystem, UpdateSeverity
from voice.command_processor import CommandProcessor, OTACommandType
from gui.gui_interface import GUIInterface

class OTADaemon:
    """Main OTA daemon class that orchestrates the update lifecycle."""
    
    def __init__(self, config_path="/etc/ota_config.json"):
        """Initialize the OTA daemon with the given configuration."""
        self.running = False
        self.config_path = config_path
        logger.info("Initializing OTA daemon")
        
        # Load configuration
        self.config_manager = ConfigManager(config_path=config_path)
        
        # Get device ID
        device_id = self.config_manager.device_id
        if not device_id:
            device_id = get_device_id()
            self.config_manager.device_id = device_id
        
        # Initialize GUI interface
        self.gui_interface = GUIInterface(
            socket_path=self.config_manager.gui_socket_path
        )
        self._setup_gui_handlers()
        
        # Initialize components
        self.ota_client = OTAClient(
            server_url=self.config_manager.update_server,
            product_type=self.config_manager.product_type,
            device_id=device_id
        )
        
        self.scheduler = TaskScheduler()
        
        self.backup_manager = BackupManager(
            backup_dir="/backups",
            backup_retention_count=self.config_manager.backup_retention_count,
            device_id=device_id
        )
        
        self.notification_system = NotificationSystem(
            gui_interface=self.gui_interface
        )
        
        self.command_processor = CommandProcessor()
        
        # Set up scheduled tasks
        self._setup_scheduled_tasks()
    
    def _setup_gui_handlers(self):
        """Set up command handlers for GUI communication."""
        # Register command handlers
        self.gui_interface.register_command_handler("check_now", self._handle_check_now)
        self.gui_interface.register_command_handler("install_now", self._handle_install_now)
        self.gui_interface.register_command_handler("get_status", self._handle_get_status)
        self.gui_interface.register_command_handler("get_version", self._handle_get_version)
        self.gui_interface.register_command_handler("connectivity_check", self._handle_connectivity_check)
        
        # Set status callback
        self.gui_interface.set_status_callback(self._handle_status_update)
        
        # Start the interface
        self.gui_interface.start()
    
    def _handle_check_now(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle immediate update check request from GUI."""
        manifest = self.check_for_updates()
        if manifest:
            return {
                "message": "Update check completed",
                "manifest": manifest,
                "update_available": self.config_manager.update_available,
                "current_version": self.config_manager.version,
                "available_version": self.config_manager.available_version,
            }
        else:
            return {"message": "Update check failed", "manifest": None}
    
    def _handle_install_now(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle immediate update installation request from GUI."""
        self._schedule_update(None)  # Schedule for immediate execution
        return {"message": "Update installation initiated"}
    
    def _handle_get_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status request from GUI."""
        return {
            "version": self.config_manager.version,
            "product_type": self.config_manager.product_type,
            "update_server": self.config_manager.update_server,
            "last_check": self.config_manager.last_check_time,
            "update_available": self.config_manager.update_available,
            "scheduled_update": self.scheduler.get_next_update_time()
        }
    
    def _handle_get_version(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle version request from GUI."""
        return {
            "current_version": self.config_manager.version,
            "available_version": self.config_manager.available_version
        }
    
    def _handle_status_update(self, status_data: Dict[str, Any]):
        """Handle sending status updates to GUI."""
        # This will be called by other components to update the GUI
        pass
    
    def _handle_connectivity_check(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle connectivity check request from GUI."""
        logger.info("Running connectivity check")
        
        # Check network connectivity
        network_status = self.ota_client.check_network()
        
        # Try to fetch manifest
        manifest_status = False
        if network_status:
            manifest = self.ota_client.fetch_manifest()
            manifest_status = manifest is not None
        
        # Check download capability
        download_status = False
        if network_status and manifest_status:
            try:
                # Create a test directory for downloads
                test_dir = Path("/tmp/ota-test")
                test_dir.mkdir(exist_ok=True)
                
                # Set download test path based on server type
                server_url = self.config_manager.update_server
                using_mock_server = "localhost" in server_url or "127.0.0.1" in server_url
                
                if using_mock_server:
                    test_file_path = "health"
                else:
                    test_file_path = "test/test.txt"
                
                # Try to download
                local_path = test_dir / "test_download.txt"
                success, _ = self.ota_client.download_file(test_file_path, local_path)
                download_status = success
                
                # Clean up
                if local_path.exists():
                    local_path.unlink()
                if test_dir.exists():
                    try:
                        test_dir.rmdir()
                    except:
                        pass
            except Exception as e:
                logger.error(f"Error during download test: {str(e)}")
                download_status = False
        
        return {
            "network_status": network_status,
            "manifest_status": manifest_status,
            "download_status": download_status,
            "server_url": self.config_manager.update_server,
            "product_type": self.config_manager.product_type,
            "device_id": self.config_manager.device_id
        }
    
    def _setup_scheduled_tasks(self):
        """Set up the scheduled tasks for the OTA daemon."""
        # Add update check tasks
        self.scheduler.add_update_check_tasks(
            check_times=self.config_manager.update_check_times,
            check_callback=self.check_for_updates
        )
        
        # Add voice command check task (runs every minute)
        self.scheduler.add_task(Task(
            name="voice_command_check",
            callback=self.check_voice_commands,
            schedule_time=None  # Run immediately and then every 10 seconds in the main loop
        ))
    
    def start(self):
        """Start the OTA daemon and run the main loop."""
        logger.info("Starting OTA daemon")
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
        
        # Start the scheduler
        self.scheduler.start()
        
        # Start the GUI interface
        self.gui_interface.start()
        
        try:
            # Main daemon loop
            while self.running:
                # Check for voice commands
                self.check_voice_commands()
                
                # Sleep to avoid CPU thrashing
                time.sleep(10)
        except Exception as e:
            logger.exception("Error in main loop: %s", str(e))
        finally:
            self.stop()
    
    def stop(self):
        """Stop the OTA daemon gracefully."""
        logger.info("Stopping OTA daemon")
        self.running = False
        
        # Stop the scheduler
        if hasattr(self, 'scheduler'):
            self.scheduler.stop()
        
        # Stop the GUI interface
        if hasattr(self, 'gui_interface'):
            self.gui_interface.stop()
    
    def handle_signal(self, signum, frame):
        """Handle termination signals to stop the daemon gracefully."""
        logger.info("Received signal %d, stopping daemon", signum)
        self.stop()
    
    def check_for_updates(self):
        """Check for available updates from the OTA server.
        
        Returns:
            The manifest dictionary if successfully fetched, None otherwise.
        """
        logger.info("Checking for updates")
        
        # Check network connectivity
        if not self.ota_client.check_network():
            logger.error("Network not available, skipping update check")
            return None
        
        # Fetch manifest from server
        manifest = self.ota_client.fetch_manifest()
        if not manifest:
            logger.error("Failed to fetch manifest, skipping update check")
            return None
        
        # Get current version
        current_version = self.config_manager.version
        
        # Check if update is available
        if manifest["version"] == current_version:
            logger.info(f"No update available (current version: {current_version})")
            # Update last check time
            self.config_manager.last_check_time = datetime.datetime.now().isoformat()
            self.config_manager.update_available = False
            self.config_manager.available_version = None
            return manifest
        
        # Update configuration
        self.config_manager.last_check_time = datetime.datetime.now().isoformat()
        self.config_manager.update_available = True
        self.config_manager.available_version = manifest["version"]
        
        # Determine update severity
        severity = UpdateSeverity.REGULAR
        if "severity" in manifest:
            try:
                severity = UpdateSeverity(manifest["severity"])
            except ValueError:
                logger.warning(f"Unknown severity: {manifest['severity']}, using REGULAR")
        
        # Extract release notes and features
        release_notes = manifest.get("release_notes", "No release notes available.")
        features = manifest.get("features", "Update available")
        
        # Calculate update size
        update_size_mb = 0
        for file_info in manifest.get("files", []):
            update_size_mb += file_info.get("size_bytes", 0) / (1024 * 1024)
        
        # Create update notification
        self.notification_system.notify_update_available(
            version=manifest["version"],
            severity=severity,
            features=features,
            release_notes=release_notes,
            size_mb=update_size_mb
        )
        
        logger.info(f"Update available: {current_version} -> {manifest['version']}")
        return manifest
    
    def check_voice_commands(self):
        """Check for voice commands related to OTA operations."""
        command_text = self.notification_system.check_for_voice_command()
        if not command_text:
            return
        
        # Process the command
        command_type, additional_info = self.command_processor.process_command(command_text)
        
        if command_type == OTACommandType.INSTALL_TONIGHT:
            self._schedule_update("03:00")
        elif command_type == OTACommandType.INSTALL_NOW:
            self._schedule_update(None)  # Schedule for immediate execution
        elif command_type == OTACommandType.ROLLBACK:
            self._prepare_rollback()
        elif command_type == OTACommandType.CANCEL_UPDATE:
            self._cancel_update()
        elif command_type == OTACommandType.UNKNOWN and additional_info == "confirmation":
            self._handle_confirmation()
    
    def _schedule_update(self, scheduled_time):
        """Schedule an update for the specified time.
        
        Args:
            scheduled_time: The time to schedule the update for (HH:MM), or None for immediate.
        """
        # Fetch manifest to get update details
        manifest = self.ota_client.fetch_manifest()
        if not manifest:
            logger.error("Failed to fetch manifest, cannot schedule update")
            return
        
        # Verify disk space
        if not self._check_disk_space(manifest):
            logger.error("Insufficient disk space for update")
            self.notification_system.notify_update_result(
                version=manifest["version"],
                success=False,
                message="Update failed: Insufficient disk space"
            )
            return
        
        # Schedule the update
        if scheduled_time:
            logger.info(f"Scheduling update to version {manifest['version']} at {scheduled_time}")
            
            # Add scheduled update task
            self.scheduler.schedule_update(
                update_time=scheduled_time,
                update_callback=self._apply_update,
                version=manifest["version"],
                update_files=manifest.get("files", [])
            )
            
            # Notify user
            self.notification_system.notify_update_scheduled(
                version=manifest["version"],
                scheduled_time=scheduled_time
            )
        else:
            # Execute update immediately
            logger.info(f"Executing update to version {manifest['version']} immediately")
            
            # Notify user
            self.notification_system.notify_update_in_progress(
                version=manifest["version"],
                progress=0.0
            )
            
            # Apply update
            self._apply_update(
                version=manifest["version"],
                update_files=manifest.get("files", [])
            )
    
    def _apply_update(self, version, update_files):
        """Apply an update.
        
        Args:
            version: The version to update to.
            update_files: List of files to update.
        """
        current_version = self.config_manager.version
        logger.info(f"Applying update from {current_version} to {version}")
        
        try:
            # Notify update in progress
            self.notification_system.notify_update_in_progress(
                version=version,
                progress=10.0
            )
            
            # Create backup
            logger.info("Creating backup before update")
            success, backup_result = self.backup_manager.create_backup(current_version)
            if not success:
                error_msg = f"Backup failed: {backup_result}"
                logger.error(error_msg)
                self.notification_system.notify_update_result(
                    version=version,
                    success=False,
                    message=error_msg
                )
                return
            
            # Backup created successfully
            logger.info(f"Backup created: {backup_result}")
            
            # Disable peripherals
            self._disable_peripherals()
            
            # Notify progress
            self.notification_system.notify_update_in_progress(
                version=version,
                progress=30.0
            )
            
            # Download update files
            logger.info("Downloading update files")
            for i, file_info in enumerate(update_files):
                remote_path = file_info["path"]
                local_path = Path(file_info["destination"])
                checksum = file_info.get("checksum")
                
                # Download the file
                success, message = self.ota_client.download_file(remote_path, local_path)
                if not success:
                    error_msg = f"Download failed: {message}"
                    logger.error(error_msg)
                    self.notification_system.notify_update_result(
                        version=version,
                        success=False,
                        message=error_msg
                    )
                    return
                
                # Verify checksum if provided
                if checksum and not self.ota_client.verify_file(local_path, checksum):
                    error_msg = f"Checksum verification failed for {local_path}"
                    logger.error(error_msg)
                    self.notification_system.notify_update_result(
                        version=version,
                        success=False,
                        message=error_msg
                    )
                    return
                
                # Update progress (30% - 80%)
                progress = 30.0 + (50.0 * (i + 1) / len(update_files))
                self.notification_system.notify_update_in_progress(
                    version=version,
                    progress=progress
                )
            
            # Update complete, notify progress
            self.notification_system.notify_update_in_progress(
                version=version,
                progress=100.0
            )
            
            # Update version in configuration
            self.config_manager.version = version
            
            # Report success to server
            self.ota_client.report_update_status(
                version=version,
                status="success",
                message="Update completed successfully"
            )
            
            # Notify user
            self.notification_system.notify_update_result(
                version=version,
                success=True,
                message="Update completed successfully"
            )
            
            logger.info(f"Update to version {version} completed successfully")
            
            # Restart system if needed
            # TODO: Implement system restart
        except Exception as e:
            error_msg = f"Update failed: {str(e)}"
            logger.error(error_msg)
            
            # Report failure to server
            self.ota_client.report_update_status(
                version=version,
                status="failed",
                message=error_msg
            )
            
            # Notify user
            self.notification_system.notify_update_result(
                version=version,
                success=False,
                message=error_msg
            )
    
    def _prepare_rollback(self):
        """Prepare for a rollback operation."""
        latest_backup = self.backup_manager.get_latest_backup()
        if not latest_backup:
            logger.error("No backup available for rollback")
            # Notify user
            self.notification_system.notify_update_result(
                version=self.config_manager.version,
                success=False,
                message="Rollback failed: No backup available"
            )
            return
        
        # Get backup details
        backups = self.backup_manager.get_available_backups()
        if not backups:
            logger.error("Error getting backup details")
            return
        
        backup_path, backup_version, timestamp = backups[0]
        
        # Notify user about rollback availability
        self.notification_system.notify_rollback_available(
            from_version=self.config_manager.version,
            to_version=backup_version
        )
        
        logger.info(f"Rollback prepared: {self.config_manager.version} -> {backup_version}")
    
    def _handle_confirmation(self):
        """Handle confirmation for rollback or other pending operations."""
        # Check if rollback is pending
        rollback_flag = Path("/var/lib/robot-ai/notifications/rollback_available.json")
        if rollback_flag.exists():
            self._execute_rollback()
    
    def _execute_rollback(self):
        """Execute a rollback operation."""
        latest_backup = self.backup_manager.get_latest_backup()
        if not latest_backup:
            logger.error("No backup available for rollback")
            return
        
        logger.info(f"Executing rollback using backup: {latest_backup}")
        
        try:
            # Disable peripherals
            self._disable_peripherals()
            
            # Perform rollback
            success, message = self.backup_manager.restore_backup(latest_backup)
            
            if success:
                logger.info("Rollback completed successfully")
                
                # Get version from backup
                backups = self.backup_manager.get_available_backups()
                if backups:
                    _, backup_version, _ = backups[0]
                    # Update version in configuration
                    self.config_manager.version = backup_version
                
                # Notify user
                self.notification_system.notify_update_result(
                    version=self.config_manager.version,
                    success=True,
                    message="Rollback completed successfully"
                )
                
                # Restart system if needed
                # TODO: Implement system restart
            else:
                logger.error(f"Rollback failed: {message}")
                
                # Notify user
                self.notification_system.notify_update_result(
                    version=self.config_manager.version,
                    success=False,
                    message=f"Rollback failed: {message}"
                )
        except Exception as e:
            error_msg = f"Rollback failed: {str(e)}"
            logger.error(error_msg)
            
            # Notify user
            self.notification_system.notify_update_result(
                version=self.config_manager.version,
                success=False,
                message=error_msg
            )
    
    def _cancel_update(self):
        """Cancel a scheduled update."""
        # Find and remove scheduled update tasks
        update_tasks = [name for name in self.scheduler.tasks.keys() if name.startswith("update_install_")]
        
        if not update_tasks:
            logger.info("No update scheduled to cancel")
            return
        
        for task_name in update_tasks:
            self.scheduler.remove_task(task_name)
        
        logger.info(f"Cancelled scheduled update tasks: {len(update_tasks)}")
        
        # Clear update notifications
        self.notification_system.clear_notifications()
    
    def _check_disk_space(self, manifest):
        """Check if there is enough disk space for the update.
        
        Args:
            manifest: The update manifest.
        
        Returns:
            True if there is enough disk space, False otherwise.
        """
        import shutil
        
        # Calculate required space (update size + backup size + buffer)
        required_mb = 0
        
        # Update size
        for file_info in manifest.get("files", []):
            required_mb += file_info.get("size_bytes", 0) / (1024 * 1024)
        
        # Backup size (estimate as 500MB)
        required_mb += 500
        
        # Buffer (100MB)
        required_mb += 100
        
        # Check available space in /
        _, _, free = shutil.disk_usage("/")
        free_mb = free / (1024 * 1024)
        
        logger.info(f"Disk space check: required={required_mb:.2f}MB, available={free_mb:.2f}MB")
        
        return free_mb >= required_mb
    
    def _disable_peripherals(self):
        """Disable peripherals during update to avoid conflicts."""
        logger.info("Disabling peripherals during update")
        
        # TODO: Implement proper peripheral disabling
        # For now, just log the intent
        
        # Example: Stop GUI service
        # subprocess.run(["systemctl", "stop", "robot-ai-gui.service"])
        
        # Example: Disable microphone
        # subprocess.run(["amixer", "set", "Capture", "nocap"])
        
        pass

def main():
    """Run the OTA daemon."""
    parser = argparse.ArgumentParser(description="OTA Daemon for robot-ai")
    parser.add_argument("--config", default="/etc/ota_config.json",
                       help="Path to configuration file")
    parser.add_argument("--simulation", action="store_true",
                       help="Use simulation mode with local mock server")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set log level based on verbosity flag
    if args.verbose:
        logging.getLogger("ota-daemon").setLevel(logging.DEBUG)
    
    try:
        daemon = OTADaemon(config_path=args.config)
        
        # Set simulation mode if specified
        if args.simulation:
            daemon.config_manager.is_simulation_mode = True
            logger.info(f"Running in simulation mode, using server: {daemon.config_manager.update_server}")
        
        daemon.start()
    except Exception as e:
        logger.error(f"Error starting OTA daemon: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    main() 