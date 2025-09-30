#!/usr/bin/env python3
"""
Multi-Exchange Symbol Test Script

Tests all 141 symbols across multiple exchanges to find the best coverage.
Also validates symbol format conversion.
"""

import asyncio
import sys
import os
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.symbols.registry import SYMBOL_REGISTRY
from core.symbols.standardizer import UniversalSymbolStandardizer
from extraction.v2.data_client import HummingbotDataClient
from core.common.logger import logger


class MultiExchangeSymbolTester:
    """Test symbol availability across multiple exchanges"""

    def __init__(self):
        self.standardizer = UniversalSymbolStandardizer()
        self.exchanges = ["kucoin", "binance", "gate_io", "okx", "ascend_ex"]
        self.results = {
            "symbol_analysis": {},
            "exchange_coverage": {ex: {"success": [], "failed": []} for ex in self.exchanges},
            "format_issues": [],
            "summary": {}
        }

    async def test_symbol_on_exchange(self, symbol_key: str, symbol_data: Dict[str, str], exchange: str) -> Dict[str, Any]:
        """
        Test a single symbol on a specific exchange.

        Args:
            symbol_key: Symbol key from registry (e.g., "btc")
            symbol_data: Symbol data dict with all formats
            exchange: Exchange connector name

        Returns:
            Test result dictionary
        """
        # Test different symbol formats
        formats_to_test = {
            "ccxt": symbol_data.get("ccxt"),           # BTC/USDT
            "hummingbot": symbol_data.get("hummingbot"), # BTC-USDT
            "ggshot": symbol_data.get("ggshot")        # BTCUSDT (will be converted)
        }

        result = {
            "symbol_key": symbol_key,
            "exchange": exchange,
            "success": False,
            "working_format": None,
            "error": None,
            "candle_count": 0,
            "latest_price": None,
            "format_tested": None
        }

        for format_name, format_symbol in formats_to_test.items():
            if not format_symbol:
                continue

            try:
                # Convert ggshot format for testing
                test_symbol = format_symbol
                if format_name == "ggshot":
                    # Try to convert BTCUSDT -> BTC/USDT for API
                    test_symbol = self.standardizer.normalize(format_symbol, "ggshot", "ccxt")
                    if not test_symbol:
                        continue

                async with HummingbotDataClient() as client:
                    df = await client.get_candles(
                        symbol=test_symbol,
                        timeframe="1h",
                        limit=3,  # Minimal request
                        connector=exchange
                    )

                    if df is not None and len(df) > 0:
                        result.update({
                            "success": True,
                            "working_format": format_name,
                            "format_tested": f"{format_name}:{format_symbol} -> {test_symbol}",
                            "candle_count": len(df),
                            "latest_price": float(df.iloc[-1]["close"]) if "close" in df.columns else None
                        })
                        return result  # Success, no need to try other formats

            except Exception as e:
                error_msg = str(e).strip()
                result["error"] = error_msg

                # Log format testing
                logger.debug(f"❌ {symbol_key} on {exchange} with {format_name} format ({format_symbol}): {error_msg}")

        return result

    async def test_symbol_across_exchanges(self, symbol_key: str, symbol_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Test a symbol across all exchanges to find where it's available.

        Returns:
            Dictionary with results for each exchange
        """
        symbol_result = {
            "symbol_key": symbol_key,
            "formats": {
                "ggshot": symbol_data.get("ggshot"),
                "ccxt": symbol_data.get("ccxt"),
                "hummingbot": symbol_data.get("hummingbot"),
                "platform": symbol_data.get("platform")
            },
            "exchanges": {},
            "available_on": [],
            "best_exchange": None,
            "format_validation": None
        }

        # Validate format conversion
        try:
            converted = self.standardizer.get_all_formats(symbol_data.get("platform"))
            if converted:
                symbol_result["format_validation"] = "✅ Valid"
            else:
                symbol_result["format_validation"] = "❌ Invalid conversion"
                self.results["format_issues"].append(symbol_key)
        except Exception as e:
            symbol_result["format_validation"] = f"❌ Error: {e}"
            self.results["format_issues"].append(symbol_key)

        # Test on each exchange
        for exchange in self.exchanges:
            try:
                exchange_result = await self.test_symbol_on_exchange(symbol_key, symbol_data, exchange)
                symbol_result["exchanges"][exchange] = exchange_result

                if exchange_result["success"]:
                    symbol_result["available_on"].append(exchange)
                    if not symbol_result["best_exchange"]:
                        symbol_result["best_exchange"] = exchange

                    self.results["exchange_coverage"][exchange]["success"].append(symbol_key)
                else:
                    self.results["exchange_coverage"][exchange]["failed"].append(symbol_key)

                # Small delay between exchange tests
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error testing {symbol_key} on {exchange}: {e}")
                symbol_result["exchanges"][exchange] = {"error": str(e), "success": False}
                self.results["exchange_coverage"][exchange]["failed"].append(symbol_key)

        return symbol_result

    async def test_all_symbols(self, test_limit: int = None) -> Dict[str, Any]:
        """
        Test all symbols across all exchanges.

        Args:
            test_limit: Optional limit for testing (for quick testing)

        Returns:
            Complete analysis results
        """
        logger.info(f"🧪 Starting multi-exchange symbol test for {len(SYMBOL_REGISTRY)} symbols across {len(self.exchanges)} exchanges")

        symbols_to_test = list(SYMBOL_REGISTRY.items())
        if test_limit:
            symbols_to_test = symbols_to_test[:test_limit]
            logger.info(f"Limited test to first {test_limit} symbols")

        # Test symbols in smaller batches to avoid overwhelming APIs
        batch_size = 5  # Smaller batches for multi-exchange testing
        total_symbols = len(symbols_to_test)

        for i in range(0, total_symbols, batch_size):
            batch = symbols_to_test[i:i + batch_size]

            logger.info(f"Testing batch {i//batch_size + 1}/{(total_symbols + batch_size - 1)//batch_size} ({len(batch)} symbols)")

            # Process batch sequentially to avoid rate limits
            for symbol_key, symbol_data in batch:
                logger.info(f"🔍 Testing {symbol_key} ({symbol_data.get('ccxt')}) across {len(self.exchanges)} exchanges...")

                symbol_result = await self.test_symbol_across_exchanges(symbol_key, symbol_data)
                self.results["symbol_analysis"][symbol_key] = symbol_result

                # Log results
                available_exchanges = len(symbol_result["available_on"])
                if available_exchanges > 0:
                    logger.info(f"✅ {symbol_key}: Available on {available_exchanges} exchanges: {symbol_result['available_on']}")
                else:
                    logger.warning(f"❌ {symbol_key}: Not available on any exchange")

            # Longer delay between batches
            await asyncio.sleep(2)

        # Generate comprehensive summary
        self._generate_summary()
        return self.results

    def _generate_summary(self):
        """Generate comprehensive summary statistics"""
        total_symbols = len(self.results["symbol_analysis"])

        # Overall statistics
        symbols_with_coverage = sum(1 for s in self.results["symbol_analysis"].values() if s["available_on"])
        coverage_rate = symbols_with_coverage / total_symbols * 100 if total_symbols > 0 else 0

        # Exchange statistics
        exchange_stats = {}
        for exchange in self.exchanges:
            success_count = len(self.results["exchange_coverage"][exchange]["success"])
            exchange_stats[exchange] = {
                "successful_symbols": success_count,
                "success_rate": success_count / total_symbols * 100 if total_symbols > 0 else 0
            }

        # Coverage distribution
        coverage_distribution = {}
        for symbol_data in self.results["symbol_analysis"].values():
            exchange_count = len(symbol_data["available_on"])
            coverage_distribution[exchange_count] = coverage_distribution.get(exchange_count, 0) + 1

        self.results["summary"] = {
            "total_symbols": total_symbols,
            "symbols_with_coverage": symbols_with_coverage,
            "overall_coverage_rate": round(coverage_rate, 2),
            "format_issues": len(self.results["format_issues"]),
            "exchange_statistics": exchange_stats,
            "coverage_distribution": coverage_distribution,
            "best_exchange": max(exchange_stats.items(), key=lambda x: x[1]["successful_symbols"])[0] if exchange_stats else None,
            "timestamp": datetime.now().isoformat()
        }

    def print_comprehensive_results(self):
        """Print detailed analysis results"""
        summary = self.results["summary"]

        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE MULTI-EXCHANGE SYMBOL ANALYSIS")
        print(f"{'='*80}")

        print(f"\n📊 OVERALL STATISTICS")
        print(f"-" * 40)
        print(f"Total symbols tested: {summary['total_symbols']}")
        print(f"Symbols with coverage: {summary['symbols_with_coverage']}")
        print(f"Overall coverage rate: {summary['overall_coverage_rate']}%")
        print(f"Format validation issues: {summary['format_issues']}")
        print(f"Best exchange: {summary['best_exchange']}")

        print(f"\n🏦 EXCHANGE PERFORMANCE")
        print(f"-" * 50)
        print(f"{'Exchange':<15} | {'Symbols':<8} | {'Success Rate':<12}")
        print(f"-" * 50)
        for exchange, stats in summary["exchange_statistics"].items():
            print(f"{exchange:<15} | {stats['successful_symbols']:<8} | {stats['success_rate']:<12.1f}%")

        print(f"\n📈 COVERAGE DISTRIBUTION")
        print(f"-" * 40)
        for exchange_count, symbol_count in sorted(summary["coverage_distribution"].items()):
            if exchange_count == 0:
                print(f"❌ No coverage: {symbol_count} symbols")
            elif exchange_count == 1:
                print(f"🟡 Single exchange: {symbol_count} symbols")
            else:
                print(f"✅ {exchange_count} exchanges: {symbol_count} symbols")

        # Show symbols with no coverage
        no_coverage = [s for s, data in self.results["symbol_analysis"].items() if not data["available_on"]]
        if no_coverage:
            print(f"\n🔴 SYMBOLS WITH NO COVERAGE ({len(no_coverage)}):")
            print(f"-" * 40)
            for symbol in sorted(no_coverage)[:20]:  # Show first 20
                formats = self.results["symbol_analysis"][symbol]["formats"]
                print(f"• {symbol:<10} ({formats.get('ccxt', 'N/A')})")
            if len(no_coverage) > 20:
                print(f"... and {len(no_coverage) - 20} more")

        # Show format issues
        if self.results["format_issues"]:
            print(f"\n🔧 FORMAT VALIDATION ISSUES ({len(self.results['format_issues'])}):")
            print(f"-" * 40)
            for symbol in sorted(self.results["format_issues"])[:10]:
                print(f"• {symbol}")
            if len(self.results["format_issues"]) > 10:
                print(f"... and {len(self.results['format_issues']) - 10} more")

    def export_results(self, filename: str = None):
        """Export results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"symbol_analysis_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"📄 Results exported to {filename}")
        return filename


async def main():
    """Main test runner"""

    # Check command line arguments
    quick_test = "--quick" in sys.argv
    full_test = "--full" in sys.argv
    export_json = "--export" in sys.argv

    if quick_test:
        test_limit = 10
        print(f"🚀 Running quick multi-exchange test with {test_limit} symbols")
    elif full_test:
        test_limit = None
        print("🚀 Running FULL multi-exchange test with all 141 symbols (this will take a while)")
    else:
        test_limit = 25  # Default moderate test
        print(f"🚀 Running moderate multi-exchange test with {test_limit} symbols")
        print("   Use --quick for 10 symbols, --full for all 141 symbols")

    tester = MultiExchangeSymbolTester()

    try:
        # Test hummingbot connection first
        async with HummingbotDataClient() as client:
            connection_test = await client.test_connection()
            if connection_test["status"] != "connected":
                print(f"❌ Cannot connect to Hummingbot API: {connection_test}")
                return

            print(f"✅ Connected to Hummingbot API at {connection_test['base_url']}")
            print(f"📡 Testing on exchanges: {tester.exchanges}")

        # Run the comprehensive tests
        results = await tester.test_all_symbols(test_limit)

        # Print results
        tester.print_comprehensive_results()

        # Export if requested
        if export_json:
            filename = tester.export_results()
            print(f"\n📁 Detailed results saved to: {filename}")

        # Provide recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"-" * 40)
        best_exchange = results["summary"]["best_exchange"]
        coverage_rate = results["summary"]["overall_coverage_rate"]

        if coverage_rate < 70:
            print(f"⚠️  Low coverage rate ({coverage_rate}%). Consider:")
            print(f"   • Adding more exchanges to Hummingbot setup")
            print(f"   • Updating symbol registry to focus on widely available pairs")
            print(f"   • Using exchange-specific symbol mapping")
        else:
            print(f"✅ Good coverage rate ({coverage_rate}%)")
            print(f"   • Primary exchange: {best_exchange}")
            print(f"   • Consider using multi-exchange fallback for missing symbols")

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())