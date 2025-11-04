"""
Aster TP/SL Order Monitoring Service

Background service that monitors open Aster trades for TP/SL order fills.
When an order triggers, marks trade as closed and logs activity to timeline.

Runs as PM2 service: pm2 start scripts/monitor_aster_orders.py --name monitor-aster-orders

Architecture:
- Polls every 30 seconds (similar to paper trading monitoring)
- Queries all open Aster trades with TP/SL orders
- Checks order status via Aster API
- On fill: marks closed, logs activity, calculates P&L

Safety:
- Non-blocking async operations
- Graceful error handling (logs but continues)
- Activity logging failures don't crash monitor
"""

import os
import asyncio
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.common.db import get_db_connection
from core.common.activity_logger import log_activity_safe
from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService


class AsterOrderMonitor:
    """Monitors open Aster trades for TP/SL order fills"""

    def __init__(self):
        self.aster_service = AsterDEXV3LiveTradingService()
        self.check_interval = 30  # seconds
        logger.info("Aster Order Monitor initialized")

    async def get_open_trades_with_orders(self) -> List[Dict[str, Any]]:
        """
        Query all open Aster trades that have TP or SL orders.

        Returns:
            List of trade records with config_id, batch_id, sl_order_id, tp_order_id, symbol
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            batch_id,
                            config_id,
                            user_id,
                            stop_loss_order_id,
                            take_profit_order_id,
                            symbol,
                            created_at
                        FROM live_trades
                        WHERE provider = 'aster'
                        AND closed_at IS NULL
                        AND (stop_loss_order_id IS NOT NULL OR take_profit_order_id IS NOT NULL)
                        ORDER BY created_at DESC
                    """)
                    rows = cur.fetchall()

                    trades = []
                    for row in rows:
                        trades.append({
                            'batch_id': row[0],
                            'config_id': row[1],
                            'user_id': row[2],
                            'sl_order_id': row[3],
                            'tp_order_id': row[4],
                            'symbol': row[5],
                            'created_at': row[6]
                        })

                    return trades

        except Exception as e:
            logger.error(f"Failed to query open trades: {e}")
            return []

    async def check_order_status(self, symbol: str, order_id: str) -> Optional[str]:
        """
        Check if an order is filled via Aster API.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            order_id: Order ID to check

        Returns:
            Order status: "FILLED", "NEW", "CANCELED", or None on error
        """
        try:
            # Query order status from Aster
            order_info = await self.aster_service._get_order_status(symbol, order_id)
            if order_info:
                return order_info.get('status')
            return None

        except Exception as e:
            logger.warning(f"Failed to check order {order_id}: {e}")
            return None

    async def mark_trade_closed(self, batch_id: str, close_reason: str) -> bool:
        """
        Mark trade as closed in database.

        Args:
            batch_id: Trade batch ID
            close_reason: 'stop_loss' or 'take_profit'

        Returns:
            True on success
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE live_trades
                        SET closed_at = NOW(),
                            close_reason = %s
                        WHERE batch_id = %s
                        AND provider = 'aster'
                    """, (close_reason, batch_id))
                    conn.commit()
                    logger.info(f"Marked trade {batch_id} as closed ({close_reason})")
                    return True

        except Exception as e:
            logger.error(f"Failed to mark trade closed: {e}")
            return False

    async def log_closure_activity(
        self,
        batch_id: str,
        config_id: str,
        user_id: str,
        symbol: str,
        close_reason: str,
        pnl: float,
        pnl_pct: float
    ):
        """
        Log trade closure activity to timeline.

        Args:
            batch_id: Trade ID
            config_id: Bot config ID
            user_id: User ID
            symbol: Trading symbol
            close_reason: 'stop_loss' or 'take_profit'
            pnl: Realized P&L in USD
            pnl_pct: P&L percentage
        """
        try:
            # Determine activity type
            # Note: TP usually = win, SL usually = loss, but check actual P&L
            activity_type = 'trade_win' if pnl >= 0 else 'trade_loss'

            # Format close reason for display
            reason_display = {
                'stop_loss': 'Stop Loss',
                'take_profit': 'Take Profit'
            }.get(close_reason, close_reason.replace('_', ' ').title())

            log_activity_safe(
                config_id=config_id,
                user_id=user_id,
                activity_type=activity_type,
                activity_source='aster_monitor',
                summary=f"{reason_display} hit: {symbol} {'+' if pnl >= 0 else ''}{pnl:.2f} ({pnl_pct:.1f}%)",
                details={
                    'symbol': symbol,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'close_reason': close_reason,
                    'close_trigger': 'automatic',
                    'monitored': True
                },
                trade_id=batch_id,
                trade_type='aster',
                related_symbol=symbol,
                priority=1,
                importance=9
            )
            logger.info(f"Activity logged for {close_reason} on trade {batch_id}")

        except Exception as e:
            logger.warning(f"Failed to log closure activity (non-critical): {e}")

    async def get_trade_pnl(self, batch_id: str) -> tuple[float, float]:
        """
        Fetch trade P&L from Aster API.

        Returns:
            (pnl, pnl_pct) tuple
        """
        try:
            user_trades = await self.aster_service.get_user_trades(limit=100)
            matched_trade = next(
                (t for t in (user_trades or []) if str(t.get('id', '')) == batch_id),
                None
            )

            if matched_trade:
                pnl = float(matched_trade.get('realizedPnl', 0))
                qty = float(matched_trade.get('qty', 0))
                price = float(matched_trade.get('price', 0))

                # Calculate percentage
                pnl_pct = 0.0
                if qty > 0 and price > 0:
                    position_value = qty * price
                    pnl_pct = (pnl / position_value) * 100 if position_value > 0 else 0

                return (pnl, pnl_pct)

            return (0.0, 0.0)

        except Exception as e:
            logger.warning(f"Failed to fetch P&L for trade {batch_id}: {e}")
            return (0.0, 0.0)

    async def check_trade(self, trade: Dict[str, Any]):
        """
        Check a single trade for TP/SL order fills.

        Args:
            trade: Trade record with batch_id, sl_order_id, tp_order_id, etc.
        """
        batch_id = trade['batch_id']
        config_id = trade['config_id']
        user_id = trade['user_id']
        symbol = trade['symbol']
        sl_order_id = trade['sl_order_id']
        tp_order_id = trade['tp_order_id']

        try:
            # Convert symbol to Aster format (e.g., "BTC/USDT" -> "BTCUSDT")
            from core.symbols import SymbolStandardizer
            standardizer = SymbolStandardizer()
            aster_symbol = standardizer.to_aster(symbol) if standardizer.is_aster_compatible(symbol) else symbol.replace('/', '').replace('-', '')

            # Check SL order
            if sl_order_id:
                sl_status = await self.check_order_status(aster_symbol, sl_order_id)
                if sl_status == "FILLED":
                    logger.info(f"Stop Loss FILLED for trade {batch_id}")

                    # Mark closed
                    await self.mark_trade_closed(batch_id, 'stop_loss')

                    # Get P&L
                    pnl, pnl_pct = await self.get_trade_pnl(batch_id)

                    # Log activity
                    await self.log_closure_activity(
                        batch_id=batch_id,
                        config_id=config_id,
                        user_id=user_id,
                        symbol=symbol,
                        close_reason='stop_loss',
                        pnl=pnl,
                        pnl_pct=pnl_pct
                    )

                    return  # Stop checking this trade

            # Check TP order
            if tp_order_id:
                tp_status = await self.check_order_status(aster_symbol, tp_order_id)
                if tp_status == "FILLED":
                    logger.info(f"Take Profit FILLED for trade {batch_id}")

                    # Mark closed
                    await self.mark_trade_closed(batch_id, 'take_profit')

                    # Get P&L
                    pnl, pnl_pct = await self.get_trade_pnl(batch_id)

                    # Log activity
                    await self.log_closure_activity(
                        batch_id=batch_id,
                        config_id=config_id,
                        user_id=user_id,
                        symbol=symbol,
                        close_reason='take_profit',
                        pnl=pnl,
                        pnl_pct=pnl_pct
                    )

                    return  # Stop checking this trade

        except Exception as e:
            logger.error(f"Error checking trade {batch_id}: {e}")

    async def monitor_loop(self):
        """Main monitoring loop - runs indefinitely"""
        logger.info(f"Starting Aster order monitor (check interval: {self.check_interval}s)")

        while True:
            try:
                # Get all open trades with TP/SL orders
                open_trades = await self.get_open_trades_with_orders()

                if open_trades:
                    logger.info(f"Monitoring {len(open_trades)} open Aster trades")

                    # Check each trade
                    for trade in open_trades:
                        await self.check_trade(trade)
                        # Small delay between checks to avoid rate limits
                        await asyncio.sleep(0.5)
                else:
                    logger.debug("No open Aster trades with TP/SL orders")

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")

            # Wait before next check
            await asyncio.sleep(self.check_interval)

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Close Aster service connections if needed
            pass
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")


async def main():
    """Main entry point"""
    monitor = AsterOrderMonitor()

    try:
        await monitor.monitor_loop()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await monitor.cleanup()
        logger.info("Monitor stopped")


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:8}</level> | {message}",
        level="INFO"
    )
    logger.add(
        "logs/aster-monitor-{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO"
    )

    asyncio.run(main())
