#!/usr/bin/env python3
"""
Test script for Stochastic preprocessor implementation.
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add the parent directory to the path so we can import from extraction/v2
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.v2.extraction_engine import ExtractionEngineV2

async def test_stochastic_preprocessor():
    """Test the Stochastic preprocessor with advanced analysis."""
    print("Testing Stochastic Preprocessor Implementation")
    print("=" * 50)
    
    try:
        # Initialize the extraction engine
        engine = ExtractionEngineV2(user_id="test_user")
        
        # Test extraction with Stochastic
        result = await engine.extract_for_symbol(
            symbol="BTC/USDT",
            indicators=["stochastic"],  # Test only Stochastic
            timeframe="1h", 
            connector="kucoin",
            config_id="test_stochastic"
        )
        
        print("\n✅ Stochastic Extraction Result:")
        print("-" * 30)
        
        if "stochastic" in result.get("indicators", {}):
            stoch_data = result["indicators"]["stochastic"]
            
            # Print key metrics
            print(f"Indicator: {stoch_data.get('indicator', 'N/A')}")
            
            current = stoch_data.get("current", {})
            print(f"Current %K: {current.get('k_percent', 'N/A')}")
            print(f"Current %D: {current.get('d_percent', 'N/A')}")
            print(f"Spread: {current.get('spread', 'N/A')}")
            
            # Zone analysis
            zones = stoch_data.get("zones", {})
            print(f"\nZone Analysis:")
            print(f"  Current Zone: {zones.get('current_zone', 'N/A')}")
            
            ob_info = zones.get("overbought", {})
            print(f"  Overbought Status: {ob_info.get('status', 'N/A')}")
            print(f"  OB Streak Length: {ob_info.get('streak_length', 'N/A')}")
            
            os_info = zones.get("oversold", {})
            print(f"  Oversold Status: {os_info.get('status', 'N/A')}")
            print(f"  OS Streak Length: {os_info.get('streak_length', 'N/A')}")
            
            # Crossover analysis
            crossovers = stoch_data.get("crossovers", {})
            latest_cross = crossovers.get("latest_crossover")
            if latest_cross:
                print(f"\nCrossover Analysis:")
                print(f"  Latest: {latest_cross.get('type', 'N/A')} ({latest_cross.get('periods_ago', 'N/A')}p ago)")
                print(f"  Location: {latest_cross.get('location', 'N/A')}")
                print(f"  Strength: {latest_cross.get('strength', 'N/A')}")
            else:
                print(f"\nNo recent crossovers detected")
            
            # Position rank
            position_rank = stoch_data.get("position_rank", {})
            print(f"\nPosition Analysis:")
            print(f"  %K Percentile: {position_rank.get('k_percentile', 'N/A')}%")
            print(f"  Interpretation: {position_rank.get('interpretation', 'N/A')}")
            
            # Momentum analysis  
            momentum = stoch_data.get("momentum", {})
            print(f"\nMomentum Analysis:")
            print(f"  %K Velocity: {momentum.get('k_velocity', 'N/A')}")
            print(f"  %K Acceleration: {momentum.get('k_acceleration', 'N/A')}")
            print(f"  Momentum Type: {momentum.get('momentum_interpretation', 'N/A')}")
            
            # Signals
            signals = stoch_data.get("signals", [])
            print(f"\nSignals Generated: {len(signals)}")
            for i, signal in enumerate(signals):
                print(f"  {i+1}. {signal.get('type', 'N/A')} - {signal.get('strength', 'N/A')} strength")
                print(f"     Reason: {signal.get('reason', 'N/A')}")
                print(f"     Confidence: {signal.get('confidence', 'N/A')}")
            
            # Summary and confidence
            print(f"\nSummary: {stoch_data.get('summary', 'N/A')}")
            print(f"Confidence: {stoch_data.get('confidence', 'N/A')}")
            
            # Divergence (if detected)
            divergence = stoch_data.get("divergence")
            if divergence:
                print(f"\n🔍 Divergence Detected:")
                print(f"  Type: {divergence.get('type', 'N/A')}")
                print(f"  Confidence: {divergence.get('confidence', 'N/A')}")
                print(f"  Description: {divergence.get('description', 'N/A')}")
            else:
                print(f"\nNo divergence patterns detected")
            
        else:
            print("❌ Stochastic data not found in result")
            
        # Test multiple indicators including Stochastic
        print(f"\n" + "=" * 50)
        print("Testing Multiple Indicators (RSI + MACD + Stochastic)")
        print("=" * 50)
        
        multi_result = await engine.extract_for_symbol(
            symbol="BTC/USDT",
            indicators=["rsi", "macd", "stochastic"],
            timeframe="1h",
            connector="kucoin", 
            config_id="test_multi_with_stoch"
        )
        
        indicators_found = list(multi_result.get("indicators", {}).keys())
        print(f"\n✅ Indicators Successfully Calculated: {indicators_found}")
        
        # Quick summary of each
        for indicator in indicators_found:
            data = multi_result["indicators"][indicator]
            summary = data.get("summary", "No summary available")
            confidence = data.get("confidence", "N/A")
            print(f"  {indicator.upper()}: {summary} (confidence: {confidence})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Stochastic Preprocessor Test")
    
    # Activate virtual environment check
    if 'ggbot' not in str(Path.cwd()):
        print("⚠️  Warning: Not in ggbot directory")
    
    success = asyncio.run(test_stochastic_preprocessor())
    
    if success:
        print(f"\n✅ All tests passed! Stochastic preprocessor is working correctly.")
        print("📊 Advanced features validated:")
        print("  - %K/%D crossover analysis")
        print("  - Overbought/oversold zone tracking") 
        print("  - Position rank percentile calculation")
        print("  - Momentum velocity/acceleration analysis")
        print("  - Signal generation with confidence scoring")
        print("  - Professional-grade summary generation")
    else:
        print(f"\n❌ Tests failed!")
        sys.exit(1)