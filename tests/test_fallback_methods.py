#!/usr/bin/env python3
"""
Test script for the new fallback methods.

Tests both:
- get_candles_with_fallback() in extraction data client
- get_current_price_with_fallback() in trading market data adapter
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extraction.v2.data_client import HummingbotDataClient
from trading.paper.market_data import MarketDataAdapter
from core.common.logger import logger

async def test_extraction_fallback():
    """Test the extraction data client fallback"""
    print("\n🧪 Testing extraction fallback...")

    async with HummingbotDataClient() as client:
        try:
            # Test with a symbol that should work on multiple exchanges
            df = await client.get_candles_with_fallback("BTC/USDT", "1h", 5)
            print(f"✅ Extraction fallback SUCCESS: Retrieved {len(df)} BTC candles")

            # Test with a symbol that might fail on some exchanges
            df2 = await client.get_candles_with_fallback("1INCH/USDT", "1h", 5)
            print(f"✅ Extraction fallback SUCCESS: Retrieved {len(df2)} 1INCH candles")

        except Exception as e:
            print(f"❌ Extraction fallback FAILED: {e}")

async def test_trading_fallback():
    """Test the trading market data adapter fallback"""
    print("\n🧪 Testing trading price fallback...")

    adapter = MarketDataAdapter()
    try:
        # Test with a major symbol
        price = await adapter.get_current_price_with_fallback("BTC/USDT")
        print(f"✅ Trading fallback SUCCESS: BTC price = ${price.mid:.2f}")

        # Test with another symbol that might need fallback
        price2 = await adapter.get_current_price_with_fallback("ETH/USDT")
        print(f"✅ Trading fallback SUCCESS: ETH price = ${price2.mid:.2f}")

    except Exception as e:
        print(f"❌ Trading fallback FAILED: {e}")

async def main():
    """Run both tests"""
    print("🚀 Testing Multi-Exchange Fallback Methods")
    print("=" * 50)

    await test_extraction_fallback()
    await test_trading_fallback()

    print("\n✅ Fallback method testing complete!")

if __name__ == "__main__":
    asyncio.run(main())