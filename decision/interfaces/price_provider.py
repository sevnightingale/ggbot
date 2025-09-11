"""
Price Provider Interface for the Decision Module.

This module defines the abstract base class that all price providers must implement.
Price providers handle fetching current market prices from different data sources.
"""

from abc import ABC, abstractmethod
from typing import Optional


class PriceProvider(ABC):
    """
    Abstract base class for all price providers.
    
    This interface abstracts the communication with different price data sources
    (YFinance, CCXT exchanges, CoinGecko, etc.) and provides a standardized way
    to fetch current market prices for trading symbols.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the price provider with necessary settings.
        
        Args:
            **kwargs: Provider-specific configuration options
        """
        self.kwargs = kwargs
    
    @abstractmethod
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get the current market price for a trading symbol.
        
        Args:
            symbol (str): Trading symbol in standard format (e.g., 'BTC/USDT', 'ETH/USD')
            
        Returns:
            Optional[float]: Current price as a float, or None if unable to fetch
            
        Raises:
            ValueError: If symbol format is invalid or not supported
            ConnectionError: If unable to connect to the data source
        """
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> list[str]:
        """
        Get list of symbols supported by this price provider.
        
        Returns:
            list[str]: List of supported trading symbols
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this price provider.
        
        Returns:
            str: Provider name (e.g., 'yfinance', 'ccxt_binance', 'coingecko')
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the price provider is accessible and functioning.
        
        This method should make a minimal API call to verify connectivity
        without consuming significant resources.
        
        Returns:
            bool: True if the provider is accessible, False otherwise
        """
        pass
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Helper method to normalize symbol format.
        
        Args:
            symbol (str): Input symbol in any format
            
        Returns:
            str: Normalized symbol format for this provider
        """
        # Default implementation - providers can override
        return symbol.upper().replace('/', '').replace('-', '').replace(':', '')