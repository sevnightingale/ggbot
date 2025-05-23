"""
Main extraction module that manages data sources and indicators.

This module provides the main functionality for extracting market data from
various sources, computing technical indicators, and storing the data in the
database for use by the decision module.

It supports two types of data sources:
1. Standard sources that implement the DataSource interface (like YFinanceDataSource)
2. Specialized sources with their own extraction scripts (like TradingView)
"""
import os
import sys
import time
import json
import asyncio
import subprocess
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID

from extraction.sources import YFinanceDataSource
from extraction.indicators import PandasTAIndicators
from extraction.indicators.crypto_indicators_mcp import CryptoIndicatorsMCP
from extraction.indicators.indicators_mcp_llm import IndicatorsMCPLLM
from extraction.utils import store_market_data_entries


class ExtractionManager:
    """
    Manages the extraction of market data from various sources.

    This class coordinates between data sources, indicator computers, and the
    database to ensure that up-to-date market data is available for trading
    decisions.
    """

    def __init__(self, user_id: str = DEFAULT_USER_ID, use_mcp: bool = True, use_llm: bool = True,
                 selected_indicators=None, llm_model: str = "gpt-4o-mini"):
        """
        Initialize the ExtractionManager.

        Args:
            user_id: User ID to associate with the extracted data
            use_mcp: Whether to use the Crypto Indicators MCP for indicator calculations
                     (default: True)
            use_llm: Whether to use LLM for indicator selection and interpretation
                     (default: True)
            selected_indicators: Optional dictionary of indicators to calculate
                     (default: None, uses predefined set)
            llm_model: LLM model to use for interpretation
                     (default: "gpt-4o-mini")
        """
        self.user_id = user_id
        self.data_sources = {}
        self.indicator_computers = {}

        # Register default data source implementation
        self.register_data_source('yfinance', YFinanceDataSource())

        # Register indicator computer based on configuration
        if use_mcp:
            if use_llm:
                # Use LLM-mediated MCP implementation
                logger.bind(user_id=self.user_id).info(
                    f"Using LLM-mediated Crypto Indicators MCP with model {llm_model}"
                )
                self.register_indicator_computer(
                    'indicators_mcp_llm',
                    IndicatorsMCPLLM(
                        user_id=user_id,
                        selected_indicators=selected_indicators,
                        llm_model=llm_model
                    )
                )
            else:
                # Use direct MCP implementation without LLM
                logger.bind(user_id=self.user_id).info("Using Crypto Indicators MCP for indicator calculations")
                self.register_indicator_computer('indicators_mcp', CryptoIndicatorsMCP(user_id=user_id))
        else:
            # Fall back to pandas-ta implementation
            logger.bind(user_id=self.user_id).info("Using pandas-ta for indicator calculations")
            self.register_indicator_computer('pandas_ta', PandasTAIndicators())
    
    def register_data_source(self, name: str, data_source) -> None:
        """
        Register a data source.
        
        Args:
            name: Name to register the data source under
            data_source: DataSource implementation to register
        """
        self.data_sources[name] = data_source
        logger.bind(user_id=self.user_id).info(f"Registered data source: {name}")
    
    def register_indicator_computer(self, name: str, indicator_computer) -> None:
        """
        Register an indicator computer.
        
        Args:
            name: Name to register the indicator computer under
            indicator_computer: IndicatorComputer implementation to register
        """
        self.indicator_computers[name] = indicator_computer
        logger.bind(user_id=self.user_id).info(f"Registered indicator computer: {name}")
    
    def extract_market_data(
        self,
        symbol: str,
        timeframe: str,
        data_source_name: str = 'yfinance',
        indicator_computer_name: str = 'pandas_ta',
        days_of_history: int = 60,
        store_in_db: bool = True
    ) -> List[Dict]:
        """
        Extract market data for a specific symbol and timeframe.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USD')
            timeframe: Timeframe (e.g., '15m', '1h', '4h', '1d')
            data_source_name: Name of the data source to use
            indicator_computer_name: Name of the indicator computer to use
            days_of_history: Number of days of historical data to fetch
            store_in_db: Whether to store the data in the database
            
        Returns:
            List of dictionaries containing the market data
        """
        # Special handling for tradingview source
        if data_source_name == 'tradingview':
            return self.extract_from_tradingview(symbol, timeframe, store_in_db)
        
        # Get the data source and indicator computer
        data_source = self.data_sources.get(data_source_name)
        if not data_source:
            logger.bind(user_id=self.user_id).error(f"Data source not found: {data_source_name}")
            return []
        
        indicator_computer = self.indicator_computers.get(indicator_computer_name)
        if not indicator_computer:
            logger.bind(user_id=self.user_id).error(f"Indicator computer not found: {indicator_computer_name}")
            return []
        
        try:
            # Fetch historical data
            logger.bind(user_id=self.user_id).info(
                f"Extracting {days_of_history} days of {symbol} {timeframe} data from {data_source_name}"
            )
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_of_history)
            
            df = data_source.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                logger.bind(user_id=self.user_id).warning(
                    f"No data found for {symbol} {timeframe} from {data_source_name}"
                )
                return []
            
            # Compute indicators
            logger.bind(user_id=self.user_id).info(
                f"Computing indicators for {symbol} {timeframe} using {indicator_computer_name}"
            )
            
            df_with_indicators = indicator_computer.compute_indicators(df)
            
            # Convert to database format
            data_entries = data_source.to_database_format(
                df=df_with_indicators,
                symbol=symbol,
                timeframe=timeframe,
                user_id=self.user_id
            )
            
            data_entries = indicator_computer.to_database_format(
                df=df_with_indicators,
                data_entries=data_entries
            )
            
            # Store in database if requested
            if store_in_db:
                stored_count = store_market_data_entries(data_entries)
                logger.bind(user_id=self.user_id).info(
                    f"Stored {stored_count} {symbol} {timeframe} data entries in database"
                )
            
            return data_entries
            
        except Exception as e:
            logger.bind(user_id=self.user_id).error(
                f"Error extracting market data for {symbol} {timeframe}: {str(e)}"
            )
            return []
    
    def extract_from_tradingview(self, symbol: str, timeframe: str, store_in_db: bool = True) -> List[Dict]:
        """
        Extract market data from TradingView using the specialized script.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSD')
            timeframe: Timeframe (e.g., '15m', '1h', '4h', '1d')
            store_in_db: Whether to store the data in the database
            
        Returns:
            List of dictionaries containing the market data
        """
        logger.bind(user_id=self.user_id).info(
            f"Running TradingView extraction script for {symbol} {timeframe}"
        )
        
        try:
            # Run the TradingView extraction script as a subprocess
            script_path = os.path.join(
                os.path.dirname(__file__), 
                'sources', 'tradingview', 'run_extraction.py'
            )
            
            # Execute the script with symbol and timeframe as arguments
            process = subprocess.run(
                [sys.executable, script_path, symbol, timeframe],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check the output file for results
            output_file = os.path.join(
                os.path.dirname(__file__), 
                'sources', 'tradingview', f'ggshot_{timeframe}_summary.txt'
            )
            
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    report_text = f.read()
                
                # Create a data entry in our standard format
                data_entry = {
                    'user_id': self.user_id,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'source': 'tradingview',
                    'data_type': 'report',
                    'raw_data': {},
                    'indicators': {'report': report_text},
                    'updated_at': datetime.now()
                }
                
                data_entries = [data_entry]
                
                # Store in database if requested
                if store_in_db:
                    stored_count = store_market_data_entries(data_entries)
                    logger.bind(user_id=self.user_id).info(
                        f"Stored {stored_count} TradingView reports in database"
                    )
                
                return data_entries
            else:
                logger.bind(user_id=self.user_id).error(
                    f"TradingView extraction output file not found: {output_file}"
                )
                return []
        
        except subprocess.CalledProcessError as e:
            logger.bind(user_id=self.user_id).error(
                f"Error running TradingView extraction script: {e.stderr}"
            )
            return []
        
        except Exception as e:
            logger.bind(user_id=self.user_id).error(
                f"Error extracting data from TradingView: {str(e)}"
            )
            return []
    
    def extract_multiple(
        self,
        symbols: List[str],
        timeframes: List[str],
        data_source_name: str = 'yfinance',
        indicator_computer_name: str = 'pandas_ta',
        days_of_history: int = 60,
        store_in_db: bool = True
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Extract market data for multiple symbols and timeframes.
        
        Args:
            symbols: List of trading pair symbols (e.g., ['BTC-USD', 'ETH-USD'])
            timeframes: List of timeframes (e.g., ['15m', '1h', '4h', '1d'])
            data_source_name: Name of the data source to use
            indicator_computer_name: Name of the indicator computer to use
            days_of_history: Number of days of historical data to fetch
            store_in_db: Whether to store the data in the database
            
        Returns:
            Dictionary of symbols to timeframes to market data entries
        """
        results = {}
        
        for symbol in symbols:
            results[symbol] = {}
            
            for timeframe in timeframes:
                logger.bind(user_id=self.user_id).info(
                    f"Extracting {symbol} {timeframe} data..."
                )
                
                data_entries = self.extract_market_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    data_source_name=data_source_name,
                    indicator_computer_name=indicator_computer_name,
                    days_of_history=days_of_history,
                    store_in_db=store_in_db
                )
                
                results[symbol][timeframe] = data_entries
                
                # Add a small delay to avoid rate limiting
                time.sleep(1)
        
        return results
    
    def scheduled_extraction(
        self,
        symbols: List[str],
        timeframes: List[str],
        data_sources: List[str] = ['yfinance'],
        indicator_computer_name: str = 'pandas_ta',
        days_of_history: Optional[int] = None
    ) -> None:
        """
        Run scheduled extraction for all specified symbols, timeframes, and data sources.
        
        Args:
            symbols: List of trading pair symbols (e.g., ['BTC-USD', 'ETH-USD'])
            timeframes: List of timeframes (e.g., ['15m', '1h', '4h', '1d'])
            data_sources: List of data source names to use
            indicator_computer_name: Name of the indicator computer to use
            days_of_history: Number of days of historical data to fetch (if None, uses timeframe-specific defaults)
        """
        logger.bind(user_id=self.user_id).info(
            f"Running scheduled extraction for symbols={symbols}, "
            f"timeframes={timeframes}, sources={data_sources}"
        )
        
        # Configure days of history per timeframe based on yfinance limitations
        timeframe_config = {
            '1d': 730,   # 2 years for daily data
            '4h': 730,   # 2 years for 4h data
            '1h': 730,   # 2 years for hourly data
            '15m': 60    # 60 days for 15-min data (yfinance limit)
        }
        
        for data_source_name in data_sources:
            try:
                if days_of_history is not None:
                    # Use the provided days_of_history for all timeframes
                    results = self.extract_multiple(
                        symbols=symbols,
                        timeframes=timeframes,
                        data_source_name=data_source_name,
                        indicator_computer_name=indicator_computer_name,
                        days_of_history=days_of_history,
                        store_in_db=True
                    )
                else:
                    # Process each timeframe with its specific history limit
                    results = {}
                    for symbol in symbols:
                        results[symbol] = {}
                        
                        for timeframe in timeframes:
                            # Get appropriate history length for this timeframe
                            days = timeframe_config.get(timeframe, 60)  # Default to 60 days if unknown timeframe
                            
                            logger.bind(user_id=self.user_id).info(
                                f"Extracting {symbol} {timeframe} with {days} days of history..."
                            )
                            
                            data_entries = self.extract_market_data(
                                symbol=symbol,
                                timeframe=timeframe,
                                data_source_name=data_source_name,
                                indicator_computer_name=indicator_computer_name,
                                days_of_history=days,
                                store_in_db=True
                            )
                            
                            results[symbol][timeframe] = data_entries
                            
                            # Add a small delay to avoid rate limiting
                            time.sleep(1)
                
                # Log the results
                for symbol, timeframe_data in results.items():
                    for timeframe, data_entries in timeframe_data.items():
                        logger.bind(user_id=self.user_id).info(
                            f"Extracted {len(data_entries)} {symbol} {timeframe} "
                            f"data entries from {data_source_name}"
                        )
            
            except Exception as e:
                logger.bind(user_id=self.user_id).error(
                    f"Error in scheduled extraction for {data_source_name}: {str(e)}"
                )


async def extract_mcp_indicators(symbols, timeframes, user_id=DEFAULT_USER_ID, use_llm=True, llm_model="gpt-4o-mini"):
    """
    Extract indicator data directly using Indicators MCP.

    This function follows the pattern established in test_indicators_llm_mcp.py,
    connecting directly to the MCP server to calculate indicators and optionally
    getting LLM interpretations of the results.

    Args:
        symbols: List of trading pair symbols (e.g., ['BTC/USDT'])
        timeframes: List of timeframes (e.g., ['15m', '1h', '4h', '1d'])
        user_id: User ID to associate with the extracted data
        use_llm: Whether to use LLM for indicator selection and interpretation
        llm_model: LLM model to use (default: "gpt-4o-mini")

    Returns:
        Dictionary of extraction results by symbol and timeframe
    """
    logger.bind(user_id=user_id).info(
        f"Extracting indicators via MCP for symbols={symbols}, timeframes={timeframes}"
    )

    # Import necessary components that match the test pattern
    from openai import OpenAI
    from core.mcp.indicators import IndicatorsMCPClient

    # Make sure we're always using LLM - following the test pattern
    if not use_llm:
        logger.bind(user_id=user_id).warning("LLM usage is required for MCP integration - forcing use_llm=True")
        use_llm = True

    # Get the OpenAI API key from environment
    llm_api_key = os.environ.get("TRADING_LLM_API_KEY")
    if not llm_api_key:
        logger.bind(user_id=user_id).error("TRADING_LLM_API_KEY environment variable not set")
        return {"error": "LLM API key not found"}

    # Initialize the OpenAI client
    llm_client = OpenAI(api_key=llm_api_key)
    mcp_client = None

    # Set default exchange for data fetching in the MCP server
    os.environ["EXCHANGE_NAME"] = os.environ.get("EXCHANGE_NAME", "binance")

    results = {}
    stored_count = 0

    try:
        # Create and connect to the MCP client - EXACTLY as in the test
        mcp_client = IndicatorsMCPClient()
        logger.bind(user_id=user_id).info("Connecting to Indicators MCP server...")
        await mcp_client.connect()
        logger.bind(user_id=user_id).info("Connected to MCP server")

        # Get available tools from the server
        tools = await mcp_client.session.get_tools()
        logger.bind(user_id=user_id).info(f"Found {len(tools)} available tools")

        # Format tools for the LLM - EXACTLY following the test pattern
        formatted_tools = []
        for tool in tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
            formatted_tools.append(tool_info)

        # Process each symbol and timeframe
        for symbol in symbols:
            results[symbol] = {}

            for timeframe in timeframes:
                logger.bind(user_id=user_id).info(f"Processing {symbol} on {timeframe} timeframe")

                try:
                    # Create the user question - EXACTLY as in the test
                    user_question = f"Calculate key technical indicators for {symbol} on the {timeframe} timeframe to assess current market conditions."

                    # Ask LLM which tool to use - EXACTLY following the test pattern
                    logger.bind(user_id=user_id).info(f"Asking LLM about: {user_question}")

                    # Format the tools as a string
                    tools_str = json.dumps(formatted_tools, indent=2)

                    # Create the prompt - EXACTLY as in the test file
                    prompt = f"""You are an AI trading assistant that uses tools to calculate technical indicators for cryptocurrency markets.

Here are the tools available to you:
{tools_str}

IMPORTANT INSTRUCTIONS:
1. You MUST use the SAME PARAMETER NAMES that are shown in the tool definitions.
   Do not rename or reformat the parameter names.

2. For any parameters requiring a trading pair, use "{symbol}" as the symbol.

3. Most indicators require a 'symbol' parameter specifying the trading pair.
   This is a REQUIRED parameter for most indicator calculations.

4. For the 'timeframe' parameter, use "{timeframe}" unless otherwise specified.

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

                    # Call the LLM API - EXACTLY as in the test
                    response = llm_client.chat.completions.create(
                        model=llm_model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that decides which tools to use to calculate technical indicators for cryptocurrency markets."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0
                    )

                    # Extract the JSON from the response - EXACTLY as in the test
                    content = response.choices[0].message.content
                    # Remove any markdown formatting
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()

                    # Parse the tool call
                    tool_call = json.loads(content)
                    logger.bind(user_id=user_id).info(f"LLM decided to use: {tool_call['tool']}")
                    logger.bind(user_id=user_id).info(f"With parameters: {json.dumps(tool_call['parameters'], indent=2)}")
                    logger.bind(user_id=user_id).info(f"Reasoning: {tool_call.get('reasoning', 'No reasoning provided')}")

                    # Execute the tool call - EXACTLY as in the test
                    logger.bind(user_id=user_id).info(f"Executing tool call: {tool_call['tool']}")

                    tool_name = tool_call['tool']
                    parameters = tool_call['parameters']

                    try:
                        # Execute the tool call
                        raw_result = await mcp_client.session.call_tool(tool_name, parameters)

                        # Process the result - Match the test's processing logic
                        result = None
                        # Add debug logging
                        logger.bind(user_id=user_id).info(f"Raw result type: {type(raw_result)}")
                        logger.bind(user_id=user_id).info(f"Raw result attributes: {dir(raw_result)}")
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
                                    result = json.loads(combined_content)
                                except json.JSONDecodeError:
                                    result = combined_content
                            else:
                                result = combined_content

                        # Handle result which could be a CallToolResult object
                        elif hasattr(raw_result, 'result'):
                            result = raw_result.result
                        else:
                            result = raw_result

                        # Simplify the approach - store minimal indicator values
                        # and focus on the LLM interpretation
                        indicators = {}

                        # Store a placeholder value based on the tool name
                        # This ensures we have something to store in the database
                        if "rsi" in tool_name.lower():
                            indicators["RSI_interpretation"] = "See LLM analysis"
                        elif "macd" in tool_name.lower():
                            indicators["MACD_interpretation"] = "See LLM analysis"
                        elif "bollinger" in tool_name.lower():
                            indicators["BB_interpretation"] = "See LLM analysis"
                        else:
                            # Generic placeholder for any other indicator
                            indicators[f"{tool_name}_interpretation"] = "See LLM analysis"


                        # Get LLM interpretation of the result - Follow the test pattern
                        interpretation = None
                        if result:
                            logger.bind(user_id=user_id).info("Getting LLM interpretation of result...")

                            # Format the result as a string, handling various types
                            if isinstance(result, (dict, list)):
                                result_str = json.dumps(result, indent=2)
                            else:
                                result_str = str(result)

                            # Create the interpretation prompt - EXACTLY as in the test
                            interp_prompt = f"""You are an AI trading assistant that has just used a tool to calculate a technical indicator.

User question: {user_question}

You used the tool "{tool_call['tool']}" with these parameters:
{json.dumps(tool_call['parameters'], indent=2)}

The tool returned this result:
{result_str}

Please interpret this result and answer the user's question based on this information.
Explain what the technical indicator suggests about market conditions, and what it might mean for traders.
Keep your answer concise and focused on the user's question.
"""

                            # Call the OpenAI API
                            interp_response = llm_client.chat.completions.create(
                                model=llm_model,
                                messages=[
                                    {"role": "system", "content": "You are a helpful assistant that explains technical indicators and their implications for cryptocurrency markets."},
                                    {"role": "user", "content": interp_prompt}
                                ],
                                temperature=0
                            )

                            interpretation = interp_response.choices[0].message.content
                            logger.bind(user_id=user_id).info("Generated LLM interpretation")

                        # Create the database entry
                        timestamp = datetime.now()
                        raw_data = {
                            'source': 'indicators_mcp',
                            'timestamp': timestamp.isoformat()
                        }

                        if interpretation:
                            raw_data['llm_interpretation'] = interpretation

                        entry = {
                            'user_id': user_id,
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'source': 'indicators_mcp',
                            'data_type': 'indicator_values',
                            'indicators': indicators,
                            'raw_data': raw_data,
                            'updated_at': timestamp
                        }

                        # Only store if we have indicators
                        if indicators:
                            # Store in database
                            stored = store_market_data_entries([entry])
                            stored_count += stored

                            logger.bind(user_id=user_id).info(
                                f"Stored {len(indicators)} indicators for {symbol} {timeframe}"
                            )
                        else:
                            logger.bind(user_id=user_id).warning(
                                f"No indicators calculated for {symbol} {timeframe}"
                            )

                        # Store results for return
                        results[symbol][timeframe] = {
                            'success': True if indicators else False,
                            'indicators': indicators,
                            'llm_interpretation': interpretation
                        }

                    except Exception as e:
                        logger.bind(user_id=user_id).error(f"Error executing tool call: {str(e)}")
                        results[symbol][timeframe] = {
                            'success': False,
                            'error': f"Error executing tool: {str(e)}"
                        }
                except Exception as e:
                    logger.bind(user_id=user_id).error(
                        f"Error extracting indicators for {symbol} {timeframe}: {str(e)}"
                    )
                    results[symbol][timeframe] = {
                        'success': False,
                        'error': str(e)
                    }

                # Add a small delay between requests to avoid overwhelming the MCP server
                await asyncio.sleep(1)

    except Exception as e:
        logger.bind(user_id=user_id).error(f"Error in MCP indicator extraction: {str(e)}")
        return {"error": f"Failed to extract indicators via MCP: {str(e)}"}

    finally:
        # Disconnect from the MCP server
        if mcp_client and mcp_client.is_connected:
            await mcp_client.disconnect()
            logger.bind(user_id=user_id).info("Disconnected from MCP server")

    logger.bind(user_id=user_id).info(f"Stored {stored_count} indicator entries in database")
    return results


async def main():
    """Main function to run the extraction process."""
    import argparse
    import sys
    import asyncio
    from datetime import datetime

    parser = argparse.ArgumentParser(description='Run market data extraction')
    parser.add_argument('--symbols', type=str, nargs='+', default=['BTC/USDT'],
                        help='Trading pair symbols to extract data for')
    parser.add_argument('--timeframes', type=str, nargs='+', default=['1d', '4h', '1h', '15m'],
                        help='Timeframes to extract data for')
    parser.add_argument('--use-llm', action='store_true', default=True,
                        help='Use LLM for indicator selection and interpretation')
    parser.add_argument('--user-id', type=str, default=DEFAULT_USER_ID,
                        help='User ID to associate with the extracted data')
    parser.add_argument('--mcp-only', action='store_true',
                        help='Only use MCP for indicator extraction')
    parser.add_argument('--tradingview', action='store_true',
                        help='Include TradingView extraction')
    parser.add_argument('--llm-model', type=str, default="gpt-4o-mini",
                        help='LLM model to use for indicator selection and interpretation')

    args = parser.parse_args()

    # Extract indicators using MCP
    if args.mcp_only or not args.tradingview:
        await extract_mcp_indicators(
            symbols=args.symbols,
            timeframes=args.timeframes,
            user_id=args.user_id,
            use_llm=args.use_llm,
            llm_model=args.llm_model
        )

    # Run TradingView extraction if requested
    if args.tradingview:
        logger.bind(user_id=args.user_id).info("Running TradingView extraction")
        manager = ExtractionManager(user_id=args.user_id)
        for symbol in args.symbols:
            for timeframe in args.timeframes:
                manager.extract_from_tradingview(symbol, timeframe)

    logger.bind(user_id=args.user_id).info("Extraction complete")


if __name__ == "__main__":
    # Run the async main function
    import asyncio
    asyncio.run(main())