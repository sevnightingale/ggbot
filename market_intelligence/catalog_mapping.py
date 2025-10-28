"""
Catalog Mapping - Data Point to Catalog Data Type Mapping

This file maps database data_points to Universal Data Layer catalog data_types.
Adding new data sources only requires adding entries here - no code changes needed.

Mapping Structure:
    Key: (source_name, point_name) tuple from database
    Value: {
        'data_type': catalog data type name (e.g., 'funding_rate'),
        'params_template': query params with optional {symbol} template
    }

Examples:
    - BTC funding rate: Use funding_rate adapter with symbol='BTC/USDT'
    - ggShot signals: Use ggshot_signals adapter with symbol from config
    - VIX index: Use vix_index adapter with no params
"""

from typing import Dict, Tuple, Any


CATALOG_MAPPING: Dict[Tuple[str, str], Dict[str, Any]] = {
    # ========================================================================
    # TRADING SIGNALS (Premium)
    # ========================================================================
    ('trading_signals', 'ggshot'): {
        'data_type': 'ggshot_signals',
        'params_template': {
            'symbol': '{symbol}',  # Replaced with actual symbol at runtime
            'include_raw': False
        }
    },

    # ========================================================================
    # DERIVATIVES & LEVERAGE (Free)
    # ========================================================================
    ('derivatives_leverage', 'btc_funding_rate'): {
        'data_type': 'funding_rate',
        'params_template': {
            'symbol': 'BTC/USDT',
            'include_mark_price': True
        }
    },

    ('derivatives_leverage', 'eth_funding_rate'): {
        'data_type': 'funding_rate',
        'params_template': {
            'symbol': 'ETH/USDT',
            'include_mark_price': True
        }
    },

    # ========================================================================
    # MACRO ECONOMICS (Grok-Powered)
    # ========================================================================
    ('macro_economics', 'vix'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'vix_index'},
        'cache_ttl': 900  # 15 minutes - VIX updates every 15 seconds during trading hours
    },

    ('macro_economics', 'dxy'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'dxy_index'},
        'cache_ttl': 900  # 15 minutes - DXY updates continuously during trading
    },

    ('macro_economics', 'cpi'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'cpi_inflation'},
        'cache_ttl': 86400  # 24 hours - CPI released monthly, no need for frequent updates
    },

    ('macro_economics', 'nfp'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'nfp_jobs'},
        'cache_ttl': 86400  # 24 hours - NFP released monthly, no need for frequent updates
    },

    # ========================================================================
    # ON-CHAIN ANALYTICS (Grok-Powered - Premium)
    # ========================================================================
    ('onchain_analytics', 'btc_tvl'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'btc_tvl'},
        'cache_ttl': 3600  # 1 hour - TVL updates hourly from DefiLlama
    },

    ('onchain_analytics', 'whale_activity'): {
        'data_type': 'grok_agentic',
        'params_template': {
            'query_type': 'whale_activity',
            'symbol': '{symbol}'
        },
        'cache_ttl': 1800  # 30 minutes - whale alerts are real-time but expensive to query
    },

    # ========================================================================
    # SENTIMENT & SOCIAL (Grok-Powered - Premium)
    # ========================================================================
    ('sentiment_social', 'twitter_sentiment'): {
        'data_type': 'grok_agentic',
        'params_template': {
            'query_type': 'twitter_sentiment',
            'symbol': '{symbol}'
        },
        'cache_ttl': 1800  # 30 minutes - sentiment shifts quickly but not second-by-second
    },

    # ========================================================================
    # NEWS & REGULATORY (Grok-Powered - Premium)
    # ========================================================================
    ('news_regulatory', 'crypto_news'): {
        'data_type': 'grok_agentic',
        'params_template': {
            'query_type': 'crypto_news',
            'symbol': '{symbol}'
        },
        'cache_ttl': 600  # 10 minutes - breaking news needs faster refresh
    },
}


def get_supported_data_points() -> list:
    """
    Get list of all supported (source, point) tuples.

    Returns:
        List of (source_name, point_name) tuples
    """
    return list(CATALOG_MAPPING.keys())


def get_data_type_for_point(source_name: str, point_name: str) -> str:
    """
    Get catalog data_type for a data point.

    Args:
        source_name: Data source name
        point_name: Data point name

    Returns:
        Catalog data_type string or None if not found
    """
    mapping = CATALOG_MAPPING.get((source_name, point_name))
    return mapping['data_type'] if mapping else None


def is_supported(source_name: str, point_name: str) -> bool:
    """
    Check if a data point is supported.

    Args:
        source_name: Data source name
        point_name: Data point name

    Returns:
        True if supported, False otherwise
    """
    return (source_name, point_name) in CATALOG_MAPPING
