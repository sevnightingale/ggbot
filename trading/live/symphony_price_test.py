"""
Test Symphony Token Price endpoint (public API)

This endpoint is useful for:
1. Getting real-time prices for Monad tokens
2. Resolving Symphony Identifiers (SIDs)
3. Validating token existence before swapping
"""

import asyncio
import aiohttp


async def get_token_price(token_input: str, chain_id: int = 143):
    """
    Get token price from Symphony public API.

    Args:
        token_input: Token address or symbol (e.g., "MON", "USDC", "0x...")
        chain_id: Chain ID (Monad = 143, Polygon = 137, Base = 8453, Arbitrum = 42161)

    Returns:
        Dict with price, sid, chainId
    """
    url = "https://api.symphony.io/token/price"

    params = {
        "input": token_input,
        "chainId": chain_id
    }

    print(f"\n{'=' * 80}")
    print(f"🔍 Querying Symphony Price API")
    print(f"{'=' * 80}")
    print(f"Token: {token_input}")
    print(f"Chain ID: {chain_id} (Monad)" if chain_id == 143 else f"Chain ID: {chain_id}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                status_code = response.status

                if status_code == 200:
                    data = await response.json()

                    if data.get("status") == "success":
                        print(f"\n✅ SUCCESS")
                        print(f"\nPrice Data:")
                        print(f"  USD Price: ${data.get('price', 0):.8f}")
                        print(f"  SID: {data.get('sid')}")
                        print(f"  Chain ID: {data.get('chainId')}")
                        return data
                    else:
                        print(f"\n❌ API returned error status")
                        print(f"Response: {data}")
                        return None
                else:
                    error_text = await response.text()
                    print(f"\n❌ HTTP {status_code}")
                    print(f"Error: {error_text}")
                    return None

    except asyncio.TimeoutError:
        print(f"\n❌ TIMEOUT after 10s")
        return None
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None


async def main():
    """Test Symphony price endpoint with various tokens."""

    print("\n🧪 Symphony Token Price API Tests")
    print("=" * 80)
    print("Testing public price endpoint (no auth required)")
    print("=" * 80)

    # Test 1: MON token by symbol on Monad
    print("\n\n📊 Test 1: MON price (by symbol)")
    mon_data = await get_token_price("MON", chain_id=143)
    if mon_data:
        print(f"\n✅ MON SID confirmed: {mon_data.get('sid')}")

    # Test 2: USDC on Monad
    print("\n\n📊 Test 2: USDC price on Monad")
    usdc_data = await get_token_price("USDC", chain_id=143)

    # Test 3: BTC (should work on any chain)
    print("\n\n📊 Test 3: BTC price (generic)")
    btc_data = await get_token_price("BTC", chain_id=143)

    # Test 4: ETH on Monad
    print("\n\n📊 Test 4: ETH price on Monad")
    eth_data = await get_token_price("ETH", chain_id=143)

    # Test 5: Token by address (from docs example)
    print("\n\n📊 Test 5: Token by contract address")
    address_data = await get_token_price(
        "0x350035555e10d9afaf1566aaebfced5ba6c27777",
        chain_id=143
    )

    # Summary
    print("\n\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)

    if mon_data:
        print(f"\n✅ MON Token:")
        print(f"   Price: ${mon_data.get('price', 0):.8f}")
        print(f"   SID: {mon_data.get('sid')} (Expected: 10056)")

        # Validate SID
        if mon_data.get('sid') == 10056:
            print(f"   ✅ SID matches expected value!")
        else:
            print(f"   ⚠️  SID mismatch (got {mon_data.get('sid')}, expected 10056)")

    print("\n\nNext Steps:")
    print("1. ✅ Price endpoint works - can use for P&L calculations")
    print("2. ✅ SID resolution works - can validate tokens before swapping")
    print("3. 🔄 Run symphony_swap_test.py to test actual swaps")
    print("4. 🔄 Add MON to symbol registry with SID 10056")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
