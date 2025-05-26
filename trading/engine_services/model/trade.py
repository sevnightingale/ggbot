"""
Trade models for the Trading Engine.

These models represent the trades being managed by the Trading Engine.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime


class TradeDirection(str, Enum):
    """Enum for trade direction (long or short)."""
    LONG = 'long'
    SHORT = 'short'


class TradeStatus(str, Enum):
    """Enum for trade status."""
    PENDING = 'pending'    # Trade decision received but not yet executed
    OPEN = 'open'          # Trade is active
    CLOSING = 'closing'    # Trade is in the process of being closed
    CLOSED = 'closed'      # Trade has been closed
    CANCELLED = 'cancelled'  # Trade was cancelled
    REJECTED = 'rejected'  # Trade was rejected
    ERROR = 'error'        # Error during trade execution or management


class Adjustment(BaseModel):
    """Model for a trade adjustment."""
    timestamp: str = Field(description="Timestamp of the adjustment")
    type: str = Field(description="Type of adjustment (e.g., 'stop_loss', 'take_profit')")
    previous_value: Optional[float] = Field(default=None, description="Previous value")
    new_value: Optional[float] = Field(default=None, description="New value")
    reason: Optional[str] = Field(default=None, description="Reason for the adjustment")
    execution_details: Optional[Dict[str, Any]] = Field(default=None, description="Execution details")


class Trade(BaseModel):
    """
    Model for a trade being managed by the Trading Engine.
    
    This represents a trade in the database and in memory.
    """
    trade_id: str = Field(description="Unique identifier for the trade")
    user_id: str = Field(description="User ID associated with the trade")
    decision_id: str = Field(description="Decision ID that created the trade")
    exchange: str = Field(description="Exchange where the trade was executed")
    symbol: str = Field(description="Trading pair symbol (e.g., 'BTC/USD')")
    direction: TradeDirection = Field(description="Trade direction (long or short)")
    
    # Status & timeline
    status: TradeStatus = Field(description="Current status of the trade")
    created_at: str = Field(description="Timestamp when the trade was created")
    entry_time: Optional[str] = Field(default=None, description="Timestamp when the trade was entered")
    last_updated: Optional[str] = Field(default=None, description="Timestamp when the trade was last updated")
    closed_at: Optional[str] = Field(default=None, description="Timestamp when the trade was closed")
    
    # Price & size information
    entry_price: Optional[float] = Field(default=None, description="Entry price of the trade")
    current_price: Optional[float] = Field(default=None, description="Current price of the trade")
    position_size: Optional[float] = Field(default=None, description="Size of the position")
    collateral_amount: Optional[float] = Field(default=None, description="Amount of collateral used")
    leverage: Optional[float] = Field(default=1.0, description="Leverage used for the trade")
    
    # Risk management
    stop_loss: Optional[float] = Field(default=None, description="Stop loss price")
    take_profit: Optional[float] = Field(default=None, description="Take profit price")
    liquidation_price: Optional[float] = Field(default=None, description="Liquidation price")
    
    # Performance
    unrealized_pnl: Optional[float] = Field(default=None, description="Unrealized profit/loss")
    profit_loss: Optional[float] = Field(default=None, description="Realized profit/loss")
    funding_paid: Optional[float] = Field(default=None, description="Funding fees paid")
    
    # Metadata
    confidence_score: Optional[float] = Field(default=None, description="Confidence score from decision")
    reasoning_log: Optional[str] = Field(default=None, description="Reasoning from decision")
    
    # Rejection/error information
    risk_rejected: Optional[bool] = Field(default=False, description="Whether rejected by risk rules")
    risk_reason: Optional[str] = Field(default=None, description="Reason for risk rejection")
    
    # Order IDs
    entry_order_id: Optional[str] = Field(default=None, description="Exchange order ID for entry")
    exit_order_id: Optional[str] = Field(default=None, description="Exchange order ID for exit")
    client_order_id: Optional[str] = Field(default=None, description="Client order ID")
    
    # Execution details & history
    execution_details: Optional[Dict[str, Any]] = Field(default=None, description="Raw execution details")
    adjustments: Optional[List[Adjustment]] = Field(default=None, description="History of adjustments")
    
    # Internal flags
    exit_triggered: Optional[bool] = Field(default=False, description="Whether exit has been triggered")
    
    @classmethod
    def from_db_record(cls, record: Dict[str, Any]) -> "Trade":
        """
        Create a Trade object from a database record.
        
        Args:
            record: Database record dictionary
            
        Returns:
            Trade object
        """
        # Map fields from DB record to Trade model
        # Convert snake_case DB fields to model fields
        mapping = {
            'trade_id': 'trade_id',
            'user_id': 'user_id',
            'decision_id': 'decision_id',
            'exchange': 'exchange',
            'pair': 'symbol',  # DB uses 'pair', model uses 'symbol'
            'direction': 'direction',
            'trade_status': 'status',  # DB uses 'trade_status', model uses 'status'
            'created_at': 'created_at',
            'entry_time': 'entry_time',
            'last_updated': 'last_updated',
            'closed_at': 'closed_at',
            'entry_price': 'entry_price',
            'current_price': 'current_price',
            'position_size': 'position_size',
            'collateral_amount': 'collateral_amount',
            'leverage': 'leverage',
            'stop_loss': 'stop_loss',
            'take_profit': 'take_profit',
            'liquidation_price': 'liquidation_price',
            'unrealized_pnl': 'unrealized_pnl',
            'profit_loss': 'profit_loss',
            'funding_paid': 'funding_paid',
            'confidence_score': 'confidence_score',
            'reasoning_log': 'reasoning_log',
            'risk_rejected': 'risk_rejected',
            'risk_reason': 'risk_reason',
            'entry_order_id': 'entry_order_id',
            'exit_order_id': 'exit_order_id',
            'client_order_id': 'client_order_id',
            'execution_details': 'execution_details',
            'adjustments': 'adjustments',
        }
        
        # Create a dictionary with mapped fields
        mapped_data = {}
        for db_field, model_field in mapping.items():
            if db_field in record:
                mapped_data[model_field] = record[db_field]
                
        # Handle special fields
        if 'status' in mapped_data:
            try:
                mapped_data['status'] = TradeStatus(mapped_data['status'])
            except ValueError:
                # Default to PENDING if status is invalid
                mapped_data['status'] = TradeStatus.PENDING
                
        if 'direction' in mapped_data:
            try:
                mapped_data['direction'] = TradeDirection(mapped_data['direction'])
            except ValueError:
                # Default to LONG if direction is invalid
                mapped_data['direction'] = TradeDirection.LONG
                
        # Create and return the Trade object
        return cls(**mapped_data)
        
    def to_db_record(self) -> Dict[str, Any]:
        """
        Convert a Trade object to a database record.
        
        Returns:
            Dictionary suitable for database storage
        """
        # Convert model to a dictionary
        data = self.model_dump()
        
        # Map fields from Trade model to DB record
        # Convert model fields to snake_case DB fields
        mapping = {
            'symbol': 'pair',  # Model uses 'symbol', DB uses 'pair'
            'status': 'trade_status',  # Model uses 'status', DB uses 'trade_status'
        }
        
        # Apply mapping
        for model_field, db_field in mapping.items():
            if model_field in data:
                data[db_field] = data.pop(model_field)
                
        # Convert enum values to strings
        if 'trade_status' in data and isinstance(data['trade_status'], TradeStatus):
            data['trade_status'] = data['trade_status'].value
            
        if 'direction' in data and isinstance(data['direction'], TradeDirection):
            data['direction'] = data['direction'].value
            
        return data