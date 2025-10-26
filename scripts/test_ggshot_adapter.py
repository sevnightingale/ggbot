#!/usr/bin/env python3
"""
Test Script: ggShot Adapter Standalone Test

Tests the ggShot adapter to ensure it correctly queries and formats signals
from the market_data table.

Usage:
    cd /home/sev/ggbot
    source .venv/bin/activate
    python scripts/test_ggshot_adapter.py
"""

import os
import sys
import asyncio
from datetime import datetime

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from market_intelligence.adapters.signals.ggshot_adapter import GGShotAdapter
from market_intelligence.types import QueryParams


async def test_adapter():
    """Test the ggShot adapter with various queries."""
    print("="*80)
    print("ggShot Adapter Test")
    print("="*80)
    print()

    # Create adapter instance
    adapter = GGShotAdapter()

    # Test symbols that should have signals (from backfill)
    test_symbols = [
        'BTC/USDT',
        'ETH/USDT',
        'SOL/USDT',
        'APT/USDT',
        'COMP/USDT'
    ]

    for symbol in test_symbols:
        print(f"\n{'='*80}")
        print(f"Testing: {symbol}")
        print(f"{'='*80}\n")

        try:
            # Query signals for symbol
            params = QueryParams(params={'symbol': symbol, 'include_raw': False})
            response = await adapter.fetch(params)

            # Display results
            data = response.data
            signals = data.get('signals', {})
            metadata = data.get('metadata', {})

            print(f"✅ Query successful")
            print(f"   Timeframes found: {len(signals)}")
            print(f"   Timeframes: {list(signals.keys())}")
            print(f"   Latest signal age: {metadata.get('latest_signal_age')}")
            print(f"   Confidence: {response.confidence:.2f}")
            print()

            # Show signal details
            if signals:
                print(f"Signal Details:")
                for tf, signal in signals.items():
                    print(f"\n  [{tf}]")
                    print(f"    Direction: {signal['direction']}")
                    print(f"    Entry Zone: {signal['entry_zone']['low']:.2f} - {signal['entry_zone']['high']:.2f} (mid: {signal['entry_zone']['mid']:.2f})")
                    print(f"    Stop Loss: {signal['stop_loss']:.2f}")
                    print(f"    Take Profit: {signal['take_profit']:.2f}")
                    print(f"    Confidence: {signal['strategy_accuracy']}%")
                    print(f"    Targets: {len(signal['targets'])} levels")

                    # Show all targets
                    for target in signal['targets']:
                        print(f"      Target {target['number']}: {target['price']:.2f}")

            else:
                print(f"⚠️  No signals found for {symbol}")

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("Test Complete")
    print(f"{'='*80}\n")

    # Test with include_raw=True
    print(f"\n{'='*80}")
    print("Testing with include_raw=True for BTC/USDT")
    print(f"{'='*80}\n")

    try:
        params = QueryParams(params={'symbol': 'BTC/USDT', 'include_raw': True})
        response = await adapter.fetch(params)

        signals = response.data.get('signals', {})
        if signals:
            # Show raw message from first timeframe
            first_tf = list(signals.keys())[0]
            first_signal = signals[first_tf]

            if 'raw_message' in first_signal:
                print(f"Raw Telegram message for {first_tf}:")
                print("-" * 80)
                print(first_signal['raw_message'][:300] + "..." if len(first_signal['raw_message']) > 300 else first_signal['raw_message'])
                print("-" * 80)
            else:
                print("⚠️  No raw message included")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

    # Cleanup
    await adapter.close()


if __name__ == "__main__":
    asyncio.run(test_adapter())
