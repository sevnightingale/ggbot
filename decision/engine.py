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
            required_indicators = ['Aroon', 'Aroon_long', 'Vortex', 'VWAP', 'RSI', 'RSI_4h']
            available_indicators = []
            
            for indicator in required_indicators:
                if indicator == 'RSI_4h':
                    data = get_indicator_data('RSI_4h')
                elif indicator == 'Aroon':
                    data = get_indicator_data('Aroon_1d')  # NEW: String-based indicator
                elif indicator == 'Aroon_long':
                    data = get_indicator_data('Aroon_60_1d')  # NEW: Long-term Aroon
                elif indicator == 'Vortex':
                    data = get_indicator_data('Vortex_1h')  # NEW: String-based indicator
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
        prompt = f"""# ggShot Signal Validation Protocol v3.0

## MISSION
You are validating a signal from the ggShot indicator - a sophisticated TradingView tool that uses AI optimization to identify potential market breakouts and reversals. ggShot analyzes key price levels and range boundaries to provide structured signals with detailed accuracy metrics.

Your task is to evaluate whether this specific ggShot signal is likely to succeed given current market conditions. Use the four-pillar analytical framework to systematically assess signal quality and assign a confidence score.

**IMPORTANT NOTE ON HISTORICAL ACCURACY:** The signal includes historical accuracy percentages. These are provided for context but should be treated as a minor data point. Your analysis must focus on current market conditions, technical indicators, and real-time confluence. Past performance statistics should not significantly influence your confidence score.

If any data point is 'null' or 'N/A' due to a calculation failure, explicitly note the missing data and proceed with analysis based on remaining indicators.

## 1. ORIGINAL GGSHOT SIGNAL
```
{self._original_signal_message}
```

## 2. CURRENT MARKET CONDITIONS
* **Current Price:** ${current_price}
* **Analysis Timeframe:** {native_timeframe}

### ENTRY ZONE CONTEXT
Compare current price with the signal's entry zone for timing context.
* **Good Entry Opportunity:** If price is at favorable end of entry zone (lower for LONG, higher for SHORT), this may provide a slight confidence boost
* **Entry Timing Note:** Entry zone position affects execution quality but doesn't invalidate the signal's directional accuracy

## 3. THE FOUR-PILLAR ANALYTICAL FRAMEWORK
Approach each pillar as a key question that must be answered to assess signal quality. Consider how the indicators interact and what story they tell together.

### --- PILLAR 0: MARKET REGIME ASSESSMENT ---
**Core Question:** "Is the current market environment suitable for the type of breakout signal that ggShot is designed to detect?"

**Available Market Regime Data:**
- **Aroon Short-term (14-period Daily):** {get_indicator_data('Aroon_1d')} - Recent 2-week trending vs ranging behavior
- **Aroon Long-term (60-period Daily):** {get_indicator_data('Aroon_60_1d')} - Macro 2-month trend structure
- **Bollinger Band Width (Daily):** {get_indicator_data('BollingerBandsWidth_1d')} - Indicates volatility regime and squeeze conditions  
- **TRIX (Daily):** {get_indicator_data('TRIX_1d')} - Reveals trend strength and momentum quality

**Key Consideration:** ggShot signals are designed for breakout/momentum scenarios. When Aroon shows ranging behavior (especially short-term), combined with low BBW (compression) or negative TRIX (no momentum), ggShot signals face significantly higher failure rates. Consider both timeframes: immediate ranging (2 weeks) poses the highest risk, while longer-term ranging (2 months) may indicate major consolidation before a significant move.

**Critical Flags to Look For:**
- **isCurrentlyRanging** in short-term Aroon = HIGH RISK for ggShot
- Combination of ranging + low volatility = Dangerous consolidation
- Short-term ranging within long-term trend = Less risky than both timeframes ranging

**Your Analysis:** Based on the multi-timeframe regime data above, what type of market environment are we in? Is price currently compressing or expanding? How does the combination of short-term and long-term market structure affect the likelihood of ggShot signal success?

### --- PILLAR 1: SIGNAL CONFIRMATION ---
**Core Question:** "Does the underlying market data support this ggShot signal's direction and strength?"

**Available Momentum & Volume Data:**
- **Volume Analysis:** {current_volume_data} - Dynamic timeframe-matched volume analysis
- **Vortex Indicator (1h):** {get_indicator_data('Vortex_1h')} - Shows directional momentum strength
- **VWAP (1h):** {get_indicator_data('VWAP_1h')} - Indicates institutional money flow alignment  
- **MFI (1h):** {get_indicator_data('MFI_1h')} - Reveals volume-based momentum patterns

**CRITICAL VOLUME CONTEXT:**
- Volume analysis uses the **signal's native timeframe** ({native_timeframe}) for accurate comparison
- Period dynamically adjusts based on timeframe (20-50 candles) for optimal baseline
- This ensures apples-to-apples comparison (e.g., 4h volume vs 4h average, not 4h vs 1h)
- Lower timeframes use more periods for stability, higher timeframes use fewer to avoid lag

**Volume Interpretation Guidelines (ggShot Founder's Thresholds):**
- **<10% above average**: Weak momentum - breakout lacks conviction
- **10-30% above average**: Moderate momentum - acceptable but watch for failure
- **30-60% above average**: Good momentum - solid breakout support
- **60-100% above average**: Strong momentum - high conviction move
- **>100% above average**: Very strong momentum - often indicates major breakout

**Your Analysis:** Pay special attention to volume as it's one of the most reliable breakout confirmation tools. How does the current volume compare to the 30-period average? Does it support or contradict the ggShot signal? Consider volume alongside momentum indicators for complete picture.

### --- PILLAR 2: BROADER CONTEXT ASSESSMENT ---
**Core Question:** "Is this trade well-positioned across multiple timeframes and near major liquidity zones?"

**Available Multi-Timeframe Data:**
- **RSI 15m:** {get_indicator_data('RSI_15m')} - Fine-grained momentum analysis
- **RSI 30m:** {get_indicator_data('RSI_30m')} - Primary signal timeframe context
- **RSI 1h:** {get_indicator_data('RSI_1h')} - Intermediate timeframe perspective
- **RSI 4h:** {get_indicator_data('RSI_4h')} - Higher timeframe trend context
- **Donchian Channel (200-period, 1h):** {get_indicator_data('DonchianChannel_200_1h')} - Major liquidity zones and breakout context

**Key Considerations:**
- Give slightly more weight to the RSI timeframe closest to the signal timeframe ({native_timeframe}) for most relevant momentum context
- Pay special attention to overheated RSI conditions, as ggShot signals can sometimes trigger late in a move, right before natural retracements occur
- Higher timeframe overbought/oversold conditions can derail otherwise good signals
- Proximity to major support/resistance levels affects profit potential
- Consider how momentum aligns or conflicts across different time horizons

**Your Analysis:** What does the multi-timeframe momentum picture tell us? Are we buying tops or selling bottoms? How much room does this trade have to develop based on major liquidity zones?

### --- PILLAR 3: IMMEDIATE MARKET CONDITIONS ---
**Core Question:** "What do current market conditions tell us about execution timing and environment?"

**Available Market Condition Data:**
- **Bollinger Bands (1h):** {get_indicator_data('BollingerBands_1h')} - Price position relative to statistical bands
- **ATR (1h):** {get_indicator_data('ATR_1h')} - Current volatility levels

**Key Considerations:**
- How does current price position relative to Bollinger Bands affect potential outcomes?
- What does current volatility (ATR) suggest about market conditions?
- Are there any immediate technical factors worth noting?

**Your Analysis:** What do these immediate market conditions suggest about the trading environment? How might they influence signal execution?

## 4. HOLISTIC ANALYSIS & CONFIDENCE SCORING

**Synthesize Your Findings:** Now step back and consider how all four pillars interact. What is the overall story these indicators tell about this ggShot signal's prospects?

**Consider:**
- How do the pillars reinforce or contradict each other?
- What factors support or challenge the signal's premise?
- What does the overall confluence of evidence suggest?

**Confidence Score Guidelines:**
Your confidence score should fall within one of these specific ranges based on the confluence of evidence:

**0.00-0.05:** Signal fundamentally contradicted by all pillars
**0.05-0.10:** Active opposition across multiple critical factors
**0.10-0.15:** Severe misalignment with only minor supporting elements
**0.15-0.20:** Predominantly negative confluence with isolated positives
**0.20-0.25:** Significant structural weaknesses overwhelming few strengths
**0.25-0.30:** Multiple major concerns with limited favorable conditions
**0.30-0.35:** Unfavorable balance with some redeeming technical factors
**0.35-0.40:** Below-average setup with notable headwinds present
**0.40-0.45:** Mixed conditions leaning negative, lacking conviction
**0.45-0.50:** Neutral setup with balanced opposing forces
**0.50-0.55:** Neutral setup with slight positive bias emerging
**0.55-0.60:** Above-average conditions with manageable concerns
**0.60-0.65:** Favorable alignment offset by specific weaknesses
**0.65-0.70:** Good confluence with isolated but notable risks
**0.70-0.75:** Strong multi-pillar support with minor contradictions
**0.75-0.80:** Very strong alignment with minimal concerns
**0.80-0.85:** Exceptional confluence across most key factors
**0.85-0.90:** Near-ideal setup with only trivial weaknesses
**0.90-0.95:** Outstanding alignment across all major pillars
**0.95-1.00:** Perfect or near-perfect technical confluence

**Confidence Score:** Based on your analysis and these guidelines, what specific confidence level (0.00-1.00) best represents this signal's probability of success?

**Important:** Confidence should be assigned based solely on the four pillars — do not inflate scores for 'gut feel' or unexplained bias. Every aspect of your score must be traceable to specific technical evidence from the pillars.

## 5. FINAL OUTPUT

FORMAT YOUR RESPONSE EXACTLY AS:

ACTION: validate
CONFIDENCE: [0.00-1.00]
STOP_LOSS: [Extract from signal]
TAKE_PROFIT: [Extract Target 1 from signal]

REASONING:
- **Entry Timing:** (Assess current price vs entry zone and timing implications)
- **Market Regime:** (Your assessment of market environment suitability for breakouts)
- **Signal Confirmation:** (How momentum, volume, and flow indicators align with signal direction)
- **Multi-Timeframe Context:** (RSI analysis across timeframes, focusing on closest to signal)
- **Risk Factors:** (Any immediate tactical risks or overextension concerns)
- **Overall Assessment:** (Synthesize how all factors combine to justify your confidence score)
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
            if line_upper.startswith('ACTION:'):
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
            elif line_upper.startswith('CONFIDENCE:'):
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
            elif line_upper.startswith('STOP_LOSS:') or line_upper.startswith('STOP LOSS:'):
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
            elif line_upper.startswith('TAKE_PROFIT:') or line_upper.startswith('TAKE PROFIT:'):
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
            elif line_upper.startswith('REASONING:') or capture_reasoning:
                if line_upper.startswith('REASONING:'):
                    capture_reasoning = True
                    # Get any text after "REASONING:" on the same line
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        reasoning_text = parts[1].strip()
                        if reasoning_text:
                            reasoning_lines.append(reasoning_text)
                elif capture_reasoning and line_stripped:
                    # Continue capturing reasoning until we hit another section
                    if any(line_upper.startswith(x) for x in ['ACTION:', 'CONFIDENCE:', 'STOP_LOSS:', 'TAKE_PROFIT:', 'STOP LOSS:', 'TAKE PROFIT:']):
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
                
                # DEBUG: Log the full response
                logger.bind(module="decision.engine", user_id=self.user_id).info(
                    "🤖 DECISION LLM RESPONSE:\n{response}",
                    response=response
                )
                
                # Parse response
                decision = self._parse_llm_response(response, mode='new_trade')
                decision['metadata'] = metadata
                
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
        
        logger.bind(module="decision.engine").info(
            f"Created intent with confidence={decision['confidence']} for Trading Module risk calculation"
        )
        
        return intent