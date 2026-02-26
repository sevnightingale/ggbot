"""
Usage Monitor - Watches credit balances and enforces limits.

Integrated into account-monitor PM2 service.
Runs alongside UniversalAccountMonitor to:
- Check credit balances for users with active bots (every 60s)
- Pause bots when credits are depleted
- Cache usage summaries for fast API reads (every 5 min)
- Send low balance warnings
"""
import os
import json
import time
import redis
import stripe
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from dataclasses import dataclass

from core.common.db import get_db_connection
from core.common.logger import logger as base_logger
from core.services.user_service import user_service

# Create usage monitor logger
logger = base_logger.bind(service="usage_monitor")


@dataclass
class BalanceStatus:
    """Represents a user's credit and usage status."""
    user_id: str
    credits_available: Decimal
    period_usage: Decimal
    net_balance: Decimal
    is_low: bool  # < 20% remaining or < $5
    is_depleted: bool  # <= 0


class UsageMonitor:
    """
    Monitors usage and enforces credit limits.

    Designed to run alongside UniversalAccountMonitor.
    Called periodically from the main monitoring loop.
    """

    def __init__(self, redis_url: str = None):
        # decode_responses=True returns strings instead of bytes
        self.redis = redis.from_url(
            redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379'),
            decode_responses=True
        )
        self.check_interval = 60  # seconds
        self.last_check = 0
        self.last_cache = 0
        self.cache_interval = 300  # 5 minutes
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

        # State tracking moved to Redis for persistence across restarts
        # Key format: credit_state:{user_id} → "ok" | "low" | "depleted"
        # Notifications only sent on state transitions (ok→low, low→depleted, ok→depleted)

        logger.info("✨ UsageMonitor initialized")

    def should_check(self) -> bool:
        """Rate limit credit checks to every 60 seconds."""
        now = time.time()
        if now - self.last_check >= self.check_interval:
            self.last_check = now
            return True
        return False

    def should_cache(self) -> bool:
        """Rate limit summary caching to every 5 minutes."""
        now = time.time()
        if now - self.last_cache >= self.cache_interval:
            self.last_cache = now
            return True
        return False

    async def check_all_active_users(self) -> dict:
        """
        Check credit status for all users with active bots.

        Returns:
            Stats dict with counts of users checked, paused, warned
        """
        stats = {"checked": 0, "paused": 0, "warned": 0, "ok": 0}

        try:
            active_users = await self._get_users_with_active_bots()

            if not active_users:
                return stats

            for user_id in active_users:
                try:
                    result = await self._check_user_credits(user_id)
                    stats["checked"] += 1
                    if result == "paused":
                        stats["paused"] += 1
                    elif result == "warned":
                        stats["warned"] += 1
                    else:
                        stats["ok"] += 1
                except Exception as e:
                    logger.error(f"Failed to check credits for user {user_id}: {e}")

            if stats["paused"] > 0 or stats["warned"] > 0:
                logger.info(f"💰 Usage check: {stats}")

        except Exception as e:
            logger.error(f"Failed to check active users: {e}")

        return stats

    async def _check_user_credits(self, user_id: str) -> str:
        """
        Check single user's credit status with tier-specific handling.

        - PREPAID users: Hard block on depletion (pause bots immediately)
        - USAGE_BASED users: Check subscription status and enforce $10 threshold

        Returns: 'ok', 'warned', 'paused'
        """
        # Get user profile to check tier and subscription status
        profile = await user_service.get_profile(user_id)
        is_prepaid = profile.is_prepaid_tier if profile else False

        # Pass is_prepaid to get_balance_status for correct usage calculation
        # PREPAID: all-time usage from activities table
        # USAGE_BASED: monthly usage from Redis
        balance = await self.get_balance_status(user_id, is_prepaid=is_prepaid)

        if is_prepaid:
            # PREPAID: Hard block - pause bots when credits depleted
            # This is backup - decision engine should catch this before LLM calls
            if balance.is_depleted:
                await self._pause_all_user_bots(user_id, reason="prepaid_credits_exhausted")
                await self._notify_user(user_id, "prepaid_depleted", balance)
                return "paused"

            if balance.is_low:
                await self._notify_user(user_id, "prepaid_low", balance)
                return "warned"
        else:
            # USAGE_BASED: Check if subscription is past_due (payment failed)
            # This is a backup in case the webhook was missed
            subscription_status = await self._get_subscription_status(user_id)
            if subscription_status == 'past_due':
                # Payment has failed - pause bots immediately
                logger.warning(f"⚠️ User {user_id} is past_due with active bots - pausing")
                await self._pause_all_user_bots(user_id, reason="payment_failed")
                await self._notify_user(user_id, "payment_failed", balance)
                return "paused"

            # Soft handling for credits - just warn, they'll be billed
            if balance.is_depleted:
                # Don't pause - usage_based users get billed for overage
                await self._notify_user(user_id, "credits_depleted", balance)
                return "warned"

            if balance.is_low:
                await self._notify_user(user_id, "credits_low", balance)
                return "warned"

        return "ok"

    async def _get_subscription_status(self, user_id: str) -> Optional[str]:
        """Get user's subscription status from database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT subscription_status FROM user_profiles WHERE user_id = %s",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get subscription status for {user_id}: {e}")
            return None

    async def get_balance_status(self, user_id: str, is_prepaid: bool = None) -> BalanceStatus:
        """
        Get combined credit + usage status for a user.

        Prepaid users: total_purchased (from Stripe grants) - cumulative Redis usage.
        Metered users: Stripe credit balance - monthly Redis usage.
        """
        # Determine tier if not provided
        if is_prepaid is None:
            is_prepaid = await self._is_prepaid_tier(user_id)

        if is_prepaid:
            # Prepaid: lifetime pool — total purchased minus all-time usage
            credits = await self._get_total_purchased_from_stripe(user_id)
            usage_raw = self.redis.get(f"usage:prepaid:{user_id}")
            usage = Decimal(usage_raw) if usage_raw else Decimal("0")
        else:
            # Metered: monthly cycle — Stripe balance minus this month's usage
            credits = await self._get_stripe_credits(user_id)
            period = datetime.utcnow().strftime("%Y-%m")
            usage_raw = self.redis.get(f"usage:user:{user_id}:{period}")
            usage = Decimal(usage_raw) if usage_raw else Decimal("0")

        net = credits - usage

        # Low balance: either < 20% remaining OR < $5 absolute
        is_low = False
        if credits > 0:
            pct_remaining = net / credits if credits > 0 else Decimal("0")
            is_low = pct_remaining < Decimal("0.2") or net < Decimal("5")

        return BalanceStatus(
            user_id=user_id,
            credits_available=credits,
            period_usage=usage,
            net_balance=net,
            is_low=is_low,
            is_depleted=net <= 0 and credits > 0  # Only depleted if they HAD credits
        )

    async def _is_prepaid_tier(self, user_id: str) -> bool:
        """Check if user is on prepaid tier."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT subscription_tier FROM user_profiles WHERE user_id = %s",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    # 'prepaid' is stored as 'ggbase' in database (legacy enum value)
                    return result[0] in ('prepaid', 'ggbase') if result else False
        except Exception as e:
            logger.error(f"Failed to check prepaid tier for {user_id}: {e}")
            return False

    async def _get_total_usage_from_activities(self, user_id: str) -> Decimal:
        """
        Get ALL-TIME usage from activities table for prepaid users.

        This is the source of truth - prepaid credits don't reset monthly,
        so we need to track total spend against the credit pool.
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COALESCE(SUM(platform_cost_usd), 0)
                        FROM activities
                        WHERE user_id = %s
                        AND platform_cost_usd > 0
                    """, (user_id,))
                    result = cur.fetchone()
                    return Decimal(str(result[0])) if result and result[0] else Decimal("0")
        except Exception as e:
            logger.error(f"Failed to get total usage for {user_id}: {e}")
            return Decimal("0")

    async def _get_stripe_credits(self, user_id: str) -> Decimal:
        """Get available credit balance from Stripe."""
        customer_id = await self._get_stripe_customer_id(user_id)
        if not customer_id:
            return Decimal("0")

        try:
            summary = stripe.billing.CreditBalanceSummary.retrieve(
                customer=customer_id,
                filter={'type': 'applicability_scope', 'applicability_scope': {'price_type': 'metered'}}
            )
            if summary.balances and len(summary.balances) > 0:
                # Stripe returns cents, convert to dollars
                balance = summary.balances[0]
                if hasattr(balance, 'available_balance') and balance.available_balance:
                    return Decimal(str(balance.available_balance.monetary.value / 100))
            return Decimal("0")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe credit balance error for {user_id}: {e}")
            return Decimal("0")
        except Exception as e:
            logger.error(f"Unexpected error getting Stripe credits for {user_id}: {e}")
            return Decimal("0")

    async def _get_total_purchased_from_stripe(self, user_id: str) -> Decimal:
        """
        Get total credits purchased from Stripe Credit Grants.

        For prepaid users, we need the TOTAL purchased (sum of all grants),
        not the "available" balance (which never decreases for prepaid).
        """
        customer_id = await self._get_stripe_customer_id(user_id)
        if not customer_id:
            return Decimal("0")

        try:
            grants = stripe.billing.CreditGrant.list(customer=customer_id, limit=100)
            total = Decimal("0")
            for grant in grants.data:
                # Stripe returns cents
                amount = Decimal(str(grant.amount.monetary.value / 100))
                total += amount
            return total
        except stripe.error.StripeError as e:
            logger.error(f"Stripe credit grants error for {user_id}: {e}")
            return Decimal("0")
        except Exception as e:
            logger.error(f"Unexpected error getting credit grants for {user_id}: {e}")
            return Decimal("0")

    async def _get_stripe_customer_id(self, user_id: str) -> Optional[str]:
        """Get Stripe customer ID from database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT stripe_customer_id FROM user_profiles WHERE user_id = %s",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get Stripe customer ID for {user_id}: {e}")
            return None

    def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user's email address from auth.users table."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT email FROM auth.users WHERE id = %s",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get email for user {user_id}: {e}")
            return None

    async def _get_users_with_active_bots(self) -> List[str]:
        """Get list of user IDs with active bots."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT user_id
                        FROM configurations
                        WHERE state = 'active'
                    """)
                    return [str(row[0]) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get users with active bots: {e}")
            return []

    async def _pause_all_user_bots(self, user_id: str, reason: str):
        """Pause all active bots for a user due to credit depletion."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Note: 'paused' is not a valid state - constraint only allows 'active'/'inactive'
                    # Setting to 'inactive' stops the scheduler and achieves the same effect
                    cur.execute("""
                        UPDATE configurations
                        SET state = 'inactive', updated_at = NOW()
                        WHERE user_id = %s AND state = 'active'
                        RETURNING config_id, config_name
                    """, (user_id,))
                    paused = cur.fetchall()
                    conn.commit()

            if paused:
                # Store pause reason for each bot (for frontend display via SSE)
                # TTL of 24 hours - reason persists for user to see why bot was paused
                for config_id, config_name in paused:
                    self.redis.setex(
                        f"bot:pause_reason:{config_id}",
                        86400,  # 24h TTL
                        reason
                    )

                # Notify via Redis pub/sub for real-time updates
                for config_id, config_name in paused:
                    self.redis.publish("bot_lifecycle", json.dumps({
                        "action": "pause",
                        "config_id": config_id,
                        "user_id": user_id,
                        "reason": reason
                    }))

                logger.warning(f"⚠️ Paused {len(paused)} bots for user {user_id}: {reason}")

        except Exception as e:
            logger.error(f"Failed to pause bots for user {user_id}: {e}")

    def _get_credit_state(self, user_id: str) -> str:
        """Get user's last known credit state from Redis."""
        state = self.redis.get(f"credit_state:{user_id}")
        return state if state else "ok"

    def _set_credit_state(self, user_id: str, state: str):
        """Set user's credit state in Redis (persists across restarts)."""
        # TTL of 90 days - if user is inactive that long, they can be re-notified
        self.redis.setex(f"credit_state:{user_id}", 90 * 24 * 3600, state)

    def clear_credit_state(self, user_id: str):
        """
        Clear user's credit state (call when credits are added).

        This allows them to receive new notifications if they go low again.
        """
        self.redis.delete(f"credit_state:{user_id}")
        logger.debug(f"Cleared credit state for user {user_id} (credits added)")

    async def _notify_user(self, user_id: str, notification_type: str, balance: BalanceStatus):
        """
        Send notification to user via email.

        Uses state-based tracking to prevent spam:
        - Only sends notifications on state transitions (ok→low, low→depleted, ok→depleted)
        - State persists in Redis across service restarts
        - State cleared when user adds credits (enabling future notifications)
        """
        # Determine new state from notification type
        if notification_type in ["credits_depleted", "prepaid_depleted", "payment_failed"]:
            new_state = "depleted"
        elif notification_type in ["credits_low", "prepaid_low"]:
            new_state = "low"
        else:
            return  # Unknown notification type

        # Get current persisted state
        current_state = self._get_credit_state(user_id)

        # State priority: ok < low < depleted
        state_priority = {"ok": 0, "low": 1, "depleted": 2}

        # Only notify on downward transitions (state getting worse)
        if state_priority.get(new_state, 0) <= state_priority.get(current_state, 0):
            # Already notified about this state or worse, skip
            logger.debug(
                f"Skipping {notification_type} for {user_id}: "
                f"already in state '{current_state}'"
            )
            return

        # Update state BEFORE sending (even if email fails, don't spam retries)
        self._set_credit_state(user_id, new_state)

        # Log the notification
        if notification_type in ["credits_depleted", "prepaid_depleted"]:
            logger.warning(
                f"💸 CREDITS DEPLETED for {user_id}: "
                f"credits=${balance.credits_available:.2f}, usage=${balance.period_usage:.2f}"
            )
        elif notification_type in ["credits_low", "prepaid_low"]:
            logger.info(
                f"⚠️ LOW CREDITS for {user_id}: "
                f"credits=${balance.credits_available:.2f}, usage=${balance.period_usage:.2f}, "
                f"remaining=${balance.net_balance:.2f}"
            )

        # Send email notification via Resend
        user_email = self._get_user_email(user_id)
        if not user_email:
            logger.warning(f"Cannot send notification - no email found for user {user_id}")
            return

        try:
            from core.services.resend_service import resend_service

            if notification_type == "prepaid_depleted":
                # Prepaid users: Bots paused, no further charges
                title = "Your Prepaid Credits Are Exhausted - Bots Paused"
                message = f"""
                <p>Your prepaid credit balance has been fully used.</p>

                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Credits Purchased:</strong> ${balance.credits_available:.2f}</p>
                    <p style="margin: 5px 0;"><strong>Usage:</strong> ${balance.period_usage:.2f}</p>
                    <p style="margin: 5px 0; color: #dc3545;"><strong>Remaining:</strong> $0.00</p>
                </div>

                <p><strong>Your bots have been paused.</strong></p>
                <p>As a prepaid user, you won't be charged anything more. Purchase additional credits to reactivate your bots.</p>
                """
                resend_service.send_generic_notification(
                    user_email=user_email,
                    title=title,
                    message=message,
                    action_text="Buy More Credits",
                    action_url="https://app.ggbots.ai/forge",
                    notification_type="error"
                )
                logger.info(f"📧 Sent prepaid depleted email to {user_email}")

            elif notification_type == "prepaid_low":
                # Prepaid users: Low balance warning
                title = "Low Prepaid Credit Balance"
                message = f"""
                <p>Your prepaid credit balance is running low.</p>

                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Credits Purchased:</strong> ${balance.credits_available:.2f}</p>
                    <p style="margin: 5px 0;"><strong>Usage:</strong> ${balance.period_usage:.2f}</p>
                    <p style="margin: 5px 0; color: #ffc107;"><strong>Remaining:</strong> ${balance.net_balance:.2f}</p>
                </div>

                <p>When your credits run out, your bots will be paused. As a prepaid user, you'll never be charged beyond what you've purchased.</p>
                <p>Consider adding more credits to ensure uninterrupted bot operation.</p>
                """
                resend_service.send_generic_notification(
                    user_email=user_email,
                    title=title,
                    message=message,
                    action_text="Buy More Credits",
                    action_url="https://app.ggbots.ai/forge",
                    notification_type="warning"
                )
                logger.info(f"📧 Sent prepaid low credits warning email to {user_email}")

            elif notification_type == "credits_depleted":
                # Usage-based users: Warning only (they'll be billed)
                title = "Your ggbots Credits Are Depleted"
                message = f"""
                <p>Your ggbots credit balance has been exhausted.</p>

                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Credits Purchased:</strong> ${balance.credits_available:.2f}</p>
                    <p style="margin: 5px 0;"><strong>Usage This Month:</strong> ${balance.period_usage:.2f}</p>
                    <p style="margin: 5px 0; color: #dc3545;"><strong>Balance:</strong> ${balance.net_balance:.2f}</p>
                </div>

                <p>Your bots will continue running. Any usage beyond your credits will be billed to your payment method.</p>
                <p>Add more credits to reduce your upcoming bill.</p>
                """
                resend_service.send_generic_notification(
                    user_email=user_email,
                    title=title,
                    message=message,
                    action_text="Add Credits",
                    action_url="https://app.ggbots.ai/forge",
                    notification_type="warning"
                )
                logger.info(f"📧 Sent credits depleted email to {user_email}")

            elif notification_type == "payment_failed":
                # Payment failed notification - email already sent by webhook handler
                # This is a backup check, just log it
                logger.warning(
                    f"🚨 PAYMENT FAILED (backup check) for {user_id}: "
                    f"Bots paused due to past_due subscription status"
                )
                # Don't send email - webhook handler already sent it
                return

            elif notification_type == "credits_low":
                title = "Low Credit Balance Warning"
                message = f"""
                <p>Your ggbots credit balance is running low.</p>

                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Credits Purchased:</strong> ${balance.credits_available:.2f}</p>
                    <p style="margin: 5px 0;"><strong>Usage This Month:</strong> ${balance.period_usage:.2f}</p>
                    <p style="margin: 5px 0; color: #ffc107;"><strong>Remaining:</strong> ${balance.net_balance:.2f}</p>
                </div>

                <p>Consider adding more credits to ensure uninterrupted bot operation.</p>
                """
                resend_service.send_generic_notification(
                    user_email=user_email,
                    title=title,
                    message=message,
                    action_text="Add Credits",
                    action_url="https://app.ggbots.ai/forge",
                    notification_type="warning"
                )
                logger.info(f"📧 Sent low credits warning email to {user_email}")

        except Exception as e:
            logger.error(f"Failed to send credit notification email to {user_email}: {e}")

    async def cache_usage_summaries(self):
        """
        Pre-compute usage summaries for fast API reads.

        Called every 5 minutes. Caches summaries in Redis for instant API responses.

        Prepaid users: total_purchased - cumulative usage (lifetime).
        Metered users: Stripe balance - monthly Redis usage.
        """
        period = datetime.utcnow().strftime("%Y-%m")
        processed_user_ids = set()

        try:
            # Pass 1: Prepaid users (cumulative keys — no monthly reset)
            prepaid_keys = self.redis.keys("usage:prepaid:*")
            for key in prepaid_keys:
                try:
                    # Key format: usage:prepaid:{user_id}
                    parts = key.split(":")
                    if len(parts) < 3:
                        continue

                    user_id = parts[2]
                    processed_user_ids.add(user_id)

                    usage_raw = self.redis.get(key)
                    usage = Decimal(usage_raw) if usage_raw else Decimal("0")

                    credits = await self._get_total_purchased_from_stripe(user_id)
                    net_balance = max(Decimal("0"), credits - usage)

                    summary = {
                        "period": "cumulative",
                        "usage_usd": float(usage),
                        "credits_usd": float(credits),
                        "net_balance_usd": float(net_balance),
                        "updated_at": datetime.utcnow().isoformat()
                    }

                    self.redis.setex(
                        f"usage:summary:{user_id}",
                        300,
                        json.dumps(summary)
                    )

                except Exception as e:
                    logger.error(f"Error caching prepaid summary for key {key}: {e}")

            # Pass 2: Metered users (monthly keys)
            monthly_keys = self.redis.keys(f"usage:user:*:{period}")
            cached_count = 0
            for key in monthly_keys:
                try:
                    parts = key.split(":")
                    if len(parts) < 3:
                        continue

                    user_id = parts[2]

                    # Skip if already cached in prepaid pass
                    if user_id in processed_user_ids:
                        continue

                    usage_raw = self.redis.get(key)
                    usage = Decimal(usage_raw) if usage_raw else Decimal("0")

                    credits = await self._get_stripe_credits(user_id)
                    net_balance = max(Decimal("0"), credits - usage)

                    summary = {
                        "period": period,
                        "usage_usd": float(usage),
                        "credits_usd": float(credits),
                        "net_balance_usd": float(net_balance),
                        "updated_at": datetime.utcnow().isoformat()
                    }

                    self.redis.setex(
                        f"usage:summary:{user_id}",
                        300,
                        json.dumps(summary)
                    )
                    cached_count += 1

                except Exception as e:
                    logger.error(f"Error caching summary for key {key}: {e}")

            total_cached = len(processed_user_ids) + cached_count
            if total_cached > 0:
                logger.debug(f"Cached {total_cached} usage summaries ({len(processed_user_ids)} prepaid, {cached_count} metered)")

        except Exception as e:
            logger.error(f"Failed to cache usage summaries: {e}")


# =============================================================================
# UTILITY FUNCTIONS (for use by external modules like ggbot.py)
# =============================================================================

def clear_credit_notification_state(user_id: str, redis_url: str = None):
    """
    Clear a user's credit notification state after they add credits.

    Call this after creating a credit grant to allow the user to
    receive future low/depleted notifications if they run low again.

    Args:
        user_id: The user's ID
        redis_url: Optional Redis URL (defaults to REDIS_URL env var)
    """
    import os
    redis_client = redis.from_url(
        redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379'),
        decode_responses=True
    )
    redis_client.delete(f"credit_state:{user_id}")
    logger.debug(f"Cleared credit notification state for user {user_id} (credits added)")


# Standalone test function
async def _test_usage_monitor():
    """Test the usage monitor standalone."""
    monitor = UsageMonitor()

    print("Testing get_users_with_active_bots...")
    users = await monitor._get_users_with_active_bots()
    print(f"Found {len(users)} users with active bots: {users[:5]}...")

    if users:
        print(f"\nTesting get_balance_status for user {users[0]}...")
        balance = await monitor.get_balance_status(users[0])
        print(f"Balance: credits=${balance.credits_available:.2f}, "
              f"usage=${balance.period_usage:.2f}, "
              f"net=${balance.net_balance:.2f}, "
              f"is_low={balance.is_low}, is_depleted={balance.is_depleted}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(_test_usage_monitor())
