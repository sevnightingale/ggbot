"""
Test script for Advanced Preprocessing V2 System.

This script demonstrates the sophisticated analysis capabilities of the 
Python-native preprocessor compared to simple analysis.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from datetime import datetime

# V2 system imports
from extraction.v2.extraction_engine import ExtractionEngineV2, extract_indicators


async def demo_simple_vs_advanced():
    """Demonstrate simple vs advanced preprocessing side by side."""
    
    print("🎯 Advanced Preprocessing Demo")
    print("=" * 60)
    
    symbol = "BTC/USDT"
    indicators = ["rsi", "macd"]
    
    # Simple preprocessing
    print("\n🔹 SIMPLE ANALYSIS:")
    print("-" * 30)
    
    simple_result = await extract_indicators(
        symbol=symbol,
        indicators=indicators,
        use_advanced_preprocessing=False,
        limit=100
    )
    
    if simple_result["status"] == "success":
        simple_rsi = simple_result["result"]["indicators"]["rsi"]
        simple_macd = simple_result["result"]["indicators"]["macd"]
        
        print(f"RSI: {simple_rsi['current']} ({simple_rsi['analysis']['zone']})")
        print(f"MACD: {simple_macd['current']['macd']:.4f} ({simple_macd['analysis']['trend']})")
    
    # Advanced preprocessing
    print("\n🔸 ADVANCED ANALYSIS:")
    print("-" * 30)
    
    advanced_result = await extract_indicators(
        symbol=symbol,
        indicators=indicators,
        use_advanced_preprocessing=True,
        limit=100
    )
    
    if advanced_result["status"] == "success":
        advanced_rsi = advanced_result["result"]["indicators"]["rsi"]
        advanced_macd = advanced_result["result"]["indicators"]["macd"]
        
        # Display sophisticated RSI analysis
        print(f"📊 RSI Analysis:")
        print(f"   Current: {advanced_rsi['current']['value']}")
        print(f"   Trend: {advanced_rsi['trend']['direction']} (strength: {advanced_rsi['trend']['strength']:.3f})")
        print(f"   Velocity: {advanced_rsi['trend']['velocity']:.3f}")
        print(f"   Zone: {advanced_rsi['zones']['current_zone']}")
        print(f"   Recent High: {advanced_rsi['extremes']['recent_high']['value']} ({advanced_rsi['extremes']['recent_high']['periods_ago']}p ago)")
        print(f"   Summary: {advanced_rsi['summary']}")
        
        # Display signals
        if advanced_rsi.get('signals'):
            print(f"   Signals: {len(advanced_rsi['signals'])} detected")
            for signal in advanced_rsi['signals']:
                print(f"     • {signal['type']}: {signal['reason']} (confidence: {signal['confidence']:.2f})")
        
        # Display patterns
        if advanced_rsi.get('patterns'):
            print(f"   Patterns: {len(advanced_rsi['patterns'])} detected")
            for pattern_name, pattern in advanced_rsi['patterns'].items():
                if isinstance(pattern, dict):
                    print(f"     • {pattern_name}: {pattern.get('description', 'N/A')}")
        
        print(f"   Overall Confidence: {advanced_rsi['confidence']}")
        
        print(f"\n📈 MACD Analysis:")
        print(f"   Current: MACD={advanced_macd['current']['macd']:.4f}, Signal={advanced_macd['current']['signal']:.4f}")
        print(f"   Trend: {advanced_macd['trend']['direction']} (strength: {advanced_macd['trend']['strength']:.3f})")
        print(f"   Momentum: {advanced_macd['trend']['momentum']}")
        
        # Display crossovers
        if advanced_macd.get('crossovers', {}).get('recent_crossovers'):
            print(f"   Recent Crossovers:")
            for crossover in advanced_macd['crossovers']['recent_crossovers']:
                print(f"     • {crossover['type']} {crossover['periods_ago']}p ago")
        
        # Display signals
        if advanced_macd.get('signals'):
            print(f"   Signals: {len(advanced_macd['signals'])} detected")
            for signal in advanced_macd['signals']:
                print(f"     • {signal['type']}: {signal['reason']}")
        
        print(f"   Summary: {advanced_macd['summary']}")
    
    print(f"\n📁 Results saved to: {simple_result.get('result', {}).get('file_path', 'N/A')}")
    print(f"📁 Advanced results saved to: {advanced_result.get('result', {}).get('file_path', 'N/A')}")


async def demo_multiple_symbols():
    """Demonstrate advanced analysis on multiple symbols."""
    
    print("\n\n🌐 Multi-Symbol Advanced Analysis")
    print("=" * 60)
    
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    indicators = ["rsi", "macd", "sma"]
    
    engine = ExtractionEngineV2(user_id="demo", use_advanced_preprocessing=True)
    
    try:
        result = await engine.extract_multiple_symbols(
            symbols=symbols,
            indicators=indicators,
            timeframe="1h",
            limit=100
        )
        
        if result["status"] == "success":
            print(f"✅ Processed {result['summary']['successful_extractions']}/{result['summary']['total_symbols']} symbols")
            
            for symbol, symbol_result in result["results"].items():
                if symbol_result["status"] == "success":
                    print(f"\n📊 {symbol}:")
                    indicators_data = symbol_result["result"]["indicators"]
                    
                    # RSI summary
                    if "rsi" in indicators_data:
                        rsi = indicators_data["rsi"]
                        trend = rsi.get("trend", {})
                        zones = rsi.get("zones", {})
                        print(f"   RSI: {rsi['current']['value']:.1f} | {trend.get('direction', 'N/A')} | {zones.get('current_zone', 'N/A')}")
                    
                    # MACD summary
                    if "macd" in indicators_data:
                        macd = indicators_data["macd"]
                        trend_info = macd.get("trend", {})
                        print(f"   MACD: {trend_info.get('direction', 'N/A')} trend | {trend_info.get('momentum', 'N/A')} momentum")
                    
                    # SMA summary
                    if "sma" in indicators_data:
                        sma = indicators_data["sma"]
                        analysis = sma.get("analysis", {})
                        print(f"   SMA: Price {analysis.get('price_position', 'N/A')} SMA | Trend: {analysis.get('trend', 'N/A')}")
                
                else:
                    print(f"\n❌ {symbol}: {symbol_result.get('error', 'Unknown error')}")
            
            print(f"\n📁 Batch results saved to: {result.get('file_path', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Multi-symbol analysis failed: {str(e)}")


async def demo_file_system():
    """Demonstrate file storage system."""
    
    print("\n\n📁 File Storage System Demo")
    print("=" * 60)
    
    from extraction.v2.file_storage import FileStorage
    
    storage = FileStorage(base_dir="demo_results")
    
    # List recent files
    recent_files = storage.list_results(limit=5)
    
    print(f"📋 Recent extraction files:")
    for file_info in recent_files:
        size_mb = file_info["size"] / 1024 / 1024
        print(f"   • {file_info['name']} ({size_mb:.2f}MB) - {file_info['modified']}")
    
    # Load latest result
    if recent_files:
        latest = storage.load_latest_result()
        if latest:
            print(f"\n📄 Latest result preview:")
            if "result" in latest and "indicators" in latest["result"]:
                indicators_count = len(latest["result"]["indicators"])
                symbol = latest["result"].get("symbol", "Unknown")
                print(f"   Symbol: {symbol}")
                print(f"   Indicators: {indicators_count} calculated")
                print(f"   Timestamp: {latest['result'].get('timestamp', 'N/A')}")


async def performance_comparison():
    """Compare performance between simple and advanced preprocessing."""
    
    print("\n\n⚡ Performance Comparison")
    print("=" * 60)
    
    from datetime import datetime
    import time
    
    symbol = "BTC/USDT"
    indicators = ["rsi", "macd", "sma", "ema"]
    
    # Test simple preprocessing
    start_time = time.time()
    simple_result = await extract_indicators(
        symbol=symbol,
        indicators=indicators,
        use_advanced_preprocessing=False,
        limit=200
    )
    simple_duration = time.time() - start_time
    
    # Test advanced preprocessing
    start_time = time.time()
    advanced_result = await extract_indicators(
        symbol=symbol,
        indicators=indicators,
        use_advanced_preprocessing=True,
        limit=200
    )
    advanced_duration = time.time() - start_time
    
    print(f"📊 Performance Results:")
    print(f"   Simple Analysis:   {simple_duration:.3f}s")
    print(f"   Advanced Analysis: {advanced_duration:.3f}s")
    print(f"   Overhead:          {((advanced_duration / simple_duration - 1) * 100):+.1f}%")
    
    # Compare output sizes
    if simple_result["status"] == "success" and advanced_result["status"] == "success":
        simple_data = json.dumps(simple_result["result"]["indicators"])
        advanced_data = json.dumps(advanced_result["result"]["indicators"])
        
        print(f"\n📈 Data Richness:")
        print(f"   Simple Output:     {len(simple_data):,} characters")
        print(f"   Advanced Output:   {len(advanced_data):,} characters")
        print(f"   Information Gain:  {((len(advanced_data) / len(simple_data) - 1) * 100):+.1f}%")


async def main():
    """Run all demonstration tests."""
    
    print("🚀 Advanced Preprocessing V2 System Demo")
    print("=" * 80)
    print("This demonstration showcases the sophisticated analysis capabilities")
    print("of the Python-native preprocessor system.\n")
    
    # Set credentials
    os.environ["HBOT_USERNAME"] = "sev"
    os.environ["HBOT_PASSWORD"] = "7nyhi93cT0Ow2X7S"
    
    try:
        await demo_simple_vs_advanced()
        await demo_multiple_symbols()
        await demo_file_system()
        await performance_comparison()
        
        print("\n\n🎉 Demo Complete!")
        print("=" * 80)
        print("Key Features Demonstrated:")
        print("✅ Sophisticated RSI analysis with trend, velocity, patterns")
        print("✅ Advanced MACD analysis with crossovers and signals")
        print("✅ Multi-symbol concurrent processing")
        print("✅ File-based storage system")
        print("✅ Performance comparison")
        print("✅ Rich analytical insights vs simple calculations")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())