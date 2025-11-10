#!/usr/bin/env python3
"""
Test the /api/v2/llm-models endpoint
"""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Use service auth for testing
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_SERVICE_KEY:
    print("❌ SUPABASE_SERVICE_KEY not found")
    exit(1)

url = "http://localhost:8000/api/v2/llm-models"
headers = {
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "x-service-auth": "signal-listener"  # Use service auth to bypass user auth
}

print("Testing GET /api/v2/llm-models...")
print()

try:
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        print(f"✅ Success! Found {data['count']} models")
        print()

        for model in data['models']:
            print(f"Model: {model['display_name']}")
            print(f"  ID: {model['model_id']}")
            print(f"  Provider: {model['provider']}")
            print(f"  Context: {model['context_display']}")
            print(f"  Thinking: {'✅' if model['supports_thinking'] else '❌'}")
            print(f"  Cost (standard): ${model['cost_per_decision']['standard']:.4f}")
            print(f"  Cost (thinking): ${model['cost_per_decision']['thinking']:.4f}")
            print()
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"❌ Request failed: {e}")
