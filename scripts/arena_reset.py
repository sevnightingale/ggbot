#!/usr/bin/env python3
"""
Arena Reset Script - Bulk reset registered arena bots to $10k.

Usage:
    # Dry run — Season 2 (default)
    python scripts/arena_reset.py

    # Dry run — specific season
    python scripts/arena_reset.py --season 2

    # Execute reset
    python scripts/arena_reset.py --season 2 --execute

    # With notification
    python scripts/arena_reset.py --season 2 --execute --notify

    # Legacy Season 1 mode (uses is_public_performance flag)
    python scripts/arena_reset.py --season 1 --execute

This script:
1. Finds all registered bots for the given season
2. Closes any open positions
3. Resets each account to $10,000
4. Updates arena_registrations.starting_balance
5. Logs all operations
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


def get_arena_bots_s1() -> List[Dict[str, Any]]:
    """Get Season 1 bots (legacy: is_public_performance flag)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.config_id, c.config_name, c.user_id, c.state, c.trading_mode,
                    pa.current_balance, pa.total_pnl, pa.total_trades,
                    pa.win_trades, pa.loss_trades, pa.open_positions
                FROM configurations c
                LEFT JOIN paper_accounts pa ON c.config_id = pa.config_id
                WHERE c.is_public_performance = true AND c.trading_mode = 'paper'
                ORDER BY c.config_name
            """)
            columns = [
                'config_id', 'config_name', 'user_id', 'state', 'trading_mode',
                'current_balance', 'total_pnl', 'total_trades', 'win_trades',
                'loss_trades', 'open_positions'
            ]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_arena_bots_s2(season_id: int) -> List[Dict[str, Any]]:
    """Get bots registered for a season via arena_registrations table."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.config_id, c.config_name, c.user_id, c.state, c.trading_mode,
                    pa.current_balance, pa.total_pnl, pa.total_trades,
                    pa.win_trades, pa.loss_trades, pa.open_positions,
                    ar.id as registration_id
                FROM arena_registrations ar
                JOIN configurations c ON ar.config_id = c.config_id
                LEFT JOIN paper_accounts pa ON c.config_id = pa.config_id
                WHERE ar.season_id = %s
                  AND ar.unregistered_at IS NULL
                  AND c.trading_mode = 'paper'
                ORDER BY c.config_name
            """, (season_id,))
            columns = [
                'config_id', 'config_name', 'user_id', 'state', 'trading_mode',
                'current_balance', 'total_pnl', 'total_trades', 'win_trades',
                'loss_trades', 'open_positions', 'registration_id'
            ]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


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


async def execute_reset(bots: List[Dict[str, Any]], season_id: int) -> List[Dict[str, Any]]:
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

    # Update arena_registrations with starting_balance for S2+
    if season_id >= 2:
        successful_ids = [r['config_id'] for r in results if r['success']]
        if successful_ids:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE arena_registrations
                        SET starting_balance = 10000
                        WHERE season_id = %s AND config_id = ANY(%s) AND unregistered_at IS NULL
                    """, (season_id, successful_ids))
                    conn.commit()
                    print(f"\n  Updated starting_balance for {len(successful_ids)} registrations")

    return results


def print_summary(bots: List[Dict[str, Any]], season_id: int, results: List[Dict[str, Any]] = None):
    """Print summary of arena bots and reset results."""
    print("\n" + "=" * 70)
    print(f"GGARENA SEASON {season_id} RESET SUMMARY")
    print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 70)

    if results:
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


async def send_notification(results: List[Dict[str, Any]], season_id: int):
    """Send notification about reset completion."""
    successful = len([r for r in results if r['success']])
    failed = len([r for r in results if not r['success']])

    message = f"""🏆 ggArena Season {season_id} Reset Complete

✓ {successful} bots reset to $10,000
✗ {failed} bots failed

Competition starts NOW! Good luck to all competitors."""

    print(f"\n📨 Notification (would be sent):\n{message}")


async def main():
    parser = argparse.ArgumentParser(description='Reset arena bots to $10k')
    parser.add_argument('--season', type=int, default=2, help='Season number (default: 2)')
    parser.add_argument('--execute', action='store_true', help='Actually execute the reset (default is dry run)')
    parser.add_argument('--notify', action='store_true', help='Send notification after reset')
    args = parser.parse_args()

    print(f"\n🏆 ggArena Season {args.season} Reset Script")
    print("-" * 40)

    # Get bots based on season
    if args.season == 1:
        bots = get_arena_bots_s1()
    else:
        bots = get_arena_bots_s2(args.season)

    if not bots:
        print(f"\n⚠️  No arena bots found for Season {args.season}")
        return

    if args.execute:
        print(f"\n🔄 Executing reset for {len(bots)} bots...\n")
        results = await execute_reset(bots, args.season)
        print_summary(bots, args.season, results)

        if args.notify:
            await send_notification(results, args.season)
    else:
        print_summary(bots, args.season)


if __name__ == "__main__":
    asyncio.run(main())
