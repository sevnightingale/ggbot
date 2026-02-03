#!/usr/bin/env python3
"""
Add $10 billing threshold to all usage_based subscriptions.

This script:
1. Finds all usage_based users with active Stripe subscriptions
2. Updates each subscription to trigger billing when usage >= $10
3. Reports results

Usage:
    python scripts/add_billing_thresholds.py --dry-run  # Preview changes
    python scripts/add_billing_thresholds.py            # Execute changes
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
env_path = Path('/home/sev/ggbot/.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

import stripe
from core.common.db import get_db_connection

# Configuration
THRESHOLD_AMOUNT_CENTS = 1000  # $10.00

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def get_usage_based_subscriptions():
    """Get all usage_based users with active Stripe subscriptions."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    user_id,
                    stripe_customer_id,
                    stripe_subscription_id,
                    subscription_status
                FROM user_profiles
                WHERE subscription_tier = 'usage_based'
                AND stripe_subscription_id IS NOT NULL
                ORDER BY updated_at DESC
            """)
            return cur.fetchall()


def check_subscription_threshold(subscription_id: str) -> dict:
    """Check if subscription already has billing threshold."""
    try:
        sub = stripe.Subscription.retrieve(subscription_id)
        threshold = getattr(sub, 'billing_thresholds', None)
        return {
            'id': subscription_id,
            'status': sub.status,
            'customer': sub.customer,
            'current_threshold': threshold.amount_gte if threshold else None,
            'subscription': sub
        }
    except Exception as e:
        return {
            'id': subscription_id,
            'error': str(e)
        }


def add_billing_threshold(subscription_id: str, dry_run: bool = True) -> dict:
    """Add billing threshold to subscription."""
    try:
        if dry_run:
            return {
                'id': subscription_id,
                'action': 'would_update',
                'threshold': THRESHOLD_AMOUNT_CENTS
            }

        updated = stripe.Subscription.modify(
            subscription_id,
            billing_thresholds={
                'amount_gte': THRESHOLD_AMOUNT_CENTS
            }
        )

        return {
            'id': subscription_id,
            'action': 'updated',
            'threshold': THRESHOLD_AMOUNT_CENTS,
            'new_status': updated.status
        }
    except Exception as e:
        return {
            'id': subscription_id,
            'action': 'error',
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Add billing thresholds to usage_based subscriptions')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()

    print("=" * 70)
    print(f"BILLING THRESHOLD UPDATE - ${THRESHOLD_AMOUNT_CENTS / 100:.2f} cap")
    print(f"Mode: {'DRY RUN (no changes)' if args.dry_run else '🔴 LIVE (will modify subscriptions)'}")
    print("=" * 70 + "\n")

    # Get subscriptions from database
    subscriptions = get_usage_based_subscriptions()
    print(f"Found {len(subscriptions)} usage_based subscriptions in database\n")

    if not subscriptions:
        print("No subscriptions to update.")
        return

    # Check and update each subscription
    results = {
        'already_set': [],
        'updated': [],
        'would_update': [],
        'errors': [],
        'skipped': []
    }

    for user_id, customer_id, sub_id, status in subscriptions:
        print(f"Processing: {sub_id[:20]}... (customer: {customer_id})")

        # Check current state
        current = check_subscription_threshold(sub_id)

        if 'error' in current:
            print(f"  ❌ Error checking: {current['error']}")
            results['errors'].append(current)
            continue

        if current['status'] not in ['active', 'past_due', 'trialing']:
            print(f"  ⏭️  Skipped (status: {current['status']})")
            results['skipped'].append(current)
            continue

        if current['current_threshold'] == THRESHOLD_AMOUNT_CENTS:
            print(f"  ✅ Already has ${THRESHOLD_AMOUNT_CENTS/100:.2f} threshold")
            results['already_set'].append(current)
            continue

        if current['current_threshold']:
            print(f"  ℹ️  Has different threshold: ${current['current_threshold']/100:.2f}")

        # Add/update threshold
        result = add_billing_threshold(sub_id, dry_run=args.dry_run)

        if result['action'] == 'would_update':
            print(f"  📝 Would add ${THRESHOLD_AMOUNT_CENTS/100:.2f} threshold")
            results['would_update'].append(result)
        elif result['action'] == 'updated':
            print(f"  ✅ Added ${THRESHOLD_AMOUNT_CENTS/100:.2f} threshold")
            results['updated'].append(result)
        else:
            print(f"  ❌ Error: {result.get('error', 'Unknown')}")
            results['errors'].append(result)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Already had threshold: {len(results['already_set'])}")
    print(f"Skipped (inactive):    {len(results['skipped'])}")

    if args.dry_run:
        print(f"Would update:          {len(results['would_update'])}")
    else:
        print(f"Updated:               {len(results['updated'])}")

    print(f"Errors:                {len(results['errors'])}")

    if args.dry_run and results['would_update']:
        print(f"\n💡 Run without --dry-run to apply changes to {len(results['would_update'])} subscriptions")


if __name__ == '__main__':
    main()
