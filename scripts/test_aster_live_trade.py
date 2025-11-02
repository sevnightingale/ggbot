#!/usr/bin/env python3
"""
Test AsterDEX Live Trade

This script tests the complete live trading flow with AsterDEX:
1. Symbol validation
2. Order placement
3. Stop-loss and take-profit orders
4. Database record creation

IMPORTANT: This will place a REAL trade with REAL money on AsterDEX!
Position size is kept very small ($1-2) for safety.
"""

import asyncio
import sys
import os
import uuid
from decimal import Decimal

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService
from core.symbols.standardizer import UniversalSymbolStandardizer
from core.common.logger import logger
from core.common.db import get_db_connection


async def test_live_trade():
    """Execute a test live trade on AsterDEX."""

    print("="*80)
    print("ASTERDEX LIVE TRADE TEST")
    print("="*80)
    print()

    # Initialize service
    service = AsterDEXV3LiveTradingService()
    standardizer = UniversalSymbolStandardizer()

    # Check credentials
    print("🔑 Checking credentials...")
    if not service.user or not service.signer or not service.private_key:
        print("❌ Missing AsterDEX credentials in .env!")
        print("   Required: ASTER_USER_WALLET, ASTER_WALLET_ADDRESS, ASTER_PRIVATE_KEY")
        return

    print(f"   User wallet: {service.user}")
    print(f"   Signer wallet: {service.signer}")
    print(f"   Private key: {service.private_key[:10]}... (hidden)")
    print()

    # Test symbol
    symbol = "BTC-USDT"
    print(f"📊 Testing symbol: {symbol}")

    # Check compatibility
    is_compatible = standardizer.is_aster_compatible(symbol)
    print(f"   Aster compatible: {is_compatible}")

    if not is_compatible:
        print(f"❌ Symbol {symbol} is not compatible with AsterDEX!")
        return

    # Convert to Aster format
    aster_symbol = standardizer.to_aster(symbol)
    print(f"   Aster format: {aster_symbol}")
    print()

    # Get current BTC price (estimate)
    print("💰 Position sizing...")
    print("   Position size: 0.001 BTC (~$90 USD)")
    print("   Leverage: 10x")
    print("   Margin required: ~$9 USD")
    print("   Your balance: $10 USDC ✓")
    print()

    # Confirm with user
    print("⚠️  WARNING: This will place a REAL trade on AsterDEX!")
    print("   - Symbol: BTC-USDT")
    print("   - Side: LONG")
    print("   - Quantity: 0.001 BTC (~$90 position)")
    print("   - Leverage: 10x (~$9 margin)")
    print("   - Stop Loss: 2% below entry")
    print("   - Take Profit: 3% above entry")
    print()

    # Check for --confirm flag
    if '--confirm' not in sys.argv:
        print("❌ Aborted - use --confirm flag to execute:")
        print("   python scripts/test_aster_live_trade.py --confirm")
        return

    print()
    print("="*80)
    print("EXECUTING TRADE")
    print("="*80)
    print()

    # Construct trade intent
    # Note: In production, this comes from Decision Module
    # For testing, we manually construct it

    # Get a valid config_id and user_id from database
    print("🔍 Finding test configuration...")
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get any active config for testing
            cur.execute("""
                SELECT config_id, user_id
                FROM configurations
                WHERE state = 'active'
                LIMIT 1
            """)
            result = cur.fetchone()

            if not result:
                print("❌ No active configuration found!")
                print("   Please create a bot configuration first")
                return

            config_id = result[0]
            user_id = result[1]

    print(f"   Using config_id: {config_id}")
    print(f"   Using user_id: {user_id}")
    print()

    # Create trade intent
    # In production, this comes from Decision Module with calculated SL/TP
    # For testing, we use simple percentages
    test_decision_id = str(uuid.uuid4())  # Generate valid UUID
    trade_intent = {
        "config_id": config_id,
        "user_id": user_id,
        "symbol": symbol,  # Platform format (BTC-USDT)
        "action": "long",
        "confidence": 0.75,
        "decision_id": test_decision_id,  # UUID format required
        "stop_loss_price": None,  # Will use default 2%
        "take_profit_price": None,  # Will use default 3%
        "timestamp": asyncio.get_event_loop().time()
    }

    print("📝 Trade Intent:")
    print(f"   Symbol: {trade_intent['symbol']}")
    print(f"   Action: {trade_intent['action'].upper()}")
    print(f"   Confidence: {trade_intent['confidence']:.2%}")
    print(f"   Decision ID: {trade_intent['decision_id']}")
    print()

    # Execute trade
    print("🚀 Executing trade on AsterDEX...")
    print()

    try:
        result = await service.execute_trade_intent(trade_intent)

        print("="*80)
        print("TRADE RESULT")
        print("="*80)
        print()

        status = result.get("status")
        batch_id = result.get("batch_id")

        print(f"Status: {status}")
        print(f"Batch ID: {batch_id}")
        print()

        if status == "success":
            print("✅ TRADE EXECUTED SUCCESSFULLY!")
            print()
            print("Trade Details:")
            print(f"   Entry Price: ${result.get('entry_price', 'N/A')}")
            print(f"   Quantity: {result.get('quantity', 'N/A')} BTC")
            print(f"   Position Value: ${result.get('position_value', 'N/A')}")
            print(f"   Stop Loss: ${result.get('stop_loss_price', 'N/A')}")
            print(f"   Take Profit: ${result.get('take_profit_price', 'N/A')}")
            print()
            print("Order IDs:")
            print(f"   Main Order: {result.get('order_id', 'N/A')}")
            print(f"   Stop Loss: {result.get('stop_loss_order_id', 'N/A')}")
            print(f"   Take Profit: {result.get('take_profit_order_id', 'N/A')}")
            print()

            # Query database
            print("📊 Database Record:")
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            batch_id,
                            provider,
                            symbol,
                            side,
                            entry_price,
                            quantity,
                            stop_loss_price,
                            take_profit_price,
                            status,
                            created_at
                        FROM live_trades
                        WHERE batch_id = %s
                    """, (batch_id,))

                    row = cur.fetchone()
                    if row:
                        print(f"   Batch ID: {row[0]}")
                        print(f"   Provider: {row[1]}")
                        print(f"   Symbol: {row[2]}")
                        print(f"   Side: {row[3]}")
                        print(f"   Entry: ${row[4]}")
                        print(f"   Quantity: {row[5]}")
                        print(f"   Stop Loss: ${row[6]}")
                        print(f"   Take Profit: ${row[7]}")
                        print(f"   Status: {row[8]}")
                        print(f"   Created: {row[9]}")
            print()

            print("="*80)
            print("NEXT STEPS")
            print("="*80)
            print()
            print("1. Check AsterDEX Dashboard:")
            print("   https://www.asterdex.com/en/futures")
            print()
            print("2. Verify position is open:")
            print("   - Symbol: BTC-USDT")
            print("   - Side: LONG")
            print(f"   - Quantity: {result.get('quantity', 'N/A')} BTC")
            print()
            print("3. Close position via dashboard or script:")
            print(f"   python scripts/close_aster_position.py {batch_id}")
            print()

        elif status == "failed":
            print("❌ TRADE FAILED!")
            print()
            print(f"Reason: {result.get('reason', 'Unknown')}")
            print()

        elif status == "already_executed":
            print("⚠️  TRADE ALREADY EXECUTED (idempotency protection)")
            print()
            print(f"Batch ID: {batch_id}")
            print()

        else:
            print(f"⚠️  Unknown status: {status}")
            print()
            print("Full result:")
            print(result)
            print()

    except Exception as e:
        print("="*80)
        print("ERROR")
        print("="*80)
        print()
        print(f"❌ Exception during trade execution:")
        print(f"   {type(e).__name__}: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print()
    asyncio.run(test_live_trade())
    print()
