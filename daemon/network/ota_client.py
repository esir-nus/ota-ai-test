"""
OTA Client for communicating with the update server.

This module handles network communication with the OTA server,
including manifest fetching, update downloading, and status reporting.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import urllib.request
import urllib.error
import hashlib

logger = logging.getLogger("ota-daemon.ota-client")

class OTAClient:
    """Client for communicating with the OTA server."""
    
    def __init__(self, server_url: str, product_type: str, device_id: str):
        """Initialize the OTA client.
        
        Args:
            server_url: The base URL of the OTA server.
            product_type: The product type for this device.
            device_id: The unique device ID.
        """
        self.server_url = server_url
        self.product_type = product_type
        self.device_id = device_id
        self.max_retries = 5
        self.retry_delay = 5  # seconds
        
        # Remove trailing slash if present
        if self.server_url.endswith('/'):
            self.server_url = self.server_url[:-1]
    
    def check_network(self) -> bool:
        """Check if the network is available.
        
        Returns:
            True if the network is available, False otherwise.
        """
        try:
            # Try to connect to the OTA server
            urllib.request.urlopen(f"{self.server_url}/ping", timeout=5)
            logger.debug("Network check successful")
            return True
        except Exception as e:
            logger.error(f"Network check failed: {str(e)}")
            return False
    
    def fetch_manifest(self) -> Optional[Dict[str, Any]]:
        """Fetch the update manifest from the server.
        
        Returns:
            The manifest as a dictionary, or None if fetching failed.
        """
        # Determine if we're using the mock server (localhost)
        using_mock_server = "localhost" in self.server_url or "127.0.0.1" in self.server_url
        
        # Set the appropriate manifest URL based on server type
        if using_mock_server:
            # Mock server uses a different path structure
            manifest_url = f"{self.server_url}/manifest/latest"
            logger.info(f"Using mock server manifest path: {manifest_url}")
        else:
            # Production server path
            manifest_url = f"{self.server_url}/{self.product_type}/manifest.json"
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Fetching manifest from {manifest_url} (attempt {attempt})")
                with urllib.request.urlopen(manifest_url, timeout=30) as response:
                    manifest_data = response.read()
                    
                    # Verify the manifest
                    manifest = json.loads(manifest_data)
                    
                    # Check if the manifest has the required fields
                    required_fields = ["version", "release_date"]
                    for field in required_fields:
                        if field not in manifest:
                            logger.error(f"Manifest is missing required field: {field}")
                            return None
                    
                    # If using mock server, ensure 'files' field exists (even if empty)
                    if using_mock_server and "files" not in manifest:
                        manifest["files"] = []
                    
                    logger.info(f"Manifest fetched successfully: {manifest['version']}")
                    return manifest
            except urllib.error.URLError as e:
                logger.error(f"Error fetching manifest (attempt {attempt}): {str(e)}")
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("Max retries reached, giving up")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing manifest: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error fetching manifest: {str(e)}")
                return None
        
        return None
    
    def download_file(self, remote_path: str, local_path: Path) -> Tuple[bool, str]:
        """Download a file from the server.
        
        Args:
            remote_path: The path to the file on the server.
            local_path: The local path to save the file to.
        
        Returns:
            A tuple of (success, message).
        """
        url = f"{self.server_url}/{remote_path}"
        
        # Create directory if it doesn't exist
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloading {url} to {local_path}")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                with urllib.request.urlopen(url, timeout=300) as response, open(local_path, 'wb') as out_file:
                    # Get content length if available
                    content_length = response.getheader('Content-Length')
                    total_size = int(content_length) if content_length else None
                    
                    # Download the file in chunks
                    downloaded = 0
                    chunk_size = 8192
                    
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        out_file.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size:
                            progress = int(downloaded / total_size * 100)
                            if progress % 10 == 0:  # Log every 10%
                                logger.debug(f"Download progress: {progress}% ({downloaded}/{total_size} bytes)")
                
                logger.info(f"Download completed: {local_path}")
                return (True, "Download completed successfully")
            except Exception as e:
                logger.error(f"Error downloading file (attempt {attempt}): {str(e)}")
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    error_msg = f"Failed to download after {self.max_retries} attempts: {str(e)}"
                    logger.error(error_msg)
                    return (False, error_msg)
        
        return (False, "Unknown error occurred")
    
    def verify_file(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify a file's integrity using its checksum.
        
        Args:
            file_path: The path to the file to verify.
            expected_checksum: The expected SHA256 checksum.
        
        Returns:
            True if the file's checksum matches the expected one, False otherwise.
        """
        if not file_path.exists():
            logger.error(f"File not found for verification: {file_path}")
            return False
        
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read and update hash in chunks
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            actual_checksum = sha256_hash.hexdigest()
            
            if actual_checksum.lower() == expected_checksum.lower():
                logger.info(f"Checksum verification successful for {file_path}")
                return True
            else:
                logger.error(f"Checksum verification failed for {file_path}")
                logger.error(f"Expected: {expected_checksum}")
                logger.error(f"Actual: {actual_checksum}")
                return False
        except Exception as e:
            logger.error(f"Error verifying checksum: {str(e)}")
            return False
    
    def report_update_status(self, version: str, status: str, message: str) -> bool:
        """Report the status of an update to the server.
        
        Args:
            version: The version that was updated to.
            status: The status of the update (e.g., "success", "failed").
            message: Additional information about the update.
        
        Returns:
            True if the report was sent successfully, False otherwise.
        """
        report_url = f"{self.server_url}/report"
        
        report_data = {
            "device_id": self.device_id,
            "product_type": self.product_type,
            "version": version,
            "status": status,
            "message": message,
            "timestamp": int(time.time())
        }
        
        try:
            data = json.dumps(report_data).encode('utf-8')
            req = urllib.request.Request(report_url, data=data, headers={
                'Content-Type': 'application/json'
            })
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    logger.info(f"Update status reported successfully: {status}")
                    return True
                else:
                    logger.error(f"Error reporting update status: {response.status} {response.reason}")
                    return False
        except Exception as e:
            logger.error(f"Error reporting update status: {str(e)}")
            return False 