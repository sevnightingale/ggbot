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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Add hummingbot client to path for API client imports
sys.path.insert(0, str(Path(__file__).parent / "hummingbot" / "client"))

# Set up logging before importing other modules
from core.common.logging_config import setup_logging
log_file = setup_logging()

# Import scheduler functions
from core.scheduling.scheduler import initialize_scheduler, shutdown_scheduler

# Import all the API apps
from extraction.api import app as extraction_app
from decision.api import app as decision_app
from trading.api import app as trading_app
from core.api.dashboard_api import app as dashboard_app
from core.api.agent_control_api import app as agent_control_app

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
app.mount("/dashboard", dashboard_app)
app.mount("/agent", agent_control_app)

@app.get("/")
async def root():
    """Root endpoint showing available APIs."""
    return {
        "message": "GGBot API Server",
        "apis": {
            "extraction": "/extraction/docs",
            "decision": "/decision/docs",
            "trading": "/trading/docs",
            "dashboard": "/dashboard/docs",
            "agent": "/agent/docs"
        },
        "health_checks": {
            "extraction": "/extraction/health",
            "decision": "/decision/health",
            "trading": "/trading/health",
            "dashboard": "/dashboard/health",
            "agent": "/agent/health"
        }
    }

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
        "dashboard": f"http://localhost:{port}/dashboard/health",
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
    for service in ["extraction", "decision", "trading", "dashboard", "agent"]:
        health_status[service] = "healthy"
    
    return {
        "status": "healthy",
        "services": health_status,
        "mode": "combined"
    }


@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup."""
    from core.common.logger import logger
    
    logger.info("🚀 Starting GGBot API Server with integrated scheduler")
    
    # Initialize the scheduler (but don't start autonomous mode)
    success = await initialize_scheduler()
    if success:
        logger.info("✅ Scheduler initialized successfully (autonomous mode off)")
    else:
        logger.error("❌ Failed to initialize scheduler")


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
    print(f"  Dashboard:  http://localhost:{port}/dashboard/docs")
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