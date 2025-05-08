"""Credential provider interface for exchange API credentials."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class CredentialProvider(ABC):
    """Abstract base class for credential providers.
    
    This interface defines the contract for retrieving exchange API credentials
    from various sources (environment, database, etc).
    """
    
    @abstractmethod
    def get_credentials(self, exchange_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get credentials for a specific exchange and user.
        
        Args:
            exchange_id: The ID of the exchange (e.g., 'binance', 'bitmex')
            user_id: Optional user ID for user-specific credentials
            
        Returns:
            Dictionary containing credentials (apiKey, secret, etc.)
            
        Raises:
            CredentialNotFoundError: If credentials cannot be found
        """
        pass
    
    @abstractmethod
    def get_exchange_options(self, exchange_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get exchange-specific options.
        
        Args:
            exchange_id: The ID of the exchange (e.g., 'binance', 'bitmex')
            user_id: Optional user ID for user-specific options
            
        Returns:
            Dictionary containing exchange options (test mode, etc.)
        """
        pass