"""
Redis WebSocket Adapter for OHLCV data.

Reads OHLCV candle data from Redis cache populated by the WebSocket
market data service (market-data-ws PM2 process).
"""

import os
import pickle
from typing import Optional
import pandas as pd
import redis.asyncio as redis

from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse, AdapterError


class RedisWebSocketAdapter(DataAdapter):
    """
    Adapter for reading OHLCV from WebSocket-populated Redis cache.

    This adapter reads from the same Redis cache that the websocket_market_data_service
    populates in real-time. Data structure:
    - Key: candles:{symbol}:{timeframe}:200
    - Value: Pickled list of OHLCV dicts with 200 candles
    """

    name = "redis_websocket"
    data_type = "ohlcv"

    def __init__(self):
        """Initialize Redis WebSocket adapter."""
        super().__init__()
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client: Optional[redis.Redis] = None

    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if not self.redis_client:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False  # Handle binary data (pickled)
            )
            await self.redis_client.ping()
        return self.redis_client

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Fetch OHLCV data from Redis WebSocket cache.

        Args:
            params: Query parameters with symbol, timeframe, limit

        Returns:
            AdapterResponse with DataFrame

        Raises:
            AdapterError: If data not found in cache or fetch fails
        """
        symbol = params.symbol
        timeframe = params.timeframe
        limit = params.get('limit', 200)

        # Build Redis key (matches WebSocket service key pattern with ws: prefix)
        cache_key = f"ws:candles:{symbol}:{timeframe}:200"

        self._log.info(f"Fetching OHLCV from Redis: {cache_key}")

        try:
            client = await self._get_redis_client()

            # Get data from Redis
            data = await client.get(cache_key)
            if not data:
                raise AdapterError(
                    f"No data in Redis for {cache_key}. "
                    f"WebSocket service may not be running or symbol not cached."
                )

            # Unpickle the candle data
            candles = pickle.loads(data)

            if not candles:
                raise AdapterError(f"Empty candle list for {symbol} {timeframe}")

            # Convert to pandas DataFrame (matching HummingbotDataClient format)
            df = pd.DataFrame(candles)

            # Convert timestamp from milliseconds to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            # Sort by timestamp (oldest first)
            df = df.sort_values('timestamp').reset_index(drop=True)

            # Limit to requested number of candles
            if len(df) > limit:
                df = df.tail(limit).reset_index(drop=True)

            self._log.info(f"✅ Retrieved {len(df)} candles from Redis WebSocket cache")

            # Calculate confidence (data is real-time from WebSocket, so high confidence)
            # Lower if data is stale
            latest_timestamp = df['timestamp'].iloc[-1]
            freshness_seconds = (pd.Timestamp.now(tz='UTC') - latest_timestamp).total_seconds()
            confidence = self.calculate_confidence(
                sample_size=len(df),
                freshness_seconds=freshness_seconds
            )

            return AdapterResponse(
                data=df,
                metadata=self.build_metadata(
                    source="redis_websocket",
                    cache_key=cache_key,
                    candle_count=len(df),
                    latest_timestamp=latest_timestamp.isoformat(),
                    freshness_seconds=freshness_seconds
                ),
                confidence=confidence,
                related_queries=self._suggest_related_queries(symbol, timeframe)
            )

        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(f"Failed to fetch from Redis WebSocket cache: {e}")

    def _suggest_related_queries(self, symbol: str, timeframe: str) -> list:
        """Suggest related queries for discovery."""
        # Suggest other timeframes for same symbol
        other_timeframes = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        related = []

        for tf in other_timeframes:
            if tf != timeframe:
                related.append(f"ohlcv:{symbol}:{tf}")
                if len(related) >= 3:
                    break

        return related

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
        await super().close()
