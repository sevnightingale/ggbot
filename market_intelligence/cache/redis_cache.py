"""
Redis cache backend for market intelligence data.

Handles caching of real-time data (OHLCV, sentiment, news) with
sub-second access times.
"""

import pickle
from typing import Any, Optional
import redis.asyncio as redis

from core.common.logger import logger
from market_intelligence.types import CacheError


class RedisCache:
    """Redis cache backend for real-time market data."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        self._log = logger.bind(cache="redis")

    async def connect(self):
        """Establish Redis connection."""
        if not self.client:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=False  # Handle binary data (pickled objects)
            )
            await self.client.ping()
            self._log.info("Redis cache connected")

    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self.client = None
            self._log.info("Redis cache closed")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Unpickled value or None if not found

        Raises:
            CacheError: If Redis operation fails
        """
        if not self.client:
            await self.connect()

        try:
            data = await self.client.get(key)
            if data:
                return pickle.loads(data)
            return None

        except Exception as e:
            self._log.error(f"Redis get failed for key '{key}': {e}")
            raise CacheError(f"Failed to get from cache: {e}")

    async def set(self, key: str, value: Any, ttl: int):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time to live in seconds

        Raises:
            CacheError: If Redis operation fails
        """
        if not self.client:
            await self.connect()

        try:
            serialized = pickle.dumps(value)
            await self.client.setex(key, ttl, serialized)
            self._log.debug(f"Cached key '{key}' with TTL {ttl}s")

        except Exception as e:
            self._log.error(f"Redis set failed for key '{key}': {e}")
            raise CacheError(f"Failed to set in cache: {e}")

    async def delete(self, key: str):
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Raises:
            CacheError: If Redis operation fails
        """
        if not self.client:
            await self.connect()

        try:
            await self.client.delete(key)
            self._log.debug(f"Deleted cache key '{key}'")

        except Exception as e:
            self._log.error(f"Redis delete failed for key '{key}': {e}")
            raise CacheError(f"Failed to delete from cache: {e}")

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise

        Raises:
            CacheError: If Redis operation fails
        """
        if not self.client:
            await self.connect()

        try:
            return bool(await self.client.exists(key))

        except Exception as e:
            self._log.error(f"Redis exists check failed for key '{key}': {e}")
            raise CacheError(f"Failed to check cache key: {e}")

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, or None if key doesn't exist

        Raises:
            CacheError: If Redis operation fails
        """
        if not self.client:
            await self.connect()

        try:
            ttl = await self.client.ttl(key)
            return ttl if ttl > 0 else None

        except Exception as e:
            self._log.error(f"Redis TTL check failed for key '{key}': {e}")
            raise CacheError(f"Failed to get TTL: {e}")
