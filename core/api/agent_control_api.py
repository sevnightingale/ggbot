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
from core.config.config_main import get_configuration
from core.common.db import get_db_connection
import json
from pathlib import Path

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
    # Use the default config_id we've been using
    default_config_id = "a93de31b-9b8a-42e3-827d-c31e580f5f36"
    
    config = get_configuration(user_id, config_type=module, config_id=default_config_id)
    
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
        
        # Update configuration in database using the default config_id
        default_config_id = "a93de31b-9b8a-42e3-827d-c31e580f5f36"
        
        # Get current unified config from database
        current_unified_config = get_configuration(user_id, config_id=default_config_id)
        
        if not current_unified_config:
            raise HTTPException(status_code=404, detail="Base configuration not found")
        
        # Update the specific module section
        current_unified_config[module] = request.config
        
        # Save updated unified config back to database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE configurations 
                    SET config_data = %s, updated_at = NOW() 
                    WHERE config_id = %s
                """, (json.dumps(current_unified_config), default_config_id))
                conn.commit()
        
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


@app.post("/api/scheduler/start")
async def start_scheduler():
    """Start autonomous trading scheduler."""
    try:
        from core.scheduling.scheduler import get_scheduler
        scheduler = get_scheduler()
        result = scheduler.start_autonomous_mode()
        
        logger.info("🚀 Scheduler start requested via API", result=result)
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/stop")
async def stop_scheduler():
    """Stop autonomous trading scheduler."""
    try:
        from core.scheduling.scheduler import get_scheduler
        scheduler = get_scheduler()
        result = scheduler.stop_autonomous_mode()
        
        logger.info("🛑 Scheduler stop requested via API", result=result)
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to stop scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get current scheduler status."""
    try:
        from core.scheduling.scheduler import get_scheduler
        scheduler = get_scheduler()
        result = scheduler.get_status()
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Bot Control Endpoints for config_instances management

@app.get("/api/bots")
async def get_all_bots():
    """Get all bot configurations with status."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        ci.config_id,
                        ci.instance_name,
                        ci.status as instance_status,
                        c.config_name,
                        c.config_type,
                        c.user_id,
                        ci.hummingbot_account,
                        ci.paper_balance_usd,
                        ci.created_at,
                        c.updated_at
                    FROM config_instances ci
                    JOIN configurations c ON ci.config_id = c.config_id
                    ORDER BY c.config_type, ci.instance_name
                """)
                
                bots = []
                for row in cur.fetchall():
                    (config_id, instance_name, instance_status, config_name, config_type,
                     user_id, hummingbot_account, paper_balance_usd, created_at, updated_at) = row
                     
                    bots.append({
                        "config_id": config_id,
                        "instance_name": instance_name,
                        "status": instance_status,
                        "config_name": config_name,
                        "config_type": config_type,
                        "user_id": user_id,
                        "hummingbot_account": hummingbot_account,
                        "paper_balance_usd": float(paper_balance_usd) if paper_balance_usd else 0,
                        "created_at": created_at.isoformat() + "Z" if created_at else None,
                        "updated_at": updated_at.isoformat() + "Z" if updated_at else None
                    })
                
                return {
                    "bots": bots,
                    "total_count": len(bots),
                    "active_count": len([b for b in bots if b["status"] == "active"]),
                    "inactive_count": len([b for b in bots if b["status"] == "inactive"])
                }
                
    except Exception as e:
        logger.error(f"Failed to get bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bots/{config_id}/start")
async def start_bot(config_id: str):
    """Start (activate) a specific bot configuration."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if bot exists
                cur.execute("""
                    SELECT ci.config_id, ci.instance_name, ci.status, c.config_name, c.config_type
                    FROM config_instances ci
                    JOIN configurations c ON ci.config_id = c.config_id
                    WHERE ci.config_id = %s
                """, (config_id,))
                
                bot = cur.fetchone()
                if not bot:
                    raise HTTPException(status_code=404, detail="Bot not found")
                
                config_id_db, instance_name, current_status, config_name, config_type = bot
                
                if current_status == "active":
                    return {
                        "status": "already_active",
                        "config_id": config_id,
                        "message": f"Bot {instance_name or config_name} is already active"
                    }
                
                # Update status to active
                cur.execute("""
                    UPDATE config_instances 
                    SET status = 'active'
                    WHERE config_id = %s
                """, (config_id,))
                conn.commit()
                
                logger.info(f"🚀 Started bot {config_id}: {instance_name or config_name}")
                
                return {
                    "status": "started",
                    "config_id": config_id,
                    "bot_name": instance_name or config_name,
                    "bot_type": config_type,
                    "message": f"Bot {instance_name or config_name} started successfully"
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start bot {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bots/{config_id}/stop")
async def stop_bot(config_id: str):
    """Stop (deactivate) a specific bot configuration."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if bot exists
                cur.execute("""
                    SELECT ci.config_id, ci.instance_name, ci.status, c.config_name, c.config_type
                    FROM config_instances ci
                    JOIN configurations c ON ci.config_id = c.config_id
                    WHERE ci.config_id = %s
                """, (config_id,))
                
                bot = cur.fetchone()
                if not bot:
                    raise HTTPException(status_code=404, detail="Bot not found")
                
                config_id_db, instance_name, current_status, config_name, config_type = bot
                
                if current_status == "inactive":
                    return {
                        "status": "already_inactive",
                        "config_id": config_id,
                        "message": f"Bot {instance_name or config_name} is already inactive"
                    }
                
                # Update status to inactive
                cur.execute("""
                    UPDATE config_instances 
                    SET status = 'inactive'
                    WHERE config_id = %s
                """, (config_id,))
                conn.commit()
                
                logger.info(f"🛑 Stopped bot {config_id}: {instance_name or config_name}")
                
                return {
                    "status": "stopped",
                    "config_id": config_id,
                    "bot_name": instance_name or config_name,
                    "bot_type": config_type,
                    "message": f"Bot {instance_name or config_name} stopped successfully"
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop bot {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bots/{config_id}/status")
async def get_bot_status(config_id: str):
    """Get detailed status for a specific bot."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get bot info
                cur.execute("""
                    SELECT 
                        ci.config_id,
                        ci.instance_name,
                        ci.status,
                        c.config_name,
                        c.config_type,
                        c.user_id,
                        c.updated_at
                    FROM config_instances ci
                    JOIN configurations c ON ci.config_id = c.config_id
                    WHERE ci.config_id = %s
                """, (config_id,))
                
                bot = cur.fetchone()
                if not bot:
                    raise HTTPException(status_code=404, detail="Bot not found")
                
                (config_id_db, instance_name, status, config_name, config_type,
                 user_id, updated_at) = bot
                 
                # Get recent activity based on bot type
                last_activity = None
                activity_type = None
                
                if config_type in ['decision', 'ggshot']:
                    # Check for recent market data or ggshot signals
                    cur.execute("""
                        SELECT updated_at, 'market_data' as type
                        FROM market_data 
                        WHERE config_id = %s 
                        ORDER BY updated_at DESC 
                        LIMIT 1
                    """, (config_id,))
                    
                    result = cur.fetchone()
                    if result:
                        last_activity, activity_type = result
                
                return {
                    "config_id": config_id,
                    "bot_name": instance_name or config_name,
                    "bot_type": config_type,
                    "status": status,
                    "user_id": user_id,
                    "last_updated": updated_at.isoformat() + "Z" if updated_at else None,
                    "last_activity": last_activity.isoformat() + "Z" if last_activity else None,
                    "activity_type": activity_type
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bot status for {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Count total running processes
    total_processes = sum(
        len(procs) for procs in active_processes.values()
    )
    
    # Get scheduler status
    scheduler_status = "unknown"
    try:
        from core.scheduling.scheduler import get_scheduler
        scheduler = get_scheduler()
        status = scheduler.get_status()
        scheduler_status = status.get("scheduler", {}).get("autonomous_mode", "unknown")
    except:
        pass
    
    return {
        "status": "healthy",
        "service": "agent-control-api",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "active_users": len(active_processes),
        "total_processes": total_processes,
        "scheduler_status": scheduler_status
    }


# Cleanup terminated processes periodically
async def cleanup_processes():
    """Remove terminated processes from tracking."""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes (reduced frequency)
        
        # Only process if there are active processes
        if active_processes:
            logger.info(f"Cleaning up processes for {len(active_processes)} users")
            
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