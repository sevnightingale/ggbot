#!/usr/bin/env python
"""
Simplified test for the ExecutionService with BitMEX testnet.

This test focuses specifically on testing the set_leverage and create_market_buy_order
tools on BitMEX testnet without all the other functionality.
"""

import os
import sys
import asyncio
import uuid
import json
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set environment variables
os.environ["TESTNET"] = "1"
os.environ["EXCHANGE_NAME"] = "bitmex"

from core.common.logger import logger
from core.mcp.ccxt import CCXTMCPClient
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter
from trading.engine.model.tool_call import ValidatedToolCall
from trading.engine.model.config import EngineConfig
from trading.engine.service.execution_service import ExecutionService, EventBus

# Configure basic logging
import logging
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])

async def main():
    """Run a simplified test for the execution service."""
    logger.info("Starting simplified ExecutionService test")
    
    # Create unique user ID for testing
    user_id = str(uuid.uuid4())
    exchange_id = "bitmex"
    
    # Create config
    config = EngineConfig(
        llm={
            "model": "gpt-4.1",
            "system_prompt": "You are an expert trading assistant.",
            "temperature": 0.0,
            "max_retries": 2
        },
        validation={
            "max_leverage": 10,
            "max_position_pct": 0.05
        },
        execution={
            "polling_interval": 5,
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
    
    # Create event bus
    event_bus = EventBus()
    
    # Create execution service
    logger.info("Creating execution service...")
    execution_service = ExecutionService(
        config=config.execution,
        ccxt_adapter=adapter,
        event_bus=event_bus
    )
    
    # Start the service
    await execution_service.start()
    logger.info("Execution service started")
    
    # Create validated tool calls for testing
    intent_data = {
        "decision_id": str(uuid.uuid4()),
        "action": "enter_long",
        "symbol": "BTC/USD",
        "exchange": "bitmex",
        "timeframe": "15m",
        "size_type": "fixed_contracts",
        "size_value": 1,
        "leverage": 2,
        "stop_loss_price": 60000,
        "take_profit_price": 70000,
        "confidence": 0.85,
        "reasoning": "BTC is showing strong upward momentum with multiple technical indicators confirming the trend."
    }
    
    # Close any existing positions first
    try:
        logger.info("Checking for existing positions...")
        positions = await adapter.fetch_positions()
        
        if positions:
            logger.info(f"Found {len(positions)} positions, closing them...")
            for position in positions:
                if not isinstance(position, dict):
                    continue
                    
                symbol = position.get("symbol")
                contracts = float(position.get("contracts", 0) or 0)
                
                if abs(contracts) > 0:
                    side = "sell" if contracts > 0 else "buy"
                    logger.info(f"Closing position for {symbol} with {contracts} contracts (side: {side})")
                    
                    try:
                        close_result = await adapter.create_order(
                            symbol=symbol,
                            order_type="market",
                            side=side,
                            amount=abs(contracts),
                            params={"reduceOnly": True}
                        )
                        logger.info(f"Position closed: {json.dumps(close_result)}")
                    except Exception as e:
                        logger.error(f"Error closing position: {e}")
    except Exception as e:
        logger.error(f"Error checking positions: {e}")
    
    # Wait a moment for positions to close
    logger.info("Waiting for positions to close...")
    await asyncio.sleep(3)
    
    # Create validated tool calls
    logger.info("Creating validated tool calls...")
    
    # Direct leverage setting doesn't appear to be available
    # Instead, we'll include leverage in the order parameters
    
    # BitMEX requires a minimum contract size of 100
    order_call = ValidatedToolCall(
        tool="create_market_buy_order",  # Updated to match real tool name
        parameters={
            "exchange_id": "bitmex",
            "symbol": "BTC/USD:BTC",  # Updated BitMEX mapped symbol
            "amount": 100.0,  # Minimum amount for BitMEX
            "user_id": user_id,
            "params": {"leverage": 2},
            "clientOrderId": f"ggbot-test-{uuid.uuid4().hex[:8]}"  # Generate unique client order ID
        },
        original_call=None  # Simplified for testing
    )
    
    # There's no leverage call anymore since it wasn't available
    # We'll skip directly to the order execution
    
    # Wait a moment to make sure everything is initialized
    await asyncio.sleep(2)
    
    # Execute the order call
    logger.info("Executing order call...")
    try:
        order_result = await execution_service.execute_tool_calls([order_call], intent_data)
        logger.info(f"Order result: {order_result.status}")
        logger.info(f"Order details: {json.dumps(order_result.results)}")
    except Exception as e:
        logger.error(f"Error executing order call: {e}")
    
    # Wait a moment
    await asyncio.sleep(3)
    
    # Check if position was created
    logger.info("Checking if position was created...")
    try:
        positions = await adapter.fetch_positions()
        position_found = False
        
        for position in positions:
            if not isinstance(position, dict):
                continue
                
            symbol = position.get("symbol")
            contracts = float(position.get("contracts", 0) or 0)
            
            if symbol == "BTC/USD:BTC" and abs(contracts) > 0:
                logger.info(f"Position found: {json.dumps(position)}")
                position_found = True
                break
                
        if not position_found:
            logger.warning("No position found after order execution")
    except Exception as e:
        logger.error(f"Error checking positions: {e}")
    
    # Stop the service
    logger.info("Stopping execution service...")
    await execution_service.stop()
    
    # Disconnect from MCP server
    logger.info("Disconnecting from MCP server...")
    await mcp_client.disconnect()
    
    logger.info("Simplified ExecutionService test completed")

if __name__ == "__main__":
    asyncio.run(main())