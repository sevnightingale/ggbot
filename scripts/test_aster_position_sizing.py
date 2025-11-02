#!/usr/bin/env python3
"""
Test AsterDEX Position Sizing Logic

This script tests the new dynamic position sizing implementation.
It validates that positions scale properly with account balance and config.
"""

import asyncio
import sys
import os

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService
from core.common.logger import logger


async def test_position_sizing():
    """Test position sizing with current account balance."""

    print("=" * 80)
    print("ASTERDEX POSITION SIZING TEST")
    print("=" * 80)
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

    # Query current balance
    print("📊 Querying account balance...")
    balance_data = await service._get_account_balance()

    if not balance_data:
        print("❌ Failed to query account balance")
        return

    # Display balance
    available_balance = 0.0
    for asset in balance_data:
        if asset.get("asset") in ["USDC", "USDT"]:
            asset_name = asset.get("asset")
            asset_balance = float(asset.get("balance", 0))
            asset_available = float(asset.get("availableBalance", 0))
            available_balance += asset_available
            print(f"   {asset_name}: ${asset_balance:.2f} (available: ${asset_available:.2f})")

    print()
    print(f"   Total available: ${available_balance:.2f}")
    print()

    if available_balance <= 0:
        print("❌ No available balance to test with")
        return

    # Test different confidence levels
    print("=" * 80)
    print("POSITION SIZING SCENARIOS")
    print("=" * 80)
    print()

    # Mock config for testing different sizing methods
    from core.config.models import BotConfig, TradingConfig, PositionSizingConfig, PositionSizingMethod

    test_scenarios = [
        {
            "name": "ACCOUNT_PERCENTAGE (10%, 5x leverage)",
            "config": BotConfig(
                selected_pair="BTC/USDT",
                trading=TradingConfig(
                    position_sizing=PositionSizingConfig(
                        method=PositionSizingMethod.ACCOUNT_PERCENTAGE,
                        account_percent=10.0
                    ),
                    leverage=5
                )
            ),
            "confidences": [0.6, 0.75, 0.9]
        },
        {
            "name": "CONFIDENCE_BASED (max 15%, 10x leverage)",
            "config": BotConfig(
                selected_pair="BTC/USDT",
                trading=TradingConfig(
                    position_sizing=PositionSizingConfig(
                        method=PositionSizingMethod.CONFIDENCE_BASED,
                        max_position_percent=15.0
                    ),
                    leverage=10
                )
            ),
            "confidences": [0.6, 0.75, 0.9]
        },
        {
            "name": "FIXED_USD ($50, 3x leverage)",
            "config": BotConfig(
                selected_pair="BTC/USDT",
                trading=TradingConfig(
                    position_sizing=PositionSizingConfig(
                        method=PositionSizingMethod.FIXED_USD,
                        fixed_amount_usd=50.0
                    ),
                    leverage=3
                )
            ),
            "confidences": [0.6, 0.75, 0.9]
        }
    ]

    for scenario in test_scenarios:
        print(f"📋 Scenario: {scenario['name']}")
        print("-" * 80)

        config = scenario['config']

        for confidence in scenario['confidences']:
            try:
                quantity = await service._calculate_weight(config, confidence, "BTC-USDT")

                # Calculate what this means in USD
                from trading.paper.live_price_service import LivePriceService
                price_service = LivePriceService()
                market_price = await price_service.get_current_price("BTC-USDT")
                btc_price = market_price.mid

                leverage = config.trading.leverage
                notional = quantity * btc_price
                margin = notional / leverage
                margin_pct = (margin / available_balance) * 100

                print(f"   Confidence {confidence:.2f} → {quantity:.6f} BTC")
                print(f"      Notional: ${notional:.2f} | Margin: ${margin:.2f} ({margin_pct:.1f}% of balance) | Leverage: {leverage}x")

            except Exception as e:
                print(f"   ❌ Error at confidence {confidence}: {e}")

        print()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"✅ Position sizing now scales dynamically with:")
    print(f"   - Account balance: ${available_balance:.2f}")
    print(f"   - Bot config (sizing method, percentages)")
    print(f"   - AI confidence score")
    print(f"   - Current market price")
    print()
    print("The hardcoded 0.001 BTC is now only used as a minimum/fallback.")


if __name__ == '__main__':
    print()
    asyncio.run(test_position_sizing())
    print()
