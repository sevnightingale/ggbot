#!/usr/bin/env python
"""
Simplified LLM-MCP Integration Test.

This script tests the integration between an LLM and MCP tools,
using a simplified server implementation that directly handles credentials.
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

class SimplifiedLLMMCPIntegrationTest:
    """Simplified test class for LLM-MCP integration."""
    
    def __init__(self):
        """Initialize the test."""
        self.llm_api_key = os.environ.get("TRADING_LLM_API_KEY")
        if not self.llm_api_key:
            raise ValueError("TRADING_LLM_API_KEY environment variable not set")
            
        self.exchange_id = os.environ.get("EXCHANGE_NAME", "bitmex")
        print(f"Using exchange: {self.exchange_id}")
        self.llm_client = OpenAI(api_key=self.llm_api_key)
        self.mcp_client = None
        
    async def connect_to_mcp(self):
        """Connect to the MCP server using the fixed implementation."""
        print(f"Connecting to CCXT MCP server with exchange {self.exchange_id}...")
        
        # Ensure environment variables are set
        os.environ["EXCHANGE_API"] = os.environ.get("EXCHANGE_API", "REDACTED_EXCHANGE_API_KEY")
        os.environ["EXCHANGE_SECRET"] = os.environ.get("EXCHANGE_SECRET", "REDACTED_EXCHANGE_SECRET")
        os.environ["EXCHANGE_NAME"] = self.exchange_id
        
        print(f"DEBUG: Using credentials for {self.exchange_id}")
        print(f"DEBUG: API key exists: {bool(os.environ.get('EXCHANGE_API'))}")
        print(f"DEBUG: Secret exists: {bool(os.environ.get('EXCHANGE_SECRET'))}")

        # Use our simplified server implementation
        server_path = str(Path(__file__).parent / "fixed_ccxt_mcp_server.py")
        print(f"DEBUG: Using server script at: {server_path}")
        
        # Create the MCP client with explicit server path
        self.mcp_client = CCXTMCPClient(
            exchange_id=self.exchange_id,
            use_local_server=True,
            server_path=server_path
        )

        await self.mcp_client.connect()
        print("Connected to MCP server")
        
    async def get_available_tools(self):
        """Get the list of available tools from the MCP server."""
        if not self.mcp_client or not self.mcp_client.is_connected:
            await self.connect_to_mcp()

        print("Getting available tools...")
        tools = await self.mcp_client.session.get_tools()

        # Debug the raw tools
        if tools:
            print(f"DEBUG: Found {len(tools)} tools")
            print(f"DEBUG: First tool name: {tools[0].name}")

        # Format tools for the LLM
        formatted_tools = []
        for tool in tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "parameters": self._parse_input_schema(tool.inputSchema)
            }
            formatted_tools.append(tool_info)

        return formatted_tools
    
    def _parse_input_schema(self, schema):
        """Parse the JSON schema to a more readable format for the LLM."""
        if not schema or not isinstance(schema, dict):
            return {}

        properties = schema.get('properties', {})
        required = schema.get('required', [])

        params = {}
        for param_name, param_info in properties.items():
            description = param_info.get('description', '')

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
1. All tool parameters MUST use snake_case (with underscores), not camelCase.
   For example, use "exchange_id" instead of "exchangeId".

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
            
        try:
            # Execute the tool call
            result = await self.mcp_client.session.call_tool(tool_name, parameters)
            print(f"DEBUG: Raw result type: {type(result)}")
            
            # Extract result if needed
            if hasattr(result, 'result'):
                result = result.result
                
            # Convert to serializable format if needed
            if isinstance(result, dict):
                # Create a copy with only serializable values
                clean_result = {}
                for k, v in result.items():
                    if isinstance(v, (str, int, float, bool, list, dict, type(None))):
                        clean_result[k] = v
                    else:
                        clean_result[k] = str(v)
                return clean_result
            elif isinstance(result, list):
                return result[:10]  # Limit to 10 items
            else:
                return str(result)
        except Exception as e:
            print(f"Error executing tool call: {str(e)}")
            return {"error": str(e)}
        
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
            
            print("\n----- Tool Result -----")
            print(json.dumps(result, indent=2))
            
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
    
    test = SimplifiedLLMMCPIntegrationTest()
    
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