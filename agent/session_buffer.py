"""
Session Buffer - Temporary storage for market data between agent tool calls.

The session buffer acts like a clipboard - it holds market data fetched by
query_market_data so that consult_rei_for_decision can access it without
Claude needing to carry the full JSON payload in context.

Architecture:
    1. query_market_data fetches 32 data points, stores in buffer
    2. Claude receives summary: "Data ready. RSI=57.9, ADX=38.0"
    3. consult_rei_for_decision reads full data from buffer
    4. Buffer clears after Rei consultation

This pattern:
- Reduces Claude's token usage (doesn't carry full JSON)
- Preserves numerical precision for Rei (Float64)
- Keeps data fresh (cleared after each decision cycle)

Usage:
    buffer = SessionBuffer()

    # In query_market_data tool:
    buffer.store("config_123", market_data)

    # In consult_rei_for_decision tool:
    data = buffer.retrieve("config_123")  # Returns and clears
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from threading import Lock

from core.common.logger import logger


@dataclass
class BufferEntry:
    """Single entry in the session buffer."""
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    symbol: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionBuffer:
    """
    Thread-safe session buffer for market data.

    Stores market data temporarily between agent tool calls.
    Data expires after TTL to prevent stale data usage.
    """

    DEFAULT_TTL = 300  # 5 minutes - enough for a decision cycle

    def __init__(self, ttl: int = DEFAULT_TTL):
        """
        Initialize session buffer.

        Args:
            ttl: Time-to-live in seconds for buffer entries
        """
        self._buffer: Dict[str, BufferEntry] = {}
        self._lock = Lock()
        self._ttl = ttl
        self._log = logger.bind(component="session_buffer")

    def store(
        self,
        session_key: str,
        data: Dict[str, Any],
        symbol: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store market data in buffer.

        Args:
            session_key: Unique key (typically config_id or user_id:symbol)
            data: Market data dict (technical indicators + market intelligence)
            symbol: Trading symbol for reference
            metadata: Optional metadata (data point counts, fetch time, etc.)
        """
        with self._lock:
            entry = BufferEntry(
                data=data,
                timestamp=time.time(),
                symbol=symbol,
                metadata=metadata or {}
            )
            self._buffer[session_key] = entry

            data_size = len(str(data))
            self._log.debug(
                f"Stored buffer entry: key={session_key}, symbol={symbol}, "
                f"size={data_size} bytes"
            )

    def retrieve(
        self,
        session_key: str,
        clear: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve market data from buffer.

        Args:
            session_key: Key used when storing
            clear: If True, removes entry after retrieval (default)

        Returns:
            Market data dict or None if not found/expired
        """
        with self._lock:
            entry = self._buffer.get(session_key)

            if entry is None:
                self._log.warning(f"Buffer miss: key={session_key}")
                return None

            # Check TTL
            age = time.time() - entry.timestamp
            if age > self._ttl:
                self._log.warning(
                    f"Buffer entry expired: key={session_key}, age={age:.1f}s > TTL={self._ttl}s"
                )
                del self._buffer[session_key]
                return None

            # Retrieve data
            data = entry.data

            if clear:
                del self._buffer[session_key]
                self._log.debug(f"Retrieved and cleared buffer: key={session_key}")
            else:
                self._log.debug(f"Retrieved buffer (kept): key={session_key}")

            return data

    def peek(self, session_key: str) -> Optional[BufferEntry]:
        """
        Peek at buffer entry without removing it.

        Args:
            session_key: Key to look up

        Returns:
            BufferEntry or None
        """
        with self._lock:
            entry = self._buffer.get(session_key)
            if entry and (time.time() - entry.timestamp) <= self._ttl:
                return entry
            return None

    def has_data(self, session_key: str) -> bool:
        """
        Check if buffer has valid (non-expired) data for key.

        Args:
            session_key: Key to check

        Returns:
            True if valid data exists
        """
        entry = self.peek(session_key)
        return entry is not None

    def clear(self, session_key: str) -> bool:
        """
        Explicitly clear a buffer entry.

        Args:
            session_key: Key to clear

        Returns:
            True if entry was cleared, False if not found
        """
        with self._lock:
            if session_key in self._buffer:
                del self._buffer[session_key]
                self._log.debug(f"Cleared buffer: key={session_key}")
                return True
            return False

    def clear_all(self) -> int:
        """
        Clear all buffer entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._buffer)
            self._buffer.clear()
            self._log.info(f"Cleared all buffer entries: count={count}")
            return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self._buffer.items()
                if (now - entry.timestamp) > self._ttl
            ]

            for key in expired_keys:
                del self._buffer[key]

            if expired_keys:
                self._log.debug(f"Cleaned up {len(expired_keys)} expired entries")

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics.

        Returns:
            Dict with entry count, total size, oldest entry age, etc.
        """
        with self._lock:
            now = time.time()

            if not self._buffer:
                return {
                    "entry_count": 0,
                    "total_size_bytes": 0,
                    "oldest_age_seconds": 0,
                    "keys": []
                }

            ages = [now - entry.timestamp for entry in self._buffer.values()]
            sizes = [len(str(entry.data)) for entry in self._buffer.values()]

            return {
                "entry_count": len(self._buffer),
                "total_size_bytes": sum(sizes),
                "oldest_age_seconds": max(ages) if ages else 0,
                "newest_age_seconds": min(ages) if ages else 0,
                "keys": list(self._buffer.keys())
            }


# Global session buffer instance
# Used by agent MCP tools to share data between calls
_global_buffer: Optional[SessionBuffer] = None


def get_session_buffer() -> SessionBuffer:
    """
    Get the global session buffer instance.

    Returns:
        SessionBuffer singleton
    """
    global _global_buffer
    if _global_buffer is None:
        _global_buffer = SessionBuffer()
    return _global_buffer


def reset_session_buffer() -> None:
    """Reset the global session buffer (for testing)."""
    global _global_buffer
    if _global_buffer:
        _global_buffer.clear_all()
    _global_buffer = None
