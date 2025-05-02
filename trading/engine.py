# trading/engine.py

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import uuid

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from trading.interfaces import Exchange, TradeRecord


class TradingEngine:
    """
    Main trading engine that coordinates between exchanges, trade records, and strategies.
    
    This class manages the lifecycle of trades, from creation to closure, and handles
    interactions with exchanges for executing trades and monitoring positions.
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        """
        Initialize the trading engine.
        
        Args:
            user_id: User ID to associate with trades (defaults to DEFAULT_USER_ID)
        """
        self.user_id = user_id
        self.exchanges = {}
        self.trade_record = None
        self.logger = logger.bind(user_id=user_id)
    
    def register_exchange(self, name: str, exchange: Exchange) -> None:
        """
        Register an exchange implementation.
        
        Args:
            name: Name to register the exchange under
            exchange: Exchange implementation
        """
        self.exchanges[name] = exchange
        self.logger.info(f"Registered exchange: {name}")
    
    def register_trade_record(self, trade_record: TradeRecord) -> None:
        """
        Register a trade record implementation.
        
        Args:
            trade_record: TradeRecord implementation
        """
        self.trade_record = trade_record
        self.logger.info("Registered trade record")
    
    def execute_trade(self, 
                      decision: str, 
                      symbol: str, 
                      amount: float,
                      price: Optional[float] = None,
                      stop_loss: Optional[float] = None,
                      take_profit: Optional[float] = None,
                      exchange_name: str = "default",
                      strategy_name: Optional[str] = None,
                      params: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Execute a trade based on a decision.
        
        Args:
            decision: Trade decision ('buy', 'sell', 'close')
            symbol: Trading pair symbol (e.g., 'BTC/USD')
            amount: Position size (as absolute amount or percentage of capital)
            price: Order price (for limit orders, None for market orders)
            stop_loss: Stop loss price level
            take_profit: Take profit price level
            exchange_name: Name of the exchange to use
            strategy_name: Name of the strategy making the decision
            params: Additional parameters for the exchange
            
        Returns:
            Tuple containing (success flag, message, trade_id)
        """
        # Validate inputs
        if not decision or not symbol or amount <= 0:
            return False, "Invalid trade parameters", None
        
        # Check if exchange is registered
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            return False, f"Exchange '{exchange_name}' not registered", None
        
        # Check if trade record is registered
        if not self.trade_record:
            return False, "No trade record implementation registered", None
        
        # Map decision to order parameters
        side = "buy" if decision == "buy" else "sell"
        order_type = "market" if price is None else "limit"
        
        # Add stop loss and take profit to params if provided
        params = params or {}
        if stop_loss is not None:
            params["stopLoss"] = stop_loss
        if take_profit is not None:
            params["takeProfit"] = take_profit
        
        try:
            # Execute the order on the exchange
            self.logger.info(f"Executing {order_type} {side} order for {amount} {symbol}")
            order_result = exchange.create_order(
                symbol=symbol,
                order_type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params
            )
            
            # Create a trade record
            trade_id = self.trade_record.create_trade(
                user_id=self.user_id,
                symbol=symbol,
                side=side,
                amount=amount,
                entry_price=price or order_result.get("price"),
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy_name=strategy_name,
                exchange_id=exchange_name
            )
            
            self.logger.info(f"Trade executed successfully: {trade_id}")
            return True, "Trade executed successfully", str(trade_id)
        
        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")
            return False, f"Error executing trade: {str(e)}", None
    
    def close_trade(self, 
                    trade_id: str, 
                    price: Optional[float] = None) -> Tuple[bool, str]:
        """
        Close an existing trade.
        
        Args:
            trade_id: ID of the trade to close
            price: Closing price (None for market close)
            
        Returns:
            Tuple containing (success flag, message)
        """
        if not self.trade_record:
            return False, "No trade record implementation registered"
        
        try:
            # Get the trade details
            trade = self.trade_record.get_trade(uuid.UUID(trade_id))
            if not trade:
                return False, f"Trade not found: {trade_id}"
            
            if trade.get("status") == "closed":
                return False, f"Trade already closed: {trade_id}"
            
            # Get the exchange
            exchange_name = trade.get("exchange_id", "default")
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                return False, f"Exchange '{exchange_name}' not registered"
            
            # Close the position on the exchange
            symbol = trade.get("symbol")
            side = "sell" if trade.get("side") == "buy" else "buy"  # Reverse side for closing
            amount = trade.get("amount")
            
            order_result = exchange.create_order(
                symbol=symbol,
                order_type="market" if price is None else "limit",
                side=side,
                amount=amount,
                price=price
            )
            
            # Calculate PnL (simplified)
            entry_price = float(trade.get("entry_price", 0))
            exit_price = price or float(order_result.get("price", 0))
            side_multiplier = 1 if trade.get("side") == "buy" else -1
            pnl = side_multiplier * (exit_price - entry_price) * amount
            
            # Update the trade record
            self.trade_record.update_trade(
                trade_id=uuid.UUID(trade_id),
                status="closed",
                exit_price=exit_price,
                exit_time=datetime.now(),
                pnl=pnl
            )
            
            self.logger.info(f"Trade closed: {trade_id}, PnL: {pnl}")
            return True, f"Trade closed successfully, PnL: {pnl}"
        
        except Exception as e:
            self.logger.error(f"Error closing trade: {str(e)}")
            return False, f"Error closing trade: {str(e)}"
    
    def get_active_trades(self) -> List[Dict[str, Any]]:
        """
        Get all active trades for the current user.
        
        Returns:
            List of dictionaries containing active trade records
        """
        if not self.trade_record:
            return []
        
        try:
            return self.trade_record.get_user_trades(
                user_id=self.user_id,
                status="open"
            )
        except Exception as e:
            self.logger.error(f"Error fetching active trades: {str(e)}")
            return []
    
    def update_trade_parameters(self, 
                               trade_id: str, 
                               stop_loss: Optional[float] = None, 
                               take_profit: Optional[float] = None) -> bool:
        """
        Update parameters for an existing trade.
        
        Args:
            trade_id: ID of the trade to update
            stop_loss: New stop loss level
            take_profit: New take profit level
            
        Returns:
            Boolean indicating success
        """
        if not self.trade_record:
            return False
        
        try:
            # Get the trade details
            trade = self.trade_record.get_trade(uuid.UUID(trade_id))
            if not trade:
                return False
            
            if trade.get("status") != "open":
                return False  # Can only update open trades
            
            # Get the exchange
            exchange_name = trade.get("exchange_id", "default")
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                return False
            
            # Update the stop loss/take profit on the exchange if needed
            # This is implementation-specific and would depend on the exchange API
            
            # Update the trade record
            return self.trade_record.update_trade(
                trade_id=uuid.UUID(trade_id),
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        
        except Exception as e:
            self.logger.error(f"Error updating trade parameters: {str(e)}")
            return False