"""
Universal Data Client - Drop-in replacement for HummingbotDataClient.

This adapter provides the same interface as HummingbotDataClient but uses
the MarketIntelligence gateway under the hood, enabling WebSocket caching
and multi-source fallback.
"""

import asyncio
import pandas as pd
from typing import Dict, List, Any

from core.common.logger import logger
from market_intelligence.gateway import MarketIntelligence
from market_intelligence.types import QueryFormat


class UniversalDataClient:
    """
    Adapter that implements HummingbotDataClient interface using MarketIntelligence.

    This is a drop-in replacement - same methods, same return types, but uses
    the Universal Data Layer for better performance and flexibility.
    """

    def __init__(self):
        """Initialize Universal Data Client with MarketIntelligence gateway."""
        self.intelligence = MarketIntelligence()
        self._log = logger.bind(component="universal_data_client")
        self._log.info("UniversalDataClient initialized with MarketIntelligence gateway")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """
        No-op for compatibility with HummingbotDataClient interface.

        MarketIntelligence handles connections internally.
        """
        pass

    async def disconnect(self):
        """Close MarketIntelligence gateway and cleanup resources."""
        if self.intelligence:
            await self.intelligence.close()
            self._log.info("UniversalDataClient disconnected")

    async def ensure_connected(self):
        """
        No-op for compatibility with HummingbotDataClient interface.

        MarketIntelligence handles connections internally.
        """
        pass

    async def get_candles_with_fallback(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get OHLCV candle data using MarketIntelligence gateway.

        This method provides the same interface as HummingbotDataClient.get_candles_with_fallback()
        but uses the Universal Data Layer which includes:
        - WebSocket cache for real-time data (priority 1)
        - Binance REST API as fallback (priority 2)
        - Automatic adapter routing and failover

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Candle timeframe (e.g., "1h", "15m", "1d")
            limit: Number of candles to retrieve

        Returns:
            pandas DataFrame with columns: timestamp, open, high, low, close, volume

        Raises:
            Exception: If all data sources fail
        """
        self._log.info(f"Fetching {limit} {timeframe} candles for {symbol} via MarketIntelligence")

        try:
            # Shield the query from cancellation to prevent partial data corruption
            # This ensures the query completes even if the parent task is cancelled
            response = await asyncio.shield(
                self.intelligence.query(
                    data_type='ohlcv',
                    params={
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'limit': limit
                    },
                    format=QueryFormat.RAW  # Raw format returns DataFrame directly
                )
            )

            # Extract DataFrame from response
            df = response.data

            # Log performance metrics
            source_info = f"from {response.source}" if response.source != "cache" else "from cache"
            cache_status = "(cached)" if response.from_cache else "(fresh)"
            self._log.info(
                f"✅ Retrieved {len(df)} candles for {symbol} {source_info} {cache_status} "
                f"in {response.latency_ms:.0f}ms"
            )

            return df

        except asyncio.CancelledError:
            # Handle cancellation gracefully - log and return empty DataFrame
            # This prevents cascading failures when scheduler times out
            self._log.warning(
                f"⚠️ Data fetch cancelled for {symbol} {timeframe} - returning empty DataFrame. "
                f"This may indicate orchestrator timeout or scheduler misfire."
            )
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        except Exception as e:
            self._log.error(f"Failed to fetch candles for {symbol}: {e}")
            raise Exception(f"MarketIntelligence failed for {symbol}: {e}")

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test MarketIntelligence gateway functionality.

        Returns:
            Dictionary with connection status and gateway info
        """
        try:
            # Test with a simple query
            response = await self.intelligence.query(
                data_type='ohlcv',
                params={'symbol': 'BTC/USDT', 'timeframe': '1h', 'limit': 10},
                format=QueryFormat.RAW
            )

            return {
                "status": "connected",
                "gateway": "MarketIntelligence",
                "test_query": "BTC/USDT 1h",
                "candles_retrieved": len(response.data),
                "source": response.source,
                "latency_ms": response.latency_ms
            }

        except Exception as e:
            return {
                "status": "connection_failed",
                "gateway": "MarketIntelligence",
                "error": str(e)
            }

    def get_supported_timeframes(self) -> List[str]:
        """
        Get list of supported timeframes.

        Returns timeframes supported by the Universal Data Layer.

        Returns:
            List of supported timeframe strings
        """
        return ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]

    def get_supported_connectors(self) -> List[str]:
        """
        Get list of data sources in Universal Data Layer.

        Note: Unlike HummingbotDataClient which has specific exchange connectors,
        MarketIntelligence uses adapters that are automatically selected based
        on availability and priority.

        Returns:
            List of adapter names
        """
        return ["redis_websocket", "binance_rest"]

    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol format for consistency.

        Args:
            symbol: Trading pair in any format

        Returns:
            Normalized symbol in "BASE/QUOTE" format
        """
        # Handle different formats: BTC-USDT, BTC_USDT, BTCUSDT -> BTC/USDT
        if "/" in symbol:
            return symbol.upper()
        elif "-" in symbol:
            return symbol.replace("-", "/").upper()
        elif "_" in symbol:
            return symbol.replace("_", "/").upper()
        else:
            return symbol.upper()
