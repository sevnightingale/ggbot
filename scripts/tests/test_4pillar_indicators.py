#!/usr/bin/env python3
"""
Test 4-Pillar Indicators Extraction and Analysis.

This test extracts all 10 indicators from the 4-pillar strategy for BTC/USDT
and analyzes the raw MCP output format, data complexity, and prompt size.
The goal is to ensure the data fits within DeepSeek R1 context limits and
understand the structure for proper prompt variable mapping.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parents[1]))

from extraction.extraction_main import extract_mcp_indicators
from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID

# 4-Pillar indicators configuration (matches ggShot config e249bb49-0455-4596-9657-09bf9e14ca14)
FOUR_PILLAR_INDICATORS = [
    # Pillar 0: Market Regime
    "Aroon",                  # Aroon - trending vs ranging market detection
    "BollingerBandsWidth",    # BBW - volatility/range detection
    
    # Pillar 1: Signal Confirmation
    "SMA_Volume_30",          # Volume SMA for breakout confirmation
    "Vortex",                 # Trend momentum alignment
    "VWAP",                   # Volume-weighted sentiment
    
    # Pillar 2: Broader Context
    "RSI",                    # Signal timeframe RSI
    "RSI_4h",                 # Higher timeframe RSI
    "DonchianChannel_200",    # Major liquidity zones
    
    # Pillar 3: Tactical Caution
    "BollingerBands",         # Statistical overextension
    "ATR"                     # Market volatility/choppiness
]

def analyze_indicator_data(indicator_name: str, raw_data: any) -> dict:
    """Analyze the structure and complexity of raw indicator data."""
    analysis = {
        "indicator": indicator_name,
        "data_type": type(raw_data).__name__,
        "size_chars": len(str(raw_data)),
        "complexity": "simple"
    }
    
    if isinstance(raw_data, dict):
        analysis["keys"] = list(raw_data.keys())
        analysis["complexity"] = "complex_dict"
        
        # Check for array data within the dict
        array_keys = []
        for key, value in raw_data.items():
            if isinstance(value, list):
                array_keys.append(f"{key}({len(value)} items)")
        
        if array_keys:
            analysis["arrays"] = array_keys
            analysis["complexity"] = "dict_with_arrays"
            
    elif isinstance(raw_data, list):
        analysis["array_length"] = len(raw_data)
        analysis["complexity"] = "array"
        
        # Sample first and last values
        if len(raw_data) > 0:
            analysis["first_value"] = raw_data[0]
            analysis["last_value"] = raw_data[-1]
    
    # Determine extraction needs
    if analysis["complexity"] in ["dict_with_arrays", "complex_dict"]:
        analysis["extraction_needed"] = True
        analysis["extraction_method"] = "last_value_from_arrays" if "arrays" in analysis else "specific_keys"
    else:
        analysis["extraction_needed"] = False
        analysis["extraction_method"] = "direct_use"
    
    return analysis

async def test_4pillar_indicators():
    """Test extraction of all 4-pillar indicators for BTC/USDT on 1h timeframe."""
    
    print("🚀 Starting 4-Pillar Indicators Analysis Test")
    print("=" * 80)
    print(f"Indicators: {len(FOUR_PILLAR_INDICATORS)} (4-pillar strategy)")
    print(f"Symbol: BTC/USDT")
    print(f"Timeframe: 1h")
    print(f"Purpose: Analyze raw MCP data for prompt engineering")
    print("=" * 80)
    
    # Test parameters
    symbols = ["BTC/USDT"]
    timeframes = ["1h"]
    
    # Create a temporary config for testing
    test_config = {
        "extraction": {
            "sources": {
                "crypto_indicators_mcp": {
                    "enabled": True,
                    "indicators": FOUR_PILLAR_INDICATORS,
                    "llm_interpretation": False  # Raw data only
                }
            }
        }
    }
    
    # We'll need to create a test config in the database temporarily
    # For now, let's use the existing ggShot config ID
    GGSHOT_CONFIG_ID = "e249bb49-0455-4596-9657-09bf9e14ca14"
    
    try:
        start_time = datetime.now()
        print(f"\n⏰ Starting extraction at {start_time.isoformat()}")
        print(f"This will test {len(FOUR_PILLAR_INDICATORS)} indicators...")
        
        # Run the extraction with raw data only
        results = await extract_mcp_indicators(
            symbols=symbols,
            timeframes=timeframes,
            config_id=GGSHOT_CONFIG_ID,
            use_llm=False  # Force no LLM interpretation for raw data analysis
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Extraction completed in {duration:.2f} seconds")
        print("=" * 80)
        
        # Analyze the results
        if "BTC/USDT" in results and "1h" in results["BTC/USDT"]:
            timeframe_data = results["BTC/USDT"]["1h"]
            
            if timeframe_data.get("status") == "success":
                indicators_data = timeframe_data.get("indicators", {})
                
                print(f"\n📊 INDICATOR DATA ANALYSIS")
                print("=" * 80)
                
                analysis_results = []
                total_prompt_size = 0
                
                for indicator_name in FOUR_PILLAR_INDICATORS:
                    if indicator_name in indicators_data:
                        raw_data = indicators_data[indicator_name]
                        analysis = analyze_indicator_data(indicator_name, raw_data)
                        analysis_results.append(analysis)
                        total_prompt_size += analysis["size_chars"]
                        
                        print(f"\n{indicator_name}:")
                        print(f"  Type: {analysis['data_type']}")
                        print(f"  Size: {analysis['size_chars']} chars")
                        print(f"  Complexity: {analysis['complexity']}")
                        
                        if "keys" in analysis:
                            print(f"  Keys: {analysis['keys']}")
                        if "arrays" in analysis:
                            print(f"  Arrays: {analysis['arrays']}")
                        if "array_length" in analysis:
                            print(f"  Array Length: {analysis['array_length']}")
                            
                        print(f"  Extraction: {analysis['extraction_method']}")
                        
                        # Show first few characters of data
                        data_preview = str(raw_data)[:100]
                        if len(str(raw_data)) > 100:
                            data_preview += "..."
                        print(f"  Preview: {data_preview}")
                    else:
                        print(f"\n❌ {indicator_name}: NOT FOUND")
                        analysis_results.append({
                            "indicator": indicator_name,
                            "status": "missing",
                            "size_chars": 0
                        })
                
                # Summary analysis
                print(f"\n📈 SUMMARY ANALYSIS")
                print("=" * 80)
                print(f"Total indicators tested: {len(FOUR_PILLAR_INDICATORS)}")
                print(f"Successfully extracted: {len([a for a in analysis_results if 'status' not in a])}")
                print(f"Missing indicators: {len([a for a in analysis_results if a.get('status') == 'missing'])}")
                print(f"Total prompt size: {total_prompt_size:,} characters")
                print(f"Average size per indicator: {total_prompt_size / len(FOUR_PILLAR_INDICATORS):.0f} characters")
                
                # Context limit analysis (DeepSeek R1 has ~32k token limit, roughly 128k chars)
                context_limit_chars = 128000  # Conservative estimate
                usage_percentage = (total_prompt_size / context_limit_chars) * 100
                print(f"Context usage: {usage_percentage:.1f}% of DeepSeek R1 limit")
                
                if usage_percentage > 80:
                    print("⚠️  WARNING: High context usage - may need data truncation")
                elif usage_percentage > 60:
                    print("⚡ MODERATE: Context usage is significant but manageable")
                else:
                    print("✅ OPTIMAL: Context usage is well within limits")
                
                # Identify complex indicators that need special handling
                complex_indicators = [a for a in analysis_results if a.get("extraction_needed")]
                if complex_indicators:
                    print(f"\n🔧 COMPLEX INDICATORS REQUIRING EXTRACTION:")
                    for indicator in complex_indicators:
                        print(f"  - {indicator['indicator']}: {indicator['extraction_method']}")
                
                # Save detailed analysis to JSON file
                output_file = Path(__file__).parent / "4pillar_analysis_results.json"
                analysis_output = {
                    "test_timestamp": datetime.now().isoformat(),
                    "test_duration_seconds": duration,
                    "total_indicators": len(FOUR_PILLAR_INDICATORS),
                    "successful_extractions": len([a for a in analysis_results if 'status' not in a]),
                    "total_prompt_size_chars": total_prompt_size,
                    "context_usage_percentage": usage_percentage,
                    "indicators_analysis": analysis_results,
                    "complete_raw_data": {
                        indicator: indicators_data.get(indicator, "MISSING") 
                        for indicator in FOUR_PILLAR_INDICATORS  # ALL 10 indicators
                    }
                }
                
                with open(output_file, 'w') as f:
                    json.dump(analysis_output, f, indent=2, default=str)
                
                print(f"\n💾 Detailed analysis saved to: {output_file}")
                
            else:
                print(f"❌ Extraction failed: {timeframe_data.get('error', 'Unknown error')}")
                
        else:
            print("❌ No results found for BTC/USDT 1h timeframe")
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        logger.error(f"4-pillar indicators test failed: {str(e)}")
        
    print("\n" + "=" * 80)
    print("🏁 4-Pillar Indicators Analysis Complete")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_4pillar_indicators())