"""
Test Symphony API connectivity with known working endpoints.
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

SYMPHONY_API_KEY = os.getenv("SYMPHONY_API_KEY")
SYMPHONY_AGENT_ID = os.getenv("SYMPHONY_AGENT_ID")


async def test_agent_positions():
    """Test the /agent/positions endpoint (known to work)."""
    url = "https://api.symphony.io/agent/positions"

    headers = {
        "x-api-key": SYMPHONY_API_KEY
    }

    params = {
        "agentId": SYMPHONY_AGENT_ID
    }

    print(f"\n{'=' * 80}")
    print(f"🔍 Testing Symphony /agent/positions (Known Working)")
    print(f"{'=' * 80}")
    print(f"Agent ID: {SYMPHONY_AGENT_ID}")
    print(f"API Key: {SYMPHONY_API_KEY[:15]}...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as response:
                status = response.status

                if status == 200:
                    data = await response.json()
                    positions = data.get('positions', [])
                    print(f"\n✅ SUCCESS - {len(positions)} open positions")
                    if positions:
                        for i, pos in enumerate(positions[:3]):  # Show first 3
                            print(f"\n  Position {i+1}:")
                            print(f"    Asset: {pos.get('asset')}")
                            print(f"    Is Long: {pos.get('isLong')}")
                            print(f"    Entry Price: ${pos.get('entryPrice', 0):.2f}")
                            print(f"    Position Size: ${pos.get('positionSize', 0):.2f}")
                            print(f"    P&L: ${pos.get('pnlUSD', 0):.2f}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"\n❌ FAILED: Status {status}")
                    print(f"Error: {error_text[:200]}")
                    return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


async def test_agent_batches():
    """Test the /agent/batches endpoint."""
    url = "https://api.symphony.io/agent/batches"

    headers = {
        "x-api-key": SYMPHONY_API_KEY
    }

    params = {
        "agentId": SYMPHONY_AGENT_ID
    }

    print(f"\n{'=' * 80}")
    print(f"🔍 Testing Symphony /agent/batches")
    print(f"{'=' * 80}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as response:
                status = response.status

                if status == 200:
                    data = await response.json()
                    batches = data.get('batches', [])
                    print(f"\n✅ SUCCESS - {len(batches)} batches found")
                    if batches:
                        for i, batch in enumerate(batches[:3]):  # Show first 3
                            print(f"\n  Batch {i+1}:")
                            print(f"    Batch ID: {batch.get('batchId')}")
                            print(f"    Status: {batch.get('status')}")
                            print(f"    Created: {batch.get('createdTimestamp', 'N/A')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"\n❌ FAILED: Status {status}")
                    print(f"Error: {error_text[:200]}")
                    return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


async def main():
    """Run connectivity tests."""

    print("\n🧪 Symphony API Connectivity Tests")
    print("=" * 80)

    if not SYMPHONY_API_KEY:
        print("❌ ERROR: SYMPHONY_API_KEY not found in .env")
        return

    if not SYMPHONY_AGENT_ID:
        print("❌ ERROR: SYMPHONY_AGENT_ID not found in .env")
        return

    # Test 1: Known working endpoint
    positions_ok = await test_agent_positions()

    # Test 2: Batches endpoint
    batches_ok = await test_agent_batches()

    # Summary
    print(f"\n{'=' * 80}")
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"  Positions endpoint: {'✅ Working' if positions_ok else '❌ Failed'}")
    print(f"  Batches endpoint: {'✅ Working' if batches_ok else '❌ Failed'}")

    if positions_ok and batches_ok:
        print("\n✅ Symphony API credentials are valid!")
        print("   Perp trading endpoints work correctly.")
        print("\n🔍 Next: Try spot trading endpoints (may not be deployed yet)")
    else:
        print("\n❌ Some connectivity issues detected")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
