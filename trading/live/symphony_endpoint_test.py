"""
Test Symphony endpoint variations to find account balance.
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

SYMPHONY_API_KEY = os.getenv("SYMPHONY_API_KEY")
USER_ADDRESS = "0xc256119769fefcc9bd5a1897607c6f66a358f3da"


async def test_endpoint(url, params=None, use_auth=False):
    """Test an endpoint and return status."""
    headers = {}
    if use_auth:
        headers["x-api-key"] = SYMPHONY_API_KEY

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            status = response.status
            if status == 200:
                try:
                    data = await response.json()
                    return status, "✅ SUCCESS", data
                except:
                    text = await response.text()
                    return status, "✅ SUCCESS (non-JSON)", text[:100]
            else:
                text = await response.text()
                return status, "❌ FAILED", text[:100]


async def main():
    print("🔍 Testing Symphony API Endpoints")
    print("=" * 80)

    # Test variations of the account endpoint
    tests = [
        ("Without auth", f"https://api.symphony.io/agent/all-positions?userAddress={USER_ADDRESS}", None, False),
        ("With auth", f"https://api.symphony.io/agent/all-positions?userAddress={USER_ADDRESS}", None, True),
        ("V1 without auth", f"https://api.symphony.io/v1/agent/all-positions?userAddress={USER_ADDRESS}", None, False),
        ("V1 with auth", f"https://api.symphony.io/v1/agent/all-positions?userAddress={USER_ADDRESS}", None, True),
        ("Account endpoint", f"https://api.symphony.io/agent/account?userAddress={USER_ADDRESS}", None, False),
        ("Account with auth", f"https://api.symphony.io/agent/account?userAddress={USER_ADDRESS}", None, True),
        ("Performance endpoint", f"https://api.symphony.io/agent/performance?userAddress={USER_ADDRESS}", None, False),
        ("User endpoint", f"https://api.symphony.io/user/account?address={USER_ADDRESS}", None, False),
        ("V1 user endpoint", f"https://api.symphony.io/v1/user/account?address={USER_ADDRESS}", None, False),
    ]

    for name, url, params, use_auth in tests:
        print(f"\n📍 {name}")
        print(f"   URL: {url}")
        status, result, data = await test_endpoint(url, params, use_auth)
        print(f"   Status: {status} {result}")
        if status == 200:
            print(f"   Data preview: {str(data)[:200]}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
