#!/usr/bin/env python3
"""
Close AsterDEX Position

Test script to close an open position on AsterDEX.
"""

import asyncio
import sys
import os

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService
from core.common.logger import logger


async def close_position():
    """Close the BTC position on AsterDEX."""

    print("="*80)
    print("CLOSE ASTERDEX POSITION")
    print("="*80)
    print()

    # Initialize service
    service = AsterDEXV3LiveTradingService()

    # Check credentials
    print("🔑 Checking credentials...")
    if not service.user or not service.signer or not service.private_key:
        print("❌ Missing AsterDEX credentials in .env!")
        return

    print(f"   User wallet: {service.user}")
    print(f"   Signer wallet: {service.signer}")
    print()

    # Get current position from AsterDEX
    print("📊 Querying open positions...")
    positions = await service._get_position_risk()

    if not positions:
        print("❌ Failed to query positions from AsterDEX")
        return

    # Find BTC position
    btc_position = None
    for pos in positions:
        if pos.get('symbol') == 'BTCUSDT':
            position_amt = float(pos.get('positionAmt', 0))
            if position_amt != 0:
                btc_position = pos
                break

    if not btc_position:
        print("❌ No open BTC position found")
        print()
        print("Checking all positions:")
        for pos in positions:
            amt = float(pos.get('positionAmt', 0))
            if amt != 0:
                print(f"   - {pos.get('symbol')}: {amt}")
        return

    # Display position info
    position_amt = float(btc_position.get('positionAmt', 0))
    entry_price = float(btc_position.get('entryPrice', 0))
    mark_price = float(btc_position.get('markPrice', 0))
    unrealized_pnl = float(btc_position.get('unRealizedProfit', 0))
    leverage = int(btc_position.get('leverage', 1))

    print("✅ Found BTC position:")
    print(f"   Symbol: BTCUSDT")
    print(f"   Position: {position_amt} BTC")
    print(f"   Entry Price: ${entry_price:,.2f}")
    print(f"   Current Price: ${mark_price:,.2f}")
    print(f"   Unrealized P&L: ${unrealized_pnl:.2f}")
    print(f"   Leverage: {leverage}x")
    print()

    # Confirm
    if '--confirm' not in sys.argv:
        print("⚠️  Use --confirm flag to close the position:")
        print("   python scripts/close_aster_position.py --confirm")
        return

    print("="*80)
    print("CLOSING POSITION")
    print("="*80)
    print()

    # Close position via market order
    # The service expects batch_id and user_id, but we can get them from the position
    # For now, let's close directly via API

    print("🔄 Placing market close order...")

    try:
        # Determine close side (opposite of position)
        close_side = "SELL" if position_amt > 0 else "BUY"
        close_quantity = abs(position_amt)

        # Place market close order
        close_result = await service._place_market_order(
            symbol="BTCUSDT",
            side=close_side,
            quantity=close_quantity,
            leverage=leverage
        )

        if close_result and "orderId" in close_result:
            close_order_id = close_result["orderId"]
            print(f"✅ Close order placed successfully!")
            print(f"   Order ID: {close_order_id}")
            print()

            # Wait for settlement
            print("⏳ Waiting 2s for settlement...")
            await asyncio.sleep(2)

            # Verify position is closed
            print("🔍 Verifying position closed...")
            positions_after = await service._get_position_risk()

            for pos in positions_after:
                if pos.get('symbol') == 'BTCUSDT':
                    final_amt = float(pos.get('positionAmt', 0))
                    if final_amt == 0:
                        print("✅ Position successfully closed!")
                        print()
                        print(f"   Final P&L: ${unrealized_pnl:.2f}")
                        print(f"   Entry: ${entry_price:,.2f}")
                        print(f"   Exit: ${mark_price:,.2f}")
                        print(f"   Price Change: {((mark_price - entry_price) / entry_price * 100):.3f}%")
                    else:
                        print(f"⚠️  Position still open: {final_amt} BTC")
                    break

        else:
            print("❌ Failed to place close order")
            print(f"   Response: {close_result}")

    except Exception as e:
        print(f"❌ Error closing position: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print()
    asyncio.run(close_position())
    print()
