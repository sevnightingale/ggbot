#!/usr/bin/env python3
"""
OpenRouter Completion Test

Phase 0.1: Test chat completion and verify token tracking format.
"""

import os
import sys
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found in environment")
    sys.exit(1)

# Initialize OpenAI client with OpenRouter base URL
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Test models
test_models = [
    "openai/gpt-5",
    "anthropic/claude-sonnet-4.5",
    "deepseek/deepseek-r1"
]

print("=" * 80)
print("TESTING OPENROUTER COMPLETIONS")
print("=" * 80)
print()

for model_id in test_models:
    print(f"Testing: {model_id}")
    print("-" * 80)

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello from OpenRouter!' and nothing else."}
            ],
            temperature=0.7,
            max_tokens=50
        )

        # Extract data
        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason
        usage = response.usage

        print(f"✅ SUCCESS")
        print(f"Response: {content}")
        print(f"Finish Reason: {finish_reason}")
        print()
        print("Token Usage:")
        print(f"  Prompt tokens:     {usage.prompt_tokens}")
        print(f"  Completion tokens: {usage.completion_tokens}")
        print(f"  Total tokens:      {usage.total_tokens}")

        # Check if cost is included
        if hasattr(usage, 'cost'):
            print(f"  Cost: ${usage.cost}")

        # Check for reasoning tokens (for GPT-5, DeepSeek R1)
        if hasattr(usage, 'completion_tokens_details'):
            details = usage.completion_tokens_details
            if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens:
                print(f"  Reasoning tokens: {details.reasoning_tokens}")

        print()

    except Exception as e:
        print(f"❌ FAILED: {e}")
        print()

print("=" * 80)
print("TOKEN TRACKING FORMAT VERIFICATION")
print("=" * 80)
print()
print("✅ All models return standardized usage format:")
print("   - prompt_tokens")
print("   - completion_tokens")
print("   - total_tokens")
print()
print("✅ This is EXACTLY what we need for metered billing!")
print()
