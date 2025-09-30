#!/usr/bin/env python3
"""
Test script to extract all 47 successful indicators with individual LLM interpretations.
Stores results in a JSON file instead of the database.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import re

# Add project root to path
sys.path.append(str(Path(__file__).parents[1]))

from core.mcp.indicators import IndicatorsMCPClient
from core.common.logger import logger
from openai import OpenAI

# Configuration
ALL_INDICATORS_CONFIG_ID = "709a882b-4761-4279-bd73-297a851c582e"
OUTPUT_FILE = "btc_indicators_complete_with_interpretations.json"

# List of 47 successful indicators from previous test
SUCCESSFUL_INDICATORS = [
    "ATR", "EMA", "KDJ", "MFI", "OBV", "ROC", "RSI", "SMA", "MACD", "VWAP",
    "Aroon", "Qstick", "Vortex", "MassIndex", "MovingMax", "MovingMin", "MovingSum",
    "ForceIndex", "UlcerIndex", "TypicalPrice", "BalanceOfPower", "BollingerBands",
    "KeltnerChannel", "ChaikinMoneyFlow", "VolumePriceTrend", "NegativeVolumeIndex",
    "RollingMovingAverage", "AbsolutePriceOscillator", "AccumulationDistribution",
    "ChandeForecastOscillator", "TripleExponentialAverage", "VolumeWeightedMovingAverage",
    "AwesomeOscillator", "ChaikinOscillator", "IchimokuCloud", "PercentagePriceOscillator",
    "PercentageVolumeOscillator", "Stochastic", "WilliamsR", "AccelerationBands",
    "BollingerBandsWidth", "ChandelierExit", "DonchianChannel", "MovingStandardDeviation",
    "ProjectionOscillator", "TrueRange", "EaseOfMovement"
]

# Mapping of indicator names to MCP tool names
INDICATOR_TO_TOOL_MAP = {
    "AbsolutePriceOscillator": "calculate_absolute_price_oscillator",
    "AccelerationBands": "calculate_acceleration_bands",
    "AccumulationDistribution": "calculate_accumulation_distribution",
    "Aroon": "calculate_aroon",
    "ATR": "calculate_average_true_range",
    "AwesomeOscillator": "calculate_awesome_oscillator",
    "BalanceOfPower": "calculate_balance_of_power",
    "BollingerBands": "calculate_bollinger_bands",
    "BollingerBandsWidth": "calculate_bollinger_bands_width",
    "ChandeForecastOscillator": "calculate_chande_forecast_oscillator",
    "ChandelierExit": "calculate_chandelier_exit",
    "ChaikinMoneyFlow": "calculate_chaikin_money_flow",
    "ChaikinOscillator": "calculate_chaikin_oscillator",
    "DonchianChannel": "calculate_donchian_channel",
    "EaseOfMovement": "calculate_ease_of_movement",
    "EMA": "calculate_exponential_moving_average",
    "ForceIndex": "calculate_force_index",
    "IchimokuCloud": "calculate_ichimoku_cloud",
    "KDJ": "calculate_kdj",
    "KeltnerChannel": "calculate_keltner_channel",
    "MACD": "calculate_macd",
    "MassIndex": "calculate_mass_index",
    "MFI": "calculate_money_flow_index",
    "MovingMax": "calculate_moving_max",
    "MovingMin": "calculate_moving_min",
    "MovingStandardDeviation": "calculate_moving_standard_deviation",
    "MovingSum": "calculate_moving_sum",
    "NegativeVolumeIndex": "calculate_negative_volume_index",
    "OBV": "calculate_on_balance_volume",
    "PercentagePriceOscillator": "calculate_percentage_price_oscillator",
    "PercentageVolumeOscillator": "calculate_percentage_volume_oscillator",
    "ProjectionOscillator": "calculate_projection_oscillator",
    "Qstick": "calculate_qstick",
    "ROC": "calculate_rate_of_change",
    "RollingMovingAverage": "calculate_rolling_moving_average",
    "RSI": "calculate_relative_strength_index",
    "SMA": "calculate_simple_moving_average",
    "Stochastic": "calculate_stochastic",
    "TripleExponentialAverage": "calculate_triple_exponential_average",
    "TrueRange": "calculate_true_range",
    "TypicalPrice": "calculate_typical_price",
    "UlcerIndex": "calculate_ulcer_index",
    "VolumeWeightedMovingAverage": "calculate_volume_weighted_moving_average",
    "VolumePriceTrend": "calculate_volume_price_trend",
    "Vortex": "calculate_vortex",
    "VWAP": "calculate_volume_weighted_average_price",
    "WilliamsR": "calculate_williams_r"
}


def parse_mcp_response(response) -> Any:
    """Parse MCP tool response to extract actual data."""
    if hasattr(response, 'content') and isinstance(response.content, list):
        # Handle MCP format with content list
        for item in response.content:
            if hasattr(item, 'text'):
                text = item.text
            elif isinstance(item, dict) and 'text' in item:
                text = item['text']
            else:
                continue
            
            # Try to parse as JSON
            try:
                return json.loads(text)
            except:
                # Return raw text if not JSON
                return text
    
    # Return as-is if not in expected format
    return response


async def calculate_indicator(mcp_client: IndicatorsMCPClient, indicator_name: str, 
                            symbol: str, timeframe: str) -> Dict[str, Any]:
    """Calculate a single indicator using MCP."""
    tool_name = INDICATOR_TO_TOOL_MAP.get(indicator_name)
    if not tool_name:
        return {"error": f"No tool mapping for {indicator_name}"}
    
    # Base parameters
    params = {
        "exchange": "binance",
        "symbol": symbol,
        "timeframe": timeframe
    }
    
    # Add default parameters based on indicator type
    if indicator_name in ["RSI", "ATR", "SMA", "EMA"]:
        params["period"] = 14
    elif indicator_name == "MACD":
        params.update({"fastPeriod": 12, "slowPeriod": 26, "signalPeriod": 9})
    elif indicator_name == "BollingerBands":
        params.update({"period": 20, "stdDev": 2})
    elif indicator_name == "Stochastic":
        params.update({"kPeriod": 14, "dPeriod": 3, "smoothing": 3})
    elif indicator_name == "IchimokuCloud":
        params.update({"tenkanPeriod": 9, "kijunPeriod": 26, "senkouSpanBPeriod": 52})
    
    try:
        logger.info(f"Calculating {indicator_name} using {tool_name}")
        result = await mcp_client.session.call_tool(tool_name, params)
        parsed_result = parse_mcp_response(result)
        return {"success": True, "data": parsed_result}
    except Exception as e:
        logger.error(f"Error calculating {indicator_name}: {str(e)}")
        return {"success": False, "error": str(e)}


async def interpret_indicator(llm_client: OpenAI, indicator_name: str, 
                            indicator_data: Any, symbol: str, timeframe: str) -> Dict[str, Any]:
    """Get LLM interpretation for a single indicator."""
    
    # Format the data for the prompt
    if isinstance(indicator_data, dict):
        data_str = json.dumps(indicator_data, indent=2)
    elif isinstance(indicator_data, list) and len(indicator_data) > 100:
        # For long arrays, show first and last 10 values
        data_preview = {
            "first_10_values": indicator_data[:10],
            "last_10_values": indicator_data[-10:],
            "total_values": len(indicator_data),
            "min": min(indicator_data) if all(isinstance(x, (int, float)) for x in indicator_data) else "N/A",
            "max": max(indicator_data) if all(isinstance(x, (int, float)) for x in indicator_data) else "N/A"
        }
        data_str = json.dumps(data_preview, indent=2)
    else:
        data_str = json.dumps(indicator_data, indent=2)
    
    prompt = f"""
Analyze the {indicator_name} indicator data for {symbol} on the {timeframe} timeframe:

{data_str}

Provide a focused interpretation of this specific indicator including:
1. The current value and what it signifies
2. The trend or direction indicated by the data
3. Key observations specific to this indicator

Format your response as JSON:
{{
    "current_value": <current or most recent value>,
    "trend": "<description of trend>",
    "signal": "<bullish/bearish/neutral signal if applicable>",
    "key_observations": "<specific insights for this indicator>",
    "analysis": "<brief analytical summary>"
}}
"""

    try:
        response = llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a technical analysis expert. Provide concise, focused interpretations of individual technical indicators."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error interpreting {indicator_name}: {str(e)}")
        return {
            "error": str(e),
            "current_value": "N/A",
            "trend": "Unable to interpret",
            "key_observations": "LLM interpretation failed"
        }


async def test_all_indicators_with_interpretations():
    """Main test function to extract and interpret all indicators."""
    
    print("🚀 Starting Comprehensive Indicator Test with LLM Interpretations")
    print("=" * 80)
    print(f"Symbol: BTC/USDT")
    print(f"Timeframe: 1h")
    print(f"Indicators to test: {len(SUCCESSFUL_INDICATORS)}")
    print(f"Output file: {OUTPUT_FILE}")
    print("=" * 80)
    
    # Initialize clients
    mcp_client = IndicatorsMCPClient(exchange_name="binance")
    
    # Check for OpenAI API key
    api_key = os.environ.get("TRADING_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found. Set TRADING_LLM_API_KEY or OPENAI_API_KEY")
        return
    
    llm_client = OpenAI(api_key=api_key)
    
    # Results structure
    results = {
        "metadata": {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "test_timestamp": datetime.utcnow().isoformat(),
            "indicators_tested": len(SUCCESSFUL_INDICATORS),
            "test_config_id": ALL_INDICATORS_CONFIG_ID
        },
        "indicators": {}
    }
    
    try:
        # Connect to MCP
        await mcp_client.connect()
        print("\n✅ Connected to MCP server")
        
        # Process each indicator
        successful_count = 0
        failed_count = 0
        
        for i, indicator_name in enumerate(SUCCESSFUL_INDICATORS, 1):
            print(f"\n[{i}/{len(SUCCESSFUL_INDICATORS)}] Processing {indicator_name}...")
            
            # Calculate indicator
            calc_result = await calculate_indicator(mcp_client, indicator_name, "BTC/USDT", "1h")
            
            if calc_result["success"]:
                print(f"  ✅ Calculated {indicator_name}")
                
                # Get LLM interpretation
                interpretation = await interpret_indicator(
                    llm_client, indicator_name, calc_result["data"], "BTC/USDT", "1h"
                )
                print(f"  ✅ Interpreted {indicator_name}")
                
                # Store results
                results["indicators"][indicator_name] = {
                    "raw_data": calc_result["data"],
                    "llm_interpretation": interpretation,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                successful_count += 1
            else:
                print(f"  ❌ Failed to calculate {indicator_name}: {calc_result['error']}")
                results["indicators"][indicator_name] = {
                    "error": calc_result["error"],
                    "timestamp": datetime.utcnow().isoformat()
                }
                failed_count += 1
            
            # Add a small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        # Update metadata
        results["metadata"]["successful_indicators"] = successful_count
        results["metadata"]["failed_indicators"] = failed_count
        results["metadata"]["success_rate"] = f"{(successful_count/len(SUCCESSFUL_INDICATORS))*100:.1f}%"
        results["metadata"]["completion_timestamp"] = datetime.utcnow().isoformat()
        
        # Save results
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'='*80}")
        print(f"✅ Test completed!")
        print(f"   - Successful: {successful_count}/{len(SUCCESSFUL_INDICATORS)}")
        print(f"   - Failed: {failed_count}/{len(SUCCESSFUL_INDICATORS)}")
        print(f"   - Success rate: {(successful_count/len(SUCCESSFUL_INDICATORS))*100:.1f}%")
        print(f"   - Results saved to: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        logger.error(f"Test error: {e}", exc_info=True)
        
    finally:
        # Disconnect from MCP
        try:
            await mcp_client.disconnect()
            print("\n✅ Disconnected from MCP server")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(test_all_indicators_with_interpretations())