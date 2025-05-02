# trading/interfaces.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime


class Exchange(ABC):
    """
    Abstract interface for cryptocurrency exchange implementations.
    
    This interface defines the methods that all exchange implementations must provide
    to interact with cryptocurrency trading platforms. Implementations may use direct
    API access or connect through MCP adaptors.
    """
    
    @abstractmethod
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, **kwargs):
        """
        Initialize the exchange with credentials if needed.
        
        Args:
            api_key: API key for authentication (optional for MCP-based implementations)
            api_secret: API secret for authentication (optional for MCP-based implementations)
            **kwargs: Additional exchange-specific parameters
        """
        pass
    
    @abstractmethod
    def get_markets(self) -> List[Dict[str, Any]]:
        """
        Get a list of available markets/trading pairs.
        
        Returns:
            List of dictionaries containing market information
        """
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker data for a symbol.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC/USD')
            
        Returns:
            Dictionary containing ticker data
        """
        pass
    
    @abstractmethod
    def create_order(self, 
                     symbol: str, 
                     order_type: str, 
                     side: str, 
                     amount: float, 
                     price: Optional[float] = None, 
                     params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new order.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC/USD')
            order_type: Type of order ('market', 'limit', etc.)
            side: Order side ('buy' or 'sell')
            amount: Order quantity
            price: Order price (required for limit orders)
            params: Additional order parameters (e.g., leverage, stop price)
            
        Returns:
            Dictionary containing order information
        """
        pass
    
    @abstractmethod
    def get_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about an order.
        
        Args:
            order_id: The ID of the order to fetch
            symbol: The trading pair symbol (may be required by some exchanges)
            
        Returns:
            Dictionary containing order information
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an open order.
        
        Args:
            order_id: The ID of the order to cancel
            symbol: The trading pair symbol (may be required by some exchanges)
            
        Returns:
            Dictionary containing cancellation result
        """
        pass


class TradeRecord(ABC):
    """
    Abstract interface for trade record implementations.
    
    This interface defines methods for creating and managing trade records,
    which track all information about trades made on behalf of users.
    """
    
    @abstractmethod
    def create_trade(self, 
                     user_id: str, 
                     symbol: str, 
                     side: str, 
                     amount: float, 
                     entry_price: float, 
                     stop_loss: Optional[float] = None, 
                     take_profit: Optional[float] = None, 
                     strategy_name: Optional[str] = None,
                     exchange_id: Optional[str] = None) -> UUID:
        """
        Create a new trade record.
        
        Args:
            user_id: ID of the user making the trade
            symbol: The trading pair symbol (e.g., 'BTC/USD')
            side: Trade direction ('long' or 'short')
            amount: Position size
            entry_price: Entry price
            stop_loss: Stop loss price level (optional)
            take_profit: Take profit price level (optional)
            strategy_name: Name of the strategy used for the trade (optional)
            exchange_id: ID of the exchange where the trade was executed (optional)
            
        Returns:
            UUID of the created trade record
        """
        pass
    
    @abstractmethod
    def update_trade(self, 
                     trade_id: UUID, 
                     status: Optional[str] = None, 
                     exit_price: Optional[float] = None, 
                     exit_time: Optional[datetime] = None, 
                     pnl: Optional[float] = None,
                     stop_loss: Optional[float] = None,
                     take_profit: Optional[float] = None) -> bool:
        """
        Update an existing trade record.
        
        Args:
            trade_id: UUID of the trade record to update
            status: New trade status (e.g., 'open', 'closed', 'cancelled')
            exit_price: Exit price (when closing the trade)
            exit_time: Time when the trade was closed
            pnl: Profit/Loss amount
            stop_loss: Updated stop loss level
            take_profit: Updated take profit level
            
        Returns:
            Boolean indicating success
        """
        pass
    
    @abstractmethod
    def get_trade(self, trade_id: UUID) -> Dict[str, Any]:
        """
        Get a specific trade record.
        
        Args:
            trade_id: UUID of the trade record to fetch
            
        Returns:
            Dictionary containing the trade record
        """
        pass
    
    @abstractmethod
    def get_user_trades(self, 
                        user_id: str, 
                        status: Optional[str] = None, 
                        symbol: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all trade records for a user.
        
        Args:
            user_id: ID of the user
            status: Filter by trade status (optional)
            symbol: Filter by trading pair symbol (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of dictionaries containing trade records
        """
        pass