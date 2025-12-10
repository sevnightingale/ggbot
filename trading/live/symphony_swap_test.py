"""
Test Symphony Spot Trading (Swap) API with MON token

Tests the /agent/swap endpoint for Monad (MON) token swaps.
Based on documentation from: https://docs.symphony.io/spot-trading

MON Details:
- Chain: Monad (new L1)
- SID: 10056
- Trading: Spot only (no perps)
- Collateral: MON is the base asset on Monad testnet
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

SYMPHONY_API_KEY = os.getenv("SYMPHONY_API_KEY")
SYMPHONY_AGENT_ID = os.getenv("SYMPHONY_AGENT_ID")  # Need your agent ID


async def test_swap_endpoint(
    token_in: str,
    token_out: str,
    weight: float,
    desired_protocol: str = None
):
    """
    Test Symphony swap endpoint.

    Args:
        token_in: Input token symbol (e.g., "MON", "USDC")
        token_out: Output token symbol or address
        weight: Percentage of balance to swap (0-100)
        desired_protocol: Optional protocol preference (e.g., "kuru", "nadfun")
    """
    url = "https://api.symphony.io/agent/swap"

    headers = {
        "x-api-key": SYMPHONY_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "agentId": SYMPHONY_AGENT_ID,
        "tokenIn": token_in,
        "tokenOut": token_out,
        "weight": weight
    }

    # Add optional protocol preference
    if desired_protocol:
        payload["intentOptions"] = {
            "desiredProtocol": desired_protocol
        }

    print(f"\n{'=' * 80}")
    print(f"🔄 Testing Swap: {token_in} → {token_out} ({weight}% of balance)")
    print(f"{'=' * 80}")
    print(f"URL: {url}")
    print(f"Payload: {payload}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                status = response.status

                if status == 200:
                    data = await response.json()
                    print(f"\n✅ SUCCESS (Status {status})")
                    print(f"\nResponse:")
                    print(f"  Message: {data.get('message')}")
                    print(f"  Batch ID: {data.get('batchId')}")
                    print(f"  Successful: {data.get('successful')}")
                    print(f"  Failed: {data.get('failed')}")

                    # Show results
                    results = data.get('results', [])
                    for i, result in enumerate(results):
                        print(f"\n  Result {i+1}:")
                        print(f"    Smart Account: {result.get('smartAccount')}")
                        result_data = result.get('result', {})
                        print(f"    Success: {result_data.get('success')}")
                        print(f"    Tx Hash: {result_data.get('executeTxHash', 'N/A')}")
                        print(f"    Explorer: {result_data.get('explorerUrl', 'N/A')}")

                    return data
                else:
                    error_text = await response.text()
                    print(f"\n❌ FAILED (Status {status})")
                    print(f"Error: {error_text}")
                    return None

    except asyncio.TimeoutError:
        print(f"\n❌ TIMEOUT after 30s")
        return None
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None


async def main():
    """Run swap tests."""

    # Validate environment
    if not SYMPHONY_API_KEY:
        print("❌ ERROR: SYMPHONY_API_KEY not found in .env")
        return

    if not SYMPHONY_AGENT_ID:
        print("❌ ERROR: SYMPHONY_AGENT_ID not found in .env")
        print("   Get this from Symphony dashboard")
        return

    print("\n🧪 Symphony Spot Trading (Swap) Tests")
    print(f"Agent ID: {SYMPHONY_AGENT_ID}")
    print(f"API Key: {SYMPHONY_API_KEY[:8]}...")

    # Test 1: Small test swap MON → USDC (1% of balance)
    print("\n\n📊 Test 1: MON → USDC (1% test swap)")
    await test_swap_endpoint(
        token_in="MON",
        token_out="USDC",  # Or use contract address: "0x..."
        weight=1.0,  # 1% of balance
        desired_protocol="kuru"  # Specify protocol if needed
    )

    # Test 2: Swap back USDC → MON (1% test)
    print("\n\n📊 Test 2: USDC → MON (1% test swap)")
    await test_swap_endpoint(
        token_in="USDC",
        token_out="MON",
        weight=1.0
    )

    # Test 3: Check if we can use token addresses instead of symbols
    print("\n\n📊 Test 3: Using token address for tokenOut")
    print("(This might fail if you don't have the exact address)")
    # Example from docs: "0x350035555e10d9afaf1566aaebfced5ba6c27777"
    # You'd need to get the actual MON or USDC contract address on Monad

    print("\n\n" + "=" * 80)
    print("✅ Tests Complete!")
    print("\nNext Steps:")
    print("1. If swaps work, we can add MON to the symbol registry")
    print("2. Create a SymphonySpotTradingService (similar to symphony_service.py)")
    print("3. Integrate with bot configuration system")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
