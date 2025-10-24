"""
Helper script to find live trading bots for Symphony API testing.

Run with:
    cd /home/sev/ggbot
    source .venv/bin/activate
    python scripts/find_live_bots.py
"""

import sys
sys.path.insert(0, '/home/sev/ggbot')

from core.common.db import get_db_connection


def find_live_bots():
    """Find all live trading bots with Symphony configuration."""

    print("\n" + "="*80)
    print("LIVE TRADING BOTS - Symphony Configuration")
    print("="*80)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Find all live bots
            cur.execute("""
                SELECT
                    c.config_id,
                    c.user_id,
                    c.config_name,
                    c.symphony_agent_id,
                    c.trading_mode,
                    c.created_at,
                    up.symphony_vault_id,
                    up.symphony_smart_account,
                    COUNT(lt.batch_id) as trade_count
                FROM configurations c
                LEFT JOIN user_profiles up ON c.user_id = up.user_id
                LEFT JOIN live_trades lt ON c.config_id = lt.config_id
                WHERE c.trading_mode = 'live'
                GROUP BY c.config_id, c.user_id, c.config_name, c.symphony_agent_id,
                         c.trading_mode, c.created_at, up.symphony_vault_id, up.symphony_smart_account
                ORDER BY c.created_at DESC
            """)

            live_bots = cur.fetchall()

    if not live_bots:
        print("\n❌ No live trading bots found")
        print("\nTo test Symphony API:")
        print("1. Create a bot in the frontend")
        print("2. Connect Symphony account in Settings")
        print("3. Use 'Duplicate as Live' to create a live bot")
        return

    print(f"\n✅ Found {len(live_bots)} live trading bot(s)\n")

    for idx, bot in enumerate(live_bots, 1):
        config_id, user_id, config_name, symphony_agent_id, trading_mode, created_at, vault_id, smart_account, trade_count = bot

        print(f"\n{'='*80}")
        print(f"BOT #{idx}: {config_name}")
        print(f"{'='*80}")
        print(f"Config ID:         {config_id}")
        print(f"User ID:           {user_id}")
        print(f"Symphony Agent:    {symphony_agent_id or 'NOT SET'}")
        print(f"Smart Account:     {smart_account or 'NOT SET'}")
        print(f"Vault Configured:  {'✅ Yes' if vault_id else '❌ No'}")
        print(f"Live Trades:       {trade_count}")
        print(f"Created:           {created_at}")

        # Test command
        if vault_id and symphony_agent_id:
            print(f"\n📋 TEST COMMAND:")
            print(f"python scripts/test_symphony_metrics.py \\")
            print(f"  --user-id {user_id} \\")
            print(f"  --config-id {config_id}")
        else:
            print(f"\n⚠️  Cannot test - missing configuration:")
            if not vault_id:
                print(f"   - No Symphony credentials in Vault")
            if not symphony_agent_id:
                print(f"   - No Symphony agent ID set")

    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    find_live_bots()
