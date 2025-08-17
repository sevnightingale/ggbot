"""
Decision Engine - Core orchestrator for the Decision Module.

This module contains the DecisionEngine class which coordinates:
- Fetching market data from the database
- Checking account status
- Managing dual-mode operation (new trades vs active trades)
- Generating trading decisions using LLMs
- Creating trade intents for the Trading Module
"""

import asyncio
import json
import uuid
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
import ccxt.async_support as ccxt

from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, DECISION_LLM_API_KEY
from core.common.logger import logger
from decision.llm_providers import get_llm_provider
from decision.interfaces.llm_provider import LLMProvider
from decision.services.price_service import PriceService
from decision.providers.ccxt_provider import CCXTPriceProvider


class DecisionEngine:
    """
    Core engine that orchestrates the decision-making process.
    
    Handles database queries, dual-mode logic, LLM interactions,
    and intent generation for trading decisions.
    """
    
    def __init__(self, user_id: str, config_id: str):
        """
        Initialize the Decision Engine.
        
        Args:
            user_id (str): UUID of the user
            config_id (str): UUID of the configuration
        """
        self.user_id = user_id
        self.config_id = config_id
        self.llm_provider: Optional[LLMProvider] = None
        self.config: Optional[Dict[str, Any]] = None
        self.price_service: Optional[PriceService] = None
        
        logger.bind(module="decision.engine", user_id=user_id).info(
            f"Initialized DecisionEngine for config {config_id}"
        )
    
    def _get_db_connection(self):
        """Get a database connection."""
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
    
    def _sanitize_for_json(self, obj: Any) -> Any:
        """
        Recursively convert Decimal objects to float for JSON serialization.
        Also handles datetime objects by converting to ISO format strings.
        
        Args:
            obj: The object to sanitize
            
        Returns:
            JSON-serializable version of the object
        """
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._sanitize_for_json(item) for item in obj)
        else:
            return obj
    
    def _calculate_time_in_trade(self, opened_at):
        """Calculate hours since trade was opened, handling both datetime and string formats."""
        if not opened_at:
            return "N/A"
        
        try:
            # If it's already a datetime object
            if isinstance(opened_at, datetime):
                if opened_at.tzinfo is None:
                    opened_at = opened_at.replace(tzinfo=timezone.utc)
                return f"{(datetime.now(timezone.utc) - opened_at).total_seconds() / 3600:.1f}"
            # If it's a string (ISO format)
            else:
                opened_dt = datetime.fromisoformat(str(opened_at).replace('Z', '+00:00'))
                if opened_dt.tzinfo is None:
                    opened_dt = opened_dt.replace(tzinfo=timezone.utc)
                return f"{(datetime.now(timezone.utc) - opened_dt).total_seconds() / 3600:.1f}"
        except Exception as e:
            logger.warning(f"Failed to calculate time in trade: {e}")
            return "N/A"
    
    async def initialize(self) -> None:
        """
        Initialize the engine by loading configuration and setting up LLM provider.
        """
        # Load configuration from database
        self.config = self._load_configuration()
        
        # Initialize LLM provider
        provider_name = self.config.get('llm_provider', 'deepseek')
        self.llm_provider = get_llm_provider(
            provider_name=provider_name,
            api_key=DECISION_LLM_API_KEY
        )
        
        # Initialize price service
        price_config = self.config.get('price_service', {})
        self.price_service = PriceService(price_config)
        
        # Health checks
        if not await self.llm_provider.health_check():
            logger.bind(module="decision.engine").warning(
                f"LLM provider {provider_name} health check failed"
            )
        
        # Check price service health
        price_health = await self.price_service.health_check()
        if price_health['overall_status'] != 'healthy':
            logger.bind(module="decision.engine").warning(
                f"Price service health check: {price_health['overall_status']}"
            )
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Load decision configuration from the database.
        
        Returns:
            Dict[str, Any]: Configuration data
        """
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT config_data 
                FROM configurations 
                WHERE user_id = %s 
                AND config_id = %s
            """, (self.user_id, self.config_id))
            
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"No configuration found for config_id {self.config_id}")
            
            # Extract decision config from unified config
            user_config = result['config_data']
            if 'decision' not in user_config:
                raise ValueError(f"No decision configuration in user config for config_id {self.config_id}")
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(f"Loaded decision configuration from unified config {self.config_id}")
            return user_config['decision']
            
        finally:
            conn.close()
    
    def _fetch_market_data(self, symbol: str) -> Dict[str, Dict[str, Any]]:
        """
        Fetch latest market data from the database using config_id + symbol pattern.
        
        This method now uses the new string-based indicator system exclusively.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTC/USD')
            
        Returns:
            Dict[str, Dict[str, Any]]: Market data organized by indicator timeframes
        """
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                f"Fetching market data for {symbol} with config_id {self.config_id}"
            )
            
            # Get the most recent data for this config_id + symbol
            cursor.execute("""
                SELECT source, data_type, indicators, raw_data, updated_at
                FROM market_data
                WHERE user_id = %s
                AND config_id = %s
                AND symbol = %s
                ORDER BY updated_at DESC
                LIMIT 1
            """, (self.user_id, self.config_id, symbol))
            
            result = cursor.fetchone()
            
            if not result:
                logger.bind(module="decision.engine", user_id=self.user_id).warning(
                    f"No market data found for config {self.config_id}, symbol {symbol}"
                )
                return {}
            
            # Process the new format - indicators are stored as string keys
            return self._process_string_based_indicators(result)
            
        finally:
            conn.close()
    
    def _process_string_based_indicators(self, db_result) -> Dict[str, Dict[str, Any]]:
        """
        Process string-based indicators from the new extraction format.
        
        Args:
            db_result: Database row with indicators stored as string keys
            
        Returns:
            Dict organized by timeframes for compatibility with existing decision logic
        """
        # Extract indicators from database result
        indicators = db_result.get('indicators') or {}
        
        # Group string-based indicators by timeframe for decision compatibility
        # E.g., "RSI_1h", "RSI_4h" → {1h: {RSI: ...}, 4h: {RSI: ...}}
        timeframe_data = {}
        
        for indicator_string, value in indicators.items():
            # Parse the indicator string (e.g., "RSI_1h" → {"indicator": "RSI", "timeframe": "1h"})
            try:
                from core.mcp.metadata import parse_indicator_string
                parsed = parse_indicator_string(indicator_string)
                
                indicator_name = parsed.get("indicator")
                timeframe = parsed.get("timeframe", "1h")  # Default to 1h
                
                # Initialize timeframe data structure if needed
                if timeframe not in timeframe_data:
                    timeframe_data[timeframe] = {
                        'indicators': {},
                        'signals': {},
                        'raw_data': {},
                        'latest_update': db_result.get('updated_at')
                    }
                
                # Store indicator value
                timeframe_data[timeframe]['indicators'][indicator_name] = value
                
                # Also store with full string name for compatibility with existing prompt logic
                timeframe_data[timeframe]['indicators'][indicator_string] = value
                
            except Exception as e:
                logger.bind(module="decision.engine", user_id=self.user_id).warning(
                    f"Error parsing indicator {indicator_string}: {e}"
                )
                continue
        
        # Add any additional data from raw_data field
        raw_data = db_result.get('raw_data') or {}
        if 'interpretation' in raw_data:
            # Add LLM interpretation to the primary timeframe
            primary_tf = next(iter(timeframe_data.keys())) if timeframe_data else '1h'
            if primary_tf not in timeframe_data:
                timeframe_data[primary_tf] = {'indicators': {}, 'signals': {}, 'raw_data': {}, 'latest_update': db_result.get('updated_at')}
            timeframe_data[primary_tf]['signals']['llm_analysis'] = raw_data['interpretation']
        
        logger.bind(module="decision.engine", user_id=self.user_id).info(
            f"Processed {len(indicators)} string-based indicators across {len(timeframe_data)} timeframes"
        )
        
        return self._sanitize_for_json(timeframe_data)
    
    def _fetch_account_state(self) -> Dict[str, Any]:
        """
        Fetch current account state from the database.
        
        Returns:
            Dict[str, Any]: Account state including balance, positions, margins
        """
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT balance_data, position_data, equity, available_margin, used_margin, updated_at
                FROM account_states
                WHERE user_id = %s
                AND config_id = %s
                ORDER BY updated_at DESC
                LIMIT 1
            """, (self.user_id, self.config_id))
            
            result = cursor.fetchone()
            if not result:
                logger.bind(module="decision.engine").warning(
                    "No account state found, using defaults"
                )
                return {
                    'equity': 0,
                    'available_margin': 0,
                    'used_margin': 0,
                    'positions': [],
                    'updated_at': None
                }
            
            # Check if data is stale (older than 5 minutes)
            if result['updated_at']:
                age = datetime.now(timezone.utc) - result['updated_at'].replace(tzinfo=timezone.utc)
                if age > timedelta(minutes=5):
                    logger.bind(module="decision.engine", user_id=self.user_id).warning(
                        f"Account state is {age.total_seconds()/60:.1f} minutes old"
                    )
            
            return {
                'equity': float(result['equity']),
                'available_margin': float(result['available_margin']) if result['available_margin'] else 0,
                'used_margin': float(result['used_margin']) if result['used_margin'] else 0,
                'positions': result['position_data'] or [],
                'balance_data': result['balance_data'],
                'updated_at': result['updated_at']
            }
            
        finally:
            conn.close()
    
    def _fetch_active_trades(self) -> List[Dict[str, Any]]:
        """
        Fetch active trades with their decision history.
        
        Returns:
            List[Dict[str, Any]]: List of active trades
        """
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT trade_id, symbol, entry_price, leverage, collateral_amount,
                       stop_loss, take_profit, opened_at, '{}'::jsonb AS execution_details
                FROM trades
                WHERE user_id = %s AND config_id = %s
                AND trade_status IN ('open', 'active', 'pending')
                ORDER BY opened_at DESC
            """, (self.user_id, self.config_id))
            
            trades = cursor.fetchall()
            
            # Convert to list of dicts and parse decision history from strategy_runs
            active_trades = []
            for trade in trades:
                trade_dict = dict(trade)
                
                # Fetch decision history from strategy_runs table
                trade_dict['decision_history'] = self._get_trade_decision_history(cursor, trade_dict['trade_id'])
                
                active_trades.append(trade_dict)
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                f"Found {len(active_trades)} active trades"
            )
            # Sanitize Decimal values before returning
            return self._sanitize_for_json(active_trades)
            
        finally:
            conn.close()
    
    def _get_trade_decision_history(self, cursor, trade_id: str) -> List[Dict[str, Any]]:
        """
        Fetch decision history for a trade from strategy_runs table.
        
        Args:
            cursor: Database cursor
            trade_id: Trade ID to fetch history for
            
        Returns:
            List of decision history entries
        """
        try:
            cursor.execute("""
                SELECT scenario, confidence_score, reasoning_log, decision_data, created_at
                FROM strategy_runs
                WHERE trade_id = %s
                ORDER BY created_at ASC
            """, (trade_id,))
            
            strategy_runs = cursor.fetchall()
            decision_history = []
            
            for run in strategy_runs:
                # Convert strategy_run to legacy decision history format
                decision_data = run['decision_data'] or {}
                
                history_entry = {
                    'timestamp': run['created_at'].isoformat() if run['created_at'] else None,
                    'action': decision_data.get('action', run['scenario'].lower()),
                    'confidence': run['confidence_score'],
                    'reasoning': run['reasoning_log'],
                    'scenario': run['scenario']  # Keep scenario for enhanced context
                }
                
                decision_history.append(history_entry)
            
            # Sanitize any Decimal values before returning
            return self._sanitize_for_json(decision_history)
            
        except Exception as e:
            logger.warning(f"Failed to fetch decision history for trade {trade_id}: {e}")
            return []
    
    async def _fetch_current_price(self, symbol: str) -> float:
        """
        Fetch current market price using the reliable PriceService.
        
        This method now uses the PriceService which provides consensus pricing
        from multiple reliable sources (YFinance + CCXT) instead of unreliable
        testnet data.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTC/USD', 'BTC/USDT')
            
        Returns:
            float: Current market price from consensus of reliable sources
            
        Raises:
            ValueError: If price service fails or prices are inconsistent
        """
        if not self.price_service:
            raise ValueError("Price service not initialized - call initialize() first")
        
        try:
            # Use reliable price service instead of testnet exchange
            current_price = await self.price_service.get_current_price(symbol)
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                f"Fetched reliable market price for {symbol}: ${current_price:,.2f}"
            )
            
            return current_price
            
        except Exception as e:
            logger.bind(module="decision.engine", user_id=self.user_id).error(
                f"Failed to fetch current price for {symbol}: {e}"
            )
            raise  # Re-raise to fail the decision process instead of using bad data
    
    def _fetch_latest_ggshot_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the latest ggShot signal for a symbol from the market_data table.
        
        Args:
            symbol (str): Trading symbol (e.g., 'AVAX/USDT')
            
        Returns:
            Optional[Dict[str, Any]]: Latest ggShot signal data or None if not found
        """
        try:
            conn = self._get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get the latest ggShot signal for this symbol from market_data table
                cur.execute("""
                    SELECT id, symbol, source, data_type, indicators, raw_data, updated_at
                    FROM market_data 
                    WHERE symbol = %s 
                    AND data_type = 'ggshot_signal'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (symbol,))
                
                result = cur.fetchone()
                if result:
                    logger.bind(module="decision.engine", user_id=self.user_id).info(f"Found ggShot signal for {symbol}: {result['id']}")
                    # Convert to expected format
                    return {
                        'signal_id': result['id'],
                        'symbol': result['symbol'],
                        'signal_type': 'ggshot',
                        'parsed_data': result['indicators'],  # ggshot signals store parsed data in indicators
                        'raw_data': result['raw_data'].get('message', '') if result['raw_data'] else '',
                        'created_at': result['updated_at']
                    }
                else:
                    logger.bind(module="decision.engine", user_id=self.user_id).warning(f"No ggShot signal found for {symbol}")
                    return None
                    
        except Exception as e:
            logger.bind(module="decision.engine", user_id=self.user_id).error(f"Error fetching ggShot signal for {symbol}: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def _update_trade_decision(self, trade_id: str, decision: str, confidence: float, reasoning: str) -> None:
        """
        Update a trade with a new decision in its history.
        
        Args:
            trade_id (str): UUID of the trade
            decision (str): The decision made (hold, adjust, close)
            confidence (float): Confidence level
            reasoning (str): Reasoning for the decision
        """
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            # First fetch current execution_details  
            cursor.execute("""
                SELECT '{}'::jsonb as execution_details
                FROM trades
                WHERE trade_id = %s
            """, (trade_id,))
            
            result = cursor.fetchone()
            execution_details = result['execution_details'] or {}
            
            # Add to decision history
            if 'decision_history' not in execution_details:
                execution_details['decision_history'] = []
            
            execution_details['decision_history'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'action': decision,
                'confidence': confidence,
                'reasoning': reasoning
            })
            
            # Store decision history in strategy_runs table for audit trail
            # Create a TRADE_MANAGEMENT strategy_run entry
            strategy_run_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO strategy_runs (
                    strategy_run_id, trade_id, config_id, scenario,
                    confidence_score, reasoning_log, decision_data, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                strategy_run_id,
                trade_id,
                self.config_id,
                'TRADE_MANAGEMENT',
                confidence,
                reasoning,
                json.dumps({
                    'action': decision,
                    'decision_type': 'trade_management',
                    'legacy_decision_history_entry': True
                }),
                datetime.now(timezone.utc)
            ))
            
            conn.commit()
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                f"Updated trade {trade_id} with decision: {decision}"
            )
            
        finally:
            conn.close()
    
    async def _format_prompt_new_trade(self, market_data: Dict, account_state: Dict, symbol: str, mode: str = "dynamic_strategy") -> str:
        """
        Format prompt for new trade evaluation.
        
        Args:
            market_data (Dict): Market data by timeframe
            account_state (Dict): Current account state
            symbol (str): Trading symbol
            mode (str): Decision mode - "dynamic_strategy" or "ggshot"
            
        Returns:
            str: Formatted prompt for the LLM
        """
        # Use mode to determine prompt type, not signal presence
        if mode == "ggshot":
            # ggShot mode - use specialized validation prompt regardless of signal presence in indicators
            return await self._format_ggshot_validation_prompt(market_data, account_state, symbol)
        else:
            # Standard mode
            return await self._format_standard_prompt(market_data, account_state, symbol)
    
    async def _format_ggshot_validation_prompt(self, market_data: Dict, account_state: Dict, symbol: str) -> str:
        """
        Format prompt for ggShot signal validation using the 4-Pillar Framework.
        
        Args:
            market_data (Dict): Market data by timeframe
            account_state (Dict): Current account state
            symbol (str): Trading symbol
            
        Returns:
            str: Formatted 4-pillar signal validation prompt
        """
        # Get the latest ggShot signal from database for this symbol
        ggshot_signal = self._fetch_latest_ggshot_signal(symbol)
        
        if not ggshot_signal:
            logger.bind(module="decision.engine", user_id=self.user_id).warning(f"No ggShot signal found for {symbol} - using standard prompt instead")
            return await self._format_standard_prompt(market_data, account_state, symbol)
        
        # Store signal data for later use in _create_intent
        self._current_ggshot_signal = ggshot_signal
        
        # Get original signal message from database raw_data
        raw_data = ggshot_signal.get('raw_data', {})
        if isinstance(raw_data, dict) and 'message' in raw_data:
            self._original_signal_message = raw_data['message']
        else:
            self._original_signal_message = str(raw_data)
        
        # Extract parsed signal details from database (minimal parsing for symbol/timeframe only)
        parsed_data = ggshot_signal.get('parsed_data', {}).get('ggshot_signal', {})
        
        # Fetch current market price
        current_price = await self._fetch_current_price(symbol)
        
        # We only need symbol and timeframe for extraction - let LLM read the original signal
        native_timeframe = parsed_data.get('timeframe', '1h')
        
        # Extract raw indicator data from market_data (NEW STRING-BASED FORMAT)
        def get_indicator_data(indicator_string: str) -> str:
            """Helper to safely extract indicator data from new string-based format"""
            try:
                # NEW APPROACH: Look for the exact string-based indicator
                # across all timeframes in the processed market_data
                for tf_data in market_data.values():
                    if isinstance(tf_data, dict) and 'indicators' in tf_data:
                        if indicator_string in tf_data['indicators']:
                            raw_data = tf_data['indicators'][indicator_string]
                            
                            # If this is a preprocessed object, extract the clean summary
                            if isinstance(raw_data, dict) and 'summary' in raw_data:
                                return raw_data['summary']
                            else:
                                return str(raw_data)
                
                return "N/A"
            except Exception as e:
                logger.bind(module="decision.engine", user_id=self.user_id).warning(f"Error extracting {indicator_string}: {e}")
                return "N/A"
        
        # Check indicator availability (updated for new ggShot config)
        def check_indicator_availability() -> tuple[bool, str, int]:
            """Check if we have minimum required indicators for reliable analysis"""
            required_indicators = ['Aroon', 'Aroon_long', 'VWAP', 'RSI', 'RSI_4h']
            available_indicators = []
            
            for indicator in required_indicators:
                if indicator == 'RSI_4h':
                    data = get_indicator_data('RSI_4h')
                elif indicator == 'Aroon':
                    data = get_indicator_data('Aroon_1d')  # NEW: String-based indicator
                elif indicator == 'Aroon_long':
                    data = get_indicator_data('Aroon_60_1d')  # NEW: Long-term Aroon
                elif indicator == 'VWAP':
                    data = get_indicator_data('VWAP_1h')   # NEW: String-based indicator
                elif indicator == 'RSI':
                    data = get_indicator_data('RSI_30m')   # NEW: String-based indicator
                else:
                    data = get_indicator_data(indicator)
                
                if data != 'N/A':
                    available_indicators.append(indicator)
            
            availability_count = len(available_indicators)
            availability_ratio = availability_count / len(required_indicators)
            
            # Require at least 4/6 critical indicators (including both Aroon timeframes)
            if availability_count < 4:
                missing = set(required_indicators) - set(available_indicators)
                warning = f"Insufficient indicators: only {availability_count}/6 available. Missing: {', '.join(missing)}"
                return False, warning, availability_count
            
            return True, f"Sufficient indicators: {availability_count}/6 available", availability_count
        
        sufficient_data, availability_message, available_count = check_indicator_availability()
        
        # Log indicator availability
        logger.bind(module="decision.engine", user_id=self.user_id).info(f"Indicator availability: {availability_message}")
        
        # Get current volume using CCXT provider with signal's native timeframe
        current_volume_data = await self._get_volume_confirmation(symbol, native_timeframe)
        
        # Log the ggShot validation prompt details
        logger.bind(module="decision.engine", user_id=self.user_id).info(f"🎯 4-Pillar ggShot validation for {symbol}:")
        logger.bind(module="decision.engine", user_id=self.user_id).info(f"   Native Timeframe: {native_timeframe}")
        logger.bind(module="decision.engine", user_id=self.user_id).info(f"   Current Price: ${current_price}" if current_price else "Price unavailable")
        logger.bind(module="decision.engine", user_id=self.user_id).info(f"   Original Signal: {self._original_signal_message[:100]}...")
        
        # Build the complete 4-pillar validation prompt
        prompt = f"""ggShot Signal Validation Protocol v4.0 (Guardrail Framework)

MISSION
You are validating a ggShot signal using the Four-Pillar Framework with empirically-validated boundaries.

PHASE 1 (Pillar-scoring judgment): Choose values strictly within each pillar's numeric range.
PHASE 2 (Math): Sum the scores. If total <0.05 set to 0.05; if >0.95 set to 0.95.
NO further edits, rescaling, or overrides after Phase 2. If you attempt to alter the post-clamp value, output "ERROR".

NOTE: Avoid rationalizing conflicting signals. When red flags appear, respect their significance and adjust confidence accordingly.

1. ORIGINAL GGSHOT SIGNAL
{self._original_signal_message}

2. CURRENT MARKET CONDITIONS  
Current Price: ${current_price}
Analysis Timeframe: {native_timeframe}

3. CONFIDENCE ASSESSMENT FRAMEWORK

Starting Baseline: 0.700 (Signal presumed valid - identify flaws to justify rejection)

Assess each pillar and determine confidence adjustments within these empirically-validated boundaries:

PILLAR 0 - MARKET REGIME ASSESSMENT
Core Question: "Is this signal aligned with or fighting the market trend?"

Available Data:
- Aroon Short-term (14-period): {get_indicator_data('Aroon_1d')}
- Aroon Long-term (60-period): {get_indicator_data('Aroon_60_1d')}  
- Bollinger Band Width: {get_indicator_data('BollingerBandsWidth_1d')}
- TRIX: {get_indicator_data('TRIX_1d')}

Assessment Boundaries:
- Strong trend alignment (both Aroon timeframes favor signal direction): +0.03 to +0.08
- Moderate trend alignment (mixed signals, some consolidation): +0.00 to +0.03
- Counter-trend setup (short-term trend opposes signal): -0.20 to -0.08
  With volume confirmation >2.5x: reduce penalty below -0.12
- Ranging/consolidating markets (both timeframes ranging): -0.06 to -0.12

Micro-adjustments within ranges:
- BBW >75th percentile + direction aligns: bias toward upper end of positive ranges
- BBW <25th percentile (ranging/squeeze): bias toward lower end of negative ranges (-0.10 to -0.12)
- TRIX momentum slope aligns with signal: bias toward upper range end
- TRIX momentum opposes signal: bias toward lower range end

Counter-trend setups have shown higher risk in our analysis. Consider this when assessing regime alignment.

PILLAR 1 - SIGNAL CONFIRMATION  
Core Question: "Do volume and momentum indicators strongly support this direction?"

Available Data:
- Volume Analysis: {current_volume_data}
- VWAP: {get_indicator_data('VWAP_1h')}
- MFI: {get_indicator_data('MFI_1h')}

Assessment Boundaries:
- Exceptional volume (>1.5x avg) with momentum alignment: +0.05 to +0.12
- Strong volume (1.0-1.5x avg) with momentum alignment: +0.00 to +0.04
- Moderate volume with mixed momentum: +0.00 to +0.02
- Weak volume (<0.75x avg): -0.06 to -0.12
- MFI strongly opposing direction (>20 points): -0.07 to -0.14

Micro-adjustments within ranges:
- Price vs VWAP favorable side by >1%: bias toward upper end of positive ranges
- Price vs VWAP wrong side by >1%: bias toward lower end of negative ranges

Weak volume and MFI divergence have been notable risk factors. Consider their combined impact.

PILLAR 2 - MULTI-TIMEFRAME CONTEXT
Core Question: "Are we buying tops or selling bottoms across timeframes?"

Available Data:
- RSI 15m: {get_indicator_data('RSI_15m')}
- RSI 30m: {get_indicator_data('RSI_30m')}  
- RSI 1h: {get_indicator_data('RSI_1h')}
- RSI 4h: {get_indicator_data('RSI_4h')}
- Donchian Channel: {get_indicator_data('DonchianChannel_200_1h')}

Assessment Boundaries:
- All timeframes aligned, RSI has room to move: +0.02 to +0.06
- Mixed timeframe signals, some overextension: -0.02 to -0.05
- Poor alignment, severe overextension: -0.04 to -0.10
- Trading into RSI extremes opposing signal: -0.06 to -0.12

Micro-adjustments within ranges:
- Donchian breakout aligning with signal direction: bias toward upper end of positive ranges
- Price at Donchian extreme opposing signal direction: bias toward lower end of negative ranges
- Donchian position >80% with direction alignment: +0.02 to +0.04 additional boost

PILLAR 3 - IMMEDIATE CONDITIONS
Core Question: "Are there immediate execution risks?"

Available Data:
- Bollinger Bands: {get_indicator_data('BollingerBands_1h')}
- ATR: {get_indicator_data('ATR_1h')}

Assessment Boundaries:
- Favorable positioning, normal volatility: +0.00 to +0.04
- Some overextension but manageable: -0.01 to -0.04
- Severe overextension, extreme volatility: -0.03 to -0.08
- Late entry timing (at edge of entry zone): -0.04 to -0.08

COMBINATION EFFECTS
When multiple red flags appear together:
- 2 red flags: -0.02 to -0.04
- 3 red flags: -0.03 to -0.06
- 4+ red flags: -0.04 to -0.08

CONFIDENCE BOUNDARIES
Mathematical limits ONLY - no subjective adjustments:
- If final calculation > 0.95: set confidence to exactly 0.95
- If final calculation < 0.05: set confidence to exactly 0.05
- Otherwise: use exact calculated value

4. ASSESSMENT APPROACH

PHASE 1 (Pillar-scoring judgment): Choose values strictly within each pillar's numeric range.
PHASE 2 (Math): Sum the scores. If total <0.05 set to 0.05; if >0.95 set to 0.95.
NO further edits, rescaling, or overrides after Phase 2. If you attempt to alter the post-clamp value, output "ERROR".

1. Start with baseline: 0.700
2. Apply each pillar adjustment sequentially (show running total after each)
3. Apply combination effects if multiple red flags present
4. Apply boundary limits ONLY if calculation exceeds 0.05-0.95 range
5. Report final confidence to 3 decimal places

5. FINAL OUTPUT

First, provide your reasoning analysis, then output the structured results:

REASONING:
Write your analysis in plain text format suitable for Telegram publishing. DO NOT USE ANY MARKDOWN FORMATTING - no asterisks (*), no bold (**), no underscores (_), no backticks (`), no headers (#). Use only plain text with dashes (-) for bullet points.

Provide your analysis using this exact structure:
- Baseline: 0.700
- Pillar 0 - Market Regime: [adjustment and decisive reasoning]
- Pillar 1 - Signal Confirmation: [adjustment and decisive reasoning]
- Pillar 2 - Multi-Timeframe: [adjustment and decisive reasoning]
- Pillar 3 - Immediate Conditions: [adjustment and decisive reasoning]
- Combination Effects: [if multiple red flags present]
- Primary Direction: [Trend-aligned / Counter-trend / Ranging market]
- Volume Strength: [Exceptional / Strong / Moderate / Weak]
- Critical Risks: [List any major red flags identified]
- Confidence Rationale: [Decisive explanation of final score]
- Final Calculation: [show math with running totals]

Use exact numerical boundaries provided for each pillar. Apply adjustments systematically without subjective offsets. Show all mathematical calculations explicitly.

After completing your reasoning and calculation above, provide the structured output in plain text format with NO FORMATTING:

ACTION: [extract direction from signal - if signal contains "Long" use "long", if contains "Short" use "short"]
CONFIDENCE: [use the exact result from your Final Calculation above, 3 decimal places]
STOP_LOSS: [extract from signal]  
TAKE_PROFIT: [extract Target 1 from signal]
"""
        
        return prompt
    
    async def _format_standard_prompt(self, market_data: Dict, account_state: Dict, symbol: str) -> str:
        """
        Format standard prompt for new trade evaluation (original logic).
        
        Args:
            market_data (Dict): Market data by timeframe
            account_state (Dict): Current account state
            symbol (str): Trading symbol
            
        Returns:
            str: Formatted prompt for the LLM
        """
        # Fetch current market price
        current_price = await self._fetch_current_price(symbol)
        
        prompt_parts = [
            f"# Trading Decision Request - New Trade Evaluation",
            f"Symbol: {symbol}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Current Market Price",
            f"- {symbol}: ${current_price}" if current_price else f"- {symbol}: Price unavailable",
            "",
            "## Account Status",
            f"- Total Equity: {account_state['equity']:.8f} BTC",
            f"- Available Margin: {account_state['available_margin']:.8f} BTC",
            f"- Used Margin: {account_state['used_margin']:.8f} BTC",
            f"- Open Positions: {len(account_state['positions'])}",
            f"- Account Balance (USD): ~${account_state['available_margin'] * (current_price or 104000):,.0f}" if current_price else f"- Account Balance (USD): ~${account_state['available_margin'] * 104000:,.0f}",
            ""
        ]
        
        # Add market data for each timeframe
        prompt_parts.append("## Market Data")
        for timeframe, data in market_data.items():
            prompt_parts.append(f"\n### {timeframe} Timeframe")
            
            # Add indicators
            if data['indicators']:
                prompt_parts.append("Indicators:")
                for indicator, value in data['indicators'].items():
                    if isinstance(value, (int, float)):
                        prompt_parts.append(f"- {indicator}: {value:.2f}")
                    else:
                        # Handle complex RSI data format - extract actual numeric values
                        if indicator == 'RSI' and isinstance(value, str):
                            # Extract numeric RSI values from the complex string format
                            rsi_value = self._extract_current_rsi_value(value)
                            if rsi_value is not None:
                                prompt_parts.append(f"- {indicator}: {rsi_value:.2f} ({'ABOVE 50 = SHORT' if rsi_value > 50 else 'BELOW 50 = LONG'})")
                                logger.info(f"🎯 EXTRACTED RSI for {timeframe}: {rsi_value:.2f} -> {'SHORT' if rsi_value > 50 else 'LONG'}")
                            else:
                                prompt_parts.append(f"- {indicator}: [Error extracting value from: {str(value)[:100]}...]")
                                logger.error(f"❌ Failed to extract RSI from: {str(value)[:200]}...")
                        else:
                            prompt_parts.append(f"- {indicator}: {value}")
            
            # Add signals
            if data['signals']:
                prompt_parts.append("\nSignals:")
                for source, signal in data['signals'].items():
                    prompt_parts.append(f"- {source}: {signal}")
        
        # Add strategy and instructions
        prompt_parts.extend([
            "",
            "## Trading Strategy",
            self.config.get('strategy', 'No strategy defined'),
            "",
            "## Risk Guidelines",
            self.config.get('risk_guidelines', 'No risk guidelines defined'),
            "",
            "## Additional Context", 
            self.config.get('additional_context', 'No additional context'),
            "",
            "## How to Use This Information",
            "The Trading Strategy section above contains the user-defined rules for making trading decisions.",
            "The Market Data section contains various technical indicators, price action, and other data points about the symbol.",
            "",
            "Your task is to analyze the Market Data through the lens of the Trading Strategy to make a decision.",
            "The strategy may include specific rules, patterns to look for, or confidence scoring guidelines.",
            "",
            "## Decision Required",
            "Based on the market data and trading strategy, should we enter a new position?",
            "",
            "Please provide your decision in this EXACT format:",
            "",
            "ACTION: [long/short/no_action]",
            "CONFIDENCE: [0.00-1.00]",
            "STOP_LOSS: [price as number only, e.g. X.XX]",
            "TAKE_PROFIT: [price as number only, e.g. X.XX]",
            "",
            "REASONING:",
            "Your detailed analysis including:",
            "- How the current market conditions align with the trading strategy",
            "- Key factors influencing your confidence score", 
            "- Exit plan and expected timeline",
            "",
            "IMPORTANT:",
            "- Express your true confidence level - avoid defaulting to middle values unless your uncertainty is genuine",
            "- Use the current market price shown above for stop loss and take profit calculations",
            "- Your confidence score should reflect how strongly the current setup matches the strategy criteria"
        ])
        
        return "\n".join(prompt_parts)
    
    def _extract_current_rsi_value(self, rsi_raw_data: str) -> float:
        """
        Extract the current RSI value from the complex MCP response format.
        
        Args:
            rsi_raw_data (str): Raw RSI data string from MCP
            
        Returns:
            float: Current RSI value or None if extraction fails
        """
        try:
            # The RSI data comes in format: "meta=None content=[TextContent(type='text', text='[0,0,56.93411542892993,...]')]"
            # We need to extract the last value from the array
            
            # Find the text content array
            if 'text=\'[' in rsi_raw_data:
                start_idx = rsi_raw_data.find('text=\'[') + 7  # Skip "text='["
                end_idx = rsi_raw_data.find(']\'', start_idx)
                if end_idx != -1:
                    array_str = rsi_raw_data[start_idx:end_idx]
                    # Split by comma and get last non-zero value
                    values = [float(x.strip()) for x in array_str.split(',') if x.strip()]
                    # Return the last value (most recent RSI)
                    if values:
                        current_rsi = values[-1]
                        logger.bind(module="decision.engine", user_id=self.user_id).info(
                            f"Successfully extracted current RSI: {current_rsi}"
                        )
                        return current_rsi
            
            logger.bind(module="decision.engine", user_id=self.user_id).warning(
                f"Failed to extract RSI from: {rsi_raw_data[:200]}..."
            )
            return None
            
        except Exception as e:
            logger.bind(module="decision.engine", user_id=self.user_id).error(
                f"Error extracting RSI value: {e}"
            )
            return None
    
    def _get_dynamic_volume_period(self, timeframe: str) -> int:
        """
        Calculate dynamic volume period based on timeframe.
        Lower timeframes get more periods for stability (closer to 50).
        Higher timeframes get fewer periods to avoid lag (closer to 20).
        
        Args:
            timeframe: Signal timeframe (e.g., '5m', '30m', '1h', '4h')
            
        Returns:
            int: Number of periods for volume average (20-50 range)
        """
        timeframe_periods = {
            '5m': 50,   # ~4 hours of data
            '15m': 50,  # ~12.5 hours of data
            '30m': 50,  # ~25 hours of data
            '1h': 35,   # ~35 hours of data
            '4h': 20,   # ~3.3 days of data
            '1d': 20,   # ~20 days of data
        }
        
        # Default to 30 if timeframe not recognized
        return timeframe_periods.get(timeframe, 30)
    
    async def _get_volume_confirmation(self, symbol: str, timeframe: str = '1h') -> str:
        """
        Get volume confirmation analysis using CCXT provider.
        Based on ggShot founder's guidance on volume thresholds.
        
        Args:
            symbol: Trading symbol to analyze
            timeframe: Timeframe for volume analysis (matches signal timeframe)
            
        Returns:
            Formatted string with volume analysis and confidence level
        """
        try:
            # Initialize CCXT provider
            ccxt_provider = CCXTPriceProvider()
            
            # Get dynamic period based on timeframe
            period = self._get_dynamic_volume_period(timeframe)
            
            # Get volume data with dynamic period and signal's native timeframe
            volume_data = await ccxt_provider.get_current_volume_data(symbol, period=period, timeframe=timeframe)
            
            if not volume_data:
                return "N/A (volume data unavailable from exchanges)"
            
            current_volume = volume_data['current_volume']
            average_volume = volume_data['average_volume']
            volume_ratio = volume_data['volume_ratio']
            
            # Calculate percentage above average
            volume_increase_pct = (volume_ratio - 1.0) * 100
            
            # Determine volume confidence level - softer interpretation for LLM reasoning
            if volume_increase_pct < 10:
                confidence_level = "Insignificant"
                confidence_desc = "The signal is weak or 'sluggish'"
            elif volume_increase_pct < 30:
                confidence_level = "Easy Confirmation" 
                confidence_desc = "Entry with risk is possible"
            elif volume_increase_pct < 60:
                confidence_level = "Good Confirmation"
                confidence_desc = "Volume supports the move"
            elif volume_increase_pct < 100:
                confidence_level = "Strong Confirmation"
                confidence_desc = "Confident entry"
            else:
                confidence_level = "Very Strong Momentum"
                confidence_desc = "Often indicates breakout"
            
            # Format the volume analysis with clear period context
            period_used = volume_data.get('period_used', 30)
            volume_analysis = f"""Timeframe: {timeframe} | Period: {period_used} candles
Current Volume: {current_volume:,.0f} (last completed {timeframe} candle)
Average Volume: {average_volume:,.0f} ({period_used}-period average)
Volume Ratio: {volume_ratio:.2f}x | Above Average: {volume_increase_pct:+.1f}%
Confirmation Level: {confidence_level} - {confidence_desc}"""
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                f"Volume analysis for {symbol} ({timeframe}, {period_used} periods): {volume_increase_pct:+.1f}% above average ({confidence_level})"
            )
            
            return volume_analysis
            
        except Exception as e:
            logger.bind(module="decision.engine", user_id=self.user_id).warning(
                f"Failed to get volume confirmation for {symbol}: {e}"
            )
            return f"N/A (volume analysis failed: {str(e)})"
    
    def _format_prompt_manage_trade(self, market_data: Dict, account_state: Dict, 
                                   active_trade: Dict, symbol: str) -> str:
        """
        Format prompt for active trade management.
        
        Args:
            market_data (Dict): Market data by timeframe
            account_state (Dict): Current account state
            active_trade (Dict): The active trade to manage
            symbol (str): Trading symbol
            
        Returns:
            str: Formatted prompt for the LLM
        """
        # Calculate current P&L if we have position data
        current_pnl = 0
        position_info = "Position details not available"
        
        for position in account_state.get('positions', []):
            if position.get('symbol') == symbol:
                current_pnl = position.get('unrealized_pnl', 0)
                position_info = (
                    f"Entry: {active_trade.get('entry_price', 'N/A')}, "
                    f"Current P&L: {current_pnl:.4f} BTC ({position.get('unrealized_pnl_pct', 0):.2f}%)"
                )
                break
        
        prompt_parts = [
            f"# Trading Decision Request - Active Trade Management",
            f"Symbol: {symbol}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Current Position",
            f"- Trade ID: {active_trade['trade_id']}",
            f"- Direction: {'Long' if active_trade.get('side') == 'long' else 'Short' if active_trade.get('side') == 'short' else 'Net'}",
            f"- {position_info}",
            f"- Leverage: {active_trade.get('leverage', 'N/A')}x",
            f"- Stop Loss: {active_trade.get('stop_loss', 'N/A')}",
            f"- Take Profit: {active_trade.get('take_profit', 'N/A')}",
            f"- Time in Trade: {self._calculate_time_in_trade(active_trade.get('opened_at'))} hours",
            ""
        ]
        
        # Add decision history
        if active_trade.get('decision_history'):
            prompt_parts.append("## Decision History")
            for i, decision in enumerate(active_trade['decision_history'][-3:]):  # Last 3 decisions
                prompt_parts.append(
                    f"{i+1}. {decision['timestamp']}: {decision['action']} "
                    f"(confidence: {decision['confidence']}) - {decision['reasoning']}"
                )
            prompt_parts.append("")
        
        # Add current market data (same as new trade)
        prompt_parts.append("## Current Market Data")
        for timeframe, data in market_data.items():
            prompt_parts.append(f"\n### {timeframe} Timeframe")
            
            if data['indicators']:
                prompt_parts.append("Indicators:")
                for indicator, value in data['indicators'].items():
                    if isinstance(value, (int, float)):
                        prompt_parts.append(f"- {indicator}: {value:.2f}")
                    else:
                        prompt_parts.append(f"- {indicator}: {value}")
            
            if data['signals']:
                prompt_parts.append("\nSignals:")
                for source, signal in data['signals'].items():
                    prompt_parts.append(f"- {source}: {signal}")
        
        # Add strategy reminder and decision request
        prompt_parts.extend([
            "",
            "## Trading Strategy",
            self.config.get('strategy', 'No strategy defined')[:200] + "...",
            "",
            "## Decision Required",
            "Should we continue holding this position, adjust it, or close it?",
            "Consider the original entry reasoning and how market conditions have changed.",
            "",
            "Please provide your decision in this EXACT format:",
            "",
            "ACTION: [hold/add/reduce/close/adjust_stops]",
            "CONFIDENCE: [0.00-1.00]",
            "STOP_LOSS: [ONLY if 'adjust_stops': price as number only, e.g. X.XX]",
            "TAKE_PROFIT: [ONLY if 'adjust_stops': price as number only, e.g. X.XX]",
            "",
            "REASONING:",
            "Your analysis including:",
            "- Current position status and P&L",
            "- Why this action based on strategy", 
            "- Risk management considerations",
            "- Updated market outlook",
            "",
            "IMPORTANT:",
            "- Express your true confidence level - avoid defaulting to middle values unless your uncertainty is genuine",
            "- Your confidence should reflect how strongly you believe in the action based on current conditions"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, response: str, mode: str = 'new_trade') -> Dict[str, Any]:
        """
        Parse LLM response focusing on confidence, stop/take profit, and reasoning.
        Position sizing will be handled by the Trading Module based on confidence.
        
        Args:
            response (str): Raw LLM response
            mode (str): 'new_trade' or 'manage_trade'
            
        Returns:
            Dict[str, Any]: Decision data with confidence, reasoning, and raw response
        """
        # Initialize result with defaults
        result = {
            'confidence': 0.5,  # Default moderate confidence if not found
            'reasoning': '',  # Will be extracted
            'raw_response': response,
            'mode': mode
        }
        
        # Parse line by line for confidence, stop/take profit, and reasoning
        lines = response.strip().split('\n')
        capture_reasoning = False
        reasoning_lines = []
        import re
        
        for line in lines:
            line_stripped = line.strip()
            line_upper = line_stripped.upper()
            
            # Look for ACTION: (uppercase format)
            if 'ACTION:' in line_upper:
                try:
                    parts = line_stripped.split(':', 1)
                    if len(parts) >= 2:
                        action_str = parts[1].strip().lower()
                        # Clean common formatting
                        action_str = action_str.replace('**', '').replace('*', '').strip()
                        if action_str in ['long', 'short', 'no_action', 'hold', 'add', 'reduce', 'close', 'adjust_stops']:
                            result['action'] = action_str
                            logger.bind(module="decision.engine").info(f"Parsed action: {result['action']}")
                except Exception as e:
                    logger.bind(module="decision.engine").warning(f"Failed to parse action: {e}")
            
            # Look for CONFIDENCE: (uppercase format)
            elif 'CONFIDENCE:' in line_upper:
                try:
                    parts = line_stripped.split(':', 1)
                    if len(parts) >= 2:
                        confidence_str = parts[1].strip()
                        # Clean formatting and extract number
                        confidence_str = confidence_str.replace('**', '').replace('*', '').replace('%', '')
                        numbers = re.findall(r'\d*\.?\d+', confidence_str)
                        if numbers:
                            confidence = float(numbers[0])
                            result['confidence'] = max(0.0, min(1.0, confidence))
                            logger.bind(module="decision.engine").info(f"Parsed confidence: {result['confidence']}")
                except Exception as e:
                    logger.bind(module="decision.engine").warning(f"Failed to parse confidence: {e}")
            
            # Look for STOP_LOSS: (uppercase format)
            elif 'STOP_LOSS:' in line_upper or 'STOP LOSS:' in line_upper:
                try:
                    parts = line_stripped.split(':', 1)
                    if len(parts) >= 2:
                        stop_loss_str = parts[1].strip()
                        # Extract number, avoid example values like "X.XX"
                        stop_loss_str = stop_loss_str.replace(',', '').replace('$', '').replace('X.XX', '').strip()
                        numbers = re.findall(r'\d+\.?\d*', stop_loss_str)
                        if numbers:
                            result['stop_loss_price'] = float(numbers[0])
                            logger.bind(module="decision.engine").info(f"Parsed stop_loss_price: {result['stop_loss_price']}")
                except Exception as e:
                    logger.bind(module="decision.engine").warning(f"Failed to parse stop_loss_price: {e}")
            
            # Look for TAKE_PROFIT: (uppercase format)
            elif 'TAKE_PROFIT:' in line_upper or 'TAKE PROFIT:' in line_upper:
                try:
                    parts = line_stripped.split(':', 1)
                    if len(parts) >= 2:
                        take_profit_str = parts[1].strip()
                        # Extract number, avoid example values like "X.XX"
                        take_profit_str = take_profit_str.replace(',', '').replace('$', '').replace('X.XX', '').strip()
                        numbers = re.findall(r'\d+\.?\d*', take_profit_str)
                        if numbers:
                            result['take_profit_price'] = float(numbers[0])
                            logger.bind(module="decision.engine").info(f"Parsed take_profit_price: {result['take_profit_price']}")
                except Exception as e:
                    logger.bind(module="decision.engine").warning(f"Failed to parse take_profit_price: {e}")
            
            # Look for REASONING: section (uppercase format)
            elif 'REASONING:' in line_upper or capture_reasoning:
                if 'REASONING:' in line_upper:
                    capture_reasoning = True
                    # Get any text after "REASONING:" on the same line
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        reasoning_text = parts[1].strip()
                        if reasoning_text:
                            reasoning_lines.append(reasoning_text)
                elif capture_reasoning and line_stripped:
                    # Continue capturing reasoning until we hit another section
                    if any(x in line_upper for x in ['ACTION:', 'CONFIDENCE:', 'STOP_LOSS:', 'TAKE_PROFIT:', 'STOP LOSS:', 'TAKE PROFIT:']):
                        capture_reasoning = False
                    else:
                        reasoning_lines.append(line)
        
        # Join reasoning lines
        if reasoning_lines:
            result['reasoning'] = '\n'.join(reasoning_lines).strip()
        else:
            # Fallback: use the entire response as reasoning if we couldn't parse it
            result['reasoning'] = response
        
        # Validate confidence is present
        if result['confidence'] == 0.5:
            logger.bind(module="decision.engine").warning(
                "Confidence not found in response, using default 0.5. This may indicate parsing issues."
            )
        
        # Add ggShot signal data if this was a signal validation
        if hasattr(self, '_current_ggshot_signal') and self._current_ggshot_signal:
            result['ggshot_signal_data'] = self._current_ggshot_signal
            result['original_signal'] = getattr(self, '_original_signal_message', 'Signal message not available')
            # Clear the temporary storage
            self._current_ggshot_signal = None
            self._original_signal_message = None
        
        logger.bind(module="decision.engine").info(
            f"Parsed LLM response: confidence={result['confidence']}, "
            f"stop_loss={result.get('stop_loss_price', 'Not found')}, "
            f"take_profit={result.get('take_profit_price', 'Not found')}, "
            f"reasoning_length={len(result['reasoning'])}, "
            f"ggshot_signal={'Yes' if result.get('ggshot_signal_data') else 'No'}"
        )
        
        return result
    
    async def make_decision(self, symbol: str = "BTC/USD", 
                          mode: str = "dynamic_strategy",
                          custom_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point to make a trading decision.
        
        Args:
            symbol (str): Trading symbol
            mode (str): Decision mode - "dynamic_strategy" or "ggshot"
            
        Returns:
            Dict[str, Any]: Trading intent ready for the Trading Module
        """
        if not self.llm_provider:
            await self.initialize()
        
        try:
            # Fetch all required data using new config_id approach
            market_data = self._fetch_market_data(symbol)
            account_state = self._fetch_account_state()
            active_trades = self._fetch_active_trades()
        except Exception as e:
            logger.bind(module="decision.engine", user_id=self.user_id).error(
                f"Failed to fetch required data: {e}"
            )
            return {
                'action': 'error',
                'confidence': 0.0,
                'error': f'Data fetch failure: {str(e)}',
                'user_id': self.user_id,
                'config_id': self.config_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        # Determine mode and process accordingly
        if active_trades:
            # Trade Management Mode
            logger.bind(module="decision.engine").info(
                f"Entering Trade Management Mode with {len(active_trades)} active trades"
            )
            
            decisions = []
            for trade in active_trades:
                # Format prompt for this specific trade
                prompt = self._format_prompt_manage_trade(
                    market_data, account_state, trade, symbol
                )
                
                # DEBUG: Log the full prompt
                logger.bind(module="decision.engine", user_id=self.user_id).info(
                    "📝 DECISION LLM USER PROMPT (MANAGE):\n{prompt}",
                    prompt=prompt
                )
                
                # Get decision from LLM (trade management uses standard mode)
                response, metadata = await self.llm_provider.generate_response(
                    prompt=prompt,
                    conversation_history=trade.get('decision_history', []),
                    temperature=0.7,
                    custom_mode="trade_management"  # Trade management has its own mode
                )
                
                # DEBUG: Log the full response
                logger.bind(module="decision.engine", user_id=self.user_id).info(
                    "🤖 DECISION LLM RESPONSE (MANAGE):\n{response}",
                    response=response
                )
                
                # Parse response
                decision = self._parse_llm_response(response, mode='manage_trade')
                decision['trade_id'] = trade['trade_id']
                decision['metadata'] = metadata
                
                # Update trade history
                self._update_trade_decision(
                    trade['trade_id'],
                    decision.get('action', 'unknown'),
                    decision['confidence'],
                    decision['reasoning']
                )
                
                decisions.append(decision)
            
            # For now, return the first decision (in future, could handle multiple)
            if decisions:
                return self._create_intent(decisions[0], mode='manage', symbol=symbol)
        
        else:
            # New Trade Mode
            logger.bind(module="decision.engine", user_id=self.user_id).info("Entering New Trade Mode")
            
            try:
                # Format prompt (this may fail if price service fails)
                prompt = await self._format_prompt_new_trade(market_data, account_state, symbol, mode)
                
                # DEBUG: Log the full prompt
                logger.bind(module="decision.engine", user_id=self.user_id).info(
                    "📝 DECISION LLM USER PROMPT:\n{prompt}",
                    prompt=prompt
                )
                
                # Get decision from LLM (pass custom_mode for ggShot system prompt)
                response, metadata = await self.llm_provider.generate_response(
                    prompt=prompt,
                    temperature=0.7,
                    custom_mode=custom_mode  # Pass custom_mode to enable ggShot system prompts
                )
                
                # NEW: Fire-and-forget parallel testing for ggShot
                if custom_mode == "ggshot":
                    asyncio.create_task(
                        self._fire_ggshot_parallel_testing(
                            original_signal=getattr(self, '_original_signal_message', ''),
                            market_data=market_data,
                            symbol=symbol,
                            user_id=self.user_id
                        )
                    )
                
                # DEBUG: Log the full response
                logger.bind(module="decision.engine", user_id=self.user_id).info(
                    "🤖 DECISION LLM RESPONSE:\n{response}",
                    response=response
                )
                
                # Parse response
                decision = self._parse_llm_response(response, mode='new_trade')
                decision['metadata'] = metadata
                
                # For ggShot mode, store the full prompt for backtesting
                if custom_mode == "ggshot":
                    decision['full_prompt'] = prompt
                
                return self._create_intent(decision, mode='new', symbol=symbol)
                
            except Exception as e:
                logger.bind(module="decision.engine", user_id=self.user_id).error(
                    f"Failed to generate decision for {symbol}: {e}"
                )
                return {
                    'action': 'error',
                    'confidence': 0.0,
                    'error': f'Decision generation failure: {str(e)}',
                    'user_id': self.user_id,
                    'config_id': self.config_id,
                    'symbol': symbol,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
    
    def _create_intent(self, decision: Dict[str, Any], mode: str, symbol: str) -> Dict[str, Any]:
        """
        Create a trading intent for the Trading Module.
        Includes confidence score, stop/take profit, and reasoning.
        Position sizing will be calculated by Trading Module based on confidence.
        
        Args:
            decision (Dict): Decision data with parsed fields and raw response
            mode (str): 'new' or 'manage'
            symbol (str): Trading symbol to use in intent
            
        Returns:
            Dict[str, Any]: Trading intent with confidence and trade parameters
        """
        # Generate a unique decision ID
        decision_id = str(uuid.uuid4())
        
        # Create intent with confidence-based approach
        intent = {
            'decision_id': decision_id,
            'user_id': self.user_id,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mode': mode,
            'symbol': symbol,  # Use dynamic symbol from make_decision parameter
            'exchange': 'bitmex',  # TODO: Make this configurable
            
            # Core fields for confidence-based risk management
            'confidence': decision['confidence'],
            'reasoning': decision['reasoning'],
            
            # Include stop/take profit if parsed
            'stop_loss_price': decision.get('stop_loss_price'),
            'take_profit_price': decision.get('take_profit_price'),
            
            # Pass the ENTIRE raw LLM response - Trading Module's LLM will understand it
            'llm_decision': decision['raw_response'],
            
            # Include metadata
            'metadata': decision.get('metadata', {}),
            
            # Use the parsed action from LLM response
            'action': decision.get('action', 'process_llm_decision'),
            
            # Include any additional context
            'decision_mode': mode,
            'trade_id': decision.get('trade_id') if mode == 'manage' else None
        }
        
        # Add ggShot signal validation information if present
        if decision.get('ggshot_signal_data'):
            intent['ggshot_signal_validation'] = True
            intent['signal_data'] = decision['ggshot_signal_data']
            intent['original_signal'] = decision.get('original_signal', 'Signal data not available')
            
            # For ggShot signals, ensure we have a valid action for trading
            # If no action was parsed but confidence >= 0.50, extract from signal direction
            if not intent.get('action') or intent.get('action') == 'no_action':
                signal_direction = decision['ggshot_signal_data'].get('parsed_data', {}).get('ggshot_signal', {}).get('direction', '').lower()
                if signal_direction in ['long', 'short'] and decision['confidence'] >= 0.50:
                    intent['action'] = signal_direction
                    logger.bind(module="decision.engine", user_id=self.user_id).info(
                        f"🎯 ggShot: Set action={signal_direction} from signal direction (confidence={decision['confidence']})"
                    )
            
            # Add full prompt for ggShot backtesting if available
            if decision.get('full_prompt'):
                intent['full_prompt'] = decision['full_prompt']
        
        logger.bind(module="decision.engine").info(
            f"Created intent with confidence={decision['confidence']} for Trading Module risk calculation"
        )
        
        return self._sanitize_for_json(intent)
    
    async def _fire_ggshot_parallel_testing(self, original_signal: str, market_data: Dict, symbol: str, user_id: str):
        """
        Fire-and-forget parallel testing call for ggShot signals.
        
        Args:
            original_signal (str): The original ggShot signal text
            market_data (Dict): Market data already loaded by decision engine
            symbol (str): Trading symbol
            user_id (str): User ID
        """
        try:
            import httpx
            
            # Extract timeframe from signal or use default
            timeframe = "30m"  # Default, could extract from market_data keys if needed
            
            logger.bind(module="decision.engine", user_id=user_id).info(
                f"🔬 Triggering parallel ggShot testing for {symbol} ({len(market_data)} timeframes of data)"
            )
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    "http://localhost:8001/test-ggshot-decision",
                    json={
                        "user_id": user_id,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "original_signal": original_signal,
                        "market_data": market_data
                    }
                )
                
            logger.bind(module="decision.engine", user_id=user_id).info(
                "✅ Parallel ggShot testing triggered successfully"
            )
            
        except Exception as e:
            logger.bind(module="decision.engine", user_id=user_id).warning(
                f"⚠️ ggShot parallel testing failed: {e} (main decision flow unaffected)"
            )
            # Never fail the main decision flow