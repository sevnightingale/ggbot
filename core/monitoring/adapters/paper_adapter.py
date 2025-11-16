"""
Paper Trading Account Adapter

Queries paper_accounts and paper_trades tables to create account snapshots.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Set, Dict
from core.domain.account_snapshot import AccountAdapter, AccountSnapshot
from core.common.db import get_db_connection
from core.common.logger import logger


class PaperAccountAdapter(AccountAdapter):
    """Adapter for fetching paper trading account state from database."""

    def __init__(self):
        self._log = logger.bind(adapter="paper_account")
        self._position_cache: Dict[str, Set[str]] = {}  # config_id -> set of trade_ids
        self._logged_closes: Set[str] = set()  # Track already logged closes

    async def get_current_snapshot(self, config_id: str) -> Optional[AccountSnapshot]:
        """
        Get current paper trading account state from database.

        Queries paper_accounts for balance/metrics and calculates live P&L from open positions.
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get account data
                    cur.execute("""
                        SELECT
                            pa.account_id,
                            pa.user_id,
                            pa.current_balance,
                            pa.total_pnl,
                            pa.open_positions,
                            pa.total_trades,
                            pa.win_trades,
                            pa.loss_trades,
                            c.trading_mode
                        FROM paper_accounts pa
                        JOIN configurations c ON pa.config_id = c.config_id
                        WHERE pa.config_id = %s
                    """, (config_id,))

                    account = cur.fetchone()
                    if not account:
                        self._log.warning(f"No paper account found for config {config_id}")
                        return None

                    (account_id, user_id, current_balance, total_pnl,
                     open_positions, total_trades, win_trades, loss_trades, trading_mode) = account

                    # Calculate win rate
                    win_rate = Decimal(win_trades) / Decimal(total_trades) if total_trades > 0 else Decimal('0')

                    # Get unrealized P&L from open positions
                    cur.execute("""
                        SELECT
                            COALESCE(SUM(unrealized_pnl), 0) as unrealized_pnl,
                            COALESCE(SUM(size_usd), 0) as position_value,
                            COALESCE(SUM(margin_used), 0) as margin_used
                        FROM paper_trades
                        WHERE config_id = %s AND status = 'open'
                    """, (config_id,))

                    position_data = cur.fetchone()
                    unrealized_pnl, position_value, margin_used = position_data or (Decimal('0'), Decimal('0'), Decimal('0'))

                    # Calculate realized P&L (total_pnl - unrealized_pnl)
                    realized_pnl = Decimal(total_pnl) - unrealized_pnl

                    # Calculate available balance (current_balance - margin_used)
                    available_balance = Decimal(current_balance) - margin_used

                    # Get win/loss stats from closed trades
                    cur.execute("""
                        SELECT
                            AVG(CASE WHEN realized_pnl > 0 THEN realized_pnl END) as avg_win,
                            AVG(CASE WHEN realized_pnl < 0 THEN realized_pnl END) as avg_loss,
                            MAX(realized_pnl) as largest_win,
                            MIN(realized_pnl) as largest_loss
                        FROM paper_trades
                        WHERE config_id = %s AND status = 'closed'
                    """, (config_id,))

                    stats = cur.fetchone()
                    avg_win, avg_loss, largest_win, largest_loss = stats or (None, None, None, None)

                    # Create snapshot
                    snapshot = AccountSnapshot(
                        snapshot_id=None,  # Will be generated on save
                        config_id=config_id,
                        user_id=str(user_id),
                        trading_mode='paper',
                        timestamp=datetime.now(timezone.utc),
                        current_balance=Decimal(current_balance),
                        available_balance=available_balance,
                        margin_used=margin_used,
                        total_pnl=Decimal(total_pnl),
                        realized_pnl=realized_pnl,
                        unrealized_pnl=unrealized_pnl,
                        total_trades=total_trades,
                        win_trades=win_trades,
                        loss_trades=loss_trades,
                        win_rate=win_rate,
                        open_positions=open_positions,
                        position_value=position_value,
                        total_exposure=position_value,  # For paper, exposure = position value
                        avg_win=Decimal(avg_win) if avg_win else None,
                        avg_loss=Decimal(avg_loss) if avg_loss else None,
                        largest_win=Decimal(largest_win) if largest_win else None,
                        largest_loss=Decimal(largest_loss) if largest_loss else None,
                        raw_data={
                            'account_id': str(account_id),
                            'source': 'paper_accounts_table'
                        }
                    )

                    # Detect and log any closed positions
                    await self._detect_and_log_closes(config_id)

                    return snapshot

        except Exception as e:
            self._log.error(f"Failed to get paper account snapshot for {config_id}: {e}")
            return None

    async def _detect_and_log_closes(self, config_id: str):
        """
        Detect closed positions and log trade_exit activities.

        Compares current open positions to cached positions to find closes.
        """
        from core.common.activity_logger import log_activity_safe

        try:
            # Get currently open positions
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT trade_id FROM paper_trades
                        WHERE config_id = %s AND status = 'open'
                    """, (config_id,))
                    current_open = {str(row[0]) for row in cur.fetchall()}

            # Get last seen open positions
            last_open = self._position_cache.get(config_id, set())

            # Find closed positions (in last but not in current)
            closed_trades = last_open - current_open

            # Log exit for each closed trade
            for trade_id in closed_trades:
                if trade_id in self._logged_closes:
                    continue  # Already logged

                # Query for close details
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT symbol, side, entry_price, current_price,
                                   realized_pnl, size_usd, close_reason,
                                   opened_at, closed_at, user_id, config_id
                            FROM paper_trades
                            WHERE trade_id = %s
                        """, (trade_id,))

                        row = cur.fetchone()
                        if not row:
                            continue

                        symbol, side, entry_price, exit_price, pnl, size_usd, \
                        close_reason, opened_at, closed_at, user_id, trade_config_id = row

                        # Calculate metrics
                        pnl_pct = (float(pnl) / float(size_usd) * 100) if size_usd else 0
                        duration = (closed_at - opened_at).total_seconds() if closed_at and opened_at else 0

                        # Log exit activity
                        log_activity_safe(
                            config_id=str(trade_config_id),
                            user_id=str(user_id),
                            activity_type='trade_exit',
                            activity_source='paper_monitor',
                            summary=f"Auto-closed {symbol}: {'+' if pnl > 0 else ''}{float(pnl):.2f} ({pnl_pct:.1f}%)",
                            details={
                                'symbol': symbol,
                                'side': side,
                                'entry_price': float(entry_price),
                                'exit_price': float(exit_price),
                                'pnl': float(pnl),
                                'pnl_pct': pnl_pct,
                                'close_reason': close_reason or 'unknown',
                                'duration_seconds': duration,
                                'source': 'position_monitor'
                            },
                            trade_id=trade_id,
                            trade_type='paper',
                            related_symbol=symbol,
                            importance=9
                        )

                        self._logged_closes.add(trade_id)
                        self._log.info(f"Logged auto-close for paper trade {trade_id} ({close_reason})")

            # Update cache
            self._position_cache[config_id] = current_open

        except Exception as e:
            # Transient errors (SSL, connection timeouts) are expected and will retry in 5s
            self._log.warning(f"Failed to detect closes for {config_id}: {e}")

    async def supports_balance(self) -> bool:
        """Paper trading always provides balance data."""
        return True
