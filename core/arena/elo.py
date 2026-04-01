"""
Elo Engine — Composite scoring and Elo rating system for The Dojo.

Pure computation functions. No external dependencies beyond stdlib + DB.

Composite Match Score:
  PnL %       — 40% (Standard) / 45% (Rapid) / 60% (Blitz)
  Sortino     — 25% / 20% / 5%
  Drawdown    — 20% / 20% / 20%
  Win Rate    — 15% / 15% / 15%

Elo uses standard formula with K-factor scaling:
  K=32 (< 10 rated events), K=24 (10-30), K=16 (> 30 AND > 1600 Elo)
"""

import json
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

from core.common.db import get_db_connection
from core.common.logger import logger

_log = logger.bind(component="elo_engine")

# ─── Format-Specific Weights ─────────────────────────────────────────────────

FORMAT_WEIGHTS = {
    'standard': {'pnl': 0.40, 'sortino': 0.25, 'drawdown': 0.20, 'win_rate': 0.15},
    'rapid':    {'pnl': 0.45, 'sortino': 0.20, 'drawdown': 0.20, 'win_rate': 0.15},
    'blitz':    {'pnl': 0.60, 'sortino': 0.05, 'drawdown': 0.20, 'win_rate': 0.15},
}

FORMAT_DURATIONS = {
    'blitz': 1,
    'rapid': 7,
    'standard': 21,
}

# Starting Elo for all bots
DEFAULT_ELO = 1200

# Sortino cap when no negative returns exist
SORTINO_CAP = 10.0


# ─── Sortino Ratio ───────────────────────────────────────────────────────────

def calculate_sortino_ratio(daily_returns: List[float], period_days: int) -> float:
    """
    Calculate annualized Sortino ratio from daily returns.

    Sortino = mean(returns) / std(negative_returns_only) * sqrt(period_days)

    Only penalizes downside volatility — upside variance is a feature for trading bots.

    Edge cases:
      - No returns → 0.0
      - No negative returns → SORTINO_CAP (capped, not infinity)
      - Single return → uses that return as mean, 0 downside std → capped
    """
    if not daily_returns:
        return 0.0

    mean_return = sum(daily_returns) / len(daily_returns)

    # Downside deviation: std of negative returns only
    negative_returns = [r for r in daily_returns if r < 0]

    if not negative_returns:
        # No downside — return capped positive value if mean is positive, else 0
        return SORTINO_CAP if mean_return > 0 else 0.0

    # Standard deviation of negative returns
    neg_mean = sum(negative_returns) / len(negative_returns)
    neg_variance = sum((r - neg_mean) ** 2 for r in negative_returns) / len(negative_returns)
    downside_std = math.sqrt(neg_variance) if neg_variance > 0 else 0.0001  # avoid div/0

    # Annualization factor: sqrt(period_days) scales to the match duration
    sortino = (mean_return / downside_std) * math.sqrt(max(period_days, 1))

    # Cap to prevent extreme outliers
    return min(max(sortino, -SORTINO_CAP), SORTINO_CAP)


# ─── Composite Score ─────────────────────────────────────────────────────────

def calculate_composite_score(
    config_id: str,
    start_time: datetime,
    end_time: datetime,
    match_format: str = 'standard',
    initial_equity: float = 10000.0,
) -> Dict[str, Any]:
    """
    Calculate composite match score for a bot over a time window.

    Queries paper_trades for the config within the window.
    Returns all components plus weighted composite.

    Returns:
        {
            'pnl_pct': float,
            'sortino': float,
            'max_drawdown_pct': float,
            'win_rate': float,
            'total_trades': int,
            'composite_score': float,  # 0.0-1.0 normalized
            'components': { ... raw values ... }
        }
    """
    weights = FORMAT_WEIGHTS.get(match_format, FORMAT_WEIGHTS['standard'])
    period_days = FORMAT_DURATIONS.get(match_format, 21)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get all closed trades in the window
            cur.execute("""
                SELECT realized_pnl, closed_at, opened_at, side, entry_price, current_price, size_usd
                FROM paper_trades
                WHERE config_id = %s
                  AND status = 'closed'
                  AND closed_at >= %s
                  AND closed_at <= %s
                ORDER BY closed_at ASC
            """, (config_id, start_time, end_time))
            trades = cur.fetchall()

    if not trades:
        return {
            'pnl_pct': 0.0,
            'sortino': 0.0,
            'max_drawdown_pct': 0.0,
            'win_rate': 0.0,
            'total_trades': 0,
            'composite_score': 0.0,
            'components': {
                'pnl_score': 0.0,
                'sortino_score': 0.0,
                'drawdown_score': 0.0,
                'win_rate_score': 0.0,
            }
        }

    # ── PnL % ──
    total_pnl = sum(float(t[0] or 0) for t in trades)
    pnl_pct = (total_pnl / initial_equity) * 100

    # ── Win Rate ──
    wins = sum(1 for t in trades if float(t[0] or 0) > 0)
    total_trades = len(trades)
    win_rate = wins / total_trades if total_trades > 0 else 0.0

    # ── Daily Returns for Sortino ──
    # Group P&L by day
    daily_pnl: Dict[str, float] = {}
    for t in trades:
        day = t[1].strftime('%Y-%m-%d') if t[1] else 'unknown'
        daily_pnl[day] = daily_pnl.get(day, 0) + float(t[0] or 0)

    daily_returns = [pnl / initial_equity for pnl in daily_pnl.values()]
    sortino = calculate_sortino_ratio(daily_returns, period_days)

    # ── Max Drawdown ──
    # Walk through trades chronologically, track running equity and peak
    running_equity = initial_equity
    peak_equity = initial_equity
    max_drawdown = 0.0

    for t in trades:
        running_equity += float(t[0] or 0)
        if running_equity > peak_equity:
            peak_equity = running_equity
        drawdown = (peak_equity - running_equity) / peak_equity if peak_equity > 0 else 0
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    max_drawdown_pct = max_drawdown * 100

    # ── Normalize to 0-1 scores ──
    # PnL: sigmoid-ish normalization. 0% → 0.5, +10% → ~0.85, -10% → ~0.15
    pnl_score = 1 / (1 + math.exp(-pnl_pct / 5))

    # Sortino: normalize to 0-1. 0 → 0.5, 2.0 → ~0.73, -2.0 → ~0.27
    sortino_score = 1 / (1 + math.exp(-sortino / 2))

    # Drawdown: inverted — lower is better. 0% → 1.0, 10% → 0.5, 20% → ~0.27
    drawdown_score = 1 / (1 + math.exp((max_drawdown_pct - 10) / 5))

    # Win rate: direct (already 0-1)
    win_rate_score = win_rate

    # ── Weighted composite ──
    composite = (
        weights['pnl'] * pnl_score +
        weights['sortino'] * sortino_score +
        weights['drawdown'] * drawdown_score +
        weights['win_rate'] * win_rate_score
    )

    return {
        'pnl_pct': round(pnl_pct, 2),
        'sortino': round(sortino, 3),
        'max_drawdown_pct': round(max_drawdown_pct, 2),
        'win_rate': round(win_rate, 3),
        'total_trades': total_trades,
        'composite_score': round(composite, 4),
        'components': {
            'pnl_score': round(pnl_score, 4),
            'sortino_score': round(sortino_score, 4),
            'drawdown_score': round(drawdown_score, 4),
            'win_rate_score': round(win_rate_score, 4),
        }
    }


# ─── Elo Update ──────────────────────────────────────────────────────────────

def _get_k_factor(config_id: str) -> int:
    """Determine K-factor based on number of rated events and current Elo."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM elo_history WHERE config_id = %s",
                (config_id,)
            )
            event_count = cur.fetchone()[0]

            cur.execute(
                "SELECT elo_rating FROM configurations WHERE config_id = %s",
                (config_id,)
            )
            row = cur.fetchone()
            elo = row[0] if row else DEFAULT_ELO

    if event_count < 10:
        return 32
    elif event_count < 30:
        return 24
    elif elo > 1600:
        return 16
    else:
        return 24


def update_elo(
    rating_a: int,
    rating_b: int,
    score_a: float,
    score_b: float,
    k_a: int = 24,
    k_b: int = 24,
) -> Tuple[int, int]:
    """
    Standard Elo update for two players.

    score_a/score_b: composite match scores (higher = better performance).
    The actual Elo outcome is derived from who scored higher:
      winner gets S=1, loser gets S=0, draw gives S=0.5 each.

    Returns (new_rating_a, new_rating_b).
    """
    # Determine outcome from composite scores
    if score_a > score_b:
        s_a, s_b = 1.0, 0.0
    elif score_b > score_a:
        s_a, s_b = 0.0, 1.0
    else:
        s_a, s_b = 0.5, 0.5

    # Expected scores
    e_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    e_b = 1 / (1 + 10 ** ((rating_a - rating_b) / 400))

    # New ratings
    new_a = round(rating_a + k_a * (s_a - e_a))
    new_b = round(rating_b + k_b * (s_b - e_b))

    # Floor at 0 (though practically never reached)
    return max(new_a, 0), max(new_b, 0)


# ─── Record Elo Change ───────────────────────────────────────────────────────

def record_elo_change(
    config_id: str,
    elo_before: int,
    elo_after: int,
    reason: str,
    match_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Write to elo_history and update configurations.elo_rating."""
    change = elo_after - elo_before

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO elo_history (config_id, elo_before, elo_after, change, reason, match_id, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                config_id, elo_before, elo_after, change, reason,
                match_id,
                json.dumps(details) if details else None,
            ))

            cur.execute("""
                UPDATE configurations SET elo_rating = %s, updated_at = NOW()
                WHERE config_id = %s
            """, (elo_after, config_id))

            conn.commit()

    _log.info(f"Elo updated: config={config_id[:8]} {elo_before}→{elo_after} ({'+' if change >= 0 else ''}{change}) reason={reason}")


# ─── Weekly Rolling Elo ──────────────────────────────────────────────────────

async def weekly_rolling_update():
    """
    Swiss-system weekly Elo update for all active Dojo-visible paper bots.

    Runs Sundays at midnight UTC. Calculates trailing 7-day composite score
    for all eligible bots, pairs them by rank, and updates Elo.

    Bots with zero trades in the window are excluded (no Elo change for idle bots).
    """
    import asyncio

    _log.info("Starting weekly rolling Elo update")
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Get all eligible bots
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT config_id, elo_rating
                FROM configurations
                WHERE state = 'active'
                  AND dojo_visible = TRUE
                  AND (trading_mode IS NULL OR trading_mode = 'paper')
                  AND (config_type IS NULL OR config_type = 'scheduled_trading')
                  AND is_house_bot = FALSE
            """)
            bots = [(str(row[0]), row[1] or DEFAULT_ELO) for row in cur.fetchall()]

    if len(bots) < 2:
        _log.info(f"Weekly Elo: only {len(bots)} eligible bots, skipping")
        return

    # Calculate composite scores for each bot (trailing 7 days)
    scored_bots = []
    for config_id, elo in bots:
        score = calculate_composite_score(config_id, week_ago, now, match_format='rapid')
        if score['total_trades'] > 0:
            scored_bots.append((config_id, elo, score['composite_score'], score))

    if len(scored_bots) < 2:
        _log.info(f"Weekly Elo: only {len(scored_bots)} bots with trades, skipping")
        return

    # Sort by composite score (Swiss-system: pair adjacent)
    scored_bots.sort(key=lambda x: x[2], reverse=True)

    updates = 0
    for i in range(0, len(scored_bots) - 1, 2):
        a_id, a_elo, a_score, a_details = scored_bots[i]
        b_id, b_elo, b_score, b_details = scored_bots[i + 1]

        k_a = _get_k_factor(a_id)
        k_b = _get_k_factor(b_id)
        new_a, new_b = update_elo(a_elo, b_elo, a_score, b_score, k_a, k_b)

        if new_a != a_elo:
            record_elo_change(a_id, a_elo, new_a, 'rolling_weekly', details={
                'composite_score': a_score,
                'opponent_id': b_id,
                'opponent_score': b_score,
            })
            updates += 1

        if new_b != b_elo:
            record_elo_change(b_id, b_elo, new_b, 'rolling_weekly', details={
                'composite_score': b_score,
                'opponent_id': a_id,
                'opponent_score': a_score,
            })
            updates += 1

    _log.info(f"Weekly Elo: {updates} rating changes across {len(scored_bots)} bots")
