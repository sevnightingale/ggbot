#!/usr/bin/env python
"""
Test BitMEX Order Data Structure

This script examines BitMEX order data structure, particularly for reduce-only orders
to understand how TP/SL orders appear in the order data.
"""

import os
import sys
import asyncio
import json
import uuid
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

from core.common.logger import logger
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter
from core.mcp.ccxt import CCXTMCPClient

# Configure logging
import logging
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])

async def test_bitmex_order_structure():
    """Test BitMEX order data structure with live examples."""
    logger.info("Starting BitMEX order structure test")
    
    # Create unique user ID for testing
    user_id = str(uuid.uuid4())
    exchange_id = "bitmex"
    
    # Create config
    config = {
        "server_path": str(Path(__file__).parent.parent.parent / "core" / "mcp" / "servers" / "ccxt_mcp_server.py"),
        "credentials": {
            "apiKey": os.environ.get("EXCHANGE_API"),
            "secret": os.environ.get("EXCHANGE_SECRET")
        }
    }
    
    # Create MCP client
    logger.info(f"Using server path: {config['server_path']}")
    
    mcp_client = CCXTMCPClient(
        exchange_id=exchange_id,
        user_id=user_id,
        use_local_server=True,
        server_path=config["server_path"]
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
        config=config
    )
    adapter.mcp_client = mcp_client
    adapter.connected = True
    
    test_results = {}
    
    try:
        # Test 1: Get current open orders
        logger.info("\n=== TEST 1: FETCH OPEN ORDERS ===")
        try:
            open_orders = await adapter.call_tool("fetch_open_orders", {})
            test_results["open_orders"] = {
                "success": True,
                "data": open_orders,
                "description": "All currently open orders on the account"
            }
            logger.info(f"Found {len(open_orders) if isinstance(open_orders, list) else 0} open orders")
            
            # If we have orders, examine their structure
            if isinstance(open_orders, list) and len(open_orders) > 0:
                logger.info("Example order structure:")
                for i, order in enumerate(open_orders[:2]):  # Show first 2 orders
                    logger.info(f"Order {i+1}: {json.dumps(order, indent=2)}")
                    
        except Exception as e:
            test_results["open_orders"] = {
                "success": False,
                "error": str(e),
                "description": "Failed to fetch open orders"
            }
            logger.error(f"Error fetching open orders: {e}")
        
        # Test 2: Get order history
        logger.info("\n=== TEST 2: FETCH ORDER HISTORY ===")
        try:
            order_history = await adapter.call_tool("fetch_orders", {
                "symbol": "BTC/USD:BTC",
                "limit": 10
            })
            test_results["order_history"] = {
                "success": True,
                "data": order_history,
                "description": "Recent order history for BTC/USD"
            }
            logger.info(f"Found {len(order_history) if isinstance(order_history, list) else 0} historical orders")
            
            # Examine order structure and look for reduce-only orders
            if isinstance(order_history, list) and len(order_history) > 0:
                logger.info("Analyzing order structure...")
                reduce_only_orders = []
                stop_orders = []
                limit_orders = []
                market_orders = []
                
                for order in order_history:
                    if isinstance(order, dict):
                        # Check order type
                        order_type = order.get('type', 'unknown')
                        if order_type == 'stop':
                            stop_orders.append(order)
                        elif order_type == 'limit':
                            limit_orders.append(order)
                        elif order_type == 'market':
                            market_orders.append(order)
                        
                        # Check for reduce-only flag
                        if order.get('reduceOnly') == True:
                            reduce_only_orders.append(order)
                        
                        # Look for TP/SL indicators
                        if order.get('takeProfitPrice') or order.get('stopLossPrice'):
                            logger.info(f"Found order with TP/SL data: {order.get('id')}")
                
                logger.info(f"Order type breakdown:")
                logger.info(f"  - Market orders: {len(market_orders)}")
                logger.info(f"  - Limit orders: {len(limit_orders)}")
                logger.info(f"  - Stop orders: {len(stop_orders)}")
                logger.info(f"  - Reduce-only orders: {len(reduce_only_orders)}")
                
                # Show examples of each type
                if stop_orders:
                    logger.info("Example stop order:")
                    logger.info(json.dumps(stop_orders[0], indent=2))
                if reduce_only_orders:
                    logger.info("Example reduce-only order:")
                    logger.info(json.dumps(reduce_only_orders[0], indent=2))
                    
        except Exception as e:
            test_results["order_history"] = {
                "success": False,
                "error": str(e),
                "description": "Failed to fetch order history"
            }
            logger.error(f"Error fetching order history: {e}")
        
        # Test 3: Create test orders to see their structure
        logger.info("\n=== TEST 3: CREATE TEST ORDERS ===")
        
        # Test 3a: Create a simple limit order
        try:
            logger.info("Creating test limit order...")
            limit_order = await adapter.call_tool("create_limit_order", {
                "symbol": "BTC/USD:BTC",
                "side": "buy",
                "amount": 100,  # Minimum for BTC
                "price": 50000  # Well below market
            })
            test_results["test_limit_order"] = {
                "success": True,
                "data": limit_order,
                "description": "Test limit order created to examine structure"
            }
            logger.info("Limit order created successfully")
            logger.info(f"Limit order structure: {json.dumps(limit_order, indent=2)}")
            
            # Cancel the order
            if isinstance(limit_order, dict) and 'id' in limit_order:
                await adapter.call_tool("cancel_order", {
                    "id": limit_order['id'],
                    "symbol": "BTC/USD:BTC"
                })
                logger.info("Test limit order cancelled")
                
        except Exception as e:
            test_results["test_limit_order"] = {
                "success": False,
                "error": str(e),
                "description": "Failed to create test limit order"
            }
            logger.error(f"Error creating test limit order: {e}")
        
        # Test 3b: Create a stop order (reduce-only)
        try:
            logger.info("Creating test stop order with reduce-only...")
            stop_order = await adapter.call_tool("create_limit_order", {
                "symbol": "BTC/USD:BTC",
                "side": "sell",
                "amount": 100,
                "price": 45000,
                "params": {
                    "stopPx": 45000,
                    "execInst": "Close",
                    "reduceOnly": True
                }
            })
            test_results["test_stop_order"] = {
                "success": True,
                "data": stop_order,
                "description": "Test stop order (reduce-only) to examine structure"
            }
            logger.info("Stop order created successfully")
            logger.info(f"Stop order structure: {json.dumps(stop_order, indent=2)}")
            
            # Cancel the order
            if isinstance(stop_order, dict) and 'id' in stop_order:
                await adapter.call_tool("cancel_order", {
                    "id": stop_order['id'],
                    "symbol": "BTC/USD:BTC"
                })
                logger.info("Test stop order cancelled")
                
        except Exception as e:
            test_results["test_stop_order"] = {
                "success": False,
                "error": str(e),
                "description": "Failed to create test stop order"
            }
            logger.error(f"Error creating test stop order: {e}")
        
        # Test 4: Check positions for related data
        logger.info("\n=== TEST 4: FETCH POSITIONS ===")
        try:
            positions = await adapter.call_tool("fetch_positions", {})
            test_results["positions"] = {
                "success": True,
                "data": positions,
                "description": "Current positions data"
            }
            logger.info(f"Found {len(positions) if isinstance(positions, list) else 0} positions")
            
            if isinstance(positions, list) and len(positions) > 0:
                for pos in positions:
                    if isinstance(pos, dict) and pos.get('contracts', 0) != 0:
                        logger.info(f"Active position: {json.dumps(pos, indent=2)}")
                        
        except Exception as e:
            test_results["positions"] = {
                "success": False,
                "error": str(e),
                "description": "Failed to fetch positions"
            }
            logger.error(f"Error fetching positions: {e}")
        
        # Save comprehensive results
        output_dir = Path(__file__).parent
        output_path = output_dir / "bitmex_order_structure_analysis.json"
        with open(output_path, "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        
        logger.info(f"\nSaved comprehensive order structure analysis to {output_path}")
        
        # Summary
        logger.info("\n=== SUMMARY ===")
        logger.info("BitMEX Order Structure Analysis Complete")
        for test_name, result in test_results.items():
            status = "✓" if result.get("success") else "✗"
            logger.info(f"{status} {test_name}: {result.get('description', 'No description')}")
        
    finally:
        # Clean up
        if mcp_client and mcp_client.is_connected:
            logger.info("Disconnecting MCP client...")
            await mcp_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_bitmex_order_structure())