"""
Test AsterDEX account balance query.

Tests the GET /fapi/v3/balance endpoint to see account equity data.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService


async def main():
    """Test Aster balance query."""

    print("Testing AsterDEX Account Balance Query")
    print("=" * 60)

    # Initialize service
    service = AsterDEXV3LiveTradingService()

    # Check credentials
    if not service.user or not service.signer or not service.private_key:
        print("❌ Missing Aster credentials in .env")
        print("   Required: ASTER_USER_WALLET, ASTER_WALLET_ADDRESS, ASTER_PRIVATE_KEY")
        return

    print(f"User Wallet: {service.user}")
    print(f"Signer: {service.signer}")
    print()

    # Query balance
    print("Querying account balance...")
    balance_data = await service._get_account_balance()

    if not balance_data:
        print("❌ Failed to get balance data")
        return

    print("✅ Balance data retrieved:")
    print()

    # Parse balance data
    import json
    print(json.dumps(balance_data, indent=2))
    print()

    # Extract stablecoin balances (USDT + USDC)
    if isinstance(balance_data, list):
        total_equity = 0.0

        for asset in balance_data:
            if asset.get('asset') in ['USDT', 'USDC']:
                asset_name = asset.get('asset')
                cross_wallet = float(asset.get('crossWalletBalance', 0))
                total_equity += cross_wallet

                print(f"{asset_name} Balance:")
                print(f"  Equity (crossWalletBalance): ${cross_wallet}")
                print(f"  Available: ${asset.get('availableBalance', 'N/A')}")
                print(f"  Settled: ${asset.get('balance', 'N/A')}")
                print(f"  Unrealized P&L: ${asset.get('crossUnPnl', 'N/A')}")
                print()

        if total_equity > 0:
            print(f"✅ TOTAL ACCOUNT EQUITY (USDT + USDC): ${total_equity:.2f}")
            print(f"   └─ This is the SOURCE OF TRUTH for charts")
            print()


if __name__ == "__main__":
    asyncio.run(main())
