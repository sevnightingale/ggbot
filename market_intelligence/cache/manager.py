"""
Cache manager for market intelligence data.

Coordinates caching across multiple backends (Redis, PostgreSQL, in-memory)
based on data type and configuration.
"""

from typing import Any, Optional
import os

from core.common.logger import logger
from market_intelligence.types import CacheConfig, CacheError
from market_intelligence.cache.redis_cache import RedisCache


class CacheManager:
    """
    Multi-backend cache manager.

    Routes cache operations to appropriate backend based on configuration.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache manager.

        Args:
            redis_url: Redis connection URL (defaults to env var or localhost)
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self._redis: Optional[RedisCache] = None
        # Future: self._postgres, self._memory
        self._log = logger.bind(component="cache_manager")

    async def get_redis(self) -> RedisCache:
        """Get or create Redis cache instance."""
        if not self._redis:
            self._redis = RedisCache(self.redis_url)
            await self._redis.connect()
        return self._redis

    async def get(self, key: str, cache_config: CacheConfig) -> Optional[Any]:
        """
        Get value from appropriate cache backend.

        Args:
            key: Cache key
            cache_config: Cache configuration from catalog

        Returns:
            Cached value or None if not found

        Raises:
            CacheError: If cache operation fails
        """
        backend = cache_config.backend

        try:
            if backend == "redis":
                redis_cache = await self.get_redis()
                value = await redis_cache.get(key)
                if value:
                    self._log.debug(f"Cache hit: {key}")
                    return value
                else:
                    self._log.debug(f"Cache miss: {key}")
                    return None

            elif backend == "postgres":
                # Future: PostgreSQL cache
                self._log.warning(f"PostgreSQL cache not yet implemented, skipping cache for {key}")
                return None

            elif backend == "memory":
                # Future: In-memory cache
                self._log.warning(f"Memory cache not yet implemented, skipping cache for {key}")
                return None

            else:
                raise CacheError(f"Unknown cache backend: {backend}")

        except CacheError:
            raise
        except Exception as e:
            self._log.error(f"Cache get failed for {key}: {e}")
            # Don't raise - allow fallback to source fetch
            return None

    async def set(self, key: str, value: Any, cache_config: CacheConfig):
        """
        Set value in appropriate cache backend.

        Args:
            key: Cache key
            value: Value to cache
            cache_config: Cache configuration from catalog

        Raises:
            CacheError: If cache operation fails
        """
        backend = cache_config.backend
        ttl = cache_config.ttl

        try:
            if backend == "redis":
                redis_cache = await self.get_redis()
                await redis_cache.set(key, value, ttl)
                self._log.debug(f"Cached to Redis: {key} (TTL: {ttl}s)")

            elif backend == "postgres":
                # Future: PostgreSQL cache
                self._log.warning(f"PostgreSQL cache not yet implemented, skipping cache for {key}")

            elif backend == "memory":
                # Future: In-memory cache
                self._log.warning(f"Memory cache not yet implemented, skipping cache for {key}")

            else:
                raise CacheError(f"Unknown cache backend: {backend}")

        except CacheError:
            raise
        except Exception as e:
            self._log.error(f"Cache set failed for {key}: {e}")
            # Don't raise - caching is optional

    async def delete(self, key: str, cache_config: CacheConfig):
        """
        Delete key from appropriate cache backend.

        Args:
            key: Cache key
            cache_config: Cache configuration from catalog

        Raises:
            CacheError: If cache operation fails
        """
        backend = cache_config.backend

        try:
            if backend == "redis":
                redis_cache = await self.get_redis()
                await redis_cache.delete(key)
                self._log.debug(f"Deleted from Redis: {key}")

            elif backend == "postgres":
                # Future: PostgreSQL cache
                pass

            elif backend == "memory":
                # Future: In-memory cache
                pass

        except Exception as e:
            self._log.warning(f"Cache delete failed for {key}: {e}")
            # Don't raise - deletion failure is not critical

    async def invalidate_pattern(self, pattern: str, cache_config: CacheConfig):
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Redis pattern (e.g., "market:ohlcv:*")
            cache_config: Cache configuration from catalog
        """
        backend = cache_config.backend

        if backend == "redis":
            redis_cache = await self.get_redis()
            if redis_cache.client:
                keys = []
                async for key in redis_cache.client.scan_iter(match=pattern):
                    keys.append(key)

                if keys:
                    await redis_cache.client.delete(*keys)
                    self._log.info(f"Invalidated {len(keys)} keys matching pattern: {pattern}")

    async def close(self):
        """Close all cache connections."""
        if self._redis:
            await self._redis.close()
            self._redis = None

        self._log.info("Cache manager closed")
