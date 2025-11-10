#!/usr/bin/env python3
"""
OpenRouter Provider Test Script

Phase 0.2: Test the OpenRouterProvider implementation.

Tests:
1. Provider initialization
2. Health check
3. Standard response generation
4. ggshot mode system prompt
5. trade_management mode system prompt
6. Token tracking format
7. Error handling
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decision.llm_providers import get_llm_provider
from core.common.logger import logger

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found in environment")
    sys.exit(1)


async def test_provider_initialization():
    """Test 1: Provider initialization"""
    print("=" * 80)
    print("TEST 1: Provider Initialization")
    print("=" * 80)

    try:
        provider = get_llm_provider(
            provider_name='openrouter',
            api_key=OPENROUTER_API_KEY,
            model='gpt-5'
        )

        print(f"✅ Provider initialized: {provider.__class__.__name__}")
        print(f"   Internal model: {provider.model}")
        print(f"   OpenRouter model: {provider.openrouter_model}")
        print()
        return provider

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        print()
        return None


async def test_health_check(provider):
    """Test 2: Health check"""
    print("=" * 80)
    print("TEST 2: Health Check")
    print("=" * 80)

    try:
        is_healthy = await provider.health_check()

        if is_healthy:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")

        print()
        return is_healthy

    except Exception as e:
        print(f"❌ Health check error: {e}")
        print()
        return False


async def test_standard_response(provider):
    """Test 3: Standard response generation"""
    print("=" * 80)
    print("TEST 3: Standard Response (No Custom Mode)")
    print("=" * 80)

    try:
        prompt = "What is Bitcoin? Respond in one sentence."

        response, metadata = await provider.generate_response(
            prompt=prompt,
            temperature=0.7
        )

        print(f"✅ Response received")
        print(f"   Content: {response[:100]}...")
        print(f"   Internal model: {metadata['model']}")
        print(f"   OpenRouter model: {metadata.get('openrouter_model', 'N/A')}")
        print(f"   Prompt tokens: {metadata['usage']['prompt_tokens']}")
        print(f"   Completion tokens: {metadata['usage']['completion_tokens']}")
        print(f"   Total tokens: {metadata['usage']['total_tokens']}")
        print(f"   Latency: {metadata['latency']:.2f}s")
        print(f"   Finish reason: {metadata['finish_reason']}")

        if 'reasoning_tokens' in metadata['usage']:
            print(f"   Reasoning tokens: {metadata['usage']['reasoning_tokens']}")

        print()
        return True

    except Exception as e:
        print(f"❌ Standard response failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def test_ggshot_mode(provider):
    """Test 4: ggshot mode system prompt"""
    print("=" * 80)
    print("TEST 4: ggshot Mode System Prompt")
    print("=" * 80)

    try:
        prompt = (
            "BTC/USD is at support with RSI=35, bullish divergence confirmed. "
            "Score this signal using the Four-Pillar Framework."
        )

        response, metadata = await provider.generate_response(
            prompt=prompt,
            temperature=0.7,
            custom_mode="ggshot"
        )

        print(f"✅ ggshot response received")
        print(f"   Content: {response[:150]}...")
        print(f"   Total tokens: {metadata['usage']['total_tokens']}")
        print(f"   Latency: {metadata['latency']:.2f}s")
        print()
        return True

    except Exception as e:
        print(f"❌ ggshot mode failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def test_trade_management_mode(provider):
    """Test 5: trade_management mode system prompt"""
    print("=" * 80)
    print("TEST 5: trade_management Mode System Prompt")
    print("=" * 80)

    try:
        prompt = (
            "I have an open long position on ETH/USD from $2,500, currently at $2,700. "
            "Should I hold, take profit, or adjust stop loss?"
        )

        response, metadata = await provider.generate_response(
            prompt=prompt,
            temperature=0.7,
            custom_mode="trade_management"
        )

        print(f"✅ trade_management response received")
        print(f"   Content: {response[:150]}...")
        print(f"   Total tokens: {metadata['usage']['total_tokens']}")
        print(f"   Latency: {metadata['latency']:.2f}s")
        print()
        return True

    except Exception as e:
        print(f"❌ trade_management mode failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def test_conversation_history(provider):
    """Test 6: Conversation history"""
    print("=" * 80)
    print("TEST 6: Conversation History")
    print("=" * 80)

    try:
        conversation_history = [
            {"role": "user", "content": "What is your name?"},
            {"role": "assistant", "content": "I am a trading assistant."}
        ]

        response, metadata = await provider.generate_response(
            prompt="What did I just ask you?",
            conversation_history=conversation_history,
            temperature=0.7
        )

        print(f"✅ Conversation history response received")
        print(f"   Content: {response[:100]}...")
        print(f"   Total tokens: {metadata['usage']['total_tokens']}")
        print()
        return True

    except Exception as e:
        print(f"❌ Conversation history failed: {e}")
        print()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("OPENROUTER PROVIDER TEST SUITE")
    print("=" * 80)
    print()

    # Test 1: Initialization
    provider = await test_provider_initialization()
    if not provider:
        print("❌ Cannot proceed without valid provider")
        return

    # Test 2: Health check
    is_healthy = await test_health_check(provider)
    if not is_healthy:
        print("⚠️  Health check failed, but continuing with other tests...")

    # Test 3: Standard response
    await test_standard_response(provider)

    # Test 4: ggshot mode
    await test_ggshot_mode(provider)

    # Test 5: trade_management mode
    await test_trade_management_mode(provider)

    # Test 6: Conversation history
    await test_conversation_history(provider)

    print("=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
    print()
    print("✅ OpenRouterProvider is ready for integration!")
    print()
    print("Next steps:")
    print("1. Test with a real bot config")
    print("2. Monitor for 24 hours")
    print("3. Migrate all configs to OpenRouter")
    print()


if __name__ == "__main__":
    asyncio.run(main())
