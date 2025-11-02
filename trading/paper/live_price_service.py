"""
Live Price Service

Provides real-time cryptocurrency prices with intelligent fallback:
1. WebSocket cache (100 symbols, <1ms, no rate limits) - PRIMARY
2. Binance REST API with caching (42 symbols, ~100ms, rate limited) - FALLBACK

This enables all 142 symbols for ggShot signal validation and paper trading
while maintaining performance and rate limit safety.
"""

import os
import pickle
import time
from typing import Dict, List, Optional
import redis.asyncio as redis
from dotenv import load_dotenv

from core.common.logger import logger
from .types import MarketPrice
from .hybrid_price_service import HybridPriceService

load_dotenv()


class LivePriceService:
    """
    Real-time price service with WebSocket-first, REST-fallback architecture.

    Delegates to HybridPriceService for intelligent price fetching across
    all 142 supported symbols.
    """

    def __init__(self):
        self.hybrid_service = HybridPriceService()
        self._log = logger.bind(component="live_price_service")

    async def get_current_price(self, symbol: str) -> MarketPrice:
        """
        Get current price with WebSocket-first, REST-fallback strategy.

        Supports all 142 symbols:
        - 100 symbols via WebSocket cache (<1ms, real-time)
        - 42 symbols via REST API with caching (~100ms, 5s cache TTL)

        Args:
            symbol: Trading pair in either format:
                    - Platform format with dash: 'BTC-USDT'
                    - CCXT/Binance format with slash: 'BTC/USDT'
                    Both are automatically normalized to slash format.

        Returns:
            MarketPrice with bid, ask, last, and mid prices

        Raises:
            Exception: If price cannot be retrieved
        """
        # Normalize symbol format: convert platform format (BTC-USDT) to CCXT format (BTC/USDT)
        # This makes the API format-agnostic and prevents symbol format errors
        if "-" in symbol:
            symbol = symbol.replace("-", "/")

        return await self.hybrid_service.get_current_price(symbol)

    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, MarketPrice]:
        """
        Get current prices for multiple symbols efficiently.

        Uses hybrid approach (WebSocket + REST fallback) for each symbol.

        Args:
            symbols: List of symbols in either format (BTC-USDT or BTC/USDT)
                     Both formats are automatically normalized.

        Returns:
            Dictionary mapping symbols to MarketPrice objects
        """
        results = {}

        for symbol in symbols:
            try:
                price = await self.get_current_price(symbol)
                results[symbol] = price
            except Exception as e:
                self._log.warning(f"Failed to get price for {symbol}: {e}")
                continue

        self._log.debug(f"Fetched {len(results)}/{len(symbols)} prices")
        return results

    async def health_check(self) -> Dict[str, any]:
        """
        Check health of live price service.

        Returns:
            Health status and diagnostic information
        """
        health_status = {
            "service": "live_price_service",
            "status": "unknown",
            "rate_limit": "unknown",
            "errors": []
        }

        try:
            # Test price fetching with BTC/USDT (WebSocket cached)
            await self.get_current_price("BTC/USDT")
            health_status["status"] = "healthy"

            # Get rate limit status
            rate_status = await self.hybrid_service.get_rate_limit_status()
            health_status["rate_limit"] = rate_status

        except Exception as e:
            health_status["status"] = "failed"
            health_status["errors"].append(f"Price fetch test failed: {str(e)}")

        return health_status

    async def close(self):
        """Close connections."""
        await self.hybrid_service.close()
        self._log.info("Live price service closed")


# Convenience functions for quick usage
async def get_live_price(symbol: str) -> MarketPrice:
    """Quick price lookup."""
    service = LivePriceService()
    return await service.get_current_price(symbol)


async def get_live_mid_price(symbol: str) -> float:
    """Get just the mid price for a symbol."""
    price = await get_live_price(symbol)
    return price.mid
