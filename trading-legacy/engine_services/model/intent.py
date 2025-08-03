"""
Intent model for the Trading Engine.

The Intent model represents a trading decision from the Decision Module.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class IntentAction(str, Enum):
    """Enum for intent action types."""
    ENTER_LONG = 'enter_long'
    ENTER_SHORT = 'enter_short'
    EXIT = 'exit'
    ADJUST = 'adjust'


class SizeType(str, Enum):
    """Enum for size types."""
    PERCENTAGE_EQUITY = 'percentage_equity'
    FIXED_USD = 'fixed_usd'
    FIXED_CONTRACTS = 'fixed_contracts'


class Intent(BaseModel):
    """
    Model for a decision intent from the Decision Module.
    
    This represents a trading decision that needs to be executed.
    """
    decision_id: str = Field(description="Unique identifier for the decision")
    action: str = Field(description="Action to perform (enter_long, enter_short, exit, adjust)")
    symbol: str = Field(description="Trading pair symbol (e.g., 'BTC/USD')")
    exchange: str = Field(description="Exchange to use for the trade")
    
    # Additional fields based on action type
    timeframe: Optional[str] = Field(default=None, description="Timeframe for the trade")
    leverage: Optional[float] = Field(default=1.0, description="Leverage to use for the trade")
    
    # Size information (for entries)
    size_type: Optional[str] = Field(default=None, description="Type of size specification")
    size_value: Optional[float] = Field(default=None, description="Size value")
    
    # Price levels (for entries, adjustments)
    stop_loss_price: Optional[float] = Field(default=None, description="Stop loss price")
    take_profit_price: Optional[float] = Field(default=None, description="Take profit price")
    
    # For exits and adjustments
    trade_id: Optional[str] = Field(default=None, description="Trade ID for exits and adjustments")
    
    # Metadata
    confidence: Optional[float] = Field(default=None, description="Confidence score for the decision")
    reasoning: Optional[str] = Field(default=None, description="Reasoning behind the decision")
    auto_exit: Optional[bool] = Field(default=False, description="Whether this is an automatic exit")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate that action is one of the supported actions."""
        try:
            return IntentAction(v).value
        except ValueError:
            raise ValueError(f"Invalid action: {v}. Must be one of: {[a.value for a in IntentAction]}")
        
    @field_validator('size_type')
    @classmethod
    def validate_size_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate that size_type is one of the supported size types."""
        if v is None:
            return v
        try:
            return SizeType(v).value
        except ValueError:
            raise ValueError(f"Invalid size_type: {v}. Must be one of: {[s.value for s in SizeType]}")
    
    @field_validator('trade_id')
    @classmethod
    def validate_trade_id(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Validate that trade_id is provided for exit and adjust actions."""
        action = values.data.get('action')
        if action in [IntentAction.EXIT.value, IntentAction.ADJUST.value] and not v:
            raise ValueError(f"trade_id is required for {action} action")
        return v