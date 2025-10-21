"""
Redis-based Bot Execution Status Tracking

Manages ephemeral bot execution phases in Redis with explicit TTLs.
Provides status color and message mapping for the frontend.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import redis.asyncio as redis
from core.common.logger import logger


# Redis client setup
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get Redis client instance (singleton pattern)."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


async def set_execution_phase(
    config_id: str, 
    phase: str, 
    message: str,
    ttl_seconds: int = 120
) -> bool:
    """
    Set bot execution phase in Redis with explicit TTL.
    
    Args:
        config_id: Bot configuration ID
        phase: Execution phase ('extracting', 'deciding', 'trading', 'completed')
        message: Human-readable status message
        ttl_seconds: TTL in seconds (default 120s = 2 minutes)
        
    Returns:
        True if successfully set
    """
    try:
        client = get_redis_client()
        
        status_data = {
            "phase": phase,
            "message": message,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        key = f"bot_execution:{config_id}"
        await client.setex(key, ttl_seconds, json.dumps(status_data))
        
        logger.debug(f"Set execution phase for {config_id}: {phase} - {message}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to set execution phase for {config_id}: {e}")
        return False


def get_execution_phase(config_id: str) -> Optional[Dict[str, Any]]:
    """
    Get current execution phase from Redis (sync version for dashboard query).
    
    Args:
        config_id: Bot configuration ID
        
    Returns:
        Status dictionary with phase, message, updated_at or None if not found
    """
    try:
        # Use sync Redis client for database query context
        import redis as sync_redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        client = sync_redis.from_url(redis_url, decode_responses=True)
        
        key = f"bot_execution:{config_id}"
        data = client.get(key)
        client.close()  # Clean up connection
        
        if data:
            return json.loads(data)
        return None
        
    except Exception as e:
        logger.error(f"Failed to get execution phase for {config_id}: {e}")
        return None


async def clear_execution_phase(config_id: str) -> bool:
    """
    Clear bot execution phase from Redis.
    
    Args:
        config_id: Bot configuration ID
        
    Returns:
        True if successfully cleared
    """
    try:
        client = get_redis_client()
        key = f"bot_execution:{config_id}"
        await client.delete(key)
        logger.debug(f"Cleared execution phase for {config_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear execution phase for {config_id}: {e}")
        return False


def get_bot_status_color(bot_state: str, execution_status: Optional[Dict[str, Any]]) -> str:
    """
    Get status circle color for bot based on state and execution phase.
    
    Args:
        bot_state: Database state ('active', 'inactive', etc.)
        execution_status: Current execution phase from Redis
        
    Returns:
        Color string for UI ('green', 'blue', 'yellow', 'gray', 'red')
    """
    if bot_state != 'active':
        return 'gray'
    
    if not execution_status:
        return 'green'  # Active but idle
    
    phase = execution_status.get('phase', '')
    
    phase_colors = {
        'extracting': 'blue',
        'deciding': 'yellow', 
        'trading': 'orange',
        'completed': 'green',
        'error': 'red'
    }
    
    return phase_colors.get(phase, 'green')


def get_bot_status_message(bot_state: str, execution_status: Optional[Dict[str, Any]]) -> str:
    """
    Get status message for bot based on state and execution phase.
    
    Args:
        bot_state: Database state ('active', 'inactive', etc.)
        execution_status: Current execution phase from Redis
        
    Returns:
        Human-readable status message
    """
    if bot_state != 'active':
        return 'Bot inactive'
    
    if not execution_status:
        return 'Monitoring markets and waiting for next analysis...'
    
    # Use the message from Redis if available
    message = execution_status.get('message')
    if message:
        return message
    
    # Fallback based on phase
    phase = execution_status.get('phase', '')
    phase_messages = {
        'extracting': 'Gathering market data and indicators...',
        'deciding': 'Analyzing market conditions for trading opportunities...',
        'trading': 'Processing trade...',
        'completed': 'Analysis complete',
        'error': 'Error occurred'
    }

    return phase_messages.get(phase, 'Processing...')


# Status phase constants for consistency
class ExecutionPhase:
    """Constants for execution phases."""
    EXTRACTING = 'extracting'
    DECIDING = 'deciding'
    TRADING = 'trading'
    COMPLETED = 'completed'
    ERROR = 'error'