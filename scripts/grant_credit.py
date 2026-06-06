#!/usr/bin/env python3
"""
Grant credits to a user

Usage:
    source .venv/bin/activate
    python scripts/grant_credit.py <email> <amount>

Example:
    python scripts/grant_credit.py user@example.com 10
"""

import os
import sys
import stripe
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.common.db import get_db_connection
from core.common.logger import logger

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


def get_user_info(email: str) -> tuple[str, str, str]:
    """Get user_id, stripe_customer_id, and current tier from email."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT up.user_id, up.stripe_customer_id, up.subscription_tier
                FROM user_profiles up
                WHERE up.email = %s
            """, (email,))
            result = cur.fetchone()
            if not result:
                raise ValueError(f"User not found: {email}")
            return result[0], result[1], result[2] or 'free'


def grant_credit(email: str, amount_dollars: float):
    """Grant credit to a user and upgrade to prepaid if on free tier."""
    try:
        user_id, stripe_customer_id, current_tier = get_user_info(email)
        amount_cents = int(amount_dollars * 100)

        print(f"👤 User: {email}")
        print(f"   User ID: {user_id}")
        print(f"   Stripe Customer: {stripe_customer_id}")
        print(f"   Current Tier: {current_tier}")
        print()

        if not stripe_customer_id:
            print("❌ User doesn't have a Stripe customer ID. Creating one...")
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=email,
                metadata={
                    'user_id': user_id
                }
            )
            stripe_customer_id = customer.id

            # Update database with Stripe customer ID
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_profiles
                        SET stripe_customer_id = %s, updated_at = NOW()
                        WHERE user_id = %s
                    """, (stripe_customer_id, user_id))
                    conn.commit()
            print(f"✅ Created Stripe customer: {stripe_customer_id}")
            print()

        # Create credit grant
        print(f"💳 Creating ${amount_dollars} credit grant...")

        credit_grant = stripe.billing.CreditGrant.create(
            customer=stripe_customer_id,
            name=f"${amount_dollars:.0f} Admin Grant",
            applicability_config={
                'scope': {'price_type': 'metered'}
            },
            category='paid',
            amount={
                'type': 'monetary',
                'monetary': {
                    'value': amount_cents,
                    'currency': 'usd'
                }
            }
        )

        print(f"✅ Credit grant created: {credit_grant.id}")
        print(f"   Amount: ${amount_dollars:.2f}")
        print()

        # If user is on free tier, upgrade to prepaid
        if current_tier == 'free':
            print("📈 Upgrading user from free to prepaid tier...")
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_profiles
                        SET subscription_tier = 'prepaid',
                            subscription_status = 'active',
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))
                    conn.commit()
            print("✅ User upgraded to prepaid tier")
        else:
            print(f"ℹ️  User remains on {current_tier} tier (credits added to balance)")

        # Clear credit notification state
        try:
            from core.monitoring.usage_monitor import clear_credit_notification_state
            clear_credit_notification_state(user_id)
            print("✅ Credit notification state cleared")
        except Exception as e:
            print(f"⚠️  Could not clear credit notification state: {e}")

        print()
        print("🎉 Credit grant complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/grant_credit.py <email> <amount>")
        print("Example: python scripts/grant_credit.py user@example.com 10")
        sys.exit(1)

    email = sys.argv[1]
    try:
        amount = float(sys.argv[2])
    except ValueError:
        print(f"❌ Invalid amount: {sys.argv[2]}")
        sys.exit(1)

    if amount <= 0:
        print("❌ Amount must be positive")
        sys.exit(1)

    print("="*60)
    print(f"🎁 Granting ${amount} Credit to {email}")
    print("="*60)
    print()

    grant_credit(email, amount)


if __name__ == "__main__":
    main()