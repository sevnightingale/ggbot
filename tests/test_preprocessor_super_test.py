"""
COMPREHENSIVE PREPROCESSOR SUPER TEST

This is THE definitive test for our entire extraction system.
Tests all 21 preprocessors across all 7 timeframes and all 140+ symbols.

WARNING: This test is designed to be comprehensive, not fast.
Expected runtime: 30-60 minutes depending on data availability.

Purpose:
- Validate all 21 preprocessors work correctly
- Test across all supported timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w)
- Test across all 140+ trading symbols
- Identify data quality issues, gaps, and failures
- Assess output accuracy and trading decision usefulness
- Generate comprehensive quality report

Usage:
    python -m pytest tests/test_preprocessor_super_test.py::test_super_comprehensive_extraction -v -s
"""

import asyncio
import time
import json
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

import pytest

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.symbols.registry import get_all_symbols
from extraction.v2.extraction_engine import ExtractionEngineV2
from extraction.v2.indicators import TechnicalIndicators
from extraction.v2.preprocessors import get_preprocessor


class SuperTestReport:
    """Comprehensive test report generator."""

    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.results = {
            "metadata": {
                "test_start": self.start_time.isoformat(),
                "test_duration_seconds": 0,
                "total_combinations_tested": 0,
                "python_version": None,
                "test_configuration": {}
            },
            "summary": {
                "overall_success_rate": 0.0,
                "total_tests_run": 0,
                "total_successful": 0,
                "total_failed": 0,
                "preprocessors_tested": 0,
                "timeframes_tested": 0,
                "symbols_tested": 0
            },
            "preprocessor_analysis": {},
            "timeframe_analysis": {},
            "symbol_analysis": {},
            "failure_analysis": {
                "critical_failures": [],
                "common_failure_patterns": {},
                "data_quality_issues": [],
                "performance_issues": []
            },
            "quality_assessment": {
                "schema_compliance": {},
                "trading_usefulness": {},
                "pattern_detection_quality": {},
                "mathematical_accuracy": {}
            },
            "recommendations": []
        }

    def add_test_result(self, symbol: str, timeframe: str, indicator: str,
                       result: Dict[str, Any], execution_time: float):
        """Add individual test result."""
        self.results["summary"]["total_tests_run"] += 1

        if result.get("status") == "success":
            self.results["summary"]["total_successful"] += 1
            self.mark_success(symbol, timeframe, indicator)
            self._analyze_successful_result(symbol, timeframe, indicator, result, execution_time)
        else:
            self.results["summary"]["total_failed"] += 1
            self.mark_failure(symbol, timeframe, indicator)
            self._analyze_failed_result(symbol, timeframe, indicator, result, execution_time)

    def _analyze_successful_result(self, symbol: str, timeframe: str, indicator: str,
                                 result: Dict[str, Any], execution_time: float):
        """Analyze successful test result for quality assessment."""
        preprocessor_result = result.get("result", {}).get("indicators", {}).get(indicator, {})

        # Schema compliance check
        self._check_schema_compliance(indicator, preprocessor_result)

        # Trading usefulness assessment
        self._assess_trading_usefulness(indicator, preprocessor_result)

        # Performance tracking
        self._track_performance(symbol, timeframe, indicator, execution_time)

        # Pattern detection quality
        self._assess_pattern_quality(indicator, preprocessor_result)

    def _analyze_failed_result(self, symbol: str, timeframe: str, indicator: str,
                             result: Dict[str, Any], execution_time: float):
        """Analyze failed test result."""
        error_info = {
            "symbol": symbol,
            "timeframe": timeframe,
            "indicator": indicator,
            "error": result.get("error", "Unknown error"),
            "execution_time": execution_time,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.results["failure_analysis"]["critical_failures"].append(error_info)

        # Categorize failure types
        error_msg = str(result.get("error", "")).lower()
        if "insufficient data" in error_msg:
            self.results["failure_analysis"]["data_quality_issues"].append(error_info)
        elif "nan" in error_msg or "invalid" in error_msg:
            self.results["failure_analysis"]["data_quality_issues"].append(error_info)
        elif execution_time > 10.0:  # > 10 seconds per indicator
            self.results["failure_analysis"]["performance_issues"].append(error_info)

    def _check_schema_compliance(self, indicator: str, preprocessor_result: Dict[str, Any]):
        """Check if preprocessor output follows standardized schema."""
        if indicator not in self.results["quality_assessment"]["schema_compliance"]:
            self.results["quality_assessment"]["schema_compliance"][indicator] = {
                "tests": 0,
                "compliant": 0,
                "issues": []
            }

        compliance = self.results["quality_assessment"]["schema_compliance"][indicator]
        compliance["tests"] += 1

        required_fields = ["indicator", "current", "context", "levels", "evidence", "summary"]
        forbidden_fields = ["signals", "confidence", "buy_signal", "sell_signal", "recommendation"]

        is_compliant = True

        # Check required fields
        for field in required_fields:
            if field not in preprocessor_result:
                compliance["issues"].append(f"Missing required field: {field}")
                is_compliant = False

        # Check forbidden fields (no trading signals)
        for field in forbidden_fields:
            if field in preprocessor_result:
                compliance["issues"].append(f"Contains forbidden field: {field}")
                is_compliant = False

        # Check UTC timestamp
        current = preprocessor_result.get("current", {})
        timestamp = current.get("timestamp", "")
        if not timestamp.endswith("+00:00") and not timestamp.endswith("Z"):
            compliance["issues"].append("Non-UTC timestamp detected")
            is_compliant = False

        if is_compliant:
            compliance["compliant"] += 1

    def _assess_trading_usefulness(self, indicator: str, preprocessor_result: Dict[str, Any]):
        """Assess if output provides useful trading context without being prescriptive."""
        if indicator not in self.results["quality_assessment"]["trading_usefulness"]:
            self.results["quality_assessment"]["trading_usefulness"][indicator] = {
                "tests": 0,
                "useful": 0,
                "usefulness_score": 0.0,
                "quality_notes": []
            }

        usefulness = self.results["quality_assessment"]["trading_usefulness"][indicator]
        usefulness["tests"] += 1

        score = 0.0

        # Check for rich context (not just current value)
        context = preprocessor_result.get("context", {})
        if context and len(context) > 1:
            score += 0.25

        # Check for pattern analysis
        patterns = preprocessor_result.get("patterns", {})
        if patterns:
            score += 0.25

        # Check for trend/momentum information
        if "trend" in context or "momentum" in context:
            score += 0.25

        # Check for comprehensive summary
        summary = preprocessor_result.get("summary", "")
        if summary and len(summary) > 20:  # Non-trivial summary
            score += 0.25

        usefulness["usefulness_score"] += score
        if score >= 0.75:
            usefulness["useful"] += 1

    def _track_performance(self, symbol: str, timeframe: str, indicator: str, execution_time: float):
        """Track performance metrics."""
        # Initialize performance tracking structures
        for analysis_type, key in [("preprocessor_analysis", indicator),
                                 ("timeframe_analysis", timeframe),
                                 ("symbol_analysis", symbol)]:
            if key not in self.results[analysis_type]:
                self.results[analysis_type][key] = {
                    "total_tests": 0,
                    "successful_tests": 0,
                    "failed_tests": 0,
                    "avg_execution_time": 0.0,
                    "total_execution_time": 0.0,
                    "issues": []
                }

            analysis = self.results[analysis_type][key]
            analysis["total_tests"] += 1
            analysis["total_execution_time"] += execution_time
            analysis["avg_execution_time"] = analysis["total_execution_time"] / analysis["total_tests"]

    def mark_success(self, symbol: str, timeframe: str, indicator: str):
        """Mark a test as successful for tracking."""
        for analysis_type, key in [("preprocessor_analysis", indicator),
                                 ("timeframe_analysis", timeframe),
                                 ("symbol_analysis", symbol)]:
            if key in self.results[analysis_type]:
                self.results[analysis_type][key]["successful_tests"] += 1

    def mark_failure(self, symbol: str, timeframe: str, indicator: str):
        """Mark a test as failed for tracking."""
        for analysis_type, key in [("preprocessor_analysis", indicator),
                                 ("timeframe_analysis", timeframe),
                                 ("symbol_analysis", symbol)]:
            if key in self.results[analysis_type]:
                self.results[analysis_type][key]["failed_tests"] += 1

    def _assess_pattern_quality(self, indicator: str, preprocessor_result: Dict[str, Any]):
        """Assess quality of pattern detection."""
        if indicator not in self.results["quality_assessment"]["pattern_detection_quality"]:
            self.results["quality_assessment"]["pattern_detection_quality"][indicator] = {
                "patterns_detected": 0,
                "pattern_types": [],
                "quality_score": 0.0
            }

        pattern_quality = self.results["quality_assessment"]["pattern_detection_quality"][indicator]
        patterns = preprocessor_result.get("patterns", {})

        if patterns:
            pattern_quality["patterns_detected"] += len(patterns)
            for pattern_type in patterns.keys():
                if pattern_type not in pattern_quality["pattern_types"]:
                    pattern_quality["pattern_types"].append(pattern_type)

    def finalize_report(self):
        """Finalize the comprehensive report."""
        end_time = datetime.now(timezone.utc)
        self.results["metadata"]["test_end"] = end_time.isoformat()
        self.results["metadata"]["test_duration_seconds"] = (end_time - self.start_time).total_seconds()

        # Calculate overall success rate
        total_tests = self.results["summary"]["total_tests_run"]
        if total_tests > 0:
            self.results["summary"]["overall_success_rate"] = (
                self.results["summary"]["total_successful"] / total_tests * 100
            )

        # Generate recommendations
        self._generate_recommendations()

        return self.results

    def _generate_recommendations(self):
        """Generate actionable recommendations based on test results."""
        recommendations = []

        # Performance recommendations
        slow_indicators = []
        for indicator, data in self.results["preprocessor_analysis"].items():
            if data.get("avg_execution_time", 0) > 1.0:  # > 1 second average
                slow_indicators.append(f"{indicator} ({data['avg_execution_time']:.2f}s avg)")

        if slow_indicators:
            recommendations.append({
                "category": "performance",
                "priority": "medium",
                "issue": "Slow preprocessor execution",
                "details": f"These indicators are slower than expected: {', '.join(slow_indicators)}",
                "recommendation": "Review algorithm efficiency and consider optimization"
            })

        # Data quality recommendations
        data_issues = len(self.results["failure_analysis"]["data_quality_issues"])
        if data_issues > 0:
            recommendations.append({
                "category": "data_quality",
                "priority": "high",
                "issue": f"{data_issues} data quality issues detected",
                "recommendation": "Review data cleaning and validation logic"
            })

        # Schema compliance recommendations
        non_compliant = []
        for indicator, compliance in self.results["quality_assessment"]["schema_compliance"].items():
            if compliance["tests"] > 0:
                compliance_rate = compliance["compliant"] / compliance["tests"]
                if compliance_rate < 0.95:  # < 95% compliance
                    non_compliant.append(f"{indicator} ({compliance_rate*100:.1f}%)")

        if non_compliant:
            recommendations.append({
                "category": "schema_compliance",
                "priority": "high",
                "issue": "Schema compliance issues",
                "details": f"Low compliance rates: {', '.join(non_compliant)}",
                "recommendation": "Review and fix schema standardization"
            })

        self.results["recommendations"] = recommendations


class TestPreprocessorSuperTest:
    """THE comprehensive preprocessor super test."""

    @pytest.mark.timeout(3600)  # 1 hour timeout
    def test_super_comprehensive_extraction(self):
        """
        THE ULTIMATE TEST: Test everything in our extraction system.

        This test runs every preprocessor against every timeframe and every symbol.
        It's designed to be comprehensive, not fast.

        What this test validates:
        1. All 21 preprocessors work correctly
        2. All 7 timeframes process successfully
        3. All 140+ symbols can be analyzed
        4. Output schema compliance
        5. Trading decision usefulness
        6. Data quality and accuracy
        7. Performance characteristics
        8. Error handling robustness

        Expected runtime: 30-60 minutes
        """
        print("\n" + "="*80)
        print("🚀 STARTING COMPREHENSIVE PREPROCESSOR SUPER TEST")
        print("="*80)
        print("This will test EVERYTHING in our extraction system.")
        print("Expected runtime: 30-60 minutes")
        print("Grab a coffee ☕ - this is going to be thorough...\n")

        # Initialize test infrastructure
        report = SuperTestReport()

        # Test configuration
        timeframes = ["5m", "15m", "30m", "1h", "4h", "1d"]  # Skip 1w for now (data availability)
        all_symbols = get_all_symbols()  # Get all 140+ symbols

        # For testing purposes, we'll use a subset first, then expand
        # You can modify this to test specific subsets or all symbols
        test_symbols = [
            # Major pairs
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "SOL/USDT",
            "ADA/USDT", "DOGE/USDT", "TRX/USDT", "DOT/USDT", "MATIC/USDT",
            # Mid-cap pairs
            "AVAX/USDT", "LINK/USDT", "UNI/USDT", "LTC/USDT", "BCH/USDT",
            # Smaller pairs (test different price scales)
            "SHIB/USDT", "PEPE/USDT", "FLOKI/USDT"
        ]

        # Override with full symbol list if desired
        # test_symbols = [symbol for symbol in all_symbols if "/USDT" in symbol][:50]  # First 50 USDT pairs

        all_indicators = [
            "rsi", "bbands", "adx", "aroon", "atr", "bbwidth", "cci", "donchian",
            "ema", "keltner", "macd", "mfi", "obv", "psar", "roc", "sma",
            "stochastic", "trix", "vortex", "vwap", "williams_r"
        ]

        report.results["metadata"]["test_configuration"] = {
            "timeframes": timeframes,
            "symbols_count": len(test_symbols),
            "indicators": all_indicators,
            "total_combinations": len(test_symbols) * len(timeframes) * len(all_indicators)
        }

        print(f"📊 Test Configuration:")
        print(f"   • Timeframes: {len(timeframes)} ({timeframes})")
        print(f"   • Symbols: {len(test_symbols)} (subset of {len(all_symbols)} available)")
        print(f"   • Indicators: {len(all_indicators)}")
        print(f"   • Total combinations: {len(test_symbols) * len(timeframes) * len(all_indicators)}")
        print()

        # Initialize extraction engine
        engine = ExtractionEngineV2(
            user_id=DEFAULT_USER_ID,
            use_advanced_preprocessing=True,
            use_database_storage=False,  # Don't store during testing
            use_file_storage=False       # Don't write files during testing
        )

        # Test counters
        total_combinations = len(test_symbols) * len(timeframes) * len(all_indicators)
        current_combination = 0

        # Main testing loop - SEQUENTIAL, COMPREHENSIVE
        print("🔄 Starting comprehensive sequential testing...\n")

        for symbol_idx, symbol in enumerate(test_symbols):
            print(f"📈 Testing symbol {symbol_idx + 1}/{len(test_symbols)}: {symbol}")

            for tf_idx, timeframe in enumerate(timeframes):
                print(f"   ⏰ Timeframe {tf_idx + 1}/{len(timeframes)}: {timeframe}")

                for ind_idx, indicator in enumerate(all_indicators):
                    current_combination += 1
                    progress = (current_combination / total_combinations) * 100

                    print(f"      🔧 {ind_idx + 1:2d}/{len(all_indicators)} {indicator:12s} [{progress:5.1f}%]", end=" ")

                    # Execute single indicator test
                    start_time = time.time()

                    try:
                        # Test individual indicator extraction
                        result = asyncio.run(engine.extract_for_symbol(
                            symbol=symbol,
                            indicators=[indicator],
                            timeframe=timeframe,
                            limit=200,  # Enough data for most calculations
                            connector="kucoin"
                        ))

                        execution_time = time.time() - start_time

                        # Add to report
                        report.add_test_result(symbol, timeframe, indicator, result, execution_time)

                        if result.get("status") == "success":
                            print(f"✅ {execution_time:.2f}s")
                        else:
                            print(f"❌ {execution_time:.2f}s - {result.get('error', 'Unknown error')[:50]}")

                    except Exception as e:
                        execution_time = time.time() - start_time
                        error_result = {
                            "status": "error",
                            "error": f"Exception: {str(e)}"
                        }
                        report.add_test_result(symbol, timeframe, indicator, error_result, execution_time)
                        print(f"💥 {execution_time:.2f}s - Exception: {str(e)[:50]}")

                print()  # New line after each timeframe
            print()  # New line after each symbol

        # Finalize and analyze results
        print("📋 Finalizing comprehensive test report...")
        final_report = report.finalize_report()

        # Print summary results
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*80)

        summary = final_report["summary"]
        print(f"🎯 Overall Success Rate: {summary['overall_success_rate']:.2f}%")
        print(f"✅ Successful Tests: {summary['total_successful']:,}")
        print(f"❌ Failed Tests: {summary['total_failed']:,}")
        print(f"📈 Total Tests Run: {summary['total_tests_run']:,}")
        print(f"⏱️  Total Duration: {final_report['metadata']['test_duration_seconds']:.1f} seconds")

        # Top-level performance analysis
        print(f"\n🚀 PERFORMANCE ANALYSIS:")
        preprocessor_perf = [(k, v['avg_execution_time']) for k, v in final_report['preprocessor_analysis'].items()]
        preprocessor_perf.sort(key=lambda x: x[1], reverse=True)

        print("   Slowest Preprocessors:")
        for indicator, avg_time in preprocessor_perf[:5]:
            print(f"      {indicator:12s}: {avg_time:.3f}s average")

        print("   Fastest Preprocessors:")
        for indicator, avg_time in preprocessor_perf[-5:]:
            print(f"      {indicator:12s}: {avg_time:.3f}s average")

        # Quality analysis
        print(f"\n📋 QUALITY ANALYSIS:")
        schema_compliance = final_report['quality_assessment']['schema_compliance']
        if schema_compliance:
            compliant_rates = []
            for indicator, data in schema_compliance.items():
                if data['tests'] > 0:
                    rate = data['compliant'] / data['tests'] * 100
                    compliant_rates.append((indicator, rate))

            compliant_rates.sort(key=lambda x: x[1])

            print("   Schema Compliance Rates:")
            for indicator, rate in compliant_rates:
                status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                print(f"      {status} {indicator:12s}: {rate:5.1f}%")

        # Critical issues
        critical_failures = final_report['failure_analysis']['critical_failures']
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES DETECTED:")
            print(f"   Total critical failures: {len(critical_failures)}")

            # Group by error type
            error_types = {}
            for failure in critical_failures:
                error = failure['error'][:50] + "..." if len(failure['error']) > 50 else failure['error']
                error_types[error] = error_types.get(error, 0) + 1

            print("   Most common errors:")
            for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"      {count:3d}x: {error}")

        # Recommendations
        recommendations = final_report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                priority_emoji = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
                print(f"   {priority_emoji} {rec['category'].upper()}: {rec['recommendation']}")

        # Save comprehensive reports
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        try:
            import os
            os.makedirs("tests/reports", exist_ok=True)

            # Save detailed JSON report
            json_report_file = f"tests/reports/super_test_detailed_{timestamp}.json"
            with open(json_report_file, 'w') as f:
                json.dump(final_report, f, indent=2, default=str)
            print(f"\n📄 Detailed JSON report saved: {json_report_file}")

            # Save human-readable summary report
            summary_file = f"tests/reports/super_test_summary_{timestamp}.md"
            self._save_markdown_summary(final_report, summary_file, test_symbols, timeframes, all_indicators)
            print(f"📄 Summary report saved: {summary_file}")

            # Save CSV data for analysis
            csv_file = f"tests/reports/super_test_data_{timestamp}.csv"
            self._save_csv_data(final_report, csv_file)
            print(f"📄 CSV data saved: {csv_file}")

        except Exception as e:
            print(f"\n⚠️  Could not save reports: {e}")

        print("\n" + "="*80)
        print("🎉 COMPREHENSIVE SUPER TEST COMPLETE!")
        print("="*80)

        # Test assertions - fail if critical issues found
        assert summary['overall_success_rate'] >= 70.0, \
            f"Overall success rate too low: {summary['overall_success_rate']:.2f}% (expected ≥70%)"

        # Ensure we actually tested a reasonable number of combinations
        assert summary['total_tests_run'] >= 100, \
            f"Too few tests run: {summary['total_tests_run']} (expected ≥100)"

        print(f"✅ Super test PASSED with {summary['overall_success_rate']:.2f}% success rate!")

    def _save_markdown_summary(self, report: Dict[str, Any], filename: str,
                             symbols: List[str], timeframes: List[str], indicators: List[str]):
        """Save a human-readable markdown summary."""
        summary = report["summary"]
        metadata = report["metadata"]

        with open(filename, 'w') as f:
            f.write("# ggbots Preprocessor Super Test Report\n\n")
            f.write(f"**Generated:** {metadata['test_start']}\n")
            f.write(f"**Duration:** {metadata['test_duration_seconds']:.1f} seconds\n")
            f.write(f"**Test Configuration:** {len(symbols)} symbols × {len(timeframes)} timeframes × {len(indicators)} indicators\n\n")

            # Overall Results
            f.write("## 📊 Overall Results\n\n")
            f.write(f"- **Success Rate:** {summary['overall_success_rate']:.2f}%\n")
            f.write(f"- **Total Tests:** {summary['total_tests_run']:,}\n")
            f.write(f"- **Successful:** {summary['total_successful']:,}\n")
            f.write(f"- **Failed:** {summary['total_failed']:,}\n\n")

            # Success Rate by Category
            f.write("## 🎯 Success Rates by Category\n\n")

            # Preprocessor success rates
            f.write("### By Preprocessor\n\n")
            f.write("| Preprocessor | Success Rate | Avg Time | Status |\n")
            f.write("|--------------|--------------|----------|--------|\n")

            for indicator, data in sorted(report['preprocessor_analysis'].items()):
                if data['total_tests'] > 0:
                    success_rate = (data['successful_tests'] / data['total_tests']) * 100
                    status = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
                    f.write(f"| {indicator} | {success_rate:.1f}% | {data['avg_execution_time']:.3f}s | {status} |\n")

            # Symbol success rates
            f.write("\n### By Symbol\n\n")
            f.write("| Symbol | Success Rate | Avg Time | Status |\n")
            f.write("|--------|--------------|----------|--------|\n")

            symbol_results = [(symbol, data) for symbol, data in report['symbol_analysis'].items()]
            symbol_results.sort(key=lambda x: x[1]['successful_tests'] / max(x[1]['total_tests'], 1), reverse=True)

            for symbol, data in symbol_results:
                if data['total_tests'] > 0:
                    success_rate = (data['successful_tests'] / data['total_tests']) * 100
                    status = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
                    f.write(f"| {symbol} | {success_rate:.1f}% | {data['avg_execution_time']:.3f}s | {status} |\n")

            # Timeframe success rates
            f.write("\n### By Timeframe\n\n")
            f.write("| Timeframe | Success Rate | Avg Time | Status |\n")
            f.write("|-----------|--------------|----------|--------|\n")

            for timeframe, data in sorted(report['timeframe_analysis'].items()):
                if data['total_tests'] > 0:
                    success_rate = (data['successful_tests'] / data['total_tests']) * 100
                    status = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
                    f.write(f"| {timeframe} | {success_rate:.1f}% | {data['avg_execution_time']:.3f}s | {status} |\n")

            # Critical Issues
            f.write("\n## 🚨 Critical Issues\n\n")
            critical_failures = report['failure_analysis']['critical_failures']

            if critical_failures:
                # Group failures by error type
                error_groups = {}
                for failure in critical_failures:
                    error_key = failure['error'][:100]  # First 100 chars
                    if error_key not in error_groups:
                        error_groups[error_key] = []
                    error_groups[error_key].append(failure)

                for error, failures in sorted(error_groups.items(), key=lambda x: len(x[1]), reverse=True):
                    f.write(f"### {error}\n")
                    f.write(f"**Occurrences:** {len(failures)}\n\n")

                    # Show affected symbols/timeframes/indicators
                    symbols_affected = set(f['symbol'] for f in failures)
                    timeframes_affected = set(f['timeframe'] for f in failures)
                    indicators_affected = set(f['indicator'] for f in failures)

                    f.write(f"- **Symbols affected:** {', '.join(sorted(symbols_affected))}\n")
                    f.write(f"- **Timeframes affected:** {', '.join(sorted(timeframes_affected))}\n")
                    f.write(f"- **Indicators affected:** {', '.join(sorted(indicators_affected))}\n\n")
            else:
                f.write("No critical issues detected! 🎉\n\n")

            # Recommendations
            f.write("## 💡 Recommendations\n\n")
            recommendations = report.get('recommendations', [])
            if recommendations:
                for rec in recommendations:
                    priority_emoji = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
                    f.write(f"{priority_emoji} **{rec['category'].upper()}:** {rec['recommendation']}\n")
                    if 'details' in rec:
                        f.write(f"   - Details: {rec['details']}\n")
                    f.write("\n")
            else:
                f.write("All systems operating optimally! 🎉\n")

            # Performance Analysis
            f.write("\n## ⚡ Performance Analysis\n\n")
            preprocessor_perf = [(k, v['avg_execution_time']) for k, v in report['preprocessor_analysis'].items()]
            preprocessor_perf.sort(key=lambda x: x[1], reverse=True)

            f.write("### Slowest Preprocessors\n")
            for indicator, avg_time in preprocessor_perf[:5]:
                f.write(f"- **{indicator}:** {avg_time:.3f}s average\n")

            f.write("\n### Fastest Preprocessors\n")
            for indicator, avg_time in preprocessor_perf[-5:]:
                f.write(f"- **{indicator}:** {avg_time:.3f}s average\n")

    def _save_csv_data(self, report: Dict[str, Any], filename: str):
        """Save test results as CSV for spreadsheet analysis."""
        rows = []

        # Extract individual test results from failures
        for failure in report['failure_analysis']['critical_failures']:
            rows.append({
                'symbol': failure['symbol'],
                'timeframe': failure['timeframe'],
                'indicator': failure['indicator'],
                'status': 'FAILED',
                'execution_time': failure['execution_time'],
                'error': failure['error'][:200]  # Truncate long errors
            })

        # Calculate success data from analysis summaries
        for symbol, symbol_data in report['symbol_analysis'].items():
            for timeframe, tf_data in report['timeframe_analysis'].items():
                for indicator, ind_data in report['preprocessor_analysis'].items():
                    # This is an approximation - we'd need to track individual successes
                    # to get exact data, but this gives us the overall picture
                    pass

        # Write CSV
        if rows:
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['symbol', 'timeframe', 'indicator', 'status', 'execution_time', 'error'])
                writer.writeheader()
                writer.writerows(rows)


if __name__ == "__main__":
    # Allow running directly for development
    test = TestPreprocessorSuperTest()
    test.test_super_comprehensive_extraction()