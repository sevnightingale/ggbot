"""
GGBot V2 Orchestrator - Clean Architecture Implementation

Main orchestrator API that coordinates all V2 modules with Supabase integration.
Provides unified entry point for autonomous trading with multi-user isolation.
"""

import asyncio
import uuid
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, field_serializer
import uvicorn
import json
import psycopg2.extras
import numpy as np

# APScheduler imports
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import STATE_RUNNING
from apscheduler.triggers.cron import CronTrigger
import redis.asyncio as redis

# Scheduler utilities
from core.scheduler import (
    cron_for,
    last_closed_close_ts,
    get_misfire_grace_time,
    format_redis_idempotency_key,
    get_redis_ttl_for_timeframe
)

# V2 Core Components
from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2, require_premium_user_v2
from core.sse import get_unified_dashboard_data

# Development Mock User (TODO: Remove when Phase 5 authentication is complete)
async def get_mock_user_for_dev():
    """Mock user for Phase 7 development - replace with real auth in Phase 5."""
    return AuthenticatedUser(
        user_id="3d47c173-9234-47c7-b57b-9159c9df5dbd",  # Real Supabase user ID
        email="user@example.com",  # Placeholder email
        claims={"sub": "3d47c173-9234-47c7-b57b-9159c9df5dbd", "email": "user@example.com"}
    )
from core.services.config_service import ConfigService, BotConfigV2, config_service
from core.services.user_service import UserService, user_service
from core.services.llm_service import LLMService, llm_service
from core.services.indicator_service import IndicatorService
from core.common.logger import logger as base_logger

# Set up orchestrator-specific logger for core trading activities
def is_orchestrator_log(record):
    """Filter for important orchestrator and trading activities only."""
    service = record["extra"].get("service")
    message = record.get("message", "")
    function_name = record.get("function", "")
    
    # Only include orchestrator service logs
    if service == "orchestrator":
        # Exclude old WebSocket spam (now using SSE)
        if "WebSocket" in message or "broadcast" in function_name:
            return False
        return True
    
    # Include critical extraction/decision/trading logs regardless of service
    important_messages = [
        "Manual trigger", "V2 autonomous cycle", "V2 Extraction completed", 
        "V2 Decision completed", "Paper trade executed", "Position closed",
        "Extraction complete", "Decision saved", "Trading result"
    ]
    
    if any(msg in message for msg in important_messages):
        return True
    
    return False

# Configure log directory and ensure it exists
LOG_DIR = os.getenv("GGBOT_LOG_DIR", "/home/sev/ggbot/logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "orchestrator.log")

# Demo mode configuration for artificial delays
DEMO_MODE = os.getenv("GGBOT_DEMO_MODE", "false").lower() == "true"

base_logger.add(
    LOG_PATH,
    filter=is_orchestrator_log,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    rotation="50 MB",      # Larger rotation for important logs
    retention="7 days",    # Keep longer for business analysis
    compression="gz",
    enqueue=True,
    level="INFO"
)

# Create orchestrator logger for core business logic
logger = base_logger.bind(service="orchestrator")

# V2 Module Integration - Complete Integration
from extraction.v2.extraction_engine import ExtractionEngineV2
from decision.engine_v2 import DecisionEngineV2
from trading.paper.supabase_service import SupabasePaperTradingService
from signals.publishing_service import publish_signal_to_telegram

# Domain Models  
from core.domain import Decision, DecisionAction, DecisionStatus, UserProfile, Symbol, Confidence


# Pydantic Models for API
class ConfigCreateRequest(BaseModel):
    config_name: str
    schema_version: str = "2.1"
    config_type: str = "autonomous_trading"
    selected_pair: str = "BTC/USDT"
    extraction: Dict[str, Any]
    decision: Dict[str, Any]
    trading: Dict[str, Any]
    llm_config: Dict[str, Any]
    telegram_integration: Optional[Dict[str, Any]] = None


class ConfigUpdateRequest(BaseModel):
    config_name: Optional[str] = None
    schema_version: Optional[str] = None
    config_type: Optional[str] = None
    selected_pair: Optional[str] = None
    extraction: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    trading: Optional[Dict[str, Any]] = None
    llm_config: Optional[Dict[str, Any]] = None
    telegram_integration: Optional[Dict[str, Any]] = None


class SignalOrchestrationRequest(BaseModel):
    signal_data: Optional[Dict[str, Any]] = None
    override_symbol: Optional[str] = None


def serialize_numpy_types(obj):
    """Recursively convert numpy types and Decimal to Python native types."""
    from decimal import Decimal
    
    if isinstance(obj, (np.integer)):
        return int(obj)
    elif isinstance(obj, (np.floating)):
        return float(obj)
    elif isinstance(obj, (np.ndarray)):
        return obj.tolist()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: serialize_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_numpy_types(item) for item in obj]
    else:
        return obj

class OrchestrationResult(BaseModel):
    status: str
    config_id: str
    extraction_result: Optional[Dict[str, Any]] = None
    decision_result: Optional[Dict[str, Any]] = None
    trading_result: Optional[Dict[str, Any]] = None
    execution_time_ms: int
    timestamp: str
    
    @field_serializer('extraction_result', 'decision_result', 'trading_result')
    def serialize_results(self, value):
        """Convert numpy types to JSON-serializable Python types."""
        if value is None:
            return None
        return serialize_numpy_types(value)


# FastAPI lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    logger.info("🚀 Starting GGBot V2 Orchestrator")
    
    # Initialize monitoring service variables
    monitoring_service = None
    monitoring_task = None
    
    # Startup tasks
    try:
        # Test database connectivity with a valid UUID
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 as test")
                cur.fetchone()
        logger.info("✅ Database connectivity verified")
        
        # Test LLM service
        # await llm_service.test_hosted_keys()
        logger.info("✅ LLM service initialized")
        
        # Start APScheduler
        scheduler.start()
        logger.info("✅ APScheduler started")
        
        # Start monitoring service (positions only - no WebSocket spam!)
        from core.monitoring.service import MonitoringService
        monitoring_service = MonitoringService()
        monitoring_task = asyncio.create_task(monitoring_service.start())
        logger.info("✅ Monitoring service started (positions only - no WebSocket spam!)")
        
        # Reconcile active bots from database
        await reconcile_active_bots()
        
        logger.info("🟢 GGBot V2 Orchestrator ready")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown tasks
    logger.info("🔄 Shutting down GGBot V2 Orchestrator")
    
    # Shutdown monitoring service
    if monitoring_service and monitoring_task:
        await monitoring_service.stop()
        if not monitoring_task.done():
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("✅ Monitoring service stopped")
    
    # Shutdown scheduler
    if scheduler.state == STATE_RUNNING:
        scheduler.shutdown(wait=False)
        logger.info("✅ APScheduler shutdown")


# Create FastAPI app
app = FastAPI(
    title="GGBot V2 Orchestrator",
    description="Unified orchestrator for autonomous AI trading with Supabase integration",
    version="2.0.0",
    lifespan=lifespan
)

# CORS handled by nginx proxy - no FastAPI CORS middleware needed

# Services
class GGBotOrchestrator:
    """Main orchestrator class coordinating all V2 modules with full integration."""
    
    def __init__(self):
        self.config_service = config_service
        self.llm_service = llm_service
        self.paper_trading = SupabasePaperTradingService()
        self._log = logger.bind(component="orchestrator")
        
        # V2 Engine instances - created per request for proper isolation
        self._extraction_engines = {}  # Cache by user_id for efficiency
        self._decision_engines = {}    # Cache by config_id
    
    async def run_autonomous_cycle(
        self,
        config_id: str,
        user_id: str,
        signal_data: Optional[Dict] = None,
        override_symbol: Optional[str] = None
    ) -> OrchestrationResult:
        """
        Run a complete trading cycle (autonomous or signal validation).
        
        Args:
            config_id: Bot configuration ID
            user_id: User ID for access validation
            signal_data: Signal data for validation mode
            override_symbol: Dynamic symbol override for signals
            
        Returns:
            OrchestrationResult with execution details
        """
        start_time = datetime.now(timezone.utc)
        self._log.info(f"Starting V2 autonomous cycle for config {config_id}")
        
        try:
            # 1. Load user configuration
            config = await self.config_service.get_config(config_id, user_id)
            if not config:
                raise HTTPException(status_code=404, detail="Configuration not found")
            
            # 2. Route based on config type
            if config.config_type == "signal_validation":
                if signal_data:
                    # Real signal from external source
                    return await self._run_signal_validation_cycle(
                        config, signal_data, override_symbol
                    )
                else:
                    # Manual trigger - fetch latest real ggShot signal
                    latest_signal = await self._fetch_latest_ggshot_signal()
                    # Convert SignalData object to dict for decision engine
                    signal_dict = self._signal_data_to_dict(latest_signal)
                    return await self._run_signal_validation_cycle(
                        config, signal_dict, override_symbol
                    )
            else:
                return await self._run_autonomous_trading_cycle(config)
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            self._log.error(f"V2 orchestration failed: {e}")
            raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")
            
    async def _run_autonomous_trading_cycle(self, config: BotConfigV2) -> OrchestrationResult:
        """Run traditional autonomous trading cycle."""
        start_time = datetime.now(timezone.utc)
        user_id = config.user_id
        config_id = config.config_id
        
        try:
            # Get or create V2 extraction engine
            extraction_engine = await self._get_extraction_engine(user_id)
            
            # Extract indicators and timeframes from config structure
            extraction_config = config.extraction or {}
            requested_indicators = self._extract_indicators_from_config(extraction_config)
            timeframes = self._extract_timeframes_from_config(extraction_config)
            
            # 4. Run V2 extraction for all timeframes
            # 🔥 WEBSOCKET DELETED - Now using Redis status for SSE stream!
            from core.sse import set_execution_phase
            await set_execution_phase(config_id, "extracting", f"Extracting {len(requested_indicators)} indicators for {config.selected_pair}...")
            
            extraction_result = await self._run_extraction_v2(
                extraction_engine, config, user_id, requested_indicators, timeframes
            )
            
            # Allow users to see extraction phase for 7 seconds (better UX) - only in demo mode
            if DEMO_MODE:
                await asyncio.sleep(7)
            
            # 5. Run V2 decision engine
            # 🔥 WEBSOCKET DELETED - Using Redis status for SSE stream!
            await set_execution_phase(config_id, "deciding", "AI decision engine analyzing market data across multiple timeframes...")
            
            decision_result = await self._run_decision_v2(
                config_id, config, extraction_result
            )
            
            # Allow users to see decision phase for 3 seconds (better UX) - only in demo mode
            if DEMO_MODE:
                await asyncio.sleep(3)
            
            # 6. Execute trading
            # 🔥 WEBSOCKET DELETED - Using Redis status for SSE stream!
            action = decision_result.get('action', 'wait')
            if action in ['wait', 'no_action', 'hold']:
                message = f"Holding position - {action} decision with confidence {decision_result.get('confidence', 0):.2f}"
            else:
                message = f"Executing {action} decision..."
            
            await set_execution_phase(config_id, "trading", message)
            
            trading_result = await self._run_trading_v2(
                config, user_id, decision_result
            )
            
            # 7. Publish to telegram if configured
            if self._should_publish_signal(config, decision_result):
                await self._trigger_signal_publishing(
                    config, {}, decision_result  # Empty signal_data for autonomous trading
                )
            
            # Calculate execution time
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            result = OrchestrationResult(
                status="success",
                config_id=str(config_id),
                extraction_result=extraction_result,
                decision_result=decision_result,
                trading_result=trading_result,
                execution_time_ms=execution_time_ms,
                timestamp=end_time.isoformat()
            )
            
            # 8. Send completion status
            # 🔥 WEBSOCKET DELETED - Using Redis status for SSE stream!
            await set_execution_phase(config_id, "completed", f"Cycle completed in {execution_time_ms/1000:.1f}s")
            
            self._log.info(f"V2 autonomous cycle completed in {execution_time_ms}ms")
            return result
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            self._log.error(f"V2 autonomous cycle failed: {e}")
            return OrchestrationResult(
                status="error",
                config_id=str(config_id),
                extraction_result={"error": str(e)},
                decision_result=None,
                trading_result=None,
                execution_time_ms=execution_time_ms,
                timestamp=end_time.isoformat()
            )
    
    async def _run_signal_validation_cycle(
        self,
        config: BotConfigV2,
        signal_data: Dict,
        override_symbol: Optional[str] = None
    ) -> OrchestrationResult:
        """Run signal validation cycle for external signals."""
        start_time = datetime.now(timezone.utc)
        user_id = config.user_id
        config_id = config.config_id
        
        try:
            # Extract symbol from signal or override
            symbol = override_symbol or signal_data.get('symbol') or config.selected_pair

            if not symbol:
                raise ValueError("No symbol specified for signal validation")
            
            self._log.info(f"Running signal validation for {symbol}")
            
            # Get indicators and timeframes from user's config (same as autonomous trading)
            extraction_config = config.extraction or {}
            signal_indicators = self._extract_indicators_from_config(extraction_config)
            timeframes = self._extract_timeframes_from_config(extraction_config)

            # Get or create extraction engine
            extraction_engine = await self._get_extraction_engine(user_id)

            # Add extracting phase for UI consistency
            from core.sse import set_execution_phase
            await set_execution_phase(config_id, "extracting", f"Extracting indicators for {symbol}...")

            # Run extraction for all configured timeframes
            extraction_result = await self._run_extraction_v2(
                extraction_engine, config, user_id,
                signal_indicators, timeframes,
                override_symbol=symbol
            )

            # Add deciding phase for UI consistency
            await set_execution_phase(config_id, "deciding", "AI decision engine analyzing signal context...")

            # Run decision with signal context
            decision_result = await self._run_decision_v2(
                config_id, config, extraction_result, signal_data
            )
            
            # Execute trading
            # 🔥 WEBSOCKET DELETED - Using Redis status for SSE stream!
            action = decision_result.get('action', 'wait')
            if action in ['wait', 'no_action', 'hold']:
                message = f"Signal rejected - {action} decision with confidence {decision_result.get('confidence', 0):.2f}"
            else:
                message = f"Signal validated - executing {action} decision..."
            
            await set_execution_phase(config_id, "trading", message)
            
            trading_result = await self._run_trading_v2(
                config, user_id, decision_result
            )
            
            # Check if signal should be published to telegram
            if self._should_publish_signal(config, decision_result):
                await self._trigger_signal_publishing(
                    config, signal_data, decision_result
                )
            
            # Calculate execution time
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            result = OrchestrationResult(
                status="success",
                config_id=str(config_id),
                extraction_result=extraction_result,
                decision_result=decision_result,
                trading_result=trading_result,
                execution_time_ms=execution_time_ms,
                timestamp=end_time.isoformat()
            )
            
            # Send completion status
            # 🔥 WEBSOCKET DELETED - Using Redis status for SSE stream!
            await set_execution_phase(config_id, "completed", f"Signal validation completed in {execution_time_ms/1000:.1f}s")
            
            self._log.info(f"Signal validation completed in {execution_time_ms}ms")
            return result
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            self._log.error(f"Signal validation failed: {e}")
            return OrchestrationResult(
                status="error",
                config_id=str(config_id),
                extraction_result={"error": str(e)},
                decision_result=None,
                trading_result=None,
                execution_time_ms=execution_time_ms,
                timestamp=end_time.isoformat()
            )
    
    def _extract_indicators_from_config(self, extraction_config: Dict) -> List[str]:
        """Extract indicators from user's extraction config."""
        requested_indicators = []
        
        # Handle new structure (selected_data_sources) 
        if "selected_data_sources" in extraction_config:
            data_sources = extraction_config.get("selected_data_sources", {})
            for source_name, source_config in data_sources.items():
                if isinstance(source_config, dict) and source_name != "signals":
                    # Get data points from non-signal sources
                    data_points = source_config.get("data_points", [])
                    requested_indicators.extend(data_points)
                        
        # Fallback to legacy structures
        elif "indicators" in extraction_config:
            requested_indicators = extraction_config["indicators"]
        else:
            # Fallback to old data_sources structure
            data_sources = extraction_config.get("data_sources", {})
            for category, indicators in data_sources.items():
                if isinstance(indicators, list):
                    requested_indicators.extend(indicators)
        
        if not requested_indicators:
            # Default to basic indicators if none specified
            requested_indicators = ["rsi", "macd", "ema"]
            
        return requested_indicators
    
    def _extract_timeframes_from_config(self, extraction_config: Dict) -> List[str]:
        """Extract timeframes from user's extraction config."""
        timeframes = ["1h"]  # Default single timeframe
        
        # Handle new structure (selected_data_sources)
        if "selected_data_sources" in extraction_config:
            data_sources = extraction_config.get("selected_data_sources", {})
            
            # First, try to get timeframes from technical_analysis (most common case)
            if "technical_analysis" in data_sources:
                ta_config = data_sources["technical_analysis"]
                if isinstance(ta_config, dict):
                    ta_timeframes = ta_config.get("timeframes", [])
                    if ta_timeframes:
                        timeframes = ta_timeframes
                        self._log.debug(f"Found {len(timeframes)} timeframes from technical_analysis: {timeframes}")
                        return timeframes
            
            # Fallback: collect all unique timeframes from all sources with data_points
            all_timeframes = set()
            for source_name, source_config in data_sources.items():
                if isinstance(source_config, dict) and source_name != "signals":
                    # Only include sources that have actual data_points configured
                    data_points = source_config.get("data_points", [])
                    if data_points:  # Only consider sources with actual indicators
                        source_timeframes = source_config.get("timeframes", [])
                        all_timeframes.update(source_timeframes)
            
            if all_timeframes:
                timeframes = list(all_timeframes)
                self._log.debug(f"Found {len(timeframes)} timeframes from all sources: {timeframes}")
        
        self._log.debug(f"Using timeframes: {timeframes}")
        return timeframes
    
    async def _fetch_latest_ggshot_signal(self):
        """Fetch the latest real ggShot signal from Telegram for manual testing."""
        from signals.listener_service import SignalData
        from telethon import TelegramClient
        import os
        import sys
        from dotenv import load_dotenv
        
        try:
            # Ensure .env is loaded
            load_dotenv()
            
            api_id = int(os.getenv('TG_API_ID'))
            api_hash = os.getenv('TG_API_HASH')
            channel_name = os.getenv('GGSHOT_CHANNEL', 'GGShot_Bot')
            
            if not api_id or not api_hash:
                raise ValueError("Missing TG_API_ID or TG_API_HASH environment variables")
            
            # Use separate session file for manual trigger to avoid conflicts
            session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
            session_path = os.path.join(session_dir, 'manual_trigger_session')
            
            client = TelegramClient(session_path, api_id, api_hash)
            await client.start()
            
            try:
                # Get channel entity
                channel = await client.get_entity(channel_name)
                
                # Fetch latest messages (limit to recent ones)
                messages = await client.get_messages(channel, limit=10)
                
                # Import ggShot parser
                sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ggshot'))
                from ggshot_parser import GGShotParser
                parser = GGShotParser()
                
                # Find the most recent valid signal
                for message in messages:
                    if message.message:
                        signal_data = parser.parse_signal(message.message)
                        if signal_data:
                            self._log.info(f"Found latest ggShot signal: {signal_data['symbol']} {signal_data['direction']}")
                            
                            # Convert to StandardizedSignalData format
                            return SignalData(
                                source='ggshot',
                                symbol=signal_data['symbol'],
                                direction=signal_data['direction'],
                                timeframe=signal_data['timeframe'],
                                confidence=signal_data.get('strategy_accuracy', 80) / 100.0,
                                entry_zone=signal_data['entry_zone'],
                                stop_loss=signal_data['stop_loss'],
                                take_profit=signal_data['target_1'],
                                reasoning=f"Latest ggShot signal with {signal_data.get('strategy_accuracy', 80)}% accuracy",
                                raw_message=message.message,
                                metadata={
                                    'targets': signal_data['targets'],
                                    'trend_line': signal_data.get('trend_line'),
                                    'strategy_accuracy': signal_data.get('strategy_accuracy'),
                                    'manual_fetch': True
                                },
                                timestamp=datetime.now(timezone.utc)
                            )
                
                raise ValueError("No valid ggShot signals found in recent messages")
                
            finally:
                await client.disconnect()
                
        except Exception as e:
            self._log.error(f"Failed to fetch latest ggShot signal: {e}")
            raise

    def _should_publish_signal(self, config: BotConfigV2, decision_result: Dict) -> bool:
        """Check if signal should be published to telegram."""
        telegram_config = config.telegram_integration or {}
        publisher_config = telegram_config.get('publisher', {})

        # Check if telegram publishing is enabled
        if not publisher_config.get('enabled', False):
            return False

        # Check if user has ggbase subscription (required for signal publishing)
        try:
            from core.common.db import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT subscription_tier, subscription_status
                        FROM user_profiles
                        WHERE user_id = %s
                    """, (config.user_id,))

                    result = cur.fetchone()
                    if not result:
                        self._log.warning(f"No user profile found for {config.user_id}")
                        return False

                    tier, status = result

                    # Must be ggbase tier with active subscription
                    if tier != 'ggbase' or status != 'active':
                        self._log.info(f"User {config.user_id} requires ggbase subscription for signal publishing")
                        return False

        except Exception as e:
            self._log.error(f"Failed to check subscription for signal publishing: {e}")
            return False

        # Always publish signals (approval/rejection status handled by publishing service)
        return True
    
    async def _trigger_signal_publishing(
        self,
        config: BotConfigV2,
        signal_data: Dict,
        decision_result: Dict
    ) -> None:
        """Trigger signal publishing to user's Telegram channel."""
        try:
            # Import the publishing service function
            from signals.publishing_service import publish_signal_to_telegram
            
            success = await publish_signal_to_telegram(
                config_id=config.config_id,
                user_id=config.user_id,
                signal_data=signal_data,
                decision_result=decision_result
            )
            
            if success:
                self._log.info(f"Successfully published signal for config {config.config_id}")
            else:
                self._log.warning(f"Failed to publish signal for config {config.config_id}")
                
        except ImportError:
            self._log.warning("Publishing service not available - signals not published")
        except Exception as e:
            self._log.error(f"Error publishing signal for config {config.config_id}: {e}")

    def _signal_data_to_dict(self, signal_data) -> Dict:
        """Convert SignalData object to dict for decision engine."""
        return {
            'source': signal_data.source,
            'symbol': signal_data.symbol,
            'direction': signal_data.direction,
            'timeframe': signal_data.timeframe,
            'confidence': signal_data.confidence,
            'entry_zone': signal_data.entry_zone,
            'stop_loss': signal_data.stop_loss,
            'take_profit': signal_data.take_profit,
            'reasoning': signal_data.reasoning,
            'raw_message': signal_data.raw_message,
            'metadata': signal_data.metadata,
            'timestamp': signal_data.timestamp.isoformat() if hasattr(signal_data.timestamp, 'isoformat') else str(signal_data.timestamp)
        }

    async def _get_extraction_engine(self, user_id: str) -> ExtractionEngineV2:
        """Get or create V2 extraction engine for user."""
        if user_id not in self._extraction_engines:
            self._extraction_engines[user_id] = ExtractionEngineV2(
                user_id=user_id,
                use_advanced_preprocessing=True,
                use_database_storage=True,
                use_file_storage=False  # Disable file storage for production (prevents bloat)
            )
        return self._extraction_engines[user_id]
    
    async def _run_extraction_v2(
        self,
        extraction_engine: ExtractionEngineV2,
        config: BotConfigV2,
        user_id: str,
        indicators: List[str],
        timeframes: List[str] = ["1h"],
        override_symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run V2 extraction engine for multiple timeframes with proper integration."""
        try:
            # Get symbol from override or config
            symbol = override_symbol or config.selected_pair or "BTC/USDT"
            
            # Extract for all timeframes
            timeframe_results = {}
            successful_extractions = 0
            
            for timeframe in timeframes:
                self._log.info(f"Extracting {len(indicators)} indicators for {symbol} ({timeframe})")
                
                # Extract using the V2 system with all 21 preprocessors
                result = await extraction_engine.extract_for_symbol(
                    symbol=symbol,
                    indicators=indicators,
                    timeframe=timeframe,
                    limit=200,
                    connector="kucoin",
                    config_id=config.config_id
                )
                
                timeframe_results[timeframe] = result
                
                if result.get("status") == "success":
                    successful_extractions += 1
                    self._log.info(f"✅ V2 Extraction completed for {symbol} ({timeframe})")
                else:
                    self._log.error(f"❌ V2 Extraction failed for {symbol} ({timeframe}): {result.get('error')}")
            
            # Prepare consolidated result
            overall_result = {
                "status": "success" if successful_extractions > 0 else "error",
                "symbol": symbol,
                "timeframes": timeframe_results,
                "summary": {
                    "total_timeframes": len(timeframes),
                    "successful_extractions": successful_extractions,
                    "failed_extractions": len(timeframes) - successful_extractions,
                    "indicators": indicators
                }
            }
            
            if successful_extractions == 0:
                overall_result["error"] = "All timeframe extractions failed"
            
            self._log.info(f"V2 Multi-timeframe extraction completed: {successful_extractions}/{len(timeframes)} successful")
            return overall_result
            
        except Exception as e:
            self._log.error(f"V2 Multi-timeframe extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "symbol": config.selected_pair or "Unknown",
                "indicators": indicators,
                "timeframes": timeframes
            }
    
    async def _get_decision_engine(self, config_id: str, user_id: str) -> DecisionEngineV2:
        """Get or create V2 decision engine for config."""
        if config_id not in self._decision_engines:
            engine = DecisionEngineV2(config_id, user_id)
            await engine.initialize()
            self._decision_engines[config_id] = engine
        return self._decision_engines[config_id]
    
    async def _run_decision_v2(
        self,
        config_id: str,
        config: BotConfigV2,
        extraction_result: Dict[str, Any],
        signal_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Run V2 decision engine with full context management."""
        try:
            # Check if extraction was successful
            if extraction_result.get("status") == "error":
                return {
                    "status": "error",
                    "error": "Extraction failed, cannot make decision",
                    "action": "wait",
                    "confidence": 0.0
                }
            
            # Get or create V2 decision engine
            decision_engine = await self._get_decision_engine(config_id, config.user_id)
            
            # Get symbol from config or signal data
            if signal_data:
                symbol = signal_data['symbol']
            else:
                symbol = config.selected_pair

            if not symbol:
                raise ValueError("No symbol specified for decision")
            
            # Run decision using V2 engine with full context management
            decision_result = await decision_engine.make_decision(
                symbol=symbol,
                signal_data=signal_data  # Pass signal data for validation mode
            )
            
            # Log the full decision result
            self._log.info(f"V2 Decision completed: {decision_result.get('action')} with confidence {decision_result.get('confidence', 0)}")
            self._log.info(f"🎯 Decision Engine Output: {decision_result}")
            return decision_result
            
        except Exception as e:
            self._log.error(f"V2 Decision failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "action": "wait",
                "confidence": 0.0
            }
    
    async def _run_trading_v2(
        self,
        config: BotConfigV2,
        user_id: str,
        decision_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run V2 trading execution with full paper trading integration."""
        try:
            # Check if decision was successful
            if decision_result.get("status") == "error":
                return {
                    "status": "skipped",
                    "reason": "Decision failed, no trading action"
                }
            
            action = decision_result.get("action", "wait")
            confidence = decision_result.get("confidence", 0.0)
            
            # Skip trading if action is wait, no_action, or hold
            if action in ["wait", "no_action", "hold"]:
                return {
                    "status": "skipped",
                    "reason": f"Decision was to {action}",
                    "action": action
                }
            
            # Get trading config from config
            trading_config = config.trading or {}
            symbol = decision_result.get("symbol") or config.selected_pair

            if not symbol:
                self._log.error("No symbol available for trading - decision result and config both missing symbol")
                return {
                    "status": "error",
                    "error": "No symbol specified for trading",
                    "action": action
                }
            
            # Map decision actions to trading actions
            if action in ["enter", "long"]:
                trading_action = "long"
            elif action == "short":
                trading_action = "short"
            elif action in ["exit", "close"]:
                trading_action = "close"
            else:
                # Fallback for unexpected actions - skip trading
                return {
                    "status": "skipped",
                    "reason": f"Unknown action: {action}",
                    "action": action
                }
            
            # Create comprehensive trading intent for paper trading service
            trading_intent = {
                "decision_id": decision_result.get("decision_id"),
                "user_id": user_id,
                "config_id": config.config_id,
                "symbol": symbol,
                "action": trading_action,
                "confidence": confidence,
                "stop_loss_price": decision_result.get("stop_loss_price"),
                "take_profit_price": decision_result.get("take_profit_price"),
                "reasoning": decision_result.get("reasoning", "V2 Decision Engine decision")
            }
            
            # Handle different trading actions
            if trading_action == "close":
                # For close actions, we need to close existing positions
                # First, get any open positions for this symbol and config
                try:
                    # Check if there are open positions for this config and symbol
                    from core.common.db import get_db_connection
                    open_positions = []
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT trade_id, symbol, side FROM paper_trades 
                                WHERE config_id = %s AND symbol = %s AND status = 'open'
                                ORDER BY opened_at DESC LIMIT 1
                            """, (config.config_id, symbol))
                            result = cur.fetchone()
                            if result:
                                open_positions.append({
                                    'trade_id': result[0],
                                    'symbol': result[1], 
                                    'side': result[2]
                                })
                    
                    if not open_positions:
                        return {
                            "status": "skipped",
                            "reason": f"No open positions to close for {symbol}",
                            "action": "close"
                        }
                    
                    # Close the most recent open position
                    position = open_positions[0]
                    trade_result = await self.paper_trading.close_position(
                        position['trade_id'], 
                        reason="ai_decision"
                    )
                    
                    self._log.info(f"V2 Position closed: {trade_result.get('status')} for {symbol}")
                    return trade_result
                    
                except Exception as e:
                    self._log.error(f"Failed to close position for {symbol}: {e}")
                    return {
                        "status": "error",
                        "error": f"Failed to close position: {str(e)}"
                    }
            else:
                # For long/short actions, execute normal trade
                trade_result = await self.paper_trading.execute_trade_intent(trading_intent)
                
                self._log.info(f"V2 Trading completed: {trade_result.get('status')} for {symbol}")
                return trade_result
            
        except Exception as e:
            self._log.error(f"V2 Trading failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    


# Initialize orchestrator
orchestrator = GGBotOrchestrator()


# APScheduler Setup and Job Functions
scheduler = AsyncIOScheduler()
execution_semaphore = asyncio.Semaphore(50)  # Global concurrency limit


async def run_once(user_id: str, config_id: str, timeframe: str):
    """
    Job function executed by APScheduler for each bot.
    Implements Redis idempotency and calls the orchestrator.
    """
    close_ts = last_closed_close_ts(timeframe)
    key = format_redis_idempotency_key(user_id, config_id, timeframe, close_ts)
    
    # Redis client setup
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    async with execution_semaphore:
        try:
            # Try to acquire idempotency lock with appropriate TTL
            ttl = get_redis_ttl_for_timeframe(timeframe)
            if not await redis_client.set(key, "executing", ex=ttl, nx=True):
                logger.info(f"Skipping execution for {user_id}:{config_id}:{timeframe}:{close_ts} - already executed")
                return  # Already executing/executed
            
            # Get job info for next fire time
            job_id = f"bot:{user_id}:{config_id}:{timeframe}"
            job = scheduler.get_job(job_id)
            next_fire = job.next_run_time.strftime('%Y-%m-%dT%H:%M:%SZ') if job and job.next_run_time else None
            
            # Status is handled inside orchestrator via set_execution_phase() calls
            
            try:
                # Run the autonomous cycle
                result = await orchestrator.run_autonomous_cycle(config_id, user_id)
                
                # 🔥 WEBSOCKET DELETED! Completion status handled in orchestrator via Redis + SSE
                
                # Mark as completed in Redis
                await redis_client.set(key, "completed", ex=ttl)
                logger.info(f"Completed execution for {user_id}:{config_id}:{timeframe}:{close_ts} in {result.execution_time_ms}ms")
                
            except Exception as e:
                # 🔥 WEBSOCKET DELETED! Error status would be handled via Redis + SSE if needed
                
                logger.error(f"Execution failed for {user_id}:{config_id}:{timeframe}:{close_ts}: {e}")
                # Leave key as "executing" to prevent retries on same candle
                
        finally:
            await redis_client.aclose()


def add_bot_job(user_id: str, config_id: str, timeframe: str, jitter: int = 15):
    """
    Add a scheduled job for a bot configuration.
    
    Args:
        user_id: User ID
        config_id: Configuration ID  
        timeframe: Trading timeframe
        jitter: Random jitter in seconds (default 15)
    """
    trigger = cron_for(timeframe)
    job_id = f"bot:{user_id}:{config_id}:{timeframe}"
    misfire_grace = get_misfire_grace_time(timeframe)
    
    scheduler.add_job(
        func=run_once,
        trigger=trigger,
        id=job_id,
        args=[user_id, config_id, timeframe],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=misfire_grace,
        jitter=jitter,
    )
    
    logger.info(f"Added scheduler job {job_id} with {timeframe} cadence")


def remove_bot_job(user_id: str, config_id: str, timeframe: str):
    """Remove a scheduled job for a bot configuration."""
    job_id = f"bot:{user_id}:{config_id}:{timeframe}"
    try:
        # Check if job exists first
        job = scheduler.get_job(job_id)
        if job:
            scheduler.remove_job(job_id)
            logger.info(f"Removed scheduler job {job_id}")
            return True
        else:
            logger.info(f"Job {job_id} was already removed or never existed")
            return True  # Consider it successful since the desired state (no job) is achieved
    except Exception as e:
        logger.warning(f"Failed to remove job {job_id}: {e}")
        return False


async def reconcile_active_bots():
    """
    Reconcile active bots from database on startup.
    Schedules jobs for all configurations with state='active'.
    """
    try:
        from core.common.db import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get all active bot configurations
                cur.execute("""
                    SELECT config_id, user_id, config_data 
                    FROM configurations 
                    WHERE state = 'active'
                """)
                
                active_configs = cur.fetchall()
                scheduled_count = 0
                
                for row in active_configs:
                    config_id, user_id, config_data = row
                    
                    try:
                        # Extract timeframe from config_data using the proper extraction function
                        timeframe = extract_timeframe_from_config(config_data)
                        
                        # Schedule the bot
                        add_bot_job(user_id, config_id, timeframe)
                        scheduled_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to schedule bot {config_id} for user {user_id}: {e}")
                
                logger.info(f"✅ Reconciled {scheduled_count} active bots from database")
                
    except Exception as e:
        logger.error(f"Failed to reconcile active bots: {e}")


def extract_timeframe_from_config(config: Dict[str, Any]) -> str:
    """
    Extract analysis_frequency (timeframe) from bot config.

    Args:
        config: Bot configuration dictionary (may be nested)

    Returns:
        Timeframe string (defaults to "1h"). For signal_driven bots, returns "signal_driven"
    """
    # Handle nested config structure from database
    if "config_data" in config:
        inner_config = config["config_data"]
        decision_config = inner_config.get("decision", {})
        config_type = config.get("config_type", "autonomous_trading")  # Use table field
    else:
        # Handle flat config structure
        decision_config = config.get("decision", {})
        config_type = config.get("config_type", "autonomous_trading")

    analysis_frequency = decision_config.get("analysis_frequency", "1h")

    # For signal validation bots, respect signal_driven frequency
    if config_type == "signal_validation" and analysis_frequency == "signal_driven":
        return "signal_driven"

    # For other bots, default signal_driven to 1h
    if analysis_frequency == "signal_driven":
        return "1h"

    return analysis_frequency


def get_next_run_from_scheduler(user_id: str, config_id: str) -> Optional[str]:
    """
    Get next run time for a specific bot from APScheduler.

    Args:
        user_id: User ID
        config_id: Bot configuration ID

    Returns:
        Next run time as ISO string or None if no job exists
    """
    try:
        # Get all jobs for this user
        user_jobs = [
            job for job in scheduler.get_jobs()
            if job.id.startswith(f"bot:{user_id}:{config_id}:")
        ]

        if user_jobs:
            job = user_jobs[0]  # Should only be one job per config
            return job.next_run_time.strftime('%Y-%m-%dT%H:%M:%SZ') if job.next_run_time else None

        return None
    except Exception as e:
        logger.warning(f"Failed to get next run for {user_id}:{config_id}: {e}")
        return None


def has_scheduler_job(user_id: str, config_id: str) -> bool:
    """
    Check if a bot has an active scheduler job.

    Args:
        user_id: User ID
        config_id: Bot configuration ID

    Returns:
        True if job exists, False otherwise
    """
    try:
        user_jobs = [
            job for job in scheduler.get_jobs()
            if job.id.startswith(f"bot:{user_id}:{config_id}:")
        ]
        return len(user_jobs) > 0
    except Exception as e:
        logger.warning(f"Failed to check scheduler job for {user_id}:{config_id}: {e}")
        return False


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GGBot V2 Orchestrator",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "Supabase authentication",
            "Multi-user isolation",
            "Subscription-aware LLM clients",
            "Dynamic indicator management",
            "V2 module integration (in progress)"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }


@app.get("/api/dashboard-stream")
async def dashboard_stream(
    request: Request,
    token: str = None
):
    """
    Server-Sent Events stream for unified dashboard data.
    
    Provides real-time updates for:
    - Bot configurations and status
    - Open positions and P&L
    - Recent decisions (5 per bot)
    - Account summaries
    
    Updates every 5 seconds with proper SSE headers and heartbeat.
    
    Authentication via:
    - Query parameter: ?token=<jwt_token>
    - Authorization header: Bearer <jwt_token>
    """
    import time
    from core.auth.supabase_auth import AuthMiddleware
    
    # Get token from query param or Authorization header
    auth_token = token
    if not auth_token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            auth_token = auth_header.split(" ", 1)[1]
    
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication required: provide token query param or Authorization header")
    
    # Authenticate the token
    try:
        current_user = await AuthMiddleware.authenticate_request(f"Bearer {auth_token}")
    except HTTPException as e:
        raise HTTPException(status_code=403, detail=f"Authentication failed: {e.detail}")
    
    async def generate():
        event_id = 0
        heartbeat_counter = 0
        logger.info(f"SSE generate function started for user {current_user.user_id}")
        try:
            while True:
                try:
                    # Get unified dashboard data for authenticated user
                    data = await get_unified_dashboard_data(current_user.user_id)
                    event_id += 1
                    heartbeat_counter += 1

                    # Send dashboard update event
                    yield f"id: {event_id}\n"
                    yield f"event: dashboard\n"
                    yield f"data: {json.dumps(data, default=str)}\n\n"

                    # Send heartbeat every 10 seconds (2 iterations)
                    if heartbeat_counter % 2 == 0:
                        yield f":keepalive {int(time.time())}\n\n"

                    await asyncio.sleep(5)  # 5-second update interval
                    
                except Exception as e:
                    logger.error(f"SSE data generation error for user {current_user.user_id}: {e}")
                    # Send error event
                    yield f"event: error\n"
                    yield f"data: {json.dumps({'message': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
                    await asyncio.sleep(5)  # Wait before retrying
                    
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for user {current_user.user_id}")
            return
        except Exception as e:
            logger.error(f"SSE stream error for user {current_user.user_id}: {e}")
            yield f"event: error\n"
            yield f"data: {json.dumps({'message': 'Stream terminated', 'error': str(e)})}\n\n"

    # Set proper SSE headers
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"  # Prevent nginx buffering
    }
    
    logger.info(f"Starting SSE dashboard stream for user {current_user.user_id}")
    return StreamingResponse(generate(), headers=headers, media_type="text/event-stream")


# Configuration Management Endpoints
@app.post("/api/v2/config")
async def create_config(
    request: ConfigCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Create a new bot configuration and corresponding paper trading account."""
    # Extract config_type separately for table field, exclude from JSONB data
    request_data = request.dict(exclude={"config_name"})
    config_type = request_data.pop("config_type", "autonomous_trading")

    # Add config_type back to config_data for BotConfigV2 constructor
    request_data["config_type"] = config_type

    config = await config_service.create_config(
        user_id=current_user.user_id,
        config_name=request.config_name,
        config_data=request_data
    )

    if not config:
        raise HTTPException(status_code=400, detail="Failed to create configuration")

    # Create paper trading account for the new config
    try:
        from trading.paper.supabase_service import SupabasePaperTradingService
        trading_service = SupabasePaperTradingService()
        account = await trading_service.get_or_create_paper_account(
            config_id=config.config_id,
            user_id=current_user.user_id
        )
        logger.info(f"Created paper account {account.account_id} for new config {config.config_id}")
    except Exception as e:
        logger.error(f"Failed to create paper account for config {config.config_id}: {e}")
        # Don't fail the config creation - account can be created later

    return {
        "status": "success",
        "config": config.to_dict()
    }


@app.get("/api/v2/config")
async def list_configs(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """List all configurations for the current user."""
    configs = await config_service.list_configs(current_user.user_id)
    
    return {
        "status": "success",
        "configs": [config.to_dict() for config in configs],
        "count": len(configs)
    }


@app.get("/api/v2/config/{config_id}")
async def get_config(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get a specific configuration."""
    config = await config_service.get_config(config_id, current_user.user_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return {
        "status": "success",
        "config": config.to_dict()
    }


@app.put("/api/v2/config/{config_id}")
async def update_config(
    config_id: str,
    request: ConfigUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Update a configuration and automatically reschedule if active."""
    # Filter out None values
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    config_name = update_data.pop("config_name", None)
    config_type = update_data.pop("config_type", None)
    
    # Check if this is an active bot before update
    current_state = await config_service.get_bot_state(config_id, current_user.user_id)
    was_active = current_state == 'active'
    
    # Get old config to compare timeframes
    old_config = await config_service.get_config(config_id, current_user.user_id)
    old_timeframe = extract_timeframe_from_config(old_config.to_jsonb()) if old_config else None
    
    config = await config_service.update_config(
        config_id=config_id,
        user_id=current_user.user_id,
        config_data=update_data,
        config_name=config_name,
        config_type=config_type
    )
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found or update failed")
    
    # If bot was active, check if timeframe changed and reschedule if needed
    reschedule_info = None
    if was_active and scheduler.running:
        new_timeframe = extract_timeframe_from_config(config.to_jsonb())
        
        if old_timeframe != new_timeframe:
            logger.info(f"Timeframe changed from {old_timeframe} to {new_timeframe} for active bot {config_id}")
            
            # Remove old job
            if old_timeframe:
                old_removed = remove_bot_job(current_user.user_id, config_id, old_timeframe)
            else:
                old_removed = True
            
            # Add new job with new timeframe
            add_bot_job(current_user.user_id, config_id, new_timeframe)
            
            # Get next run time for response
            job_id = f"bot:{current_user.user_id}:{config_id}:{new_timeframe}"
            job = scheduler.get_job(job_id)
            next_run = job.next_run_time.strftime('%Y-%m-%dT%H:%M:%SZ') if job and job.next_run_time else None
            
            reschedule_info = {
                "rescheduled": True,
                "old_timeframe": old_timeframe,
                "new_timeframe": new_timeframe,
                "next_run": next_run
            }
            
            # 🔥 WEBSOCKET DELETED! Schedule changes will show up in SSE stream
    
    response = {
        "status": "success",
        "config": config.to_dict()
    }
    
    if reschedule_info:
        response["schedule_update"] = reschedule_info
    
    return response


@app.delete("/api/v2/config/{config_id}")
async def delete_config(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Delete a configuration."""
    success = await config_service.delete_config(config_id, current_user.user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return {
        "status": "success",
        "message": "Configuration deleted successfully"
    }


# Orchestration Endpoints
@app.post("/api/v2/orchestrate/{config_id}")
async def run_orchestration(
    config_id: str,
    request: SignalOrchestrationRequest = SignalOrchestrationRequest(),
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> OrchestrationResult:
    """Run autonomous trading cycle or signal validation for a configuration."""
    try:
        result = await orchestrator.run_autonomous_cycle(
            config_id,
            current_user.user_id,
            signal_data=request.signal_data,
            override_symbol=request.override_symbol
        )
        
        if result.status == "error":
            # Extract error details from the result object
            error_detail = "Unknown orchestration error"
            if result.extraction_result and isinstance(result.extraction_result, dict):
                error_detail = result.extraction_result.get('error', error_detail)
            
            # Log the full result for debugging
            logger.error(f"Orchestration failed for config {config_id}: {error_detail}")
            logger.error(f"Full result object: {result.dict()}")
            raise HTTPException(status_code=500, detail=f"Orchestration failed: {error_detail}")
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log any unexpected exceptions
        logger.error(f"Unexpected error in orchestration endpoint for config {config_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/test/signal-publishing/{config_id}")
async def test_signal_publishing(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Test signal publishing functionality with mock data."""
    try:
        from signals.publishing_service import publish_signal_to_telegram
        
        # Mock signal data for testing
        mock_signal_data = {
            'symbol': 'BTC/USDT',
            'direction': 'LONG',
            'source': 'manual_trigger',
            'raw_message': 'Test signal for Telegram publishing functionality'
        }
        
        # Mock decision result
        mock_decision_result = {
            'action': 'VALIDATE',
            'confidence': 0.85,
            'reasoning': 'This is a test signal to validate the Telegram publishing functionality. The signal shows strong technical indicators with RSI oversold conditions and bullish MACD crossover.'
        }
        
        # Attempt to publish the test signal
        success = await publish_signal_to_telegram(
            config_id=config_id,
            user_id=current_user.user_id,
            signal_data=mock_signal_data,
            decision_result=mock_decision_result
        )
        
        return {
            "status": "success" if success else "failed",
            "message": "Test signal published successfully" if success else "Failed to publish test signal",
            "signal_data": mock_signal_data,
            "decision_result": mock_decision_result,
            "config_id": config_id,
            "user_id": current_user.user_id
        }
        
    except Exception as e:
        logger.error(f"Signal publishing test failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Signal publishing test failed: {str(e)}")


# User Management Endpoints
@app.get("/api/v2/user/profile")
async def get_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get current user profile."""
    profile = await current_user.load_profile()
    
    return {
        "status": "success",
        "profile": {
            "user_id": profile.user_id,
            "subscription_tier": profile.subscription_tier.value,
            "subscription_status": profile.subscription_status.value,
            "can_use_premium_features": profile.can_use_premium_features,
            "requires_own_llm_keys": profile.requires_own_llm_keys,
            "can_publish_telegram_signals": profile.can_publish_telegram_signals,
            "can_use_signal_validation": profile.can_use_signal_validation,
            "paid_data_points": profile.paid_data_points
        }
    }


@app.get("/api/v2/user/indicators")
async def get_user_indicators(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get indicators available to the current user."""
    indicators = await IndicatorService.get_user_available_indicators(current_user.user_id)
    
    return {
        "status": "success",
        "indicators": indicators,
        "count": len(indicators)
    }


@app.get("/api/v2/data-sources-with-points")
async def get_data_sources_with_points(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get all data sources with their data points for frontend configuration."""
    try:
        from core.common.db import get_db_connection
        
        # Get user profile to check paid data points
        profile = await current_user.load_profile()
        paid_data_points = profile.paid_data_points if hasattr(profile, 'paid_data_points') else []
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get all data sources with their data points
                cur.execute("""
                    SELECT 
                        ds.source_id,
                        ds.name as source_name,
                        ds.display_name as source_display_name,
                        ds.description as source_description,
                        ds.enabled as source_enabled,
                        ds.requires_premium as source_requires_premium,
                        ds.sort_order as source_sort_order,
                        dp.data_point_id,
                        dp.name as point_name,
                        dp.display_name as point_display_name,
                        dp.description as point_description,
                        dp.config_values,
                        dp.requires_premium as point_requires_premium,
                        dp.enabled as point_enabled,
                        dp.sort_order as point_sort_order
                    FROM data_sources ds
                    LEFT JOIN data_points dp ON ds.source_id = dp.source_id
                    WHERE ds.enabled = true AND (dp.enabled IS NULL OR dp.enabled = true)
                    ORDER BY ds.sort_order ASC, dp.sort_order ASC
                """)
                
                rows = cur.fetchall()
                
                # Group by data source
                sources_dict = {}
                for row in rows:
                    source_id = row[0]
                    
                    if source_id not in sources_dict:
                        sources_dict[source_id] = {
                            "source_id": source_id,
                            "name": row[1],
                            "display_name": row[2],
                            "description": row[3],
                            "enabled": row[4],
                            "requires_premium": row[5],
                            "sort_order": row[6],
                            "data_points": []
                        }
                    
                    # Add data point if it exists (LEFT JOIN might have nulls)
                    if row[7] is not None:  # data_point_id
                        point_requires_premium = row[12]
                        point_name = row[8]
                        
                        # Check if user has access to this data point
                        has_access = not point_requires_premium or point_name in paid_data_points
                        
                        data_point = {
                            "data_point_id": row[7],
                            "name": point_name,
                            "display_name": row[9],
                            "description": row[10],
                            "config_values": row[11],
                            "requires_premium": point_requires_premium,
                            "enabled": row[13],
                            "sort_order": row[14],
                            "has_access": has_access,
                            "is_locked": point_requires_premium and not has_access
                        }
                        
                        sources_dict[source_id]["data_points"].append(data_point)
                
                # Convert to list and sort
                sources_list = list(sources_dict.values())
                sources_list.sort(key=lambda x: x["sort_order"])
                
                for source in sources_list:
                    source["data_points"].sort(key=lambda x: x["sort_order"])
                
                return {
                    "status": "success",
                    "data_sources": sources_list,
                    "paid_data_points": paid_data_points,
                    "count": len(sources_list)
                }
                
    except Exception as e:
        logger.error(f"Failed to get data sources with points: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data sources: {str(e)}")


# LLM Credential Management Endpoints
@app.post("/api/v2/user/llm-credentials")
async def store_llm_credential(
    request: Dict[str, str],
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Store a user's LLM API credential securely in Vault."""
    try:
        from core.auth.vault_utils import store_credential
        
        credential_name = request.get("credential_name")
        provider = request.get("provider") 
        api_key = request.get("api_key")
        
        if not all([credential_name, provider, api_key]):
            raise HTTPException(status_code=400, detail="Missing required fields: credential_name, provider, api_key")
        
        if provider not in ["openai", "deepseek", "anthropic", "xai"]:
            raise HTTPException(status_code=400, detail="Invalid provider. Must be one of: openai, deepseek, anthropic, xai")
        
        user_id = current_user.user_id
        credential_id = await store_credential(user_id, credential_name, provider, api_key)
        
        if credential_id is None:
            raise HTTPException(status_code=500, detail="Failed to store credential")
        
        return {
            "status": "success",
            "credential_id": credential_id,
            "message": f"Credential '{credential_name}' stored securely"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store LLM credential: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store credential: {str(e)}")


@app.get("/api/v2/user/llm-credentials")
async def list_llm_credentials(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """List all LLM credentials for the current user (without API keys)."""
    try:
        from core.auth.vault_utils import list_credentials
        
        user_id = current_user.user_id
        credentials = await list_credentials(user_id)
        
        return {
            "status": "success",
            "credentials": credentials,
            "count": len(credentials)
        }
        
    except Exception as e:
        logger.error(f"Failed to list LLM credentials: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list credentials: {str(e)}")


@app.get("/api/v2/user/llm-credentials/{credential_name}")
async def get_llm_credential(
    credential_name: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get a specific LLM credential (with API key for internal use only)."""
    try:
        from core.auth.vault_utils import get_credential
        
        user_id = current_user.user_id
        credential = await get_credential(user_id, credential_name)
        
        if credential is None:
            raise HTTPException(status_code=404, detail=f"Credential '{credential_name}' not found")
        
        return {
            "status": "success",
            "credential": credential
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get LLM credential: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get credential: {str(e)}")


@app.delete("/api/v2/user/llm-credentials/{credential_name}")
async def delete_llm_credential(
    credential_name: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Delete a user's LLM credential."""
    try:
        from core.auth.vault_utils import delete_credential
        
        user_id = current_user.user_id
        success = await delete_credential(user_id, credential_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Credential '{credential_name}' not found")
        
        return {
            "status": "success",
            "message": f"Credential '{credential_name}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete LLM credential: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete credential: {str(e)}")


# Bot Data Endpoints for Dashboard
@app.get("/api/v2/bot/{config_id}/metrics")
async def get_bot_metrics(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get performance metrics for a bot configuration."""
    try:
        from core.common.db import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Query paper account summary
                cur.execute("""
                    SELECT initial_balance, current_balance, total_pnl, 
                           total_trades, win_trades, loss_trades
                    FROM paper_accounts 
                    WHERE config_id = %s AND user_id = %s
                """, (config_id, current_user.user_id))
                
                account = cur.fetchone()
                if not account:
                    # Return default metrics if no account exists yet
                    return {
                        "status": "success",
                        "config_id": config_id,
                        "account": {
                            "balance": 10000.0,
                            "total_pnl": 0.0
                        },
                        "performance": {
                            "total_trades": 0,
                            "win_rate": 0.0,
                            "avg_trade": 0.0
                        }
                    }
                
                # Calculate additional metrics from paper_trades
                cur.execute("""
                    SELECT AVG(realized_pnl) as avg_trade,
                           COUNT(*) as closed_trades,
                           AVG(EXTRACT(EPOCH FROM (closed_at - opened_at))/3600) as avg_duration_hours
                    FROM paper_trades 
                    WHERE config_id = %s AND user_id = %s AND status = 'closed'
                """, (config_id, current_user.user_id))
                
                trade_stats = cur.fetchone()
                
                win_rate = float(account['win_trades']) / float(account['total_trades']) if account['total_trades'] > 0 else 0.0
                
                return {
                    "status": "success",
                    "config_id": config_id,
                    "account": {
                        "balance": float(account['current_balance']),
                        "total_pnl": float(account['total_pnl'])
                    },
                    "performance": {
                        "total_trades": account['total_trades'],
                        "win_trades": account['win_trades'],
                        "loss_trades": account['loss_trades'],
                        "win_rate": round(win_rate, 3),
                        "avg_trade": float(trade_stats['avg_trade'] or 0) if trade_stats else 0.0
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed to get bot metrics for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot metrics")


@app.get("/api/v2/bot/{config_id}/positions")
async def get_bot_positions(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get live positions for a bot configuration."""
    try:
        from core.common.db import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT symbol, side, entry_price, current_price, size_usd, 
                           unrealized_pnl, leverage, opened_at
                    FROM paper_trades 
                    WHERE config_id = %s AND user_id = %s AND status = 'open'
                    ORDER BY opened_at DESC
                """, (config_id, current_user.user_id))
                
                positions = []
                for row in cur.fetchall():
                    # Map database side to display format
                    side_display = "LONG" if row['side'].lower() == 'buy' else "SHORT"
                    
                    positions.append({
                        "symbol": row['symbol'],
                        "side": side_display,
                        "size": float(row['size_usd']),
                        "entryPrice": float(row['entry_price']),
                        "currentPrice": float(row['current_price'] or row['entry_price']),
                        "unrealizedPnL": float(row['unrealized_pnl'] or 0),
                        "timestamp": row['opened_at'].isoformat() + "Z"
                    })
                
                return {
                    "status": "success",
                    "config_id": config_id,
                    "positions": positions
                }
                
    except Exception as e:
        logger.error(f"Failed to get bot positions for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot positions")


@app.get("/api/v2/bot/{config_id}/trades")
async def get_bot_trades(
    config_id: str,
    limit: int = 100,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get trade history for a bot configuration."""
    try:
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT trade_id, symbol, side, entry_price, size_usd, realized_pnl,
                           opened_at, closed_at, confidence_score, status
                    FROM paper_trades
                    WHERE config_id = %s AND user_id = %s
                    ORDER BY opened_at DESC
                    LIMIT %s
                """, (config_id, current_user.user_id, limit))
                
                trades = []
                for row in cur.fetchall():
                    trades.append({
                        "id": str(row['trade_id']),
                        "symbol": row['symbol'],
                        "side": row['side'],
                        "quantity": float(row['size_usd']),
                        "price": float(row['entry_price']),
                        "pnl": float(row['realized_pnl'] or 0),
                        "timestamp": row['opened_at'].isoformat() + "Z",
                        "closed_at": row['closed_at'].isoformat() + "Z" if row['closed_at'] else None,
                        "confidence": float(row['confidence_score'] or 0),
                        "status": row['status']
                    })
                
                return {
                    "status": "success", 
                    "config_id": config_id,
                    "trades": trades,
                    "count": len(trades)
                }
                
    except Exception as e:
        logger.error(f"Failed to get bot trades for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot trades")


@app.get("/api/v2/bot/{config_id}/account")
async def get_bot_account(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get account summary for a bot configuration."""
    try:
        from trading.paper.supabase_service import SupabasePaperTradingService
        
        service = SupabasePaperTradingService()
        
        # Get account summary
        account_summary = await service.get_account_summary(config_id)
        
        if "error" in account_summary:
            return {
                "status": "success",
                "config_id": config_id,
                "account": {
                    "initial_balance": 10000.0,
                    "current_balance": 10000.0,
                    "total_pnl": 0.0,
                    "open_positions": 0,
                    "total_trades": 0,
                    "win_trades": 0,
                    "loss_trades": 0,
                    "win_rate": 0.0,
                    "total_return_pct": 0.0
                }
            }
        
        # Calculate additional metrics
        initial_balance = account_summary.get("initial_balance", 10000.0)
        current_balance = account_summary.get("current_balance", 10000.0)
        total_pnl = account_summary.get("total_pnl", 0.0)
        
        # Total return percentage
        total_return_pct = ((current_balance - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0.0
        
        return {
            "status": "success",
            "config_id": config_id,
            "account": {
                "initial_balance": initial_balance,
                "current_balance": current_balance,
                "total_pnl": total_pnl,
                "open_positions": account_summary.get("open_positions", 0),
                "total_trades": account_summary.get("total_trades", 0),
                "win_trades": account_summary.get("win_trades", 0),
                "loss_trades": account_summary.get("loss_trades", 0),
                "win_rate": account_summary.get("win_rate", 0.0),
                "total_return_pct": round(total_return_pct, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get account for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get account")


@app.get("/api/v2/bot/{config_id}/decisions")
async def get_bot_decisions(
    config_id: str,
    limit: int = 50,
    hours_back: int = 24,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get decision history for a bot configuration."""
    try:
        from core.common.db import get_db_connection
        
        # Validate config belongs to user
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Query decisions for this config in the last N hours, ordered by newest first
                cur.execute("""
                    SELECT 
                        decision_id,
                        symbol,
                        action,
                        status,
                        confidence,
                        reasoning,
                        prompt,
                        market_data,
                        decision_data,
                        created_at
                    FROM decisions 
                    WHERE config_id = %s 
                        AND user_id = %s
                        AND created_at >= NOW() - make_interval(hours => %s)
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (config_id, current_user.user_id, hours_back, limit))
                
                rows = cur.fetchall()
                
                # Transform database rows to API format
                decisions = []
                for row in rows:
                    decisions.append({
                        "decision_id": str(row['decision_id']),
                        "symbol": row['symbol'],
                        "action": row['action'],
                        "status": row['status'],
                        "confidence": float(row['confidence']) if row['confidence'] else 0.0,
                        "reasoning": row['reasoning'],
                        "prompt": row['prompt'],
                        "market_data": row['market_data'],
                        "decision_data": row['decision_data'],
                        "created_at": row['created_at'].isoformat() if row['created_at'] else None
                    })
                
                logger.info(f"✅ Retrieved {len(decisions)} decisions for config {config_id}")
                
                return {
                    "status": "success",
                    "config_id": config_id,
                    "decisions": decisions,
                    "count": len(decisions),
                    "filters": {
                        "limit": limit,
                        "hours_back": hours_back
                    }
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get decisions for {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get decisions")


# Bot Lifecycle Endpoints (placeholders for now)
@app.post("/api/v2/bot/{config_id}/start")
async def start_bot(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Start a bot by scheduling its autonomous trading cycle."""
    try:
        # Get bot configuration
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        # Check if already active
        current_state = await config_service.get_bot_state(config_id, current_user.user_id)
        if current_state == 'active':
            return {
                "status": "already_active",
                "message": "Bot is already running",
                "config_id": config_id
            }
        
        # Extract timeframe from config
        config_dict = config.to_jsonb()
        timeframe = extract_timeframe_from_config(config_dict)

        # Handle signal_driven bots differently - they don't get scheduled jobs
        if timeframe == "signal_driven":
            # Update state to active (but don't schedule)
            success = await config_service.set_bot_state(config_id, current_user.user_id, 'active')
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update bot state")

            next_run = None  # Signal-driven bots don't have scheduled runs
        else:
            # Schedule the bot job for time-based bots
            add_bot_job(current_user.user_id, config_id, timeframe)

            # Update state to active
            success = await config_service.set_bot_state(config_id, current_user.user_id, 'active')
            if not success:
                # Remove the job if state update failed
                remove_bot_job(current_user.user_id, config_id, timeframe)
                raise HTTPException(status_code=500, detail="Failed to update bot state")

            # Get next run time for response
            job_id = f"bot:{current_user.user_id}:{config_id}:{timeframe}"
            job = scheduler.get_job(job_id)
            next_run = job.next_run_time.strftime('%Y-%m-%dT%H:%M:%SZ') if job and job.next_run_time else None
        
        # 🔥 WEBSOCKET DELETED! Bot state changes will show up in SSE stream
        
        return {
            "status": "started",
            "config_id": config_id,
            "timeframe": timeframe,
            "next_run": next_run,
            "message": f"Bot scheduled for {timeframe} trading"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start bot {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")


@app.post("/api/v2/bot/{config_id}/stop")
async def stop_bot(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Stop a bot by removing its scheduled job and updating state."""
    try:
        # Get bot configuration
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        # Check if already inactive
        current_state = await config_service.get_bot_state(config_id, current_user.user_id)
        if current_state == 'inactive':
            return {
                "status": "already_stopped",
                "message": "Bot is already stopped",
                "config_id": config_id
            }
        
        # Extract timeframe from config
        config_dict = config.to_jsonb()
        timeframe = extract_timeframe_from_config(config_dict)

        # Handle signal_driven bots differently - they don't have scheduled jobs to remove
        if timeframe == "signal_driven":
            job_removed = True  # No job to remove, so consider it successful
        else:
            # Remove the scheduled job for time-based bots
            job_removed = remove_bot_job(current_user.user_id, config_id, timeframe)

        # Update state to inactive
        success = await config_service.set_bot_state(config_id, current_user.user_id, 'inactive')
        if not success:
            logger.warning(f"Job removed but failed to update state for bot {config_id}")
        
        # 🔥 WEBSOCKET DELETED! Bot state changes will show up in SSE stream
        
        return {
            "status": "stopped",
            "config_id": config_id,
            "timeframe": timeframe,
            "job_removed": job_removed,
            "message": "Bot stopped successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop bot {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")


@app.get("/api/v2/scheduler/status")
async def get_scheduler_status(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get scheduler status and active jobs for the current user."""
    try:
        # Get all active jobs for the current user
        user_jobs = [
            job for job in scheduler.get_jobs() 
            if job.id.startswith(f"bot:{current_user.user_id}:")
        ]
        
        # Format job information
        jobs_info = []
        for job in user_jobs:
            # Parse job ID to extract config_id and timeframe
            parts = job.id.split(":")
            if len(parts) >= 4:
                config_id = parts[2]
                timeframe = parts[3]
                
                jobs_info.append({
                    "job_id": job.id,
                    "config_id": config_id,
                    "timeframe": timeframe,
                    "next_run": job.next_run_time.strftime('%Y-%m-%dT%H:%M:%SZ') if job.next_run_time else None,
                    "misfire_grace_time": job.misfire_grace_time
                })
        
        return {
            "status": "success",
            "scheduler_running": scheduler.state == STATE_RUNNING,
            "active_jobs": jobs_info,
            "job_count": len(user_jobs),
            "total_jobs_in_scheduler": len(scheduler.get_jobs())
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")


@app.post("/api/v2/scheduler/reconcile")
async def manual_reconcile(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Manually trigger scheduler reconciliation (admin function)."""
    try:
        if not scheduler.state == STATE_RUNNING:
            raise HTTPException(status_code=503, detail="Scheduler is not running")
        
        # Store counts before reconciliation
        jobs_before = len(scheduler.get_jobs())
        user_jobs_before = len([j for j in scheduler.get_jobs() if j.id.startswith(f"bot:{current_user.user_id}:")])
        
        # Run reconciliation
        await reconcile_active_bots()
        
        # Check counts after
        jobs_after = len(scheduler.get_jobs())
        user_jobs_after = len([j for j in scheduler.get_jobs() if j.id.startswith(f"bot:{current_user.user_id}:")])
        
        return {
            "status": "success",
            "message": "Reconciliation completed",
            "jobs_before": jobs_before,
            "jobs_after": jobs_after,
            "user_jobs_before": user_jobs_before,
            "user_jobs_after": user_jobs_after,
            "change": jobs_after - jobs_before
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual reconciliation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")


@app.get("/api/v2/bot/{config_id}/status")
async def get_bot_status(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get bot status with real scheduler state."""
    try:
        # Get bot state from database
        state = await config_service.get_bot_state(config_id, current_user.user_id)
        config = await config_service.get_config(config_id, current_user.user_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
            
        # Extract timeframe from config
        config_dict = config.to_jsonb()
        timeframe = extract_timeframe_from_config(config_dict)
        
        # Check if job exists in scheduler
        job_id = f"bot:{current_user.user_id}:{config_id}:{timeframe}"
        job = scheduler.get_job(job_id)
        next_run = job.next_run_time.strftime('%Y-%m-%dT%H:%M:%SZ') if job and job.next_run_time else None
        
        return {
            "status": "success",
            "config_id": config_id,
            "bot_status": state or "inactive",  # 'active' or 'inactive'
            "is_scheduled": job is not None,
            "next_run": next_run,
            "timeframe": timeframe,
            "scheduler_job_exists": job is not None
        }
        
    except Exception as e:
        logger.error(f"Failed to get bot status for {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bot status: {str(e)}")


# 🔥 OLD WEBSOCKET SUPPORT DELETED - Now using SSE stream!
# 🔥 WEBSOCKET STATUS FUNCTIONS DELETED! 
# Status now via Redis + SSE stream at /api/dashboard-stream


# 🔥 ALL WEBSOCKET MESSAGE FUNCTIONS DELETED!


# 🔥 WEBSOCKET CODE DELETED! Now using SSE at /api/dashboard-stream 🔥


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


# Development Mode: Override authentication for Phase 7 testing
import os
if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true":
    logger.warning("⚠️  DEVELOPMENT MODE ACTIVE: Using mock authentication - DO NOT USE IN PRODUCTION")
    app.dependency_overrides[get_current_user_v2] = get_mock_user_for_dev

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "ggbot:app",
        host="0.0.0.0",
        port=8000,  # V2 Orchestrator port (matches nginx configuration)
        reload=True,
        log_level="info"
    )