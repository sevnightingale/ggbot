"""
Hummingbot Monitoring Service

Provides real-time and historical trade monitoring for ggbot users.
Queries active positions, orders, and trade history from the Hummingbot API.
"""

import asyncio
import json
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from decimal import Decimal

try:
    from common.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class HummingbotMonitoringService:
    """Monitor trades and positions from Hummingbot API for ggbot users."""
    
    def __init__(self, api_url: str = None, username: str = "admin", password: str = "admin"):
        """Initialize monitoring service with Hummingbot API credentials."""
        
        # Determine API URL - use environment variable or default
        if api_url is None:
            api_url = os.getenv("HUMMINGBOT_API_HOST", "http://localhost:15888")
        
        self.api_url = api_url
        self.username = username
        self.password = password
        
        if hasattr(logger, 'bind'):
            logger.bind(service="hummingbot_monitor").info(
                f"HummingbotMonitoringService initialized with API at {api_url}"
            )
        else:
            logger.info(f"HummingbotMonitoringService initialized with API at {api_url}")
    
    async def get_active_positions(self, user_id: str = None, 
                                 connector_names: List[str] = None) -> Dict[str, Any]:
        """
        Get all active positions for a user across connectors.
        
        Args:
            user_id: Filter by specific user (optional)
            connector_names: Filter by specific connectors (optional)
            
        Returns:
            Dictionary with active positions data
        """
        try:
            # Build filter request
            filter_request = {}
            if connector_names:
                filter_request["connector_names"] = connector_names
            
            response = requests.post(
                f"{self.api_url}/trading/positions",
                json=filter_request,
                auth=(self.username, self.password),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                positions_data = response.json()
                
                # Filter by user_id if provided (positions have instance names with user info)
                if user_id:
                    filtered_positions = []
                    for position in positions_data.get("data", []):
                        # Check if position instance name contains user_id
                        instance_name = position.get("instance_name", "")
                        if user_id in instance_name or f"ggshot-" in instance_name:
                            filtered_positions.append(position)
                    positions_data["data"] = filtered_positions
                
                return {
                    "status": "success",
                    "active_positions": positions_data.get("data", []),
                    "total_count": len(positions_data.get("data", [])),
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                }
                
            else:
                error_msg = response.text
                logger.error(f"Failed to get active positions: {error_msg}")
                return {"status": "error", "error": error_msg}
                
        except Exception as e:
            logger.error(f"Error getting active positions: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_active_orders(self, user_id: str = None,
                              connector_names: List[str] = None) -> Dict[str, Any]:
        """
        Get all active (in-flight) orders for a user.
        
        Args:
            user_id: Filter by specific user (optional)
            connector_names: Filter by specific connectors (optional)
            
        Returns:
            Dictionary with active orders data
        """
        try:
            # Build filter request
            filter_request = {}
            if connector_names:
                filter_request["connector_names"] = connector_names
            
            response = requests.post(
                f"{self.api_url}/trading/orders/active",
                json=filter_request,
                auth=(self.username, self.password),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                orders_data = response.json()
                
                # Filter by user_id if provided
                if user_id:
                    filtered_orders = []
                    for order in orders_data.get("data", []):
                        # Check if order is from a ggshot instance
                        instance_name = order.get("instance_name", "")
                        if user_id in instance_name or "ggshot-" in instance_name:
                            filtered_orders.append(order)
                    orders_data["data"] = filtered_orders
                
                return {
                    "status": "success",
                    "active_orders": orders_data.get("data", []),
                    "total_count": len(orders_data.get("data", [])),
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                }
                
            else:
                error_msg = response.text
                logger.error(f"Failed to get active orders: {error_msg}")
                return {"status": "error", "error": error_msg}
                
        except Exception as e:
            logger.error(f"Error getting active orders: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_trade_history(self, user_id: str = None,
                              connector_names: List[str] = None,
                              days: int = 7,
                              limit: int = 100) -> Dict[str, Any]:
        """
        Get historical trades for a user.
        
        Args:
            user_id: Filter by specific user (optional)
            connector_names: Filter by specific connectors (optional)
            days: Number of days of history to retrieve
            limit: Maximum number of trades to return
            
        Returns:
            Dictionary with trade history data
        """
        try:
            # Build filter request with time range
            from datetime import timedelta
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days)
            
            filter_request = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "limit": limit
            }
            
            if connector_names:
                filter_request["connector_names"] = connector_names
            
            response = requests.post(
                f"{self.api_url}/trading/trades",
                json=filter_request,
                auth=(self.username, self.password),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                trades_data = response.json()
                
                # Filter by user_id if provided
                if user_id:
                    filtered_trades = []
                    for trade in trades_data.get("data", []):
                        # Check if trade is from a ggshot instance
                        instance_name = trade.get("instance_name", "")
                        if user_id in instance_name or "ggshot-" in instance_name:
                            filtered_trades.append(trade)
                    trades_data["data"] = filtered_trades
                
                return {
                    "status": "success",
                    "trade_history": trades_data.get("data", []),
                    "total_count": len(trades_data.get("data", [])),
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "days": days
                    },
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                }
                
            else:
                error_msg = response.text
                logger.error(f"Failed to get trade history: {error_msg}")
                return {"status": "error", "error": error_msg}
                
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_bot_status(self, instance_name: str) -> Dict[str, Any]:
        """
        Get status of a specific bot instance.
        
        Args:
            instance_name: Name of the bot instance to check
            
        Returns:
            Dictionary with bot status information
        """
        try:
            response = requests.get(
                f"{self.api_url}/bot-orchestration/{instance_name}/status",
                auth=(self.username, self.password)
            )
            
            if response.status_code == 200:
                status_data = response.json()
                return {
                    "status": "success",
                    "bot_status": status_data,
                    "instance_name": instance_name,
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                error_msg = response.text
                return {"status": "error", "error": error_msg}
                
        except Exception as e:
            logger.error(f"Error getting bot status for {instance_name}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_portfolio_state(self, account_names: List[str] = None,
                                connector_names: List[str] = None) -> Dict[str, Any]:
        """
        Get current portfolio state across accounts and connectors.
        
        Args:
            account_names: Filter by specific accounts (optional)
            connector_names: Filter by specific connectors (optional)
            
        Returns:
            Dictionary with portfolio state data
        """
        try:
            # Build filter request
            filter_request = {}
            if account_names:
                filter_request["account_names"] = account_names
            if connector_names:
                filter_request["connector_names"] = connector_names
            
            response = requests.post(
                f"{self.api_url}/portfolio/state",
                json=filter_request,
                auth=(self.username, self.password),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                portfolio_data = response.json()
                return {
                    "status": "success",
                    "portfolio": portfolio_data,
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                error_msg = response.text
                logger.error(f"Failed to get portfolio state: {error_msg}")
                return {"status": "error", "error": error_msg}
                
        except Exception as e:
            logger.error(f"Error getting portfolio state: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for a specific user.
        
        Args:
            user_id: User ID to get dashboard data for
            
        Returns:
            Complete dashboard data including positions, orders, trades, and portfolio
        """
        try:
            logger.bind(service="hummingbot_monitor").info(
                f"Getting dashboard data for user {user_id}"
            )
            
            # Get all data in parallel for better performance
            tasks = [
                self.get_active_positions(user_id, ["binance"]),
                self.get_active_orders(user_id, ["binance"]),
                self.get_trade_history(user_id, ["binance"], days=30),
                self.get_portfolio_state(["master_account"], ["binance"])
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            positions_result = results[0] if not isinstance(results[0], Exception) else {"status": "error", "error": str(results[0])}
            orders_result = results[1] if not isinstance(results[1], Exception) else {"status": "error", "error": str(results[1])}
            trades_result = results[2] if not isinstance(results[2], Exception) else {"status": "error", "error": str(results[2])}
            portfolio_result = results[3] if not isinstance(results[3], Exception) else {"status": "error", "error": str(results[3])}
            
            # Calculate summary statistics
            active_positions_count = len(positions_result.get("active_positions", []))
            active_orders_count = len(orders_result.get("active_orders", []))
            total_trades = len(trades_result.get("trade_history", []))
            
            # Calculate P&L from positions
            total_unrealized_pnl = 0.0
            for position in positions_result.get("active_positions", []):
                unrealized_pnl = position.get("unrealized_pnl", 0)
                if isinstance(unrealized_pnl, (int, float)):
                    total_unrealized_pnl += float(unrealized_pnl)
            
            return {
                "status": "success",
                "user_id": user_id,
                "summary": {
                    "active_positions": active_positions_count,
                    "active_orders": active_orders_count,
                    "total_trades_30d": total_trades,
                    "total_unrealized_pnl": total_unrealized_pnl
                },
                "positions": positions_result,
                "orders": orders_result,
                "trades": trades_result,
                "portfolio": portfolio_result,
                "retrieved_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}


async def test_monitoring_service():
    """Test the HummingbotMonitoringService with sample queries."""
    
    service = HummingbotMonitoringService()
    
    print("🔍 Testing Hummingbot Monitoring Service...")
    
    # Test portfolio state
    print("\n📊 Portfolio State:")
    portfolio = await service.get_portfolio_state()
    print(f"Status: {portfolio.get('status')}")
    
    # Test active positions
    print("\n📈 Active Positions:")
    positions = await service.get_active_positions()
    print(f"Status: {positions.get('status')}, Count: {positions.get('total_count', 0)}")
    
    # Test dashboard data for test user
    print("\n🎯 User Dashboard (test_user):")
    dashboard = await service.get_user_dashboard_data("test_user")
    print(f"Status: {dashboard.get('status')}")
    if dashboard.get('status') == 'success':
        summary = dashboard.get('summary', {})
        print(f"Active Positions: {summary.get('active_positions', 0)}")
        print(f"Active Orders: {summary.get('active_orders', 0)}")
        print(f"Total Trades (30d): {summary.get('total_trades_30d', 0)}")
        print(f"Unrealized P&L: ${summary.get('total_unrealized_pnl', 0):.2f}")


if __name__ == "__main__":
    asyncio.run(test_monitoring_service())