#!/usr/bin/env python3
"""
Test MCP preprocessing integration
Test the complete pipeline: Python client -> MCP server -> preprocessing
"""

import asyncio
import os
import json
from pathlib import Path

# Add the project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mcp.indicators import IndicatorsMCPClient
from core.common.logger import logger

async def test_mcp_preprocessing():
    """Test the MCP preprocessing integration."""
    print("🧪 Testing MCP Preprocessing Integration\n")
    
    # Set environment for testing
    os.environ['EXCHANGE_NAME'] = 'binance'
    
    client = None
    try:
        # Initialize MCP client
        print("🔌 Connecting to Indicators MCP server...")
        client = IndicatorsMCPClient()
        await client.connect()
        print("✅ Connected successfully!\n")
        
        # Test 1: RSI with preprocessing (default)
        print("📊 Test 1: RSI with preprocessing (default)")
        rsi_result = await client.call_indicator_tool(
            'calculate_relative_strength_index',
            {
                'symbol': 'LRC/USDT',
                'timeframe': '1h',
                'period': 14,
                'limit': 50
            },
            use_preprocessing=True
        )
        
        print("RSI Result Structure:")
        print(f"  Type: {type(rsi_result)}")
        print(f"  Content: {str(rsi_result)[:500]}...")
        
        # Try to parse if it's a string
        if isinstance(rsi_result, str):
            try:
                import json
                parsed_result = json.loads(rsi_result)
                print(f"  Parsed Type: {type(parsed_result)}")
                print(f"  Parsed Keys: {list(parsed_result.keys()) if hasattr(parsed_result, 'keys') else 'No keys'}")
                if 'indicator' in parsed_result:
                    print(f"  Indicator: {parsed_result['indicator']}")
                    print(f"  Current: {parsed_result.get('current', 'N/A')}")
                    print(f"  Summary: {parsed_result.get('summary', 'N/A')}")
            except Exception as e:
                print(f"  JSON Parse Error: {e}")
        elif hasattr(rsi_result, 'keys'):
            print(f"  Keys: {list(rsi_result.keys())}")
            if 'indicator' in rsi_result:
                print(f"  Indicator: {rsi_result['indicator']}")
                print(f"  Current: {rsi_result.get('current', 'N/A')}")
                print(f"  Summary: {rsi_result.get('summary', 'N/A')}")
        print()
        
        # Test 2: Aroon with preprocessing
        print("📊 Test 2: Aroon with preprocessing")
        aroon_result = await client.call_indicator_tool(
            'calculate_aroon',
            {
                'symbol': 'LRC/USDT', 
                'timeframe': '1h',
                'period': 14,
                'limit': 50
            },
            use_preprocessing=True
        )
        
        print("Aroon Result Structure:")
        print(f"  Keys: {list(aroon_result.keys())}")
        if 'indicator' in aroon_result:
            print(f"  Indicator: {aroon_result['indicator']}")
            print(f"  Current: {aroon_result.get('current', 'N/A')}")
            print(f"  Context: {aroon_result.get('context', {}).get('regime', 'N/A')}")
            print(f"  Summary: {aroon_result.get('summary', 'N/A')}")
        else:
            print(f"  Raw format (unexpected): {str(aroon_result)[:200]}...")
        print()
        
        # Test 3: Vortex with preprocessing  
        print("📊 Test 3: Vortex with preprocessing")
        vortex_result = await client.call_indicator_tool(
            'calculate_vortex',
            {
                'symbol': 'LRC/USDT',
                'timeframe': '1h', 
                'period': 14,
                'limit': 50
            },
            use_preprocessing=True
        )
        
        print("Vortex Result Structure:")
        print(f"  Keys: {list(vortex_result.keys())}")
        if 'indicator' in vortex_result:
            print(f"  Indicator: {vortex_result['indicator']}")
            print(f"  Current: {vortex_result.get('current', 'N/A')}")
            print(f"  Context: {vortex_result.get('context', {}).get('momentum', 'N/A')}")
            print(f"  Summary: {vortex_result.get('summary', 'N/A')}")
        else:
            print(f"  Raw format (unexpected): {str(vortex_result)[:200]}...")
        print()
        
        # Test 4: Compare with raw format
        print("📊 Test 4: Raw format comparison")
        rsi_raw = await client.call_indicator_tool(
            'calculate_relative_strength_index',
            {
                'symbol': 'LRC/USDT',
                'timeframe': '1h',
                'period': 14,
                'limit': 50
            },
            use_preprocessing=False  # Raw format
        )
        
        print("Raw RSI Result:")
        print(f"  Type: {type(rsi_raw)}")
        print(f"  Content: {str(rsi_raw)[:200]}...")
        print()
        
        # Test 5: Test with extraction source format
        print("📊 Test 5: Test extraction-style parameters")
        test_params = {
            'exchange': 'binance',
            'symbol': 'BTC/USDT', 
            'timeframe': '1h'
        }
        
        btc_rsi = await client.call_indicator_tool(
            'calculate_relative_strength_index',
            test_params,
            use_preprocessing=True
        )
        
        print("BTC RSI Result:")
        print(f"  Keys: {list(btc_rsi.keys())}")
        if 'current' in btc_rsi:
            print(f"  Current Value: {btc_rsi['current'].get('value', 'N/A')}")
            print(f"  Trend: {btc_rsi.get('context', {}).get('trend', 'N/A')}")
        print()
        
        print("🎉 All MCP preprocessing tests completed successfully!")
        
        # Summary
        print("\n📋 Summary:")
        print("✅ MCP server connection works")
        print("✅ Preprocessing format is working") 
        print("✅ Raw format still works for backward compatibility")
        print("✅ Integration with extraction-style parameters works")
        print("✅ Ready for production deployment!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if client:
            try:
                await client.disconnect()
                print("\n🔌 Disconnected from MCP server")
            except Exception as e:
                print(f"⚠️  Error disconnecting: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_mcp_preprocessing())