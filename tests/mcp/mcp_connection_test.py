"""
Test script for verifying connectivity with both MCP servers.
Based on MCP SDK version 1.7.1 format requirements.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_test")

# Import the MCP SDK components
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession


async def test_crypto_indicators_mcp():
    """Test connection to the Crypto Indicators MCP server."""
    logger.info("=== Testing Crypto Indicators MCP ===")
    
    # Get the path to the Crypto Indicators MCP script
    script_path = os.path.join(
        project_root, 'core', 'mcp', 'servers', 'crypto-indicators-mcp', 'index.js'
    )
    
    # Verify the script exists
    if not os.path.exists(script_path):
        logger.error(f"Script not found at: {script_path}")
        return
    
    logger.info(f"Using script at: {script_path}")
    
    try:
        # Set up server parameters using the correct format for SDK 1.7.1
        params = StdioServerParameters(
            command="node",
            args=[script_path],
            env={"EXCHANGE_NAME": "binance"}
        )
        
        # Connect to the server
        logger.info("Connecting to Crypto Indicators MCP server...")
        async with stdio_client(params) as streams:
            logger.info("Stream connection established, initializing session...")
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                logger.info("Session initialized successfully!")
                
                # Get available tools
                logger.info("Fetching available tools...")
                tools = await session.get_tools()
                logger.info(f"Found {len(tools)} tools")
                
                # Display some tool names
                if tools:
                    tool_names = [tool.get('name', 'Unknown') for tool in tools[:5]]
                    logger.info(f"Sample tools: {', '.join(tool_names)}")
                
                # Test a calculation if RSI tool is available
                rsi_tool = next((t.get('name') for t in tools 
                               if 'rsi' in t.get('name', '').lower()), None)
                
                if rsi_tool:
                    logger.info(f"Testing {rsi_tool} with sample data...")
                    sample_prices = [100.0, 102.0, 104.0, 103.0, 105.0, 107.0]
                    
                    result = await session.call_tool(
                        rsi_tool, 
                        {"prices": sample_prices, "period": 14}
                    )
                    logger.info(f"Calculation result: {result}")
                else:
                    logger.info("No RSI calculation tool found")
                
                logger.info("Crypto Indicators MCP test completed successfully!")
                
    except Exception as e:
        logger.error(f"Error testing Crypto Indicators MCP: {str(e)}")


async def test_ccxt_mcp():
    """Test connection to the CCXT MCP server."""
    logger.info("=== Testing CCXT MCP ===")
    
    # Get the path to the CCXT MCP config file
    config_path = os.path.join(project_root, 'core', 'config', 'ccxt-accounts.json')
    
    # Verify the config file exists
    if not os.path.exists(config_path):
        logger.error(f"Config file not found at: {config_path}")
        return
    
    logger.info(f"Using config at: {config_path}")
    
    try:
        # Set up server parameters using the correct format for SDK 1.7.1
        params = StdioServerParameters(
            command="ccxt-mcp",
            args=["--config", config_path]
        )
        
        # Connect to the server
        logger.info("Connecting to CCXT MCP server...")
        async with stdio_client(params) as streams:
            logger.info("Stream connection established, initializing session...")
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                logger.info("Session initialized successfully!")
                
                # Get available tools
                logger.info("Fetching available tools...")
                tools = await session.get_tools()
                logger.info(f"Found {len(tools)} tools")
                
                # Display some tool names
                if tools:
                    tool_names = [tool.get('name', 'Unknown') for tool in tools[:5]]
                    logger.info(f"Sample tools: {', '.join(tool_names)}")
                
                # Test getExchangeIds if available
                exchange_ids_tool = next((t.get('name') for t in tools 
                                      if 'getExchangeIds' in t.get('name', '')), None)
                
                if exchange_ids_tool:
                    logger.info(f"Testing {exchange_ids_tool}...")
                    result = await session.call_tool(exchange_ids_tool, {})
                    logger.info(f"Found exchanges: {result}")
                else:
                    logger.info("No getExchangeIds tool found")
                
                logger.info("CCXT MCP test completed successfully!")
                
    except Exception as e:
        logger.error(f"Error testing CCXT MCP: {str(e)}")


async def main():
    """Run all tests."""
    try:
        await test_crypto_indicators_mcp()
        await test_ccxt_mcp()
    except Exception as e:
        logger.error(f"Error in main routine: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())