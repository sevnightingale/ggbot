#!/usr/bin/env python3
"""
Debug BollingerBandsWidth calculation issue.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parents[1]))

from core.mcp.indicators import IndicatorsMCPClient
from core.common.logger import logger

async def debug_bollinger_bands_width():
    """Debug the BollingerBandsWidth calculation."""
    
    print("🔍 Debugging BollingerBandsWidth Error")
    print("=" * 60)
    
    # Create MCP client
    mcp_client = IndicatorsMCPClient()
    
    try:
        # Connect to MCP
        await mcp_client.connect()
        print("✅ Connected to MCP server")
        
        # Test parameters
        symbol = "BTC/USDT"
        timeframe = "1h"
        
        print(f"\n📊 Testing with {symbol} on {timeframe}")
        
        # Test 1: Regular Bollinger Bands (this should work)
        print("\n1️⃣ Testing regular BollingerBands...")
        try:
            bb_params = {
                "symbol": symbol,
                "timeframe": timeframe,
                "period": 20,
                "stdDev": 2,
                "limit": 100
            }
            
            bb_result = await mcp_client.session.call_tool('calculate_bollinger_bands', bb_params)
            print(f"✅ BollingerBands: {str(bb_result)[:100]}...")
            
        except Exception as e:
            print(f"❌ BollingerBands failed: {str(e)}")
        
        # Test 2: Bollinger Bands Width (this is failing)
        print("\n2️⃣ Testing BollingerBandsWidth...")
        try:
            bbw_params = {
                "symbol": symbol,
                "timeframe": timeframe,
                "period": 20,
                "stdDev": 2,
                "limit": 100
            }
            
            bbw_result = await mcp_client.session.call_tool('calculate_bollinger_bands_width', bbw_params)
            print(f"✅ BollingerBandsWidth: {str(bbw_result)[:100]}...")
            
        except Exception as e:
            print(f"❌ BollingerBandsWidth failed: {str(e)}")
        
        # Test 3: Try with different parameters
        print("\n3️⃣ Testing BollingerBandsWidth with minimal params...")
        try:
            minimal_params = {
                "symbol": symbol
            }
            
            bbw_result = await mcp_client.session.call_tool('calculate_bollinger_bands_width', minimal_params)
            print(f"✅ BollingerBandsWidth (minimal): {str(bbw_result)[:100]}...")
            
        except Exception as e:
            print(f"❌ BollingerBandsWidth (minimal) failed: {str(e)}")
        
        # Test 4: List available tools to confirm the tool exists
        print("\n4️⃣ Checking available tools...")
        tools = await mcp_client.session.get_tools()
        bb_tools = [tool for tool in tools if 'bollinger' in tool.name.lower()]
        print("Found Bollinger tools:")
        for tool in bb_tools:
            print(f"  - {tool.name}: {tool.description}")
            
    except Exception as e:
        print(f"❌ Failed to connect or test: {str(e)}")
        
    finally:
        try:
            await mcp_client.disconnect()
            print("\n✅ Disconnected from MCP")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(debug_bollinger_bands_width())