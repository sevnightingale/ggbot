#!/usr/bin/env python
"""
Simple test script for CCXT MCP client.

This script tests basic functionality of the CCXT MCP client,
including connection and fetching market data.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
load_dotenv()

# Import necessary components
from core.mcp.ccxt import CCXTMCPClient
from core.common.logger import logger

async def test_ccxt_connection():
    """Test connecting to CCXT MCP server."""
    print("Testing CCXT MCP connection...")
    
    client = CCXTMCPClient(exchange_id=os.environ.get("EXCHANGE_NAME", "binance"))
    try:
        await client.connect()
        print("Connection successful!")
        return True
    except Exception as e:
        print(f"Connection failed: {type(e).__name__}: {str(e)}")
        return False
    finally:
        if client.is_connected:
            await client.disconnect()
            print("Disconnected from CCXT MCP server")

async def test_list_available_tools():
    """Test listing available tools on the server."""
    print("\nTesting list_tools...")
    
    client = CCXTMCPClient()
    try:
        await client.connect()
        tools = await client.session.get_tools()
        print(f"Found {len(tools)} tools, first 5 are:")
        for i, tool in enumerate(tools[:5]):
            print(f"{i+1}. {tool}")
        return True
    except Exception as e:
        print(f"list_tools failed: {type(e).__name__}: {str(e)}")
        return False
    finally:
        if client.is_connected:
            await client.disconnect()
            print("Disconnected from CCXT MCP server")

async def test_fetch_markets():
    """Test fetchMarkets which is available on the server."""
    print("\nTesting fetchMarkets...")
    
    exchange_id = os.environ.get("EXCHANGE_NAME", "binance")
    
    client = CCXTMCPClient(exchange_id=exchange_id)
    try:
        await client.connect()
        result = await client.session.call_tool(
            'fetchMarkets',
            {
                'exchangeId': exchange_id
            }
        )
        
        # Just print a summary to avoid overwhelming output
        market_count = len(result) if isinstance(result, list) else 'unknown'
        print(f"Got {market_count} markets")
        
        # Print first market if available
        if isinstance(result, list) and len(result) > 0:
            print(f"First market: {result[0]}")
            
        return True
    except Exception as e:
        print(f"fetchMarkets failed: {type(e).__name__}: {str(e)}")
        return False
    finally:
        if client.is_connected:
            await client.disconnect()
            print("Disconnected from CCXT MCP server")

async def test_fetch_ticker():
    """Test fetching ticker data for a symbol."""
    print("\nTesting fetchTicker...")
    
    exchange_id = os.environ.get("EXCHANGE_NAME", "binance")
    symbol = "BTC/USD"  # Using BTC/USD for Bitmex
    
    client = CCXTMCPClient(exchange_id=exchange_id)
    try:
        await client.connect()
        result = await client.session.call_tool(
            'fetchTicker',
            {
                'exchangeId': exchange_id,
                'symbol': symbol
            }
        )
        
        # Extract and print key information
        price = result.get('last', 'N/A')
        print(f"Current price for {symbol}: {price}")
        return True
    except Exception as e:
        print(f"fetchTicker failed: {type(e).__name__}: {str(e)}")
        return False
    finally:
        if client.is_connected:
            await client.disconnect()
            print("Disconnected from CCXT MCP server")

async def test_client_context_manager():
    """Test using the client as an async context manager."""
    print("\nTesting client as context manager...")
    
    exchange_id = os.environ.get("EXCHANGE_NAME", "binance")
    symbol = "ETH/USD"  # Using ETH/USD for Bitmex
    
    try:
        async with CCXTMCPClient(exchange_id=exchange_id) as client:
            print("Connected via context manager")
            print(f"Fetching ticker for {symbol} on {exchange_id}...")
            result = await client.session.call_tool(
                'fetchTicker',
                {
                    'exchangeId': exchange_id, 
                    'symbol': symbol
                }
            )
            price = result.get('last', 'N/A')
            print(f"Got ticker price: {price} USD")
        print("Context manager exited successfully")
        return True
    except Exception as e:
        print(f"Context manager test failed: {type(e).__name__}: {str(e)}")
        return False

async def main():
    """Main function to run all tests."""
    # Print loaded environment variables (without secrets)
    print(f"Using exchange: {os.environ.get('EXCHANGE_NAME', 'Not set')}")
    print(f"API key present: {bool(os.environ.get('EXCHANGE_API', ''))}")
    print(f"API secret present: {bool(os.environ.get('EXCHANGE_SECRET', ''))}")
    
    print("\nStarting CCXT MCP tests")
    
    # Run tests
    connection_success = await test_ccxt_connection()
    tools_success = await test_list_available_tools()
    markets_success = await test_fetch_markets()
    ticker_success = await test_fetch_ticker()
    context_success = await test_client_context_manager()
    
    # Print summary
    print("\n----- Test Results -----")
    print(f"Connection test: {'PASSED' if connection_success else 'FAILED'}")
    print(f"List tools test: {'PASSED' if tools_success else 'FAILED'}")
    print(f"Fetch markets test: {'PASSED' if markets_success else 'FAILED'}")
    print(f"Fetch ticker test: {'PASSED' if ticker_success else 'FAILED'}")
    print(f"Context manager test: {'PASSED' if context_success else 'FAILED'}")
    
    # Overall result
    all_passed = all([
        connection_success,
        tools_success,
        markets_success,
        ticker_success,
        context_success
    ])
    
    print("\nOverall result:", "PASSED" if all_passed else "FAILED")

if __name__ == "__main__":
    asyncio.run(main())