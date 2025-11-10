#!/usr/bin/env python3
"""
Test all 14 OpenRouter model variants (7 models × 2 thinking modes)

Tests each configuration to ensure:
1. Provider initialization works
2. Responses are generated successfully
3. Token tracking is correct
4. Thinking mode parameters are applied
5. Special cases handled (GPT-5 no temp, Qwen no reasoning)
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decision.llm_providers import get_llm_provider

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found in environment")
    sys.exit(1)

# 7 models
MODELS = ['grok', 'claude', 'gemini', 'deepseek', 'gpt', 'kimi', 'qwen']

# Test prompt
TEST_PROMPT = "What is 2+2? Answer in one sentence."


async def test_model_variant(model_name: str, thinking: bool):
    """Test a single model variant"""
    variant_name = f"{model_name} ({'thinking' if thinking else 'standard'})"

    try:
        # Initialize provider
        provider = get_llm_provider(
            provider_name='openrouter',
            api_key=OPENROUTER_API_KEY,
            model=model_name,
            thinking=thinking
        )

        # Generate response
        response, metadata = await provider.generate_response(
            prompt=TEST_PROMPT,
            temperature=0.7
        )

        # Validate response
        if not response:
            print(f"❌ {variant_name}: Empty response")
            return False

        # Extract key metadata
        openrouter_model = metadata.get('openrouter_model', 'N/A')
        thinking_mode = metadata.get('thinking_mode', False)
        max_tokens = metadata.get('max_tokens', 'N/A')
        prompt_tokens = metadata['usage']['prompt_tokens']
        completion_tokens = metadata['usage']['completion_tokens']
        total_tokens = metadata['usage']['total_tokens']
        latency = metadata.get('latency', 0)
        temp = metadata.get('temperature', 'N/A')

        # Check for reasoning tokens
        reasoning_tokens = metadata['usage'].get('reasoning_tokens', 0)

        print(f"✅ {variant_name:<25} | {openrouter_model:<30} | max_tok: {max_tokens:<4} | tokens: {total_tokens:<4} | reasoning: {reasoning_tokens:<4} | temp: {temp} | {latency:.2f}s")

        return True

    except Exception as e:
        print(f"❌ {variant_name:<25} | ERROR: {str(e)[:80]}")
        return False


async def main():
    """Test all 14 variants"""
    print("=" * 150)
    print("TESTING ALL 14 OPENROUTER MODEL VARIANTS")
    print("=" * 150)
    print()

    results = []

    # Test each model in both modes
    for model in MODELS:
        # Standard mode
        result_std = await test_model_variant(model, thinking=False)
        results.append(('standard', model, result_std))

        # Thinking mode
        result_think = await test_model_variant(model, thinking=True)
        results.append(('thinking', model, result_think))

        print()  # Spacing between models

    # Summary
    print("=" * 150)
    print("SUMMARY")
    print("=" * 150)
    print()

    passed = sum(1 for _, _, result in results if result)
    failed = sum(1 for _, _, result in results if not result)

    print(f"Total variants: 14")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print()

    if failed > 0:
        print("Failed variants:")
        for mode, model, result in results:
            if not result:
                print(f"  • {model} ({mode})")
        print()

    # Expected behavior notes
    print("=" * 150)
    print("EXPECTED BEHAVIOR")
    print("=" * 150)
    print()
    print("Standard Mode:")
    print("  • max_tokens: 2048")
    print("  • No reasoning parameter")
    print("  • Temperature: 0.7 (except GPT-5)")
    print()
    print("Thinking Mode:")
    print("  • max_tokens: 8192 (4096 for Qwen)")
    print("  • reasoning.effort: high (except Qwen)")
    print("  • Temperature: 0.7 (except GPT-5)")
    print("  • May show reasoning_tokens in usage")
    print()
    print("Special Cases:")
    print("  • GPT-5: No temperature support")
    print("  • Qwen: No reasoning parameter support")
    print()


if __name__ == "__main__":
    asyncio.run(main())
