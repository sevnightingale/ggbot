"""
Real-time Monitoring Service for ggbots Platform

Provides comprehensive real-time monitoring for positions, metrics, and scheduler status.
Replaces HTTP polling with efficient WebSocket-based updates.
"""

import asyncio
import time
from datetime import datetime, timezone, timedelta
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
                            
                            # Only broadcast if user is connected
                            if user_id in self.ws_manager.active_connections:
                                await self._broadcast_position_update(user_id, config_id, positions)
                                
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
                        metrics = await self._calculate_metrics(config_id)
                        
                        # Get recent decisions (replaces HTTP polling)
                        decisions = await self._get_recent_decisions(config_id)
                        
                        # Broadcast metrics update
                        await self._broadcast_metrics_update(user_id, config_id, metrics)
                        
                        # Broadcast decisions update (new)
                        await self._broadcast_decisions_update(user_id, config_id, decisions)
                        
                    except Exception as e:
                        logger.error(f"❌ Metrics calculation failed for {config_id}: {e}")
                        continue
                
                # Broadcast scheduler status and bot statuses to all connected users
                for user_id in connected_users:
                    try:
                        scheduler_status = await self._get_scheduler_status(user_id)
                        await self._broadcast_scheduler_update(user_id, scheduler_status)
                        
                        # Broadcast bot status updates - these should REINFORCE correct state, not break it
                        bot_statuses = await self._get_user_bot_statuses(user_id)
                        await self._broadcast_bot_statuses_update(user_id, bot_statuses)
                        
                    except Exception as e:
                        logger.error(f"❌ Scheduler/bot status failed for {user_id}: {e}")
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
            losing_trades = len([t for t in recent_trades if float(t.get('realized_pnl', 0)) < 0])
            neutral_trades = total_trades - winning_trades - losing_trades
            
            win_rate = (winning_trades / total_trades) if total_trades > 0 else 0
            loss_rate = (losing_trades / total_trades) if total_trades > 0 else 0
            neutral_rate = (neutral_trades / total_trades) if total_trades > 0 else 0
            
            # Calculate total realized PnL from closed trades
            realized_pnl = sum(float(t.get('realized_pnl', 0)) for t in recent_trades)
            avg_trade = realized_pnl / total_trades if total_trades > 0 else 0
            
            # Calculate average profit/loss percentages
            profitable_trades = [t for t in recent_trades if float(t.get('realized_pnl', 0)) > 0]
            losing_trades_list = [t for t in recent_trades if float(t.get('realized_pnl', 0)) < 0]
            
            avg_profit_per_trade = 0
            if profitable_trades:
                # Calculate percentage returns for winning trades (P&L / size_usd * 100)
                profit_percentages = []
                for t in profitable_trades:
                    pnl = float(t.get('realized_pnl', 0))
                    size_usd = float(t.get('size_usd', 0))
                    if size_usd > 0:
                        profit_percentages.append((pnl / size_usd) * 100)
                avg_profit_per_trade = sum(profit_percentages) / len(profit_percentages) if profit_percentages else 0
            
            avg_loss_per_trade = 0
            if losing_trades_list:
                # Calculate percentage returns for losing trades (negative values)
                loss_percentages = []
                for t in losing_trades_list:
                    pnl = float(t.get('realized_pnl', 0))
                    size_usd = float(t.get('size_usd', 0))
                    if size_usd > 0:
                        loss_percentages.append((pnl / size_usd) * 100)  # This will be negative
                avg_loss_per_trade = sum(loss_percentages) / len(loss_percentages) if loss_percentages else 0
            
            # Calculate average trade duration
            avg_trade_duration = "0m"
            if recent_trades:
                duration_minutes = []
                for t in recent_trades:
                    opened_at = t.get('opened_at')
                    closed_at = t.get('closed_at')
                    if opened_at and closed_at:
                        # Parse datetime strings if they're strings
                        if isinstance(opened_at, str):
                            opened_at = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
                        if isinstance(closed_at, str):
                            closed_at = datetime.fromisoformat(closed_at.replace('Z', '+00:00'))
                        
                        duration = (closed_at - opened_at).total_seconds() / 60  # minutes
                        duration_minutes.append(duration)
                
                if duration_minutes:
                    avg_minutes = sum(duration_minutes) / len(duration_minutes)
                    if avg_minutes < 60:
                        avg_trade_duration = f"{int(avg_minutes)}m"
                    elif avg_minutes < 1440:  # less than 24 hours
                        hours = int(avg_minutes / 60)
                        minutes = int(avg_minutes % 60)
                        avg_trade_duration = f"{hours}h{minutes}m" if minutes > 0 else f"{hours}h"
                    else:
                        days = int(avg_minutes / 1440)
                        avg_trade_duration = f"{days}d"
            
            # Generate historical P&L data for chart (last 30 data points)
            profit_loss_data = await self._generate_cumulative_pnl_series(config_id, 30)
            
            # Get unrealized PnL from account summary (includes all open positions)
            unrealized_pnl = float(account_summary.get("total_pnl", 0))  # This should include unrealized
            
            # Total P&L = realized from closed trades + unrealized from open positions
            total_pnl = realized_pnl + unrealized_pnl
            
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
                
                # NEW: Additional fields for PerformancePanel
                "winTrades": winning_trades,
                "lossTrades": losing_trades,
                "neutralTrades": neutral_trades,
                "lossRate": loss_rate,
                "neutralRate": neutral_rate,
                "avgProfitPerTrade": avg_profit_per_trade,
                "avgLossPerTrade": avg_loss_per_trade,
                "avgTradeDuration": avg_trade_duration,
                "profitLossData": profit_loss_data,
                
                "recentTrades": [
                    {
                        "id": str(t.get('trade_id', '')),
                        "symbol": t.get('symbol', ''),
                        "side": t.get('side', ''),
                        "quantity": float(t.get('size_usd', 0)) / float(t.get('entry_price', 1)),  # Convert USD size to quantity
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
        """Get current positions for a config with enhanced data for ActivityPanel."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get positions with enhanced data including decision context
                    cur.execute("""
                        SELECT 
                            pt.trade_id,
                            pt.symbol,
                            pt.side,
                            pt.entry_price,
                            pt.current_price,
                            pt.size_usd,
                            pt.unrealized_pnl,
                            pt.leverage,
                            pt.stop_loss,
                            pt.take_profit,
                            pt.confidence_score,
                            pt.opened_at,
                            d.confidence as decision_confidence,
                            d.reasoning,
                            d.decision_data
                        FROM paper_trades pt
                        LEFT JOIN decisions d ON pt.decision_id = d.decision_id
                        WHERE pt.config_id = %s 
                        AND pt.status = 'open'
                        ORDER BY pt.opened_at DESC
                    """, (config_id,))
                    
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                    
                    positions = []
                    for row in rows:
                        position_dict = dict(zip(columns, row))
                        
                        # Calculate time in trade
                        opened_at = position_dict.get('opened_at')
                        time_in_trade = "0m"
                        if opened_at:
                            if isinstance(opened_at, str):
                                opened_at = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
                            
                            duration = (datetime.now(timezone.utc) - opened_at.replace(tzinfo=timezone.utc)).total_seconds() / 60
                            if duration < 60:
                                time_in_trade = f"{int(duration)}m"
                            elif duration < 1440:  # less than 24 hours
                                hours = int(duration / 60)
                                minutes = int(duration % 60)
                                time_in_trade = f"{hours}h{minutes}m" if minutes > 0 else f"{hours}h"
                            else:
                                days = int(duration / 1440)
                                time_in_trade = f"{days}d"
                        
                        # Map database side to display format
                        side_display = "LONG" if position_dict['side'].lower() in ['buy', 'long'] else "SHORT"
                        
                        # Enhanced position data for ActivityPanel
                        enhanced_position = {
                            "id": str(position_dict.get('trade_id', '')),
                            "symbol": position_dict.get('symbol', ''),
                            "side": side_display,
                            "size": float(position_dict.get('size_usd', 0)),
                            "entryPrice": float(position_dict.get('entry_price', 0)),
                            "currentPrice": float(position_dict.get('current_price') or position_dict.get('entry_price', 0)),
                            "unrealizedPnL": float(position_dict.get('unrealized_pnl', 0)),
                            "timestamp": position_dict.get('opened_at', '').isoformat() if hasattr(position_dict.get('opened_at', ''), 'isoformat') else str(position_dict.get('opened_at', '')),
                            
                            # NEW: Enhanced fields for ActivityPanel
                            "timeInTrade": time_in_trade,
                            "confidence": float(position_dict.get('decision_confidence') or position_dict.get('confidence_score', 0)) * 100,  # Convert to percentage
                            "reasoning_text": position_dict.get('reasoning', 'Position opened based on market analysis'),
                            "signal_timeframe": "5m",  # TODO: Extract from config or decision data
                            "volume_analysis": "Volume confirmation completed",  # TODO: Add real volume analysis
                            
                            # Optional: Stop loss and take profit for advanced display
                            "stopLoss": float(position_dict.get('stop_loss', 0)) if position_dict.get('stop_loss') else None,
                            "takeProfit": float(position_dict.get('take_profit', 0)) if position_dict.get('take_profit') else None,
                        }
                        
                        positions.append(enhanced_position)
                    
                    return positions
            
        except Exception as e:
            logger.error(f"❌ Failed to get enhanced positions for {config_id}: {e}")
            # Fallback to basic positions if enhanced query fails
            try:
                basic_positions = await self.paper_trading.get_open_positions(config_id)
                return basic_positions if basic_positions else []
            except:
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
    
    async def _generate_cumulative_pnl_series(self, config_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Generate cumulative P&L data series for performance chart."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get all closed trades in the last N days, ordered by close time
                    cur.execute("""
                        SELECT closed_at, realized_pnl
                        FROM paper_trades 
                        WHERE config_id = %s 
                        AND status = 'closed' 
                        AND closed_at >= NOW() - INTERVAL '%s days'
                        ORDER BY closed_at ASC
                    """, (config_id, days))
                    
                    trades = cur.fetchall()
                    
                    if not trades:
                        # Return empty series if no trades
                        return []
                    
                    # Generate cumulative P&L series
                    cumulative_pnl = 0
                    series = []
                    
                    for closed_at, realized_pnl in trades:
                        cumulative_pnl += float(realized_pnl or 0)
                        series.append({
                            "date": closed_at.strftime("%Y-%m-%d"),
                            "profit": round(cumulative_pnl, 2)
                        })
                    
                    # If we have fewer than 10 points, pad with current value
                    if len(series) > 0 and len(series) < 10:
                        last_date = datetime.fromisoformat(series[-1]["date"]).date()
                        last_profit = series[-1]["profit"]
                        
                        # Add points up to today
                        current_date = last_date + timedelta(days=1)
                        today = datetime.now(timezone.utc).date()
                        
                        while current_date <= today and len(series) < 10:
                            series.append({
                                "date": current_date.strftime("%Y-%m-%d"),
                                "profit": last_profit
                            })
                            current_date += timedelta(days=1)
                    
                    return series[-30:]  # Return last 30 data points max
                    
        except Exception as e:
            logger.error(f"❌ Failed to generate P&L series for {config_id}: {e}")
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
    
    async def _get_user_bot_statuses(self, user_id: str) -> List[Dict[str, Any]]:
        """Get status for all bots belonging to a user, correlating DB state with scheduler jobs."""
        try:
            from ggbot import scheduler  # Import the global scheduler
            
            # Get all user configurations from database
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id, state, config_data
                        FROM configurations 
                        WHERE user_id = %s AND state != 'archived'
                        ORDER BY config_id
                    """, (user_id,))
                    
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    configs = [dict(zip(columns, row)) for row in results]
            
            bot_statuses = []
            
            # Debug: Log all available scheduler jobs at the start
            if scheduler:
                all_jobs = scheduler.get_jobs()
                logger.info(f"🔍 DEBUG: Found {len(all_jobs)} total scheduler jobs")
                user_job_ids = [j.id for j in all_jobs if user_id in j.id]
                if user_job_ids:
                    logger.info(f"🔍 DEBUG: User {user_id[:8]} has jobs: {user_job_ids}")
            
            for config in configs:
                config_id = config['config_id']
                db_state = config.get('state', 'inactive')
                
                # Extract timeframe from config data
                config_data = config.get('config_data', {})
                extraction_config = config_data.get('extraction', {})
                
                # Try to find timeframe in various locations
                timeframe = None
                if isinstance(extraction_config, dict):
                    # Look for timeframe in extraction config
                    for indicator_group in extraction_config.values():
                        if isinstance(indicator_group, dict) and 'timeframe' in indicator_group:
                            timeframe = indicator_group['timeframe']
                            break
                    
                    # Fallback to a common timeframe if not found
                    if not timeframe:
                        timeframe = '5m'
                else:
                    timeframe = '5m'  # Default fallback
                
                # Check if there's a corresponding scheduler job
                job_id = f"bot:{user_id}:{config_id}:{timeframe}"
                job = scheduler.get_job(job_id) if scheduler else None
                
                # Debug logging for job lookup
                if db_state == 'active' and not job:
                    logger.warning(f"🔍 Active bot {config_id[:8]} has no scheduler job! Looking for job_id: {job_id}")
                    if scheduler:
                        all_jobs = scheduler.get_jobs()
                        user_jobs = [j.id for j in all_jobs if user_id in j.id]
                        logger.warning(f"🔍 Available jobs for user: {user_jobs}")
                
                next_run = None
                if job and job.next_run_time:
                    next_run = job.next_run_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                
                bot_status = {
                    "config_id": config_id,
                    "state": db_state,
                    "timeframe": timeframe,
                    "next_run": next_run,
                    "has_scheduled_job": job is not None,
                    "job_id": job_id if job else None
                }
                
                bot_statuses.append(bot_status)
            
            return bot_statuses
            
        except Exception as e:
            logger.error(f"❌ Failed to get bot statuses for {user_id}: {e}")
            return []
    
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
            
            await self.ws_manager.broadcast_to_user(user_id, message)
            
            # Only log position updates occasionally to reduce spam
            if hasattr(self, 'position_broadcast_count'):
                self.position_broadcast_count += 1
            else:
                self.position_broadcast_count = 1
            
            if self.position_broadcast_count % 10 == 0:
                logger.info(f"📡 Position update #{self.position_broadcast_count} sent to {user_id} for {config_id}")
            
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
            
            await self.ws_manager.broadcast_to_user(user_id, message)
            # Reduced logging for metrics updates
            pass
            
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
    
    async def _broadcast_bot_statuses_update(self, user_id: str, bot_statuses: List[Dict[str, Any]]):
        """Broadcast individual bot statuses for timer updates."""
        try:
            message = {
                "type": "bot_statuses_update",
                "bot_statuses": bot_statuses,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await self.ws_manager.broadcast_to_user(user_id, message)
            
            # Log what we're actually sending to debug the issue
            active_bots = len([bs for bs in bot_statuses if bs.get('state') == 'active'])
            inactive_bots = len([bs for bs in bot_statuses if bs.get('state') == 'inactive'])
            
            # Only log bot status updates occasionally to reduce spam
            if hasattr(self, 'bot_status_broadcast_count'):
                self.bot_status_broadcast_count += 1
            else:
                self.bot_status_broadcast_count = 1
            
            if self.bot_status_broadcast_count % 5 == 0:  # Log more frequently for debugging
                logger.info(f"📡 Bot status update #{self.bot_status_broadcast_count} to {user_id}: {active_bots} active, {inactive_bots} inactive")
                logger.info(f"🔍 Bot states being sent: {[(bs.get('config_id', 'unknown')[:8], bs.get('state', 'unknown')) for bs in bot_statuses]}")
            
        except Exception as e:
            logger.error(f"❌ Failed to broadcast bot statuses update: {e}")