"""
Symphony Live Trading Account Adapter

Queries Symphony API to create account snapshots.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from core.domain.account_snapshot import AccountAdapter, AccountSnapshot
from trading.live.symphony_service import SymphonyLiveTradingService
from core.common.db import get_db_connection
from core.common.logger import logger


class SymphonyAccountAdapter(AccountAdapter):
    """Adapter for fetching Symphony account state from API."""

    def __init__(self):
        self._log = logger.bind(adapter="symphony_account")
        self.symphony_service = SymphonyLiveTradingService()

    async def get_current_snapshot(self, config_id: str) -> Optional[AccountSnapshot]:
        """
        Get current Symphony account state from API.

        Note: Symphony currently does not provide balance data.
        Once their API adds balance support, we'll update this adapter.
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

            # Get account metrics from Symphony
            metrics = await self.symphony_service.get_account_metrics(config_id)

            if not metrics:
                self._log.warning(f"No Symphony metrics for config {config_id}")
                return None

            # Extract metrics
            total_pnl = Decimal(str(metrics.get('total_pnl', 0)))
            total_trades = int(metrics.get('total_trades', 0))
            win_trades = int(metrics.get('win_trades', 0))
            loss_trades = int(metrics.get('loss_trades', 0))
            win_rate = Decimal(str(metrics.get('win_rate', 0)))

            # Get open positions
            open_positions_list = await self.symphony_service.get_open_positions(config_id)
            num_open_positions = len(open_positions_list) if open_positions_list else 0

            # Calculate position metrics from open positions
            position_value = Decimal('0')
            unrealized_pnl = Decimal('0')

            if open_positions_list:
                for pos in open_positions_list:
                    pos_value = Decimal(str(pos.get('size_usd', 0)))
                    pos_pnl = Decimal(str(pos.get('unrealized_pnl', 0)))
                    position_value += pos_value
                    unrealized_pnl += pos_pnl

            # Calculate realized P&L (total - unrealized)
            realized_pnl = total_pnl - unrealized_pnl

            # Note: Symphony doesn't provide balance, margin, or advanced stats yet
            # We'll fill these in when their API supports it

            # Create snapshot
            snapshot = AccountSnapshot(
                snapshot_id=None,
                config_id=config_id,
                user_id=user_id,
                trading_mode='symphony',
                timestamp=datetime.now(timezone.utc),
                current_balance=None,  # Not available from Symphony API yet
                available_balance=None,
                margin_used=None,
                total_pnl=total_pnl,
                realized_pnl=realized_pnl,
                unrealized_pnl=unrealized_pnl,
                total_trades=total_trades,
                win_trades=win_trades,
                loss_trades=loss_trades,
                win_rate=win_rate,
                open_positions=num_open_positions,
                position_value=position_value,
                total_exposure=position_value,
                avg_win=None,  # Not available yet
                avg_loss=None,
                largest_win=None,
                largest_loss=None,
                raw_data={
                    'metrics': metrics,
                    'source': 'symphony_api',
                    'balance_available': False  # Flag for when balance API is added
                }
            )

            return snapshot

        except Exception as e:
            self._log.error(f"Failed to get Symphony account snapshot for {config_id}: {e}")
            return None

    async def supports_balance(self) -> bool:
        """
        Symphony does not currently provide balance data.

        TODO: Update to return True once Symphony adds balance endpoint.
        """
        return False
