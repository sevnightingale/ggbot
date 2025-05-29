"""
Agent Control API

Provides REST endpoints for controlling the trading bot including
starting/stopping modules and managing configurations.
"""
import os
import asyncio
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.config.config_main import get_configuration, save_configuration
from core.common.db import get_db_connection

app = FastAPI(title="Agent Control API", version="1.0.0")

# Global process tracking
active_processes: Dict[str, Dict[str, subprocess.Popen]] = {}


class StartRequest(BaseModel):
    modules: List[str] = ["all"]  # ["extraction", "decision", "trading", "monitoring"]


class StopRequest(BaseModel):
    modules: List[str] = ["all"]
    close_positions: bool = False


class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]


def is_module_running(user_id: str, module: str) -> bool:
    """Check if a module is running for a user."""
    return (user_id in active_processes and 
            module in active_processes[user_id] and
            active_processes[user_id][module].poll() is None)


async def start_module(user_id: str, module: str):
    """Start a specific module for a user."""
    if is_module_running(user_id, module):
        logger.info(f"Module {module} already running for user {user_id}")
        return
    
    # Initialize user process dict if needed
    if user_id not in active_processes:
        active_processes[user_id] = {}
    
    # Module-specific start commands
    if module == "extraction":
        # Start extraction scheduler
        cmd = [
            "python", "-m", "extraction.scheduled_extraction",
            "--user-id", user_id,
            "--continuous"
        ]
    elif module == "decision":
        # Start decision scheduler
        cmd = [
            "python", "-m", "decision.scheduled_decision",
            "--user-id", user_id,
            "--continuous"
        ]
    elif module == "trading":
        # Trading is started via API, just ensure API is running
        return  # Trading API handles its own lifecycle
    elif module == "monitoring":
        # Start monitoring service
        cmd = [
            "python", "-m", "core.monitoring.service",
            "--user-id", user_id
        ]
    else:
        raise ValueError(f"Unknown module: {module}")
    
    # Start the process
    env = os.environ.copy()
    env["USER_ID"] = user_id
    
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    active_processes[user_id][module] = process
    logger.info(f"Started {module} for user {user_id} (PID: {process.pid})")


async def stop_module(user_id: str, module: str):
    """Stop a specific module for a user."""
    if not is_module_running(user_id, module):
        logger.info(f"Module {module} not running for user {user_id}")
        return
    
    process = active_processes[user_id][module]
    process.terminate()
    
    # Wait for graceful shutdown
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        logger.warning(f"Force killing {module} for user {user_id}")
        process.kill()
    
    del active_processes[user_id][module]
    logger.info(f"Stopped {module} for user {user_id}")


@app.post("/api/agent/{user_id}/start")
async def start_agent(
    user_id: str,
    request: StartRequest,
    background_tasks: BackgroundTasks
):
    """Start the trading bot for a user."""
    modules_to_start = request.modules
    
    if "all" in modules_to_start:
        modules_to_start = ["extraction", "decision", "monitoring"]
    
    started_modules = []
    
    for module in modules_to_start:
        try:
            await start_module(user_id, module)
            started_modules.append(module)
        except Exception as e:
            logger.error(f"Failed to start {module}: {e}")
    
    return {
        "status": "started",
        "modules_started": started_modules,
        "message": f"Started {len(started_modules)} modules"
    }


@app.post("/api/agent/{user_id}/stop")
async def stop_agent(
    user_id: str,
    request: StopRequest
):
    """Stop the trading bot for a user."""
    modules_to_stop = request.modules
    
    if "all" in modules_to_stop:
        modules_to_stop = list(active_processes.get(user_id, {}).keys())
    
    stopped_modules = []
    
    # Close positions if requested
    if request.close_positions:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM trades
                    WHERE user_id = %s AND trade_status = 'open'
                """, (user_id,))
                open_positions = cur.fetchone()[0]
                
                if open_positions > 0:
                    # TODO: Implement position closing via Trading API
                    logger.warning(f"User {user_id} has {open_positions} open positions")
    
    for module in modules_to_stop:
        try:
            await stop_module(user_id, module)
            stopped_modules.append(module)
        except Exception as e:
            logger.error(f"Failed to stop {module}: {e}")
    
    # Check for open positions
    open_positions = 0
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM trades
                WHERE user_id = %s AND trade_status = 'open'
            """, (user_id,))
            open_positions = cur.fetchone()[0]
    
    return {
        "status": "stopped",
        "modules_stopped": stopped_modules,
        "open_positions": open_positions,
        "message": f"Stopped {len(stopped_modules)} modules"
    }


@app.post("/api/agent/{user_id}/pause")
async def pause_agent(user_id: str):
    """Pause trading (stop decision module but keep monitoring)."""
    try:
        await stop_module(user_id, "decision")
        
        # Get active positions count
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM trades
                    WHERE user_id = %s AND trade_status = 'open'
                """, (user_id,))
                active_positions = cur.fetchone()[0]
        
        return {
            "status": "paused",
            "active_positions": active_positions,
            "message": "Trading paused, monitoring continues"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/{user_id}/resume")
async def resume_agent(user_id: str, background_tasks: BackgroundTasks):
    """Resume trading (restart decision module)."""
    try:
        await start_module(user_id, "decision")
        
        return {
            "status": "resumed",
            "message": "Trading resumed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/{user_id}/{module}")
async def get_configuration_endpoint(user_id: str, module: str):
    """Get configuration for a specific module."""
    config = get_configuration(user_id, module)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return {
        "module": module,
        "config": config,
        "last_updated": datetime.utcnow().isoformat() + "Z"  # TODO: Track update time
    }


@app.put("/api/config/{user_id}/{module}")
async def update_configuration(
    user_id: str,
    module: str,
    request: ConfigUpdateRequest
):
    """Update configuration for a specific module."""
    try:
        # Validate module name
        if module not in ["extraction", "decision", "trading"]:
            raise HTTPException(status_code=400, detail="Invalid module name")
        
        # Save configuration
        save_configuration(user_id, module, request.config)
        
        # If module is running, it will pick up changes on next cycle
        module_running = is_module_running(user_id, module)
        
        return {
            "status": "updated",
            "module": module,
            "config": request.config,
            "message": f"Configuration updated. Module {'will reload on next cycle' if module_running else 'is not running'}"
        }
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Count total running processes
    total_processes = sum(
        len(procs) for procs in active_processes.values()
    )
    
    return {
        "status": "healthy",
        "service": "agent-control-api",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "active_users": len(active_processes),
        "total_processes": total_processes
    }


# Cleanup terminated processes periodically
async def cleanup_processes():
    """Remove terminated processes from tracking."""
    while True:
        await asyncio.sleep(60)  # Check every minute
        
        for user_id in list(active_processes.keys()):
            for module in list(active_processes[user_id].keys()):
                process = active_processes[user_id][module]
                if process.poll() is not None:
                    # Process has terminated
                    del active_processes[user_id][module]
                    logger.warning(f"Cleaned up terminated {module} for user {user_id}")
            
            # Remove user if no processes
            if not active_processes[user_id]:
                del active_processes[user_id]


@app.on_event("startup")
async def startup_event():
    """Start background cleanup task."""
    asyncio.create_task(cleanup_processes())


@app.on_event("shutdown")
async def shutdown_event():
    """Stop all processes on shutdown."""
    logger.info("Shutting down Agent Control API, stopping all processes...")
    
    for user_id in list(active_processes.keys()):
        for module in list(active_processes[user_id].keys()):
            try:
                await stop_module(user_id, module)
            except Exception as e:
                logger.error(f"Error stopping {module} for {user_id}: {e}")


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("AGENT_CONTROL_API_PORT", "5004"))
    host = os.environ.get("AGENT_CONTROL_API_HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)