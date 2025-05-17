"""
Integration tests for the OTA daemon.

These tests verify the functionality of multiple components working together
using a mock update server.
"""

import json
import os
import shutil
import tempfile
import threading
import time
import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from unittest.mock import patch, Mock

# Import the modules we need to test
from OTA.daemon.network.ota_client import OTAClient
from OTA.daemon.backup.system_backup import BackupManager
from OTA.daemon.update.update_manager import UpdateManager
from OTA.daemon.scheduler.task_scheduler import TaskScheduler, Task


# Define a mock HTTP server for testing
class MockOTAServer(BaseHTTPRequestHandler):
    """Mock OTA server for testing."""
    
    # Server configuration
    manifest = {
        "version": "1.1.0",
        "product_type": "robot-a",
        "severity": "regular",
        "release_notes": "Test release notes",
        "features": "Test features",
        "files": [
            {
                "path": "/updates/test_file.txt",
                "destination": "/opt/robot-ai/test_file.txt",
                "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "size_bytes": 1024,
                "executable": False
            }
        ]
    }
    
    # Test update file content
    update_content = b"This is a test update file."
    
    def do_GET(self):
        """Handle GET requests."""
        # Return manifest
        if self.path == "/api/update/manifest" or self.path == "/api/update/manifest/robot-a":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.manifest).encode("utf-8"))
        
        # Return update file
        elif self.path == "/updates/test_file.txt":
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(self.update_content)
        
        # Not found
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests."""
        # Update report endpoint
        if self.path == "/api/update/report":
            # Read the request body
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode("utf-8"))
        
        # Not found
        else:
            self.send_response(404)
            self.end_headers()


class TestOTAIntegration(unittest.TestCase):
    """Integration tests for the OTA daemon."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for all tests."""
        # Start the mock server
        cls.server = HTTPServer(("localhost", 8000), MockOTAServer)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Wait for server to start
        time.sleep(0.1)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Stop the mock server
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join()
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Create temporary directories
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create directories for the test
        self.backup_dir = self.test_dir / "backups"
        self.downloads_dir = self.test_dir / "downloads"
        self.application_dir = self.test_dir / "opt" / "robot-ai"
        
        # Create the directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.application_dir.mkdir(parents=True, exist_ok=True)
        
        # Create initial test file in application dir
        with open(self.application_dir / "test_file.txt", "w") as f:
            f.write("Initial content")
        
        # Create OTA client
        self.ota_client = OTAClient(
            server_url="http://localhost:8000/api/update",
            product_type="robot-a",
            device_id="TEST-DEVICE-123"
        )
        
        # Create backup manager
        self.backup_manager = BackupManager(
            backup_dir=str(self.backup_dir),
            backup_retention_count=2,
            device_id="TEST-DEVICE-123"
        )
        
        # Create update manager
        self.update_manager = UpdateManager(
            network_client=self.ota_client,
            backup_manager=self.backup_manager
        )
        self.update_manager.temp_dir = self.downloads_dir
        
        # Create scheduler
        self.scheduler = TaskScheduler()
    
    def tearDown(self):
        """Clean up after each test."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_end_to_end_update_flow(self):
        """Test the end-to-end update process."""
        # 1. Check for updates
        self.assertTrue(self.ota_client.check_network())
        
        # 2. Fetch manifest
        manifest = self.ota_client.fetch_manifest()
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["version"], "1.1.0")
        
        # 3. Download update file
        download_path = self.downloads_dir / "test_file.txt"
        success, message = self.ota_client.download_file(
            "/updates/test_file.txt", 
            download_path
        )
        self.assertTrue(success)
        self.assertTrue(download_path.exists())
        
        # Verify file content
        with open(download_path, "rb") as f:
            content = f.read()
        self.assertEqual(content, MockOTAServer.update_content)
        
        # 4. Create backup
        success, backup_path = self.backup_manager.create_backup("1.0.0")
        self.assertTrue(success)
        self.assertTrue(Path(backup_path).exists())
        
        # 5. Apply update
        update_files = [{
            "source_path": str(download_path),
            "destination": str(self.application_dir / "test_file.txt"),
            "executable": False
        }]
        
        success, message = self.update_manager.apply_updates(update_files)
        self.assertTrue(success)
        
        # Verify the update was applied
        with open(self.application_dir / "test_file.txt", "rb") as f:
            content = f.read()
        self.assertEqual(content, MockOTAServer.update_content)
        
        # 6. Report update status
        success = self.ota_client.report_update_status(
            version="1.1.0",
            status="success",
            message="Update completed successfully"
        )
        self.assertTrue(success)
    
    def test_scheduled_update(self):
        """Test scheduling an update."""
        # Create a mock update function
        update_executed = threading.Event()
        
        def update_callback(version, update_files):
            self.assertEqual(version, "1.1.0")
            self.assertEqual(len(update_files), 1)
            update_executed.set()
        
        # Schedule an immediate update (no schedule_time)
        task = Task(
            name="update_install_1_1_0",
            callback=update_callback,
            schedule_time=None,  # Immediate execution
            kwargs={
                "version": "1.1.0",
                "update_files": ["/updates/test_file.txt"]
            }
        )
        
        self.scheduler.add_task(task)
        
        # Start the scheduler
        self.scheduler.start()
        
        # Wait for the update to be executed (with timeout)
        update_executed.wait(timeout=1)
        
        # Verify that the update was executed
        self.assertTrue(update_executed.is_set())
        
        # Stop the scheduler
        self.scheduler.stop()
    
    def test_rollback(self):
        """Test the rollback process."""
        # Create a backup
        original_content = "Original content"
        with open(self.application_dir / "test_file.txt", "w") as f:
            f.write(original_content)
        
        success, backup_path = self.backup_manager.create_backup("1.0.0")
        self.assertTrue(success)
        
        # Apply a "bad" update
        with open(self.application_dir / "test_file.txt", "w") as f:
            f.write("Bad update content")
        
        # Perform rollback
        success, message = self.backup_manager.restore_backup(backup_path)
        self.assertTrue(success)
        
        # Verify the rollback restored the original content
        with open(self.application_dir / "test_file.txt", "r") as f:
            content = f.read()
        self.assertEqual(content, original_content)


if __name__ == "__main__":
    unittest.main() 