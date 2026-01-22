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

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Query, Header
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, field_serializer
import uvicorn
import json
import psycopg2.extras
import numpy as np
import stripe

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

class ServiceUser:
    """Represents an authenticated service."""
    def __init__(self, service_name: str):
        self.service_name = service_name

import time
from collections import defaultdict

service_calls = defaultdict(list)

async def get_service_user(request: Request):
    """Authenticate service-to-service requests."""
    auth_header = request.headers.get('authorization', '')
    service_header = request.headers.get('x-service-auth', '')

    # Allow multiple trusted services
    allowed_services = ['signal-listener', 'agent-runner']

    if not auth_header.startswith('Bearer ') or service_header not in allowed_services:
        raise HTTPException(status_code=401, detail="Service authentication required")

    # Rate limiting per service
    now = time.time()
    calls = service_calls[service_header]
    service_calls[service_header] = [t for t in calls if now - t < 60]

    # Different rate limits per service (agent-runner needs higher limit)
    rate_limit = 600 if service_header == 'agent-runner' else 120  # 10 req/sec vs 2 req/sec
    if len(service_calls[service_header]) >= rate_limit:
        raise HTTPException(status_code=429, detail="Service rate limit exceeded")

    service_calls[service_header].append(now)

    token = auth_header.split(' ')[1]
    service_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not service_key or token != service_key:
        raise HTTPException(status_code=401, detail="Invalid service token")

    return ServiceUser(service_name=service_header)

async def get_mock_user_for_dev():
    """Mock user for development."""
    return AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000000",
        email="user@example.com",
        claims={"sub": "00000000-0000-0000-0000-000000000000", "email": "user@example.com"}
    )
from core.services.config_service import ConfigService, BotConfigV2, config_service
from core.services.user_service import UserService, user_service
from core.services.llm_service import LLMService, llm_service
from core.services.indicator_service import IndicatorService
from core.common.logger import logger as base_logger

DEMO_MODE = os.getenv("GGBOT_DEMO_MODE", "false").lower() == "true"

logger = base_logger

from extraction.v2.extraction_engine import ExtractionEngineV2
from decision.engine_v2 import DecisionEngineV2
from trading.paper.supabase_service import SupabasePaperTradingService
from trading.live.symphony_service import SymphonyLiveTradingService
from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService
from signals.publishing_service import publish_signal_to_telegram
from core.domain import Decision, DecisionAction, DecisionStatus, UserProfile, Symbol, Confidence
class ConfigCreateRequest(BaseModel):
    config_name: str
    schema_version: str = "2.1"
    config_type: str = "scheduled_trading"
    trading_mode: str = "paper"  # 'paper' | 'symphony' | 'aster'
    symphony_agent_id: Optional[str] = None  # Required when trading_mode='symphony'
    selected_pair: Optional[str] = "BTC/USDT"  # Optional for agents
    extraction: Optional[Dict[str, Any]] = None  # Optional for agents and signal_validation
    decision: Optional[Dict[str, Any]] = None  # Optional for agents
    trading: Dict[str, Any]  # Always required
    llm_config: Optional[Dict[str, Any]] = None  # Optional for agents
    telegram_integration: Optional[Dict[str, Any]] = None
    agent_strategy: Optional[Dict[str, Any]] = None  # For agent-type configs


class ConfigUpdateRequest(BaseModel):
    config_name: Optional[str] = None
    schema_version: Optional[str] = None
    config_type: Optional[str] = None
    trading_mode: Optional[str] = None  # Allow updating trading mode
    symphony_agent_id: Optional[str] = None  # Allow updating Symphony agent ID
    profile_image_url: Optional[str] = None  # Bot avatar image URL
    selected_pair: Optional[str] = None
    extraction: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    trading: Optional[Dict[str, Any]] = None
    llm_config: Optional[Dict[str, Any]] = None
    telegram_integration: Optional[Dict[str, Any]] = None
    agent_strategy: Optional[Dict[str, Any]] = None


class SignalOrchestrationRequest(BaseModel):
    signal_data: Optional[Dict[str, Any]] = None
    override_symbol: Optional[str] = None


def serialize_numpy_types(obj):
    """
    Recursively convert numpy types, pandas types, and Decimal to Python native types.

    This is a belt-and-suspenders approach to ensure ALL numpy/pandas types are
    converted before Pydantic serialization, preventing serialization errors.
    """
    from decimal import Decimal
    import pandas as pd

    # Handle numpy integer types
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    # Handle numpy float types
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    # Handle numpy boolean types (CRITICAL: This prevents PydanticSerializationError)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    # Handle numpy arrays
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    # Handle pandas NA/NaT values
    elif pd.isna(obj):
        return None
    # Handle Decimal types
    elif isinstance(obj, Decimal):
        return float(obj)
    # Recursively handle dictionaries
    elif isinstance(obj, dict):
        return {key: serialize_numpy_types(value) for key, value in obj.items()}
    # Recursively handle lists
    elif isinstance(obj, list):
        return [serialize_numpy_types(item) for item in obj]
    # Recursively handle tuples (convert to list)
    elif isinstance(obj, tuple):
        return [serialize_numpy_types(item) for item in obj]
    # Return all other types as-is
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


        # Start APScheduler (if enabled)
        enable_scheduler = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
        if enable_scheduler:
            scheduler.start()
            logger.info("✅ APScheduler started")

            # Schedule daily Stripe meter reporting (midnight UTC)
            from billing.stripe_meter_reporter import run_daily_report
            from apscheduler.triggers.cron import CronTrigger

            scheduler.add_job(
                func=run_daily_report,
                trigger=CronTrigger(hour=0, minute=0),  # Midnight UTC daily
                id="stripe_meter_reporting",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
                misfire_grace_time=3600  # 1 hour grace period
            )
            logger.info("✅ Stripe meter reporting scheduled (daily at midnight UTC)")
        else:
            logger.info("⏸️  APScheduler disabled (ENABLE_SCHEDULER=false)")

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

# Include API routers
from api.paper_trading import router as paper_trading_router
from api.agent import router as agent_router
from api.activities import router as activities_router
from api.snapshots import router as snapshots_router
from api.assistant import router as assistant_router
from api.admin import router as admin_router
from api.public import router as public_router
from api.usage import router as usage_router
app.include_router(paper_trading_router)
app.include_router(agent_router)
app.include_router(activities_router)
app.include_router(snapshots_router)
app.include_router(assistant_router)
app.include_router(admin_router)
app.include_router(public_router)
app.include_router(usage_router)


class GGBotOrchestrator:
    """Main orchestrator class coordinating all V2 modules with full integration."""
    
    def __init__(self):
        self.config_service = config_service
        self.llm_service = llm_service
        self.paper_trading = SupabasePaperTradingService()
        self.symphony_trading = SymphonyLiveTradingService()
        self.aster_trading = AsterDEXV3LiveTradingService()
        self._log = logger.bind(component="orchestrator")

        self._extraction_engines = {}
        self._decision_engines = {}
    
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
            config = await self.config_service.get_config(config_id, user_id)
            if not config:
                raise HTTPException(status_code=404, detail="Configuration not found")

            # Permission check: Verify user can still activate/run bots
            user_profile = await user_service.get_profile(user_id)
            is_first_run_allowed = False  # Creation auto-run (free, doesn't count)
            is_free_manual_run = False    # Manual "Run Once" using free runs

            if not user_profile.can_activate_bots:
                # Check if this is their free first run (creation auto-run)
                if not config.first_run_used:
                    self._log.info(
                        f"Allowing free first run for config {config_id} - "
                        f"user {user_id} is on {user_profile.subscription_tier.value} tier"
                    )
                    is_first_run_allowed = True
                # Check if they have free manual runs remaining
                elif config.free_runs_remaining > 0:
                    self._log.info(
                        f"Allowing free manual run for config {config_id} - "
                        f"{config.free_runs_remaining} free runs remaining"
                    )
                    is_free_manual_run = True
                else:
                    self._log.warning(
                        f"Blocking bot execution for config {config_id} - "
                        f"user {user_id} lost activation permission (tier: {user_profile.subscription_tier.value}), "
                        f"no free runs remaining"
                    )
                    # Auto-deactivate bot if user lost permission
                    await self.config_service.set_bot_state(config_id, user_id, "inactive")
                    raise HTTPException(
                        status_code=403,
                        detail="No free test runs remaining. Subscribe to run your bot again."
                    )

            self._log.info(f"🔍 DEBUG: config.config_type = '{config.config_type}', signal_data present = {signal_data is not None}")

            # Execute the appropriate cycle
            if config.config_type == "signal_validation":
                if signal_data:
                    result = await self._run_signal_validation_cycle(
                        config, signal_data, override_symbol
                    )
                else:
                    latest_signal = await self._fetch_latest_ggshot_signal()
                    signal_dict = self._signal_data_to_dict(latest_signal)
                    result = await self._run_signal_validation_cycle(
                        config, signal_dict, override_symbol
                    )
            else:
                result = await self._run_autonomous_trading_cycle(config)

            # Handle free run tracking after successful execution
            if result.status != "error":
                if is_first_run_allowed:
                    # Mark creation auto-run as used
                    await self.config_service.mark_first_run_used(config_id)
                    self._log.info(f"Marked first run used for config {config_id}")
                elif is_free_manual_run:
                    # Decrement free manual runs
                    remaining = await self.config_service.decrement_free_runs(config_id)
                    self._log.info(f"Decremented free runs for config {config_id}, {remaining} remaining")

            return result
            
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
            extraction_engine = await self._get_extraction_engine(user_id)

            extraction_config = config.extraction or {}
            requested_indicators = self._extract_indicators_from_config(extraction_config)
            timeframes = self._extract_timeframes_from_config(extraction_config)

            from core.sse import set_execution_phase
            await set_execution_phase(config_id, "extracting", f"Gathering market data for {config.selected_pair}...")

            extraction_result = await self._run_extraction_v2(
                extraction_engine, config, user_id, requested_indicators, timeframes
            )

            # UX delay: Give extraction phase time to display
            await asyncio.sleep(3)

            await set_execution_phase(config_id, "deciding", "Analyzing market conditions for trading opportunities...")

            decision_result = await self._run_decision_v2(
                config_id, config, extraction_result
            )

            # UX delay: Give decision phase time to display (longest phase for AI reasoning)
            await asyncio.sleep(7)

            action = decision_result.get('action', 'wait')
            if action in ['wait', 'no_action', 'hold']:
                message = "No trading opportunity found - waiting for better setup..."
            elif action == 'long':
                message = "Opening long position..."
            elif action == 'short':
                message = "Opening short position..."
            elif action == 'close':
                message = "Closing position..."
            else:
                message = f"Executing trade..."

            await set_execution_phase(config_id, "trading", message)

            trading_result = await self._run_trading_v2(
                config, user_id, decision_result
            )

            # UX delay: Give trading phase time to display
            await asyncio.sleep(3)
            
            if self._should_publish_signal(config, decision_result):
                await self._trigger_signal_publishing(
                    config, {}, decision_result
                )
            
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
            symbol = override_symbol or signal_data.get('symbol') or config.selected_pair

            if not symbol:
                raise ValueError("No symbol specified for signal validation")

            self._log.info(f"Running signal validation for {symbol}")

            extraction_config = config.extraction or {}
            signal_indicators = self._extract_indicators_from_config(extraction_config)
            timeframes = self._extract_timeframes_from_config(extraction_config)

            extraction_engine = await self._get_extraction_engine(user_id)

            from core.sse import set_execution_phase
            await set_execution_phase(config_id, "extracting", f"Gathering market data for {symbol} signal...")

            extraction_result = await self._run_extraction_v2(
                extraction_engine, config, user_id,
                signal_indicators, timeframes,
                override_symbol=symbol
            )

            # UX delay: Give extraction phase time to display
            await asyncio.sleep(3)

            await set_execution_phase(config_id, "deciding", "Analyzing signal against current market conditions...")

            decision_result = await self._run_decision_v2(
                config_id, config, extraction_result, signal_data
            )

            # UX delay: Give decision phase time to display (longest phase for AI reasoning)
            await asyncio.sleep(7)

            action = decision_result.get('action', 'wait')
            if action in ['wait', 'no_action', 'hold']:
                message = "Signal rejected - conditions not favorable..."
            else:
                message = f"Signal validated - executing {action} position..."

            await set_execution_phase(config_id, "trading", message)

            trading_result = await self._run_trading_v2(
                config, user_id, decision_result
            )

            # UX delay: Give trading phase time to display
            await asyncio.sleep(3)
            
            if self._should_publish_signal(config, decision_result):
                await self._trigger_signal_publishing(
                    config, signal_data, decision_result
                )
            
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
        """Extract technical indicators from user's extraction config.

        Only extracts from 'technical_analysis' source. Market intelligence sources
        (derivatives_leverage, macro_economics, sentiment_social, etc.) are handled
        separately by market_intelligence.orchestrator.fetch_market_intelligence().
        """
        requested_indicators = []

        if "selected_data_sources" in extraction_config:
            data_sources = extraction_config.get("selected_data_sources", {})
            # Only extract from technical_analysis source
            # Other sources are handled by the market_intelligence orchestrator
            ta_config = data_sources.get("technical_analysis", {})
            if isinstance(ta_config, dict):
                data_points = ta_config.get("data_points", [])
                requested_indicators.extend(data_points)

        elif "indicators" in extraction_config:
            requested_indicators = extraction_config["indicators"]
        else:
            # Legacy format fallback
            data_sources = extraction_config.get("data_sources", {})
            for category, indicators in data_sources.items():
                if isinstance(indicators, list):
                    requested_indicators.extend(indicators)

        if not requested_indicators:
            requested_indicators = ["rsi", "macd", "ema"]

        return requested_indicators
    
    def _extract_timeframes_from_config(self, extraction_config: Dict) -> List[str]:
        """Extract timeframes from user's extraction config."""
        timeframes = ["1h"]
        
        if "selected_data_sources" in extraction_config:
            data_sources = extraction_config.get("selected_data_sources", {})
            
            if "technical_analysis" in data_sources:
                ta_config = data_sources["technical_analysis"]
                if isinstance(ta_config, dict):
                    ta_timeframes = ta_config.get("timeframes", [])
                    if ta_timeframes:
                        timeframes = ta_timeframes
                        self._log.debug(f"Found {len(timeframes)} timeframes from technical_analysis: {timeframes}")
                        return timeframes
            
            all_timeframes = set()
            for source_name, source_config in data_sources.items():
                if isinstance(source_config, dict) and source_name != "signals":
                    data_points = source_config.get("data_points", [])
                    if data_points:
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
            load_dotenv()
            
            api_id = int(os.getenv('TG_API_ID'))
            api_hash = os.getenv('TG_API_HASH')
            channel_name = os.getenv('GGSHOT_CHANNEL', 'GGShot_Bot')
            
            if not api_id or not api_hash:
                raise ValueError("Missing TG_API_ID or TG_API_HASH environment variables")
            
            session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
            session_path = os.path.join(session_dir, 'manual_trigger_session')
            
            client = TelegramClient(session_path, api_id, api_hash)
            await client.start()
            
            try:
                channel = await client.get_entity(channel_name)
                messages = await client.get_messages(channel, limit=10)

                from signals.ggshot_parser import GGShotParser
                parser = GGShotParser()
                
                for message in messages:
                    if message.message:
                        signal_data = parser.parse_signal(message.message)
                        if signal_data:
                            self._log.info(f"Found latest ggShot signal: {signal_data['symbol']} {signal_data['direction']}")

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

        if not publisher_config.get('enabled', False):
            return False

        # Only publish on trade entries (long/short), not waits
        action = decision_result.get('action', 'wait').lower()
        if action not in ['long', 'short', 'enter', 'buy', 'sell']:
            return False

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

                    # Match publishing_service logic: allow all paid tiers
                    paid_tiers = ('usage_based', 'ggbase', 'pro')
                    if tier not in paid_tiers or status != 'active':
                        self._log.info(f"User {config.user_id} requires paid subscription for signal publishing")
                        return False

        except Exception as e:
            self._log.error(f"Failed to check subscription for signal publishing: {e}")
            return False

        return True
    
    async def _trigger_signal_publishing(
        self,
        config: BotConfigV2,
        signal_data: Dict,
        decision_result: Dict
    ) -> None:
        """Trigger signal publishing to user's Telegram group."""
        try:
            from signals.publishing_service import publish_signal_to_telegram

            # Enrich signal_data with bot context for scheduled_trading bots
            enriched_signal_data = {
                **signal_data,
                'bot_name': config.config_name,
                'symbol': config.selected_pair,
                'config_type': config.config_type
            }

            success = await publish_signal_to_telegram(
                config_id=config.config_id,
                user_id=config.user_id,
                signal_data=enriched_signal_data,
                decision_result=decision_result
            )

            if success:
                self._log.info(f"📡 Published signal to Telegram for {config.config_name}")
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
                use_file_storage=False
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
            symbol = override_symbol or config.selected_pair or "BTC/USDT"

            # Extract all timeframes in parallel for speed
            self._log.info(f"Extracting {len(indicators)} indicators for {symbol} across {len(timeframes)} timeframes in parallel")

            tasks = [
                extraction_engine.extract_for_symbol(
                    symbol=symbol,
                    indicators=indicators,
                    timeframe=timeframe,
                    limit=200,
                    connector="kucoin",
                    config_id=config.config_id
                )
                for timeframe in timeframes
            ]

            results = await asyncio.gather(*tasks)

            # Map results back to timeframes
            timeframe_results = {}
            successful_extractions = 0

            for timeframe, result in zip(timeframes, results):
                timeframe_results[timeframe] = result

                if result.get("status") == "success":
                    successful_extractions += 1
                    self._log.info(f"✅ V2 Extraction completed for {symbol} ({timeframe})")
                else:
                    self._log.error(f"❌ V2 Extraction failed for {symbol} ({timeframe}): {result.get('error')}")
            
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

            # Query ggShot signals for additional market context (requires both config + permission)
            try:
                from core.services.user_service import UserService

                # Check if ggshot is enabled in bot config
                extraction_config = config.extraction or {}
                selected_sources = extraction_config.get('selected_data_sources', {})
                trading_signals_config = selected_sources.get('trading_signals', {})
                ggshot_enabled = 'ggshot' in trading_signals_config.get('data_points', [])

                if ggshot_enabled:
                    # Check if user has permission to access ggshot signals
                    user_service = UserService()
                    profile = await user_service.get_profile(user_id)

                    if profile and profile.paid_data_points and 'ggshot' in profile.paid_data_points:
                        # User has paid access and ggshot is enabled in config
                        from market_intelligence.adapters.signals.ggshot_adapter import GGShotAdapter
                        from market_intelligence.types import QueryParams

                        ggshot_adapter = GGShotAdapter()
                        params = QueryParams(params={'symbol': symbol, 'include_raw': False})
                        ggshot_response = await ggshot_adapter.fetch(params)

                        if ggshot_response.data and ggshot_response.data.get('signals'):
                            overall_result["ggshot_signals"] = ggshot_response.data['signals']
                            overall_result["ggshot_metadata"] = ggshot_response.data.get('metadata', {})
                            overall_result["ggshot_confidence"] = ggshot_response.confidence

                            timeframes_found = list(ggshot_response.data['signals'].keys())
                            self._log.info(f"✅ Fetched ggShot signals for {symbol}: {len(timeframes_found)} timeframes ({', '.join(timeframes_found)})")
                        else:
                            self._log.info(f"No ggShot signals found for {symbol}")
                            overall_result["ggshot_signals"] = {}

                        await ggshot_adapter.close()
                    else:
                        # User does not have permission to ggshot signals
                        self._log.debug(f"User {user_id} does not have access to ggshot signals (paid_data_points: {profile.paid_data_points if profile else 'no profile'})")
                        overall_result["ggshot_signals"] = {}
                else:
                    # ggShot not enabled in config
                    self._log.debug(f"ggShot signals not enabled in config for {config.config_id}")
                    overall_result["ggshot_signals"] = {}

            except Exception as e:
                self._log.warning(f"Failed to fetch ggShot signals (non-critical): {e}")
                overall_result["ggshot_signals"] = {}

            # Fetch market intelligence via orchestrator (funding rates, macro, etc.)
            # This uses the Universal Data Layer to fetch non-technical data sources
            # based on config.extraction.selected_data_sources
            try:
                from market_intelligence.orchestrator import fetch_market_intelligence

                market_intel = await fetch_market_intelligence(
                    config=config,
                    user_id=user_id,
                    symbol=symbol
                )

                if market_intel:
                    overall_result["market_intelligence"] = market_intel
                    total_points = sum(len(category) for category in market_intel.values())
                    categories = list(market_intel.keys())
                    self._log.info(
                        f"✅ Market intelligence: {total_points} data points from "
                        f"{len(categories)} categories ({', '.join(categories)})"
                    )
                else:
                    overall_result["market_intelligence"] = {}
                    self._log.debug("No market intelligence sources enabled in config")

            except Exception as e:
                self._log.warning(f"Failed to fetch market intelligence (non-critical): {e}")
                overall_result["market_intelligence"] = {}

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
            if extraction_result.get("status") == "error":
                return {
                    "status": "error",
                    "error": "Extraction failed, cannot make decision",
                    "action": "wait",
                    "confidence": 0.0
                }

            decision_engine = await self._get_decision_engine(config_id, config.user_id)

            if signal_data:
                symbol = signal_data['symbol']
            else:
                symbol = config.selected_pair

            if not symbol:
                raise ValueError("No symbol specified for decision")

            # Extract ggshot signals and market intelligence from extraction result if available
            ggshot_signals = extraction_result.get('ggshot_signals', {})
            market_intelligence = extraction_result.get('market_intelligence', {})

            decision_result = await decision_engine.make_decision(
                symbol=symbol,
                signal_data=signal_data,
                ggshot_signals=ggshot_signals,
                market_intelligence=market_intelligence
            )
            
            self._log.info(f"V2 Decision completed: {decision_result.get('action')} with confidence {decision_result.get('confidence', 0)}")
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
            if decision_result.get("status") == "error":
                return {
                    "status": "skipped",
                    "reason": "Decision failed, no trading action"
                }
            
            action = decision_result.get("action", "wait")
            confidence = decision_result.get("confidence", 0.0)

            # For signal_validation configs: gate trades with confidence threshold
            # For scheduled_trading configs: trust the bot's decision (no confidence gating)
            if config.config_type == "signal_validation":
                if config.telegram_integration and config.telegram_integration.get("publisher"):
                    publisher_config = config.telegram_integration.get("publisher", {})
                    threshold = publisher_config.get("confidence_threshold", 0.7)
                    if confidence < threshold:
                        self._log.info(
                            f"Signal rejected: confidence {confidence:.2f} below threshold {threshold:.2f}"
                        )
                        return {
                            "status": "skipped",
                            "reason": f"Signal confidence {confidence:.2f} below threshold {threshold:.2f}",
                            "action": action,
                            "confidence": confidence
                        }

            if action in ["wait", "no_action", "hold"]:
                return {
                    "status": "skipped",
                    "reason": f"Decision was to {action}",
                    "action": action
                }
            
            trading_config = config.trading or {}
            symbol = decision_result.get("symbol") or config.selected_pair

            if not symbol:
                self._log.error("No symbol available for trading - decision result and config both missing symbol")
                return {
                    "status": "error",
                    "error": "No symbol specified for trading",
                    "action": action
                }
            
            if action in ["enter", "long"]:
                trading_action = "long"
            elif action == "short":
                trading_action = "short"
            elif action in ["exit", "close"]:
                trading_action = "close"
            else:
                return {
                    "status": "skipped",
                    "reason": f"Unknown action: {action}",
                    "action": action
                }
            
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
            
            # Determine trading mode (paper vs symphony vs aster)
            trading_mode = getattr(config, 'trading_mode', 'paper')
            is_live = trading_mode == 'symphony'
            is_aster = trading_mode == 'aster'

            if trading_action == "close":
                try:
                    from core.common.db import get_db_connection
                    open_positions = []

                    if is_live or is_aster:
                        # Live/Aster trading: Query live_trades for batch_id
                        provider = 'aster' if is_aster else 'symphony'
                        with get_db_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    SELECT batch_id FROM live_trades
                                    WHERE config_id = %s AND provider = %s AND closed_at IS NULL
                                    ORDER BY created_at DESC LIMIT 1
                                """, (config.config_id, provider))
                                result = cur.fetchone()
                                if result:
                                    open_positions.append({'batch_id': result[0]})
                    else:
                        # Paper trading: Query paper_trades for trade_id
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

                    position = open_positions[0]

                    # Route to appropriate service
                    if is_aster:
                        trade_result = await self.aster_trading.close_position(
                            position['batch_id'],
                            user_id
                        )
                    elif is_live:
                        trade_result = await self.symphony_trading.close_position(
                            position['batch_id'],
                            reason="position_management"
                        )
                    else:
                        trade_result = await self.paper_trading.close_position(
                            position['trade_id'],
                            reason="position_management"
                        )

                    self._log.info(f"V2 Position closed: {trade_result.get('status')} for {symbol} (mode={trading_mode})")
                    return trade_result

                except Exception as e:
                    self._log.error(f"Failed to close position for {symbol}: {e}")
                    return {
                        "status": "error",
                        "error": f"Failed to close position: {str(e)}"
                    }
            else:
                # Route based on trading mode
                if is_aster:
                    trade_result = await self.aster_trading.execute_trade_intent(trading_intent)
                    self._log.info(f"V2 AsterDEX live trade completed: {trade_result.get('status')} for {symbol}")
                elif is_live:
                    trade_result = await self.symphony_trading.execute_trade_intent(trading_intent)
                    self._log.info(f"V2 Symphony live trade completed: {trade_result.get('status')} for {symbol}")
                else:
                    trade_result = await self.paper_trading.execute_trade_intent(trading_intent)
                    self._log.info(f"V2 Paper trade completed: {trade_result.get('status')} for {symbol}")

                return trade_result
            
        except Exception as e:
            self._log.error(f"V2 Trading failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    


orchestrator = GGBotOrchestrator()

scheduler = AsyncIOScheduler()
execution_semaphore = asyncio.Semaphore(50)




async def run_once(user_id: str, config_id: str, timeframe: str):
    """
    Job function executed by APScheduler for each bot.
    Implements Redis idempotency and calls the orchestrator.
    """
    close_ts = last_closed_close_ts(timeframe)
    key = format_redis_idempotency_key(user_id, config_id, timeframe, close_ts)
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    async with execution_semaphore:
        try:
            ttl = get_redis_ttl_for_timeframe(timeframe)
            if not await redis_client.set(key, "executing", ex=ttl, nx=True):
                logger.info(f"Skipping execution for {user_id}:{config_id}:{timeframe}:{close_ts} - already executed")
                return
            
            job_id = f"bot:{user_id}:{config_id}:{timeframe}"
            job = scheduler.get_job(job_id)
            next_fire = job.next_run_time.strftime('%Y-%m-%dT%H:%M:%SZ') if job and job.next_run_time else None
            
            try:
                result = await orchestrator.run_autonomous_cycle(config_id, user_id)

                await redis_client.set(key, "completed", ex=ttl)
                logger.info(f"Completed execution for {user_id}:{config_id}:{timeframe}:{close_ts} in {result.execution_time_ms}ms")
                
            except Exception as e:
                logger.error(f"Execution failed for {user_id}:{config_id}:{timeframe}:{close_ts}: {e}")
                
        finally:
            await redis_client.aclose()


def add_bot_job(user_id: str, config_id: str, timeframe: str, jitter: int = 30):
    """
    Add a scheduled job for a bot configuration.

    Args:
        user_id: User ID
        config_id: Configuration ID
        timeframe: Trading timeframe
        jitter: Random jitter in seconds (default 30, spread load to prevent API timeouts)
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
        job = scheduler.get_job(job_id)
        if job:
            scheduler.remove_job(job_id)
            logger.info(f"Removed scheduler job {job_id}")
            return True
        else:
            logger.info(f"Job {job_id} was already removed or never existed")
            return True
    except Exception as e:
        logger.warning(f"Failed to remove job {job_id}: {e}")
        return False


async def reconcile_active_bots():
    """Reconcile active bots from database on startup."""
    try:
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT config_id, user_id, config_type, config_data
                    FROM configurations
                    WHERE state = 'active'
                """)

                active_configs = cur.fetchall()
                scheduled_count = 0

                for row in active_configs:
                    config_id, user_id, config_type, config_data = row

                    try:
                        actual_config_type = config_type or 'scheduled_trading'
                        if actual_config_type != 'scheduled_trading':
                            logger.info(f"Skipping {actual_config_type} config {config_id} - not scheduling signal_validation configs")
                            continue

                        timeframe = extract_timeframe_from_config(config_data)

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
        config_type = config.get("config_type", "scheduled_trading")  # Use table field
    else:
        # Handle flat config structure
        decision_config = config.get("decision", {})
        config_type = config.get("config_type", "scheduled_trading")

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
    """Create a new bot configuration with specified trading mode."""
    # Extract fields that go in table columns, not JSONB
    request_data = request.dict(exclude={"config_name", "trading_mode", "symphony_agent_id"})
    config_type = request_data.pop("config_type", "scheduled_trading")
    trading_mode = request.trading_mode
    symphony_agent_id = request.symphony_agent_id

    # Validate trading mode
    if trading_mode not in ["paper", "symphony", "aster"]:
        raise HTTPException(status_code=400, detail="Invalid trading_mode. Must be 'paper', 'symphony', or 'aster'")

    # Check Pro subscription for live trading modes
    if trading_mode in ["symphony", "aster"]:
        profile = await user_service.get_profile(current_user.user_id)
        if not profile.can_use_live_trading:
            raise HTTPException(
                status_code=403,
                detail="Pro subscription required for live trading. Please upgrade to continue."
            )

    # Symphony-specific validations
    if trading_mode == "symphony":
        # Check Symphony credentials
        from core.auth.vault_utils import VaultManager
        credentials = await VaultManager.get_symphony_credential(current_user.user_id)
        if not credentials:
            raise HTTPException(
                status_code=400,
                detail="Symphony account not connected. Please connect in Settings first."
            )

        # Validate symphony_agent_id is provided
        if not symphony_agent_id or not symphony_agent_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Symphony Agent ID is required for Symphony live trading."
            )

        # Validate symphony_agent_id format (UUID)
        import re
        if not re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", symphony_agent_id, re.IGNORECASE):
            raise HTTPException(
                status_code=400,
                detail="Invalid Symphony Agent ID format (should be a UUID)."
            )

    # Aster-specific validations
    if trading_mode == "aster":
        # Check Aster credentials
        from core.auth.vault_utils import VaultManager
        credentials = await VaultManager.get_aster_credential(current_user.user_id)
        if not credentials:
            raise HTTPException(
                status_code=400,
                detail="AsterDEX account not connected. Please connect in Settings first."
            )

    # Validate symbol has real-time price data (WebSocket cached)
    selected_pair = request_data.get("selected_pair")
    if selected_pair:
        from core.symbols.registry import is_websocket_cached, get_websocket_cached_count

        if not is_websocket_cached(selected_pair, format_type="ccxt"):
            cached_count = get_websocket_cached_count()
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Symbol {selected_pair} requires real-time price data for trading. "
                    f"Please choose from {cached_count} available symbols with WebSocket price feeds. "
                    f"This ensures fast position monitoring and reliable trade execution."
                )
            )

        # Check symbol compatibility with trading mode
        if trading_mode == "symphony":
            from core.symbols import UniversalSymbolStandardizer
            standardizer = UniversalSymbolStandardizer()
            if not standardizer.is_symphony_compatible(selected_pair, "ccxt"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Symbol {selected_pair} is not compatible with Symphony live trading."
                )

        if trading_mode == "aster":
            from core.symbols import UniversalSymbolStandardizer
            standardizer = UniversalSymbolStandardizer()
            if not standardizer.is_aster_compatible(selected_pair, "ccxt"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Symbol {selected_pair} is not compatible with AsterDEX trading."
                )

    # Add config_type back to config_data for BotConfigV2 constructor
    request_data["config_type"] = config_type

    # Use symphony/aster directly - no more 'live' mapping (Schema v2.2+)
    config = await config_service.create_config(
        user_id=current_user.user_id,
        config_name=request.config_name,
        config_data=request_data,
        trading_mode=trading_mode,
        symphony_agent_id=symphony_agent_id if trading_mode == "symphony" else None
    )

    if not config:
        raise HTTPException(status_code=400, detail="Failed to create configuration")

    # Only create paper account for paper trading mode
    if trading_mode == "paper":
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

    # Create initial account_snapshot for timeline and metrics
    # Paper starts at $10,000, live modes start at $0 (will sync from exchange)
    initial_balance = 10000.0 if trading_mode == "paper" else 0.0
    try:
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO account_snapshots (
                        config_id, user_id, trading_mode,
                        current_balance, available_balance, margin_used,
                        total_pnl, realized_pnl, unrealized_pnl,
                        total_trades, win_trades, loss_trades, open_positions
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s, 0,
                        0, 0, 0,
                        0, 0, 0, 0
                    )
                """, (
                    config.config_id, current_user.user_id, trading_mode,
                    initial_balance, initial_balance
                ))
                conn.commit()
        logger.info(f"Created initial account_snapshot for config {config.config_id} (balance=${initial_balance})")
    except Exception as e:
        logger.error(f"Failed to create initial account_snapshot for config {config.config_id}: {e}")
        # Non-critical - account monitor will create snapshot on next cycle

    logger.bind(user_id=current_user.user_id).info(
        f"Created {trading_mode} bot '{request.config_name}' (config_id={config.config_id})"
    )

    # Log bot_created activity for timeline
    from core.common.activity_logger import log_activity_safe
    log_activity_safe(
        config_id=config.config_id,
        user_id=current_user.user_id,
        activity_type='bot_created',
        activity_source='user_action',
        summary=f"Created {trading_mode} bot: {request.config_name}",
        details={
            'config_name': request.config_name,
            'config_type': config_type,
            'trading_mode': trading_mode,
            'selected_pair': request_data.get('selected_pair'),
        },
        related_symbol=request_data.get('selected_pair'),
        importance=8  # High importance for lifecycle event
    )

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
    config_id: str
) -> Dict[str, Any]:
    """Get a specific configuration (PUBLIC for competition viewing)."""
    from core.common.db import get_db_connection

    try:
        # Get config without user_id verification (public viewing)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        config_id,
                        user_id,
                        config_name,
                        config_type,
                        state,
                        trading_mode,
                        symphony_agent_id,
                        created_at,
                        updated_at,
                        config_data,
                        profile_image_url,
                        is_public_performance
                    FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                row = cur.fetchone()

                if not row:
                    raise HTTPException(status_code=404, detail="Configuration not found")

                # Extract data while connection is still open
                config = {
                    "config_id": str(row[0]),
                    "user_id": str(row[1]),
                    "config_name": row[2],
                    "config_type": row[3],
                    "state": row[4],
                    "trading_mode": row[5],
                    "symphony_agent_id": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                    "config_data": row[9],
                    "profile_image_url": row[10],
                    "is_public_performance": row[11] or False
                }

        return {
            "status": "success",
            "config": config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration: {str(e)}")


@app.get("/api/v2/configs/{config_id}/strategy")
async def get_config_strategy(
    config_id: str
) -> Dict[str, Any]:
    """
    Get agent strategy for a configuration (PUBLIC for timeline viewing).

    Used by Activity Timeline to display strategy in "View Configuration" modal.
    Returns just the agent_strategy content, or 404 if not an agent config.
    """
    from core.common.db import get_db_connection

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT config_type, config_data
                    FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                row = cur.fetchone()

                if not row:
                    raise HTTPException(status_code=404, detail="Configuration not found")

                config_type = row[0]
                config_data = row[1]

                # Check if this is an agent config
                if config_type != 'agent':
                    raise HTTPException(status_code=404, detail="Not an agent configuration")

                # Extract agent_strategy
                agent_strategy = config_data.get('agent_strategy', {})
                strategy_content = agent_strategy.get('content', '')

                if not strategy_content:
                    raise HTTPException(status_code=404, detail="No strategy defined for this agent")

                return {
                    "status": "success",
                    "strategy": strategy_content,
                    "version": agent_strategy.get('version', 1),
                    "autonomously_editable": agent_strategy.get('autonomously_editable', False),
                    "last_updated_at": agent_strategy.get('last_updated_at'),
                    "last_updated_by": agent_strategy.get('last_updated_by', 'user')
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve strategy: {str(e)}")


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
    trading_mode = update_data.pop("trading_mode", None)
    symphony_agent_id = update_data.pop("symphony_agent_id", None)
    profile_image_url = update_data.pop("profile_image_url", None)

    # Validate symbol has real-time price data if changing selected_pair
    selected_pair = update_data.get("selected_pair")
    if selected_pair:
        from core.symbols.registry import is_websocket_cached, get_websocket_cached_count

        if not is_websocket_cached(selected_pair, format_type="ccxt"):
            cached_count = get_websocket_cached_count()
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Symbol {selected_pair} requires real-time price data for trading. "
                    f"Please choose from {cached_count} available symbols with WebSocket price feeds. "
                    f"This ensures fast position monitoring and reliable trade execution."
                )
            )

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
        config_type=config_type,
        trading_mode=trading_mode,
        symphony_agent_id=symphony_agent_id,
        profile_image_url=profile_image_url
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
    """Delete a configuration and clean up associated scheduler jobs."""
    # Clean up all scheduler jobs for this config before deleting from database
    removed_jobs = []
    all_jobs = scheduler.get_jobs()
    job_prefix = f"bot:{current_user.user_id}:{config_id}:"

    for job in all_jobs:
        if job.id.startswith(job_prefix):
            try:
                scheduler.remove_job(job.id)
                removed_jobs.append(job.id)
                logger.info(f"Removed scheduler job {job.id} for deleted config")
            except Exception as e:
                logger.warning(f"Failed to remove job {job.id}: {e}")

    # Delete config from database
    success = await config_service.delete_config(config_id, current_user.user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Configuration not found")

    logger.info(f"Deleted config {config_id} and removed {len(removed_jobs)} scheduler jobs")

    return {
        "status": "success",
        "message": "Configuration deleted successfully",
        "removed_jobs": len(removed_jobs)
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


@app.post("/api/v2/signal-validation/{config_id}")
async def run_signal_validation(
    config_id: str,
    user_id: str,
    request: SignalOrchestrationRequest,
    _: ServiceUser = Depends(get_service_user)
) -> OrchestrationResult:
    """Signal validation endpoint for service-to-service calls."""
    try:
        logger.info(f"Signal validation triggered by service for config {config_id}, user {user_id}")

        result = await orchestrator.run_autonomous_cycle(
            config_id,
            user_id,
            signal_data=request.signal_data,
            override_symbol=request.override_symbol
        )

        if result.status == "error":
            error_detail = "Unknown signal validation error"
            if result.extraction_result and isinstance(result.extraction_result, dict):
                error_detail = result.extraction_result.get('error', error_detail)

            logger.error(f"Signal validation failed for config {config_id}: {error_detail}")
            raise HTTPException(status_code=500, detail=f"Signal validation failed: {error_detail}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in signal validation for config {config_id}: {e}")
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
        from signals.publishing_service import SignalPublishingService, AccessControlService

        # Check permissions first and give specific error
        access_control = AccessControlService()
        can_publish = await access_control.can_publish_signals(current_user.user_id)
        if not can_publish:
            raise HTTPException(
                status_code=403,
                detail="Telegram publishing requires an active subscription. Upgrade at ggbots.ai/pricing"
            )

        # Check telegram config exists
        telegram_config = await access_control.get_user_telegram_config(config_id)
        if not telegram_config:
            raise HTTPException(
                status_code=400,
                detail="Telegram publishing not configured. Enable it and enter your channel ID first."
            )

        # Create service and test message
        service = SignalPublishingService()

        # Send a simple test message directly
        test_message = (
            "🧪 ggbots Test Message\n\n"
            "Your Telegram publishing is configured correctly!\n\n"
            "Your bot's trading signals will appear here.\n\n"
            "🌐 https://ggbots.ai"
        )

        success = await service.telegram_bot.send_message(
            chat_id=telegram_config.chat_id,
            text=test_message
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to send message. Make sure @ggFilter_Bot is admin in your channel/group with 'Post Messages' permission."
            )

        return {
            "status": "success",
            "message": "Test message sent successfully!",
            "chat_id": telegram_config.chat_id,
            "config_id": config_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signal publishing test failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Signal publishing test failed: {str(e)}")


# Symbols API Endpoints
@app.get("/api/v2/symbols/supported")
async def get_supported_symbols() -> Dict[str, Any]:
    """Get all 141 supported trading symbols."""
    try:
        from core.symbols.standardizer import UniversalSymbolStandardizer
        standardizer = UniversalSymbolStandardizer()

        # Get symbols in different formats for frontend use
        platform_symbols = standardizer.get_supported_symbols("platform")  # BTC-USDT format
        ccxt_symbols = standardizer.get_supported_symbols("ccxt")          # BTC/USDT format

        return {
            "status": "success",
            "data": {
                "platform": sorted(platform_symbols),  # For internal use
                "display": sorted(ccxt_symbols),       # For UI display (BTC/USDT looks better)
                "count": len(platform_symbols)
            }
        }

    except Exception as e:
        logger.error(f"Failed to get supported symbols: {e}")
        return {
            "status": "error",
            "data": {
                "platform": [],
                "display": [],
                "count": 0
            },
            "error": str(e)
        }


@app.get("/api/v2/symbols/search/{query}")
async def search_symbols(query: str) -> Dict[str, Any]:
    """Search symbols by base currency or partial match."""
    try:
        from core.symbols.standardizer import UniversalSymbolStandardizer
        standardizer = UniversalSymbolStandardizer()

        platform_symbols = standardizer.get_supported_symbols("platform")
        ccxt_symbols = standardizer.get_supported_symbols("ccxt")

        query = query.upper().strip()

        # Search logic
        platform_matches = []
        display_matches = []

        for platform_symbol, ccxt_symbol in zip(platform_symbols, ccxt_symbols):
            # Match base currency (BTC from BTC-USDT)
            base_currency = platform_symbol.split('-')[0]

            # Check if query matches base currency or symbol
            if (query in platform_symbol or
                query in base_currency or
                query in ccxt_symbol):
                platform_matches.append(platform_symbol)
                display_matches.append(ccxt_symbol)

        return {
            "status": "success",
            "data": {
                "query": query,
                "platform": platform_matches[:20],  # Limit results
                "display": display_matches[:20],
                "count": len(platform_matches)
            }
        }

    except Exception as e:
        logger.error(f"Failed to search symbols: {e}")
        return {
            "status": "error",
            "data": {
                "query": query,
                "platform": [],
                "display": [],
                "count": 0
            },
            "error": str(e)
        }




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
            "can_use_live_trading": profile.can_use_live_trading,
            "can_activate_bots": profile.can_activate_bots,
            "can_use_agents": profile.can_use_agents,
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


@app.get("/api/v2/llm-models")
async def get_llm_models(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get all available LLM models for OpenRouter."""
    try:
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get all enabled models
                cur.execute("""
                    SELECT
                        model_id,
                        display_name,
                        provider,
                        openrouter_model_id,
                        supports_thinking,
                        enabled,
                        max_context_tokens,
                        context_display,
                        pricing_input_per_1m,
                        pricing_output_per_1m,
                        cost_per_decision_standard,
                        cost_per_decision_thinking,
                        description,
                        sort_order
                    FROM llm_models
                    WHERE enabled = true
                    ORDER BY sort_order ASC
                """)

                rows = cur.fetchall()

                models = []
                for row in rows:
                    models.append({
                        "model_id": row[0],
                        "display_name": row[1],
                        "provider": row[2],
                        "openrouter_model_id": row[3],
                        "supports_thinking": row[4],
                        "enabled": row[5],
                        "max_context_tokens": row[6],
                        "context_display": row[7],
                        "pricing": {
                            "input_per_1m": float(row[8]),
                            "output_per_1m": float(row[9])
                        },
                        "cost_per_decision": {
                            "standard": float(row[10]),
                            "thinking": float(row[11])
                        },
                        "description": row[12],
                        "sort_order": row[13]
                    })

                return {
                    "status": "success",
                    "models": models,
                    "count": len(models)
                }

    except Exception as e:
        logger.error(f"Failed to get LLM models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM models: {str(e)}")


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


# Billing & Usage Endpoints
@app.get("/api/v2/billing/usage")
async def get_billing_usage(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Get current billing period LLM token usage for the authenticated user.

    Returns total unreported costs and breakdown by activity type.
    """
    try:
        from core.common.db import get_db_connection

        user_id = current_user.user_id

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get total unreported usage
                cur.execute("""
                    SELECT
                        SUM(platform_cost_usd) as total_cost,
                        SUM(input_tokens) as total_input_tokens,
                        SUM(output_tokens) as total_output_tokens,
                        SUM(reasoning_tokens) as total_reasoning_tokens,
                        COUNT(*) as activity_count
                    FROM activities
                    WHERE user_id = %s
                      AND platform_cost_usd IS NOT NULL
                      AND platform_cost_usd > 0
                      AND stripe_reported = FALSE
                """, (user_id,))

                result = cur.fetchone()
                total_cost = float(result[0]) if result[0] else 0.0
                total_input = int(result[1]) if result[1] else 0
                total_output = int(result[2]) if result[2] else 0
                total_reasoning = int(result[3]) if result[3] else 0
                activity_count = int(result[4]) if result[4] else 0

                # Get breakdown by model
                cur.execute("""
                    SELECT
                        model,
                        provider,
                        thinking_mode,
                        SUM(platform_cost_usd) as cost,
                        SUM(input_tokens) as input_tokens,
                        SUM(output_tokens) as output_tokens,
                        COUNT(*) as call_count
                    FROM activities
                    WHERE user_id = %s
                      AND platform_cost_usd IS NOT NULL
                      AND platform_cost_usd > 0
                      AND stripe_reported = FALSE
                    GROUP BY model, provider, thinking_mode
                    ORDER BY cost DESC
                """, (user_id,))

                model_breakdown = []
                for row in cur.fetchall():
                    model_breakdown.append({
                        "model": row[0],
                        "provider": row[1],
                        "thinking_mode": row[2],
                        "cost_usd": float(row[3]) if row[3] else 0.0,
                        "input_tokens": int(row[4]) if row[4] else 0,
                        "output_tokens": int(row[5]) if row[5] else 0,
                        "call_count": int(row[6])
                    })

                return {
                    "status": "success",
                    "usage": {
                        "total_cost_usd": total_cost,
                        "total_input_tokens": total_input,
                        "total_output_tokens": total_output,
                        "total_reasoning_tokens": total_reasoning,
                        "activity_count": activity_count,
                        "model_breakdown": model_breakdown
                    }
                }

    except Exception as e:
        logger.error(f"Failed to get billing usage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get billing usage: {str(e)}")


@app.get("/api/v2/billing/usage/breakdown")
async def get_billing_breakdown(
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
    config_id: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get detailed billing breakdown with optional filters.

    Query params:
        - config_id: Filter by specific bot/agent configuration
        - days: Number of days to include (default 30)
    """
    try:
        from core.common.db import get_db_connection
        from datetime import datetime, timedelta

        user_id = current_user.user_id
        start_date = datetime.utcnow() - timedelta(days=days)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Build query with optional config_id filter
                config_filter = "AND config_id = %s" if config_id else ""
                params = [user_id, start_date, config_id] if config_id else [user_id, start_date]

                # Get breakdown by bot/agent
                cur.execute(f"""
                    SELECT
                        a.config_id,
                        c.name as config_name,
                        c.config_type,
                        SUM(a.platform_cost_usd) as total_cost,
                        SUM(a.input_tokens) as input_tokens,
                        SUM(a.output_tokens) as output_tokens,
                        COUNT(*) as call_count,
                        MIN(a.created_at) as first_activity,
                        MAX(a.created_at) as last_activity
                    FROM activities a
                    LEFT JOIN configurations c ON a.config_id = c.config_id
                    WHERE a.user_id = %s
                      AND a.created_at >= %s
                      AND a.platform_cost_usd IS NOT NULL
                      AND a.platform_cost_usd > 0
                      {config_filter}
                    GROUP BY a.config_id, c.name, c.config_type
                    ORDER BY total_cost DESC
                """, params)

                bot_breakdown = []
                for row in cur.fetchall():
                    bot_breakdown.append({
                        "config_id": row[0],
                        "config_name": row[1],
                        "config_type": row[2],
                        "total_cost_usd": float(row[3]) if row[3] else 0.0,
                        "input_tokens": int(row[4]) if row[4] else 0,
                        "output_tokens": int(row[5]) if row[5] else 0,
                        "call_count": int(row[6]),
                        "first_activity": row[7].isoformat() if row[7] else None,
                        "last_activity": row[8].isoformat() if row[8] else None
                    })

                # Get daily aggregation
                cur.execute(f"""
                    SELECT
                        DATE(created_at) as date,
                        SUM(platform_cost_usd) as daily_cost,
                        SUM(input_tokens) as input_tokens,
                        SUM(output_tokens) as output_tokens,
                        COUNT(*) as call_count
                    FROM activities
                    WHERE user_id = %s
                      AND created_at >= %s
                      AND platform_cost_usd IS NOT NULL
                      AND platform_cost_usd > 0
                      {config_filter}
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """, params)

                daily_breakdown = []
                for row in cur.fetchall():
                    daily_breakdown.append({
                        "date": row[0].isoformat() if row[0] else None,
                        "cost_usd": float(row[1]) if row[1] else 0.0,
                        "input_tokens": int(row[2]) if row[2] else 0,
                        "output_tokens": int(row[3]) if row[3] else 0,
                        "call_count": int(row[4])
                    })

                return {
                    "status": "success",
                    "breakdown": {
                        "by_bot": bot_breakdown,
                        "by_day": daily_breakdown,
                        "days": days,
                        "config_id": config_id
                    }
                }

    except Exception as e:
        logger.error(f"Failed to get billing breakdown: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get billing breakdown: {str(e)}")


# Symphony Live Trading Endpoints
@app.post("/api/v2/symphony/setup")
async def setup_symphony_account(
    request: Dict[str, str],
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Store Symphony API credentials for live trading.

    Request body:
        - api_key: Symphony API key (starts with 'sk_')
        - smart_account: Ethereum address (0x...)
    """
    try:
        api_key = request.get("api_key", "").strip()
        smart_account = request.get("smart_account", "").strip()

        # Validate API key format
        if not api_key or not api_key.startswith("sk_"):
            raise HTTPException(
                status_code=400,
                detail="Invalid API key format. Should start with 'sk_'"
            )

        # Validate smart account format
        import re
        if not re.match(r"^0x[a-fA-F0-9]{40}$", smart_account):
            raise HTTPException(
                status_code=400,
                detail="Invalid smart account address. Should be a valid Ethereum address (0x...)"
            )

        # Store credentials in Vault
        from core.auth.vault_utils import VaultManager
        success = await VaultManager.store_symphony_credential(
            user_id=current_user.user_id,
            api_key=api_key,
            smart_account=smart_account
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to store Symphony credentials"
            )

        logger.bind(user_id=current_user.user_id).info("Symphony account connected successfully")

        return {
            "status": "success",
            "message": "Symphony account connected successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to setup Symphony account: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup Symphony account: {str(e)}"
        )


@app.get("/api/v2/symphony/status")
async def get_symphony_status(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Check if user has Symphony account connected."""
    try:
        from core.auth.vault_utils import VaultManager

        credentials = await VaultManager.get_symphony_credential(current_user.user_id)

        if credentials:
            return {
                "connected": True,
                "smart_account": credentials.get("smart_account")
            }
        else:
            return {
                "connected": False,
                "smart_account": None
            }

    except Exception as e:
        logger.error(f"Failed to check Symphony status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check Symphony status: {str(e)}"
        )


@app.post("/api/v2/symphony/disconnect")
async def disconnect_symphony_account(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Disconnect Symphony account and disable all live trading bots.

    This will:
    - Remove Symphony credentials from Vault
    - Set all user's live bots to paper mode
    """
    try:
        from core.auth.vault_utils import VaultManager

        success = await VaultManager.delete_symphony_credential(current_user.user_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to disconnect Symphony account"
            )

        logger.bind(user_id=current_user.user_id).info("Symphony account disconnected")

        return {
            "status": "success",
            "message": "Symphony account disconnected. All live bots have been disabled."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect Symphony account: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect Symphony account: {str(e)}"
        )


@app.post("/api/v2/aster/setup")
async def setup_aster_account(
    request: Dict[str, str],
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Store AsterDEX credentials for live trading.

    Request body:
        - user_wallet: User's Ethereum wallet address (0x...)
        - aster_wallet: AsterDEX wallet address (0x...)
        - private_key: AsterDEX wallet private key (0x... or without 0x prefix)
    """
    try:
        user_wallet = request.get("user_wallet", "").strip()
        aster_wallet = request.get("aster_wallet", "").strip()
        private_key = request.get("private_key", "").strip()

        # Validate user wallet format
        import re
        if not re.match(r"^0x[a-fA-F0-9]{40}$", user_wallet):
            raise HTTPException(
                status_code=400,
                detail="Invalid user wallet address. Should be a valid Ethereum address (0x...)"
            )

        # Validate aster wallet format
        if not re.match(r"^0x[a-fA-F0-9]{40}$", aster_wallet):
            raise HTTPException(
                status_code=400,
                detail="Invalid aster wallet address. Should be a valid Ethereum address (0x...)"
            )

        # Validate private key format (with or without 0x prefix)
        if not re.match(r"^(0x)?[a-fA-F0-9]{64}$", private_key):
            raise HTTPException(
                status_code=400,
                detail="Invalid private key format. Should be 64 hex characters (with or without 0x prefix)"
            )

        # Store credentials in Vault
        from core.auth.vault_utils import VaultManager
        success = await VaultManager.store_aster_credential(
            user_id=current_user.user_id,
            user_wallet=user_wallet,
            aster_wallet=aster_wallet,
            private_key=private_key
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to store AsterDEX credentials"
            )

        logger.bind(user_id=current_user.user_id).info("AsterDEX account connected successfully")

        return {
            "status": "success",
            "message": "AsterDEX account connected successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to setup AsterDEX account: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup AsterDEX account: {str(e)}"
        )


@app.get("/api/v2/aster/status")
async def get_aster_status(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Check if user has AsterDEX account connected."""
    try:
        from core.auth.vault_utils import VaultManager

        credentials = await VaultManager.get_aster_credential(current_user.user_id)

        if credentials:
            return {
                "connected": True,
                "user_wallet": credentials.get("user_wallet"),
                "aster_wallet": credentials.get("aster_wallet")
            }
        else:
            return {
                "connected": False,
                "user_wallet": None,
                "aster_wallet": None
            }

    except Exception as e:
        logger.error(f"Failed to check AsterDEX status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check AsterDEX status: {str(e)}"
        )


@app.post("/api/v2/aster/disconnect")
async def disconnect_aster_account(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Disconnect AsterDEX account and disable all aster trading bots.

    This will:
    - Remove AsterDEX credentials from Vault
    - Set all user's aster bots to paper mode
    """
    try:
        from core.auth.vault_utils import VaultManager

        success = await VaultManager.delete_aster_credential(current_user.user_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to disconnect AsterDEX account"
            )

        logger.bind(user_id=current_user.user_id).info("AsterDEX account disconnected")

        return {
            "status": "success",
            "message": "AsterDEX account disconnected. All aster bots have been disabled."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect AsterDEX account: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect AsterDEX account: {str(e)}"
        )


@app.get("/api/v2/positions/live/{config_id}")
async def get_live_positions(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get open live positions for a bot configuration from Symphony."""
    try:
        # Verify user owns this config
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Check if it's a Symphony live trading bot
        if getattr(config, 'trading_mode', 'paper') != 'symphony':
            return {
                "positions": [],
                "message": "Not a Symphony live trading bot"
            }

        # Get positions from Symphony service
        positions = await orchestrator.symphony_trading.get_open_positions(config_id)

        return {
            "positions": positions,
            "count": len(positions)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get live positions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get live positions: {str(e)}"
        )


@app.post("/api/v2/positions/live/{batch_id}/close")
async def close_live_position(
    batch_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Close a live position by batch_id."""
    try:
        # Verify user owns this position
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT lt.config_id
                    FROM live_trades lt
                    JOIN configurations c ON lt.config_id = c.config_id
                    WHERE lt.batch_id = %s AND c.user_id = %s AND lt.closed_at IS NULL
                """, (batch_id, current_user.user_id))

                result = cur.fetchone()
                if not result:
                    raise HTTPException(
                        status_code=404,
                        detail="Position not found or already closed"
                    )

        # Close position via Symphony service
        close_result = await orchestrator.symphony_trading.close_position(
            batch_id=batch_id,
            reason="manual"
        )

        if close_result.get("status") != "success":
            raise HTTPException(
                status_code=500,
                detail=close_result.get("reason", "Failed to close position")
            )

        return close_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close live position: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to close live position: {str(e)}"
        )


@app.get("/api/v2/positions/aster/{config_id}")
async def get_aster_positions(
    config_id: str
) -> Dict[str, Any]:
    """Get open Aster positions for a bot configuration (PUBLIC for competition viewing)."""
    from core.common.db import get_db_connection

    try:
        # Verify config exists (no auth required for public viewing)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT config_data FROM configurations WHERE config_id = %s
                """, (config_id,))
                row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Configuration not found")

        config_data = row[0]

        # Check if it's an Aster trading bot
        if config_data.get('trading_mode', 'paper') != 'aster':
            return {
                "positions": [],
                "message": "Not an Aster trading bot"
            }

        # Get positions from Aster service
        positions = await orchestrator.aster_trading.get_open_positions(config_id)

        return {
            "positions": positions,
            "count": len(positions)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Aster positions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Aster positions: {str(e)}"
        )


@app.post("/api/v2/positions/aster/{order_id}/close")
async def close_aster_position(
    order_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Close an Aster position by order_id."""
    try:
        # Verify user owns this position
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT lt.config_id, c.user_id
                    FROM live_trades lt
                    JOIN configurations c ON lt.config_id = c.config_id
                    WHERE lt.batch_id = %s AND lt.provider = 'aster'
                """, (order_id,))
                result = cur.fetchone()

                if not result:
                    raise HTTPException(status_code=404, detail="Position not found")

                config_id, user_id = result
                if user_id != current_user.user_id:
                    raise HTTPException(status_code=403, detail="Unauthorized")

        # Close position via Aster service
        close_result = await orchestrator.aster_trading.close_position(order_id)

        return close_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close Aster position: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to close Aster position: {str(e)}"
        )


@app.get("/api/v2/account/live/{config_id}")
async def get_live_account_metrics(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get account metrics for live trading bot from Symphony."""
    try:
        # Verify user owns this config
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Check if it's a Symphony live trading bot
        if getattr(config, 'trading_mode', 'paper') != 'symphony':
            raise HTTPException(
                status_code=400,
                detail="Not a Symphony live trading bot"
            )

        # Get metrics from Symphony service
        metrics = await orchestrator.symphony_trading.get_account_metrics(config_id)

        if not metrics:
            # Return default empty metrics
            return {
                'config_id': config_id,
                'current_balance': 10000.0,
                'total_pnl': 0,
                'total_trades': 0,
                'win_trades': 0,
                'loss_trades': 0,
                'win_rate': 0,
                'open_positions': 0,
                'portfolio_return_pct': 0,
                'updated_at': datetime.now().isoformat()
            }

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get live account metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get live account metrics: {str(e)}"
        )


@app.get("/api/v2/trades/live/{config_id}")
async def get_live_trade_history(
    config_id: str,
    limit: int = 50,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """Get closed trade history for live trading bot from Symphony."""
    try:
        # Verify user owns this config
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Check if it's a Symphony live trading bot
        if getattr(config, 'trading_mode', 'paper') != 'symphony':
            raise HTTPException(
                status_code=400,
                detail="Not a Symphony live trading bot"
            )

        # Get trade history from Symphony service
        trades = await orchestrator.symphony_trading.get_trade_history(config_id, limit)

        return {
            'trades': trades,
            'count': len(trades)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get live trade history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get live trade history: {str(e)}"
        )



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
    """
    Get account summary for a bot configuration.

    Returns comprehensive account metrics including total equity,
    performance percentage, and margin details.
    """
    try:
        from trading.paper.supabase_service import SupabasePaperTradingService
        from core.common.db import get_db_connection
        from core.domain.metrics_calculator import AccountMetricsCalculator
        from decimal import Decimal

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
                    "available_balance": 10000.0,
                    "margin_used": 0.0,
                    "total_pnl": 0.0,
                    "unrealized_pnl": 0.0,
                    "realized_pnl": 0.0,
                    "total_equity": 10000.0,
                    "performance_percent": 0.0,
                    "open_positions": 0,
                    "total_trades": 0,
                    "win_trades": 0,
                    "loss_trades": 0,
                    "win_rate": 0.0
                }
            }

        # Extract base metrics
        initial_balance = Decimal(str(account_summary.get("initial_balance", 10000.0)))
        current_balance = Decimal(str(account_summary.get("current_balance", 10000.0)))
        total_pnl = Decimal(str(account_summary.get("total_pnl", 0.0)))

        # Get unrealized P&L and margin from open positions
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COALESCE(SUM(unrealized_pnl), 0) as unrealized_pnl,
                        COALESCE(SUM(margin_used), 0) as margin_used
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'open'
                """, (config_id,))
                position_data = cur.fetchone()
                unrealized_pnl = Decimal(str(position_data[0])) if position_data else Decimal('0')
                margin_used = Decimal(str(position_data[1])) if position_data else Decimal('0')

        # Calculate metrics using centralized calculator
        total_equity = AccountMetricsCalculator.calculate_total_equity(
            current_balance,
            unrealized_pnl
        )

        available_balance = AccountMetricsCalculator.calculate_available_balance(
            current_balance,
            margin_used
        )

        realized_pnl = AccountMetricsCalculator.calculate_realized_pnl(
            total_pnl,
            unrealized_pnl
        )

        performance_percent = AccountMetricsCalculator.calculate_performance_percent(
            total_equity,
            initial_balance
        )

        return {
            "status": "success",
            "config_id": config_id,
            "account": {
                "initial_balance": float(initial_balance),
                "current_balance": float(current_balance),
                "available_balance": float(available_balance),
                "margin_used": float(margin_used),
                "total_pnl": float(total_pnl),
                "unrealized_pnl": float(unrealized_pnl),
                "realized_pnl": float(realized_pnl),
                "total_equity": float(total_equity),
                "performance_percent": float(performance_percent) if performance_percent is not None else 0.0,
                "open_positions": account_summary.get("open_positions", 0),
                "total_trades": account_summary.get("total_trades", 0),
                "win_trades": account_summary.get("win_trades", 0),
                "loss_trades": account_summary.get("loss_trades", 0),
                "win_rate": account_summary.get("win_rate", 0.0)
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


# Agent Trade Execution Endpoint
@app.post("/api/v2/agent/execute-trade")
async def agent_execute_trade(
    request: Dict[str, Any],
    user_id: str = Query(...),
    x_service_auth: Optional[str] = Header(None, alias="X-Service-Auth")
) -> Dict[str, Any]:
    """
    Execute trade for agent with optional position sizing overrides.

    This endpoint is called by autonomous agents via MCP tools.
    Supports position size and leverage overrides for agent decision-making.

    Args:
        request: Trade execution request with:
            - config_id: Bot configuration ID
            - symbol: Trading symbol (any format accepted)
            - side: "long" or "short"
            - confidence: Optional confidence score (0.0-1.0, default 0.7)
            - stop_loss_price: Optional stop loss price
            - take_profit_price: Optional take_profit price
            - decision_id: Optional decision UUID to link
            - position_size_override: Optional position size in base asset (e.g., 0.005 BTC)
            - position_size_usd_override: Optional total position size in USD NOTIONAL (e.g., 500)
                                          Note: This is the FULL POSITION SIZE, not margin/collateral
                                          Example: 1000 with 10x leverage = $1000 position using $100 margin
            - leverage_override: Optional leverage (e.g., 15)
        user_id: User ID (passed as query param by service client)
        x_service_auth: Service authentication header

    Returns:
        Trade execution result with status, trade_id/batch_id, etc.
    """
    try:
        # Service authentication check (same as signal-listener pattern)
        if x_service_auth != "agent-runner":
            raise HTTPException(status_code=401, detail="Unauthorized service")

        # Extract required fields
        config_id = request.get("config_id")
        symbol = request.get("symbol")
        side = request.get("side")

        if not config_id or not symbol or not side:
            raise HTTPException(status_code=400, detail="Missing required fields: config_id, symbol, side")

        # Validate config belongs to user
        config = await config_service.get_config(config_id, user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Build trade intent with overrides
        intent = {
            "config_id": config_id,
            "user_id": user_id,
            "symbol": symbol,
            "action": side,  # "long" or "short"
            "confidence": request.get("confidence", 0.7),
            "stop_loss_price": request.get("stop_loss_price"),
            "take_profit_price": request.get("take_profit_price"),
            "decision_id": request.get("decision_id"),
            # Agent override parameters
            "position_size_override": request.get("position_size_override"),
            "position_size_usd_override": request.get("position_size_usd_override"),
            "leverage_override": request.get("leverage_override")
        }

        # Route to appropriate trading service based on trading_mode
        trading_mode = getattr(config, 'trading_mode', 'paper')
        is_live = trading_mode == 'symphony'
        is_aster = trading_mode == 'aster'

        if is_aster:
            result = await orchestrator.aster_trading.execute_trade_intent(intent)
            return {
                "status": "success",
                "message": "Trade executed on AsterDEX",
                "trade": {
                    "batch_id": result.get("batch_id"),
                    "status": result.get("status")
                }
            }
        elif is_live:
            result = await orchestrator.symphony_trading.execute_trade_intent(intent)
            return {
                "status": "success",
                "message": "Trade executed on Symphony",
                "trade": {
                    "batch_id": result.get("batch_id"),
                    "status": result.get("status")
                }
            }
        else:
            # Paper trading
            result = await orchestrator.paper_trading.execute_trade_intent(intent)
            return {
                "status": "success",
                "message": "Paper trade executed",
                "trade": {
                    "trade_id": result.get("trade_id"),
                    "entry_price": result.get("entry_price"),
                    "size_usd": result.get("size_usd"),
                    "status": result.get("status")
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent trade execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")


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


@app.post("/api/v2/bot/{config_id}/reset-account")
async def reset_account(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Reset paper trading account to initial state.

    Closes all open positions, resets balance to $10k, clears all stats,
    but preserves trade history for analysis. Sets last_reset_at timestamp
    to distinguish current run metrics from historical data.
    """
    try:
        # Verify user owns this configuration
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Initialize paper trading service
        paper_trading = SupabasePaperTradingService()

        # Execute reset
        result = await paper_trading.reset_account(config_id, current_user.user_id)

        if result['status'] == 'failed':
            raise HTTPException(status_code=500, detail=result.get('reason', 'Reset failed'))

        logger.info(f"Account reset successful for config_id={config_id}, user_id={current_user.user_id}")

        return {
            "status": "success",
            "config_id": config_id,
            "positions_closed": result.get('positions_closed', 0),
            "new_balance": result.get('new_balance', 10000.0),
            "reset_at": result.get('reset_at'),
            "message": result.get('message', 'Account reset successfully')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset account {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset account: {str(e)}")


@app.post("/api/v2/bot/{config_id}/arena/register")
async def register_for_arena(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Register a bot for ggArena Season 1 competition.

    Requirements:
    - User must own the bot
    - Bot must be in 'active' state
    - User must have active subscription (usage-based)

    Sets is_public_performance = true for the configuration.
    Account will be reset to $10k when competition starts (Jan 21).
    """
    try:
        # 1. Verify user owns this configuration
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # 2. Verify bot is active
        if config.state != 'active':
            raise HTTPException(
                status_code=400,
                detail="Bot must be active to enter the Arena. Start your bot first."
            )

        # 3. Verify user has active subscription
        profile = await user_service.get_profile(current_user.user_id)
        if not profile or not profile.can_use_premium_features:
            raise HTTPException(
                status_code=403,
                detail="Arena registration requires an active subscription."
            )

        # 4. Set is_public_performance = true and record registration time
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE configurations
                    SET is_public_performance = true,
                        arena_registered_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE config_id = %s AND user_id = %s
                """, (config_id, current_user.user_id))
                conn.commit()

        # 5. If competition has started, reset account to $10k immediately
        from datetime import datetime, timezone
        competition_start = datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc)
        account_reset = False

        if datetime.now(timezone.utc) >= competition_start:
            try:
                from trading.paper.supabase_service import SupabasePaperTradingService
                paper_trading = SupabasePaperTradingService()
                reset_result = await paper_trading.reset_account(config_id, current_user.user_id)
                account_reset = reset_result.get('status') == 'success'
                logger.info(f"Late arena entry - account reset: config_id={config_id}, success={account_reset}")
            except Exception as e:
                logger.error(f"Failed to reset account for late arena entry: {e}")

        logger.info(f"Bot registered for Arena: config_id={config_id}, user_id={current_user.user_id}, account_reset={account_reset}")

        if account_reset:
            return {
                "status": "success",
                "config_id": config_id,
                "message": "You're in! Your account has been reset to $10,000. Good luck!",
                "competition_start": "2026-01-21T12:00:00Z",
                "account_reset": True
            }
        else:
            return {
                "status": "success",
                "config_id": config_id,
                "message": "Your bot is registered for ggArena Season 1! Account will be reset to $10,000 on January 21st.",
                "competition_start": "2026-01-21T12:00:00Z",
                "account_reset": False
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register bot for arena {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/api/v2/bot/{config_id}/arena/unregister")
async def unregister_from_arena(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> Dict[str, Any]:
    """
    Remove bot from ggArena competition.

    Sets is_public_performance = false for the configuration.
    """
    try:
        # 1. Verify user owns this configuration
        config = await config_service.get_config(config_id, current_user.user_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # 2. Set is_public_performance = false
        from core.common.db import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE configurations
                    SET is_public_performance = false, updated_at = CURRENT_TIMESTAMP
                    WHERE config_id = %s AND user_id = %s
                """, (config_id, current_user.user_id))
                conn.commit()

        logger.info(f"Bot unregistered from Arena: config_id={config_id}, user_id={current_user.user_id}")

        return {
            "status": "success",
            "config_id": config_id,
            "message": "Your bot has been removed from ggArena Season 1."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister bot from arena {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unregistration failed: {str(e)}")


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


# =============================================================================
# STRIPE INTEGRATION
# =============================================================================

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Request models
class CheckoutRequest(BaseModel):
    plan: str  # 'usage', 'monthly', or 'annual'
    coupon: Optional[str] = None


class CreditPurchaseRequest(BaseModel):
    amount_cents: int  # Amount in cents: 1000 = $10, 2500 = $25, etc.

@app.post("/api/v2/create-checkout-session")
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Create Stripe Checkout session for subscription upgrade."""

    # Map plan to price ID
    price_ids = {
        'usage': os.environ.get('STRIPE_PRICE_ID_USAGE'),
        'monthly': os.environ.get('STRIPE_PRICE_ID_MONTHLY'),
    }

    # Add annual if available
    if os.environ.get('STRIPE_PRICE_ID_ANNUAL'):
        price_ids['annual'] = os.environ['STRIPE_PRICE_ID_ANNUAL']

    if request.plan not in price_ids or not price_ids[request.plan]:
        raise HTTPException(400, f"Invalid plan: {request.plan}")

    try:
        # Get or create Stripe customer
        customer_id = await get_or_create_stripe_customer(current_user.user_id, current_user.email)

        # Build line items - metered billing doesn't use quantity
        if request.plan == 'usage':
            line_items = [{'price': price_ids[request.plan]}]
        else:
            line_items = [{'price': price_ids[request.plan], 'quantity': 1}]

        # Build checkout session params
        checkout_params = {
            'customer': customer_id,
            'mode': 'subscription',
            'line_items': line_items,
            'success_url': f"{os.environ['FRONTEND_URL']}/success?session_id={{CHECKOUT_SESSION_ID}}",
            'cancel_url': f"{os.environ['FRONTEND_URL']}/forge",
            'client_reference_id': str(current_user.user_id),
            'subscription_data': {
                'metadata': {
                    'user_id': str(current_user.user_id),
                    'plan': request.plan
                }
            },
            'metadata': {
                'user_id': str(current_user.user_id)
            },
            'allow_promotion_codes': request.plan != 'usage',  # No promos for usage plan
        }

        # Add trial only for monthly/annual plans (not usage-based)
        if request.plan in ['monthly', 'annual']:
            checkout_params['subscription_data']['trial_period_days'] = 14

        # Add coupon if provided
        if request.coupon:
            checkout_params['discounts'] = [{'coupon': request.coupon}]

        # Create Stripe Checkout session
        session = stripe.checkout.Session.create(**checkout_params)

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created Stripe checkout session: {session.id} for plan: {request.plan}"
        )

        return {'checkout_url': session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(500, f"Payment system error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(500, "Internal server error")


@app.post("/api/v2/stripe-webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""

    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.environ['STRIPE_WEBHOOK_SECRET']

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        logger.error("Invalid webhook payload")
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        raise HTTPException(400, "Invalid signature")

    # Log webhook event
    logger.info(f"Received Stripe webhook: {event['type']}")

    # Handle different event types
    event_type = event['type']

    if event_type == 'checkout.session.completed':
        await handle_checkout_completed(event['data']['object'])

    elif event_type == 'customer.subscription.updated':
        await handle_subscription_updated(event['data']['object'])

    elif event_type == 'customer.subscription.deleted':
        await handle_subscription_deleted(event['data']['object'])

    elif event_type == 'invoice.payment_failed':
        await handle_payment_failed(event['data']['object'])

    return {'received': True}


@app.post("/api/v2/create-portal-session")
async def create_portal_session(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Create Stripe billing portal session."""

    from core.common.db import get_db_connection

    # Get Stripe customer ID from database
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT stripe_customer_id
                FROM user_profiles
                WHERE user_id = %s
            """, (str(current_user.user_id),))
            result = cur.fetchone()

    if not result or not result[0]:
        raise HTTPException(404, "No active subscription found. Please upgrade first.")

    customer_id = result[0]

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{os.environ['FRONTEND_URL']}/forge",
        )

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created billing portal session for customer: {customer_id}"
        )

        return {'portal_url': session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal session: {e}")
        raise HTTPException(500, f"Error accessing billing portal: {str(e)}")


@app.get("/api/v2/me")
async def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Get current user's profile with subscription info."""
    profile = await current_user.load_profile()

    # Debug logging
    logger.info(f"🔍 /me endpoint - user: {current_user.user_id}, tier: {profile.subscription_tier.value}, can_activate: {profile.can_activate_bots}, can_agents: {profile.can_use_agents}")

    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "subscription_tier": profile.subscription_tier.value,
        "subscription_status": profile.subscription_status.value,
        "can_use_premium_features": profile.can_use_premium_features,
        "can_publish_telegram_signals": profile.can_publish_telegram_signals,
        "can_use_signal_validation": profile.can_use_signal_validation,
        "can_use_live_trading": profile.can_use_live_trading,
        "can_activate_bots": profile.can_activate_bots,
        "can_use_agents": profile.can_use_agents,
        "requires_own_llm_keys": profile.requires_own_llm_keys,
        "paid_data_points": profile.paid_data_points,
        "has_stripe_integration": profile.has_stripe_integration,
        "subscription_expires_at": profile.subscription_expires_at.isoformat() if profile.subscription_expires_at else None
    }


# =============================================================================
# WEBHOOK HANDLERS
# =============================================================================

async def handle_checkout_completed(session):
    """Handle successful checkout - activate subscription and/or create credit grant."""
    from core.common.db import get_db_connection

    metadata = session.get('metadata', {})
    user_id = metadata.get('user_id')
    customer_id = session['customer']
    subscription_id = session.get('subscription')  # May be None for payment mode

    # Check if this is a credit purchase
    is_credit_purchase = metadata.get('type') == 'credit_purchase'

    if is_credit_purchase:
        # Create Stripe Credit Grant
        amount_cents = int(metadata.get('amount_cents', 0))
        if amount_cents > 0:
            try:
                stripe.billing.CreditGrant.create(
                    customer=customer_id,
                    name=f"${amount_cents / 100:.0f} Credit Pack",
                    applicability_config={
                        'scope': {'price_type': 'metered'}
                    },
                    category='paid',
                    amount={
                        'type': 'monetary',
                        'monetary': {
                            'value': amount_cents,
                            'currency': 'usd'
                        }
                    }
                )
                logger.bind(user_id=user_id).info(
                    f"Credit grant created: ${amount_cents / 100:.2f}"
                )
            except stripe.error.StripeError as e:
                logger.error(f"Failed to create credit grant: {e}")
                # Don't raise - subscription still needs to be processed

    # Handle subscription activation if present (new subscriber or regular upgrade)
    if subscription_id:
        # Get plan from subscription_data metadata
        plan = session.get('subscription_data', {}).get('metadata', {}).get('plan', 'usage')

        # Map plan to subscription tier
        tier_map = {
            'usage': 'usage_based',
            'monthly': 'pro',
            'annual': 'pro'
        }
        subscription_tier = tier_map.get(plan, 'usage_based')

        # For ongoing subscriptions, subscription_expires_at should be NULL
        # Only set expiration date when subscription is cancelled
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET subscription_tier = %s,
                        subscription_status = 'active',
                        stripe_customer_id = %s,
                        stripe_subscription_id = %s,
                        subscription_expires_at = NULL,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (subscription_tier, customer_id, subscription_id, user_id))
                conn.commit()

        logger.bind(user_id=user_id).info(
            f"Subscription activated: tier={subscription_tier}, plan={plan}, Customer: {customer_id}, Subscription: {subscription_id}"
        )
    elif is_credit_purchase:
        # Payment mode (no subscription) - credit pack purchase
        # For free/expired users, upgrade them to prepaid tier (stored as 'ggbase')
        # For existing active paid users, keep their tier (credits just add to balance)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get current tier and check if subscription is expired
                cur.execute("""
                    SELECT subscription_tier, subscription_status, subscription_expires_at
                    FROM user_profiles WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                current_tier = result[0] if result else 'free'
                current_status = result[1] if result else None
                expires_at = result[2] if result else None

                # Check if subscription is expired
                from datetime import datetime, timezone
                is_expired = (
                    expires_at is not None and
                    expires_at <= datetime.now(timezone.utc)
                )

                # Upgrade to prepaid if free tier OR has expired subscription
                if current_tier == 'free' or is_expired:
                    # Upgrade to prepaid tier (ggbase)
                    # Clear subscription_expires_at since prepaid doesn't expire (credits do)
                    cur.execute("""
                        UPDATE user_profiles
                        SET subscription_tier = 'ggbase',
                            subscription_status = 'active',
                            subscription_expires_at = NULL,
                            stripe_customer_id = %s,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (customer_id, user_id))
                    logger.bind(user_id=user_id).info(
                        f"Upgraded to prepaid tier (was {current_tier}, expired={is_expired}): Customer: {customer_id}"
                    )
                else:
                    # Existing active paid user - just ensure customer_id is set
                    cur.execute("""
                        UPDATE user_profiles
                        SET stripe_customer_id = %s,
                            updated_at = NOW()
                        WHERE user_id = %s AND stripe_customer_id IS NULL
                    """, (customer_id, user_id))
                    logger.bind(user_id=user_id).info(
                        f"Credit purchase completed (existing {current_tier} subscriber): Customer: {customer_id}"
                    )
                conn.commit()


async def handle_subscription_updated(subscription):
    """Handle subscription updates."""
    from core.common.db import get_db_connection

    subscription_id = subscription['id']
    status = subscription['status']

    # Map Stripe status to our status
    status_map = {
        'active': 'active',
        'canceled': 'cancelled',
        'past_due': 'past_due',
        'unpaid': 'past_due',
        'incomplete': 'past_due'
    }

    our_status = status_map.get(status, 'active')

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET subscription_status = %s,
                    updated_at = NOW()
                WHERE stripe_subscription_id = %s
            """, (our_status, subscription_id))
            conn.commit()

    logger.info(f"Subscription updated: {subscription_id}, status: {our_status}")


async def handle_subscription_deleted(subscription):
    """Handle subscription cancellation."""
    from core.common.db import get_db_connection
    from datetime import datetime

    subscription_id = subscription['id']
    cancel_at = datetime.fromtimestamp(subscription['ended_at'])

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET subscription_tier = 'free',
                    subscription_status = 'cancelled',
                    subscription_expires_at = %s,
                    updated_at = NOW()
                WHERE stripe_subscription_id = %s
            """, (cancel_at, subscription_id))
            conn.commit()

    logger.info(f"Subscription cancelled: {subscription_id}, access until: {cancel_at}")


async def handle_payment_failed(invoice):
    """Handle failed payment."""
    from core.common.db import get_db_connection

    subscription_id = invoice['subscription']

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET subscription_status = 'past_due',
                    updated_at = NOW()
                WHERE stripe_subscription_id = %s
            """, (subscription_id,))
            conn.commit()

    logger.warning(f"Payment failed for subscription: {subscription_id}")


# =============================================================================
# CREDITS ENDPOINTS
# =============================================================================

def get_stripe_customer_id(user_id: str) -> str | None:
    """Get Stripe customer ID from database (read-only, doesn't create)."""
    from core.common.db import get_db_connection

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT stripe_customer_id
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()

    return result[0] if result and result[0] else None


def has_usage_based_subscription(user_id: str) -> bool:
    """Check if user has an active usage_based subscription."""
    from core.common.db import get_db_connection

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT subscription_tier, subscription_status
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()

    if not result:
        return False

    tier, status = result
    # User has usage_based subscription if tier is usage_based and status is active
    return tier == 'usage_based' and status == 'active'


@app.get("/api/v2/credits/balance")
async def get_credit_balance(current_user: AuthenticatedUser = Depends(get_current_user_v2)):
    """Get user's credit balance from Stripe Credit Grants."""
    customer_id = get_stripe_customer_id(str(current_user.user_id))

    if not customer_id:
        return {'available_usd': 0.0, 'ledger_usd': 0.0}

    try:
        # Query Stripe Credit Balance Summary for metered price types
        summary = stripe.billing.CreditBalanceSummary.retrieve(
            customer=customer_id,
            filter={
                'type': 'applicability_scope',
                'applicability_scope': {'price_type': 'metered'}
            }
        )

        # Extract balance from response
        # Stripe returns available_balance and ledger_balance (not available/ledger)
        if summary.balances and len(summary.balances) > 0:
            balance = summary.balances[0]
            available = balance.available_balance.monetary.value / 100 if balance.available_balance else 0
            ledger = balance.ledger_balance.monetary.value / 100 if balance.ledger_balance else 0
        else:
            available = 0.0
            ledger = 0.0

        return {
            'available_usd': available,
            'ledger_usd': ledger
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error fetching credit balance: {e}")
        raise HTTPException(500, f"Error fetching credit balance: {str(e)}")


@app.post("/api/v2/credits/purchase")
async def purchase_credits(
    request: CreditPurchaseRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Create Stripe Checkout session for credit purchase.

    All credit purchases use payment mode (no subscription).
    - Free tier users → become prepaid (ggbase) tier
    - Existing paid users → credits add to their balance
    """
    amount_cents = request.amount_cents

    # Validate amount (min $5, max $500)
    if amount_cents < 500:
        raise HTTPException(400, "Minimum credit purchase is $5")
    if amount_cents > 50000:
        raise HTTPException(400, "Maximum credit purchase is $500")

    try:
        # Get or create Stripe customer
        customer_id = await get_or_create_stripe_customer(
            str(current_user.user_id),
            current_user.email
        )

        # Credit purchase line item (one-time payment)
        credit_line_item = {
            'price_data': {
                'currency': 'usd',
                'unit_amount': amount_cents,
                'product_data': {
                    'name': f'${amount_cents / 100:.0f} Credit Pack',
                    'description': 'Prepaid credits for ggbots usage. Never expires.'
                }
            },
            'quantity': 1
        }

        # All credit purchases use payment mode (prepaid model)
        # No metered subscription - webhook will set tier appropriately
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode='payment',
            line_items=[credit_line_item],
            success_url=f"{os.environ['FRONTEND_URL']}/credits/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.environ['FRONTEND_URL']}/forge",
            metadata={
                'user_id': str(current_user.user_id),
                'type': 'credit_purchase',
                'amount_cents': str(amount_cents)
            }
        )

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created credit purchase checkout: ${amount_cents/100:.2f}"
        )

        return {'checkout_url': session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating credit checkout: {e}")
        raise HTTPException(500, f"Payment system error: {str(e)}")


@app.post("/api/v2/credits/crypto-checkout")
async def create_crypto_checkout(
    request: CreditPurchaseRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Create NOWPayments invoice for crypto credit purchase."""
    import httpx

    amount_cents = request.amount_cents

    # Validate amount (min $5, max $500)
    if amount_cents < 500:
        raise HTTPException(400, "Minimum credit purchase is $5")
    if amount_cents > 50000:
        raise HTTPException(400, "Maximum credit purchase is $500")

    amount_usd = amount_cents / 100

    api_key = os.environ.get("PAYMENTS_API_KEY")
    if not api_key:
        raise HTTPException(500, "Crypto payments not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.nowpayments.io/v1/invoice",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "price_amount": amount_usd,
                    "price_currency": "usd",
                    "order_id": f"credits_{current_user.user_id}_{amount_cents}",
                    "order_description": f"${amount_usd:.0f} Credit Pack for ggbots",
                    "ipn_callback_url": "https://ggbots-api.nightingale.business/api/v2/webhooks/nowpayments",
                    "success_url": f"{os.environ['FRONTEND_URL']}/credits/success",
                    "cancel_url": f"{os.environ['FRONTEND_URL']}/forge"
                },
                timeout=30.0
            )

            if response.status_code != 200:
                logger.error(f"NOWPayments API error: {response.status_code} - {response.text}")
                raise HTTPException(500, "Crypto payment service error")

            data = response.json()

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created crypto checkout: ${amount_usd:.2f}, invoice_id={data.get('id')}"
        )

        return {"invoice_url": data["invoice_url"]}

    except httpx.RequestError as e:
        logger.error(f"NOWPayments request error: {e}")
        raise HTTPException(500, "Crypto payment service unavailable")


@app.post("/api/v2/webhooks/nowpayments")
async def nowpayments_webhook(request: Request):
    """Handle NOWPayments IPN callback - create credit grant after crypto payment."""
    import hmac
    import hashlib

    # Get IPN secret for signature verification
    ipn_secret = os.environ.get("PAYMENTS_IPN_KEY")
    if not ipn_secret:
        logger.error("PAYMENTS_IPN_KEY not configured")
        raise HTTPException(500, "Webhook not configured")

    # Verify HMAC-SHA512 signature
    signature = request.headers.get("x-nowpayments-sig")
    body = await request.body()

    try:
        body_dict = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON")

    # NOWPayments signature: HMAC-SHA512 of sorted JSON
    sorted_body = json.dumps(body_dict, separators=(',', ':'), sort_keys=True)
    expected_sig = hmac.new(
        ipn_secret.encode(),
        sorted_body.encode(),
        hashlib.sha512
    ).hexdigest()

    if signature != expected_sig:
        logger.warning("NOWPayments webhook signature mismatch")
        raise HTTPException(403, "Invalid signature")

    # Check payment status
    payment_status = body_dict.get("payment_status")
    if payment_status != "finished":
        # Payment not complete yet - acknowledge but don't process
        logger.info(f"NOWPayments webhook: status={payment_status}, ignoring")
        return {"status": "ignored", "reason": f"status is {payment_status}"}

    # Extract order_id for idempotency check
    order_id = body_dict.get("order_id", "")

    # Idempotency check - prevent duplicate credit grants on webhook retry
    import redis
    redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
    processed_key = f"nowpayments:processed:{order_id}"

    existing = redis_client.get(processed_key)
    if existing:
        logger.info(f"NOWPayments order {order_id} already processed (status={existing.decode()}), ignoring duplicate")
        return {"status": "duplicate", "order_id": order_id}

    # Mark as processing (24h TTL to handle retries)
    redis_client.setex(processed_key, 86400, "processing")

    # Extract user_id and amount from order_id (format: "credits_{user_id}_{amount_cents}")
    if not order_id.startswith("credits_"):
        logger.error(f"Invalid order_id format: {order_id}")
        raise HTTPException(400, "Invalid order_id")

    parts = order_id.split("_")
    if len(parts) != 3:
        logger.error(f"Invalid order_id format: {order_id}")
        raise HTTPException(400, "Invalid order_id format")

    user_id = parts[1]
    amount_cents = int(parts[2])

    # Get user email for Stripe customer creation
    from core.common.db import get_db_connection
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT au.email
                FROM user_profiles up
                JOIN auth.users au ON up.user_id = au.id
                WHERE up.user_id = %s
            """, (user_id,))
            result = cur.fetchone()

    if not result:
        logger.error(f"User not found: {user_id}")
        raise HTTPException(400, "User not found")

    email = result[0]

    # Get or create Stripe customer
    customer_id = await get_or_create_stripe_customer(user_id, email)

    # Check user's current tier and expiration to decide how to handle the credit purchase
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT subscription_tier, subscription_expires_at
                FROM user_profiles WHERE user_id = %s
            """, (user_id,))
            tier_result = cur.fetchone()
            current_tier = tier_result[0] if tier_result else 'free'
            expires_at = tier_result[1] if tier_result else None

    # Check if subscription is expired
    from datetime import datetime, timezone
    is_expired = (
        expires_at is not None and
        expires_at <= datetime.now(timezone.utc)
    )

    if current_tier == 'free' or is_expired:
        # Free tier or expired user buying credits via crypto → upgrade to prepaid (ggbase)
        # NO metered subscription - they pay upfront only
        # Clear subscription_expires_at since prepaid doesn't expire (credits do)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET subscription_tier = 'ggbase',
                        subscription_status = 'active',
                        subscription_expires_at = NULL,
                        stripe_customer_id = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (customer_id, user_id))
                conn.commit()

        logger.bind(user_id=user_id).info(
            f"Upgraded to prepaid tier via crypto (was {current_tier}, expired={is_expired}): Customer: {customer_id}"
        )
    elif current_tier == 'ggbase':
        # Already prepaid - just add more credits (no tier change needed)
        logger.bind(user_id=user_id).info(
            f"Adding credits to existing prepaid account via crypto"
        )
    else:
        # Already on active usage_based or pro tier - credits will apply as discounts
        logger.bind(user_id=user_id).info(
            f"Adding credits to existing {current_tier} account via crypto"
        )

    # Create Stripe Credit Grant
    try:
        stripe.billing.CreditGrant.create(
            customer=customer_id,
            name=f"${amount_cents / 100:.0f} Credit Pack (Crypto)",
            applicability_config={
                'scope': {'price_type': 'metered'}
            },
            category='paid',
            amount={
                'type': 'monetary',
                'monetary': {
                    'value': amount_cents,
                    'currency': 'usd'
                }
            }
        )

        logger.bind(user_id=user_id).info(
            f"Crypto credit grant created: ${amount_cents / 100:.2f}"
        )

        # Mark as completed (30-day TTL for audit trail)
        redis_client.setex(processed_key, 86400 * 30, "completed")

    except stripe.error.StripeError as e:
        logger.error(f"Failed to create credit grant: {e}")
        raise HTTPException(500, "Failed to create credit grant")

    return {"status": "success"}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_or_create_stripe_customer(user_id: str, email: str) -> str:
    """Get existing Stripe customer ID or create new customer."""
    from core.common.db import get_db_connection

    # Check database for existing customer
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT stripe_customer_id
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()

    if result and result[0]:
        return result[0]

    # Create new Stripe customer
    try:
        customer = stripe.Customer.create(
            email=email,
            metadata={'user_id': user_id}
        )

        # Save to database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET stripe_customer_id = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (customer.id, user_id))
                conn.commit()

        logger.bind(user_id=user_id).info(f"Created Stripe customer: {customer.id}")
        return customer.id

    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe customer: {e}")
        raise


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


import os
if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true":
    logger.warning("⚠️  DEVELOPMENT MODE ACTIVE: Using mock authentication - DO NOT USE IN PRODUCTION")
    app.dependency_overrides[get_current_user_v2] = get_mock_user_for_dev

if __name__ == "__main__":
    # Disable reload in production (PM2 handles process management)
    is_dev = os.getenv("DEV_MODE", "false").lower() == "true"
    uvicorn.run(
        "ggbot:app",
        host="0.0.0.0",
        port=8000,
        reload=is_dev,
        log_level="info"
    )