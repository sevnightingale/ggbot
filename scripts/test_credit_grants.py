#!/usr/bin/env python3
"""
Test Stripe Credit Grants - Verify credit balance and invoice preview

Usage:
    source .venv/bin/activate
    python scripts/test_credit_grants.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stripe
from core.common.db import get_db_connection

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

def get_user_stripe_id(email: str) -> tuple[str, str]:
    """Get user_id and stripe_customer_id from email."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT up.user_id, up.stripe_customer_id
                FROM user_profiles up
                JOIN auth.users au ON up.user_id = au.id
                WHERE au.email = %s
            """, (email,))
            result = cur.fetchone()
            if not result:
                raise ValueError(f"User not found: {email}")
            return result[0], result[1]


def check_credit_balance(customer_id: str):
    """Check customer's available credit balance."""
    print(f"\n📊 Credit Balance for {customer_id}")
    print("-" * 50)

    try:
        # List all credit grants for this customer
        grants = stripe.billing.CreditGrant.list(customer=customer_id)

        if not grants.data:
            print("❌ No credit grants found")
            return

        print(f"Found {len(grants.data)} credit grant(s):\n")

        total_available = 0
        for grant in grants.data:
            name = grant.name or "Unnamed"
            amount = grant.amount.monetary.value / 100  # Convert cents to dollars
            currency = grant.amount.monetary.currency.upper()

            # Get balance info
            ledger = grant.get("ledger_balance", {}).get("monetary", {}).get("value", 0) / 100
            available = grant.get("available_balance", {}).get("monetary", {}).get("value", 0) / 100

            status = "✅ Active" if grant.effective_at else "⏳ Pending"
            if grant.voided_at:
                status = "❌ Voided"
            elif grant.expires_at and grant.expires_at < int(os.time()):
                status = "⚠️ Expired"

            print(f"  📦 {name}")
            print(f"     ID: {grant.id}")
            print(f"     Original: ${amount:.2f} {currency}")
            print(f"     Available: ${available:.2f} {currency}")
            print(f"     Category: {grant.category}")
            print(f"     Status: {status}")
            print()

            total_available += available

        print(f"💰 Total Available Credits: ${total_available:.2f}")

    except stripe.error.StripeError as e:
        print(f"❌ Stripe API error: {e}")


def check_upcoming_invoice(customer_id: str):
    """Preview the upcoming invoice to see credit application."""
    print(f"\n📄 Upcoming Invoice Preview")
    print("-" * 50)

    try:
        # Get upcoming invoice
        invoice = stripe.Invoice.upcoming(customer=customer_id)

        subtotal = invoice.subtotal / 100
        total = invoice.total / 100

        print(f"  Subtotal: ${subtotal:.2f}")

        # Check for applied credits
        if hasattr(invoice, 'total_discount_amounts') and invoice.total_discount_amounts:
            for discount in invoice.total_discount_amounts:
                print(f"  Discount: -${discount.amount / 100:.2f}")

        # Credits show up in the applied_balance or as line items
        if invoice.starting_balance:
            print(f"  Starting Balance: ${invoice.starting_balance / 100:.2f}")

        if invoice.ending_balance:
            print(f"  Ending Balance: ${invoice.ending_balance / 100:.2f}")

        # Check for credit balance transactions
        if hasattr(invoice, 'pre_payment_credit_notes_amount'):
            if invoice.pre_payment_credit_notes_amount:
                print(f"  Credit Notes: -${invoice.pre_payment_credit_notes_amount / 100:.2f}")

        print(f"\n  📊 Total Due: ${total:.2f}")

        # Note about credits
        print("\n  ℹ️  Note: Credits apply at invoice FINALIZATION, not preview.")
        print("     Run a bot to generate usage, then check the finalized invoice.")

    except stripe.error.InvalidRequestError as e:
        if "No upcoming invoices" in str(e):
            print("  ℹ️  No upcoming invoice (no usage recorded yet)")
            print("     Run a bot to generate some LLM usage first!")
        else:
            print(f"❌ Error: {e}")
    except stripe.error.StripeError as e:
        print(f"❌ Stripe API error: {e}")


def check_recent_invoices(customer_id: str, limit: int = 3):
    """Check recent invoices to see if credits were applied."""
    print(f"\n📜 Recent Invoices")
    print("-" * 50)

    try:
        invoices = stripe.Invoice.list(customer=customer_id, limit=limit)

        if not invoices.data:
            print("  No invoices found")
            return

        for inv in invoices.data:
            status_emoji = {
                "paid": "✅",
                "open": "📬",
                "draft": "📝",
                "void": "❌",
                "uncollectible": "⚠️"
            }.get(inv.status, "❓")

            print(f"\n  {status_emoji} Invoice {inv.number or inv.id[:20]}")
            print(f"     Status: {inv.status}")
            print(f"     Total: ${inv.total / 100:.2f}")
            print(f"     Amount Paid: ${inv.amount_paid / 100:.2f}")

            # Check if credits were applied
            if inv.subtotal != inv.total:
                credit_applied = (inv.subtotal - inv.total) / 100
                if credit_applied > 0:
                    print(f"     💳 Credits Applied: ${credit_applied:.2f}")

    except stripe.error.StripeError as e:
        print(f"❌ Stripe API error: {e}")


def main():
    email = "redacted@example.com"

    print("=" * 60)
    print("🧪 Stripe Credit Grants Test")
    print("=" * 60)

    try:
        user_id, customer_id = get_user_stripe_id(email)
        print(f"\n👤 User: {email}")
        print(f"   User ID: {user_id}")
        print(f"   Stripe Customer: {customer_id}")

        if not customer_id:
            print("\n❌ No Stripe customer ID found for this user")
            return

        check_credit_balance(customer_id)
        check_upcoming_invoice(customer_id)
        check_recent_invoices(customer_id)

        print("\n" + "=" * 60)
        print("✅ Test complete!")
        print("\nNext steps:")
        print("  1. Run one of your bots to generate LLM usage")
        print("  2. Wait for daily meter reporting (or run manually)")
        print("  3. Check the finalized invoice to see credits applied")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
