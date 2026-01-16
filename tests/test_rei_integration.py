"""
Rei Integration Test - Tests ReiService connectivity and basic functionality.

This test validates:
1. ReiService instantiation with API key from environment
2. get_agent() endpoint connectivity
3. chat_completion() with JSON response format
4. Response parsing and error handling

Usage:
    cd /home/sev/ggbot && source .venv/bin/activate
    python -m tests.test_rei_integration

Requires:
    - REI_01_UNIT_SECRET in .env
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv(project_root / ".env")

from core.services.rei_service import (
    ReiService,
    ReiResponse,
    ReiAuthenticationError,
    ReiAPIError
)
from core.common.logger import logger


async def test_rei_service_init():
    """Test 1: ReiService instantiation."""
    print("\n" + "="*60)
    print("TEST 1: ReiService Instantiation")
    print("="*60)

    api_key = os.getenv("REI_01_UNIT_SECRET")

    if not api_key:
        print("❌ REI_01_UNIT_SECRET not found in environment")
        return False

    print(f"✅ API key found (length: {len(api_key)} chars)")

    try:
        rei = ReiService(agent_secret_key=api_key)
        print(f"✅ ReiService instantiated successfully")
        print(f"   Base URL: {rei.BASE_URL}")
        print(f"   Timeout: {rei.timeout}s")
        print(f"   Max retries: {rei.max_retries}")
        await rei.close()
        return True
    except Exception as e:
        print(f"❌ Failed to instantiate ReiService: {e}")
        return False


async def test_get_agent():
    """Test 2: get_agent() endpoint."""
    print("\n" + "="*60)
    print("TEST 2: get_agent() - Retrieve Unit Info")
    print("="*60)

    try:
        async with ReiService() as rei:
            agent_info = await rei.get_agent()

            print("✅ get_agent() succeeded")
            print(f"\nAgent Info:")
            print(json.dumps(agent_info, indent=2, default=str))
            return True

    except ReiAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Check that REI_01_UNIT_SECRET is correct")
        return False

    except ReiAPIError as e:
        print(f"❌ API error: {e}")
        if e.status_code:
            print(f"   Status code: {e.status_code}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_simple_chat():
    """Test 3: Simple chat completion."""
    print("\n" + "="*60)
    print("TEST 3: chat_completion() - Simple Query")
    print("="*60)

    try:
        async with ReiService() as rei:
            messages = [{
                "role": "user",
                "content": "What is 2 + 2? Answer in one word."
            }]

            print("Sending simple query to Rei...")
            response = await rei.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=50
            )

            print("✅ chat_completion() succeeded")
            print(f"\nResponse content: {response.content}")
            print(f"Model: {response.model}")
            if response.usage:
                print(f"Usage: {response.usage}")
            return True

    except ReiAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False

    except ReiAPIError as e:
        print(f"❌ API error: {e}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_json_response():
    """Test 4: Chat completion with JSON response format."""
    print("\n" + "="*60)
    print("TEST 4: chat_completion() - JSON Response Format")
    print("="*60)

    try:
        async with ReiService() as rei:
            messages = [{
                "role": "user",
                "content": """Analyze this simple market data and provide a decision.

RSI: 35 (oversold territory)
MACD: Bullish crossover
Price trend: Downtrend for 3 days

Provide your analysis as JSON with these fields:
- action: "long", "short", or "wait"
- confidence: 0.0 to 1.0
- reasoning: brief explanation
- key_signals: list of important signals"""
            }]

            print("Sending JSON query to Rei...")
            response = await rei.chat_completion(
                messages=messages,
                temperature=0.45,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            print("✅ chat_completion() with JSON format succeeded")
            print(f"\nRaw response:\n{response.content}")

            # Try to parse as JSON
            try:
                parsed = json.loads(response.content)
                print(f"\n✅ Response parsed as valid JSON")
                print(f"   Action: {parsed.get('action', 'N/A')}")
                print(f"   Confidence: {parsed.get('confidence', 'N/A')}")
                print(f"   Reasoning: {parsed.get('reasoning', 'N/A')[:100]}...")
            except json.JSONDecodeError as e:
                print(f"\n⚠️  Response is not valid JSON: {e}")

            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_trading_decision_format():
    """Test 5: Full trading decision format (mimics consult_rei_for_decision)."""
    print("\n" + "="*60)
    print("TEST 5: Trading Decision - Full Format")
    print("="*60)

    # Build a message similar to what consult_rei_for_decision would send
    market_data = {
        "symbol": "BTC/USDT",
        "timeframe": "4h",
        "technical_indicators": {
            "rsi": {"current": 31.5, "interpretation": "oversold"},
            "macd": {"histogram": 0.12, "signal": "bullish_crossover"},
            "adx": {"value": 38.2, "trend_strength": "strong"},
            "bbands": {"position": "near_lower", "width": 0.045}
        },
        "market_intelligence": {
            "funding_rate": {"btc": 0.008, "signal": "neutral"},
            "whale_activity": {"signal": "distribution", "confidence": 0.65}
        }
    }

    message_content = f"""TRADING DECISION REQUEST

Symbol: {market_data['symbol']}
Timeframe: {market_data['timeframe']}

TECHNICAL INDICATORS:
{json.dumps(market_data['technical_indicators'], indent=2)}

MARKET INTELLIGENCE:
{json.dumps(market_data['market_intelligence'], indent=2)}

CURRENT POSITIONS: None
ACCOUNT BALANCE: $10,000 USD

Based on this market data, what trading action should I take?

Respond with JSON:
{{
  "action": "enter_long" | "enter_short" | "exit" | "wait",
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation of key factors",
  "key_signals": ["signal1", "signal2"],
  "warnings": ["any concerns"]
}}"""

    try:
        async with ReiService() as rei:
            print("Sending full trading decision query to Rei...")
            print(f"\nMessage length: {len(message_content)} chars")

            response = await rei.chat_completion(
                messages=[{"role": "user", "content": message_content}],
                temperature=0.45,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            print("✅ Trading decision query succeeded")
            print(f"\nRaw response:\n{response.content}")

            try:
                parsed = json.loads(response.content)
                print(f"\n✅ Valid JSON response")
                print(f"   Action: {parsed.get('action', 'N/A')}")
                print(f"   Confidence: {parsed.get('confidence', 'N/A')}")

                # Validate expected fields
                required_fields = ["action", "confidence", "reasoning"]
                missing = [f for f in required_fields if f not in parsed]
                if missing:
                    print(f"   ⚠️  Missing fields: {missing}")
                else:
                    print(f"   ✅ All required fields present")

            except json.JSONDecodeError as e:
                print(f"\n⚠️  Response is not valid JSON: {e}")

            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Rei integration tests."""
    print("\n" + "="*70)
    print("REI INTEGRATION TEST SUITE")
    print("="*70)
    print(f"Project root: {project_root}")
    print(f"API key env var: REI_01_UNIT_SECRET")

    results = {}

    # Run tests
    results["instantiation"] = await test_rei_service_init()

    if results["instantiation"]:
        results["get_agent"] = await test_get_agent()
        results["simple_chat"] = await test_simple_chat()
        results["json_response"] = await test_json_response()
        results["trading_decision"] = await test_trading_decision_format()
    else:
        print("\n⚠️  Skipping remaining tests - instantiation failed")

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")

    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n✅ All tests passed! Rei integration is working.")
    else:
        print("\n⚠️  Some tests failed. Check output above for details.")

    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
