"""
Base Bot Handler Interface

Defines the interface that all bot type handlers must implement.
Each bot type (ggshot, demo, etc.) extends this base class with
specific logic for pipeline detection and status messaging.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from core.common.logger import logger


class BaseBotHandler(ABC):
    """
    Abstract base class for all bot type handlers.
    
    Each bot type must implement:
    - Pipeline phase detection logic
    - Status message generation
    - Context data extraction
    """
    
    def __init__(self, bot_config: Dict[str, Any]):
        """
        Initialize base bot handler.
        
        Args:
            bot_config: Bot configuration from config_instances JOIN configurations
        """
        # Ensure UUID fields are converted to strings
        self.config_id = str(bot_config['config_id'])
        self.config_type = str(bot_config['config_type'])
        self.user_id = str(bot_config.get('user_id')) if bot_config.get('user_id') else None
        self.instance_name = bot_config.get('instance_name')
        
        # Now we can safely use string operations
        self.config_name = bot_config.get('config_name', f"Bot {self.config_id[:8]}")
        self.config_data = bot_config.get('config_data', {})
        
        self.logger = logger.bind(
            module=f"bot.{self.config_type}",
            config_id=self.config_id[:8]
        )
        
        self.logger.debug(f"Initialized {self.config_type} bot handler: {self.config_name}")
    
    @abstractmethod
    async def detect_pipeline_phase(self) -> str:
        """
        Detect current pipeline phase for this bot.
        
        Must return one of: "idle", "extraction", "decision", "trading"
        
        Returns:
            str: Current pipeline phase
        """
        pass
    
    @abstractmethod
    async def detect_sub_phase(self, main_phase: str) -> Optional[str]:
        """
        Detect sub-phase within the main pipeline phase.
        
        Args:
            main_phase: The main pipeline phase
            
        Returns:
            Optional[str]: Sub-phase identifier or None
        """
        pass
    
    @abstractmethod
    async def extract_context_data(self) -> Dict[str, Any]:
        """
        Extract contextual data for status message generation.
        
        Examples: symbol, timeframe, confidence, indicator names, etc.
        
        Returns:
            Dict[str, Any]: Context data for message templates
        """
        pass
    
    @abstractmethod
    async def generate_status_message(self, phase: str, sub_phase: Optional[str], 
                                    context: Dict[str, Any]) -> str:
        """
        Generate human-readable status message for current state.
        
        Args:
            phase: Main pipeline phase
            sub_phase: Sub-phase identifier
            context: Contextual data for message generation
            
        Returns:
            str: Human-readable status message
        """
        pass
    
    # Utility methods available to all bot handlers
    
    def get_time_since_last_activity(self, table: str, time_column: str = 'created_at',
                                   where_clause: str = None, include_user_filter: bool = True) -> Optional[timedelta]:
        """
        Calculate time since last activity in specified table.
        
        Args:
            table: Database table name
            time_column: Timestamp column name
            where_clause: Optional WHERE clause (without WHERE keyword)
            include_user_filter: Whether to filter by user_id
            
        Returns:
            Optional[timedelta]: Time since last activity or None if no activity
        """
        try:
            from core.monitoring.active_bot_monitor import active_bot_monitor
            
            conn = active_bot_monitor._get_db_connection()
            try:
                with conn.cursor() as cur:
                    if include_user_filter:
                        base_query = f"""
                            SELECT {time_column}
                            FROM {table}
                            WHERE user_id = %s
                        """
                        params = [self.user_id]
                    else:
                        base_query = f"""
                            SELECT {time_column}
                            FROM {table}
                            WHERE 1=1
                        """
                        params = []
                    
                    if where_clause:
                        base_query += f" AND {where_clause}"
                    
                    base_query += f" ORDER BY {time_column} DESC LIMIT 1"
                    
                    cur.execute(base_query, params)
                    result = cur.fetchone()
                    
                    if result and result[0]:
                        last_activity = result[0]
                        if isinstance(last_activity, str):
                            last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                        
                        # Ensure timezone awareness
                        if last_activity.tzinfo is None:
                            last_activity = last_activity.replace(tzinfo=datetime.now().astimezone().tzinfo)
                        
                        now = datetime.now(last_activity.tzinfo)
                        return now - last_activity
                    
                    return None
                    
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Failed to get last activity from {table}: {str(e)}")
            return None
    
    def format_time_ago(self, time_delta: Optional[timedelta]) -> str:
        """
        Format timedelta as human-readable "X ago" string.
        
        Args:
            time_delta: Time delta to format
            
        Returns:
            str: Formatted time string
        """
        if not time_delta:
            return "unknown"
        
        total_seconds = int(time_delta.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s ago"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m ago"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            return f"{hours}h ago"
        else:
            days = total_seconds // 86400
            return f"{days}d ago"
    
    def is_recent_activity(self, time_delta: Optional[timedelta], 
                          threshold_minutes: int = 5) -> bool:
        """
        Check if activity is recent (within threshold).
        
        Args:
            time_delta: Time since activity
            threshold_minutes: Threshold in minutes
            
        Returns:
            bool: True if activity is recent
        """
        if not time_delta:
            return False
        
        return time_delta.total_seconds() < (threshold_minutes * 60)
    
    def get_phase_from_timing(self, extraction_time: Optional[timedelta],
                            decision_time: Optional[timedelta]) -> str:
        """
        Determine pipeline phase based on activity timing.
        
        Args:
            extraction_time: Time since last extraction activity
            decision_time: Time since last decision activity
            
        Returns:
            str: Pipeline phase
        """
        # If we have recent decision activity, we might be in trading phase
        if self.is_recent_activity(decision_time, threshold_minutes=2):
            return "trading"
        
        # If we have recent extraction but no recent decision, we're in decision phase
        if self.is_recent_activity(extraction_time, threshold_minutes=5):
            if not decision_time or decision_time > extraction_time:
                return "decision"
        
        # If we have very recent extraction activity, we're in extraction phase
        if self.is_recent_activity(extraction_time, threshold_minutes=2):
            return "extraction"
        
        # Default to idle
        return "idle"