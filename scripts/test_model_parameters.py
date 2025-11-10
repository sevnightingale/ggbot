#!/usr/bin/env python3
"""
Query OpenRouter for supported parameters for each selected model.

Models:
1. x-ai/grok-4-fast
2. anthropic/claude-sonnet-4.5
3. google/gemini-2.5-pro
4. deepseek/deepseek-chat-v3.1
5. openai/gpt-5
6. moonshotai/kimi-k2-thinking
7. qwen/qwen3-max
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found in environment")
    sys.exit(1)

# Selected models
MODELS = [
    "x-ai/grok-4-fast",
    "anthropic/claude-sonnet-4.5",
    "google/gemini-2.5-pro",
    "deepseek/deepseek-chat-v3.1",
    "openai/gpt-5",
    "moonshotai/kimi-k2-thinking",
    "qwen/qwen3-max"
]

# Pricing from CONTEXT.md
PRICING = {
    "x-ai/grok-4-fast": {"input": 0.20, "output": 0.50, "context": "2M"},
    "anthropic/claude-sonnet-4.5": {"input": 3.00, "output": 15.00, "context": "1M"},
    "google/gemini-2.5-pro": {"input": 1.25, "output": 10.00, "context": "1.05M"},
    "deepseek/deepseek-chat-v3.1": {"input": 0.20, "output": 0.80, "context": "164K"},
    "openai/gpt-5": {"input": 1.25, "output": 10.00, "context": "400K"},
    "moonshotai/kimi-k2-thinking": {"input": 0.60, "output": 2.50, "context": "262K"},
    "qwen/qwen3-max": {"input": 1.20, "output": 6.00, "context": "256K"}
}


def get_model_parameters(model_id: str):
    """
    Query OpenRouter for supported parameters for a model.

    API: GET https://openrouter.ai/api/v1/parameters/{author}/{slug}
    """
    # Split model ID into author/slug
    parts = model_id.split('/')
    if len(parts) != 2:
        print(f"❌ Invalid model ID format: {model_id}")
        return None

    author, slug = parts

    url = f"https://openrouter.ai/api/v1/parameters/{author}/{slug}"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data.get('data', {})
        else:
            print(f"❌ Error {response.status_code} for {model_id}: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Exception for {model_id}: {e}")
        return None


def main():
    print("=" * 100)
    print("OPENROUTER MODEL PARAMETERS ANALYSIS")
    print("=" * 100)
    print()

    results = {}

    # Query each model
    for model_id in MODELS:
        print(f"Querying: {model_id}...")
        params = get_model_parameters(model_id)

        if params:
            results[model_id] = params
            print(f"✅ Found {len(params.get('supported_parameters', []))} supported parameters")
        else:
            print(f"❌ Failed to get parameters")

        print()

    # Display detailed results
    print("=" * 100)
    print("DETAILED PARAMETER SUPPORT BY MODEL")
    print("=" * 100)
    print()

    # Collect all unique parameters
    all_params = set()
    for model_id, data in results.items():
        all_params.update(data.get('supported_parameters', []))

    all_params = sorted(all_params)

    # Display table header
    print(f"{'Parameter':<30}", end='')
    for model_id in MODELS:
        short_name = model_id.split('/')[1][:15]
        print(f"{short_name:<17}", end='')
    print()
    print("-" * 100)

    # Display each parameter
    for param in all_params:
        print(f"{param:<30}", end='')

        for model_id in MODELS:
            if model_id in results:
                supported = param in results[model_id].get('supported_parameters', [])
                print(f"{'✅' if supported else '❌':<17}", end='')
            else:
                print(f"{'?':<17}", end='')

        print()

    print()
    print("=" * 100)
    print("PRICING COMPARISON (per 1M tokens)")
    print("=" * 100)
    print()

    print(f"{'Model':<35} {'Context':<12} {'Input':<12} {'Output':<12} {'Cost/Decision*'}")
    print("-" * 100)

    for model_id in MODELS:
        pricing = PRICING.get(model_id, {})
        context = pricing.get('context', 'N/A')
        input_price = pricing.get('input', 0)
        output_price = pricing.get('output', 0)

        # Calculate cost per decision (5K input + 2K output)
        cost_per_decision = (input_price * 5 / 1000) + (output_price * 2 / 1000)

        print(f"{model_id:<35} {context:<12} ${input_price:<11.2f} ${output_price:<11.2f} ${cost_per_decision:.4f}")

    print()
    print("*Cost per decision assumes 5K input tokens + 2K output tokens")
    print()

    print("=" * 100)
    print("KEY PARAMETERS TO CONSIDER")
    print("=" * 100)
    print()

    # Check for critical parameters
    critical_params = ['temperature', 'max_tokens', 'top_p', 'reasoning', 'include_reasoning', 'verbosity']

    for param in critical_params:
        if param in all_params:
            print(f"✅ {param:<25} - Supported by:")
            for model_id in MODELS:
                if model_id in results and param in results[model_id].get('supported_parameters', []):
                    print(f"     • {model_id}")
            print()

    print()
    print("=" * 100)
    print("RECOMMENDATIONS")
    print("=" * 100)
    print()
    print("Based on parameter analysis:")
    print("1. Check which models support 'reasoning' or 'include_reasoning'")
    print("2. Identify common parameters supported by all models (temperature, max_tokens, etc.)")
    print("3. Determine model-specific parameters that need special handling")
    print("4. Consider cost vs. capability tradeoffs")
    print()


if __name__ == "__main__":
    main()
