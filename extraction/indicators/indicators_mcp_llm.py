"""
LLM-mediated Crypto Indicators MCP implementation.

This module provides an IndicatorComputer implementation that uses an LLM to:
1. Select appropriate technical indicators based on user configuration
2. Interpret the results of technical indicators
3. Store both raw indicator values and interpretations
"""

import os
import json
import asyncio
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from openai import OpenAI, AsyncOpenAI

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.mcp.indicators import IndicatorsMCPClient
from extraction.interfaces.indicator_computer import IndicatorComputer


class IndicatorsMCPLLM(IndicatorComputer):
    """
    LLM-mediated IndicatorComputer implementation that uses the Crypto Indicators MCP.
    
    This class combines the strengths of a Large Language Model with the Crypto Indicators MCP
    to provide both technical indicators and meaningful interpretations of those indicators.
    """
    
    def __init__(self, 
                 user_id=DEFAULT_USER_ID, 
                 exchange_name="binance", 
                 selected_indicators=None,
                 llm_model="gpt-4o-mini"):
        """
        Initialize the LLM-mediated MCP indicator calculator.
        
        Args:
            user_id: User ID to associate with this indicator computer
            exchange_name: Name of the exchange to use for data (default: binance)
            selected_indicators: List of indicator names to use (default: None, uses predefined set)
            llm_model: LLM model to use for interpretation (default: gpt-4o-mini)
        """
        self.user_id = user_id
        self.exchange_name = exchange_name
        self.llm_model = llm_model
        self._log = logger.bind(user_id=user_id, component="IndicatorsMCPLLM")
        self.mcp_client = None
        self.llm_client = None
        
        # Define the default selection of indicators and their parameters
        self.default_indicators = {
            'RSI': {'period': 14},
            'MACD': {'fastPeriod': 12, 'slowPeriod': 26, 'signalPeriod': 9},
            'BollingerBands': {'period': 20, 'stdDev': 2.0},
            'SMA': [{'period': 20}, {'period': 50}, {'period': 200}],
            'EMA': [{'period': 9}, {'period': 21}, {'period': 55}]
        }
        
        # Use user-selected indicators if provided, otherwise use defaults
        self.selected_indicators = selected_indicators or self.default_indicators
        
        # Check if LLM API key is available
        self.llm_api_key = os.environ.get("TRADING_LLM_API_KEY")
        if not self.llm_api_key:
            self._log.warning("TRADING_LLM_API_KEY environment variable not set. LLM interpretation will be disabled.")
        
    async def _ensure_clients_connected(self):
        """
        Ensure both MCP and LLM clients are connected.
        
        Creates new clients if they don't exist, or reconnects existing clients.
        """
        # Connect to MCP client
        if not self.mcp_client:
            self._log.info(f"Creating new Indicators MCP client for {self.exchange_name}")
            self.mcp_client = IndicatorsMCPClient(
                user_id=self.user_id,
                exchange_name=self.exchange_name
            )
            await self.mcp_client.connect()
        elif not self.mcp_client.is_connected:
            self._log.info(f"Reconnecting existing Indicators MCP client")
            await self.mcp_client.connect()
        
        # Initialize LLM client if API key is available
        if self.llm_api_key and not self.llm_client:
            self._log.info("Initializing LLM client")
            self.llm_client = AsyncOpenAI(api_key=self.llm_api_key)
    
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators and interpret them using LLM.
        
        This is a synchronous wrapper that runs the async computation in a new event loop.
        
        Args:
            df: DataFrame containing OHLCV price data
            
        Returns:
            DataFrame with added indicator columns and interpretations
        """
        self._log.info("Computing indicators using LLM-mediated Crypto Indicators MCP")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run the async computation in the event loop
            return loop.run_until_complete(self._compute_indicators_async(df))
        finally:
            # Clean up the event loop
            loop.close()
    
    async def _compute_indicators_async(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Asynchronously calculate and interpret technical indicators.
        
        Args:
            df: DataFrame containing OHLCV price data
            
        Returns:
            DataFrame with added indicator columns and LLM interpretations
        """
        if df.empty:
            self._log.warning("Empty DataFrame provided, cannot compute indicators")
            return df
            
        # Ensure the required columns exist
        required_columns = self.get_required_columns()
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            self._log.error(f"Missing required columns: {missing}")
            return df
            
        try:
            # Ensure the clients are connected
            await self._ensure_clients_connected()
            
            # Create a copy of the DataFrame
            result_df = df.copy()
            
            # Extract prices for indicators - handle both capitalized and lowercase column names
            close_prices = df['Close'].tolist() if 'Close' in df.columns else df['close'].tolist()
            
            # Add symbol information for MCP tool calls
            # Try to extract symbol from DataFrame or use a default
            symbol = "BTC/USDT"  # Default symbol
            
            # Try different ways to get the symbol from the DataFrame
            if 'Symbol' in df.columns and len(df) > 0:
                symbol = df['Symbol'].iloc[0]
            elif 'symbol' in df.columns and len(df) > 0:
                symbol = df['symbol'].iloc[0]
            
            # Same for timeframe
            timeframe = "1h"  # Default timeframe
            if 'Timeframe' in df.columns and len(df) > 0:
                timeframe = df['Timeframe'].iloc[0]
            elif 'timeframe' in df.columns and len(df) > 0:
                timeframe = df['timeframe'].iloc[0]
            
            self._log.info(f"Calculating indicators for {symbol} on {timeframe} timeframe")
            
            # Get available tools from MCP
            tools = await self.mcp_client.session.get_tools()
            
            # Format tools for LLM consumption
            formatted_tools = []
            for tool in tools:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": self._parse_input_schema(tool.inputSchema)
                }
                formatted_tools.append(tool_info)
            
            # Filter tools based on selected indicators
            filtered_tools = self._filter_tools_by_selected_indicators(formatted_tools)
            
            # Generate LLM prompt for indicator selection
            prompt = self._generate_indicator_selection_prompt(symbol, timeframe, filtered_tools)
            
            # Prepare to collect indicator calculations and LLM interpretations
            indicator_values = {}
            indicator_interpretations = {}
            
            # If LLM client is available, use it to select and interpret indicators
            if self.llm_client:
                try:
                    # Ask LLM which indicators to calculate
                    tool_calls = await self._ask_llm_for_tool_calls(prompt)
                    
                    # Process each suggested tool call
                    for i, tool_call in enumerate(tool_calls):
                        tool_name = tool_call["tool"]
                        parameters = tool_call["parameters"]
                        
                        # Ensure symbol parameter is included
                        parameters["symbol"] = symbol
                        parameters["timeframe"] = timeframe
                        
                        self._log.info(f"Calling indicator tool: {tool_name}")
                        
                        # Execute the tool call
                        try:
                            raw_result = await self.mcp_client.session.call_tool(tool_name, parameters)
                            processed_result = self._process_tool_result(raw_result)
                            
                            # Extract the indicator name from the tool name (e.g., calculate_relative_strength_index -> RSI)
                            indicator_name = self._get_indicator_name_from_tool(tool_name)
                            
                            # Store the result
                            indicator_values[indicator_name] = processed_result
                            
                            # Record the result in the DataFrame if possible
                            self._add_indicator_to_dataframe(result_df, indicator_name, processed_result)
                            
                        except Exception as e:
                            self._log.error(f"Error calling tool {tool_name}: {str(e)}")
                    
                    # Generate interpretation prompt
                    interpretation_prompt = self._generate_interpretation_prompt(
                        symbol, timeframe, indicator_values
                    )
                    
                    # Get LLM interpretation
                    interpretation = await self._get_llm_interpretation(interpretation_prompt)
                    
                    # Store interpretation in the DataFrame
                    result_df.attrs['llm_interpretation'] = interpretation
                    
                    # Also attach it to the last row for database storage
                    if len(result_df) > 0:
                        result_df.loc[result_df.index[-1], 'llm_interpretation'] = interpretation
                    
                except Exception as e:
                    self._log.error(f"Error during LLM processing: {str(e)}")
            
            # If no LLM client or LLM processing failed, calculate indicators directly
            if not indicator_values:
                self._log.info("Calculating indicators directly without LLM")
                indicator_values = await self._calculate_indicators_directly(close_prices, symbol, timeframe)
                
                # Record the results in the DataFrame
                for indicator_name, result in indicator_values.items():
                    self._add_indicator_to_dataframe(result_df, indicator_name, result)
            
            return result_df
            
        except Exception as e:
            self._log.error(f"Error during indicator calculation process: {str(e)}")
            # Return the original DataFrame if any error occurs
            return df
        finally:
            # Ensure we clean up the MCP client
            if self.mcp_client and self.mcp_client.is_connected:
                try:
                    await self.mcp_client.disconnect()
                    self._log.info("Disconnected from Indicators MCP server")
                except Exception as e:
                    self._log.error(f"Error disconnecting from MCP: {str(e)}")
    
    def _parse_input_schema(self, schema: Dict) -> Dict:
        """
        Parse the JSON schema to a more readable format for the LLM.
        
        Args:
            schema: JSON schema for the tool parameters
            
        Returns:
            Simplified parameter schema for LLM consumption
        """
        if not schema or not isinstance(schema, dict):
            return {}

        properties = schema.get('properties', {})
        required = schema.get('required', [])

        params = {}
        for param_name, param_info in properties.items():
            description = param_info.get('description', '')
            
            params[param_name] = {
                "type": param_info.get('type', 'string'),
                "description": description,
                "required": param_name in required
            }

        return params
    
    def _filter_tools_by_selected_indicators(self, tools: List[Dict]) -> List[Dict]:
        """
        Filter the tools list based on selected indicators.
        
        Args:
            tools: List of all available tools
            
        Returns:
            Filtered list of tools that match selected indicators
        """
        if not self.selected_indicators:
            return tools
        
        filtered_tools = []
        
        for tool in tools:
            tool_name = tool["name"].lower()
            
            # Include all general tools and the ones matching our selected indicators
            if any(ind.lower() in tool_name for ind in self.selected_indicators.keys()):
                filtered_tools.append(tool)
            # Always include general fetch tools
            elif "fetch" in tool_name or "ohlcv" in tool_name:
                filtered_tools.append(tool)
        
        return filtered_tools
    
    def _generate_indicator_selection_prompt(self, symbol: str, timeframe: str, tools: List[Dict]) -> str:
        """
        Generate a prompt for the LLM to select appropriate indicators.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Chart timeframe
            tools: List of available tools
            
        Returns:
            Formatted prompt for the LLM
        """
        # Convert the list of tools to a formatted string
        tools_str = json.dumps(tools, indent=2)
        
        # Get a comma-separated list of selected indicator types
        selected_indicators_str = ", ".join(self.selected_indicators.keys())
        
        prompt = f"""You are an AI trading assistant that calculates technical indicators for cryptocurrency markets. 
You need to analyze {symbol} on a {timeframe} timeframe using the following indicators: {selected_indicators_str}.

Here are the tools available to you:
{tools_str}

IMPORTANT INSTRUCTIONS:
1. You MUST use the tool names EXACTLY as shown (e.g., 'calculate_relative_strength_index').
2. You MUST use the SAME PARAMETER NAMES that are shown in the tool definitions.
3. For parameters requiring a trading pair, use "{symbol}".
4. For parameters requiring a timeframe, use "{timeframe}".
5. Include all required parameters for each tool.

For each selected indicator:
1. Identify the corresponding calculation tool
2. Select appropriate parameters based on industry standards
3. Return a list of tool calls in the following format:

[
  {{
    "tool": "tool_name",
    "parameters": {{
      "param1": "value1",
      "param2": "value2"
    }}
  }},
  {{
    "tool": "another_tool_name",
    "parameters": {{
      "param1": "value1",
      "param2": "value2"
    }}
  }}
]

Return ONLY a valid JSON array of objects, no additional text.
"""
        return prompt
    
    async def _ask_llm_for_tool_calls(self, prompt: str) -> List[Dict]:
        """
        Ask the LLM which tools to call for the given trading scenario.
        
        Args:
            prompt: Prompt for the LLM
            
        Returns:
            List of tool calls to execute
        """
        self._log.info("Asking LLM for indicator tool selection")
        
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that decides which technical indicator tools to use for cryptocurrency market analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            content = response.choices[0].message.content
            
            # Try to extract JSON from the response
            try:
                # Look for JSON array in the response
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content.strip()
                
                tool_calls = json.loads(json_str)
                
                if isinstance(tool_calls, list):
                    self._log.info(f"LLM suggested {len(tool_calls)} tool calls")
                    return tool_calls
                else:
                    self._log.warning("LLM response not in expected format, defaulting to direct calculation")
                    return []
                    
            except json.JSONDecodeError:
                self._log.warning(f"Failed to parse LLM response as JSON: {content[:100]}...")
                return []
                
        except Exception as e:
            self._log.error(f"Error getting tool calls from LLM: {str(e)}")
            return []
    
    def _process_tool_result(self, raw_result: Any) -> Dict:
        """
        Process the raw tool result into a consistent format.
        
        Args:
            raw_result: Raw result from the MCP tool call
            
        Returns:
            Processed result in a consistent format
        """
        try:
            # Handle different formats that might be returned
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
                        return {"raw": combined_content}
                else:
                    return {"raw": combined_content}
            
            # Handle result which could be a CallToolResult object
            elif hasattr(raw_result, 'result'):
                result = raw_result.result
                
                # If result is a string that looks like JSON, try to parse it
                if isinstance(result, str):
                    try:
                        if result.strip().startswith('{') or result.strip().startswith('['):
                            return json.loads(result)
                    except json.JSONDecodeError:
                        pass
                
                # Otherwise return as is
                return result
            
            # If raw_result is a string that looks like JSON, try to parse it
            elif isinstance(raw_result, str):
                try:
                    if raw_result.strip().startswith('{') or raw_result.strip().startswith('['):
                        return json.loads(raw_result)
                except json.JSONDecodeError:
                    pass
                
                return {"raw": raw_result}
            
            # Handle dictionary result
            elif isinstance(raw_result, dict):
                return raw_result
            
            # Default fallback
            return {"raw": str(raw_result)}
            
        except Exception as e:
            self._log.warning(f"Error processing tool result: {str(e)}")
            return {"error": str(e)}
    
    def _get_indicator_name_from_tool(self, tool_name: str) -> str:
        """
        Extract a clean indicator name from a tool name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Clean indicator name
        """
        # Remove the 'calculate_' prefix if present
        if tool_name.startswith('calculate_'):
            name = tool_name[len('calculate_'):]
        else:
            name = tool_name
        
        # Map common names to cleaner format
        name_mapping = {
            'relative_strength_index': 'RSI',
            'moving_average_convergence_divergence': 'MACD',
            'bollinger_bands': 'BB',
            'simple_moving_average': 'SMA',
            'exponential_moving_average': 'EMA',
            'average_true_range': 'ATR',
            'stochastic_oscillator': 'Stoch',
            'volume_weighted_average_price': 'VWAP',
            'ichimoku_cloud': 'Ichimoku',
            'parabolic_sar': 'PSAR',
            'williams_r': 'Williams %R'
        }
        
        # Try to find a match in our mapping
        for key, value in name_mapping.items():
            if key in name:
                return value
        
        # If no match, convert to title case and return
        return ' '.join(word.capitalize() for word in name.split('_'))
    
    def _add_indicator_to_dataframe(self, df: pd.DataFrame, indicator_name: str, result: Dict) -> None:
        """
        Add indicator values to the DataFrame.
        
        Args:
            df: DataFrame to update
            indicator_name: Name of the indicator
            result: Indicator calculation result
        """
        try:
            # Handle different result formats for different indicators
            if indicator_name == 'RSI':
                if 'values' in result:
                    df[f'{indicator_name}_14'] = pd.Series(result['values'], index=df.index)
                
            elif indicator_name == 'MACD':
                macd_line_key = next((k for k in ['macdLine', 'macd', 'macd_line'] if k in result), None)
                signal_line_key = next((k for k in ['signalLine', 'signal', 'signal_line'] if k in result), None)
                histogram_key = next((k for k in ['histogram', 'hist'] if k in result), None)
                
                if macd_line_key:
                    df['MACD_Line'] = pd.Series(result[macd_line_key], index=df.index)
                if signal_line_key:
                    df['MACD_Signal'] = pd.Series(result[signal_line_key], index=df.index)
                if histogram_key:
                    df['MACD_Histogram'] = pd.Series(result[histogram_key], index=df.index)
            
            elif indicator_name == 'BB':
                upper_key = next((k for k in ['upperBand', 'upper', 'upper_band'] if k in result), None)
                middle_key = next((k for k in ['middleBand', 'middle', 'middle_band', 'sma'] if k in result), None)
                lower_key = next((k for k in ['lowerBand', 'lower', 'lower_band'] if k in result), None)
                
                if upper_key:
                    df['BB_Upper'] = pd.Series(result[upper_key], index=df.index)
                if middle_key:
                    df['BB_Middle'] = pd.Series(result[middle_key], index=df.index)
                if lower_key:
                    df['BB_Lower'] = pd.Series(result[lower_key], index=df.index)
            
            elif indicator_name.startswith('SMA') or indicator_name.startswith('EMA'):
                value_key = next((k for k in ['values', 'sma', 'ema'] if k in result), None)
                
                if value_key:
                    # Extract period from result if available, otherwise use a default
                    period = result.get('period', 14)
                    df[f'{indicator_name}_{period}'] = pd.Series(result[value_key], index=df.index)
            
            else:
                # Generic handling for other indicators
                # Look for a 'values' key or similar
                value_key = next((k for k in ['values', 'data', 'result'] if k in result), None)
                
                if value_key:
                    df[indicator_name] = pd.Series(result[value_key], index=df.index)
                else:
                    # Save the whole result as a JSON string
                    df[indicator_name] = str(result)
        
        except Exception as e:
            self._log.warning(f"Error adding {indicator_name} to DataFrame: {str(e)}")
    
    def _generate_interpretation_prompt(self, symbol: str, timeframe: str, indicator_values: Dict) -> str:
        """
        Generate a prompt for the LLM to interpret the indicators.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Chart timeframe
            indicator_values: Dictionary of indicator values
            
        Returns:
            Formatted prompt for the LLM
        """
        # Format the indicator values for the prompt
        indicator_values_str = json.dumps(indicator_values, indent=2)
        
        prompt = f"""You are an AI trading assistant that provides insight on cryptocurrency market conditions based on technical indicators.

I have just calculated the following technical indicators for {symbol} on a {timeframe} timeframe:

{indicator_values_str}

Please provide a concise interpretation of these indicators:

1. What is the current market trend for {symbol} according to these indicators?
2. Are there any significant signals or patterns?
3. What might these indicators suggest for future price movement?
4. Is the market overbought, oversold, or in neutral territory?
5. What trading strategy would be appropriate based on these indicators?

Provide your interpretation in a clear, structured format that's easy to understand for a trader.
Keep your response under 300 words and focused on actionable insights.
"""
        return prompt
    
    async def _get_llm_interpretation(self, prompt: str) -> str:
        """
        Get the LLM's interpretation of the indicators.
        
        Args:
            prompt: Prompt for the LLM
            
        Returns:
            LLM's interpretation
        """
        self._log.info("Getting LLM interpretation of indicators")
        
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that explains technical indicators and their implications for cryptocurrency markets."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2  # Slightly more creative for interpretations
            )
            
            interpretation = response.choices[0].message.content
            return interpretation
            
        except Exception as e:
            self._log.error(f"Error getting interpretation from LLM: {str(e)}")
            return "Failed to generate interpretation due to an error."
    
    async def _calculate_indicators_directly(self, close_prices: List[float], symbol: str, timeframe: str) -> Dict:
        """
        Calculate indicators directly without LLM mediation.
        
        This is a fallback method if LLM selection isn't available.
        
        Args:
            close_prices: List of close prices
            symbol: Trading pair symbol
            timeframe: Chart timeframe
            
        Returns:
            Dictionary of indicator values
        """
        indicator_values = {}
        
        # Calculate RSI if selected
        if 'RSI' in self.selected_indicators:
            try:
                period = self.selected_indicators['RSI'].get('period', 14)
                result = await self.mcp_client.calculate_rsi(
                    prices=close_prices,
                    period=period,
                    symbol=symbol,
                    timeframe=timeframe
                )
                indicator_values['RSI'] = self._process_tool_result(result)
            except Exception as e:
                self._log.error(f"Error calculating RSI: {str(e)}")
        
        # Calculate MACD if selected
        if 'MACD' in self.selected_indicators:
            try:
                params = self.selected_indicators['MACD']
                fast_period = params.get('fastPeriod', 12)
                slow_period = params.get('slowPeriod', 26)
                signal_period = params.get('signalPeriod', 9)
                
                result = await self.mcp_client.calculate_macd(
                    prices=close_prices,
                    fast_period=fast_period,
                    slow_period=slow_period,
                    signal_period=signal_period,
                    symbol=symbol,
                    timeframe=timeframe
                )
                indicator_values['MACD'] = self._process_tool_result(result)
            except Exception as e:
                self._log.error(f"Error calculating MACD: {str(e)}")
        
        # Calculate Bollinger Bands if selected
        if 'BollingerBands' in self.selected_indicators:
            try:
                params = self.selected_indicators['BollingerBands']
                period = params.get('period', 20)
                std_dev = params.get('stdDev', 2.0)
                
                result = await self.mcp_client.calculate_bollinger_bands(
                    prices=close_prices,
                    period=period,
                    std_dev=std_dev,
                    symbol=symbol,
                    timeframe=timeframe
                )
                indicator_values['BB'] = self._process_tool_result(result)
            except Exception as e:
                self._log.error(f"Error calculating Bollinger Bands: {str(e)}")
        
        # Calculate SMAs if selected
        if 'SMA' in self.selected_indicators:
            sma_params = self.selected_indicators['SMA']
            if isinstance(sma_params, list):
                for params in sma_params:
                    period = params.get('period', 20)
                    try:
                        result = await self.mcp_client.calculate_sma(
                            prices=close_prices,
                            period=period,
                            symbol=symbol,
                            timeframe=timeframe
                        )
                        indicator_values[f'SMA_{period}'] = self._process_tool_result(result)
                    except Exception as e:
                        self._log.error(f"Error calculating SMA-{period}: {str(e)}")
            else:
                period = sma_params.get('period', 20)
                try:
                    result = await self.mcp_client.calculate_sma(
                        prices=close_prices,
                        period=period,
                        symbol=symbol,
                        timeframe=timeframe
                    )
                    indicator_values[f'SMA_{period}'] = self._process_tool_result(result)
                except Exception as e:
                    self._log.error(f"Error calculating SMA-{period}: {str(e)}")
        
        # Calculate EMAs if selected
        if 'EMA' in self.selected_indicators:
            ema_params = self.selected_indicators['EMA']
            if isinstance(ema_params, list):
                for params in ema_params:
                    period = params.get('period', 9)
                    try:
                        result = await self.mcp_client.calculate_ema(
                            prices=close_prices,
                            period=period,
                            symbol=symbol,
                            timeframe=timeframe
                        )
                        indicator_values[f'EMA_{period}'] = self._process_tool_result(result)
                    except Exception as e:
                        self._log.error(f"Error calculating EMA-{period}: {str(e)}")
            else:
                period = ema_params.get('period', 9)
                try:
                    result = await self.mcp_client.calculate_ema(
                        prices=close_prices,
                        period=period,
                        symbol=symbol,
                        timeframe=timeframe
                    )
                    indicator_values[f'EMA_{period}'] = self._process_tool_result(result)
                except Exception as e:
                    self._log.error(f"Error calculating EMA-{period}: {str(e)}")
        
        return indicator_values
    
    def get_indicator_names(self) -> List[str]:
        """Get a list of all indicators that this computer can calculate."""
        indicators = []
        
        # Add basic indicators from selected indicators
        for name in self.selected_indicators.keys():
            indicators.append(name)
        
        # Add more specific indicators based on parameters
        if 'SMA' in self.selected_indicators:
            sma_params = self.selected_indicators['SMA']
            if isinstance(sma_params, list):
                for params in sma_params:
                    period = params.get('period', 20)
                    indicators.append(f'SMA_{period}')
            else:
                period = sma_params.get('period', 20)
                indicators.append(f'SMA_{period}')
        
        if 'EMA' in self.selected_indicators:
            ema_params = self.selected_indicators['EMA']
            if isinstance(ema_params, list):
                for params in ema_params:
                    period = params.get('period', 9)
                    indicators.append(f'EMA_{period}')
            else:
                period = ema_params.get('period', 9)
                indicators.append(f'EMA_{period}')
        
        # Add LLM interpretation
        indicators.append('llm_interpretation')
        
        return indicators
    
    def get_indicator_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get the parameters used for each indicator."""
        return self.selected_indicators
    
    def get_required_columns(self) -> List[str]:
        """Get the required columns from the DataFrame for computing indicators."""
        return ['Open', 'High', 'Low', 'Close', 'Volume']
    
    def to_database_format(self, df: pd.DataFrame, data_entries: List[Dict]) -> List[Dict]:
        """
        Update a list of data entries with calculated indicators and LLM interpretations.
        
        This overrides the parent class method to add LLM interpretations.
        
        Args:
            df: DataFrame with calculated indicators and interpretations
            data_entries: List of data entry dictionaries to update
            
        Returns:
            Updated list of data entries
        """
        # First call the parent implementation
        updated_entries = super().to_database_format(df, data_entries)
        
        # Get LLM interpretation from DataFrame attributes or the last row
        llm_interpretation = None
        if hasattr(df, 'attrs') and 'llm_interpretation' in df.attrs:
            llm_interpretation = df.attrs['llm_interpretation']
        elif 'llm_interpretation' in df.columns and len(df) > 0:
            llm_interpretation = df['llm_interpretation'].iloc[-1]
        
        # Add LLM interpretation to each entry if available
        if llm_interpretation:
            for entry in updated_entries:
                # Store in raw_data with a special key
                if 'raw_data' not in entry or not isinstance(entry['raw_data'], dict):
                    entry['raw_data'] = {}
                
                entry['raw_data']['llm_interpretation'] = llm_interpretation
        
        return updated_entries