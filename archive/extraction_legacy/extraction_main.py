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


async def extract_mcp_indicators(symbols, timeframes, user_id=DEFAULT_USER_ID, use_llm=True, llm_model="gpt-4o-mini", config_id=None):
    """
    Extract indicator data using the new string-based indicator system.

    This function uses the updated CryptoIndicatorsMCPSource with config_id support
    for precise indicator extraction based on configuration.

    Args:
        symbols: List of trading pair symbols (e.g., ['BTC/USDT'])
        timeframes: List of timeframes (IGNORED - indicators specify their own timeframes)
        user_id: User ID to associate with the extracted data
        use_llm: Whether to use LLM for indicator interpretation
        llm_model: LLM model to use (default: "gpt-4o-mini")
        config_id: Configuration ID to use for extraction settings (REQUIRED for new system)

    Returns:
        Dictionary of extraction results by symbol
    """
    logger.bind(user_id=user_id).info(
        f"NEW SYSTEM: Extracting indicators for symbols={symbols} with config_id={config_id}"
    )
    
    if not config_id:
        logger.error("config_id is required for extraction system")
        return {"error": "config_id is required"}

    # Use the new CryptoIndicatorsMCPSource
    from extraction.sources.crypto_indicators_mcp import CryptoIndicatorsMCPSource

    try:
        # Get configuration for this config_id
        user_config = get_configuration(user_id=user_id, config_id=config_id) or {}
        extraction_config = user_config.get('extraction', {})
        mcp_source_config = extraction_config.get('sources', {}).get('crypto_indicators_mcp', {})
        
        if not mcp_source_config.get('enabled', False):
            logger.error(f"crypto_indicators_mcp not enabled for config_id {config_id}")
            return {"error": "MCP source not enabled in configuration"}
        
        # Create the source with configuration
        source = CryptoIndicatorsMCPSource(user_id, mcp_source_config)
        
        # Call extract with config_id for new mode
        results = await source.extract(symbols, timeframes, config_id)
        
        logger.bind(user_id=user_id).info(
            f"✅ NEW SYSTEM extraction complete for {len(symbols)} symbols"
        )
        
        return results
        
    except Exception as e:
        logger.bind(user_id=user_id).error(f"Error in extraction: {str(e)}")
        return {"error": str(e)}


# ============================================================================
# LEGACY IMPLEMENTATION - KEPT FOR FALLBACK/TESTING
# ============================================================================
async def extract_mcp_indicators_legacy(symbols, timeframes, user_id=DEFAULT_USER_ID, use_llm=True, llm_model="gpt-4o-mini", config_id=None):
    """
    LEGACY: Extract indicator data using the old cross-product approach.
    
    This function is kept for fallback and comparison purposes.
    """
    logger.bind(user_id=user_id).info(
        f"LEGACY SYSTEM: Extracting indicators for symbols={symbols}, timeframes={timeframes}"
    )
    
    # Initialize LLM client if needed
    llm_client = None
    if use_llm:
        import openai
        llm_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Initialize MCP client
    mcp_client = None
    
    try:
        # Import and initialize MCP client
        from core.mcp.client import MCPClient
        mcp_client = MCPClient(
            name="indicators",
            server_script_path="core/mcp/servers/crypto-indicators-mcp/index.js",
            user_id=user_id
        )
        
        # Connect to MCP server
        await mcp_client.connect()
        logger.bind(user_id=user_id).info("Connected to Indicators MCP")
        
        # Get available tools
        tools = await mcp_client.session.list_tools()
        logger.bind(user_id=user_id).info(f"Available MCP tools: {len(tools)}")
        
        # Results dictionary
        results = {}
        stored_count = 0
        
        # Filter to only indicator calculation tools (not fetch/analysis tools)
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
                    # Step 1: Get indicators from configuration using config_id
                    if config_id:
                        # Use specific config_id
                        user_config = get_configuration(user_id=user_id, config_id=config_id) or {}
                        extraction_config = user_config.get('extraction', {})
                    else:
                        # Fallback to legacy method
                        extraction_config = get_configuration(user_id, 'extraction') or {}
                    
                    mcp_source_config = extraction_config.get('sources', {}).get('crypto_indicators_mcp', {})
                    
                    # Get configured indicators
                    selected_indicators = mcp_source_config.get('indicators', ['RSI'])  # Default to RSI if not configured
                    
                    logger.bind(user_id=user_id).info(f"Using configured indicators: {selected_indicators}")

                    # Step 2: Calculate each selected indicator
                    indicator_results = {}
                    
                    # First, fetch current volume data for 4-pillar analysis
                    try:
                        # Get OHLCV data to extract current volume (last completed candle)
                        volume_params = {
                            "exchange": os.environ.get("EXCHANGE_NAME", "binance"),
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "limit": 5  # Just need a few recent candles
                        }
                        
                        # Use a simple indicator call to get OHLCV data
                        volume_result = await mcp_client.session.call_tool(
                            'calculate_simple_moving_average',  # Any indicator that returns OHLCV
                            {**volume_params, "period": 1}  # Minimal period
                        )
                        
                        # Extract current volume from the result
                        if volume_result and isinstance(volume_result, dict):
                            # Look for OHLCV data in various possible formats
                            ohlcv_data = None
                            if 'ohlcv' in volume_result:
                                ohlcv_data = volume_result['ohlcv']
                            elif 'data' in volume_result and isinstance(volume_result['data'], list):
                                ohlcv_data = volume_result['data']
                            
                            if ohlcv_data and len(ohlcv_data) > 0:
                                # Get the last completed candle's volume (index 4 = volume)
                                last_candle = ohlcv_data[-1] if isinstance(ohlcv_data[-1], list) else None
                                if last_candle and len(last_candle) > 4:
                                    current_volume = last_candle[4]  # Volume is at index 4
                                    indicator_results['current_volume'] = current_volume
                                    logger.bind(user_id=user_id).info(f"✓ Extracted current volume: {current_volume}")
                                else:
                                    logger.bind(user_id=user_id).warning("Could not extract volume from OHLCV candle data")
                            else:
                                logger.bind(user_id=user_id).warning("No OHLCV data found in volume fetch result")
                        else:
                            logger.bind(user_id=user_id).warning("Volume fetch returned invalid result")
                            
                    except Exception as e:
                        logger.bind(user_id=user_id).warning(f"Failed to fetch current volume: {str(e)}")
                        # Continue without volume data - this is not critical
                    
                    for indicator_name in selected_indicators:
                        try:
                            # Parse special indicator patterns
                            actual_indicator = indicator_name
                            target_timeframe = timeframe  # Default to signal timeframe
                            custom_period = None
                            use_volume_data = False
                            
                            # Check for multi-timeframe indicators (e.g., RSI_4h)
                            if '_' in indicator_name:
                                parts = indicator_name.split('_')
                                if len(parts) == 2 and parts[1] in ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']:
                                    actual_indicator = parts[0]
                                    target_timeframe = parts[1]
                                    logger.bind(user_id=user_id).info(f"Multi-timeframe indicator detected: {actual_indicator} on {target_timeframe}")
                                elif 'Volume' in indicator_name:
                                    # Handle volume-based indicators (e.g., SMA_Volume_30)
                                    if len(parts) == 3 and parts[0] in ['SMA', 'EMA'] and parts[1] == 'Volume':
                                        actual_indicator = parts[0]
                                        use_volume_data = True
                                        custom_period = int(parts[2])
                                        logger.bind(user_id=user_id).info(f"Volume indicator detected: {actual_indicator} on volume with period {custom_period}")
                                elif len(parts) == 2 and parts[1].isdigit():
                                    # Handle indicators with custom periods (e.g., DonchianChannel_200)
                                    actual_indicator = parts[0]
                                    custom_period = int(parts[1])
                                    logger.bind(user_id=user_id).info(f"Custom period indicator: {actual_indicator} with period {custom_period}")
                            
                            # Map user-friendly name to MCP tool name
                            mcp_tool_name = get_mcp_tool_name(actual_indicator)
                            if not mcp_tool_name:
                                logger.bind(user_id=user_id).warning(f"Unknown indicator: {actual_indicator}")
                                continue
                            
                            # Get tool info to understand parameters
                            tool_info = get_tool_info(mcp_tool_name)
                            if not tool_info:
                                logger.bind(user_id=user_id).warning(f"No tool info for: {mcp_tool_name}")
                                continue
                            
                            # Call the MCP tool
                            logger.bind(user_id=user_id).info(f"Calculating {indicator_name} ({mcp_tool_name}) for {symbol} {target_timeframe}")
                            
                            # Build parameters for the MCP tool call
                            params = {
                                "exchange": os.environ.get("EXCHANGE_NAME", "binance"),
                                "symbol": symbol,
                                "timeframe": target_timeframe  # Use target timeframe instead of signal timeframe
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
                                                if 'period' in param_name.lower() and custom_period:
                                                    params[param_name] = custom_period  # Use parsed custom period
                                                elif 'period' in param_name.lower():
                                                    params[param_name] = 14  # Default period
                                                else:
                                                    params[param_name] = param_info.get('default', 0)
                                            elif param_info.get('type') == 'string':
                                                params[param_name] = param_info.get('default', '')
                            
                            # Special handling for volume-based indicators
                            if use_volume_data and actual_indicator == 'SMA':
                                # Use VWMA as a proxy for SMA on volume
                                logger.bind(user_id=user_id).info(f"Using VWMA as proxy for SMA on volume")
                                mcp_tool_name = 'calculate_volume_weighted_moving_average'
                                # Update tool info for VWMA
                                tool_info = get_tool_info(mcp_tool_name)
                                if not tool_info:
                                    logger.bind(user_id=user_id).warning(f"VWMA tool not found, skipping {indicator_name}")
                                    continue
                            
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
                    
                    # Check if LLM interpretation is enabled in config
                    use_llm_interpretation = mcp_source_config.get('llm_interpretation', True)
                    
                    # Step 3: Get LLM interpretation of the results (if enabled)
                    interpretation_data = None
                    if indicator_results and use_llm_interpretation:
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
                    else:
                        if indicator_results and not use_llm_interpretation:
                            logger.bind(user_id=user_id).info("LLM interpretation disabled - storing raw data only")
                        
                    # Step 4: Store the results in the database
                    if indicator_results:
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
                                "llm_model": llm_model if interpretation_data else None
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