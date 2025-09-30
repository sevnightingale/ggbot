#!/usr/bin/env python
"""
Test CCXT MCP Tools with Edge Cases

This script tests various edge cases for CCXT MCP tools to identify
exchange-specific errors and limitations that should be documented
in the exchange guide.
"""

import os
import sys
import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.common.logger import logger
from core.mcp.ccxt import CCXTMCPClient
from trading.exchanges.ccxt_mcp import CCXTMCPAdapter
from trading.engine.model.config import EngineConfig

# Configure logging
import logging
logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])

# Test scenarios with edge case values
TEST_SCENARIOS = {
    "create_market_buy_order": [
        # Test minimum order sizes
        {"symbol": "BTC/USD", "amount": 1, "description": "Below BTC minimum (should fail)"},
        {"symbol": "BTC/USD", "amount": 99, "description": "Just below BTC minimum (should fail)"},
        {"symbol": "BTC/USD", "amount": 100, "description": "Exactly BTC minimum (should pass)"},
        {"symbol": "BTC/USD", "amount": 101, "description": "Above BTC minimum (should pass)"},
        {"symbol": "ETH/USD", "amount": 0.5, "description": "Below standard minimum (should fail)"},
        {"symbol": "ETH/USD", "amount": 1, "description": "Standard minimum (should pass)"},
        {"symbol": "ETH/USD", "amount": 10, "description": "Normal amount (should pass)"},
        # Test large orders
        {"symbol": "BTC/USD", "amount": 1000000, "description": "Very large order (check if allowed)"},
        # Test decimal amounts
        {"symbol": "BTC/USD", "amount": 100.5, "description": "Decimal amount (check if rounded)"},
    ],
    
    "create_limit_order": [
        # Test with various prices
        {"symbol": "BTC/USD", "side": "buy", "amount": 100, "price": 1, "description": "Very low price"},
        {"symbol": "BTC/USD", "side": "buy", "amount": 100, "price": 50000, "description": "Normal price"},
        {"symbol": "BTC/USD", "side": "buy", "amount": 100, "price": 1000000, "description": "Very high price"},
        # Test price precision
        {"symbol": "BTC/USD", "side": "buy", "amount": 100, "price": 50000.123456789, "description": "Many decimals"},
    ],
    
    "create_stop_order": [
        # Test stop orders with different parameters
        {"symbol": "BTC/USD", "side": "sell", "amount": 100, "description": "Missing stopPrice (should fail)"},
        {"symbol": "BTC/USD", "side": "sell", "amount": 100, "stopPrice": 45000, "description": "With stopPrice"},
        {"symbol": "BTC/USD", "side": "sell", "amount": 100, "stopPrice": 45000, "price": 44000, 
         "description": "Stop-limit attempt (BitMEX doesn't support)"},
    ],
    
    "set_leverage": [
        # Test leverage limits
        {"symbol": "BTC/USD", "leverage": 0, "description": "Zero leverage (should fail)"},
        {"symbol": "BTC/USD", "leverage": 1, "description": "Minimum leverage"},
        {"symbol": "BTC/USD", "leverage": 50, "description": "Medium leverage"},
        {"symbol": "BTC/USD", "leverage": 100, "description": "Maximum leverage"},
        {"symbol": "BTC/USD", "leverage": 101, "description": "Above maximum (should fail)"},
        {"symbol": "BTC/USD", "leverage": 2.5, "description": "Decimal leverage (check if allowed)"},
    ],
    
    "create_reduce_only_order": [
        # Test reduce-only orders
        {"symbol": "BTC/USD", "side": "sell", "amount": 100, "order_type": "market", 
         "description": "Market reduce-only"},
        {"symbol": "BTC/USD", "side": "sell", "amount": 100, "order_type": "limit", "price": 110000,
         "description": "Limit reduce-only"},
    ]
}


async def test_tool_with_params(adapter: CCXTMCPAdapter, tool_name: str, params: Dict[str, Any], 
                               description: str) -> Dict[str, Any]:
    """Test a single tool call with given parameters."""
    result = {
        "tool": tool_name,
        "params": params,
        "description": description,
        "success": False,
        "response": None,
        "error": None,
        "error_type": None
    }
    
    try:
        logger.info(f"\nTesting: {tool_name}")
        logger.info(f"Description: {description}")
        logger.info(f"Params: {json.dumps(params, indent=2)}")
        
        response = await adapter.call_tool(tool_name, params)
        result["success"] = True
        result["response"] = response
        logger.info(f"✅ Success: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        result["error"] = str(e)
        result["error_type"] = type(e).__name__
        logger.error(f"❌ Error: {type(e).__name__}: {str(e)}")
    
    return result


async def close_all_positions(adapter: CCXTMCPAdapter):
    """Close any open positions before testing."""
    try:
        positions = await adapter.fetch_positions()
        for position in positions:
            if isinstance(position, dict) and position.get("contracts", 0) != 0:
                symbol = position["symbol"]
                contracts = float(position["contracts"])
                side = "sell" if contracts > 0 else "buy"
                
                logger.info(f"Closing position: {symbol} with {abs(contracts)} contracts")
                await adapter.create_order(
                    symbol=symbol,
                    order_type="market",
                    side=side,
                    amount=abs(contracts),
                    params={"reduceOnly": True}
                )
    except Exception as e:
        logger.error(f"Error closing positions: {e}")


async def cancel_all_orders(adapter: CCXTMCPAdapter):
    """Cancel all open orders."""
    try:
        orders = await adapter.fetch_open_orders()
        for order in orders:
            if isinstance(order, dict) and order.get("id"):
                logger.info(f"Cancelling order: {order['id']}")
                await adapter.cancel_order(order["id"], order.get("symbol"))
    except Exception as e:
        logger.error(f"Error cancelling orders: {e}")


async def main():
    """Run edge case tests for CCXT MCP tools."""
    logger.info("🚀 Starting CCXT MCP Edge Case Testing")
    
    # Configuration
    user_id = str(uuid.uuid4())
    exchange_id = "bitmex"
    server_path = str(Path(__file__).parent.parent.parent / "core" / "mcp" / "servers" / "ccxt_mcp_server.py")
    
    config = EngineConfig(
        llm={
            "model": "gpt-4o",
            "system_prompt": "Test system"
        },
        validation={
            "max_leverage": 100,
            "max_position_pct": 1.0
        },
        execution={
            "polling_interval": 5,
            "max_retries": 2
        },
        default_exchange=exchange_id,
        use_testnet=True,
        server_path=server_path,
        credentials={
            "apiKey": os.environ.get("EXCHANGE_API"),
            "secret": os.environ.get("EXCHANGE_SECRET")
        }
    )
    
    # Create MCP client
    mcp_client = CCXTMCPClient(
        exchange_id=exchange_id,
        user_id=user_id,
        use_local_server=True,
        server_path=server_path
    )
    
    # Connect to MCP server
    logger.info("Connecting to MCP server...")
    await mcp_client.connect()
    
    # Create adapter
    adapter = CCXTMCPAdapter(exchange_id, user_id, config.model_dump())
    adapter.mcp_client = mcp_client
    adapter.connected = True
    
    # Clean up before testing
    logger.info("Cleaning up existing positions and orders...")
    await close_all_positions(adapter)
    await cancel_all_orders(adapter)
    await asyncio.sleep(2)
    
    # Run tests
    all_results = []
    
    for tool_name, test_cases in TEST_SCENARIOS.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing tool: {tool_name}")
        logger.info(f"{'='*60}")
        
        for test_case in test_cases:
            # Make a copy to avoid modifying the original
            params = test_case.copy()
            description = params.pop("description")
            
            result = await test_tool_with_params(adapter, tool_name, params, description)
            all_results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(0.5)
            
            # Clean up orders after each test (but not positions to avoid excessive trading)
            if tool_name in ["create_limit_order", "create_stop_order"]:
                await cancel_all_orders(adapter)
    
    # Final cleanup
    logger.info("\nFinal cleanup...")
    await close_all_positions(adapter)
    await cancel_all_orders(adapter)
    
    # Save results
    output_file = Path(__file__).parent / "edge_case_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"\nResults saved to: {output_file}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY OF EDGE CASE FINDINGS")
    logger.info("="*60)
    
    # Group errors by type
    error_types = {}
    for result in all_results:
        if not result["success"]:
            error_type = result["error_type"] or "Unknown"
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append({
                "tool": result["tool"],
                "description": result["description"],
                "error": result["error"]
            })
    
    for error_type, errors in error_types.items():
        logger.info(f"\n{error_type} ({len(errors)} cases):")
        for error in errors[:3]:  # Show first 3 examples
            logger.info(f"  - {error['tool']}: {error['description']}")
            logger.info(f"    Error: {error['error'][:100]}...")
    
    # Disconnect
    await mcp_client.disconnect()
    logger.info("\n✅ Edge case testing completed!")


if __name__ == "__main__":
    asyncio.run(main())