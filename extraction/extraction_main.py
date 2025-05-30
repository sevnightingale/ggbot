"""
Main extraction module using MCP for technical indicators.

This module provides functionality for extracting market data and computing
technical indicators using the Crypto Indicators MCP, with LLM-based analysis
and interpretation of the results.

The ExtractionManager class provides a configuration-driven architecture
that reads user settings from the database and executes appropriate data sources.
"""
import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.config.config_main import get_configuration
from extraction.utils import store_market_data_entries
from core.mcp.metadata import get_mcp_tool_name, get_tool_info

# Load environment variables from .env file at project root
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parents[1] / '.env'  # Go up 1 level from extraction/ to project root
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, continue without it


async def extract_mcp_indicators(symbols, timeframes, user_id=DEFAULT_USER_ID, use_llm=True, llm_model="gpt-4o-mini"):
    """
    Extract indicator data directly using Indicators MCP.

    This function connects directly to the MCP server to calculate indicators
    and gets LLM interpretations of the results.

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

    # Import necessary components
    from openai import OpenAI
    from core.mcp.indicators import IndicatorsMCPClient

    # Make sure we're always using LLM - required for MCP integration
    if not use_llm:
        logger.bind(user_id=user_id).warning("LLM usage is required for MCP integration - forcing use_llm=True")
        use_llm = True

    # Get the OpenAI API key from environment
    llm_api_key = os.environ.get("EXTRACTION_LLM_API_KEY")
    if not llm_api_key:
        logger.bind(user_id=user_id).error("EXTRACTION_LLM_API_KEY environment variable not set")
        return {"error": "LLM API key not found"}

    # Initialize the OpenAI client
    llm_client = OpenAI(api_key=llm_api_key)
    mcp_client = None

    # Set default exchange for data fetching in the MCP server
    os.environ["EXCHANGE_NAME"] = os.environ.get("EXCHANGE_NAME", "binance")

    results = {}
    stored_count = 0

    try:
        # Create and connect to the MCP client
        mcp_client = IndicatorsMCPClient()
        await mcp_client.connect()
        logger.bind(user_id=user_id).info("Successfully connected to Indicators MCP")

        # Get available tools from the MCP server
        tools = await mcp_client.session.get_tools()
        logger.bind(user_id=user_id).info(f"Available MCP tools: {len(tools)}")

        # Get indicator tools (filter out non-indicator tools)
        indicator_tools = [t for t in tools if not any(
            keyword in t.name for keyword in ['fetch', 'backtest', 'analyze', 'get']
        )]
        logger.bind(user_id=user_id).info(f"Available indicator tools: {len(indicator_tools)}")

        # Process each symbol and timeframe combination
        for symbol in symbols:
            if symbol not in results:
                results[symbol] = {}

            for timeframe in timeframes:
                logger.bind(user_id=user_id).info(f"Processing {symbol} {timeframe}")

                try:
                    # Step 1: Get indicators from user configuration (not LLM selection)
                    user_config = get_configuration(user_id, 'extraction') or {}
                    mcp_source_config = user_config.get('sources', {}).get('crypto_indicators_mcp', {})
                    
                    # Get configured indicators
                    selected_indicators = mcp_source_config.get('indicators', ['RSI'])  # Default to RSI if not configured
                    
                    logger.bind(user_id=user_id).info(f"Using configured indicators: {selected_indicators}")

                    # Step 2: Calculate each selected indicator
                    indicator_results = {}
                    
                    for indicator_name in selected_indicators:
                        try:
                            # Map user-friendly name to MCP tool name
                            mcp_tool_name = get_mcp_tool_name(indicator_name)
                            if not mcp_tool_name:
                                logger.bind(user_id=user_id).warning(f"Unknown indicator: {indicator_name}")
                                continue
                            
                            # Get tool info to understand parameters
                            tool_info = get_tool_info(mcp_tool_name)
                            if not tool_info:
                                logger.bind(user_id=user_id).warning(f"No tool info for: {mcp_tool_name}")
                                continue
                            
                            # Call the MCP tool
                            logger.bind(user_id=user_id).info(f"Calculating {indicator_name} ({mcp_tool_name}) for {symbol} {timeframe}")
                            
                            # Build parameters for the MCP tool call
                            params = {
                                "exchange": os.environ.get("EXCHANGE_NAME", "binance"),
                                "symbol": symbol,
                                "timeframe": timeframe
                            }
                            
                            # Add default parameters based on tool schema
                            if 'parameters' in tool_info and 'properties' in tool_info['parameters']:
                                for param_name, param_info in tool_info['parameters']['properties'].items():
                                    if param_name not in params:
                                        # Check if user has custom parameter in config
                                        config_param_name = f"{indicator_name}_{param_name}"
                                        if config_param_name in mcp_source_config:
                                            params[param_name] = mcp_source_config[config_param_name]
                                        elif param_name in tool_info['parameters'].get('required', []):
                                            # Use default values for required parameters
                                            if param_info.get('type') == 'number':
                                                if 'period' in param_name.lower():
                                                    params[param_name] = 14  # Default period
                                                else:
                                                    params[param_name] = param_info.get('default', 0)
                                            elif param_info.get('type') == 'string':
                                                params[param_name] = param_info.get('default', '')
                            
                            # Call the MCP tool through the session
                            result = await mcp_client.session.call_tool(mcp_tool_name, params)
                            
                            # DEBUG: Log raw indicator data
                            logger.bind(user_id=user_id).info(
                                f"🔍 RAW {indicator_name} DATA for {symbol} {timeframe}: {str(result)[:500]}..."
                            )
                            
                            if result and not isinstance(result, str) or (isinstance(result, str) and not result.startswith("Error")):
                                indicator_results[indicator_name] = result
                                logger.bind(user_id=user_id).info(f"Successfully calculated {indicator_name}")
                            else:
                                logger.bind(user_id=user_id).warning(f"Failed to calculate {indicator_name}: {result}")
                                
                        except Exception as e:
                            logger.bind(user_id=user_id).error(f"Error calculating {indicator_name}: {str(e)}")
                            continue
                    
                    # Step 3: Get LLM interpretation of the results
                    if indicator_results:
                        interpretation_prompt = f"""
Analyze the raw indicator data for {symbol} on the {timeframe} timeframe:

{json.dumps(indicator_results, indent=2)}

Your task is to extract and summarize the key information from this raw data:
1. For each indicator, identify the CURRENT VALUE (the most recent data point)
2. Describe the RECENT TREND based on the historical data
3. Note any significant levels or patterns in the data

Focus only on objective data analysis. Do NOT make trading recommendations or sentiment assessments.

Format your response as a JSON object:
{{
    "indicators": {{
        "indicator_name": {{
            "current_value": numeric_value,
            "trend": "description of recent trend",
            "key_observations": "notable patterns or levels"
        }}
    }},
    "summary": "brief objective summary of the data"
}}
"""

                        logger.bind(user_id=user_id).info("Requesting interpretation from LLM")
                        
                        # DEBUG: Log the prompt being sent to LLM
                        system_prompt = "You are a technical analysis assistant. Your task is to analyze raw indicator data and extract key information: current values, trends, and patterns. Provide objective data analysis only, without trading recommendations."
                        logger.bind(user_id=user_id).info(
                            f"📋 EXTRACTION LLM SYSTEM PROMPT:\n{system_prompt}"
                        )
                        logger.bind(user_id=user_id).info(
                            f"📝 EXTRACTION LLM USER PROMPT:\n{interpretation_prompt}"
                        )
                        
                        interpretation_response = llm_client.chat.completions.create(
                            model=llm_model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": interpretation_prompt}
                            ],
                            temperature=0.3,
                            response_format={"type": "json_object"}
                        )
                        
                        interpretation = interpretation_response.choices[0].message.content
                        
                        # DEBUG: Log the LLM response
                        logger.bind(user_id=user_id).info(
                            f"🤖 EXTRACTION LLM RESPONSE:\n{interpretation}"
                        )
                        
                        try:
                            interpretation_data = json.loads(interpretation)
                        except json.JSONDecodeError:
                            logger.bind(user_id=user_id).error(f"Failed to parse interpretation: {interpretation}")
                            interpretation_data = {
                                "sentiment": "neutral",
                                "analysis": interpretation,
                                "error": "Failed to parse LLM response"
                            }
                        
                        # Step 4: Store the results in the database
                        market_data_entry = {
                            "user_id": user_id,
                            "source": "indicators_mcp",
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "data_type": "indicator_analysis",
                            "updated_at": datetime.utcnow(),
                            "raw_data": {
                                "indicators": indicator_results,
                                "selected_indicators": selected_indicators,
                                "interpretation": interpretation_data,
                                "llm_model": llm_model
                            },
                            "indicators": indicator_results  # Also store in indicators column
                        }
                        
                        # Store in database
                        stored = store_market_data_entries([market_data_entry])
                        if stored > 0:
                            stored_count += 1
                            logger.bind(user_id=user_id).info(f"Stored indicator data for {symbol} {timeframe}")
                        else:
                            logger.bind(user_id=user_id).error(f"Failed to store data for {symbol} {timeframe}")
                        
                        # Add to results
                        results[symbol][timeframe] = {
                            "status": "success",
                            "indicators": indicator_results,
                            "interpretation": interpretation_data,
                            "stored": stored > 0
                        }
                        
                    else:
                        logger.bind(user_id=user_id).warning(f"No indicators calculated for {symbol} {timeframe}")
                        results[symbol][timeframe] = {
                            "status": "error",
                            "error": "No indicators could be calculated"
                        }
                        
                except Exception as e:
                    logger.bind(user_id=user_id).error(f"Error processing {symbol} {timeframe}: {str(e)}")
                    results[symbol][timeframe] = {
                        "status": "error", 
                        "error": str(e)
                    }

        logger.bind(user_id=user_id).info(f"MCP extraction complete. Stored {stored_count} entries.")
        return results

    except Exception as e:
        logger.bind(user_id=user_id).error(f"Error in MCP extraction: {str(e)}")
        return {"error": str(e)}
        
    finally:
        # Clean up MCP connection
        if mcp_client:
            try:
                await mcp_client.disconnect()
                logger.bind(user_id=user_id).info("Disconnected from Indicators MCP")
            except Exception as e:
                logger.bind(user_id=user_id).error(f"Error disconnecting from MCP: {str(e)}")


class ExtractionManager:
    """
    Configuration-driven extraction orchestrator.
    
    This class reads user configuration from the database and manages
    multiple data sources based on user preferences.
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        """
        Initialize the ExtractionManager with user configuration.
        
        Args:
            user_id: User ID to load configuration for
        """
        self.user_id = user_id
        self.config = get_configuration(user_id, 'extraction') or {}
        self.symbols = self.config.get('symbols', ['BTC/USDT'])
        self.timeframes = self.config.get('timeframes', ['15m', '1h'])
        self.sources = {}
        
        self.logger = logger.bind(user_id=user_id)
        self.logger.info(f"Initialized ExtractionManager with {len(self.symbols)} symbols, {len(self.timeframes)} timeframes")
    
    async def initialize_sources(self):
        """
        Dynamically load configured data sources.
        """
        sources_config = self.config.get('sources', {})
        
        for source_name, source_config in sources_config.items():
            if source_config.get('enabled', False):
                self.logger.info(f"Initializing data source: {source_name}")
                
                try:
                    source = await self._create_source(source_name, source_config)
                    if source:
                        self.sources[source_name] = source
                        self.logger.info(f"Successfully initialized {source_name}")
                    else:
                        self.logger.warning(f"Failed to create source {source_name}")
                except Exception as e:
                    self.logger.error(f"Error initializing {source_name}: {str(e)}")
    
    async def _create_source(self, source_name: str, source_config: dict):
        """
        Create a data source instance based on the source name.
        
        Args:
            source_name: Name of the data source
            source_config: Configuration for the data source
            
        Returns:
            Data source instance or None if creation failed
        """
        if source_name == 'crypto_indicators_mcp':
            from extraction.sources.crypto_indicators_mcp import CryptoIndicatorsMCPSource
            return CryptoIndicatorsMCPSource(self.user_id, source_config)
        elif source_name == 'tradingview':
            # Future implementation
            self.logger.warning(f"TradingView source not yet implemented")
            return None
        elif source_name == 'yfinance':
            # Future implementation
            self.logger.warning(f"YFinance source not yet implemented")
            return None
        else:
            self.logger.error(f"Unknown data source: {source_name}")
            return None
    
    async def extract_all(self):
        """
        Run extraction for all enabled sources.
        
        Returns:
            Dictionary of extraction results by source and symbol/timeframe
        """
        self.logger.info(f"Starting extraction for {len(self.sources)} sources")
        
        results = {}
        total_stored = 0
        
        for source_name, source in self.sources.items():
            self.logger.info(f"Running extraction for {source_name}")
            
            try:
                source_results = await source.extract(self.symbols, self.timeframes)
                results[source_name] = source_results
                
                # Count stored entries
                if isinstance(source_results, dict):
                    for symbol_results in source_results.values():
                        if isinstance(symbol_results, dict):
                            for timeframe_result in symbol_results.values():
                                if isinstance(timeframe_result, dict) and timeframe_result.get('stored'):
                                    total_stored += 1
                                    
            except Exception as e:
                self.logger.error(f"Error in {source_name} extraction: {str(e)}")
                results[source_name] = {'error': str(e)}
        
        self.logger.info(f"Extraction complete. Total entries stored: {total_stored}")
        return results


def main():
    """
    Main entry point for the extraction module.
    
    This can be used for testing or running extraction manually.
    """
    import asyncio
    
    # Example usage
    symbols = ["BTC/USDT"]
    timeframes = ["1h", "4h"]
    
    # Run the extraction
    results = asyncio.run(extract_mcp_indicators(symbols, timeframes))
    
    # Print results
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()