"""
Hybrid Price Service

Provides real-time cryptocurrency prices with intelligent fallback:
1. WebSocket cache (100 symbols, <1ms, no rate limits) - PRIMARY
2. Binance REST API with 5s caching (42 symbols, ~100ms, rate limited) - FALLBACK

This enables:
- Fast autonomous trading for 100 WebSocket-cached symbols
- ggShot signal validation and paper trading for all 142 symbols
- Safe rate limit management
"""

import os
import time
import asyncio
from typing import Dict, Optional, Tuple
import pickle
import redis.asyncio as redis
from binance import AsyncClient
from dotenv import load_dotenv

from core.common.logger import logger
from .types import MarketPrice

load_dotenv()


class RateLimitTracker:
    """Monitors Binance REST API usage to prevent rate limit violations."""

    def __init__(self, limit_per_minute: int = 1200):
        """
        Args:
            limit_per_minute: Binance weight limit (default 1200)
        """
        self.limit = limit_per_minute
        self.calls = []  # List of (timestamp, weight) tuples
        self._log = logger.bind(component="rate_limit_tracker")

    def record_call(self, weight: int = 2):
        """Record a REST API call with its weight."""
        now = time.time()
        self.calls.append((now, weight))

        # Clean old calls (older than 1 minute)
        cutoff = now - 60
        self.calls = [(t, w) for t, w in self.calls if t > cutoff]

    def get_current_usage(self) -> Tuple[int, float]:
        """
        Get current rate limit usage.

        Returns:
            Tuple of (total_weight_used, usage_percentage)
        """
        now = time.time()
        cutoff = now - 60

        # Sum weight from last minute
        total_weight = sum(w for t, w in self.calls if t > cutoff)
        usage_pct = (total_weight / self.limit) * 100

        return total_weight, usage_pct

    async def check_and_throttle(self):
        """Check rate limit and throttle if necessary."""
        weight, usage_pct = self.get_current_usage()

        if usage_pct > 80:
            # Approaching limit - add delay
            delay = 0.5
            self._log.warning(
                f"Rate limit at {usage_pct:.1f}% ({weight}/{self.limit} weight/min) - throttling {delay}s"
            )
            await asyncio.sleep(delay)
        elif usage_pct > 90:
            # Very close to limit - longer delay
            delay = 2.0
            self._log.error(
                f"Rate limit at {usage_pct:.1f}% ({weight}/{self.limit} weight/min) - throttling {delay}s"
            )
            await asyncio.sleep(delay)


class HybridPriceService:
    """
    Hybrid price service with WebSocket-first, REST-fallback architecture.

    Architecture:
    - Tier 1 (100 symbols): WebSocket cache (sub-ms, no limits)
    - Tier 2 (42 symbols): REST API with 5s cache (100ms, rate limited)

    This enables:
    - All 142 symbols supported for ggShot + paper trading
    - Only 100 symbols for autonomous bot creation (performance requirement)
    - Safe rate limit management with monitoring and caching
    """

    # 5-second cache for REST API prices
    CACHE_TTL = 5.0

    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client: Optional[redis.Redis] = None
        self.binance_client: Optional[AsyncClient] = None

        # REST price cache: {symbol: (MarketPrice, timestamp)}
        self.rest_cache: Dict[str, Tuple[MarketPrice, float]] = {}

        # Rate limit tracking
        self.rate_tracker = RateLimitTracker()

        self._log = logger.bind(component="hybrid_price_service")

        # Stats
        self.stats = {
            "websocket_hits": 0,
            "rest_cache_hits": 0,
            "rest_api_calls": 0
        }

    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if not self.redis_client:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False  # Handle binary data (pickled)
            )
            await self.redis_client.ping()
        return self.redis_client

    async def _get_binance_client(self) -> AsyncClient:
        """Get or create Binance client."""
        if not self.binance_client:
            self.binance_client = await AsyncClient.create()
        return self.binance_client

    async def get_current_price(self, symbol: str) -> MarketPrice:
        """
        Get current price with WebSocket-first, REST-fallback strategy.

        Args:
            symbol: Trading pair in internal format (e.g., 'BTC/USDT')

        Returns:
            MarketPrice with bid, ask, last, and mid prices

        Raises:
            Exception: If price cannot be retrieved
        """
        try:
            # Strategy 1: Try WebSocket cache (100 symbols, <1ms)
            ws_price = await self._try_websocket_cache(symbol)
            if ws_price:
                self.stats["websocket_hits"] += 1
                return ws_price

            # Strategy 2: Try REST cache (5s TTL)
            cached_price = self._check_rest_cache(symbol)
            if cached_price:
                self.stats["rest_cache_hits"] += 1
                self._log.debug(f"REST cache hit for {symbol}")
                return cached_price

            # Strategy 3: Fetch from Binance REST API
            rest_price = await self._fetch_from_rest_api(symbol)
            self.stats["rest_api_calls"] += 1

            # Cache it
            self.rest_cache[symbol] = (rest_price, time.time())

            self._log.info(
                f"REST API fetch for {symbol}: ${rest_price.mid:.2f} "
                f"(Stats: WS={self.stats['websocket_hits']}, "
                f"Cache={self.stats['rest_cache_hits']}, "
                f"API={self.stats['rest_api_calls']})"
            )

            return rest_price

        except Exception as e:
            error_msg = str(e) or repr(e) or type(e).__name__
            self._log.error(f"Failed to get price for {symbol}: {error_msg}")
            raise

    async def _try_websocket_cache(self, symbol: str) -> Optional[MarketPrice]:
        """
        Try to get price from WebSocket cache.

        Returns:
            MarketPrice if found in cache, None otherwise
        """
        try:
            client = await self._get_redis_client()

            # Get live candle from WebSocket cache
            live_key = f"price:live:{symbol}"
            data = await client.get(live_key)

            if not data:
                return None

            # Unpickle live candle
            candle = pickle.loads(data)
            price = float(candle['close'])

            # Simulate realistic bid/ask spread (0.05% typical for major pairs)
            spread_pct = 0.0005
            spread_amount = price * spread_pct

            market_price = MarketPrice(
                symbol=symbol,
                bid=price - spread_amount,
                ask=price + spread_amount,
                last=price,
                mid=price,
                timestamp=time.time()
            )

            return market_price

        except Exception as e:
            # WebSocket cache miss - this is normal for non-cached symbols
            self._log.debug(f"WebSocket cache miss for {symbol}: {e}")
            return None

    def _check_rest_cache(self, symbol: str) -> Optional[MarketPrice]:
        """
        Check if we have a cached REST price that's still fresh.

        Returns:
            Cached MarketPrice if fresh, None otherwise
        """
        if symbol not in self.rest_cache:
            return None

        cached_price, cached_time = self.rest_cache[symbol]
        age = time.time() - cached_time

        if age < self.CACHE_TTL:
            return cached_price

        # Cache expired
        del self.rest_cache[symbol]
        return None

    async def _fetch_from_rest_api(self, symbol: str) -> MarketPrice:
        """
        Fetch current price from Binance REST API.

        Args:
            symbol: Trading pair in internal format (e.g., 'BTC/USDT')

        Returns:
            MarketPrice from API

        Raises:
            Exception: If API call fails
        """
        # Rate limit check and throttle if needed
        await self.rate_tracker.check_and_throttle()

        # Convert symbol format: BTC/USDT -> BTCUSDT
        binance_symbol = symbol.replace('/', '')

        try:
            client = await self._get_binance_client()

            # Fetch ticker (2 weight)
            ticker = await client.get_ticker(symbol=binance_symbol)

            # Record the API call
            self.rate_tracker.record_call(weight=2)

            # Extract price
            price = float(ticker['lastPrice'])
            bid = float(ticker.get('bidPrice', price * 0.9995))
            ask = float(ticker.get('askPrice', price * 1.0005))

            market_price = MarketPrice(
                symbol=symbol,
                bid=bid,
                ask=ask,
                last=price,
                mid=price,
                timestamp=time.time()
            )

            return market_price

        except Exception as e:
            self._log.error(f"Binance REST API error for {symbol}: {e}")
            raise Exception(f"Failed to fetch price from Binance API: {e}")

    async def get_rate_limit_status(self) -> Dict:
        """
        Get current rate limit status.

        Returns:
            Dictionary with rate limit info
        """
        weight, usage_pct = self.rate_tracker.get_current_usage()

        return {
            "weight_used": weight,
            "weight_limit": self.rate_tracker.limit,
            "usage_percentage": usage_pct,
            "status": "ok" if usage_pct < 80 else "warning" if usage_pct < 90 else "critical"
        }

    async def close(self):
        """Close connections."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

        if self.binance_client:
            await self.binance_client.close_connection()
            self.binance_client = None

        self._log.info("Hybrid price service closed")
