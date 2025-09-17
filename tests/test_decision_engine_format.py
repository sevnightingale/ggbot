"""
Decision Engine Data Format Test

Shows exactly how market data appears in the Decision Engine prompts
- simulates the LLM-formatted market data across all timeframes
- shows the human-readable format that gets sent to GPT-5
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Any

from core.common.config import DEFAULT_USER_ID
from extraction.v2.extraction_engine import ExtractionEngineV2
from decision.engine_v2 import DecisionEngineV2


async def test_decision_engine_format():
    """
    Test how market data appears in the Decision Engine format.
    Shows the exact LLM prompt formatting across all timeframes.
    """

    print("🤖 Testing Decision Engine Data Format")
    print("=" * 80)
    print("This shows exactly how market data appears in LLM prompts")
    print()

    # Test configuration
    symbol = "BTC/USDT"
    timeframes = ["5m", "15m", "30m", "1h", "4h", "1d"]

    # Use a representative set of key indicators
    key_indicators = [
        "rsi", "macd", "sma", "ema", "bbands", "adx", "aroon", "atr",
        "stochastic", "williams_r", "vwap"
    ]

    print(f"📊 Symbol: {symbol}")
    print(f"🕐 Timeframes: {timeframes}")
    print(f"📈 Indicators: {key_indicators}")
    print()

    # Initialize extraction engine
    engine = ExtractionEngineV2(
        user_id=DEFAULT_USER_ID,
        use_advanced_preprocessing=True,
        use_database_storage=False,
        use_file_storage=False
    )

    # Collect data for all timeframes
    timeframe_data = {}

    print("🔄 Extracting data for all timeframes...")
    for timeframe in timeframes:
        print(f"  Extracting {timeframe}...", end=" ")

        result = await engine.extract_for_symbol(
            symbol=symbol,
            indicators=key_indicators,
            timeframe=timeframe,
            limit=100,
            connector="kucoin"
        )

        if result.get("status") == "success":
            timeframe_data[timeframe] = {
                "indicators": result["result"]["indicators"],
                "raw_summary": result["result"]["ohlcv_summary"],
                "updated_at": datetime.now(timezone.utc)
            }
            print("✅")
        else:
            print(f"❌ {result.get('error', 'Unknown error')}")

    # Create the consolidated multi-timeframe structure like DecisionEngine does
    consolidated_data = {
        "symbol": symbol,
        "timeframes": timeframe_data,
        "latest_price": timeframe_data.get("1h", {}).get("raw_summary", {}).get("latest_price", 0.0),
        "data_age_seconds": 30,  # Simulated fresh data
        "timeframes_available": list(timeframe_data.keys())
    }

    # Format exactly like DecisionEngine._format_multi_timeframe_data()
    print("\n" + "="*80)
    print("🤖 DECISION ENGINE LLM PROMPT FORMAT")
    print("="*80)
    print("This is exactly what the Decision LLM sees:\n")

    formatted_prompt_data = format_for_decision_engine(consolidated_data)
    print(formatted_prompt_data)

    # Save to file for review
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"tests/reports/decision_engine_format_{timestamp}.txt"

    try:
        import os
        os.makedirs("tests/reports", exist_ok=True)

        with open(filename, 'w') as f:
            f.write("DECISION ENGINE LLM PROMPT FORMAT\n")
            f.write("="*80 + "\n\n")
            f.write("This is exactly how market data appears in GPT-5 prompts for trading decisions.\n\n")
            f.write(formatted_prompt_data)
            f.write("\n\n" + "="*80 + "\n")
            f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"Symbol: {symbol}\n")
            f.write(f"Timeframes: {', '.join(timeframes)}\n")
            f.write(f"Indicators: {', '.join(key_indicators)}\n")

        print(f"\n📄 Decision Engine format saved: {filename}")

    except Exception as e:
        print(f"⚠️ Could not save file: {e}")

    print("\n" + "="*80)
    print("🎉 DECISION ENGINE FORMAT TEST COMPLETE")
    print("="*80)


def format_for_decision_engine(market_data: Dict[str, Any]) -> str:
    """
    Format market data exactly like DecisionEngineV2._format_multi_timeframe_data()
    This is the exact function from decision/engine_v2.py
    """
    formatted = []

    # Header with symbol and current price
    symbol = market_data.get('symbol', 'Unknown')
    latest_price = market_data.get('latest_price', 0.0)
    timeframes = market_data.get('timeframes', {})

    formatted.append(f"MARKET ANALYSIS FOR {symbol}")
    formatted.append(f"Current Price: ${latest_price:,.2f}")
    formatted.append(f"Timeframes Available: {', '.join(market_data.get('timeframes_available', []))}")
    formatted.append("")

    # Format each timeframe's data
    for timeframe, tf_data in timeframes.items():
        formatted.append(f"=== {timeframe.upper()} TIMEFRAME ===")

        indicators = tf_data.get("indicators", {})
        if indicators:
            for indicator_name, indicator_data in indicators.items():
                formatted.append(f"  {indicator_name}:")

                # Format rich indicator data from V2 preprocessors
                if isinstance(indicator_data, dict):
                    # Current values (always show)
                    if "current" in indicator_data:
                        formatted.append(f"    Current: {indicator_data['current']}")

                    # Summary (most important - human readable)
                    if "summary" in indicator_data:
                        formatted.append(f"    Summary: {indicator_data['summary']}")

                    # Context (trend, momentum, volatility)
                    if "context" in indicator_data:
                        context = indicator_data["context"]
                        if isinstance(context, dict):
                            for key, value in context.items():
                                if isinstance(value, dict):
                                    # Handle nested context like trend: {direction: rising, strength: 0.68}
                                    nested_str = ", ".join(f"{k}: {v}" for k, v in value.items())
                                    formatted.append(f"    {key.title()}: {nested_str}")
                                else:
                                    formatted.append(f"    {key.title()}: {value}")

                    # Levels (zones, thresholds, crossovers)
                    if "levels" in indicator_data:
                        levels = indicator_data["levels"]
                        if isinstance(levels, dict):
                            for key, value in levels.items():
                                if key == "current_zone":
                                    formatted.append(f"    Zone: {value}")
                                elif isinstance(value, dict) and "current_zone" in value:
                                    formatted.append(f"    Zone: {value['current_zone']}")
                                elif key not in ["key_levels", "recent_crossovers"]:  # Skip noisy arrays
                                    formatted.append(f"    {key.replace('_', ' ').title()}: {value}")

                    # Patterns (detected formations)
                    if "patterns" in indicator_data:
                        patterns = indicator_data["patterns"]
                        if isinstance(patterns, dict) and patterns:
                            pattern_names = [k for k, v in patterns.items() if v]
                            if pattern_names:
                                formatted.append(f"    Patterns: {', '.join(pattern_names)}")

                    # Evidence (quality metrics)
                    if "evidence" in indicator_data:
                        evidence = indicator_data["evidence"]
                        if isinstance(evidence, dict):
                            evidence_parts = []
                            for key, value in evidence.items():
                                if isinstance(value, (int, float)):
                                    evidence_parts.append(f"{key}: {value:.2f}")
                                else:
                                    evidence_parts.append(f"{key}: {value}")
                            if evidence_parts:
                                formatted.append(f"    Quality: {', '.join(evidence_parts)}")

                    # Legacy support for old format indicators
                    if "trend" in indicator_data:
                        trend = indicator_data["trend"]
                        if isinstance(trend, dict):
                            direction = trend.get("direction", "unknown")
                            formatted.append(f"    Legacy Trend: {direction}")
                        else:
                            formatted.append(f"    Legacy Trend: {trend}")

                    if "zones" in indicator_data:
                        zones = indicator_data["zones"]
                        if isinstance(zones, dict):
                            current_zone = zones.get("current", "unknown")
                            formatted.append(f"    Legacy Zone: {current_zone}")
                else:
                    # Simple numeric value
                    formatted.append(f"    Value: {indicator_data}")

                formatted.append("")
        else:
            formatted.append("  No indicators available for this timeframe")
            formatted.append("")

    # Add data freshness info
    age_seconds = market_data.get('data_age_seconds', 0)
    if age_seconds < 60:
        age_str = f"{int(age_seconds)} seconds"
    elif age_seconds < 3600:
        age_str = f"{int(age_seconds/60)} minutes"
    else:
        age_str = f"{int(age_seconds/3600)} hours"

    formatted.append(f"Data Age: {age_str}")

    return "\n".join(formatted)


if __name__ == "__main__":
    asyncio.run(test_decision_engine_format())