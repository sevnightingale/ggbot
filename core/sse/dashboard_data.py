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
    - Open positions with current P&L
    - Recent decisions (5 per bot, last 2 hours)
    - Account summaries enhanced with portfolio analytics

    Enhanced with runtime data from scheduler and Redis execution status.

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

        # Enhance accounts with portfolio analytics (async operation)
        if db_data.get('accounts'):
            enhanced_accounts = await _enhance_accounts_with_portfolio_data(db_data['accounts'])
            db_data['accounts'] = enhanced_accounts

        return db_data

    except Exception as e:
        logger.error(f"Failed to get unified dashboard data for user {user_id}: {e}")
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
        SELECT c.config_id, c.user_id, c.config_name, c.state, c.config_data,
               c.created_at, c.updated_at
        FROM configurations c
        WHERE c.user_id = %s AND c.state != 'archived'
    ),
    open_positions AS (
        SELECT pt.config_id, pt.trade_id, pt.symbol, pt.side, pt.size_usd,
               pt.entry_price, pt.current_price, pt.unrealized_pnl, pt.opened_at,
               pt.stop_loss, pt.take_profit, pt.leverage
        FROM paper_trades pt
        INNER JOIN bot_configs bc ON pt.config_id = bc.config_id
        WHERE pt.status = 'open'
        ORDER BY pt.opened_at DESC
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
    account_summaries AS (
        SELECT pa.config_id, pa.account_id, pa.current_balance, pa.total_pnl, 
               pa.total_trades, pa.win_trades, pa.loss_trades, pa.open_positions,
               pa.updated_at
        FROM paper_accounts pa
        INNER JOIN bot_configs bc ON pa.config_id = bc.config_id
    )
    SELECT json_build_object(
        'bots', COALESCE((SELECT json_agg(
            json_build_object(
                'config_id', bc.config_id,
                'user_id', bc.user_id,
                'config_name', bc.config_name,
                'config_type', 'autonomous_trading',
                'state', bc.state,
                'config_data', json_build_object(
                    'schema_version', bc.config_data->>'schema_version',
                    'config_type', bc.config_data->>'config_type',
                    'selected_pair', bc.config_data->>'selected_pair',
                    'extraction', bc.config_data->'extraction',
                    'decision', bc.config_data->'decision',
                    'trading', bc.config_data->'trading',
                    'llm_config', bc.config_data->'llm_config',
                    'telegram_integration', bc.config_data->'telegram_integration'
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
            
            if result and result[0]:
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
            logger.error(f"Failed to enhance account {account.get('config_id', 'unknown')} with portfolio data: {e}")
            # Return original account data on error
            enhanced_accounts.append(account)

    return enhanced_accounts


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