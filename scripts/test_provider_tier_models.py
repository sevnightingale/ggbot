#!/usr/bin/env python3
"""
Test Provider + Tier Model System

Tests each model we plan to use in the new architecture.
MUST pass before implementing any changes.
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Load env
env_file = Path('/home/sev/ggbot/.env')
for line in env_file.read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        key, val = line.split('=', 1)
        # Strip quotes from value
        val = val.strip().strip('"').strip("'")
        os.environ[key.strip()] = val

from openai import AsyncOpenAI

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not found")
    sys.exit(1)

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Models to test - Provider + Tier architecture
# Format: (provider, tier, model_id, description)
MODELS_TO_TEST = [
    # Grok (xAI)
    ("grok", "economy", "x-ai/grok-3-mini", "Grok 3 Mini"),
    ("grok", "standard", "x-ai/grok-4-fast", "Grok 4 Fast"),
    ("grok", "premium", "x-ai/grok-4", "Grok 4"),

    # DeepSeek
    ("deepseek", "economy", "deepseek/deepseek-chat", "DeepSeek V3"),
    ("deepseek", "standard", "deepseek/deepseek-v3.2", "DeepSeek V3.2"),
    ("deepseek", "premium", "deepseek/deepseek-r1", "DeepSeek R1"),

    # Gemini (Google)
    ("gemini", "economy", "google/gemini-2.0-flash-001", "Gemini 2.0 Flash"),
    ("gemini", "standard", "google/gemini-2.5-pro", "Gemini 2.5 Pro"),
    ("gemini", "premium", "google/gemini-3-pro-preview", "Gemini 3 Pro Preview"),

    # Claude (Anthropic)
    ("claude", "economy", "anthropic/claude-haiku-4.5", "Claude Haiku 4.5"),
    ("claude", "standard", "anthropic/claude-sonnet-4.5", "Claude Sonnet 4.5"),
    ("claude", "premium", "anthropic/claude-opus-4.5", "Claude Opus 4.5"),

    # GPT (OpenAI)
    ("openai", "economy", "openai/gpt-4.1-mini", "GPT-4.1 Mini"),
    ("openai", "standard", "openai/gpt-5", "GPT-5"),
    ("openai", "premium", "openai/gpt-5-pro", "GPT-5 Pro"),

    # Kimi (MoonshotAI)
    ("kimi", "economy", "moonshotai/kimi-k2", "Kimi K2"),
    ("kimi", "standard", "moonshotai/kimi-k2-0905", "Kimi K2 0905"),
    ("kimi", "premium", "moonshotai/kimi-k2-thinking", "Kimi K2 Thinking"),

    # Qwen
    ("qwen", "economy", "qwen/qwen-turbo", "Qwen Turbo"),
    ("qwen", "standard", "qwen/qwen-plus", "Qwen Plus"),
    ("qwen", "premium", "qwen/qwen3-max", "Qwen3 Max"),
]

TEST_PROMPT = "What is 2+2? Reply with just the number."

async def test_model(provider: str, tier: str, model_id: str, description: str) -> dict:
    """Test a single model and return results."""
    result = {
        "provider": provider,
        "tier": tier,
        "model_id": model_id,
        "description": description,
        "success": False,
        "response": None,
        "error": None,
        "latency_ms": None,
        "tokens_used": None
    }

    start = time.time()
    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": TEST_PROMPT}],
            max_tokens=50,
            timeout=60
        )

        latency = (time.time() - start) * 1000
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else None

        result["success"] = True
        result["response"] = content[:100] if content else "EMPTY"
        result["latency_ms"] = round(latency)
        result["tokens_used"] = tokens

    except Exception as e:
        result["error"] = str(e)[:200]
        result["latency_ms"] = round((time.time() - start) * 1000)

    return result

async def main():
    print("=" * 100)
    print("PROVIDER + TIER MODEL VERIFICATION TEST")
    print("=" * 100)
    print(f"\nTesting {len(MODELS_TO_TEST)} models...")
    print()

    results = []

    for provider, tier, model_id, description in MODELS_TO_TEST:
        print(f"Testing {provider}/{tier}: {model_id}...", end=" ", flush=True)
        result = await test_model(provider, tier, model_id, description)
        results.append(result)

        if result["success"]:
            print(f"OK ({result['latency_ms']}ms, {result['tokens_used']} tokens)")
        else:
            print(f"FAILED: {result['error'][:80]}")

        # Small delay between requests
        await asyncio.sleep(0.5)

    # Summary
    print()
    print("=" * 100)
    print("RESULTS SUMMARY")
    print("=" * 100)
    print()

    passed = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"PASSED: {len(passed)}/{len(results)}")
    print(f"FAILED: {len(failed)}/{len(results)}")
    print()

    if failed:
        print("FAILED MODELS:")
        print("-" * 80)
        for r in failed:
            print(f"  {r['provider']}/{r['tier']}: {r['model_id']}")
            print(f"    Error: {r['error']}")
        print()

    # Print working models by provider
    print("WORKING MODELS BY PROVIDER:")
    print("-" * 80)

    providers = {}
    for r in passed:
        if r["provider"] not in providers:
            providers[r["provider"]] = {}
        providers[r["provider"]][r["tier"]] = {
            "model_id": r["model_id"],
            "description": r["description"]
        }

    for provider, tiers in sorted(providers.items()):
        print(f"\n{provider.upper()}:")
        for tier in ["economy", "standard", "premium"]:
            if tier in tiers:
                print(f"  {tier:10} -> {tiers[tier]['model_id']} ({tiers[tier]['description']})")
            else:
                print(f"  {tier:10} -> FAILED/MISSING")

    print()
    print("=" * 100)

    if failed:
        print("SOME MODELS FAILED - DO NOT PROCEED WITH IMPLEMENTATION")
        return 1
    else:
        print("ALL MODELS PASSED - SAFE TO PROCEED WITH IMPLEMENTATION")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
