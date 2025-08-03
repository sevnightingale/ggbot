"""
New Hummingbot-based Trading Module

Clean break replacement for the legacy CCXT-based trading system.
"""

from .services import MarketDataService, HummingbotExecutionAdapter, TradeIntent

__all__ = ['MarketDataService', 'HummingbotExecutionAdapter', 'TradeIntent']