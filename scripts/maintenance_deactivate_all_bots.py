#!/usr/bin/env python3
"""
Maintenance Script: Deactivate All Active Bots

This script:
1. Queries all active autonomous trading bot configurations
2. Excludes signal_validation configs (those remain active)
3. Saves their config_ids to a JSON file (for restoration)
4. Deactivates all bots (sets state='inactive')
5. Stops scheduler jobs via API

Usage:
    python scripts/maintenance_deactivate_all_bots.py

Output:
    - scripts/maintenance_backup_active_bots.json (list of deactivated bots)
    - Console summary of deactivated bots

Note:
    Signal validation configs are intentionally preserved and will continue
    processing ggShot signals during maintenance.
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.common.db import get_db_connection
import requests


def get_active_bots():
    """Query all active bot configurations (excluding signal_validation configs)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    user_id,
                    config_type,
                    config_data->>'symbol' as symbol,
                    config_data->>'timeframe' as timeframe,
                    created_at
                FROM configurations
                WHERE state = 'active'
                  AND (config_type IS NULL OR config_type != 'signal_validation')
                ORDER BY user_id, created_at
            """)

            columns = [desc[0] for desc in cur.description]
            results = cur.fetchall()

            return [dict(zip(columns, row)) for row in results]


def deactivate_bots(bot_ids):
    """Deactivate all bots by setting state='inactive'."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE configurations
                SET state = 'inactive'
                WHERE id = ANY(%s)
            """, (bot_ids,))
            conn.commit()
            return cur.rowcount


def stop_scheduler_jobs(config_ids):
    """Stop scheduler jobs via orchestrator API."""
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    service_key = os.getenv('SERVICE_KEY')

    if not service_key:
        print("⚠️  WARNING: SERVICE_KEY not found in .env - skipping scheduler stop calls")
        return 0

    stopped_count = 0
    failed_count = 0

    for config_id in config_ids:
        try:
            response = requests.post(
                f"{api_url}/api/v2/bot/{config_id}/stop",
                headers={
                    'Authorization': f'Bearer {service_key}',
                    'X-Service-Auth': 'maintenance-script'
                },
                timeout=5
            )

            if response.status_code == 200:
                stopped_count += 1
            else:
                failed_count += 1
                print(f"⚠️  Failed to stop scheduler for {config_id}: {response.status_code}")

        except Exception as e:
            failed_count += 1
            print(f"⚠️  Error stopping scheduler for {config_id}: {e}")

    return stopped_count


def main():
    print("=" * 80)
    print("MAINTENANCE: Deactivating All Active Bots")
    print("=" * 80)
    print()

    # Step 1: Get all active bots
    print("📊 Querying active bots (excluding signal_validation configs)...")
    active_bots = get_active_bots()

    if not active_bots:
        print("✅ No active bots found. Nothing to deactivate.")
        print("ℹ️  Note: Signal validation configs are preserved and not affected.")
        return

    print(f"Found {len(active_bots)} active autonomous trading bots")
    print("ℹ️  Note: Signal validation configs will remain active")
    print()

    # Step 2: Show summary by user
    user_counts = {}
    for bot in active_bots:
        user_id = bot['user_id']
        user_counts[user_id] = user_counts.get(user_id, 0) + 1

    print(f"Active bots across {len(user_counts)} users:")
    for user_id, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {user_id}: {count} bots")

    if len(user_counts) > 10:
        print(f"  ... and {len(user_counts) - 10} more users")
    print()

    # Step 3: Save backup file
    backup_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'maintenance_backup_active_bots.json'
    )

    backup_data = {
        'deactivated_at': datetime.utcnow().isoformat(),
        'total_count': len(active_bots),
        'config_ids': [bot['id'] for bot in active_bots],
        'details': active_bots
    }

    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2, default=str)

    print(f"💾 Backup saved to: {backup_file}")
    print()

    # Step 4: Confirm deactivation
    print("⚠️  WARNING: This will deactivate ALL active autonomous trading bots!")
    print("ℹ️  Signal validation configs will NOT be affected.")
    print()
    confirm = input("Type 'DEACTIVATE' to proceed: ").strip()

    if confirm != 'DEACTIVATE':
        print("❌ Cancelled. No bots were deactivated.")
        return

    print()

    # Step 5: Stop scheduler jobs
    print("🛑 Stopping scheduler jobs...")
    config_ids = [bot['id'] for bot in active_bots]
    stopped_count = stop_scheduler_jobs(config_ids)
    print(f"✅ Stopped {stopped_count} scheduler jobs")
    print()

    # Step 6: Deactivate bots in database
    print("🔄 Deactivating bots in database...")
    deactivated_count = deactivate_bots(config_ids)
    print(f"✅ Deactivated {deactivated_count} bots")
    print()

    # Step 7: Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total bots deactivated: {deactivated_count}")
    print(f"Scheduler jobs stopped: {stopped_count}")
    print(f"Backup file: {backup_file}")
    print()
    print("✅ Maintenance complete. All autonomous trading bots are now inactive.")
    print("ℹ️  Signal validation configs remain active and unaffected.")
    print()
    print("To restore bots later, use the backup file with:")
    print(f"  python scripts/maintenance_restore_bots.py {backup_file}")
    print()


if __name__ == '__main__':
    main()
