"""
Event models for the Trading Engine.

These models represent events that can be emitted by various
components of the Trading Engine for monitoring and logging.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class EventType(str, Enum):
    """Event types that can be emitted by the Trading Engine."""
    # General events
    ENGINE_STARTED = 'engine_started'
    ENGINE_STOPPED = 'engine_stopped'
    
    # LLM events
    LLM_CALL_STARTED = 'llm_call_started'
    LLM_CALL_SUCCEEDED = 'llm_call_succeeded'
    LLM_CALL_FAILED = 'llm_call_failed'
    LLM_RESPONSE_INVALID = 'llm_response_invalid'
    
    # Validation events
    VALIDATION_STARTED = 'validation_started'
    VALIDATION_SUCCEEDED = 'validation_succeeded'
    VALIDATION_FAILED = 'validation_failed'
    
    # Execution events
    TOOL_CALL_STARTED = 'tool_call_started'
    TOOL_CALL_SUCCEEDED = 'tool_call_succeeded'
    TOOL_CALL_FAILED = 'tool_call_failed'
    TOOL_CALLS_BATCH_STARTED = 'tool_calls_batch_started'
    TOOL_CALLS_BATCH_SUCCEEDED = 'tool_calls_batch_succeeded'
    TOOL_CALLS_BATCH_FAILED = 'tool_calls_batch_failed'
    
    # Trade events
    TRADE_REGISTERED = 'trade_registered'
    TRADE_UPDATED = 'trade_updated'
    TRADE_UNREGISTERED = 'trade_unregistered'
    TRADE_EXIT_TRIGGERED = 'trade_exit_triggered'
    
    # Position events
    POSITION_POLLING_STARTED = 'position_polling_started'
    POSITION_POLLING_SUCCEEDED = 'position_polling_succeeded'
    POSITION_POLLING_FAILED = 'position_polling_failed'
    POSITION_NOT_FOUND = 'position_not_found'
    
    # Decision events
    DECISION_RECEIVED = 'decision_received'
    DECISION_PROCESSED = 'decision_processed'
    DECISION_REJECTED = 'decision_rejected'
    DECISION_FAILED = 'decision_failed'


class Event(BaseModel):
    """
    Model for an event emitted by the Trading Engine.
    
    Events are used for monitoring, logging, and potentially
    triggering actions in other components.
    """
    event_type: EventType = Field(description="Type of event")
    timestamp: str = Field(description="Timestamp when the event occurred")
    user_id: Optional[str] = Field(default=None, description="User ID associated with the event")
    trade_id: Optional[str] = Field(default=None, description="Trade ID associated with the event")
    decision_id: Optional[str] = Field(default=None, description="Decision ID associated with the event")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional event details")
    
    @classmethod
    def create(cls, event_type: EventType, **kwargs) -> "Event":
        """
        Create a new event with the current timestamp.
        
        Args:
            event_type: Type of event
            **kwargs: Additional event fields
            
        Returns:
            Event object
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        return cls(event_type=event_type, timestamp=timestamp, **kwargs)