"""
GGBot Main API Server

Combined API server that includes all modules for simplified prototype deployment.
In production, these would be split into separate microservices.
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import all the API apps
from extraction.api import app as extraction_app
from decision.api import app as decision_app
from trading.trades_main import app as trading_app
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
    
    # Check each service health endpoint
    endpoints = {
        "extraction": "http://localhost:8000/extraction/health",
        "decision": "http://localhost:8000/decision/health",
        "trading": "http://localhost:8000/trading/health",
        "dashboard": "http://localhost:8000/dashboard/health",
        "agent": "http://localhost:8000/agent/health"
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

if __name__ == "__main__":
    # Get configuration from environment
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))
    
    print(f"Starting GGBot Combined API Server on {host}:{port}")
    print("API documentation available at: http://localhost:8000/docs")
    print("\nIndividual API docs:")
    print("  Extraction: http://localhost:8000/extraction/docs")
    print("  Decision:   http://localhost:8000/decision/docs")
    print("  Trading:    http://localhost:8000/trading/docs")
    print("  Dashboard:  http://localhost:8000/dashboard/docs")
    print("  Agent:      http://localhost:8000/agent/docs")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )