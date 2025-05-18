"""
Configuration manager for the OTA daemon.

This module handles loading, saving, and managing the daemon's configuration.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger("ota-daemon.config")

class ConfigManager:
    """Manages configuration for the OTA daemon."""
    
    def __init__(self, config_path: str = "/etc/ota_config.json"):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file.
        """
        self.config_path = config_path
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self._config = json.load(f)
            else:
                # Create default configuration
                self._config = {
                    'product_type': 'robot_ai',
                    'version': '1.0.0',
                    'update_server': 'https://updates.robot-ai.example.com',
                    'update_check_times': ['03:00', '04:00', '05:00'],
                    'backup_retention_count': 2,
                    'device_id': None,
                    'last_check_time': None,
                    'update_available': False,
                    'available_version': None,
                    'gui': {
                        'socket_path': '/tmp/robot-ai-ota.sock',
                        'notification_timeout': 30,  # seconds
                        'status_update_interval': 5  # seconds
                    }
                }
                self._save_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            raise
    
    @property
    def product_type(self) -> str:
        """Get the product type."""
        return self._config.get('product_type', 'robot_ai')
    
    @product_type.setter
    def product_type(self, value: str):
        """Set the product type."""
        self._config['product_type'] = value
        self._save_config()
    
    @property
    def version(self) -> str:
        """Get the current version."""
        return self._config.get('version', '1.0.0')
    
    @version.setter
    def version(self, value: str):
        """Set the current version."""
        self._config['version'] = value
        self._save_config()
    
    @property
    def update_server(self) -> str:
        """Get the update server URL."""
        return self._config.get('update_server', 'https://updates.robot-ai.example.com')
    
    @update_server.setter
    def update_server(self, value: str):
        """Set the update server URL."""
        self._config['update_server'] = value
        self._save_config()
    
    @property
    def update_check_times(self) -> List[str]:
        """Get the update check times."""
        return self._config.get('update_check_times', ['03:00', '04:00', '05:00'])
    
    @update_check_times.setter
    def update_check_times(self, value: List[str]):
        """Set the update check times."""
        self._config['update_check_times'] = value
        self._save_config()
    
    @property
    def backup_retention_count(self) -> int:
        """Get the number of backups to retain."""
        return self._config.get('backup_retention_count', 2)
    
    @backup_retention_count.setter
    def backup_retention_count(self, value: int):
        """Set the number of backups to retain."""
        self._config['backup_retention_count'] = value
        self._save_config()
    
    @property
    def device_id(self) -> Optional[str]:
        """Get the device ID."""
        return self._config.get('device_id')
    
    @device_id.setter
    def device_id(self, value: str):
        """Set the device ID."""
        self._config['device_id'] = value
        self._save_config()
    
    @property
    def last_check_time(self) -> Optional[str]:
        """Get the last update check time."""
        return self._config.get('last_check_time')
    
    @last_check_time.setter
    def last_check_time(self, value: Optional[str]):
        """Set the last update check time."""
        self._config['last_check_time'] = value
        self._save_config()
    
    @property
    def update_available(self) -> bool:
        """Get whether an update is available."""
        return self._config.get('update_available', False)
    
    @update_available.setter
    def update_available(self, value: bool):
        """Set whether an update is available."""
        self._config['update_available'] = value
        self._save_config()
    
    @property
    def available_version(self) -> Optional[str]:
        """Get the available update version."""
        return self._config.get('available_version')
    
    @available_version.setter
    def available_version(self, value: Optional[str]):
        """Set the available update version."""
        self._config['available_version'] = value
        self._save_config()
    
    @property
    def gui_socket_path(self) -> str:
        """Get the GUI socket path."""
        return self._config.get('gui', {}).get('socket_path', '/tmp/robot-ai-ota.sock')
    
    @gui_socket_path.setter
    def gui_socket_path(self, value: str):
        """Set the GUI socket path."""
        if 'gui' not in self._config:
            self._config['gui'] = {}
        self._config['gui']['socket_path'] = value
        self._save_config()
    
    @property
    def gui_notification_timeout(self) -> int:
        """Get the GUI notification timeout in seconds."""
        return self._config.get('gui', {}).get('notification_timeout', 30)
    
    @gui_notification_timeout.setter
    def gui_notification_timeout(self, value: int):
        """Set the GUI notification timeout in seconds."""
        if 'gui' not in self._config:
            self._config['gui'] = {}
        self._config['gui']['notification_timeout'] = value
        self._save_config()
    
    @property
    def gui_status_update_interval(self) -> int:
        """Get the GUI status update interval in seconds."""
        return self._config.get('gui', {}).get('status_update_interval', 5)
    
    @gui_status_update_interval.setter
    def gui_status_update_interval(self, value: int):
        """Set the GUI status update interval in seconds."""
        if 'gui' not in self._config:
            self._config['gui'] = {}
        self._config['gui']['status_update_interval'] = value
        self._save_config() 