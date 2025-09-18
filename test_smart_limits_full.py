#!/usr/bin/env python3
"""
Comprehensive test of smart limits implementation.
Tests all 21 indicators across all 7 timeframes against research matrix.
"""

import asyncio
from extraction.v2.smart_limits import get_smart_limit, get_batch_limit
from extraction.v2.indicators import TechnicalIndicators

# All 21 indicators from our system
ALL_INDICATORS = [
    'rsi', 'stochastic', 'williams_r', 'cci', 'mfi',           # Core Oscillators
    'sma', 'ema', 'macd', 'adx', 'aroon',                     # Trend Indicators
    'atr', 'bbands', 'bbwidth', 'keltner', 'donchian',        # Volatility Indicators
    'obv', 'vwap',                                             # Volume Indicators
    'trix', 'psar', 'roc', 'vortex'                           # Advanced Indicators
]

# All 7 timeframes from research
ALL_TIMEFRAMES = ['1h', '2h', '4h', '6h', '12h', '1d', '1w']

# Expected research matrix (from DOCS/RESEARCH.md)
EXPECTED_LIMITS = {
    'rsi': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'stochastic': {'1h': 80, '2h': 80, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'williams_r': {'1h': 80, '2h': 80, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'cci': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'mfi': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'sma': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 100, '1d': 150, '1w': 150},
    'ema': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'macd': {'1h': 150, '2h': 150, '4h': 150, '6h': 150, '12h': 150, '1d': 200, '1w': 200},
    'adx': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'aroon': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'atr': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'bbands': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 120, '1d': 150, '1w': 150},
    'bbwidth': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 120, '1d': 150, '1w': 150},
    'keltner': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'donchian': {'1h': 100, '2h': 100, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'obv': {'1h': 80, '2h': 80, '4h': 100, '6h': 100, '12h': 100, '1d': 100, '1w': 100},
    'vwap': {'1h': 120, '2h': 120, '4h': 120, '6h': 100, '12h': 100, '1d': 100, '1w': 100},  # Note: None converted to 100
    'trix': {'1h': 100, '2h': 100, '4h': 100, '6h': 120, '12h': 120, '1d': 120, '1w': 120},
    'psar': {'1h': 60, '2h': 60, '4h': 80, '6h': 80, '12h': 100, '1d': 100, '1w': 100},
    'roc': {'1h': 80, '2h': 80, '4h': 60, '6h': 60, '12h': 60, '1d': 60, '1w': 60},
    'vortex': {'1h': 80, '2h': 80, '4h': 80, '6h': 80, '12h': 80, '1d': 80, '1w': 80}
}


def test_individual_limits():
    """Test each indicator×timeframe combination matches research."""
    print("=== Testing Individual Limits (21 indicators × 7 timeframes = 147 combinations) ===")

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for indicator in ALL_INDICATORS:
        for timeframe in ALL_TIMEFRAMES:
            total_tests += 1
            actual = get_smart_limit(indicator, timeframe)
            expected = EXPECTED_LIMITS[indicator][timeframe]

            if actual == expected:
                passed_tests += 1
                print(f"✅ {indicator:12} {timeframe:3} -> {actual:3} candles")
            else:
                failed_tests.append((indicator, timeframe, expected, actual))
                print(f"❌ {indicator:12} {timeframe:3} -> {actual:3} candles (expected {expected})")

    print(f"\n=== Individual Limits Summary ===")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print(f"\nFailed tests:")
        for indicator, timeframe, expected, actual in failed_tests:
            print(f"  {indicator} {timeframe}: expected {expected}, got {actual}")

    return len(failed_tests) == 0


def test_batch_limits():
    """Test batch limit calculation."""
    print("\n=== Testing Batch Limits ===")

    test_cases = [
        # Single indicators
        (['rsi'], '1h', 100),
        (['macd'], '1d', 200),
        (['psar'], '1h', 60),

        # Mixed batches - should use max
        (['rsi', 'macd'], '1h', 150),  # max(100, 150) = 150
        (['psar', 'rsi', 'macd'], '1h', 150),  # max(60, 100, 150) = 150
        (['bbands', 'bbwidth'], '1d', 150),  # max(150, 150) = 150

        # Different timeframes
        (['rsi', 'macd'], '1d', 200),  # max(100, 200) = 200
        (['stochastic', 'williams_r'], '1h', 80),  # max(80, 80) = 80
    ]

    passed = 0
    for indicators, timeframe, expected in test_cases:
        actual = get_batch_limit(indicators, timeframe)
        if actual == expected:
            print(f"✅ {indicators} on {timeframe}: {actual} candles")
            passed += 1
        else:
            print(f"❌ {indicators} on {timeframe}: got {actual}, expected {expected}")

    print(f"\nBatch tests: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_aliases():
    """Test indicator name aliases work correctly."""
    print("\n=== Testing Aliases ===")

    alias_tests = [
        ('bollinger_bands', 'bbands'),
        ('bb', 'bbands'),
        ('bb_width', 'bbwidth'),
        ('parabolic_sar', 'psar'),
        ('sar', 'psar'),
        ('rate_of_change', 'roc'),
        ('dc', 'donchian'),
        ('kc', 'keltner')
    ]

    passed = 0
    for alias, canonical in alias_tests:
        alias_result = get_smart_limit(alias, '1h')
        canonical_result = get_smart_limit(canonical, '1h')

        if alias_result == canonical_result:
            print(f"✅ {alias} -> {canonical}: {alias_result} candles")
            passed += 1
        else:
            print(f"❌ {alias} -> {canonical}: {alias_result} vs {canonical_result}")

    print(f"\nAlias tests: {passed}/{len(alias_tests)} passed")
    return passed == len(alias_tests)


def test_efficiency_gains():
    """Test efficiency calculations."""
    print("\n=== Testing Efficiency Gains ===")

    from extraction.v2.smart_limits import get_efficiency_report

    test_cases = [
        (['psar'], '1h'),      # 70% reduction (60 vs 200)
        (['rsi'], '1h'),       # 50% reduction (100 vs 200)
        (['macd'], '1d'),      # 0% reduction (200 vs 200)
        (['rsi', 'macd'], '1h') # 25% reduction (150 vs 200)
    ]

    for indicators, timeframe in test_cases:
        report = get_efficiency_report(indicators, timeframe)
        print(f"📊 {indicators} on {timeframe}:")
        print(f"   Smart limit: {report['smart_limit']} candles")
        print(f"   Savings: {report['candles_saved']} candles ({report['percent_reduction']}%)")


async def test_extraction_engine_integration():
    """Test integration with actual extraction engine."""
    print("\n=== Testing Extraction Engine Integration ===")

    try:
        from extraction.v2.extraction_engine import ExtractionEngineV2

        engine = ExtractionEngineV2()

        # Test a few key combinations
        test_cases = [
            (['rsi'], '1h', 100),
            (['macd'], '1d', 200),
            (['psar'], '1h', 60),
            (['rsi', 'macd'], '1h', 150)
        ]

        passed = 0
        for indicators, timeframe, expected_limit in test_cases:
            try:
                result = await engine.extract_for_symbol('BTC/USDT', indicators, timeframe)
                if result['status'] == 'success':
                    actual_limit = result['result']['limit_used']
                    if actual_limit == expected_limit:
                        print(f"✅ Engine test {indicators} {timeframe}: {actual_limit} candles")
                        passed += 1
                    else:
                        print(f"❌ Engine test {indicators} {timeframe}: got {actual_limit}, expected {expected_limit}")
                else:
                    print(f"❌ Engine test {indicators} {timeframe}: extraction failed")
            except Exception as e:
                print(f"❌ Engine test {indicators} {timeframe}: {str(e)}")

        print(f"\nEngine integration tests: {passed}/{len(test_cases)} passed")
        return passed == len(test_cases)

    except Exception as e:
        print(f"❌ Cannot test extraction engine: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("🧪 COMPREHENSIVE SMART LIMITS TEST")
    print("=" * 50)

    # Test individual limits
    individual_pass = test_individual_limits()

    # Test batch calculations
    batch_pass = test_batch_limits()

    # Test aliases
    alias_pass = test_aliases()

    # Test efficiency reporting
    test_efficiency_gains()

    # Test extraction engine integration
    engine_pass = asyncio.run(test_extraction_engine_integration())

    # Final summary
    print(f"\n🏁 FINAL RESULTS")
    print("=" * 30)
    print(f"Individual limits: {'✅ PASS' if individual_pass else '❌ FAIL'}")
    print(f"Batch limits: {'✅ PASS' if batch_pass else '❌ FAIL'}")
    print(f"Aliases: {'✅ PASS' if alias_pass else '❌ FAIL'}")
    print(f"Engine integration: {'✅ PASS' if engine_pass else '❌ FAIL'}")

    all_pass = individual_pass and batch_pass and alias_pass and engine_pass
    print(f"\nOVERALL: {'🎉 ALL TESTS PASSED' if all_pass else '💥 SOME TESTS FAILED'}")

    return all_pass


if __name__ == "__main__":
    main()