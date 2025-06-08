#!/usr/bin/env python
"""
Trading Engine for the GGBot Trading Module.

This file serves as the main facade for the Trading Module, coordinating
the interaction between the Decision Module and the various Trading Engine
services: LLM interpretation, validation, and execution.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from core.common.logger import logger
from core.common.db import get_db_connection
from trading.engine_services.model.intent import Intent
from trading.engine_services.model.trade import Trade
from trading.engine_services.model.event import Event, EventType
from trading.engine_services.model.tool_call import ToolCall, ValidatedToolCall
from trading.engine_services.model.config import EngineConfig
from trading.engine_services.service.llm_service import LLMService
from trading.engine_services.service.validation_service import ValidationService
from trading.engine_services.service.execution_service import ExecutionService
from trading.compiler import TradeCompiler
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter
from trading.interfaces import TradingInterface


# Import the real database implementation
from trading.db import get_trade_db

# Get the database instance
db = get_trade_db()


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
        
        # Extract entry price from successful market order in execution results
        entry_price = self._extract_entry_price_from_execution(execution_result)
        if entry_price is None:
            logger.error(f"Cannot create trade record for {trade_id}: no valid entry_price in execution result")
            logger.error(f"Execution result: {execution_result}")
            raise ValueError("Cannot create trade record without valid entry_price - main order likely failed")
        
        # Prepare trade data
        trade_data = {
            'trade_id': trade_id,
            'user_id': self.user_id,
            'decision_id': decision_data.get('decision_id'),
            'config_id': decision_data.get('config_id'),
            'symbol': decision_data.get('symbol'),
            'exchange': decision_data.get('exchange'),
            'action': decision_data.get('action'),
            'entry_price': entry_price,
            'position_size': execution_result.get('position_size'),
            'leverage': decision_data.get('leverage', 1.0),
            'stop_loss_price': decision_data.get('stop_loss_price'),
            'take_profit_price': decision_data.get('take_profit_price'),
            'collateral_amount': decision_data.get('collateral_amount'),
            'confidence': decision_data.get('confidence'),
            'reasoning': decision_data.get('reasoning'),
            'status': 'open',
            'execution_result': execution_result,
            'direction': 'long',  # Default to long for market buy orders
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Create trade in DB
        await db.create_trade(trade_data)
        
        # Create strategy_runs entry for TRADE_ENTRY scenario
        await self._create_strategy_run(
            trade_id=trade_id,
            config_id=decision_data.get('config_id'),
            decision_id=decision_data.get('decision_id'),
            scenario='TRADE_ENTRY',
            leverage=decision_data.get('leverage'),
            confidence_score=decision_data.get('confidence'),
            reasoning_log=decision_data.get('reasoning'),
            decision_data={
                'action': decision_data.get('action'),
                'symbol': decision_data.get('symbol'),
                'entry_conditions': {
                    'price': trade_data.get('entry_price'),
                    'stop_loss': decision_data.get('stop_loss_price'),
                    'take_profit': decision_data.get('take_profit_price'),
                    'collateral_amount': decision_data.get('collateral_amount')
                },
                'market_context': decision_data.get('market_context', {}),
                'execution_details': execution_result
            }
        )
        
        # Register with execution service for monitoring
        trade = Trade.model_validate(trade_data)
        if hasattr(self.engine, 'execution_service'):
            await self.engine.execution_service.register_trade(trade_id, trade_data)
        
        return {
            'trade_id': trade_id,
            'status': 'success',
            'message': 'Trade created successfully'
        }
    
    def _extract_entry_price_from_execution(self, execution_result: Dict) -> Optional[float]:
        """
        Extract entry price from execution result, looking for successful market buy/sell orders.
        
        Args:
            execution_result: The execution result containing order details
            
        Returns:
            Entry price as float, or None if not found
        """
        try:
            # Look for results in the execution result
            results = execution_result.get('results', {})
            
            if isinstance(results, dict) and 'results' in results:
                order_results = results['results']
            else:
                return None
                
            # Look for market buy or sell orders (main position orders)
            for result in order_results:
                tool = result.get('tool', '')
                if 'market' in tool.lower() and ('buy' in tool.lower() or 'sell' in tool.lower()):
                    # Extract price from the order result
                    result_text = result.get('result', '')
                    if isinstance(result_text, str):
                        # Parse the JSON content from the text - handle MCP TextContent format
                        import json
                        import re
                        
                        # First try to extract JSON from MCP TextContent format
                        # Format: "meta=None content=[TextContent(type='text', text='{...}', annotations=None)] isError=False"
                        logger.info(f"🔍 DEBUG: Checking MCP format for {tool}")
                        logger.info(f"🔍 DEBUG: Result text (first 200 chars): {result_text[:200]}")
                        
                        if "TextContent(type='text', text='" in result_text:
                            # Extract the JSON from the text field - improved parsing
                            text_start = result_text.find("text='") + 6
                            text_end = result_text.find("', annotations=", text_start)
                            
                            if text_start > 5 and text_end > text_start:
                                json_str = result_text[text_start:text_end]
                                logger.info(f"🔍 DEBUG: Extracted raw JSON string (first 200 chars): {json_str[:200]}")
                                
                                # Handle escaped characters properly - improved unescaping
                                # The JSON is double-escaped: \\n becomes \n, \\\" becomes \"
                                json_str = json_str.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                logger.info(f"🔍 DEBUG: After unescaping (first 200 chars): {json_str[:200]}")
                                
                                try:
                                    order_data = json.loads(json_str)
                                    logger.info(f"🔍 DEBUG: Successfully parsed JSON, keys: {list(order_data.keys())}")
                                    
                                    # BitMEX market orders usually have 'average' or 'price' fields
                                    entry_price = order_data.get('average') or order_data.get('price')
                                    logger.info(f"🔍 DEBUG: Found average={order_data.get('average')}, price={order_data.get('price')}")
                                    
                                    if entry_price:
                                        logger.info(f"✅ Extracted entry price: {entry_price} from {tool} (MCP format)")
                                        return float(entry_price)
                                        
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse JSON from MCP TextContent in {tool}: {e}")
                                    logger.warning(f"JSON string was: {json_str[:500]}...")
                            else:
                                logger.warning(f"Could not find proper text boundaries in MCP format for {tool}")
                        
                        # Fallback: Look for JSON in the text content (original approach)
                        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                        if json_match:
                            try:
                                order_data = json.loads(json_match.group(0))
                                
                                # BitMEX market orders usually have 'average' or 'price' fields
                                entry_price = order_data.get('average') or order_data.get('price')
                                if entry_price:
                                    logger.info(f"Extracted entry price: {entry_price} from {tool} (fallback regex)")
                                    return float(entry_price)
                                    
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse JSON from {tool} result (fallback)")
                                
            logger.warning("No entry price found in execution results")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting entry price from execution result: {e}")
            return None
    
    def _parse_mcp_textcontent(self, result_text: str) -> Optional[Dict]:
        """
        Parse MCP TextContent format to extract JSON data.
        
        Args:
            result_text: Raw MCP result string
            
        Returns:
            Parsed JSON data as dict, or None if parsing fails
        """
        try:
            import json
            
            if "TextContent(type='text', text='" in result_text:
                # Extract the JSON from the text field
                text_start = result_text.find("text='") + 6
                text_end = result_text.find("', annotations=", text_start)
                
                if text_start > 5 and text_end > text_start:
                    json_str = result_text[text_start:text_end]
                    
                    # Handle escaped characters properly
                    json_str = json_str.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                    
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON from MCP TextContent: {e}")
                        return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing MCP TextContent: {e}")
            return None
        
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
    
    async def _create_strategy_run(self, trade_id: str, config_id: Optional[str], 
                                   decision_id: Optional[str], scenario: str,
                                   leverage: Optional[int] = None, 
                                   confidence_score: Optional[float] = None,
                                   reasoning_log: Optional[str] = None,
                                   decision_data: Optional[Dict] = None,
                                   parent_strategy_run_id: Optional[str] = None) -> str:
        """Create a strategy_runs entry for decision tracking."""
        
        strategy_run_id = str(uuid.uuid4())
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                INSERT INTO strategy_runs (
                    strategy_run_id, trade_id, config_id, decision_id, leverage,
                    confidence_score, reasoning_log, decision_data, scenario,
                    parent_strategy_run_id, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                strategy_run_id,
                trade_id,
                config_id,
                decision_id,
                leverage,
                confidence_score,
                reasoning_log,
                json.dumps(decision_data) if decision_data else None,
                scenario,
                parent_strategy_run_id,
                datetime.now()
            )
            
            cursor.execute(query, values)
            conn.commit()
            
            logger.info(f"Created strategy_run {strategy_run_id} for trade {trade_id} (scenario: {scenario})")
            return strategy_run_id


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
            config=self.config.validation,
            trade_compiler=self.trade_compiler
        )
        
        self.execution_service = ExecutionService(
            config=self.config.execution,
            ccxt_adapter=self.ccxt_adapter,
            event_bus=self.event_bus,
            db=db,
            user_id=user_id
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
        self.event_bus.emit(Event.create(
            event_type=EventType.ENGINE_STARTED,
            user_id=self.user_id
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
        self.event_bus.emit(Event.create(
            event_type=EventType.ENGINE_STOPPED,
            user_id=self.user_id
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
            context = await self._get_validation_context(intent_data)
            validated_calls = await self.validation_service.validate_tool_calls(
                tool_calls, intent_data, context
            )
            logger.info(f"Validation passed for {len(validated_calls)} tool calls")
            
            # 5. Execute validated calls - the LLM has already interpreted the intent
            # and generated the appropriate tool calls, so we don't need strict action matching
            result = await self._execute_validated_calls(intent_data, validated_calls)
                
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"Error processing decision {intent_data.get('decision_id')}: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            
            # Emit error event
            self.event_bus.emit(Event.create(
                event_type=EventType.DECISION_FAILED,
                decision_id=intent_data.get("decision_id"),
                details={"error": str(e)}
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
    
    async def _get_original_strategy_run_id(self, trade_id: str) -> Optional[str]:
        """Get the original TRADE_ENTRY strategy_run_id for a trade."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT strategy_run_id 
                    FROM strategy_runs 
                    WHERE trade_id = %s AND scenario = 'TRADE_ENTRY'
                    ORDER BY created_at ASC 
                    LIMIT 1
                """
                
                cursor.execute(query, (trade_id,))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                    
                logger.warning(f"No original TRADE_ENTRY strategy_run found for trade {trade_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting original strategy_run_id for trade {trade_id}: {e}")
            return None
    
    async def _get_validation_context(self, intent_data: Optional[Dict] = None) -> Dict:
        """Get context information for validation."""
        try:
            # Check if we have account state from the API (working test pattern)
            account_state = intent_data.get('_account_state') if intent_data else None
            
            if account_state:
                logger.info("Using account state from API for validation context")
                return {
                    "balance": account_state.get('balance_data', {}),
                    "positions": account_state.get('position_data', []),
                    "account_state": account_state,  # Include full account state for risk calculations
                    "user_id": self.user_id,
                    "risk_limits": self.config.risk_rules or {},
                    "timestamp": asyncio.get_event_loop().time()
                }
            else:
                # Fallback to live exchange data
                logger.info("Fetching validation context from exchange")
                balance = await self.ccxt_adapter.fetch_balance()
                positions = await self.ccxt_adapter.fetch_positions()
                
                return {
                    "balance": balance,
                    "positions": positions,
                    "user_id": self.user_id,
                    "risk_limits": self.config.risk_rules or {},
                    "timestamp": asyncio.get_event_loop().time()
                }
        except Exception as e:
            logger.warning(f"Error getting validation context: {e}")
            # Return minimal context
            return {
                "user_id": self.user_id,
                "risk_limits": self.config.risk_rules or {},
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
            
            # Create strategy_runs entry for TRADE_EXIT scenario
            # Find the original TRADE_ENTRY strategy_run to link to
            original_strategy_run_id = await self._get_original_strategy_run_id(trade_id)
            
            await self.trade_manager._create_strategy_run(
                trade_id=trade_id,
                config_id=intent_data.get('config_id'),
                decision_id=decision_id,
                scenario='TRADE_EXIT',
                reasoning_log=reasoning,
                decision_data={
                    'action': 'exit',
                    'exit_conditions': {
                        'exit_price': exec_results.get("average_price"),
                        'exit_reason': reasoning
                    },
                    'execution_details': execution_result
                },
                parent_strategy_run_id=original_strategy_run_id
            )
            
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
    
    async def _execute_validated_calls(self, intent_data: Dict, validated_calls: List[ValidatedToolCall]) -> Dict:
        """
        Execute validated tool calls regardless of action type.
        
        The LLM has already interpreted the intent and generated appropriate tool calls,
        so we just need to execute them and manage the trade records accordingly.
        """
        try:
            decision_id = intent_data.get('decision_id', 'unknown')
            
            # 1. Generate trade ID for database record
            trade_id = str(uuid.uuid4())
            
            # 2. Execute the validated calls
            execution_result = await self.execution_service.execute_tool_calls(validated_calls, intent_data)
            
            # 3. Determine if this is creating a new trade or managing an existing one
            # by checking if we're opening a position (has create order calls)
            is_new_trade = any(
                'create' in call.tool and 'order' in call.tool
                for call in validated_calls
            )
            
            if is_new_trade:
                # Store order details for trade lifecycle tracking
                await self._store_order_details(trade_id, execution_result, intent_data)
                
                # Create a new trade record (existing logic)
                execution_data = execution_result.to_dict() if hasattr(execution_result, 'to_dict') else execution_result
                trade_result = await self.trade_manager.create_trade(
                    intent_data, 
                    execution_data
                )
                
                return {
                    "status": "success",
                    "decision_id": decision_id,
                    "trade_id": trade_result.get("trade_id"),
                    "message": "Trade executed successfully"
                }
            else:
                # This is managing an existing trade (exit, adjust, etc.)
                # The execution result contains the details
                return {
                    "status": "success",
                    "decision_id": decision_id,
                    "message": "Trade action executed successfully",
                    "execution_result": execution_result
                }
                
        except Exception as e:
            import traceback
            logger.error(f"Error executing validated calls: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return {
                "status": "error",
                "decision_id": intent_data.get('decision_id', 'unknown'),
                "message": f"Error executing trade action: {str(e)}"
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
            
            # Create strategy_runs entry for TRADE_MANAGEMENT scenario
            # Find the original TRADE_ENTRY strategy_run to link to
            original_strategy_run_id = await self._get_original_strategy_run_id(trade_id)
            
            await self.trade_manager._create_strategy_run(
                trade_id=trade_id,
                config_id=intent_data.get('config_id'),
                decision_id=decision_id,
                scenario='TRADE_MANAGEMENT',
                reasoning_log=reasoning,
                decision_data={
                    'action': 'adjust',
                    'adjustments': {
                        'stop_loss_price': stop_loss_price,
                        'take_profit_price': take_profit_price
                    },
                    'execution_details': execution_result
                },
                parent_strategy_run_id=original_strategy_run_id
            )
            
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
    
    async def _store_order_details(self, trade_id: str, execution_result: Any, intent_data: Dict):
        """
        Store order details in trade_orders table for trade lifecycle tracking.
        
        This enables VWAP calculation and precise P&L tracking when positions are synced.
        """
        try:
            
            # Extract order information from execution result
            # Handle nested structure: execution_result['results']['results']
            results_data = execution_result.get('results', {}) if isinstance(execution_result, dict) else {}
            if isinstance(results_data, dict) and 'results' in results_data:
                results = results_data['results']
            else:
                results = []
            
            for result in results:
                if isinstance(result, dict) and result.get('result') and not result.get('error'):
                    result_text = result['result']
                    
                    # Parse MCP TextContent format to extract JSON
                    order_data = self._parse_mcp_textcontent(result_text)
                    if not order_data:
                        continue
                    
                    # Extract order details
                    order_id = order_data.get('id')
                    if not order_id:
                        continue
                    
                    # Store in trade_orders table
                    await self._insert_trade_order(
                        trade_id=trade_id,
                        exchange=intent_data.get('exchange', 'bitmex'),
                        symbol=intent_data.get('symbol', ''),
                        exchange_order_id=str(order_id),
                        client_order_id=order_data.get('clientOrderId'),
                        order_type=order_data.get('type', 'market'),
                        side=order_data.get('side', 'buy'),
                        price=order_data.get('price'),
                        size=order_data.get('amount'),
                        status=order_data.get('status', 'open')
                    )
                    
            logger.info(f"Stored order details for trade {trade_id}")
            
        except Exception as e:
            logger.error(f"Error storing order details: {e}")
    
    async def _insert_trade_order(self, trade_id: str, exchange: str, symbol: str, 
                                 exchange_order_id: str, client_order_id: Optional[str],
                                 order_type: str, side: str, price: Optional[float],
                                 size: Optional[float], status: str):
        """Insert order record into trade_orders table."""
        
        from core.common.db import get_db_connection
        
        conn = await get_db_connection()
        try:
            cursor = conn.cursor()
            
            query = """
                INSERT INTO trade_orders (
                    trade_id, exchange, symbol, exchange_order_id, client_order_id,
                    order_type, side, price, size, status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                trade_id, exchange, symbol, exchange_order_id, client_order_id,
                order_type, side, price, size, status, datetime.now()
            )
            
            cursor.execute(query, values)
            conn.commit()
            
        finally:
            conn.close()


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