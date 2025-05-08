"""Environment-based credential provider implementation."""

import os
from typing import Dict, Optional, Any

from ..interfaces.credential_provider import CredentialProvider
from ...common.logger import logger


class CredentialNotFoundError(Exception):
    """Raised when credentials cannot be found."""
    pass


class EnvCredentialProvider(CredentialProvider):
    """Retrieves credentials from environment variables.
    
    This provider is primarily used during development and testing.
    It looks for environment variables in the format:
    
    - EXCHANGE_API (API key)
    - EXCHANGE_SECRET (API secret)
    - EXCHANGE_NAME (Exchange ID)
    
    Additional exchange-specific options can be set via environment variables.
    """
    
    def __init__(self):
        self.logger = logger.bind(component="EnvCredentialProvider")
        
    def get_credentials(self, exchange_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get credentials from environment variables.
        
        Args:
            exchange_id: The ID of the exchange
            user_id: Optional user ID (ignored in this implementation)
            
        Returns:
            Dictionary with apiKey and secret fields
            
        Raises:
            CredentialNotFoundError: If credentials are not set in environment
        """
        # Check if the exchange ID matches the configured exchange
        env_exchange = os.environ.get("EXCHANGE_NAME", "").lower()
        
        # Handle the case where EXCHANGE_NAME is set but doesn't match requested exchange
        if env_exchange and env_exchange != exchange_id.lower():
            self.logger.warning(
                f"Requested credentials for {exchange_id} but EXCHANGE_NAME is {env_exchange}"
            )
        
        api_key = os.environ.get("EXCHANGE_API", "")
        secret = os.environ.get("EXCHANGE_SECRET", "")
        
        if not api_key or not secret:
            raise CredentialNotFoundError(
                f"Credentials for {exchange_id} not found in environment variables"
            )
            
        return {
            "apiKey": api_key,
            "secret": secret
        }
    
    def get_exchange_options(self, exchange_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get exchange options from environment variables.
        
        Args:
            exchange_id: The ID of the exchange
            user_id: Optional user ID (ignored in this implementation)
            
        Returns:
            Dictionary with exchange options
        """
        # For now, we'll always use testnet mode
        return {
            "test": True  # Use testnet by default for safety
        }