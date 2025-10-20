"""
Paper Trading Type Definitions

Common type definitions for paper trading components.
"""

from dataclasses import dataclass


@dataclass
class MarketPrice:
    """Market price data structure"""
    symbol: str
    bid: float
    ask: float
    last: float
    mid: float
    timestamp: float

    def __post_init__(self):
        if self.mid is None:
            self.mid = (self.bid + self.ask) / 2


@dataclass
class TradingRules:
    """Trading rules data structure"""
    symbol: str
    min_order_size: float
    max_order_size: float
    price_step: float
    size_step: float
    min_notional: float
