"""
Response formatter for market intelligence data.

Formats adapter responses in different modes (RAW, ANALYSIS, LLM) based on
consumer needs and catalog configuration.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from market_intelligence.types import (
    QueryFormat,
    AdapterResponse,
    MarketDataResponse,
    CatalogEntry
)
from core.common.logger import logger


class ResponseFormatter:
    """
    Formats market intelligence responses for different consumers.

    Supports three modes:
    - RAW: Direct adapter output (for system use)
    - ANALYSIS: Structured with metadata and insights (for dashboards)
    - LLM: Natural language with summary and key points (for agents)
    """

    def __init__(self):
        self._log = logger.bind(component="response_formatter")

    def format_response(
        self,
        data_type: str,
        query_params: Dict[str, Any],
        adapter_response: AdapterResponse,
        catalog_entry: CatalogEntry,
        format_mode: QueryFormat = QueryFormat.RAW,
        source: str = "",
        latency_ms: float = 0.0,
        from_cache: bool = False
    ) -> MarketDataResponse:
        """
        Format adapter response based on requested mode.

        Args:
            data_type: Type of data (ohlcv, sentiment, etc.)
            query_params: Original query parameters
            adapter_response: Response from adapter
            catalog_entry: Catalog definition for this data type
            format_mode: Output format mode
            source: Which adapter provided the data
            latency_ms: Query execution time
            from_cache: Whether result came from cache

        Returns:
            Formatted MarketDataResponse
        """
        if format_mode == QueryFormat.RAW:
            return self._format_raw(
                data_type, query_params, adapter_response,
                source, latency_ms, from_cache
            )

        elif format_mode == QueryFormat.ANALYSIS:
            return self._format_analysis(
                data_type, query_params, adapter_response, catalog_entry,
                source, latency_ms, from_cache
            )

        elif format_mode == QueryFormat.LLM:
            return self._format_llm(
                data_type, query_params, adapter_response, catalog_entry,
                source, latency_ms, from_cache
            )

        else:
            self._log.warning(f"Unknown format mode: {format_mode}, defaulting to RAW")
            return self._format_raw(
                data_type, query_params, adapter_response,
                source, latency_ms, from_cache
            )

    def _format_raw(
        self,
        data_type: str,
        query_params: Dict[str, Any],
        adapter_response: AdapterResponse,
        source: str,
        latency_ms: float,
        from_cache: bool
    ) -> MarketDataResponse:
        """Format in RAW mode - minimal processing."""
        return MarketDataResponse(
            data_type=data_type,
            query_params=query_params,
            timestamp=datetime.now(timezone.utc),
            data=adapter_response.data,
            summary="",
            key_insights=[],
            confidence=adapter_response.confidence,
            signals=[],
            source=source,
            latency_ms=latency_ms,
            from_cache=from_cache,
            related=adapter_response.related_queries
        )

    def _format_analysis(
        self,
        data_type: str,
        query_params: Dict[str, Any],
        adapter_response: AdapterResponse,
        catalog_entry: CatalogEntry,
        source: str,
        latency_ms: float,
        from_cache: bool
    ) -> MarketDataResponse:
        """Format in ANALYSIS mode - structured with insights."""
        # Extract insights from data (basic implementation)
        insights = self._extract_insights(adapter_response.data, data_type)

        # Generate summary
        summary = self._generate_summary(data_type, query_params, adapter_response)

        return MarketDataResponse(
            data_type=data_type,
            query_params=query_params,
            timestamp=datetime.now(timezone.utc),
            data=adapter_response.data,
            summary=summary,
            key_insights=insights,
            confidence=adapter_response.confidence,
            signals=[],  # Future: extract trading signals
            source=source,
            latency_ms=latency_ms,
            from_cache=from_cache,
            related=adapter_response.related_queries
        )

    def _format_llm(
        self,
        data_type: str,
        query_params: Dict[str, Any],
        adapter_response: AdapterResponse,
        catalog_entry: CatalogEntry,
        source: str,
        latency_ms: float,
        from_cache: bool
    ) -> MarketDataResponse:
        """Format in LLM mode - natural language optimized for agents."""
        # Use catalog agent format if available
        if catalog_entry.agent_format:
            formatted = catalog_entry.format_for_agent(adapter_response, query_params)
            summary = formatted['summary']
            insights = formatted['insights']
        else:
            # Fallback to basic formatting
            summary = self._generate_summary(data_type, query_params, adapter_response)
            insights = self._extract_insights(adapter_response.data, data_type)

        return MarketDataResponse(
            data_type=data_type,
            query_params=query_params,
            timestamp=datetime.now(timezone.utc),
            data=adapter_response.data,
            summary=summary,
            key_insights=insights,
            confidence=adapter_response.confidence,
            signals=[],
            source=source,
            latency_ms=latency_ms,
            from_cache=from_cache,
            related=adapter_response.related_queries
        )

    def _generate_summary(
        self,
        data_type: str,
        query_params: Dict[str, Any],
        adapter_response: AdapterResponse
    ) -> str:
        """Generate basic summary of the data."""
        symbol = query_params.get('symbol', 'unknown')

        if data_type == 'ohlcv':
            return f"Retrieved OHLCV data for {symbol}"
        elif data_type.startswith('sentiment'):
            return f"Retrieved sentiment data for {symbol}"
        elif data_type.startswith('news'):
            return f"Retrieved news data for {symbol}"
        elif data_type.startswith('onchain'):
            return f"Retrieved on-chain data for {symbol}"
        else:
            return f"Retrieved {data_type} data"

    def _extract_insights(self, data: Any, data_type: str) -> List[str]:
        """Extract key insights from data (basic implementation)."""
        insights = []

        # Type-specific insight extraction (basic)
        if data_type == 'ohlcv' and hasattr(data, 'shape'):
            insights.append(f"Dataset contains {len(data)} periods")

        elif data_type.startswith('sentiment') and isinstance(data, dict):
            if 'sentiment_score' in data:
                score = data['sentiment_score']
                insights.append(f"Sentiment score: {score:.2f}")
            if 'mentions' in data:
                mentions = data['mentions']
                insights.append(f"Based on {mentions} mentions")

        elif data_type.startswith('news') and isinstance(data, list):
            insights.append(f"Found {len(data)} news articles")

        return insights
