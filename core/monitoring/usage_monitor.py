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

        # Track warnings sent to avoid spam (user_id -> last_warned_timestamp)
        self.warned_users = {}
        self.warn_cooldown = 3600  # Don't re-warn within 1 hour

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
        Check single user's credit status.

        Returns: 'ok', 'warned', 'paused'
        """
        balance = await self.get_balance_status(user_id)

        if balance.is_depleted:
            await self._pause_all_user_bots(user_id, reason="credits_depleted")
            await self._notify_user(user_id, "credits_depleted", balance)
            return "paused"

        if balance.is_low:
            await self._notify_user(user_id, "credits_low", balance)
            return "warned"

        return "ok"

    async def get_balance_status(self, user_id: str) -> BalanceStatus:
        """Get combined credit + usage status for a user."""
        period = datetime.utcnow().strftime("%Y-%m")

        # Get usage from Redis (instant)
        usage_key = f"usage:user:{user_id}:{period}"
        usage_raw = self.redis.get(usage_key)
        usage = Decimal(usage_raw) if usage_raw else Decimal("0")

        # Get credits from Stripe
        credits = await self._get_stripe_credits(user_id)

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
                    cur.execute("""
                        UPDATE configurations
                        SET state = 'paused', updated_at = NOW()
                        WHERE user_id = %s AND state = 'active'
                        RETURNING config_id, config_name
                    """, (user_id,))
                    paused = cur.fetchall()
                    conn.commit()

            if paused:
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

    async def _notify_user(self, user_id: str, notification_type: str, balance: BalanceStatus):
        """
        Send notification to user.

        Rate-limited to avoid spam - won't re-notify within cooldown period.
        """
        now = time.time()
        last_warned = self.warned_users.get(user_id, 0)

        if now - last_warned < self.warn_cooldown:
            # Already warned recently, skip
            return

        self.warned_users[user_id] = now

        # Log the notification (TODO: Implement email via Resend)
        if notification_type == "credits_depleted":
            logger.warning(
                f"💸 CREDITS DEPLETED for {user_id}: "
                f"credits=${balance.credits_available:.2f}, usage=${balance.period_usage:.2f}"
            )
        elif notification_type == "credits_low":
            logger.info(
                f"⚠️ LOW CREDITS for {user_id}: "
                f"credits=${balance.credits_available:.2f}, usage=${balance.period_usage:.2f}, "
                f"remaining=${balance.net_balance:.2f}"
            )

        # TODO: Send email notification via Resend
        # await send_credit_notification_email(user_id, notification_type, balance)

    async def cache_usage_summaries(self):
        """
        Pre-compute usage summaries for fast API reads.

        Called every 5 minutes. Caches summaries in Redis for instant API responses.
        """
        period = datetime.utcnow().strftime("%Y-%m")

        try:
            # Get all users with usage this period
            keys = self.redis.keys(f"usage:user:*:{period}")

            cached_count = 0
            for key in keys:
                try:
                    # Extract user_id from key format: usage:user:{user_id}:{period}
                    parts = key.split(":")
                    if len(parts) < 3:
                        continue

                    user_id = parts[2]
                    usage_raw = self.redis.get(key)
                    usage = Decimal(usage_raw) if usage_raw else Decimal("0")

                    # Get credits from Stripe
                    credits = await self._get_stripe_credits(user_id)

                    summary = {
                        "period": period,
                        "usage_usd": float(usage),
                        "credits_usd": float(credits),
                        "net_balance_usd": float(credits - usage),
                        "updated_at": datetime.utcnow().isoformat()
                    }

                    # Cache with 5 minute TTL
                    self.redis.setex(
                        f"usage:summary:{user_id}",
                        300,
                        json.dumps(summary)
                    )
                    cached_count += 1

                except Exception as e:
                    logger.error(f"Error caching summary for key {key}: {e}")

            if cached_count > 0:
                logger.debug(f"📊 Cached {cached_count} usage summaries")

        except Exception as e:
            logger.error(f"Failed to cache usage summaries: {e}")


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
