"""
Trading Engine

This module provides the central orchestration component for executing trades 
based on decisions from the Decision Module. It handles the conversion of high-level
trade intents into executable exchange commands via the LLM, validates these
through the TradeCompiler, and coordinates execution and position management.

The TradingEngine serves as the primary interface between the Decision Module
and the cryptocurrency exchanges, ensuring all trades are properly validated,
executed, and tracked.
"""

import json
import uuid
import asyncio
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from openai import OpenAI  # Import at top level like simplified_llm_mcp_test.py

from core.common.logger import logger
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter
from trading.compiler import TradeCompiler, TradeCompilerValidationError


# Temporary DB placeholder - will be replaced with proper DB implementation
class MockDb:
    """Temporary mock database for prototype implementation."""
    
    async def get_trade(self, trade_id, user_id):
        """Get a trade record by ID."""
        logger.debug(f"DB: Getting trade {trade_id} for user {user_id}")
        return {'trade_id': trade_id, 'trade_status': 'open', 'user_id': user_id}
    
    async def create_trade(self, data):
        """Create a new trade record."""
        trade_id = data.get('trade_id', str(uuid.uuid4()))
        logger.debug(f"DB: Creating trade record {trade_id}")
        return trade_id
    
    async def update_trade(self, trade_id, data):
        """Update an existing trade record."""
        logger.debug(f"DB: Updating trade {trade_id} with {data}")
        return True
    
    async def log_rejection(self, data):
        """Log a trade rejection."""
        logger.debug(f"DB: Logging rejection {data}")
        return True
        
    async def log_error(self, data):
        """Log a trade error."""
        logger.debug(f"DB: Logging error {data}")
        return True
    
    async def get_active_trades(self, user_id, status='open'):
        """Get all active trades for a user."""
        logger.debug(f"DB: Getting active trades for user {user_id} with status {status}")
        return [{'trade_id': f'mock_trade_{i}', 'trade_status': status, 'user_id': user_id} for i in range(3)]

db = MockDb()


# Add debugging function to directly test OpenAI API - like in simplified_llm_mcp_test.py
def debug_openai_direct():
    """Debug the OpenAI API response format directly."""
    try:
        # Get API key from environment
        api_key = os.environ.get("TRADING_LLM_API_KEY")
        if not api_key:
            print("No API key found in TRADING_LLM_API_KEY")
            return
            
        # Create client
        print("Creating OpenAI client...")
        client = OpenAI(api_key=api_key)
        
        # Make API call
        print("Making direct API call to OpenAI...")
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


# LLM Provider for Trading Agent
class TradingLLMProvider:
    """
    Provider for LLM services used by the Trading Agent.
    This implementation uses OpenAI API but can be adapted for other LLMs.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the LLM provider.
        
        Args:
            config: Configuration dictionary with API keys and model settings
        """
        self.config = config
        self.api_key = self._get_api_key()
        self.model = config.get('model', 'gpt-4')
        self.temperature = config.get('temperature', 0)
        
        # Flag to use mock responses for testing
        self.use_mock = config.get('use_mock_llm', False)
        
        # Initialize OpenAI client if key is available - EXACTLY matching simplified_llm_mcp_test.py
        if self.api_key and not self.use_mock:
            try:
                # Create client - EXACTLY like simplified_llm_mcp_test.py
                # OpenAI is now imported at top level
                self.llm_client = OpenAI(api_key=self.api_key)
                logger.info(f"Initialized OpenAI client with model {self.model}")
            except ImportError:
                logger.warning("OpenAI package not found. Install with: pip install openai")
                self.use_mock = True  # Force mock mode since OpenAI is unavailable
                logger.info("Falling back to mock LLM due to missing OpenAI package")
        else:
            self.llm_client = None
        
        logger.info(f"Initialized Trading LLM Provider with model {self.model}")
        
    def _get_api_key(self) -> str:
        """Get API key from config or environment."""
        # Try config first
        api_key = self.config.get('api_key')
        
        # Then try environment variables
        if not api_key:
            api_key = os.environ.get('TRADING_LLM_API_KEY')
            
        if not api_key and not self.config.get('use_mock_llm', False):
            logger.warning("No API key found for LLM. Set TRADING_LLM_API_KEY or use_mock_llm=True")
            
        return api_key
        
    async def generate(self, prompt: str) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The generated response
        """
        if self.use_mock:
            logger.info("Using mock LLM response generation")
            return await self._generate_mock_response(prompt)
            
        # Check API key exists
        if not self.api_key:
            raise ValueError("No API key provided for LLM. Set TRADING_LLM_API_KEY")
            
        # Determine LLM type based on API key format
        # Claude keys start with 'sk-ant-' or 'sk-proj-'
        is_claude = self.api_key.startswith(('sk-ant-', 'sk-proj-'))
        # DeepSeek keys are typically UUID format with 4 hyphens
        is_deepseek = len(self.api_key) == 36 and self.api_key.count('-') == 4
        
        logger.info(f"Making real LLM API call with model: {self.model}, temp: {self.temperature}")
        logger.debug(f"LLM prompt (truncated): {prompt[:300]}...")
        
        # Use appropriate API based on key type
        if is_claude:
            response_text = await self._generate_claude_response(prompt)
        elif is_deepseek:
            response_text = await self._generate_deepseek_response(prompt)
        else:
            # Default to OpenAI
            response_text = await self._generate_openai_response(prompt)
            
        logger.debug(f"LLM response (truncated): {response_text[:300]}...")
        return response_text
            
    async def _generate_openai_response(self, prompt: str) -> str:
        """
        Generate a response using the OpenAI API.
        EXACTLY matching the approach in simplified_llm_mcp_test.py
        """
        try:
            # Check if client is already initialized
            if not self.llm_client:
                raise ValueError("OpenAI client not initialized")
                
            # Format messages - EXACTLY like simplified_llm_mcp_test.py
            messages = [
                {"role": "system", "content": "You are a trading agent responsible for executing trades. You must respond in JSON format with tool calls."},
                {"role": "user", "content": prompt}
            ]
            
            logger.info(f"Making OpenAI API call with model {self.model}")
            
            # Need to run synchronous call in background for async context
            # EXACTLY match the call pattern from simplified_llm_mcp_test.py
            response = await asyncio.to_thread(
                self.llm_client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            
            logger.info("OpenAI API call completed successfully")
            
            # Extract the JSON from the response - EXACTLY like simplified_llm_mcp_test.py
            content = response.choices[0].message.content
            
            # Debug logging of raw content
            logger.info(f"Raw LLM content: {content[:200] + '...' if len(content) > 200 else content}")
            
            # Remove any markdown formatting - EXACTLY like simplified_llm_mcp_test.py
            if "```json" in content:
                logger.info("Found ```json marker in content")
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                logger.info("Found ``` marker in content")
                content = content.split("```")[1].split("```")[0].strip()
            else:
                logger.info("No markdown code blocks found in content")
                
            # Log the cleaned content
            logger.info(f"Cleaned content: {content[:200] + '...' if len(content) > 200 else content}")
                
            # Return the raw string content - simplified_llm_mcp_test.py does json.loads() on this
            return content
            
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {e}", exc_info=True)
            raise  # Re-raise to match simplified_llm_mcp_test.py error handling
            
    async def _generate_claude_response(self, prompt: str) -> str:
        """
        Generate a response using Anthropic Claude API.
        """
        try:
            import aiohttp
            
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            # Map our model name to Claude model
            claude_model = "claude-3-haiku-20240307"
            if "claude" in self.model:
                claude_model = self.model
            elif "gpt-4" in self.model:
                claude_model = "claude-3-opus-20240229"  # Use highest quality model
            elif "gpt-3.5" in self.model:
                claude_model = "claude-3-sonnet-20240229"  # Mid-tier
                
            payload = {
                "model": claude_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 4000,
                "temperature": self.temperature,
                "system": "You are a trading agent responsible for executing trades. You must respond in JSON format with a list of tool calls."
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Claude API error: {response.status}, {error_text}")
                        
                    result = await response.json()
                    response_text = result.get("content", [{}])[0].get("text", "")
                    
                    if not response_text:
                        raise ValueError("Empty response from Claude API")
                        
                    return response_text
                    
        except Exception as e:
            logger.error(f"Error in Claude API call: {e}", exc_info=True)
            raise
            
    async def _generate_deepseek_response(self, prompt: str) -> str:
        """
        Generate a response using DeepSeek API.
        """
        try:
            import aiohttp
            
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Use best DeepSeek model
            deepseek_model = "deepseek-chat"
            
            payload = {
                "model": deepseek_model,
                "messages": [
                    {"role": "system", "content": "You are a trading agent responsible for executing trades. You must respond in JSON format with a list of tool calls."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature,
                "max_tokens": 4000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"DeepSeek API error: {response.status}, {error_text}")
                        
                    result = await response.json()
                    response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    if not response_text:
                        raise ValueError("Empty response from DeepSeek API")
                        
                    return response_text
                    
        except Exception as e:
            logger.error(f"Error in DeepSeek API call: {e}", exc_info=True)
            raise
    
    async def _generate_mock_response(self, prompt: str) -> str:
        """Generate a mock response for testing."""
        # Extract intent details from prompt
        # Look for JSON in the prompt between triple backticks
        intent_data = {}
        try:
            match = re.search(r'```json\s*(.*?)\s*```', prompt, re.DOTALL)
            if match:
                intent_json = match.group(1)
                intent_data = json.loads(intent_json)
                logger.info(f"Successfully parsed intent from prompt JSON block")
            else:
                logger.warning("Couldn't find JSON intent in prompt between triple backticks")
        except Exception as e:
            logger.warning(f"Error parsing intent from prompt: {e}")
            
        # Extract action, symbol, and leverage info
        action = intent_data.get('action', 'unknown')
        symbol = intent_data.get('symbol', 'BTC/USD')
        leverage = intent_data.get('leverage', 1)
        amount = 0.001  # Default mock amount
        
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
            
            return json.dumps(calls)
            
        elif action == 'exit':
            # Exit existing position
            return json.dumps([{
                "tool": "create_order",
                "parameters": {
                    "symbol": symbol,
                    "side": "sell",  # Assuming long position for mock
                    "type": "market",
                    "amount": amount,
                    "reduceOnly": True
                }
            }])
            
        elif action == 'adjust':
            # Adjust stop loss or take profit
            stop_price = intent_data.get('stop_loss_price', 60000)
            
            return json.dumps([
                # Cancel existing SL order
                {
                    "tool": "cancel_order",
                    "parameters": {
                        "symbol": symbol,
                        "id": "old_sl_id_placeholder"
                    }
                },
                # Create new SL order
                {
                    "tool": "create_order",
                    "parameters": {
                        "symbol": symbol,
                        "side": "sell",
                        "type": "stop",
                        "amount": amount,
                        "stopPrice": stop_price,
                        "reduceOnly": True
                    }
                }
            ])
            
        else:
            # Default fallback - just fetch balance
            logger.info("Using default fetch_balance fallback for mock response")
            return json.dumps([{
                "tool": "fetch_balance",
                "parameters": {}
            }])

def initialize_llm_provider(config: Dict) -> TradingLLMProvider:
    """
    Initialize the LLM provider for trading.
    
    Args:
        config: Configuration dictionary, potentially containing API keys
               and model settings
        
    Returns:
        Configured TradingLLMProvider instance
    """
    # Check if we need to override the config with real API key
    if 'api_key' not in config or not config.get('api_key'):
        # Try to get API key from environment
        api_key = os.environ.get('TRADING_LLM_API_KEY')
        if api_key:
            # Update config with API key
            config = config.copy()  # Don't modify the original
            config['api_key'] = api_key
            logger.info("Using TRADING_LLM_API_KEY from environment")
            
    # Ensure we're using reasonable defaults for reliability
    if 'model' not in config:
        config['model'] = 'gpt-4-turbo'  # Default to GPT-4 Turbo for better tools usage
    
    if 'temperature' not in config:
        config['temperature'] = 0.2  # Low temperature for consistent outputs
        
    # Create the provider
    provider = TradingLLMProvider(config)
    return provider

class TradingEngine:
    def __init__(self, user_id, config):
        self.user_id = user_id
        self.config = config
        self.llm_provider = initialize_llm_provider(config)
        self.ccxt_adapter = CCXTMCPAdapter(user_id, config) # Handles connection
        self.trade_compiler = TradeCompiler(config, self.ccxt_adapter) # Needs adapter for exchange info
        # Pass self reference to TradeManager if needed for callbacks like auto-exit
        self.trade_manager = TradeManager(user_id, config, self.ccxt_adapter, self.trade_compiler, trading_engine_ref=self)
        self.available_tools = None # Cache available MCP tools
        
    def _clean_json_keys(self, obj):
        """
        Recursively clean JSON keys that might have extra quotes or other formatting issues.
        This handles cases where the LLM returns keys like '"type"' instead of 'type'.
        
        Args:
            obj: The object (dict, list, or primitive) to clean
            
        Returns:
            Cleaned object with properly formatted keys
        """
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in obj.items():
                new_key = k
                # Simple unwrap: if key is like '"actual_key"', transform to 'actual_key'
                if isinstance(k, str) and len(k) > 2 and k.startswith('"') and k.endswith('"'):
                    new_key = k[1:-1]
                    logger.info(f"Cleaned quoted key: {k} -> {new_key}")
                
                # Handle camelCase vs snake_case for common order parameters
                if isinstance(k, str):
                    if k.lower() == 'ordertype' or k.lower() == 'order_type':
                        new_key = 'type'
                        logger.info(f"Normalized key: {k} -> {new_key}")
                
                # Clean the value recursively
                new_dict[new_key] = self._clean_json_keys(v)
            return new_dict
        elif isinstance(obj, list):
            return [self._clean_json_keys(item) for item in obj]
        else:
            return obj

    async def _get_available_tools(self):
        # Fetch tool list from CCXT MCP server via adapter if not cached
        if not self.available_tools:
             logger.debug("Fetching available tools...")
             await self.ccxt_adapter.ensure_connected() # Use ensure_connected instead of connect
             self.available_tools = await self.ccxt_adapter.get_tools_list()
             logger.debug(f"Available tools fetched: {len(self.available_tools) if self.available_tools else 0} tools")
        return self.available_tools

    async def process_decision_intent(self, intent_data):
        """
        Process a trading decision intent from the Decision Module.
        (Intent structure documented above)
        """
        # Use provided decision_id or generate a new one
        decision_id = intent_data.get('decision_id', str(uuid.uuid4()))
        # Add decision_id back to intent_data if it was generated
        intent_data['decision_id'] = decision_id
        action = intent_data.get('action')
        logger.info(f"Processing intent {decision_id}, Action: {action}")
        logger.debug(f"Full Intent Data: {intent_data}")


        try:
            # 1. Get available tools for the LLM
            tools_schema = await self._get_available_tools()

            # 2. LLM Proposes Tool Calls
            prompt = self._create_llm_prompt(intent_data, tools_schema)
            # Ensure llm_provider is initialized before calling methods
            if not self.llm_provider:
                logger.error("LLM Provider not initialized")
                raise RuntimeError("LLM Provider not initialized")
                
            logger.info(f"Generating LLM response for {decision_id}")
            llm_response_text = await self.llm_provider.generate(prompt)
            logger.info(f"LLM response received for {decision_id}")
            
            # Use our robust _parse_llm_response method instead of direct json.loads
            try:
                # Parse using our robust method that handles markdown and various formats
                proposed_tool_calls = await self._parse_llm_response(llm_response_text)
                logger.info(f"Successfully parsed LLM response using _parse_llm_response")
                logger.info(f"Parsed tool calls: {json.dumps(proposed_tool_calls)}")
                
                # Clean JSON keys to handle quoted keys like '"type"' -> 'type'
                proposed_tool_calls = self._clean_json_keys(proposed_tool_calls)
                logger.info(f"Cleaned JSON keys in proposed tool calls")
                logger.info(f"Cleaned tool calls: {json.dumps(proposed_tool_calls)}")
                
            except Exception as e:
                logger.error(f"Error parsing LLM response: {e}")
                logger.debug(f"LLM response: {llm_response_text}")
                # No fallback, just use empty list
                proposed_tool_calls = []
                
            logger.info(f"LLM proposed {len(proposed_tool_calls)} tool calls for {decision_id}")


            # 3. Compiler Validates Proposed Calls
            # If we have no tool calls to validate, raise a specific error
            if not proposed_tool_calls:
                logger.error(f"No tool calls to validate for decision {decision_id}")
                raise TradeCompilerValidationError("LLM provided no valid tool calls to execute trade")
            
            # Pass equity, existing positions etc. as context if needed for risk checks    
            current_context = await self._get_validation_context()
            logger.debug(f"Calling compiler for {decision_id} with context: {current_context}")
            
            try:
                validated_tool_calls = await self.trade_compiler.validate_and_finalize(
                    proposed_tool_calls,
                    intent_data, # Pass original intent for context
                    current_context
                )
                logger.info(f"Compiler validated calls for {decision_id}: {validated_tool_calls}")
            except Exception as e:
                logger.error(f"Error during validation for {decision_id}: {str(e)}")
                if not proposed_tool_calls:
                    raise TradeCompilerValidationError("LLM provided no valid tool calls to execute trade")
                raise


            # 4. Execute Validated Calls based on action
            if action in ['enter_long', 'enter_short']:
                result = await self._execute_entry(intent_data, validated_tool_calls)
            elif action == 'exit':
                result = await self._execute_exit(intent_data, validated_tool_calls)
            elif action == 'adjust':
                result = await self._execute_adjustment(intent_data, validated_tool_calls)
            else:
                logger.error(f"Unknown action '{action}' received in intent {decision_id}")
                raise ValueError(f"Unknown action: {action}")

            logger.info(f"Intent {decision_id} processed successfully.")
            return {'status': 'success', 'decision_id': decision_id, **result}

        except TradeCompilerValidationError as e:
            # Log the rejection and reason
            logger.warning(f"Trade intent {decision_id} rejected by compiler: {e}")
            await self._log_trade_rejection(decision_id, intent_data, str(e), proposed_tool_calls) # Log proposed calls too
            return {'status': 'rejected', 'decision_id': decision_id, 'reason': str(e)}
        except Exception as e:
            # Log general processing error
            logger.error(f"Error processing decision {decision_id}: {e}", exc_info=True)
            await self._log_trade_error(decision_id, intent_data, str(e))
            return {'status': 'error', 'decision_id': decision_id, 'message': str(e)}

    async def _execute_entry(self, intent_data, validated_tool_calls):
        """
        Execute an entry trade based on validated tool calls.
        
        Args:
            intent_data: Dictionary with intent information
            validated_tool_calls: List of validated tool calls to execute
            
        Returns:
            Dictionary with execution results and trade_id
        """
        decision_id = intent_data.get('decision_id')
        logger.info(f"Executing entry for intent {decision_id}...")
        
        try:
            # Ensure CCXT adapter is connected
            await self.ccxt_adapter.ensure_connected()
            
            # Execute calls via adapter with timeout
            try:
                execution_results = await asyncio.wait_for(
                    self.ccxt_adapter.execute_batch(validated_tool_calls),
                    timeout=20.0  # 20 second timeout to prevent hanging on exchange calls
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout executing batch of {len(validated_tool_calls)} tool calls")
                return {
                    'status': 'error',
                    'message': f"Execution timed out after 20 seconds",
                    'execution': None
                }
            logger.info(f"Execution results for entry {decision_id}: {json.dumps(execution_results)[:200]}...")
            
            # Check for errors in execution results
            if not self._check_execution_success(execution_results):
                error_msgs = self._extract_error_messages(execution_results)
                logger.error(f"Errors in execution for intent {decision_id}: {error_msgs}")
                return {
                    'status': 'error',
                    'message': f"Execution failed: {error_msgs}",
                    'execution': execution_results
                }
            
            # Extract trade details from execution results
            trade_details = self._extract_trade_details(execution_results)
            
            # Create trade record in database
            status = 'pending' if not trade_details.get('entry_order_id') else 'open'
            trade_id = await self._create_trade_record(intent_data, trade_details, status, execution_results, validated_tool_calls)
            
            # Register trade with manager for position tracking (if we have order ID)
            if status == 'open' and trade_id:
                await self.trade_manager.register_trade(trade_id)
                
            logger.info(f"Executed entry for intent {decision_id}, trade_id: {trade_id}, status: {status}")
            
            return {
                'status': 'success',
                'trade_id': trade_id,
                'execution': execution_results,
                'trade_status': status
            }
            
        except Exception as e:
            logger.error(f"Error executing entry for intent {decision_id}: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f"Internal error: {str(e)}",
                'execution': None
            }

    async def _execute_exit(self, intent_data, validated_tool_calls):
        """
        Execute an exit trade based on validated tool calls.
        
        Args:
            intent_data: Dictionary with intent information
            validated_tool_calls: List of validated tool calls to execute
            
        Returns:
            Dictionary with execution results and trade_id
        """
        trade_id = intent_data.get('trade_id')
        decision_id = intent_data.get('decision_id')
        
        if not trade_id:
            logger.error(f"Missing trade_id for exit action in intent {decision_id}")
            return {
                'status': 'error',
                'message': "trade_id is required for exit action",
                'execution': None
            }
            
        try:
            # Verify the trade exists and is open in DB
            trade_data = await db.get_trade(trade_id=trade_id, user_id=self.user_id)
            
            if not trade_data:
                logger.error(f"Trade {trade_id} not found for exit action")
                return {
                    'status': 'error',
                    'message': f"Trade {trade_id} not found",
                    'execution': None
                }
                
            if trade_data.get('trade_status') != 'open':
                logger.warning(f"Attempted to exit trade {trade_id} with status {trade_data.get('trade_status')}")
                # If already closed, just return success
                if trade_data.get('trade_status') == 'closed':
                    return {
                        'status': 'success',
                        'message': f"Trade {trade_id} is already closed",
                        'trade_id': trade_id,
                        'execution': None
                    }
                # Otherwise, error
                return {
                    'status': 'error',
                    'message': f"Cannot exit trade with status {trade_data.get('trade_status')}",
                    'execution': None
                }
                
            # Ensure CCXT adapter is connected
            await self.ccxt_adapter.ensure_connected()
            
            logger.info(f"Executing exit for trade {trade_id} based on intent {decision_id}")
            
            # Execute calls via adapter with timeout
            try:
                execution_results = await asyncio.wait_for(
                    self.ccxt_adapter.execute_batch(validated_tool_calls),
                    timeout=20.0  # 20 second timeout to prevent hanging on exchange calls
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout executing exit for trade {trade_id}")
                return {
                    'status': 'error',
                    'message': f"Exit execution timed out after 20 seconds",
                    'trade_id': trade_id,
                    'execution': None
                }
            logger.info(f"Execution results for exit {decision_id} (Trade {trade_id}): {json.dumps(execution_results)[:200]}...")
            
            # Check for errors in execution results
            if not self._check_execution_success(execution_results):
                error_msgs = self._extract_error_messages(execution_results)
                logger.error(f"Errors in execution for exit {decision_id}: {error_msgs}")
                return {
                    'status': 'error',
                    'message': f"Exit execution failed: {error_msgs}",
                    'trade_id': trade_id,
                    'execution': execution_results
                }
            
            # Extract exit details from execution results
            exit_details = self._extract_exit_details(execution_results)
            
            # Update trade record to 'closed' in database
            await self._update_trade_record(
                trade_id, 
                'closed', 
                exit_details, 
                execution_results, 
                validated_tool_calls
            )
            
            # Unregister trade from manager
            await self.trade_manager.unregister_trade(trade_id)
            
            logger.info(f"Executed exit for trade {trade_id}")
            
            return {
                'status': 'success',
                'trade_id': trade_id,
                'execution': execution_results,
                'trade_status': 'closed'
            }
            
        except Exception as e:
            logger.error(f"Error executing exit for trade {trade_id}: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f"Internal error: {str(e)}",
                'trade_id': trade_id,
                'execution': None
            }

    async def _execute_adjustment(self, intent_data, validated_tool_calls):
        """
        Execute trade adjustment based on validated tool calls.
        
        Args:
            intent_data: Dictionary with intent information
            validated_tool_calls: List of validated tool calls to execute
            
        Returns:
            Dictionary with execution results and trade_id
        """
        trade_id = intent_data.get('trade_id')
        decision_id = intent_data.get('decision_id')
        
        if not trade_id:
            logger.error(f"Missing trade_id for adjust action in intent {decision_id}")
            return {
                'status': 'error',
                'message': "trade_id is required for adjust action",
                'execution': None
            }
            
        try:
            # Verify the trade exists and is open in DB
            trade_data = await db.get_trade(trade_id=trade_id, user_id=self.user_id)
            
            if not trade_data:
                logger.error(f"Trade {trade_id} not found for adjustment action")
                return {
                    'status': 'error',
                    'message': f"Trade {trade_id} not found",
                    'execution': None
                }
                
            if trade_data.get('trade_status') != 'open':
                logger.warning(f"Attempted to adjust trade {trade_id} with status {trade_data.get('trade_status')}")
                return {
                    'status': 'error',
                    'message': f"Cannot adjust trade with status {trade_data.get('trade_status')}",
                    'execution': None
                }
                
            # Ensure CCXT adapter is connected
            await self.ccxt_adapter.ensure_connected()
            
            logger.info(f"Executing adjustment for trade {trade_id} based on intent {decision_id}")
            
            # Execute calls via adapter with timeout
            try:
                execution_results = await asyncio.wait_for(
                    self.ccxt_adapter.execute_batch(validated_tool_calls),
                    timeout=20.0  # 20 second timeout to prevent hanging on exchange calls
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout executing adjustment for trade {trade_id}")
                return {
                    'status': 'error',
                    'message': f"Adjustment execution timed out after 20 seconds",
                    'trade_id': trade_id,
                    'execution': None
                }
            logger.info(f"Execution results for adjustment {decision_id} (Trade {trade_id}): {json.dumps(execution_results)[:200]}...")
            
            # Check for errors in execution results
            if not self._check_execution_success(execution_results):
                error_msgs = self._extract_error_messages(execution_results)
                logger.error(f"Errors in execution for adjustment {decision_id}: {error_msgs}")
                return {
                    'status': 'error',
                    'message': f"Adjustment execution failed: {error_msgs}",
                    'trade_id': trade_id,
                    'execution': execution_results
                }
            
            # Extract adjustment details from execution results
            adjustment_details = self._extract_adjustment_details(execution_results, intent_data)
            
            # Update trade record in database
            await self._update_trade_record(
                trade_id, 
                'open', 
                adjustment_details, 
                execution_results, 
                validated_tool_calls,
                is_adjustment=True
            )
            
            # Notify trade manager of adjustment
            await self.trade_manager.notify_adjustment(trade_id, adjustment_details)
            
            logger.info(f"Executed adjustment for trade {trade_id}")
            
            return {
                'status': 'success',
                'trade_id': trade_id,
                'execution': execution_results,
                'trade_status': 'open',
                'adjustment': adjustment_details
            }
            
        except Exception as e:
            logger.error(f"Error executing adjustment for trade {trade_id}: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f"Internal error: {str(e)}",
                'trade_id': trade_id,
                'execution': None
            }
            
    def _check_execution_success(self, execution_results: Dict) -> bool:
        """
        Check if execution was successful by examining MCP results.
        
        Args:
            execution_results: Dictionary with MCP execution results
            
        Returns:
            True if execution was successful, False otherwise
        """
        # No results means failure
        if not execution_results or 'results' not in execution_results:
            return False
            
        results = execution_results.get('results', [])
        
        # Check each result for errors
        for result in results:
            # Skip if no result or tool
            if not isinstance(result, dict):
                continue
                
            # Check for error field
            if result.get('error'):
                return False
                
            # Check result field for errors
            result_data = result.get('result')
            if isinstance(result_data, dict) and result_data.get('error'):
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
        
        if not execution_results or 'results' not in execution_results:
            return "No execution results returned"
            
        results = execution_results.get('results', [])
        
        # Check each result for errors
        for result in results:
            # Skip if no result or tool
            if not isinstance(result, dict):
                continue
                
            # Extract error from error field
            if result.get('error'):
                error_msgs.append(f"{result.get('tool', 'Unknown tool')}: {result.get('error')}")
                
            # Extract error from result field
            result_data = result.get('result')
            if isinstance(result_data, dict) and result_data.get('error'):
                error_msgs.append(f"{result.get('tool', 'Unknown tool')}: {result_data.get('error')}")
                
        if not error_msgs:
            return "Unknown execution error"
            
        return "; ".join(error_msgs)

    # --- LLM Prompt and Response Handling ---
    def _create_llm_prompt(self, intent_data, tools_schema):
        """
        Create a detailed prompt for the LLM to generate tool calls.
        
        Args:
            intent_data: Dictionary containing trade intent information
            tools_schema: Schema of available CCXT MCP tools
            
        Returns:
            Formatted prompt string
        """
        # Extract key information from intent for highlighting
        action = intent_data.get('action', 'unknown')
        symbol = intent_data.get('symbol', 'unknown')
        leverage = intent_data.get('leverage', 1)
        
        # Format tools schema to be more readable
        formatted_tools = []
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
            
        # Construct prompt similar to simplified_llm_mcp_test.py but adapted for our use case
        # The f-string + JSON curly braces cause conflicts, so escape carefully
        prompt = f"""You are a trading agent responsible for translating high-level trading intents into specific CCXT MCP tool calls for execution on cryptocurrency exchanges.

Here are the tools available to you:
{tools_text}

Here is the trading intent to execute:
```json
{json.dumps(intent_data, indent=2)}
```

IMPORTANT INSTRUCTIONS:
1. All tool parameters MUST use snake_case (with underscores), not camelCase.
2. You MUST use the exchange "{intent_data.get('exchange', 'bitmex')}" for all tool calls that require an exchange.
3. Based on the trading intent to {action_phrase}, determine the correct sequence of tool calls.

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

    def _parse_llm_response(self, llm_response_text):
        """
        Parse LLM text response into a list of tool call dictionaries.
        
        Args:
            llm_response_text: Raw text response from the LLM
            
        Returns:
            List of tool call dictionaries
            
        Raises:
            ValueError: If response cannot be parsed into valid format
        """
        # Add more defensive handling for llm_response_text
        if not llm_response_text:
            logger.error("Empty LLM response received")
            return []  # Return empty list instead of raising error
        
        if not isinstance(llm_response_text, str):
            logger.error(f"Non-string LLM response of type {type(llm_response_text)}: {llm_response_text}")
            # Try to convert to string if possible
            try:
                llm_response_text = str(llm_response_text)
            except Exception as e:
                logger.error(f"Failed to convert non-string response to string: {e}")
                return []  # Return empty list instead of raising error
        
        # Clean up the response to extract JSON
        response_text = llm_response_text.strip()
        logger.debug(f"Parsing LLM response (truncated): {response_text[:200]}...")
        
        # Look for JSON content in markdown code blocks
        json_content = None
        
        # Try to find ```json ... ``` pattern
        json_block_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', response_text)
        if json_block_match:
            json_content = json_block_match.group(1)
            logger.debug("Found JSON in code block")
        else:
            # Look for array pattern not in code block
            array_match = re.search(r'\[\s*{[\s\S]*}\s*\]', response_text)
            if array_match:
                json_content = array_match.group(0)
                logger.debug("Found JSON array pattern")
            else:
                # Attempt to use entire response as last resort
                # Remove any non-JSON text before and after the array
                cleaned_text = re.sub(r'^[^[]*(\[[\s\S]*\])[^]]*$', r'\1', response_text)
                if cleaned_text.startswith('[') and cleaned_text.endswith(']'):
                    json_content = cleaned_text
                    logger.debug("Using cleaned text as JSON")
                else:
                    # Just try the raw response as a last resort
                    json_content = response_text
                    logger.debug("Using full response text as JSON")
        
        logger.debug(f"Extracted JSON content (truncated): {json_content[:200] if json_content else 'None'}...")
        
        # Parse the content to JSON
        try:
            if not json_content:
                logger.warning("Could not find JSON content in response, returning empty list")
                return []  # Return empty list instead of raising error
                
            # Parse JSON
            parsed = json.loads(json_content)
            
            # Validate structure
            if not isinstance(parsed, list):
                logger.warning("LLM response was valid JSON but not a list, returning empty list")
                return []  # Return empty list instead of raising error
                
            # Validate list items
            valid_items = []
            
            for idx, item in enumerate(parsed):
                if not isinstance(item, dict):
                    logger.warning(f"Item {idx} is not a dictionary, skipping")
                    continue
                    
                if 'tool' not in item:
                    logger.warning(f"Item {idx} missing 'tool' key, skipping")
                    continue
                    
                if 'parameters' not in item:
                    logger.warning(f"Item {idx} missing 'parameters' key, skipping")
                    # Try to fix common issue: parameters as a sibling instead of nested
                    if any(k != 'tool' for k in item.keys()):
                        # Create fixed item with proper structure
                        fixed_item = {
                            'tool': item['tool'],
                            'parameters': {k: v for k, v in item.items() if k != 'tool'}
                        }
                        logger.info(f"Fixed item {idx} by restructuring parameters")
                        valid_items.append(fixed_item)
                    continue
                    
                # Add valid item
                valid_items.append(item)
                
            if not valid_items:
                logger.warning("No valid tool calls found in response, returning empty list")
                return []  # Return empty list instead of raising error
                
            logger.info(f"Successfully parsed {len(valid_items)} tool calls from LLM response")
            return valid_items
            
        except json.JSONDecodeError as e:
            # Try to recover from common JSON errors
            try:
                # Replace single quotes with double quotes
                fixed_content = json_content.replace("'", "\"")
                # Fix unquoted property names
                fixed_content = re.sub(r'(\s*)(\w+)(\s*):([^/])', r'\1"\2"\3:\4', fixed_content)
                
                parsed = json.loads(fixed_content)
                logger.warning(f"Recovered from JSON parse error by fixing format issues")
                
                # Validate structure after recovery
                if not isinstance(parsed, list):
                    logger.warning("Fixed JSON was not a list, returning empty list")
                    return []  # Return empty list instead of raising error
                    
                return parsed
                
            except (json.JSONDecodeError, ValueError) as recovery_error:
                logger.error(f"Failed to parse LLM response as JSON: {e}. Recovery also failed: {recovery_error}")
                logger.debug(f"Problematic response: {llm_response_text}")
                return []  # Return empty list instead of raising error
                
        except ValueError as e:
            logger.error(f"LLM response format error: {e}")
            logger.debug(f"Problematic response: {llm_response_text}")
            return []  # Return empty list instead of raising error
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}", exc_info=True)
            return []  # Return empty list instead of raising error


    async def _get_validation_context(self):
        # Fetch necessary context for validation (e.g., current equity, open positions)
        # Example: equity = await self.ccxt_adapter.fetch_balance() # Needs fetchBalance tool
        logger.debug("Fetching validation context (using mock equity)")
        return {"equity": 10000.0} # Placeholder - replace with actual balance fetching

    async def _log_trade_rejection(self, decision_id, intent_data, reason, proposed_calls):
        # Log rejection details to database or logging system
        log_data = {
            "decision_id": decision_id,
            "user_id": self.user_id,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "reason": reason,
            "intent_data": intent_data,
            "proposed_calls": proposed_calls
        }
        logger.warning(f"Trade Rejected: {json.dumps(log_data)}")
        # await db.log_rejection(log_data) # Replace with actual DB call
        pass

    async def _log_trade_error(self, decision_id, intent_data, error_message):
        # Log processing error details
        log_data = {
            "decision_id": decision_id,
            "user_id": self.user_id,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "error_message": error_message,
            "intent_data": intent_data
        }
        logger.error(f"Trade Error: {json.dumps(log_data)}")
        # await db.log_error(log_data) # Replace with actual DB call
        pass

    def _extract_trade_details(self, execution_results):
        # Parse execution results to get entry order ID, avg price, etc.
        # This depends heavily on the MCP server's response format for createOrder
        # Example: Assuming results = {'results': [{'tool': 'createOrder', 'result': {'id': '123', 'average': 65000.5}}]}
        entry_order_id = None
        avg_price = None
        try:
             if execution_results and 'results' in execution_results:
                  for res in execution_results['results']:
                       if res.get('tool') == 'createOrder' and isinstance(res.get('result'), dict):
                            entry_order_id = res['result'].get('id') # CCXT order ID
                            avg_price = res['result'].get('average') # Filled price
                            # May need to handle multiple createOrder calls if SL/TP placed immediately
                            break # Take first createOrder result for now
        except Exception as e:
             logger.error(f"Error parsing execution results for trade details: {e}", exc_info=True)

        details = {"entry_order_id": entry_order_id}
        if avg_price is not None:
            details["entry_price"] = float(avg_price)

        logger.debug(f"Extracted trade details: {details}")
        return details

    def _extract_exit_details(self, execution_results):
        # Parse execution results for exit order
        exit_order_id = None
        avg_price = None
        try:
             if execution_results and 'results' in execution_results:
                  for res in execution_results['results']:
                       # Assuming exit is also a createOrder call (market or limit reduceOnly)
                       if res.get('tool') == 'createOrder' and isinstance(res.get('result'), dict):
                            exit_order_id = res['result'].get('id')
                            avg_price = res['result'].get('average')
                            break
        except Exception as e:
             logger.error(f"Error parsing execution results for exit details: {e}", exc_info=True)

        details = {"exit_order_id": exit_order_id}
        if avg_price is not None:
             details["exit_price"] = float(avg_price) # Add exit price if available

        logger.debug(f"Extracted exit details: {details}")
        return details

    def _extract_adjustment_details(self, execution_results, intent_data=None):
        """
        Extract adjustment details from execution results.
        
        Args:
            execution_results: Dictionary with execution results
            intent_data: Original intent data (optional)
            
        Returns:
            Dictionary with adjustment details
        """
        details = {
            "adjustment_time": datetime.utcnow().isoformat() + 'Z',
            "raw_results": execution_results
        }
        
        # Extract information from the intent data if provided
        if intent_data:
            # Add adjustment reasoning from intent if available
            if intent_data.get('reasoning'):
                details['reasoning'] = intent_data.get('reasoning')
                
            # Add new stop loss or take profit values from intent if available
            if intent_data.get('stop_loss_price'):
                details['stop_loss'] = intent_data.get('stop_loss_price')
                
            if intent_data.get('take_profit_price'):
                details['take_profit'] = intent_data.get('take_profit_price')
        
        # Try to extract cancel/create order IDs from the execution results
        results = execution_results.get('results', [])
        for result in results:
            if not isinstance(result, dict):
                continue
                
            tool = result.get('tool', '')
            result_data = result.get('result')
            
            # Extract cancel order ID
            if tool == 'cancel_order' and isinstance(result_data, dict) and result_data.get('id'):
                details['cancelled_order_id'] = result_data.get('id')
                
            # Extract create order ID for new stop loss or take profit
            if tool == 'create_order' and isinstance(result_data, dict) and result_data.get('id'):
                order_type = result_data.get('type', '').lower()
                
                # Determine if this is a stop loss or take profit order
                is_stop_loss = False
                is_take_profit = False
                
                if 'stop' in order_type or 'stoploss' in str(result_data).lower() or 'stop_loss' in str(result_data).lower():
                    is_stop_loss = True
                    details['new_stop_loss_order_id'] = result_data.get('id')
                    
                if 'takeprofit' in str(result_data).lower() or 'take_profit' in str(result_data).lower() or 'limit' in order_type:
                    is_take_profit = True
                    details['new_take_profit_order_id'] = result_data.get('id')
        
        logger.debug(f"Extracted adjustment details: {json.dumps(details)}")
        return details

    async def _create_trade_record(self, intent_data, trade_details, status, execution_results, validated_calls):
        # Create a new record in the 'trades' database table
        trade_id = str(uuid.uuid4())
        record = {
            "trade_id": trade_id,
            "user_id": self.user_id,
            "config_id": self.config.get('config_id'), # Assuming config has an ID
            "decision_id": intent_data.get('decision_id'),
            "exchange": intent_data.get('exchange', self.config.get('default_exchange')),
            "pair": intent_data.get('symbol'),
            "direction": 'long' if intent_data.get('action') == 'enter_long' else 'short',
            "timeframe": intent_data.get('timeframe'),
            "entry_price": trade_details.get('entry_price'), # From execution
            "position_size": None, # TODO: Calculate or get from execution if possible
            "collateral_amount": None, # TODO: Calculate
            "leverage": intent_data.get('leverage'),
            "stop_loss": intent_data.get('stop_loss_price'), # Initial intent SL
            "take_profit": intent_data.get('take_profit_price'), # Initial intent TP
            "confidence_score": intent_data.get('confidence'),
            "reasoning_log": intent_data.get('reasoning'),
            "trade_status": status,
            "risk_rejected": False, # Assuming this function only called on success
            "risk_reason": None,
            "entry_order_id": trade_details.get('entry_order_id'),
            "client_order_id": validated_calls[0]['parameters'].get('clientOrderId') if validated_calls else None, # Example Coid
            "created_at": datetime.utcnow().isoformat() + 'Z',
            "entry_time": datetime.utcnow().isoformat() + 'Z' if status == 'open' else None, # Approx time
            "execution_details": {"intent": intent_data, "validated_calls": validated_calls, "results": execution_results},
            "adjustments": []
        }
        logger.info(f"Creating trade record {trade_id} with status {status}")
        # await db.create_trade(record) # Replace with actual DB call
        return trade_id # Return the generated trade_id

    async def _update_trade_record(self, trade_id, status, details, execution_results, validated_calls, is_adjustment=False):
        # Update an existing record in the 'trades' database table
        update_data = {
            "trade_status": status,
            "last_updated": datetime.utcnow().isoformat() + 'Z'
        }
        if status == 'closed':
             update_data["closed_at"] = datetime.utcnow().isoformat() + 'Z'
             update_data["exit_order_id"] = details.get('exit_order_id')
             # TODO: Calculate final P/L here based on entry/exit details
             # update_data["profit_loss"] = calculate_pnl(...)

        # Append execution details for audit trail
        # Note: This could make the JSONB field large over time
        exec_details_update = {"validated_calls": validated_calls, "results": execution_results}

        if is_adjustment:
             # Add adjustment details to the adjustments array field
             adjustment_entry = {
                 "timestamp": datetime.utcnow().isoformat() + 'Z',
                 "details": details,
                 "execution": exec_details_update
             }
             # This requires fetching the existing adjustments and appending
             # update_data["adjustments"] = existing_adjustments + [adjustment_entry]
             # Also update SL/TP fields if they were changed by the adjustment intent
             # update_data["stop_loss"] = intent_data.get('new_stop_loss') # Example
             pass # Placeholder for adjustment update logic
        else:
             # Overwrite or append execution details? Appending might be better for audit.
             # update_data["execution_details"] = existing_details + [exec_details_update] # If appending
             pass # Placeholder for non-adjustment update logic

        logger.info(f"Updating trade record {trade_id} to status {status}")
        # await db.update_trade(trade_id, update_data) # Replace with actual DB call
        pass

    # --- Methods called by other components (e.g., Decision Module) ---
    async def get_trade_status(self, trade_id):
         # Fetch status from TradeManager cache or DB
         logger.info(f"Querying status for trade {trade_id}")
         cached_status = await self.trade_manager.get_cached_status(trade_id)
         if cached_status:
              logger.debug(f"Returning cached status for {trade_id}")
              # Maybe enrich with latest price/pnl if available in cache?
              return {"trade_id": trade_id, **cached_status} # Return cached dict
         else:
              logger.debug(f"Fetching status from DB for {trade_id}")
              db_trade = await db.get_trade(trade_id=trade_id, user_id=self.user_id) # Replace with actual DB call
              if db_trade:
                   return db_trade # Return full DB record
              else:
                   return {"status": "error", "message": f"Trade {trade_id} not found"}


    async def get_active_trades(self):
         # Fetch list of active trades from TradeManager cache
         logger.info("Querying all active trades from TradeManager cache")
         active_trades_list = list(self.trade_manager.active_trades.values())
         # Optionally enrich with latest price/pnl if cached?
         return active_trades_list # Return list of trade dicts


class TradeManager:
    """
    Manages the lifecycle of active trades, including position tracking 
    and monitoring for stop-loss/take-profit conditions.
    
    Responsibilities:
    - Maintain state of active trades
    - Poll exchange for position updates
    - Check for SL/TP conditions
    - Provide position status to the TradingEngine
    - Manage trade lifecycle events
    """
    
    def __init__(self, 
                 user_id: str, 
                 config: Dict, 
                 ccxt_adapter,
                 trade_compiler, 
                 trading_engine_ref=None,
                 polling_interval: int = 60):
        """
        Initialize the TradeManager.
        
        Args:
            user_id: User identifier
            config: Configuration dictionary
            ccxt_adapter: Instance of CCXTMCPAdapter for exchange communications
            trade_compiler: Instance of TradeCompiler for validating commands
            trading_engine_ref: Reference to TradingEngine for callbacks (e.g., auto exits)
            polling_interval: Interval in seconds for polling position updates
        """
        self.user_id = user_id
        self.config = config
        self.ccxt_adapter = ccxt_adapter
        self.trade_compiler = trade_compiler
        self.trading_engine_ref = trading_engine_ref
        self.polling_interval = polling_interval
        
        # Dictionary to track active trades: {trade_id: trade_data}
        self.active_trades = {}
        
        # Polling task
        self.polling_task = None
        self.running = False
        
        # Logger setup with context
        self.logger = logger.bind(user_id=user_id)
        self.logger.info("TradeManager initialized")
    
    async def start(self):
        """
        Start the trade manager and polling task.
        """
        if self.running:
            self.logger.warning("TradeManager already running")
            return
            
        self.running = True
        self.logger.info(f"Starting TradeManager with polling interval {self.polling_interval}s")
        
        # Load active trades from database
        await self._load_active_trades_from_db()
        
        # Start polling task
        self.polling_task = asyncio.create_task(self._polling_loop())
        
    async def stop(self):
        """
        Stop the trade manager and polling task.
        """
        if not self.running:
            return
            
        self.running = False
        self.logger.info("Stopping TradeManager")
        
        # Cancel polling task
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
            self.polling_task = None
    
    async def register_trade(self, trade_id: str):
        """
        Register a new trade for tracking.
        
        Args:
            trade_id: Unique identifier for the trade
        """
        self.logger.info(f"Registering trade {trade_id} for tracking")
        
        # Fetch trade details from database
        trade_data = await db.get_trade(trade_id=trade_id, user_id=self.user_id)
        
        if not trade_data:
            self.logger.error(f"Trade {trade_id} not found in database")
            return False
            
        # Add to active trades dictionary
        self.active_trades[trade_id] = {
            "trade_id": trade_id,
            "symbol": trade_data.get("pair"),
            "exchange": trade_data.get("exchange"),
            "direction": trade_data.get("direction"),
            "entry_price": trade_data.get("entry_price"),
            "stop_loss": trade_data.get("stop_loss"),
            "take_profit": trade_data.get("take_profit"),
            "position_size": trade_data.get("position_size"),
            "leverage": trade_data.get("leverage"),
            "last_update": datetime.utcnow().isoformat() + 'Z',
            "status": trade_data.get("trade_status", "open"),
            "entry_order_id": trade_data.get("entry_order_id"),
            "exit_triggered": False,
            "current_price": None,
            "unrealized_pnl": None
        }
        
        self.logger.info(f"Trade {trade_id} registered for tracking")
        return True
    
    async def unregister_trade(self, trade_id: str):
        """
        Unregister a trade from tracking.
        
        Args:
            trade_id: Unique identifier for the trade
        """
        if trade_id in self.active_trades:
            self.logger.info(f"Unregistering trade {trade_id} from tracking")
            del self.active_trades[trade_id]
            return True
        else:
            self.logger.warning(f"Attempted to unregister trade {trade_id} that is not being tracked")
            return False
    
    async def notify_adjustment(self, trade_id: str, adjustment_details: Dict):
        """
        Update trade data after an adjustment.
        
        Args:
            trade_id: Unique identifier for the trade
            adjustment_details: Details of the adjustment
        """
        if trade_id not in self.active_trades:
            self.logger.warning(f"Adjustment notification for trade {trade_id} that is not being tracked")
            return False
            
        # Update trade data with adjusted values (if provided)
        for key, value in adjustment_details.items():
            if key in ["stop_loss", "take_profit", "position_size"]:
                self.active_trades[trade_id][key] = value
                
        self.active_trades[trade_id]["last_update"] = datetime.utcnow().isoformat() + 'Z'
        self.logger.info(f"Trade {trade_id} updated with adjustment: {adjustment_details}")
        return True
    
    async def get_cached_status(self, trade_id: str) -> Optional[Dict]:
        """
        Get the cached status of a trade.
        
        Args:
            trade_id: Unique identifier for the trade
            
        Returns:
            Dictionary with trade status or None if not found
        """
        return self.active_trades.get(trade_id)
    
    async def _load_active_trades_from_db(self):
        """
        Load active trades from the database.
        """
        self.logger.info("Loading active trades from database")
        
        # Fetch active trades from database
        active_trades = await db.get_active_trades(user_id=self.user_id, status="open")
        
        # Register each trade
        for trade_data in active_trades:
            trade_id = trade_data.get("trade_id")
            if trade_id:
                await self.register_trade(trade_id)
        
        self.logger.info(f"Loaded {len(self.active_trades)} active trades")
    
    async def _polling_loop(self):
        """
        Main polling loop for position updates.
        """
        self.logger.info("Starting position polling loop")
        
        while self.running:
            try:
                # Only poll if there are active trades
                if self.active_trades:
                    self.logger.debug(f"Polling {len(self.active_trades)} active trades...")
                    await self._poll_positions()
                    
                # Wait for next polling interval
                await asyncio.sleep(self.polling_interval)
                
            except asyncio.CancelledError:
                self.logger.info("Polling task cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in polling loop: {e}", exc_info=True)
                # Continue polling even after errors (with a short delay)
                await asyncio.sleep(5)
    
    async def _poll_positions(self):
        """
        Poll exchange for position updates.
        """
        try:
            # Group positions by exchange for efficient polling
            exchanges_to_poll = set(trade.get("exchange") for trade in self.active_trades.values())
            
            for exchange in exchanges_to_poll:
                # Get positions for this exchange
                positions = await self._fetch_positions(exchange)
                
                # Check each active trade on this exchange
                for trade_id, trade_data in list(self.active_trades.items()):
                    if trade_data.get("exchange") != exchange:
                        continue
                        
                    # Find position for this trade
                    symbol = trade_data.get("symbol")
                    position = self._find_position_in_results(positions, symbol)
                    
                    if position:
                        # Position found - update trade data
                        await self._update_trade_with_position(trade_id, trade_data, position)
                    else:
                        # No position found - handle potential exit
                        await self._handle_missing_position(trade_id, trade_data)
                        
        except Exception as e:
            self.logger.error(f"Error polling positions: {e}", exc_info=True)
    
    async def _fetch_positions(self, exchange: str) -> List[Dict]:
        """
        Fetch positions from the exchange.
        
        Args:
            exchange: Exchange identifier
            
        Returns:
            List of position objects
        """
        try:
            # Prepare call to fetch positions
            tool_call = {
                "tool": "fetch_positions",
                "parameters": {}
            }
            
            # Use the CCXTMCPAdapter to fetch positions
            positions_result = await self.ccxt_adapter.call_tool("fetch_positions", {})
            
            # Return positions list or empty list if error
            if isinstance(positions_result, list):
                return positions_result
            else:
                self.logger.warning(f"Error fetching positions from {exchange}: {positions_result}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching positions from {exchange}: {e}", exc_info=True)
            return []
    
    def _find_position_in_results(self, positions: List[Dict], symbol: str) -> Optional[Dict]:
        """
        Find a position for a specific symbol in the results.
        
        Args:
            positions: List of position objects
            symbol: Symbol to find
            
        Returns:
            Position object or None if not found
        """
        # Try to match exactly
        for position in positions:
            if position.get("symbol") == symbol:
                return position
                
        # Try to match with CCXT symbol mapping if exact match not found
        mapped_symbol = self.ccxt_adapter.map_symbol(symbol)
        for position in positions:
            if position.get("symbol") == mapped_symbol:
                return position
                
        # Position not found
        return None
    
    async def _update_trade_with_position(self, trade_id: str, trade_data: Dict, position: Dict):
        """
        Update trade data with position information.
        
        Args:
            trade_id: Unique identifier for the trade
            trade_data: Current trade data
            position: Position object from exchange
        """
        # Extract position details
        position_size = position.get("contracts") or position.get("amount") or 0
        current_price = position.get("markPrice") or position.get("entryPrice") or 0
        unrealized_pnl = position.get("unrealizedPnl") or 0
        liquidation_price = position.get("liquidationPrice")
        
        # Ignore if size is zero
        if position_size == 0:
            self.logger.debug(f"Position has zero size for trade {trade_id}")
            return
            
        # Update trade data
        previous_price = trade_data.get("current_price")
        previous_data_timestamp = trade_data.get("last_update")
        
        trade_data.update({
            "current_price": current_price,
            "position_size": position_size,
            "unrealized_pnl": unrealized_pnl,
            "liquidation_price": liquidation_price,
            "last_update": datetime.utcnow().isoformat() + 'Z'
        })
        
        # Check for stop loss / take profit
        if not trade_data.get("exit_triggered"):
            exit_triggered = await self._check_exit_conditions(trade_id, trade_data, current_price)
            
            if exit_triggered:
                trade_data["exit_triggered"] = True
        
        # Update database with position status (not on every poll to reduce DB load)
        if previous_price is None or abs(current_price - previous_price) > 0.01 * previous_price:
            await self._update_db_with_status(trade_id, trade_data)
    
    async def _handle_missing_position(self, trade_id: str, trade_data: Dict):
        """
        Handle case where a position is not found on the exchange.
        
        Args:
            trade_id: Unique identifier for the trade
            trade_data: Current trade data
        """
        # Check if already marked as exit_triggered to avoid duplicate checks
        if trade_data.get("exit_triggered"):
            return
            
        # Check if we should ignore missing positions (e.g., during position setup)
        now = datetime.utcnow()
        last_update_str = trade_data.get("last_update", "")
        if last_update_str:
            try:
                last_update = datetime.fromisoformat(last_update_str.rstrip('Z'))
                seconds_since_update = (now - last_update).total_seconds()
                
                # If position was just created, it might not be visible yet
                if seconds_since_update < 60:
                    self.logger.debug(f"Position for trade {trade_id} not found, but was updated recently. Ignoring.")
                    return
            except ValueError:
                # Invalid datetime format, proceed with missing position check
                pass
                
        # Position should exist but was not found - consider it closed
        self.logger.warning(f"Position for trade {trade_id} not found on exchange. Marking as closed.")
        
        # Update trade status
        trade_data.update({
            "status": "closed",
            "current_price": None,
            "position_size": 0,
            "unrealized_pnl": 0,
            "last_update": datetime.utcnow().isoformat() + 'Z',
            "exit_triggered": True
        })
        
        # Update database
        await self._update_db_with_status(trade_id, trade_data, force_closed=True)
        
        # Remove from active trades
        await self.unregister_trade(trade_id)
    
    async def _check_exit_conditions(self, trade_id: str, trade_data: Dict, current_price: float) -> bool:
        """
        Check if stop loss or take profit conditions are met.
        
        Args:
            trade_id: Unique identifier for the trade
            trade_data: Current trade data
            current_price: Current price
            
        Returns:
            True if exit was triggered, False otherwise
        """
        # Skip check if no stop loss or take profit set
        stop_loss = trade_data.get("stop_loss")
        take_profit = trade_data.get("take_profit")
        
        if not stop_loss and not take_profit:
            return False
            
        # Get trade direction
        direction = trade_data.get("direction", "").lower()
        if not direction:
            self.logger.warning(f"Trade {trade_id} has no direction set, skipping exit check")
            return False
            
        # Check if stop loss triggered
        sl_triggered = False
        if stop_loss:
            if direction == "long" and current_price <= stop_loss:
                sl_triggered = True
                self.logger.info(f"Stop loss triggered for long trade {trade_id}: {current_price} <= {stop_loss}")
            elif direction == "short" and current_price >= stop_loss:
                sl_triggered = True
                self.logger.info(f"Stop loss triggered for short trade {trade_id}: {current_price} >= {stop_loss}")
                
        # Check if take profit triggered
        tp_triggered = False
        if take_profit:
            if direction == "long" and current_price >= take_profit:
                tp_triggered = True
                self.logger.info(f"Take profit triggered for long trade {trade_id}: {current_price} >= {take_profit}")
            elif direction == "short" and current_price <= take_profit:
                tp_triggered = True
                self.logger.info(f"Take profit triggered for short trade {trade_id}: {current_price} <= {take_profit}")
                
        # If either condition triggered, execute exit
        if sl_triggered or tp_triggered:
            exit_reason = "stop_loss" if sl_triggered else "take_profit"
            await self._execute_auto_exit(trade_id, trade_data, exit_reason)
            return True
            
        return False
    
    async def _execute_auto_exit(self, trade_id: str, trade_data: Dict, exit_reason: str):
        """
        Execute an automatic exit for a trade.
        
        Args:
            trade_id: Unique identifier for the trade
            trade_data: Current trade data
            exit_reason: Reason for exit ("stop_loss" or "take_profit")
        """
        self.logger.info(f"Executing automatic exit for trade {trade_id} due to {exit_reason}")
        
        # Check if TradingEngine reference is available
        if not self.trading_engine_ref:
            self.logger.error(f"Cannot execute auto exit: TradingEngine reference not available")
            return
            
        # Create exit intent
        exit_intent = self._create_exit_intent(trade_id, trade_data, exit_reason)
        
        try:
            # Execute exit via TradingEngine
            result = await self.trading_engine_ref.process_decision_intent(exit_intent)
            
            if result.get("status") == "success":
                self.logger.info(f"Auto exit for trade {trade_id} executed successfully")
            else:
                self.logger.error(f"Auto exit for trade {trade_id} failed: {result.get('reason', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Error executing auto exit for trade {trade_id}: {e}", exc_info=True)
    
    def _create_exit_intent(self, trade_id: str, trade_data: Dict, exit_reason: str) -> Dict:
        """
        Create exit intent for automatic exit.
        
        Args:
            trade_id: Unique identifier for the trade
            trade_data: Current trade data
            exit_reason: Reason for exit
            
        Returns:
            Exit intent dictionary
        """
        return {
            "decision_id": str(uuid.uuid4()),
            "action": "exit",
            "trade_id": trade_id,
            "symbol": trade_data.get("symbol"),
            "exchange": trade_data.get("exchange"),
            "reason": f"Automatic exit triggered by {exit_reason}",
            "confidence": 1.0,  # High confidence for auto exits
            "auto_exit": True,
            "exit_reason": exit_reason
        }
    
    async def _update_db_with_status(self, trade_id: str, trade_data: Dict, force_closed: bool = False):
        """
        Update database with current trade status.
        
        Args:
            trade_id: Unique identifier for the trade
            trade_data: Current trade data
            force_closed: If True, force status to "closed"
        """
        # Prepare database update
        status = "closed" if force_closed else trade_data.get("status", "open")
        current_price = trade_data.get("current_price")
        position_size = trade_data.get("position_size")
        unrealized_pnl = trade_data.get("unrealized_pnl")
        
        update_data = {
            "trade_status": status,
            "current_price": current_price,
            "position_size": position_size,
            "unrealized_pnl": unrealized_pnl,
            "last_updated": datetime.utcnow().isoformat() + 'Z'
        }
        
        # Add liquidation price if available
        if "liquidation_price" in trade_data:
            update_data["liquidation_price"] = trade_data["liquidation_price"]
            
        # Handle closed trades
        if status == "closed":
            update_data["closed_at"] = datetime.utcnow().isoformat() + 'Z'
            
            # Calculate final P/L if available
            if unrealized_pnl is not None:
                update_data["profit_loss"] = unrealized_pnl
                
        try:
            # Update database
            # await db.update_trade(trade_id, update_data)
            self.logger.debug(f"Updated database for trade {trade_id} with status {status}")
            
            # Create trade_updates record for history
            trade_update = {
                "update_id": str(uuid.uuid4()),
                "trade_id": trade_id,
                "user_id": self.user_id,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "price": current_price,
                "unrealized_pnl": unrealized_pnl,
                "position_size": position_size,
                "update_type": "periodic"
            }
            
            # await db.create_trade_update(trade_update)
            self.logger.debug(f"Created trade update record for trade {trade_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating database for trade {trade_id}: {e}", exc_info=True)
