#!/usr/bin/env python
"""
Interfaces for the Trading Module.

This module defines interfaces (abstract classes) that standardize
the structure of various trading components.

STATUS: IMPLEMENTED - PARTIALLY COMPLETE
This file contains the core interface definitions for the Trading Module,
defining the contract that concrete implementations must follow.
Includes:
- TradeDirection enum
- TradeStatus enum
- TradingInterface abstract class
- ExchangeInterface abstract class

NEXT STEPS:
- Add TradeIntent interface for standardized Decision Module communication
- Add TradeCompilerInterface for the compiler component
- Add TradeManagerInterface for position tracking components
- Update TradingInterface to match the revised architecture
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from uuid import UUID


class TradeDirection(Enum):
    """Enum for trade direction (long or short)."""
    LONG = 'long'
    SHORT = 'short'


class TradeStatus(Enum):
    """Enum for trade status."""
    PENDING = 'pending'  # Trade decision received but not yet executed
    OPEN = 'open'        # Trade is active
    CLOSED = 'closed'    # Trade has been closed
    CANCELLED = 'cancelled'  # Trade was cancelled
    ERROR = 'error'      # Error during trade execution or management


class TradingInterface(ABC):
    """
    Interface for the trading components.
    
    Defines the standard methods that must be implemented by
    any trading component.
    """
    
    @abstractmethod
    async def process_decision(self, decision: Dict) -> Dict:
        """
        Process a trading decision from the Decision Module.
        
        Args:
            decision: Dictionary containing the trading decision
            
        Returns:
            Dictionary with execution results
        """
        pass
    
    @abstractmethod
    async def get_trade_status(self, trade_id: Union[str, UUID]) -> Dict:
        """
        Get the current status of a trade.
        
        Args:
            trade_id: Unique identifier of the trade
            
        Returns:
            Dictionary with trade status information
        """
        pass
    
    @abstractmethod
    async def get_active_trades(self) -> Dict:
        """
        Get a list of all active trades.
        
        Returns:
            Dictionary with a list of active trade records
        """
        pass


class ExchangeInterface(ABC):
    """
    Interface for exchange adapters.
    
    Defines the standard methods that must be implemented by
    any exchange adapter.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the exchange.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the exchange.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def ensure_connected(self) -> bool:
        """
        Ensure connection to the exchange is established.
        
        Returns:
            True if connected, False otherwise
        """
        pass
    
    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Dict:
        """
        Fetch current ticker data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USD')
            
        Returns:
            Dictionary containing ticker data
        """
        pass
    
    @abstractmethod
    async def fetch_ohlcv(self, 
                         symbol: str, 
                         timeframe: str = '1h', 
                         since: Optional[int] = None, 
                         limit: Optional[int] = None) -> List:
        """
        Fetch OHLCV (candle) data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USD')
            timeframe: Timeframe (e.g., '1m', '1h', '1d')
            since: Optional timestamp in milliseconds to fetch data since
            limit: Optional limit on number of candles to fetch
            
        Returns:
            List of OHLCV candles [timestamp, open, high, low, close, volume]
        """
        pass
    
    @abstractmethod
    async def create_market_buy_order(self, 
                                     symbol: str, 
                                     amount: float, 
                                     params: Optional[Dict] = None) -> Dict:
        """
        Create a market buy order.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USD')
            amount: Amount to buy
            params: Optional additional parameters
            
        Returns:
            Dictionary containing order details
        """
        pass
    
    @abstractmethod
    async def create_market_sell_order(self, 
                                      symbol: str, 
                                      amount: float, 
                                      params: Optional[Dict] = None) -> Dict:
        """
        Create a market sell order.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USD')
            amount: Amount to sell
            params: Optional additional parameters
            
        Returns:
            Dictionary containing order details
        """
        pass