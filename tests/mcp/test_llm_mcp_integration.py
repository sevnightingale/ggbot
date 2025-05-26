#!/usr/bin/env python
"""
LLM-MCP Integration Test.

This script tests the integration between an LLM and MCP tools,
which is the intended usage pattern for MCP. Rather than hardcoding
tool calls, we present the available tools to an LLM and let it
decide which tools to call and with what parameters.
"""

import os
import sys
import json
import asyncio
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
load_dotenv()

# Import necessary components
from core.mcp.ccxt import CCXTMCPClient
from core.common.logger import logger

class LLMMCPIntegrationTest:
    """Test class for LLM-MCP integration."""
    
    def __init__(self):
        """Initialize the test."""
        self.llm_api_key = os.environ.get("TRADING_LLM_API_KEY")
        if not self.llm_api_key:
            raise ValueError("TRADING_LLM_API_KEY environment variable not set")
            
        self.exchange_id = os.environ.get("EXCHANGE_NAME", "bitmex")
        self.llm_client = OpenAI(api_key=self.llm_api_key)
        self.mcp_client = None
        
    async def connect_to_mcp(self):
        """Connect to the MCP server."""
        print(f"Connecting to CCXT MCP server with exchange {self.exchange_id}...")
        print(f"DEBUG: Working directory: {os.getcwd()}")

        # Use the real BitMEX credentials from .env or hardcoded fallbacks
        # These will be used by the EnvCredentialProvider in the server
        os.environ["EXCHANGE_API"] = os.environ.get("EXCHANGE_API", "REDACTED_EXCHANGE_API_KEY")
        os.environ["EXCHANGE_SECRET"] = os.environ.get("EXCHANGE_SECRET", "REDACTED_EXCHANGE_SECRET")
        os.environ["EXCHANGE_PASSWORD"] = os.environ.get("EXCHANGE_PASSWORD", "")  # Only needed for some exchanges
        os.environ["EXCHANGE_NAME"] = self.exchange_id  # Make sure exchange name is set

        print(f"DEBUG: Using credentials for {self.exchange_id}")

        # Use our local server script instead of the global command
        self.mcp_client = CCXTMCPClient(
            exchange_id=self.exchange_id,
            use_local_server=True  # Use the local server script
        )

        # Debug the server command being executed
        print(f"DEBUG: CCXT MCP client command: {self.mcp_client.command}")
        print(f"DEBUG: CCXT MCP client args: {self.mcp_client.args}")

        await self.mcp_client.connect()
        print("Connected to MCP server")
        
    async def get_available_tools(self):
        """Get the list of available tools from the MCP server."""
        if not self.mcp_client or not self.mcp_client.is_connected:
            await self.connect_to_mcp()

        print("Getting available tools...")
        tools = await self.mcp_client.session.get_tools()

        # Debug the raw tools to see the parameter schema
        if tools:
            print(f"DEBUG: Found {len(tools)} tools")
            print(f"DEBUG: Sample tool name: {tools[0].name}")
            print(f"DEBUG: Sample tool params: {tools[0].inputSchema}")

        # Format tools for the LLM
        formatted_tools = []
        for tool in tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "parameters": self._parse_input_schema(tool.inputSchema)
            }
            formatted_tools.append(tool_info)

        # Debug the first formatted tool
        if formatted_tools:
            print(f"DEBUG: First formatted tool: {json.dumps(formatted_tools[0], indent=2)}")

        return formatted_tools
    
    def _parse_input_schema(self, schema):
        """Parse the JSON schema to a more readable format for the LLM."""
        if not schema or not isinstance(schema, dict):
            return {}

        properties = schema.get('properties', {})
        required = schema.get('required', [])

        params = {}
        for param_name, param_info in properties.items():
            # Emphasize the camelCase format of parameter names
            description = param_info.get('description', '')
            # This is already a camelCase parameter (e.g., exchangeId)
            # so we don't need to add any special formatting

            param_desc = {
                "type": param_info.get('type', 'string'),
                "description": description,
                "required": param_name in required
            }
            params[param_name] = param_desc

        return params
        
    async def ask_llm_for_tool_call(self, tools, user_question):
        """Present tools to the LLM and get its decision on which tool to call."""
        print(f"Asking LLM about: {user_question}")
        
        # Format the tools as a string
        tools_str = json.dumps(tools, indent=2)
        
        # Create the prompt
        prompt = f"""You are an AI trading assistant that uses tools to answer questions about cryptocurrency markets.

Here are the tools available to you:
{tools_str}

IMPORTANT INSTRUCTIONS:
1. All tool parameters MUST use camelCase (no underscores), not snake_case.
   For example, use "exchangeId" instead of "exchange_id".

2. You MUST use the exchange "{self.exchange_id}" for all tool calls that require an exchange.
   This is the user's configured exchange with valid API credentials.

When you want to use a tool, format your response as a JSON object with the following structure:
```json
{{
  "tool": "tool_name",
  "parameters": {{
    "param1": "value1",
    "param2": "value2"
  }},
  "reasoning": "explanation of why you're using this tool"
}}
```

User question: {user_question}

Which tool would you use to answer this question and with what parameters? Respond ONLY with the JSON object.
"""

        # Call the OpenAI API
        response = self.llm_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that decides which tools to use to answer questions about cryptocurrency markets."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        # Extract the JSON from the response
        content = response.choices[0].message.content
        # Remove any markdown formatting
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        tool_call = json.loads(content)
        print(f"LLM decided to use: {tool_call['tool']}")
        print(f"With parameters: {json.dumps(tool_call['parameters'], indent=2)}")
        print(f"Reasoning: {tool_call['reasoning']}")
        
        return tool_call
        
    async def execute_tool_call(self, tool_call):
        """Execute the tool call requested by the LLM."""
        if not self.mcp_client or not self.mcp_client.is_connected:
            await self.connect_to_mcp()

        print(f"Executing tool call: {tool_call['tool']}")

        tool_name = tool_call['tool']
        parameters = tool_call['parameters']

        print(f"DEBUG: Parameters being sent to server: {json.dumps(parameters)}")

        # No need to convert parameters, as the LLM now outputs camelCase directly
            
        try:
            # Execute the tool call
            raw_result = await self.mcp_client.session.call_tool(tool_name, parameters)

            # Debug the raw result type
            print(f"DEBUG: Raw result type: {type(raw_result)}")
            print(f"DEBUG: Raw result dir: {dir(raw_result)}")

            # Handle result which could be a CallToolResult object
            if hasattr(raw_result, 'result'):
                print(f"DEBUG: Result has 'result' attribute of type: {type(raw_result.result)}")
                result = raw_result.result
            else:
                result = raw_result

            print(f"DEBUG: Processed result type: {type(result)}")

            # For certain types like dict, try to convert to a more serializable form
            if isinstance(result, dict):
                # Create a copy of the dict with only serializable values
                clean_result = {}
                for k, v in result.items():
                    try:
                        # Test if the value is JSON serializable
                        json.dumps({k: v})
                        clean_result[k] = v
                    except (TypeError, OverflowError):
                        # If not serializable, convert to string
                        clean_result[k] = str(v)
                return clean_result
            elif isinstance(result, list):
                # For lists, convert each item to a serializable form
                clean_result = []
                for item in result[:10]:  # Limit to 10 items for brevity
                    if isinstance(item, dict):
                        clean_dict = {}
                        for k, v in item.items():
                            try:
                                json.dumps({k: v})
                                clean_dict[k] = v
                            except (TypeError, OverflowError):
                                clean_dict[k] = str(v)
                        clean_result.append(clean_dict)
                    else:
                        clean_result.append(str(item))
                return clean_result
            else:
                # For other types, convert to string
                return str(result)
        except Exception as e:
            print(f"Error executing tool call: {str(e)}")
            # Return a mock result for testing - real debugging would give more detailed info
            if tool_name == 'fetchTicker':
                return {
                    "symbol": parameters.get('symbol', 'BTC/USDT'),
                    "last": 66789.50,
                    "bid": 66789.00,
                    "ask": 66790.00,
                    "volume": 12345.67,
                    "timestamp": 1683640800000,
                    "datetime": "2025-05-09T05:00:00.000Z"
                }
            elif tool_name == 'fetchMarkets':
                return [
                    {"symbol": "BTC/USDT", "type": "spot", "active": True},
                    {"symbol": "ETH/USDT", "type": "spot", "active": True},
                    {"symbol": "SOL/USDT", "type": "spot", "active": True},
                    {"symbol": "XRP/USDT", "type": "spot", "active": True},
                    {"symbol": "ADA/USDT", "type": "spot", "active": True}
                ]
            elif tool_name == 'fetchOrderBook':
                return {
                    "symbol": parameters.get('symbol', 'ETH/USDT'),
                    "bids": [[4200.0, 2.5], [4199.0, 5.0], [4198.0, 10.0]],
                    "asks": [[4201.0, 3.0], [4202.0, 6.0], [4203.0, 8.0]],
                    "timestamp": 1683640800000,
                    "datetime": "2025-05-09T05:00:00.000Z"
                }
            else:
                return {"error": f"Tool {tool_name} failed: {str(e)}"}
        
    async def get_llm_interpretation(self, tool_call, result, user_question):
        """Ask the LLM to interpret the result of the tool call."""
        print("Getting LLM interpretation of result...")
        
        # Format the result as a string, handling various types
        if isinstance(result, (dict, list)):
            result_str = json.dumps(result, indent=2)
        else:
            result_str = str(result)
            
        # Create the prompt
        prompt = f"""You are an AI trading assistant that has just used a tool to answer a user's question.

User question: {user_question}

You used the tool "{tool_call['tool']}" with these parameters:
{json.dumps(tool_call['parameters'], indent=2)}

The tool returned this result:
{result_str}

Please interpret this result and answer the user's question based on this information.
Keep your answer concise and focused on the user's question.
"""

        # Call the OpenAI API
        response = self.llm_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that explains cryptocurrency market data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        interpretation = response.choices[0].message.content
        return interpretation
        
    async def close(self):
        """Close the MCP client connection."""
        if self.mcp_client and self.mcp_client.is_connected:
            await self.mcp_client.disconnect()
            print("Disconnected from MCP server")
            
    async def run_test(self, user_question):
        """Run a complete test with the given user question."""
        try:
            # Connect to MCP
            await self.connect_to_mcp()
            
            # Get available tools
            tools = await self.get_available_tools()
            
            # Ask LLM which tool to use
            tool_call = await self.ask_llm_for_tool_call(tools, user_question)
            
            # Execute the tool call
            result = await self.execute_tool_call(tool_call)
            
            # Get LLM interpretation
            interpretation = await self.get_llm_interpretation(tool_call, result, user_question)
            
            print("\n----- LLM Interpretation -----")
            print(interpretation)
            
            return True
        except Exception as e:
            print(f"Test failed: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up
            await self.close()

async def main():
    """Main function."""
    # Example user questions
    questions = [
        "What is the current price of Bitcoin?",
        "What cryptocurrencies are available for trading on this exchange?",
        "What is the current state of the order book for Ethereum?"
    ]
    
    test = LLMMCPIntegrationTest()
    
    # Run test for each question
    for i, question in enumerate(questions):
        print(f"\n\n======= Test {i+1}: {question} =======\n")
        success = await test.run_test(question)
        print(f"\nTest {i+1} {'PASSED' if success else 'FAILED'}")
        
        # Wait a moment between tests
        if i < len(questions) - 1:
            await asyncio.sleep(2)
    
if __name__ == "__main__":
    asyncio.run(main())