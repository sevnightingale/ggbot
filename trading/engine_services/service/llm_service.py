"""
LLM Service for the Trading Engine.

This service handles all interactions with Large Language Models (LLMs)
for generating and parsing trading tool calls based on intents from
the Decision Module.
"""

import os
import json
import logging
import asyncio
import re
import random
from typing import Dict, List, Optional, Any, Union, Tuple

from core.common.logger import logger
from trading.engine_services.model.config import EngineConfig, LLMConfig
from trading.engine_services.model.intent import Intent
from trading.engine_services.model.tool_call import ToolCall
from trading.engine_services.model.event import Event, EventType


class LLMService:
    """
    Service for interacting with LLMs to generate trading tool calls.
    
    This service is responsible for:
    1. Sending prompts to the LLM based on trading intents
    2. Parsing and normalizing the LLM responses
    3. Converting responses to structured tool calls
    4. Handling errors and retries
    """
    
    def __init__(self, config: Union[EngineConfig, LLMConfig], user_id: Optional[str] = None, event_bus=None, llm_client=None):
        """
        Initialize the LLM service.
        
        Args:
            config: Configuration for the LLM service or full engine config
            user_id: Optional user ID for the current session
            event_bus: Optional event bus for emitting events
            llm_client: Optional pre-configured LLM client for testing
        """
        # Extract LLM config from EngineConfig if provided
        if isinstance(config, EngineConfig):
            self.config = config.llm
        else:
            self.config = config
            
        self.user_id = user_id
        self.event_bus = event_bus
        self.api_key = self._get_api_key()
        
        # Initialize the LLM client if not provided
        self.llm_client = llm_client
        
        if not self.llm_client and not self.config.use_mock:
            self._initialize_llm_client()
            
        logger.info(f"LLMService initialized with model {self.config.model}")
    
    def _get_api_key(self) -> Optional[str]:
        """
        Get API key from config or environment variables.
        
        Returns:
            API key or None if not found
        """
        # Try config first
        api_key = self.config.api_key
        
        # Then try environment variables
        if not api_key:
            # Try provider-specific environment variables
            if self.config.model.startswith("gpt-"):
                api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('TRADING_LLM_API_KEY')
            elif self.config.model.startswith("claude-"):
                api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('TRADING_LLM_API_KEY')
            else:
                # Generic fallback
                api_key = os.environ.get('TRADING_LLM_API_KEY')
                
        if not api_key and not self.config.use_mock:
            logger.warning(f"No API key found for LLM model {self.config.model}")
            
        return api_key
    
    def _initialize_llm_client(self):
        """Initialize the appropriate LLM client based on the model."""
        try:
            # Initialize OpenAI client for GPT models
            if self.config.model.startswith("gpt-"):
                self._initialize_openai_client()
            # Initialize Anthropic client for Claude models
            elif self.config.model.startswith("claude-"):
                self._initialize_anthropic_client()
            # Add other model providers as needed
            else:
                logger.warning(f"Unsupported model type: {self.config.model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}", exc_info=True)
            logger.info("Falling back to mock LLM responses")
            self.config.use_mock = True
    
    def _initialize_openai_client(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            
            if not self.api_key:
                raise ValueError("API key is required for OpenAI")
                
            self.llm_client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            logger.error("OpenAI package not found. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            raise
    
    def _initialize_anthropic_client(self):
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic
            
            if not self.api_key:
                raise ValueError("API key is required for Anthropic")
                
            self.llm_client = Anthropic(api_key=self.api_key)
            logger.info("Anthropic client initialized successfully")
        except ImportError:
            logger.error("Anthropic package not found. Install with: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}", exc_info=True)
            raise
    
    async def process_intent(self, intent_data: Dict, tools_schema: List[Dict] = None) -> List[ToolCall]:
        """
        Process a trading intent and generate tool calls.
        
        Args:
            intent_data: Trading intent data from the Decision Module (can be structured or semi-structured)
            tools_schema: Optional schema of available tools
            
        Returns:
            List of tool calls to execute
            
        Raises:
            ValueError: If the LLM response cannot be parsed
        """
        # Extract decision_id for logging and events
        decision_id = intent_data.get('decision_id', 'unknown')
        
        # Emit event for intent processing start
        if self.event_bus:
            self.event_bus.emit(Event.create(
                EventType.LLM_CALL_STARTED,
                user_id=self.user_id,
                decision_id=decision_id,
                details={"model": self.config.model}
            ))
        
        # Create prompt from intent and tools schema
        prompt = self._create_prompt(intent_data, tools_schema)
        
        try:
            # Generate response from LLM
            logger.info(f"Generating LLM response for intent {decision_id}")
            llm_response_text = await self._generate_response(prompt)
            logger.info(f"LLM response received for intent {decision_id}")
            
            # Parse response into tool calls
            tool_calls = await self._parse_response(llm_response_text)
            logger.info(f"Parsed {len(tool_calls)} tool calls from LLM response")
            
            # Emit success event
            if self.event_bus:
                self.event_bus.emit(Event.create(
                    EventType.LLM_CALL_SUCCEEDED,
                    user_id=self.user_id,
                    decision_id=decision_id,
                    details={"tool_call_count": len(tool_calls)}
                ))
                
            return tool_calls
            
        except Exception as e:
            # Emit failure event
            if self.event_bus:
                self.event_bus.emit(Event.create(
                    EventType.LLM_CALL_FAILED,
                    user_id=self.user_id,
                    decision_id=decision_id,
                    details={"error": str(e)}
                ))
                
            logger.error(f"Error processing intent with LLM: {e}", exc_info=True)
            raise
    
    def _create_prompt(self, intent_data: Dict, tools_schema: List[Dict] = None) -> str:
        """
        Create a prompt for the LLM based on the intent data and tools schema.
        
        Args:
            intent_data: Trading intent data from the Decision Module (dict or semi-structured)
            tools_schema: Optional schema of available tools
            
        Returns:
            Formatted prompt string
        """
        # Extract key information from intent data for highlighting (safely using .get())
        action = intent_data.get('action', 'trade')
        symbol = intent_data.get('symbol', 'unknown')
        exchange = intent_data.get('exchange', 'unknown')
        leverage = intent_data.get('leverage', 1)
        
        # Format tools schema to be more readable
        formatted_tools = []
        
        if tools_schema:
            for tool in tools_schema:
                tool_name = tool.get('name', '')
                tool_desc = tool.get('description', '')
                
                # Format parameters
                params_list = []
                for param_name, param_info in tool.get('parameters', {}).items():
                    required = param_info.get('required', False)
                    req_text = "required" if required else "optional"
                    desc = param_info.get('description', '')
                    param_type = param_info.get('type', 'string')
                    params_list.append(f"  - {param_name} ({param_type}, {req_text}): {desc}")
                    
                # Build tool description
                tool_text = f"Tool: {tool_name}\nDescription: {tool_desc}\nParameters:\n" + "\n".join(params_list)
                formatted_tools.append(tool_text)
        
        # Create action phrase safely
        action_phrase = f"{action.replace('_', ' ')} {symbol} with {leverage}x leverage"
            
        # Join the formatted tools with newlines
        tools_text = "\n".join(formatted_tools)
        
        # User system prompt from config if available
        system_prompt = self.config.system_prompt or "You are a trading agent responsible for translating high-level trading intents into specific CCXT MCP tool calls for execution on cryptocurrency exchanges."
        
        # Add symbol mapping note - this is generic and exchange-agnostic
        symbol_mapping_note = """
NOTE ABOUT SYMBOLS:
Use standard trading pair format (e.g., "BTC/USD") in your tool calls.
The system will automatically map this to the correct exchange-specific format if needed.
"""
            
        # Construct prompt
        prompt = f"""{system_prompt}

Here are the tools available to you:
{tools_text}
{symbol_mapping_note}
Here is the trading intent to execute:
```
{json.dumps(intent_data, indent=2, default=str)}
```

IMPORTANT INSTRUCTIONS:
1. All tool parameters MUST use snake_case (with underscores), not camelCase.
2. You MUST use the exchange "{exchange}" for all tool calls that require an exchange.
3. Based on the trading intent to {action_phrase}, determine the correct sequence of tool calls.
4. CRITICAL: The system prompt above contains an EXCHANGE GUIDE with specific rules - you MUST follow ALL rules in that guide.
5. For position sizing: If the intent specifies collateral and leverage, calculate position size as: collateral × leverage = total position value.
6. Check the exchange guide for:
   - Whether you need to set leverage or if it's already configured
   - Minimum order sizes and how to handle them
   - Required parameter formats for each tool
   - Error messages to expect and how to handle them
7. Do NOT attempt operations that the exchange guide says will fail or are not supported.

When you want to use a tool, format your response as a JSON object with this structure:
```
{{
  "tool": "tool_name",
  "parameters": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}
```

If multiple tools are needed, provide a list of tool calls in this format:
```
[
  {{
    "tool": "set_leverage",
    "parameters": {{
      "symbol": "BTC/USD",
      "leverage": 10
    }}
  }},
  {{
    "tool": "create_order",
    "parameters": {{
      "symbol": "BTC/USD",
      "side": "buy",
      "type": "market",
      "amount": 0.001
    }}
  }}
]
```

Which tool(s) would you use to execute this trading intent and with what parameters? Respond ONLY with the JSON.
"""
        return prompt
    
    async def _generate_response(self, prompt: str) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The generated response text
            
        Raises:
            Exception: If the LLM call fails
        """
        if self.config.use_mock:
            logger.info("Using mock LLM response generation")
            return await self._generate_mock_response(prompt)
            
        # Get provider based on model name
        if self.config.model.startswith("gpt-"):
            return await self._generate_openai_response(prompt)
        elif self.config.model.startswith("claude-"):
            return await self._generate_anthropic_response(prompt)
        else:
            # Default to OpenAI (can be replaced with another provider)
            return await self._generate_openai_response(prompt)
    
    async def _generate_openai_response(self, prompt: str) -> str:
        """
        Generate a response using the OpenAI API.
        
        Args:
            prompt: The prompt to send to OpenAI
            
        Returns:
            The generated response text
            
        Raises:
            Exception: If the API call fails
        """
        # Retry logic
        retries = 0
        max_retries = self.config.max_retries
        backoff = 1.0
        
        while True:
            try:
                # Check if client is initialized
                if not self.llm_client:
                    raise ValueError("OpenAI client not initialized")
                    
                # Format messages
                messages = [
                    {"role": "system", "content": self.config.system_prompt},
                    {"role": "user", "content": prompt}
                ]
                
                logger.info(f"Making OpenAI API call with model {self.config.model}")
                
                # Run synchronous call in background for async context
                response = await asyncio.to_thread(
                    self.llm_client.chat.completions.create,
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature
                )
                
                logger.info("OpenAI API call completed successfully")
                
                # Extract content from response
                content = response.choices[0].message.content
                
                return content
                
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    logger.error(f"OpenAI API call failed after {retries} retries: {e}")
                    raise
                
                # Calculate backoff with jitter
                sleep_time = backoff * (0.5 + random.random())
                logger.warning(f"OpenAI API call failed: {e}. Retrying in {sleep_time:.2f}s ({retries}/{max_retries})")
                await asyncio.sleep(sleep_time)
                backoff *= self.config.backoff_factor
    
    async def _generate_anthropic_response(self, prompt: str) -> str:
        """
        Generate a response using the Anthropic API.
        
        Args:
            prompt: The prompt to send to Anthropic
            
        Returns:
            The generated response text
            
        Raises:
            Exception: If the API call fails
        """
        # Retry logic
        retries = 0
        max_retries = self.config.max_retries
        backoff = 1.0
        
        while True:
            try:
                # Check if client is initialized
                if not self.llm_client:
                    raise ValueError("Anthropic client not initialized")
                    
                logger.info(f"Making Anthropic API call with model {self.config.model}")
                
                # Run synchronous call in background for async context
                response = await asyncio.to_thread(
                    self.llm_client.messages.create,
                    model=self.config.model,
                    max_tokens=4000,
                    system=self.config.system_prompt,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature
                )
                
                logger.info("Anthropic API call completed successfully")
                
                # Extract content from response
                content = response.content[0].text
                
                return content
                
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    logger.error(f"Anthropic API call failed after {retries} retries: {e}")
                    raise
                
                # Calculate backoff with jitter
                sleep_time = backoff * (0.5 + random.random())
                logger.warning(f"Anthropic API call failed: {e}. Retrying in {sleep_time:.2f}s ({retries}/{max_retries})")
                await asyncio.sleep(sleep_time)
                backoff *= self.config.backoff_factor
    
    async def _generate_mock_response(self, prompt: str) -> str:
        """
        Generate a mock response for testing.
        
        Args:
            prompt: The prompt (used to extract intent details)
            
        Returns:
            A mock response string in JSON format
        """
        # Extract intent from prompt
        intent_data = {}
        try:
            # Extract JSON from triple backticks
            matches = re.findall(r'```json\s*(.*?)\s*```', prompt, re.DOTALL)
            if matches:
                intent_json = matches[0]
                intent_data = json.loads(intent_json)
                logger.info("Successfully parsed intent from prompt JSON block")
        except Exception as e:
            logger.warning(f"Error parsing intent from prompt: {e}")
            
        # Extract key information
        action = intent_data.get('action', 'unknown')
        symbol = intent_data.get('symbol', 'BTC/USD')
        exchange = intent_data.get('exchange', 'bitmex')
        leverage = intent_data.get('leverage', 1)
        
        # Default values
        amount = 0.001  # Small amount for testing
        
        logger.info(f"Generating mock response for action: {action}, symbol: {symbol}, leverage: {leverage}")
        
        # Generate appropriate tool calls based on action
        if action in ['enter_long', 'enter_short']:
            side = 'buy' if action == 'enter_long' else 'sell'
            calls = []
            
            # Add leverage call if needed
            if leverage and leverage > 1:
                calls.append({
                    "tool": "set_leverage",
                    "parameters": {
                        "symbol": symbol,
                        "leverage": leverage
                    }
                })
                
            # Add order creation call
            calls.append({
                "tool": "create_order",
                "parameters": {
                    "symbol": symbol,
                    "side": side,
                    "type": "market",
                    "amount": amount
                }
            })
            
            # Add stop loss and take profit if specified
            sl_price = intent_data.get('stop_loss_price')
            tp_price = intent_data.get('take_profit_price')
            
            if sl_price:
                calls.append({
                    "tool": "create_order",
                    "parameters": {
                        "symbol": symbol,
                        "side": "sell" if action == "enter_long" else "buy",
                        "type": "stop",
                        "amount": amount,
                        "price": sl_price,  # For limit orders after stop
                        "stop_price": sl_price,
                        "reduce_only": True
                    }
                })
                
            if tp_price:
                calls.append({
                    "tool": "create_order",
                    "parameters": {
                        "symbol": symbol,
                        "side": "sell" if action == "enter_long" else "buy",
                        "type": "limit",
                        "amount": amount,
                        "price": tp_price,
                        "reduce_only": True
                    }
                })
                
            return json.dumps(calls)
            
        elif action == 'exit':
            # Get trade_id for exit
            trade_id = intent_data.get('trade_id')
            
            # If we know trade ID, we could potentially look up direction in DB
            # but for mocking, we'll just assume a long position
            direction = "long"  # Default for mocking
            
            return json.dumps([{
                "tool": "create_order",
                "parameters": {
                    "symbol": symbol,
                    "side": "sell" if direction == "long" else "buy",
                    "type": "market",
                    "amount": amount,
                    "reduce_only": True
                }
            }])
            
        elif action == 'adjust':
            # Adjust stop loss or take profit
            sl_price = intent_data.get('stop_loss_price')
            tp_price = intent_data.get('take_profit_price')
            
            calls = []
            
            if sl_price:
                # Cancel existing SL order (would need order_id in real implementation)
                calls.append({
                    "tool": "cancel_all_orders",
                    "parameters": {
                        "symbol": symbol
                    }
                })
                
                # Create new SL order
                calls.append({
                    "tool": "create_order",
                    "parameters": {
                        "symbol": symbol,
                        "side": "sell",  # Assuming long position
                        "type": "stop",
                        "amount": amount,
                        "stop_price": sl_price,
                        "reduce_only": True
                    }
                })
                
            return json.dumps(calls)
            
        else:
            # Default fallback - just fetch balance
            logger.info("Using default fetch_balance fallback for mock response")
            return json.dumps([{
                "tool": "fetch_balance",
                "parameters": {}
            }])
    
    async def _parse_response(self, response_text: str) -> List[ToolCall]:
        """
        Parse the LLM response into a list of tool calls.
        
        Args:
            response_text: Raw text response from the LLM
            
        Returns:
            List of tool call dictionaries
            
        Raises:
            ValueError: If the response cannot be parsed into valid format
        """
        if not response_text:
            logger.error("Empty LLM response received")
            if self.event_bus:
                self.event_bus.emit(Event.create(EventType.LLM_RESPONSE_INVALID, details={"error": "Empty response"}))
            return []
        
        # Clean up the response to extract JSON
        cleaned_text = response_text.strip()
        logger.debug(f"Parsing LLM response (truncated): {cleaned_text[:200]}...")
        
        # Extract JSON content from markdown
        json_content = None
        
        # Look for JSON content in code blocks
        code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        code_blocks = re.findall(code_block_pattern, cleaned_text)
        
        if code_blocks:
            # Use the first code block that contains valid JSON
            for block in code_blocks:
                try:
                    # Validate this is valid JSON
                    json.loads(block)
                    json_content = block
                    logger.debug("Found valid JSON in code block")
                    break
                except json.JSONDecodeError:
                    continue
        
        # If no valid JSON found in code blocks, try to find JSON array in the entire text
        if not json_content:
            array_pattern = r'\[\s*{[\s\S]*}\s*\]'
            array_match = re.search(array_pattern, cleaned_text)
            
            if array_match:
                json_content = array_match.group(0)
                logger.debug("Found JSON array pattern")
        
        # If still no JSON content, use the whole response as a last resort
        if not json_content:
            json_content = cleaned_text
            logger.debug("Using full response as JSON content")
        
        logger.debug(f"Extracted JSON content (truncated): {json_content[:200] if json_content else 'None'}...")
        
        try:
            # Parse the content to JSON
            parsed_data = json.loads(json_content)
            
            # Ensure we have a list of tool calls
            if not isinstance(parsed_data, list):
                # If it's a single tool call (not in a list), wrap it in a list
                if isinstance(parsed_data, dict) and 'tool' in parsed_data:
                    parsed_data = [parsed_data]
                else:
                    logger.warning(f"Unexpected JSON structure, not a list or a tool call: {type(parsed_data)}")
                    if self.event_bus:
                        self.event_bus.emit(Event.create(
                            EventType.LLM_RESPONSE_INVALID,
                            details={"error": "Not a list or a tool call"}
                        ))
                    return []
            
            # Validate each tool call and convert to ToolCall objects
            tool_calls = []
            
            for item in parsed_data:
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dict item in tool calls list: {item}")
                    continue
                
                # Check if it has the required fields
                if 'tool' not in item:
                    logger.warning(f"Skipping item missing 'tool' field: {item}")
                    continue
                
                # Get tool name
                tool_name = item.get('tool')
                
                # Get parameters, handling the case where parameters might be at the top level
                parameters = {}
                
                if 'parameters' in item and isinstance(item['parameters'], dict):
                    # Normal case: parameters are in a nested 'parameters' field
                    parameters = item['parameters']
                else:
                    # Alternative case: parameters are top-level fields
                    parameters = {k: v for k, v in item.items() if k != 'tool'}
                
                # Create and append the tool call
                tool_call = ToolCall(tool=tool_name, parameters=parameters)
                tool_calls.append(tool_call)
            
            logger.info(f"Successfully parsed {len(tool_calls)} tool calls from LLM response")
            return tool_calls
            
        except json.JSONDecodeError as e:
            # Try to recover by fixing common JSON issues
            logger.warning(f"JSON parse error: {e}. Attempting to fix...")
            
            try:
                # Replace single quotes with double quotes
                fixed_content = json_content.replace("'", '"')
                
                # Fix unquoted property names
                fixed_content = re.sub(r'(\s*)(\w+)(\s*):([^/])', r'\1"\2"\3:\4', fixed_content)
                
                # Try parsing again
                parsed_data = json.loads(fixed_content)
                
                # Ensure it's a list
                if not isinstance(parsed_data, list):
                    if isinstance(parsed_data, dict) and 'tool' in parsed_data:
                        parsed_data = [parsed_data]
                    else:
                        raise ValueError(f"Fixed JSON is not a list or a tool call: {type(parsed_data)}")
                
                # Convert to Tool Call objects
                tool_calls = []
                for item in parsed_data:
                    if not isinstance(item, dict) or 'tool' not in item:
                        continue
                        
                    tool_name = item.get('tool')
                    parameters = item.get('parameters', {})
                    
                    if not isinstance(parameters, dict):
                        parameters = {}
                        
                    tool_call = ToolCall(tool=tool_name, parameters=parameters)
                    tool_calls.append(tool_call)
                
                logger.info(f"Recovered {len(tool_calls)} tool calls after fixing JSON format")
                return tool_calls
                
            except (json.JSONDecodeError, ValueError) as recovery_error:
                logger.error(f"Failed to fix JSON: {recovery_error}")
                if self.event_bus:
                    self.event_bus.emit(Event.create(
                        EventType.LLM_RESPONSE_INVALID,
                        details={"error": f"JSON parsing failed: {e}"}
                    ))
                raise ValueError(f"Failed to parse LLM response as JSON: {e}")
                
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}", exc_info=True)
            if self.event_bus:
                self.event_bus.emit(Event.create(
                    EventType.LLM_RESPONSE_INVALID,
                    details={"error": f"Parsing error: {e}"}
                ))
            raise ValueError(f"Error parsing LLM response: {e}")