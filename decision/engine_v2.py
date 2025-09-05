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
import openai

from core.common.logger import logger
from core.config import ConfigRepository, BotConfig, config_repo
from core.domain import (
    # Strategy tracking
    StrategyRun, DecisionScenario, DecisionOutcome, DecisionContext,
    strategy_run_repo,
    
    # Position management  
    Position, PositionStatus, PositionSide, position_repo,
    
    # Market data
    MarketDataSnapshot, DataFreshness, market_data_repo,
    
    # Value objects
    Symbol, Money, Confidence
)


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
        self.config: Optional[BotConfig] = None
        
        # OpenAI client
        self.openai_client = openai.AsyncOpenAI()
        
        logger.bind(config_id=config_id).info("DecisionEngineV2 initialized")
    
    async def initialize(self) -> None:
        """Load configuration and validate setup."""
        try:
            self.config = config_repo.get_config(self.config_id, self.user_id)
            if not self.config:
                raise ConfigurationError(f"Configuration {self.config_id} not found")
            # Use getattr to safely access config_type, default to "autonomous" if not found
            config_type = getattr(self.config, 'config_type', 'autonomous')
            logger.bind(config_id=self.config_id, mode=config_type).info("Configuration loaded")
        except Exception as e:
            logger.bind(config_id=self.config_id).error(f"Failed to load config: {e}")
            raise ConfigurationError(f"Failed to load config {self.config_id}: {e}")
    
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
            # Route based on configuration type
            if self.config.config_type == "signal_validation":
                return await self._handle_signal_validation(symbol, signal_data)
            elif self.config.config_type == "autonomous_trading":
                return await self._handle_autonomous_trading(symbol)
            else:
                raise ValueError(f"Unknown config_type: {self.config.config_type}")
                
        except (DecisionError, MarketDataError, ConfigurationError, LLMError):
            # Re-raise domain-specific errors (they're already logged)
            raise
        except Exception as e:
            logger.bind(config_id=self.config_id).error(f"Unexpected decision error: {e}")
            raise DecisionError(f"Decision making failed: {e}")
    
    async def _handle_signal_validation(self, symbol: str, 
                                      signal_data: Dict) -> Dict[str, Any]:
        """
        Handle signal validation mode - validate external signals.
        
        Process:
        1. Get fresh market data for signal symbol
        2. Use signal validation prompt template  
        3. Call GPT-5 for validation decision
        4. Create validation strategy run
        5. Return trading intent if validation passes
        """
        if not symbol or not signal_data:
            return self._create_error_intent("Signal validation requires symbol and signal_data")
        
        symbol_obj = Symbol.from_string(symbol)
        
        # Step 1: Get fresh market data
        market_data = await self._get_fresh_market_data(symbol_obj)
        if not market_data:
            return self._create_error_intent(f"No fresh market data available for {symbol}")
        
        # Step 2: Get current price
        current_price = await self._get_current_price(symbol_obj)
        
        # Step 3: Build prompt from template
        prompt = self._build_signal_validation_prompt(
            symbol_obj, signal_data, market_data, current_price
        )
        
        # Step 4: Call GPT-5
        llm_response = await self._call_gpt5(prompt)
        
        # Step 5: Parse response
        decision_data = self._parse_llm_response(llm_response)
        
        # Step 6: Create strategy run
        strategy_run = await self._create_strategy_run(
            DecisionScenario.SIGNAL_VALIDATION,
            symbol_obj,
            decision_data,
            market_data,
            current_price
        )
        
        # Step 7: Return intent
        return self._create_trading_intent(strategy_run, 'signal_validation')
    
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
        
        symbol_obj = Symbol.from_string(trading_symbol)
        
        # Check for active positions
        active_positions = await position_repo.get_active_positions(self.config_id)
        
        if active_positions:
            # Handle multiple active positions
            results = []
            for position in active_positions:
                try:
                    result = await self._handle_position_management(symbol_obj, position)
                    results.append(result)
                except Exception as e:
                    logger.bind(config_id=self.config_id, trade_id=position.trade_id).error(f"Position management failed: {e}")
                    results.append(self._create_error_intent(f"Position management failed for {position.trade_id}: {e}"))
            
            # For now, return the first successful result or first error
            return results[0] if results else self._create_error_intent("No position management results")
        else:
            # Opportunity analysis mode
            return await self._handle_opportunity_analysis(symbol_obj)
    
    async def _handle_opportunity_analysis(self, symbol: Symbol) -> Dict[str, Any]:
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
            return self._create_error_intent(f"No fresh market data available for {symbol.internal_format}")
        
        # Step 2: Get current price
        current_price = await self._get_current_price(symbol)
        
        # Step 3: Build prompt from template
        prompt = self._build_opportunity_analysis_prompt(symbol, market_data, current_price)
        
        # Step 4: Call GPT-5
        llm_response = await self._call_gpt5(prompt)
        
        # Step 5: Parse response
        decision_data = self._parse_llm_response(llm_response)
        
        # Step 6: Create strategy run
        strategy_run = await self._create_strategy_run(
            DecisionScenario.OPPORTUNITY_ANALYSIS,
            symbol,
            decision_data,
            market_data,
            current_price
        )
        
        # Step 7: Return intent
        return self._create_trading_intent(strategy_run, 'opportunity_analysis')
    
    async def _handle_position_management(self, symbol: Symbol, 
                                        position: Position) -> Dict[str, Any]:
        """
        Manage existing position with full context.
        
        Process:
        1. Get position management context (original entry decision)
        2. Get fresh market data
        3. Use position management prompt template with context
        4. Call GPT-5 for management decision
        5. Create position management strategy run
        6. Return management intent
        """
        # Step 1: Get original context
        original_context = strategy_run_repo.get_position_management_context(position.trade_id)
        if not original_context:
            logger.warning(f"No original context found for position {position.trade_id}")
        
        # Step 2: Get fresh market data
        market_data = await self._get_fresh_market_data(symbol)
        if not market_data:
            return self._create_error_intent(f"No fresh market data for position management")
        
        # Step 3: Get current price and update position
        current_price = await self._get_current_price(symbol)
        position.update_current_price(current_price)
        
        # Step 4: Build prompt with context
        prompt = self._build_position_management_prompt(
            symbol, position, market_data, current_price, original_context
        )
        
        # Step 5: Call GPT-5
        llm_response = await self._call_gpt5(prompt)
        
        # Step 6: Parse response
        decision_data = self._parse_llm_response(llm_response)
        
        # Step 7: Create strategy run
        strategy_run = await self._create_strategy_run(
            DecisionScenario.POSITION_MANAGEMENT,
            symbol,
            decision_data,
            market_data,
            current_price,
            trade_id=position.trade_id
        )
        
        # Step 8: Return intent
        return self._create_trading_intent(strategy_run, 'position_management')
    
    async def _get_fresh_market_data(self, symbol: Symbol) -> MarketDataSnapshot:
        """
        Get fresh market data for this config.
        
        NOTE: Orchestrator is responsible for ensuring fresh data exists.
        DecisionEngine just retrieves it from database.
        """
        # Get market data for this specific config (not universal)
        snapshot = await market_data_repo.get_fresh_data_for_config(
            symbol=symbol, 
            config_id=self.config_id,
            user_id=None  # Will be derived from config_id
        )
        
        if snapshot:
            logger.bind(
                config_id=self.config_id, 
                symbol=symbol.internal_format, 
                age_seconds=snapshot.age_seconds,
                indicators_count=len(snapshot.indicators)
            ).info("Retrieved market data for decision")
            return snapshot
        
        # If no data available, orchestrator failed to ensure freshness
        logger.bind(config_id=self.config_id, symbol=symbol.internal_format).error(
            "No market data available - orchestrator should have ensured fresh data"
        )
        raise MarketDataError(
            f"No market data available for {symbol.internal_format}. "
            f"Orchestrator should have triggered extraction and waited for completion."
        )
    
    async def _get_current_price(self, symbol: Symbol) -> Decimal:
        """
        Get current market price using the same Hummingbot API as paper trading.
        """
        try:
            from trading.paper.market_data import MarketDataAdapter
            
            adapter = MarketDataAdapter()
            market_price = await adapter.get_current_price(symbol.internal_format)
            
            # Use mid price (average of bid/ask)
            price = Decimal(str(market_price.mid))
            
            logger.bind(
                config_id=self.config_id, 
                symbol=symbol.internal_format, 
                price=float(price),
                bid=market_price.bid,
                ask=market_price.ask
            ).debug("Retrieved current price from Hummingbot API")
            
            return price
            
        except Exception as e:
            logger.bind(config_id=self.config_id, symbol=symbol.internal_format).error(f"Failed to get current price from Hummingbot API: {e}")
            
            # Fallback: try to get price from market data
            try:
                snapshot = await market_data_repo.get_fresh_data_for_config(
                    symbol=symbol, 
                    config_id=self.config_id,
                    user_id=None
                )
                
                if snapshot and snapshot.price_data and snapshot.price_data.price:
                    logger.bind(config_id=self.config_id, symbol=symbol.internal_format).warning("Using fallback price from market data")
                    return snapshot.price_data.price
                    
            except Exception as fallback_error:
                logger.bind(config_id=self.config_id, symbol=symbol.internal_format).error(f"Fallback price fetch also failed: {fallback_error}")
            
            # Emergency fallback with warning
            logger.bind(config_id=self.config_id, symbol=symbol.internal_format).error(
                "All price sources failed - using emergency mock price"
            )
            return Decimal("100.00")
    
    def _build_signal_validation_prompt(self, symbol: Symbol, signal_data: Dict,
                                      market_data: MarketDataSnapshot,
                                      current_price: Decimal) -> str:
        """Build signal validation prompt from template."""
        # Inject variables into system prompt template
        system_prompt = self.config.decision.system_prompt.format(
            SYMBOL=symbol.internal_format,
            CURRENT_PRICE=f"${current_price:,.2f}",
            MARKET_DATA=self._format_market_data_for_llm(market_data)
        )
        
        # Inject variables into user prompt template  
        user_prompt = self.config.decision.user_prompt.format(
            SYMBOL=symbol.internal_format,
            CURRENT_PRICE=f"${current_price:,.2f}",
            MARKET_DATA=self._format_market_data_for_llm(market_data),
            SIGNAL_DATA=self._format_signal_data_for_llm(signal_data)
        )
        
        return f"{system_prompt}\n\nUser: {user_prompt}"
    
    def _build_opportunity_analysis_prompt(self, symbol: Symbol,
                                         market_data: MarketDataSnapshot,
                                         current_price: Decimal) -> str:
        """Build opportunity analysis prompt from template."""
        system_prompt = self.config.decision.system_prompt.format(
            SYMBOL=symbol.internal_format,
            CURRENT_PRICE=f"${current_price:,.2f}",
            MARKET_DATA=self._format_market_data_for_llm(market_data)
        )
        
        user_prompt = self.config.decision.user_prompt.format(
            SYMBOL=symbol.internal_format,
            CURRENT_PRICE=f"${current_price:,.2f}",
            MARKET_DATA=self._format_market_data_for_llm(market_data)
        )
        
        return f"{system_prompt}\n\nUser: {user_prompt}"
    
    def _build_position_management_prompt(self, symbol: Symbol, position: Position,
                                        market_data: MarketDataSnapshot,
                                        current_price: Decimal,
                                        original_context: Optional[Dict]) -> str:
        """Build position management prompt with original context."""
        # Calculate position metrics
        metrics = position.calculate_metrics()
        
        # Format original context
        context_summary = "No original context available"
        if original_context:
            entry_decision = original_context.get('entry_decision', {})
            context_summary = f"""
Original Entry Decision:
- Entry Confidence: {entry_decision.get('confidence', 0):.1%}
- Entry Reasoning: {entry_decision.get('reasoning', 'N/A')[:200]}...
- Position Age: {position.time_in_position.total_seconds() / 3600:.1f} hours
- Current P&L: {metrics.unrealized_pnl if metrics else 'N/A'}
"""
        
        system_prompt = self.config.decision.system_prompt.format(
            SYMBOL=symbol.internal_format,
            CURRENT_PRICE=f"${current_price:,.2f}",
            MARKET_DATA=self._format_market_data_for_llm(market_data),
            POSITION_CONTEXT=context_summary
        )
        
        user_prompt = self.config.decision.user_prompt.format(
            SYMBOL=symbol.internal_format,
            CURRENT_PRICE=f"${current_price:,.2f}",
            MARKET_DATA=self._format_market_data_for_llm(market_data),
            POSITION_CONTEXT=context_summary
        )
        
        return f"{system_prompt}\n\nUser: {user_prompt}"
    
    def _format_market_data_for_llm(self, market_data: MarketDataSnapshot) -> str:
        """Format market data for LLM consumption."""
        summary = market_data.get_summary_for_llm()
        
        formatted = f"Market Data for {summary['symbol']} (Freshness: {summary['freshness']}):\n"
        
        for timeframe, data in summary.get('timeframes', {}).items():
            formatted += f"\n{timeframe} Timeframe:\n"
            for indicator, value in data['indicators'].items():
                formatted += f"  - {indicator}: {value}\n"
        
        if 'volume_analysis' in summary:
            vol = summary['volume_analysis']
            formatted += f"\nVolume Analysis:\n"
            formatted += f"  - Current/Average Ratio: {vol['volume_ratio']:.2f}x\n"
            formatted += f"  - Confidence Level: {vol['confidence_level']}\n"
        
        return formatted
    
    def _format_signal_data_for_llm(self, signal_data: Dict) -> str:
        """Format signal data for LLM consumption."""
        return f"""
Signal Information:
- Signal Type: {signal_data.get('type', 'Unknown')}
- Direction: {signal_data.get('direction', 'Unknown')}
- Confidence: {signal_data.get('confidence', 'Unknown')}
- Source: {signal_data.get('source', 'Unknown')}
- Raw Message: {signal_data.get('message', 'No message provided')[:500]}...
"""
    
    async def _call_gpt5(self, prompt: str) -> str:
        """Call GPT-5 API with the formatted prompt."""
        try:
            # Split prompt into system and user parts
            if "User: " in prompt:
                system_part, user_part = prompt.split("User: ", 1)
                messages = [
                    {"role": "system", "content": system_part.strip()},
                    {"role": "user", "content": user_part.strip()}
                ]
            else:
                messages = [{"role": "user", "content": prompt}]
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",  # TODO: Update to GPT-5 when available
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"GPT API call failed: {e}")
            raise
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured decision data."""
        # Simple parsing - look for structured output
        parsed = {
            'action': 'no_action',
            'confidence': 0.5,
            'reasoning': response,
            'stop_loss_price': None,
            'take_profit_price': None
        }
        
        lines = response.upper().split('\n')
        
        for line in lines:
            line = line.strip()
            
            if 'ACTION:' in line:
                action = line.split('ACTION:')[1].strip().lower()
                if action in ['long', 'short', 'hold', 'close', 'no_action', 'validate']:
                    parsed['action'] = action
            
            elif 'CONFIDENCE:' in line:
                try:
                    conf_str = line.split('CONFIDENCE:')[1].strip()
                    # Extract number (handle both 0.8 and 80% formats)
                    import re
                    numbers = re.findall(r'\d*\.?\d+', conf_str)
                    if numbers:
                        conf = float(numbers[0])
                        parsed['confidence'] = min(1.0, max(0.0, conf if conf <= 1.0 else conf/100))
                except:
                    pass
            
            elif 'STOP_LOSS:' in line or 'STOP LOSS:' in line:
                try:
                    sl_str = line.split('LOSS:')[1].strip()
                    import re
                    numbers = re.findall(r'\d+\.?\d*', sl_str)
                    if numbers:
                        parsed['stop_loss_price'] = float(numbers[0])
                except:
                    pass
            
            elif 'TAKE_PROFIT:' in line or 'TAKE PROFIT:' in line:
                try:
                    tp_str = line.split('PROFIT:')[1].strip()
                    import re
                    numbers = re.findall(r'\d+\.?\d*', tp_str)
                    if numbers:
                        parsed['take_profit_price'] = float(numbers[0])
                except:
                    pass
        
        return parsed
    
    async def _create_strategy_run(self, scenario: DecisionScenario, symbol: Symbol,
                                 decision_data: Dict, market_data: MarketDataSnapshot,
                                 current_price: Decimal,
                                 trade_id: Optional[str] = None) -> StrategyRun:
        """Create and save strategy run record."""
        # Map action to outcome
        outcome_map = {
            'long': DecisionOutcome.ENTER_LONG,
            'short': DecisionOutcome.ENTER_SHORT,
            'hold': DecisionOutcome.HOLD_POSITION,
            'close': DecisionOutcome.CLOSE_POSITION,
            'no_action': DecisionOutcome.NO_ACTION,
            'validate': DecisionOutcome.VALIDATION_PASSED  # Default, could be FAILED based on confidence
        }
        
        outcome = outcome_map.get(decision_data['action'], DecisionOutcome.NO_ACTION)
        
        # For signal validation, set outcome based on confidence
        if scenario == DecisionScenario.SIGNAL_VALIDATION:
            outcome = (DecisionOutcome.VALIDATION_PASSED 
                      if decision_data['confidence'] >= 0.7 
                      else DecisionOutcome.VALIDATION_FAILED)
        
        # Create decision context
        context = DecisionContext(
            market_data=market_data.get_summary_for_llm(),
            current_price=float(current_price),
            strategy_template=self.config.decision.user_prompt,
            llm_reasoning=decision_data['reasoning'],
            confidence_factors={
                'market_data_freshness': market_data.freshness_level.value,
                'decision_scenario': scenario.value,
                'parsed_confidence': decision_data['confidence']
            },
            timestamp=datetime.now()
        )
        
        # Create strategy run
        if scenario == DecisionScenario.OPPORTUNITY_ANALYSIS:
            strategy_run = StrategyRun.create_opportunity_analysis(
                config_id=self.config_id,
                symbol=symbol,
                outcome=outcome,
                confidence=Confidence(score=Decimal(str(decision_data['confidence']))),
                reasoning=decision_data['reasoning'],
                context=context,
                trade_id=trade_id
            )
        elif scenario == DecisionScenario.POSITION_MANAGEMENT:
            strategy_run = StrategyRun.create_position_management(
                trade_id=trade_id,
                config_id=self.config_id,
                symbol=symbol,
                outcome=outcome,
                confidence=Confidence(score=Decimal(str(decision_data['confidence']))),
                reasoning=decision_data['reasoning'],
                context=context
            )
        else:  # SIGNAL_VALIDATION
            strategy_run = StrategyRun.create_signal_validation(
                config_id=self.config_id,
                symbol=symbol,
                outcome=outcome,
                confidence=Confidence(score=Decimal(str(decision_data['confidence']))),
                reasoning=decision_data['reasoning'],
                context=context,
                trade_id=trade_id
            )
        
        # Save strategy run
        await strategy_run_repo.save(strategy_run)
        
        return strategy_run
    
    def _create_trading_intent(self, strategy_run: StrategyRun, 
                             decision_type: str) -> Dict[str, Any]:
        """Create trading intent from strategy run."""
        return {
            'decision_id': strategy_run.strategy_run_id,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'decision_type': decision_type,
            'scenario': strategy_run.scenario.value,
            'outcome': strategy_run.outcome.value,
            
            # Core decision data
            'action': strategy_run.outcome.value.lower(),
            'confidence': strategy_run.confidence.score,
            'reasoning': strategy_run.reasoning_log,
            'symbol': strategy_run.symbol.internal_format,
            
            # Trade parameters
            'stop_loss_price': strategy_run.stop_loss_price,
            'take_profit_price': strategy_run.take_profit_price,
            
            # Context
            'strategy_run_id': strategy_run.strategy_run_id,
            'trade_id': strategy_run.trade_id,
            'market_data_freshness': strategy_run.decision_context.confidence_factors.get('market_data_freshness'),
            'decision_context': strategy_run.decision_context.to_dict()
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