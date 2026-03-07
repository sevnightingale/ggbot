"""
Account Performance Adapter

Fetches bot trading history and performance metrics from internal database.
Provides the LLM with awareness of recent wins, losses, and account health
so user strategies can reference performance state.
"""

from datetime import datetime, timezone
from typing import Dict, Any

from core.common.db import get_db_connection
from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse, AdapterError


class AccountPerformanceAdapter(DataAdapter):
    """
    Adapter for bot account performance data.

    Queries internal database (paper_accounts/live_trades + account_snapshots)
    to surface trading history as market intelligence data.
    """

    name = "account_performance"
    data_type = "account_performance"

    RECENT_TRADES_LIMIT = 10

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Fetch account performance for a bot configuration.

        Args:
            params: Must contain 'config_id'. Optional 'trading_mode' (default: 'paper').

        Returns:
            AdapterResponse with account performance data
        """
        config_id = params.get('config_id')
        if not config_id:
            raise AdapterError("config_id parameter is required")

        trading_mode = params.get('trading_mode', 'paper')

        try:
            if trading_mode == 'hyperliquid':
                data = self._fetch_live_performance(config_id)
            else:
                data = self._fetch_paper_performance(config_id)

            data['fetched_at'] = datetime.now(timezone.utc).isoformat()

            self._log.debug(
                f"Fetched account performance for config {config_id[:8]}: "
                f"{data['total_trades']} trades, {data['win_rate_pct']:.1f}% win rate"
            )

            return AdapterResponse(
                data=data,
                metadata=self.build_metadata(
                    source='internal_db',
                    config_id=config_id,
                    trading_mode=trading_mode
                ),
                confidence=1.0,
                related_queries=[]
            )

        except AdapterError:
            raise
        except Exception as e:
            self._log.error(f"Error fetching account performance for {config_id[:8]}: {e}")
            raise AdapterError(f"Failed to fetch account performance: {e}")

    def _fetch_paper_performance(self, config_id: str) -> Dict[str, Any]:
        """Fetch performance from paper trading tables."""
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

                # Ensure peak is at least initial balance
                peak_equity = max(peak_equity, initial_balance)

                # Average win/loss from closed trades
                cur.execute("""
                    SELECT
                        AVG(CASE WHEN realized_pnl > 0 THEN realized_pnl / size_usd * 100 END) as avg_win_pct,
                        AVG(CASE WHEN realized_pnl < 0 THEN realized_pnl / size_usd * 100 END) as avg_loss_pct
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'closed' AND size_usd > 0
                """, (config_id,))
                avg_row = cur.fetchone()
                avg_win_pct = round(float(avg_row[0]), 1) if avg_row and avg_row[0] else 0.0
                avg_loss_pct = round(float(avg_row[1]), 1) if avg_row and avg_row[1] else 0.0

                # Recent closed trades
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
            recent_rows=recent_rows
        )

    def _fetch_live_performance(self, config_id: str) -> Dict[str, Any]:
        """Fetch performance from Hyperliquid live trading tables."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Aggregate from live_trades
                cur.execute("""
                    SELECT
                        COUNT(*) as total_trades,
                        COUNT(*) FILTER (WHERE realized_pnl > 0) as win_trades,
                        COUNT(*) FILTER (WHERE realized_pnl < 0) as loss_trades,
                        SUM(realized_pnl) as total_pnl,
                        AVG(CASE WHEN realized_pnl > 0 THEN realized_pnl / NULLIF(size_usd, 0) * 100 END) as avg_win_pct,
                        AVG(CASE WHEN realized_pnl < 0 THEN realized_pnl / NULLIF(size_usd, 0) * 100 END) as avg_loss_pct
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

                # Get current equity from latest snapshot
                cur.execute("""
                    SELECT current_balance, unrealized_pnl
                    FROM account_snapshots
                    WHERE config_id = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (config_id,))
                snap = cur.fetchone()
                if snap:
                    current_equity = float(snap[0] or 0) + float(snap[1] or 0)
                else:
                    current_equity = 0.0

                # Peak equity from snapshots
                cur.execute("""
                    SELECT MAX(current_balance + COALESCE(unrealized_pnl, 0))
                    FROM account_snapshots
                    WHERE config_id = %s
                """, (config_id,))
                peak_row = cur.fetchone()
                peak_equity = float(peak_row[0]) if peak_row and peak_row[0] else current_equity

                # Initial balance: use earliest snapshot balance or derive from pnl
                cur.execute("""
                    SELECT current_balance
                    FROM account_snapshots
                    WHERE config_id = %s
                    ORDER BY timestamp ASC
                    LIMIT 1
                """, (config_id,))
                first_snap = cur.fetchone()
                initial_balance = float(first_snap[0]) if first_snap and first_snap[0] else current_equity

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
            initial_balance=initial_balance,
            peak_equity=peak_equity,
            total_trades=total_trades,
            win_trades=win_trades,
            loss_trades=loss_trades,
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            recent_rows=recent_rows
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
        recent_rows: list
    ) -> Dict[str, Any]:
        """Build standardized response from computed stats."""
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
                # Handle naive timestamps by assuming UTC
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

        # Build interpretation summary
        if total_trades == 0:
            interpretation = "No trades yet."
        else:
            # Recent streak
            recent_5 = recent_trades[:5]
            recent_wins = sum(1 for t in recent_5 if t['pnl_pct'] > 0)
            recent_losses = len(recent_5) - recent_wins

            parts = []
            if drawdown_pct < -1:
                parts.append(f"Account down {abs(drawdown_pct):.1f}% from peak.")
            elif equity_change_pct > 1:
                parts.append(f"Account up {equity_change_pct:.1f}% from start.")
            else:
                parts.append("Account near starting balance.")

            if recent_5:
                parts.append(f"Recent performance: {recent_wins}W {recent_losses}L in last {len(recent_5)} trades.")
            parts.append(f"Win rate {win_rate:.1f}%.")
            interpretation = " ".join(parts)

        return {
            'account_equity': round(account_equity, 2),
            'initial_balance': round(initial_balance, 2),
            'equity_change_pct': round(equity_change_pct, 1),
            'peak_equity': round(peak_equity, 2),
            'drawdown_from_peak_pct': round(drawdown_pct, 1),
            'total_trades': total_trades,
            'win_trades': win_trades,
            'loss_trades': loss_trades,
            'win_rate_pct': round(win_rate, 1),
            'avg_win_pct': avg_win_pct,
            'avg_loss_pct': avg_loss_pct,
            'recent_trades': recent_trades,
            'interpretation': interpretation,
        }

    def _empty_performance(self) -> Dict[str, Any]:
        """Return empty performance data when no account exists."""
        return {
            'account_equity': 0.0,
            'initial_balance': 0.0,
            'equity_change_pct': 0.0,
            'peak_equity': 0.0,
            'drawdown_from_peak_pct': 0.0,
            'total_trades': 0,
            'win_trades': 0,
            'loss_trades': 0,
            'win_rate_pct': 0.0,
            'avg_win_pct': 0.0,
            'avg_loss_pct': 0.0,
            'recent_trades': [],
            'interpretation': 'No trading history available.',
        }
