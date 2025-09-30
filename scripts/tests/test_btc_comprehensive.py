"""
BTC Comprehensive Test - All Timeframes & All Indicators

Tests all 21 preprocessors across all 7 timeframes for BTC/USDT only.
Outputs detailed results to a human-readable file for review.

Usage:
    python -m pytest tests/test_btc_comprehensive.py::test_btc_all_indicators_all_timeframes -v -s

Or run directly:
    python tests/test_btc_comprehensive.py
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any
import pandas as pd

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from extraction.v2.extraction_engine import ExtractionEngineV2


async def test_btc_comprehensive():
    """
    Comprehensive test of all 21 indicators across all 7 timeframes for BTC/USDT.
    Saves detailed results to a human-readable file.
    """

    print("🚀 Starting BTC Comprehensive Test")
    print("Testing all 21 indicators across all 7 timeframes for BTC/USDT")
    print("=" * 80)

    # Test configuration
    symbol = "BTC/USDT"
    timeframes = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
    all_indicators = [
        "rsi", "bbands", "adx", "aroon", "atr", "bbwidth", "cci", "donchian",
        "ema", "keltner", "macd", "mfi", "obv", "psar", "roc", "sma",
        "stochastic", "trix", "vortex", "vwap", "williams_r"
    ]

    # Initialize extraction engine
    engine = ExtractionEngineV2(
        user_id=DEFAULT_USER_ID,
        use_advanced_preprocessing=True,
        use_database_storage=False,  # Don't store during testing
        use_file_storage=False       # Don't store during testing
    )

    # Results collection
    test_results = {
        "test_info": {
            "symbol": symbol,
            "timeframes": timeframes,
            "indicators": all_indicators,
            "total_combinations": len(timeframes) * len(all_indicators),
            "test_start": datetime.now(timezone.utc).isoformat(),
            "test_duration_seconds": 0
        },
        "results_by_timeframe": {},
        "summary": {
            "successful_tests": 0,
            "failed_tests": 0,
            "total_tests": 0
        }
    }

    start_time = time.time()

    # Test each timeframe
    for tf_idx, timeframe in enumerate(timeframes):
        print(f"\n📊 Testing timeframe {tf_idx + 1}/{len(timeframes)}: {timeframe}")
        print("-" * 50)

        timeframe_results = {
            "timeframe": timeframe,
            "indicators": {},
            "summary": {
                "successful": 0,
                "failed": 0,
                "total": len(all_indicators)
            }
        }

        # Test each indicator for this timeframe
        for ind_idx, indicator in enumerate(all_indicators):
            print(f"  {ind_idx + 1:2d}. {indicator:12s}", end=" ")

            indicator_start = time.time()

            try:
                # Extract single indicator
                result = await engine.extract_for_symbol(
                    symbol=symbol,
                    indicators=[indicator],
                    timeframe=timeframe,
                    limit=200,  # Good amount of data for analysis
                    connector="kucoin"
                )

                execution_time = time.time() - indicator_start

                if result.get("status") == "success":
                    print(f"✅ {execution_time:.3f}s")

                    # Extract the indicator result
                    indicator_data = result["result"]["indicators"].get(indicator, {})

                    timeframe_results["indicators"][indicator] = {
                        "status": "success",
                        "execution_time": round(execution_time, 3),
                        "data": indicator_data
                    }

                    timeframe_results["summary"]["successful"] += 1
                    test_results["summary"]["successful_tests"] += 1

                else:
                    print(f"❌ {execution_time:.3f}s - {result.get('error', 'Unknown error')[:50]}")

                    timeframe_results["indicators"][indicator] = {
                        "status": "failed",
                        "execution_time": round(execution_time, 3),
                        "error": result.get("error", "Unknown error")
                    }

                    timeframe_results["summary"]["failed"] += 1
                    test_results["summary"]["failed_tests"] += 1

            except Exception as e:
                execution_time = time.time() - indicator_start
                print(f"💥 {execution_time:.3f}s - Exception: {str(e)[:50]}")

                timeframe_results["indicators"][indicator] = {
                    "status": "exception",
                    "execution_time": round(execution_time, 3),
                    "error": f"Exception: {str(e)}"
                }

                timeframe_results["summary"]["failed"] += 1
                test_results["summary"]["failed_tests"] += 1

            test_results["summary"]["total_tests"] += 1

        # Add timeframe results
        test_results["results_by_timeframe"][timeframe] = timeframe_results

        # Print timeframe summary
        tf_success_rate = (timeframe_results["summary"]["successful"] / len(all_indicators)) * 100
        print(f"  📈 {timeframe} Summary: {timeframe_results['summary']['successful']}/{len(all_indicators)} successful ({tf_success_rate:.1f}%)")

    # Finalize test
    total_duration = time.time() - start_time
    test_results["test_info"]["test_duration_seconds"] = round(total_duration, 1)
    test_results["test_info"]["test_end"] = datetime.now(timezone.utc).isoformat()

    # Calculate overall success rate
    total_tests = test_results["summary"]["total_tests"]
    if total_tests > 0:
        overall_success_rate = (test_results["summary"]["successful_tests"] / total_tests) * 100
        test_results["summary"]["overall_success_rate"] = round(overall_success_rate, 2)

    # Save results to file
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Save detailed JSON
    json_filename = f"tests/reports/btc_comprehensive_{timestamp}.json"
    try:
        import os
        os.makedirs("tests/reports", exist_ok=True)

        with open(json_filename, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        print(f"\n📄 Detailed JSON saved: {json_filename}")
    except Exception as e:
        print(f"⚠️ Could not save JSON: {e}")

    # Save human-readable report
    markdown_filename = f"tests/reports/btc_comprehensive_{timestamp}.md"
    try:
        save_human_readable_report(test_results, markdown_filename)
        print(f"📄 Human-readable report saved: {markdown_filename}")
    except Exception as e:
        print(f"⚠️ Could not save markdown: {e}")

    # Print final summary
    print("\n" + "=" * 80)
    print("🎉 BTC COMPREHENSIVE TEST COMPLETE")
    print("=" * 80)
    print(f"🎯 Overall Success Rate: {test_results['summary'].get('overall_success_rate', 0):.2f}%")
    print(f"✅ Successful: {test_results['summary']['successful_tests']}")
    print(f"❌ Failed: {test_results['summary']['failed_tests']}")
    print(f"📈 Total Tests: {test_results['summary']['total_tests']}")
    print(f"⏱️ Total Duration: {total_duration:.1f} seconds")

    return test_results


def save_human_readable_report(test_results: Dict[str, Any], filename: str):
    """Save a human-readable markdown report of the BTC test results."""

    with open(filename, 'w') as f:
        # Header
        test_info = test_results["test_info"]
        summary = test_results["summary"]

        f.write("# BTC Comprehensive Test Report\n\n")
        f.write(f"**Symbol:** {test_info['symbol']}\n")
        f.write(f"**Test Date:** {test_info['test_start']}\n")
        f.write(f"**Duration:** {test_info['test_duration_seconds']} seconds\n")
        f.write(f"**Total Combinations:** {test_info['total_combinations']}\n\n")

        # Overall Summary
        f.write("## 📊 Overall Results\n\n")
        f.write(f"- **Success Rate:** {summary.get('overall_success_rate', 0):.2f}%\n")
        f.write(f"- **Successful Tests:** {summary['successful_tests']}\n")
        f.write(f"- **Failed Tests:** {summary['failed_tests']}\n")
        f.write(f"- **Total Tests:** {summary['total_tests']}\n\n")

        # Results by Timeframe
        f.write("## 📈 Results by Timeframe\n\n")

        for timeframe, tf_data in test_results["results_by_timeframe"].items():
            tf_summary = tf_data["summary"]
            success_rate = (tf_summary["successful"] / tf_summary["total"]) * 100 if tf_summary["total"] > 0 else 0

            f.write(f"### {timeframe.upper()} Timeframe\n")
            f.write(f"**Success Rate:** {success_rate:.1f}% ({tf_summary['successful']}/{tf_summary['total']})\n\n")

            # Indicator results table
            f.write("| Indicator | Status | Execution Time | Notes |\n")
            f.write("|-----------|--------|----------------|-------|\n")

            for indicator, ind_data in tf_data["indicators"].items():
                status_emoji = "✅" if ind_data["status"] == "success" else "❌"
                execution_time = f"{ind_data['execution_time']:.3f}s"
                notes = ""

                if ind_data["status"] != "success":
                    error_msg = ind_data.get("error", "Unknown error")
                    notes = error_msg[:50] + "..." if len(error_msg) > 50 else error_msg
                else:
                    # Check if we have useful data
                    indicator_data = ind_data.get("data", {})
                    if "summary" in indicator_data:
                        summary_text = indicator_data["summary"]
                        notes = summary_text[:40] + "..." if len(summary_text) > 40 else summary_text

                f.write(f"| {indicator} | {status_emoji} | {execution_time} | {notes} |\n")

            f.write("\n")

        # Performance Analysis
        f.write("## ⚡ Performance Analysis\n\n")

        # Collect all execution times
        indicator_times = {}
        for tf_data in test_results["results_by_timeframe"].values():
            for indicator, ind_data in tf_data["indicators"].items():
                if ind_data["status"] == "success":
                    if indicator not in indicator_times:
                        indicator_times[indicator] = []
                    indicator_times[indicator].append(ind_data["execution_time"])

        # Calculate averages
        avg_times = []
        for indicator, times in indicator_times.items():
            avg_time = sum(times) / len(times) if times else 0
            avg_times.append((indicator, avg_time, len(times)))

        avg_times.sort(key=lambda x: x[1], reverse=True)

        f.write("### Slowest Indicators (Average Execution Time)\n")
        for indicator, avg_time, count in avg_times[:10]:
            f.write(f"- **{indicator}:** {avg_time:.3f}s average ({count} timeframes)\n")

        f.write("\n### Fastest Indicators (Average Execution Time)\n")
        for indicator, avg_time, count in avg_times[-10:]:
            f.write(f"- **{indicator}:** {avg_time:.3f}s average ({count} timeframes)\n")

        # Timeframe Performance
        f.write("\n### Performance by Timeframe\n")
        timeframe_performance = []
        for timeframe, tf_data in test_results["results_by_timeframe"].items():
            total_time = sum(ind_data["execution_time"] for ind_data in tf_data["indicators"].values())
            avg_time = total_time / len(tf_data["indicators"]) if tf_data["indicators"] else 0
            timeframe_performance.append((timeframe, total_time, avg_time))

        timeframe_performance.sort(key=lambda x: x[2], reverse=True)

        f.write("| Timeframe | Total Time | Avg per Indicator | Status |\n")
        f.write("|-----------|------------|-------------------|--------|\n")
        for timeframe, total_time, avg_time in timeframe_performance:
            status = "🟢" if avg_time < 1.0 else "🟡" if avg_time < 3.0 else "🔴"
            f.write(f"| {timeframe} | {total_time:.1f}s | {avg_time:.3f}s | {status} |\n")

        # FULL INDICATOR OUTPUT - Complete preprocessor results
        f.write("\n## 🔍 COMPLETE INDICATOR OUTPUT\n\n")
        f.write("Full preprocessor output for ALL indicators across ALL timeframes:\n\n")

        for timeframe, tf_data in test_results["results_by_timeframe"].items():
            f.write(f"# {timeframe.upper()} TIMEFRAME\n\n")

            for indicator, ind_data in tf_data["indicators"].items():
                f.write(f"## {indicator.upper()}\n")

                if ind_data.get("status") == "success":
                    # Write the COMPLETE preprocessor output
                    indicator_result = ind_data.get("data", {})

                    f.write("```json\n")
                    f.write(json.dumps(indicator_result, indent=2, default=str))
                    f.write("\n```\n\n")

                    # Also write a formatted version for readability
                    f.write("**Human-readable format:**\n")
                    f.write(f"- **Indicator:** {indicator_result.get('indicator', 'N/A')}\n")

                    current = indicator_result.get("current", {})
                    if current:
                        f.write(f"- **Current Value:** {current}\n")

                    summary = indicator_result.get("summary", "No summary")
                    f.write(f"- **Summary:** {summary}\n")

                    context = indicator_result.get("context", {})
                    if context:
                        f.write(f"- **Context:** {context}\n")

                    levels = indicator_result.get("levels", {})
                    if levels:
                        f.write(f"- **Levels:** {levels}\n")

                    patterns = indicator_result.get("patterns", {})
                    if patterns:
                        f.write(f"- **Patterns:** {patterns}\n")

                    evidence = indicator_result.get("evidence", {})
                    if evidence:
                        f.write(f"- **Evidence:** {evidence}\n")

                else:
                    f.write(f"**STATUS:** {ind_data.get('status', 'unknown').upper()}\n")
                    f.write(f"**ERROR:** {ind_data.get('error', 'Unknown error')}\n")

                f.write("\n---\n\n")

        f.write("\n---\n")
        f.write("*Generated by ggbots V2 Extraction System*\n")


def test_btc_all_indicators_all_timeframes():
    """Pytest-compatible test wrapper."""
    result = asyncio.run(test_btc_comprehensive())

    # Assert reasonable success rate
    success_rate = result["summary"].get("overall_success_rate", 0)
    assert success_rate >= 80.0, f"BTC test success rate too low: {success_rate:.2f}%"

    print(f"✅ BTC comprehensive test PASSED with {success_rate:.2f}% success rate!")


if __name__ == "__main__":
    # Allow running directly
    asyncio.run(test_btc_comprehensive())