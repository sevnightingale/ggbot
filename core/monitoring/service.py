"""
🔥 SIMPLIFIED Monitoring Service for ggbots Platform

Now focused ONLY on critical position monitoring for stop-loss/take-profit execution.
WebSocket spam DELETED! Dashboard data now via SSE stream.
"""

import asyncio
import random
import time
from datetime import datetime, timezone
from typing import List, Tuple

from core.common.logger import logger as base_logger
from core.common.db import get_db_connection
from trading.paper.supabase_service import SupabasePaperTradingService

# Create monitoring logger with service binding
logger = base_logger.bind(service="monitoring")


class MonitoringService:
    """
    🔥 SIMPLIFIED monitoring service - positions only!
    
    ONLY monitors:
    - Position prices and P&L (critical for stop-loss/take-profit execution)
    
    🔥 DELETED:
    - WebSocket broadcasts (now using SSE)
    - Bot metrics spam  
    - Scheduler status spam
    - All the fucking complexity!
    """
    
    def __init__(self):
        # 🔥 WebSocket manager DELETED!
        self.paper_trading = SupabasePaperTradingService()
        self.running = False
        self.cycle_count = 0
        
        logger.info("🔧 SIMPLIFIED MonitoringService initialized (positions only!)")
    
    async def start(self):
        """Start ONLY position monitoring (no more WebSocket spam!)."""
        logger.info("🚀 Starting SIMPLIFIED monitoring: positions only, no WebSocket spam!")
        self.running = True
        
        try:
            # 🔥 DELETED metrics_scheduler_monitor - that was WebSocket spam!
            await self._position_monitor()
        except Exception as e:
            logger.error(f"❌ Position monitoring failed: {e}")
            raise
        finally:
            logger.info("🛑 Position monitoring stopped")
    
    async def stop(self):
        """Gracefully stop monitoring service."""
        logger.info("🛑 Stopping simplified monitoring service...")
        self.running = False
    
    async def _position_monitor(self):
        """
        🔥 SIMPLIFIED position monitoring loop.
        
        Updates prices for ALL open positions every 3 seconds with jitter.
        This is essential for stop-loss and take-profit execution.
        
        NO MORE WEBSOCKET SPAM!
        """
        logger.info("📈 SIMPLIFIED position monitor started - no WebSocket spam!")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Get all configs with open positions (for logging only)
                configs_with_positions = await self._get_configs_with_positions()

                if configs_with_positions and self.cycle_count % 20 == 0:  # Log every minute
                    logger.info(f"📊 Monitoring {len(configs_with_positions)} configs with open positions")

                # 🚀 BATCH OPTIMIZATION: Update ALL positions at once instead of per-config
                try:
                    total_updated = await self.paper_trading.update_position_prices(config_id=None)

                    if total_updated > 0:
                        logger.debug(f"📊 Batch updated {total_updated} positions across all configs")

                except Exception as e:
                    logger.error(f"❌ Batch position update failed: {e}")
                
                self.cycle_count += 1
                
                # Log performance stats occasionally
                if self.cycle_count % 20 == 0 and configs_with_positions:  # Every minute
                    elapsed = time.time() - start_time
                    logger.debug(
                        f"📊 Position monitor cycle {self.cycle_count}: "
                        f"{len(configs_with_positions)} configs, {elapsed:.1f}s"
                    )
                    
            except Exception as e:
                logger.error(f"❌ Position monitor error: {e}")
            
            # 🔥 ADD JITTER to prevent thundering herd! 
            jitter = random.uniform(-0.3, 0.3)  # +/- 0.3 seconds
            await asyncio.sleep(3 + jitter)  # Base 3 seconds + jitter
    
    async def _get_configs_with_positions(self) -> List[Tuple[str, str]]:
        """Get all configurations that have open positions."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT pt.config_id, c.user_id 
                        FROM paper_trades pt
                        JOIN configurations c ON pt.config_id = c.config_id
                        WHERE pt.status = 'open'
                        ORDER BY pt.config_id
                    """)
                    results = cur.fetchall()
                    return [(row[0], row[1]) for row in results]
                    
        except Exception as e:
            logger.error(f"❌ Failed to get configs with positions: {e}")
            return []


# 🔥 ALL THE OTHER WEBSOCKET SPAM METHODS DELETED!
# Dashboard data now comes from SSE stream at /api/dashboard-stream
# This monitoring service ONLY does position price updates for SL/TP execution!