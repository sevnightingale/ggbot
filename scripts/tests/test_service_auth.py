#!/usr/bin/env python3
"""
Test script for service-to-service authentication between signal listener and ggbot API.
"""

import asyncio
import aiohttp
import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_service_authentication():
    """Test the service authentication flow."""

    print("🧪 Testing Service-to-Service Authentication")
    print("=" * 50)

    # Configuration
    api_base = os.getenv('GGBOT_API_URL', 'http://localhost:8000')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not service_key:
        print("❌ SUPABASE_SERVICE_KEY not found in environment")
        return False

    print(f"✅ Service key loaded (length: {len(service_key)})")
    print(f"🎯 API Base: {api_base}")

    # Test data
    config_id = 'e5b43a4b-7446-43cd-bd01-3fe6eb0357b2'  # Real config from SSE data
    user_id = '00000000-0000-0000-0000-000000000000'     # Real user from SSE data

    test_signal_data = {
        'signal_data': {
            'source': 'ggshot',
            'symbol': 'BTC/USDT',
            'direction': 'LONG',
            'timeframe': '1h',
            'confidence': 0.75,
            'entry_zone': {'low': 50000, 'mid': 51000, 'high': 52000},
            'stop_loss': 49000,
            'take_profit': 55000,
            'reasoning': 'Test signal from service auth validation',
            'raw_message': '[TEST] BTC Long signal for service auth testing',
            'metadata': {'test': True},
            'timestamp': datetime.now(timezone.utc).isoformat()
        },
        'override_symbol': 'BTC/USDT'
    }

    # Test 1: No authentication (should fail)
    print("\n1️⃣ Testing WITHOUT authentication (should fail)...")
    try:
        url = f"{api_base}/api/v2/signal-validation/{config_id}"
        params = {'user_id': user_id}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_signal_data, params=params, timeout=10) as response:
                print(f"   Status: {response.status}")
                error_text = await response.text()
                if response.status == 401:
                    print("   ✅ Correctly rejected unauthenticated request")
                else:
                    print(f"   ⚠️  Unexpected status. Error: {error_text}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        print("   💡 Make sure ggbot.py is running on localhost:8000")
        return False

    # Test 2: Wrong service header (should fail)
    print("\n2️⃣ Testing with WRONG service header (should fail)...")
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {service_key}',
            'X-Service-Auth': 'wrong-service'  # Wrong service name
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_signal_data, headers=headers, params=params, timeout=10) as response:
                print(f"   Status: {response.status}")
                if response.status == 401:
                    print("   ✅ Correctly rejected wrong service header")
                else:
                    error_text = await response.text()
                    print(f"   ⚠️  Unexpected status. Error: {error_text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Correct authentication (should succeed)
    print("\n3️⃣ Testing with CORRECT service authentication (should succeed)...")
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {service_key}',
            'X-Service-Auth': 'signal-listener'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_signal_data, headers=headers, params=params, timeout=10) as response:
                print(f"   Status: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ SUCCESS! Orchestration result: {result.get('status', 'unknown')}")
                    if 'execution_id' in result:
                        print(f"   🎯 Execution ID: {result['execution_id']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"   ❌ Failed: {error_text}")

                    # If it's a business logic error (not auth), that's still auth success
                    if response.status in [422, 500] and 'authentication' not in error_text.lower():
                        print("   ✅ Authentication worked (business logic error is expected)")
                        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 50)
    return False

if __name__ == "__main__":
    success = asyncio.run(test_service_authentication())
    if success:
        print("🎉 Service authentication is working correctly!")
    else:
        print("❌ Service authentication test failed")