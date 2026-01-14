#!/usr/bin/env python3
"""
Cleanup script for phantom Symphony live_trades records.

These are records where:
- We called Symphony's batch-open API
- Symphony returned a batchId (we stored it)
- But successful=0 (no trades actually executed)
- Result: our DB has "open" trades that don't exist in Symphony

This script:
1. Fetches all "open" live_trades for a config
2. Checks which batch_ids have ACTUAL positions in Symphony
3. Marks phantom records as closed with reason='phantom_cleanup'

Usage:
    python scripts/cleanup_phantom_symphony_trades.py --config-id <UUID> [--execute]

    Without --execute, runs in dry-run mode (shows what would be cleaned up).
"""

import argparse
import asyncio
import aiohttp
from datetime import datetime

import sys
sys.path.insert(0, '/home/sev/ggbot')

from core.common.db import get_db_connection
from core.auth.vault_utils import VaultManager


async def get_symphony_batch_positions(api_key: str, agent_id: str) -> dict:
    """
    Get all batches and their positions from Symphony.
    Returns dict mapping batch_id -> list of positions
    """
    base_url = "https://api.symphony.io"
    batch_positions = {}

    async with aiohttp.ClientSession() as session:
        # First get all batches
        async with session.get(
            f"{base_url}/agent/batches",
            params={"agentId": agent_id},
            headers={"x-api-key": api_key}
        ) as resp:
            if resp.status != 200:
                print(f"Failed to get batches: {resp.status}")
                return {}
            data = await resp.json()
            batches = data.get('batches', [])

        print(f"Found {len(batches)} total batches in Symphony")

        # For each batch, get its positions
        for batch in batches:
            batch_id = batch.get('batchId')
            if not batch_id:
                continue

            async with session.get(
                f"{base_url}/agent/batch-positions",
                params={"agentId": agent_id, "batchId": batch_id},
                headers={"x-api-key": api_key}
            ) as resp:
                if resp.status == 200:
                    batch_data = await resp.json()
                    positions = batch_data.get('positions', [])
                    orders = batch_data.get('orders', [])

                    # A batch has "real" trades if it has positions or orders
                    if positions or orders:
                        batch_positions[batch_id] = {
                            'positions': positions,
                            'orders': orders,
                            'positions_count': batch_data.get('positionsCount', 0),
                            'orders_count': batch_data.get('ordersCount', 0)
                        }

    print(f"Found {len(batch_positions)} batches with actual positions/orders")
    return batch_positions


async def cleanup_phantom_trades(config_id: str, execute: bool = False):
    """
    Clean up phantom live_trades records for a config.
    """
    print(f"\n{'='*60}")
    print(f"PHANTOM SYMPHONY TRADES CLEANUP")
    print(f"Config ID: {config_id}")
    print(f"Mode: {'EXECUTE' if execute else 'DRY-RUN'}")
    print(f"{'='*60}\n")

    # Get config details
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT config_name, user_id, symphony_agent_id, trading_mode
                FROM configurations
                WHERE config_id = %s
            """, (config_id,))
            result = cur.fetchone()

            if not result:
                print(f"ERROR: Config not found: {config_id}")
                return

            config_name, user_id, agent_id, trading_mode = result

            if trading_mode != 'symphony':
                print(f"ERROR: Config is not Symphony mode (mode={trading_mode})")
                return

            print(f"Config: {config_name}")
            print(f"Agent ID: {agent_id}")

            # Get all "open" live_trades
            cur.execute("""
                SELECT batch_id, created_at
                FROM live_trades
                WHERE config_id = %s AND closed_at IS NULL
                ORDER BY created_at ASC
            """, (config_id,))

            open_trades = cur.fetchall()
            print(f"\nFound {len(open_trades)} 'open' trades in our database")

    if not open_trades:
        print("No open trades to clean up!")
        return

    # Get Symphony credentials and fetch real positions
    creds = await VaultManager.get_symphony_credential(user_id)
    if not creds:
        print("ERROR: No Symphony credentials found")
        return

    api_key = creds['api_key']

    print("\nFetching actual positions from Symphony...")
    symphony_batches = await get_symphony_batch_positions(api_key, agent_id)

    # Categorize our trades
    real_trades = []
    phantom_trades = []

    for batch_id, created_at in open_trades:
        if batch_id in symphony_batches:
            batch_info = symphony_batches[batch_id]
            # Check if there are actual open positions (not just closed ones)
            open_positions = [p for p in batch_info['positions'] if p.get('status', '').lower() != 'closed']
            if open_positions:
                real_trades.append((batch_id, created_at, len(open_positions)))
            else:
                # Batch exists but all positions are closed
                phantom_trades.append((batch_id, created_at, 'positions_closed'))
        else:
            # Batch has no positions at all
            phantom_trades.append((batch_id, created_at, 'no_positions'))

    print(f"\n{'='*60}")
    print(f"ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Real trades (have open positions): {len(real_trades)}")
    print(f"Phantom trades (no real positions): {len(phantom_trades)}")

    if real_trades:
        print(f"\n--- Real Trades (will keep open) ---")
        for batch_id, created, pos_count in real_trades[:5]:
            print(f"  {batch_id} | {created} | {pos_count} open positions")
        if len(real_trades) > 5:
            print(f"  ... and {len(real_trades) - 5} more")

    if phantom_trades:
        print(f"\n--- Phantom Trades (will mark closed) ---")
        for batch_id, created, reason in phantom_trades[:10]:
            print(f"  {batch_id} | {created} | {reason}")
        if len(phantom_trades) > 10:
            print(f"  ... and {len(phantom_trades) - 10} more")

    if not phantom_trades:
        print("\nNo phantom trades to clean up!")
        return

    if not execute:
        print(f"\n{'='*60}")
        print(f"DRY-RUN: Would mark {len(phantom_trades)} records as closed")
        print(f"Run with --execute to apply changes")
        print(f"{'='*60}")
        return

    # Execute the cleanup
    print(f"\n{'='*60}")
    print(f"EXECUTING CLEANUP...")
    print(f"{'='*60}")

    phantom_batch_ids = [batch_id for batch_id, _, _ in phantom_trades]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Mark phantom trades as closed
            # Note: live_trades doesn't have close_reason, just closed_at
            cur.execute("""
                UPDATE live_trades
                SET closed_at = NOW()
                WHERE config_id = %s
                AND batch_id = ANY(%s)
                AND closed_at IS NULL
            """, (config_id, phantom_batch_ids))

            updated = cur.rowcount
            conn.commit()

    print(f"\n✅ Marked {updated} phantom records as closed (phantom_cleanup)")

    # Verify
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM live_trades
                WHERE config_id = %s AND closed_at IS NULL
            """, (config_id,))
            remaining = cur.fetchone()[0]

    print(f"\nRemaining open trades: {remaining}")


def main():
    parser = argparse.ArgumentParser(description='Cleanup phantom Symphony live_trades')
    parser.add_argument('--config-id', required=True, help='Configuration ID to clean up')
    parser.add_argument('--execute', action='store_true', help='Actually execute cleanup (default: dry-run)')

    args = parser.parse_args()

    asyncio.run(cleanup_phantom_trades(args.config_id, args.execute))


if __name__ == '__main__':
    main()
