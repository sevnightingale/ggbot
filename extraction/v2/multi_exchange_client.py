"""
Multi-Exchange Data Client with Intelligent Fallback

Provides automatic failover across multiple exchanges to maximize symbol coverage.
Integrates seamlessly with existing V2 extraction architecture.
"""

import asyncio
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import os

from core.common.logger import logger
from core.symbols.standardizer import UniversalSymbolStandardizer
from .data_client import HummingbotDataClient


class ExchangeHealthTracker:
    """Track exchange performance and health for intelligent routing"""

    def __init__(self):
        self.health_data = {
            # Exchange priority order (best to worst)
            "binance": {"success_rate": 95.0, "avg_response_time": 0.8, "last_success": None, "total_requests": 0, "successes": 0},
            "kucoin": {"success_rate": 90.0, "avg_response_time": 1.2, "last_success": None, "total_requests": 0, "successes": 0},
            "okx": {"success_rate": 88.0, "avg_response_time": 1.0, "last_success": None, "total_requests": 0, "successes": 0},
            "gate_io": {"success_rate": 85.0, "avg_response_time": 1.5, "last_success": None, "total_requests": 0, "successes": 0},
            "ascend_ex": {"success_rate": 80.0, "avg_response_time": 2.0, "last_success": None, "total_requests": 0, "successes": 0},
        }
        self.symbol_exchange_cache = {}  # Cache successful symbol-exchange pairs
        self._log = logger.bind(component="exchange_health")

    def get_exchange_priority_for_symbol(self, symbol: str) -> List[str]:
        """
        Get ordered list of exchanges to try for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            List of exchange names in priority order
        """
        # Check cache first
        if symbol in self.symbol_exchange_cache:
            cached_exchange = self.symbol_exchange_cache[symbol]
            # Put cached exchange first, then others by health
            priority_list = [cached_exchange]
            for exchange in self._get_exchanges_by_health():
                if exchange != cached_exchange:
                    priority_list.append(exchange)
            return priority_list

        # Default to health-based ordering
        return self._get_exchanges_by_health()

    def _get_exchanges_by_health(self) -> List[str]:
        """Get exchanges ordered by health score"""
        exchanges = list(self.health_data.keys())
        # Sort by composite score: success_rate * (1 / avg_response_time)
        exchanges.sort(key=lambda ex: (
            self.health_data[ex]["success_rate"] *
            (1 / max(self.health_data[ex]["avg_response_time"], 0.1))
        ), reverse=True)
        return exchanges

    def record_request(self, exchange: str, success: bool, response_time: float = None):
        """Record the result of an exchange request"""
        if exchange not in self.health_data:
            return

        health = self.health_data[exchange]
        health["total_requests"] += 1

        if success:
            health["successes"] += 1
            health["last_success"] = datetime.utcnow()
            if response_time:
                # Update moving average response time
                current_avg = health["avg_response_time"]
                health["avg_response_time"] = (current_avg * 0.8) + (response_time * 0.2)

        # Update success rate
        health["success_rate"] = (health["successes"] / health["total_requests"]) * 100

    def cache_successful_symbol_exchange(self, symbol: str, exchange: str):
        """Cache a successful symbol-exchange mapping"""
        self.symbol_exchange_cache[symbol] = exchange
        self._log.debug(f"Cached {symbol} -> {exchange}")

    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        return {
            "exchange_health": self.health_data.copy(),
            "cached_mappings": len(self.symbol_exchange_cache),
            "best_exchange": self._get_exchanges_by_health()[0] if self.health_data else None
        }


class MultiExchangeDataClient:
    """
    Enhanced data client with multi-exchange fallback capability.

    Seamlessly integrates with existing ExtractionEngineV2 while adding
    intelligent exchange routing and fallback.
    """

    def __init__(self, enable_caching: bool = True, enable_health_tracking: bool = True):
        """
        Initialize multi-exchange client.

        Args:
            enable_caching: Enable symbol-exchange caching for performance
            enable_health_tracking: Enable exchange health monitoring
        """
        self.standardizer = UniversalSymbolStandardizer()
        self.health_tracker = ExchangeHealthTracker() if enable_health_tracking else None
        self.enable_caching = enable_caching
        self.enable_health_tracking = enable_health_tracking

        # Connection pool for efficient multi-exchange handling
        self._client_pool = {}
        self._log = logger.bind(component="multi_exchange_client")

        self._log.info(f"Initialized MultiExchangeDataClient with caching={enable_caching}, health_tracking={enable_health_tracking}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup all connections."""
        await self._cleanup_connections()

    async def _cleanup_connections(self):
        """Clean up all client connections"""
        for client in self._client_pool.values():
            if hasattr(client, '__aexit__'):
                try:
                    await client.disconnect()
                except:
                    pass  # Ignore cleanup errors
        self._client_pool.clear()

    async def _get_client_for_exchange(self, exchange: str) -> HummingbotDataClient:
        """Get or create a client for specific exchange"""
        if exchange not in self._client_pool:
            client = HummingbotDataClient()
            await client.connect()
            self._client_pool[exchange] = client
        return self._client_pool[exchange]

    async def get_candles_with_fallback(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        preferred_exchange: str = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Get candle data with automatic exchange fallback.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Candle timeframe
            limit: Number of candles to retrieve
            preferred_exchange: Preferred exchange (optional)

        Returns:
            Tuple of (DataFrame, successful_exchange)
        """
        start_time = datetime.utcnow()

        # Determine exchange priority
        if preferred_exchange and self.health_tracker:
            exchange_priority = [preferred_exchange] + [
                ex for ex in self.health_tracker.get_exchange_priority_for_symbol(symbol)
                if ex != preferred_exchange
            ]
        elif self.health_tracker:
            exchange_priority = self.health_tracker.get_exchange_priority_for_symbol(symbol)
        else:
            # Default fallback order if no health tracking
            exchange_priority = ["binance", "kucoin", "okx", "gate_io", "ascend_ex"]
            if preferred_exchange and preferred_exchange not in exchange_priority:
                exchange_priority.insert(0, preferred_exchange)

        self._log.info(f"Attempting to fetch {symbol} data from {len(exchange_priority)} exchanges: {exchange_priority}")

        # Track attempts for reporting
        attempts = []

        # Try each exchange in priority order
        for i, exchange in enumerate(exchange_priority):
            attempt_start = datetime.utcnow()
            attempt = {
                "exchange": exchange,
                "attempt_number": i + 1,
                "start_time": attempt_start,
                "success": False,
                "error": None,
                "response_time": None
            }

            try:
                self._log.debug(f"Trying {symbol} on {exchange} (attempt {i+1}/{len(exchange_priority)})")

                client = await self._get_client_for_exchange(exchange)
                df = await client.get_candles(symbol, timeframe, limit, exchange)

                if df is not None and len(df) > 0:
                    # Success!
                    attempt_end = datetime.utcnow()
                    response_time = (attempt_end - attempt_start).total_seconds()

                    attempt.update({
                        "success": True,
                        "response_time": response_time,
                        "candle_count": len(df)
                    })

                    # Update health tracking
                    if self.health_tracker:
                        self.health_tracker.record_request(exchange, True, response_time)
                        self.health_tracker.cache_successful_symbol_exchange(symbol, exchange)

                    attempts.append(attempt)

                    total_time = (attempt_end - start_time).total_seconds()
                    self._log.info(f"✅ {symbol} data retrieved from {exchange} in {response_time:.2f}s (total: {total_time:.2f}s, attempt {i+1})")

                    return df, exchange

                else:
                    attempt["error"] = "No data returned"

            except Exception as e:
                attempt_end = datetime.utcnow()
                response_time = (attempt_end - attempt_start).total_seconds()
                error_msg = str(e).strip()

                attempt.update({
                    "error": error_msg,
                    "response_time": response_time
                })

                # Update health tracking
                if self.health_tracker:
                    self.health_tracker.record_request(exchange, False, response_time)

                self._log.debug(f"❌ {symbol} failed on {exchange}: {error_msg}")

            attempts.append(attempt)

            # Small delay between exchange attempts to be respectful
            if i < len(exchange_priority) - 1:  # Don't delay after last attempt
                await asyncio.sleep(0.5)

        # All exchanges failed
        total_time = (datetime.utcnow() - start_time).total_seconds()
        self._log.error(f"❌ {symbol} failed on all {len(exchange_priority)} exchanges in {total_time:.2f}s")

        # Create detailed error report
        error_summary = f"Symbol {symbol} not available on any exchange. Attempts: "
        error_details = []
        for attempt in attempts:
            error_details.append(f"{attempt['exchange']}({attempt['error'] or 'unknown error'})")
        error_summary += ", ".join(error_details)

        raise Exception(error_summary)

    async def get_candles(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        connector: str = "kucoin"  # For backward compatibility
    ) -> pd.DataFrame:
        """
        Get candle data with automatic fallback (backward compatible interface).

        This method maintains the same signature as HummingbotDataClient.get_candles()
        for seamless integration with existing code.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Candle timeframe
            limit: Number of candles to retrieve
            connector: Preferred exchange connector

        Returns:
            pandas DataFrame with OHLCV data
        """
        df, successful_exchange = await self.get_candles_with_fallback(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            preferred_exchange=connector
        )
        return df

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connections to all exchanges and return comprehensive status.

        Returns:
            Dictionary with connection status for each exchange
        """
        self._log.info("Testing connections to all exchanges...")

        test_results = {}
        overall_status = "success"

        available_exchanges = ["binance", "kucoin", "okx", "gate_io", "ascend_ex"]

        for exchange in available_exchanges:
            try:
                client = await self._get_client_for_exchange(exchange)
                exchange_test = await client.test_connection()
                test_results[exchange] = exchange_test

                if exchange_test.get("status") != "connected":
                    overall_status = "partial"

            except Exception as e:
                test_results[exchange] = {
                    "status": "error",
                    "error": str(e)
                }
                overall_status = "partial"

        # Add health summary if tracking is enabled
        if self.health_tracker:
            test_results["health_summary"] = self.health_tracker.get_health_summary()

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "exchanges": test_results,
            "total_exchanges": len(available_exchanges),
            "available_exchanges": [ex for ex, result in test_results.items() if result.get("status") == "connected"]
        }

    def get_supported_timeframes(self) -> List[str]:
        """Get list of supported timeframes (same as HummingbotDataClient)"""
        return ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]

    def get_supported_connectors(self) -> List[str]:
        """Get list of supported exchange connectors"""
        return ["binance", "kucoin", "okx", "gate_io", "ascend_ex"]

    def get_health_summary(self) -> Optional[Dict[str, Any]]:
        """Get exchange health summary (if health tracking enabled)"""
        if self.health_tracker:
            return self.health_tracker.get_health_summary()
        return None


# Convenience functions for backward compatibility
async def get_market_data_with_fallback(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100,
    preferred_exchange: str = "kucoin"
) -> pd.DataFrame:
    """
    Convenience function to quickly get market data with fallback.

    Args:
        symbol: Trading pair (e.g., "BTC/USDT")
        timeframe: Candle timeframe
        limit: Number of candles to retrieve
        preferred_exchange: Preferred exchange connector

    Returns:
        pandas DataFrame with OHLCV data
    """
    async with MultiExchangeDataClient() as client:
        return await client.get_candles(symbol, timeframe, limit, preferred_exchange)