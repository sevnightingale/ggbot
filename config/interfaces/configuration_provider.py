# config/interfaces/configuration_provider.py

from abc import ABC, abstractmethod
from typing import Dict, Any

class ConfigurationProvider(ABC):
    """
    Abstract interface for configuration providers.
    
    Different implementations can source configurations from files,
    databases, or UI inputs.
    """
    
    @abstractmethod
    def get_config(self, user_id: str, config_type: str = None) -> Dict[str, Any]:
        """
        Get configuration for a specific user and configuration type.
        
        Args:
            user_id: The user's unique identifier
            config_type: The type of configuration to retrieve (e.g., 'extraction', 'decision')
            
        Returns:
            A dictionary containing the configuration values
        """
        pass
    
    @abstractmethod
    def set_config(self, user_id: str, config_type: str, config_data: Dict[str, Any]) -> None:
        """
        Set configuration for a specific user and configuration type.
        
        Args:
            user_id: The user's unique identifier
            config_type: The type of configuration to set (e.g., 'extraction', 'decision')
            config_data: The configuration data to store
        """
        pass