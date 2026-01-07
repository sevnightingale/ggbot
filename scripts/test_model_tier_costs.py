"""
Test script to measure actual costs for all 21 model+tier combinations.

Runs a real trading decision prompt against each model/tier and records:
- Input/output tokens
- Provider cost
- Platform cost (with 70% markup)
- Response time

Usage:
    python scripts/test_model_tier_costs.py
"""

import asyncio
import time
from decimal import Decimal
from typing import Dict, List, Tuple
from core.common.logger import logger
from core.services.llm_key_service import LLMKeyService
from core.services.llm_pricing_service import LLMPricingService
from decision.llm_providers.openrouter_provider import OpenRouterProvider

# All 7 models x 3 tiers = 21 combinations
MODELS = ['grok', 'deepseek', 'gemini', 'gpt', 'claude', 'kimi', 'qwen']
TIERS = ['economy', 'standard', 'premium']

async def test_model_tier(model: str, tier: str, user_prompt: str) -> Dict:
    """Test a single model+tier combination."""

    try:
        # Get API key (use None for user_id to get platform key)
        api_key = await LLMKeyService.get_api_key(
            user_id=None,
            provider="openrouter"
        )

        if not api_key:
            return {
                'model': model,
                'tier': tier,
                'error': 'No API key available',
                'success': False
            }

        # Initialize provider with specific tier
        provider = OpenRouterProvider(
            api_key=api_key,
            model=model,
            reasoning_tier=tier
        )

        # Time the request
        start_time = time.time()

        # Generate response (no system_prompt arg - it's handled internally)
        response = await provider.generate_response(
            prompt=user_prompt,
            temperature=0.7
        )

        elapsed_time = time.time() - start_time

        # Extract usage info
        metadata = response.get('metadata', {})
        usage = metadata.get('usage', {})
        input_tokens = usage.get('input_tokens', 0) or usage.get('prompt_tokens', 0)
        output_tokens = usage.get('output_tokens', 0) or usage.get('completion_tokens', 0)

        # Calculate costs
        provider_cost, platform_cost = LLMPricingService.calculate_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider='openrouter',
            model=model,
            thinking_mode=(tier == 'premium')
        )

        return {
            'model': model,
            'tier': tier,
            'openrouter_model': metadata.get('openrouter_model', 'unknown'),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'provider_cost': provider_cost,
            'platform_cost': platform_cost,
            'response_time_sec': round(elapsed_time, 2),
            'success': True
        }

    except Exception as e:
        logger.error(f"Error testing {model}/{tier}: {e}")
        return {
            'model': model,
            'tier': tier,
            'error': str(e),
            'success': False
        }


async def run_all_tests():
    """Run tests for all 21 model+tier combinations."""

    # Load test prompt
    try:
        with open('/tmp/test_prompt.txt', 'r') as f:
            user_prompt = f.read()
        print(f"Loaded test prompt: {len(user_prompt)} chars")
    except FileNotFoundError:
        print("ERROR: No test prompt found. Run this first:")
        print("  python -c \"from core.common.db import get_db_connection; ...\"")
        return

    print("\n" + "=" * 100)
    print("TESTING ALL 21 MODEL+TIER COMBINATIONS")
    print("=" * 100 + "\n")

    results = []

    for model in MODELS:
        for tier in TIERS:
            print(f"Testing {model}/{tier}...", end=" ", flush=True)

            result = await test_model_tier(model, tier, user_prompt)
            results.append(result)

            if result['success']:
                print(f"OK - ${result['platform_cost']:.4f} ({result['input_tokens']} in, {result['output_tokens']} out, {result['response_time_sec']}s)")
            else:
                print(f"FAILED - {result.get('error', 'unknown error')}")

            # Small delay between requests to avoid rate limiting
            await asyncio.sleep(1)

    # Print summary table
    print("\n" + "=" * 100)
    print("RESULTS SUMMARY")
    print("=" * 100)
    print(f"\n{'Model':<12} {'Tier':<10} {'OpenRouter Model':<35} {'In Tok':<8} {'Out Tok':<8} {'Cost':<10} {'Time':<8}")
    print("-" * 100)

    for r in results:
        if r['success']:
            print(f"{r['model']:<12} {r['tier']:<10} {r['openrouter_model']:<35} {r['input_tokens']:<8} {r['output_tokens']:<8} ${r['platform_cost']:<9.4f} {r['response_time_sec']:<8}s")
        else:
            print(f"{r['model']:<12} {r['tier']:<10} {'FAILED':<35} {'-':<8} {'-':<8} {'-':<10} {'-':<8}")

    # Print cost matrix for easy copying
    print("\n" + "=" * 100)
    print("COST MATRIX (for UpgradeModal)")
    print("=" * 100)
    print("\nconst MODEL_TIER_COSTS = {")

    for model in MODELS:
        model_results = [r for r in results if r['model'] == model and r['success']]
        if model_results:
            costs = {}
            for r in model_results:
                costs[r['tier']] = r['platform_cost']

            economy = costs.get('economy', 0)
            standard = costs.get('standard', 0)
            premium = costs.get('premium', 0)
            print(f"  '{model}': {{ economy: {economy:.4f}, standard: {standard:.4f}, premium: {premium:.4f} }},")

    print("}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
