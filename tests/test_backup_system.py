"""
Unit tests for the BackupManager component.

These tests verify the functionality of the backup system using mocks
to avoid actual file system operations.
"""

import unittest
from unittest.mock import patch, Mock, MagicMock, mock_open, call
import tempfile
import tarfile
import shutil
import subprocess
import os
import datetime
from pathlib import Path

from OTA.daemon.backup.system_backup import BackupManager

class TestBackupManager(unittest.TestCase):
    """Test cases for the BackupManager class."""
    
    def setUp(self):
        """Set up test fixtures for BackupManager tests."""
        # Create a temporary directory for backup operations
        self.temp_dir = tempfile.TemporaryDirectory()
        self.backup_dir = Path(self.temp_dir.name) / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the backup manager
        self.backup_manager = BackupManager(
            backup_dir=str(self.backup_dir),
            backup_retention_count=2,
            device_id="TEST-DEVICE-123"
        )
    
    def tearDown(self):
        """Clean up test fixtures after tests."""
        self.temp_dir.cleanup()
    
    @patch('OTA.daemon.backup.system_backup.tarfile.open')
    @patch('OTA.daemon.backup.system_backup.tempfile.TemporaryDirectory')
    @patch('OTA.daemon.backup.system_backup.subprocess.run')
    @patch('OTA.daemon.backup.system_backup.Path')
    def test_create_backup(self, mock_path, mock_subprocess, mock_temp_dir, mock_tarfile):
        """Test creating a backup."""
        # Mock the temporary directory
        mock_temp_dir_instance = MagicMock()
        mock_temp_dir_instance.__enter__.return_value = "/temp/dir"
        mock_temp_dir.return_value = mock_temp_dir_instance
        
        # Mock subprocess run for rsync
        mock_subprocess.return_value.returncode = 0
        
        # Mock Path operations
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.is_file.side_effect = [False, False]  # Directories
        
        # Mock tarfile operations
        mock_tar = MagicMock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar
        
        # Mock _verify_backup
        self.backup_manager._verify_backup = Mock(return_value=True)
        
        # Mock _cleanup_old_backups
        self.backup_manager._cleanup_old_backups = Mock()
        
        # Call create_backup
        success, result = self.backup_manager.create_backup("1.0.0")
        
        # Verify results
        self.assertTrue(success)
        self.assertIn("robot-ai_backup_1.0.0_TEST-DEVICE-123", result)
        
        # Verify that the backup creation process was correctly executed
        mock_temp_dir.assert_called_once()
        mock_subprocess.assert_called()
        mock_tar.add.assert_called_once_with("/temp/dir", arcname="")
        self.backup_manager._verify_backup.assert_called_once()
        self.backup_manager._cleanup_old_backups.assert_called_once()
    
    def test_verify_backup(self):
        """Test backup verification."""
        # Create a mock backup file
        mock_backup_path = Mock()
        mock_backup_path.exists.return_value = True
        mock_backup_path.stat.return_value.st_size = 1024  # Non-zero size
        
        # Create a mock tarfile
        with patch('OTA.daemon.backup.system_backup.tarfile.open') as mock_tarfile:
            mock_tar = MagicMock()
            mock_tarfile.return_value.__enter__.return_value = mock_tar
            
            # Mock reading tar members to return 5 members
            mock_tar.__iter__.return_value = range(5)
            
            # Test verification
            result = self.backup_manager._verify_backup(mock_backup_path)
            self.assertTrue(result)
            
            # Test verification of empty archive
            mock_tar.__iter__.return_value = range(0)
            result = self.backup_manager._verify_backup(mock_backup_path)
            self.assertFalse(result)
            
            # Test verification of non-existent file
            mock_backup_path.exists.return_value = False
            result = self.backup_manager._verify_backup(mock_backup_path)
            self.assertFalse(result)
    
    @patch('OTA.daemon.backup.system_backup.Path.glob')
    @patch('OTA.daemon.backup.system_backup.Path.unlink')
    def test_cleanup_old_backups(self, mock_unlink, mock_glob):
        """Test cleanup of old backups."""
        # Create mock backup files (sorted by modification time, newest first)
        mock_backups = [
            MagicMock(stat=lambda: MagicMock(st_mtime=100)),  # Newest
            MagicMock(stat=lambda: MagicMock(st_mtime=90)),   # Second newest
            MagicMock(stat=lambda: MagicMock(st_mtime=80)),   # Will be deleted
            MagicMock(stat=lambda: MagicMock(st_mtime=70))    # Will be deleted
        ]
        
        mock_glob.return_value = mock_backups
        
        # Call cleanup
        self.backup_manager._cleanup_old_backups()
        
        # Verify that only old backups were deleted (retention count is 2)
        self.assertEqual(mock_unlink.call_count, 2)
        mock_unlink.assert_has_calls([call(), call()])
    
    @patch('OTA.daemon.backup.system_backup.Path.glob')
    def test_get_available_backups(self, mock_glob):
        """Test retrieval of available backups."""
        # Create mock backup files with their timestamps
        test_date = datetime.datetime(2023, 5, 15, 10, 30, 0)
        date_str = test_date.strftime("%Y%m%d_%H%M%S")
        
        backup1 = MagicMock(
            name=f"robot-ai_backup_1.0.0_TEST-DEVICE-123_{date_str}.tar.gz",
            stat=lambda: MagicMock(st_mtime=100)
        )
        backup2 = MagicMock(
            name=f"robot-ai_backup_0.9.0_TEST-DEVICE-123_20230510_093000.tar.gz",
            stat=lambda: MagicMock(st_mtime=90)
        )
        
        mock_glob.return_value = [backup1, backup2]
        
        # Get available backups
        backups = self.backup_manager.get_available_backups()
        
        # Verify results
        self.assertEqual(len(backups), 2)
        
        # First backup details
        self.assertEqual(backups[0][1], "1.0.0")  # Version
        self.assertEqual(backups[0][2], test_date)  # Timestamp
        
        # Second backup details
        self.assertEqual(backups[1][1], "0.9.0")  # Version
        self.assertEqual(backups[1][2].year, 2023)
        self.assertEqual(backups[1][2].month, 5)
        self.assertEqual(backups[1][2].day, 10)
    
    @patch('OTA.daemon.backup.system_backup.tarfile.open')
    @patch('OTA.daemon.backup.system_backup.tempfile.TemporaryDirectory')
    @patch('OTA.daemon.backup.system_backup.subprocess.run')
    @patch('OTA.daemon.backup.system_backup.Path')
    @patch('OTA.daemon.backup.system_backup.shutil')
    def test_restore_backup(self, mock_shutil, mock_path, mock_subprocess, 
                           mock_temp_dir, mock_tarfile):
        """Test backup restoration."""
        # Mock the backup path
        mock_backup_path = MagicMock()
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.is_file.side_effect = [False, True]  # Directory then file
        
        # Mock the temporary directory
        mock_temp_dir_instance = MagicMock()
        mock_temp_dir_instance.__enter__.return_value = "/temp/dir"
        mock_temp_dir.return_value = mock_temp_dir_instance
        
        # Mock tarfile operations
        mock_tar = MagicMock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar
        
        # Mock subprocess run for rsync
        mock_subprocess.return_value.returncode = 0
        
        # Call restore_backup
        success, message = self.backup_manager.restore_backup("/path/to/backup.tar.gz")
        
        # Verify results
        self.assertTrue(success)
        self.assertIn("Backup restored successfully", message)
        
        # Verify that the restoration process was correctly executed
        mock_tarfile.assert_called_once()
        mock_tar.extractall.assert_called_once()
        mock_subprocess.assert_called()
    
    @patch('OTA.daemon.backup.system_backup.Path.glob')
    def test_get_latest_backup(self, mock_glob):
        """Test retrieval of the latest backup."""
        # Create mock backup files (sorted by modification time, newest first)
        mock_backups = [
            MagicMock(stat=lambda: MagicMock(st_mtime=100)),  # Newest
            MagicMock(stat=lambda: MagicMock(st_mtime=90))    # Second newest
        ]
        
        mock_glob.return_value = mock_backups
        
        # Get latest backup
        latest = self.backup_manager.get_latest_backup()
        
        # Verify that the newest backup was returned
        self.assertEqual(latest, str(mock_backups[0]))
        
        # Test with no backups
        mock_glob.return_value = []
        latest = self.backup_manager.get_latest_backup()
        self.assertIsNone(latest)


if __name__ == '__main__':
    unittest.main() 