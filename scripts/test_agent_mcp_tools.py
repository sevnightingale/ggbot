#!/usr/bin/env python3
"""
Test all agent MCP tools via the service client.

This script simulates what the agent does when calling tools,
testing the full HTTP flow: service_client.py -> api/agent.py -> services

Usage:
    export TEST_CONFIG_ID=your-config-id
    export TEST_USER_ID=your-user-id
    python scripts/test_agent_mcp_tools.py
"""

import asyncio
import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, '/home/sev/ggbot')

from agent.service_client import GGBotAPIClient
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")

# Load environment
load_dotenv()


async def test_query_market_data(client: GGBotAPIClient, config_id: str):
    """Test Tool 1: query_market_data"""
    logger.info("🔧 Testing query_market_data...")

    try:
        result = await client.query_market_data(
            config_id=config_id,
            symbol="BTC",
            indicators=["RSI", "MACD"],
            data_sources={"macro_economics": ["vix"]},
            timeframe="1h"
        )
        logger.success(f"✅ query_market_data: {result.get('status')}")
        return True
    except Exception as e:
        logger.error(f"❌ query_market_data failed: {e}")
        return False


async def test_get_current_price(client: GGBotAPIClient):
    """Test Tool 1b: get_current_price"""
    logger.info("🔧 Testing get_current_price...")

    try:
        result = await client.get_current_price(symbol="BTC")
        logger.success(f"✅ get_current_price: ${result.get('current_price', 0):,.2f}")
        return True
    except Exception as e:
        logger.error(f"❌ get_current_price failed: {e}")
        return False


async def test_execute_trade(client: GGBotAPIClient, config_id: str) -> str:
    """Test Tool 2: execute_trade (with Aster overrides)"""
    logger.info("🔧 Testing execute_trade (with position size & leverage overrides)...")

    try:
        # Get current price first
        price_result = await client.get_current_price(symbol="BTC")
        current_price = price_result.get('current_price', 110000)

        # Execute trade with overrides
        logger.info(f"Calling execute_trade with symbol='BTC', size_usd=100, leverage=5")
        result = await client.execute_trade(
            config_id=config_id,
            symbol="BTC",
            side="long",
            confidence=0.8,
            stop_loss_price=current_price * 0.98,  # 2% SL
            take_profit_price=current_price * 1.05,  # 5% TP
            size_usd=100.0,  # $100 position (NOTIONAL)
            leverage=5  # 5x leverage = $20 margin required
        )
        logger.info(f"execute_trade returned: {result}")

        trade_data = result.get('trade', {})
        # Handle both paper (trade_id) and live (batch_id) responses
        trade_id = trade_data.get('trade_id') or trade_data.get('batch_id')

        # Debug: Show full response if no ID
        if not trade_id:
            logger.warning(f"⚠️ No trade/batch ID in response: {trade_data}")

        logger.success(f"✅ execute_trade: {result.get('status')} (id: {trade_id})")
        return trade_id
    except Exception as e:
        logger.error(f"❌ execute_trade failed: {e}")
        return None


async def test_get_positions(client: GGBotAPIClient, config_id: str):
    """Test Tool 3: get_positions"""
    logger.info("🔧 Testing get_positions...")

    try:
        result = await client.get_positions(config_id=config_id)
        positions = result.get('positions', [])
        logger.success(f"✅ get_positions: {len(positions)} open positions")
        return True
    except Exception as e:
        logger.error(f"❌ get_positions failed: {e}")
        return False


async def test_get_account_status(client: GGBotAPIClient, config_id: str):
    """Test Tool 4: get_account_status"""
    logger.info("🔧 Testing get_account_status...")

    try:
        result = await client.get_account_status(config_id=config_id)
        account = result.get('account', {})
        balance = account.get('balance', 0)
        logger.success(f"✅ get_account_status: Balance ${balance:,.2f}")
        return True
    except Exception as e:
        logger.error(f"❌ get_account_status failed: {e}")
        return False


async def test_close_position(client: GGBotAPIClient, config_id: str, trade_id: str):
    """Test Tool 5: close_position"""
    logger.info("🔧 Testing close_position...")

    if not trade_id:
        logger.warning("⚠️ Skipping close_position (no trade_id)")
        return False

    try:
        result = await client.close_position(
            config_id=config_id,
            trade_id=trade_id
        )
        logger.success(f"✅ close_position: {result.get('status')}")
        return True
    except Exception as e:
        logger.error(f"❌ close_position failed: {e}")
        return False


async def test_update_strategy(client: GGBotAPIClient, config_id: str):
    """Test Tool 6: update_strategy"""
    logger.info("🔧 Testing update_strategy...")

    try:
        result = await client.update_strategy(
            config_id=config_id,
            strategy_content="Test strategy update from MCP tool test",
            updated_by="agent"
        )
        logger.success(f"✅ update_strategy: {result.get('status')}")
        return True
    except Exception as e:
        # Expected to fail if autonomously_editable=false
        if "403" in str(e) or "cannot modify strategy" in str(e).lower():
            logger.info("✅ update_strategy: Correctly blocked (autonomously_editable=false)")
            return True
        else:
            logger.error(f"❌ update_strategy failed: {e}")
            return False


async def test_record_trade_observation(client: GGBotAPIClient, config_id: str, trade_id: str):
    """Test Tool 8: record_trade_observation"""
    logger.info("🔧 Testing record_trade_observation...")

    if not trade_id:
        logger.warning("⚠️ Skipping record_trade_observation (no trade_id)")
        return False

    try:
        result = await client.record_trade_observation(
            config_id=config_id,
            trade_id=trade_id,
            observation_type="win_analysis",
            what_went_well="Test observation - entry timing was good",
            what_went_wrong="Test observation - exit could be improved",
            predictive_data_points={"RSI": "oversold signal", "VIX": "low volatility"},
            decision_review="Test review of decision quality",
            importance=7
        )
        logger.success(f"✅ record_trade_observation: {result.get('status')}")
        return True
    except Exception as e:
        logger.error(f"❌ record_trade_observation failed: {e}")
        return False


async def test_query_trade_observations(client: GGBotAPIClient, config_id: str):
    """Test Tool 9: query_trade_observations"""
    logger.info("🔧 Testing query_trade_observations...")

    try:
        result = await client.query_trade_observations(
            config_id=config_id,
            symbol=None,
            observation_type=None,
            min_importance=5,
            limit=10
        )
        observations = result.get('observations', [])
        logger.success(f"✅ query_trade_observations: {len(observations)} observations found")
        return True
    except Exception as e:
        logger.error(f"❌ query_trade_observations failed: {e}")
        return False


async def main():
    """Run all MCP tool tests"""

    # Configuration
    config_id = os.getenv('TEST_CONFIG_ID')
    user_id = os.getenv('TEST_USER_ID')

    if not config_id or not user_id:
        logger.error("❌ Missing TEST_CONFIG_ID or TEST_USER_ID environment variables")
        logger.info("")
        logger.info("Set these in .env or pass as environment variables:")
        logger.info("  export TEST_CONFIG_ID=your-config-id")
        logger.info("  export TEST_USER_ID=your-user-id")
        logger.info("")
        logger.info("Example:")
        logger.info("  TEST_CONFIG_ID=bb2560fd-b053-464f-8a58-8e254e4d36fa \\")
        logger.info("  TEST_USER_ID=00000000-0000-0000-0000-000000000000 \\")
        logger.info("  python scripts/test_agent_mcp_tools.py")
        return

    logger.info("=" * 80)
    logger.info("🚀 Starting MCP Tool Tests")
    logger.info("=" * 80)
    logger.info(f"Config ID: {config_id}")
    logger.info(f"User ID:   {user_id}")
    logger.info("")

    # Create service client (reads API_BASE_URL and SUPABASE_SERVICE_KEY from env)
    client = GGBotAPIClient(user_id=user_id)

    # Track results
    results = {}
    trade_id = None

    # Test each tool in sequence
    logger.info("=" * 80)
    logger.info("TESTING ALL 11 MCP TOOLS")
    logger.info("=" * 80)
    logger.info("")

    # 1. Query market data
    results['query_market_data'] = await test_query_market_data(client, config_id)
    await asyncio.sleep(1)

    # 1b. Get current price
    results['get_current_price'] = await test_get_current_price(client)
    await asyncio.sleep(1)

    # 2. Execute trade (returns trade_id)
    trade_id = await test_execute_trade(client, config_id)
    results['execute_trade'] = trade_id is not None
    await asyncio.sleep(1)

    # 3. Get positions
    results['get_positions'] = await test_get_positions(client, config_id)
    await asyncio.sleep(1)

    # 4. Get account status
    results['get_account_status'] = await test_get_account_status(client, config_id)
    await asyncio.sleep(1)

    # Wait a bit before closing (let position monitoring update)
    if trade_id:
        logger.info("⏳ Waiting 5s for position monitoring to update...")
        await asyncio.sleep(5)

    # 5. Close position
    results['close_position'] = await test_close_position(client, config_id, trade_id)
    await asyncio.sleep(1)

    # 6. Update strategy
    results['update_strategy'] = await test_update_strategy(client, config_id)
    await asyncio.sleep(1)

    # 8. Record trade observation (needs closed trade)
    results['record_trade_observation'] = await test_record_trade_observation(client, config_id, trade_id)
    await asyncio.sleep(1)

    # 9. Query trade observations
    results['query_trade_observations'] = await test_query_trade_observations(client, config_id)

    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for tool, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status:12} - {tool}")

    logger.info("")
    logger.info(f"Results: {passed}/{total} tools passed")

    if passed == total:
        logger.success("🎉 ALL TESTS PASSED!")
    else:
        logger.warning(f"⚠️ {total - passed} tests failed")

    logger.info("")
    logger.info("=" * 80)

    # Cleanup
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
