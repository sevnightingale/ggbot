"""
Server-Sent Events (SSE) module for ggbots platform.

Provides unified dashboard data streaming and Redis-based execution status tracking.
Replaces complex WebSocket architecture with clean, efficient SSE streaming.
"""

from .dashboard_data import get_unified_dashboard_data
from .redis_status import (
    set_execution_phase,
    get_execution_phase,
    clear_execution_phase,
    get_bot_status_color,
    get_bot_status_message
)

__all__ = [
    'get_unified_dashboard_data',
    'set_execution_phase',
    'get_execution_phase', 
    'clear_execution_phase',
    'get_bot_status_color',
    'get_bot_status_message'
]