"""
Market Intelligence Orchestrator

Provides config-driven market intelligence fetching across 150+ data sources
without bloating ggbot.py. Uses the Universal Data Layer (MarketIntelligence gateway)
with automatic caching, permission checks, and error handling.

This module solves the scalability problem: adding new data sources requires only
updating catalog_mapping.py, not modifying ggbot.py or this orchestrator.
"""

import asyncio
from typing import Dict, Any, Optional, List
from core.common.logger import logger
from core.common.db import get_db_connection, db_fetch_one
from core.services.user_service import UserService
from core.symbols.standardizer import UniversalSymbolStandardizer
from market_intelligence.gateway import MarketIntelligence
from market_intelligence.types import QueryFormat, DataSourceError


async def fetch_market_intelligence(
    config,  # BotConfigV2
    user_id: str,
    symbol: str,
    data_points_override: Optional[Dict[str, List[str]]] = None,
    run_id: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch all enabled market intelligence for a bot configuration.

    This is the main entry point called by ggbot.py. It:
    1. Parses config to find enabled data sources (or uses override)
    2. Checks user permissions for premium data
    3. Maps data_point names to catalog data_types
    4. Queries MarketIntelligence gateway for each enabled source
    5. Aggregates results by category

    Args:
        config: BotConfigV2 with config.extraction.selected_data_sources
        user_id: User ID for permission checks
        symbol: Trading pair in any format (BTCUSDT, BTC-USDT, or BTC/USDT)
                Automatically normalized to CCXT format (BTC/USDT) for data queries
        data_points_override: Optional override for dynamic queries (bypasses config).
                             Format: {'macro_economics': ['vix', 'dxy'], ...}

    Returns:
        Dict organized by category:
        {
            'derivatives_leverage': {
                'btc_funding_rate': {
                    'funding_rate_pct': 0.0026,
                    'interpretation': {...}
                }
            },
            'macro_economics': {
                'vix': {...},
                'dxy': {...}
            }
        }

    Examples:
        # Config-based (default behavior)
        market_intel = await fetch_market_intelligence(config, user_id, symbol)

        # Dynamic query (for agents - no config update)
        market_intel = await fetch_market_intelligence(
            config, user_id, symbol,
            data_points_override={'macro_economics': ['vix', 'dxy']}
        )
    """
    _bind_extra = {"component": "intelligence_orchestrator", "user_id": user_id}
    if run_id:
        _bind_extra["run_id"] = run_id
    _log = logger.bind(**_bind_extra)

    # Normalize symbol format to CCXT standard (BTC/USDT)
    # Handles multiple input formats: BTCUSDT (ggshot), BTC-USDT (platform), BTC/USDT (ccxt)
    standardizer = UniversalSymbolStandardizer()
    normalized_symbol = symbol

    # Try normalizing from common formats to CCXT
    if '/' not in symbol and '-' not in symbol:
        # Likely ggshot format (BTCUSDT) - try normalizing
        ccxt_symbol = standardizer.normalize(symbol, "ggshot", "ccxt")
        if ccxt_symbol:
            normalized_symbol = ccxt_symbol
            _log.debug(f"Normalized symbol: {symbol} → {normalized_symbol} (ggshot→ccxt)")
    elif '-' in symbol:
        # Platform format (BTC-USDT) - convert to CCXT
        ccxt_symbol = standardizer.normalize(symbol, "platform", "ccxt")
        if ccxt_symbol:
            normalized_symbol = ccxt_symbol
            _log.debug(f"Normalized symbol: {symbol} → {normalized_symbol} (platform→ccxt)")
    else:
        # Already in CCXT format (BTC/USDT) or unknown format
        _log.debug(f"Symbol already in CCXT format or unknown: {symbol}")

    symbol = normalized_symbol  # Use normalized symbol for all queries

    # Get selected data sources (override takes precedence)
    if data_points_override:
        selected_sources = data_points_override
        _log.debug(f"Using data_points_override: {list(data_points_override.keys())}")
    else:
        selected_sources = _parse_config_sources(config)

    if not selected_sources:
        _log.debug("No market intelligence sources enabled")
        return {}

    # Get user permissions
    user_permissions = await _get_user_permissions(user_id)

    # Initialize gateway
    gateway = MarketIntelligence()

    # Aggregate results by category
    results = {}
    total_points = 0

    try:
        # Build list of all queries to execute in parallel
        query_tasks = []
        query_metadata = []  # Track which query is which

        for source_name, data_points in selected_sources.items():
            for point_name in data_points:
                # Check permission
                if not await _check_permission(user_id, source_name, point_name, user_permissions):
                    _log.debug(f"User lacks permission for {source_name}.{point_name}")
                    continue

                # Get catalog mapping
                mapping = _get_catalog_mapping(source_name, point_name)
                if not mapping:
                    _log.warning(f"No catalog mapping for {source_name}.{point_name}")
                    continue

                # Prepare query params (replace {symbol}, {config_id}, {trading_mode} templates)
                params = mapping['params_template'].copy()
                config_id = getattr(config, 'config_id', None) or ''
                trading_mode = 'paper'
                if hasattr(config, 'trading_mode'):
                    trading_mode = getattr(config, 'trading_mode', 'paper') or 'paper'
                params = _replace_param_templates(params, symbol=symbol, config_id=config_id, trading_mode=trading_mode)

                # Include symbol in params for cache key generation
                # Global data (VIX, DXY, CPI, NFP, btc_tvl, lunar_phase, mercury_status)
                # uses 'global' to share cache across all bots instead of duplicating per-symbol
                is_global = mapping.get('global', False)
                if 'symbol' not in params:
                    params['symbol'] = 'global' if is_global else symbol

                # Get cache TTL override if specified
                cache_ttl_override = mapping.get('cache_ttl')

                # Create query coroutine
                query_task = gateway.query(
                    data_type=mapping['data_type'],
                    params=params,
                    format=QueryFormat.RAW,
                    cache_ttl_override=cache_ttl_override
                )

                query_tasks.append(query_task)
                query_metadata.append({
                    'source_name': source_name,
                    'point_name': point_name
                })

        if not query_tasks:
            _log.debug("No data points to query after permission checks")
            return {}

        # Execute all queries in parallel
        _log.info(f"⚡ Executing {len(query_tasks)} data point queries in parallel...")
        query_results = await asyncio.gather(*query_tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(query_results):
            meta = query_metadata[i]
            source_name = meta['source_name']
            point_name = meta['point_name']

            # Initialize category dict if needed
            if source_name not in results:
                results[source_name] = {}

            # Handle errors gracefully
            if isinstance(result, Exception):
                if isinstance(result, DataSourceError):
                    _log.debug(f"Failed to fetch {source_name}.{point_name}: {result}")
                else:
                    _log.error(f"Unexpected error fetching {source_name}.{point_name}: {result}")
                continue

            # Store successful result
            results[source_name][point_name] = result.data
            total_points += 1

            _log.debug(
                f"{source_name}.{point_name}: fetched from {result.source} "
                f"({result.latency_ms:.0f}ms, cached={result.from_cache})"
            )

        if total_points > 0:
            categories = list(results.keys())
            _log.info(
                f"✅ Market intelligence complete: {total_points} data points from "
                f"{len(categories)} categories ({', '.join(categories)})"
            )
        else:
            _log.debug("No market intelligence data points fetched")

        return results

    finally:
        # Cleanup gateway
        await gateway.close()


def _parse_config_sources(config) -> Dict[str, List[str]]:
    """
    Parse config to extract enabled data sources.

    Args:
        config: BotConfigV2

    Returns:
        Dict mapping source_name to list of data_point names:
        {
            'derivatives_leverage': ['btc_funding_rate', 'eth_funding_rate'],
            'macro_economics': ['vix', 'dxy']
        }
    """
    try:
        selected_sources = config.extraction.get('selected_data_sources', {})

        # Filter out technical_analysis (handled separately by ExtractionEngineV2)
        # Only process non-technical sources through orchestrator
        filtered_sources = {}
        for source_name, source_config in selected_sources.items():
            if source_name == 'technical_analysis':
                continue  # Skip - handled by old extraction system

            data_points = source_config.get('data_points', [])
            if data_points:
                filtered_sources[source_name] = data_points

        return filtered_sources

    except (AttributeError, TypeError) as e:
        logger.warning(f"Failed to parse config sources: {e}")
        return {}


async def _get_user_permissions(user_id: str) -> List[str]:
    """
    Get user's paid_data_points array for permission checks.

    Args:
        user_id: User ID

    Returns:
        List of data point names user has access to (e.g., ['ggshot'])
    """
    try:
        user_service = UserService()
        profile = await user_service.get_profile(user_id)

        if profile and profile.paid_data_points:
            return profile.paid_data_points

        return []

    except Exception as e:
        logger.warning(f"Failed to get user permissions: {e}")
        return []


async def _check_permission(
    user_id: str,
    source_name: str,
    point_name: str,
    user_permissions: List[str]
) -> bool:
    """
    Check if user has permission to access a data point.

    Args:
        user_id: User ID
        source_name: Data source name (e.g., 'derivatives_leverage')
        point_name: Data point name (e.g., 'btc_funding_rate')
        user_permissions: User's paid_data_points array

    Returns:
        True if user has access, False otherwise
    """
    # Query database for data point's requires_premium AND enabled flags
    try:
        result = await db_fetch_one("""
            SELECT dp.requires_premium, dp.enabled, ds.enabled as source_enabled
            FROM data_points dp
            JOIN data_sources ds ON dp.source_id = ds.source_id
            WHERE ds.name = %s AND dp.name = %s
        """, (source_name, point_name))

        if not result:
            logger.warning(f"Data point not found: {source_name}.{point_name}")
            return False

        requires_premium, point_enabled, source_enabled = result

        # Check if data point or source is disabled
        if not point_enabled or not source_enabled:
            logger.debug(f"Data point disabled: {source_name}.{point_name} (point_enabled={point_enabled}, source_enabled={source_enabled})")
            return False

        # If free, allow access
        if not requires_premium:
            return True

        # If premium, check user permissions
        # For now, point_name must be in paid_data_points array
        # Example: 'ggshot' in user.paid_data_points grants access to ggshot signals
        return point_name in user_permissions

    except Exception as e:
        logger.error(f"Permission check failed for {source_name}.{point_name}: {e}")
        return False  # Deny access on error (fail-safe)


def _get_catalog_mapping(source_name: str, point_name: str) -> Optional[Dict[str, Any]]:
    """
    Get catalog mapping for a data point.

    Args:
        source_name: Data source name (e.g., 'derivatives_leverage')
        point_name: Data point name (e.g., 'btc_funding_rate')

    Returns:
        Mapping dict with 'data_type' and 'params_template', or None if not found
    """
    from market_intelligence.catalog_mapping import CATALOG_MAPPING

    key = (source_name, point_name)
    return CATALOG_MAPPING.get(key)


def _replace_param_templates(params: Dict[str, Any], **replacements) -> Dict[str, Any]:
    """
    Replace template variables in params dict.

    Args:
        params: Params dict with potential {symbol} templates
        **replacements: Keyword arguments for replacement (e.g., symbol='BTC/USDT')

    Returns:
        Params dict with templates replaced

    Example:
        params = {'symbol': '{symbol}', 'limit': 200}
        result = _replace_param_templates(params, symbol='BTC/USDT')
        # result = {'symbol': 'BTC/USDT', 'limit': 200}
    """
    replaced = {}
    for key, value in params.items():
        if isinstance(value, str) and '{' in value:
            # Replace template
            replaced[key] = value.format(**replacements)
        else:
            replaced[key] = value
    return replaced
