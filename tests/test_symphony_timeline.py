#!/usr/bin/env python3
"""
Test Symphony timeline endpoints to verify data is fetched correctly.
"""

import asyncio
import sys
import httpx

# Test Symphony bot from context
SYMPHONY_CONFIG_ID = "256da34d-8e05-4b57-89cf-875e075dd2c9"  # test2
BASE_URL = "http://localhost:8000"


async def test_symphony_timeline():
    """Test all 3 timeline endpoints for Symphony bot."""

    print("="*80)
    print("TESTING SYMPHONY TIMELINE ENDPOINTS")
    print("="*80)
    print(f"\nTesting with Symphony bot: {SYMPHONY_CONFIG_ID}\n")

    async with httpx.AsyncClient() as client:
        # Test 1: Activities endpoint
        print("1. Testing /api/v2/activities/{config_id}")
        print("-" * 80)
        try:
            response = await client.get(
                f"{BASE_URL}/api/v2/activities/{SYMPHONY_CONFIG_ID}",
                params={"limit": 10}
            )

            if response.status_code != 200:
                print(f"❌ Activities endpoint failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                return False

            activities_result = response.json()

            print(f"✅ Activities endpoint successful")
            print(f"   Status: {activities_result.get('status')}")
            print(f"   Activities count: {activities_result.get('count', 0)}")

            if activities_result.get('activities'):
                print(f"   Sample activity types:")
                for activity in activities_result['activities'][:3]:
                    print(f"     - {activity['type']} at {activity['timestamp']}")

        except Exception as e:
            print(f"❌ Activities endpoint failed: {e}")
            return False

        # Test 2: Balance series endpoint
        print("\n2. Testing /api/v2/activities/{config_id}/balance-series")
        print("-" * 80)
        try:
            response = await client.get(
                f"{BASE_URL}/api/v2/activities/{SYMPHONY_CONFIG_ID}/balance-series",
                params={"mode": "pnl"}
            )

            if response.status_code != 200:
                print(f"❌ Balance series endpoint failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                return False

            balance_result = response.json()

            print(f"✅ Balance series endpoint successful")
            print(f"   Status: {balance_result.get('status')}")
            print(f"   Balance points: {len(balance_result.get('balance_series', []))}")
            print(f"   Current balance: ${balance_result.get('current_balance', 0):.2f}")
            print(f"   Initial balance: ${balance_result.get('initial_balance', 0):.2f}")
            print(f"   Mode: {balance_result.get('mode', 'N/A')}")

            if balance_result.get('balance_series'):
                series = balance_result['balance_series']
                print(f"   First point: {series[0]['timestamp']} = ${series[0]['balance']:.2f}")
                if len(series) > 1:
                    print(f"   Last point:  {series[-1]['timestamp']} = ${series[-1]['balance']:.2f}")

        except Exception as e:
            print(f"❌ Balance series endpoint failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test 3: Metadata endpoint
        print("\n3. Testing /api/v2/activities/{config_id}/metadata")
        print("-" * 80)
        try:
            response = await client.get(
                f"{BASE_URL}/api/v2/activities/{SYMPHONY_CONFIG_ID}/metadata"
            )

            if response.status_code != 200:
                print(f"❌ Metadata endpoint failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                return False

            metadata_result = response.json()

            print(f"✅ Metadata endpoint successful")
            print(f"   Status: {metadata_result.get('status')}")

            metadata = metadata_result.get('metadata', {})
            print(f"   Bot name: {metadata.get('botName', 'N/A')}")
            print(f"   Starting balance: ${metadata.get('startingBalance', 0):.2f}")
            print(f"   Current balance: ${metadata.get('currentBalance', 0):.2f}")
            print(f"   Total trades: {metadata.get('totalTrades', 0)}")
            print(f"   Win rate: {metadata.get('winRate', 0):.1f}%")
            print(f"   Performance: ${metadata.get('performance', 0):.2f}")

        except Exception as e:
            print(f"❌ Metadata endpoint failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("✅ All Symphony timeline endpoints working correctly!")
    print("\nSymphony bots now show:")
    print("  - Activity timeline (from activities table)")
    print("  - P&L chart line (from Symphony API trade history)")
    print("  - Account metrics (from Symphony API)")
    print("\nReady for production use.")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_symphony_timeline())
    sys.exit(0 if success else 1)
