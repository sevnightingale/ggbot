import asyncio
import logging
from datetime import datetime, timezone # Use timezone aware datetime
import math
# Assume CCXTMCPAdapter, TradeCompiler classes exist and are imported
# Assume logger is configured

logger = logging.getLogger(__name__)

# Placeholder - replace with actual DB interaction logic using an async DB library (e.g., asyncpg, databases)
class MockDb:
    # Simulate DB storage
    _trades = {}
    _updates = []
    _errors = []
    _rejections = []

    async def get_trade(self, trade_id, user_id):
        logger.debug(f"DB: Getting trade {trade_id} for user {user_id}")
        trade = self._trades.get(trade_id)
        # In real DB, filter by user_id too
        return trade.copy() if trade and trade.get('user_id') == user_id else None

    async def get_active_trades(self, user_id, trade_status='open'):
         logger.debug(f"DB: Getting active trades for user {user_id} with trade_status {trade_status}")
         active = [t.copy() for t in self._trades.values() if t.get('user_id') == user_id and t.get('trade_status') == trade_status]
         logger.debug(f"DB: Found {len(active)} active trades")
         return active

    async def create_trade(self, record):
         trade_id = record['trade_id']
         logger.debug(f"DB: Creating trade {trade_id}")
         if trade_id in self._trades:
              logger.error(f"DB: Trade ID {trade_id} already exists!")
              return None # Or raise error
         self._trades[trade_id] = record.copy()
         return trade_id

    async def update_trade(self, trade_id, update_data):
         logger.debug(f"DB: Updating trade {trade_id} with {update_data}")
         if trade_id in self._trades:
              # Handle adjustments array update carefully
              if 'adjustments' in update_data and isinstance(update_data['adjustments'], list):
                   # Assumes update_data['adjustments'] contains the *new* entry to append
                   if 'adjustments' not in self._trades[trade_id] or not isinstance(self._trades[trade_id]['adjustments'], list):
                        self._trades[trade_id]['adjustments'] = []
                   self._trades[trade_id]['adjustments'].extend(update_data['adjustments']) # Append new adjustment(s)
                   del update_data['adjustments'] # Remove from main update dict

              self._trades[trade_id].update(update_data)
              logger.debug(f"DB: Trade {trade_id} updated state: {self._trades[trade_id]}")

         else:
              logger.error(f"DB: Cannot update trade {trade_id}, not found.")


    async def log_position_update(self, trade_id, data):
         update_record = {
             "update_id": str(uuid.uuid4()),
             "trade_id": trade_id,
             "user_id": self._trades.get(trade_id, {}).get('user_id'), # Get user_id from trade
             "timestamp": datetime.now(timezone.utc).isoformat(),
             **data # Add fields like price, pnl, size
         }
         logger.debug(f"DB: Logging position update for {trade_id}: {data}")
         self._updates.append(update_record)

    async def log_rejection(self, data):
         logger.debug(f"DB: Logging rejection {data}")
         self._rejections.append(data)

    async def log_error(self, data):
         logger.debug(f"DB: Logging error {data}")
         self._errors.append(data)


db = MockDb() # Use Mock DB instance

class TradeManager:
    def __init__(self, user_id, config, ccxt_adapter, trade_compiler, trading_engine_ref=None): # Added engine ref
        self.user_id = user_id
        self.config = config
        self.ccxt_adapter = ccxt_adapter
        self.trade_compiler = trade_compiler # Needed to validate its own calls
        self.trading_engine_ref = trading_engine_ref # Reference to call process_decision_intent
        self.active_trades = {} # trade_id -> trade_info dict (loaded from DB)
        self.polling_task = None
        self.polling_interval = config.get('polling_interval_seconds', 60) # More specific name
        self._stop_event = asyncio.Event() # For graceful shutdown

    async def set_trading_engine_ref(self, engine_ref):
        # Allow setting the reference after initialization if needed (e.g., circular dependency)
        self.trading_engine_ref = engine_ref
        logger.info("TradingEngine reference set in TradeManager.")

    async def _load_active_trades_from_db(self):
        logger.info(f"Loading active trades from database for user {self.user_id}...")
        try:
            active_db_trades = await db.get_active_trades(user_id=self.user_id, trade_status='open')
            count = 0
            new_active_trades = {}
            for trade in active_db_trades:
                trade_id = trade.get('trade_id')
                if trade_id:
                    new_active_trades[trade_id] = trade
                    count += 1
            self.active_trades = new_active_trades # Replace cache with fresh data
            logger.info(f"Loaded {count} active trades.")
        except Exception as e:
            logger.error(f"Failed to load active trades from DB: {e}", exc_info=True)


    async def start(self):
        self._stop_event.clear()
        await self._load_active_trades_from_db() # Load state on start
        if not self.polling_task or self.polling_task.done():
            # Ensure polling interval is valid
            if self.polling_interval <= 0:
                 logger.error(f"Invalid polling_interval_seconds: {self.polling_interval}. Must be > 0. Polling disabled.")
                 return
            self.polling_task = asyncio.create_task(self._polling_loop(), name=f"TradeManagerPolling-{self.user_id}")
            logger.info(f"TradeManager polling task started for user {self.user_id} (Interval: {self.polling_interval}s).")
        else:
             logger.warning(f"TradeManager polling task already running for user {self.user_id}.")


    async def stop(self):
        logger.info(f"Stopping TradeManager for user {self.user_id}...")
        self._stop_event.set() # Signal loop to stop
        if self.polling_task and not self.polling_task.done():
            logger.info("Attempting to cancel polling task...")
            self.polling_task.cancel()
            try:
                # Wait for the task to acknowledge cancellation
                await asyncio.wait_for(self.polling_task, timeout=5.0)
                logger.info("Polling task successfully cancelled.")
            except asyncio.CancelledError:
                logger.info("Polling task was cancelled.")
            except asyncio.TimeoutError:
                 logger.warning("Polling task did not cancel within timeout.")
            except Exception as e:
                 logger.error(f"Error during polling task shutdown: {e}", exc_info=True)
            self.polling_task = None
        self.active_trades.clear() # Clear cache on stop
        logger.info(f"TradeManager stopped for user {self.user_id}.")

    async def register_trade(self, trade_id):
        # Load trade from DB and add to self.active_trades if status is open
        logger.info(f"Attempting to register trade {trade_id} for user {self.user_id}...")
        try:
            trade_info = await db.get_trade(trade_id=trade_id, user_id=self.user_id)
            if trade_info and trade_info.get('trade_status') == 'open':
                # Add or update the trade info in the cache
                self.active_trades[trade_id] = trade_info
                logger.info(f"Registered/Updated trade {trade_id} for tracking.")
                return True
            else:
                trade_status = trade_info.get('trade_status') if trade_info else 'Not Found'
                logger.warning(f"Could not register trade {trade_id}. DB Status: '{trade_status}'")
                # Ensure it's removed if status is not open
                if trade_id in self.active_trades:
                     del self.active_trades[trade_id]
                return False
        except Exception as e:
             logger.error(f"Error registering trade {trade_id} from DB: {e}", exc_info=True)
             return False


    async def unregister_trade(self, trade_id):
        if trade_id in self.active_trades:
            del self.active_trades[trade_id]
            logger.info(f"Unregistered trade {trade_id} from tracking.")
            return True
        logger.debug(f"Attempted to unregister trade {trade_id}, but it was not being tracked.")
        return False

    async def get_cached_status(self, trade_id):
         """ Returns the cached status dictionary for a trade, or None """
         return self.active_trades.get(trade_id)


    async def get_position_status(self, trade_id):
        """
        Fetches the current position status from the exchange for a given trade_id.
        Handles validation of the fetch call and parsing of the result.
        Returns a dictionary with 'status' ('success', 'error', 'closed') and data/message.
        """
        if trade_id not in self.active_trades:
            logger.warning(f"get_position_status called for untracked trade_id: {trade_id}")
            # Try reloading from DB in case it became active recently
            is_now_active = await self.register_trade(trade_id)
            if not is_now_active:
                 return {'status': 'error', 'message': 'Trade not actively tracked or not open'}

        # Get potentially updated trade info from cache
        trade_info = self.active_trades.get(trade_id)
        if not trade_info: # Should not happen if register_trade succeeded, but check anyway
             logger.error(f"Trade info disappeared from cache for {trade_id} after registration.")
             return {'status': 'error', 'message': 'Internal cache error'}

        exchange = trade_info.get('exchange')
        pair = trade_info.get('pair') # Standard pair

        if not exchange or not pair:
             logger.error(f"Missing exchange ('{exchange}') or pair ('{pair}') for trade {trade_id}")
             return {'status': 'error', 'message': 'Trade info incomplete'}

        logger.debug(f"Fetching position status for trade {trade_id} ({exchange}/{pair})")

        try:
            # Prepare the 'fetchPositions' tool call proposal
            # Use a unique decision_id for polling calls for logging/tracing
            internal_intent = {'action': 'fetch_positions', 'symbol': pair, 'exchange': exchange, 'decision_id': f'poll-{trade_id}-{int(datetime.now(timezone.utc).timestamp())}'}
            # Fetch specific symbol if possible, otherwise fetch all (adapter/compiler might handle this)
            # CCXT often requires symbol for fetchPositions on specific exchanges
            proposed_call = [{"tool": "fetchPositions", "parameters": {"symbol": pair}}]

            logger.debug(f"Proposing fetchPositions call for {trade_id}: {proposed_call}")

            # Validate the call (maps symbol, checks if tool allowed etc.)
            validated_calls = await self.trade_compiler.validate_and_finalize(
                proposed_call, internal_intent, {} # Context might include user_id if needed by compiler
            )
            # The compiler should have mapped the symbol if necessary
            exchange_symbol = validated_calls[0]['parameters'].get('symbol')
            if not exchange_symbol:
                 # This indicates a compiler logic error or missing map
                 raise TradeCompilerValidationError("Compiler did not return a symbol in validated call for fetchPositions")

            logger.debug(f"Executing validated fetchPositions for {trade_id} (Exchange Symbol: {exchange_symbol})")
            # Execute validated call via adapter
            mcp_response = await self.ccxt_adapter.execute_batch(validated_calls)
            logger.debug(f"MCP Response for fetchPositions {trade_id}: {mcp_response}")


            # Process MCP response carefully
            positions_result_list = []
            if isinstance(mcp_response, dict) and 'results' in mcp_response and isinstance(mcp_response['results'], list) and len(mcp_response['results']) > 0:
                 call_result = mcp_response['results'][0]
                 if call_result.get('tool') == 'fetchPositions':
                      if isinstance(call_result.get('result'), list):
                           positions_result_list = call_result['result']
                      elif call_result.get('error'):
                           # Handle errors reported by the MCP server itself
                           raise RuntimeError(f"MCP error fetching positions: {call_result['error']}")
                      else:
                           logger.warning(f"Unexpected result format from MCP fetchPositions for {trade_id}: {call_result.get('result')}")
                 else:
                      logger.error(f"Unexpected tool '{call_result.get('tool')}' in MCP response for fetchPositions call {trade_id}")
                      raise RuntimeError("Received MCP response for wrong tool")
            else:
                 logger.error(f"Invalid MCP response structure for fetchPositions {trade_id}: {mcp_response}")
                 raise RuntimeError("Invalid MCP response structure")


            # Find the specific position in the list returned
            position_data = self._find_position_in_results(positions_result_list, exchange_symbol)

            if not position_data:
                 # Position not found in the results from the exchange
                 logger.warning(f"Position for active trade {trade_id} ({exchange_symbol}) not found in fetchPositions result on {exchange}.")
                 # Check DB status again to see if it was closed externally/manually
                 db_status = await self._get_trade_status_from_db(trade_id)
                 if db_status != 'open':
                     logger.info(f"Trade {trade_id} status in DB is '{db_status}'. Unregistering.")
                     await self.unregister_trade(trade_id) # Remove from active polling
                     return {'status': 'closed', 'message': f'Position closed (DB status: {db_status})'}
                 else:
                     # Still marked as open in DB, but not found on exchange. This is problematic.
                     # Possible reasons: Liquidation, manual closure, exchange issue, race condition.
                     logger.error(f"POSITION NOT FOUND: Trade {trade_id} ({exchange_symbol} on {exchange}) is 'open' in DB but position not returned by exchange. Requires investigation!")
                     # Action: Maybe mark trade as errored in DB? Trigger alert?
                     # For now, return error status to polling loop.
                     return {'status': 'error', 'message': 'Position not found on exchange, but DB shows open'}


            # Position found, calculate metrics
            logger.debug(f"Found position data for {trade_id}: {position_data}")
            current_status_metrics = self._calculate_current_metrics(trade_info, position_data)
            return {'status': 'success', **current_status_metrics}

        except TradeCompilerValidationError as e:
             # Errors during the validation phase (symbol mapping, etc.)
             logger.error(f"Compiler error during get_position_status for {trade_id}: {e}", exc_info=True)
             return {'status': 'error', 'message': f"Compiler validation failed: {e}"}
        except Exception as e:
            # Catch other errors (network, MCP execution, parsing, etc.)
            logger.error(f"Generic error fetching position status for {trade_id}: {e}", exc_info=True)
            return {'status': 'error', 'message': f"Failed to fetch status: {e}"}


    async def _polling_loop(self):
        """ Background task that periodically polls exchange for updates on active trades. """
        while not self._stop_event.is_set():
            start_time = asyncio.get_event_loop().time()
            trade_ids_to_poll = list(self.active_trades.keys()) # Copy keys for safe iteration

            if not trade_ids_to_poll:
                 logger.info("No active trades to poll.")
            else:
                logger.info(f"Polling {len(trade_ids_to_poll)} active trades...")
                # Create tasks to fetch status concurrently
                tasks = [asyncio.create_task(self.get_position_status(tid), name=f"poll-{tid}") for tid in trade_ids_to_poll]

                # Wait for all polling tasks to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                for i, result_or_exc in enumerate(results):
                    trade_id = trade_ids_to_poll[i] # Get corresponding trade_id

                    # Check if trade is still supposed to be active before processing result
                    if trade_id not in self.active_trades:
                         logger.debug(f"Trade {trade_id} was unregistered during polling, skipping result processing.")
                         continue

                    trade_info = self.active_trades[trade_id] # Get current info from cache

                    if isinstance(result_or_exc, Exception):
                         logger.error(f"Polling task for trade {trade_id} raised an exception: {result_or_exc}", exc_info=result_or_exc)
                         # Handle exception - maybe increment error count, mark trade as needing attention?
                         self.active_trades[trade_id]['_poll_error_count'] = self.active_trades[trade_id].get('_poll_error_count', 0) + 1
                         # TODO: Add logic to unregister/alert if error count exceeds threshold

                    elif isinstance(result_or_exc, dict):
                         status = result_or_exc.get('status')
                         if status == 'success':
                              # Reset error count on success
                              self.active_trades[trade_id]['_poll_error_count'] = 0
                              # Update DB (trades table current price, trade_updates table)
                              await self._update_db_with_status(trade_id, result_or_exc)
                              # Update local cache *with the fetched data*
                              self.active_trades[trade_id].update(result_or_exc)
                              # Check SL/TP conditions based on the *newly fetched* status
                              await self._check_exit_conditions(trade_id, self.active_trades[trade_id], result_or_exc)
                         elif status == 'closed':
                              logger.info(f"Trade {trade_id} reported as closed during polling, removing from active polling.")
                              # Ensure DB is updated if needed (though get_position_status might have done it)
                              await self._update_trade_status_in_db(trade_id, 'closed')
                              await self.unregister_trade(trade_id)
                         elif status == 'error':
                              logger.warning(f"Polling error status received for trade {trade_id}: {result_or_exc.get('message')}")
                              self.active_trades[trade_id]['_poll_error_count'] = self.active_trades[trade_id].get('_poll_error_count', 0) + 1
                              # TODO: Add logic based on error count
                         else:
                              logger.warning(f"Unknown status '{status}' received for trade {trade_id}: {result_or_exc}")
                    else:
                         logger.error(f"Unexpected result type from polling task for trade {trade_id}: {type(result_or_exc)}")

            # Calculate time elapsed and sleep until next interval
            elapsed = asyncio.get_event_loop().time() - start_time
            sleep_duration = max(0.1, self.polling_interval - elapsed) # Ensure minimum sleep
            logger.info(f"Polling cycle finished in {elapsed:.2f}s. Sleeping for {sleep_duration:.2f}s.")
            try:
                 # Wait for the interval or until stop event is set
                 await asyncio.wait_for(self._stop_event.wait(), timeout=sleep_duration)
                 if self._stop_event.is_set():
                      logger.info("Stop event set, exiting polling loop.")
                      break # Exit loop if stop event is set
            except asyncio.TimeoutError:
                 pass # Timeout reached, continue to next iteration
            except asyncio.CancelledError:
                 logger.info("Polling sleep interrupted by cancellation.")
                 break # Exit loop if cancelled

        logger.info(f"Polling loop stopped for user {self.user_id}.")


    async def _check_exit_conditions(self, trade_id, trade_info, current_status):
        """ Checks if current price hits SL or TP levels defined in trade_info. """
        if not self.trading_engine_ref:
             logger.warning(f"TradingEngine reference not set in TradeManager, cannot trigger auto-exits for {trade_id}.")
             return

        # Ensure we have necessary data
        current_price = current_status.get('current_price')
        sl_price = trade_info.get('stop_loss')
        tp_price = trade_info.get('take_profit')
        direction = trade_info.get('direction')

        # Convert prices to float, handle None carefully
        try:
            current_price_f = float(current_price) if current_price is not None else None
            sl_price_f = float(sl_price) if sl_price is not None else None
            tp_price_f = float(tp_price) if tp_price is not None else None
        except (ValueError, TypeError):
             logger.warning(f"Invalid price format for checking exit conditions on trade {trade_id}. Prices: current={current_price}, sl={sl_price}, tp={tp_price}")
             return

        if current_price_f is None or direction not in ['long', 'short']:
             logger.debug(f"Cannot check exit conditions for {trade_id}, missing current_price or valid direction.")
             return

        exit_reason = None
        trigger_price = current_price_f # Price that triggered the condition

        # Check stop loss
        if sl_price_f is not None:
            if direction == 'long' and current_price_f <= sl_price_f:
                exit_reason = 'stop_loss_hit'
            elif direction == 'short' and current_price_f >= sl_price_f:
                exit_reason = 'stop_loss_hit'

        # Check take profit (only if SL not already hit)
        if exit_reason is None and tp_price_f is not None:
            if direction == 'long' and current_price_f >= tp_price_f:
                exit_reason = 'take_profit_hit'
            elif direction == 'short' and current_price_f <= tp_price_f:
                exit_reason = 'take_profit_hit'

        if exit_reason:
            logger.info(f"Exit condition '{exit_reason}' triggered for trade {trade_id} at price {trigger_price} (SL={sl_price_f}, TP={tp_price_f})")
            # Prevent triggering multiple exits for the same condition using a flag in the cache
            if self.active_trades.get(trade_id, {}).get('_exit_triggered'):
                 logger.info(f"Exit already marked as triggered for {trade_id}, skipping.")
                 return
            # Mark as triggered *before* sending intent
            self.active_trades[trade_id]['_exit_triggered'] = True

            # Generate an exit intent and send it to the TradingEngine
            exit_intent = self._create_exit_intent(trade_id, exit_reason, trigger_price, trade_info)
            logger.info(f"Submitting auto-exit intent to TradingEngine for {trade_id}: {exit_intent}")
            # Use asyncio.create_task to avoid blocking the polling loop
            # Handle potential errors from process_decision_intent if needed
            asyncio.create_task(self.trading_engine_ref.process_decision_intent(exit_intent), name=f"autoexit-{trade_id}")
            # Consider unregistering here or wait for confirmation? Waiting is safer.


    def _create_exit_intent(self, trade_id, reason, trigger_price, trade_info):
         """ Creates the semi-structured intent dict for the TradingEngine """
         decision_id = f'autoexit-{trade_id}-{reason}-{int(datetime.now(timezone.utc).timestamp())}' # Unique ID
         return {
             'decision_id': decision_id,
             'action': 'exit',
             'trade_id': trade_id, # Crucial link back to the trade being closed
             'symbol': trade_info.get('pair'), # Use standard symbol from trade record
             'exchange': trade_info.get('exchange'),
             'reasoning': f"Automatic exit triggered: {reason} at price {trigger_price}",
             'order_type': 'market', # Usually close with market order on SL/TP hit for speed
             # Include other relevant info if needed by LLM/Compiler for exit
             'original_direction': trade_info.get('direction')
         }

    def _find_position_in_results(self, positions_result_list, exchange_symbol):
        """ Finds the position matching the exchange_symbol in the list returned by fetchPositions """
        if not positions_result_list: return None
        logger.debug(f"Searching for symbol '{exchange_symbol}' in {len(positions_result_list)} positions.")
        for pos in positions_result_list:
             if not isinstance(pos, dict):
                  logger.warning(f"Skipping non-dict item in positions list: {pos}")
                  continue
             # CCXT position structure varies slightly but usually has 'symbol' or 'info.symbol'
             pos_symbol = pos.get('symbol', pos.get('info', {}).get('symbol'))
             logger.debug(f"Checking position symbol: '{pos_symbol}'")
             if pos_symbol == exchange_symbol:
                  # Found the position by symbol
                  # Check if position size is non-zero (or close to zero) using 'contracts' or 'size'
                  size_key = 'contracts' if 'contracts' in pos else 'size'
                  try:
                       size_str = pos.get(size_key)
                       if size_str is None:
                            logger.warning(f"Position found for {exchange_symbol} but missing size key ('{size_key}')")
                            return None # Cannot determine if open
                       size = float(size_str)
                  except (ValueError, TypeError):
                       logger.warning(f"Position found for {exchange_symbol} but invalid size value: {pos.get(size_key)}")
                       return None # Cannot determine if open

                  # Use a small tolerance for floating point comparison
                  if abs(size) > 1e-9:
                     logger.debug(f"Found open position for {exchange_symbol} with size {size}.")
                     return pos # Return the full position dictionary
                  else:
                     logger.info(f"Found position for {exchange_symbol} but size is {size}. Treating as closed.")
                     return None # Treat zero size as closed
        logger.debug(f"Symbol '{exchange_symbol}' not found in positions list.")
        return None # Not found


    def _calculate_current_metrics(self, trade_info, position_data):
        """ Extracts metrics from CCXT position data and calculates P/L etc. """
        # Use .get with defaults and careful type conversion
        metrics = {'last_updated': datetime.now(timezone.utc).isoformat()}
        try:
            entry_price_f = float(trade_info.get('entry_price')) if trade_info.get('entry_price') is not None else None
            direction = trade_info.get('direction')

            # --- Extract raw values from position_data ---
            # Prefer 'markPrice' for PnL, fallback to 'lastPrice'
            current_price_str = position_data.get('markPrice', position_data.get('lastPrice'))
            # Size key varies ('contracts' often for derivatives, 'size' might be base/quote) - needs care!
            size_key = 'contracts' if 'contracts' in position_data else 'size'
            position_size_str = position_data.get(size_key)
            unrealized_pnl_str = position_data.get('unrealizedPnl')
            liquidation_price_str = position_data.get('liquidationPrice')

            # --- Convert to float, handle errors ---
            metrics['current_price'] = float(current_price_str) if current_price_str is not None else None
            metrics['position_size'] = float(position_size_str) if position_size_str is not None else None # Note: This might be contracts or base/quote units!
            metrics['unrealized_pnl'] = float(unrealized_pnl_str) if unrealized_pnl_str is not None else None
            metrics['liquidation_price'] = float(liquidation_price_str) if liquidation_price_str is not None and float(liquidation_price_str) > 0 else None # Set to None if 0 or invalid

            # --- Calculate PNL Percentage (basic example) ---
            metrics['pnl_percentage'] = None
            if entry_price_f and entry_price_f != 0 and metrics['current_price'] and direction:
                price_diff = metrics['current_price'] - entry_price_f
                if direction == 'long':
                    metrics['pnl_percentage'] = (price_diff / entry_price_f) * 100
                elif direction == 'short':
                    metrics['pnl_percentage'] = (-price_diff / entry_price_f) * 100

            logger.debug(f"Calculated metrics for trade {trade_info.get('trade_id')}: {metrics}")

        except (ValueError, TypeError, KeyError) as e:
             logger.error(f"Error calculating metrics for trade {trade_info.get('trade_id')}: {e}. Position data: {position_data}", exc_info=True)
             # Return partial data or error indicator? Returning what we have for now.
             metrics.update({'calculation_error': str(e)}) # Add error flag/msg

        return metrics


    async def _update_db_with_status(self, trade_id, status_result):
        # Update 'trades' table (current_price, last_updated) and add record to 'trade_updates'
        logger.debug(f"Updating DB for trade {trade_id} with status: {status_result}")
        try:
            # Data for the main 'trades' table update
            trade_update_data = {
                'current_price': status_result.get('current_price'),
                'last_updated': status_result.get('last_updated', datetime.now(timezone.utc).isoformat()),
                'liquidation_price': status_result.get('liquidation_price')
                # Add other fields like unrealized PNL if needed in main table
            }
            # Filter out None values before updating DB
            trade_update_data = {k: v for k, v in trade_update_data.items() if v is not None}
            if trade_update_data: # Only update if there's data
                 await db.update_trade(trade_id, trade_update_data)

            # Data for the 'trade_updates' history table
            update_log_data = {
                 'price': status_result.get('current_price'),
                 'unrealized_pnl': status_result.get('unrealized_pnl'),
                 'position_size': status_result.get('position_size'),
                 'update_type': 'periodic' # Mark this as a periodic poll update
                 # Add funding rate if available in position data
            }
            # Filter out None values
            update_log_data = {k: v for k, v in update_log_data.items() if v is not None}
            if update_log_data: # Only log if there's data
                 await db.log_position_update(trade_id, update_log_data)

        except Exception as e:
            logger.error(f"Failed to update DB for trade {trade_id} status: {e}", exc_info=True)


    async def _get_trade_status_from_db(self, trade_id):
         # Helper to get just the status field from DB
         try:
             trade = await db.get_trade(trade_id=trade_id, user_id=self.user_id)
             return trade.get('trade_status') if trade else None
         except Exception as e:
             logger.error(f"Failed to get DB status for trade {trade_id}: {e}", exc_info=True)
             return None

    async def _update_trade_status_in_db(self, trade_id, new_status):
         """ Helper to specifically update only the status field in the DB """
         logger.info(f"Updating DB status for trade {trade_id} to '{new_status}'")
         try:
             await db.update_trade(trade_id, {'trade_status': new_status, 'last_updated': datetime.now(timezone.utc).isoformat()})
         except Exception as e:
              logger.error(f"Failed to update DB status for trade {trade_id} to '{new_status}': {e}", exc_info=True)


    async def notify_adjustment(self, trade_id, adjustment_details):
         # Called by TradingEngine after an adjustment is executed
         # Reload trade info from DB to get updated SL/TP etc. in the cache
         logger.info(f"Received notification of adjustment for trade {trade_id}. Reloading info.")
         if trade_id in self.active_trades:
              try:
                   trade_info = await db.get_trade(trade_id=trade_id, user_id=self.user_id)
                   if trade_info:
                        self.active_trades[trade_id] = trade_info # Update cache with latest DB state
                        logger.info(f"Cache updated for adjusted trade {trade_id}.")
                   else:
                        # Trade might have been closed or deleted? Remove from cache.
                        logger.warning(f"Failed to reload trade info for adjusted trade {trade_id}, removing from cache.")
                        await self.unregister_trade(trade_id)
              except Exception as e:
                   logger.error(f"Error reloading trade info after adjustment for {trade_id}: {e}", exc_info=True)


## Exchange Symbol Mapping

The system relies on a standardized symbol format internally (e.g., 'BTC/USD', 'ETH/USDT'). The `TradeCompiler` is responsible for mapping these to the specific format required by each exchange before execution, using a predefined mapping.

```python
# Example mapping - LOAD FROM CONFIGURATION (e.g., YAML file)
# Keys should be lowercase exchange IDs as used by CCXT/config
# Values are dictionaries mapping StandardSymbol -> ExchangeSpecificSymbol
EXCHANGE_SYMBOL_MAP = {
    'bitmex': {
        # Standard : Exchange Specific (Check BitMEX API docs for current symbols)
        'BTC/USD': 'XBTUSD', # Inverse Perpetual often uses XBTUSD
        'BTC/USDT': 'XBTUSDT', # Linear Perpetual
        'ETH/USD': 'ETHUSD', # Inverse Perpetual
        'ETH/USDT': 'ETHUSDT', # Linear Perpetual
    },
    'binance': {
        # Standard : Exchange Specific (Binance uses different symbols for Spot vs Futures)
        # Assuming USD-M Futures (check API docs for exact symbols like BTCUSDT.P or just BTCUSDT)
        'BTC/USD': 'BTCUSD_PERP', # Example for a BTC/USD perp if it exists
        'BTC/USDT': 'BTCUSDT',
        'ETH/USDT': 'ETHUSDT',
        'SOL/USDT': 'SOLUSDT',
    },
    'bybit': {
         # Standard : Exchange Specific (V5 Unified API symbols are generally close to standard)
         'BTC/USD': 'BTCUSD', # Inverse Perpetual
         'BTC/USDT': 'BTCUSDT', # Linear Perpetual
         'ETH/USDT': 'ETHUSDT', # Linear Perpetual
         'SOL/USDT': 'SOLUSDT',
    }
    # Add mappings for other supported exchanges (e.g., kraken, okx, kucoin)
}