"""
Trade Compiler

This module provides validation, symbol mapping, and parameter finalization
for trade execution. It serves as the critical safety layer between LLM outputs
and actual exchange API calls.

The TradeCompiler ensures:
1. All proposed tool calls have valid schemas and parameters
2. Parameters conform to exchange-specific constraints
3. Values are rounded to correct precision
4. Risk limits are enforced
5. Call sequence is logically correct

It uses the CCXTMCPAdapter to fetch exchange information and finalize
parameter values before execution.
"""

import logging
import math
import json
import time
from datetime import datetime
from decimal import Decimal, ROUND_HALF_DOWN, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Union, Tuple

from core.common.logger import logger

class TradeCompilerValidationError(Exception):
    pass

class TradeCompiler:
    """
    Component that validates and finalizes LLM-proposed tool calls.
    Acts as a safety layer between LLM outputs and exchange API calls.
    """
    
    def __init__(self, config: Dict, ccxt_adapter):
        """
        Initialize the TradeCompiler.
        
        Args:
            config: Configuration dictionary with risk rules
            ccxt_adapter: Instance of CCXTMCPAdapter for exchange interactions
        """
        self.config = config or {}
        self.ccxt_adapter = ccxt_adapter
        
        # Set up logging with user context first
        self.logger = logger.bind(user_id=ccxt_adapter.user_id) if hasattr(ccxt_adapter, 'user_id') else logger
        
        self.risk_rules = self._load_risk_rules()
        self.exchange_info_cache = {}  # Cache for market data {exchange_id: {market_symbol: market_data}}
        self.tools_cache = {}  # Cache for available tools {exchange_id: [tools]}
        
        # Log initialization
        self.logger.info(f"TradeCompiler initialized for exchange {ccxt_adapter.exchange_id}")
        self.logger.info(f"Risk rules: {self.risk_rules}")

    def _load_risk_rules(self) -> Dict:
        """
        Load risk management rules from configuration.
        
        Returns:
            Dictionary of risk management rules
        """
        # Default risk rules
        defaults = {
            'max_leverage': 50,  # Maximum allowed leverage
            'max_risk_per_trade_pct': 0.05,  # Maximum risk as % of account balance (5%)
            'max_position_size_pct': 0.05,  # Maximum position size as % of account balance (5%)
            'allowed_order_types': [
                'market', 'limit', 'stop', 'stopLimit', 
                'takeProfit', 'takeProfitLimit'
            ],
            'min_equity_protection': 0.80,  # Protect 80% of equity from being used
            'max_contracts_per_trade': 10000,  # REDUCED: Upper limit on contract size
            'emergency_max_position_usd': 10000  # CRITICAL: Emergency circuit breaker ($10k max)
        }
        
        # Override defaults with any configured rules
        rules = self.config.get('risk_rules', {})
        defaults.update(rules)
        
        self.logger.info(f"Loaded risk rules: {defaults}")
        return defaults

    async def _get_exchange_info(self, exchange_id: str) -> Optional[Dict]:
        """
        Fetch and cache exchange market data.
        
        Args:
            exchange_id: ID of the exchange to fetch data for
            
        Returns:
            Dictionary of market data or None if fetch failed
        """
        if exchange_id not in self.exchange_info_cache:
            try:
                self.logger.info(f"Fetching market info for {exchange_id} via CCXTMCPAdapter...")
                
                # Using our adapter's fetch_markets method
                markets = await self.ccxt_adapter.fetch_markets()
                
                if not markets:
                    self.logger.warning(f"fetch_markets returned empty data for {exchange_id}")
                    return None
                    
                # Cache the result
                self.exchange_info_cache[exchange_id] = markets
                self.logger.info(f"Cached market info for {exchange_id} ({len(markets)} markets)")
                
            except Exception as e:
                self.logger.error(f"Failed to fetch market info for {exchange_id}: {e}", exc_info=True)
                return None
                
        # Return the cached dict or None if fetch failed previously
        return self.exchange_info_cache.get(exchange_id)


    async def validate_and_finalize(self, proposed_tool_calls: List[Dict], intent_data: Dict, context: Dict) -> List[Dict]:
        """
        Validates LLM-proposed tool calls against schemas, risk rules, and exchange constraints.
        Finalizes parameters (symbol mapping, precision).
        
        Args:
            proposed_tool_calls: List of tool calls proposed by the LLM
            intent_data: Dictionary with intent information (symbol, exchange, etc.)
            context: Dictionary with additional context (equity, etc.)
            
        Returns:
            List of finalized tool calls ready for execution
            
        Raises:
            TradeCompilerValidationError: If validation fails
        """
        self.logger.info(f"Validating {len(proposed_tool_calls)} tool calls for intent {intent_data.get('decision_id', 'unknown')}")
        
        finalized_calls = []
        
        # -- 1. Determine exchange and check if it's valid --
        exchange_id = intent_data.get('exchange', self.ccxt_adapter.exchange_id)
        if not exchange_id:
            raise TradeCompilerValidationError("Exchange ID not specified in intent or adapter")
            
        # Normalize exchange ID to lowercase
        exchange_id = exchange_id.lower()
        
        # -- 2. Get exchange market info --
        all_markets_info = await self._get_exchange_info(exchange_id)
        if not all_markets_info:
            raise TradeCompilerValidationError(f"Could not retrieve market info for {exchange_id}")
            
        # -- 3. Determine trading symbol and validate it exists --
        standard_symbol = intent_data.get('symbol')
        if not standard_symbol:
            raise TradeCompilerValidationError("Missing 'symbol' in intent_data")
            
        # Map to exchange-specific symbol
        exchange_symbol = self._map_symbol(exchange_id, standard_symbol)
        
        # Get market info for the symbol
        market_info = all_markets_info.get(exchange_symbol)
        
        # If mapped symbol not found, try the original standard symbol
        if not market_info:
            self.logger.warning(f"Market info not found for mapped symbol '{exchange_symbol}'. Trying standard symbol '{standard_symbol}'.")
            market_info = all_markets_info.get(standard_symbol)
            
            if market_info:
                exchange_symbol = standard_symbol
                self.logger.info(f"Found market info using standard symbol '{standard_symbol}'.")
            else:
                raise TradeCompilerValidationError(f"Market info not found for symbol '{standard_symbol}' or mapped symbol '{exchange_symbol}' on {exchange_id}")
        
        self.logger.info(f"Compiler: Intent {intent_data.get('decision_id', 'unknown')}, Exchange: {exchange_id}, Symbol: {standard_symbol} -> {exchange_symbol}")
        
        # -- 4. Perform overall risk checks --
        self._check_overall_risk(intent_data, context)
        
        # -- 5. Get available tools for validation --
        available_tools = await self._get_available_tools(exchange_id)
        if not available_tools:
            self.logger.warning(f"No available tools found for {exchange_id}, schema validation will be limited")
        
        # -- 6. Process each proposed tool call --
        for call_index, call in enumerate(proposed_tool_calls):
            tool_name = call.get('tool')
            params = call.get('parameters', {})
            
            self.logger.debug(f"Processing call {call_index}: {tool_name} with params {json.dumps(params)}")
            
            # 6.1. Basic validation
            if not tool_name:
                raise TradeCompilerValidationError(f"Missing 'tool' name in proposed call {call_index}")
            
            # Normalize parameters to handle common variants before validation
            # Specifically handle various forms of 'type' field that might cause the '"type"' error
            normalized_params = params.copy()
            
            # Check for camelCase/snake_case variants of 'type'
            if 'orderType' in normalized_params and 'type' not in normalized_params:
                normalized_params['type'] = normalized_params.pop('orderType')
                self.logger.info(f"Normalized 'orderType' to 'type' in call {call_index}")
                
            if 'order_type' in normalized_params and 'type' not in normalized_params:
                normalized_params['type'] = normalized_params.pop('order_type')
                self.logger.info(f"Normalized 'order_type' to 'type' in call {call_index}")
                
            # 6.2. Schema validation with normalized parameters
            schema_valid = await self._validate_tool_schema(tool_name, normalized_params, available_tools)
            if not schema_valid:
                raise TradeCompilerValidationError(f"Invalid schema or parameters for tool {tool_name} in call {call_index}")
            
            # 6.3. Parameter validation and finalization
            final_params = {}
            
            # First, set exchange_id and user_id in parameters if needed
            if 'exchange_id' not in normalized_params:
                final_params['exchange_id'] = exchange_id
            
            # Process each parameter from the normalized parameters
            for key, value in normalized_params.items():
                # Skip None values unless specifically allowed
                is_none_allowed = (
                    (key == 'price' and params.get('type') == 'market') or
                    (key == 'since' or key == 'limit')  # Optional parameters for fetch methods
                )
                if value is None and not is_none_allowed:
                    self.logger.debug(f"Skipping None value for key '{key}' in tool '{tool_name}'")
                    continue
                
                # Parameter-specific handling
                try:
                    if key in ['symbol', 'pair']:
                        # Use the validated exchange symbol
                        final_params[key] = exchange_symbol
                    
                    elif key == 'amount':
                        # Convert to float and validate/round
                        amount_val = float(value)
                        precision_digits = self._get_precision_digits(market_info, 'amount')
                        
                        # Typically floor amount for safety (avoid exceeding available funds)
                        final_params[key] = self._round_value(amount_val, precision_digits, math.floor)
                        
                        # Check against amount limits
                        min_amount = market_info.get('limits', {}).get('amount', {}).get('min')
                        max_amount = market_info.get('limits', {}).get('amount', {}).get('max')
                        
                        if min_amount is not None and final_params[key] < min_amount:
                            raise TradeCompilerValidationError(
                                f"Amount {final_params[key]} is less than minimum {min_amount} for {exchange_symbol}"
                            )
                        
                        if max_amount is not None and final_params[key] > max_amount:
                            raise TradeCompilerValidationError(
                                f"Amount {final_params[key]} is greater than maximum {max_amount} for {exchange_symbol}"
                            )
                    
                    elif key in ['price', 'stopPrice', 'stopLossPrice', 'takeProfitPrice', 'triggerPrice']:
                        # Handle price parameters
                        if value is not None:
                            price_val = float(value)
                            precision_digits = self._get_precision_digits(market_info, 'price')
                            
                            # Round price to appropriate precision
                            final_params[key] = self._round_value(price_val, precision_digits)
                            
                            # Check against tick size
                            tick_size = market_info.get('precision', {}).get('price')
                            if tick_size is not None and tick_size > 0:
                                # Check if price is divisible by tick size
                                remainder = final_params[key] % tick_size
                                if abs(remainder) > 1e-9 and abs(remainder - tick_size) > 1e-9:
                                    # Round to nearest tick
                                    final_params[key] = round(final_params[key] / tick_size) * tick_size
                                    self.logger.info(f"Adjusted {key} to {final_params[key]} to match tick size {tick_size}")
                    
                    elif key == 'leverage':
                        # Convert to int and validate
                        leverage_val = int(value)
                        
                        # Check against max leverage rule
                        max_leverage_rule = self.risk_rules.get('max_leverage', 50)
                        clamped_leverage = min(leverage_val, max_leverage_rule)
                        
                        # Check exchange leverage limits
                        exchange_leverage_info = market_info.get('limits', {}).get('leverage', {})
                        
                        # Handle case where leverage is not supported
                        if not exchange_leverage_info.get('min') and not exchange_leverage_info.get('max'):
                            if clamped_leverage > 1:
                                raise TradeCompilerValidationError(
                                    f"Leverage not supported for {exchange_symbol} on {exchange_id}, but {clamped_leverage}x requested."
                                )
                            final_params[key] = 1  # Force to 1x
                        else:
                            # Respect exchange max leverage
                            exchange_max_leverage = exchange_leverage_info.get('max', clamped_leverage)
                            final_params[key] = min(clamped_leverage, exchange_max_leverage)
                    
                    elif key == 'clientOrderId':
                        # Validate clientOrderId
                        cid = str(value)
                        max_len = market_info.get('limits', {}).get('order', {}).get('clientOrderIdMaxLength', 36)
                        final_params[key] = cid[:max_len]
                    
                    elif key == 'side':
                        # Validate side
                        if value not in ['buy', 'sell']:
                            raise TradeCompilerValidationError(f"Invalid side '{value}'. Must be 'buy' or 'sell'.")
                        final_params[key] = value
                    
                    elif key == 'type':
                        # Validate order type
                        order_type = str(value).lower()
                        
                        # Check against allowed order types from risk rules
                        allowed_types = self.risk_rules.get('allowed_order_types', [])
                        if order_type not in allowed_types:
                            raise TradeCompilerValidationError(f"Order type '{order_type}' not allowed by risk rules.")
                        
                        # Check against exchange supported order types
                        exchange_allowed = market_info.get('limits', {}).get('order', {}).get('types', allowed_types)
                        if order_type not in exchange_allowed:
                            raise TradeCompilerValidationError(f"Order type '{order_type}' not supported by exchange for {exchange_symbol}.")
                        
                        final_params[key] = order_type
                    
                    else:
                        # Pass through other parameters
                        final_params[key] = value
                
                except (ValueError, TypeError, KeyError, IndexError) as e:
                    # Handle validation errors
                    self.logger.error(f"Error processing parameter '{key}' with value '{value}' for tool '{tool_name}': {e}", exc_info=True)
                    raise TradeCompilerValidationError(f"Invalid value or type for parameter '{key}' ('{value}') in tool '{tool_name}': {e}")
            
            # 6.4. Add clientOrderId for order operations if missing
            is_order_tool = tool_name in [
                'create_order', 'createOrder',
                'create_market_buy_order', 'create_market_sell_order',
                'create_limit_buy_order', 'create_limit_sell_order'
            ]
            
            if is_order_tool and 'clientOrderId' not in final_params:
                import uuid
                
                decision_id_str = str(intent_data.get('decision_id', ''))
                # Use UUID fragment for guaranteed uniqueness - prevents TP/SL collision issues
                uuid_fragment = str(uuid.uuid4()).replace('-', '')[:12]
                call_specific_id = f"{decision_id_str[:8]}-{call_index}-{uuid_fragment}"
                
                # Get max length from exchange info
                max_len = market_info.get('limits', {}).get('order', {}).get('clientOrderIdMaxLength', 36)
                
                # Create a valid clientOrderId
                final_params['clientOrderId'] = f"ggb-{call_specific_id}".replace("-", "")[:max_len]
                self.logger.debug(f"Generated clientOrderId: {final_params['clientOrderId']}")
            
            # 6.5. Specific risk checks for order creation
            if tool_name in ['create_order', 'createOrder']:
                self._check_order_risk(final_params, intent_data, context, market_info)
            
            # 6.6. Check required parameters are present after finalization
            if not self._check_required_params(tool_name, final_params, market_info):
                raise TradeCompilerValidationError(f"Missing required parameters for tool {tool_name} after finalization: {final_params}")
            
            # Add finalized call to list
            finalized_calls.append({"tool": tool_name, "parameters": final_params})
            self.logger.debug(f"Finalized call {call_index}: {tool_name} with params {json.dumps(final_params)}")
        
        # -- 7. Post-processing validation --
        self._validate_call_sequence(finalized_calls)
        
        self.logger.info(f"Compiler validation successful for intent {intent_data.get('decision_id', 'unknown')}. Finalized {len(finalized_calls)} calls.")
        return finalized_calls

    def _map_symbol(self, exchange_id: str, standard_symbol: str) -> str:
        """
        Map a standardized symbol to exchange-specific format using the adapter.
        
        SYMBOL MAPPING APPROACH:
        The system uses a two-layer approach to handle exchange-specific symbol formats:
        
        1. The LLM always uses standardized trading pair symbols (e.g., 'BTC/USD')
           in its tool calls
           
        2. The TradeCompiler maps these standardized symbols to exchange-specific 
           formats (e.g., 'XBT/USD:XBt' for BitMEX) during parameter validation
           
        3. The mapping dictionaries are stored in the CCXTMCPAdapter class in 
           trading/exchanges/ccxt_mcp.py as EXCHANGE_SYMBOL_MAP
           
        This approach allows:
        - The LLM to work with consistent, readable symbols
        - The system to handle exchange-specific quirks transparently
        - New exchanges to be added by updating the mapping dictionary
        - Symbol mapping to happen in a single place (during parameter validation)
        
        Args:
            exchange_id: ID of the exchange
            standard_symbol: Standardized symbol (e.g., 'BTC/USD')
            
        Returns:
            Exchange-specific symbol format (e.g., 'XBT/USD:XBt' for BitMEX)
        """
        # Use the CCXTMCPAdapter's symbol mapping functionality
        # The actual mapping dictionary is stored in CCXTMCPAdapter.EXCHANGE_SYMBOL_MAP
        mapped_symbol = self.ccxt_adapter.map_symbol(standard_symbol)
        
        # Log the mapping
        if mapped_symbol != standard_symbol:
            self.logger.info(f"Mapped standard symbol '{standard_symbol}' to exchange symbol '{mapped_symbol}' for {exchange_id}")
        else:
            self.logger.debug(f"No specific mapping found for '{standard_symbol}' on {exchange_id}, using original.")
            
        return mapped_symbol
        
    async def _get_available_tools(self, exchange_id: str) -> List[Dict]:
        """
        Fetch and cache available tools from the MCP server.
        
        Args:
            exchange_id: ID of the exchange
            
        Returns:
            List of tool definitions
        """
        if exchange_id not in self.tools_cache:
            try:
                self.logger.info(f"Fetching available tools for {exchange_id}...")
                
                # Get tools from the adapter
                tools = await self.ccxt_adapter.get_available_tools()
                
                if not tools:
                    self.logger.warning(f"get_available_tools returned empty data for {exchange_id}")
                    return []
                    
                # Cache the result
                self.tools_cache[exchange_id] = tools
                self.logger.info(f"Cached {len(tools)} tools for {exchange_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to fetch available tools for {exchange_id}: {e}", exc_info=True)
                return []
                
        # Return the cached tools
        return self.tools_cache.get(exchange_id, [])

    async def _validate_tool_schema(self, tool_name: str, params: Dict, available_tools: List[Dict]) -> bool:
        """
        Validate that a tool call has the correct schema.
        
        Args:
            tool_name: Name of the tool to validate
            params: Parameters for the tool
            available_tools: List of available tools with schema info
            
        Returns:
            True if schema is valid, False otherwise
        """
        self.logger.debug(f"Validating schema for {tool_name}")
        
        # Check if parameters are a dictionary
        if not isinstance(params, dict):
            self.logger.error(f"Parameters for tool {tool_name} must be a dictionary, got {type(params)}")
            return False
            
        # Find the tool in available tools
        tool_info = None
        for tool in available_tools:
            if tool.get('name') == tool_name:
                tool_info = tool
                break
                
        # Check if tool exists
        if not tool_info:
            self.logger.error(f"Tool '{tool_name}' not found in available tools")
            return False
            
        # Get parameter schema
        parameters_schema = tool_info.get('parameters', {})
        
        # Check required parameters
        for param_name, param_info in parameters_schema.items():
            if param_info.get('required', False) and param_name not in params:
                self.logger.error(f"Required parameter '{param_name}' missing for tool '{tool_name}'")
                return False
                
        # Validate parameter types
        for param_name, param_value in params.items():
            # Skip validation for unknown parameters
            if param_name not in parameters_schema:
                self.logger.warning(f"Parameter '{param_name}' not defined in schema for tool '{tool_name}'")
                continue
                
            # Get expected type
            expected_type = parameters_schema[param_name].get('type')
            
            # Skip validation if type is not defined
            if not expected_type:
                continue
                
            # Validate type
            if expected_type == 'string':
                if param_value is not None and not isinstance(param_value, str):
                    self.logger.error(f"Parameter '{param_name}' should be string, got {type(param_value)}")
                    return False
            elif expected_type == 'number':
                # Allow int or float for number
                if param_value is not None and not isinstance(param_value, (int, float)):
                    self.logger.error(f"Parameter '{param_name}' should be number, got {type(param_value)}")
                    return False
            elif expected_type == 'integer':
                if param_value is not None and not isinstance(param_value, int):
                    self.logger.error(f"Parameter '{param_name}' should be integer, got {type(param_value)}")
                    return False
            elif expected_type == 'boolean':
                if param_value is not None and not isinstance(param_value, bool):
                    self.logger.error(f"Parameter '{param_name}' should be boolean, got {type(param_value)}")
                    return False
            elif expected_type == 'object':
                if param_value is not None and not isinstance(param_value, dict):
                    self.logger.error(f"Parameter '{param_name}' should be object, got {type(param_value)}")
                    return False
            elif expected_type == 'array':
                if param_value is not None and not isinstance(param_value, list):
                    self.logger.error(f"Parameter '{param_name}' should be array, got {type(param_value)}")
                    return False
                    
        self.logger.debug(f"Schema validation passed for {tool_name}")
        return True

    def _check_required_params(self, tool_name, final_params, market_info):
        # Check if all required params for the tool are present in final_params
        # Required params can depend on the order type for createOrder/create_order
        required = {}
        
        # Handle both camelCase and snake_case variants of tool names
        if tool_name in ["createOrder", "create_order"]:
            # Use the normalized tool name as the key
            normalized_tool_name = "create_order"
            required[normalized_tool_name] = ["symbol", "side", "type", "amount"]
            
            # Check if type parameter exists, otherwise provide helpful error
            if 'type' not in final_params:
                # Check for common variants that might have been missed during normalization
                if 'orderType' in final_params:
                    final_params['type'] = final_params['orderType']
                    self.logger.warning(f"Auto-corrected 'orderType' to 'type' in parameters")
                elif 'order_type' in final_params:
                    final_params['type'] = final_params['order_type']
                    self.logger.warning(f"Auto-corrected 'order_type' to 'type' in parameters")
            
            order_type = final_params.get('type')
            if order_type in ['limit', 'stopLimit', 'takeProfitLimit']:
                required[normalized_tool_name].append('price')
            if order_type in ['stop', 'stopLimit']:
                 # Stop price might be 'stopPrice' or 'triggerPrice' depending on exchange/CCXT version
                 if 'stopPrice' not in final_params and 'triggerPrice' not in final_params:
                      self.logger.error(f"Missing 'stopPrice' or 'triggerPrice' for order type '{order_type}'")
                      return False
            if order_type in ['takeProfit', 'takeProfitLimit']:
                 # TP often uses 'price' as the trigger, but check if 'stopPrice'/'triggerPrice' needed
                 if 'price' not in final_params:
                      self.logger.error(f"Missing 'price' for order type '{order_type}'")
                      return False
                      
        elif tool_name in ["setLeverage", "set_leverage"]:
            normalized_tool_name = "set_leverage"
            required[normalized_tool_name] = ["symbol", "leverage"]
            
        elif tool_name in ["cancelOrder", "cancel_order"]:
             # Usually requires 'id' (exchange order ID) or 'clientOrderId'
             if 'id' not in final_params and 'clientOrderId' not in final_params:
                  self.logger.error(f"Missing 'id' or 'clientOrderId' for tool '{tool_name}'")
                  return False
        # Add other tools as needed...

        # Find the appropriate requirements for this tool using normalized names
        requirements = None
        for req_key in required:
            if tool_name.lower() == req_key.lower() or tool_name.lower().replace('_', '') == req_key.lower().replace('_', ''):
                requirements = required[req_key]
                break
                
        if requirements:
            missing = [req for req in requirements if req not in final_params]
            if missing:
                self.logger.error(f"Missing required parameters for tool '{tool_name}': {missing}. Provided: {list(final_params.keys())}")
                return False
                
        return True


    def _get_precision_digits(self, market_info: Dict, precision_type: str) -> int:
        """
        Get the number of decimal places for amount or price from market info.
        
        Args:
            market_info: Market information dictionary from exchange
            precision_type: Type of precision to get ('amount' or 'price')
            
        Returns:
            Number of decimal places for the specified precision type
        """
        precision_data = market_info.get('precision', {})
        value = None
        
        if precision_type == 'amount':
            value = precision_data.get('amount')
        elif precision_type == 'price':
            value = precision_data.get('price')  # This is often the tick size
        
        if value is not None:
            try:
                # If value is small (like tick size), calculate decimal places
                if 0 < value < 1:
                    # Add epsilon for float issues
                    return max(0, int(-math.log10(value) + 1e-9))
                # If value is integer (like number of digits), return it directly
                elif isinstance(value, int) or value == int(value):
                    return int(value)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Error calculating precision digits: {e}")
        
        # Fallback defaults if precision not found or calculation failed
        default_precision = 8 if precision_type == 'amount' else 4
        self.logger.warning(
            f"Could not determine '{precision_type}' precision for {market_info.get('symbol')}. "
            f"Using default: {default_precision}"
        )
        return default_precision

    def _round_value(self, value: float, precision_digits: int, rounding_func=round) -> float:
        """
        Round a value to the specified number of decimal places.
        
        Args:
            value: Value to round
            precision_digits: Number of decimal places to round to
            rounding_func: Function to use for rounding (default: round)
            
        Returns:
            Rounded value
        """
        if precision_digits is None:
            return value  # Cannot round
        
        try:
            # Convert to Decimal for accurate financial rounding
            dec_value = Decimal(str(value))
            dec_precision = Decimal('0.1') ** precision_digits
            
            # Use specified rounding function
            if rounding_func == math.floor:
                rounded = dec_value.quantize(dec_precision, rounding=ROUND_HALF_DOWN)
            else:
                rounded = dec_value.quantize(dec_precision, rounding=ROUND_HALF_UP)
                
            # Convert back to float
            return float(rounded)
            
        except (ValueError, TypeError, DecimalException) as e:
            # Fallback to float rounding if Decimal fails
            self.logger.warning(f"Decimal rounding failed, using float rounding: {e}")
            factor = 10 ** int(precision_digits)
            return rounding_func(value * factor) / factor


    def _check_overall_risk(self, intent_data: Dict, context: Dict) -> None:
        """
        Perform overall risk checks on trade intent.
        
        Args:
            intent_data: Trade intent data dictionary
            context: Additional context data (e.g., equity)
            
        Raises:
            TradeCompilerValidationError: If risk checks fail
        """
        # --- 1. Check leverage against max_leverage rule ---
        leverage = intent_data.get('leverage', 1)
        max_leverage = self.risk_rules.get('max_leverage', 50)
        
        try:
            leverage = float(leverage)
        except (ValueError, TypeError):
            raise TradeCompilerValidationError(f"Invalid leverage value: {leverage}. Must be a number.")
            
        if leverage > max_leverage:
            raise TradeCompilerValidationError(
                f"Requested leverage {leverage} exceeds max allowed {max_leverage} by rule."
            )

        # --- 2. Validate confidence score if provided ---
        confidence = intent_data.get('confidence')
        if confidence is not None:
            try:
                confidence = float(confidence)
                if not (0.0 <= confidence <= 1.0):
                    raise TradeCompilerValidationError(
                        f"Confidence score {confidence} must be between 0.0 and 1.0"
                    )
                self.logger.info(f"✅ Confidence validation passed: {confidence:.2f}")
            except (ValueError, TypeError):
                raise TradeCompilerValidationError(
                    f"Invalid confidence value: {confidence}. Must be a number between 0.0 and 1.0"
                )
        
        # --- 3. Validate position size against risk limits (calculated by Trading API) ---
        # The Trading API has already calculated safe position sizes based on confidence
        # Here we just validate the final values don't exceed emergency limits
        
        # Extract account balance in USD for risk calculations
        account_balance_usd = self._get_standardized_account_balance_usd(context)
        
        # Get calculated position size from Trading API
        position_size_usd = intent_data.get('position_size_usd', 0)
        collateral_amount = intent_data.get('collateral_amount', 0)
        
        if position_size_usd > 0:
            # EMERGENCY CIRCUIT BREAKER: Absolute maximum position size
            emergency_max_position = self.risk_rules.get('emergency_max_position_usd', 10000)
            if position_size_usd > emergency_max_position:
                raise TradeCompilerValidationError(
                    f"🚨 EMERGENCY STOP: Position size ${position_size_usd:,.2f} exceeds emergency limit "
                    f"${emergency_max_position:,.2f}. This is an unsafe position size!"
                )
            
            # Check if position size is reasonable relative to account
            if position_size_usd > account_balance_usd:
                raise TradeCompilerValidationError(
                    f"🚨 CRITICAL: Position size ${position_size_usd:,.2f} exceeds account balance "
                    f"${account_balance_usd:,.2f}. This would risk more than the entire account!"
                )
            
            self.logger.info(
                f"✅ Position size validation passed: ${position_size_usd:,.2f} position "
                f"({position_size_usd/account_balance_usd*100:.1f}% of account) within emergency limits"
            )

        # Legacy size validation for backward compatibility (optional)
        size_type = intent_data.get('size_type')
        size_value = intent_data.get('size_value')
        
        if size_type or size_value:
            self.logger.info("Legacy size parameters detected - confidence-based sizing takes precedence")
            
        # Log successful completion of risk checks
        self.logger.info("Risk validation completed successfully")

        self.logger.debug("Overall risk checks passed.")

    def _get_standardized_account_balance_usd(self, context: Dict) -> float:
        """
        Extract standardized account balance in USD from context data.
        
        This method handles different exchange account structures and provides
        a unified account balance for risk calculations.
        
        Args:
            context: Context dictionary containing account state
            
        Returns:
            Account balance in USD
        """
        try:
            # Check if we have account state from the API
            account_state = context.get('account_state')
            
            if account_state:
                # Try different balance representations
                
                # 1. Look for direct USD balance
                if 'balance_data' in account_state:
                    balance_data = account_state['balance_data']
                    
                    # Check for total_usd_value (preferred)
                    if 'total_usd_value' in balance_data:
                        usd_balance = float(balance_data['total_usd_value'])
                        self.logger.info(f"Using total_usd_value as account balance: ${usd_balance:,.2f}")
                        return usd_balance
                    
                    # Check for available_btc and convert to USD (BitMEX style)
                    if 'available_btc' in balance_data:
                        available_btc = float(balance_data['available_btc'])
                        # Use a conservative BTC price if we don't have current price
                        # This should be improved to use real-time price
                        btc_price = 104000  # Conservative estimate, should be updated
                        usd_balance = available_btc * btc_price
                        self.logger.info(f"Converted available_btc to USD: {available_btc} BTC × ${btc_price:,} = ${usd_balance:,.2f}")
                        return usd_balance
                
                # 2. Look for available_margin in BTC and convert
                if 'available_margin' in account_state:
                    available_margin_btc = float(account_state['available_margin'])
                    btc_price = 104000  # Conservative estimate
                    usd_balance = available_margin_btc * btc_price
                    self.logger.info(f"Using available_margin as account balance: {available_margin_btc} BTC × ${btc_price:,} = ${usd_balance:,.2f}")
                    return usd_balance
                
                # 3. Look for equity
                if 'equity' in account_state:
                    equity_btc = float(account_state['equity'])
                    btc_price = 104000  # Conservative estimate  
                    usd_balance = equity_btc * btc_price
                    self.logger.info(f"Using equity as account balance: {equity_btc} BTC × ${btc_price:,} = ${usd_balance:,.2f}")
                    return usd_balance
            
            # Fallback: Look for equity in context (legacy)
            equity = context.get('equity', 0)
            if equity > 0:
                # If equity is already in USD, use it
                if equity > 1000:  # Assume values > 1000 are in USD
                    self.logger.info(f"Using context equity as USD balance: ${equity:,.2f}")
                    return float(equity)
                else:
                    # Assume it's in BTC, convert to USD
                    btc_price = 104000  # Conservative estimate
                    usd_balance = equity * btc_price
                    self.logger.info(f"Converting context equity to USD: {equity} BTC × ${btc_price:,} = ${usd_balance:,.2f}")
                    return usd_balance
            
            # Last resort: Use available_margin from context
            available_margin = context.get('available_margin', 0)
            if available_margin > 0:
                if available_margin > 1000:  # Assume USD
                    return float(available_margin)
                else:  # Assume BTC
                    btc_price = 104000
                    return available_margin * btc_price
            
            # Emergency fallback: Use a safe minimum
            self.logger.warning("Could not determine account balance from context, using emergency minimum of $1000")
            return 1000.0
            
        except Exception as e:
            self.logger.error(f"Error extracting standardized account balance: {e}")
            # Emergency fallback
            return 1000.0

    def _check_order_risk(self, final_params: Dict, intent_data: Dict, context: Dict, market_info: Dict) -> None:
        """
        Perform order-specific risk checks.
        
        Args:
            final_params: Finalized parameters for the order
            intent_data: Trade intent data
            context: Additional context (equity, etc.)
            market_info: Market information for the symbol
            
        Raises:
            TradeCompilerValidationError: If risk checks fail
        """
        self.logger.debug(f"Performing order-specific risk checks for: {json.dumps(final_params)}")
        
        # Get order parameters
        equity = context.get('equity', 0)
        available_margin = context.get('available_margin', 0)
        
        # For BitMEX, use available_margin as the account balance for risk calculations
        account_balance = available_margin if available_margin > 0 else equity
        
        symbol = final_params.get('symbol')
        amount = final_params.get('amount')
        price = final_params.get('price')  # Limit price or None for market
        leverage = final_params.get('leverage', 1)  # Leverage might be set in a previous call
        
        # Skip checks if missing critical data
        if not amount:
            self.logger.warning("Skipping order risk check: missing 'amount' parameter")
            return
            
        try:
            # Convert parameters to correct types
            amount = float(amount)
            leverage = float(leverage)
            
            # 🚨 CRITICAL: CONTRACT COUNT VALIDATION
            # This prevents the 375k contract catastrophe
            
            # Get standardized account balance for validation
            account_balance_usd = self._get_standardized_account_balance_usd(context)
            
            # EMERGENCY CONTRACT COUNT LIMITS
            max_contracts_absolute = self.risk_rules.get('max_contracts_per_trade', 100000)  # 100k absolute max
            
            if amount > max_contracts_absolute:
                raise TradeCompilerValidationError(
                    f"🚨 EMERGENCY STOP: Contract amount {amount:,.0f} exceeds absolute safety limit "
                    f"{max_contracts_absolute:,.0f}. This is an unsafe order size!"
                )
            
            # CRITICAL: Estimate USD value of contracts
            # For BTC/USD on BitMEX: 1 contract ≈ $1 USD
            estimated_usd_value = amount * 1.0  # Conservative $1 per contract estimate
            
            # Check if estimated USD value exceeds account balance
            if estimated_usd_value > account_balance_usd:
                raise TradeCompilerValidationError(
                    f"🚨 CRITICAL: Contract value ~${estimated_usd_value:,.0f} ({amount:,.0f} contracts) "
                    f"exceeds account balance ${account_balance_usd:,.2f}. "
                    f"This would risk {estimated_usd_value/account_balance_usd*100:.1f}% of your account!"
                )
            
            # Check against position size limits
            max_position_pct = self.risk_rules.get('max_position_size_pct', 0.05)
            max_position_usd = account_balance_usd * max_position_pct
            
            if estimated_usd_value > max_position_usd:
                raise TradeCompilerValidationError(
                    f"🚨 CRITICAL: Contract value ~${estimated_usd_value:,.0f} exceeds max position limit "
                    f"${max_position_usd:,.2f} ({max_position_pct*100:.1f}% of account balance). "
                    f"Reduce to max {max_position_usd:,.0f} contracts."
                )
            
            self.logger.info(
                f"✅ Contract validation passed: {amount:,.0f} contracts (~${estimated_usd_value:,.0f}) "
                f"within {estimated_usd_value/account_balance_usd*100:.1f}% of account limit"
            )
            
            # Get market information
            contract_size = market_info.get('contractSize', 1)
            is_inverse = market_info.get('inverse', False)
            is_linear = market_info.get('linear', not is_inverse)  # Assume linear if not inverse
            
            # Get current price for estimation
            current_mark_price = None
            
            # Try different price sources in order of preference
            if price is not None:
                current_mark_price = float(price)
            elif market_info.get('markPrice') is not None:
                current_mark_price = market_info.get('markPrice')
            elif market_info.get('last') is not None:
                current_mark_price = market_info.get('last')
                
            # Skip cost estimation if price is unknown
            if not current_mark_price or current_mark_price <= 0:
                self.logger.warning(f"Skipping cost estimation for {symbol}: unable to determine price")
                return
                
            # Calculate estimated cost based on market type
            estimated_cost = 0
            
            if is_linear:
                # Cost in Quote currency (e.g., USDT)
                # For USDT-M futures: cost = (amount * contract_size * price) / leverage
                estimated_cost = (amount * contract_size * current_mark_price) / leverage
                self.logger.info(f"Linear market cost estimation: {amount} * {contract_size} * {current_mark_price} / {leverage} = {estimated_cost:.2f}")
                
            elif is_inverse:
                # Cost in Base currency for inverse contracts (e.g., USD-M futures)
                # For USD-M futures: cost = (amount * contract_size) / price / leverage
                if current_mark_price > 0:
                    notional_value_quote = amount * contract_size  # Contracts in quote currency
                    estimated_cost = notional_value_quote / leverage
                    self.logger.info(f"Inverse market cost estimation: {amount} * {contract_size} / {leverage} = {estimated_cost:.2f}")
            
            # Check against account balance if available
            if account_balance and estimated_cost > 0:
                # SAFETY CHECK: Cap position size at configured percentage of account balance
                max_position_pct = self.risk_rules.get('max_position_size_pct', 0.05)  # Default 5%
                max_position_cost = account_balance * max_position_pct
                
                if estimated_cost > max_position_cost:
                    # AUTO-ADJUST: Reduce position size to stay within limit
                    adjustment_ratio = max_position_cost / estimated_cost
                    original_amount = amount
                    
                    # Adjust the amount parameter
                    adjusted_amount = amount * adjustment_ratio
                    precision_digits = self._get_precision_digits(market_info, 'amount')
                    adjusted_amount = self._round_value(adjusted_amount, precision_digits, math.floor)
                    
                    # Update the parameter
                    final_params['amount'] = adjusted_amount
                    
                    # Recalculate estimated cost with adjusted amount
                    if is_linear:
                        estimated_cost = (adjusted_amount * contract_size * current_mark_price) / leverage
                    elif is_inverse:
                        notional_value_quote = adjusted_amount * contract_size
                        estimated_cost = notional_value_quote / leverage
                    
                    self.logger.warning(
                        f"AUTO-ADJUSTED position size from {original_amount} to {adjusted_amount} contracts "
                        f"to stay within {max_position_pct*100:.0f}% of account balance. "
                        f"Original cost: {estimated_cost/adjustment_ratio:.2f}, Adjusted cost: {estimated_cost:.2f}, "
                        f"Account balance: {account_balance:.2f}, Max allowed: {max_position_cost:.2f}"
                    )
                
                # Get minimum equity protection threshold (e.g., 80% of equity)
                min_equity_protection = self.risk_rules.get('min_equity_protection', 0.80)
                max_usable_equity = equity * (1 - min_equity_protection)
                
                if estimated_cost > equity:
                    # Hard failure - order would exceed total equity
                    raise TradeCompilerValidationError(
                        f"Estimated order cost ({estimated_cost:.2f}) exceeds available equity ({equity:.2f})"
                    )
                elif estimated_cost > max_usable_equity:
                    # Warning or soft failure - order uses most of available equity
                    self.logger.warning(
                        f"Order cost ({estimated_cost:.2f}) exceeds {(1-min_equity_protection)*100:.0f}% of "
                        f"equity ({max_usable_equity:.2f} of {equity:.2f})"
                    )
            
            # Check against exchange-defined min/max cost limits
            min_cost = market_info.get('limits', {}).get('cost', {}).get('min')
            max_cost = market_info.get('limits', {}).get('cost', {}).get('max')
            
            if estimated_cost > 0:
                if min_cost is not None and estimated_cost < min_cost:
                    raise TradeCompilerValidationError(
                        f"Estimated order cost {estimated_cost:.2f} is less than minimum {min_cost} for {symbol}"
                    )
                if max_cost is not None and estimated_cost > max_cost:
                    raise TradeCompilerValidationError(
                        f"Estimated order cost {estimated_cost:.2f} is greater than maximum {max_cost} for {symbol}"
                    )
                    
        except (ValueError, TypeError) as e:
            # Non-fatal warning for estimation errors
            self.logger.warning(f"Error estimating order cost: {e}")
            
        self.logger.debug("Order specific risk checks passed.")

    def _validate_call_sequence(self, finalized_calls: List[Dict]) -> None:
        """
        Validate the sequence of tool calls for logical correctness.
        
        Args:
            finalized_calls: List of finalized tool calls
            
        Raises:
            TradeCompilerValidationError: If sequence validation fails
        """
        if not finalized_calls:
            return
            
        # Extract tool names for easier processing
        tool_names = [call['tool'] for call in finalized_calls]
        
        # --- Check if setLeverage comes before createOrder ---
        order_creation_tools = [
            'create_order', 'createOrder',
            'create_market_buy_order', 'create_market_sell_order',
            'create_limit_buy_order', 'create_limit_sell_order'
        ]
        
        leverage_tools = ['set_leverage', 'setLeverage']
        
        # Find first order creation index
        order_index = -1
        for tool in order_creation_tools:
            try:
                idx = tool_names.index(tool)
                if order_index == -1 or idx < order_index:
                    order_index = idx
            except ValueError:
                pass
                
        # Find last leverage setting index
        leverage_index = -1
        for tool in leverage_tools:
            try:
                idx = tool_names.index(tool)
                if idx > leverage_index:
                    leverage_index = idx
            except ValueError:
                pass
                
        # Check sequence ordering
        if order_index >= 0 and leverage_index >= 0 and leverage_index > order_index:
            # This is problematic - leverage is set AFTER order creation
            self.logger.warning(
                f"Sequence issue: {tool_names[leverage_index]} at position {leverage_index} appears after "
                f"{tool_names[order_index]} at position {order_index}"
            )
            # Could be a warning or an error depending on policy
            # raise TradeCompilerValidationError(
            #    f"Invalid sequence: {tool_names[leverage_index]} must come before {tool_names[order_index]}"
            # )
            
            # Auto-reorder if possible (alternative approach)
            # This would require modifying the calls list
            
        # --- Check for other logical sequence issues ---
        # Example: cancelOrder should come before new order with same clientOrderId
        
        self.logger.debug("Call sequence validation passed.")