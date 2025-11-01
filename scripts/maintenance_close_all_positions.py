#!/usr/bin/env python3
"""
Maintenance Script: Close All Open Paper Positions

This script:
1. Queries all open paper trading positions
2. Fetches current market prices
3. Closes all positions with realized P&L
4. Saves summary to JSON file

Usage:
    python scripts/maintenance_close_all_positions.py

Output:
    - scripts/maintenance_closed_positions.json (summary of closed positions)
    - Console summary of closed positions
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.common.db import get_db_connection
from trading.paper.live_price_service import LivePriceService


def get_open_positions():
    """Query all open paper trading positions."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    pt.id as trade_id,
                    pt.config_id,
                    pt.user_id,
                    pt.symbol,
                    pt.side,
                    pt.quantity,
                    pt.entry_price,
                    pt.current_price,
                    pt.unrealized_pnl,
                    pt.stop_loss,
                    pt.take_profit,
                    pt.confidence,
                    pt.created_at,
                    pa.current_balance
                FROM paper_trades pt
                JOIN paper_accounts pa ON pt.config_id = pa.config_id
                WHERE pt.status = 'open'
                ORDER BY pt.created_at
            """)

            columns = [desc[0] for desc in cur.description]
            results = cur.fetchall()

            return [dict(zip(columns, row)) for row in results]


def close_position(trade_id, exit_price, exit_reason="maintenance_close"):
    """Close a position and calculate realized P&L."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get position details
            cur.execute("""
                SELECT
                    config_id,
                    symbol,
                    side,
                    quantity,
                    entry_price
                FROM paper_trades
                WHERE id = %s
            """, (trade_id,))

            position = cur.fetchone()
            if not position:
                return None

            config_id, symbol, side, quantity, entry_price = position

            # Calculate realized P&L
            if side == 'long':
                pnl = (exit_price - entry_price) * quantity
            else:  # short
                pnl = (entry_price - exit_price) * quantity

            # Update trade
            cur.execute("""
                UPDATE paper_trades
                SET
                    status = 'closed',
                    exit_price = %s,
                    current_price = %s,
                    realized_pnl = %s,
                    unrealized_pnl = 0,
                    exit_reason = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (exit_price, exit_price, pnl, exit_reason, trade_id))

            # Update account balance
            cur.execute("""
                UPDATE paper_accounts
                SET
                    current_balance = current_balance + %s,
                    total_pnl = total_pnl + %s,
                    total_trades = total_trades + 1,
                    winning_trades = winning_trades + CASE WHEN %s > 0 THEN 1 ELSE 0 END,
                    losing_trades = losing_trades + CASE WHEN %s <= 0 THEN 1 ELSE 0 END,
                    updated_at = NOW()
                WHERE config_id = %s
            """, (pnl, pnl, pnl, pnl, config_id))

            conn.commit()

            return {
                'trade_id': trade_id,
                'config_id': config_id,
                'symbol': symbol,
                'side': side,
                'quantity': float(quantity),
                'entry_price': float(entry_price),
                'exit_price': float(exit_price),
                'realized_pnl': float(pnl),
                'exit_reason': exit_reason
            }


def main():
    print("=" * 80)
    print("MAINTENANCE: Closing All Open Paper Positions")
    print("=" * 80)
    print()

    # Step 1: Get all open positions
    print("📊 Querying open positions...")
    open_positions = get_open_positions()

    if not open_positions:
        print("✅ No open positions found. Nothing to close.")
        return

    print(f"Found {len(open_positions)} open positions")
    print()

    # Step 2: Show summary
    total_unrealized = sum(float(p['unrealized_pnl'] or 0) for p in open_positions)
    symbols = set(p['symbol'] for p in open_positions)

    print(f"Positions across {len(symbols)} symbols:")
    for symbol in sorted(symbols)[:10]:
        count = sum(1 for p in open_positions if p['symbol'] == symbol)
        print(f"  {symbol}: {count} positions")

    if len(symbols) > 10:
        print(f"  ... and {len(symbols) - 10} more symbols")

    print()
    print(f"Total unrealized P&L: ${total_unrealized:,.2f}")
    print()

    # Step 3: Confirm closure
    print("⚠️  WARNING: This will close ALL open paper trading positions!")
    print()
    confirm = input("Type 'CLOSE' to proceed: ").strip()

    if confirm != 'CLOSE':
        print("❌ Cancelled. No positions were closed.")
        return

    print()

    # Step 4: Initialize price service
    print("💰 Fetching current market prices...")
    price_service = LivePriceService()

    # Get unique symbols
    unique_symbols = list(set(p['symbol'] for p in open_positions))

    # Fetch prices in batch
    prices = {}
    for symbol in unique_symbols:
        try:
            price_data = price_service.get_price(symbol)
            if price_data and price_data.get('price'):
                prices[symbol] = price_data['price']
            else:
                print(f"⚠️  No price found for {symbol}, using current_price from DB")
        except Exception as e:
            print(f"⚠️  Error fetching price for {symbol}: {e}")

    print(f"✅ Fetched prices for {len(prices)}/{len(unique_symbols)} symbols")
    print()

    # Step 5: Close all positions
    print("🔄 Closing positions...")
    closed_positions = []
    failed_positions = []

    for position in open_positions:
        trade_id = position['trade_id']
        symbol = position['symbol']

        # Use fetched price or fall back to DB current_price
        exit_price = prices.get(symbol) or float(position['current_price'])

        try:
            result = close_position(trade_id, exit_price, "maintenance_close")
            if result:
                closed_positions.append(result)
                print(f"✅ Closed {symbol} position (P&L: ${result['realized_pnl']:,.2f})")
            else:
                failed_positions.append({'trade_id': trade_id, 'symbol': symbol, 'error': 'Not found'})
        except Exception as e:
            failed_positions.append({'trade_id': trade_id, 'symbol': symbol, 'error': str(e)})
            print(f"❌ Failed to close {symbol}: {e}")

    print()

    # Step 6: Save summary
    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'maintenance_closed_positions.json'
    )

    summary_data = {
        'closed_at': datetime.utcnow().isoformat(),
        'total_positions': len(open_positions),
        'successfully_closed': len(closed_positions),
        'failed': len(failed_positions),
        'total_realized_pnl': sum(p['realized_pnl'] for p in closed_positions),
        'closed_positions': closed_positions,
        'failed_positions': failed_positions
    }

    with open(output_file, 'w') as f:
        json.dump(summary_data, f, indent=2, default=str)

    print(f"💾 Summary saved to: {output_file}")
    print()

    # Step 7: Final summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total positions: {len(open_positions)}")
    print(f"Successfully closed: {len(closed_positions)}")
    print(f"Failed: {len(failed_positions)}")
    print(f"Total realized P&L: ${summary_data['total_realized_pnl']:,.2f}")
    print()

    if failed_positions:
        print("⚠️  Failed positions:")
        for fp in failed_positions:
            print(f"  {fp['trade_id']} ({fp['symbol']}): {fp['error']}")
        print()

    print("✅ Maintenance complete. All positions are now closed.")
    print()


if __name__ == '__main__':
    main()
