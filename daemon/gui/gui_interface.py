"""
GUI Communication Interface for OTA Daemon.

This module handles communication between the OTA daemon and the Tkinter GUI
using Unix sockets for IPC (Inter-Process Communication).
"""

import json
import logging
import os
import socket
import threading
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger("ota-daemon.gui")

class GUIInterface:
    """Interface for communicating with the Tkinter GUI."""
    
    def __init__(self, socket_path: str = "/tmp/robot-ai-ota.sock"):
        """Initialize the GUI interface.
        
        Args:
            socket_path: Path to the Unix socket for GUI communication.
        """
        self.socket_path = socket_path
        self._server_socket = None
        self._running = False
        self._command_handlers = {}
        self._status_callback = None
        
        # Create socket directory if it doesn't exist
        os.makedirs(os.path.dirname(socket_path), exist_ok=True)
    
    def register_command_handler(self, command: str, handler: Callable):
        """Register a handler for a specific GUI command.
        
        Args:
            command: The command name to handle.
            handler: The function to call when the command is received.
        """
        self._command_handlers[command] = handler
    
    def set_status_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set a callback for sending status updates to the GUI.
        
        Args:
            callback: Function to call with status updates.
        """
        self._status_callback = callback
    
    def start(self):
        """Start the GUI interface server."""
        if self._running:
            logger.warning("GUI interface already running")
            return
        
        # Remove existing socket if it exists
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        # Create and bind the socket
        self._server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_socket.bind(self.socket_path)
        self._server_socket.listen(1)
        
        # Set socket permissions for GUI access
        os.chmod(self.socket_path, 0o666)
        
        self._running = True
        
        # Start listener thread
        self._listener_thread = threading.Thread(target=self._listen_for_connections)
        self._listener_thread.daemon = True
        self._listener_thread.start()
        
        logger.info("GUI interface started")
    
    def stop(self):
        """Stop the GUI interface server."""
        self._running = False
        
        if self._server_socket:
            self._server_socket.close()
            
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        logger.info("GUI interface stopped")
    
    def send_status_update(self, status_data: Dict[str, Any]):
        """Send a status update to the GUI.
        
        Args:
            status_data: Status information to send.
        """
        if self._status_callback:
            try:
                self._status_callback(status_data)
            except Exception as e:
                logger.error(f"Error sending status update: {str(e)}")
    
    def _listen_for_connections(self):
        """Listen for incoming GUI connections."""
        while self._running:
            try:
                client_socket, _ = self._server_socket.accept()
                # Handle client connection in a new thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self._running:  # Only log if not shutting down
                    logger.error(f"Error accepting connection: {str(e)}")
    
    def _handle_client(self, client_socket: socket.socket):
        """Handle communication with a connected GUI client.
        
        Args:
            client_socket: The client's socket connection.
        """
        try:
            # Set a timeout to prevent hanging
            client_socket.settimeout(5)
            
            # Receive data
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return
            
            # Parse command
            try:
                command_data = json.loads(data)
                command = command_data.get('command')
                parameters = command_data.get('parameters', {})
                
                if command in self._command_handlers:
                    # Execute handler
                    response = self._command_handlers[command](parameters)
                    
                    # Send response
                    response_data = {
                        'status': 'success',
                        'data': response
                    }
                else:
                    response_data = {
                        'status': 'error',
                        'message': f'Unknown command: {command}'
                    }
                
                # Send response
                client_socket.sendall(json.dumps(response_data).encode('utf-8'))
            except json.JSONDecodeError:
                error_response = {
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }
                client_socket.sendall(json.dumps(error_response).encode('utf-8'))
        except Exception as e:
            logger.error(f"Error handling client connection: {str(e)}")
        finally:
            client_socket.close() 