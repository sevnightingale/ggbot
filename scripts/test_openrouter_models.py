#!/usr/bin/env python3
"""
OpenRouter Model Availability Test

Phase 0.1: Verify which models are available and get exact model names.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found in environment")
    sys.exit(1)

print("🔍 Fetching OpenRouter model list...")
print(f"API Key: {OPENROUTER_API_KEY[:15]}...")
print()

# Query model list
url = "https://openrouter.ai/api/v1/models"
headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    if 'data' not in data:
        print(f"❌ Unexpected response format: {json.dumps(data, indent=2)}")
        sys.exit(1)

    models = data['data']
    print(f"✅ Found {len(models)} models available on OpenRouter\n")

    # Our models of interest
    target_keywords = ['gpt-4', 'gpt-5', 'claude', 'deepseek', 'grok']

    print("=" * 80)
    print("MODELS WE CARE ABOUT")
    print("=" * 80)
    print()

    found_models = []

    for model in models:
        model_id = model.get('id', '')
        model_name = model.get('name', '')

        # Check if this is one of our target models
        if any(keyword in model_id.lower() for keyword in target_keywords):
            pricing = model.get('pricing', {})
            context_length = model.get('context_length', 'N/A')

            # Parse pricing (strings to avoid float issues)
            prompt_price = pricing.get('prompt', '0')
            completion_price = pricing.get('completion', '0')

            # Convert to per-1K-token pricing for readability
            try:
                prompt_per_1k = float(prompt_price) * 1000
                completion_per_1k = float(completion_price) * 1000
            except:
                prompt_per_1k = 0
                completion_per_1k = 0

            found_models.append({
                'id': model_id,
                'name': model_name,
                'prompt_per_1k': prompt_per_1k,
                'completion_per_1k': completion_per_1k,
                'context_length': context_length
            })

    # Sort by provider then model name
    found_models.sort(key=lambda x: x['id'])

    # Display results
    for model in found_models:
        print(f"Model ID: {model['id']}")
        print(f"  Name: {model['name']}")
        print(f"  Input:  ${model['prompt_per_1k']:.4f} per 1K tokens")
        print(f"  Output: ${model['completion_per_1k']:.4f} per 1K tokens")
        print(f"  Context: {model['context_length']:,} tokens")
        print()

    print("=" * 80)
    print("MODEL NAME MAPPING")
    print("=" * 80)
    print()
    print("Internal Name → OpenRouter Model ID")
    print("-" * 80)

    # Show suggested mappings (user will need to confirm exact names)
    suggestions = {
        'gpt-4': [m['id'] for m in found_models if 'gpt-4' in m['id'].lower()],
        'gpt-5': [m['id'] for m in found_models if 'gpt-5' in m['id'].lower() or 'o1' in m['id'].lower() or 'o3' in m['id'].lower()],
        'claude-opus-4': [m['id'] for m in found_models if 'claude' in m['id'].lower() and 'opus' in m['id'].lower()],
        'claude-sonnet-4.5': [m['id'] for m in found_models if 'claude' in m['id'].lower() and 'sonnet' in m['id'].lower()],
        'deepseek-reasoner': [m['id'] for m in found_models if 'deepseek' in m['id'].lower()],
        'grok-4': [m['id'] for m in found_models if 'grok' in m['id'].lower()],
    }

    for internal_name, candidates in suggestions.items():
        if candidates:
            print(f"{internal_name:25} → {', '.join(candidates)}")
        else:
            print(f"{internal_name:25} → ❌ NOT FOUND")

    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("1. Review the model IDs above")
    print("2. Confirm which exact models we want to use")
    print("3. Test a completion with one of these models")
    print()

except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response: {e.response.text}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
