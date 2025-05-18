"""
Tests for the GUI communication interface.
"""

import json
import os
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from typing import Dict, Any

from daemon.gui.gui_interface import GUIInterface

class TestGUIInterface(unittest.TestCase):
    """Test cases for the GUI interface."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for the socket
        self.temp_dir = tempfile.TemporaryDirectory()
        self.socket_path = Path(self.temp_dir.name) / "test.sock"
        
        # Create the GUI interface
        self.gui = GUIInterface(socket_path=str(self.socket_path))
        
        # Start the interface
        self.gui.start()
        
        # Give it time to start
        time.sleep(0.1)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.gui.stop()
        self.temp_dir.cleanup()
    
    def test_command_handling(self):
        """Test handling of GUI commands."""
        # Register a test command handler
        test_result = {"called": False, "params": None}
        
        def test_handler(params):
            test_result["called"] = True
            test_result["params"] = params
            return {"status": "ok"}
        
        self.gui.register_command_handler("test_command", test_handler)
        
        # Create a client socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(self.socket_path))
        
        # Send a test command
        command_data = {
            "command": "test_command",
            "parameters": {"test": "value"}
        }
        sock.sendall(json.dumps(command_data).encode("utf-8"))
        
        # Receive response
        response = sock.recv(4096).decode("utf-8")
        response_data = json.loads(response)
        
        # Close the socket
        sock.close()
        
        # Verify the handler was called
        self.assertTrue(test_result["called"])
        self.assertEqual(test_result["params"], {"test": "value"})
        self.assertEqual(response_data["status"], "success")
    
    def test_status_updates(self):
        """Test sending status updates."""
        # Create a test client
        received_updates = []
        client_ready = threading.Event()
        
        def client_thread():
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(str(self.socket_path))
            client_ready.set()
            
            while True:
                try:
                    data = sock.recv(4096)
                    if not data:
                        break
                    received_updates.append(json.loads(data.decode("utf-8")))
                except:
                    break
            
            sock.close()
        
        # Start client thread
        client = threading.Thread(target=client_thread)
        client.daemon = True
        client.start()
        
        # Wait for client to connect
        client_ready.wait(timeout=1.0)
        
        # Send a test status update
        test_status = {"status": "test", "value": 123}
        self.gui.send_status_update(test_status)
        
        # Give it time to process
        time.sleep(0.1)
        
        # Verify the update was received
        self.assertEqual(len(received_updates), 1)
        self.assertEqual(received_updates[0]["status"], "test")
        self.assertEqual(received_updates[0]["value"], 123)
    
    def test_invalid_command(self):
        """Test handling of invalid commands."""
        # Create a client socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(self.socket_path))
        
        # Send an invalid command
        command_data = {
            "command": "nonexistent_command",
            "parameters": {}
        }
        sock.sendall(json.dumps(command_data).encode("utf-8"))
        
        # Receive response
        response = sock.recv(4096).decode("utf-8")
        response_data = json.loads(response)
        
        # Close the socket
        sock.close()
        
        # Verify error response
        self.assertEqual(response_data["status"], "error")
        self.assertIn("Unknown command", response_data["message"])
    
    def test_invalid_json(self):
        """Test handling of invalid JSON data."""
        # Create a client socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(self.socket_path))
        
        # Send invalid JSON
        sock.sendall(b"not json data")
        
        # Receive response
        response = sock.recv(4096).decode("utf-8")
        response_data = json.loads(response)
        
        # Close the socket
        sock.close()
        
        # Verify error response
        self.assertEqual(response_data["status"], "error")
        self.assertEqual(response_data["message"], "Invalid JSON data") 