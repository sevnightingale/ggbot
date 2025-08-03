"""
Hummingbot Trading API Endpoints

Provides REST API endpoints for the frontend to query Hummingbot trading data.
Integrates with HummingbotMonitoringService to provide real-time trade monitoring.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
import asyncio

from trading.services.hummingbot_monitoring_service import HummingbotMonitoringService

router = APIRouter(prefix="/hummingbot", tags=["Hummingbot Trading"])

# Initialize monitoring service
monitoring_service = HummingbotMonitoringService()


@router.get("/portfolio/{user_id}", response_model=Dict[str, Any])
async def get_user_portfolio(user_id: str) -> Dict[str, Any]:
    """
    Get portfolio state for a specific user.
    
    Args:
        user_id: User ID to get portfolio for
        
    Returns:
        Portfolio state including balances across connectors
    """
    try:
        result = await monitoring_service.get_portfolio_state(
            account_names=["master_account"],
            connector_names=["binance"]
        )
        
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get portfolio"))
        
        return {
            "user_id": user_id,
            "portfolio": result.get("portfolio", {}),
            "retrieved_at": result.get("retrieved_at")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio: {str(e)}")


@router.get("/positions/{user_id}", response_model=Dict[str, Any])
async def get_user_positions(
    user_id: str,
    connector_names: Optional[List[str]] = Query(default=["binance"])
) -> Dict[str, Any]:
    """
    Get active positions for a specific user.
    
    Args:
        user_id: User ID to get positions for
        connector_names: List of connectors to filter by
        
    Returns:
        Active positions with P&L and status information
    """
    try:
        result = await monitoring_service.get_active_positions(
            user_id=user_id,
            connector_names=connector_names
        )
        
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get positions"))
        
        return {
            "user_id": user_id,
            "positions": result.get("active_positions", []),
            "total_count": result.get("total_count", 0),
            "retrieved_at": result.get("retrieved_at")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting positions: {str(e)}")


@router.get("/orders/{user_id}", response_model=Dict[str, Any])
async def get_user_orders(
    user_id: str,
    connector_names: Optional[List[str]] = Query(default=["binance"])
) -> Dict[str, Any]:
    """
    Get active orders for a specific user.
    
    Args:
        user_id: User ID to get orders for
        connector_names: List of connectors to filter by
        
    Returns:
        Active orders with status and fill information
    """
    try:
        result = await monitoring_service.get_active_orders(
            user_id=user_id,
            connector_names=connector_names
        )
        
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get orders"))
        
        return {
            "user_id": user_id,
            "orders": result.get("active_orders", []),
            "total_count": result.get("total_count", 0),
            "retrieved_at": result.get("retrieved_at")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting orders: {str(e)}")


@router.get("/trades/{user_id}", response_model=Dict[str, Any])
async def get_user_trades(
    user_id: str,
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=100, ge=1, le=1000),
    connector_names: Optional[List[str]] = Query(default=["binance"])
) -> Dict[str, Any]:
    """
    Get trade history for a specific user.
    
    Args:
        user_id: User ID to get trades for
        days: Number of days of history to retrieve (1-90)
        limit: Maximum number of trades to return (1-1000)
        connector_names: List of connectors to filter by
        
    Returns:
        Historical trades with execution details and P&L
    """
    try:
        result = await monitoring_service.get_trade_history(
            user_id=user_id,
            connector_names=connector_names,
            days=days,
            limit=limit
        )
        
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get trades"))
        
        return {
            "user_id": user_id,
            "trades": result.get("trade_history", []),
            "total_count": result.get("total_count", 0),
            "time_range": result.get("time_range", {}),
            "retrieved_at": result.get("retrieved_at")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trades: {str(e)}")


@router.get("/dashboard/{user_id}", response_model=Dict[str, Any])
async def get_user_dashboard(user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive dashboard data for a specific user.
    
    Args:
        user_id: User ID to get dashboard data for
        
    Returns:
        Complete trading dashboard with positions, orders, trades, and summary stats
    """
    try:
        result = await monitoring_service.get_user_dashboard_data(user_id)
        
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to get dashboard data"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard: {str(e)}")


@router.get("/bot/{instance_name}/status", response_model=Dict[str, Any])
async def get_bot_status(instance_name: str) -> Dict[str, Any]:
    """
    Get status of a specific bot instance.
    
    Args:
        instance_name: Name of the bot instance (e.g., ggshot-solusdt-long-abc123)
        
    Returns:
        Bot status including execution state and performance metrics
    """
    try:
        result = await monitoring_service.get_bot_status(instance_name)
        
        if result.get("status") != "success":
            raise HTTPException(status_code=404, detail=f"Bot '{instance_name}' not found")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting bot status: {str(e)}")


@router.get("/system/status", response_model=Dict[str, Any])
async def get_system_status() -> Dict[str, Any]:
    """
    Get overall Hummingbot system status and health.
    
    Returns:
        System status including API health, active bots count, and connection status
    """
    try:
        # Test basic connectivity
        portfolio_result = await monitoring_service.get_portfolio_state()
        api_healthy = portfolio_result.get("status") == "success"
        
        # Get active positions and orders counts
        positions_result = await monitoring_service.get_active_positions()
        orders_result = await monitoring_service.get_active_orders()
        
        active_positions = len(positions_result.get("active_positions", [])) if positions_result.get("status") == "success" else 0
        active_orders = len(orders_result.get("active_orders", [])) if orders_result.get("status") == "success" else 0
        
        return {
            "status": "healthy" if api_healthy else "degraded",
            "api_connection": api_healthy,
            "active_positions": active_positions,
            "active_orders": active_orders,
            "paper_trading_enabled": True,
            "connectors_available": ["binance"],
            "last_checked": portfolio_result.get("retrieved_at")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "api_connection": False,
            "error": str(e)
        }


# WebSocket endpoint for real-time updates (future implementation)
@router.get("/stream/{user_id}")
async def stream_user_updates(user_id: str):
    """
    WebSocket endpoint for real-time trading updates.
    
    TODO: Implement WebSocket streaming for live position/order updates
    """
    return {"message": "WebSocket streaming not yet implemented"}