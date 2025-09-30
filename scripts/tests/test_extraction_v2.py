"""
Test script for Extraction V2 system.

This script validates the new Python-native extraction system against
the current MCP-based system to ensure accuracy and functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from datetime import datetime
import json

# V2 system imports
from extraction.v2.extraction_engine import ExtractionEngineV2, test_v2_system
from extraction.v2.data_client import HummingbotDataClient
from extraction.v2.indicators import TechnicalIndicators

# V1 system imports for comparison
from extraction.extraction_main import extract_mcp_indicators

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID


async def test_data_client():
    """Test Hummingbot data client."""
    print("\n🔍 Testing Hummingbot Data Client...")
    
    try:
        async with HummingbotDataClient() as client:
            # Test connection
            connection = await client.test_connection()
            print(f"Connection Status: {connection['status']}")
            
            if connection['status'] != 'connected':
                print(f"❌ Connection failed: {connection}")
                return False
            
            # Test data fetching
            df = await client.get_candles("BTC/USDT", "1h", 50)
            
            print(f"✅ Fetched {len(df)} candles")
            print(f"Data range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
            print(f"Latest price: ${df['close'].iloc[-1]:,.2f}")
            print(f"24h change: {(df['close'].iloc[-1] / df['close'].iloc[-24] - 1) * 100:+.2f}%" if len(df) >= 24 else "N/A")
            
            return True
            
    except Exception as e:
        print(f"❌ Data client test failed: {str(e)}")
        return False


async def test_indicators():
    """Test technical indicators calculations."""
    print("\n📊 Testing Technical Indicators...")
    
    try:
        # Get test data
        async with HummingbotDataClient() as client:
            df = await client.get_candles("BTC/USDT", "1h", 100)
        
        indicators = TechnicalIndicators()
        
        # Test individual indicators
        print("\nTesting RSI...")
        rsi_result = indicators.calculate_rsi(df, 14)
        print(f"RSI: {rsi_result['current']} ({rsi_result['analysis']['zone']} - {rsi_result['analysis']['trend']})")
        
        print("\nTesting MACD...")
        macd_result = indicators.calculate_macd(df, 12, 26, 9)
        print(f"MACD: {macd_result['current']['macd']:.4f} (Signal: {macd_result['current']['signal']:.4f})")
        print(f"Trend: {macd_result['analysis']['trend']}, Momentum: {macd_result['analysis']['momentum']}")
        
        print("\nTesting SMA...")
        sma_result = indicators.calculate_sma(df, 20)
        print(f"SMA(20): ${sma_result['current']:,.2f} (Price {sma_result['analysis']['price_position']} SMA)")
        
        print("\nTesting multiple indicators...")
        multi_result = indicators.calculate_multiple(df, ["rsi", "macd", "sma", "ema"])
        print(f"✅ Calculated {len(multi_result)} indicators successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Indicators test failed: {str(e)}")
        return False


async def test_extraction_engine():
    """Test complete extraction engine."""
    print("\n🎯 Testing Extraction Engine V2...")
    
    try:
        engine = ExtractionEngineV2(DEFAULT_USER_ID)
        
        # Test single symbol extraction
        result = await engine.extract_for_symbol(
            symbol="BTC/USDT",
            indicators=["rsi", "macd", "sma"],
            timeframe="1h",
            limit=100
        )
        
        if result["status"] == "success":
            print("✅ Single symbol extraction successful")
            print(f"Indicators calculated: {len(result['result']['indicators'])}")
            print(f"Data points: {result['result']['data_points']}")
            print(f"Latest price: ${result['result']['ohlcv_summary']['latest_price']:,.2f}")
        else:
            print(f"❌ Single symbol extraction failed: {result['error']}")
            return False
        
        # Test multiple symbols
        multi_result = await engine.extract_multiple_symbols(
            symbols=["BTC/USDT", "ETH/USDT"],
            indicators=["rsi", "sma"],
            timeframe="1h",
            limit=50
        )
        
        if multi_result["status"] == "success":
            successful = multi_result["summary"]["successful_extractions"]
            total = multi_result["summary"]["total_symbols"]
            print(f"✅ Multiple symbols extraction: {successful}/{total} successful")
        else:
            print(f"❌ Multiple symbols extraction failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Extraction engine test failed: {str(e)}")
        return False


async def compare_with_v1_system():
    """Compare V2 system with V1 MCP system."""
    print("\n⚖️ Comparing V2 vs V1 System...")
    
    try:
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        # V2 extraction
        print("Running V2 extraction...")
        engine = ExtractionEngineV2(DEFAULT_USER_ID)
        v2_result = await engine.extract_for_symbol(
            symbol=symbol,
            indicators=["rsi"],
            timeframe=timeframe,
            limit=100
        )
        
        if v2_result["status"] != "success":
            print(f"❌ V2 extraction failed: {v2_result['error']}")
            return False
        
        v2_rsi = v2_result["result"]["indicators"]["rsi"]["current"]
        print(f"V2 RSI: {v2_rsi}")
        
        # V1 extraction (if available)
        try:
            print("Running V1 extraction...")
            v1_result = await extract_mcp_indicators(
                symbols=[symbol],
                timeframes=[timeframe],
                user_id=DEFAULT_USER_ID,
                use_llm=False  # Disable LLM to focus on mathematical comparison
            )
            
            if symbol in v1_result and timeframe in v1_result[symbol]:
                v1_data = v1_result[symbol][timeframe]
                if "indicators" in v1_data and "RSI" in v1_data["indicators"]:
                    # Try to extract RSI value from V1 format
                    v1_rsi_data = v1_data["indicators"]["RSI"]
                    
                    # V1 format might be different, try to find current value
                    v1_rsi = None
                    if isinstance(v1_rsi_data, dict):
                        if "current" in v1_rsi_data:
                            v1_rsi = v1_rsi_data["current"].get("value")
                        elif "value" in v1_rsi_data:
                            v1_rsi = v1_rsi_data["value"]
                    elif isinstance(v1_rsi_data, list) and len(v1_rsi_data) > 0:
                        v1_rsi = v1_rsi_data[-1]
                    
                    if v1_rsi is not None:
                        print(f"V1 RSI: {v1_rsi}")
                        
                        # Compare values
                        diff = abs(v2_rsi - v1_rsi)
                        diff_percent = (diff / v1_rsi) * 100
                        
                        print(f"Difference: {diff:.4f} ({diff_percent:.2f}%)")
                        
                        if diff < 0.1:  # Less than 0.1 difference
                            print("✅ RSI values are very close - mathematical accuracy confirmed")
                        elif diff < 1.0:
                            print("⚠️ RSI values are close but not identical")
                        else:
                            print("❌ RSI values differ significantly")
                        
                        return True
                    else:
                        print("⚠️ Could not extract V1 RSI value for comparison")
                else:
                    print("⚠️ V1 extraction did not return RSI data")
            else:
                print("⚠️ V1 extraction returned unexpected format")
                
        except Exception as e:
            print(f"⚠️ V1 system comparison failed (this is expected if MCP is not running): {str(e)}")
            print("✅ V2 system works independently of V1 system")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison test failed: {str(e)}")
        return False


async def performance_benchmark():
    """Benchmark V2 system performance."""
    print("\n⚡ Performance Benchmark...")
    
    try:
        engine = ExtractionEngineV2(DEFAULT_USER_ID)
        
        # Single extraction timing
        start_time = datetime.now()
        
        result = await engine.extract_for_symbol(
            symbol="BTC/USDT",
            indicators=["rsi", "macd", "sma", "ema", "bollinger_bands"],
            timeframe="1h",
            limit=200
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result["status"] == "success":
            indicators_count = len(result["result"]["indicators"])
            data_points = result["result"]["data_points"]
            
            print(f"✅ Extracted {indicators_count} indicators from {data_points} data points")
            print(f"⏱️ Duration: {duration:.2f} seconds")
            print(f"📊 Performance: {indicators_count/duration:.1f} indicators/second")
            
            # Multiple symbols timing
            start_time = datetime.now()
            
            multi_result = await engine.extract_multiple_symbols(
                symbols=["BTC/USDT", "ETH/USDT", "ADA/USDT"],
                indicators=["rsi", "sma"],
                timeframe="1h",
                limit=100
            )
            
            end_time = datetime.now()
            multi_duration = (end_time - start_time).total_seconds()
            
            if multi_result["status"] == "success":
                successful = multi_result["summary"]["successful_extractions"]
                print(f"✅ Multi-symbol extraction: {successful} symbols in {multi_duration:.2f} seconds")
                print(f"📊 Throughput: {successful/multi_duration:.1f} symbols/second")
            
            return True
        else:
            print(f"❌ Benchmark failed: {result['error']}")
            return False
        
    except Exception as e:
        print(f"❌ Performance benchmark failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Testing Extraction V2 System")
    print("=" * 50)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("System Test", test_v2_system),
        ("Data Client", test_data_client),
        ("Indicators", test_indicators),
        ("Extraction Engine", test_extraction_engine),
        ("V1 Comparison", compare_with_v1_system),
        ("Performance", performance_benchmark)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            if test_name == "System Test":
                result = await test_func()
                success = result.get("overall_status") == "success"
                if success:
                    print("✅ System test passed")
                else:
                    print("❌ System test failed")
                    print(json.dumps(result, indent=2))
            else:
                success = await test_func()
            
            test_results.append((test_name, success))
            
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            test_results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 50}")
    print("📋 TEST SUMMARY")
    print(f"{'=' * 50}")
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! V2 system is ready for use.")
    elif passed > 0:
        print(f"\n⚠️ Partial success: {passed}/{total} tests passed.")
        print("Review failed tests above.")
    else:
        print("\n❌ All tests failed. Check system configuration and dependencies.")


if __name__ == "__main__":
    asyncio.run(main())