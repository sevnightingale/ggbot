"""
Integration test for Universal Data Layer with Preprocessor system.

Tests the critical integration: MarketIntelligence → OHLCV data → Preprocessors → Technical indicators

This validates that MarketIntelligence can replace HummingbotDataClient in the actual
extraction pipeline without breaking indicator calculations.
"""

import asyncio
import sys
import os
import pandas as pd
import pandas_ta as ta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from market_intelligence.gateway import MarketIntelligence
from market_intelligence.types import QueryFormat
from extraction.v2.preprocessors.rsi import RSIPreprocessor
from extraction.v2.preprocessors.macd import MACDPreprocessor
from extraction.v2.preprocessors.bbands import BollingerBandsPreprocessor
from core.common.logger import logger


async def test_ohlcv_to_indicators():
    """
    Test 1: Fetch OHLCV → Calculate indicators with pandas-ta → Verify data structure.

    This mimics what ExtractionEngine does with raw OHLCV data.
    """
    print("\n" + "="*80)
    print("Test 1: OHLCV → Technical Indicators (pandas-ta)")
    print("="*80)

    intelligence = MarketIntelligence()

    try:
        # Query OHLCV data
        response = await intelligence.query(
            data_type='ohlcv',
            params={
                'symbol': 'BTC/USDT',
                'timeframe': '1h',
                'limit': 200
            },
            format=QueryFormat.RAW
        )

        df = response.data

        print(f"\n✅ Got OHLCV data: {len(df)} candles")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Sample row:\n{df.iloc[-1]}")

        # Verify required columns for technical analysis
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in df.columns]
        assert not missing, f"Missing required columns: {missing}"

        # Calculate basic technical indicators using pandas-ta
        df['rsi'] = ta.rsi(df['close'], length=14)
        macd_result = ta.macd(df['close'])
        df['macd'] = macd_result['MACD_12_26_9']
        df['macd_signal'] = macd_result['MACDs_12_26_9']
        df['macd_histogram'] = macd_result['MACDh_12_26_9']

        # Bollinger Bands
        bbands_result = ta.bbands(df['close'], length=20, std=2)
        df['bb_upper'] = bbands_result['BBU_20_2.0']
        df['bb_middle'] = bbands_result['BBM_20_2.0']
        df['bb_lower'] = bbands_result['BBL_20_2.0']

        print(f"\n✅ Calculated indicators successfully")
        print(f"   RSI: {df['rsi'].iloc[-1]:.2f}")
        print(f"   MACD: {df['macd'].iloc[-1]:.4f}")
        print(f"   BB Upper: {df['bb_upper'].iloc[-1]:.2f}")

        # Verify no NaN in recent values (after warmup period)
        recent_rsi = df['rsi'].iloc[-10:]
        assert not recent_rsi.isna().all(), "RSI should have valid values"

        print("\n✅ Test 1 PASSED: OHLCV data works with pandas-ta indicators")
        return True, df

    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None

    finally:
        await intelligence.close()


async def test_indicators_to_preprocessors(df_with_indicators):
    """
    Test 2: Indicator data → Preprocessors → Rich market analysis.

    This validates that preprocessors can process indicators calculated from
    MarketIntelligence OHLCV data.
    """
    print("\n" + "="*80)
    print("Test 2: Technical Indicators → Preprocessors → Market Analysis")
    print("="*80)

    if df_with_indicators is None:
        print("❌ Skipping Test 2: No indicator data from Test 1")
        return False

    df = df_with_indicators

    try:
        # Test RSI Preprocessor
        print("\n--- Testing RSI Preprocessor ---")
        rsi_preprocessor = RSIPreprocessor()
        rsi_analysis = rsi_preprocessor.preprocess(
            rsi_values=df['rsi'],
            prices=df['close'],
            period=14
        )

        print(f"✅ RSI Preprocessor output:")
        print(f"   Indicator: {rsi_analysis.get('indicator')}")
        print(f"   Current value: {rsi_analysis.get('current', {}).get('value')}")
        print(f"   Trend: {rsi_analysis.get('context', {}).get('trend', {}).get('direction')}")
        print(f"   Zone: {rsi_analysis.get('levels', {}).get('overbought', {}).get('status')}")
        print(f"   Patterns: {list(rsi_analysis.get('patterns', {}).keys())}")
        print(f"   Summary: {rsi_analysis.get('summary')}")

        # Validate RSI output structure
        assert rsi_analysis.get('indicator') == 'RSI', "Should have indicator name"
        assert 'current' in rsi_analysis, "Should have current section"
        assert 'context' in rsi_analysis, "Should have context section"
        assert 'levels' in rsi_analysis, "Should have levels section"
        assert 'patterns' in rsi_analysis, "Should have patterns section"
        assert 'summary' in rsi_analysis, "Should have summary"
        assert 'signals' not in rsi_analysis, "Should NOT have signals (analysis only)"
        assert 'confidence' not in rsi_analysis, "Should NOT have confidence scores"

        # Test MACD Preprocessor
        print("\n--- Testing MACD Preprocessor ---")
        macd_preprocessor = MACDPreprocessor()
        macd_analysis = macd_preprocessor.preprocess(
            macd_line=df['macd'],
            signal_line=df['macd_signal'],
            histogram=df['macd_histogram'],
            prices=df['close']
        )

        print(f"✅ MACD Preprocessor output:")
        print(f"   Indicator: {macd_analysis.get('indicator')}")
        print(f"   Histogram: {macd_analysis.get('current', {}).get('histogram')}")
        print(f"   Crossover state: {macd_analysis.get('levels', {}).get('crossover_state')}")
        print(f"   Summary: {macd_analysis.get('summary')}")

        # Validate MACD output structure
        assert macd_analysis.get('indicator') == 'MACD', "Should have indicator name"
        assert 'current' in macd_analysis, "Should have current section"
        assert 'summary' in macd_analysis, "Should have summary"

        # Test Bollinger Bands Preprocessor
        print("\n--- Testing Bollinger Bands Preprocessor ---")
        bbands_preprocessor = BollingerBandsPreprocessor()
        bbands_analysis = bbands_preprocessor.preprocess(
            upper_band=df['bb_upper'],
            middle_band=df['bb_middle'],
            lower_band=df['bb_lower'],
            prices=df['close']
        )

        print(f"✅ Bollinger Bands Preprocessor output:")
        print(f"   Indicator: {bbands_analysis.get('indicator')}")
        print(f"   Position: {bbands_analysis.get('context', {}).get('position_in_bands')}")
        print(f"   Bandwidth: {bbands_analysis.get('context', {}).get('bandwidth')}")
        print(f"   Summary: {bbands_analysis.get('summary')}")

        # Validate BB output structure
        assert bbands_analysis.get('indicator') == 'Bollinger_Bands', "Should have indicator name"
        assert 'context' in bbands_analysis, "Should have context section"
        assert 'summary' in bbands_analysis, "Should have summary"

        print("\n✅ Test 2 PASSED: All preprocessors work with MarketIntelligence data")
        return True

    except Exception as e:
        print(f"\n❌ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_end_to_end_pipeline():
    """
    Test 3: Complete end-to-end pipeline validation.

    Query → Indicators → Preprocessors in one flow, simulating real ExtractionEngine behavior.
    """
    print("\n" + "="*80)
    print("Test 3: End-to-End Pipeline (Query → Indicators → Preprocessors)")
    print("="*80)

    intelligence = MarketIntelligence()

    try:
        # Step 1: Query OHLCV
        print("\n[1/3] Querying OHLCV data...")
        response = await intelligence.query(
            data_type='ohlcv',
            params={'symbol': 'ETH/USDT', 'timeframe': '15m', 'limit': 200},
            format=QueryFormat.RAW
        )
        df = response.data
        print(f"   ✅ Got {len(df)} candles")

        # Step 2: Calculate indicators
        print("\n[2/3] Calculating technical indicators...")
        df['rsi'] = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'])
        df['macd'] = macd['MACD_12_26_9']
        df['macd_signal'] = macd['MACDs_12_26_9']
        df['macd_histogram'] = macd['MACDh_12_26_9']
        print(f"   ✅ Calculated RSI and MACD")

        # Step 3: Preprocess indicators
        print("\n[3/3] Running preprocessors...")
        rsi_preprocessor = RSIPreprocessor()
        rsi_result = rsi_preprocessor.preprocess(df['rsi'], df['close'])

        macd_preprocessor = MACDPreprocessor()
        macd_result = macd_preprocessor.preprocess(
            df['macd'], df['macd_signal'], df['macd_histogram'], df['close']
        )
        print(f"   ✅ Preprocessed RSI and MACD")

        # Validate complete output
        analysis_output = {
            'symbol': 'ETH/USDT',
            'timeframe': '15m',
            'candle_count': len(df),
            'indicators': {
                'rsi': rsi_result,
                'macd': macd_result
            },
            'source': response.source,
            'from_cache': response.from_cache,
            'latency_ms': response.latency_ms
        }

        print(f"\n✅ Complete analysis output structure:")
        print(f"   Symbol: {analysis_output['symbol']}")
        print(f"   Timeframe: {analysis_output['timeframe']}")
        print(f"   Candles: {analysis_output['candle_count']}")
        print(f"   Source: {analysis_output['source']}")
        print(f"   From cache: {analysis_output['from_cache']}")
        print(f"   Latency: {analysis_output['latency_ms']:.0f}ms")
        print(f"   RSI Summary: {analysis_output['indicators']['rsi']['summary']}")
        print(f"   MACD Summary: {analysis_output['indicators']['macd']['summary']}")

        # This is the format ExtractionEngine would store in database
        assert analysis_output['indicators']['rsi']['indicator'] == 'RSI'
        assert analysis_output['indicators']['macd']['indicator'] == 'MACD'
        assert 'summary' in analysis_output['indicators']['rsi']
        assert 'summary' in analysis_output['indicators']['macd']

        print("\n✅ Test 3 PASSED: End-to-end pipeline working perfectly")
        return True

    except Exception as e:
        print(f"\n❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await intelligence.close()


async def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("UNIVERSAL DATA LAYER → PREPROCESSOR INTEGRATION TESTS")
    print("="*80)

    results = []

    # Test 1: OHLCV → Indicators
    test1_passed, df_with_indicators = await test_ohlcv_to_indicators()
    results.append(test1_passed)

    # Test 2: Indicators → Preprocessors
    if test1_passed:
        test2_passed = await test_indicators_to_preprocessors(df_with_indicators)
        results.append(test2_passed)
    else:
        results.append(False)

    # Test 3: End-to-End Pipeline
    test3_passed = await test_end_to_end_pipeline()
    results.append(test3_passed)

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"\n  Passed: {passed}/{total}")
    print(f"  Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ VALIDATED: MarketIntelligence data is compatible with Preprocessors")
        print("✅ READY: Can replace HummingbotDataClient in ExtractionEngine")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\n❌ BLOCKED: Integration issues must be resolved before migration")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
