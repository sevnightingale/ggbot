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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import aiohttp
import json
from typing import Dict, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Add hummingbot client to path for API client imports
sys.path.insert(0, str(Path(__file__).parent / "hummingbot" / "client"))

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
from trading.api import app as trading_app
# Dashboard API removed - legacy and unused
from core.api.agent_control_api import app as agent_control_app

# Import config API router
from core.api.config_api import router as config_router

# Import users API router
from core.api.users_api import router as users_router

# Import test API router
from core.api.test_api import router as test_router

# Create the main app
app = FastAPI(
    title="GGBot API",
    description="Combined API for GGBot cryptocurrency trading system",
    version="1.0.0"
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
app.mount("/trading", trading_app)
# Dashboard mount removed - legacy
app.mount("/agent", agent_control_app)

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

# Include the users router directly
app.include_router(users_router)

# Include the test router directly
app.include_router(test_router)

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
    logger.info("🤖 Registered bot handlers: decision, ggshot")
    
    # Main monitoring loop
    while True:
        try:
            # Get active bot configs
            active_configs = await bot_monitor.get_active_bot_configs()
            
            if active_configs:
                logger.debug(f"Monitoring {len(active_configs)} active bots")
                
                # Process each active bot using the proper monitor method
                for bot_config in active_configs:
                    try:
                        # Use the monitor's single bot method
                        await bot_monitor.monitor_single_bot(bot_config)
                        
                    except Exception as e:
                        logger.error(f"Error processing bot config {bot_config.get('config_id', 'unknown')}: {e}")
            else:
                logger.debug("No active bots to monitor")
            
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

@app.on_event("startup")
async def startup_event():
    """Initialize scheduler and trading execution adapter on startup."""
    from core.common.logger import logger
    
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
    
    # Initialize the trading execution adapter since mounted apps don't trigger lifespan events
    try:
        from trading.services.hummingbot_execution_adapter import HummingbotExecutionAdapter
        import trading.api as trading_module
        
        logger.info("🔧 Initializing HummingbotExecutionAdapter...")
        trading_module.execution_adapter = HummingbotExecutionAdapter()
        logger.info("✅ HummingbotExecutionAdapter initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize HummingbotExecutionAdapter: {e}")
        # Don't fail startup if trading adapter fails, just log the error


@app.on_event("shutdown") 
async def shutdown_event():
    """Gracefully shutdown scheduler on API shutdown."""
    from core.common.logger import logger
    
    logger.info("🔄 Shutting down GGBot API Server...")
    
    # Shutdown the scheduler
    await shutdown_scheduler()
    
    logger.info("✅ Scheduler shutdown complete")

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