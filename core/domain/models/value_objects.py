"""
Value objects for the GGBot domain.

Value objects are immutable objects that represent concepts without identity.
They are defined by their attributes rather than a unique identifier.
"""

from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
import re


class Money(BaseModel):
    """
    Represents a monetary amount with currency.
    
    Immutable value object for financial calculations.
    """
    amount: Decimal = Field(..., description="Monetary amount")
    currency: str = Field(default="USD", description="Currency code")
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount has reasonable precision"""
        # Allow negative amounts for trading P&L (losses are real business data)
        return v.quantize(Decimal('0.00000001'))  # 8 decimal places
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code format"""
        if not v.isalpha() or len(v) != 3:
            raise ValueError("Currency must be 3-letter code (e.g., 'USD')")
        return v.upper()
    
    def add(self, other: 'Money') -> 'Money':
        """Add another Money object"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """Subtract another Money object"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)
    
    def multiply(self, factor: Decimal) -> 'Money':
        """Multiply by a factor"""
        return Money(amount=self.amount * factor, currency=self.currency)
    
    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"


class Symbol(BaseModel):
    """
    Represents a trading pair symbol with standardization.
    
    Handles conversion between different exchange formats:
    - Internal: BTC/USDT
    - BitMEX: BTC/USDT:USDT
    - Binance: BTCUSDT
    - Hummingbot: BTC-USDT
    """
    base: str = Field(..., description="Base currency (e.g., BTC)")
    quote: str = Field(..., description="Quote currency (e.g., USDT)")
    
    @field_validator('base', 'quote')
    @classmethod
    def validate_currency(cls, v):
        """Validate currency format"""
        if not v.isalpha() or len(v) < 2 or len(v) > 10:
            raise ValueError("Currency must be 2-10 letters")
        return v.upper()
    
    @property
    def internal_format(self) -> str:
        """Standard internal format: BTC/USDT"""
        return f"{self.base}/{self.quote}"
    
    @property
    def binance_format(self) -> str:
        """Binance format: BTCUSDT"""
        return f"{self.base}{self.quote}"
    
    @property
    def hummingbot_format(self) -> str:
        """Hummingbot format: BTC-USDT"""
        return f"{self.base}-{self.quote}"
    
    @property
    def bitmex_format(self) -> str:
        """BitMEX perpetual format: BTC/USDT:USDT"""
        return f"{self.base}/{self.quote}:{self.quote}"
    
    @classmethod
    def from_string(cls, symbol_str: str) -> 'Symbol':
        """
        Parse symbol from various string formats.
        
        Supports:
        - BTC/USDT (internal)
        - BTCUSDT (Binance)
        - BTC-USDT (Hummingbot)
        - BTC/USDT:USDT (BitMEX)
        """
        # BitMEX perpetual format
        if ':' in symbol_str:
            base_quote = symbol_str.split(':')[0]
            if '/' in base_quote:
                base, quote = base_quote.split('/')
                return cls(base=base, quote=quote)
        
        # Internal format
        if '/' in symbol_str:
            base, quote = symbol_str.split('/')
            return cls(base=base, quote=quote)
        
        # Hummingbot format
        if '-' in symbol_str:
            base, quote = symbol_str.split('-')
            return cls(base=base, quote=quote)
        
        # Binance format - need to guess split point
        # Common quote currencies to try
        quote_currencies = ['USDT', 'BUSD', 'USD', 'BTC', 'ETH', 'BNB']
        for quote in quote_currencies:
            if symbol_str.endswith(quote):
                base = symbol_str[:-len(quote)]
                if len(base) >= 2:  # Valid base currency
                    return cls(base=base, quote=quote)
        
        raise ValueError(f"Cannot parse symbol format: {symbol_str}")
    
    def __str__(self) -> str:
        return self.internal_format


class Confidence(BaseModel):
    """
    Represents AI confidence score with validation.
    
    Used for position sizing and decision quality metrics.
    """
    score: Decimal = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v):
        """Ensure score has reasonable precision"""
        return v.quantize(Decimal('0.001'))  # 3 decimal places
    
    @property
    def percentage(self) -> Decimal:
        """Get confidence as percentage (0-100)"""
        return self.score * 100
    
    @property
    def is_high_confidence(self) -> bool:
        """True if confidence >= 0.7"""
        return self.score >= Decimal('0.7')
    
    @property
    def is_low_confidence(self) -> bool:
        """True if confidence < 0.3"""
        return self.score < Decimal('0.3')
    
    def __str__(self) -> str:
        return f"{self.percentage:.1f}%"


class Timeframe(BaseModel):
    """
    Represents trading timeframes with standardization.
    
    Supports: 5m, 15m, 30m, 1h, 4h, 1d, 1w
    """
    value: str = Field(..., description="Timeframe string")
    
    @field_validator('value')
    @classmethod
    def validate_timeframe(cls, v):
        """Validate timeframe format"""
        valid_timeframes = ['5m', '15m', '30m', '1h', '4h', '1d', '1w']
        if v not in valid_timeframes:
            raise ValueError(f"Invalid timeframe: {v}. Must be one of {valid_timeframes}")
        return v
    
    @property
    def minutes(self) -> int:
        """Get timeframe in minutes"""
        mapping = {
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080
        }
        return mapping[self.value]
    
    @property
    def is_intraday(self) -> bool:
        """True if timeframe is less than 1 day"""
        return self.minutes < 1440
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.value == other
        elif isinstance(other, Timeframe):
            return self.value == other.value
        return False


# Immutable configuration ensures value objects cannot be modified
for cls in [Money, Symbol, Confidence, Timeframe]:
    cls.model_config = {
        'frozen': True,  # Make immutable
        'validate_assignment': True,
        'extra': 'forbid'
    }