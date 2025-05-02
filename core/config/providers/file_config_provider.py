# config/providers/file_config_provider.py

import json
import os
from pathlib import Path
from typing import Dict, Any

from core.config.interfaces.configuration_provider import ConfigurationProvider
from core.common.logger import logger

class FileConfigProvider(ConfigurationProvider):
    """
    A file-based configuration provider implementation.
    
    This provider stores configuration data in JSON files, with one file per user.
    It's suitable for the MVP phase but should be replaced with a database-backed
    provider for production use with multiple users.
    """
    
    def __init__(self, config_dir=None):
        """
        Initialize the file config provider.
        
        Args:
            config_dir: Optional directory path for configuration files
                        (defaults to /config/users/)
        """
        # Default to /config/users/ directory
        self.config_dir = config_dir or Path(__file__).parent.parent / "users"
        os.makedirs(self.config_dir, exist_ok=True)
        
    def _get_user_config_path(self, user_id: str) -> Path:
        """Get the path to a user's configuration file."""
        return self.config_dir / f"{user_id}.json"
    
    def get_config(self, user_id: str, config_type: str = None) -> Dict[str, Any]:
        """
        Get configuration for a specific user and configuration type.
        
        Args:
            user_id: The user's unique identifier
            config_type: The type of configuration to retrieve (e.g., 'extraction', 'decision')
            
        Returns:
            A dictionary containing the configuration values
        """
        log = logger.bind(user_id=user_id)
        config_path = self._get_user_config_path(user_id)
        
        # Check if config file exists
        if not config_path.exists():
            log.warning(f"Configuration file not found for user {user_id}")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Return specific config type if requested
            if config_type:
                return config.get(config_type, {})
            
            return config
        except (json.JSONDecodeError, IOError) as e:
            log.error(f"Error reading configuration file: {e}")
            return {}
    
    def set_config(self, user_id: str, config_type: str, config_data: Dict[str, Any]) -> None:
        """
        Set configuration for a specific user and configuration type.
        
        Args:
            user_id: The user's unique identifier
            config_type: The type of configuration to set (e.g., 'extraction', 'decision')
            config_data: The configuration data to store
        """
        log = logger.bind(user_id=user_id)
        config_path = self._get_user_config_path(user_id)
        
        # Load existing config or create new one
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError):
                log.warning(f"Error reading existing config, creating new one for {user_id}")
                config = {}
        else:
            config = {}
        
        # Update the specific config type
        config[config_type] = config_data
        
        # Write back to file
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            log.info(f"Configuration saved for user {user_id}, type {config_type}")
        except IOError as e:
            log.error(f"Error writing configuration file: {e}")
            raise