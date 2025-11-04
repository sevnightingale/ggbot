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

    # Extract USDT balance if available
    if isinstance(balance_data, list):
        for asset in balance_data:
            if asset.get('asset') == 'USDT':
                print("USDT Balance Details:")
                print(f"  ✅ Account Balance (availableBalance): ${asset.get('availableBalance', 'N/A')}")
                print(f"     └─ SOURCE OF TRUTH for trading equity")
                print()
                print(f"  Settled Balance (balance): ${asset.get('balance', 'N/A')}")
                print(f"     └─ Excludes unrealized P&L")
                print()
                print(f"  Cross Wallet Balance: ${asset.get('crossWalletBalance', 'N/A')}")
                print(f"  Cross Unrealized P&L: ${asset.get('crossUnPnl', 'N/A')}")
                print(f"  Max Withdraw: ${asset.get('maxWithdrawAmount', 'N/A')}")
                print()


if __name__ == "__main__":
    asyncio.run(main())
