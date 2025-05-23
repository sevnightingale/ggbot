#!/usr/bin/env python
"""
Trading Engine for the GGBot Trading Module.

This file serves as the main facade for the Trading Module, coordinating
the interaction between the Decision Module and the various Trading Engine
services: LLM interpretation, validation, and execution.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Union

from core.common.logger import logger
from trading.engine.model.intent import Intent
from trading.engine.model.trade import Trade
from trading.engine.model.event import Event, EventType
from trading.engine.model.tool_call import ToolCall, ValidatedToolCall
from trading.engine.model.config import EngineConfig
from trading.engine.service.llm_service import LLMService
from trading.engine.service.validation_service import ValidationService
from trading.engine.service.execution_service import ExecutionService
from trading.compiler import TradeCompiler
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter
from trading.interfaces import TradingInterface


# Mock DB implementation - this will be replaced with a real DB in production
class MockDb:
    """Temporary mock database for prototype implementation."""
    
    async def get_trade(self, trade_id, user_id):
        """Get a trade record by ID."""
        logger.debug(f"DB: Getting trade {trade_id} for user {user_id}")
        return {'trade_id': trade_id, 'trade_status': 'open', 'user_id': user_id}
    
    async def create_trade(self, data):
        """Create a new trade record."""
        trade_id = data.get('trade_id', str(uuid.uuid4()))
        logger.info(f"DB: Creating trade record {trade_id}")
        logger.info(f"Trade data: {data}")
        return trade_id
    
    async def update_trade(self, trade_id, data):
        """Update an existing trade record."""
        logger.info(f"DB: Updating trade {trade_id}")
        logger.info(f"Update data: {data}")
        return True
    
    async def log_rejection(self, data):
        """Log a trade rejection."""
        logger.info(f"DB: Logging rejection")
        logger.info(f"Rejection data: {data}")
        return True
        
    async def log_error(self, data):
        """Log a trade error."""
        logger.info(f"DB: Logging error")
        logger.info(f"Error data: {data}")
        return True
    
    async def get_active_trades(self, user_id, status='open'):
        """Get all active trades for a user."""
        logger.debug(f"DB: Getting active trades for user {user_id} with status {status}")
        return []  # Empty list since we're starting fresh


# Global mock db instance for testing
# Will be replaced with proper injection in production
db = MockDb()


class EventBus:
    """Simple event bus for the Trading Engine."""
    
    def __init__(self):
        self.subscribers = {}
        
    def subscribe(self, event_type: str, callback):
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
    def emit(self, event: Event):
        """Emit an event to subscribers."""
        event_type = event.event_type.value
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                asyncio.create_task(callback(event))


class TradeManager:
    """
    Manager for trade lifecycle and position monitoring.
    
    Note: This simplified implementation will be expanded with more robust
    position monitoring and lifecycle management. It currently serves as
    a compatibility interface for the existing test suite.
    """
    
    def __init__(self, user_id: str, config: Dict, ccxt_adapter, trade_compiler, engine):
        """Initialize the trade manager."""
        self.user_id = user_id
        self.config = config
        self.ccxt_adapter = ccxt_adapter
        self.trade_compiler = trade_compiler
        self.engine = engine
        
    async def create_trade(self, decision_data: Dict, execution_result: Dict) -> Dict:
        """Create a new trade record from a decision and execution result."""
        # Create a new trade ID if one doesn't exist
        trade_id = str(uuid.uuid4())
        
        # Prepare trade data
        trade_data = {
            'trade_id': trade_id,
            'user_id': self.user_id,
            'decision_id': decision_data.get('decision_id'),
            'symbol': decision_data.get('symbol'),
            'exchange': decision_data.get('exchange'),
            'action': decision_data.get('action'),
            'entry_price': execution_result.get('entry_price'),
            'position_size': execution_result.get('position_size'),
            'leverage': decision_data.get('leverage', 1.0),
            'stop_loss_price': decision_data.get('stop_loss_price'),
            'take_profit_price': decision_data.get('take_profit_price'),
            'status': 'open',
            'execution_result': execution_result
        }
        
        # Create trade in DB
        await db.create_trade(trade_data)
        
        # Register with execution service for monitoring
        trade = Trade.model_validate(trade_data)
        if hasattr(self.engine, 'execution_service'):
            await self.engine.execution_service.register_trade(trade)
        
        return {
            'trade_id': trade_id,
            'status': 'success',
            'message': 'Trade created successfully'
        }
        
    async def update_trade(self, trade_id: str, update_data: Dict) -> Dict:
        """Update an existing trade record."""
        # Get existing trade first
        trade_data = await db.get_trade(trade_id, self.user_id)
        
        if not trade_data:
            return {
                'status': 'error',
                'message': f'Trade {trade_id} not found'
            }
            
        # Update the trade data
        for key, value in update_data.items():
            trade_data[key] = value
            
        # Update in DB
        await db.update_trade(trade_id, trade_data)
        
        return {
            'trade_id': trade_id,
            'status': 'success',
            'message': 'Trade updated successfully'
        }
        
    async def get_active_trades(self) -> List:
        """Get a list of active trades for the user."""
        return await db.get_active_trades(self.user_id, 'open')


class TradingEngine(TradingInterface):
    """
    Trading Engine that coordinates LLM-based trade execution.
    
    This is the main facade that orchestrates the interaction between
    the LLM, validation, and execution services.
    """
    
    def __init__(self, user_id: str, config: Dict):
        """Initialize the Trading Engine with configuration."""
        self.user_id = user_id
        
        # Convert dict config to EngineConfig for type safety
        self.config = EngineConfig.model_validate(config)
        self.event_bus = EventBus()
        
        # Create standard components
        exchange_id = self.config.default_exchange
        self.ccxt_adapter = CCXTMCPAdapter(exchange_id, user_id, config)
        self.trade_compiler = TradeCompiler(config, self.ccxt_adapter)
        
        # Initialize the services with dependency injection
        self.llm_service = LLMService(
            config=self.config,
            user_id=user_id,
            event_bus=self.event_bus
        )
        
        self.validation_service = ValidationService(
            config=self.config,
            trade_compiler=self.trade_compiler
        )
        
        self.execution_service = ExecutionService(
            config=self.config,
            ccxt_adapter=self.ccxt_adapter,
            event_bus=self.event_bus
        )
        
        # Create the trade manager
        self.trade_manager = TradeManager(
            user_id=user_id,
            config=config,
            ccxt_adapter=self.ccxt_adapter,
            trade_compiler=self.trade_compiler,
            engine=self
        )
        
        # For compatibility with the test module
        self.llm_provider = self.llm_service
        logger.info(f"TradingEngine initialized for user {user_id}")
        
    async def start(self):
        """Start the Trading Engine and its services."""
        logger.info("Starting TradingEngine services")
        
        # Connect to exchange
        await self.ccxt_adapter.connect()
        
        # Start the execution service (monitoring)
        await self.execution_service.start()
        
        # Emit started event
        self.event_bus.emit(Event(
            event_type=EventType.ENGINE_STARTED,
            data={"user_id": self.user_id}
        ))
        
        logger.info("TradingEngine services started")
        
    async def stop(self):
        """Stop the Trading Engine and its services."""
        logger.info("Stopping TradingEngine services")
        
        # Stop execution service
        await self.execution_service.stop()
        
        # Disconnect from exchange
        await self.ccxt_adapter.disconnect()
        
        # Emit stopped event
        self.event_bus.emit(Event(
            event_type=EventType.ENGINE_STOPPED,
            data={"user_id": self.user_id}
        ))
        
        logger.info("TradingEngine services stopped")
        
    async def process_decision(self, decision: Dict) -> Dict:
        """
        Process a trading decision from the Decision Module.
        
        Args:
            decision: Dictionary containing the trading decision
            
        Returns:
            Dictionary with execution results
        """
        # Delegate to the intent processing method
        return await self.process_decision_intent(decision)
    
    async def process_decision_intent(self, intent_data: Dict) -> Dict:
        """
        Process a trading decision intent.
        
        This is the main public API for the Trading Module. It takes a trading decision
        from the Decision Module (which can be in any format, structured or unstructured)
        and processes it through the LLM to generate tool calls for execution.
        """
        logger.info(f"Processing decision intent: {intent_data.get('decision_id')}")
        
        try:
            # 1. Get available tools for the LLM
            await self.ccxt_adapter.ensure_connected()
            tools_schema = await self.ccxt_adapter.get_tools_schema()
            
            # 2. Process via LLM to get tool calls - pass intent_data directly without validation
            # The LLM can handle semi-structured or unstructured input
            tool_calls = await self.llm_service.process_intent(intent_data, tools_schema)
            logger.info(f"LLM generated {len(tool_calls)} tool calls")
            
            # 3. Extract basic information for validation context and execution
            # We still need to know basic info like action, symbol, etc.
            action = intent_data.get('action', '')
            decision_id = intent_data.get('decision_id', 'unknown')
            
            # 4. Validate tool calls
            context = await self._get_validation_context()
            validated_calls = await self.validation_service.validate_tool_calls(
                tool_calls, intent_data, context
            )
            logger.info(f"Validation passed for {len(validated_calls)} tool calls")
            
            # 5. Execute validated calls based on action
            if action.startswith('enter_'):
                result = await self._execute_entry(intent_data, validated_calls)
            elif action == 'exit':
                result = await self._execute_exit(intent_data, validated_calls)
            elif action == 'adjust':
                result = await self._execute_adjustment(intent_data, validated_calls)
            else:
                raise ValueError(f"Unknown action: {action}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error processing decision {intent_data.get('decision_id')}: {e}", exc_info=True)
            
            # Emit error event
            self.event_bus.emit(Event(
                event_type=EventType.ENGINE_ERROR,
                data={
                    "decision_id": intent_data.get("decision_id"),
                    "error": str(e)
                }
            ))
            
            return {
                "status": "error",
                "decision_id": intent_data.get("decision_id", "unknown"),
                "message": str(e)
            }
    
    async def get_trade_status(self, trade_id: Union[str, uuid.UUID]) -> Dict:
        """
        Get the current status of a trade.
        
        Args:
            trade_id: Unique identifier of the trade
            
        Returns:
            Dictionary with trade status information
        """
        try:
            # Get trade from DB
            trade_data = await db.get_trade(str(trade_id), self.user_id)
            
            if not trade_data:
                return {
                    "status": "error",
                    "message": f"Trade {trade_id} not found"
                }
                
            # Check current position status
            symbol = trade_data.get("symbol")
            if symbol:
                # Fetch position from exchange
                position = await self.ccxt_adapter.fetch_position(symbol)
                if position:
                    trade_data["current_position"] = position
            
            return {
                "status": "success",
                "trade": trade_data
            }
        except Exception as e:
            logger.error(f"Error getting trade status for {trade_id}: {e}")
            return {
                "status": "error",
                "message": f"Error getting trade status: {str(e)}"
            }
    
    async def get_active_trades(self) -> Dict:
        """
        Get a list of all active trades.
        
        Returns:
            Dictionary with a list of active trade records
        """
        try:
            active_trades = await self.trade_manager.get_active_trades()
            return {
                "status": "success",
                "trades": active_trades
            }
        except Exception as e:
            logger.error(f"Error getting active trades: {e}")
            return {
                "status": "error",
                "message": f"Error getting active trades: {str(e)}"
            }
    
    async def _get_validation_context(self) -> Dict:
        """Get context information for validation."""
        try:
            # Get account balance
            balance = await self.ccxt_adapter.fetch_balance()
            
            # Get active positions
            positions = await self.ccxt_adapter.fetch_positions()
            
            return {
                "balance": balance,
                "positions": positions,
                "user_id": self.user_id,
                "risk_limits": self.config.get("risk_rules", {}),
                "timestamp": asyncio.get_event_loop().time()
            }
        except Exception as e:
            logger.warning(f"Error getting validation context: {e}")
            # Return minimal context
            return {
                "user_id": self.user_id,
                "risk_limits": self.config.get("risk_rules", {}),
                "timestamp": asyncio.get_event_loop().time()
            }
    
    async def _execute_entry(self, intent_data: Dict, validated_calls: List[ValidatedToolCall]) -> Dict:
        """Execute an entry trade (long or short)."""
        try:
            decision_id = intent_data.get('decision_id', 'unknown')
            
            # 1. Execute the validated calls
            execution_result = await self.execution_service.execute_tool_calls(validated_calls, intent_data)
            
            # 2. Create a trade record
            execution_data = execution_result.model_dump() if hasattr(execution_result, 'model_dump') else execution_result
            trade_result = await self.trade_manager.create_trade(
                intent_data, 
                execution_data
            )
            
            # 3. Return success with trade ID
            return {
                "status": "success",
                "decision_id": decision_id,
                "trade_id": trade_result.get("trade_id"),
                "message": "Trade executed successfully"
            }
        except Exception as e:
            logger.error(f"Error executing entry trade: {e}", exc_info=True)
            return {
                "status": "error",
                "decision_id": intent_data.get('decision_id', 'unknown'),
                "message": f"Error executing entry trade: {str(e)}"
            }
    
    async def _execute_exit(self, intent_data: Dict, validated_calls: List[ValidatedToolCall]) -> Dict:
        """Execute an exit trade."""
        try:
            symbol = intent_data.get('symbol')
            decision_id = intent_data.get('decision_id', 'unknown')
            reasoning = intent_data.get('reasoning', '')
            
            # 1. Execute the validated calls
            execution_result = await self.execution_service.execute_tool_calls(validated_calls, intent_data)
            
            # 2. Update the trade record
            # We need to find the active trade for this symbol first
            active_trades = await self.trade_manager.get_active_trades()
            trade_to_exit = None
            
            for trade in active_trades:
                if trade.get("symbol") == symbol:
                    trade_to_exit = trade
                    break
                    
            if not trade_to_exit:
                return {
                    "status": "error",
                    "decision_id": decision_id,
                    "message": f"No active trade found for {symbol}"
                }
                
            # Update the trade with exit information
            trade_id = trade_to_exit.get("trade_id")
            exec_results = execution_result.results if hasattr(execution_result, 'results') else {}
            await self.trade_manager.update_trade(trade_id, {
                "status": "closed",
                "exit_price": exec_results.get("average_price"),
                "exit_time": asyncio.get_event_loop().time(),
                "exit_reason": reasoning
            })
            
            # 3. Return success with trade ID
            return {
                "status": "success",
                "decision_id": decision_id,
                "trade_id": trade_id,
                "message": "Trade exited successfully"
            }
        except Exception as e:
            logger.error(f"Error executing exit trade: {e}", exc_info=True)
            return {
                "status": "error",
                "decision_id": intent_data.get('decision_id', 'unknown'),
                "message": f"Error executing exit trade: {str(e)}"
            }
    
    async def _execute_adjustment(self, intent_data: Dict, validated_calls: List[ValidatedToolCall]) -> Dict:
        """Execute a trade adjustment."""
        try:
            symbol = intent_data.get('symbol')
            decision_id = intent_data.get('decision_id', 'unknown')
            reasoning = intent_data.get('reasoning', '')
            stop_loss_price = intent_data.get('stop_loss_price')
            take_profit_price = intent_data.get('take_profit_price')
            
            # 1. Execute the validated calls
            execution_result = await self.execution_service.execute_tool_calls(validated_calls, intent_data)
            
            # 2. Update the trade record
            # Find the active trade for this symbol
            active_trades = await self.trade_manager.get_active_trades()
            trade_to_adjust = None
            
            for trade in active_trades:
                if trade.get("symbol") == symbol:
                    trade_to_adjust = trade
                    break
                    
            if not trade_to_adjust:
                return {
                    "status": "error",
                    "decision_id": decision_id,
                    "message": f"No active trade found for {symbol}"
                }
                
            # Update the trade with adjustment information
            trade_id = trade_to_adjust.get("trade_id")
            await self.trade_manager.update_trade(trade_id, {
                "stop_loss_price": stop_loss_price,
                "take_profit_price": take_profit_price,
                "last_adjustment": asyncio.get_event_loop().time(),
                "adjustment_reason": reasoning
            })
            
            # 3. Return success with trade ID
            return {
                "status": "success",
                "decision_id": decision_id,
                "trade_id": trade_id,
                "message": "Trade adjusted successfully"
            }
        except Exception as e:
            logger.error(f"Error executing trade adjustment: {e}", exc_info=True)
            return {
                "status": "error",
                "decision_id": intent_data.get('decision_id', 'unknown'),
                "message": f"Error executing trade adjustment: {str(e)}"
            }


# Debug helper for tests
def debug_openai_direct():
    """Debug the OpenAI API response format directly."""
    try:
        from openai import OpenAI
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Get API key
        api_key = os.environ.get("TRADING_LLM_API_KEY")
        if not api_key:
            print("No API key found in TRADING_LLM_API_KEY")
            return
            
        # Create client
        print("Creating OpenAI client...")
        client = OpenAI(api_key=api_key)
        
        # Make API call
        print("Making API call...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello world"}
            ],
            temperature=0
        )
        
        # Debug response
        print(f"Response type: {type(response)}")
        print(f"Response dir: {dir(response)}")
        print(f"Response has 'choices'? {hasattr(response, 'choices')}")
        
        if hasattr(response, 'choices') and len(response.choices) > 0:
            first_choice = response.choices[0]
            print(f"First choice type: {type(first_choice)}")
            print(f"First choice dir: {dir(first_choice)}")
            print(f"First choice has 'message'? {hasattr(first_choice, 'message')}")
            
            if hasattr(first_choice, 'message'):
                message = first_choice.message
                print(f"Message type: {type(message)}")
                print(f"Message dir: {dir(message)}")
                print(f"Message has 'content'? {hasattr(message, 'content')}")
                
                if hasattr(message, 'content'):
                    content = message.content
                    print(f"Content type: {type(content)}")
                    print(f"Content: {content}")
        
        print("Response structure check complete")
        
    except Exception as e:
        print(f"Error in debug_openai_direct: {e}")