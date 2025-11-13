#!/usr/bin/env python3
"""Test AsterDEX account endpoint"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService

async def main():
    service = AsterDEXV3LiveTradingService()

    print("🔍 Testing AsterDEX /fapi/v3/account endpoint...\n")

    account_data = await service._get_account_balance()

    if not account_data:
        print("❌ Failed to get account data")
        return

    print("✅ Account data received!\n")
    print("=" * 60)
    print("ACCOUNT SUMMARY")
    print("=" * 60)

    # Extract key fields
    total_wallet = float(account_data.get('totalWalletBalance', 0))
    total_unrealized = float(account_data.get('totalUnrealizedProfit', 0))
    total_margin = float(account_data.get('totalMarginBalance', 0))
    available = float(account_data.get('availableBalance', 0))

    print(f"Total Wallet Balance:      ${total_wallet:.2f}")
    print(f"Total Unrealized Profit:   ${total_unrealized:.2f}")
    print(f"Total Margin Balance:      ${total_margin:.2f}")
    print(f"Available Balance:         ${available:.2f}")

    print("\n" + "=" * 60)
    print("CALCULATED VALUES")
    print("=" * 60)

    total_equity = total_wallet + total_unrealized
    print(f"Total Equity:              ${total_equity:.2f}")
    print(f"  (wallet + unrealized)")

    print("\n" + "=" * 60)
    print("POSITION SIZING TEST")
    print("=" * 60)

    # Test different confidence levels
    test_confidences = [0.3, 0.5, 0.7, 1.0]

    for confidence in test_confidences:
        # Simulate CONFIDENCE_BASED sizing: confidence * max_position_percent * equity
        # Assuming max_position_percent = 20% (typical default)
        max_position_percent = 0.20
        position_size_usd = confidence * max_position_percent * total_equity

        print(f"\nConfidence {confidence:.1f}:")
        print(f"  Position size: ${position_size_usd:.2f}")
        print(f"  ({confidence*100:.0f}% × 20% × ${total_equity:.2f})")

        # With 10x leverage
        leverage = 10
        margin_required = position_size_usd / leverage
        print(f"  Margin required (10x): ${margin_required:.2f}")

        if margin_required <= available:
            print(f"  ✅ Can execute (available: ${available:.2f})")
        else:
            print(f"  ❌ Insufficient margin (available: ${available:.2f})")

    print("\n" + "=" * 60)
    print("RAW RESPONSE FIELDS")
    print("=" * 60)
    print(f"All fields returned:")
    for key, value in account_data.items():
        if key != 'assets':  # Skip assets array for brevity
            print(f"  {key}: {value}")

    # Show asset breakdown if available
    if 'assets' in account_data and isinstance(account_data['assets'], list):
        print(f"\nAsset breakdown ({len(account_data['assets'])} assets):")
        for asset in account_data['assets'][:5]:  # Show first 5
            asset_name = asset.get('asset', 'N/A')
            balance = float(asset.get('walletBalance', 0))
            unrealized = float(asset.get('unrealizedProfit', 0))
            if balance != 0 or unrealized != 0:  # Only show non-zero
                print(f"  {asset_name}: wallet=${balance:.2f}, unrealized=${unrealized:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
