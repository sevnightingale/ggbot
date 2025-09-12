"""
Bot Execution Status Management

Provides functions for tracking and updating bot execution status for SSE streaming.
Replaces complex WebSocket message broadcasting with simple database operations.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from core.common.db import get_db_connection
from core.common.logger import logger


async def set_bot_execution_status(
    config_id: str, 
    phase: str, 
    message: str, 
    progress: int = 0
) -> None:
    """
    Update bot execution status in database.
    
    Args:
        config_id: Bot configuration ID
        phase: Execution phase ('idle', 'extracting', 'deciding', 'trading', 'completed', 'error')
        message: Status message for user display
        progress: Progress percentage (0-100)
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO bot_execution_status (config_id, phase, message, progress, updated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (config_id) 
                    DO UPDATE SET 
                        phase = EXCLUDED.phase,
                        message = EXCLUDED.message,
                        progress = EXCLUDED.progress,
                        updated_at = NOW()
                """, (config_id, phase, message, progress))
                
                logger.info(f"🔄 Bot {config_id[:8]} status: {phase} - {message}")
                
    except Exception as e:
        logger.error(f"❌ Failed to set bot execution status: {e}")


async def get_bot_execution_status(config_id: str) -> Dict[str, Any]:
    """
    Get current bot execution status.
    
    Args:
        config_id: Bot configuration ID
        
    Returns:
        Dict with phase, message, progress, updated_at
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT phase, message, progress, updated_at
                    FROM bot_execution_status 
                    WHERE config_id = %s
                """, (config_id,))
                
                result = cur.fetchone()
                if result:
                    return {
                        "phase": result[0],
                        "message": result[1],
                        "progress": result[2],
                        "updated_at": result[3].isoformat() if result[3] else None
                    }
                else:
                    # Return default idle status
                    return {
                        "phase": "idle",
                        "message": "Bot ready",
                        "progress": 0,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                    
    except Exception as e:
        logger.error(f"❌ Failed to get bot execution status: {e}")
        return {
            "phase": "error",
            "message": f"Status error: {str(e)}",
            "progress": 0,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }


async def get_all_bot_execution_statuses(user_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Get execution statuses for all user's bots.
    
    Args:
        user_id: User ID
        
    Returns:
        Dict mapping config_id to status dict
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.config_id, 
                           COALESCE(bes.phase, 'idle') as phase,
                           COALESCE(bes.message, 'Bot ready') as message,
                           COALESCE(bes.progress, 0) as progress,
                           COALESCE(bes.updated_at, NOW()) as updated_at
                    FROM configurations c
                    LEFT JOIN bot_execution_status bes ON c.config_id = bes.config_id
                    WHERE c.user_id = %s AND c.state != 'archived'
                """, (user_id,))
                
                results = {}
                for row in cur.fetchall():
                    config_id, phase, message, progress, updated_at = row
                    results[config_id] = {
                        "phase": phase,
                        "message": message,
                        "progress": progress,
                        "updated_at": updated_at.isoformat() if updated_at else None
                    }
                
                return results
                
    except Exception as e:
        logger.error(f"❌ Failed to get bot execution statuses: {e}")
        return {}


async def clear_bot_execution_status(config_id: str, delay_seconds: int = 0) -> None:
    """
    Clear bot execution status back to idle after optional delay.
    
    Args:
        config_id: Bot configuration ID
        delay_seconds: Seconds to wait before clearing (for UX)
    """
    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)
    
    await set_bot_execution_status(config_id, "idle", "Bot ready")


def get_phase_color(phase: str) -> str:
    """
    Get UI color for execution phase.
    
    Args:
        phase: Execution phase
        
    Returns:
        Color string for frontend
    """
    colors = {
        'idle': '#6b7280',      # Gray
        'extracting': '#3b82f6', # Blue  
        'deciding': '#f59e0b',   # Orange
        'trading': '#10b981',    # Green
        'completed': '#10b981',  # Green
        'error': '#ef4444'       # Red
    }
    return colors.get(phase, '#6b7280')


def should_show_spinner(phase: str) -> bool:
    """
    Determine if spinner should be shown for phase.
    
    Args:
        phase: Execution phase
        
    Returns:
        True if spinner should be shown
    """
    return phase in ['extracting', 'deciding', 'trading']