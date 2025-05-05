"""
Basic MCP connectivity test script.

This script performs minimal testing of MCP connectivity without requiring
authenticated exchange access.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import only what we need for basic connectivity testing
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession


async def test_ccxt_mcp_connection():
    """Test basic connection to CCXT MCP server."""
    print("\n=== Testing CCXT MCP Connection ===")
    
    # CCXT MCP config path
    ccxt_config_path = os.path.join(project_root, 'core', 'config', 'ccxt-accounts.json')
    
    try:
        # Set up connection parameters
        params = StdioServerParameters(
            command=f"ccxt-mcp --config {ccxt_config_path}"
        )
        
        # Connect to the CCXT MCP server
        print("Connecting to CCXT MCP server...")
        async with stdio_client(params) as streams:
            print("Established stream connection, initializing session...")
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("Session initialized!")
                
                # Test a simple public API call
                print("Fetching available exchange IDs...")
                exchange_ids = await session.call_tool("getExchangeIds", {})
                if 'ids' in exchange_ids:
                    print(f"Success! Found {len(exchange_ids['ids'])} exchanges")
                    print(f"Sample exchanges: {', '.join(exchange_ids['ids'][:5])}")
                else:
                    print(f"Unexpected response: {exchange_ids}")
                
                print("Connection test completed successfully!")
                
    except Exception as e:
        print(f"Error connecting to CCXT MCP: {str(e)}")
        

async def test_indicators_mcp_connection():
    """Test basic connection to Crypto Indicators MCP server."""
    print("\n=== Testing Crypto Indicators MCP Connection ===")
    
    # Crypto Indicators MCP script path
    crypto_indicators_path = os.path.join(
        project_root, 'core', 'mcp', 'servers', 'crypto-indicators-mcp', 'index.js'
    )
    
    try:
        # Set up connection parameters
        params = StdioServerParameters(
            command=f"node {crypto_indicators_path}",
            env={'EXCHANGE_NAME': 'binance'}  # This is just a default setting
        )
        
        # Connect to the Crypto Indicators MCP server
        print("Connecting to Crypto Indicators MCP server...")
        async with stdio_client(params) as streams:
            print("Established stream connection, initializing session...")
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("Session initialized!")
                
                # Get available tools (which should include all the indicators)
                print("Fetching available tools...")
                tools = await session.get_tools()
                print(f"Success! Found {len(tools)} tools")
                
                # If we have tools, test a simple calculation with dummy data
                if tools:
                    print("Testing a simple RSI calculation with sample data...")
                    sample_prices = [100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 108.0, 
                                     107.0, 105.0, 104.0, 103.0, 104.0, 105.0, 106.0]
                    
                    rsi_result = await session.call_tool(
                        "calculateRSI", 
                        {"prices": sample_prices, "period": 14}
                    )
                    
                    if 'values' in rsi_result:
                        print(f"RSI calculation successful! Last value: {rsi_result['values'][-1]:.2f}")
                    else:
                        print(f"Unexpected RSI response: {rsi_result}")
                
                print("Connection test completed successfully!")
                
    except Exception as e:
        print(f"Error connecting to Crypto Indicators MCP: {str(e)}")


async def main():
    """Run all tests."""
    try:
        await test_ccxt_mcp_connection()
        await test_indicators_mcp_connection()
        print("\nAll tests completed!")
    except Exception as e:
        print(f"\nError in main test routine: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())