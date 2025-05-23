#!/usr/bin/env python
"""
Test for position monitoring functionality (Step 28 in FLOW.md).

This test focuses on trade status monitoring, using direct tool calls to
demonstrate which tools are most effective for retrieving trading data
from the BitMEX testnet.
"""

import os
import sys
import asyncio
import json
import uuid
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables for API keys
load_dotenv()

# Set environment variables
os.environ["TESTNET"] = "1"
os.environ["EXCHANGE_NAME"] = "bitmex"

# Make sure OpenAI key is set from TRADING_LLM_API_KEY
if "TRADING_LLM_API_KEY" in os.environ:
    os.environ["OPENAI_API_KEY"] = os.environ["TRADING_LLM_API_KEY"]

from core.common.logger import logger
from trading.engine.model.intent import Intent
from trading.engine.model.config import EngineConfig
from trading.engine.model.tool_call import ToolCall
from trading.engine.service.llm_service import LLMService
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter
from core.mcp.ccxt import CCXTMCPClient

# Configure logging
import logging
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])

# This section intentionally left blank - no parsing functions needed
# The test now only retrieves and stores raw data from the exchange

async def main():
    """Run a simplified test for trade status monitoring."""
    logger.info("Starting trade status monitoring test")
    
    # Create unique user ID for testing
    user_id = str(uuid.uuid4())
    exchange_id = "bitmex"
    
    # Create config
    config = EngineConfig(
        llm={
            "model": "gpt-4.1",
            "system_prompt": "You are an expert trading assistant specializing in cryptocurrency exchange APIs. Your task is to find information about active trades and positions by using the appropriate exchange API tools. When searching for active trades, prioritize tools that could return position details, open orders, or account balance data.",
            "temperature": 0.0,
            "max_retries": 2
        },
        validation={
            "max_leverage": 10,
            "max_position_pct": 0.05
        },
        execution={
            "polling_interval": 5,  # Use shorter interval for testing
            "max_retries": 2
        },
        default_exchange="bitmex",
        use_testnet=True,
        server_path=str(Path(__file__).parent.parent.parent / "core" / "mcp" / "servers" / "ccxt_mcp_server.py"),
        credentials={
            "apiKey": os.environ.get("EXCHANGE_API"),
            "secret": os.environ.get("EXCHANGE_SECRET")
        }
    )
    
    # Create MCP client
    logger.info(f"Using server path: {config.server_path}")
    
    mcp_client = CCXTMCPClient(
        exchange_id=exchange_id,
        user_id=user_id,
        use_local_server=True,
        server_path=config.server_path
    )
    
    # Connect to MCP server
    logger.info("Connecting to MCP server...")
    await mcp_client.connect()
    logger.info("MCP client connected successfully")
    
    # Create CCXT adapter
    logger.info("Creating CCXT adapter...")
    adapter = CCXTMCPAdapter(
        exchange_id=exchange_id,
        user_id=user_id,
        config=config.model_dump()
    )
    adapter.mcp_client = mcp_client
    adapter.connected = True
    
    # Print adapter and client info
    logger.info(f"Adapter exchange: {adapter.exchange_id}")
    logger.info(f"MCP client connected: {mcp_client.is_connected}")
    logger.info(f"MCP client has session: {hasattr(mcp_client, 'session')}")
    
    # Initialize LLM service
    logger.info("Creating LLM service...")
    llm_service = LLMService(config=config, user_id=user_id)
    
    try:
        # First test: Run a series of direct tool calls to gather trade status
        await run_direct_tool_calls(adapter)
        
        # Second test: Use LLM to determine the best tools for monitoring
        await run_llm_trade_monitoring(adapter, llm_service)
        
        logger.info("All trade status monitoring tests completed successfully")
    finally:
        # Clean up
        if mcp_client and mcp_client.is_connected:
            logger.info("Disconnecting MCP client...")
            await mcp_client.disconnect()

async def run_direct_tool_calls(adapter):
    """Run direct tool calls to get raw trade status data from the exchange."""
    logger.info("\n=== DISCOVERING AVAILABLE TRADE STATUS TOOLS ===")
    
    # First get the list of available tools from the adapter
    logger.info("Getting available tools...")
    available_tools = await adapter.get_tools_schema()
    tool_names = [tool["name"] for tool in available_tools]
    logger.info(f"Available tools: {tool_names}")
    
    # Try relevant tools for trade and position status based on what's available
    results = []
    working_tools = []
    
    # Try fetch_orders if available - should show our active trade
    if "fetch_orders" in tool_names:
        tool = "fetch_orders"
        params = {"symbol": "BTC/USD:BTC", "limit": 5}
        
        logger.info(f"Trying {tool} to get trade status...")
        try:
            result = await adapter.call_tool(tool, params)
            logger.info(f"Received raw result from {tool}")
            
            # Record the raw result
            results.append({
                "tool": tool,
                "parameters": params,
                "raw_result": result
            })
            
            working_tools.append(tool)
            logger.info(f"✓ Tool {tool} executed successfully")
                
        except Exception as e:
            logger.error(f"✗ Error with {tool}: {e}")
            results.append({
                "tool": tool,
                "parameters": params,
                "error": str(e)
            })
    
    # Try fetch_balance - shows account status
    if "fetch_balance" in tool_names:
        tool = "fetch_balance"
        params = {}
        
        logger.info(f"Trying {tool} to get account and position status...")
        try:
            result = await adapter.call_tool(tool, params)
            logger.info(f"Received raw result from {tool}")
            
            # Record the raw result
            results.append({
                "tool": tool,
                "parameters": params,
                "raw_result": result
            })
            
            working_tools.append(tool)
            logger.info(f"✓ Tool {tool} executed successfully")
                
        except Exception as e:
            logger.error(f"✗ Error with {tool}: {e}")
            results.append({
                "tool": tool,
                "parameters": params,
                "error": str(e)
            })
    
    # Try fetch_positions if available
    if "fetch_positions" in tool_names:
        tool = "fetch_positions"
        params = {"symbol": "BTC/USD:BTC"}
        
        logger.info(f"Trying {tool} to get position details...")
        try:
            result = await adapter.call_tool(tool, params)
            logger.info(f"Received raw result from {tool}")
            
            # Record the raw result
            results.append({
                "tool": tool,
                "parameters": params,
                "raw_result": result
            })
            
            working_tools.append(tool)
            logger.info(f"✓ Tool {tool} executed successfully")
                
        except Exception as e:
            logger.error(f"✗ Error with {tool}: {e}")
            results.append({
                "tool": tool,
                "parameters": params,
                "error": str(e)
            })
    
    # Try fetch_ticker to get current price
    if "fetch_ticker" in tool_names:
        tool = "fetch_ticker"
        params = {"symbol": "BTC/USD:BTC"}
        
        logger.info(f"Trying {tool} to get current price...")
        try:
            result = await adapter.call_tool(tool, params)
            logger.info(f"Received raw result from {tool}")
            
            # Record the raw result
            results.append({
                "tool": tool,
                "parameters": params,
                "raw_result": result
            })
            
            working_tools.append(tool)
            logger.info(f"✓ Tool {tool} executed successfully")
                
        except Exception as e:
            logger.error(f"✗ Error with {tool}: {e}")
            results.append({
                "tool": tool,
                "parameters": params,
                "error": str(e)
            })
    
    # Save the raw results
    output_dir = Path(__file__).parent
    output_path = output_dir / "raw_trade_status_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved raw trade status results to {output_path}")
    logger.info(f"Working tools for trade status monitoring: {working_tools}")
    
    return working_tools

async def run_llm_trade_monitoring(adapter, llm_service):
    """Use an LLM to get raw trade status data from the exchange using appropriate tools."""
    logger.info("\n=== RUNNING LLM-BASED TRADE STATUS MONITORING ===")
    
    # Get available tools
    try:
        # Get tools directly from the adapter
        logger.info("Getting available tools from MCP adapter...")
        tools = await adapter.get_tools_schema()
        
        if not tools or len(tools) == 0:
            logger.error("No tools available from MCP adapter!")
            return
            
        logger.info(f"Retrieved {len(tools)} tools from MCP adapter")
        
        # Create a more specific intent for finding active trades
        trade_status_intent = {
            "decision_id": str(uuid.uuid4()),
            "action": "find_active_trades",
            "exchange": "bitmex",
            "query_type": "active_trade_details",
            "symbol": "BTC/USD",  # Focus on this specific trading pair
            "reason": "Need to find all information about active trades and positions for BTC/USD pair including current price, position size, unrealized PnL, and entry price."
        }
        
        # Process the intent with the LLM service
        logger.info("Asking LLM to generate tool calls for finding active trades...")
        tool_calls = await llm_service.process_intent(trade_status_intent, tools)
        
        if not tool_calls or len(tool_calls) == 0:
            logger.error("LLM did not generate any tool calls!")
            return
            
        logger.info(f"LLM generated {len(tool_calls)} tool calls:")
        for i, call in enumerate(tool_calls):
            logger.info(f"Tool call {i+1}: {call.tool} with params: {call.parameters}")
        
        # Execute the tool calls
        logger.info("Executing LLM-selected tools to find active trades...")
        status_data = []
        
        for i, call in enumerate(tool_calls):
            logger.info(f"Executing tool call {i+1}: {call.tool}")
            try:
                # Map symbol if needed
                if "symbol" in call.parameters:
                    symbol = call.parameters["symbol"]
                    mapped_symbol = adapter.map_symbol(symbol)
                    call.parameters["symbol"] = mapped_symbol
                    logger.info(f"Mapped symbol {symbol} to {mapped_symbol}")
                
                # Execute the tool call
                result = await adapter.call_tool(call.tool, call.parameters)
                logger.info(f"Received raw result from {call.tool}")
                
                # Record the raw result
                status_data.append({
                    "tool": call.tool,
                    "parameters": call.parameters,
                    "raw_result": result
                })
                
                logger.info(f"Tool call {i+1} executed successfully")
                
            except Exception as e:
                logger.error(f"Error executing tool {call.tool}: {e}")
                status_data.append({
                    "tool": call.tool,
                    "parameters": call.parameters,
                    "error": str(e)
                })
        
        # Save the raw results
        output_dir = Path(__file__).parent
        output_path = output_dir / "raw_llm_trade_status_results.json"
        with open(output_path, "w") as f:
            json.dump(status_data, f, indent=2)
        
        logger.info(f"Saved raw LLM-guided trade status results to {output_path}")
        
        # Count successful calls
        successful_calls = sum(1 for data in status_data if "error" not in data)
        logger.info(f"Successfully executed {successful_calls} of {len(status_data)} LLM-selected tools")
        
    except Exception as e:
        logger.error(f"Error in LLM-based trade monitoring: {e}")
        return

async def main():
    """Run a simplified test for trade status monitoring."""
    logger.info("Starting trade status monitoring test")
    
    # Create unique user ID for testing
    user_id = str(uuid.uuid4())
    exchange_id = "bitmex"
    
    # Create config
    config = EngineConfig(
        llm={
            "model": "gpt-4.1",
            "system_prompt": "You are an expert trading assistant specializing in cryptocurrency exchange APIs. Your task is to find information about active trades and positions by using the appropriate exchange API tools. When searching for active trades, prioritize tools that could return position details, open orders, or account balance data.",
            "temperature": 0.0,
            "max_retries": 2
        },
        validation={
            "max_leverage": 10,
            "max_position_pct": 0.05
        },
        execution={
            "polling_interval": 5,  # Use shorter interval for testing
            "max_retries": 2
        },
        default_exchange="bitmex",
        use_testnet=True,
        server_path=str(Path(__file__).parent.parent.parent / "core" / "mcp" / "servers" / "ccxt_mcp_server.py"),
        credentials={
            "apiKey": os.environ.get("EXCHANGE_API"),
            "secret": os.environ.get("EXCHANGE_SECRET")
        }
    )
    
    # Create MCP client
    logger.info(f"Using server path: {config.server_path}")
    
    mcp_client = CCXTMCPClient(
        exchange_id=exchange_id,
        user_id=user_id,
        use_local_server=True,
        server_path=config.server_path
    )
    
    # Connect to MCP server
    logger.info("Connecting to MCP server...")
    await mcp_client.connect()
    logger.info("MCP client connected successfully")
    
    # Create CCXT adapter
    logger.info("Creating CCXT adapter...")
    adapter = CCXTMCPAdapter(
        exchange_id=exchange_id,
        user_id=user_id,
        config=config.model_dump()
    )
    adapter.mcp_client = mcp_client
    adapter.connected = True
    
    # Print adapter and client info
    logger.info(f"Adapter exchange: {adapter.exchange_id}")
    logger.info(f"MCP client connected: {mcp_client.is_connected}")
    logger.info(f"MCP client has session: {hasattr(mcp_client, 'session')}")
    
    # Initialize LLM service
    logger.info("Creating LLM service...")
    llm_service = LLMService(config=config, user_id=user_id)
    
    try:
        # First test: Run a series of direct tool calls to gather raw trade status data
        await run_direct_tool_calls(adapter)
        
        # Second test: Use LLM to determine the best tools for monitoring
        await run_llm_trade_monitoring(adapter, llm_service)
        
        logger.info("\n=== TEST SUMMARY ===")
        logger.info("Successfully retrieved raw trade status data from BitMEX testnet")
        logger.info("Raw data from direct tool calls saved to: raw_trade_status_results.json")
        logger.info("Raw data from LLM-guided tool calls saved to: raw_llm_trade_status_results.json")
        logger.info("All trade status monitoring tests completed successfully")
    finally:
        # Clean up
        if mcp_client and mcp_client.is_connected:
            logger.info("Disconnecting MCP client...")
            await mcp_client.disconnect()

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())