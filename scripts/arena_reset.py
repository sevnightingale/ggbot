#!/usr/bin/env python3
"""
Arena Reset Script - Bulk reset all registered arena bots to $10k.

Usage:
    # Dry run (preview only)
    python scripts/arena_reset.py

    # Execute reset
    python scripts/arena_reset.py --execute

    # With notification
    python scripts/arena_reset.py --execute --notify

This script:
1. Finds all bots with is_public_performance = true
2. Closes any open positions
3. Resets each account to $10,000
4. Logs all operations
5. Optionally sends notification summary
"""

import asyncio
import argparse
from datetime import datetime
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.common.db import get_db_connection
from core.common.logger import logger
from trading.paper.supabase_service import SupabasePaperTradingService


def get_arena_bots() -> List[Dict[str, Any]]:
    """Get all bots registered for arena (is_public_performance = true)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.config_id,
                    c.config_name,
                    c.user_id,
                    c.state,
                    c.trading_mode,
                    pa.current_balance,
                    pa.total_pnl,
                    pa.total_trades,
                    pa.win_trades,
                    pa.loss_trades,
                    pa.open_positions
                FROM configurations c
                LEFT JOIN paper_accounts pa ON c.config_id = pa.config_id
                WHERE c.is_public_performance = true
                AND c.trading_mode = 'paper'
                ORDER BY c.config_name
            """)

            columns = [
                'config_id', 'config_name', 'user_id', 'state', 'trading_mode',
                'current_balance', 'total_pnl', 'total_trades', 'win_trades',
                'loss_trades', 'open_positions'
            ]

            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]


async def reset_bot(paper_trading: SupabasePaperTradingService, bot: Dict[str, Any]) -> Dict[str, Any]:
    """Reset a single bot's account."""
    try:
        result = await paper_trading.reset_account(
            config_id=str(bot['config_id']),
            user_id=str(bot['user_id'])
        )
        return {
            'config_id': bot['config_id'],
            'config_name': bot['config_name'],
            'success': result['status'] == 'success',
            'positions_closed': result.get('positions_closed', 0),
            'old_balance': bot['current_balance'],
            'new_balance': result.get('new_balance', 10000),
            'error': result.get('reason') if result['status'] != 'success' else None
        }
    except Exception as e:
        return {
            'config_id': bot['config_id'],
            'config_name': bot['config_name'],
            'success': False,
            'error': str(e)
        }


async def execute_reset(bots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Execute reset for all arena bots."""
    paper_trading = SupabasePaperTradingService()
    results = []

    for bot in bots:
        print(f"  Resetting: {bot['config_name']}...", end=" ", flush=True)
        result = await reset_bot(paper_trading, bot)
        results.append(result)

        if result['success']:
            print(f"✓ ${result['old_balance']:,.2f} → $10,000.00")
        else:
            print(f"✗ FAILED: {result['error']}")

    return results


def print_summary(bots: List[Dict[str, Any]], results: List[Dict[str, Any]] = None):
    """Print summary of arena bots and reset results."""
    print("\n" + "=" * 70)
    print("GGARENA RESET SUMMARY")
    print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 70)

    if results:
        # Post-reset summary
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]

        print(f"\n✓ Successfully reset: {len(successful)} bots")
        print(f"✗ Failed: {len(failed)} bots")

        if successful:
            total_old = sum(r['old_balance'] or 0 for r in successful)
            positions_closed = sum(r['positions_closed'] for r in successful)
            print(f"\nTotal previous equity: ${total_old:,.2f}")
            print(f"Total positions closed: {positions_closed}")
            print(f"All accounts now at: $10,000.00")

        if failed:
            print("\n⚠️  FAILED RESETS:")
            for r in failed:
                print(f"  - {r['config_name']}: {r['error']}")
    else:
        # Pre-reset summary (dry run)
        print(f"\nFound {len(bots)} registered arena bots:\n")

        print(f"{'Bot Name':<30} {'State':<10} {'Balance':>12} {'P&L':>12} {'Trades':>8} {'Open':>6}")
        print("-" * 80)

        for bot in bots:
            name = (bot['config_name'] or 'Unnamed')[:28]
            state = bot['state'] or 'unknown'
            balance = f"${bot['current_balance']:,.2f}" if bot['current_balance'] else "N/A"
            pnl = f"${bot['total_pnl']:,.2f}" if bot['total_pnl'] else "$0.00"
            trades = bot['total_trades'] or 0
            open_pos = bot['open_positions'] or 0

            print(f"{name:<30} {state:<10} {balance:>12} {pnl:>12} {trades:>8} {open_pos:>6}")

        total_balance = sum(b['current_balance'] or 0 for b in bots)
        total_pnl = sum(b['total_pnl'] or 0 for b in bots)
        total_trades = sum(b['total_trades'] or 0 for b in bots)
        total_open = sum(b['open_positions'] or 0 for b in bots)

        print("-" * 80)
        print(f"{'TOTALS':<30} {'':<10} ${total_balance:>11,.2f} ${total_pnl:>11,.2f} {total_trades:>8} {total_open:>6}")

        print(f"\n⚠️  This is a DRY RUN. No changes made.")
        print(f"    Run with --execute to reset all {len(bots)} bots to $10,000.00")


async def send_notification(results: List[Dict[str, Any]]):
    """Send notification about reset completion (placeholder for Telegram/email)."""
    successful = len([r for r in results if r['success']])
    failed = len([r for r in results if not r['success']])

    message = f"""🏆 ggArena Season 1 Reset Complete

✓ {successful} bots reset to $10,000
✗ {failed} bots failed

Competition starts NOW! Good luck to all competitors."""

    print(f"\n📨 Notification (would be sent):\n{message}")
    # TODO: Integrate with actual notification service
    # from signals.telegram_publisher import send_admin_notification
    # await send_admin_notification(message)


async def main():
    parser = argparse.ArgumentParser(description='Reset all arena bots to $10k')
    parser.add_argument('--execute', action='store_true', help='Actually execute the reset (default is dry run)')
    parser.add_argument('--notify', action='store_true', help='Send notification after reset')
    args = parser.parse_args()

    print("\n🏆 ggArena Reset Script")
    print("-" * 40)

    # Get all arena bots
    bots = get_arena_bots()

    if not bots:
        print("\n⚠️  No arena bots found (is_public_performance = true)")
        return

    if args.execute:
        print(f"\n🔄 Executing reset for {len(bots)} bots...\n")
        results = await execute_reset(bots)
        print_summary(bots, results)

        if args.notify:
            await send_notification(results)
    else:
        print_summary(bots)


if __name__ == "__main__":
    asyncio.run(main())
