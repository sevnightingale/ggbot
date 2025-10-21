"""
Live Price Service

Provides real-time cryptocurrency prices from WebSocket-cached data.
Replaces Hummingbot API dependency with direct Redis access to live candle data.
"""

import os
import pickle
import time
from typing import Dict, List, Optional
import redis.asyncio as redis
from dotenv import load_dotenv

from core.common.logger import logger
from .types import MarketPrice

load_dotenv()


class LivePriceService:
    """
    Real-time price service using WebSocket-cached live candles.

    This service accesses the same Redis cache populated by the WebSocket
    market data service (market-data-ws PM2 process). Live candles are updated
    every ~1 second as trades happen on Binance.
    """

    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client: Optional[redis.Redis] = None
        self._log = logger.bind(component="live_price_service")

    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if not self.redis_client:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False  # Handle binary data (pickled)
            )
            await self.redis_client.ping()
        return self.redis_client

    async def get_current_price(self, symbol: str) -> MarketPrice:
        """
        Get current price for a symbol from candle data.

        First tries live candle (if available), then falls back to latest closed candle.

        Args:
            symbol: Trading pair in internal format (e.g., 'BTC/USDT')

        Returns:
            MarketPrice with bid, ask, last, and mid prices

        Raises:
            Exception: If no price data available
        """
        try:
            client = await self._get_redis_client()

            # Try live candle first
            live_key = f"price:live:{symbol}"
            data = await client.get(live_key)

            # Fallback to latest closed candle from 5m window
            if not data:
                candle_key = f"candles:{symbol}:5m:200"
                data = await client.get(candle_key)

                if not data:
                    raise Exception(
                        f"No price data for {symbol}. "
                        f"Ensure WebSocket service is running and symbol is in coverage list."
                    )

                # Unpickle and get latest candle
                candles = pickle.loads(data)
                if not candles:
                    raise Exception(f"Empty candle data for {symbol}")

                candle = candles[-1]  # Latest closed candle
                self._log.debug(f"Using latest closed candle for {symbol}")
            else:
                # Using live candle
                candle = pickle.loads(data)
                self._log.debug(f"Using live candle for {symbol}")

            price = float(candle['close'])

            # Simulate realistic bid/ask spread (0.05% typical for major pairs)
            spread_pct = 0.0005
            spread_amount = price * spread_pct

            market_price = MarketPrice(
                symbol=symbol,
                bid=price - spread_amount,
                ask=price + spread_amount,
                last=price,
                mid=price,  # Will be calculated as (bid + ask) / 2 in __post_init__
                timestamp=time.time()
            )

            self._log.debug(f"Price for {symbol}: ${market_price.mid:.2f}")
            return market_price

        except Exception as e:
            error_msg = str(e) or repr(e) or type(e).__name__
            self._log.error(f"Failed to get price for {symbol}: {error_msg}")
            raise

    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, MarketPrice]:
        """
        Get current prices for multiple symbols efficiently.

        Args:
            symbols: List of symbols in internal format

        Returns:
            Dictionary mapping symbols to MarketPrice objects
        """
        results = {}

        try:
            client = await self._get_redis_client()

            # Try to fetch all prices (live first, then fallback to candles)
            for symbol in symbols:
                try:
                    price = await self.get_current_price(symbol)
                    results[symbol] = price
                except Exception as e:
                    self._log.warning(f"Failed to get price for {symbol}: {e}")
                    continue

            self._log.debug(f"Fetched {len(results)}/{len(symbols)} prices")
            return results

        except Exception as e:
            error_msg = str(e) or repr(e) or type(e).__name__
            self._log.error(f"Failed to fetch multiple prices: {error_msg}")
            # Return what we have so far
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
            "redis": "unknown",
            "errors": []
        }

        try:
            # Test Redis connection
            client = await self._get_redis_client()
            await client.ping()
            health_status["redis"] = "healthy"

            # Test price fetching with BTC/USDT (should always be available)
            try:
                await self.get_current_price("BTC/USDT")
                health_status["status"] = "healthy"
            except Exception as e:
                health_status["status"] = "degraded"
                health_status["errors"].append(f"Price fetch test failed: {str(e)}")

        except Exception as e:
            health_status["redis"] = "failed"
            health_status["status"] = "failed"
            health_status["errors"].append(f"Redis connectivity failed: {str(e)}")

        return health_status

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
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
