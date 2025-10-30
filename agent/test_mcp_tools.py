#!/usr/bin/env python3
"""
Test MCP tools directly without the agent SDK.
This helps verify tool implementations work correctly.
"""

import asyncio
import json
from agent.service_client import AgentServiceClient

async def test_query_market_data():
    """Test query_market_data tool with proper format"""
    print("\n=== Testing query_market_data ===")

    # This simulates what the agent SDK should send
    args = {
        "symbol": "BTCUSDT",
        "categories": {
            "technical_analysis": ["RSI", "MACD"]
        },
        "timeframe": "1h"
    }

    print(f"Args: {json.dumps(args, indent=2)}")

    try:
        # Import the tool function directly
        from agent.mcp_server import query_market_data

        # Call it
        result = await query_market_data(args)
        print(f"✅ Success: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_get_account_status():
    """Test get_account_status tool"""
    print("\n=== Testing get_account_status ===")

    args = {}

    try:
        from agent.mcp_server import get_account_status
        result = await get_account_status(args)
        print(f"✅ Success: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_service_client():
    """Test the service client directly"""
    print("\n=== Testing AgentServiceClient ===")

    client = AgentServiceClient(
        base_url="http://localhost:5858",
        config_id="d13d5536-2498-4f27-b2bc-e4f98958e1d8"
    )

    try:
        result = await client.query_market_data(
            config_id="d13d5536-2498-4f27-b2bc-e4f98958e1d8",
            symbol="BTCUSDT",
            indicators=["RSI", "MACD"],
            data_sources=None,
            timeframe="1h"
        )
        print(f"✅ Success: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP Tool Testing Suite")
    print("=" * 60)
    print("\nMake sure ggbot.py is running on port 5858!")
    print("Run: python ggbot.py")
    print("=" * 60)

    results = []

    # Test 1: Service client (requires ggbot.py running)
    results.append(("Service Client", await test_service_client()))

    # Test 2: Tool wrapper (requires agent context)
    print("\n⚠️  Note: Tool wrappers need agent_context initialized")
    print("Skipping direct tool tests for now - they need the agent runtime")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

if __name__ == "__main__":
    asyncio.run(main())
