"""
Dynamic account configuration for CCXT MCP client.

This module provides functionality to dynamically generate CCXT account 
configurations from credential providers, allowing for runtime resolution
of exchange API credentials without hardcoding them in configuration files.
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

from core.common.logger import logger
from core.config.interfaces.credential_provider import CredentialProvider
from core.config.providers.env_credential_provider import EnvCredentialProvider, CredentialNotFoundError


class DynamicAccountManager:
    """
    Manages dynamic creation of CCXT account configuration files.
    
    This class handles the generation of temporary CCXT account configuration
    files based on credentials retrieved from credential providers at runtime.
    """
    
    def __init__(self, credential_provider: Optional[CredentialProvider] = None):
        """
        Initialize the dynamic account manager.
        
        Args:
            credential_provider: Provider for retrieving exchange credentials
        """
        self.credential_provider = credential_provider or EnvCredentialProvider()
        self.logger = logger.bind(component="DynamicAccountManager", user_id="system")
        self._temp_files = []
        
    def __del__(self):
        """Clean up temporary files on object destruction."""
        self._cleanup_temp_files()
        
    def _cleanup_temp_files(self):
        """Remove any temporary files created by this manager."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.logger.debug(f"Removed temporary config file: {temp_file}")
            except Exception as e:
                self.logger.warning(f"Failed to remove temporary file {temp_file}: {str(e)}")
                
        self._temp_files = []
        
    def create_config_file(
        self, 
        exchange_id: str, 
        user_id: Optional[str] = None
    ) -> str:
        """
        Create a temporary CCXT account configuration file.
        
        Args:
            exchange_id: ID of the exchange to configure
            user_id: Optional user ID for retrieving user-specific credentials
            
        Returns:
            Path to the generated configuration file
            
        Raises:
            CredentialNotFoundError: If credentials cannot be found
        """
        # Get credentials from provider
        try:
            credentials = self.credential_provider.get_credentials(exchange_id, user_id)
            options = self.credential_provider.get_exchange_options(exchange_id, user_id)
        except CredentialNotFoundError as e:
            self.logger.error(f"Failed to get credentials for {exchange_id}: {str(e)}")
            raise
            
        # Generate a unique account ID
        account_id = f"{exchange_id}-{str(uuid.uuid4())[:8]}"
        
        # Create account configuration
        account_config = {
            "id": account_id,
            "exchangeId": exchange_id,
            "apiKey": credentials.get("apiKey", ""),
            "secret": credentials.get("secret", ""),
            "description": f"Dynamic {exchange_id.capitalize()} Account",
            "tag": "dynamic"
        }
        
        # Add options if available
        if options:
            account_config["options"] = options
            
        # Create full configuration
        config = {
            "accounts": [account_config]
        }
        
        # Write to temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.json', prefix=f'ccxt-config-{exchange_id}-')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(config, f, indent=2)
                
            self._temp_files.append(temp_path)
            self.logger.info(f"Created dynamic config for {exchange_id} at {temp_path}")
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Failed to create config file: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(f"Failed to create CCXT config file: {str(e)}")
            
    def add_account_to_existing_config(
        self,
        config_path: str,
        exchange_id: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        Add a dynamically configured account to an existing configuration file.
        
        This creates a new temporary file with the combined configuration.
        
        Args:
            config_path: Path to existing configuration file
            exchange_id: ID of the exchange to configure
            user_id: Optional user ID for retrieving user-specific credentials
            
        Returns:
            Path to the new configuration file
            
        Raises:
            CredentialNotFoundError: If credentials cannot be found
        """
        # Read existing config
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to read existing config {config_path}: {str(e)}")
            config = {"accounts": []}
            
        # Get credentials from provider
        try:
            credentials = self.credential_provider.get_credentials(exchange_id, user_id)
            options = self.credential_provider.get_exchange_options(exchange_id, user_id)
        except CredentialNotFoundError as e:
            self.logger.error(f"Failed to get credentials for {exchange_id}: {str(e)}")
            raise
            
        # Generate a unique account ID
        account_id = f"{exchange_id}-{str(uuid.uuid4())[:8]}"
        
        # Create account configuration
        account_config = {
            "id": account_id,
            "exchangeId": exchange_id,
            "apiKey": credentials.get("apiKey", ""),
            "secret": credentials.get("secret", ""),
            "description": f"Dynamic {exchange_id.capitalize()} Account",
            "tag": "dynamic"
        }
        
        # Add options if available
        if options:
            account_config["options"] = options
            
        # Add to accounts list
        config.setdefault("accounts", []).append(account_config)
        
        # Write to temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.json', prefix='ccxt-config-combined-')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(config, f, indent=2)
                
            self._temp_files.append(temp_path)
            self.logger.info(f"Added dynamic account for {exchange_id} to config at {temp_path}")
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Failed to create combined config file: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(f"Failed to create combined CCXT config file: {str(e)}")