"""
Voice Command Processor for the OTA daemon.

This module handles processing voice commands related to OTA updates,
including commands to schedule updates and trigger rollbacks.
"""

import logging
import re
from enum import Enum
from typing import Optional, Tuple

logger = logging.getLogger("ota-daemon.voice")

class OTACommandType(Enum):
    """Types of OTA voice commands."""
    INSTALL_TONIGHT = "install_tonight"
    INSTALL_NOW = "install_now"
    ROLLBACK = "rollback"
    CANCEL_UPDATE = "cancel_update"
    UNKNOWN = "unknown"

class CommandProcessor:
    """Processes voice commands for OTA operations."""
    
    def __init__(self):
        """Initialize the command processor."""
        # Command patterns for different actions
        self.command_patterns = {
            OTACommandType.INSTALL_TONIGHT: [
                r"install tonight",
                r"update tonight",
                r"install the update tonight",
                r"perform the update tonight"
            ],
            OTACommandType.INSTALL_NOW: [
                r"install now",
                r"update now",
                r"install the update now",
                r"perform the update now"
            ],
            OTACommandType.ROLLBACK: [
                r"rollback",
                r"roll back",
                r"rollback to last update",
                r"rollback to previous version",
                r"restore previous version"
            ],
            OTACommandType.CANCEL_UPDATE: [
                r"cancel update",
                r"cancel the update",
                r"stop the update"
            ]
        }
        
        # Confirmation patterns
        self.confirmation_patterns = [
            r"confirm",
            r"yes",
            r"proceed",
            r"confirmed",
            r"confirm rollback"
        ]
        
        # Compile regular expressions for faster matching
        self.compiled_patterns = {
            command_type: [re.compile(rf"\b{pattern}\b", re.IGNORECASE) 
                         for pattern in patterns]
            for command_type, patterns in self.command_patterns.items()
        }
        
        self.compiled_confirmation_patterns = [
            re.compile(rf"\b{pattern}\b", re.IGNORECASE) 
            for pattern in self.confirmation_patterns
        ]
    
    def process_command(self, command_text: str) -> Tuple[OTACommandType, Optional[str]]:
        """Process a voice command and determine the OTA action.
        
        Args:
            command_text: The text of the voice command.
        
        Returns:
            A tuple of (command_type, additional_info).
        """
        if not command_text:
            return (OTACommandType.UNKNOWN, None)
        
        logger.debug(f"Processing voice command: {command_text}")
        
        # Check for each type of command
        for command_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(command_text):
                    logger.info(f"Detected OTA command: {command_type.value}")
                    return (command_type, None)
        
        # Check for confirmation
        for pattern in self.compiled_confirmation_patterns:
            if pattern.search(command_text):
                logger.info("Detected confirmation command")
                return (OTACommandType.UNKNOWN, "confirmation")
        
        logger.debug("No matching OTA command found")
        return (OTACommandType.UNKNOWN, None)
    
    def is_update_command(self, command_text: str) -> bool:
        """Check if the command is an update command.
        
        Args:
            command_text: The text of the voice command.
        
        Returns:
            True if the command is an update command, False otherwise.
        """
        command_type, _ = self.process_command(command_text)
        return command_type in [OTACommandType.INSTALL_TONIGHT, OTACommandType.INSTALL_NOW]
    
    def is_rollback_command(self, command_text: str) -> bool:
        """Check if the command is a rollback command.
        
        Args:
            command_text: The text of the voice command.
        
        Returns:
            True if the command is a rollback command, False otherwise.
        """
        command_type, _ = self.process_command(command_text)
        return command_type == OTACommandType.ROLLBACK
    
    def is_cancel_command(self, command_text: str) -> bool:
        """Check if the command is a cancel command.
        
        Args:
            command_text: The text of the voice command.
        
        Returns:
            True if the command is a cancel command, False otherwise.
        """
        command_type, _ = self.process_command(command_text)
        return command_type == OTACommandType.CANCEL_UPDATE
    
    def is_confirmation(self, command_text: str) -> bool:
        """Check if the command is a confirmation.
        
        Args:
            command_text: The text of the voice command.
        
        Returns:
            True if the command is a confirmation, False otherwise.
        """
        _, additional_info = self.process_command(command_text)
        return additional_info == "confirmation" 