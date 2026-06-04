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
from .redis_status import get_execution_phase, get_bot_status_color, get_bot_status_message, get_redis_client
from trading.paper.positions import PositionManager


async def get_unified_dashboard_data(user_id: str) -> Dict[str, Any]:
    """
    Get all dashboard data for a user with enhanced portfolio analytics.

    Combines:
    - Bot configurations (non-archived)
    - Open positions with current P&L (paper and live)
    - Recent decisions (5 per bot, last 2 hours)
    - Account summaries enhanced with portfolio analytics

    Enhanced with runtime data from scheduler, Redis execution status, and exchange APIs
    (Hyperliquid).

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

            # Fetch pause_reason from Redis for inactive bots (async operation)
            await _fetch_pause_reasons_for_bots(db_data['bots'])

        # Enrich paper positions with current prices from Redis
        # (position monitor writes ephemeral price data to Redis, not Postgres)
        if db_data.get('positions'):
            paper_positions = [p for p in db_data['positions'] if p.get('source') == 'paper']
            if paper_positions:
                try:
                    from trading.paper.supabase_service import enrich_positions_from_redis
                    enrich_positions_from_redis(paper_positions)
                except Exception as e:
                    logger.debug(f"Redis position enrichment failed (using DB values): {e}")

        # Enrich live positions with exchange API data
        # account_snapshots handles account-level metrics, but individual positions
        # need enrichment because the DB query returns NULL for live position details
        if db_data.get('bots'):
            # Check for any live trading bots (hyperliquid)
            has_live_bots = any(
                b.get('trading_mode') == 'hyperliquid'
                for b in db_data['bots']
            )
            if has_live_bots:
                enriched_positions, enriched_accounts = await _enrich_live_positions_and_accounts(
                    db_data.get('bots', []),
                    db_data.get('positions', []) or [],
                    db_data.get('accounts', [])
                )
                db_data['positions'] = enriched_positions
                # Merge enriched accounts (don't replace, as paper accounts come from DB)
                if enriched_accounts:
                    existing_config_ids = {a.get('config_id') for a in db_data.get('accounts', [])}
                    for account in enriched_accounts:
                        if account.get('config_id') not in existing_config_ids:
                            db_data['accounts'].append(account)

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
    # Note: initial_equity is denormalized on configurations table to avoid expensive
    # DISTINCT ON scan of activities table (set on bot creation and reset)
    query = """
    WITH bot_configs AS (
        SELECT c.config_id, c.user_id, c.config_name, c.config_type, c.state, c.config_data,
               c.trading_mode, c.profile_image_url,
               c.first_run_used, c.free_runs_remaining,
               c.initial_equity,
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

        -- Hyperliquid trading positions (batch_ids only - details fetched from Hyperliquid Info API)
        SELECT lt.config_id, lt.batch_id::text AS position_id, lt.symbol AS symbol, NULL AS side, NULL AS size_usd,
               NULL AS entry_price, NULL AS current_price, NULL AS unrealized_pnl, lt.created_at AS opened_at,
               NULL AS stop_loss, NULL AS take_profit, NULL AS leverage, 'hyperliquid' AS source
        FROM live_trades lt
        INNER JOIN bot_configs bc ON lt.config_id = bc.config_id
        WHERE lt.closed_at IS NULL AND bc.trading_mode = 'hyperliquid'
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
    -- NOTE: first_activities CTE removed - initial_equity now stored on configurations table
    deposit_flows AS (
        -- Sum deposits/withdrawals per HL config for cost_basis calculation
        SELECT a.config_id,
               COALESCE(SUM(CASE WHEN a.activity_type = 'deposit' THEN (a.details->>'amount_usdc')::numeric ELSE 0 END), 0) as total_deposits,
               COALESCE(SUM(CASE WHEN a.activity_type = 'withdrawal' THEN (a.details->>'amount_usdc')::numeric ELSE 0 END), 0) as total_withdrawals
        FROM activities a
        INNER JOIN bot_configs bc ON a.config_id = bc.config_id
        WHERE a.activity_type IN ('deposit', 'withdrawal')
          AND bc.trading_mode = 'hyperliquid'
        GROUP BY a.config_id
    ),
    latest_activities AS (
        -- Get latest activity with equity for each of the USER'S bots only
        -- Uses idx_activities_equity_latest partial index (config_id, created_at DESC WHERE total_equity IS NOT NULL)
        SELECT DISTINCT ON (a.config_id)
               a.config_id,
               a.total_equity as current_equity
        FROM activities a
        INNER JOIN bot_configs bc ON a.config_id = bc.config_id
        WHERE a.total_equity IS NOT NULL
        ORDER BY a.config_id, a.created_at DESC
    ),
    account_summaries AS (
        -- Get latest snapshot per config using LATERAL join for index-driven lookup
        -- Forces use of idx_snapshots_latest (config_id, timestamp DESC) — one index seek per config
        SELECT
               snap.config_id,
               snap.snapshot_id as account_id,
               snap.current_balance,
               snap.available_balance,
               snap.margin_used,
               snap.total_pnl,
               snap.unrealized_pnl,
               snap.total_trades,
               snap.win_trades,
               snap.loss_trades,
               snap.open_positions,
               snap.win_rate,
               snap.timestamp as updated_at,
               snap.trading_mode as source,
               -- Calculate performance percentage using cost_basis (initial + deposits - withdrawals)
               -- For Hyperliquid bots: use total_pnl / cost_basis (deposit-immune)
               -- For other bots: use (current_equity - initial_equity) / initial_equity
               CASE
                   WHEN bc.trading_mode = 'hyperliquid' AND snap.total_pnl IS NOT NULL AND bc.initial_equity > 0
                   THEN (snap.total_pnl / (bc.initial_equity + COALESCE(df.total_deposits, 0) - COALESCE(df.total_withdrawals, 0)) * 100)
                   WHEN bc.initial_equity IS NOT NULL AND bc.initial_equity > 0 AND la.current_equity IS NOT NULL
                   THEN ((la.current_equity - bc.initial_equity) / bc.initial_equity * 100)
                   ELSE 0
               END as performance_pct
        FROM bot_configs bc
        LEFT JOIN latest_activities la ON bc.config_id = la.config_id
        LEFT JOIN deposit_flows df ON bc.config_id = df.config_id
        LEFT JOIN LATERAL (
            SELECT asn.config_id, asn.snapshot_id, asn.current_balance, asn.available_balance,
                   asn.margin_used, asn.total_pnl, asn.unrealized_pnl, asn.total_trades,
                   asn.win_trades, asn.loss_trades, asn.open_positions, asn.win_rate,
                   asn.timestamp, asn.trading_mode
            FROM account_snapshots asn
            WHERE asn.config_id = bc.config_id
            ORDER BY asn.timestamp DESC
            LIMIT 1
        ) snap ON true
        WHERE snap.config_id IS NOT NULL
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
                'profile_image_url', bc.profile_image_url,
                'first_run_used', COALESCE(bc.first_run_used, false),
                'free_runs_remaining', COALESCE(bc.free_runs_remaining, 3),
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
    - pause_reason when bot is inactive (for credit exhaustion feedback)
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

    # Note: pause_reason is fetched separately in _fetch_pause_reasons_for_bots()
    # because it requires async Redis access

    # Derive scheduling info from DB state + config timeframe (no scheduler needed)
    from core.scheduler.utils import calculate_next_run, extract_timeframe_from_config

    bot_state = bot.get('state', 'inactive')
    bot['is_scheduled'] = bot_state == 'active'
    if bot['is_scheduled']:
        config_data = bot.get('config_data', {})
        timeframe = extract_timeframe_from_config(config_data)
        bot['next_run'] = calculate_next_run(timeframe) if timeframe and timeframe != 'signal_driven' else None
    else:
        bot['next_run'] = None


async def _fetch_pause_reasons_for_bots(bots: List[Dict[str, Any]]) -> None:
    """
    Fetch pause_reason from Redis for inactive bots.

    When UsageMonitor pauses bots due to credit exhaustion, it stores the reason
    in Redis. This function fetches those reasons for the frontend to display
    appropriate messaging.
    """
    try:
        redis_client = get_redis_client()

        for bot in bots:
            config_id = bot.get('config_id')
            bot_state = bot.get('state', 'inactive')

            if bot_state == 'inactive' and config_id:
                # Key format: bot:pause_reason:{config_id}
                pause_reason = await redis_client.get(f"bot:pause_reason:{config_id}")
                bot['pause_reason'] = pause_reason  # Will be None if not set
            else:
                bot['pause_reason'] = None

    except Exception as e:
        logger.warning(f"Failed to fetch pause reasons from Redis: {e}")
        # Set pause_reason to None for all bots on error
        for bot in bots:
            bot['pause_reason'] = None


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
    Fetch live exchange data for Hyperliquid bots and merge with SSE response.

    Args:
        bots: List of bot configurations
        positions: List of positions from database (may include hyperliquid batch_ids)
        accounts: List of accounts from database (paper only)

    Returns:
        tuple: (enriched_positions, enriched_accounts)
    """
    from trading.live.hyperliquid_service import HyperliquidLiveTradingService

    hyperliquid = HyperliquidLiveTradingService()

    # Filter bots by trading mode
    hyperliquid_bots = [b for b in bots if b.get('trading_mode') == 'hyperliquid']

    if not hyperliquid_bots:
        return positions, accounts

    enriched_positions = list(positions)
    enriched_accounts = list(accounts)

    try:
        # Fetch Hyperliquid data for hyperliquid bots
        if hyperliquid_bots:
            # Group bots by user_id to avoid duplicate API calls per user
            user_bots: Dict[str, List[Dict[str, Any]]] = {}
            for bot in hyperliquid_bots:
                uid = bot.get('user_id', '')
                if uid not in user_bots:
                    user_bots[uid] = []
                user_bots[uid].append(bot)

            for user_id, bots_for_user in user_bots.items():
                try:
                    # Fetch account metrics + positions once per user
                    # (all bots share same Hyperliquid account)
                    hl_tasks = []
                    for bot in bots_for_user:
                        config_id = bot['config_id']
                        hl_tasks.append(hyperliquid.get_account_metrics(config_id, user_id))
                        hl_tasks.append(hyperliquid.get_open_positions(config_id, user_id))

                    hl_results = await asyncio.gather(*hl_tasks, return_exceptions=True)

                    for i, bot in enumerate(bots_for_user):
                        config_id = bot['config_id']

                        # Account metrics (even indices)
                        account_result = hl_results[i * 2]
                        if isinstance(account_result, dict) and account_result.get('status') == 'success':
                            enriched_accounts.append({
                                'config_id': config_id,
                                'source': 'hyperliquid',
                                'account_id': f"hyperliquid_{config_id}",
                                'current_balance': account_result.get('balance'),
                                'available_balance': account_result.get('available_balance'),
                                'unrealized_pnl': account_result.get('total_unrealized_pnl'),
                                'open_positions': account_result.get('positions_count', 0),
                            })
                        elif isinstance(account_result, Exception):
                            logger.warning(f"Failed to fetch Hyperliquid account for {config_id}: {account_result}")

                        # Positions (odd indices)
                        positions_result = hl_results[i * 2 + 1]
                        if isinstance(positions_result, list):
                            # Remove placeholder hyperliquid positions from DB
                            enriched_positions = [
                                p for p in enriched_positions
                                if not (p.get('config_id') == config_id and p.get('source') == 'hyperliquid')
                            ]

                            # Look up live_trade metadata (opened_at, SL/TP prices) for this config
                            trade_metadata = {}
                            try:
                                with get_db_connection() as conn:
                                    with conn.cursor() as cur:
                                        # Join activities to get intended SL/TP prices
                                        cur.execute("""
                                            SELECT lt.batch_id, lt.symbol, lt.created_at,
                                                   lt.stop_loss_order_id, lt.take_profit_order_id,
                                                   a.details->>'stop_loss_price' AS sl_price,
                                                   a.details->>'take_profit_price' AS tp_price
                                            FROM live_trades lt
                                            LEFT JOIN activities a
                                              ON a.trade_id = lt.batch_id
                                              AND a.activity_type = 'trade_entry'
                                            WHERE lt.config_id = %s AND lt.provider = 'hyperliquid'
                                              AND lt.closed_at IS NULL
                                            ORDER BY lt.created_at DESC
                                        """, (config_id,))
                                        for row in cur.fetchall():
                                            trade_metadata[row[1]] = {
                                                'batch_id': row[0],
                                                'opened_at': row[2].isoformat() if row[2] else None,
                                                'sl_order_id': row[3],
                                                'tp_order_id': row[4],
                                                'stop_loss_price': float(row[5]) if row[5] else None,
                                                'take_profit_price': float(row[6]) if row[6] else None,
                                            }
                            except Exception as meta_err:
                                logger.warning(f"Failed to fetch live_trade metadata: {meta_err}")

                            # Get current prices from Redis/price service
                            try:
                                from trading.paper.live_price_service import LivePriceService
                                price_service = LivePriceService()
                            except Exception:
                                price_service = None

                            # Add enriched Hyperliquid positions
                            for pos in positions_result:
                                pos_symbol = pos.get('symbol', '')
                                meta = trade_metadata.get(pos_symbol, {})

                                # Fetch current price
                                current_price = None
                                if price_service:
                                    try:
                                        mp = await price_service.get_current_price(pos_symbol)
                                        current_price = mp.mid
                                    except Exception:
                                        pass

                                enriched_positions.append({
                                    'config_id': config_id,
                                    'position_id': meta.get('batch_id') or pos.get('batch_id'),
                                    'symbol': pos_symbol,
                                    'side': pos.get('side'),
                                    'size_usd': float(pos.get('size', 0)) * float(pos.get('entry_price', 0)),
                                    'entry_price': pos.get('entry_price'),
                                    'current_price': current_price,
                                    'unrealized_pnl': pos.get('unrealized_pnl'),
                                    'opened_at': meta.get('opened_at'),
                                    'stop_loss': meta.get('stop_loss_price'),
                                    'take_profit': meta.get('take_profit_price'),
                                    'liquidation_price': pos.get('liquidation_price'),
                                    'leverage': pos.get('leverage'),
                                    'margin_type': pos.get('margin_type', 'cross'),
                                    'source': 'hyperliquid'
                                })
                        elif isinstance(positions_result, Exception):
                            logger.warning(f"Failed to fetch Hyperliquid positions for {config_id}: {positions_result}")

                except Exception as e:
                    logger.warning(f"Failed to enrich Hyperliquid data for user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Failed to enrich live positions and accounts: {e}")
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