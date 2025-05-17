"""
Configuration manager for the OTA daemon.

This module handles loading, validating, and accessing configuration settings
for the OTA daemon.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ota-daemon.config")

class ConfigManager:
    """Manages configuration for the OTA daemon."""
    
    DEFAULT_CONFIG = {
        "product_type": "robot_ai",
        "version": "1.0.0",
        "update_server": "https://updates.robot-ai.example.com",
        "update_check_times": ["03:00", "04:00", "05:00"],
        "backup_retention_count": 2,
        "device_id": None  # Will be generated if not provided
    }
    
    def __init__(self, config_path: str = "/etc/ota_config.json"):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file.
        """
        self.config_path = Path(config_path)
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from the config file."""
        try:
            if self.config_path.exists():
                logger.info(f"Loading configuration from {self.config_path}")
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                logger.info("Configuration loaded successfully")
            else:
                logger.warning(f"Configuration file {self.config_path} not found. Using defaults.")
                self.save_config()  # Create default config file
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            logger.info("Using default configuration")
    
    def save_config(self) -> None:
        """Save current configuration to the config file."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Saving configuration to {self.config_path}")
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: The configuration key.
            default: Default value if key is not found.
        
        Returns:
            The configuration value or default if not found.
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save to disk.
        
        Args:
            key: The configuration key.
            value: The value to set.
        """
        self.config[key] = value
        self.save_config()
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """Update multiple configuration values and save to disk.
        
        Args:
            config_dict: Dictionary of configuration keys and values.
        """
        self.config.update(config_dict)
        self.save_config()
    
    @property
    def product_type(self) -> str:
        """Get the product type."""
        return self.get("product_type")
    
    @property
    def version(self) -> str:
        """Get the current version."""
        return self.get("version")
    
    @version.setter
    def version(self, value: str) -> None:
        """Set the current version."""
        self.set("version", value)
    
    @property
    def update_server(self) -> str:
        """Get the update server URL."""
        return self.get("update_server")
    
    @property
    def update_check_times(self) -> List[str]:
        """Get the update check times."""
        return self.get("update_check_times")
    
    @property
    def backup_retention_count(self) -> int:
        """Get the number of backups to retain."""
        return self.get("backup_retention_count")
    
    @property
    def device_id(self) -> Optional[str]:
        """Get the device ID."""
        return self.get("device_id")
    
    @device_id.setter
    def device_id(self, value: str) -> None:
        """Set the device ID."""
        self.set("device_id", value) 