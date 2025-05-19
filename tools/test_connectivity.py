#!/usr/bin/env python3
"""
OTA Daemon-to-Server Connectivity Test Tool

This script tests the connection between the OTA daemon and the mock server,
verifying that the daemon can fetch the manifest and download update packages.
"""

import argparse
import json
import logging
import os
import sys
import urllib.request
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from daemon.core.config_manager import ConfigManager
from daemon.network.ota_client import OTAClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ota-connectivity-test")

def test_server_health(server_url):
    """Test if the server is up and responding to health checks."""
    try:
        # Mock server has a health check endpoint
        if "localhost" in server_url or "127.0.0.1" in server_url:
            health_url = f"{server_url}/health"
        else:
            health_url = f"{server_url}/ping"
            
        logger.info(f"Testing server health at {health_url}")
        with urllib.request.urlopen(health_url, timeout=5) as response:
            if response.status == 200:
                logger.info("✅ Server is up and responding to health checks")
                return True
            else:
                logger.error(f"❌ Server returned unexpected status: {response.status}")
                return False
    except Exception as e:
        logger.error(f"❌ Server health check failed: {str(e)}")
        return False

def test_manifest_fetch(ota_client):
    """Test if the OTA client can fetch the manifest."""
    logger.info("Testing manifest fetching")
    manifest = ota_client.fetch_manifest()
    
    if manifest:
        logger.info(f"✅ Successfully fetched manifest for version {manifest['version']}")
        logger.info(f"Manifest contents: {json.dumps(manifest, indent=2)}")
        return True
    else:
        logger.error("❌ Failed to fetch manifest")
        return False

def test_download_ability(ota_client, server_url):
    """Test if the OTA client can download a test file."""
    try:
        # Create a test directory for downloads
        test_dir = Path("test_downloads")
        test_dir.mkdir(exist_ok=True)
        
        # Check if we're using the mock server
        using_mock_server = "localhost" in server_url or "127.0.0.1" in server_url
        
        # Set appropriate test download path
        if using_mock_server:
            # Mock server has a health endpoint that returns JSON we can use for testing
            test_file_path = "health"
        else:
            # Production server might have a different test file
            test_file_path = "test/test.txt"
        
        logger.info(f"Testing file download from {server_url}/{test_file_path}")
        
        # Use OTA client to perform download
        local_path = test_dir / "test_download.txt"
        success, message = ota_client.download_file(test_file_path, local_path)
        
        if success:
            logger.info(f"✅ Successfully downloaded test file to {local_path}")
            logger.info(f"File contents: {local_path.read_text()[:100]}...")
            return True
        else:
            logger.error(f"❌ Failed to download test file: {message}")
            return False
    except Exception as e:
        logger.error(f"❌ Test download failed: {str(e)}")
        return False
    finally:
        # Clean up test files
        if local_path.exists():
            local_path.unlink()
        if test_dir.exists():
            try:
                test_dir.rmdir()
            except:
                pass

def main():
    """Run the connectivity tests."""
    parser = argparse.ArgumentParser(description="Test OTA daemon-to-server connectivity")
    parser.add_argument("--config", default="/etc/ota_config.json",
                       help="Path to OTA configuration file")
    parser.add_argument("--server", default=None,
                       help="Server URL to test (overrides config file)")
    parser.add_argument("--simulation", action="store_true",
                       help="Use simulation mode (use local mock server)")
    parser.add_argument("--device-id", default="test-device",
                       help="Device ID to use for testing")
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config_manager = ConfigManager(config_path=args.config)
        
        # Override simulation mode if specified
        if args.simulation:
            config_manager.is_simulation_mode = True
            logger.info("Using simulation mode (mock server)")
        
        # Get server URL (from args or config)
        server_url = args.server if args.server else config_manager.update_server
        
        logger.info(f"Testing connectivity to server: {server_url}")
        
        # Create OTA client
        ota_client = OTAClient(
            server_url=server_url,
            product_type=config_manager.product_type,
            device_id=args.device_id
        )
        
        # Run tests
        server_up = test_server_health(server_url)
        
        if not server_up:
            logger.error("Cannot continue testing as server is not reachable.")
            return 1
        
        manifest_ok = test_manifest_fetch(ota_client)
        download_ok = test_download_ability(ota_client, server_url)
        
        # Print summary
        logger.info("\n--- Connectivity Test Summary ---")
        logger.info(f"Server health check: {'✅ PASS' if server_up else '❌ FAIL'}")
        logger.info(f"Manifest fetch test: {'✅ PASS' if manifest_ok else '❌ FAIL'}")
        logger.info(f"Download test: {'✅ PASS' if download_ok else '❌ FAIL'}")
        
        if server_up and manifest_ok and download_ok:
            logger.info("🎉 All tests passed! The OTA daemon can communicate with the server.")
            return 0
        else:
            logger.error("❌ Some tests failed. Check the logs for details.")
            return 1
    except Exception as e:
        logger.error(f"Error during connectivity test: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 