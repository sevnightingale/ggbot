"""
Dojo Public — Public-facing leaderboard and stats for The Dojo.

All functions use sync get_db_connection (called from API endpoints, not async scheduler).
"""

from typing import Dict, Any, List

from core.common.db import get_db_connection
from core.common.logger import logger

_log = logger.bind(component="dojo_public")


def get_dojo_bots() -> List[Dict[str, Any]]:
    """Get all active, visible paper bots with ELO and performance data."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.config_id,
                    c.config_name,
                    c.elo_rating,
                    c.is_house_bot,
                    c.config_data->>'selected_pair' AS selected_pair,
                    c.config_data->'llm_config'->>'provider' AS llm_provider,
                    c.profile_image_url,
                    pa.total_trades,
                    pa.win_trades,
                    pa.total_pnl,
                    CASE WHEN pa.total_trades > 0
                        THEN ROUND((pa.win_trades::numeric / pa.total_trades) * 100, 1)
                        ELSE 0 END AS win_rate
                FROM configurations c
                LEFT JOIN paper_accounts pa ON pa.config_id = c.config_id
                WHERE c.state = 'active'
                  AND c.dojo_visible = TRUE
                  AND (c.trading_mode IS NULL OR c.trading_mode = 'paper')
                  AND (c.config_type IS NULL OR c.config_type = 'scheduled_trading')
                ORDER BY c.elo_rating DESC, c.config_name ASC
            """)

            bots = []
            for row in cur.fetchall():
                bots.append({
                    "config_id": str(row[0]),
                    "config_name": row[1] or "Unnamed Bot",
                    "elo_rating": row[2] or 1200,
                    "is_house_bot": row[3] or False,
                    "selected_pair": row[4] or "BTC/USDT",
                    "llm_provider": row[5] or "default",
                    "profile_image_url": row[6],
                    "total_trades": row[7] or 0,
                    "win_trades": row[8] or 0,
                    "total_pnl": float(row[9]) if row[9] else 0.0,
                    "win_rate": float(row[10]) if row[10] else 0.0,
                })
            return bots


def get_house_bots() -> List[Dict[str, Any]]:
    """Get all House Bots for the Dojo challenge UI."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.config_id,
                    c.config_name,
                    c.elo_rating,
                    c.state,
                    c.config_data->>'selected_pair' AS selected_pair,
                    c.config_data->'decision'->>'analysis_frequency' AS frequency,
                    c.profile_image_url
                FROM configurations c
                WHERE c.is_house_bot = TRUE
                ORDER BY c.config_name ASC
            """)

            bots = []
            for row in cur.fetchall():
                name = row[1] or "House Bot"
                # Derive format from name
                if 'Blitz' in name:
                    match_format = 'blitz'
                elif 'Rapid' in name:
                    match_format = 'rapid'
                else:
                    match_format = 'standard'

                bots.append({
                    "config_id": str(row[0]),
                    "config_name": name,
                    "elo_rating": row[2] or 1200,
                    "state": row[3] or "inactive",
                    "selected_pair": row[4] or "BTC/USDT",
                    "frequency": row[5] or "4h",
                    "format": match_format,
                    "profile_image_url": row[6],
                    "match_record": {"wins": 0, "losses": 0, "draws": 0},  # Phase 4
                })
            return bots


def get_dojo_stats() -> Dict[str, Any]:
    """Get aggregate Dojo statistics."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total_bots,
                    COALESCE(ROUND(AVG(c.elo_rating)), 1200) AS avg_elo,
                    COALESCE(MAX(c.elo_rating), 1200) AS max_elo,
                    COUNT(*) FILTER (WHERE c.is_house_bot = TRUE) AS house_bots
                FROM configurations c
                WHERE c.state = 'active'
                  AND c.dojo_visible = TRUE
                  AND (c.trading_mode IS NULL OR c.trading_mode = 'paper')
                  AND (c.config_type IS NULL OR c.config_type = 'scheduled_trading')
            """)
            row = cur.fetchone()
            return {
                "total_bots": row[0] or 0,
                "avg_elo": int(row[1]) if row[1] else 1200,
                "max_elo": int(row[2]) if row[2] else 1200,
                "house_bots": row[3] or 0,
                "active_matches": 0,  # Phase 4
                "total_matches": 0,   # Phase 4
            }
