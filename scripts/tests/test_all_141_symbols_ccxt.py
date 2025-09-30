#!/usr/bin/env python3
"""
Comprehensive test of all 141 ggShot symbols across all 5 CCXT exchanges.

This test validates that our CCXT provider can handle all symbols from our 
ggShot signal list across all major exchanges. It provides detailed logging
and analysis to identify any missing mappings, delisted symbols, or infrastructure issues.
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.common.logger import logger
from decision.providers.ccxt_provider import CCXTPriceProvider


# All 141 ggShot symbols extracted from the CCXT provider mappings
GGSHOT_SYMBOLS = [
    '1INCH/USDT', 'AAVE/USDT', 'ACH/USDT', 'ADA/USDT', 'ALGO/USDT', 'ALICE/USDT', 'ALPHA/USDT', 'ALT/USDT',
    'ANKR/USDT', 'APE/USDT', 'API3/USDT', 'APT/USDT', 'ARB/USDT', 'ARKM/USDT', 'AR/USDT', 'ASTR/USDT',
    'ATOM/USDT', 'AUCTION/USDT', 'AVAX/USDT', 'AXS/USDT', 'BAKE/USDT', 'BAL/USDT', 'BAND/USDT', 'BAT/USDT',
    'BCH/USDT', 'BEL/USDT', 'BIGTIME/USDT', 'BNB/USDT', 'BNT/USDT', 'BOME/USDT', 'BTC/USDT', 'CAKE/USDT',
    'CELR/USDT', 'CETUS/USDT', 'CFX/USDT', 'CHR/USDT', 'CHZ/USDT', 'COMP/USDT', 'COTI/USDT', 'CRV/USDT',
    'CYBER/USDT', 'DASH/USDT', 'DOGE/USDT', 'DOT/USDT', 'DYDX/USDT', 'EGLD/USDT', 'ENA/USDT', 'ENS/USDT',
    'ETC/USDT', 'ETH/USDT', 'ETHFI/USDT', 'FET/USDT', 'FIL/USDT', 'FLM/USDT', 'FLOW/USDT', 'GALA/USDT',
    'GMT/USDT', 'GMX/USDT', 'GRT/USDT', 'GTC/USDT', 'HBAR/USDT', 'HIGH/USDT', 'HOOK/USDT', 'ICP/USDT',
    'ICX/USDT', 'ID/USDT', 'INJ/USDT', 'IOST/USDT', 'IOTX/USDT', 'JASMY/USDT', 'JTO/USDT', 'JUP/USDT',
    'KAVA/USDT', 'KNC/USDT', 'KSM/USDT', 'LDO/USDT', 'LEVER/USDT', 'LINK/USDT', 'LPT/USDT', 'LQTY/USDT',
    'LRC/USDT', 'LTC/USDT', 'MAGIC/USDT', 'MANA/USDT', 'MASK/USDT', 'MATIC/USDT', 'MKR/USDT', 'NEAR/USDT',
    'NEO/USDT', 'NKN/USDT', 'NMR/USDT', 'NOT/USDT', 'NTRN/USDT', 'OGN/USDT', 'ONDO/USDT', 'ONE/USDT',
    'ONT/USDT', 'OP/USDT', 'ORDI/USDT', 'PENDLE/USDT', 'PEOPLE/USDT', 'PYTH/USDT', 'QTUM/USDT', 'RARE/USDT',
    'RENDER/USDT', 'RLC/USDT', 'ROSE/USDT', 'RSR/USDT', 'RUNE/USDT', 'RVN/USDT', 'SAND/USDT', 'SEI/USDT',
    'SFP/USDT', 'SKLUS/USDT', 'SNX/USDT', 'SOL/USDT', 'STORJ/USDT', 'STRK/USDT', 'STX/USDT', 'SUI/USDT',
    'S/USDT', 'SUSHI/USDT', 'SXP/USDT', 'TAO/USDT', 'THETA/USDT', 'TIA/USDT', 'TRB/USDT', 'TRX/USDT',
    'TURBO/USDT', 'TWT/USDT', 'VANRY/USDT', 'VET/USDT', 'WIF/USDT', 'WLD/USDT', 'WOO/USDT', 'W/USDT',
    'XRP/USDT', 'YFI/USDT', 'ZIL/USDT', 'ZRO/USDT', 'ZRX/USDT'
]

# Exchange names in priority order
EXCHANGES = ['binance', 'coinbase', 'kraken', 'okx', 'bybit']


class SymbolTestResult:
    """Results for a single symbol test"""
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.exchange_results: Dict[str, Any] = {}
        self.successful_exchanges: List[str] = []
        self.failed_exchanges: List[str] = []
        self.price_obtained: bool = False
        self.final_price: float = None
        self.final_exchange: str = None
        self.errors: List[str] = []


class ExchangeTestSuite:
    """Test suite for all exchanges and symbols"""
    
    def __init__(self):
        self.provider = CCXTPriceProvider()
        self.results: Dict[str, SymbolTestResult] = {}
        self.start_time = datetime.now()
        
    async def test_single_symbol_single_exchange(self, symbol: str, exchange: str) -> Tuple[bool, Any, str]:
        """
        Test a single symbol on a single exchange.
        
        Returns:
            (success: bool, result: Any, error_message: str)
        """
        try:
            # Get the mapped symbol for this exchange
            exchange_map = self.provider.EXCHANGE_SYMBOL_MAPS.get(exchange, {})
            mapped_symbol = exchange_map.get(symbol)
            
            if not mapped_symbol:
                return False, None, f"No mapping for {symbol} on {exchange}"
            
            # Test the specific exchange
            price = await self.provider._get_price_from_exchange(exchange, symbol)
            
            if price and price > 0:
                return True, price, ""
            else:
                return False, None, f"No price returned from {exchange}"
                
        except Exception as e:
            error_msg = f"Exception on {exchange}: {str(e)}"
            # Only log detailed errors for debugging if needed
            return False, None, error_msg
    
    async def test_single_symbol_all_exchanges(self, symbol: str) -> SymbolTestResult:
        """Test a single symbol across all exchanges"""
        result = SymbolTestResult(symbol)
        
        # Test each exchange individually (minimal logging during test)
        for exchange in EXCHANGES:
            success, price, error = await self.test_single_symbol_single_exchange(symbol, exchange)
            
            result.exchange_results[exchange] = {
                'success': success,
                'price': price,
                'error': error
            }
            
            if success:
                result.successful_exchanges.append(exchange)
                if not result.price_obtained:
                    result.price_obtained = True
                    result.final_price = price
                    result.final_exchange = exchange
            else:
                result.failed_exchanges.append(exchange)
                result.errors.append(f"{exchange}: {error}")
        
        # Test the provider's get_current_price method (which tries exchanges in order)
        try:
            provider_price = await self.provider.get_current_price(symbol)
            
            if provider_price:
                result.final_price = provider_price
                result.price_obtained = True
                
        except Exception as e:
            error_msg = f"Provider method failed: {str(e)}"
            result.errors.append(f"provider: {error_msg}")
        
        # Quick progress indicator
        status = "✅" if result.price_obtained else "❌"
        print(f"{status} {symbol}: {len(result.successful_exchanges)}/{len(EXCHANGES)} exchanges")
        
        return result
    
    async def test_all_symbols(self):
        """Test all 141 symbols across all exchanges"""
        print("🎯 STARTING COMPREHENSIVE CCXT SYMBOL TEST")
        print("=" * 80)
        print(f"Testing {len(GGSHOT_SYMBOLS)} symbols across {len(EXCHANGES)} exchanges")
        print(f"Exchanges: {', '.join(EXCHANGES)}")
        print(f"Start time: {self.start_time}")
        print("=" * 80)
        
        # Test all symbols with minimal output during processing
        for i, symbol in enumerate(GGSHOT_SYMBOLS):
            try:
                print(f"[{i+1:3}/{len(GGSHOT_SYMBOLS)}] Processing {symbol:15}", end=" ")
                result = await self.test_single_symbol_all_exchanges(symbol)
                self.results[symbol] = result
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"❌ {symbol}: CRITICAL ERROR - {str(e)}")
                
                # Create a failure result
                result = SymbolTestResult(symbol)
                result.errors.append(f"Critical error: {str(e)}")
                self.results[symbol] = result
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 100)
        print("📊 COMPREHENSIVE TEST SUMMARY REPORT")
        print("=" * 100)
        print(f"Test duration: {duration}")
        print(f"Total symbols tested: {len(self.results)}")
        
        # Overall statistics
        total_symbols = len(self.results)
        successful_symbols = sum(1 for r in self.results.values() if r.price_obtained)
        failed_symbols = total_symbols - successful_symbols
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   ✅ Successful symbols: {successful_symbols}/{total_symbols} ({successful_symbols/total_symbols*100:.1f}%)")
        print(f"   ❌ Failed symbols: {failed_symbols}/{total_symbols} ({failed_symbols/total_symbols*100:.1f}%)")
        
        # Exchange performance analysis
        print(f"\n📈 EXCHANGE PERFORMANCE ANALYSIS:")
        exchange_stats = {exchange: {'success': 0, 'fail': 0} for exchange in EXCHANGES}
        
        for result in self.results.values():
            for exchange in EXCHANGES:
                if exchange in result.exchange_results:
                    if result.exchange_results[exchange]['success']:
                        exchange_stats[exchange]['success'] += 1
                    else:
                        exchange_stats[exchange]['fail'] += 1
        
        for exchange in EXCHANGES:
            success = exchange_stats[exchange]['success']
            fail = exchange_stats[exchange]['fail']
            total = success + fail
            if total > 0:
                success_rate = success / total * 100
                print(f"   {exchange:>10}: {success:>3}/{total:>3} symbols ({success_rate:>5.1f}%)")
        
        # Sample of specific errors for Binance (to diagnose the issue)
        print(f"\n🔍 BINANCE ERROR ANALYSIS:")
        binance_errors = {}
        for result in self.results.values():
            if 'binance' in result.exchange_results:
                error = result.exchange_results['binance'].get('error', '')
                if error and not result.exchange_results['binance']['success']:
                    error_key = error[:100]  # Truncate long errors
                    binance_errors[error_key] = binance_errors.get(error_key, 0) + 1
        
        for error, count in sorted(binance_errors.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {error[:80]}... ({count} times)")
        
        # Failed symbols analysis (top 20)
        if failed_symbols > 0:
            print(f"\n❌ FAILED SYMBOLS (top 20 of {failed_symbols} total):")
            failed_list = [(symbol, result) for symbol, result in self.results.items() if not result.price_obtained]
            for symbol, result in failed_list[:20]:
                print(f"   {symbol:>15}: All exchanges failed")
        
        # Symbols with limited exchange support (top 20)
        limited_support = [(symbol, result) for symbol, result in self.results.items() 
                          if result.price_obtained and len(result.successful_exchanges) <= 2]
        if limited_support:
            print(f"\n⚠️  SYMBOLS WITH LIMITED EXCHANGE SUPPORT (top 20):")
            for symbol, result in limited_support[:20]:
                print(f"   {symbol:>15}: Only works on {', '.join(result.successful_exchanges)}")
        
        # Most common error types
        print(f"\n🔍 MOST COMMON FAILURE REASONS:")
        error_counts = {}
        for result in self.results.values():
            for error in result.errors:
                if 'not found in' in error or 'not supported' in error:
                    error_type = "Symbol not listed on exchange"
                elif 'No price returned' in error:
                    error_type = "No price returned (symbol may be delisted)"
                elif 'timeout' in error.lower() or 'network' in error.lower():
                    error_type = "Network/timeout issues"
                elif 'rate limit' in error.lower() or 'limit' in error.lower():
                    error_type = "Rate limiting"
                elif 'Exception' in error:
                    error_type = "Network/connection exceptions"
                else:
                    error_type = "Other errors"
                
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {error_type:>40}: {count:>4} occurrences")
        
        # Recommendations
        print(f"\n💡 KEY FINDINGS & RECOMMENDATIONS:")
        if exchange_stats['binance']['fail'] > exchange_stats['binance']['success']:
            print("   🚨 Binance has high failure rate - investigate connection/rate limiting")
        
        best_exchange = max(exchange_stats.items(), key=lambda x: x[1]['success'])[0]
        print(f"   🏆 Most reliable exchange: {best_exchange}")
        
        if failed_symbols > 20:
            print(f"   ⚠️  {failed_symbols} symbols failed on ALL exchanges - may be delisted")
        
        print(f"   ✅ CHZ/USDT mapping fix: {'SUCCESS' if any('CHZ/USDT' in str(r.successful_exchanges) for r in self.results.values()) else 'FAILED'}")
        
        print("\n" + "=" * 100)
        print("✅ COMPREHENSIVE TEST COMPLETED")
        print("=" * 100)


async def main():
    """Main test execution"""
    suite = ExchangeTestSuite()
    
    try:
        await suite.test_all_symbols()
        suite.generate_summary_report()
        
    except Exception as e:
        logger.error(f"💥 Test suite failed: {str(e)}")
        logger.error(traceback.format_exc())
        return 1
    
    finally:
        # Cleanup
        try:
            await suite.provider.cleanup()
        except:
            pass
    
    return 0


if __name__ == "__main__":
    # Configure logging for detailed output
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Run the test
    exit_code = asyncio.run(main())
    sys.exit(exit_code)