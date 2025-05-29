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
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

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
                AND config_type = 'decision'
            """, (self.user_id, self.config_id))
            
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"No decision configuration found for config_id {self.config_id}")
            
            logger.bind(module="decision.engine", user_id=self.user_id).info("Loaded decision configuration")
            return result['config_data']
            
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
                
                for row in results:
                    source = row['source']
                    data_type = row['data_type']
                    
                    if data_type == 'indicator_values' and row['indicators']:
                        timeframe_data['indicators'].update(row['indicators'])
                    
                    elif data_type == 'indicator_analysis' and row['raw_data']:
                        # Extract LLM interpretation from indicator analysis
                        if 'interpretation' in row['raw_data']:
                            timeframe_data['signals']['llm_analysis'] = row['raw_data']['interpretation']
                        
                        # Also extract raw indicators if needed
                        if 'indicators' in row['raw_data']:
                            timeframe_data['raw_data']['indicators'] = row['raw_data']['indicators']
                    
                    elif data_type == 'report' and row['raw_data']:
                        # Extract ggshot or other signals
                        if 'report' in row['raw_data']:
                            timeframe_data['signals'][source] = row['raw_data']['report']
                    
                    elif data_type == 'llm_interpretation' and row['raw_data']:
                        # Include LLM interpretations if available (legacy)
                        if 'interpretation' in row['raw_data']:
                            timeframe_data['signals']['llm_analysis'] = row['raw_data']['interpretation']
                    
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
    
    def _format_prompt_new_trade(self, market_data: Dict, account_state: Dict, symbol: str) -> str:
        """
        Format prompt for new trade evaluation.
        
        Args:
            market_data (Dict): Market data by timeframe
            account_state (Dict): Current account state
            symbol (str): Trading symbol
            
        Returns:
            str: Formatted prompt for the LLM
        """
        prompt_parts = [
            f"# Trading Decision Request - New Trade Evaluation",
            f"Symbol: {symbol}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
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
            "## IMPORTANT: Strategy Implementation Rules",
            "You MUST follow the trading strategy exactly as written above. Do NOT use general market analysis.",
            "If the strategy says 'Always enter trades', then you MUST generate a buy or sell decision.",
            "Focus on the specific indicators mentioned in the strategy (e.g., RSI levels, price action).",
            "Do not override the strategy with broader market sentiment unless explicitly instructed.",
            "",
            "## Decision Required",
            "Based on the above data and the EXACT strategy rules, should we enter a new position?",
            "Please provide your decision in the following format:",
            "",
            "Decision: [buy/sell/hold]",
            "Confidence: [0.0-1.0]",
            "Position Size: [percentage of capital, e.g., 0.02 for 2%]",
            "Leverage: [1-10]",
            "Stop Loss: [price level]",
            "Take Profit: [price level]",
            "Reasoning: [Your detailed analysis following the strategy rules exactly]"
        ])
        
        return "\n".join(prompt_parts)
    
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
            "Decision: [hold/adjust/close]",
            "Confidence: [0.0-1.0]",
            "Action Details: [if adjust: new stop loss/take profit; if close: market or limit]",
            "Reasoning: [Your analysis considering the trade history and current conditions]"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, response: str, mode: str = 'new_trade') -> Dict[str, Any]:
        """
        Parse the LLM response into a structured format.
        
        Args:
            response (str): Raw LLM response
            mode (str): 'new_trade' or 'manage_trade'
            
        Returns:
            Dict[str, Any]: Parsed decision data
        """
        # Initialize result
        result = {
            'decision': 'hold',
            'confidence': 0.0,
            'reasoning': '',
            'raw_response': response
        }
        
        # Parse line by line
        lines = response.strip().split('\n')
        reasoning_lines = []
        capture_reasoning = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Decision:'):
                decision = line.replace('Decision:', '').strip().lower()
                result['decision'] = decision
            
            elif line.startswith('Confidence:'):
                try:
                    confidence = float(line.replace('Confidence:', '').strip())
                    result['confidence'] = max(0.0, min(1.0, confidence))
                except:
                    pass
            
            elif mode == 'new_trade' and line.startswith('Position Size:'):
                try:
                    size = float(line.replace('Position Size:', '').strip().rstrip('%'))
                    result['position_size'] = size / 100 if size > 1 else size
                except:
                    pass
            
            elif mode == 'new_trade' and line.startswith('Leverage:'):
                try:
                    result['leverage'] = int(float(line.replace('Leverage:', '').strip().rstrip('x')))
                except:
                    pass
            
            elif line.startswith('Stop Loss:'):
                try:
                    result['stop_loss'] = float(line.replace('Stop Loss:', '').strip())
                except:
                    pass
            
            elif line.startswith('Take Profit:'):
                try:
                    result['take_profit'] = float(line.replace('Take Profit:', '').strip())
                except:
                    pass
            
            elif mode == 'manage_trade' and line.startswith('Action Details:'):
                result['action_details'] = line.replace('Action Details:', '').strip()
            
            elif line.startswith('Reasoning:'):
                capture_reasoning = True
                reasoning_lines.append(line.replace('Reasoning:', '').strip())
            
            elif capture_reasoning and line:
                reasoning_lines.append(line)
        
        result['reasoning'] = ' '.join(reasoning_lines)
        
        # Validate required fields
        if mode == 'new_trade' and result['decision'] in ['buy', 'sell']:
            # Ensure we have required fields for a new trade
            if 'position_size' not in result:
                result['position_size'] = 0.02  # Default 2%
            if 'leverage' not in result:
                result['leverage'] = 5  # Default 5x
        
        logger.bind(module="decision.engine").info(
            f"Parsed LLM response: decision={result['decision']}, "
            f"confidence={result['confidence']}"
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
                
                # Get decision from LLM
                response, metadata = await self.llm_provider.generate_response(
                    prompt=prompt,
                    conversation_history=trade.get('decision_history', []),
                    temperature=0.7
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
            prompt = self._format_prompt_new_trade(market_data, account_state, symbol)
            
            # Get decision from LLM
            response, metadata = await self.llm_provider.generate_response(
                prompt=prompt,
                temperature=0.7
            )
            
            # Parse response
            decision = self._parse_llm_response(response, mode='new_trade')
            decision['metadata'] = metadata
            
            return self._create_intent(decision, mode='new')
    
    def _create_intent(self, decision: Dict[str, Any], mode: str) -> Dict[str, Any]:
        """
        Create a trading intent for the Trading Module.
        
        Args:
            decision (Dict): Parsed decision from LLM
            mode (str): 'new' or 'manage'
            
        Returns:
            Dict[str, Any]: Trading intent
        """
        # Generate a unique decision ID
        decision_id = str(uuid.uuid4())
        
        # Base intent structure
        intent = {
            'decision_id': decision_id,
            'user_id': self.user_id,
            'config_id': self.config_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'confidence': decision['confidence'],
            'reasoning': decision['reasoning'],
            'metadata': decision.get('metadata', {})
        }
        
        # Add mode-specific fields
        if mode == 'new' and decision['decision'] in ['buy', 'sell']:
            intent.update({
                'action': 'open_position',
                'side': 'long' if decision['decision'] == 'buy' else 'short',
                'symbol': 'BTC/USD',  # TODO: Make this dynamic
                'position_size': decision.get('position_size', 0.02),
                'leverage': decision.get('leverage', 5),
                'stop_loss': decision.get('stop_loss'),
                'take_profit': decision.get('take_profit')
            })
        
        elif mode == 'manage':
            intent['trade_id'] = decision.get('trade_id')
            
            if decision['decision'] == 'close':
                intent['action'] = 'close_position'
            elif decision['decision'] == 'adjust':
                intent['action'] = 'adjust_position'
                intent['adjustments'] = decision.get('action_details', {})
            else:  # hold
                intent['action'] = 'hold_position'
        
        else:
            # No action needed
            intent['action'] = 'no_action'
        
        logger.bind(module="decision.engine").info(
            f"Created intent: {intent['action']} with confidence {intent['confidence']}"
        )
        
        return intent