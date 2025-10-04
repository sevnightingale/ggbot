"""
Symphony.io Test Trade Script

Quick test of Symphony agentic trading API.
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SYMPHONY_API_KEY = os.getenv("SYMPHONY_API_KEY")
SYMPHONY_BASE_URL = "https://api.symphony.io"


async def open_trade(
    agent_id: str,
    symbol: str,
    action: str,  # "LONG" or "SHORT"
    weight: float,  # 0-100
    leverage: float,  # minimum 1.1
    trigger_price: float = 0,
    stop_loss_price: float = 0,
    take_profit_price: float = 0
):
    """
    Open a batch trade on Symphony.

    Returns batch_id for tracking/closing the trade.
    """
    url = f"{SYMPHONY_BASE_URL}/agent/batch-open"

    headers = {
        "x-api-key": SYMPHONY_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "agentId": agent_id,
        "symbol": symbol,
        "action": action.upper(),
        "weight": weight,
        "leverage": leverage,
        "orderOptions": {
            "triggerPrice": trigger_price,
            "stopLossPrice": stop_loss_price,
            "takeProfitPrice": take_profit_price
        }
    }

    print(f"\n🚀 Opening {action.upper()} position for {symbol}")
    print(f"   Weight: {weight}% | Leverage: {leverage}x")
    print(f"\nRequest payload:")
    print(payload)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"\n✅ Trade submitted successfully!")
                print(f"   Batch ID: {data['batchId']}")
                print(f"   Successful: {data['successful']}")
                print(f"   Failed: {data['failed']}")
                print(f"\nFull response:")
                print(data)
                return data
            else:
                error_text = await response.text()
                print(f"\n❌ Error {response.status}: {error_text}")
                return None


async def close_trade(agent_id: str, batch_id: str):
    """Close a batch trade on Symphony."""
    url = f"{SYMPHONY_BASE_URL}/agent/batch-close"

    headers = {
        "x-api-key": SYMPHONY_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "agentId": agent_id,
        "batchId": batch_id
    }

    print(f"\n🔴 Closing batch: {batch_id}")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"\n✅ Trade closed successfully!")
                print(f"   Successful: {data['successful']}")
                print(f"   Skipped: {data.get('skipped', 0)}")
                print(f"   Failed: {data['failed']}")
                print(f"\nFull response:")
                print(data)
                return data
            else:
                error_text = await response.text()
                print(f"\n❌ Error {response.status}: {error_text}")
                return None


async def get_positions(agent_id: str):
    """Get all positions for an agent."""
    url = f"{SYMPHONY_BASE_URL}/agent/positions"

    headers = {
        "x-api-key": SYMPHONY_API_KEY
    }

    params = {
        "agentId": agent_id
    }

    print(f"\n📊 Fetching positions for agent: {agent_id}")

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"\n✅ Positions retrieved!")
                print(f"   Open Orders: {data['ordersCount']}")
                print(f"   Open Positions: {data['positionsCount']}")
                print(f"\nFull response:")
                print(data)
                return data
            else:
                error_text = await response.text()
                print(f"\n❌ Error {response.status}: {error_text}")
                return None


async def main():
    """Test trade execution."""

    # Configuration
    AGENT_ID = "22b35152-f3a5-4b21-8a0f-04691c155e33"
    SYMBOL = "BTC"
    ACTION = "LONG"
    WEIGHT = 25  # 25% of $25 = $6.25 (meets 5 USDC minimum)
    LEVERAGE = 2

    print("=" * 60)
    print("🎯 Symphony.io Test Trade")
    print("=" * 60)

    # Open trade
    result = await open_trade(
        agent_id=AGENT_ID,
        symbol=SYMBOL,
        action=ACTION,
        weight=WEIGHT,
        leverage=LEVERAGE
    )

    if result and 'batchId' in result:
        batch_id = result['batchId']
        print(f"\n💾 Save this batch ID to close later: {batch_id}")

        # Get positions
        await asyncio.sleep(2)  # Wait for trade to settle
        await get_positions(AGENT_ID)

        # Uncomment to close immediately (for testing):
        # await asyncio.sleep(5)
        # await close_trade(AGENT_ID, batch_id)


if __name__ == "__main__":
    asyncio.run(main())
