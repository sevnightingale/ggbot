#!/usr/bin/env python3
"""
Symbol Extraction Test Script

Tests all 141 symbols in our registry to verify they work with hummingbot-api.
This will help identify any symbols that are failing extraction.
"""

import asyncio
import sys
import os
from typing import Dict, List, Any
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.symbols.registry import SYMBOL_REGISTRY
from core.symbols.standardizer import UniversalSymbolStandardizer
from extraction.v2.data_client import HummingbotDataClient
from core.common.logger import logger


class SymbolExtractionTester:
    """Test extraction capabilities for all supported symbols"""

    def __init__(self):
        self.standardizer = UniversalSymbolStandardizer()
        self.results = {
            "success": [],
            "failed": [],
            "errors": {}
        }

    async def test_symbol(self, symbol_key: str, symbol_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Test candle data extraction for a single symbol.

        Args:
            symbol_key: Symbol key from registry (e.g., "btc")
            symbol_data: Symbol data dict with all formats

        Returns:
            Test result dictionary
        """
        ccxt_format = symbol_data.get("ccxt")  # BTC/USDT format for hummingbot
        hummingbot_format = symbol_data.get("hummingbot")  # BTC-USDT format

        result = {
            "symbol_key": symbol_key,
            "ccxt_format": ccxt_format,
            "hummingbot_format": hummingbot_format,
            "success": False,
            "error": None,
            "candle_count": 0,
            "latest_price": None
        }

        try:
            async with HummingbotDataClient() as client:
                # Test with minimal data request (5 candles, 1h timeframe)
                df = await client.get_candles(
                    symbol=ccxt_format,  # Will be converted to hummingbot format internally
                    timeframe="1h",
                    limit=5,
                    connector="kucoin"
                )

                if df is not None and len(df) > 0:
                    result.update({
                        "success": True,
                        "candle_count": len(df),
                        "latest_price": float(df.iloc[-1]["close"]) if "close" in df.columns else None
                    })

                    logger.info(f"✅ {symbol_key} ({ccxt_format}): {len(df)} candles, latest price: {result['latest_price']}")
                else:
                    result["error"] = "No data returned"
                    logger.warning(f"❌ {symbol_key} ({ccxt_format}): No data returned")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ {symbol_key} ({ccxt_format}): {str(e)}")

        return result

    async def test_all_symbols(self, test_limit: int = None) -> Dict[str, Any]:
        """
        Test extraction for all symbols in registry.

        Args:
            test_limit: Optional limit for testing (for quick testing)

        Returns:
            Complete test results
        """
        logger.info(f"🧪 Starting symbol extraction test for {len(SYMBOL_REGISTRY)} symbols")

        symbols_to_test = list(SYMBOL_REGISTRY.items())
        if test_limit:
            symbols_to_test = symbols_to_test[:test_limit]
            logger.info(f"Limited test to first {test_limit} symbols")

        # Test symbols in batches to avoid overwhelming the API
        batch_size = 10
        total_symbols = len(symbols_to_test)

        for i in range(0, total_symbols, batch_size):
            batch = symbols_to_test[i:i + batch_size]
            batch_results = []

            logger.info(f"Testing batch {i//batch_size + 1}/{(total_symbols + batch_size - 1)//batch_size}")

            # Process batch concurrently with limited concurrency
            tasks = []
            for symbol_key, symbol_data in batch:
                task = self.test_symbol(symbol_key, symbol_data)
                tasks.append(task)

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch task failed: {result}")
                    continue

                if result["success"]:
                    self.results["success"].append(result)
                else:
                    self.results["failed"].append(result)
                    self.results["errors"][result["symbol_key"]] = result["error"]

            # Small delay between batches
            await asyncio.sleep(1)

        # Generate summary
        total_tested = len(self.results["success"]) + len(self.results["failed"])
        success_rate = len(self.results["success"]) / total_tested * 100 if total_tested > 0 else 0

        summary = {
            "total_symbols": len(SYMBOL_REGISTRY),
            "tested_symbols": total_tested,
            "successful": len(self.results["success"]),
            "failed": len(self.results["failed"]),
            "success_rate": round(success_rate, 2),
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"📊 Test completed: {summary['successful']}/{summary['tested_symbols']} symbols successful ({summary['success_rate']}%)")

        return {
            "summary": summary,
            "results": self.results
        }

    def print_detailed_results(self, results: Dict[str, Any]):
        """Print detailed test results to console"""

        summary = results["summary"]
        print(f"\n{'='*60}")
        print(f"SYMBOL EXTRACTION TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total symbols in registry: {summary['total_symbols']}")
        print(f"Symbols tested: {summary['tested_symbols']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success rate: {summary['success_rate']}%")
        print(f"Test completed: {summary['timestamp']}")

        if self.results["failed"]:
            print(f"\n🔴 FAILED SYMBOLS ({len(self.results['failed'])}):")
            print("-" * 40)
            for failed in self.results["failed"]:
                print(f"• {failed['symbol_key']:10} ({failed['ccxt_format']:12}) - {failed['error']}")

        if self.results["success"]:
            print(f"\n✅ SUCCESSFUL SYMBOLS ({len(self.results['success'])}):")
            print("-" * 40)
            print("Symbol Key | Format     | Candles | Latest Price")
            print("-" * 40)
            for success in self.results["success"][:10]:  # Show first 10
                price = f"${success['latest_price']:,.2f}" if success['latest_price'] else "N/A"
                print(f"{success['symbol_key']:10} | {success['ccxt_format']:10} | {success['candle_count']:7} | {price}")

            if len(self.results["success"]) > 10:
                print(f"... and {len(self.results['success']) - 10} more successful symbols")


async def main():
    """Main test runner"""

    # Check if we want to run a quick test or full test
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        test_limit = 20
        print(f"🚀 Running quick test with {test_limit} symbols")
    else:
        test_limit = None
        print("🚀 Running full test with all 141 symbols")

    tester = SymbolExtractionTester()

    try:
        # Test hummingbot connection first
        async with HummingbotDataClient() as client:
            connection_test = await client.test_connection()
            if connection_test["status"] != "connected":
                print(f"❌ Cannot connect to Hummingbot API: {connection_test}")
                return

            print(f"✅ Connected to Hummingbot API at {connection_test['base_url']}")

        # Run the tests
        results = await tester.test_all_symbols(test_limit)

        # Print results
        tester.print_detailed_results(results)

        # Exit with error code if we have failures
        if results["results"]["failed"]:
            print(f"\n⚠️  Found {len(results['results']['failed'])} failing symbols")
            sys.exit(1)
        else:
            print(f"\n🎉 All symbols tested successfully!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())