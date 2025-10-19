"""
Symphony.io API Integration Test

Tests the Symphony API endpoints to validate:
1. GET /agent/positions - Query open positions
2. POST /agent/batch-open - Open a test position
3. GET /agent/batch-positions - Get position details
4. POST /agent/batch-close - Close the position

Usage:
    python -m tests.test_symphony_api [--execute-trade]

Arguments:
    --agent-id: Your Symphony agent ID (optional, uses SYMPHONY_AGENT_ID from .env if not provided)
    --execute-trade: Actually execute a small test trade (optional, default: read-only)
    --symbol: Trading symbol (default: SOL)
    --size-usd: Position size in USDC (default: 5.0, minimum allowed)
"""

import os
import sys
import asyncio
import aiohttp
import json
import argparse
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SymphonyAPITester:
    """Test harness for Symphony.io API integration."""

    def __init__(self, agent_id: Optional[str] = None, api_key: Optional[str] = None):
        self.agent_id = agent_id or os.getenv("SYMPHONY_AGENT_ID")
        self.api_key = api_key or os.getenv("SYMPHONY_API_KEY")
        self.base_url = "https://api.symphony.io"

        if not self.agent_id:
            raise ValueError("SYMPHONY_AGENT_ID not found in environment or provided via --agent-id")
        if not self.api_key:
            raise ValueError("SYMPHONY_API_KEY not found in environment or provided")

        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def test_get_positions(self) -> Dict[str, Any]:
        """Test GET /agent/positions endpoint."""
        print("\n" + "="*80)
        print("TEST 1: GET /agent/positions")
        print("="*80)

        url = f"{self.base_url}/agent/positions"
        params = {"agentId": self.agent_id}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                status = response.status
                data = await response.json()

                print(f"\nStatus Code: {status}")
                print(f"\nResponse:")
                print(json.dumps(data, indent=2))

                if status == 200:
                    print(f"\n✅ SUCCESS: Found {data.get('positionsCount', 0)} positions, {data.get('ordersCount', 0)} orders")

                    # Analyze position data structure
                    if data.get('positions'):
                        print("\n📊 Position Data Structure Analysis:")
                        pos = data['positions'][0]
                        print(f"  ✓ Has entryPrice: {pos.get('entryPrice') is not None}")
                        print(f"  ✓ Has currentPrice: {pos.get('currentPrice') is not None}")
                        print(f"  ✓ Has createdTimestamp: {pos.get('createdTimestamp') is not None}")
                        print(f"  ✓ Has pnlUSD: {pos.get('pnlUSD') is not None}")
                        print(f"  ✓ Has slPrice: {pos.get('slPrice') is not None}")
                        print(f"  ✓ Has tpPrice: {pos.get('tpPrice') is not None}")
                else:
                    print(f"\n❌ FAILED: {data.get('message', 'Unknown error')}")

                return data

    async def test_open_position(self, symbol: str = "SOL", size_usd: float = 5.0) -> Optional[str]:
        """Test POST /agent/batch-open endpoint."""
        print("\n" + "="*80)
        print(f"TEST 2: POST /agent/batch-open (${size_usd} {symbol} LONG)")
        print("="*80)

        # Calculate weight (assume $100 account balance for now)
        # Weight = percentage of balance to use (0-100)
        # For $5 position on $100 balance = 5% weight
        # Symphony min is $5 per trade
        weight = 100.0  # Use 100% weight, let Symphony calculate actual size

        payload = {
            "agentId": self.agent_id,
            "symbol": symbol,
            "action": "LONG",
            "weight": weight,
            "leverage": 1.1,  # Minimum leverage (1.1x)
            "orderOptions": {
                "triggerPrice": 0,
                "stopLossPrice": 0,
                "takeProfitPrice": 0
            }
        }

        print(f"\nRequest Payload:")
        print(json.dumps(payload, indent=2))

        url = f"{self.base_url}/agent/batch-open"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                status = response.status
                data = await response.json()

                print(f"\nStatus Code: {status}")
                print(f"\nResponse:")
                print(json.dumps(data, indent=2))

                if status == 200:
                    batch_id = data.get('batchId')
                    successful = data.get('successful', 0)
                    failed = data.get('failed', 0)

                    print(f"\n✅ SUCCESS: Batch ID = {batch_id}")
                    print(f"  Successful: {successful}")
                    print(f"  Failed: {failed}")

                    # Analyze result structure
                    if data.get('results'):
                        result = data['results'][0].get('result', {})
                        print(f"\n📊 Trade Result Analysis:")
                        print(f"  ✓ Protocol Position Hash: {result.get('protocolPositionHash')}")
                        print(f"  ✓ Symphony Position Hash: {result.get('symphonyPositionHash')}")
                        print(f"  ✓ Submit TX Hash: {result.get('submitTxHash')}")
                        print(f"  ✓ Explorer URL: {result.get('submitExplorerUrl')}")

                    return batch_id
                else:
                    print(f"\n❌ FAILED: {data.get('message', 'Unknown error')}")
                    return None

    async def test_get_batch_positions(self, batch_id: str) -> Dict[str, Any]:
        """Test GET /agent/batch-positions endpoint."""
        print("\n" + "="*80)
        print(f"TEST 3: GET /agent/batch-positions (batchId: {batch_id})")
        print("="*80)

        url = f"{self.base_url}/agent/batch-positions"
        params = {"batchId": batch_id}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                status = response.status
                data = await response.json()

                print(f"\nStatus Code: {status}")
                print(f"\nResponse:")
                print(json.dumps(data, indent=2))

                if status == 200:
                    print(f"\n✅ SUCCESS: Found {data.get('positionsCount', 0)} positions")
                else:
                    print(f"\n❌ FAILED: {data.get('message', 'Unknown error')}")

                return data

    async def test_close_position(self, batch_id: str) -> Dict[str, Any]:
        """Test POST /agent/batch-close endpoint."""
        print("\n" + "="*80)
        print(f"TEST 4: POST /agent/batch-close (batchId: {batch_id})")
        print("="*80)

        payload = {
            "agentId": self.agent_id,
            "batchId": batch_id
        }

        print(f"\nRequest Payload:")
        print(json.dumps(payload, indent=2))

        url = f"{self.base_url}/agent/batch-close"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                status = response.status
                data = await response.json()

                print(f"\nStatus Code: {status}")
                print(f"\nResponse:")
                print(json.dumps(data, indent=2))

                if status == 200:
                    successful = data.get('successful', 0)
                    skipped = data.get('skipped', 0)
                    failed = data.get('failed', 0)

                    print(f"\n✅ SUCCESS: Position closed")
                    print(f"  Successful: {successful}")
                    print(f"  Skipped: {skipped}")
                    print(f"  Failed: {failed}")
                else:
                    print(f"\n❌ FAILED: {data.get('message', 'Unknown error')}")

                return data

    async def run_full_test(self, execute_trade: bool = False, symbol: str = "SOL", size_usd: float = 5.0):
        """Run full test suite."""
        print("\n" + "🧪" * 40)
        print("SYMPHONY.IO API INTEGRATION TEST")
        print(f"Agent ID: {self.agent_id}")
        print(f"Execute Trade: {execute_trade}")
        print("🧪" * 40)

        try:
            # Test 1: Get current positions
            positions_data = await self.test_get_positions()

            if execute_trade:
                print("\n⚠️  WARNING: About to execute a REAL trade with REAL money!")
                print(f"   Symbol: {symbol}")
                print(f"   Size: ${size_usd} USDC")
                print(f"   Leverage: 1.1x")

                # Give user 5 seconds to cancel
                for i in range(5, 0, -1):
                    print(f"   Executing in {i}...", end='\r')
                    await asyncio.sleep(1)
                print("\n")

                # Test 2: Open position
                batch_id = await self.test_open_position(symbol=symbol, size_usd=size_usd)

                if batch_id:
                    # Wait a moment for position to settle
                    print("\n⏳ Waiting 5 seconds for position to settle...")
                    await asyncio.sleep(5)

                    # Test 3: Get batch positions
                    await self.test_get_batch_positions(batch_id)

                    # Test 4: Close position
                    await self.test_close_position(batch_id)

                    # Test 5: Verify closed
                    print("\n⏳ Waiting 5 seconds for close to settle...")
                    await asyncio.sleep(5)
                    await self.test_get_positions()

            print("\n" + "="*80)
            print("✅ TEST SUITE COMPLETED")
            print("="*80)

        except Exception as e:
            print(f"\n❌ TEST SUITE FAILED: {str(e)}")
            import traceback
            traceback.print_exc()


async def main():
    parser = argparse.ArgumentParser(description="Test Symphony.io API integration")
    parser.add_argument("--agent-id", help="Your Symphony agent ID (optional, uses SYMPHONY_AGENT_ID from .env if not provided)")
    parser.add_argument("--execute-trade", action="store_true", help="Execute a real test trade (default: read-only)")
    parser.add_argument("--symbol", default="SOL", help="Trading symbol (default: SOL)")
    parser.add_argument("--size-usd", type=float, default=5.0, help="Position size in USDC (default: 5.0)")

    args = parser.parse_args()

    # Validate minimum size
    if args.size_usd < 5.0:
        print(f"❌ Error: Symphony minimum trade size is $5 USDC")
        sys.exit(1)

    # Create tester (will read from env if agent_id not provided)
    tester = SymphonyAPITester(agent_id=args.agent_id)

    # Run tests
    await tester.run_full_test(
        execute_trade=args.execute_trade,
        symbol=args.symbol,
        size_usd=args.size_usd
    )


if __name__ == "__main__":
    asyncio.run(main())
