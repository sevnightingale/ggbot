"""
ggShot Bot Handler

Implements bot monitoring logic specific to ggShot signal filtering.
Tracks the ggShot pipeline: Telegram signal → Extraction → Decision → Publishing

Data Sources:
- market_data: Telegram signals and indicator extraction
- ggshot_filter: Decision results and confidence scores
- logs: Real-time pipeline activity and context
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .base_bot import BaseBotHandler


class GGShotBotHandler(BaseBotHandler):
    """
    ggShot-specific bot handler for monitoring signal filtering pipeline.
    
    Pipeline phases:
    1. IDLE: Waiting for signals
    2. EXTRACTION: Processing market data and indicators  
    3. DECISION: 4-pillar validation and confidence scoring
    4. TRADING: Signal approved/rejected (maps to Telegram publishing)
    """
    
    def __init__(self, bot_config: Dict[str, Any]):
        """Initialize ggShot bot handler."""
        super().__init__(bot_config)
        
        # ggShot-specific configuration
        self.confidence_threshold = float(
            self.config_data.get('decision', {}).get('confidence_threshold', 0.5)
        )
        
        # Message rotation state
        self.last_message_rotation = datetime.utcnow()
        self.current_idle_message_index = 0
        
        self.logger.debug(
            f"ggShot handler initialized with confidence threshold: {self.confidence_threshold}"
        )
    
    async def detect_pipeline_phase(self) -> str:
        """
        Detect current ggShot pipeline phase based on recent activity.
        
        Returns:
            str: Current pipeline phase
        """
        # Get timing for different pipeline activities using ggShot-specific user_id
        signal_time = await self._get_ggshot_signal_time()
        decision_time = await self._get_ggshot_decision_time()
        
        # ggShot-specific phase detection logic
        
        # If we have a very recent decision (within 1 minute), we're in trading phase
        if self.is_recent_activity(decision_time, threshold_minutes=1):
            return "trading"
        
        # If we have recent extraction but decision is older, we're in decision phase
        if self.is_recent_activity(signal_time, threshold_minutes=3):
            if not decision_time or decision_time > signal_time:
                return "decision"
        
        # If we have very recent signal activity (within 1 minute), extraction phase
        if self.is_recent_activity(signal_time, threshold_minutes=1):
            return "extraction"
        
        # Default to idle - no recent activity
        return "idle"
    
    async def detect_sub_phase(self, main_phase: str) -> Optional[str]:
        """
        Detect sub-phase within main pipeline phase.
        
        Args:
            main_phase: Main pipeline phase
            
        Returns:
            Optional[str]: Sub-phase identifier
        """
        if main_phase == "idle":
            return await self._detect_idle_sub_phase()
        elif main_phase == "extraction":
            return await self._detect_extraction_sub_phase()
        elif main_phase == "decision":
            return await self._detect_decision_sub_phase()
        elif main_phase == "trading":
            return await self._detect_trading_sub_phase()
        
        return None
    
    async def _detect_idle_sub_phase(self) -> str:
        """Detect idle sub-phase for message rotation."""
        # Rotate idle messages every 30 seconds
        now = datetime.utcnow()
        if (now - self.last_message_rotation).total_seconds() > 30:
            self.current_idle_message_index = (self.current_idle_message_index + 1) % 3
            self.last_message_rotation = now
        
        idle_phases = ["waiting", "scanning", "last_signal"]
        return idle_phases[self.current_idle_message_index]
    
    async def _detect_extraction_sub_phase(self) -> str:
        """Detect extraction sub-phase based on timing."""
        signal_time = await self._get_ggshot_signal_time()
        
        if not signal_time:
            return "signal_received"
        
        elapsed_seconds = signal_time.total_seconds()
        
        if elapsed_seconds < 10:
            return "signal_received"
        elif elapsed_seconds < 30:
            return "indicators_loading"
        elif elapsed_seconds < 60:
            return "indicators_processing"
        else:
            return "indicators_complete"
    
    async def _detect_decision_sub_phase(self) -> str:
        """Detect decision sub-phase based on timing and logs."""
        decision_time = await self._get_ggshot_decision_time()
        signal_time = await self._get_ggshot_signal_time()
        
        # If we have decision but it's older than signal, we're processing new signal
        if decision_time and signal_time and signal_time < decision_time:
            elapsed = signal_time.total_seconds()
            
            if elapsed < 30:
                return "llm_starting"
            elif elapsed < 90:
                return "pillar_analysis"
            else:
                return "confidence_scoring"
        
        return "decision_complete"
    
    async def _detect_trading_sub_phase(self) -> str:
        """Detect trading sub-phase based on recent decision."""
        # Get the latest decision result
        latest_decision = await self._get_latest_decision()
        
        if latest_decision:
            confidence = latest_decision.get('confidence_score', 0)
            filter_status = latest_decision.get('filter_status', '')
            
            if filter_status == 'APPROVED':
                return "signal_approved"
            else:
                return "signal_rejected"
        
        return "signal_approved"  # Default
    
    async def extract_context_data(self) -> Dict[str, Any]:
        """
        Extract contextual data for ggShot status messages.
        
        Returns:
            Dict[str, Any]: Context data including symbols, confidence, etc.
        """
        context = {}
        
        # Get latest signal data
        latest_signal = await self._get_latest_signal()
        if latest_signal:
            context.update({
                'symbol': latest_signal.get('symbol', 'BTC/USDT'),
                'timeframe': latest_signal.get('timeframe', '1h'),
            })
            
            # Extract indicator count if available
            indicators = latest_signal.get('indicators', {})
            if isinstance(indicators, dict):
                indicator_count = len(indicators.get('results', {}))
                if indicator_count > 0:
                    context['indicatorCount'] = indicator_count
        
        # Get latest decision data
        latest_decision = await self._get_latest_decision()
        if latest_decision:
            context.update({
                'confidence': round(float(latest_decision.get('confidence_score', 0)) * 100, 1),
                'direction': latest_decision.get('signal_direction', 'LONG'),
                'entryPrice': float(latest_decision.get('entry_price', 0)) if latest_decision.get('entry_price') else None
            })
        
        # Get time since last signal for idle messages
        signal_time = await self._get_ggshot_signal_time()
        if signal_time:
            context['timeSinceLastSignal'] = self.format_time_ago(signal_time)
        else:
            # If no signal time found, provide a default message
            context['timeSinceLastSignal'] = 'No recent signals'
        
        return context
    
    async def generate_status_message(self, phase: str, sub_phase: Optional[str], 
                                    context: Dict[str, Any]) -> str:
        """
        Generate ggShot-specific status message.
        
        Args:
            phase: Main pipeline phase
            sub_phase: Sub-phase identifier  
            context: Contextual data
            
        Returns:
            str: Human-readable status message
        """
        symbol = context.get('symbol', 'BTC/USDT')
        direction = context.get('direction', 'LONG')
        confidence = context.get('confidence', 0)
        indicator_count = context.get('indicatorCount', 14)
        time_since = context.get('timeSinceLastSignal', 'unknown')
        
        if phase == "idle":
            return self._generate_idle_message(sub_phase, time_since)
        elif phase == "extraction":
            return self._generate_extraction_message(sub_phase, symbol, indicator_count)
        elif phase == "decision":
            return self._generate_decision_message(sub_phase, symbol, confidence)
        elif phase == "trading":
            return self._generate_trading_message(sub_phase, symbol, direction, confidence)
        
        return f"Monitoring {symbol}..."
    
    def _generate_idle_message(self, sub_phase: Optional[str], time_since: str) -> str:
        """Generate idle phase messages with rotation."""
        # Only include last signal message if we have actual signal time
        if time_since == 'No recent signals':
            messages = [
                "Monitoring 140+ crypto pairs...",
                "Waiting for high-confidence setup...",
                "Scanning for trading opportunities..."
            ]
        else:
            messages = [
                "Monitoring 140+ crypto pairs...",
                "Waiting for high-confidence setup...",
                f"Last signal: {time_since}"
            ]
        
        if sub_phase == "waiting":
            return messages[0]
        elif sub_phase == "scanning": 
            return messages[1]
        elif sub_phase == "last_signal":
            return messages[2]
        
        return messages[0]
    
    def _generate_extraction_message(self, sub_phase: Optional[str], 
                                   symbol: str, indicator_count: int) -> str:
        """Generate extraction phase messages."""
        if sub_phase == "signal_received":
            return f"Signal received: {symbol}"
        elif sub_phase == "indicators_loading":
            return f"Fetching {symbol} price data..."
        elif sub_phase == "indicators_processing":
            return f"Processing {indicator_count} technical indicators..."
        elif sub_phase == "indicators_complete":
            return f"Completed {symbol} analysis"
        
        return f"Analyzing {symbol} indicators..."
    
    def _generate_decision_message(self, sub_phase: Optional[str], 
                                 symbol: str, confidence: float) -> str:
        """Generate decision phase messages."""
        if sub_phase == "llm_starting":
            return "Initializing 4-pillar validation..."
        elif sub_phase == "pillar_analysis":
            return f"Analyzing market regime for {symbol}..."
        elif sub_phase == "confidence_scoring":
            return "Calculating confidence score..."
        elif sub_phase == "decision_complete" and confidence > 0:
            return f"Confidence score: {confidence}%"
        
        return f"Evaluating {symbol} signal quality..."
    
    def _generate_trading_message(self, sub_phase: Optional[str], 
                                symbol: str, direction: str, confidence: float) -> str:
        """Generate trading phase messages."""
        if sub_phase == "signal_approved":
            return f"Signal approved: {symbol} {direction}"
        elif sub_phase == "signal_rejected":
            return f"Signal rejected: {symbol} {direction} (low confidence)"
        
        return f"Processing {symbol} {direction} signal..."
    
    async def _get_latest_signal(self) -> Optional[Dict[str, Any]]:
        """Get latest signal from market_data table."""
        try:
            from core.monitoring.active_bot_monitor import active_bot_monitor
            
            conn = active_bot_monitor._get_db_connection()
            try:
                with conn.cursor() as cur:
                    # ggShot signals have specific user_id and config_id IS NULL
                    cur.execute("""
                        SELECT symbol, timeframe, indicators, updated_at
                        FROM market_data
                        WHERE user_id = %s 
                          AND source = 'telegram' 
                          AND config_id IS NULL
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """, ('00000000-0000-0000-0000-000000000001',))
                    
                    result = cur.fetchone()
                    if result:
                        return dict(result)
                    return None
                    
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Failed to get latest signal: {str(e)}")
            return None
    
    async def _get_latest_decision(self) -> Optional[Dict[str, Any]]:
        """Get latest decision from ggshot_filter table."""
        try:
            from core.monitoring.active_bot_monitor import active_bot_monitor
            
            conn = active_bot_monitor._get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT symbol, signal_direction, confidence_score, 
                               filter_status, entry_price, created_at
                        FROM ggshot_filter
                        ORDER BY created_at DESC
                        LIMIT 1
                    """)
                    
                    result = cur.fetchone()
                    if result:
                        return dict(result)
                    return None
                    
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Failed to get latest decision: {str(e)}")
            return None
    
    async def _get_ggshot_signal_time(self) -> Optional[timedelta]:
        """Get time since last ggShot signal."""
        try:
            from core.monitoring.active_bot_monitor import active_bot_monitor
            from datetime import datetime
            
            conn = active_bot_monitor._get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT updated_at
                        FROM market_data
                        WHERE user_id = %s 
                          AND source = 'telegram' 
                          AND config_id IS NULL
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """, ('00000000-0000-0000-0000-000000000001',))
                    
                    result = cur.fetchone()
                    if result and result.get('updated_at'):
                        last_activity = result['updated_at']
                        if isinstance(last_activity, str):
                            last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                        
                        # Ensure timezone awareness - use UTC for consistency
                        from datetime import timezone
                        if last_activity.tzinfo is None:
                            last_activity = last_activity.replace(tzinfo=timezone.utc)
                        
                        now = datetime.now(timezone.utc)
                        time_diff = now - last_activity
                        
                        # Log for debugging
                        self.logger.info(f"ggShot last signal: {last_activity}, Now: {now}, Diff: {time_diff}")
                        
                        return time_diff
                    
                    return None
                    
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Failed to get ggShot signal time: {type(e).__name__}: {str(e)}")
            self.logger.error(f"Exception details: {repr(e)}")
            return None
    
    async def _get_ggshot_decision_time(self) -> Optional[timedelta]:
        """Get time since last ggShot decision."""
        try:
            from core.monitoring.active_bot_monitor import active_bot_monitor
            from datetime import datetime, timezone
            
            conn = active_bot_monitor._get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT created_at
                        FROM ggshot_filter
                        ORDER BY created_at DESC
                        LIMIT 1
                    """)
                    
                    result = cur.fetchone()
                    if result and result.get('created_at'):
                        last_activity = result['created_at']
                        if isinstance(last_activity, str):
                            last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                        
                        # Ensure timezone awareness
                        if last_activity.tzinfo is None:
                            last_activity = last_activity.replace(tzinfo=timezone.utc)
                        
                        now = datetime.now(timezone.utc)
                        time_diff = now - last_activity
                        
                        # Log for debugging
                        self.logger.info(f"ggShot last decision: {last_activity}, Now: {now}, Diff: {time_diff}")
                        
                        return time_diff
                    
                    return None
                    
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Failed to get ggShot decision time: {type(e).__name__}: {str(e)}")
            self.logger.error(f"Exception details: {repr(e)}")
            return None