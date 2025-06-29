"""
Dashboard API

Provides REST endpoints for frontend dashboard functionality including
position monitoring, performance metrics, and agent control.
"""
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.common.db import get_db_connection

app = FastAPI(title="Dashboard API", version="1.0.0")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

    async def broadcast_to_user(self, user_id: str, data: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(data)

manager = ConnectionManager()


class Position(BaseModel):
    trade_id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percentage: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    duration: str
    decision_id: Optional[str] = None


class PerformanceMetrics(BaseModel):
    period: str
    metrics: Dict[str, Any]
    daily_pnl: List[Dict[str, Any]]


class AgentStatus(BaseModel):
    overall_status: str
    modules: Dict[str, Dict[str, Any]]


@app.get("/api/dashboard/{user_id}/positions")
async def get_current_positions(user_id: str):
    """Get current open positions for a user (legacy API - kept for backward compatibility)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    t.trade_id, 
                    t.symbol,
                    CASE 
                        WHEN t.size_contracts > 0 THEN 'long'
                        WHEN t.size_contracts < 0 THEN 'short'
                        ELSE 'unknown'
                    END as side,
                    t.collateral_amount as size,
                    t.entry_price,
                    COALESCE(t.mark_price, t.entry_price) as current_price,
                    COALESCE(t.unrealized_pnl, 0) as unrealized_pnl,
                    t.stop_loss,
                    t.take_profit,
                    t.config_id as decision_id,  -- Map config_id to decision_id for compatibility
                    t.opened_at as created_at
                FROM trades t
                WHERE t.user_id = %s 
                  AND t.trade_status = 'open'
                ORDER BY t.opened_at DESC
            """, (user_id,))
            
            results = cur.fetchall()
            positions = []
            
            for row in results:
                (trade_id, symbol, side, size, entry_price, 
                 current_price, unrealized_pnl, stop_loss, 
                 take_profit, decision_id, created_at) = row
                
                # Calculate duration
                duration_td = datetime.utcnow() - created_at
                hours = int(duration_td.total_seconds() // 3600)
                minutes = int((duration_td.total_seconds() % 3600) // 60)
                duration = f"{hours}h {minutes}m"
                
                # Calculate PnL percentage
                if entry_price and entry_price > 0:
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    if side == "short":
                        pnl_pct = -pnl_pct
                else:
                    pnl_pct = 0
                
                positions.append(Position(
                    trade_id=str(trade_id),
                    symbol=symbol,
                    side=side,
                    size=float(size),
                    entry_price=float(entry_price) if entry_price else 0,
                    current_price=float(current_price) if current_price else 0,
                    unrealized_pnl=float(unrealized_pnl) if unrealized_pnl else 0,
                    unrealized_pnl_percentage=pnl_pct,
                    stop_loss=float(stop_loss) if stop_loss else None,
                    take_profit=float(take_profit) if take_profit else None,
                    duration=duration,
                    decision_id=str(decision_id) if decision_id else None
                ))
            
            # Calculate total unrealized PnL
            total_pnl = sum(p.unrealized_pnl for p in positions)
            
    return {
        "positions": positions,
        "total_positions": len(positions),
        "total_unrealized_pnl": total_pnl
    }


@app.get("/api/dashboard/{user_id}/trades")
async def get_current_trades(user_id: str):
    """Get current trades via trade lifecycle system."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    trade_id,
                    symbol,
                    side,
                    trade_status,
                    size_contracts,
                    entry_price,
                    COALESCE(mark_price, entry_price) as mark_price,
                    unrealized_pnl,
                    opened_at,
                    closed_at,
                    last_updated
                FROM trades
                WHERE user_id = %s
                ORDER BY opened_at DESC
            """, (user_id,))
            
            results = cur.fetchall()
            trades = []
            
            for row in results:
                (trade_id, symbol, side, trade_status, size_contracts, 
                 entry_price, mark_price, unrealized_pnl, 
                 opened_at, closed_at, last_updated) = row
                
                trades.append({
                    "trade_id": str(trade_id),
                    "symbol": symbol,
                    "side": side,
                    "trade_status": trade_status,
                    "size_contracts": float(size_contracts) if size_contracts else 0,
                    "entry_price": float(entry_price) if entry_price else 0,
                    "mark_price": float(mark_price) if mark_price else 0,
                    "unrealized_pnl": float(unrealized_pnl) if unrealized_pnl else 0,
                    "opened_at": opened_at.isoformat() + "Z" if opened_at else None,
                    "closed_at": closed_at.isoformat() + "Z" if closed_at else None,
                    "last_updated": last_updated.isoformat() + "Z" if last_updated else None
                })
            
    return {
        "trades": trades,
        "total_trades": len(trades)
    }


@app.get("/api/dashboard/{user_id}/performance")
async def get_performance_metrics(user_id: str, period: str = "7d"):
    """Get performance metrics for a user."""
    # Parse period
    period_days = {
        "1d": 1,
        "7d": 7,
        "30d": 30,
        "all": 9999
    }.get(period, 7)
    
    start_date = datetime.utcnow() - timedelta(days=period_days)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get closed trades for the period
            cur.execute("""
                SELECT 
                    realized_pnl,
                    closed_at::date as date
                FROM trades
                WHERE user_id = %s
                  AND trade_status = 'closed'
                  AND closed_at >= %s
                ORDER BY closed_at
            """, (user_id, start_date))
            
            trades = cur.fetchall()
            
            # Calculate metrics
            total_pnl = 0
            winning_trades = 0
            losing_trades = 0
            total_win = 0
            total_loss = 0
            daily_pnl_dict = {}
            
            for pnl, date in trades:
                if pnl:
                    pnl_float = float(pnl)
                    total_pnl += pnl_float
                    
                    if pnl_float > 0:
                        winning_trades += 1
                        total_win += pnl_float
                    else:
                        losing_trades += 1
                        total_loss += abs(pnl_float)
                    
                    # Aggregate daily PnL
                    date_str = date.isoformat()
                    if date_str not in daily_pnl_dict:
                        daily_pnl_dict[date_str] = {"pnl": 0, "trades": 0}
                    daily_pnl_dict[date_str]["pnl"] += pnl_float
                    daily_pnl_dict[date_str]["trades"] += 1
            
            total_trades = winning_trades + losing_trades
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            avg_win = total_win / winning_trades if winning_trades > 0 else 0
            avg_loss = -total_loss / losing_trades if losing_trades > 0 else 0
            profit_factor = total_win / total_loss if total_loss > 0 else 0
            
            # Get account balance for percentage calculation
            cur.execute("""
                SELECT total_equity
                FROM account_monitoring
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id,))
            
            equity_result = cur.fetchone()
            total_equity = float(equity_result[0]) if equity_result else 10000  # Default
            total_pnl_pct = (total_pnl / total_equity) * 100 if total_equity > 0 else 0
            
            # Calculate max drawdown
            cur.execute("""
                SELECT MIN(total_equity) as min_equity, MAX(total_equity) as max_equity
                FROM account_monitoring
                WHERE user_id = %s AND timestamp >= %s
            """, (user_id, start_date))
            
            drawdown_result = cur.fetchone()
            if drawdown_result and drawdown_result[0] and drawdown_result[1]:
                max_drawdown = ((float(drawdown_result[1]) - float(drawdown_result[0])) / 
                               float(drawdown_result[1])) * 100
            else:
                max_drawdown = 0
            
            # Convert daily PnL to list
            daily_pnl = [
                {"date": date, "pnl": data["pnl"], "trades": data["trades"]}
                for date, data in sorted(daily_pnl_dict.items())
            ]
    
    return PerformanceMetrics(
        period=period,
        metrics={
            "total_pnl": total_pnl,
            "total_pnl_percentage": total_pnl_pct,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": 0  # TODO: Calculate Sharpe ratio
        },
        daily_pnl=daily_pnl
    )


@app.get("/api/agent/{user_id}/status")
async def get_agent_status(user_id: str):
    """Get the status of all modules for a user's agent."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get last run times for each module
            modules_status = {}
            
            # Extraction status
            cur.execute("""
                SELECT created_at
                FROM market_data
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            extraction_result = cur.fetchone()
            if extraction_result:
                last_extraction = extraction_result[0]
                # Calculate next run (assuming 15m intervals)
                next_extraction = last_extraction + timedelta(minutes=15)
                extraction_status = "running" if datetime.utcnow() < next_extraction else "idle"
            else:
                last_extraction = None
                next_extraction = None
                extraction_status = "stopped"
            
            modules_status["extraction"] = {
                "status": extraction_status,
                "last_run": last_extraction.isoformat() + "Z" if last_extraction else None,
                "next_run": next_extraction.isoformat() + "Z" if next_extraction else None,
                "errors": 0  # TODO: Track errors
            }
            
            # Decision status
            cur.execute("""
                SELECT created_at, state_data->>'mode' as mode
                FROM account_states
                WHERE user_id = %s
                  AND state_data->>'type' = 'decision'
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            decision_result = cur.fetchone()
            if decision_result:
                last_decision, mode = decision_result
                decision_status = "running"
            else:
                last_decision = None
                mode = None
                decision_status = "stopped"
            
            modules_status["decision"] = {
                "status": decision_status,
                "last_run": last_decision.isoformat() + "Z" if last_decision else None,
                "mode": mode,
                "errors": 0
            }
            
            # Trading status
            cur.execute("""
                SELECT COUNT(*)
                FROM trades
                WHERE user_id = %s AND trade_status = 'open'
            """, (user_id,))
            
            active_positions = cur.fetchone()[0]
            
            cur.execute("""
                SELECT opened_at as created_at
                FROM trades
                WHERE user_id = %s
                ORDER BY opened_at DESC
                LIMIT 1
            """, (user_id,))
            
            last_trade_result = cur.fetchone()
            last_execution = last_trade_result[0] if last_trade_result else None
            
            modules_status["trading"] = {
                "status": "running" if active_positions > 0 else "idle",
                "active_positions": active_positions,
                "last_execution": last_execution.isoformat() + "Z" if last_execution else None
            }
            
            # Monitoring status
            cur.execute("""
                SELECT timestamp
                FROM account_monitoring
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id,))
            
            monitoring_result = cur.fetchone()
            last_update = monitoring_result[0] if monitoring_result else None
            monitoring_status = "running" if last_update and (
                datetime.utcnow() - last_update).seconds < 600 else "stopped"
            
            modules_status["monitoring"] = {
                "status": monitoring_status,
                "last_update": last_update.isoformat() + "Z" if last_update else None
            }
            
            # Overall status
            all_statuses = [m["status"] for m in modules_status.values()]
            if all(s == "stopped" for s in all_statuses):
                overall_status = "stopped"
            elif any(s == "running" for s in all_statuses):
                overall_status = "running"
            else:
                overall_status = "idle"
    
    return AgentStatus(
        overall_status=overall_status,
        modules=modules_status
    )


@app.websocket("/ws/dashboard/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time dashboard updates."""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Wait for any message from client (heartbeat)
            data = await websocket.receive_text()
            
            # Send current positions update
            positions = await get_current_positions(user_id)
            await manager.broadcast_to_user(user_id, {
                "type": "position_update",
                "data": positions
            })
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "dashboard-api",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "websocket_connections": len(manager.active_connections)
    }


# Background task to push updates to connected clients
async def push_updates():
    """Push updates to connected WebSocket clients."""
    while True:
        await asyncio.sleep(30)  # Update every 30 seconds
        
        # Only process if there are active connections
        if manager.active_connections:
            logger.info(f"Pushing updates to {len(manager.active_connections)} active connections")
            
            for user_id in list(manager.active_connections.keys()):
                try:
                    # Get latest positions
                    positions = await get_current_positions(user_id)
                    
                    # Send update
                    await manager.broadcast_to_user(user_id, {
                        "type": "position_update",
                        "data": positions
                    })
                except Exception as e:
                    logger.error(f"Error pushing update to {user_id}: {e}")


@app.on_event("startup")
async def startup_event():
    """Start background update task."""
    asyncio.create_task(push_updates())


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("DASHBOARD_API_PORT", "5003"))
    host = os.environ.get("DASHBOARD_API_HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)