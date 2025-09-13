#!/usr/bin/env python3
"""
Test script for LLM provider integration.

Tests the new config-based LLM selection system.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from decision.llm_providers import get_llm_provider, get_available_providers
from core.services.llm_key_service import LLMKeyService


async def test_providers():
    """Test all available LLM providers."""
    print("🔬 Testing LLM Provider Integration")
    print("=" * 50)

    # Check available providers
    providers = get_available_providers()
    print(f"Available providers: {providers}")
    print()

    # Test each provider
    for provider in providers:
        print(f"Testing {provider.upper()} provider...")

        try:
            # Get platform API key
            api_key = LLMKeyService._get_platform_api_key(provider)
            if not api_key:
                print(f"❌ No platform API key found for {provider}")
                continue

            # Create provider instance
            llm_provider = get_llm_provider(
                provider_name=provider,
                api_key=api_key
            )

            print(f"✅ Provider created: {llm_provider.__class__.__name__}")
            print(f"   Model: {llm_provider.model}")

            # Test basic functionality with a simple prompt
            test_prompt = "Say 'OK' if you can read this message."

            print(f"   Testing with prompt: {test_prompt}")
            response, metadata = await llm_provider.generate_response(
                prompt=test_prompt,
                temperature=0.0
            )

            print(f"   Response: {response[:100]}...")
            print(f"   Latency: {metadata.get('latency', 'unknown'):.2f}s")
            print(f"   Model used: {metadata.get('model', 'unknown')}")
            print(f"✅ {provider.upper()} test completed successfully")

        except Exception as e:
            print(f"❌ {provider.upper()} test failed: {e}")

        print()

    print("🎉 LLM Provider testing completed!")


async def test_key_resolution():
    """Test API key resolution logic."""
    print("\n🔑 Testing API Key Resolution")
    print("=" * 50)

    test_user_id = "00000000-0000-0000-0000-000000000001"

    for provider in get_available_providers():
        try:
            api_key = await LLMKeyService.get_api_key(test_user_id, provider)
            print(f"✅ {provider}: Key resolved (***{api_key[-4:]})")
        except Exception as e:
            print(f"❌ {provider}: {e}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    print("🚀 Starting LLM Provider Tests\n")

    # Run tests
    asyncio.run(test_key_resolution())
    # Uncomment below to test actual LLM calls (will use API quota)
    # asyncio.run(test_providers())

    print("\n✨ All tests completed!")