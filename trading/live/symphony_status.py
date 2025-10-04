"""
Get Symphony position status.
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

SYMPHONY_API_KEY = os.getenv("SYMPHONY_API_KEY")
SYMPHONY_BASE_URL = "https://api.symphony.io"
AGENT_ID = "22b35152-f3a5-4b21-8a0f-04691c155e33"


async def get_positions():
    """Get all positions for an agent."""
    url = f"{SYMPHONY_BASE_URL}/agent/positions"
    headers = {"x-api-key": SYMPHONY_API_KEY}
    params = {"agentId": AGENT_ID}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            data = await response.json()

            print("📊 Position Status")
            print("=" * 60)
            print(f"Open Positions: {data['positionsCount']}")
            print(f"Open Orders: {data['ordersCount']}")

            if data['positions']:
                for i, pos in enumerate(data['positions'], 1):
                    print(f"\n🔹 Position {i}")
                    print(f"   Asset: {pos['asset']}")
                    print(f"   Direction: {'LONG' if pos['isLong'] else 'SHORT'}")
                    print(f"   Leverage: {pos['leverage']}x")
                    print(f"   Entry Price: ${pos['entryPrice']:,.2f}")
                    print(f"   Current Price: ${pos['currentPrice']:,.2f}")
                    print(f"   Position Size: ${pos['positionSize']:,.2f}")
                    print(f"   Collateral: ${pos['collateralAmount']:,.2f}")
                    print(f"   PnL: ${pos['pnlUSD']:,.4f} ({pos['pnlPercentage']:.4f}%)")
                    print(f"   Liquidation Price: ${pos['liquidationPrice']:,.2f}")
                    print(f"   Status: {pos['status']}")
                    print(f"   Batch ID: {pos['batchId']}")
            else:
                print("\n✅ No open positions")

            return data


if __name__ == "__main__":
    asyncio.run(get_positions())
