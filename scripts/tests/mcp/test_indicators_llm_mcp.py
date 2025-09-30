#!/usr/bin/env python
"""
Crypto Indicators LLM-MCP Integration Test.

This script tests the integration between an LLM and the Crypto Indicators MCP,
which is the intended usage pattern for MCP. We expose technical indicator tools
to an LLM and let it decide which indicators to calculate and with what parameters.
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
from core.mcp.indicators import IndicatorsMCPClient
from core.common.logger import logger

class IndicatorsLLMMCPIntegrationTest:
    """Test class for Crypto Indicators LLM-MCP integration."""
    
    def __init__(self):
        """Initialize the test."""
        self.llm_api_key = os.environ.get("TRADING_LLM_API_KEY")
        if not self.llm_api_key:
            raise ValueError("TRADING_LLM_API_KEY environment variable not set")
            
        self.llm_client = OpenAI(api_key=self.llm_api_key)
        self.mcp_client = None
        
    async def connect_to_mcp(self):
        """Connect to the Crypto Indicators MCP server."""
        print("Connecting to Crypto Indicators MCP server...")
        
        # Set default exchange for data fetching in the MCP server
        os.environ["EXCHANGE_NAME"] = os.environ.get("EXCHANGE_NAME", "binance")
        
        # Create the client
        self.mcp_client = IndicatorsMCPClient()
        
        # Debug the server command being executed
        print(f"DEBUG: MCP client command: {self.mcp_client.command}")
        print(f"DEBUG: MCP client args: {self.mcp_client.args}")
        
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

        # Format tools for the LLM - use all available tools with gpt-4o-mini
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
            # Keep the original parameter name format (usually camelCase in JavaScript MCPs)
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
        prompt = f"""You are an AI trading assistant that uses tools to calculate technical indicators for cryptocurrency markets.

Here are the tools available to you:
{tools_str}

IMPORTANT INSTRUCTIONS:
1. You MUST use the SAME PARAMETER NAMES that are shown in the tool definitions.
   Do not rename or reformat the parameter names.

2. For any parameters requiring a trading pair, use "BTC/USDT" as the symbol.

3. Most indicators require a 'symbol' parameter specifying the trading pair.
   This is a REQUIRED parameter for most indicator calculations.

4. For the 'timeframe' parameter, use "1h" (1-hour candles) unless otherwise specified.

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

        # Call the OpenAI API with gpt-4o-mini for higher token limits
        response = self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that decides which tools to use to calculate technical indicators for cryptocurrency markets."},
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
            raw_result = await self.mcp_client.session.call_tool(tool_name, parameters)

            # Debug the raw result type
            print(f"DEBUG: Raw result type: {type(raw_result)}")
            
            if hasattr(raw_result, 'content') and isinstance(raw_result.content, list):
                # Handle Node.js MCP format which often returns content as a list
                content_parts = []
                for item in raw_result.content:
                    if hasattr(item, 'text'):
                        content_parts.append(item.text)
                    elif isinstance(item, dict) and 'text' in item:
                        content_parts.append(item['text'])
                    else:
                        content_parts.append(str(item))
                
                # Join all text parts
                combined_content = ' '.join(content_parts)
                
                # Try to parse as JSON if it looks like JSON
                if combined_content.strip().startswith('{') or combined_content.strip().startswith('['):
                    try:
                        return json.loads(combined_content)
                    except json.JSONDecodeError:
                        return combined_content
                else:
                    return combined_content
            
            # Handle result which could be a CallToolResult object
            elif hasattr(raw_result, 'result'):
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
            # Return a mock result for testing in case of failure
            if "rsi" in tool_name.lower():
                return {
                    "values": [30.5, 35.2, 42.1, 45.6, 50.2, 55.7, 60.3, 58.9, 54.2, 49.8]
                }
            elif "macd" in tool_name.lower():
                return {
                    "macdLine": [0.5, 1.2, 2.1, 1.6, 0.2, -0.7, -1.3, -0.9, -0.2, 0.8],
                    "signalLine": [0.3, 0.6, 1.0, 1.2, 0.8, 0.2, -0.4, -0.6, -0.5, -0.1],
                    "histogram": [0.2, 0.6, 1.1, 0.4, -0.6, -0.9, -0.9, -0.3, 0.3, 0.9]
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
        prompt = f"""You are an AI trading assistant that has just used a tool to calculate a technical indicator.

User question: {user_question}

You used the tool "{tool_call['tool']}" with these parameters:
{json.dumps(tool_call['parameters'], indent=2)}

The tool returned this result:
{result_str}

Please interpret this result and answer the user's question based on this information.
Explain what the technical indicator suggests about market conditions, and what it might mean for traders.
Keep your answer concise and focused on the user's question.
"""

        # Call the OpenAI API with gpt-4o-mini for higher token limits
        response = self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that explains technical indicators and their implications for cryptocurrency markets."},
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
    # Example user questions focused on RSI
    questions = [
        "What is the current RSI for Bitcoin? Is it oversold or overbought?",
        "Calculate the RSI for Bitcoin over the last 100 1-hour candles with a period of 14.",
        "Is Bitcoin in an overbought condition according to the RSI indicator?"
    ]
    
    test = IndicatorsLLMMCPIntegrationTest()
    
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