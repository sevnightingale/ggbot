"""
Symphony Live Trading Account Adapter

Queries Symphony API to create account snapshots.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Set, Dict, List
from core.domain.account_snapshot import AccountAdapter, AccountSnapshot
from trading.live.symphony_service import SymphonyLiveTradingService
from core.common.db import get_db_connection
from core.common.logger import logger


class SymphonyAccountAdapter(AccountAdapter):
    """Adapter for fetching Symphony account state from API."""

    def __init__(self):
        self._log = logger.bind(adapter="symphony_account")
        self.symphony_service = SymphonyLiveTradingService()
        self._position_cache: Dict[str, Set[str]] = {}  # config_id -> set of batch_ids
        self._logged_closes: Set[str] = set()  # Track already logged closes

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
            # Symphony returns win_rate as 0-100 percentage, convert to 0-1 for database
            # Database column is NUMERIC(5,4) which can only hold 0-9.9999
            raw_win_rate = metrics.get('win_rate', 0)
            win_rate = Decimal(str(raw_win_rate)) / Decimal('100')

            # Get open positions
            open_positions_list = await self.symphony_service.get_open_positions(config_id)
            num_open_positions = len(open_positions_list) if open_positions_list else 0

            # Calculate position metrics from open positions
            # Now using collateralAmount for accurate margin tracking
            position_value = Decimal('0')  # Total notional position size
            unrealized_pnl = Decimal('0')
            margin_used = Decimal('0')  # Total collateral deployed

            if open_positions_list:
                for pos in open_positions_list:
                    pos_value = Decimal(str(pos.get('size_usd', 0)))
                    pos_pnl = Decimal(str(pos.get('unrealized_pnl', 0)))
                    pos_collateral = Decimal(str(pos.get('collateral', 0)))
                    position_value += pos_value
                    unrealized_pnl += pos_pnl
                    margin_used += pos_collateral

            # Calculate realized P&L (total - unrealized)
            realized_pnl = total_pnl - unrealized_pnl

            # Note: Symphony doesn't provide account balance yet
            # But we now have margin_used from collateralAmount

            # Create snapshot
            snapshot = AccountSnapshot(
                snapshot_id=None,
                config_id=config_id,
                user_id=user_id,
                trading_mode='symphony',
                timestamp=datetime.now(timezone.utc),
                current_balance=None,  # Not available from Symphony API yet
                available_balance=None,
                margin_used=margin_used if margin_used > 0 else None,  # From collateralAmount
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
                    'balance_available': False,  # Flag for when balance API is added
                    'margin_available': True,  # We now have collateralAmount from /agent/positions
                    'total_collateral': float(margin_used) if margin_used else 0
                }
            )

            # Detect and log any closed positions (pass already-fetched positions to avoid duplicate API call)
            await self._detect_and_log_closes(config_id, user_id, open_positions_list)

            return snapshot

        except Exception as e:
            self._log.error(f"Failed to get Symphony account snapshot for {config_id}: {e}")
            return None

    async def _detect_and_log_closes(self, config_id: str, user_id: str, open_positions: Optional[List] = None):
        """
        Detect closed Symphony positions and log trade_exit activities.

        Compares current open positions to cached positions to find closes.

        Args:
            config_id: Bot configuration ID
            user_id: User ID
            open_positions: Pre-fetched open positions (avoids duplicate API call)
        """
        from core.common.activity_logger import log_activity_safe
        from core.symbols import UniversalSymbolStandardizer

        try:
            # Use pre-fetched positions if available, otherwise fetch (fallback)
            if open_positions is None:
                open_positions = await self.symphony_service.get_open_positions(config_id)
            current_open = {pos.get('batch_id') for pos in open_positions if pos.get('batch_id')}

            # Get last seen open positions
            last_open = self._position_cache.get(config_id, set())

            # Find closed positions (in last but not in current)
            closed_batches = last_open - current_open

            # Get API key for querying closed batch details
            if closed_batches:
                from core.auth.vault_utils import VaultManager
                credentials = await VaultManager.get_symphony_credential(user_id)
                if not credentials:
                    self._log.warning(f"No Symphony credentials for user {user_id}, cannot log closes")
                    return

                api_key = credentials['api_key']

            # Log each close
            for batch_id in closed_batches:
                if batch_id in self._logged_closes:
                    continue  # Already logged

                try:
                    # Query Symphony for closed batch details
                    batch_data = await self.symphony_service._get_batch_positions(api_key, batch_id)
                    positions = batch_data.get('positions', [])

                    if positions:
                        # Get first position from batch
                        pos = positions[0]

                        # Extract position details
                        standardizer = UniversalSymbolStandardizer()
                        symbol = standardizer.from_symphony(pos.get('asset', ''))
                        entry_price = pos.get('entryPrice', 0)
                        exit_price = pos.get('currentPrice', 0)
                        pnl = pos.get('pnlUSD', 0)
                        size_usd = pos.get('positionSize', 0)
                        leverage = pos.get('leverage', 1)
                        side = 'long' if pos.get('isLong') else 'short'

                        # Calculate P&L percentage and duration
                        pnl_pct = (pnl / size_usd * 100) if size_usd > 0 else 0

                        # Parse timestamps if available
                        duration_seconds = None
                        if pos.get('createdTimestamp') and pos.get('lastUpdatedTimestamp'):
                            try:
                                created = datetime.fromisoformat(pos['createdTimestamp'].replace('Z', '+00:00'))
                                closed = datetime.fromisoformat(pos['lastUpdatedTimestamp'].replace('Z', '+00:00'))
                                duration_seconds = (closed - created).total_seconds()
                            except Exception:
                                pass

                        # Log exit activity
                        log_activity_safe(
                            config_id=config_id,
                            user_id=user_id,
                            activity_type='trade_exit',
                            activity_source='symphony_monitor',
                            summary=f"Auto-closed {symbol}: {'+' if pnl > 0 else ''}{pnl:.2f} ({pnl_pct:.1f}%)",
                            details={
                                'symbol': symbol,
                                'side': side,
                                'entry_price': float(entry_price),
                                'exit_price': float(exit_price),
                                'pnl': float(pnl),
                                'pnl_pct': pnl_pct,
                                'close_reason': 'auto',  # Symphony doesn't provide specific reason
                                'duration_seconds': duration_seconds,
                                'size_usd': float(size_usd),
                                'leverage': float(leverage),
                                'source': 'position_monitor',
                                'close_time': pos.get('lastUpdatedTimestamp')  # Store accurate timestamp
                            },
                            trade_id=batch_id,
                            trade_type='symphony',
                            related_symbol=symbol,
                            importance=9
                        )

                        self._logged_closes.add(batch_id)
                        self._log.info(f"Logged auto-close for Symphony batch {batch_id}")

                except Exception as e:
                    self._log.error(f"Failed to log Symphony close for batch {batch_id}: {e}")

            # Update cache
            self._position_cache[config_id] = current_open

        except Exception as e:
            # Transient errors (API timeouts, SSL issues) are expected and will retry in 5s
            self._log.warning(f"Failed to detect Symphony closes for {config_id}: {e}")

    async def supports_balance(self) -> bool:
        """
        Symphony does not currently provide balance data.

        TODO: Update to return True once Symphony adds balance endpoint.
        """
        return False
