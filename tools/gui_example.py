#!/usr/bin/env python3
"""
OTA GUI Example - Manifest Display and Connectivity Test

This script demonstrates how to connect to the OTA daemon's socket interface
and display manifest data and connectivity test results in a Tkinter GUI.
"""

import json
import os
import socket
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext
from threading import Thread
import time

# Socket path for OTA daemon communication
SOCKET_PATH = "/tmp/robot-ai-ota.sock"

class OTAClientGUI:
    """Example GUI for demonstrating OTA manifest and connectivity features."""
    
    def __init__(self, root):
        """Initialize the GUI.
        
        Args:
            root: The Tkinter root window.
        """
        self.root = root
        self.root.title("OTA Client Example")
        self.root.geometry("800x600")
        
        # Create main notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.status_tab = ttk.Frame(self.notebook)
        self.manifest_tab = ttk.Frame(self.notebook)
        self.connectivity_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.status_tab, text="Status")
        self.notebook.add(self.manifest_tab, text="Manifest Data")
        self.notebook.add(self.connectivity_tab, text="Connectivity Test")
        
        # Initialize tabs
        self._setup_status_tab()
        self._setup_manifest_tab()
        self._setup_connectivity_tab()
        
        # Initial data refresh
        self.refresh_status()
    
    def _setup_status_tab(self):
        """Set up the status tab with current OTA status."""
        frame = ttk.Frame(self.status_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Version information
        ttk.Label(frame, text="OTA Status", font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )
        
        ttk.Label(frame, text="Current Version:").grid(row=1, column=0, sticky="w")
        self.current_version_label = ttk.Label(frame, text="Loading...")
        self.current_version_label.grid(row=1, column=1, sticky="w")
        
        ttk.Label(frame, text="Available Version:").grid(row=2, column=0, sticky="w")
        self.available_version_label = ttk.Label(frame, text="None")
        self.available_version_label.grid(row=2, column=1, sticky="w")
        
        ttk.Label(frame, text="Update Available:").grid(row=3, column=0, sticky="w")
        self.update_available_label = ttk.Label(frame, text="No")
        self.update_available_label.grid(row=3, column=1, sticky="w")
        
        ttk.Label(frame, text="Last Check:").grid(row=4, column=0, sticky="w")
        self.last_check_label = ttk.Label(frame, text="Never")
        self.last_check_label.grid(row=4, column=1, sticky="w")
        
        ttk.Label(frame, text="Product Type:").grid(row=5, column=0, sticky="w")
        self.product_type_label = ttk.Label(frame, text="Unknown")
        self.product_type_label.grid(row=5, column=1, sticky="w")
        
        ttk.Label(frame, text="Update Server:").grid(row=6, column=0, sticky="w")
        self.server_label = ttk.Label(frame, text="Unknown")
        self.server_label.grid(row=6, column=1, sticky="w")
        
        # Button frame
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20, sticky="w")
        
        self.check_now_button = ttk.Button(
            button_frame, text="Check Now", command=self.check_for_updates
        )
        self.check_now_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.install_now_button = ttk.Button(
            button_frame, text="Install Now", command=self.install_now
        )
        self.install_now_button.pack(side=tk.LEFT)
        
        self.refresh_button = ttk.Button(
            button_frame, text="Refresh Status", command=self.refresh_status
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(10, 0))
    
    def _setup_manifest_tab(self):
        """Set up the manifest tab to display manifest data."""
        frame = ttk.Frame(self.manifest_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(frame, text="Manifest Data", font=("Arial", 14, "bold")).pack(
            anchor="w", pady=(0, 10)
        )
        
        # Manifest display area (scrollable text)
        self.manifest_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=20)
        self.manifest_text.pack(fill=tk.BOTH, expand=True)
        self.manifest_text.config(state=tk.DISABLED)
        
        # Refresh button
        ttk.Button(
            frame, text="Refresh Manifest", command=self.check_for_updates
        ).pack(anchor="w", pady=(10, 0))
    
    def _setup_connectivity_tab(self):
        """Set up the connectivity test tab."""
        frame = ttk.Frame(self.connectivity_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(frame, text="Connectivity Test", font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )
        
        # Test result indicators
        ttk.Label(frame, text="Network Status:").grid(row=1, column=0, sticky="w")
        self.network_status_label = ttk.Label(frame, text="Not Tested")
        self.network_status_label.grid(row=1, column=1, sticky="w")
        
        ttk.Label(frame, text="Manifest Fetch:").grid(row=2, column=0, sticky="w")
        self.manifest_status_label = ttk.Label(frame, text="Not Tested")
        self.manifest_status_label.grid(row=2, column=1, sticky="w")
        
        ttk.Label(frame, text="Download Test:").grid(row=3, column=0, sticky="w")
        self.download_status_label = ttk.Label(frame, text="Not Tested")
        self.download_status_label.grid(row=3, column=1, sticky="w")
        
        ttk.Label(frame, text="Server URL:").grid(row=4, column=0, sticky="w")
        self.conn_server_label = ttk.Label(frame, text="Unknown")
        self.conn_server_label.grid(row=4, column=1, sticky="w")
        
        ttk.Label(frame, text="Device ID:").grid(row=5, column=0, sticky="w")
        self.device_id_label = ttk.Label(frame, text="Unknown")
        self.device_id_label.grid(row=5, column=1, sticky="w")
        
        # Test details
        ttk.Label(frame, text="Test Details:", font=("Arial", 11, "bold")).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(10, 5)
        )
        
        self.test_details_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=10)
        self.test_details_text.grid(row=7, column=0, columnspan=2, sticky="nsew")
        self.test_details_text.config(state=tk.DISABLED)
        
        # Run test button
        ttk.Button(
            frame, text="Run Connectivity Test", command=self.run_connectivity_test
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(10, 0))
    
    def refresh_status(self):
        """Refresh the OTA status display."""
        try:
            response = self._send_command("get_status", {})
            if response and response.get("status") == "success":
                data = response.get("data", {})
                
                # Update status labels
                self.current_version_label.config(text=data.get("version", "Unknown"))
                self.available_version_label.config(
                    text=data.get("available_version", "None")
                )
                self.update_available_label.config(
                    text="Yes" if data.get("update_available") else "No"
                )
                self.last_check_label.config(text=data.get("last_check", "Never"))
                self.product_type_label.config(text=data.get("product_type", "Unknown"))
                self.server_label.config(text=data.get("update_server", "Unknown"))
            else:
                print("Error fetching status:", response)
        except Exception as e:
            print(f"Error refreshing status: {str(e)}")
    
    def check_for_updates(self):
        """Check for updates and display manifest data."""
        try:
            # Disable the check button while processing
            self.check_now_button.config(state=tk.DISABLED)
            
            # Send the check_now command
            response = self._send_command("check_now", {})
            
            # Update manifest display
            if response and response.get("status") == "success":
                data = response.get("data", {})
                manifest = data.get("manifest")
                
                # Update status tab
                self.refresh_status()
                
                # Update manifest tab
                self.manifest_text.config(state=tk.NORMAL)
                self.manifest_text.delete(1.0, tk.END)
                
                if manifest:
                    # Format the manifest as pretty JSON
                    pretty_manifest = json.dumps(manifest, indent=2)
                    self.manifest_text.insert(tk.END, pretty_manifest)
                else:
                    self.manifest_text.insert(tk.END, "No manifest data available.")
                
                self.manifest_text.config(state=tk.DISABLED)
            else:
                print("Error checking for updates:", response)
            
            # Re-enable the check button
            self.check_now_button.config(state=tk.NORMAL)
        except Exception as e:
            print(f"Error checking for updates: {str(e)}")
            # Re-enable the check button
            self.check_now_button.config(state=tk.NORMAL)
    
    def install_now(self):
        """Trigger immediate update installation."""
        try:
            response = self._send_command("install_now", {})
            if response and response.get("status") == "success":
                print("Update installation initiated")
            else:
                print("Error initiating update:", response)
        except Exception as e:
            print(f"Error installing update: {str(e)}")
    
    def run_connectivity_test(self):
        """Run connectivity test and display results."""
        try:
            # Update UI to show test is running
            self.network_status_label.config(text="Testing...")
            self.manifest_status_label.config(text="Testing...")
            self.download_status_label.config(text="Testing...")
            
            # Clear test details
            self.test_details_text.config(state=tk.NORMAL)
            self.test_details_text.delete(1.0, tk.END)
            self.test_details_text.insert(tk.END, "Running connectivity test...\n")
            self.test_details_text.config(state=tk.DISABLED)
            
            # Update UI immediately
            self.root.update()
            
            # Send the connectivity_check command
            response = self._send_command("connectivity_check", {})
            
            if response and response.get("status") == "success":
                data = response.get("data", {})
                
                # Update status indicators
                network_status = data.get("network_status", False)
                manifest_status = data.get("manifest_status", False)
                download_status = data.get("download_status", False)
                
                self.network_status_label.config(
                    text="✅ Connected" if network_status else "❌ Failed"
                )
                self.manifest_status_label.config(
                    text="✅ Success" if manifest_status else "❌ Failed"
                )
                self.download_status_label.config(
                    text="✅ Success" if download_status else "❌ Failed"
                )
                
                # Update server and device info
                self.conn_server_label.config(text=data.get("server_url", "Unknown"))
                self.device_id_label.config(text=data.get("device_id", "Unknown"))
                
                # Update test details
                self.test_details_text.config(state=tk.NORMAL)
                self.test_details_text.delete(1.0, tk.END)
                
                details = [
                    "Connectivity Test Results:",
                    f"Server URL: {data.get('server_url', 'Unknown')}",
                    f"Product Type: {data.get('product_type', 'Unknown')}",
                    f"Device ID: {data.get('device_id', 'Unknown')}",
                    "",
                    f"Network Connection: {'Success' if network_status else 'Failed'}",
                    f"Manifest Fetch: {'Success' if manifest_status else 'Failed'}",
                    f"Download Test: {'Success' if download_status else 'Failed'}",
                    "",
                    "Test completed at: " + time.strftime("%Y-%m-%d %H:%M:%S")
                ]
                
                self.test_details_text.insert(tk.END, "\n".join(details))
                self.test_details_text.config(state=tk.DISABLED)
            else:
                print("Error running connectivity test:", response)
                
                # Update status indicators
                self.network_status_label.config(text="❌ Test Failed")
                self.manifest_status_label.config(text="❌ Test Failed")
                self.download_status_label.config(text="❌ Test Failed")
                
                # Update test details
                self.test_details_text.config(state=tk.NORMAL)
                self.test_details_text.delete(1.0, tk.END)
                self.test_details_text.insert(tk.END, "Connectivity test failed. Check if OTA daemon is running.")
                self.test_details_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error running connectivity test: {str(e)}")
            
            # Update status indicators
            self.network_status_label.config(text="❌ Error")
            self.manifest_status_label.config(text="❌ Error")
            self.download_status_label.config(text="❌ Error")
            
            # Update test details
            self.test_details_text.config(state=tk.NORMAL)
            self.test_details_text.delete(1.0, tk.END)
            self.test_details_text.insert(tk.END, f"Error: {str(e)}\n\nCheck if OTA daemon is running.")
            self.test_details_text.config(state=tk.DISABLED)
    
    def _send_command(self, command, parameters):
        """Send a command to the OTA daemon and get the response.
        
        Args:
            command: The command to send.
            parameters: A dictionary of parameters for the command.
            
        Returns:
            The response from the daemon, or None if an error occurred.
        """
        try:
            # Create socket
            client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_socket.settimeout(30)  # 30 second timeout
            
            # Connect to the daemon socket
            client_socket.connect(SOCKET_PATH)
            
            # Prepare command data
            command_data = {
                "command": command,
                "parameters": parameters
            }
            
            # Send the command
            client_socket.sendall(json.dumps(command_data).encode('utf-8'))
            
            # Receive the response
            response_data = client_socket.recv(65536).decode('utf-8')
            response = json.loads(response_data)
            
            # Close the socket
            client_socket.close()
            
            return response
        except Exception as e:
            print(f"Error sending command '{command}': {str(e)}")
            return None


def main():
    """Run the OTA Client GUI example."""
    root = tk.Tk()
    app = OTAClientGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 