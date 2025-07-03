"""
Crypto Indicators MCP source implementation for the configuration-driven extraction system.

This module provides a source implementation that uses MCP metadata for direct
indicator calls, with configuration-driven indicator selection and optional LLM interpretation.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from core.common.logger import logger
from core.mcp.indicators import IndicatorsMCPClient
from core.mcp.metadata import get_mcp_tool_name, get_tool_info, get_available_indicators, parse_indicator_string, get_mcp_tool_name_from_string
from extraction.utils import store_market_data_entries

# Load environment variables from .env file at project root
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parents[2] / '.env'  # Go up 2 levels from extraction/sources/ to project root
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, continue without it


class CryptoIndicatorsMCPSource:
    """
    Configuration-driven Crypto Indicators MCP source.
    
    This source reads indicator configuration from user settings and calls
    MCP tools directly without LLM selection, optionally using LLM for interpretation.
    """
    
    def __init__(self, user_id: str, config: Dict[str, Any]):
        """
        Initialize the Crypto Indicators MCP source.
        
        Args:
            user_id: User ID to associate with extracted data
            config: Source configuration from user settings
        """
        self.user_id = user_id
        self.config = config
        self.mcp_client = None
        
        # Extract configuration
        self.indicators = config.get('indicators', ['RSI'])
        self.use_llm_selection = config.get('use_llm_selection', False)
        self.llm_interpretation = config.get('llm_interpretation', True) 
        self.llm_model = config.get('llm_model', 'gpt-4o-mini')
        
        self.logger = logger.bind(user_id=user_id, source="crypto_indicators_mcp")
        self.logger.info(f"Initialized CryptoIndicatorsMCPSource with {len(self.indicators)} indicators")
    
    async def extract(self, symbols: List[str], timeframes: List[str] = None, config_id: str = None) -> Dict[str, Any]:
        """
        Extract indicator data for symbols using either legacy or new extraction pattern.
        
        BACKWARDS COMPATIBILITY MODE:
        - If config_id is None: Uses legacy (symbol, timeframe) pattern
        - If config_id provided: Uses new config-driven string-based indicators
        
        Args:
            symbols: List of trading symbols
            timeframes: List of timeframes (used in legacy mode)
            config_id: Configuration ID for new extraction pattern
            
        Returns:
            Dictionary of extraction results by symbol and timeframe/config
        """
        # Determine extraction mode
        if config_id:
            self.logger.info(f"NEW MODE: Extracting for {len(symbols)} symbols with config_id {config_id}")
            return await self._extract_new_mode(symbols, config_id)
        else:
            self.logger.info(f"LEGACY MODE: Extracting for {len(symbols)} symbols, {len(timeframes or [])} timeframes")
            return await self._extract_legacy_mode(symbols, timeframes or [])
    
    async def _extract_legacy_mode(self, symbols: List[str], timeframes: List[str]) -> Dict[str, Any]:
        """Legacy extraction using (symbol, timeframe) pattern."""
        # Import LLM client if needed
        llm_client = None
        if self.llm_interpretation:
            try:
                from openai import OpenAI
                llm_api_key = os.environ.get("EXTRACTION_LLM_API_KEY")
                if not llm_api_key:
                    self.logger.error("EXTRACTION_LLM_API_KEY not found, disabling LLM interpretation")
                    self.llm_interpretation = False
                else:
                    llm_client = OpenAI(api_key=llm_api_key)
            except ImportError:
                self.logger.error("OpenAI package not available, disabling LLM interpretation")
                self.llm_interpretation = False
        
        # Set exchange environment
        os.environ["EXCHANGE_NAME"] = os.environ.get("EXCHANGE_NAME", "binance")
        
        results = {}
        
        try:
            # Connect to MCP client
            self.mcp_client = IndicatorsMCPClient()
            await self.mcp_client.connect()
            self.logger.info("Connected to Indicators MCP")
            
            # Process each symbol/timeframe combination (LEGACY)
            for symbol in symbols:
                if symbol not in results:
                    results[symbol] = {}
                
                for timeframe in timeframes:
                    self.logger.info(f"LEGACY: Processing {symbol} {timeframe}")
                    
                    try:
                        # Calculate indicators using old method
                        indicator_results = await self._calculate_indicators_legacy(symbol, timeframe)
                        
                        if indicator_results:
                            # Get LLM interpretation if enabled
                            interpretation = None
                            if self.llm_interpretation and llm_client:
                                interpretation = await self._interpret_with_llm(
                                    llm_client, indicator_results, symbol, timeframe
                                )
                            
                            # Store in database using legacy pattern (no config_id)
                            stored = await self._store_results_legacy(
                                symbol, timeframe, indicator_results, interpretation
                            )
                            
                            results[symbol][timeframe] = {
                                "status": "success",
                                "indicators": indicator_results,
                                "interpretation": interpretation,
                                "stored": stored
                            }
                        else:
                            results[symbol][timeframe] = {
                                "status": "error",
                                "error": "No indicators calculated"
                            }
                            
                    except Exception as e:
                        self.logger.error(f"Error processing {symbol} {timeframe}: {str(e)}")
                        results[symbol][timeframe] = {
                            "status": "error",
                            "error": str(e)
                        }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in legacy MCP extraction: {str(e)}")
            return {"error": str(e)}
            
        finally:
            # Clean up MCP connection
            if self.mcp_client:
                try:
                    await self.mcp_client.disconnect()
                    self.logger.info("Disconnected from Indicators MCP")
                except Exception as e:
                    self.logger.error(f"Error disconnecting from MCP: {str(e)}")
    
    async def _extract_new_mode(self, symbols: List[str], config_id: str) -> Dict[str, Any]:
        """New extraction using config_id + string-based indicators."""
        results = {}
        
        try:
            # Connect to MCP client
            self.mcp_client = IndicatorsMCPClient()
            await self.mcp_client.connect()
            self.logger.info("Connected to Indicators MCP for NEW MODE")
            
            for symbol in symbols:
                self.logger.info(f"NEW MODE: Processing {symbol} with config {config_id}")
                
                try:
                    # Group indicators by timeframe for efficient extraction
                    timeframe_groups = self._group_indicators_by_timeframe()
                    
                    symbol_indicators = {}
                    
                    for timeframe, indicator_strings in timeframe_groups.items():
                        # Extract all indicators for this timeframe in one session
                        timeframe_results = await self._extract_timeframe_indicators(
                            symbol, timeframe, indicator_strings
                        )
                        symbol_indicators.update(timeframe_results)
                    
                    # Store using new pattern: config_id + symbol
                    stored = await self._store_results_new_format(config_id, symbol, symbol_indicators)
                    
                    results[symbol] = {
                        "status": "success", 
                        "indicators": symbol_indicators,
                        "config_id": config_id,
                        "stored": stored
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error processing {symbol} in new mode: {str(e)}")
                    results[symbol] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in MCP extraction: {str(e)}")
            return {"error": str(e)}
            
        finally:
            # Clean up MCP connection
            if self.mcp_client:
                try:
                    await self.mcp_client.disconnect()
                    self.logger.info("Disconnected from Indicators MCP")
                except Exception as e:
                    self.logger.error(f"Error disconnecting from MCP: {str(e)}")
    
    async def _calculate_indicators_legacy(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        Calculate indicators using MCP metadata for direct tool calls (LEGACY METHOD).
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            Dictionary of calculated indicators
        """
        indicator_results = {}
        
        for indicator_name in self.indicators:
            try:
                # Map user-friendly name to MCP tool name
                mcp_tool_name = get_mcp_tool_name(indicator_name)
                if not mcp_tool_name:
                    self.logger.warning(f"Unknown indicator: {indicator_name}")
                    continue
                
                # Get tool info to understand parameters
                tool_info = get_tool_info(mcp_tool_name)
                if not tool_info:
                    self.logger.warning(f"No tool info for: {mcp_tool_name}")
                    continue
                
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
                            if config_param_name in self.config:
                                params[param_name] = self.config[config_param_name]
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
                self.logger.info(f"Calling {mcp_tool_name} for {symbol} {timeframe}")
                result = await self.mcp_client.session.call_tool(mcp_tool_name, params)
                
                if result and not (isinstance(result, str) and result.startswith("Error")):
                    indicator_results[indicator_name] = result
                    self.logger.info(f"Successfully calculated {indicator_name}")
                else:
                    self.logger.warning(f"Failed to calculate {indicator_name}: {result}")
                    
            except Exception as e:
                self.logger.error(f"Error calculating {indicator_name}: {str(e)}")
                continue
        
        return indicator_results
    
    async def _interpret_with_llm(self, llm_client, indicator_results: Dict[str, Any], 
                                 symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        Get LLM interpretation of indicator results.
        
        Args:
            llm_client: OpenAI client instance
            indicator_results: Dictionary of calculated indicators
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            Dictionary containing LLM interpretation or None if failed
        """
        try:
            interpretation_prompt = f"""
Analyze the following technical indicator data for {symbol} on the {timeframe} timeframe:

{json.dumps(indicator_results, indent=2)}

Your goal is to extract maximum analytical value from this indicator data. Focus on:

1. **Data Quality & Patterns**: Assess the indicator values, identify trends, patterns, cycles, and any anomalies
2. **Historical Context**: Analyze the progression of values over time, identify key levels, breakouts, or reversals
3. **Technical Analysis**: Interpret what the indicator values reveal about price action, momentum, volatility, or volume
4. **Key Levels & Zones**: Identify significant support/resistance levels, overbought/oversold zones, or critical thresholds
5. **Data Insights**: Extract any additional insights that would be valuable for decision-making

Do NOT provide trading recommendations or advice. Focus purely on analytical interpretation of the data.

Format your response as a JSON object with these fields:
{{
    "current_state": "description of current indicator state",
    "trend_analysis": "analysis of trend and momentum from the data",
    "key_levels": ["important levels or zones identified"],
    "pattern_analysis": "any patterns, cycles, or technical formations observed",
    "data_quality": "assessment of data reliability and significance",
    "analytical_insights": ["key insights extracted from the data"],
    "time_series_summary": "summary of how the indicator has evolved over the time period",
    "confidence_in_analysis": 0.0-1.0
}}
"""
            
            self.logger.info(f"Requesting interpretation from LLM for {symbol} {timeframe}")
            
            response = llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a technical analysis expert specialized in interpreting technical indicator data. Your role is to extract maximum analytical value from indicator time series data through pattern recognition, trend analysis, and data interpretation. Focus on objective analysis, not trading recommendations."},
                    {"role": "user", "content": interpretation_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            interpretation = response.choices[0].message.content
            
            try:
                return json.loads(interpretation)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse LLM interpretation: {interpretation}")
                return {
                    "current_state": "unknown",
                    "trend_analysis": "Unable to parse LLM response",
                    "analytical_insights": [interpretation[:500]],  # Truncate if too long
                    "error": "Failed to parse LLM response"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting LLM interpretation: {str(e)}")
            return None
    
    async def _store_results_legacy(self, symbol: str, timeframe: str, 
                           indicator_results: Dict[str, Any], 
                           interpretation: Optional[Dict[str, Any]]) -> bool:
        """
        Store extraction results in the database using legacy pattern (no config_id).
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            indicator_results: Calculated indicators
            interpretation: LLM interpretation (optional)
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            market_data_entry = {
                "user_id": self.user_id,
                "source": "crypto_indicators_mcp",
                "symbol": symbol,
                "timeframe": timeframe,
                "data_type": "indicator_analysis",
                "updated_at": datetime.utcnow(),
                "indicators": {
                    "configured_indicators": self.indicators,
                    "results": indicator_results
                },
                "raw_data": {
                    "interpretation": interpretation,
                    "llm_model": self.llm_model if interpretation else None,
                    "config": {
                        "use_llm_selection": self.use_llm_selection,
                        "llm_interpretation": self.llm_interpretation
                    }
                }
            }
            
            stored_count = store_market_data_entries([market_data_entry])
            
            if stored_count > 0:
                self.logger.info(f"Stored indicator data for {symbol} {timeframe}")
                return True
            else:
                self.logger.error(f"Failed to store data for {symbol} {timeframe}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error storing results: {str(e)}")
            return False
    
    def _group_indicators_by_timeframe(self) -> Dict[str, List[str]]:
        """Group string indicators by their timeframes for efficient extraction."""
        groups = {}
        
        for indicator_string in self.indicators:
            parsed = parse_indicator_string(indicator_string)
            timeframe = parsed.get("timeframe", "1h")  # Default fallback
            
            if timeframe not in groups:
                groups[timeframe] = []
            groups[timeframe].append(indicator_string)
        
        return groups
    
    async def _extract_timeframe_indicators(self, symbol: str, timeframe: str, 
                                          indicator_strings: List[str]) -> Dict[str, Any]:
        """Extract multiple indicators for a specific timeframe."""
        results = {}
        
        for indicator_string in indicator_strings:
            try:
                parsed = parse_indicator_string(indicator_string)
                mcp_tool_name = get_mcp_tool_name(parsed["indicator"])
                
                if not mcp_tool_name:
                    self.logger.warning(f"No MCP tool for {indicator_string}")
                    continue
                
                # Build parameters with period override if specified
                params = {
                    "exchange": os.environ.get("EXCHANGE_NAME", "binance"),
                    "symbol": symbol,
                    "timeframe": timeframe
                }
                
                # Add period if specified in string
                if "period" in parsed:
                    params["period"] = parsed["period"]
                elif f"{parsed['indicator']}_period" in self.config:
                    params["period"] = self.config[f"{parsed['indicator']}_period"]
                
                # Call MCP tool
                result = await self.mcp_client.session.call_tool(mcp_tool_name, params)
                
                if result and not (isinstance(result, str) and result.startswith("Error")):
                    results[indicator_string] = result  # Store with full string name
                    self.logger.info(f"✅ Extracted {indicator_string}")
                else:
                    self.logger.warning(f"❌ Failed {indicator_string}: {result}")
                    
            except Exception as e:
                self.logger.error(f"Error extracting {indicator_string}: {str(e)}")
        
        return results
    
    async def _store_results_new_format(self, config_id: str, symbol: str, 
                                       indicators: Dict[str, Any]) -> bool:
        """Store results using new config_id + symbol pattern."""
        try:
            market_data_entry = {
                "user_id": self.user_id,
                "config_id": config_id,  # NEW FIELD
                "source": "crypto_indicators_mcp",
                "symbol": symbol,
                "timeframe": "mixed",  # Not used anymore
                "data_type": "indicator_analysis",
                "updated_at": datetime.utcnow(),
                "indicators": indicators,  # String-based keys
                "raw_data": {
                    "config": {
                        "string_indicators": self.indicators,
                        "llm_interpretation": self.llm_interpretation
                    }
                }
            }
            
            stored_count = store_market_data_entries([market_data_entry])
            return stored_count > 0
            
        except Exception as e:
            self.logger.error(f"Error storing results: {str(e)}")
            return False