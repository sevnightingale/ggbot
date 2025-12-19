"""
Public API Endpoints

Public-facing endpoints that require no authentication.
Used for showcase features like the Arena competition page.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query

from core.common.db import get_db_connection
from core.common.logger import logger

router = APIRouter(prefix="/api/v2/public", tags=["public"])


@router.get("/arena/performance")
async def get_arena_performance(
    hours: int = Query(default=504, ge=1, le=720)  # Default 21 days (504 hours), max 30 days
) -> Dict[str, Any]:
    """
    Get performance comparison for Arena showcase bots.

    Public endpoint - no authentication required.
    Returns performance data only for bots marked with is_public_performance = true.

    Formula: total_equity = current_balance + unrealized_pnl
    (Source: AccountMetricsCalculator.calculate_total_equity)

    Args:
        hours: Time window in hours (default 504 = 21 days for competition)

    Returns:
        {
            "success": true,
            "hours": 504,
            "competition_days": 21,
            "bots": [
                {
                    "config_id": "...",
                    "config_name": "The Nomad",
                    "profile_image_url": "...",
                    "description": "Bot description text",
                    "data_points": [{"timestamp": "...", "equity": 10500.50}, ...],
                    "current_equity": 10500.50,
                    "current_pnl": 500.50,
                    "initial_balance": 10000.00,
                    "total_trades": 45,
                    "win_rate": 0.67,
                    "open_positions": 2,
                    "frequency": "1h",
                    "model": "grok",
                    "symbol": "BTC/USDT",
                    "data_sources": {...},
                    "stop_loss": "5",
                    "take_profit": "10",
                    "max_margin": "20"
                }
            ]
        }
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get equity snapshots for showcase bots only
            # Formula: total_equity = current_balance + unrealized_pnl
            # (Matches AccountMetricsCalculator.calculate_total_equity)
            cur.execute("""
                SELECT
                    c.config_id,
                    c.config_name,
                    c.profile_image_url,
                    s.timestamp,
                    COALESCE(s.current_balance, 0) +
                    COALESCE(s.unrealized_pnl, 0) as total_equity,
                    s.total_pnl,
                    s.total_trades,
                    s.win_rate,
                    s.open_positions,
                    pa.initial_balance,
                    s.current_balance,
                    s.unrealized_pnl,
                    c.description,
                    c.config_data->'decision'->>'analysis_frequency' as frequency,
                    c.config_data->'llm_config'->>'model' as model,
                    c.config_data->>'selected_pair' as symbol,
                    c.config_data->'extraction'->'selected_data_sources' as data_sources,
                    c.config_data->'trading'->'risk_management'->>'default_stop_loss_percent' as stop_loss,
                    c.config_data->'trading'->'risk_management'->>'default_take_profit_percent' as take_profit,
                    c.config_data->'trading'->'position_sizing'->>'max_margin_percent' as max_margin
                FROM account_snapshots s
                JOIN configurations c ON s.config_id = c.config_id
                LEFT JOIN paper_accounts pa ON s.config_id = pa.config_id
                WHERE c.is_public_performance = true
                AND c.state = 'active'
                AND s.timestamp >= %s
                ORDER BY c.config_name, s.timestamp ASC
            """, (cutoff_time,))

            rows = cur.fetchall()

            # Group by bot
            bots_data = {}
            for row in rows:
                config_id = row[0]
                config_name = row[1]
                profile_image_url = row[2]
                timestamp = row[3]
                total_equity = float(row[4])
                total_pnl = float(row[5] or 0)
                total_trades = row[6] or 0
                win_rate = float(row[7] or 0)
                open_positions = row[8] or 0
                initial_balance = float(row[9] or 10000)
                current_balance = float(row[10] or 0)
                unrealized_pnl = float(row[11] or 0)
                description = row[12]
                frequency = row[13]
                model = row[14]
                symbol = row[15]
                data_sources = row[16]  # JSONB - already parsed
                stop_loss = row[17]
                take_profit = row[18]
                max_margin = row[19]

                if config_id not in bots_data:
                    bots_data[config_id] = {
                        "config_id": config_id,
                        "config_name": config_name,
                        "profile_image_url": profile_image_url,
                        "description": description,
                        "data_points": [],
                        "current_equity": total_equity,
                        "current_pnl": total_pnl,
                        "initial_balance": initial_balance,
                        "total_trades": total_trades,
                        "win_rate": win_rate,
                        "open_positions": open_positions,
                        "current_balance": current_balance,
                        "unrealized_pnl": unrealized_pnl,
                        # Config details
                        "frequency": frequency,
                        "model": model,
                        "symbol": symbol,
                        "data_sources": data_sources,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "max_margin": max_margin
                    }

                # Add data point
                bots_data[config_id]["data_points"].append({
                    "timestamp": timestamp.isoformat(),
                    "equity": total_equity
                })

                # Update current values (last snapshot)
                bots_data[config_id]["current_equity"] = total_equity
                bots_data[config_id]["current_pnl"] = total_pnl
                bots_data[config_id]["total_trades"] = total_trades
                bots_data[config_id]["win_rate"] = win_rate
                bots_data[config_id]["open_positions"] = open_positions
                bots_data[config_id]["current_balance"] = current_balance
                bots_data[config_id]["unrealized_pnl"] = unrealized_pnl

            # Convert to list and sort by current equity descending
            bots_list = list(bots_data.values())
            bots_list.sort(key=lambda x: x["current_equity"], reverse=True)

    logger.info(f"Arena performance query: {len(bots_list)} showcase bots, {hours}h window")

    return {
        "success": True,
        "hours": hours,
        "competition_days": hours // 24,
        "bots": bots_list
    }
