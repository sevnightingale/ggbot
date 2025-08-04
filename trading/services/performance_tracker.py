"""
Performance Tracker Service

Queries both ggBot and Hummingbot databases to provide unified performance metrics
for each configuration. Tracks P&L, win rate, trade count, and account balance.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

from core.common.logger import logger
from core.common.db import get_db_connection


class PerformanceTracker:
    """
    Tracks trading performance across both ggBot and Hummingbot databases.
    
    Key responsibilities:
    - Query strategy_runs for trade decisions and outcomes
    - Query Hummingbot for actual execution data (when available)
    - Calculate P&L, win rate, and other performance metrics
    - Provide per-config and per-user performance summaries
    """
    
    def __init__(self):
        """Initialize the performance tracker."""
        self.logger = logger.bind(service="performance_tracker")
        
        # Hummingbot database connection info (if accessible)
        self.hb_conn_str = "postgresql://admin:password123@localhost:5434/hummingbot_logs"
        
    async def get_config_performance(self, config_id: str) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for a specific configuration.
        
        Args:
            config_id: Configuration UUID
            
        Returns:
            Dict containing P&L, trades, win_rate, account_balance, etc.
        """
        try:
            performance = {
                "config_id": config_id,
                "total_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "trade_count": 0,
                "win_count": 0,
                "loss_count": 0,
                "win_rate": 0.0,
                "account_balance": 10000.0,  # Default paper balance
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "last_trade_time": None,
                "active_positions": 0,
                "trades": []
            }
            
            # Query ggBot database for strategy runs and trades
            with get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                # Get account balance from config_instances
                cur.execute("""
                    SELECT paper_balance_usd 
                    FROM config_instances 
                    WHERE config_id = %s
                """, (config_id,))
                
                balance_row = cur.fetchone()
                if balance_row:
                    performance["account_balance"] = float(balance_row["paper_balance_usd"])
                
                # Get trade entries from strategy_runs
                cur.execute("""
                    SELECT 
                        sr.run_id,
                        sr.scenario,
                        sr.run_result,
                        sr.reasoning_log,
                        sr.decision_data,
                        sr.created_at
                    FROM strategy_runs sr
                    WHERE sr.config_id = %s
                    AND sr.scenario IN ('TRADE_ENTRY', 'TRADE_EXIT', 'TRADE_MANAGEMENT')
                    ORDER BY sr.created_at DESC
                    LIMIT 100
                """, (config_id,))
                
                strategy_runs = cur.fetchall()
                
                # Process trades to calculate P&L
                trades_map = {}  # Group by trade_id
                
                for run in strategy_runs:
                    decision_data = run.get("decision_data", {})
                    trade_id = decision_data.get("trade_id")
                    
                    if trade_id:
                        if trade_id not in trades_map:
                            trades_map[trade_id] = {
                                "trade_id": trade_id,
                                "entry_time": None,
                                "exit_time": None,
                                "entry_price": None,
                                "exit_price": None,
                                "direction": None,
                                "pnl": None,
                                "pnl_pct": None,
                                "status": "open"
                            }
                        
                        trade = trades_map[trade_id]
                        
                        if run["scenario"] == "TRADE_ENTRY":
                            trade["entry_time"] = run["created_at"]
                            trade["entry_price"] = decision_data.get("entry_price")
                            trade["direction"] = decision_data.get("direction", "long")
                            
                        elif run["scenario"] == "TRADE_EXIT":
                            trade["exit_time"] = run["created_at"]
                            trade["exit_price"] = decision_data.get("exit_price")
                            trade["status"] = "closed"
                            
                            # Calculate P&L if we have entry and exit prices
                            if trade["entry_price"] and trade["exit_price"]:
                                entry = float(trade["entry_price"])
                                exit = float(trade["exit_price"])
                                
                                if trade["direction"] == "long":
                                    pnl_pct = ((exit - entry) / entry) * 100
                                else:  # short
                                    pnl_pct = ((entry - exit) / entry) * 100
                                
                                # Assume position size is 5% of account (can be enhanced later)
                                position_size = performance["account_balance"] * 0.05
                                pnl = position_size * (pnl_pct / 100)
                                
                                trade["pnl"] = pnl
                                trade["pnl_pct"] = pnl_pct
                
                # Calculate aggregate metrics
                closed_trades = [t for t in trades_map.values() if t["status"] == "closed" and t["pnl"] is not None]
                performance["trades"] = list(trades_map.values())
                performance["trade_count"] = len(closed_trades)
                performance["active_positions"] = len([t for t in trades_map.values() if t["status"] == "open"])
                
                if closed_trades:
                    # Calculate totals and averages
                    total_pnl = sum(t["pnl"] for t in closed_trades)
                    wins = [t for t in closed_trades if t["pnl"] > 0]
                    losses = [t for t in closed_trades if t["pnl"] < 0]
                    
                    performance["total_pnl"] = total_pnl
                    performance["total_pnl_pct"] = (total_pnl / performance["account_balance"]) * 100
                    performance["win_count"] = len(wins)
                    performance["loss_count"] = len(losses)
                    performance["win_rate"] = (len(wins) / len(closed_trades)) * 100 if closed_trades else 0
                    
                    if wins:
                        performance["largest_win"] = max(t["pnl"] for t in wins)
                        performance["avg_win"] = sum(t["pnl"] for t in wins) / len(wins)
                    
                    if losses:
                        performance["largest_loss"] = min(t["pnl"] for t in losses)
                        performance["avg_loss"] = sum(t["pnl"] for t in losses) / len(losses)
                    
                    # Get last trade time
                    latest_trade = max(closed_trades, key=lambda t: t["exit_time"] or t["entry_time"])
                    performance["last_trade_time"] = latest_trade["exit_time"] or latest_trade["entry_time"]
            
            # Try to enhance with Hummingbot data if available
            await self._enhance_with_hummingbot_data(config_id, performance)
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Failed to get performance for config {config_id}: {e}")
            return performance  # Return partial data on error
    
    async def _enhance_with_hummingbot_data(self, config_id: str, performance: Dict) -> None:
        """
        Enhance performance data with actual execution data from Hummingbot.
        
        Args:
            config_id: Configuration UUID
            performance: Performance dict to enhance
        """
        try:
            # Get instance name for this config
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT instance_name, hummingbot_account 
                    FROM config_instances 
                    WHERE config_id = %s
                """, (config_id,))
                
                instance_info = cur.fetchone()
                if not instance_info:
                    return
                
                instance_name = instance_info[0]
            
            # Try to connect to Hummingbot database
            try:
                hb_conn = psycopg2.connect(self.hb_conn_str)
                hb_cur = hb_conn.cursor(cursor_factory=RealDictCursor)
                
                # Get actual trades from Hummingbot
                hb_cur.execute("""
                    SELECT 
                        timestamp,
                        market,
                        trade_type,
                        price,
                        amount,
                        trade_fee,
                        order_id
                    FROM trade_fills
                    WHERE config_file_path LIKE %s
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, (f"%{instance_name}%",))
                
                hb_trades = hb_cur.fetchall()
                
                if hb_trades:
                    # Update with real execution data
                    performance["hummingbot_trades"] = len(hb_trades)
                    performance["last_hb_trade"] = hb_trades[0]["timestamp"]
                    
                    # Calculate real P&L from Hummingbot trades
                    # (This is simplified - real implementation would match trades properly)
                    buy_trades = [t for t in hb_trades if t["trade_type"] == "BUY"]
                    sell_trades = [t for t in hb_trades if t["trade_type"] == "SELL"]
                    
                    if buy_trades and sell_trades:
                        avg_buy = sum(float(t["price"]) * float(t["amount"]) for t in buy_trades) / sum(float(t["amount"]) for t in buy_trades)
                        avg_sell = sum(float(t["price"]) * float(t["amount"]) for t in sell_trades) / sum(float(t["amount"]) for t in sell_trades)
                        
                        # Update with real P&L if available
                        real_pnl = (avg_sell - avg_buy) * min(
                            sum(float(t["amount"]) for t in buy_trades),
                            sum(float(t["amount"]) for t in sell_trades)
                        )
                        
                        performance["hummingbot_pnl"] = real_pnl
                
                hb_cur.close()
                hb_conn.close()
                
            except psycopg2.Error as e:
                # Hummingbot DB not accessible - this is okay
                self.logger.debug(f"Hummingbot database not accessible: {e}")
                
        except Exception as e:
            self.logger.debug(f"Could not enhance with Hummingbot data: {e}")
    
    async def get_all_active_configs(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get performance summary for all active configurations for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of config performance summaries
        """
        try:
            configs = []
            
            with get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                # Get all configurations for the user
                cur.execute("""
                    SELECT 
                        c.config_id,
                        c.config_name,
                        c.config_type,
                        ci.instance_name,
                        ci.paper_balance_usd,
                        ci.status
                    FROM configurations c
                    LEFT JOIN config_instances ci ON c.config_id = ci.config_id
                    WHERE c.user_id = %s
                    ORDER BY c.created_at DESC
                """, (user_id,))
                
                config_rows = cur.fetchall()
                
                # Get basic performance for each config
                for row in config_rows:
                    config_summary = {
                        "config_id": row["config_id"],
                        "config_name": row["config_name"],
                        "config_type": row["config_type"],
                        "status": row["status"] or "inactive",
                        "account_balance": float(row["paper_balance_usd"]) if row["paper_balance_usd"] else 10000.0,
                        "total_pnl": 0.0,
                        "total_pnl_pct": 0.0,
                        "trade_count": 0,
                        "win_rate": 0.0,
                        "last_trade_time": None
                    }
                    
                    # Get quick stats from strategy_runs
                    cur.execute("""
                        SELECT 
                            COUNT(DISTINCT decision_data->>'trade_id') as trade_count,
                            MAX(created_at) as last_activity
                        FROM strategy_runs
                        WHERE config_id = %s
                        AND scenario IN ('TRADE_ENTRY', 'TRADE_EXIT')
                    """, (row["config_id"],))
                    
                    stats = cur.fetchone()
                    if stats:
                        config_summary["trade_count"] = stats["trade_count"] or 0
                        config_summary["last_trade_time"] = stats["last_activity"]
                    
                    configs.append(config_summary)
            
            # Get detailed performance for active configs (async)
            for config in configs:
                if config["status"] == "active":
                    detailed = await self.get_config_performance(config["config_id"])
                    config["total_pnl"] = detailed["total_pnl"]
                    config["total_pnl_pct"] = detailed["total_pnl_pct"]
                    config["win_rate"] = detailed["win_rate"]
                    config["active_positions"] = detailed["active_positions"]
            
            return configs
            
        except Exception as e:
            self.logger.error(f"Failed to get configs for user {user_id}: {e}")
            return []
    
    async def get_recent_trades(self, config_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent trades for a configuration.
        
        Args:
            config_id: Configuration UUID
            limit: Maximum number of trades to return
            
        Returns:
            List of recent trades with details
        """
        try:
            trades = []
            
            with get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                # Get recent trade decisions
                cur.execute("""
                    SELECT 
                        sr.run_id,
                        sr.scenario,
                        sr.run_result,
                        sr.decision_data,
                        sr.created_at,
                        sr.reasoning_log
                    FROM strategy_runs sr
                    WHERE sr.config_id = %s
                    AND sr.scenario = 'TRADE_ENTRY'
                    ORDER BY sr.created_at DESC
                    LIMIT %s
                """, (config_id, limit))
                
                entries = cur.fetchall()
                
                for entry in entries:
                    decision_data = entry.get("decision_data", {})
                    
                    trade = {
                        "trade_id": decision_data.get("trade_id"),
                        "symbol": decision_data.get("symbol"),
                        "direction": decision_data.get("direction", "long"),
                        "entry_time": entry["created_at"],
                        "entry_price": decision_data.get("entry_price"),
                        "confidence": decision_data.get("confidence"),
                        "reasoning": entry.get("reasoning_log", "")[:200],  # Truncate for display
                        "status": "open",
                        "pnl": None,
                        "pnl_pct": None
                    }
                    
                    # Look for exit
                    if trade["trade_id"]:
                        cur.execute("""
                            SELECT decision_data, created_at
                            FROM strategy_runs
                            WHERE config_id = %s
                            AND scenario = 'TRADE_EXIT'
                            AND decision_data->>'trade_id' = %s
                        """, (config_id, trade["trade_id"]))
                        
                        exit_row = cur.fetchone()
                        if exit_row:
                            exit_data = exit_row.get("decision_data", {})
                            trade["exit_time"] = exit_row["created_at"]
                            trade["exit_price"] = exit_data.get("exit_price")
                            trade["status"] = "closed"
                            
                            # Calculate P&L
                            if trade["entry_price"] and trade["exit_price"]:
                                entry = float(trade["entry_price"])
                                exit = float(trade["exit_price"])
                                
                                if trade["direction"] == "long":
                                    trade["pnl_pct"] = ((exit - entry) / entry) * 100
                                else:
                                    trade["pnl_pct"] = ((entry - exit) / entry) * 100
                                
                                # Rough P&L calc (assumes 5% position size on 10k account)
                                trade["pnl"] = 500 * (trade["pnl_pct"] / 100)
                    
                    trades.append(trade)
            
            return trades
            
        except Exception as e:
            self.logger.error(f"Failed to get recent trades for {config_id}: {e}")
            return []


# Singleton instance
_performance_tracker = None

def get_performance_tracker() -> PerformanceTracker:
    """Get or create the singleton PerformanceTracker instance."""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker