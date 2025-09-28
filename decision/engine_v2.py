"""
Decision Engine V2 - Clean Architecture Implementation

A complete rewrite of the decision engine using domain models, repositories,
and clean separation of concerns. Supports both autonomous trading and signal
validation modes with context-aware position management.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from decimal import Decimal

from core.common.logger import logger
from core.services.config_service import config_service
from core.common.db import get_db_connection, DecimalEncoder
from core.services.llm_key_service import LLMKeyService
from decision.llm_providers import get_llm_provider
from decision.prompts.opportunity_analysis import build_opportunity_analysis_prompt
from decision.prompts.signal_validation import build_signal_validation_prompt
from decision.prompts.position_management import build_position_management_prompt
import uuid
import json


# Custom JSON encoder for database serialization
class DecisionJSONEncoder(DecimalEncoder):
    """Extended JSON encoder that handles Decimal and datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# Custom exceptions for clean error handling
class DecisionError(Exception):
    """Base exception for decision engine errors."""
    pass

class MarketDataError(DecisionError):
    """Exception for market data related errors."""
    pass

class ConfigurationError(DecisionError):
    """Exception for configuration related errors."""
    pass

class LLMError(DecisionError):
    """Exception for LLM API related errors."""
    pass


class DecisionEngineV2:
    """
    Clean decision engine using domain models and template-based prompts.
    
    Key improvements over V1:
    - Uses ConfigRepository instead of raw JSONB queries
    - Domain model-based data access
    - Template-based prompt system with variable injection
    - Mode-aware decision routing (autonomous vs signal validation)
    - Context preservation for position management
    - Direct OpenAI API integration (no custom provider complexity)
    """
    
    def __init__(self, config_id: str, user_id: str = None):
        """Initialize decision engine for a specific configuration."""
        self.config_id = config_id
        self.user_id = user_id
        self.config = None
        self.llm_provider = None  # Will be initialized dynamically based on config

        logger.bind(config_id=config_id).info("DecisionEngineV2 initialized")
    
    async def initialize(self) -> None:
        """Load configuration and validate setup."""
        try:
            self.config = await config_service.get_config(self.config_id, self.user_id)
            if not self.config:
                raise ConfigurationError(f"Configuration {self.config_id} not found")

            # Initialize LLM provider based on config
            await self._initialize_llm_provider()

            # Now using BotConfigV2 which has config_type
            config_type = self.config.config_type
            logger.bind(config_id=self.config_id, mode=config_type).info("Configuration and LLM provider loaded")
        except Exception as e:
            logger.bind(config_id=self.config_id).error(f"Failed to load config: {e}")
            raise ConfigurationError(f"Failed to load config {self.config_id}: {e}")

    async def _initialize_llm_provider(self) -> None:
        """Initialize LLM provider based on configuration."""
        try:
            # Get LLM configuration from llm_config section (V2 format)
            llm_config = self.config.llm_config if hasattr(self.config, 'llm_config') else {}

            if isinstance(llm_config, dict) and llm_config:
                provider_name = llm_config.get('provider', 'default')
                model_name = llm_config.get('model', None)

                # Handle default provider mapping to XAI/Grok
                if provider_name == 'default':
                    provider_name = 'xai'
                    model_name = model_name or 'grok-4-fast-non-reasoning'
                elif not model_name:
                    # Set default models for explicit providers
                    if provider_name == 'xai':
                        model_name = 'grok-4-fast-non-reasoning'
                    elif provider_name == 'deepseek':
                        model_name = 'deepseek-reasoner'
                    elif provider_name == 'openai':
                        model_name = 'gpt-5'
                    elif provider_name == 'anthropic':
                        model_name = 'claude-opus-4-1-20250805'
            else:
                # Fallback to legacy decision config
                decision_config = self.config.decision if hasattr(self.config, 'decision') else {}
                if isinstance(decision_config, dict):
                    provider_name = decision_config.get('llm_provider', 'default')
                    model_name = decision_config.get('llm_model', None)

                    # Handle default provider mapping
                    if provider_name == 'default':
                        provider_name = 'xai'
                        model_name = model_name or 'grok-4-fast-non-reasoning'
                    elif not model_name:
                        model_name = 'grok-4-fast-non-reasoning' if provider_name == 'xai' else 'deepseek-reasoner'
                else:
                    # Handle legacy format where decision might be a string or other type
                    provider_name = 'xai'  # New default is XAI/Grok
                    model_name = 'grok-4-fast-non-reasoning'

            # Get API key with user/platform priority
            api_key = await LLMKeyService.get_api_key(self.user_id, provider_name)

            # Create provider instance - resolve "default" model to None for proper default handling
            resolved_model = None if model_name == "default" else model_name
            self.llm_provider = get_llm_provider(
                provider_name=provider_name,
                api_key=api_key,
                model=resolved_model  # Uses provider default if None
            )

            logger.bind(
                config_id=self.config_id,
                user_id=self.user_id,
                provider=provider_name,
                model=model_name or "default"
            ).info("LLM provider initialized successfully")

        except Exception as e:
            logger.bind(config_id=self.config_id, user_id=self.user_id).error(f"Failed to initialize LLM provider: {e}")
            raise ConfigurationError(f"Failed to initialize LLM provider: {e}")
    
    async def make_decision(self, symbol: Optional[str] = None, 
                          signal_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main entry point for decision making.
        
        Routes to appropriate decision type based on config_type and current state.
        
        Args:
            symbol: Trading symbol (required for signal validation, optional for autonomous)
            signal_data: External signal data (for signal validation mode)
            
        Returns:
            Decision intent ready for trading module
        """
        if not self.config:
            await self.initialize()
        
        try:
            # Route based on config type and signal data presence
            config_type = self.config.config_type

            logger.bind(config_id=self.config_id).info(
                f"🔍 DECISION DEBUG: config_type='{config_type}', signal_data present={signal_data is not None}, signal_data type={type(signal_data)}"
            )

            if config_type == "signal_validation" and signal_data:
                # Signal validation mode: Always evaluate signals independently
                # Bypasses position management to allow multiple concurrent positions
                logger.bind(config_id=self.config_id, symbol=symbol).info(
                    "🔍 DECISION DEBUG: Signal validation mode: Evaluating signal independently (bypassing position management)"
                )
                return await self._handle_signal_validation(symbol, signal_data)
            else:
                # Autonomous trading mode: Check for existing positions first
                logger.bind(config_id=self.config_id, symbol=symbol).info(
                    f"🔍 DECISION DEBUG: Autonomous trading mode: Checking for existing positions (config_type={config_type}, signal_data={signal_data is not None})"
                )
                return await self._handle_autonomous_trading(symbol)
                
        except (DecisionError, MarketDataError, ConfigurationError, LLMError):
            # Re-raise domain-specific errors (they're already logged)
            raise
        except Exception as e:
            logger.bind(config_id=self.config_id).error(f"Unexpected decision error: {e}")
            raise DecisionError(f"Decision making failed: {e}")
    
    async def _handle_signal_validation(self, symbol: str, signal_data: Dict) -> Dict[str, Any]:
        """
        Handle signal validation mode - validate external signal using current market data.
        
        Process:
        1. Get fresh market data for signal's symbol
        2. Build signal validation prompt (4-pillar ggShot framework)
        3. Call GPT-5 for validation decision
        4. Create signal validation decision record
        5. Return trading intent
        """
        # Get fresh market data for signal's symbol
        market_data = await self._get_fresh_market_data(symbol)
        if not market_data:
            return self._create_error_intent(f"No market data available for signal {symbol}")
        
        # Get current price
        current_price = await self._get_current_price(symbol)
        
        # Get volume confirmation analysis
        volume_analysis = await self._get_volume_confirmation(symbol, signal_data.get('timeframe', '1h'))
        
        # Build signal validation prompt
        prompt = await self._build_signal_validation_prompt(
            symbol, signal_data, market_data, current_price, volume_analysis
        )
        
        # Call LLM for validation
        llm_response = await self._call_llm(prompt)
        
        # Parse response
        decision_data = self._parse_llm_response(llm_response)
        
        # Save signal validation decision to database
        decision_id = await self._save_signal_decision_to_db(
            symbol, decision_data, signal_data, market_data, 
            current_price, prompt, llm_response
        )
        
        # Return signal validation intent
        return self._create_signal_validation_intent(
            decision_id, symbol, decision_data, signal_data
        )
    
    async def _handle_autonomous_trading(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle autonomous trading mode - opportunity analysis or position management.
        
        Process:
        1. Check for active positions
        2a. If positions exist: Position management with context
        2b. If no positions: Opportunity analysis
        """
        # Use symbol from config if not provided
        trading_symbol = symbol or self.config.selected_pair
        if not trading_symbol:
            return self._create_error_intent("No trading symbol specified")
        
        # Check for active position to determine routing
        active_position = await self._get_active_position(trading_symbol, self.config_id)
        
        if active_position:
            # Route to position management
            logger.bind(config_id=self.config_id, user_id=self.user_id).info(
                f"Routing to position management for existing {active_position['side']} position in {trading_symbol}"
            )
            return await self._handle_position_management(trading_symbol, active_position)
        else:
            # Route to opportunity analysis
            logger.bind(config_id=self.config_id, user_id=self.user_id).info(
                f"No active position found, routing to opportunity analysis for {trading_symbol}"
            )
            return await self._handle_opportunity_analysis(trading_symbol)
    
    async def _handle_opportunity_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze market for new trading opportunities.
        
        Process:
        1. Get fresh market data
        2. Use opportunity analysis prompt template
        3. Call GPT-5 for trading decision
        4. Create opportunity analysis strategy run
        5. Return trading intent
        """
        # Step 1: Get fresh market data
        market_data = await self._get_fresh_market_data(symbol)
        if not market_data:
            return self._create_error_intent(f"No fresh market data available for {symbol}")
        
        # Step 2: Get current price
        current_price = await self._get_current_price(symbol)
        
        # Step 2.5: Get volume confirmation analysis
        volume_analysis = await self._get_volume_confirmation(symbol, '1h')  # Default timeframe for autonomous
        
        # Step 3: Build prompt from template
        prompt = await self._build_opportunity_analysis_prompt(symbol, market_data, current_price, volume_analysis)
        
        # Step 4: Call LLM
        llm_response = await self._call_llm(prompt)
        
        # Step 5: Parse response
        decision_data = self._parse_llm_response(llm_response)
        
        # Step 6: Save decision to database
        decision_id = await self._save_decision_to_db(symbol, decision_data, market_data, current_price, prompt, llm_response)
        
        # Step 7: Return intent
        return self._create_trading_intent_simple(decision_id, symbol, decision_data)
    
    # TODO: Re-implement position management when domain objects are available
    # async def _handle_position_management(...)
    
    async def _get_fresh_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get fresh market data for this config from the database.
        
        Retrieves data for all timeframes and consolidates into timeframe-organized structure.
        NOTE: Orchestrator is responsible for ensuring fresh data exists.
        DecisionEngine just retrieves and organizes it from database.
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get all market data for this config and symbol across all timeframes
                    cur.execute("""
                        SELECT timeframe, data_points, raw_data, updated_at 
                        FROM market_data 
                        WHERE config_id = %s AND symbol = %s 
                        ORDER BY timeframe ASC, updated_at DESC
                    """, (self.config_id, symbol))
                    
                    rows = cur.fetchall()
                    if not rows:
                        logger.bind(config_id=self.config_id, symbol=symbol).error(
                            "No market data available - orchestrator should have ensured fresh data"
                        )
                        raise MarketDataError(
                            f"No market data available for {symbol}. "
                            f"Orchestrator should have triggered extraction and waited for completion."
                        )
                    
                    # Group data by timeframe (taking most recent for each timeframe)
                    timeframe_data = {}
                    latest_price = None
                    oldest_update = None
                    
                    for timeframe, data_points, raw_data, updated_at in rows:
                        # Only take the first (most recent) entry for each timeframe
                        if timeframe not in timeframe_data:
                            timeframe_data[timeframe] = {
                                "indicators": data_points.get("indicators", {}) if data_points else {},
                                "raw_summary": raw_data.get("metadata", {}) if raw_data else {},
                                "updated_at": updated_at
                            }
                            
                            # Extract latest price from first timeframe processed
                            if latest_price is None and raw_data and raw_data.get("metadata"):
                                latest_price = raw_data["metadata"].get("latest_price")
                            
                            # Track age
                            if oldest_update is None or updated_at < oldest_update:
                                oldest_update = updated_at
                    
                    # Calculate data age
                    age_seconds = (datetime.now(timezone.utc) - oldest_update).total_seconds() if oldest_update else 0
                    
                    # Prepare consolidated multi-timeframe structure
                    consolidated_data = {
                        "symbol": symbol,
                        "timeframes": timeframe_data,
                        "latest_price": latest_price or 0.0,
                        "data_age_seconds": age_seconds,
                        "timeframes_available": list(timeframe_data.keys())
                    }
                    
                    logger.bind(
                        config_id=self.config_id, 
                        symbol=symbol,
                        timeframes_count=len(timeframe_data),
                        age_seconds=age_seconds
                    ).info("Retrieved multi-timeframe market data for decision")
                    
                    return consolidated_data
                    
        except MarketDataError:
            raise  # Re-raise domain errors
        except Exception as e:
            logger.bind(config_id=self.config_id, symbol=symbol).error(f"Failed to get market data: {e}")
            raise MarketDataError(f"Failed to retrieve market data: {e}")
    
    async def _get_current_price(self, symbol: str) -> Decimal:
        """
        Get current market price using multi-exchange fallback for maximum reliability.
        """
        try:
            from trading.paper.market_data import MarketDataAdapter

            adapter = MarketDataAdapter()
            market_price = await adapter.get_current_price_with_fallback(symbol)

            # Use mid price (average of bid/ask)
            price = Decimal(str(market_price.mid))

            logger.bind(
                config_id=self.config_id,
                symbol=symbol,
                price=float(price),
                bid=market_price.bid,
                ask=market_price.ask
            ).debug("Retrieved current price with multi-exchange fallback")

            return price

        except Exception as e:
            logger.bind(config_id=self.config_id, symbol=symbol).error(f"Failed to get current price from all exchanges: {e}")
            # No more dangerous mock fallback - let the error propagate for proper handling
            raise MarketDataError(f"Unable to get current price for {symbol} from any exchange: {e}")
    
    async def _build_signal_validation_prompt(
        self, 
        symbol: str,
        signal_data: Dict,
        market_data: Dict[str, Any],
        current_price: Decimal,
        volume_analysis: str
    ) -> str:
        """Build signal validation prompt using template."""
        
        signal_context = self._format_signal_for_llm(signal_data)
        market_context = self._format_market_data_for_llm(market_data)
        # NO FALLBACK - fail explicitly if config is missing required data
        user_prompt = self.config.decision.get('user_prompt') if isinstance(self.config.decision, dict) else getattr(self.config.decision, 'user_prompt', None)
        if not user_prompt:
            raise ValueError(f"Missing required user_prompt in decision config for {self.config_id}. Fix the config data.")
        user_strategy = user_prompt
        
        # Extract signal direction for prompt
        signal_direction = signal_data.get('direction', 'UNKNOWN')

        return build_signal_validation_prompt(
            symbol=symbol,
            current_price=f"${current_price:,.2f}",
            market_data=market_context,
            volume_analysis=volume_analysis,
            signal_context=signal_context,
            user_strategy=user_strategy,
            signal_direction=signal_direction
        )
    
    async def _build_opportunity_analysis_prompt(self, symbol: str,
                                                market_data: Dict[str, Any],
                                                current_price: Decimal,
                                                volume_analysis: str) -> str:
        """Build opportunity analysis prompt from template."""
        
        market_context = self._format_market_data_for_llm(market_data)
        # NO FALLBACK - fail explicitly if config is missing required data
        user_prompt = self.config.decision.get('user_prompt') if isinstance(self.config.decision, dict) else getattr(self.config.decision, 'user_prompt', None)
        if not user_prompt:
            raise ValueError(f"Missing required user_prompt in decision config for {self.config_id}. Fix the config data.")
        user_strategy = user_prompt
        
        return build_opportunity_analysis_prompt(
            symbol=symbol,
            current_price=f"${current_price:,.2f}",
            market_data=market_context,
            volume_analysis=volume_analysis,
            user_strategy=user_strategy
        )
    
    async def _handle_position_management(self, symbol: str, position_data: Dict) -> Dict[str, Any]:
        """
        Handle position management for existing position.
        
        Process:
        1. Get fresh market data
        2. Get current price
        3. Get volume analysis
        4. Build position management prompt with trade context
        5. Call GPT-5 for position decision
        6. Create position management decision record
        7. Return position management intent
        """
        # Step 1: Get fresh market data
        market_data = await self._get_fresh_market_data(symbol)
        if not market_data:
            return self._create_error_intent(f"No fresh market data available for {symbol}")
        
        # Step 2: Get current price
        current_price = await self._get_current_price(symbol)
        
        # Step 2.5: Get volume confirmation analysis
        volume_analysis = await self._get_volume_confirmation(symbol, '1h')  # Default timeframe for position management
        
        # Step 3: Build position management prompt with context
        prompt = await self._build_position_management_prompt(
            symbol, position_data, market_data, current_price, volume_analysis
        )
        
        # Step 4: Call LLM
        llm_response = await self._call_llm(prompt)
        
        # Step 5: Parse response
        decision_data = self._parse_llm_response(llm_response)
        
        # Step 6: Save decision to database (with parent decision link)
        decision_id = await self._save_position_decision_to_db(
            symbol, decision_data, position_data, market_data, 
            current_price, prompt, llm_response
        )
        
        # Step 7: Return position management intent
        return self._create_position_management_intent(
            decision_id, symbol, decision_data, position_data
        )

    async def _build_position_management_prompt(
        self, 
        symbol: str,
        position_data: Dict,
        market_data: Dict[str, Any],
        current_price: Decimal,
        volume_analysis: str
    ) -> str:
        """Build position management prompt from template."""
        
        # Format position context for LLM
        position_context = self._format_position_data_for_llm(position_data, current_price)
        market_context = self._format_market_data_for_llm(market_data)
        # NO FALLBACK - fail explicitly if config is missing required data
        user_prompt = self.config.decision.get('user_prompt') if isinstance(self.config.decision, dict) else getattr(self.config.decision, 'user_prompt', None)
        if not user_prompt:
            raise ValueError(f"Missing required user_prompt in decision config for {self.config_id}. Fix the config data.")
        user_strategy = user_prompt
        
        return build_position_management_prompt(
            symbol=symbol,
            current_price=f"${current_price:,.2f}",
            market_data=market_context,
            volume_analysis=volume_analysis,
            position_data=position_context,
            user_strategy=user_strategy
        )
    
    def _format_position_data_for_llm(self, position_data: Dict, current_price: Decimal) -> str:
        """Format position data for LLM consumption with performance context."""
        
        # Calculate performance metrics
        entry_price = position_data['entry_price']
        unrealized_pnl = position_data['unrealized_pnl']
        size_usd = position_data['size_usd']
        side = position_data['side']
        
        # Calculate percentage gain/loss
        if side == 'buy':
            pnl_percentage = ((float(current_price) - entry_price) / entry_price) * 100
        else:  # sell/short
            pnl_percentage = ((entry_price - float(current_price)) / entry_price) * 100
        
        # Calculate position duration
        from datetime import datetime, timezone
        opened_at = position_data['opened_at']
        if isinstance(opened_at, str):
            opened_at = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
        
        duration = datetime.now(timezone.utc) - opened_at
        hours_held = duration.total_seconds() / 3600
        
        # Format performance status
        if pnl_percentage > 5:
            performance_status = "Strong Winner"
        elif pnl_percentage > 1:
            performance_status = "Winning"
        elif pnl_percentage > -1:
            performance_status = "Break-even"
        elif pnl_percentage > -5:
            performance_status = "Losing"
        else:
            performance_status = "Strong Loser"
        
        # Format the position summary
        stop_loss_text = f"${position_data['stop_loss']:,.2f}" if position_data['stop_loss'] else 'None set'
        take_profit_text = f"${position_data['take_profit']:,.2f}" if position_data['take_profit'] else 'None set'
        
        position_summary = f"""
CURRENT POSITION DETAILS:
Position Type: {side.upper()} {position_data['symbol']}
Entry Price: ${entry_price:,.2f}
Current Price: ${current_price:,.2f}
Position Size: ${size_usd:,.2f}
Unrealized P&L: ${unrealized_pnl:+.2f} ({pnl_percentage:+.1f}%)
Performance: {performance_status}
Duration: {hours_held:.1f} hours

ORIGINAL TRADE CONTEXT:
Entry Reasoning: {position_data['entry_reasoning']}
Entry Confidence: {position_data['entry_confidence']:.1%}
Stop Loss: {stop_loss_text}
Take Profit: {take_profit_text}
"""
        
        return position_summary
    
    async def _save_decision_to_db(self, symbol: str, decision_data: Dict[str, Any], 
                                   market_data: Dict[str, Any], current_price: Decimal,
                                   prompt: str, llm_response: str) -> str:
        """Save decision to the decisions table."""
        decision_id = str(uuid.uuid4())
        
        # Map decision actions to schema-compliant actions
        raw_action = decision_data.get('action', 'no_action')
        if raw_action in ['long', 'short', 'enter']:
            schema_action = 'enter'
        elif raw_action in ['exit', 'close']:
            schema_action = 'exit'
        else:  # wait, no_action, hold, etc.
            schema_action = 'wait'
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    decision_data_json = {**decision_data, 'raw_action': raw_action}  # Preserve original action

                    cur.execute("""
                        INSERT INTO decisions (
                            decision_id, user_id, config_id, symbol, action, status,
                            confidence, reasoning, prompt, decision_data, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        decision_id,
                        self.user_id,
                        self.config_id,
                        symbol,
                        schema_action,  # Use schema-compliant action
                        'completed',
                        decision_data.get('confidence', 0.5),
                        decision_data.get('reasoning', llm_response),
                        prompt,
                        json.dumps(decision_data_json, cls=DecisionJSONEncoder),
                        datetime.now(timezone.utc).isoformat()
                    ))
                    conn.commit()

            logger.bind(
                config_id=self.config_id,
                decision_id=decision_id,
                symbol=symbol,
                action=decision_data.get('action')
            ).info("Decision saved to database")

            return decision_id
                    
        except Exception as e:
            logger.bind(config_id=self.config_id, symbol=symbol).error(f"Failed to save decision: {e}")
            raise DecisionError(f"Failed to save decision to database: {e}")
    
    def _create_trading_intent_simple(self, decision_id: str, symbol: str, 
                                    decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create simplified trading intent."""
        return {
            'decision_id': decision_id,
            'user_id': self.user_id,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'decision_type': 'opportunity_analysis',
            'symbol': symbol,
            
            # Core decision data
            'action': decision_data.get('action', 'no_action'),
            'confidence': decision_data.get('confidence', 0.5),
            'reasoning': decision_data.get('reasoning', 'No reasoning provided'),
            
            # Trade parameters
            'stop_loss_price': decision_data.get('stop_loss_price'),
            'take_profit_price': decision_data.get('take_profit_price'),
        }
    
    def _format_market_data_for_llm(self, market_data: Dict[str, Any]) -> str:
        """Format multi-timeframe market data for LLM consumption."""
        if not market_data:
            return "No market data available"
        
        # Handle new multi-timeframe structure
        if 'timeframes' in market_data:
            return self._format_multi_timeframe_data(market_data)
        
        # Fallback to legacy single-timeframe formatting
        return self._format_legacy_market_data(market_data)
    
    def _format_multi_timeframe_data(self, market_data: Dict[str, Any]) -> str:
        """Format multi-timeframe market data with rich context."""
        formatted = []
        
        # Header with symbol and current price
        symbol = market_data.get('symbol', 'Unknown')
        latest_price = market_data.get('latest_price', 0.0)
        timeframes = market_data.get('timeframes', {})
        
        formatted.append(f"MARKET ANALYSIS FOR {symbol}")
        formatted.append(f"Current Price: ${latest_price:,.2f}")
        formatted.append(f"Timeframes Available: {', '.join(market_data.get('timeframes_available', []))}")
        formatted.append("")
        
        # Format each timeframe's data
        for timeframe, tf_data in timeframes.items():
            formatted.append(f"=== {timeframe.upper()} TIMEFRAME ===")
            
            indicators = tf_data.get("indicators", {})
            if indicators:
                for indicator_name, indicator_data in indicators.items():
                    formatted.append(f"  {indicator_name}:")
                    
                    # Format rich indicator data from V2 preprocessors
                    if isinstance(indicator_data, dict):
                        # Current values (always show)
                        if "current" in indicator_data:
                            formatted.append(f"    Current: {indicator_data['current']}")
                        
                        # Summary (most important - human readable)
                        if "summary" in indicator_data:
                            formatted.append(f"    Summary: {indicator_data['summary']}")
                        
                        # Context (trend, momentum, volatility)
                        if "context" in indicator_data:
                            context = indicator_data["context"]
                            if isinstance(context, dict):
                                for key, value in context.items():
                                    if isinstance(value, dict):
                                        # Handle nested context like trend: {direction: rising, strength: 0.68}
                                        nested_str = ", ".join(f"{k}: {v}" for k, v in value.items())
                                        formatted.append(f"    {key.title()}: {nested_str}")
                                    else:
                                        formatted.append(f"    {key.title()}: {value}")
                        
                        # Levels (zones, thresholds, crossovers)
                        if "levels" in indicator_data:
                            levels = indicator_data["levels"]
                            if isinstance(levels, dict):
                                for key, value in levels.items():
                                    if key == "current_zone":
                                        formatted.append(f"    Zone: {value}")
                                    elif isinstance(value, dict) and "current_zone" in value:
                                        formatted.append(f"    Zone: {value['current_zone']}")
                                    elif key not in ["key_levels", "recent_crossovers"]:  # Skip noisy arrays
                                        formatted.append(f"    {key.replace('_', ' ').title()}: {value}")
                        
                        # Patterns (detected formations)
                        if "patterns" in indicator_data:
                            patterns = indicator_data["patterns"]
                            if isinstance(patterns, dict) and patterns:
                                pattern_names = [k for k, v in patterns.items() if v]
                                if pattern_names:
                                    formatted.append(f"    Patterns: {', '.join(pattern_names)}")
                        
                        # Evidence (quality metrics)
                        if "evidence" in indicator_data:
                            evidence = indicator_data["evidence"]
                            if isinstance(evidence, dict):
                                evidence_parts = []
                                for key, value in evidence.items():
                                    if isinstance(value, (int, float)):
                                        evidence_parts.append(f"{key}: {value:.2f}")
                                    else:
                                        evidence_parts.append(f"{key}: {value}")
                                if evidence_parts:
                                    formatted.append(f"    Quality: {', '.join(evidence_parts)}")
                        
                        # Legacy support for old format indicators
                        if "trend" in indicator_data:
                            trend = indicator_data["trend"]
                            if isinstance(trend, dict):
                                direction = trend.get("direction", "unknown")
                                formatted.append(f"    Legacy Trend: {direction}")
                            else:
                                formatted.append(f"    Legacy Trend: {trend}")
                        
                        if "zones" in indicator_data:
                            zones = indicator_data["zones"]
                            if isinstance(zones, dict):
                                current_zone = zones.get("current", "unknown")
                                formatted.append(f"    Legacy Zone: {current_zone}")
                    else:
                        # Simple numeric value
                        formatted.append(f"    Value: {indicator_data}")
                    
                    formatted.append("")
            else:
                formatted.append("  No indicators available for this timeframe")
                formatted.append("")
        
        # Add data freshness info
        age_seconds = market_data.get('data_age_seconds', 0)
        if age_seconds < 60:
            age_str = f"{int(age_seconds)} seconds"
        elif age_seconds < 3600:
            age_str = f"{int(age_seconds/60)} minutes"
        else:
            age_str = f"{int(age_seconds/3600)} hours"
            
        formatted.append(f"Data Age: {age_str}")
        
        return "\n".join(formatted)
    
    def _format_legacy_market_data(self, market_data: Dict[str, Any]) -> str:
        """Format legacy single-timeframe market data."""
        formatted = "Market Data:\n"
        
        # Extract key information from the legacy market data
        if 'symbol' in market_data:
            formatted += f"Symbol: {market_data['symbol']}\n"
        if 'timeframe' in market_data:
            formatted += f"Timeframe: {market_data['timeframe']}\n"
        if 'indicators' in market_data and market_data['indicators']:
            formatted += "Technical Indicators:\n"
            for indicator, value in market_data['indicators'].items():
                formatted += f"  - {indicator}: {value}\n"
        if 'ohlcv_summary' in market_data:
            summary = market_data['ohlcv_summary']
            formatted += f"Latest Price: ${summary.get('latest_price', 'N/A'):,.2f}\n"
            formatted += f"24h Price Change: {summary.get('price_change_24h', 'N/A'):.2f}%\n"
        
        return formatted
    
    def _format_signal_for_llm(self, signal_data: Dict) -> str:
        """Format signal data for LLM consumption."""
        # Get the raw ggShot signal (this is the most important part!)
        raw_signal = signal_data.get('raw_message', 'No original message available')

        return f"""
## GGSHOT SIGNAL (RAW)
{raw_signal}

## PARSED SIGNAL DATA
- Source: {signal_data.get('source', 'Unknown')}
- Symbol: {signal_data.get('symbol', 'Unknown')}
- Direction: {signal_data.get('direction', 'Unknown')}
- Timeframe: {signal_data.get('timeframe', 'Unknown')}
- Entry Zone: {signal_data.get('entry_zone', 'N/A')}
- Stop Loss: {signal_data.get('stop_loss', 'N/A')}
- Take Profit: {signal_data.get('take_profit', 'N/A')}
"""
    
    async def _call_llm(self, prompt: str, custom_mode: Optional[str] = None) -> str:
        """Call LLM API using configured provider."""
        if not self.llm_provider:
            await self.initialize()  # Initialize if not already done

        try:
            # Log the prompt being sent to the LLM
            logger.bind(config_id=self.config_id, user_id=self.user_id).info("🤖 Prompt sent to Decision LLM")
            logger.bind(config_id=self.config_id, user_id=self.user_id).info(f"PROMPT:\n{prompt}")

            # Call the configured LLM provider
            response_text, metadata = await self.llm_provider.generate_response(
                prompt=prompt,
                temperature=0.7,  # Could be configurable in future
                custom_mode=custom_mode
            )

            # Log the response from the LLM
            logger.bind(config_id=self.config_id, user_id=self.user_id).info("🤖 Response received from Decision LLM")
            logger.bind(config_id=self.config_id, user_id=self.user_id).info(f"LLM RESPONSE:\n{response_text}")

            # Log metadata for debugging
            logger.bind(
                config_id=self.config_id,
                user_id=self.user_id,
                model=metadata.get('model'),
                latency=metadata.get('latency'),
                tokens=metadata.get('usage', {}).get('total_tokens', 'unknown')
            ).info("LLM call completed with metadata")

            return response_text

        except Exception as e:
            logger.bind(config_id=self.config_id, user_id=self.user_id).error(f"LLM API call failed: {e}")
            raise LLMError(f"LLM API call failed: {e}")
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured decision data with standardized format."""
        # Initialize with defaults
        parsed = {
            'action': 'wait',  # Default to wait instead of no_action
            'confidence': 0.5,
            'reasoning': '',
            'stop_loss_price': None,
            'take_profit_price': None
        }
        
        lines = response.split('\n')
        reasoning_lines = []
        in_reasoning_section = False
        
        for line in lines:
            line_upper = line.strip().upper()
            line_orig = line.strip()
            
            # Parse ACTION (required)
            if 'ACTION:' in line_upper:
                action = line_upper.split('ACTION:')[1].strip().lower()
                # Standardized actions: long, short, hold, wait
                # Handle synonyms: buy->long, sell->short, no_action->wait
                if action in ['long', 'buy']:
                    parsed['action'] = 'long'
                elif action in ['short', 'sell']:
                    parsed['action'] = 'short'
                elif action in ['hold', 'wait', 'no_action']:
                    parsed['action'] = 'wait'
                elif action in ['close', 'exit']:
                    parsed['action'] = 'close'
                else:
                    # Keep original if it's a valid action, otherwise default to wait
                    if action in ['long', 'short', 'hold', 'wait', 'close']:
                        parsed['action'] = action
            
            # Parse CONFIDENCE (required)
            elif 'CONFIDENCE:' in line_upper:
                try:
                    conf_str = line_upper.split('CONFIDENCE:')[1].strip()
                    import re
                    numbers = re.findall(r'\d*\.?\d+', conf_str)
                    if numbers:
                        conf = float(numbers[0])
                        parsed['confidence'] = min(1.0, max(0.0, conf if conf <= 1.0 else conf/100))
                except:
                    pass
            
            # Parse REASONING (required) - can be multi-line
            elif 'REASONING:' in line_upper:
                in_reasoning_section = True
                reasoning_content = line_orig.split('REASONING:')[1].strip()
                if reasoning_content:
                    reasoning_lines.append(reasoning_content)
            
            # Parse STOP_LOSS (optional)
            elif 'STOP_LOSS:' in line_upper or 'STOP LOSS:' in line_upper:
                try:
                    sl_str = line_upper.split('LOSS:')[1].strip()
                    # Handle "null" or "none" cases
                    if sl_str.lower() in ['null', 'none', 'n/a']:
                        parsed['stop_loss_price'] = None
                    else:
                        import re
                        numbers = re.findall(r'\d+\.?\d*', sl_str)
                        if numbers:
                            parsed['stop_loss_price'] = float(numbers[0])
                except:
                    pass
            
            # Parse TAKE_PROFIT (optional)
            elif 'TAKE_PROFIT:' in line_upper or 'TAKE PROFIT:' in line_upper:
                try:
                    tp_str = line_upper.split('PROFIT:')[1].strip()
                    # Handle "null" or "none" cases
                    if tp_str.lower() in ['null', 'none', 'n/a']:
                        parsed['take_profit_price'] = None
                    else:
                        import re
                        numbers = re.findall(r'\d+\.?\d*', tp_str)
                        if numbers:
                            parsed['take_profit_price'] = float(numbers[0])
                except:
                    pass
            
            # Continue collecting reasoning lines
            elif in_reasoning_section and line_orig.strip():
                # Stop if we hit another header
                if any(header in line_upper for header in ['ACTION:', 'CONFIDENCE:', 'STOP_LOSS:', 'TAKE_PROFIT:']):
                    in_reasoning_section = False
                else:
                    reasoning_lines.append(line_orig)
        
        # Compile reasoning
        if reasoning_lines:
            parsed['reasoning'] = ' '.join(reasoning_lines).strip()
        else:
            # Fallback to full response if no reasoning section found
            parsed['reasoning'] = response.strip()
        
        return parsed
    
    async def _save_signal_decision_to_db(
        self, 
        symbol: str, 
        decision_data: Dict[str, Any],
        signal_data: Dict,
        market_data: Dict[str, Any], 
        current_price: Decimal,
        prompt: str, 
        llm_response: str
    ) -> str:
        """Save signal validation decision to the decisions table."""
        decision_id = str(uuid.uuid4())
        
        # Map signal validation actions to schema-compliant actions
        raw_action = decision_data.get('action', 'wait')
        if raw_action in ['long', 'short']:
            schema_action = 'enter'
        elif raw_action in ['close', 'exit']:
            schema_action = 'exit'
        else:  # wait, hold, etc.
            schema_action = 'wait'
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    decision_data_json = {
                        'signal_source': signal_data.get('source'),
                        'signal_data': signal_data,
                        'validation_framework': '4-pillar',
                        'current_price': float(current_price),
                        'raw_action': raw_action  # Preserve original action
                    }

                    cur.execute("""
                        INSERT INTO decisions (
                            decision_id, user_id, config_id, symbol, action, status,
                            confidence, reasoning, prompt, decision_data, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        decision_id,
                        self.user_id,
                        self.config_id,
                        symbol,
                        schema_action,  # Use schema-compliant action
                        'completed',
                        decision_data.get('confidence', 0.5),
                        decision_data.get('reasoning', llm_response),
                        prompt,
                        json.dumps(decision_data_json, cls=DecisionJSONEncoder),
                        datetime.now(timezone.utc).isoformat()
                    ))
                    conn.commit()

            logger.bind(
                config_id=self.config_id,
                decision_id=decision_id,
                symbol=symbol,
                action=decision_data.get('action')
            ).info("Signal validation decision saved to database")

            return decision_id
                    
        except Exception as e:
            logger.bind(config_id=self.config_id, symbol=symbol).error(f"Failed to save signal decision: {e}")
            raise DecisionError(f"Failed to save signal decision to database: {e}")
    
    def _create_signal_validation_intent(
        self, 
        decision_id: str, 
        symbol: str,
        decision_data: Dict[str, Any], 
        signal_data: Dict
    ) -> Dict[str, Any]:
        """Create signal validation trading intent."""
        return {
            'decision_id': decision_id,
            'user_id': self.user_id,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'decision_type': 'signal_validation',
            'symbol': symbol,
            'signal_source': signal_data.get('source'),
            
            # Core decision data
            'action': decision_data.get('action', 'no_action'),
            'confidence': decision_data.get('confidence', 0.5),
            'reasoning': decision_data.get('reasoning', 'No reasoning provided'),
            
            # Trade parameters (use signal defaults if not overridden by decision)
            'stop_loss_price': decision_data.get('stop_loss_price') or signal_data.get('stop_loss'),
            'take_profit_price': decision_data.get('take_profit_price') or signal_data.get('take_profit'),
            
            # Signal context
            'original_signal': signal_data.get('raw_message', ''),
            'signal_confidence': signal_data.get('confidence', 0.0),
            'signal_timeframe': signal_data.get('timeframe'),
        }
    
    def _get_dynamic_volume_period(self, timeframe: str) -> int:
        """
        Get dynamic period for volume average calculation based on timeframe.
        
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
    
    async def _get_active_position(self, symbol: str, config_id: str) -> Optional[Dict]:
        """
        Check for active position for this symbol and config.
        
        Args:
            symbol: Trading symbol to check
            config_id: Configuration ID for position isolation
            
        Returns:
            Position data dict if active position exists, None otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Query for open position with entry decision context
                    cur.execute("""
                        SELECT 
                            pt.trade_id,
                            pt.symbol,
                            pt.side,
                            pt.entry_price,
                            pt.current_price,
                            pt.size_usd,
                            pt.unrealized_pnl,
                            pt.opened_at,
                            pt.stop_loss,
                            pt.take_profit,
                            pt.confidence_score,
                            d.reasoning as entry_reasoning,
                            d.confidence as entry_confidence,
                            d.decision_data as entry_decision_data
                        FROM paper_trades pt
                        LEFT JOIN decisions d ON pt.decision_id = d.decision_id
                        WHERE pt.config_id = %s 
                          AND pt.symbol = %s 
                          AND pt.status = 'open'
                        ORDER BY pt.opened_at DESC
                        LIMIT 1
                    """, (config_id, symbol))
                    
                    row = cur.fetchone()
                    if not row:
                        return None
                    
                    # Convert to dict with position details
                    position_data = {
                        'trade_id': row[0],
                        'symbol': row[1],
                        'side': row[2],  # 'buy' or 'sell'
                        'entry_price': float(row[3]),
                        'current_price': float(row[4]) if row[4] else float(row[3]),
                        'size_usd': float(row[5]),
                        'unrealized_pnl': float(row[6]) if row[6] else 0.0,
                        'opened_at': row[7],
                        'stop_loss': float(row[8]) if row[8] else None,
                        'take_profit': float(row[9]) if row[9] else None,
                        'confidence_score': float(row[10]) if row[10] else 0.0,
                        'entry_reasoning': row[11] if row[11] else 'No reasoning available',
                        'entry_confidence': float(row[12]) if row[12] else 0.0,
                        'entry_decision_data': row[13] if row[13] else {}
                    }
                    
                    logger.bind(config_id=self.config_id, user_id=self.user_id).info(
                        f"Found active position for {symbol}: {position_data['side']} ${position_data['size_usd']:.2f}, P&L: ${position_data['unrealized_pnl']:.2f}"
                    )
                    
                    return position_data
                    
        except Exception as e:
            logger.bind(config_id=self.config_id, user_id=self.user_id).warning(
                f"Failed to check for active position {symbol}: {e}"
            )
            return None

    async def _get_volume_confirmation(self, symbol: str, timeframe: str = '1h') -> str:
        """
        Get volume confirmation analysis using existing market data.
        Based on ggShot founder's guidance on volume thresholds.
        
        Args:
            symbol: Trading symbol to analyze
            timeframe: Timeframe for volume analysis (matches signal timeframe)
            
        Returns:
            Formatted string with volume analysis and confidence level
        """
        try:
            # Get volume data from recent market data extraction
            volume_data = await self._get_volume_data_from_extraction(symbol, timeframe)
            
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
            
            logger.bind(config_id=self.config_id, user_id=self.user_id).info(
                f"Volume analysis for {symbol} ({timeframe}, {period_used} periods): {volume_increase_pct:+.1f}% above average ({confidence_level})"
            )
            
            return volume_analysis
            
        except Exception as e:
            logger.bind(config_id=self.config_id, user_id=self.user_id).warning(
                f"Failed to get volume confirmation for {symbol}: {e}"
            )
            return f"N/A (volume analysis failed: {str(e)})"

    async def _get_volume_data_from_extraction(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        Get volume data from recent market data extraction.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for volume analysis
            
        Returns:
            Dictionary with volume analysis data or None if unavailable
        """
        try:
            from core.common.db import get_db_connection
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get recent market data for this symbol and timeframe
                    cur.execute("""
                        SELECT raw_data FROM market_data 
                        WHERE user_id = %s AND symbol = %s AND timeframe = %s
                        ORDER BY updated_at DESC LIMIT 1
                    """, (self.user_id, symbol, timeframe))
                    
                    result = cur.fetchone()
                    if not result:
                        return None
                    
                    raw_data = result[0] if isinstance(result, tuple) else result['raw_data']
                    if not raw_data or not isinstance(raw_data, dict):
                        return None

                    # Extract volume data from OHLCV candles (V2 structure)
                    candles = raw_data.get('candles', [])
                    if not candles or not isinstance(candles, list):
                        return None

                    volumes = [candle.get('volume', 0) for candle in candles if isinstance(candle, dict) and 'volume' in candle]
                    if not volumes or len(volumes) < 2:
                        return None
                    
                    # Get dynamic period for averaging
                    period = min(self._get_dynamic_volume_period(timeframe), len(volumes) - 1)
                    
                    # Calculate volume metrics
                    current_volume = volumes[-1]  # Latest candle volume
                    recent_volumes = volumes[-period-1:-1]  # Previous N periods
                    average_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else current_volume
                    
                    volume_ratio = current_volume / average_volume if average_volume > 0 else 1.0
                    
                    return {
                        'current_volume': current_volume,
                        'average_volume': average_volume,
                        'volume_ratio': volume_ratio,
                        'period_used': period
                    }
                    
        except Exception as e:
            logger.bind(config_id=self.config_id, user_id=self.user_id).warning(
                f"Failed to get volume data from extraction for {symbol}: {e}"
            )
            return None

    async def _save_position_decision_to_db(
        self, 
        symbol: str, 
        decision_data: Dict[str, Any],
        position_data: Dict,
        market_data: Dict[str, Any], 
        current_price: Decimal,
        prompt: str, 
        llm_response: str
    ) -> str:
        """Save position management decision to the decisions table with position context."""
        decision_id = str(uuid.uuid4())
        
        # Map position management actions to schema-compliant actions
        raw_action = decision_data.get('action', 'wait')
        if raw_action in ['close', 'exit']:
            schema_action = 'exit'
        else:  # wait, hold, etc.
            schema_action = 'wait'
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    decision_data_json = {
                        'decision_type': 'position_management',
                        'position_data': position_data,
                        'current_price': float(current_price),
                        'raw_action': raw_action,  # Preserve original action
                        **decision_data
                    }

                    cur.execute("""
                        INSERT INTO decisions (
                            decision_id, user_id, config_id, symbol, action, status,
                            confidence, reasoning, prompt, market_data, decision_data,
                            parent_decision_id, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        decision_id,
                        self.user_id,
                        self.config_id,
                        symbol,
                        schema_action,  # Use schema-compliant action
                        'completed',
                        decision_data.get('confidence', 0.5),
                        decision_data.get('reasoning', llm_response),
                        prompt,
                        json.dumps(market_data, cls=DecisionJSONEncoder),
                        json.dumps(decision_data_json, cls=DecisionJSONEncoder),
                        position_data.get('entry_decision_id'),  # Link to original entry decision
                        datetime.now(timezone.utc).isoformat()
                    ))
                    conn.commit()


            logger.bind(
                config_id=self.config_id,
                decision_id=decision_id,
                symbol=symbol,
                action=decision_data.get('action'),
                trade_id=position_data.get('trade_id')
            ).info("Position management decision saved to database")

            return decision_id
                    
        except Exception as e:
            logger.bind(config_id=self.config_id, symbol=symbol).error(f"Failed to save position decision: {e}")
            raise DecisionError(f"Failed to save position decision to database: {e}")

    def _create_position_management_intent(
        self, 
        decision_id: str, 
        symbol: str,
        decision_data: Dict[str, Any], 
        position_data: Dict
    ) -> Dict[str, Any]:
        """Create position management trading intent."""
        return {
            'decision_id': decision_id,
            'user_id': self.user_id,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'decision_type': 'position_management',
            'symbol': symbol,
            
            # Core decision data
            'action': decision_data.get('action', 'wait'),
            'confidence': decision_data.get('confidence', 0.5),
            'reasoning': decision_data.get('reasoning', 'No reasoning provided'),
            
            # Trade parameters
            'stop_loss_price': decision_data.get('stop_loss_price'),
            'take_profit_price': decision_data.get('take_profit_price'),
            
            # Position context for trading engine
            'trade_id': position_data.get('trade_id'),
            'existing_position': {
                'entry_price': position_data.get('entry_price'),
                'size_usd': position_data.get('size_usd'),
                'side': position_data.get('side'),
                'unrealized_pnl': position_data.get('unrealized_pnl')
            }
        }

    def _create_error_intent(self, error_message: str) -> Dict[str, Any]:
        """Create error intent."""
        return {
            'action': 'error',
            'confidence': 0.0,
            'error': error_message,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }