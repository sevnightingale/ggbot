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
from core.common.db import get_db_connection
import uuid
import json


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
            # For now, just handle autonomous trading (opportunity analysis)
            # TODO: Re-enable signal validation and position management later
            return await self._handle_autonomous_trading(symbol)
                
        except (DecisionError, MarketDataError, ConfigurationError, LLMError):
            # Re-raise domain-specific errors (they're already logged)
            raise
        except Exception as e:
            logger.bind(config_id=self.config_id).error(f"Unexpected decision error: {e}")
            raise DecisionError(f"Decision making failed: {e}")
    
    # TODO: Re-implement signal validation mode when domain objects are available
    # async def _handle_signal_validation(...)
    
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
        
        # For now, skip position management and just do opportunity analysis
        # TODO: Re-enable position management later
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
        
        # Step 3: Build prompt from template
        prompt = self._build_opportunity_analysis_prompt(symbol, market_data, current_price)
        
        # Step 4: Call GPT-5
        llm_response = await self._call_gpt5(prompt)
        
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
        Get current market price using the same Hummingbot API as paper trading.
        """
        try:
            from trading.paper.market_data import MarketDataAdapter
            
            adapter = MarketDataAdapter()
            market_price = await adapter.get_current_price(symbol)
            
            # Use mid price (average of bid/ask)
            price = Decimal(str(market_price.mid))
            
            logger.bind(
                config_id=self.config_id, 
                symbol=symbol, 
                price=float(price),
                bid=market_price.bid,
                ask=market_price.ask
            ).debug("Retrieved current price from Hummingbot API")
            
            return price
            
        except Exception as e:
            logger.bind(config_id=self.config_id, symbol=symbol).error(f"Failed to get current price from Hummingbot API: {e}")
            
            # Emergency fallback with warning
            logger.bind(config_id=self.config_id, symbol=symbol).error(
                "Price source failed - using emergency mock price"
            )
            return Decimal("100.00")
    
    # TODO: Re-implement signal validation prompt when needed
    # def _build_signal_validation_prompt(...)
    
    def _build_opportunity_analysis_prompt(self, symbol: str,
                                         market_data: Dict[str, Any],
                                         current_price: Decimal) -> str:
        """Build opportunity analysis prompt from template."""
        system_prompt = self.config.decision.system_prompt.format(
            SYMBOL=symbol,
            CURRENT_PRICE=f"${current_price:,.2f}",
            MARKET_DATA=self._format_market_data_for_llm(market_data)
        )
        
        user_prompt = self.config.decision.user_prompt.format(
            SYMBOL=symbol,
            CURRENT_PRICE=f"${current_price:,.2f}",
            MARKET_DATA=self._format_market_data_for_llm(market_data)
        )
        
        return f"{system_prompt}\n\nUser: {user_prompt}"
    
    # TODO: Re-implement position management prompt when needed
    # def _build_position_management_prompt(...)
    
    async def _save_decision_to_db(self, symbol: str, decision_data: Dict[str, Any], 
                                   market_data: Dict[str, Any], current_price: Decimal,
                                   prompt: str, llm_response: str) -> str:
        """Save decision to the decisions table."""
        decision_id = str(uuid.uuid4())
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO decisions (
                            decision_id, user_id, config_id, symbol, action, status,
                            confidence, reasoning, prompt, market_data, decision_data,
                            created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        decision_id,
                        self.user_id,
                        self.config_id,
                        symbol,
                        decision_data.get('action', 'no_action'),
                        'completed',
                        decision_data.get('confidence', 0.5),
                        decision_data.get('reasoning', llm_response),
                        prompt,
                        json.dumps(market_data),
                        json.dumps(decision_data),
                        datetime.now(timezone.utc)
                    ))
                    
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
                        if "current" in indicator_data:
                            formatted.append(f"    Current Value: {indicator_data['current']}")
                        if "trend" in indicator_data:
                            trend = indicator_data["trend"]
                            if isinstance(trend, dict):
                                direction = trend.get("direction", "unknown")
                                formatted.append(f"    Trend: {direction}")
                            else:
                                formatted.append(f"    Trend: {trend}")
                        if "signals" in indicator_data:
                            signals = indicator_data["signals"]
                            if signals:
                                formatted.append(f"    Signals: {', '.join(signals)}")
                        if "zones" in indicator_data:
                            zones = indicator_data["zones"]
                            if isinstance(zones, dict):
                                current_zone = zones.get("current", "unknown")
                                formatted.append(f"    Zone: {current_zone}")
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
        """Call GPT-5 API using the new Responses API."""
        try:
            # Use the new Responses API with high reasoning for trading decisions
            response = await self.openai_client.responses.create(
                model="gpt-5",
                input=prompt,
                reasoning={"effort": "high"},  # High reasoning for complex trading decisions
                text={"verbosity": "medium"}   # Medium verbosity for balanced output
            )
            
            return response.output_text
            
        except Exception as e:
            logger.error(f"GPT-5 API call failed: {e}")
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
    
    # TODO: Re-implement strategy run creation when domain objects are available
    # async def _create_strategy_run(...)
    # def _create_trading_intent(...)
    
    def _create_error_intent(self, error_message: str) -> Dict[str, Any]:
        """Create error intent."""
        return {
            'action': 'error',
            'confidence': 0.0,
            'error': error_message,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }