"""
Execution Service for the Trading Engine.

This service handles the execution of validated tool calls through the CCXT MCP adapter,
position monitoring, and trade lifecycle management.
"""

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

from core.common.logger import logger
from trading.engine_services.model.config import ExecutionConfig
from trading.engine_services.model.intent import Intent
from trading.engine_services.model.tool_call import ValidatedToolCall
from trading.engine_services.model.trade import Trade, TradeStatus
from trading.engine_services.model.event import Event, EventType


class EventBus:
    """
    Simple event bus implementation for trading engine components.
    
    This allows components to emit and subscribe to events for loosely
    coupled communication.
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self.subscribers = {}
        
    def subscribe(self, event_type: str, callback):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is emitted
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
    def emit(self, event: Event):
        """
        Emit an event to all subscribers.
        
        Args:
            event: Event to emit
        """
        event_type = event.event_type.value
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}", exc_info=True)


class ExecutionResult:
    """Result of executing a batch of tool calls."""
    
    def __init__(
        self, 
        intent_id: str, 
        results: Dict,
        status: str = "success",
        message: Optional[str] = None
    ):
        """
        Initialize the execution result.
        
        Args:
            intent_id: Decision ID that triggered the execution
            results: Raw results from the CCXT MCP adapter
            status: Status of the execution (success, error)
            message: Optional message for error status
        """
        self.intent_id = intent_id
        self.results = results
        self.status = status
        self.message = message
        
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "intent_id": self.intent_id,
            "results": self.results,
            "status": self.status,
            "message": self.message
        }


class ExecutionService:
    """
    Service for executing tool calls and monitoring positions.
    
    This service is responsible for:
    1. Executing validated tool calls via the CCXT MCP adapter
    2. Tracking active trades and their status
    3. Polling for position updates from the exchange
    4. Triggering auto-exit logic for stop loss and take profit
    """
    
    def __init__(
        self, 
        config: ExecutionConfig, 
        ccxt_adapter,
        event_bus=None,
        db=None,
        user_id=None
    ):
        """
        Initialize the execution service.
        
        Args:
            config: Configuration for the execution service
            ccxt_adapter: CCXT MCP adapter for exchange interaction
            event_bus: Optional event bus for emitting events
            db: Database connection for trade persistence
            user_id: User ID for trade queries
        """
        self.config = config
        self.ccxt_adapter = ccxt_adapter
        self.event_bus = event_bus or EventBus()
        self.db = db  # Real database connection
        self.user_id = user_id
        
        # Active trades tracking
        self.active_trades = {}
        
        # Service state
        self._running = False
        
        logger.info("ExecutionService initialized")
    
    async def start(self):
        """
        Start the execution service and position monitoring.
        
        This will begin polling for position updates for active trades.
        """
        if self._running:
            logger.warning("ExecutionService already running")
            return
            
        self._running = True
        
        # Load active trades from database
        await self._load_active_trades_from_db()
        
        # Note: Position monitoring is handled by AccountMonitoringService
        # No need for duplicate polling here
        
        # Emit event
        self.event_bus.emit(Event.create(EventType.ENGINE_STARTED))
        
        logger.info("ExecutionService started")
    
    async def stop(self):
        """
        Stop the execution service.
        
        This will clean up resources and mark the service as stopped.
        """
        if not self._running:
            return
            
        self._running = False
        
        logger.info("Stopping ExecutionService...")
        
        # Emit event
        self.event_bus.emit(Event.create(EventType.ENGINE_STOPPED))
        
        logger.info("ExecutionService stopped")
    
    async def execute_tool_calls(
        self, 
        validated_calls: List[ValidatedToolCall], 
        intent_data: Dict
    ) -> ExecutionResult:
        """
        Execute a sequence of validated tool calls.
        
        Args:
            validated_calls: List of validated tool calls to execute
            intent_data: Original intent data that generated the calls (dict)
            
        Returns:
            ExecutionResult with the results of the execution
        """
        # Extract decision_id for logging and events
        decision_id = intent_data.get('decision_id', 'unknown')
        
        if not validated_calls:
            logger.warning(f"No validated tool calls to execute for intent {decision_id}")
            return ExecutionResult(
                intent_id=decision_id,
                results={},
                status="error",
                message="No validated tool calls to execute"
            )
            
        try:
            # Ensure exchange connection is established
            await self.ccxt_adapter.ensure_connected()
            
            # Emit event for batch execution start
            self.event_bus.emit(Event.create(
                EventType.TOOL_CALLS_BATCH_STARTED,
                decision_id=decision_id,
                details={"call_count": len(validated_calls)}
            ))
            
            # Convert ValidatedToolCall objects to dictionaries
            raw_calls = []
            for call in validated_calls:
                raw_calls.append({
                    "tool": call.tool,
                    "parameters": call.parameters
                })
                
            # Execute the calls via the adapter with timeout
            try:
                # Default timeout is 20 seconds
                execution_results = await asyncio.wait_for(
                    self.ccxt_adapter.execute_batch(raw_calls),
                    timeout=20.0
                )
            except asyncio.TimeoutError:
                logger.error(f"Execution timed out for intent {decision_id}")
                
                # Emit event for batch execution failure
                self.event_bus.emit(Event.create(
                    EventType.TOOL_CALLS_BATCH_FAILED,
                    decision_id=decision_id,
                    details={"error": "Execution timed out after 20 seconds"}
                ))
                
                return ExecutionResult(
                    intent_id=decision_id,
                    results={},
                    status="error",
                    message="Execution timed out after 20 seconds"
                )
                
            # Check for errors in the results
            if not self._check_execution_success(execution_results):
                error_msgs = self._extract_error_messages(execution_results)
                logger.error(f"Errors in execution for intent {decision_id}: {error_msgs}")
                
                # Emit event for batch execution failure
                self.event_bus.emit(Event.create(
                    EventType.TOOL_CALLS_BATCH_FAILED,
                    decision_id=decision_id,
                    details={"error": error_msgs}
                ))
                
                return ExecutionResult(
                    intent_id=decision_id,
                    results=execution_results,
                    status="error",
                    message=f"Execution failed: {error_msgs}"
                )
                
            # Emit event for batch execution success
            self.event_bus.emit(Event.create(
                EventType.TOOL_CALLS_BATCH_SUCCEEDED,
                decision_id=decision_id,
                details={"result_count": len(execution_results.get("results", []))}
            ))
            
            # Return successful result
            return ExecutionResult(
                intent_id=decision_id,
                results=execution_results,
                status="success"
            )
            
        except Exception as e:
            logger.error(f"Error executing tool calls for intent {decision_id}: {e}", exc_info=True)
            
            # Emit event for batch execution failure
            self.event_bus.emit(Event.create(
                EventType.TOOL_CALLS_BATCH_FAILED,
                decision_id=decision_id,
                details={"error": str(e)}
            ))
            
            return ExecutionResult(
                intent_id=decision_id,
                results={},
                status="error",
                message=f"Internal error: {str(e)}"
            )
    
    async def register_trade(self, trade_id: str, trade_data: Dict = None):
        """
        Register a trade for monitoring.
        
        Args:
            trade_id: ID of the trade to register
            trade_data: Optional trade data (if not provided, will be loaded from DB)
            
        Returns:
            True if registration succeeded, False otherwise
        """
        logger.info(f"Registering trade {trade_id} for monitoring")
        
        # If trade data is not provided, load it from the database
        if not trade_data and self.db:
            try:
                trade_data = await self.db.get_trade(trade_id)
            except Exception as e:
                logger.error(f"Error loading trade {trade_id} from database: {e}", exc_info=True)
                return False
                
        if not trade_data:
            logger.error(f"Cannot register trade {trade_id}: No trade data provided or available")
            return False
            
        # Create a Trade object from the data (for compatibility with existing methods)
        try:
            trade = Trade.from_db_record(trade_data)
        except Exception as e:
            logger.error(f"Error creating Trade object for {trade_id}: {e}", exc_info=True)
            # Fallback: create minimal Trade object
            trade = Trade(
                trade_id=trade_id,
                user_id=trade_data.get("user_id", "unknown"),
                decision_id=trade_data.get("decision_id", "unknown"),
                exchange=trade_data.get("exchange", "unknown"),
                symbol=trade_data.get("symbol", "unknown"),
                direction=trade_data.get("direction", "long"),
                trade_status=TradeStatus.OPEN,
                created_at=datetime.utcnow().isoformat()
            )
            
        # Store Trade object
        self.active_trades[trade_id] = trade
        
        # Emit event
        self.event_bus.emit(Event.create(
            EventType.TRADE_REGISTERED,
            trade_id=trade_id,
            user_id=trade.user_id,
            details={"symbol": trade.symbol}
        ))
        
        return True
    
    async def unregister_trade(self, trade_id: str):
        """
        Unregister a trade from monitoring.
        
        Args:
            trade_id: ID of the trade to unregister
            
        Returns:
            True if unregistration succeeded, False otherwise
        """
        if trade_id in self.active_trades:
            logger.info(f"Unregistering trade {trade_id} from monitoring")
            
            # Get user_id before removing
            user_id = self.active_trades[trade_id].user_id
            
            # Remove from active trades
            del self.active_trades[trade_id]
            
            # Emit event
            self.event_bus.emit(Event.create(
                EventType.TRADE_UNREGISTERED,
                trade_id=trade_id,
                user_id=user_id
            ))
            
            return True
        else:
            logger.warning(f"Attempted to unregister trade {trade_id} that is not being monitored")
            return False
    
    async def notify_adjustment(self, trade_id: str, adjustment_details: Dict):
        """
        Update trade data after an adjustment.
        
        Args:
            trade_id: ID of the trade to update
            adjustment_details: Details of the adjustment
            
        Returns:
            True if update succeeded, False otherwise
        """
        if trade_id not in self.active_trades:
            logger.warning(f"Adjustment notification for trade {trade_id} that is not being monitored")
            return False
            
        try:
            # Update trade data with adjusted values
            trade = self.active_trades[trade_id]
            
            # Update stop loss and take profit if provided
            if "stop_loss" in adjustment_details:
                trade.stop_loss = adjustment_details["stop_loss"]
                
            if "take_profit" in adjustment_details:
                trade.take_profit = adjustment_details["take_profit"]
                
            # Update last updated timestamp
            trade.last_updated = datetime.utcnow().isoformat()
            
            # Emit event
            self.event_bus.emit(Event.create(
                EventType.TRADE_UPDATED,
                trade_id=trade_id,
                user_id=trade.user_id,
                details={"adjustment": adjustment_details}
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing adjustment for trade {trade_id}: {e}", exc_info=True)
            return False
    
    def get_active_trades(self) -> Dict[str, Trade]:
        """
        Get a dictionary of all active trades.
        
        Returns:
            Dictionary of trade_id -> Trade objects
        """
        return self.active_trades.copy()
    
    def get_trade_status(self, trade_id: str) -> Optional[Trade]:
        """
        Get the current status of a trade.
        
        Args:
            trade_id: ID of the trade to get status for
            
        Returns:
            Trade object or None if not found
        """
        return self.active_trades.get(trade_id)
    
    async def _load_active_trades_from_db(self):
        """
        Load active trades from the database.
        
        This should be called on startup to initialize the
        active trades tracking.
        """
        if not self.db:
            logger.warning("No database connection available for loading active trades")
            return
            
        try:
            logger.info("Loading active trades from database")
            
            # Query database for active trades - use the engine's user_id
            active_trades = await self.db.get_active_trades(user_id=self.user_id, trade_status="open")
            
            # Register each trade
            count = 0
            for trade_data in active_trades:
                trade_id = trade_data.get("trade_id")
                if trade_id and await self.register_trade(trade_id, trade_data):
                    count += 1
                    
            logger.info(f"Loaded {count} active trades from database")
            
        except Exception as e:
            logger.error(f"Error loading active trades from database: {e}", exc_info=True)
    
    async def _monitor_positions_loop(self):
        """
        Main loop for monitoring positions of active trades.
        
        This continuously polls the exchange for position updates,
        checks for stop loss / take profit conditions, and updates
        the database with current trade status.
        """
        try:
            logger.info("Starting position monitoring loop")
            
            # Emit event
            self.event_bus.emit(Event.create(EventType.POSITION_POLLING_STARTED))
            
            while self._running and not self._stop_event.is_set():
                # Monitor active trades
                await self._poll_positions()
                
                # Wait for the next polling interval or until stopped
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.config.polling_interval
                    )
                except asyncio.TimeoutError:
                    # Timeout means polling interval elapsed, continue with next iteration
                    pass
                    
        except asyncio.CancelledError:
            logger.info("Position monitoring task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in position monitoring loop: {e}", exc_info=True)
            
            # Emit event
            self.event_bus.emit(Event.create(
                EventType.POSITION_POLLING_FAILED,
                details={"error": str(e)}
            ))
            
            # Try to restart the monitoring loop if still running
            if self._running and not self._stop_event.is_set():
                logger.info("Restarting position monitoring loop after error")
                self._polling_task = asyncio.create_task(
                    self._monitor_positions_loop(),
                    name="ExecutionService_Monitor_Restart"
                )
    
    async def _poll_positions(self):
        """
        Poll exchange for position updates for all active trades.
        
        This checks the current state of positions on the exchange
        and updates the in-memory trade objects as well as the database.
        """
        try:
            # Skip polling if there are no active trades
            if not self.active_trades:
                return
                
            logger.debug(f"Polling {len(self.active_trades)} active trades for position updates")
            
            # Group trades by exchange for more efficient polling
            trades_by_exchange = {}
            for trade_id, trade in self.active_trades.items():
                exchange = trade.exchange
                if exchange not in trades_by_exchange:
                    trades_by_exchange[exchange] = []
                trades_by_exchange[exchange].append((trade_id, trade))
                
            # Poll each exchange
            for exchange, trades in trades_by_exchange.items():
                # Fetch all positions for this exchange in a single call
                try:
                    # Ensure connection
                    await self.ccxt_adapter.ensure_connected()
                    
                    # Fetch positions
                    positions = await self.ccxt_adapter.call_tool("fetch_positions", {})
                    
                    # Check each trade on this exchange
                    for trade_id, trade in trades:
                        # Find matching position
                        position = self._find_position_for_trade(positions, trade)
                        
                        if position:
                            # Position found - update trade data
                            await self._update_trade_with_position(trade_id, trade, position)
                        else:
                            # No position found - handle potential exit
                            await self._handle_missing_position(trade_id, trade)
                            
                except Exception as e:
                    logger.error(f"Error polling positions for exchange {exchange}: {e}", exc_info=True)
                    
                    # Emit event for exchange polling failure
                    self.event_bus.emit(Event.create(
                        EventType.POSITION_POLLING_FAILED,
                        details={"exchange": exchange, "error": str(e)}
                    ))
                    
        except Exception as e:
            logger.error(f"Error in position polling: {e}", exc_info=True)
    
    def _find_position_for_trade(self, positions: List[Dict], trade: Trade) -> Optional[Dict]:
        """
        Find the position object for a trade in the positions list.
        
        Args:
            positions: List of position objects from the exchange
            trade: Trade object to find position for
            
        Returns:
            Position object or None if not found
        """
        # Skip if positions is not a list or is empty
        if not isinstance(positions, list) or not positions:
            return None
            
        # Get symbol from trade
        trade_symbol = trade.symbol
        
        # Try to find exact match
        for position in positions:
            if not isinstance(position, dict):
                continue
                
            position_symbol = position.get("symbol")
            
            if position_symbol == trade_symbol:
                # Check if position has size
                size = float(position.get("contracts", 0) or position.get("size", 0) or 0)
                
                if abs(size) > 0:
                    return position
                    
        # Try with symbol mapping if direct match not found
        mapped_symbol = self.ccxt_adapter.map_symbol(trade_symbol)
        
        if mapped_symbol != trade_symbol:
            for position in positions:
                if not isinstance(position, dict):
                    continue
                    
                position_symbol = position.get("symbol")
                
                if position_symbol == mapped_symbol:
                    # Check if position has size
                    size = float(position.get("contracts", 0) or position.get("size", 0) or 0)
                    
                    if abs(size) > 0:
                        return position
                        
        # No matching position found
        return None
    
    async def _update_trade_with_position(self, trade_id: str, trade: Trade, position: Dict):
        """
        Update trade data with position information from the exchange.
        
        Args:
            trade_id: ID of the trade to update
            trade: Trade object to update
            position: Position object from the exchange
        """
        try:
            # Extract position details
            position_size = float(position.get("contracts", 0) or position.get("size", 0) or 0)
            current_price = float(position.get("markPrice", 0) or position.get("entryPrice", 0) or 0)
            unrealized_pnl = float(position.get("unrealizedPnl", 0) or 0)
            liquidation_price = position.get("liquidationPrice")
            if liquidation_price:
                liquidation_price = float(liquidation_price)
                
            # Update trade object
            trade.position_size = position_size
            trade.current_price = current_price
            trade.unrealized_pnl = unrealized_pnl
            if liquidation_price:
                trade.liquidation_price = liquidation_price
                
            # Update last updated timestamp
            trade.last_updated = datetime.utcnow().isoformat()
            
            # Update database if available
            if self.db:
                await self._update_db_with_status(trade_id, trade)
                
            # Check for stop loss / take profit
            if not trade.exit_triggered:
                exit_triggered = await self._check_exit_conditions(trade_id, trade, current_price)
                
                if exit_triggered:
                    trade.exit_triggered = True
                    
            # Emit event
            self.event_bus.emit(Event.create(
                EventType.TRADE_UPDATED,
                trade_id=trade_id,
                user_id=trade.user_id,
                details={
                    "current_price": current_price,
                    "position_size": position_size,
                    "unrealized_pnl": unrealized_pnl
                }
            ))
            
        except Exception as e:
            logger.error(f"Error updating trade {trade_id} with position data: {e}", exc_info=True)
    
    async def _handle_missing_position(self, trade_id: str, trade: Trade):
        """
        Handle case where a position is not found on the exchange.
        
        This could happen if:
        1. The position was closed externally
        2. The position was liquidated
        3. There's a temporary API issue
        
        Args:
            trade_id: ID of the trade to handle
            trade: Trade object to handle
        """
        # Skip if exit already triggered
        if trade.exit_triggered:
            return
            
        # Check if the trade was recently created (within 60 seconds)
        if trade.created_at:
            try:
                created_at = datetime.fromisoformat(trade.created_at.rstrip('Z'))
                now = datetime.utcnow()
                seconds_since_creation = (now - created_at).total_seconds()
                
                # If position was just created, it might not be visible yet
                if seconds_since_creation < 60:
                    logger.debug(f"Position for trade {trade_id} not found, but was created recently ({seconds_since_creation:.1f}s ago). Ignoring.")
                    return
            except (ValueError, TypeError):
                # Invalid datetime format, proceed with missing position check
                pass
                
        # Position should exist but was not found - consider it closed
        logger.warning(f"Position for trade {trade_id} not found on exchange. Marking as closed.")
        
        # Emit event
        self.event_bus.emit(Event.create(
            EventType.POSITION_NOT_FOUND,
            trade_id=trade_id,
            user_id=trade.user_id,
            details={"symbol": trade.symbol}
        ))
        
        # Update trade status to CLOSED
        trade.trade_status = TradeStatus.CLOSED
        trade.closed_at = datetime.utcnow().isoformat()
        
        # Update database if available
        if self.db:
            await self._update_db_with_status(trade_id, trade, force_closed=True)
            
        # Remove from active trades
        await self.unregister_trade(trade_id)
    
    async def _check_exit_conditions(self, trade_id: str, trade: Trade, current_price: float) -> bool:
        """
        Check if stop loss or take profit conditions are met.
        
        Args:
            trade_id: ID of the trade to check
            trade: Trade object to check
            current_price: Current price of the trading pair
            
        Returns:
            True if exit was triggered, False otherwise
        """
        # Skip if no stop loss or take profit set
        if trade.stop_loss is None and trade.take_profit is None:
            return False
            
        # Skip if exit already triggered
        if trade.exit_triggered:
            return False
            
        # Check stop loss
        sl_triggered = False
        if trade.stop_loss is not None:
            if trade.direction == "long" and current_price <= trade.stop_loss:
                sl_triggered = True
                logger.info(f"Stop loss triggered for trade {trade_id} at price {current_price} (SL: {trade.stop_loss})")
            elif trade.direction == "short" and current_price >= trade.stop_loss:
                sl_triggered = True
                logger.info(f"Stop loss triggered for trade {trade_id} at price {current_price} (SL: {trade.stop_loss})")
                
        # Check take profit
        tp_triggered = False
        if trade.take_profit is not None:
            if trade.direction == "long" and current_price >= trade.take_profit:
                tp_triggered = True
                logger.info(f"Take profit triggered for trade {trade_id} at price {current_price} (TP: {trade.take_profit})")
            elif trade.direction == "short" and current_price <= trade.take_profit:
                tp_triggered = True
                logger.info(f"Take profit triggered for trade {trade_id} at price {current_price} (TP: {trade.take_profit})")
                
        # Handle exit if triggered
        if sl_triggered or tp_triggered:
            # Create exit intent
            exit_reason = "stop_loss" if sl_triggered else "take_profit"
            
            # Emit event
            self.event_bus.emit(Event.create(
                EventType.TRADE_EXIT_TRIGGERED,
                trade_id=trade_id,
                user_id=trade.user_id,
                details={
                    "reason": exit_reason,
                    "trigger_price": current_price,
                    "reference_price": trade.stop_loss if sl_triggered else trade.take_profit
                }
            ))
            
            # Execute exit
            await self._execute_auto_exit(trade_id, trade, exit_reason, current_price)
            
            return True
            
        return False
    
    async def _execute_auto_exit(
        self, 
        trade_id: str,
        trade: Trade,
        exit_reason: str,
        current_price: float
    ):
        """
        Execute an automatic exit for a trade.
        
        Args:
            trade_id: ID of the trade to exit
            trade: Trade object to exit
            exit_reason: Reason for exit ("stop_loss" or "take_profit")
            current_price: Current price triggering the exit
        """
        try:
            logger.info(f"Executing automatic {exit_reason} exit for trade {trade_id}")
            
            # Prepare exit order parameters
            symbol = trade.symbol
            side = "sell" if trade.direction == "long" else "buy"
            position_size = trade.position_size or 0.001  # Use a small default if size unknown
            
            # Create market exit order
            exit_call = {
                "tool": "create_order",
                "parameters": {
                    "symbol": symbol,
                    "side": side,
                    "type": "market",
                    "amount": abs(position_size),
                    "reduce_only": True,
                    "client_order_id": f"autoexit-{exit_reason}-{trade_id[:8]}"
                }
            }
            
            # Execute the exit order
            execution_result = await self.ccxt_adapter.call_tool(
                exit_call["tool"],
                exit_call["parameters"]
            )
            
            # Check if exit was successful
            if isinstance(execution_result, dict) and "id" in execution_result:
                logger.info(f"Successfully executed {exit_reason} exit for trade {trade_id}")
                
                # Update trade in memory
                trade.trade_status = TradeStatus.CLOSED
                trade.closed_at = datetime.utcnow().isoformat()
                trade.exit_order_id = execution_result["id"]
                
                # Update profit/loss
                if current_price and trade.entry_price:
                    if trade.direction == "long":
                        trade.profit_loss = (current_price - trade.entry_price) * trade.position_size
                    else:
                        trade.profit_loss = (trade.entry_price - current_price) * trade.position_size
                        
                # Update database
                if self.db:
                    await self._update_db_with_status(trade_id, trade, force_closed=True)
                    
                # Unregister from active trades
                await self.unregister_trade(trade_id)
                
            else:
                # Exit failed - log but keep trade active
                error_msg = execution_result.get("error", "Unknown error") if isinstance(execution_result, dict) else str(execution_result)
                logger.error(f"Failed to execute {exit_reason} exit for trade {trade_id}: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error executing auto exit for trade {trade_id}: {e}", exc_info=True)
    
    async def _update_db_with_status(self, trade_id: str, trade: Trade, force_closed: bool = False):
        """
        Update the database with current trade status.
        
        Args:
            trade_id: ID of the trade to update
            trade: Trade object to update in DB
            force_closed: Whether to force status to CLOSED
        """
        if not self.db:
            return
            
        try:
            # Convert Trade object to a DB record
            db_record = trade.to_db_record()
            
            # Force status to CLOSED if requested
            if force_closed:
                db_record["trade_status"] = TradeStatus.CLOSED.value
                if "closed_at" not in db_record or not db_record["closed_at"]:
                    db_record["closed_at"] = datetime.utcnow().isoformat()
                    
            # Ensure last_updated is set
            if "last_updated" not in db_record or not db_record["last_updated"]:
                db_record["last_updated"] = datetime.utcnow().isoformat()
                
            # Update database
            await self.db.update_trade(trade_id, db_record)
            
            # Create trade update record for position history
            update_record = {
                "trade_id": trade_id,
                "user_id": trade.user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "price": trade.current_price,
                "unrealized_pnl": trade.unrealized_pnl,
                "position_size": trade.position_size,
                "update_type": "force_closed" if force_closed else "periodic"
            }
            
            # Log position update
            if hasattr(self.db, "log_position_update"):
                await self.db.log_position_update(trade_id, update_record)
                
        except Exception as e:
            logger.error(f"Error updating database for trade {trade_id}: {e}", exc_info=True)
    
    def _check_execution_success(self, execution_results: Dict) -> bool:
        """
        Check if execution was successful by examining MCP results.
        
        Args:
            execution_results: Dictionary with MCP execution results
            
        Returns:
            True if execution was successful, False otherwise
        """
        # No results means failure
        if not execution_results or "results" not in execution_results:
            return False
            
        results = execution_results.get("results", [])
        
        # Check each result for errors
        for result in results:
            # Skip if no result or tool
            if not isinstance(result, dict):
                continue
                
            # Check for error field
            if result.get("error"):
                return False
                
            # Check result field for errors
            result_data = result.get("result")
            if isinstance(result_data, dict) and result_data.get("error"):
                return False
                
        return True
    
    def _extract_error_messages(self, execution_results: Dict) -> str:
        """
        Extract error messages from execution results.
        
        Args:
            execution_results: Dictionary with MCP execution results
            
        Returns:
            String with error messages
        """
        error_msgs = []
        
        if not execution_results or "results" not in execution_results:
            return "No execution results returned"
            
        results = execution_results.get("results", [])
        
        # Check each result for errors
        for result in results:
            # Skip if no result or tool
            if not isinstance(result, dict):
                continue
                
            # Extract error from error field
            if result.get("error"):
                error_msgs.append(f"{result.get('tool', 'Unknown tool')}: {result.get('error')}")
                
            # Extract error from result field
            result_data = result.get("result")
            if isinstance(result_data, dict) and result_data.get("error"):
                error_msgs.append(f"{result.get('tool', 'Unknown tool')}: {result_data.get('error')}")
                
        if not error_msgs:
            return "Unknown execution error"
            
        return "; ".join(error_msgs)