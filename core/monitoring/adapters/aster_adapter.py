"""
AsterDEX Account Adapter

Queries AsterDEX API to create account snapshots.
Uses /fapi/v3/account and /fapi/v3/income endpoints.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Set, Dict
from core.domain.account_snapshot import AccountAdapter, AccountSnapshot
from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService
from core.common.db import get_db_connection
from core.common.logger import logger


class AsterAccountAdapter(AccountAdapter):
    """Adapter for fetching AsterDEX account state from API."""

    def __init__(self):
        self._log = logger.bind(adapter="aster_account")
        self.aster_service = AsterDEXV3LiveTradingService()
        self._last_income_check: Dict[str, datetime] = {}  # config_id -> last check timestamp
        self._logged_closes: Set[str] = set()  # Track already logged tranIds

    async def get_current_snapshot(self, config_id: str) -> Optional[AccountSnapshot]:
        """
        Get current AsterDEX account state from API.

        Uses:
        - /fapi/v3/account for balance, unrealized P&L, and positions
        - /fapi/v3/income for realized P&L and trade statistics
        """
        try:
            # Get user_id from config
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM configurations WHERE config_id = %s", (config_id,))
                    result = cur.fetchone()
                    if not result:
                        self._log.warning(f"Config {config_id} not found")
                        return None
                    user_id = str(result[0])

            # Get account data from /fapi/v3/account
            account_data = await self.aster_service._get_account_balance()
            if not account_data:
                self._log.error(f"Failed to get account data for config {config_id}")
                return None

            # Extract account-level data
            total_wallet_balance = Decimal(str(account_data.get('totalWalletBalance', 0)))
            total_unrealized_pnl = Decimal(str(account_data.get('totalUnrealizedProfit', 0)))
            available_balance = Decimal(str(account_data.get('availableBalance', 0)))
            total_margin_balance = Decimal(str(account_data.get('totalMarginBalance', 0)))
            total_initial_margin = Decimal(str(account_data.get('totalInitialMargin', 0)))

            # Get positions from account data
            positions = account_data.get('positions', [])
            open_positions = []
            position_value = Decimal('0')

            for pos in positions:
                pos_amt = Decimal(str(pos.get('positionAmt', 0)))
                if pos_amt != 0:  # Only count non-zero positions
                    open_positions.append(pos)
                    # notional = positionAmt * markPrice
                    mark_price = Decimal(str(pos.get('markPrice', 0)))
                    position_value += abs(pos_amt * mark_price)

            num_open_positions = len(open_positions)

            # Use totalWalletBalance directly as realized P&L
            # (Aster API only returns limited income history, not full trade log)
            realized_pnl = total_wallet_balance

            # Calculate total P&L (realized + unrealized)
            total_pnl = total_wallet_balance + total_unrealized_pnl

            # Get recent income history for basic trade stats (limited to what API returns)
            income_records = await self.aster_service.get_income_history(
                income_type='REALIZED_PNL',  # Only realized P&L
                start_time=None,   # All available
                limit=1000
            )

            # Calculate trade statistics from available records
            # NOTE: These are incomplete - API only returns recent trades
            trade_pnls = []
            if income_records:
                for record in income_records:
                    income_amount = Decimal(str(record.get('income', 0)))
                    if income_amount != 0:
                        trade_pnls.append(income_amount)

            total_trades = len(trade_pnls) if trade_pnls else 0
            wins = [pnl for pnl in trade_pnls if pnl > 0]
            losses = [pnl for pnl in trade_pnls if pnl < 0]

            win_trades = len(wins)
            loss_trades = len(losses)
            win_rate = Decimal(win_trades) / Decimal(total_trades) if total_trades > 0 else Decimal('0')

            avg_win = sum(wins) / len(wins) if wins else None
            avg_loss = sum(losses) / len(losses) if losses else None
            largest_win = max(wins) if wins else None
            largest_loss = min(losses) if losses else None

            # Create snapshot
            snapshot = AccountSnapshot(
                snapshot_id=None,
                config_id=config_id,
                user_id=user_id,
                trading_mode='aster',
                timestamp=datetime.now(timezone.utc),
                current_balance=total_wallet_balance,
                available_balance=available_balance,
                margin_used=total_initial_margin,
                total_pnl=total_pnl,
                realized_pnl=realized_pnl,
                unrealized_pnl=total_unrealized_pnl,
                total_trades=total_trades,
                win_trades=win_trades,
                loss_trades=loss_trades,
                win_rate=win_rate,
                open_positions=num_open_positions,
                position_value=position_value,
                total_exposure=position_value,
                avg_win=avg_win,
                avg_loss=avg_loss,
                largest_win=largest_win,
                largest_loss=largest_loss,
                raw_data={
                    'account_data': {
                        'totalWalletBalance': str(total_wallet_balance),
                        'totalUnrealizedProfit': str(total_unrealized_pnl),
                        'totalMarginBalance': str(total_margin_balance),
                        'num_positions': len(positions),
                        'num_open_positions': num_open_positions
                    },
                    'income_records_count': len(income_records) if income_records else 0,
                    'source': 'aster_api'
                }
            )

            # Detect and log any closed positions
            await self._detect_and_log_closes(config_id, user_id)

            return snapshot

        except Exception as e:
            self._log.error(f"Failed to get Aster account snapshot for {config_id}: {e}")
            return None

    async def _detect_and_log_closes(self, config_id: str, user_id: str):
        """
        Detect closed Aster positions via income history.

        Queries /fapi/v3/income for REALIZED_PNL events since last check.
        """
        from core.common.activity_logger import log_activity_safe

        try:
            # Get last check time (default to 1 hour ago on first run)
            last_check = self._last_income_check.get(
                config_id,
                datetime.now(timezone.utc) - timedelta(hours=1)
            )

            # Query Aster income for REALIZED_PNL since last check
            start_time = int(last_check.timestamp() * 1000)  # Convert to ms
            income_records = await self.aster_service.get_income_history(
                income_type='REALIZED_PNL',
                start_time=start_time,
                limit=100
            )

            # Log each new realized P&L (= closed trade)
            for record in income_records or []:
                tran_id = str(record.get('tranId'))
                if tran_id in self._logged_closes:
                    continue  # Already logged

                symbol = record.get('symbol', 'N/A')
                pnl = float(record.get('income', 0))
                close_time_ms = record.get('time')  # Accurate timestamp from Aster!
                trade_id = str(record.get('tradeId', tran_id))

                # Calculate P&L display
                pnl_display = f"{'+' if pnl > 0 else ''}{pnl:.2f}"

                # Log exit activity
                log_activity_safe(
                    config_id=config_id,
                    user_id=user_id,
                    activity_type='trade_exit',
                    activity_source='aster_monitor',
                    summary=f"Auto-closed {symbol}: {pnl_display}",
                    details={
                        'symbol': symbol,
                        'pnl': pnl,
                        'close_time_ms': close_time_ms,  # Store Aster timestamp
                        'tran_id': tran_id,
                        'trade_id': trade_id,
                        'source': 'position_monitor',
                        'close_reason': 'auto'
                    },
                    trade_id=trade_id,
                    trade_type='aster',
                    related_symbol=symbol,
                    importance=9
                )

                self._logged_closes.add(tran_id)
                self._log.info(f"Logged auto-close for Aster trade {trade_id} ({symbol})")

            # Update last check time
            self._last_income_check[config_id] = datetime.now(timezone.utc)

        except Exception as e:
            # Transient errors (API timeouts, connection issues) are expected and will retry in 5s
            self._log.warning(f"Failed to detect Aster closes for {config_id}: {e}")

    async def supports_balance(self) -> bool:
        """AsterDEX provides balance data."""
        return True
