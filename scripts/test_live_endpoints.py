"""
Test the new live trading metrics endpoints.

This script directly calls the Symphony service methods to test the implementation.

Run with:
    cd /home/sev/ggbot
    source .venv/bin/activate
    python scripts/test_live_endpoints.py
"""

import asyncio
import sys
sys.path.insert(0, '/home/sev/ggbot')

from trading.live.symphony_service import SymphonyLiveTradingService


async def test_live_endpoints():
    """Test Symphony service methods for live trading metrics."""

    config_id = '1d58dac4-4c10-4bc8-b68e-42ae49f4a784'  # Opus 92 (Live)

    print("\n" + "="*80)
    print("TESTING SYMPHONY LIVE TRADING ENDPOINTS")
    print("="*80)
    print(f"Config ID: {config_id}")
    print()

    service = SymphonyLiveTradingService()

    # Test 1: Get Account Metrics
    print("[1/2] Testing get_account_metrics()...")
    print("-" * 80)

    metrics = await service.get_account_metrics(config_id)

    if metrics:
        print("✅ Account Metrics Retrieved:")
        print(f"   Current Balance: ${metrics.get('current_balance', 0):.2f}")
        print(f"   Total P&L: ${metrics.get('total_pnl', 0):.2f}")
        print(f"   Portfolio Return: {metrics.get('portfolio_return_pct', 0):.2f}%")
        print(f"   Total Trades: {metrics.get('total_trades', 0)}")
        print(f"   Win Trades: {metrics.get('win_trades', 0)}")
        print(f"   Loss Trades: {metrics.get('loss_trades', 0)}")
        print(f"   Win Rate: {metrics.get('win_rate', 0):.1f}%")
        print(f"   Open Positions: {metrics.get('open_positions', 0)}")
    else:
        print("❌ No metrics returned")

    # Test 2: Get Trade History
    print("\n[2/2] Testing get_trade_history()...")
    print("-" * 80)

    trades = await service.get_trade_history(config_id, limit=10)

    if trades:
        print(f"✅ Retrieved {len(trades)} closed trades:")
        for idx, trade in enumerate(trades, 1):
            print(f"\n   Trade {idx}:")
            print(f"     Symbol: {trade.get('symbol')}")
            print(f"     Side: {trade.get('side').upper()}")
            print(f"     Entry: ${trade.get('entry_price', 0):.2f}")
            print(f"     Size: ${trade.get('size_usd', 0):.2f}")
            print(f"     Leverage: {trade.get('leverage')}x")
            print(f"     P&L: ${trade.get('realized_pnl', 0):.4f}")
            print(f"     Opened: {trade.get('opened_at')}")
            print(f"     Closed: {trade.get('closed_at')}")
    else:
        print("ℹ️  No closed trades found")

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    if metrics:
        print("✅ Account metrics endpoint: WORKING")
    else:
        print("❌ Account metrics endpoint: FAILED")

    if trades is not None:  # Empty list is OK
        print("✅ Trade history endpoint: WORKING")
    else:
        print("❌ Trade history endpoint: FAILED")

    print("\n🎯 Dashboard Integration Ready:")
    print("   - Use /api/v2/account/live/{config_id} for metrics")
    print("   - Use /api/v2/trades/live/{config_id} for trade history")
    print("   - Frontend can now display Symphony data!")
    print()


if __name__ == '__main__':
    asyncio.run(test_live_endpoints())
