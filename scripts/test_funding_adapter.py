#!/usr/bin/env python3
"""
Test script for Binance Funding Rate Adapter.

Tests fetching funding rates for BTC and ETH from Binance Futures API.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from market_intelligence.adapters.derivatives.binance_funding import BinanceFundingAdapter
from market_intelligence.types import QueryParams


async def test_funding_rates():
    """Test fetching funding rates for BTC and ETH."""

    adapter = BinanceFundingAdapter()

    print("\n" + "="*80)
    print("TESTING BINANCE FUNDING RATE ADAPTER")
    print("="*80)

    # Test 1: Fetch BTC funding rate
    print("\n📊 Test 1: Fetching BTC/USDT funding rate...")
    print("-" * 80)

    try:
        params = QueryParams(params={'symbol': 'BTC/USDT'})
        response = await adapter.fetch(params)

        print(f"✅ SUCCESS!")
        print(f"\nData:")
        print(json.dumps(response.data, indent=2, default=str))
        print(f"\nMetadata:")
        print(json.dumps(response.metadata, indent=2, default=str))
        print(f"\nConfidence: {response.confidence}")
        print(f"Related Queries: {response.related_queries}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Fetch ETH funding rate with mark price
    print("\n" + "="*80)
    print("📊 Test 2: Fetching ETH/USDT funding rate with mark price...")
    print("-" * 80)

    try:
        params = QueryParams(params={'symbol': 'ETH/USDT', 'include_mark_price': True})
        response = await adapter.fetch(params)

        print(f"✅ SUCCESS!")
        print(f"\nData:")
        print(json.dumps(response.data, indent=2, default=str))
        print(f"\nMetadata:")
        print(json.dumps(response.metadata, indent=2, default=str))
        print(f"\nConfidence: {response.confidence}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Test interpretation logic with mock extreme values
    print("\n" + "="*80)
    print("🧪 Test 3: Testing interpretation logic...")
    print("-" * 80)

    test_rates = [
        (0.0001, "Slight long bias"),
        (0.006, "High long leverage"),
        (0.015, "Extreme long leverage"),
        (-0.0002, "Slight short bias"),
        (-0.006, "High short leverage"),
        (-0.015, "Extreme short leverage"),
        (0.00005, "Neutral")
    ]

    for rate, expected_level in test_rates:
        interpretation = adapter._interpret_funding_rate(rate)
        rate_pct = rate * 100
        print(f"\nRate: {rate_pct:+.4f}% → {interpretation['level']}")
        print(f"  Risk: {interpretation['risk']}")
        print(f"  Interpretation: {interpretation['interpretation']}")
        print(f"  Trading Implication: {interpretation['trading_implication']}")

    # Clean up
    await adapter.close()

    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Check frontend UI - MarketDataSelector should show 'Crypto Derivatives'")
    print("  2. Create bot config with funding rates enabled")
    print("  3. Verify decision engine receives funding rate context")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_funding_rates())
