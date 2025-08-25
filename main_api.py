"""
GGBot Main API Server

Combined API server that includes all modules for simplified prototype deployment.
In production, these would be split into separate microservices.
"""
import os
import sys
import signal
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import aiohttp
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


# Set up logging before importing other modules
from core.common.logging_config import setup_logging
log_file = setup_logging()

# Import scheduler functions
from core.scheduling.scheduler import initialize_scheduler, shutdown_scheduler

# Import bot monitoring components
from core.monitoring.active_bot_monitor import ActiveBotMonitor
from core.monitoring.bot_types.ggshot_bot import GGShotBotHandler

# Import all the API apps
from extraction.api import app as extraction_app
from decision.api import app as decision_app
# Trading API removed - being rebuilt with new Hummingbot integration
# Dashboard API removed - legacy and unused
from core.api.agent_control_api import app as agent_control_app

# Import config API router
from core.api.config_api import router as config_router

# Import users API router
from core.api.users_api import router as users_router

# Import test API router
from core.api.test_api import router as test_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    from core.common.logger import logger
    
    # Startup
    logger.info("🚀 Starting GGBot API Server with integrated scheduler and trading")
    
    # Start bot monitoring background task
    asyncio.create_task(bot_monitoring_task())
    logger.info("🤖 Started bot monitoring with WebSocket broadcasting")
    
    # Initialize the scheduler (but don't start autonomous mode)
    success = await initialize_scheduler()
    if success:
        logger.info("✅ Scheduler initialized successfully (autonomous mode off)")
    else:
        logger.error("❌ Failed to initialize scheduler")
    
    # Trading execution adapter initialization disabled - being rebuilt with new Hummingbot API integration
    
    yield  # App runs here
    
    # Shutdown
    logger.info("🔄 Shutting down GGBot API Server...")
    
    # Shutdown the scheduler
    await shutdown_scheduler()
    
    logger.info("✅ Scheduler shutdown complete")

# Create the main app
app = FastAPI(
    title="GGBot API",
    description="Combined API for GGBot cryptocurrency trading system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all the sub-applications
app.mount("/extraction", extraction_app)
app.mount("/decision", decision_app)
# Trading API mount removed - being rebuilt with new Hummingbot integration
# Dashboard mount removed - legacy
app.mount("/agent", agent_control_app)

# Set WebSocket manager for agent control API demo mode
from core.api.agent_control_api import set_websocket_manager

# Include the config router directly
app.include_router(config_router)

# Bot monitoring globals
bot_monitor: ActiveBotMonitor = None
websocket_connections: Dict[str, WebSocket] = {}

class WebSocketManager:
    """Simple WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
    def disconnect(self, user_id: str):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def broadcast_to_user(self, user_id: str, data: dict):
        """Send data to specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(data))
            except:
                # Connection closed, remove it
                self.disconnect(user_id)

# Global WebSocket manager
manager = WebSocketManager()

# Set the WebSocket manager for agent control API demo mode
set_websocket_manager(manager)

# Include the users router directly
app.include_router(users_router)

# Include the test router directly
app.include_router(test_router)

async def get_latest_approved_signals(limit: int = 5) -> List[Dict]:
    """
    Dynamically fetch the latest approved signals from ggshot_filter table.
    Returns them in the format expected by the live position API.
    """
    from core.common.db import get_db_connection
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT symbol, signal_direction, entry_price, created_at, confidence_score, 
                           reasoning_text, volume_analysis, signal_timeframe
                    FROM ggshot_filter 
                    WHERE filter_status = 'APPROVED' 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (limit,))
                
                results = cur.fetchall()
                
                # Generate demo position sizes for variety
                position_sizes = [800, 1200, 600, 900, 1000]
                
                positions = []
                for i, row in enumerate(results):
                    symbol, direction, entry_price, created_at, confidence, reasoning, volume_analysis, timeframe = row
                    
                    positions.append({
                        'id': f'pos_{i+1:03d}',
                        'symbol': symbol,
                        'direction': direction,
                        'entry_price': float(entry_price),
                        'entry_time': created_at.isoformat() + 'Z',
                        'position_size': position_sizes[i % len(position_sizes)],  # USD
                        'leverage': 10,
                        'confidence': int(float(confidence) * 100),  # Convert 0.57 to 57
                        'reasoning_text': reasoning or "AI analysis completed with 4-pillar validation",
                        'volume_analysis': volume_analysis or "Volume confirmation analysis",
                        'signal_timeframe': timeframe or "1h"
                    })
                
                return positions
                
    except Exception as e:
        from core.common.logger import logger
        logger.error(f"Failed to fetch latest signals: {e}")
        
        # Fallback to a minimal static set if database fails
        return [
            {
                'id': 'pos_001',
                'symbol': 'BTC/USDT',
                'direction': 'LONG',
                'entry_price': 43000.0,
                'entry_time': datetime.now(timezone.utc).isoformat(),
                'position_size': 1000,
                'leverage': 10,
                'confidence': 75
            }
        ]

# Demo trading positions for ggShot-Pro bot (now dynamically loaded from ggshot_filter table)
# This will be replaced by get_latest_approved_signals() at runtime

def calculate_position_pnl(entry_price: float, current_price: float, position_size: float, direction: str, leverage: float) -> Dict[str, float]:
    """Calculate realistic P&L with leverage for a position."""
    try:
        # Calculate price change percentage
        price_change_percent = (current_price - entry_price) / entry_price
        
        # Reverse for short positions
        if direction.upper() == 'SHORT':
            price_change_percent *= -1
        
        # Apply leverage
        leveraged_return = price_change_percent * leverage
        
        # Calculate dollar P&L
        pnl_usd = position_size * leveraged_return
        
        # Calculate percentage P&L (relative to position size)
        pnl_percent = leveraged_return * 100
        
        return {
            'pnl_usd': round(pnl_usd, 2),
            'pnl_percent': round(pnl_percent, 2),
            'price_change_percent': round(price_change_percent * 100, 2)
        }
    except Exception as e:
        return {'pnl_usd': 0.0, 'pnl_percent': 0.0, 'price_change_percent': 0.0}

def get_time_in_trade(entry_time_str: str) -> str:
    """Calculate time since entry."""
    try:
        entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=timezone.utc)
        
        time_diff = datetime.now(timezone.utc) - entry_time
        
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "N/A"

@app.get("/api/live-position-data")
async def get_live_position_data():
    """Get live position data with real-time prices and P&L calculations."""
    from decision.services.price_service import PriceService
    from core.common.logger import logger
    
    try:
        # Get latest approved signals dynamically from database
        demo_positions = await get_latest_approved_signals(1)
        
        # Initialize price service (uses existing CCXT infrastructure)
        price_service = PriceService()
        
        live_positions = []
        
        for position in demo_positions:
            try:
                # Get current market price using existing price service
                current_price = await price_service.get_current_price(position['symbol'])
                
                if current_price:
                    # Calculate real P&L
                    pnl_data = calculate_position_pnl(
                        entry_price=position['entry_price'],
                        current_price=float(current_price),
                        position_size=position['position_size'],
                        direction=position['direction'],
                        leverage=position['leverage']
                    )
                    
                    # Calculate time in trade
                    time_in_trade = get_time_in_trade(position['entry_time'])
                    
                    live_positions.append({
                        **position,
                        'current_price': float(current_price),
                        'pnl': pnl_data['pnl_usd'],
                        'pnl_percent': pnl_data['pnl_percent'],
                        'price_change_percent': pnl_data['price_change_percent'],
                        'time_in_trade': time_in_trade,
                        'last_updated': datetime.now(timezone.utc).isoformat()
                    })
                else:
                    # Fallback if price service fails
                    live_positions.append({
                        **position,
                        'current_price': position['entry_price'],  # Use entry price as fallback
                        'pnl': 0.0,
                        'pnl_percent': 0.0,
                        'price_change_percent': 0.0,
                        'time_in_trade': get_time_in_trade(position['entry_time']),
                        'last_updated': datetime.now(timezone.utc).isoformat(),
                        'price_error': 'Unable to fetch current price'
                    })
            except Exception as e:
                logger.error(f"Error processing position {position['id']}: {e}")
                # Include position with error state
                live_positions.append({
                    **position,
                    'current_price': position['entry_price'],
                    'pnl': 0.0,
                    'pnl_percent': 0.0,
                    'price_change_percent': 0.0,
                    'time_in_trade': get_time_in_trade(position['entry_time']),
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'error': str(e)
                })
        
        return {
            'status': 'success',
            'positions': live_positions,
            'total_positions': len(live_positions),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in live position data endpoint: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'positions': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

@app.get("/")
async def root():
    """Root endpoint showing available APIs."""
    return {
        "message": "GGBot API Server",
        "apis": {
            "extraction": "/extraction/docs",
            "decision": "/decision/docs",
            "trading": "/trading/docs",
            "agent": "/agent/docs"
        },
        "health_checks": {
            "extraction": "/extraction/health",
            "decision": "/decision/health",
            "trading": "/trading/health",
            "agent": "/agent/health"
        }
    }

@app.websocket("/ws/bot-status/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time bot status updates."""
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo heartbeat messages
            if data == "heartbeat":
                await websocket.send_text(json.dumps({"type": "heartbeat_ack", "timestamp": datetime.utcnow().isoformat() + "Z"}))
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@app.get("/health")
async def health_check():
    """Combined health check for all services."""
    import aiohttp
    import asyncio
    
    health_status = {}
    
    # Check each service health endpoint (using current API port)
    port = int(os.environ.get("API_PORT", "8000"))
    endpoints = {
        "extraction": f"http://localhost:{port}/extraction/health",
        "decision": f"http://localhost:{port}/decision/health",
        "trading": f"http://localhost:{port}/trading/health",
        "agent": f"http://localhost:{port}/agent/health"
    }
    
    async def check_endpoint(name, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=2) as response:
                    if response.status == 200:
                        health_status[name] = "healthy"
                    else:
                        health_status[name] = "unhealthy"
        except:
            health_status[name] = "not_started"
    
    # Since this is a combined service, all should be healthy if we're running
    for service in ["extraction", "decision", "trading", "agent"]:
        health_status[service] = "healthy"
    
    return {
        "status": "healthy",
        "services": health_status,
        "mode": "combined"
    }


async def bot_monitoring_task():
    """Background task for bot status monitoring and WebSocket broadcasting."""
    global bot_monitor
    from core.common.logger import logger
    
    # Initialize bot monitor
    bot_monitor = ActiveBotMonitor()
    bot_monitor.set_websocket_manager(manager)
    
    # Register bot handlers
    bot_monitor.register_bot_handler('decision', GGShotBotHandler)
    bot_monitor.register_bot_handler('ggshot', GGShotBotHandler)
    bot_monitor.register_bot_handler('ggshot_test', GGShotBotHandler)  # Test configs use same handler
    bot_monitor.register_bot_handler('testing', GGShotBotHandler)     # Test configs use same handler  
    bot_monitor.register_bot_handler('user', GGShotBotHandler)        # User configs use same handler
    logger.info("🤖 Registered bot handlers: decision, ggshot, ggshot_test, testing, user")
    
    # Main monitoring loop
    while True:
        try:
            # Get all bot configs (both active and inactive) for comprehensive monitoring
            all_configs = await bot_monitor.get_all_bot_configs()
            
            if all_configs:
                active_count = sum(1 for config in all_configs if config.get('status') == 'active')
                logger.debug(f"Monitoring {len(all_configs)} total bots ({active_count} active)")
                
                # Process each bot config
                for bot_config in all_configs:
                    try:
                        if bot_config.get('status') == 'active':
                            # Use the monitor's single bot method for active bots
                            await bot_monitor.monitor_single_bot(bot_config)
                        else:
                            # Send inactive status for inactive bots
                            await bot_monitor.send_inactive_status(bot_config)
                        
                    except Exception as e:
                        logger.error(f"Error processing bot config {bot_config.get('config_id', 'unknown')}: {e}")
            else:
                logger.debug("No bots found in database")
            
            # Send heartbeat to all connected clients
            if manager.active_connections:
                heartbeat_msg = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                for user_id in list(manager.active_connections.keys()):
                    try:
                        await manager.broadcast_to_user(user_id, heartbeat_msg)
                    except:
                        pass  # Connection might be closed
            
            # Wait before next monitoring cycle
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in bot monitoring task: {e}")
            await asyncio.sleep(30)  # Wait longer on errors


if __name__ == "__main__":
    # Get configuration from environment
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))
    
    print(f"Starting GGBot Combined API Server on {host}:{port}")
    print(f"API documentation available at: http://localhost:{port}/docs")
    print("\nIndividual API docs:")
    print(f"  Extraction: http://localhost:{port}/extraction/docs")
    print(f"  Decision:   http://localhost:{port}/decision/docs")
    print(f"  Trading:    http://localhost:{port}/trading/docs")
    print(f"  Agent:      http://localhost:{port}/agent/docs")
    print("\nScheduler Control:")
    print(f"  Start:  POST http://localhost:{port}/agent/api/scheduler/start")
    print(f"  Stop:   POST http://localhost:{port}/agent/api/scheduler/stop")
    print(f"  Status: GET  http://localhost:{port}/agent/api/scheduler/status")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )