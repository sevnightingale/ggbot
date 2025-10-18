"""
Universal Data Layer - Market Intelligence Platform

A catalog-driven system for accessing 150+ market intelligence data sources
through a unified interface, optimized for both trading bots and AI agents.
"""

from market_intelligence.types import (
    QueryFormat,
    QueryParams,
    AdapterResponse,
    MarketDataResponse,
    DataSourceError,
    CatalogError,
    CacheError,
    AdapterError
)

__version__ = "1.0.0"
__all__ = [
    "QueryFormat",
    "QueryParams",
    "AdapterResponse",
    "MarketDataResponse",
    "DataSourceError",
    "CatalogError",
    "CacheError",
    "AdapterError",
]
