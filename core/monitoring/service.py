"""
Real-time Monitoring Service for ggbots Platform

Provides comprehensive real-time monitoring for positions, metrics, and scheduler status.
Replaces HTTP polling with efficient WebSocket-based updates.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

from core.common.logger import logger as base_logger

# Set up monitoring-specific logger with aggressive log management
base_logger.add(
    "/home/sev/ggbot/logs/monitoring.log",
    filter=lambda record: record["extra"].get("service") == "monitoring",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    rotation="10 MB",      # Rotate every 10MB (small files)
    retention="2 days",    # Keep only 2 days of logs  
    compression="gz",      # Compress old logs
    enqueue=True,          # Thread-safe logging
    level="INFO"           # Only INFO and above (no DEBUG spam)
)

# Create monitoring logger with service binding
logger = base_logger.bind(service="monitoring")
from core.common.db import get_db_connection
from core.services.config_service import ConfigService
from trading.paper.supabase_service import SupabasePaperTradingService


class MonitoringService:
    """
    Real-time monitoring service for ggbots trading platform.
    
    Monitors:
    - Position prices and P&L (critical for stop-loss/take-profit)
    - Bot metrics and performance data
    - Scheduler status and job information
    
    Broadcasts updates via WebSocket to connected users only.
    """
    
    def __init__(self, websocket_manager):
        self.ws_manager = websocket_manager
        self.paper_trading = SupabasePaperTradingService()
        self.config_service = ConfigService()
        self.running = False
        self.cycle_count = 0
        
        # Performance tracking
        self.last_stats_time = time.time()
        
        logger.info("🔧 MonitoringService initialized")
    
    async def start(self):
        """Start all monitoring tasks concurrently."""
        logger.info("🚀 Starting monitoring service with 7-second intervals")
        self.running = True
        
        try:
            await asyncio.gather(
                self._position_monitor(),
                self._metrics_scheduler_monitor(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"❌ Monitoring service failed: {e}")
            raise
        finally:
            logger.info("🛑 Monitoring service stopped")
    
    async def stop(self):
        """Gracefully stop monitoring service."""
        logger.info("🛑 Stopping monitoring service...")
        self.running = False
    
    async def _position_monitor(self):
        """
        Critical position monitoring loop.
        
        Updates prices for ALL open positions every 7 seconds.
        This is essential for stop-loss and take-profit execution.
        """
        logger.info("📈 Position monitor started")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Get all configs with open positions
                configs_with_positions = await self._get_configs_with_positions()
                
                if configs_with_positions and self.cycle_count % 4 == 0:
                    logger.info(f"🔍 Monitoring {len(configs_with_positions)} configs with open positions")
                
                for config_id, user_id in configs_with_positions:
                    try:
                        # Update position prices (critical for risk management)
                        updated_count = await self.paper_trading.update_position_prices(config_id)
                        
                        if updated_count > 0:
                            # Get fresh positions to broadcast
                            positions = await self._get_positions(config_id)
                            logger.info(f"🔍 POSITION MONITOR DEBUG: Got {len(positions)} positions from _get_positions for {config_id}")
                            
                            # Only broadcast if user is connected
                            if user_id in self.ws_manager.active_connections:
                                await self._broadcast_position_update(user_id, config_id, positions)
                            else:
                                logger.info(f"🔍 POSITION MONITOR DEBUG: User {user_id} not connected, skipping broadcast")
                                
                    except Exception as e:
                        logger.error(f"❌ Position update failed for {config_id}: {e}")
                        continue
                
                # Log performance stats every 30 seconds
                if self.cycle_count % 4 == 0 and configs_with_positions:
                    elapsed = time.time() - start_time
                    logger.debug(
                        f"📊 Position monitor cycle {self.cycle_count}: "
                        f"{len(configs_with_positions)} configs, {elapsed:.1f}s"
                    )
                    
            except Exception as e:
                logger.error(f"❌ Position monitor error: {e}")
            
            await asyncio.sleep(7)
    
    async def _metrics_scheduler_monitor(self):
        """
        Metrics and scheduler monitoring loop.
        
        Calculates metrics for all active bots and provides scheduler updates.
        Broadcasts only to connected users for optimal performance.
        """
        logger.info("📊 Metrics/scheduler monitor started")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Get all active configurations
                all_configs = await self._get_all_active_configs()
                
                # Get connected users for broadcasting
                connected_users = set(self.ws_manager.active_connections.keys())
                
                if connected_users and self.cycle_count % 8 == 0:
                    logger.info(f"🔍 Processing {len(all_configs)} configs for {len(connected_users)} connected users")
                
                # Process metrics for all configs
                for config_id, user_id in all_configs:
                    if user_id not in connected_users:
                        continue  # Skip if user not connected
                        
                    try:
                        # Calculate metrics
                        logger.info(f"🔍 METRICS LOOP DEBUG: Calculating metrics for {config_id}")
                        metrics = await self._calculate_metrics(config_id)
                        logger.info(f"🔍 METRICS LOOP DEBUG: Calculated metrics keys: {list(metrics.keys()) if metrics else 'None'}")
                        
                        # Get recent decisions (replaces HTTP polling)
                        decisions = await self._get_recent_decisions(config_id)
                        logger.info(f"🔍 DECISIONS DEBUG: Got {len(decisions)} decisions for {config_id}")
                        
                        # Broadcast metrics update
                        await self._broadcast_metrics_update(user_id, config_id, metrics)
                        
                        # Broadcast decisions update (new)
                        await self._broadcast_decisions_update(user_id, config_id, decisions)
                        
                    except Exception as e:
                        logger.error(f"❌ Metrics calculation failed for {config_id}: {e}")
                        continue
                
                # Broadcast scheduler status to all connected users
                for user_id in connected_users:
                    try:
                        scheduler_status = await self._get_scheduler_status(user_id)
                        await self._broadcast_scheduler_update(user_id, scheduler_status)
                        
                    except Exception as e:
                        logger.error(f"❌ Scheduler status failed for {user_id}: {e}")
                        continue
                
                self.cycle_count += 1
                
                # Log performance stats every minute
                if self.cycle_count % 8 == 0:
                    elapsed = time.time() - start_time
                    logger.info(
                        f"📊 Metrics monitor cycle {self.cycle_count}: "
                        f"{len(all_configs)} configs, {len(connected_users)} users, {elapsed:.1f}s"
                    )
                    
            except Exception as e:
                logger.error(f"❌ Metrics monitor error: {e}")
            
            await asyncio.sleep(7)
    
    # Helper Methods
    
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
    
    async def _get_all_active_configs(self) -> List[Tuple[str, str]]:
        """Get all active bot configurations."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id, user_id 
                        FROM configurations 
                        WHERE state != 'archived'
                        ORDER BY config_id
                    """)
                    results = cur.fetchall()
                    return [(row[0], row[1]) for row in results]
                    
        except Exception as e:
            logger.error(f"❌ Failed to get active configs: {e}")
            return []
    
    async def _calculate_metrics(self, config_id: str) -> Dict[str, Any]:
        """Calculate bot metrics (extracted from existing endpoint logic)."""
        try:
            # Get account summary
            account_summary = await self.paper_trading.get_account_summary(config_id)
            
            if "error" in account_summary:
                return {"error": account_summary["error"]}
            
            # Get recent trades for performance calculation
            recent_trades = await self._get_recent_trades(config_id)
            
            # Calculate performance metrics
            total_trades = len(recent_trades)
            winning_trades = len([t for t in recent_trades if float(t.get('realized_pnl', 0)) > 0])
            win_rate = (winning_trades / total_trades) if total_trades > 0 else 0
            
            # Calculate total realized PnL from closed trades
            realized_pnl = sum(float(t.get('realized_pnl', 0)) for t in recent_trades)
            avg_trade = realized_pnl / total_trades if total_trades > 0 else 0
            
            # Get unrealized PnL from account summary (includes all open positions)
            unrealized_pnl = float(account_summary.get("total_pnl", 0))  # This should include unrealized
            
            # Total P&L = realized from closed trades + unrealized from open positions
            total_pnl = realized_pnl + unrealized_pnl
            
            logger.info(f"🔍 PNL DEBUG: Realized PnL: {realized_pnl}, Unrealized PnL: {unrealized_pnl}, Total: {total_pnl}")
            
            # Transform to match frontend interface (useBotMetrics.ts)
            return {
                # Direct properties (not nested) to match frontend BotMetrics interface
                "balance": float(account_summary.get("current_balance", account_summary.get("balance", 10000))),
                "totalPnL": total_pnl,
                "totalTrades": total_trades,
                "winRate": win_rate,  # As decimal (0.0-1.0), not percentage
                "avgTrade": avg_trade,
                "maxDrawdown": 0,  # TODO: Calculate from trade history
                "sharpeRatio": 0,  # TODO: Calculate from returns
                "recentTrades": [
                    {
                        "id": str(t.get('trade_id', '')),
                        "symbol": t.get('symbol', ''),
                        "side": t.get('side', ''),
                        "quantity": float(t.get('quantity', 0)),
                        "price": float(t.get('entry_price', 0)),
                        "pnl": float(t.get('realized_pnl', 0)),
                        "timestamp": t.get('opened_at', '').isoformat() if hasattr(t.get('opened_at', ''), 'isoformat') else str(t.get('opened_at', ''))
                    }
                    for t in recent_trades[:10]  # Last 10 trades
                ],
                "last_updated": datetime.now(timezone.utc).isoformat(),
                
                # Keep original structure for backward compatibility if needed
                "_original": {
                    "account_summary": account_summary,
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "win_rate": win_rate
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate metrics for {config_id}: {e}")
            return {"error": str(e)}
    
    async def _get_positions(self, config_id: str) -> List[Dict[str, Any]]:
        """Get current positions for a config (extracted from existing endpoint)."""
        try:
            logger.info(f"🔍 GET_POSITIONS DEBUG: Calling paper_trading.get_open_positions for {config_id}")
            positions = await self.paper_trading.get_open_positions(config_id)
            logger.info(f"🔍 GET_POSITIONS DEBUG: Raw positions from service: {positions}")
            result = positions if positions else []
            logger.info(f"🔍 GET_POSITIONS DEBUG: Returning {len(result)} positions")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get positions for {config_id}: {e}")
            return []
    
    async def _get_recent_trades(self, config_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent completed trades for a config."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM paper_trades 
                        WHERE config_id = %s AND status = 'closed'
                        ORDER BY opened_at DESC 
                        LIMIT %s
                    """, (config_id, limit))
                    
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    return [dict(zip(columns, row)) for row in results]
                    
        except Exception as e:
            logger.error(f"❌ Failed to get recent trades for {config_id}: {e}")
            return []
    
    async def _get_recent_decisions(self, config_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent decisions for a config (replaces HTTP polling)."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT decision_id, symbol, action, status, confidence, 
                               reasoning, created_at, decision_data
                        FROM decisions 
                        WHERE config_id = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (config_id, limit))
                    
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    decisions = []
                    
                    for row in results:
                        decision_dict = dict(zip(columns, row))
                        # Convert datetime to ISO string for JSON serialization
                        if decision_dict.get('created_at'):
                            decision_dict['created_at'] = decision_dict['created_at'].isoformat()
                        # Convert Decimal to float for confidence
                        if decision_dict.get('confidence'):
                            decision_dict['confidence'] = float(decision_dict['confidence'])
                        decisions.append(decision_dict)
                    
                    return decisions
                    
        except Exception as e:
            logger.error(f"❌ Failed to get recent decisions for {config_id}: {e}")
            return []
    
    async def _get_scheduler_status(self, user_id: str) -> Dict[str, Any]:
        """Get scheduler status for a user (extracted from existing endpoint)."""
        try:
            from ggbot import scheduler  # Import the global scheduler
            
            if not scheduler:
                return {
                    "status": "error",
                    "scheduler_running": False,
                    "active_jobs": [],
                    "job_count": 0,
                    "error": "Scheduler not initialized"
                }
            
            # Get jobs for this user
            all_jobs = scheduler.get_jobs()
            user_jobs = [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                }
                for job in all_jobs 
                if user_id in job.id  # Assuming job IDs contain user_id
            ]
            
            return {
                "status": "success",
                "scheduler_running": True,
                "active_jobs": user_jobs,
                "job_count": len(user_jobs),
                "total_jobs_in_scheduler": len(all_jobs)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get scheduler status for {user_id}: {e}")
            return {
                "status": "error",
                "scheduler_running": False,
                "active_jobs": [],
                "job_count": 0,
                "error": str(e)
            }
    
    # Broadcasting Methods
    
    async def _broadcast_position_update(self, user_id: str, config_id: str, positions: List[Dict[str, Any]]):
        """Broadcast position update to user."""
        try:
            message = {
                "type": "position_update",
                "config_id": config_id,
                "positions": positions,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # DEBUGGING: Log the actual positions data being sent
            logger.info(f"🔍 POSITION DEBUG: Sending {len(positions)} positions for {config_id}")
            logger.info(f"🔍 POSITION DEBUG: Raw positions data: {positions}")
            
            await self.ws_manager.broadcast_to_user(user_id, message)
            
            # Always log position updates now for debugging
            if hasattr(self, 'position_broadcast_count'):
                self.position_broadcast_count += 1
            else:
                self.position_broadcast_count = 1
            
            logger.info(f"📡 Position update #{self.position_broadcast_count} sent to {user_id} for {config_id} with {len(positions)} positions")
            
        except Exception as e:
            logger.error(f"❌ Failed to broadcast position update: {e}")
    
    async def _broadcast_metrics_update(self, user_id: str, config_id: str, metrics: Dict[str, Any]):
        """Broadcast metrics update to user."""
        try:
            message = {
                "type": "metrics_update",
                "config_id": config_id,
                "metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # DEBUGGING: Log the actual metrics data being sent
            logger.info(f"🔍 METRICS DEBUG: Sending metrics for {config_id}")
            logger.info(f"🔍 METRICS DEBUG: Balance: {metrics.get('balance', 'MISSING')}")
            logger.info(f"🔍 METRICS DEBUG: Total PnL: {metrics.get('totalPnL', 'MISSING')}")
            logger.info(f"🔍 METRICS DEBUG: Raw metrics: {metrics}")
            
            await self.ws_manager.broadcast_to_user(user_id, message)
            logger.info(f"📡 Metrics update sent to {user_id} for {config_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to broadcast metrics update: {e}")
    
    async def _broadcast_decisions_update(self, user_id: str, config_id: str, decisions: List[Dict[str, Any]]):
        """Broadcast decisions update to user (replaces HTTP polling)."""
        try:
            message = {
                "type": "decisions_update",
                "config_id": config_id,
                "decisions": decisions,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await self.ws_manager.broadcast_to_user(user_id, message)
            # Only log decisions updates occasionally to reduce spam
            if hasattr(self, 'decisions_broadcast_count'):
                self.decisions_broadcast_count += 1
            else:
                self.decisions_broadcast_count = 1
            
            if self.decisions_broadcast_count % 10 == 0:
                logger.info(f"📡 Decisions update #{self.decisions_broadcast_count} sent to {user_id} for {config_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to broadcast decisions update: {e}")
    
    async def _broadcast_scheduler_update(self, user_id: str, scheduler_status: Dict[str, Any]):
        """Broadcast scheduler status update to user."""
        try:
            message = {
                "type": "scheduler_update",
                "scheduler_status": scheduler_status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await self.ws_manager.broadcast_to_user(user_id, message)
            # Reduced logging for scheduler updates
            pass
            
        except Exception as e:
            logger.error(f"❌ Failed to broadcast scheduler update: {e}")