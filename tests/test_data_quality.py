"""
Data Quality Test - Comprehensive Market Data Point Validation

This script calls ALL market data points (technical indicators + market intelligence)
and outputs results for manual review. Use to verify data quality and catch issues.

Run: cd /home/sev/ggbot && source .venv/bin/activate && python tests/test_data_quality.py
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.common.logger import logger

# ============================================================================
# CONFIGURATION
# ============================================================================

TEST_SYMBOL = "BTC/USDT"
TEST_TIMEFRAME = "4h"
TEST_CANDLE_LIMIT = 200

# All 21 technical indicators
TECHNICAL_INDICATORS = [
    "rsi", "macd", "stochastic", "williams_r", "cci", "mfi",
    "adx", "psar", "aroon", "atr", "bbands", "obv",
    "sma", "ema", "roc", "vwap", "trix", "vortex",
    "bbwidth", "keltner", "donchian"
]

# Some indicators have different input vs output names
INDICATOR_ALIASES = {
    "bbands": "bollinger_bands"  # Input as bbands, output as bollinger_bands
}

# All 11 market intelligence data points (excluding legacy aliases)
MARKET_INTEL_DATA_POINTS = [
    ("trading_signals", "ggshot"),
    ("derivatives_leverage", "btc_funding_rate"),
    ("derivatives_leverage", "eth_funding_rate"),
    ("macro_economics", "vix"),
    ("macro_economics", "dxy"),
    ("macro_economics", "cpi"),
    ("macro_economics", "nfp"),
    ("onchain_analytics", "btc_tvl"),
    ("onchain_analytics", "whale_activity"),
    ("sentiment_social", "twitter_sentiment"),
    ("news_regulatory", "crypto_news"),
]


# ============================================================================
# TECHNICAL INDICATORS TEST
# ============================================================================

async def test_technical_indicators() -> Dict[str, Any]:
    """
    Test all 21 technical indicators using ExtractionEngineV2.

    Returns dict with results for each indicator.
    """
    from extraction.v2.extraction_engine import ExtractionEngineV2

    print("\n" + "="*60)
    print("TECHNICAL INDICATORS TEST")
    print("="*60)

    results = {
        "test_type": "technical_indicators",
        "symbol": TEST_SYMBOL,
        "timeframe": TEST_TIMEFRAME,
        "candles_requested": TEST_CANDLE_LIMIT,
        "timestamp": datetime.utcnow().isoformat(),
        "indicators": {},
        "summary": {
            "total": len(TECHNICAL_INDICATORS),
            "success": 0,
            "errors": 0,
            "error_list": []
        }
    }

    # Initialize engine (no storage for test)
    engine = ExtractionEngineV2(
        user_id="test_user",
        use_advanced_preprocessing=True,
        use_database_storage=False,
        use_file_storage=False
    )

    try:
        # Extract all indicators at once
        print(f"\nFetching {TEST_CANDLE_LIMIT} candles for {TEST_SYMBOL} ({TEST_TIMEFRAME})...")

        extraction_result = await engine.extract_for_symbol(
            symbol=TEST_SYMBOL,
            indicators=TECHNICAL_INDICATORS,
            timeframe=TEST_TIMEFRAME,
            limit=TEST_CANDLE_LIMIT
        )

        # Engine returns {status, result} - extract inner result
        inner_result = extraction_result.get("result", extraction_result)

        # Store OHLCV summary
        results["ohlcv_summary"] = inner_result.get("ohlcv_summary", {})
        results["candles_received"] = inner_result.get("data_points", 0)

        # Process each indicator result
        indicator_data = inner_result.get("indicators", {})

        for indicator in TECHNICAL_INDICATORS:
            # Check both input name and alias
            result_key = INDICATOR_ALIASES.get(indicator, indicator)
            ind_result = indicator_data.get(result_key) or indicator_data.get(indicator)

            if ind_result:

                # Check for errors
                if isinstance(ind_result, dict) and "error" in ind_result:
                    results["indicators"][indicator] = {
                        "status": "ERROR",
                        "error": ind_result.get("error"),
                        "message": ind_result.get("message", "Unknown error")
                    }
                    results["summary"]["errors"] += 1
                    results["summary"]["error_list"].append(f"{indicator}: {ind_result.get('error')}")
                    print(f"  ❌ {indicator}: ERROR - {ind_result.get('error')}")
                else:
                    results["indicators"][indicator] = {
                        "status": "OK",
                        "data": ind_result
                    }
                    results["summary"]["success"] += 1

                    # Extract key value for display
                    if isinstance(ind_result, dict):
                        current = ind_result.get("current", {})
                        if isinstance(current, dict):
                            value = current.get("value", "N/A")
                        else:
                            value = current
                        print(f"  ✅ {indicator}: {value}")
                    else:
                        print(f"  ✅ {indicator}: {ind_result}")
            else:
                results["indicators"][indicator] = {
                    "status": "MISSING",
                    "error": "Indicator not in results"
                }
                results["summary"]["errors"] += 1
                results["summary"]["error_list"].append(f"{indicator}: missing from results")
                print(f"  ⚠️ {indicator}: MISSING from results")

        print(f"\n✅ Technical Indicators: {results['summary']['success']}/{results['summary']['total']} succeeded")

    except Exception as e:
        print(f"\n❌ FATAL ERROR in technical indicators: {e}")
        results["fatal_error"] = str(e)
        import traceback
        results["traceback"] = traceback.format_exc()

    finally:
        await engine.cleanup()

    return results


# ============================================================================
# MARKET INTELLIGENCE TEST
# ============================================================================

async def test_market_intelligence() -> Dict[str, Any]:
    """
    Test all 11 market intelligence data points using MarketIntelligence gateway.

    Returns dict with results for each data point.
    """
    from market_intelligence.gateway import MarketIntelligence
    from market_intelligence.types import QueryFormat
    from market_intelligence.catalog_mapping import CATALOG_MAPPING

    print("\n" + "="*60)
    print("MARKET INTELLIGENCE TEST")
    print("="*60)

    results = {
        "test_type": "market_intelligence",
        "symbol": TEST_SYMBOL,
        "timestamp": datetime.utcnow().isoformat(),
        "data_points": {},
        "summary": {
            "total": len(MARKET_INTEL_DATA_POINTS),
            "success": 0,
            "errors": 0,
            "error_list": []
        }
    }

    gateway = MarketIntelligence()

    try:
        for source_name, point_name in MARKET_INTEL_DATA_POINTS:
            full_name = f"{source_name}.{point_name}"
            print(f"\n  Testing {full_name}...")

            # Get mapping
            mapping = CATALOG_MAPPING.get((source_name, point_name))

            if not mapping:
                results["data_points"][full_name] = {
                    "status": "ERROR",
                    "error": "No catalog mapping found"
                }
                results["summary"]["errors"] += 1
                results["summary"]["error_list"].append(f"{full_name}: no catalog mapping")
                print(f"    ❌ No catalog mapping")
                continue

            # Prepare params (replace {symbol} template)
            params = mapping['params_template'].copy()
            for key, value in params.items():
                if isinstance(value, str) and '{symbol}' in value:
                    params[key] = value.replace('{symbol}', TEST_SYMBOL)

            # Add symbol for cache key
            if 'symbol' not in params:
                params['symbol'] = TEST_SYMBOL

            try:
                # Query the gateway
                result = await gateway.query(
                    data_type=mapping['data_type'],
                    params=params,
                    format=QueryFormat.RAW,
                    cache_ttl_override=mapping.get('cache_ttl')
                )

                results["data_points"][full_name] = {
                    "status": "OK",
                    "source": result.source,
                    "latency_ms": result.latency_ms,
                    "from_cache": result.from_cache,
                    "data": result.data
                }
                results["summary"]["success"] += 1
                print(f"    ✅ OK ({result.source}, {result.latency_ms:.0f}ms, cached={result.from_cache})")

            except Exception as e:
                results["data_points"][full_name] = {
                    "status": "ERROR",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                results["summary"]["errors"] += 1
                results["summary"]["error_list"].append(f"{full_name}: {str(e)[:100]}")
                print(f"    ❌ ERROR: {str(e)[:80]}...")

        print(f"\n✅ Market Intelligence: {results['summary']['success']}/{results['summary']['total']} succeeded")

    except Exception as e:
        print(f"\n❌ FATAL ERROR in market intelligence: {e}")
        results["fatal_error"] = str(e)
        import traceback
        results["traceback"] = traceback.format_exc()

    finally:
        await gateway.close()

    return results


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all data quality tests and save results."""
    print("\n" + "="*60)
    print("DATA QUALITY TEST SUITE")
    print(f"Started: {datetime.utcnow().isoformat()}")
    print("="*60)

    all_results = {
        "test_run": datetime.utcnow().isoformat(),
        "test_symbol": TEST_SYMBOL,
        "test_timeframe": TEST_TIMEFRAME,
        "sections": {}
    }

    # Run technical indicators test
    tech_results = await test_technical_indicators()
    all_results["sections"]["technical_indicators"] = tech_results

    # Run market intelligence test
    intel_results = await test_market_intelligence()
    all_results["sections"]["market_intelligence"] = intel_results

    # Summary
    total_success = (
        tech_results["summary"]["success"] +
        intel_results["summary"]["success"]
    )
    total_tests = (
        tech_results["summary"]["total"] +
        intel_results["summary"]["total"]
    )
    total_errors = (
        tech_results["summary"]["errors"] +
        intel_results["summary"]["errors"]
    )

    all_results["overall_summary"] = {
        "total_data_points": total_tests,
        "successful": total_success,
        "errors": total_errors,
        "success_rate": f"{(total_success/total_tests)*100:.1f}%"
    }

    print("\n" + "="*60)
    print("OVERALL SUMMARY")
    print("="*60)
    print(f"Total Data Points: {total_tests}")
    print(f"Successful: {total_success}")
    print(f"Errors: {total_errors}")
    print(f"Success Rate: {(total_success/total_tests)*100:.1f}%")

    if total_errors > 0:
        print("\nError List:")
        for err in tech_results["summary"].get("error_list", []):
            print(f"  - {err}")
        for err in intel_results["summary"].get("error_list", []):
            print(f"  - {err}")

    # Save results to file
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data_quality_results.json"
    )

    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n📄 Results saved to: {output_path}")

    return all_results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
