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
    - VIX index: Use vix_index adapter with no params
"""

from typing import Dict, Tuple, Any


CATALOG_MAPPING: Dict[Tuple[str, str], Dict[str, Any]] = {
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
        'cache_ttl': 14400,  # 4 hours - VIX is context, not trigger; saves $0.025/query
        'global': True,  # Not symbol-specific — share cache across all bots
    },

    ('macro_economics', 'dxy'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'dxy_index'},
        'cache_ttl': 14400,  # 4 hours - DXY moves slowly relative to crypto volatility
        'global': True,
    },

    ('macro_economics', 'cpi'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'cpi_inflation'},
        'cache_ttl': 86400,  # 24 hours - CPI released monthly
        'global': True,
    },

    ('macro_economics', 'nfp'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'nfp_jobs'},
        'cache_ttl': 86400,  # 24 hours - NFP released monthly
        'global': True,
    },

    ('macro_economics', 'usdt_dominance'): {
        'data_type': 'coingecko_global',
        'params_template': {'query_type': 'usdt_dominance'},
        'cache_ttl': 14400,  # 4 hours
        'global': True,
    },

    ('macro_economics', 'move_index'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'move_index'},
        'cache_ttl': 14400,  # 4 hours
        'global': True,
    },

    # ========================================================================
    # ON-CHAIN ANALYTICS (Grok-Powered - Premium)
    # ========================================================================
    ('onchain_analytics', 'btc_tvl'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'btc_tvl'},
        'cache_ttl': 21600,  # 6 hours - TVL changes very slowly
        'global': True,  # BTC TVL is not per-symbol
    },

    ('onchain_analytics', 'whale_activity'): {
        'data_type': 'grok_agentic',
        'params_template': {
            'query_type': 'whale_activity',
            'symbol': '{symbol}'
        },
        'cache_ttl': 14400  # 4 hours - whale moves take time to matter; reduced from 2h to cut API costs
    },

    # ========================================================================
    # SENTIMENT & SOCIAL (Grok-Powered)
    # ========================================================================
    ('sentiment_social', 'twitter_sentiment'): {
        'data_type': 'grok_agentic',
        'params_template': {
            'query_type': 'twitter_sentiment',
            'symbol': '{symbol}'
        },
        'cache_ttl': 21600  # 6 hours - sentiment doesn't flip in minutes; reduced from 4h to cut API costs
    },

    # Astrology / Timing Signals (2026-01-23)
    ('sentiment_social', 'lunar_phase'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'lunar_phase'},
        'cache_ttl': 43200,  # 12 hours - moon phase changes slowly
        'global': True,
    },

    ('sentiment_social', 'mercury_status'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'mercury_status'},
        'cache_ttl': 86400,  # 24 hours - retrograde status changes very slowly
        'global': True,
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
        'cache_ttl': 14400  # 4 hours - breaking news is rarely actionable in minutes; reduced from 2h to cut API costs
    },

    # ========================================================================
    # ACCOUNT PERFORMANCE (Internal - Free)
    # ========================================================================
    ('account_performance', 'trading_history'): {
        'data_type': 'account_performance',
        'params_template': {
            'config_id': '{config_id}',
            'trading_mode': '{trading_mode}',
        },
        'cache_ttl': 300,  # 5 minutes
    },

    # ========================================================================
    # LEGACY CATEGORY ALIASES (for backward compatibility)
    # Maps old category names to correct catalog entries
    # ========================================================================
    # on_chain -> onchain_analytics
    ('on_chain', 'whale_activity'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'whale_activity', 'symbol': '{symbol}'},
        'cache_ttl': 14400
    },
    ('on_chain', 'btc_tvl'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'btc_tvl'},
        'cache_ttl': 21600,
        'global': True,
    },
    ('on_chain', 'Whale Activity'): {  # Display name variant
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'whale_activity', 'symbol': '{symbol}'},
        'cache_ttl': 14400
    },

    # news_events / news -> news_regulatory
    ('news_events', 'crypto_news'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'crypto_news', 'symbol': '{symbol}'},
        'cache_ttl': 14400
    },
    ('news', 'crypto_news'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'crypto_news', 'symbol': '{symbol}'},
        'cache_ttl': 14400
    },
    ('news', 'Crypto News Feed'): {  # Display name variant
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'crypto_news', 'symbol': '{symbol}'},
        'cache_ttl': 14400
    },

    # sentiment -> sentiment_social
    ('sentiment', 'twitter_sentiment'): {
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'twitter_sentiment', 'symbol': '{symbol}'},
        'cache_ttl': 21600
    },
    ('sentiment', 'Twitter Sentiment'): {  # Display name variant
        'data_type': 'grok_agentic',
        'params_template': {'query_type': 'twitter_sentiment', 'symbol': '{symbol}'},
        'cache_ttl': 21600
    },

    # derivatives -> derivatives_leverage
    ('derivatives', 'btc_funding_rate'): {
        'data_type': 'funding_rate',
        'params_template': {'symbol': 'BTC/USDT', 'include_mark_price': True}
    },
    ('derivatives', 'eth_funding_rate'): {
        'data_type': 'funding_rate',
        'params_template': {'symbol': 'ETH/USDT', 'include_mark_price': True}
    },
    ('derivatives', 'BTC Funding Rate'): {  # Display name variant
        'data_type': 'funding_rate',
        'params_template': {'symbol': 'BTC/USDT', 'include_mark_price': True}
    },
    ('derivatives', 'ETH Funding Rate'): {  # Display name variant
        'data_type': 'funding_rate',
        'params_template': {'symbol': 'ETH/USDT', 'include_mark_price': True}
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
