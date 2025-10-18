"""
Market Intelligence Gateway - Unified query interface for all data sources.

This is the main entry point for querying market intelligence. It coordinates
catalog lookup, validation, caching, adapter routing, and response formatting.
"""

import time
import importlib
from typing import Dict, Any, Optional
from pathlib import Path
import pandas as pd

from core.common.logger import logger
from market_intelligence.types import (
    QueryFormat,
    QueryParams,
    MarketDataResponse,
    AdapterResponse,
    DataSourceError,
    CatalogError
)
from market_intelligence.catalog import DataCatalog
from market_intelligence.cache.manager import CacheManager
from market_intelligence.response_formatter import ResponseFormatter
from market_intelligence.adapters.base import DataAdapter


class MarketIntelligence:
    """
    Universal market intelligence gateway.

    Provides unified query interface for 150+ data sources with automatic
    caching, fallback, and formatting.
    """

    def __init__(self, catalog_dir: Optional[str] = None, redis_url: Optional[str] = None):
        """
        Initialize market intelligence gateway.

        Args:
            catalog_dir: Path to catalog directory (optional)
            redis_url: Redis connection URL (optional)
        """
        self.catalog = DataCatalog(catalog_dir)
        self.cache_manager = CacheManager(redis_url)
        self.formatter = ResponseFormatter()
        self._adapter_cache: Dict[str, DataAdapter] = {}
        self._log = logger.bind(component="market_intelligence")

        # Load catalog entries
        try:
            self.catalog.load_all()
        except CatalogError as e:
            self._log.error(f"Failed to load catalog: {e}")
            raise

    async def query(
        self,
        data_type: str,
        params: Dict[str, Any],
        format: QueryFormat = QueryFormat.RAW
    ) -> MarketDataResponse:
        """
        Universal query interface for market intelligence.

        Args:
            data_type: Type of data (ohlcv, sentiment, news, onchain, etc.)
            params: Query parameters (varies by data_type)
            format: Output format (RAW, ANALYSIS, or LLM)

        Returns:
            MarketDataResponse with requested data

        Raises:
            CatalogError: If data_type not found in catalog
            DataSourceError: If all sources fail
        """
        start_time = time.time()

        # Get catalog entry
        catalog_entry = self.catalog.get(data_type)
        if not catalog_entry:
            available_types = ', '.join(self.catalog.list_all()[:10])
            raise CatalogError(
                f"Unknown data type: {data_type}. "
                f"Available types include: {available_types}..."
            )

        # Validate parameters
        try:
            validated_params = catalog_entry.validate_params(params)
        except ValueError as e:
            raise DataSourceError(f"Invalid parameters for {data_type}: {e}")

        # Build cache key
        cache_key = catalog_entry.build_cache_key(validated_params)

        # Check cache
        cached_data = await self.cache_manager.get(cache_key, catalog_entry.cache)
        if cached_data:
            latency_ms = (time.time() - start_time) * 1000
            self._log.info(f"Cache hit for {data_type}: {cache_key} ({latency_ms:.0f}ms)")

            # Wrap cached data in AdapterResponse if it's not already
            if isinstance(cached_data, AdapterResponse):
                adapter_response = cached_data
            else:
                # Raw cached data (from WebSocket service) - needs transformation
                # Convert list of candle dicts to DataFrame for OHLCV data
                if data_type == 'ohlcv' and isinstance(cached_data, list):
                    df = pd.DataFrame(cached_data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df = df.sort_values('timestamp').reset_index(drop=True)

                    # Apply limit if specified
                    limit = validated_params.get('limit', 200)
                    if len(df) > limit:
                        df = df.tail(limit).reset_index(drop=True)

                    data = df
                else:
                    data = cached_data

                # Wrap in AdapterResponse
                adapter_response = AdapterResponse(
                    data=data,
                    metadata={"cache_hit": True, "source": "websocket_cache"},
                    confidence=1.0,
                    related_queries=[]
                )

            # Format cached response
            return self.formatter.format_response(
                data_type=data_type,
                query_params=validated_params,
                adapter_response=adapter_response,
                catalog_entry=catalog_entry,
                format_mode=format,
                source="cache",
                latency_ms=latency_ms,
                from_cache=True
            )

        # Cache miss - fetch from source
        self._log.info(f"Cache miss for {data_type}: {cache_key}")

        # Try sources in priority order
        query_params_obj = QueryParams(validated_params)
        last_error = None

        for source_config in catalog_entry.sources:
            try:
                # Get adapter instance
                adapter = await self._get_adapter(source_config.adapter)

                # Fetch data
                self._log.info(f"Fetching {data_type} from {source_config.adapter}")
                adapter_response = await adapter.fetch(query_params_obj)

                # Cache the result
                await self.cache_manager.set(cache_key, adapter_response, catalog_entry.cache)

                # Calculate total latency
                latency_ms = (time.time() - start_time) * 1000

                self._log.info(
                    f"Successfully fetched {data_type} from {source_config.adapter} "
                    f"({latency_ms:.0f}ms)"
                )

                # Format and return response
                return self.formatter.format_response(
                    data_type=data_type,
                    query_params=validated_params,
                    adapter_response=adapter_response,
                    catalog_entry=catalog_entry,
                    format_mode=format,
                    source=source_config.adapter,
                    latency_ms=latency_ms,
                    from_cache=False
                )

            except Exception as e:
                last_error = e
                self._log.warning(
                    f"Adapter {source_config.adapter} failed for {data_type}: {e}"
                )
                # Continue to next source
                continue

        # All sources failed
        raise DataSourceError(
            f"All sources failed for {data_type}. Last error: {last_error}"
        )

    async def _get_adapter(self, adapter_name: str) -> DataAdapter:
        """
        Get or create adapter instance.

        Args:
            adapter_name: Class name of adapter

        Returns:
            Adapter instance

        Raises:
            DataSourceError: If adapter cannot be loaded
        """
        # Check cache first
        if adapter_name in self._adapter_cache:
            return self._adapter_cache[adapter_name]

        # Dynamically import and instantiate adapter
        try:
            # Determine module path based on adapter name
            # Convention: TwitterSentimentAdapter -> market_intelligence.adapters.sentiment.twitter
            module_path = self._adapter_name_to_module(adapter_name)

            module = importlib.import_module(module_path)
            adapter_class = getattr(module, adapter_name)
            adapter_instance = adapter_class()

            # Cache the instance
            self._adapter_cache[adapter_name] = adapter_instance

            return adapter_instance

        except (ImportError, AttributeError) as e:
            raise DataSourceError(f"Failed to load adapter {adapter_name}: {e}")

    def _adapter_name_to_module(self, adapter_name: str) -> str:
        """
        Convert adapter class name to module path.

        Examples:
            RedisWebSocketAdapter -> market_intelligence.adapters.market_data.redis_websocket
            TwitterSentimentAdapter -> market_intelligence.adapters.sentiment.twitter
            GlassnodeAdapter -> market_intelligence.adapters.onchain.glassnode
        """
        # Remove 'Adapter' suffix
        name_without_suffix = adapter_name.replace('Adapter', '')

        # Convert PascalCase to snake_case, preserving compound words
        import re
        # Special case for WebSocket to avoid redis_web_socket
        name_without_suffix = name_without_suffix.replace('WebSocket', 'Websocket')
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', name_without_suffix).lower()

        # Determine category from name patterns
        if 'websocket' in snake_case or 'rest' in snake_case or 'ccxt' in snake_case:
            category = 'market_data'
        elif 'twitter' in snake_case or 'reddit' in snake_case or 'telegram' in snake_case:
            category = 'sentiment'
        elif 'news' in snake_case:
            category = 'news'
        elif 'glassnode' in snake_case or 'etherscan' in snake_case or 'nansen' in snake_case:
            category = 'onchain'
        elif 'edgar' in snake_case or 'alpha_vantage' in snake_case:
            category = 'fundamentals'
        elif 'fred' in snake_case or 'bls' in snake_case or 'treasury' in snake_case:
            category = 'macro'
        else:
            # Default to market_data
            category = 'market_data'

        return f"market_intelligence.adapters.{category}.{snake_case}"

    async def list_data_types(self, category: Optional[str] = None) -> list:
        """
        List available data types.

        Args:
            category: Filter by category (optional)

        Returns:
            List of available data type names
        """
        if category:
            return self.catalog.list_by_category(category)
        return self.catalog.list_all()

    async def get_catalog_entry(self, data_type: str):
        """
        Get catalog entry for a data type.

        Args:
            data_type: Name of data type

        Returns:
            CatalogEntry or None if not found
        """
        return self.catalog.get(data_type)

    async def close(self):
        """Clean up resources."""
        # Close cache connections
        await self.cache_manager.close()

        # Close adapter connections
        for adapter in self._adapter_cache.values():
            if hasattr(adapter, 'close'):
                await adapter.close()

        self._log.info("Market intelligence gateway closed")
