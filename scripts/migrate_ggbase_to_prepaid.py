#!/usr/bin/env python3
"""
Database Migration: Rename 'ggbase' tier to 'prepaid'

This migration updates all user_profiles records that have subscription_tier='ggbase'
to use the new 'prepaid' tier name.

Run: cd /home/sev/ggbot && source .venv/bin/activate && python scripts/migrate_ggbase_to_prepaid.py
"""

from core.common.db import get_db_connection
from core.common.logger import logger


def migrate_ggbase_to_prepaid():
    """Migrate all 'ggbase' tier users to 'prepaid' tier."""

    print("=" * 60)
    print("MIGRATION: Rename 'ggbase' tier to 'prepaid'")
    print("=" * 60)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # First, count how many users will be affected
            cur.execute("""
                SELECT COUNT(*)
                FROM user_profiles
                WHERE subscription_tier = 'ggbase'
            """)
            count = cur.fetchone()[0]

            print(f"\n📊 Found {count} users with 'ggbase' tier")

            if count == 0:
                print("✅ No migration needed - no 'ggbase' users found")
                return

            # Show users that will be migrated
            cur.execute("""
                SELECT user_id, subscription_status, created_at
                FROM user_profiles
                WHERE subscription_tier = 'ggbase'
                ORDER BY created_at DESC
                LIMIT 10
            """)
            users = cur.fetchall()

            print("\n📋 Users to migrate (showing first 10):")
            for user in users:
                print(f"   - {user[0]} (status: {user[1]}, created: {user[2]})")

            if count > 10:
                print(f"   ... and {count - 10} more")

            # Confirm before proceeding
            print("\n" + "=" * 60)
            confirm = input("Proceed with migration? (yes/no): ")

            if confirm.lower() != 'yes':
                print("❌ Migration cancelled")
                return

            # Perform the migration
            cur.execute("""
                UPDATE user_profiles
                SET subscription_tier = 'prepaid',
                    updated_at = NOW()
                WHERE subscription_tier = 'ggbase'
                RETURNING user_id
            """)

            migrated = cur.fetchall()
            conn.commit()

            print(f"\n✅ Successfully migrated {len(migrated)} users from 'ggbase' to 'prepaid'")

            # Verify
            cur.execute("""
                SELECT COUNT(*)
                FROM user_profiles
                WHERE subscription_tier = 'ggbase'
            """)
            remaining = cur.fetchone()[0]

            if remaining == 0:
                print("✅ Verification passed - no 'ggbase' users remaining")
            else:
                print(f"⚠️ Warning: {remaining} users still have 'ggbase' tier")

            # Show current tier distribution
            cur.execute("""
                SELECT subscription_tier, COUNT(*)
                FROM user_profiles
                GROUP BY subscription_tier
                ORDER BY COUNT(*) DESC
            """)
            tiers = cur.fetchall()

            print("\n📊 Current tier distribution:")
            for tier, count in tiers:
                print(f"   {tier or 'NULL'}: {count} users")


if __name__ == "__main__":
    migrate_ggbase_to_prepaid()
