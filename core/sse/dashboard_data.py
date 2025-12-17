"""
Unified Dashboard Data Provider

Provides optimized data fetching for the SSE dashboard stream.
Combines bot configs, positions, decisions, and accounts with enhanced
portfolio analytics from PositionManager for professional metrics.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from core.common.db import get_db_connection, DecimalEncoder
from core.common.logger import logger
from .redis_status import get_execution_phase, get_bot_status_color, get_bot_status_message
from trading.paper.positions import PositionManager


async def get_unified_dashboard_data(user_id: str) -> Dict[str, Any]:
    """
    Get all dashboard data for a user with enhanced portfolio analytics.

    Combines:
    - Bot configurations (non-archived)
    - Open positions with current P&L (paper and live)
    - Recent decisions (5 per bot, last 2 hours)
    - Account summaries enhanced with portfolio analytics

    Enhanced with runtime data from scheduler, Redis execution status, and Symphony API.

    Args:
        user_id: User UUID string

    Returns:
        Dictionary with 'bots', 'positions', 'decisions', 'accounts', 'timestamp'
    """
    try:
        # Get database data in single query
        db_data = _get_dashboard_data_from_db(user_id)

        # Enhance bots with runtime data
        if db_data.get('bots'):
            for bot in db_data['bots']:
                _enhance_bot_with_runtime_data(bot)

        # NOTE: Account data now comes from account_snapshots table (written by UniversalAccountMonitor)
        # No need to enrich live positions/accounts - already handled by background monitor

        return db_data

    except Exception as e:
        import traceback
        logger.error(f"Failed to get unified dashboard data for user {user_id}: {e}\n{traceback.format_exc()}")
        # Return empty structure on error
        return {
            'bots': [],
            'positions': [],
            'decisions': [],
            'accounts': [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e)
        }


def _get_dashboard_data_from_db(user_id: str) -> Dict[str, Any]:
    """Execute the unified dashboard query against PostgreSQL."""
    
    # Optimized single query using CTEs with proper filtering and limits
    query = """
    WITH bot_configs AS (
        SELECT c.config_id, c.user_id, c.config_name, c.config_type, c.state, c.config_data,
               c.trading_mode, c.symphony_agent_id,
               c.created_at, c.updated_at
        FROM configurations c
        WHERE c.user_id = %s AND c.state != 'archived'
    ),
    open_positions AS (
        -- Paper trading positions
        SELECT pt.config_id, pt.trade_id::text AS position_id, pt.symbol, pt.side, pt.size_usd,
               pt.entry_price, pt.current_price, pt.unrealized_pnl, pt.opened_at,
               pt.stop_loss, pt.take_profit, pt.leverage, 'paper' AS source
        FROM paper_trades pt
        INNER JOIN bot_configs bc ON pt.config_id = bc.config_id
        WHERE pt.status = 'open' AND (bc.trading_mode IS NULL OR bc.trading_mode = 'paper')

        UNION ALL

        -- Symphony trading positions (batch_ids only - details fetched from Symphony)
        SELECT lt.config_id, lt.batch_id::text AS position_id, NULL AS symbol, NULL AS side, NULL AS size_usd,
               NULL AS entry_price, NULL AS current_price, NULL AS unrealized_pnl, lt.created_at AS opened_at,
               NULL AS stop_loss, NULL AS take_profit, NULL AS leverage, 'symphony' AS source
        FROM live_trades lt
        INNER JOIN bot_configs bc ON lt.config_id = bc.config_id
        WHERE lt.closed_at IS NULL AND bc.trading_mode = 'symphony'

        UNION ALL

        -- Aster trading positions (batch_ids only - details fetched from AsterDEX)
        SELECT lt.config_id, lt.batch_id::text AS position_id, NULL AS symbol, NULL AS side, NULL AS size_usd,
               NULL AS entry_price, NULL AS current_price, NULL AS unrealized_pnl, lt.created_at AS opened_at,
               NULL AS stop_loss, NULL AS take_profit, NULL AS leverage, 'aster' AS source
        FROM live_trades lt
        INNER JOIN bot_configs bc ON lt.config_id = bc.config_id
        WHERE lt.closed_at IS NULL AND bc.trading_mode = 'aster'
        ORDER BY opened_at DESC
    ),
    recent_decisions AS (
        SELECT * FROM (
            SELECT d.config_id, d.decision_id, d.symbol, d.action, d.confidence,
                   d.reasoning, d.created_at,
                   ROW_NUMBER() OVER (
                       PARTITION BY d.config_id
                       ORDER BY d.created_at DESC
                   ) AS rn
            FROM decisions d
            INNER JOIN bot_configs bc ON d.config_id = bc.config_id
        ) ranked_decisions
        WHERE rn <= 5  -- 5 most recent decisions per bot (no time filter)
    ),
    first_activities AS (
        -- Get first activity for each bot (for performance calculation)
        SELECT DISTINCT ON (config_id)
               config_id,
               total_equity as initial_equity
        FROM activities
        WHERE total_equity IS NOT NULL
        ORDER BY config_id, created_at ASC
    ),
    latest_activities AS (
        -- Get latest activity for each bot (for performance calculation)
        SELECT DISTINCT ON (config_id)
               config_id,
               total_equity as current_equity
        FROM activities
        WHERE total_equity IS NOT NULL
        ORDER BY config_id, created_at DESC
    ),
    account_summaries AS (
        -- Get latest snapshot per config from universal account monitor
        SELECT DISTINCT ON (asn.config_id)
               asn.config_id,
               asn.snapshot_id as account_id,
               asn.current_balance,
               asn.available_balance,
               asn.margin_used,
               asn.total_pnl,
               asn.unrealized_pnl,
               asn.total_trades,
               asn.win_trades,
               asn.loss_trades,
               asn.open_positions,
               asn.win_rate,
               asn.timestamp as updated_at,
               asn.trading_mode as source,
               -- Calculate performance percentage from activities
               CASE
                   WHEN fa.initial_equity IS NOT NULL AND fa.initial_equity > 0 AND la.current_equity IS NOT NULL
                   THEN ((la.current_equity - fa.initial_equity) / fa.initial_equity * 100)
                   ELSE 0
               END as performance_pct
        FROM account_snapshots asn
        INNER JOIN bot_configs bc ON asn.config_id = bc.config_id
        LEFT JOIN first_activities fa ON asn.config_id = fa.config_id
        LEFT JOIN latest_activities la ON asn.config_id = la.config_id
        ORDER BY asn.config_id, asn.timestamp DESC
    )
    SELECT json_build_object(
        'bots', COALESCE((SELECT json_agg(
            json_build_object(
                'config_id', bc.config_id,
                'user_id', bc.user_id,
                'config_name', bc.config_name,
                'config_type', bc.config_type,
                'state', bc.state,
                'trading_mode', bc.trading_mode,
                'symphony_agent_id', bc.symphony_agent_id,
                'config_data', json_build_object(
                    'schema_version', bc.config_data->>'schema_version',
                    'config_type', bc.config_data->>'config_type',
                    'selected_pair', bc.config_data->>'selected_pair',
                    'extraction', bc.config_data->'extraction',
                    'decision', bc.config_data->'decision',
                    'trading', bc.config_data->'trading',
                    'llm_config', bc.config_data->'llm_config',
                    'telegram_integration', bc.config_data->'telegram_integration',
                    'agent_strategy', bc.config_data->'agent_strategy'
                ),
                'created_at', bc.created_at,
                'updated_at', bc.updated_at
            )
        ) FROM bot_configs bc), '[]'::json),
        'positions', COALESCE((SELECT json_agg(op.*) FROM open_positions op), '[]'::json),
        'decisions', COALESCE((SELECT json_agg(rd.*) FROM recent_decisions rd), '[]'::json),
        'accounts', COALESCE((SELECT json_agg(ac.*) FROM account_summaries ac), '[]'::json),
        'timestamp', NOW()
    ) AS dashboard_data
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id,))
            result = cur.fetchone()

            # Check if result exists and has at least one element before accessing
            if result and len(result) > 0 and result[0]:
                return result[0]  # Return the JSON object
            else:
                # Return empty structure if no data
                return {
                    'bots': [],
                    'positions': [],
                    'decisions': [],
                    'accounts': [],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }


def _enhance_bot_with_runtime_data(bot: Dict[str, Any]) -> None:
    """
    Enhance bot data with runtime information from scheduler and Redis.
    
    Adds:
    - execution_status from Redis
    - status_color, status_message for UI
    - show_spinner flag
    - next_run, is_scheduled from APScheduler (TODO)
    """
    config_id = bot.get('config_id')
    if not config_id:
        return
        
    # Get current execution status from Redis
    execution_status = get_execution_phase(config_id)
    bot['execution_status'] = execution_status
    
    # Get bot state from database
    bot_state = bot.get('state', 'inactive')
    
    # Calculate UI status info
    bot['status_color'] = get_bot_status_color(bot_state, execution_status)
    bot['status_message'] = get_bot_status_message(bot_state, execution_status)
    bot['show_spinner'] = execution_status.get('phase') in ['extracting', 'deciding', 'trading'] if execution_status else False
    
    # Get scheduler info from APScheduler
    from ggbot import get_next_run_from_scheduler, has_scheduler_job

    user_id = bot.get('user_id')
    if user_id and config_id:
        bot['next_run'] = get_next_run_from_scheduler(user_id, config_id)
        bot['is_scheduled'] = has_scheduler_job(user_id, config_id)
    else:
        bot['next_run'] = None
        bot['is_scheduled'] = bot_state == 'active'



async def _enhance_accounts_with_portfolio_data(accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhance account data with comprehensive portfolio analytics.

    Args:
        accounts: List of account dictionaries from database

    Returns:
        Enhanced accounts with portfolio analytics fields
    """
    if not accounts:
        return accounts

    enhanced_accounts = []
    manager = PositionManager()

    for account in accounts:
        try:
            config_id = account.get('config_id')
            if not config_id:
                enhanced_accounts.append(account)
                continue

            # Get comprehensive portfolio summary
            portfolio = await manager.get_portfolio_summary(config_id)

            # Create enhanced account with portfolio analytics
            enhanced_account = dict(account)  # Copy original data

            # Add portfolio analytics fields
            enhanced_account.update({
                'unrealized_pnl': portfolio.unrealized_pnl,
                'current_pnl': portfolio.current_pnl,  # Aggregate unrealized P&L of open positions
                'portfolio_return_pct': portfolio.portfolio_return_pct,  # Total P&L as % of initial balance
                'total_balance': portfolio.total_balance,
                'available_balance': portfolio.available_balance,
                'position_value': portfolio.position_value,
                'win_rate': portfolio.win_rate,
                'avg_win': portfolio.avg_win,
                'avg_loss': portfolio.avg_loss,
                'largest_win': portfolio.largest_win,
                'largest_loss': portfolio.largest_loss,
                'sharpe_ratio': portfolio.sharpe_ratio
            })

            enhanced_accounts.append(enhanced_account)

        except Exception as e:
            # Transient DB errors (SSL, connection timeouts) are expected with Supabase
            # Gracefully degrade - return account without portfolio enhancement
            logger.warning(f"Failed to enhance account {account.get('config_id', 'unknown')} with portfolio data: {e}")
            # Return original account data on error
            enhanced_accounts.append(account)

    return enhanced_accounts


async def _enrich_live_positions_and_accounts(
    bots: List[Dict[str, Any]],
    positions: List[Dict[str, Any]],
    accounts: List[Dict[str, Any]]
) -> tuple:
    """
    Fetch Symphony and AsterDEX data for live/aster bots and merge with SSE response.

    Args:
        bots: List of bot configurations
        positions: List of positions from database (may include live/aster batch_ids)
        accounts: List of accounts from database (paper only)

    Returns:
        tuple: (enriched_positions, enriched_accounts)
    """
    from trading.live.symphony_service import SymphonyLiveTradingService
    from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService

    symphony = SymphonyLiveTradingService()
    aster = AsterDEXV3LiveTradingService()

    # Filter for symphony and aster bots
    symphony_bots = [b for b in bots if b.get('trading_mode') == 'symphony']
    aster_bots = [b for b in bots if b.get('trading_mode') == 'aster']

    if not symphony_bots and not aster_bots:
        return positions, accounts

    enriched_positions = list(positions)
    enriched_accounts = list(accounts)

    # Fetch Symphony data for each symphony bot (in parallel)
    tasks = []
    for bot in symphony_bots:
        config_id = bot['config_id']
        tasks.append(symphony.get_account_metrics(config_id))
        tasks.append(symphony.get_open_positions(config_id))

    try:
        # Gather all results, catching exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results (account metrics and positions alternate)
        for i, bot in enumerate(symphony_bots):
            config_id = bot['config_id']

            # Extract account metrics (even indices: 0, 2, 4, ...)
            account_result = results[i * 2]
            if isinstance(account_result, dict) and not isinstance(account_result, Exception):
                enriched_accounts.append({
                    **account_result,
                    'source': 'live',
                    'account_id': f"symphony_{config_id}"  # Synthetic ID for consistency
                })
            elif isinstance(account_result, Exception):
                logger.warning(f"Failed to fetch Symphony account for {config_id}: {account_result}")

            # Extract positions (odd indices: 1, 3, 5, ...)
            positions_result = results[i * 2 + 1]
            if isinstance(positions_result, list):
                # Remove placeholder live positions from DB (they have NULL fields)
                enriched_positions = [
                    p for p in enriched_positions
                    if not (p.get('config_id') == config_id and p.get('source') == 'live')
                ]

                # Add enriched Symphony positions
                for pos in positions_result:
                    enriched_positions.append({
                        'config_id': config_id,
                        'position_id': pos.get('batch_id'),
                        'symbol': pos.get('symbol'),
                        'side': pos.get('side'),
                        'size_usd': pos.get('size_usd'),
                        'entry_price': pos.get('entry_price'),
                        'current_price': pos.get('current_price'),
                        'unrealized_pnl': pos.get('unrealized_pnl'),
                        'opened_at': pos.get('opened_at'),
                        'stop_loss': pos.get('stop_loss'),
                        'take_profit': pos.get('take_profit'),
                        'leverage': pos.get('leverage'),
                        'source': 'live'
                    })
            elif isinstance(positions_result, Exception):
                logger.warning(f"Failed to fetch Symphony positions for {config_id}: {positions_result}")

        # Fetch AsterDEX data for aster bots (similar pattern)
        aster_tasks = []
        for bot in aster_bots:
            config_id = bot['config_id']
            # Aster service doesn't have account_metrics yet, so just fetch positions
            aster_tasks.append(aster.get_open_positions(config_id))

        if aster_tasks:
            aster_results = await asyncio.gather(*aster_tasks, return_exceptions=True)

            for i, bot in enumerate(aster_bots):
                config_id = bot['config_id']
                positions_result = aster_results[i]

                if isinstance(positions_result, list):
                    # Remove placeholder aster positions from DB
                    enriched_positions = [
                        p for p in enriched_positions
                        if not (p.get('config_id') == config_id and p.get('source') == 'aster')
                    ]

                    # Add enriched Aster positions
                    for pos in positions_result:
                        enriched_positions.append({
                            'config_id': config_id,
                            'position_id': pos.get('batch_id') or pos.get('order_id'),
                            'symbol': pos.get('symbol'),
                            'side': pos.get('side'),
                            'size_usd': pos.get('size_usd'),
                            'entry_price': pos.get('entry_price'),
                            'current_price': pos.get('current_price'),
                            'unrealized_pnl': pos.get('unrealized_pnl'),
                            'opened_at': pos.get('opened_at'),
                            'stop_loss': pos.get('stop_loss'),
                            'take_profit': pos.get('take_profit'),
                            'leverage': pos.get('leverage'),
                            'source': 'aster'
                        })
                elif isinstance(positions_result, Exception):
                    logger.warning(f"Failed to fetch Aster positions for {config_id}: {positions_result}")

    except Exception as e:
        logger.error(f"Failed to enrich live/aster positions and accounts: {e}")
        # Return original data on error

    return enriched_positions, enriched_accounts


def _extract_timeframe_from_config(config_data: Dict[str, Any]) -> str:
    """
    Extract timeframe from bot configuration data.

    Args:
        config_data: Bot configuration dictionary

    Returns:
        Timeframe string (e.g., '1h', '5m') or '5m' as default
    """
    try:
        if isinstance(config_data, dict):
            # Check various possible locations for timeframe
            if 'timeframe' in config_data:
                return config_data['timeframe']
            elif 'extraction_config' in config_data:
                extraction = config_data['extraction_config']
                if isinstance(extraction, dict) and 'timeframe' in extraction:
                    return extraction['timeframe']
        return '5m'  # Default fallback
    except Exception:
        return '5m'