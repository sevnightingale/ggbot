"""
GGBot Orchestrator — coordinates extraction, decision, and trading cycles.

Extracted from ggbot.py to allow both API ("Run Now") and scheduler processes
to share the same orchestration logic without importing FastAPI app creation.
"""

import asyncio
import json
import os
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from fastapi import HTTPException

from core.services.config_service import config_service, BotConfigV2
from core.services.user_service import user_service
from core.services.llm_service import llm_service
from core.common.logger import logger

from extraction.v2.extraction_engine import ExtractionEngineV2
from decision.engine_v2 import DecisionEngineV2
from trading.paper.supabase_service import SupabasePaperTradingService
from trading.live.symphony_service import SymphonyLiveTradingService
from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService
from trading.live.hyperliquid_service import HyperliquidLiveTradingService

from core.scheduler.utils import extract_timeframe_from_config

# Import OrchestrationResult from ggbot (it's a Pydantic model used by API responses)
# We define it here to avoid circular imports
from pydantic import BaseModel, field_serializer
import numpy as np


def serialize_numpy_types(obj):
    """
    Recursively convert numpy types, pandas types, and Decimal to Python native types.
    """
    from decimal import Decimal
    import pandas as pd

    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: serialize_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
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


class GGBotOrchestrator:
    """Main orchestrator class coordinating all V2 modules with full integration."""

    # Maximum cached extraction engines to prevent memory leaks
    # Engines are evicted LRU-style when limit is exceeded
    MAX_EXTRACTION_ENGINES = 30  # Per user_id

    def __init__(self):
        self.config_service = config_service
        self.llm_service = llm_service
        self.paper_trading = SupabasePaperTradingService()
        self.symphony_trading = SymphonyLiveTradingService()
        self.aster_trading = AsterDEXV3LiveTradingService()
        self.hyperliquid_trading = HyperliquidLiveTradingService()
        self._log = logger.bind(component="orchestrator")

        self._extraction_engines: OrderedDict = OrderedDict()

    async def run_autonomous_cycle(
        self,
        config_id: str,
        user_id: str,
        signal_data: Optional[Dict] = None,
        override_symbol: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> OrchestrationResult:
        """
        Run a complete trading cycle (autonomous or signal validation).

        Args:
            config_id: Bot configuration ID
            user_id: User ID for access validation
            signal_data: Signal data for validation mode
            override_symbol: Dynamic symbol override for signals
            run_id: 6-char hex correlation ID for log tracing

        Returns:
            OrchestrationResult with execution details
        """
        start_time = datetime.now(timezone.utc)
        log = self._log.bind(config_id=config_id, run_id=run_id) if run_id else self._log.bind(config_id=config_id)
        log.info(f"Starting V2 autonomous cycle")

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
                    log.info(
                        f"Allowing free first run - "
                        f"user on {user_profile.subscription_tier.value} tier"
                    )
                    is_first_run_allowed = True
                # Check if they have free manual runs remaining
                elif config.free_runs_remaining > 0:
                    log.info(
                        f"Allowing free manual run - "
                        f"{config.free_runs_remaining} free runs remaining"
                    )
                    is_free_manual_run = True
                else:
                    log.warning(
                        f"Blocking bot execution - "
                        f"lost activation permission (tier: {user_profile.subscription_tier.value}), "
                        f"no free runs remaining"
                    )
                    # Auto-deactivate bot — scheduler reconcile loop will detect
                    # the inactive state and remove the job within 10s
                    await self.config_service.set_bot_state(config_id, user_id, "inactive")
                    raise HTTPException(
                        status_code=403,
                        detail="No free test runs remaining. Subscribe to run your bot again."
                    )

            # Validate config has a symbol before doing any work
            if not signal_data and not override_symbol and not config.selected_pair:
                raise HTTPException(
                    status_code=400,
                    detail="Configure a trading pair before running this bot."
                )

            log.debug(f"config.config_type = '{config.config_type}', signal_data present = {signal_data is not None}")

            # Execute the appropriate cycle
            if config.config_type == "signal_validation":
                if signal_data:
                    result = await self._run_signal_validation_cycle(
                        config, signal_data, override_symbol, run_id=run_id
                    )
                else:
                    latest_signal = await self._fetch_latest_ggshot_signal()
                    signal_dict = self._signal_data_to_dict(latest_signal)
                    result = await self._run_signal_validation_cycle(
                        config, signal_dict, override_symbol, run_id=run_id
                    )
            else:
                result = await self._run_autonomous_trading_cycle(config, run_id=run_id)

            # Handle free run tracking after successful execution
            if result.status != "error":
                if is_first_run_allowed:
                    # Mark creation auto-run as used
                    await self.config_service.mark_first_run_used(config_id)
                    log.info(f"Marked first run used")
                elif is_free_manual_run:
                    # Decrement free manual runs
                    remaining = await self.config_service.decrement_free_runs(config_id)
                    log.info(f"Decremented free runs, {remaining} remaining")

            return result

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            log.error(f"V2 orchestration failed: {e}")
            raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")

    async def _run_autonomous_trading_cycle(self, config: BotConfigV2, run_id: Optional[str] = None) -> OrchestrationResult:
        """Run traditional autonomous trading cycle."""
        start_time = datetime.now(timezone.utc)
        user_id = config.user_id
        config_id = config.config_id

        try:
            extraction_engine = await self._get_extraction_engine(user_id)

            extraction_config = config.extraction or {}
            requested_indicators = self._extract_indicators_from_config(extraction_config)
            timeframes = self._extract_timeframes_from_config(extraction_config)
            tf_indicator_groups = self._build_timeframe_indicator_groups(extraction_config)

            from core.sse import set_execution_phase
            await set_execution_phase(config_id, "extracting", f"Gathering market data for {config.selected_pair}...")

            extraction_result = await self._run_extraction_v2(
                extraction_engine, config, user_id, requested_indicators, timeframes,
                run_id=run_id, tf_indicator_groups=tf_indicator_groups or None
            )

            await set_execution_phase(config_id, "deciding", "Analyzing market conditions for trading opportunities...")

            decision_result = await self._run_decision_v2(
                config_id, config, extraction_result, run_id=run_id
            )

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
                config, user_id, decision_result, run_id=run_id
            )

            # Arena mirror: route trade to DGClaw
            # Phase 2 (user agents via claw API) checked first, Phase 1 (admin via ACP SDK) as fallback
            arena_agent = await self._get_user_arena_agent(config)
            if arena_agent:
                asyncio.create_task(
                    self._execute_claw_arena_trade(arena_agent, config, decision_result, run_id)
                )
            elif self._is_arena_enabled(config):
                await self._enqueue_arena_trade(config, decision_result, run_id)

            if await self._should_publish_signal(config, decision_result):
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
        override_symbol: Optional[str] = None,
        run_id: Optional[str] = None
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
            tf_indicator_groups = self._build_timeframe_indicator_groups(extraction_config)

            extraction_engine = await self._get_extraction_engine(user_id)

            from core.sse import set_execution_phase
            await set_execution_phase(config_id, "extracting", f"Gathering market data for {symbol} signal...")

            extraction_result = await self._run_extraction_v2(
                extraction_engine, config, user_id,
                signal_indicators, timeframes,
                override_symbol=symbol, run_id=run_id,
                tf_indicator_groups=tf_indicator_groups or None
            )

            await set_execution_phase(config_id, "deciding", "Analyzing signal against current market conditions...")

            decision_result = await self._run_decision_v2(
                config_id, config, extraction_result, signal_data, run_id=run_id
            )

            action = decision_result.get('action', 'wait')
            if action in ['wait', 'no_action', 'hold']:
                message = "Signal rejected - conditions not favorable..."
            else:
                message = f"Signal validated - executing {action} position..."

            await set_execution_phase(config_id, "trading", message)

            trading_result = await self._run_trading_v2(
                config, user_id, decision_result, run_id=run_id
            )

            # Arena mirror: route trade to DGClaw
            arena_agent = await self._get_user_arena_agent(config)
            if arena_agent:
                asyncio.create_task(
                    self._execute_claw_arena_trade(arena_agent, config, decision_result, run_id)
                )
            elif self._is_arena_enabled(config):
                await self._enqueue_arena_trade(config, decision_result, run_id)

            if await self._should_publish_signal(config, decision_result):
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
            ta_config = data_sources.get("technical_analysis", {})
            if isinstance(ta_config, dict):
                data_points = ta_config.get("data_points", [])
                requested_indicators.extend(data_points)

        elif "indicators" in extraction_config:
            requested_indicators = extraction_config["indicators"]
        else:
            data_sources = extraction_config.get("data_sources", {})
            for category, indicators in data_sources.items():
                if isinstance(indicators, list):
                    requested_indicators.extend(indicators)

        if not requested_indicators:
            requested_indicators = ["rsi", "macd", "ema"]

        return requested_indicators

    def _build_timeframe_indicator_groups(self, extraction_config: Dict) -> Dict[str, List[str]]:
        """Build {timeframe: [indicators]} mapping, respecting per-indicator overrides.

        If per_indicator_timeframes is set, indicators with overrides use their
        custom timeframe list; all others fall back to the global timeframes array.
        Returns empty dict if no TA config exists (caller uses legacy path).
        """
        ta_config = extraction_config.get('selected_data_sources', {}).get('technical_analysis', {})
        if not isinstance(ta_config, dict):
            return {}

        all_indicators = ta_config.get('data_points', [])
        if not all_indicators:
            return {}

        global_tfs = ta_config.get('timeframes', ['1h'])
        per_indicator = ta_config.get('per_indicator_timeframes', {})

        # Build reverse mapping: timeframe -> list of indicators for that TF
        tf_to_indicators: Dict[str, List[str]] = {}
        for indicator in all_indicators:
            tfs = per_indicator.get(indicator, global_tfs)
            for tf in tfs:
                tf_to_indicators.setdefault(tf, []).append(indicator)

        return tf_to_indicators

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
        from dotenv import load_dotenv

        try:
            load_dotenv()

            api_id = int(os.getenv('TG_API_ID'))
            api_hash = os.getenv('TG_API_HASH')
            channel_name = os.getenv('GGSHOT_CHANNEL', 'GGShot_Bot')

            if not api_id or not api_hash:
                raise ValueError("Missing TG_API_ID or TG_API_HASH environment variables")

            session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sessions')
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

    async def _should_publish_signal(self, config: BotConfigV2, decision_result: Dict) -> bool:
        """Check if signal should be published to telegram."""
        telegram_config = config.telegram_integration or {}
        publisher_config = telegram_config.get('publisher', {})

        if not publisher_config.get('enabled', False):
            return False

        action = decision_result.get('action', 'wait').lower()
        if action not in ['long', 'short', 'enter', 'buy', 'sell']:
            return False

        try:
            from core.common.db import db_fetch_one
            result = await db_fetch_one("""
                SELECT subscription_tier, subscription_status
                FROM user_profiles
                WHERE user_id = %s
            """, (config.user_id,))

            if not result:
                self._log.warning(f"No user profile found for {config.user_id}")
                return False

            tier, status = result

            paid_tiers = ('usage_based', 'prepaid', 'pro')
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

            trading_mode = getattr(config, 'trading_mode', 'paper')
            live_tag = 'Hyperliquid' if trading_mode == 'hyperliquid' else None
            enriched_signal_data = {
                **signal_data,
                'bot_name': config.config_name,
                'symbol': config.selected_pair,
                'config_type': config.config_type,
                'live_tag': live_tag
            }

            success = await publish_signal_to_telegram(
                config_id=config.config_id,
                user_id=config.user_id,
                signal_data=enriched_signal_data,
                decision_result=decision_result
            )

            if success:
                self._log.info(f"Published signal to Telegram for {config.config_name}")
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
        """Get or create V2 extraction engine for user with LRU eviction."""
        if user_id in self._extraction_engines:
            self._extraction_engines.move_to_end(user_id)
            return self._extraction_engines[user_id]

        while len(self._extraction_engines) >= self.MAX_EXTRACTION_ENGINES:
            oldest_user_id, oldest_engine = self._extraction_engines.popitem(last=False)
            try:
                await oldest_engine.cleanup()
                self._log.info(f"Evicted extraction engine for user {oldest_user_id} (LRU)")
            except Exception as e:
                self._log.warning(f"Error cleaning up evicted extraction engine: {e}")

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
        override_symbol: Optional[str] = None,
        run_id: Optional[str] = None,
        tf_indicator_groups: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """Run V2 extraction engine for multiple timeframes with proper integration.

        If tf_indicator_groups is provided, each timeframe gets only the indicators
        assigned to it (per-indicator timeframe customization). Otherwise falls back
        to running all indicators on all timeframes.
        """
        try:
            symbol = override_symbol or config.selected_pair or "BTC/USDT"

            if tf_indicator_groups:
                # Per-indicator timeframe mode: each TF gets its own indicator subset
                self._log.debug(
                    f"Extracting with per-indicator TFs for {symbol}: "
                    f"{len(tf_indicator_groups)} timeframes, "
                    f"{sum(len(v) for v in tf_indicator_groups.values())} total indicator-TF pairs"
                )
                tasks = [
                    extraction_engine.extract_for_symbol(
                        symbol=symbol,
                        indicators=indicators_for_tf,
                        timeframe=tf,
                        limit=200,
                        connector="kucoin",
                        config_id=config.config_id
                    )
                    for tf, indicators_for_tf in tf_indicator_groups.items()
                ]
                effective_timeframes = list(tf_indicator_groups.keys())
            else:
                # Legacy mode: all indicators on all timeframes
                self._log.debug(f"Extracting {len(indicators)} indicators for {symbol} across {len(timeframes)} timeframes in parallel")
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
                effective_timeframes = timeframes

            results = await asyncio.gather(*tasks)

            timeframe_results = {}
            successful_extractions = 0

            for timeframe, result in zip(effective_timeframes, results):
                timeframe_results[timeframe] = result

                if result.get("status") == "success":
                    successful_extractions += 1
                    self._log.debug(f"V2 Extraction completed for {symbol} ({timeframe})")
                else:
                    self._log.error(f"V2 Extraction failed for {symbol} ({timeframe}): {result.get('error')}")

            overall_result = {
                "status": "success" if successful_extractions > 0 else "error",
                "symbol": symbol,
                "timeframes": timeframe_results,
                "summary": {
                    "total_timeframes": len(effective_timeframes),
                    "successful_extractions": successful_extractions,
                    "failed_extractions": len(effective_timeframes) - successful_extractions,
                    "indicators": indicators
                }
            }

            if successful_extractions == 0:
                overall_result["error"] = "All timeframe extractions failed"

            # Query ggShot signals for additional market context
            try:
                from core.services.user_service import UserService

                extraction_config = config.extraction or {}
                selected_sources = extraction_config.get('selected_data_sources', {})
                trading_signals_config = selected_sources.get('trading_signals', {})
                ggshot_enabled = 'ggshot' in trading_signals_config.get('data_points', [])

                if ggshot_enabled:
                    user_svc = UserService()
                    profile = await user_svc.get_profile(user_id)

                    if profile and profile.paid_data_points and 'ggshot' in profile.paid_data_points:
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
                            self._log.info(f"Fetched ggShot signals for {symbol}: {len(timeframes_found)} timeframes ({', '.join(timeframes_found)})")
                        else:
                            self._log.info(f"No ggShot signals found for {symbol}")
                            overall_result["ggshot_signals"] = {}

                        await ggshot_adapter.close()
                    else:
                        self._log.debug(f"User {user_id} does not have access to ggshot signals (paid_data_points: {profile.paid_data_points if profile else 'no profile'})")
                        overall_result["ggshot_signals"] = {}
                else:
                    self._log.debug(f"ggShot signals not enabled in config for {config.config_id}")
                    overall_result["ggshot_signals"] = {}

            except Exception as e:
                self._log.warning(f"Failed to fetch ggShot signals (non-critical): {e}")
                overall_result["ggshot_signals"] = {}

            # Fetch market intelligence via orchestrator
            try:
                from market_intelligence.orchestrator import fetch_market_intelligence

                market_intel = await fetch_market_intelligence(
                    config=config,
                    user_id=user_id,
                    symbol=symbol,
                    run_id=run_id
                )

                if market_intel:
                    overall_result["market_intelligence"] = market_intel
                    total_points = sum(len(category) for category in market_intel.values())
                    categories = list(market_intel.keys())
                    self._log.info(
                        f"Market intelligence: {total_points} data points from "
                        f"{len(categories)} categories ({', '.join(categories)})"
                    )
                else:
                    overall_result["market_intelligence"] = {}
                    self._log.debug("No market intelligence sources enabled in config")

            except Exception as e:
                self._log.warning(f"Failed to fetch market intelligence (non-critical): {e}")
                overall_result["market_intelligence"] = {}

            # Clean up stale market_data rows for timeframes no longer in config.
            # Old rows linger after config changes and pollute LLM prompts.
            # Use effective_timeframes (which accounts for per-indicator TF overrides).
            try:
                from core.common.db import db_execute
                deleted = await db_execute("""
                    DELETE FROM market_data
                    WHERE config_id = %s AND symbol = %s
                      AND timeframe != ALL(%s)
                """, (config.config_id, symbol, effective_timeframes))
                if deleted > 0:
                    self._log.info(f"Cleaned up {deleted} stale market_data rows for removed timeframes")
            except Exception as e:
                self._log.warning(f"Failed to clean stale market_data (non-critical): {e}")

            self._log.info(f"V2 Multi-timeframe extraction completed: {successful_extractions}/{len(effective_timeframes)} successful")
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
        """Create a fresh V2 decision engine (DB is source of truth each cycle)."""
        engine = DecisionEngineV2(config_id, user_id)
        await engine.initialize()
        return engine

    async def _run_decision_v2(
        self,
        config_id: str,
        config: BotConfigV2,
        extraction_result: Dict[str, Any],
        signal_data: Optional[Dict] = None,
        run_id: Optional[str] = None
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

            if signal_data:
                symbol = signal_data['symbol']
            else:
                symbol = config.selected_pair

            if not symbol:
                raise ValueError("No symbol specified for decision")

            ggshot_signals = extraction_result.get('ggshot_signals', {})
            market_intelligence = extraction_result.get('market_intelligence', {})

            # Route to Rei decision engine if enabled
            if getattr(config, 'rei_enabled', False):
                from decision.rei_engine import ReiDecisionEngine
                rei_engine = ReiDecisionEngine(config_id, config.user_id)

                open_positions = []
                account_balance = None
                try:
                    from trading.paper.supabase_service import SupabasePaperTradingService
                    paper_service = SupabasePaperTradingService()
                    open_positions = await paper_service.get_open_positions(config_id)
                    account_summary = await paper_service.get_account_summary(config_id)
                    account_balance = account_summary.get('current_balance', 10000.0)
                except Exception as e:
                    self._log.warning(f"Could not fetch positions/balance for Rei context: {e}")

                decision_result = await rei_engine.make_decision(
                    symbol=symbol,
                    extraction_result=extraction_result,
                    open_positions=open_positions,
                    account_balance=account_balance,
                    market_intelligence=market_intelligence,
                )
                self._log.info(f"Rei Decision completed: {decision_result.get('action')} with confidence {decision_result.get('confidence', 0)}")
                return decision_result

            # Standard OpenRouter LLM decision engine
            decision_engine = await self._get_decision_engine(config_id, config.user_id)

            decision_result = await decision_engine.make_decision(
                symbol=symbol,
                signal_data=signal_data,
                ggshot_signals=ggshot_signals,
                market_intelligence=market_intelligence,
                run_id=run_id
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

    # =========================================================================
    # Arena Mirror — DGClaw parallel execution layer
    # =========================================================================

    def _is_arena_enabled(self, config: BotConfigV2) -> bool:
        """Check if this config should mirror trades to DGClaw arena."""
        arena_configs = os.environ.get('ARENA_ENABLED_CONFIGS', '')
        if not arena_configs:
            return False
        return config.config_id in [c.strip() for c in arena_configs.split(',') if c.strip()]

    async def _enqueue_arena_trade(
        self, config: BotConfigV2, decision_result: Dict[str, Any], run_id: Optional[str] = None
    ):
        """
        Enqueue a trade intent to the arena Redis queue for sebastian_virtuals to process.
        Fire-and-forget — does not block the bot cycle.
        """
        try:
            action = decision_result.get('action', 'wait')
            if action in ['wait', 'no_action', 'hold']:
                return  # Nothing to mirror

            import redis as sync_redis
            r = sync_redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

            trading_config = config.trading or {}
            arena_intent = {
                'config_id': config.config_id,
                'config_name': config.config_name,
                'user_id': config.user_id,
                'symbol': decision_result.get('symbol') or config.selected_pair,
                'action': action,
                'confidence': decision_result.get('confidence', 0),
                'stop_loss_price': decision_result.get('stop_loss_price'),
                'take_profit_price': decision_result.get('take_profit_price'),
                'leverage': trading_config.get('leverage', 3),
                'max_margin_percent': trading_config.get('position_sizing', {}).get('max_margin_percent', 20),
                'run_id': run_id,
                'enqueued_at': datetime.now(timezone.utc).isoformat(),
            }

            r.lpush('arena:trade_queue', json.dumps(arena_intent))
            r.close()
            self._log.info(f"Arena trade enqueued: {action} {arena_intent['symbol']}")

        except Exception as e:
            # Non-fatal — arena mirror failing should never affect the primary trade
            self._log.error(f"Failed to enqueue arena trade: {e}")

    # =========================================================================
    # Arena Phase 2 — Claw API direct routing (user agents)
    # =========================================================================

    async def _get_user_arena_agent(self, config: BotConfigV2) -> Optional[Dict[str, Any]]:
        """
        Check if this config has an arena agent assigned (1-bot-1-agent model).

        Returns dict with claw_api_key and wallet_address, or None.
        """
        from core.common.db import db_fetch_one

        result = await db_fetch_one("""
            SELECT aa.wallet_address, aa.claw_api_key_vault_id, aa.agent_name
            FROM arena_agents aa
            WHERE aa.assigned_config_id = %s AND aa.status = 'assigned'
        """, (config.config_id,))

        if not result or not result[1]:
            return None

        wallet_address, claw_vault_id, agent_name = result

        # Decrypt claw API key from vault
        claw_key_row = await db_fetch_one("""
            SELECT decrypted_secret
            FROM vault.decrypted_secrets
            WHERE id = %s
        """, (claw_vault_id,))

        if not claw_key_row:
            self._log.error(f"Vault secret missing for arena agent {agent_name}")
            return None

        return {
            'wallet_address': wallet_address,
            'claw_api_key': claw_key_row[0],
            'agent_name': agent_name,
        }

    async def _execute_claw_arena_trade(
        self,
        arena_agent: Dict[str, Any],
        config: BotConfigV2,
        decision_result: Dict[str, Any],
        run_id: Optional[str] = None,
    ):
        """
        Execute arena trade via claw REST API. Fire-and-forget.

        Same position sizing logic as Phase 1 dgclaw_service but async.
        """
        try:
            action = decision_result.get('action', 'wait')
            if action in ['wait', 'no_action', 'hold']:
                return

            from trading.virtuals.claw_api import ClawAPIClient

            client = ClawAPIClient(arena_agent['claw_api_key'])
            wallet = arena_agent['wallet_address']

            # Determine side
            if action in ('long', 'enter_long', 'enter'):
                side = 'long'
            elif action in ('short', 'enter_short'):
                side = 'short'
            elif action in ('exit', 'close'):
                # Close position — need to determine pair
                symbol = decision_result.get('symbol') or config.selected_pair
                pair = self._arena_to_pair(symbol)
                if pair:
                    result = await client.close_trade(pair)
                    self._log.info(f"Arena close {pair}: {result.get('status')}")
                return
            else:
                return

            # Get DGClaw balance for position sizing
            account = await client.get_dgclaw_account(wallet)
            if not account:
                self._log.warning("Arena: DGClaw account query failed, skipping")
                return

            balance = account.get('balance', 0)
            if balance <= 0:
                self._log.warning("Arena: DGClaw balance is $0, skipping")
                return

            # Position sizing: confidence x max_margin% x balance x leverage
            trading_config = config.trading or {}
            confidence = decision_result.get('confidence', 0.5)
            leverage = trading_config.get('leverage', 3)
            max_margin_pct = trading_config.get('position_sizing', {}).get('max_margin_percent', 20)

            margin = confidence * (max_margin_pct / 100.0) * balance
            size_usd = margin * leverage

            # Safety cap: 90% of balance as margin
            max_margin = balance * 0.90
            if margin > max_margin:
                margin = max_margin
                size_usd = margin * leverage

            if size_usd < 10:
                self._log.debug(f"Arena size ${size_usd:.2f} below $10 minimum, skipping")
                return

            # Convert symbol to HL pair name
            symbol = decision_result.get('symbol') or config.selected_pair
            pair = self._arena_to_pair(symbol)
            if not pair:
                self._log.warning(f"Arena: cannot convert symbol {symbol}")
                return

            self._log.info(
                f"Arena trade: {side.upper()} {pair} ${size_usd:.0f} @ {leverage}x "
                f"(agent={arena_agent['agent_name']})"
            )

            # SL/TP
            sl = decision_result.get('stop_loss_price')
            tp = decision_result.get('take_profit_price')

            result = await client.create_trade(
                pair=pair,
                side=side,
                size=size_usd,
                leverage=leverage,
                stop_loss=sl,
                take_profit=tp,
            )

            status = result.get('status', 'unknown')
            self._log.info(f"Arena trade result: {status} (job={result.get('job_id', 'N/A')})")

            # Log activity
            try:
                from core.common.activity_logger import log_activity_safe
                log_activity_safe(
                    config_id=config.config_id,
                    user_id=config.user_id,
                    activity_type=f"arena_{side}",
                    activity_source="claw_arena",
                    summary=f"Arena: {side.upper()} {pair} ${size_usd:.0f} @ {leverage}x",
                    details={
                        "pair": pair,
                        "side": side,
                        "size_usd": round(size_usd, 2),
                        "leverage": leverage,
                        "agent": arena_agent['agent_name'],
                        "job_id": result.get('job_id'),
                        "status": status,
                    },
                    importance=5,
                )
            except Exception:
                pass

        except Exception as e:
            self._log.error(f"Claw arena trade failed: {e}")

    @staticmethod
    def _arena_to_pair(symbol: str) -> Optional[str]:
        """Convert any symbol format to HL bare name (e.g., 'ETH')."""
        if not symbol:
            return None
        # Strip common suffixes: BTC/USDT -> BTC, BTC-USDT -> BTC, BTCUSDT -> BTC
        for sep in ['/', '-']:
            if sep in symbol:
                symbol = symbol.split(sep)[0]
        # Handle BTCUSDT-style (no separator)
        for suffix in ['USDT', 'USD', 'USDC', 'PERP']:
            if symbol.upper().endswith(suffix) and len(symbol) > len(suffix):
                symbol = symbol[:-len(suffix)]
        return symbol.upper() if symbol.isalpha() and len(symbol) <= 10 else None

    async def _run_trading_v2(
        self,
        config: BotConfigV2,
        user_id: str,
        decision_result: Dict[str, Any],
        run_id: Optional[str] = None
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

            # Normalize action to trading_action
            if action in ["enter", "long", "enter_long"]:
                trading_action = "long"
            elif action in ["short", "enter_short"]:
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

            # Determine trading mode
            trading_mode = getattr(config, 'trading_mode', 'paper')
            is_live = trading_mode == 'symphony'
            is_aster = trading_mode == 'aster'
            is_hyperliquid = trading_mode == 'hyperliquid'

            if trading_action == "close":
                try:
                    from core.common.db import db_fetch_one
                    open_positions = []

                    if is_live or is_aster or is_hyperliquid:
                        provider = 'hyperliquid' if is_hyperliquid else ('aster' if is_aster else 'symphony')
                        result = await db_fetch_one("""
                            SELECT batch_id FROM live_trades
                            WHERE config_id = %s AND provider = %s AND closed_at IS NULL
                            ORDER BY created_at DESC LIMIT 1
                        """, (config.config_id, provider))
                        if result:
                            open_positions.append({'batch_id': result[0]})
                    else:
                        result = await db_fetch_one("""
                            SELECT trade_id, symbol, side FROM paper_trades
                            WHERE config_id = %s AND symbol = %s AND status = 'open'
                            ORDER BY opened_at DESC LIMIT 1
                        """, (config.config_id, symbol))
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

                    if is_hyperliquid:
                        trade_result = await self.hyperliquid_trading.close_position(
                            position['batch_id'],
                            user_id,
                            close_reason='position_management'
                        )
                    elif is_aster:
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
                if is_hyperliquid:
                    trade_result = await self.hyperliquid_trading.execute_trade_intent(trading_intent)
                    self._log.info(f"V2 Hyperliquid live trade completed: {trade_result.get('status')} for {symbol}")
                elif is_aster:
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
