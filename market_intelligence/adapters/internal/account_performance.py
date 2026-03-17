"""
Account Performance Adapter

Pre-computed by account-monitor service every 5 minutes and cached in Redis.
The adapter reads from Redis (sub-ms, async-safe) instead of querying the DB
directly — this avoids sync DB calls in the async bot execution pipeline
which previously caused event loop deadlocks under pool contention.

The _fetch_paper_performance / _fetch_live_performance methods are called by
the account-monitor process (where sync DB is safe), not by the adapter's
fetch() method.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from core.common.db import get_db_connection
from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse, AdapterError


class AccountPerformanceAdapter(DataAdapter):
    """
    Adapter for bot account performance data.

    fetch() reads pre-computed data from Redis (written by account-monitor).
    _fetch_*() methods are called by the monitor process for computation.
    """

    name = "account_performance"
    data_type = "account_performance"

    RECENT_TRADES_LIMIT = 10
    REDIS_KEY_PREFIX = "acct_perf"

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Read pre-computed account performance from Redis.

        Data is written by account-monitor every 5 minutes. This method
        does NO database queries — it only reads from Redis.
        """
        config_id = params.get('config_id')
        if not config_id:
            raise AdapterError("config_id parameter is required")

        # Read from Redis (written by account-monitor)
        try:
            import redis as sync_redis
            r = sync_redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            cached = r.get(f"{self.REDIS_KEY_PREFIX}:{config_id}")
            r.close()

            if cached:
                data = json.loads(cached)
                self._log.debug(
                    f"Account performance for {config_id[:8]} from Redis "
                    f"({data.get('total_trades', 0)} trades, {data.get('win_rate_pct', 0):.1f}% win rate)"
                )
                return AdapterResponse(
                    data=data,
                    metadata=self.build_metadata(source='redis_cache', config_id=config_id),
                    confidence=1.0,
                    related_queries=[]
                )
        except Exception as e:
            self._log.debug(f"Redis read failed for {config_id[:8]}: {e}")

        # No cached data yet — monitor will populate on next 5-min cycle
        self._log.debug(f"No cached account performance for {config_id[:8]}, returning empty")
        return AdapterResponse(
            data=self._empty_performance(),
            metadata=self.build_metadata(source='empty_fallback', config_id=config_id),
            confidence=0.5,
            related_queries=[]
        )

    # =========================================================================
    # Computation methods — called by account-monitor (sync DB is safe there)
    # =========================================================================

    def _fetch_paper_performance(self, config_id: str) -> Dict[str, Any]:
        """Fetch performance from paper trading tables. Called by account-monitor."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Account summary
                cur.execute("""
                    SELECT initial_balance, current_balance, total_pnl,
                           total_trades, win_trades, loss_trades
                    FROM paper_accounts
                    WHERE config_id = %s
                """, (config_id,))
                account = cur.fetchone()

                if not account:
                    return self._empty_performance()

                initial_balance, current_balance, total_pnl, total_trades, win_trades, loss_trades = account
                initial_balance = float(initial_balance or 0)
                current_balance = float(current_balance or 0)

                # Peak equity from snapshots
                cur.execute("""
                    SELECT MAX(current_balance + COALESCE(unrealized_pnl, 0))
                    FROM account_snapshots
                    WHERE config_id = %s
                """, (config_id,))
                peak_row = cur.fetchone()
                peak_equity = float(peak_row[0]) if peak_row and peak_row[0] else initial_balance
                peak_equity = max(peak_equity, initial_balance)

                # Average win/loss + largest win/loss from closed trades
                cur.execute("""
                    SELECT
                        AVG(CASE WHEN realized_pnl > 0 THEN realized_pnl / NULLIF(size_usd, 0) * 100 END),
                        AVG(CASE WHEN realized_pnl < 0 THEN realized_pnl / NULLIF(size_usd, 0) * 100 END),
                        MAX(CASE WHEN realized_pnl > 0 THEN realized_pnl / NULLIF(size_usd, 0) * 100 END),
                        MIN(CASE WHEN realized_pnl < 0 THEN realized_pnl / NULLIF(size_usd, 0) * 100 END)
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'closed' AND size_usd > 0
                """, (config_id,))
                stats_row = cur.fetchone()
                avg_win_pct = round(float(stats_row[0]), 1) if stats_row and stats_row[0] else 0.0
                avg_loss_pct = round(float(stats_row[1]), 1) if stats_row and stats_row[1] else 0.0
                largest_win_pct = round(float(stats_row[2]), 1) if stats_row and stats_row[2] else 0.0
                largest_loss_pct = round(float(stats_row[3]), 1) if stats_row and stats_row[3] else 0.0

                # Drawdown duration: time since peak equity was last reached
                cur.execute("""
                    SELECT timestamp FROM account_snapshots
                    WHERE config_id = %s
                      AND (current_balance + COALESCE(unrealized_pnl, 0)) >= %s - 0.01
                    ORDER BY timestamp DESC LIMIT 1
                """, (config_id, peak_equity))
                peak_ts_row = cur.fetchone()

                # Recent closed trades (for streak + history)
                cur.execute("""
                    SELECT side, symbol, realized_pnl, size_usd, close_reason, closed_at
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'closed' AND closed_at IS NOT NULL
                    ORDER BY closed_at DESC
                    LIMIT %s
                """, (config_id, self.RECENT_TRADES_LIMIT))
                recent_rows = cur.fetchall()

        return self._build_response(
            account_equity=current_balance,
            initial_balance=initial_balance,
            peak_equity=peak_equity,
            total_trades=total_trades or 0,
            win_trades=win_trades or 0,
            loss_trades=loss_trades or 0,
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            largest_win_pct=largest_win_pct,
            largest_loss_pct=largest_loss_pct,
            peak_timestamp=peak_ts_row[0] if peak_ts_row else None,
            recent_rows=recent_rows,
            use_pnl_based_metrics=False,
            total_pnl=float(total_pnl or 0),
        )

    def _fetch_live_performance(self, config_id: str) -> Dict[str, Any]:
        """Fetch performance from Hyperliquid live trading tables. Called by account-monitor."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Aggregate from live_trades
                cur.execute("""
                    SELECT
                        COUNT(*) as total_trades,
                        COUNT(*) FILTER (WHERE realized_pnl > 0) as win_trades,
                        COUNT(*) FILTER (WHERE realized_pnl < 0) as loss_trades,
                        SUM(realized_pnl) as total_pnl,
                        AVG(CASE WHEN realized_pnl > 0 THEN realized_pnl / NULLIF(size_usd, 0) * 100 END),
                        AVG(CASE WHEN realized_pnl < 0 THEN realized_pnl / NULLIF(size_usd, 0) * 100 END),
                        MAX(CASE WHEN realized_pnl > 0 THEN realized_pnl / NULLIF(size_usd, 0) * 100 END),
                        MIN(CASE WHEN realized_pnl < 0 THEN realized_pnl / NULLIF(size_usd, 0) * 100 END)
                    FROM live_trades
                    WHERE config_id = %s AND closed_at IS NOT NULL
                """, (config_id,))
                stats = cur.fetchone()

                total_trades = stats[0] or 0
                win_trades = stats[1] or 0
                loss_trades = stats[2] or 0
                total_pnl = float(stats[3] or 0)
                avg_win_pct = round(float(stats[4]), 1) if stats[4] else 0.0
                avg_loss_pct = round(float(stats[5]), 1) if stats[5] else 0.0
                largest_win_pct = round(float(stats[6]), 1) if stats[6] else 0.0
                largest_loss_pct = round(float(stats[7]), 1) if stats[7] else 0.0

                # Current equity from latest snapshot
                cur.execute("""
                    SELECT current_balance, unrealized_pnl, total_pnl
                    FROM account_snapshots
                    WHERE config_id = %s
                    ORDER BY timestamp DESC LIMIT 1
                """, (config_id,))
                snap = cur.fetchone()
                if snap:
                    current_equity = float(snap[0] or 0) + float(snap[1] or 0)
                    # Use snapshot total_pnl (realized + unrealized) for deposit-immune metrics
                    snapshot_total_pnl = float(snap[2]) if snap[2] is not None else total_pnl
                else:
                    current_equity = 0.0
                    snapshot_total_pnl = total_pnl

                # Peak total_pnl from snapshots (deposit-immune peak)
                cur.execute("""
                    SELECT MAX(total_pnl)
                    FROM account_snapshots
                    WHERE config_id = %s AND total_pnl IS NOT NULL
                """, (config_id,))
                peak_pnl_row = cur.fetchone()
                peak_pnl = float(peak_pnl_row[0]) if peak_pnl_row and peak_pnl_row[0] else 0.0

                # Initial equity from configurations table
                cur.execute("""
                    SELECT initial_equity
                    FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                init_row = cur.fetchone()
                initial_equity = float(init_row[0]) if init_row and init_row[0] else current_equity

                # Peak equity = initial + peak_pnl (deposit-immune)
                peak_equity = initial_equity + max(peak_pnl, 0)

                # Drawdown duration: time since peak pnl was last reached
                cur.execute("""
                    SELECT timestamp FROM account_snapshots
                    WHERE config_id = %s AND total_pnl IS NOT NULL
                      AND total_pnl >= %s - 0.01
                    ORDER BY timestamp DESC LIMIT 1
                """, (config_id, peak_pnl))
                peak_ts_row = cur.fetchone()

                # Recent closed trades
                cur.execute("""
                    SELECT side, symbol, realized_pnl, size_usd, NULL as close_reason, closed_at
                    FROM live_trades
                    WHERE config_id = %s AND closed_at IS NOT NULL
                    ORDER BY closed_at DESC
                    LIMIT %s
                """, (config_id, self.RECENT_TRADES_LIMIT))
                recent_rows = cur.fetchall()

        return self._build_response(
            account_equity=current_equity,
            initial_balance=initial_equity,
            peak_equity=peak_equity,
            total_trades=total_trades,
            win_trades=win_trades,
            loss_trades=loss_trades,
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            largest_win_pct=largest_win_pct,
            largest_loss_pct=largest_loss_pct,
            peak_timestamp=peak_ts_row[0] if peak_ts_row else None,
            recent_rows=recent_rows,
            use_pnl_based_metrics=True,
            total_pnl=snapshot_total_pnl,
        )

    def _build_response(
        self,
        account_equity: float,
        initial_balance: float,
        peak_equity: float,
        total_trades: int,
        win_trades: int,
        loss_trades: int,
        avg_win_pct: float,
        avg_loss_pct: float,
        largest_win_pct: float,
        largest_loss_pct: float,
        peak_timestamp,
        recent_rows: list,
        use_pnl_based_metrics: bool = False,
        total_pnl: float = 0.0,
    ) -> Dict[str, Any]:
        """Build standardized response from computed stats."""

        # Performance metrics: HL uses total_pnl-based math (deposit-immune)
        if use_pnl_based_metrics and initial_balance > 0:
            equity_change_pct = total_pnl / initial_balance * 100
            # Drawdown from peak pnl
            peak_pnl = peak_equity - initial_balance
            drawdown_pct = ((total_pnl - peak_pnl) / initial_balance * 100) if peak_pnl > total_pnl else 0.0
        else:
            equity_change_pct = ((account_equity - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0.0
            drawdown_pct = ((account_equity - peak_equity) / peak_equity * 100) if peak_equity > 0 else 0.0

        win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0.0

        # Build recent trades list
        now = datetime.now(timezone.utc)
        recent_trades = []
        for row in recent_rows:
            side, symbol, pnl, size_usd, close_reason, closed_at = row
            pnl_pct = (float(pnl) / float(size_usd) * 100) if size_usd and float(size_usd) > 0 else 0.0

            hours_ago = 0.0
            if closed_at:
                if closed_at.tzinfo is None:
                    closed_at = closed_at.replace(tzinfo=timezone.utc)
                hours_ago = (now - closed_at).total_seconds() / 3600

            recent_trades.append({
                'side': side,
                'symbol': symbol,
                'pnl_pct': round(pnl_pct, 1),
                'close_reason': close_reason,
                'closed_ago_hours': round(hours_ago, 1)
            })

        # Consecutive streak from most recent trades
        consecutive_wins, consecutive_losses = self._compute_streak(recent_trades)

        # Hours since last trade
        hours_since_last_trade = recent_trades[0]['closed_ago_hours'] if recent_trades else None

        # Drawdown duration
        drawdown_duration_hours = None
        if peak_timestamp and drawdown_pct < -0.1:
            if peak_timestamp.tzinfo is None:
                peak_timestamp = peak_timestamp.replace(tzinfo=timezone.utc)
            drawdown_duration_hours = round((now - peak_timestamp).total_seconds() / 3600, 1)

        # Interpretation summary
        if total_trades == 0:
            interpretation = "No trades yet."
        else:
            recent_5 = recent_trades[:5]
            recent_wins = sum(1 for t in recent_5 if t['pnl_pct'] > 0)
            recent_losses = len(recent_5) - recent_wins

            parts = []
            if drawdown_pct < -1:
                parts.append(f"Account down {abs(drawdown_pct):.1f}% from peak.")
                if drawdown_duration_hours and drawdown_duration_hours > 1:
                    parts.append(f"In drawdown for {drawdown_duration_hours:.0f}h.")
            elif equity_change_pct > 1:
                parts.append(f"Account up {equity_change_pct:.1f}% from start.")
            else:
                parts.append("Account near starting balance.")

            if consecutive_wins >= 3:
                parts.append(f"On a {consecutive_wins}-trade winning streak.")
            elif consecutive_losses >= 3:
                parts.append(f"On a {consecutive_losses}-trade losing streak.")
            elif recent_5:
                parts.append(f"Recent: {recent_wins}W {recent_losses}L in last {len(recent_5)} trades.")

            parts.append(f"Win rate {win_rate:.1f}%.")
            interpretation = " ".join(parts)

        return {
            'account_equity': round(account_equity, 2),
            'initial_balance': round(initial_balance, 2),
            'equity_change_pct': round(equity_change_pct, 1),
            'peak_equity': round(peak_equity, 2),
            'drawdown_from_peak_pct': round(drawdown_pct, 1),
            'drawdown_duration_hours': drawdown_duration_hours,
            'total_trades': total_trades,
            'win_trades': win_trades,
            'loss_trades': loss_trades,
            'win_rate_pct': round(win_rate, 1),
            'avg_win_pct': avg_win_pct,
            'avg_loss_pct': avg_loss_pct,
            'largest_win_pct': largest_win_pct,
            'largest_loss_pct': largest_loss_pct,
            'consecutive_wins': consecutive_wins,
            'consecutive_losses': consecutive_losses,
            'hours_since_last_trade': hours_since_last_trade,
            'recent_trades': recent_trades,
            'interpretation': interpretation,
        }

    @staticmethod
    def _compute_streak(recent_trades: List[Dict]) -> tuple:
        """Compute consecutive win/loss streak from most recent trades."""
        consecutive_wins = 0
        consecutive_losses = 0

        if not recent_trades:
            return 0, 0

        # Count from most recent
        for t in recent_trades:
            if t['pnl_pct'] > 0:
                if consecutive_losses > 0:
                    break  # streak broken
                consecutive_wins += 1
            elif t['pnl_pct'] < 0:
                if consecutive_wins > 0:
                    break
                consecutive_losses += 1
            # pnl_pct == 0: skip (breakeven doesn't break streak)

        return consecutive_wins, consecutive_losses

    def _empty_performance(self) -> Dict[str, Any]:
        """Return empty performance data when no account exists."""
        return {
            'account_equity': 0.0,
            'initial_balance': 0.0,
            'equity_change_pct': 0.0,
            'peak_equity': 0.0,
            'drawdown_from_peak_pct': 0.0,
            'drawdown_duration_hours': None,
            'total_trades': 0,
            'win_trades': 0,
            'loss_trades': 0,
            'win_rate_pct': 0.0,
            'avg_win_pct': 0.0,
            'avg_loss_pct': 0.0,
            'largest_win_pct': 0.0,
            'largest_loss_pct': 0.0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'hours_since_last_trade': None,
            'recent_trades': [],
            'interpretation': 'No trading history available.',
        }
