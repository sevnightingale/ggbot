"""
Universal Account Monitor Service

Single monitoring service for ALL trading modes (paper, symphony, aster).
Monitors positions, tracks balances, and stores account snapshots.
"""

import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Optional, List
from core.common.db import get_db_connection
from core.common.logger import logger as base_logger
from core.domain.account_snapshot import AccountSnapshot
from core.monitoring.adapters import PaperAccountAdapter, SymphonyAccountAdapter, AsterAccountAdapter

# Create monitoring logger
logger = base_logger.bind(service="universal_account_monitor")


class UniversalAccountMonitor:
    """
    Universal monitoring service for all trading modes.

    Features:
    - Monitors paper, Symphony, and AsterDEX bots at same cadence (5s)
    - Stores snapshots only on meaningful change or heartbeat (5min)
    - Unified interface for all consumers
    - Efficient adapter pattern
    """

    def __init__(self):
        self.running = False
        self.cycle_count = 0
        self.last_snapshots: Dict[str, AccountSnapshot] = {}  # config_id -> last snapshot
        self.last_heartbeat: Dict[str, datetime] = {}  # config_id -> last heartbeat time

        # Create adapters
        self.adapters = {
            'paper': PaperAccountAdapter(),
            'symphony': SymphonyAccountAdapter(),
            'aster': AsterAccountAdapter()
        }

        # Configuration
        self.monitor_interval = 5  # Check every 5 seconds
        self.heartbeat_interval = 300  # Force snapshot every 5 minutes
        self.change_threshold = Decimal('0.001')  # Store if balance changes >0.1%

        logger.info("✨ UniversalAccountMonitor initialized")

    async def start(self):
        """Start the monitoring service."""
        logger.info("🚀 Starting Universal Account Monitor")
        self.running = True

        try:
            await self._monitor_loop()
        except Exception as e:
            logger.error(f"❌ Monitor loop failed: {e}")
            raise
        finally:
            logger.info("🛑 Monitor stopped")

    async def stop(self):
        """Stop the monitoring service."""
        logger.info("🛑 Stopping Universal Account Monitor...")
        self.running = False

    async def _monitor_loop(self):
        """
        Main monitoring loop.

        Checks all active bots every 5 seconds.
        Stores snapshots on meaningful change or 5-min heartbeat.
        """
        logger.info("📊 Monitor loop started (5s checks, 5min heartbeat)")

        while self.running:
            try:
                start_time = datetime.now(timezone.utc)

                # Get all active configurations
                active_configs = await self._get_active_configs()

                if active_configs:
                    # Process each config
                    for config in active_configs:
                        try:
                            await self._process_config(config)
                        except Exception as e:
                            logger.error(f"Failed to process config {config['config_id']}: {e}")

                    # Log stats occasionally
                    if self.cycle_count % 12 == 0:  # Every minute (12 * 5s)
                        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                        logger.info(
                            f"📊 Cycle {self.cycle_count}: {len(active_configs)} configs, "
                            f"{elapsed:.1f}s, {len(self.last_snapshots)} cached"
                        )

                self.cycle_count += 1

            except Exception as e:
                logger.error(f"❌ Monitor loop error: {e}")

            # Sleep with jitter to prevent thundering herd
            jitter = random.uniform(-0.3, 0.3)
            await asyncio.sleep(self.monitor_interval + jitter)

    async def _process_config(self, config: Dict):
        """
        Process a single configuration.

        Gets current snapshot, compares with last, and saves if changed or heartbeat.
        """
        config_id = config['config_id']
        trading_mode = config['trading_mode']

        # Get adapter for this trading mode
        adapter = self.adapters.get(trading_mode)
        if not adapter:
            logger.warning(f"No adapter for trading mode: {trading_mode}")
            return

        # Get current snapshot
        snapshot = await adapter.get_current_snapshot(config_id)
        if not snapshot:
            return

        # Check if we should save this snapshot
        should_save, is_heartbeat = self._should_save_snapshot(config_id, snapshot)

        if should_save:
            snapshot.is_heartbeat = is_heartbeat
            await self._save_snapshot(snapshot)

            # Update cache
            self.last_snapshots[config_id] = snapshot
            if is_heartbeat:
                self.last_heartbeat[config_id] = snapshot.timestamp

    def _should_save_snapshot(self, config_id: str, snapshot: AccountSnapshot) -> tuple[bool, bool]:
        """
        Determine if snapshot should be saved.

        Returns:
            (should_save, is_heartbeat)
        """
        # Always save first snapshot
        if config_id not in self.last_snapshots:
            return (True, False)

        last_snapshot = self.last_snapshots[config_id]

        # Check for heartbeat (5 min since last heartbeat)
        last_heartbeat_time = self.last_heartbeat.get(config_id, last_snapshot.timestamp)
        time_since_heartbeat = (snapshot.timestamp - last_heartbeat_time).total_seconds()

        if time_since_heartbeat >= self.heartbeat_interval:
            return (True, True)

        # Check for meaningful change
        if self._has_meaningful_change(last_snapshot, snapshot):
            return (True, False)

        # No change, don't save
        return (False, False)

    def _has_meaningful_change(self, last: AccountSnapshot, current: AccountSnapshot) -> bool:
        """
        Check if there's a meaningful change between snapshots.

        Changes that trigger save:
        - Balance changed >0.1%
        - Position opened/closed
        - P&L changed significantly
        """
        # Position count changed
        if last.open_positions != current.open_positions:
            return True

        # Total P&L changed (any change in realized P&L indicates trade close)
        if abs(current.total_pnl - last.total_pnl) > Decimal('0.01'):  # $0.01 threshold
            return True

        # Balance changed significantly (if available)
        if current.current_balance and last.current_balance:
            balance_change_pct = abs(
                (current.current_balance - last.current_balance) / last.current_balance
            )
            if balance_change_pct >= self.change_threshold:
                current.balance_change_pct = balance_change_pct * Decimal('100')
                return True

        # No meaningful change
        return False

    async def _save_snapshot(self, snapshot: AccountSnapshot):
        """Save snapshot to database."""
        try:
            import json

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    snapshot_id = str(uuid.uuid4())
                    snapshot.snapshot_id = snapshot_id

                    cur.execute("""
                        INSERT INTO account_snapshots (
                            snapshot_id, config_id, user_id, trading_mode, timestamp,
                            current_balance, available_balance, margin_used,
                            total_pnl, realized_pnl, unrealized_pnl,
                            total_trades, win_trades, loss_trades, win_rate,
                            open_positions, position_value, total_exposure,
                            avg_win, avg_loss, largest_win, largest_loss,
                            sharpe_ratio, max_drawdown,
                            raw_data, balance_change_pct, is_heartbeat
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s,
                            %s, %s, %s
                        )
                    """, (
                        snapshot_id, snapshot.config_id, snapshot.user_id,
                        snapshot.trading_mode, snapshot.timestamp,
                        snapshot.current_balance, snapshot.available_balance, snapshot.margin_used,
                        snapshot.total_pnl, snapshot.realized_pnl, snapshot.unrealized_pnl,
                        snapshot.total_trades, snapshot.win_trades, snapshot.loss_trades, snapshot.win_rate,
                        snapshot.open_positions, snapshot.position_value, snapshot.total_exposure,
                        snapshot.avg_win, snapshot.avg_loss, snapshot.largest_win, snapshot.largest_loss,
                        snapshot.sharpe_ratio, snapshot.max_drawdown,
                        json.dumps(snapshot.raw_data) if snapshot.raw_data else None,  # JSON encode dict
                        snapshot.balance_change_pct, snapshot.is_heartbeat
                    ))

                conn.commit()

                log_msg = f"💾 Saved snapshot for {snapshot.config_id} ({snapshot.trading_mode})"
                if snapshot.is_heartbeat:
                    log_msg += " [HEARTBEAT]"
                elif snapshot.balance_change_pct:
                    log_msg += f" [CHANGE: {snapshot.balance_change_pct:.2f}%]"
                logger.debug(log_msg)

        except Exception as e:
            logger.error(f"Failed to save snapshot for {snapshot.config_id}: {e}")

    async def _get_active_configs(self) -> List[Dict]:
        """Get all active bot configurations (state='active')."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id, user_id, trading_mode, config_name
                        FROM configurations
                        WHERE state = 'active'
                        ORDER BY config_id
                    """)

                    results = cur.fetchall()
                    return [
                        {
                            'config_id': row[0],
                            'user_id': row[1],
                            'trading_mode': row[2],
                            'config_name': row[3]
                        }
                        for row in results
                    ]

        except Exception as e:
            logger.error(f"Failed to get active configs: {e}")
            return []


async def main():
    """Main entry point for the monitoring service."""
    monitor = UniversalAccountMonitor()

    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("⌨️  Keyboard interrupt received")
        await monitor.stop()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        await monitor.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())
