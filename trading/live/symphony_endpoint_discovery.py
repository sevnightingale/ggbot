"""
Discover correct Symphony API endpoints through testing.
"""

import asyncio
import aiohttp


async def test_endpoint(method: str, url: str, params=None, headers=None):
    """Test an endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    status = response.status
                    if status == 200:
                        data = await response.json()
                        return status, data
                    else:
                        text = await response.text()
                        return status, text[:200]
            elif method == "POST":
                async with session.post(url, json=params, headers=headers, timeout=10) as response:
                    status = response.status
                    if status == 200:
                        data = await response.json()
                        return status, data
                    else:
                        text = await response.text()
                        return status, text[:200]
    except Exception as e:
        return None, str(e)


async def main():
    """Test various endpoint paths."""

    print("\n🔍 Symphony API Endpoint Discovery")
    print("=" * 80)

    base_url = "https://api.symphony.io"

    # Test different paths for price endpoint
    price_paths = [
        "/token/price",
        "/v1/token/price",
        "/api/token/price",
        "/api/v1/token/price",
        "/price",
        "/token-price",
        "/tokens/price",
    ]

    params = {"input": "MON", "chainId": 143}

    print("\n📊 Testing Token Price Endpoint Paths:")
    for path in price_paths:
        url = f"{base_url}{path}"
        print(f"\n  Trying: {path}")
        status, result = await test_endpoint("GET", url, params=params)

        if status == 200:
            print(f"    ✅ SUCCESS: {status}")
            print(f"    Data: {result}")
            break
        elif status == 404:
            print(f"    ❌ Not found")
        elif status:
            print(f"    ⚠️  Status {status}: {result[:100]}")
        else:
            print(f"    ❌ Error: {result}")

    # Test swap endpoint paths
    print("\n\n📊 Testing Swap Endpoint Paths:")
    swap_paths = [
        "/agent/swap",
        "/v1/agent/swap",
        "/api/agent/swap",
        "/api/v1/agent/swap",
    ]

    swap_payload = {
        "agentId": "test",
        "tokenIn": "MON",
        "tokenOut": "USDC",
        "weight": 1
    }

    for path in swap_paths:
        url = f"{base_url}{path}"
        print(f"\n  Trying: {path}")
        status, result = await test_endpoint("POST", url, params=swap_payload)

        if status == 200:
            print(f"    ✅ SUCCESS: {status}")
            print(f"    Data: {result}")
            break
        elif status == 404:
            print(f"    ❌ Not found")
        elif status == 401 or status == 403:
            print(f"    ✅ Endpoint exists but needs auth: {status}")
        elif status:
            print(f"    Status {status}: {result[:100]}")
        else:
            print(f"    ❌ Error: {result}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
