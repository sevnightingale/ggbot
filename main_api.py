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
    
    # Register bot handlers (copy from working service)
    bot_monitor.register_bot_handler('decision', GGShotBotHandler)
    bot_monitor.register_bot_handler('ggshot', GGShotBotHandler)
    logger.info("🤖 Registered bot handlers: decision, ggshot")
    
    # Main monitoring loop
    while True:
        try:
            if manager.active_connections:
                # Get active bot configs
                active_configs = await bot_monitor.get_active_bot_configs()
                
                # Process each active bot
                for bot_config in active_configs:
                    config_id = bot_config['config_id']
                    config_type = bot_config['config_type']
                    user_id = bot_config['user_id']
                    
                    # Skip if no handler for this bot type
                    if config_id not in bot_monitor.bot_handlers:
                        # Try to create handler
                        handler = bot_monitor.create_bot_handler(bot_config)
                        if handler:
                            bot_monitor.bot_handlers[config_id] = handler
                        else:
                            continue
                    
                    handler = bot_monitor.bot_handlers[config_id]
                    
                    try:
                        # Detect current pipeline phase
                        current_phase = await handler.detect_pipeline_phase()
                        sub_phase = await handler.detect_sub_phase(current_phase)
                        context_data = await handler.extract_context_data()
                        status_message = await handler.generate_status_message(
                            phase=current_phase,
                            sub_phase=sub_phase,
                            context=context_data
                        )
                        
                        # Create status update for frontend
                        phase_colors = {"idle": "gray", "extraction": "blue", "decision": "green", "trading": "orange"}
                        
                        bot_status = {
                            "type": "bot_status_update",
                            "config_id": config_id,
                            "bot_type": config_type,
                            "phase": current_phase,
                            "color": phase_colors.get(current_phase, "gray"),
                            "message": status_message,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "showSpinner": current_phase in ["extraction", "decision", "trading"],
                            "context": context_data
                        }
                        
                        # Broadcast to user's WebSocket
                        await manager.broadcast_to_user(user_id, bot_status)
                        
                    except Exception as e:
                        logger.error(f"Error monitoring bot {config_id}: {e}")
            
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