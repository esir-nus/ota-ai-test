#!/usr/bin/env python3
"""
OTA Daemon GUI Client

A simple client for interacting with the OTA daemon.
"""

import json
import socket
import tkinter as tk
from tkinter import ttk, messagebox

class OTADaemonClient:
    def __init__(self, socket_path="/tmp/robot-ai-ota.sock"):
        self.socket_path = socket_path
    
    def send_command(self, command, parameters=None):
        """Send a command to the OTA daemon."""
        if parameters is None:
            parameters = {}
        
        # Create command data
        command_data = {
            "command": command,
            "parameters": parameters
        }
        
        # Connect to socket
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        try:
            client_socket.connect(self.socket_path)
            client_socket.sendall(json.dumps(command_data).encode('utf-8'))
            
            # Receive response
            response_data = client_socket.recv(4096).decode('utf-8')
            return json.loads(response_data)
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            client_socket.close()

class OTADaemonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OTA Daemon GUI")
        self.root.geometry("300x250")
        
        self.client = OTADaemonClient()
        
        # Create frame
        frame = ttk.Frame(root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        ttk.Button(frame, text="Check Now", command=self.check_now).pack(fill=tk.X, pady=5)
        ttk.Button(frame, text="Install Now", command=self.install_now).pack(fill=tk.X, pady=5)
        ttk.Button(frame, text="Get Status", command=self.get_status).pack(fill=tk.X, pady=5)
        
        # Output area
        self.output = tk.Text(frame, height=8, width=40)
        self.output.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def display_result(self, result):
        """Display result in the output area."""
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, json.dumps(result, indent=2))
    
    def check_now(self):
        """Send check_now command."""
        result = self.client.send_command("check_now")
        self.display_result(result)
    
    def install_now(self):
        """Send install_now command."""
        result = self.client.send_command("install_now")
        self.display_result(result)
    
    def get_status(self):
        """Send get_status command."""
        result = self.client.send_command("get_status")
        self.display_result(result)

if __name__ == "__main__":
    root = tk.Tk()
    app = OTADaemonGUI(root)
    root.mainloop()