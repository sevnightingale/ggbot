"""
Get Symphony account balance and performance.
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

SYMPHONY_API_KEY = os.getenv("SYMPHONY_API_KEY")
SYMPHONY_BASE_URL = "https://api.symphony.io"
AGENT_ID = "22b35152-f3a5-4b21-8a0f-04691c155e33"

# Smart account address from previous trade
USER_ADDRESS = "0xc256119769fefcc9bd5a1897607c6f66a358f3da"


async def get_batches():
    """Get all batches for the agent."""
    url = f"{SYMPHONY_BASE_URL}/agent/batches"

    headers = {
        "x-api-key": SYMPHONY_API_KEY
    }

    params = {
        "agentId": AGENT_ID
    }

    print(f"📜 Fetching trade batches for agent")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()

                print(f"\nTotal Batches: {len(data['batches'])}")

                for batch in data['batches']:
                    print(f"\n🔹 Batch ID: {batch['batchId']}")
                    print(f"   Status: {batch['status']}")
                    print(f"   Created: {batch['createTimestamp']}")

                return data
            else:
                error_text = await response.text()
                print(f"\n❌ Error {response.status}: {error_text}")
                return None


async def get_account_performance(user_address: str):
    """Get account summary and performance."""
    url = f"{SYMPHONY_BASE_URL}/v1/agent/all-positions"

    params = {
        "userAddress": user_address
    }

    print(f"📊 Fetching account performance for: {user_address}")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()

                if data['success'] and 'data' in data:
                    account_data = data['data']
                    summary = account_data['accountSummary']

                    print("\n💰 Account Summary")
                    print("-" * 60)
                    print(f"Total Equity: ${summary['totalEquity']:.2f}")
                    print(f"Available Balance: ${summary['availableBalance']:.2f}")
                    print(f"Margin Used: ${summary['marginUsed']:.2f}")
                    print(f"Initial Capital: ${summary['initialCapital']:.2f}")

                    print("\n📈 Performance")
                    print("-" * 60)
                    print(f"Total PnL: ${summary['totalPnl']:.4f}")
                    print(f"Realized PnL: ${summary['totalRealizedPnl']:.4f}")
                    print(f"Unrealized PnL: ${summary['totalUnrealizedPnl']:.4f}")
                    print(f"Total Fees Paid: ${summary['totalFeesPaid']:.4f}")
                    print(f"ROI: ${summary['performance']['roi']:.4f} ({summary['performance']['roiPercent']:.2f}%)")

                    print("\n📊 Trading Stats")
                    print("-" * 60)
                    print(f"Total Trades: {summary['totalTrades']}")
                    print(f"Total Volume: ${summary['totalVolume']:.2f}")
                    print(f"Average Trade Size: ${summary['performance']['averageTradeSize']:.2f}")
                    print(f"Open Positions: {summary['openPositionsCount']}")
                    print(f"Closed Positions: {summary['closedPositionsCount']}")
                    print(f"Liquidated Positions: {summary['liquidatedPositionsCount']}")
                    print(f"Account Status: {summary['accountStatus']}")

                    if account_data.get('openPositions'):
                        print("\n🔹 Open Positions")
                        print("-" * 60)
                        for pos in account_data['openPositions']:
                            print(f"\n   {pos['asset']} {'LONG' if pos['isLong'] else 'SHORT'} @ {pos['leverage']}x")
                            print(f"   Entry: ${pos['entryPrice']:,.2f} | Current: ${pos['currentPrice']:,.2f}")
                            print(f"   Size: ${pos['positionSize']:,.2f} | Collateral: ${pos['collateralAmount']:.2f}")
                            print(f"   PnL: ${pos['pnlUSDValue']:,.4f} ({pos['pnlPercentage']:.4f}%)")

                    print("\n" + "=" * 60)
                    return data
                else:
                    print(f"\n❌ Unexpected response format: {data}")
                    return None
            else:
                error_text = await response.text()
                print(f"\n❌ Error {response.status}: {error_text}")
                return None


if __name__ == "__main__":
    asyncio.run(get_batches())
