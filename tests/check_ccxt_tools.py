#!/usr/bin/env python3
"""
Check what tools are available in the CCXT MCP server.
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mcp.ccxt import CCXTMCPClient
from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID


async def check_ccxt_tools():
    """Check what tools are available in CCXT MCP."""
    print("Checking CCXT MCP available tools...")
    
    client = CCXTMCPClient(user_id=DEFAULT_USER_ID)
    
    try:
        await client.connect()
        print("✓ Connected to CCXT MCP server")
        
        # Get available tools via session
        tools = await client.session.list_tools()
        print(f"\nAvailable tools ({len(tools)}):")
        
        for tool in tools:
            print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')}")
        
        return tools
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return []
    
    finally:
        await client.disconnect()


async def test_specific_tool():
    """Test a specific tool to see if it works."""
    print("\nTesting specific tools...")
    
    client = CCXTMCPClient(user_id=DEFAULT_USER_ID)
    
    try:
        await client.connect()
        
        # Try to get ticker using session
        try:
            result = await client.session.call_tool(
                'fetch_ohlcv',
                {
                    'exchange_id': 'binance',
                    'symbol': 'BTC/USDT',
                    'timeframe': '15m',
                    'limit': 1
                }
            )
            print("✓ fetch_ohlcv works:", len(result) if result else "No data")
            
            if result:
                latest_price = result[0][4]  # Close price
                print(f"  Latest BTC/USDT close: ${latest_price:,.2f}")
            
        except Exception as e:
            print(f"✗ fetch_ohlcv error: {str(e)}")
        
        # Try ticker if available
        try:
            result = await client.session.call_tool(
                'fetch_ticker',
                {
                    'exchange_id': 'binance',
                    'symbol': 'BTC/USDT'
                }
            )
            print("✓ fetch_ticker works:", result.get('last') if result else "No data")
            
        except Exception as e:
            print(f"✗ fetch_ticker error: {str(e)}")
        
    except Exception as e:
        print(f"✗ Connection error: {str(e)}")
    
    finally:
        await client.disconnect()


async def main():
    """Run all checks."""
    tools = await check_ccxt_tools()
    await test_specific_tool()
    
    print(f"\nSummary: Found {len(tools)} available tools")


if __name__ == "__main__":
    asyncio.run(main())