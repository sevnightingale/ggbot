"""
Validation Service for the Trading Engine.

This service handles validation of tool calls proposed by the LLM,
including schema validation, risk checks, and parameter finalization.
It serves as a critical safety layer between the LLM-generated tool calls
and the execution service.
"""

import math
import json
import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_DOWN, ROUND_HALF_UP, DecimalException
from typing import Dict, List, Optional, Any, Union, Tuple

from core.common.logger import logger
from trading.engine.model.config import ValidationConfig
from trading.engine.model.intent import Intent
from trading.engine.model.tool_call import ToolCall, ValidatedToolCall
from trading.engine.model.event import Event, EventType


class ValidationError(Exception):
    """Exception raised for validation errors in the ValidationService."""
    pass


class ValidationService:
    """
    Service for validating and finalizing LLM-proposed tool calls.
    
    This service is responsible for:
    1. Validating tool calls against schemas
    2. Enforcing risk management rules
    3. Mapping symbols to exchange-specific formats
    4. Adjusting parameters based on exchange requirements
    5. Finalizing parameters for execution
    """
    
    def __init__(
        self,
        config: ValidationConfig,
        trade_compiler = None,
        event_bus = None
    ):
        """
        Initialize the validation service.
        
        Args:
            config: Configuration for validation rules
            trade_compiler: Optional existing TradeCompiler instance
            event_bus: Optional event bus for emitting events
        """
        self.config = config
        self.trade_compiler = trade_compiler
        self.event_bus = event_bus
        
        logger.info(f"ValidationService initialized with max leverage {config.max_leverage}")
    
    async def validate_tool_calls(
        self,
        tool_calls: List[ToolCall],
        intent_data: Dict,
        context: Dict
    ) -> List[ValidatedToolCall]:
        """
        Validate and finalize tool calls using the TradeCompiler.
        
        Args:
            tool_calls: List of tool calls to validate
            intent_data: Original intent data that generated the tool calls (dict)
            context: Additional context (e.g., equity, positions)
            
        Returns:
            List of validated tool calls
            
        Raises:
            ValidationError: If validation fails
        """
        if not self.trade_compiler:
            logger.error("No trade compiler available for validation")
            raise ValidationError("No trade compiler available for validation")
            
        if not tool_calls:
            logger.warning("No tool calls to validate")
            raise ValidationError("No tool calls to validate")
            
        try:
            # Extract decision_id for logging and events
            decision_id = intent_data.get('decision_id', 'unknown')
            
            # Emit event for validation started
            if self.event_bus:
                self.event_bus.emit(Event.create(
                    EventType.VALIDATION_STARTED,
                    user_id=None,  # Would be set from context if available
                    decision_id=decision_id,
                    details={"call_count": len(tool_calls)}
                ))
            
            # Convert ToolCall objects to dictionaries for the compiler
            raw_calls = []
            for call in tool_calls:
                raw_calls.append({
                    "tool": call.tool,
                    "parameters": call.parameters
                })
                
            # Validate and finalize the calls using the trade compiler
            try:
                validated_raw_calls = await self.trade_compiler.validate_and_finalize(
                    raw_calls,
                    intent_data,  # Pass the raw intent_data dictionary directly
                    context
                )
            except Exception as e:
                logger.error(f"Error validating tool calls: {e}", exc_info=True)
                
                # Emit validation failed event
                if self.event_bus:
                    self.event_bus.emit(Event.create(
                        EventType.VALIDATION_FAILED,
                        user_id=None,  # Would be set from context if available
                        decision_id=decision_id,
                        details={"error": str(e)}
                    ))
                    
                raise ValidationError(f"Compiler validation failed: {e}")
                
            # Convert validated calls back to ValidatedToolCall objects
            validated_calls = []
            for idx, validated_raw in enumerate(validated_raw_calls):
                # Find the corresponding original call
                original_call = tool_calls[idx] if idx < len(tool_calls) else None
                
                # Create ValidatedToolCall object
                validated_call = ValidatedToolCall(
                    tool=validated_raw["tool"],
                    parameters=validated_raw["parameters"],
                    original_call=original_call
                )
                
                validated_calls.append(validated_call)
                
            # Emit validation succeeded event
            if self.event_bus:
                self.event_bus.emit(Event.create(
                    EventType.VALIDATION_SUCCEEDED,
                    user_id=None,  # Would be set from context if available
                    decision_id=decision_id,
                    details={"validated_count": len(validated_calls)}
                ))
                
            return validated_calls
            
        except ValidationError:
            # Re-raise ValidationError to maintain error type
            raise
        except Exception as e:
            logger.error(f"Unexpected error in validation: {e}", exc_info=True)
            
            # Emit validation failed event
            if self.event_bus:
                self.event_bus.emit(Event.create(
                    EventType.VALIDATION_FAILED,
                    user_id=None,  # Would be set from context if available
                    decision_id=intent_data.get('decision_id', 'unknown'),
                    details={"error": str(e)}
                ))
                
            raise ValidationError(f"Validation failed: {e}")
    
    # The following methods could be implemented to provide standalone validation
    # functionality without relying on the TradeCompiler. These would be used if
    # you're not using the existing compiler implementation.
    
    def validate_tool_schema(self, tool_name: str, parameters: Dict, tools_schema: List[Dict]) -> bool:
        """
        Validate that a tool call matches the expected schema.
        
        Args:
            tool_name: Name of the tool to validate
            parameters: Parameters for the tool
            tools_schema: Schema of available tools
            
        Returns:
            True if schema is valid, False otherwise
        """
        # Find the tool schema
        tool_info = None
        for tool in tools_schema:
            if tool.get("name") == tool_name:
                tool_info = tool
                break
                
        if not tool_info:
            logger.error(f"Tool '{tool_name}' not found in schema")
            return False
            
        # Get parameter schemas
        param_schemas = tool_info.get("parameters", {})
        
        # Check required parameters
        for param_name, param_info in param_schemas.items():
            if param_info.get("required", False) and param_name not in parameters:
                logger.error(f"Required parameter '{param_name}' missing for tool '{tool_name}'")
                return False
                
        # Validate parameter types
        for param_name, param_value in parameters.items():
            if param_name not in param_schemas:
                # Unknown parameter - log warning but continue
                logger.warning(f"Unknown parameter '{param_name}' for tool '{tool_name}'")
                continue
                
            # Get expected type
            param_info = param_schemas[param_name]
            expected_type = param_info.get("type")
            
            if not expected_type:
                continue
                
            if expected_type == "string":
                if param_value is not None and not isinstance(param_value, str):
                    logger.error(f"Parameter '{param_name}' should be string, got {type(param_value).__name__}")
                    return False
            elif expected_type == "number":
                if param_value is not None and not isinstance(param_value, (int, float)):
                    logger.error(f"Parameter '{param_name}' should be number, got {type(param_value).__name__}")
                    return False
            elif expected_type == "integer":
                if param_value is not None and not isinstance(param_value, int):
                    logger.error(f"Parameter '{param_name}' should be integer, got {type(param_value).__name__}")
                    return False
            elif expected_type == "boolean":
                if param_value is not None and not isinstance(param_value, bool):
                    logger.error(f"Parameter '{param_name}' should be boolean, got {type(param_value).__name__}")
                    return False
            elif expected_type == "object":
                if param_value is not None and not isinstance(param_value, dict):
                    logger.error(f"Parameter '{param_name}' should be object, got {type(param_value).__name__}")
                    return False
            elif expected_type == "array":
                if param_value is not None and not isinstance(param_value, list):
                    logger.error(f"Parameter '{param_name}' should be array, got {type(param_value).__name__}")
                    return False
                    
        return True
    
    def map_symbol(self, symbol: str, exchange_id: str, symbol_map: Dict) -> str:
        """
        Map a standardized symbol to exchange-specific format.
        
        Args:
            symbol: Standardized symbol (e.g., 'BTC/USD')
            exchange_id: ID of the exchange
            symbol_map: Mapping of symbols by exchange
            
        Returns:
            Exchange-specific symbol
        """
        # Get exchange-specific mapping
        exchange_map = symbol_map.get(exchange_id.lower(), {})
        
        # Map symbol if it exists in the mapping, otherwise use as-is
        mapped_symbol = exchange_map.get(symbol, symbol)
        
        # Log mapping
        if mapped_symbol != symbol:
            logger.info(f"Mapped {symbol} to {mapped_symbol} for {exchange_id}")
            
        return mapped_symbol
    
    def get_precision_digits(self, market_info: Dict, precision_type: str) -> int:
        """
        Get the number of decimal places for amount or price from market info.
        
        Args:
            market_info: Market information dictionary from exchange
            precision_type: Type of precision to get ('amount' or 'price')
            
        Returns:
            Number of decimal places
        """
        precision_data = market_info.get("precision", {})
        value = None
        
        if precision_type == "amount":
            value = precision_data.get("amount")
        elif precision_type == "price":
            value = precision_data.get("price")
            
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
                logger.warning(f"Error calculating precision digits: {e}")
                
        # Fallback defaults
        default_precision = 8 if precision_type == "amount" else 2
        logger.warning(
            f"Could not determine '{precision_type}' precision. "
            f"Using default: {default_precision}"
        )
        return default_precision
    
    def round_value(
        self,
        value: float,
        precision_digits: int,
        rounding_func=round
    ) -> float:
        """
        Round a value to the specified number of decimal places.
        
        Args:
            value: Value to round
            precision_digits: Number of decimal places to round to
            rounding_func: Function to use for rounding
            
        Returns:
            Rounded value
        """
        if precision_digits is None:
            return value
            
        try:
            # Convert to Decimal for accurate financial rounding
            dec_value = Decimal(str(value))
            dec_precision = Decimal("0.1") ** precision_digits
            
            # Use specified rounding function
            if rounding_func == math.floor:
                rounded = dec_value.quantize(dec_precision, rounding=ROUND_HALF_DOWN)
            else:
                rounded = dec_value.quantize(dec_precision, rounding=ROUND_HALF_UP)
                
            # Convert back to float
            return float(rounded)
            
        except (ValueError, TypeError, DecimalException) as e:
            # Fallback to float rounding
            logger.warning(f"Decimal rounding failed, using float rounding: {e}")
            factor = 10 ** precision_digits
            return rounding_func(value * factor) / factor
    
    def check_risk_limits(self, intent: Intent, context: Dict) -> Tuple[bool, str]:
        """
        Check if the intent violates risk limits.
        
        Args:
            intent: Trading intent to check
            context: Additional context (e.g., equity)
            
        Returns:
            Tuple of (is_valid, reason), where is_valid is True if within limits
        """
        # Check leverage against max_leverage rule
        leverage = intent.leverage or 1
        max_leverage = self.config.max_leverage
        
        if leverage > max_leverage:
            return (False, f"Requested leverage {leverage} exceeds max allowed {max_leverage}")
            
        # Check position size against risk limits
        size_type = intent.size_type
        size_value = intent.size_value
        equity = context.get("equity")
        
        if size_type and size_value and equity:
            # Check percentage-based risk
            if size_type == "percentage_equity":
                if not isinstance(size_value, (int, float)) or not 0 < size_value <= 1:
                    return (False, f"Invalid size_value '{size_value}' for percentage_equity")
                    
                max_risk_pct = self.config.max_risk_per_trade_pct
                if size_value > max_risk_pct:
                    return (
                        False,
                        f"Requested size {size_value*100:.2f}% exceeds max risk "
                        f"per trade {max_risk_pct*100:.2f}%"
                    )
                    
            # Check fixed USD position size
            elif size_type == "fixed_usd":
                if not isinstance(size_value, (int, float)) or size_value <= 0:
                    return (False, f"Invalid size_value '{size_value}' for fixed_usd")
                    
                max_risk_pct = self.config.max_risk_per_trade_pct
                max_risk_amount = equity * max_risk_pct
                
                if size_value > max_risk_amount:
                    return (
                        False,
                        f"Fixed USD size ${size_value} exceeds max risk of "
                        f"${max_risk_amount:.2f} ({max_risk_pct*100:.0f}% of equity ${equity:.2f})"
                    )
                    
            # Check fixed contracts position size
            elif size_type == "fixed_contracts":
                if not isinstance(size_value, (int, float)) or size_value <= 0:
                    return (False, f"Invalid size_value '{size_value}' for fixed_contracts")
                    
                max_contracts = self.config.max_contracts_per_trade
                if size_value > max_contracts:
                    return (
                        False,
                        f"Requested contracts {size_value} exceeds max allowed {max_contracts}"
                    )
                    
        # All checks passed
        return (True, "")