"""
System Backup Module for the OTA daemon.

This module handles creating, managing, and restoring system backups
for the Robot-AI system during OTA updates.
"""

import datetime
import glob
import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger("ota-daemon.backup")

class BackupManager:
    """Manages system backups for the OTA daemon."""
    
    def __init__(self, 
                backup_dir: str = "/backups",
                backup_retention_count: int = 2,
                device_id: str = "UNKNOWN"):
        """Initialize the backup manager.
        
        Args:
            backup_dir: Directory to store backups.
            backup_retention_count: Number of backups to retain.
            device_id: The device ID for backup file naming.
        """
        self.backup_dir = Path(backup_dir)
        self.backup_retention_count = backup_retention_count
        self.device_id = device_id
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Directories and files to include in backup
        self.backup_locations = [
            "/opt/robot-ai",  # Main application
            "/etc/robot-ai",  # Configuration
            "/etc/ota_config.json"  # OTA configuration
        ]
        
        # Directories and files to exclude from backup
        self.exclude_patterns = [
            "*.log",
            "*.tmp",
            "__pycache__",
            ".git",
            "logs",
            "backups/*",
            "models/cv/*",  # Exclude large model files
            "models/voices/*"  # Exclude large voice files
        ]
    
    def create_backup(self, version: str) -> Tuple[bool, str]:
        """Create a system backup before applying an update.
        
        Args:
            version: Current version before the update.
        
        Returns:
            A tuple of (success, message or backup_path).
        """
        try:
            # Generate timestamp for backup filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"robot-ai_backup_{version}_{self.device_id}_{timestamp}.tar.gz"
            backup_path = self.backup_dir / backup_filename
            
            logger.info(f"Creating backup at {backup_path}")
            
            # Create a temporary directory for staging backup content
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                
                # Copy files to backup
                for location in self.backup_locations:
                    src_path = Path(location)
                    
                    if not src_path.exists():
                        logger.warning(f"Backup location {location} does not exist, skipping")
                        continue
                    
                    # Determine destination path in temp directory
                    if src_path.is_file():
                        # For files, create the parent directory structure
                        dest_path = temp_dir_path / src_path.relative_to("/")
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_path, dest_path)
                    else:
                        # For directories, copy the whole structure
                        dest_path = temp_dir_path / src_path.relative_to("/")
                        dest_path.mkdir(parents=True, exist_ok=True)
                        
                        # Use subprocess for more efficient directory copying with exclusions
                        exclude_args = []
                        for pattern in self.exclude_patterns:
                            exclude_args.extend(["--exclude", pattern])
                        
                        cmd = ["rsync", "-a"] + exclude_args + [f"{src_path}/", f"{dest_path}/"]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode != 0:
                            logger.error(f"Error copying {src_path}: {result.stderr}")
                
                # Create tar archive
                with tarfile.open(backup_path, "w:gz") as tar:
                    # Add all files from temp directory to the archive
                    tar.add(temp_dir, arcname="")
            
            # Verify the backup
            if self._verify_backup(backup_path):
                logger.info(f"Backup created successfully: {backup_path}")
                
                # Cleanup old backups
                self._cleanup_old_backups()
                
                return (True, str(backup_path))
            else:
                logger.error(f"Backup verification failed: {backup_path}")
                return (False, "Backup verification failed")
        except Exception as e:
            error_msg = f"Error creating backup: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
    
    def _verify_backup(self, backup_path: Path) -> bool:
        """Verify the integrity of a backup archive.
        
        Args:
            backup_path: Path to the backup archive.
        
        Returns:
            True if the backup is valid, False otherwise.
        """
        try:
            # Check if the file exists and is not empty
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                logger.error(f"Backup file does not exist or is empty: {backup_path}")
                return False
            
            # Try to open and read the tar file
            with tarfile.open(backup_path, "r:gz") as tar:
                # Just check if we can read the tar members
                member_count = sum(1 for _ in tar)
                if member_count == 0:
                    logger.error(f"Backup archive is empty: {backup_path}")
                    return False
                
                logger.debug(f"Backup archive contains {member_count} files")
            
            return True
        except Exception as e:
            logger.error(f"Error verifying backup: {str(e)}")
            return False
    
    def _cleanup_old_backups(self) -> None:
        """Clean up old backups to maintain the retention count."""
        try:
            # Get all backup files sorted by modification time (newest first)
            backup_files = sorted(
                self.backup_dir.glob(f"robot-ai_backup_*_{self.device_id}_*.tar.gz"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Keep only the specified number of backups
            for old_backup in backup_files[self.backup_retention_count:]:
                logger.info(f"Removing old backup: {old_backup}")
                old_backup.unlink()
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
    
    def get_available_backups(self) -> List[Tuple[str, str, datetime.datetime]]:
        """Get a list of available backups.
        
        Returns:
            A list of tuples containing (backup_path, version, timestamp).
        """
        try:
            backups = []
            
            # Find all backup files for this device
            backup_files = sorted(
                self.backup_dir.glob(f"robot-ai_backup_*_{self.device_id}_*.tar.gz"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for backup_file in backup_files:
                try:
                    # Parse version and timestamp from filename
                    # Format: robot-ai_backup_VERSION_DEVICE-ID_TIMESTAMP.tar.gz
                    parts = backup_file.name.split("_")
                    if len(parts) >= 4:
                        version = parts[2]
                        timestamp_str = parts[-1].split(".")[0]  # Remove .tar.gz
                        timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        
                        backups.append((str(backup_file), version, timestamp))
                except Exception as e:
                    logger.error(f"Error parsing backup filename {backup_file.name}: {str(e)}")
            
            return backups
        except Exception as e:
            logger.error(f"Error getting available backups: {str(e)}")
            return []
    
    def restore_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Restore a system backup.
        
        Args:
            backup_path: Path to the backup archive to restore.
        
        Returns:
            A tuple of (success, message).
        """
        backup_path_obj = Path(backup_path)
        
        if not backup_path_obj.exists():
            error_msg = f"Backup file does not exist: {backup_path}"
            logger.error(error_msg)
            return (False, error_msg)
        
        try:
            logger.info(f"Restoring backup from {backup_path}")
            
            # Create a temporary directory for extracting the backup
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                
                # Extract the backup archive
                with tarfile.open(backup_path_obj, "r:gz") as tar:
                    tar.extractall(path=temp_dir_path)
                
                # Restore files from the backup
                for location in self.backup_locations:
                    dest_path = Path(location)
                    src_path = temp_dir_path / dest_path.relative_to("/")
                    
                    if not src_path.exists():
                        logger.warning(f"Backup does not contain {location}, skipping")
                        continue
                    
                    # Remove the destination if it exists
                    if dest_path.exists():
                        if dest_path.is_file():
                            dest_path.unlink()
                        else:
                            # Only remove directory contents, not the directory itself
                            for item in dest_path.glob("*"):
                                if item.is_file():
                                    item.unlink()
                                else:
                                    shutil.rmtree(item)
                    else:
                        # Create destination directory if it doesn't exist
                        if dest_path.parent.exists():
                            dest_path.mkdir(parents=True, exist_ok=True)
                    
                    # Copy files from backup to destination
                    if src_path.is_file():
                        # For files, copy the file
                        shutil.copy2(src_path, dest_path)
                    else:
                        # For directories, use rsync for efficient copying
                        cmd = ["rsync", "-a", f"{src_path}/", f"{dest_path}/"]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode != 0:
                            logger.error(f"Error restoring {src_path} to {dest_path}: {result.stderr}")
            
            logger.info(f"Backup restored successfully from {backup_path}")
            return (True, f"Backup restored successfully from {backup_path}")
        except Exception as e:
            error_msg = f"Error restoring backup: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
    
    def get_latest_backup(self) -> Optional[str]:
        """Get the path to the latest backup file.
        
        Returns:
            The path to the latest backup file, or None if no backups are available.
        """
        try:
            # Get all backup files sorted by modification time (newest first)
            backup_files = sorted(
                self.backup_dir.glob(f"robot-ai_backup_*_{self.device_id}_*.tar.gz"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if not backup_files:
                logger.warning("No backup files found")
                return None
            
            latest_backup = backup_files[0]
            logger.debug(f"Latest backup: {latest_backup}")
            return str(latest_backup)
        except Exception as e:
            logger.error(f"Error getting latest backup: {str(e)}")
            return None 