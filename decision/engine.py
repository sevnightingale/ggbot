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
import psycopg2
from psycopg2.extras import RealDictCursor
import ccxt

from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, DECISION_LLM_API_KEY
from core.common.logger import logger
from decision.llm_providers import get_llm_provider
from decision.interfaces.llm_provider import LLMProvider


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
        
        # Health check
        if not await self.llm_provider.health_check():
            logger.bind(module="decision.engine").warning(
                f"LLM provider {provider_name} health check failed"
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
                AND config_type = 'user'
            """, (self.user_id, self.config_id))
            
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"No user configuration found for config_id {self.config_id}")
            
            # Extract decision config from unified config
            user_config = result['config_data']
            if 'decision' not in user_config:
                raise ValueError(f"No decision configuration in user config for config_id {self.config_id}")
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(f"Loaded decision configuration from unified config {self.config_id}")
            return user_config['decision']
            
        finally:
            conn.close()
    
    def _fetch_market_data(self, symbol: str, timeframes: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch latest market data from the database.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTC/USD')
            timeframes (List[str]): List of timeframes to fetch (e.g., ['15m', '1h', '4h'])
            
        Returns:
            Dict[str, Dict[str, Any]]: Market data organized by timeframe
        """
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            market_data = {}
            
            for timeframe in timeframes:
                # Get the most recent data for this symbol/timeframe
                cursor.execute("""
                    SELECT source, data_type, indicators, raw_data, updated_at
                    FROM market_data
                    WHERE user_id = %s
                    AND symbol = %s
                    AND timeframe = %s
                    ORDER BY updated_at DESC
                    LIMIT 10
                """, (self.user_id, symbol, timeframe))
                
                results = cursor.fetchall()
                
                # Organize data by source and type
                timeframe_data = {
                    'indicators': {},
                    'signals': {},
                    'raw_data': {},
                    'latest_update': None
                }
                
                # Track what data types we've already processed to avoid overwriting newer data with older
                processed_types = set()
                
                for row in results:
                    source = row['source']
                    data_type = row['data_type']
                    
                    # Since results are ordered by updated_at DESC, only process the first occurrence of each data type
                    if data_type in processed_types:
                        continue
                        
                    if data_type == 'indicator_values' and row['indicators']:
                        timeframe_data['indicators'].update(row['indicators'])
                        processed_types.add(data_type)
                    
                    elif data_type == 'indicator_analysis' and row['raw_data']:
                        # Extract LLM interpretation from indicator analysis
                        if 'interpretation' in row['raw_data']:
                            timeframe_data['signals']['llm_analysis'] = row['raw_data']['interpretation']
                        
                        # Also extract raw indicators if needed
                        if 'indicators' in row['raw_data']:
                            timeframe_data['raw_data']['indicators'] = row['raw_data']['indicators']
                        processed_types.add(data_type)
                    
                    elif data_type == 'report' and row['raw_data']:
                        # Extract ggshot or other signals
                        if 'report' in row['raw_data']:
                            timeframe_data['signals'][source] = row['raw_data']['report']
                        processed_types.add(data_type)
                    
                    elif data_type == 'llm_interpretation' and row['raw_data']:
                        # Include LLM interpretations if available (legacy)
                        if 'interpretation' in row['raw_data']:
                            timeframe_data['signals']['llm_analysis'] = row['raw_data']['interpretation']
                        processed_types.add(data_type)
                    
                    # Track latest update
                    if not timeframe_data['latest_update'] or row['updated_at'] > timeframe_data['latest_update']:
                        timeframe_data['latest_update'] = row['updated_at']
                
                market_data[timeframe] = timeframe_data
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                f"Fetched market data for {symbol} across {len(timeframes)} timeframes"
            )
            return market_data
            
        finally:
            conn.close()
    
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
                SELECT trade_id, pair, entry_price, leverage, collateral_amount,
                       stop_loss, take_profit, created_at, execution_details
                FROM trades
                WHERE user_id = %s
                AND config_id = %s
                AND trade_status IN ('open', 'active', 'pending')
                ORDER BY created_at DESC
            """, (self.user_id, self.config_id))
            
            trades = cursor.fetchall()
            
            # Convert to list of dicts and parse decision history
            active_trades = []
            for trade in trades:
                trade_dict = dict(trade)
                
                # Extract decision history from execution_details
                if trade_dict.get('execution_details') and 'decision_history' in trade_dict['execution_details']:
                    trade_dict['decision_history'] = trade_dict['execution_details']['decision_history']
                else:
                    trade_dict['decision_history'] = []
                
                active_trades.append(trade_dict)
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                f"Found {len(active_trades)} active trades"
            )
            return active_trades
            
        finally:
            conn.close()
    
    async def _fetch_current_price(self, symbol: str) -> Optional[float]:
        """
        Fetch current market price for a symbol using direct CCXT connection.
        Uses the user's configured exchange from the database.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTC/USD')
            
        Returns:
            float: Current price, or None if fetch fails
        """
        try:
            # Get exchange configuration from user's trading config
            exchange_name = self.config.get('exchange', 'bitmex')
            use_testnet = self.config.get('testnet', True)
            
            # Get credentials from database config
            conn = self._get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT config_data 
                    FROM configurations 
                    WHERE user_id = %s 
                    AND config_id = %s 
                    AND config_type = 'user'
                """, (self.user_id, self.config_id))
                
                result = cursor.fetchone()
                if not result:
                    raise ValueError("No configuration found")
                
                user_config = result['config_data']
                credentials = user_config.get('exchanges', {}).get(exchange_name, {})
                
                if not credentials.get('api_key') or not credentials.get('api_secret'):
                    # Fallback to environment variables
                    credentials = {
                        'api_key': os.getenv('EXCHANGE_API'),
                        'api_secret': os.getenv('EXCHANGE_SECRET')
                    }
                    
            finally:
                conn.close()
            
            if not credentials.get('api_key') or not credentials.get('api_secret'):
                logger.bind(module="decision.engine", user_id=self.user_id).warning(
                    f"No credentials found for {exchange_name}, cannot fetch current price"
                )
                return None
            
            # Create exchange client
            exchange_class = getattr(ccxt, exchange_name)
            config = {
                'apiKey': credentials['api_key'],
                'secret': credentials['api_secret'],
                'enableRateLimit': True,
                'options': {}
            }
            
            if use_testnet:
                config['options']['testnet'] = True
            
            exchange = exchange_class(config)
            
            # Load markets first
            await exchange.load_markets()
            
            # Fetch ticker
            ticker = await exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Close exchange connection
            await exchange.close()
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                f"Fetched current price for {symbol} from {exchange_name}: ${current_price:,.2f}"
            )
            
            return current_price
            
        except Exception as e:
            logger.bind(module="decision.engine", user_id=self.user_id).error(
                f"Failed to fetch current price for {symbol}: {e}"
            )
            return None
    
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
                SELECT execution_details
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
            
            # Update the trade
            cursor.execute("""
                UPDATE trades
                SET execution_details = %s
                WHERE trade_id = %s
            """, (json.dumps(execution_details), trade_id))
            
            conn.commit()
            
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                f"Updated trade {trade_id} with decision: {decision}"
            )
            
        finally:
            conn.close()
    
    async def _format_prompt_new_trade(self, market_data: Dict, account_state: Dict, symbol: str) -> str:
        """
        Format prompt for new trade evaluation.
        
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
            f"- {symbol}: ${current_price:,.2f}" if current_price else f"- {symbol}: Price unavailable",
            "",
            "## Account Status",
            f"- Total Equity: {account_state['equity']:.8f} BTC",
            f"- Available Margin: {account_state['available_margin']:.8f} BTC",
            f"- Used Margin: {account_state['used_margin']:.8f} BTC",
            f"- Open Positions: {len(account_state['positions'])}",
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
            "## CRITICAL: MANDATORY TRADING RULES",
            "🚨 YOU MUST ALWAYS GENERATE A TRADING DECISION - NEVER 'no_action' 🚨",
            "",
            "The strategy states: 'Always enter trades based on RSI position relative to 50'",
            "- RSI > 50 = MANDATORY SHORT position",  
            "- RSI < 50 = MANDATORY LONG position",
            "- You MUST examine the RSI values above and determine if they are above or below 50",
            "- Generate 'short' if RSI > 50, 'long' if RSI < 50",
            "- 'no_action' is NEVER allowed per the strategy requirements",
            "",
            "FOLLOW THE STRATEGY EXACTLY - Do NOT use broader market analysis to override this.",
            "",
            "## Decision Required",
            "Based on the above data and the EXACT strategy rules, should we enter a new position?",
            "",
            "IMPORTANT: Use the current market price shown above for all calculations.",
            "",
            "Please provide your decision in the following format:",
            "",
            "Action: [long/short/no_action]",
            "Confidence: [0.0-1.0] (REQUIRED - your confidence level in this decision)",
            "Risk_Percentage: [percentage of account to risk, e.g., '2%']",
            "Collateral_USD: [REQUIRED - USD amount of collateral based on current price, e.g., '$200']",
            "Leverage: [REQUIRED - leverage multiplier as number, e.g., '10']",
            "Total_Position_USD: [total position size in USD, e.g., '$2,000']",
            "Stop_Loss: [price level and reasoning, e.g., '$108,000 - below key support']",
            "Take_Profit: [price level(s) and reasoning, e.g., '$115,000 - 3:1 risk/reward at resistance']",
            "Reasoning: [REQUIRED - Your detailed analysis following the strategy rules exactly, including:",
            "  - Why this entry based on the strategy (RSI above/below 50)",
            "  - What you expect to happen",
            "  - Risk management rationale",
            "  - Exit plan and timeline]",
            "",
            "IMPORTANT: You MUST include ALL fields above. Each field should be on its own line.",
            "Example calculation: If current BTC price is $67,000 and risking 2% of available margin = $200 collateral. With 10x leverage = $2,000 total position."
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
            f"- Direction: {'Long' if active_trade.get('pair', '').endswith('buy') else 'Short'}",
            f"- {position_info}",
            f"- Leverage: {active_trade.get('leverage', 'N/A')}x",
            f"- Stop Loss: {active_trade.get('stop_loss', 'N/A')}",
            f"- Take Profit: {active_trade.get('take_profit', 'N/A')}",
            f"- Time in Trade: {(datetime.now(timezone.utc) - active_trade['created_at'].replace(tzinfo=timezone.utc)).total_seconds() / 3600:.1f} hours",
            ""
        ]
        
        # Add decision history
        if active_trade.get('decision_history'):
            prompt_parts.append("## Decision History")
            for i, decision in enumerate(active_trade['decision_history'][-3:]):  # Last 3 decisions
                prompt_parts.append(
                    f"{i+1}. {decision['timestamp']}: {decision['action']} "
                    f"(confidence: {decision['confidence']}) - {decision['reasoning'][:100]}..."
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
            "## Strategy Reminder",
            self.config.get('strategy', 'No strategy defined')[:200] + "...",
            "",
            "## Decision Required",
            "Should we continue holding this position, adjust it, or close it?",
            "Consider the original entry reasoning and how market conditions have changed.",
            "",
            "Please provide your decision in the following format:",
            "",
            "Action: [hold/add/reduce/close/adjust_stops]",
            "Confidence: [0.0-1.0] (REQUIRED - your confidence level in this decision)",
            "Position Size: [ONLY if 'add' or 'reduce' action:",
            "  - For 'add': Additional position details like new trade entry",
            "  - For 'reduce': Percentage to close (e.g., 'Close 50% of position')]",
            "Stop Loss: [ONLY if 'adjust_stops': New stop loss level and reasoning]",
            "Take Profit: [ONLY if 'adjust_stops': New take profit level and reasoning]",
            "Reasoning: [REQUIRED - Your analysis including:",
            "  - Current position status and P&L",
            "  - Why this action based on strategy",
            "  - Risk management considerations",
            "  - Updated market outlook]",
            "",
            "IMPORTANT: You MUST include both Confidence and Reasoning fields. These are required."
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, response: str, mode: str = 'new_trade') -> Dict[str, Any]:
        """
        Minimal parsing of LLM response - extract only confidence and reasoning.
        The Trading Module's LLM will handle the actual trading instructions.
        
        Args:
            response (str): Raw LLM response
            mode (str): 'new_trade' or 'manage_trade'
            
        Returns:
            Dict[str, Any]: Decision data with confidence, reasoning, and raw response
        """
        # Initialize result with defaults
        result = {
            'decision': 'trading_llm_will_parse',  # Placeholder - Trading Module will determine
            'confidence': 0.5,  # Default moderate confidence if not found
            'reasoning': '',  # Will be extracted
            'raw_response': response,
            'mode': mode
        }
        
        # Parse line by line for confidence, leverage, collateral, and reasoning
        lines = response.strip().split('\n')
        capture_reasoning = False
        reasoning_lines = []
        import re
        
        for line in lines:
            line_stripped = line.strip()
            
            # Look for confidence in various formats
            if 'confidence:' in line_stripped.lower():
                # Try to extract confidence value
                # Handle formats like "Confidence: 0.65" or "**Confidence:** 0.8"
                try:
                    # Remove markdown formatting
                    clean_line = line_stripped.replace('**', '').replace('*', '')
                    # Split by colon and get the number
                    parts = clean_line.split(':')
                    if len(parts) >= 2:
                        confidence_str = parts[1].strip()
                        # Extract first number found
                        numbers = re.findall(r'\d*\.?\d+', confidence_str)
                        if numbers:
                            confidence = float(numbers[0])
                            result['confidence'] = max(0.0, min(1.0, confidence))
                            logger.bind(module="decision.engine").info(f"Parsed confidence: {result['confidence']}")
                except Exception as e:
                    logger.bind(module="decision.engine").warning(f"Failed to parse confidence: {e}")
            
            # Look for leverage
            elif 'leverage:' in line_stripped.lower():
                try:
                    clean_line = line_stripped.replace('**', '').replace('*', '')
                    parts = clean_line.split(':')
                    if len(parts) >= 2:
                        leverage_str = parts[1].strip()
                        # Extract number, handle "10x" or "10" format
                        numbers = re.findall(r'\d+', leverage_str)
                        if numbers:
                            result['leverage'] = int(numbers[0])
                            logger.bind(module="decision.engine").info(f"Parsed leverage: {result['leverage']}")
                except Exception as e:
                    logger.bind(module="decision.engine").warning(f"Failed to parse leverage: {e}")
            
            # Look for collateral USD
            elif 'collateral_usd:' in line_stripped.lower():
                try:
                    clean_line = line_stripped.replace('**', '').replace('*', '')
                    parts = clean_line.split(':')
                    if len(parts) >= 2:
                        collateral_str = parts[1].strip()
                        # Extract number, handle "$200" or "200" format
                        numbers = re.findall(r'\d+\.?\d*', collateral_str)
                        if numbers:
                            result['collateral_usd'] = float(numbers[0])
                            logger.bind(module="decision.engine").info(f"Parsed collateral_usd: {result['collateral_usd']}")
                except Exception as e:
                    logger.bind(module="decision.engine").warning(f"Failed to parse collateral_usd: {e}")
            
            # Look for reasoning section
            elif 'reasoning:' in line_stripped.lower() or capture_reasoning:
                if 'reasoning:' in line_stripped.lower():
                    capture_reasoning = True
                    # Get any text after "Reasoning:" on the same line
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        reasoning_text = parts[1].strip()
                        if reasoning_text:
                            reasoning_lines.append(reasoning_text)
                elif capture_reasoning and line_stripped:
                    # Continue capturing reasoning until we hit another section
                    if any(line_stripped.lower().startswith(x) for x in ['action:', 'confidence:', 'position size:', 'stop loss:', 'take profit:', '**action:', '**confidence:', '**position']):
                        capture_reasoning = False
                    else:
                        reasoning_lines.append(line)
        
        # Join reasoning lines
        if reasoning_lines:
            result['reasoning'] = '\n'.join(reasoning_lines).strip()
        else:
            # Fallback: use the entire response as reasoning if we couldn't parse it
            result['reasoning'] = response
        
        logger.bind(module="decision.engine").info(
            f"Parsed LLM response: confidence={result['confidence']}, "
            f"leverage={result.get('leverage', 'Not found')}, "
            f"collateral_usd={result.get('collateral_usd', 'Not found')}, "
            f"reasoning_length={len(result['reasoning'])}, passing full response to Trading Module"
        )
        
        return result
    
    async def make_decision(self, symbol: str = "BTC/USD", 
                          timeframes: List[str] = None) -> Dict[str, Any]:
        """
        Main entry point to make a trading decision.
        
        Args:
            symbol (str): Trading symbol
            timeframes (List[str]): Timeframes to analyze
            
        Returns:
            Dict[str, Any]: Trading intent ready for the Trading Module
        """
        if not self.llm_provider:
            await self.initialize()
        
        if not timeframes:
            timeframes = ['15m', '1h', '4h']
        
        # Fetch all required data
        market_data = self._fetch_market_data(symbol, timeframes)
        account_state = self._fetch_account_state()
        active_trades = self._fetch_active_trades()
        
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
                
                # Get decision from LLM
                response, metadata = await self.llm_provider.generate_response(
                    prompt=prompt,
                    conversation_history=trade.get('decision_history', []),
                    temperature=0.7
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
                    decision['decision'],
                    decision['confidence'],
                    decision['reasoning']
                )
                
                decisions.append(decision)
            
            # For now, return the first decision (in future, could handle multiple)
            if decisions:
                return self._create_intent(decisions[0], mode='manage')
        
        else:
            # New Trade Mode
            logger.bind(module="decision.engine", user_id=self.user_id).info("Entering New Trade Mode")
            
            # Format prompt
            prompt = await self._format_prompt_new_trade(market_data, account_state, symbol)
            
            # DEBUG: Log the full prompt
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                "📝 DECISION LLM USER PROMPT:\n{prompt}",
                prompt=prompt
            )
            
            # Get decision from LLM
            response, metadata = await self.llm_provider.generate_response(
                prompt=prompt,
                temperature=0.7
            )
            
            # DEBUG: Log the full response
            logger.bind(module="decision.engine", user_id=self.user_id).info(
                "🤖 DECISION LLM RESPONSE:\n{response}",
                response=response
            )
            
            # Parse response
            decision = self._parse_llm_response(response, mode='new_trade')
            decision['metadata'] = metadata
            
            return self._create_intent(decision, mode='new')
    
    def _create_intent(self, decision: Dict[str, Any], mode: str) -> Dict[str, Any]:
        """
        Create a trading intent for the Trading Module.
        Includes parsed confidence/reasoning and raw LLM decision.
        
        Args:
            decision (Dict): Decision data with parsed fields and raw response
            mode (str): 'new' or 'manage'
            
        Returns:
            Dict[str, Any]: Trading intent with both parsed metadata and raw decision
        """
        # Generate a unique decision ID
        decision_id = str(uuid.uuid4())
        
        # Create intent with parsed metadata and raw LLM decision
        intent = {
            'decision_id': decision_id,
            'user_id': self.user_id,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mode': mode,
            'symbol': 'BTC/USD',  # TODO: Make this dynamic
            'exchange': 'bitmex',  # TODO: Make this configurable
            
            # Include parsed confidence and reasoning for Decision Module use
            'confidence': decision['confidence'],
            'reasoning': decision['reasoning'],
            
            # Include parsed trading parameters if found
            'leverage': decision.get('leverage'),  # Will be None if not parsed
            'collateral_amount': decision.get('collateral_usd'),  # Will be None if not parsed
            
            # Pass the ENTIRE raw LLM response - Trading Module's LLM will understand it
            'llm_decision': decision['raw_response'],
            
            # Include metadata
            'metadata': decision.get('metadata', {}),
            
            # Signal to Trading Module that this needs LLM processing
            'action': 'process_llm_decision',
            
            # Include any additional context
            'decision_mode': mode,
            'trade_id': decision.get('trade_id') if mode == 'manage' else None
        }
        
        logger.bind(module="decision.engine").info(
            f"Created intent with raw LLM decision for Trading Module processing"
        )
        
        return intent