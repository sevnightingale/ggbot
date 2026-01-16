# Usage & Billing Tracking System

**Status**: ✅ BACKEND COMPLETE (Frontend Phase 5 pending)
**Created**: 2026-01-15
**Completed Backend**: 2026-01-15
**Priority**: HIGH - Revenue protection + user visibility
**Complexity**: Medium (~12-18 hours)

### Implementation Status
- [x] Phase 1: Redis Counter Foundation
- [x] Phase 2: Usage Monitor in Account Monitor
- [x] Phase 3: API Endpoints
- [x] Phase 4: Idempotency & Security Fixes
- [ ] Phase 5: Frontend Integration (pending)

---

## Executive Summary

The current billing system has **critical gaps** in visibility, enforcement, and tracking. This plan addresses:

1. **No real-time usage visibility** - Users can't see their spend
2. **No per-bot cost tracking** - No breakdown by configuration
3. **Scheduler runs without permission checks** - Bots run after subscription lapses
4. **No credit depletion handling** - Users can accrue debt
5. **Agent LLM calls not tracked** - Revenue leakage
6. **Idempotency gaps** - Double billing/credit risks

**Solution**: Redis-based usage counters + Account Monitor as Usage Watchdog + minimal ggbot.py changes.

---

## Current State Analysis

### What Exists

| Component | Status | Notes |
|-----------|--------|-------|
| `activities` table | ✅ Working | Logs all LLM costs with tokens |
| Daily Stripe reporting | ✅ Working | Midnight UTC via APScheduler |
| `/api/v2/billing/usage` | ✅ Exists | Returns unreported usage (not used by frontend) |
| `/api/v2/billing/usage/breakdown` | ✅ Exists | Per-bot breakdown (not used by frontend) |
| `/api/v2/credits/balance` | ✅ Exists | Returns Stripe credit balance |
| Credit Packs | ✅ Working | Stripe + NOWPayments |

### Critical Gaps Identified

#### Gap 1: Scheduler Has No Permission Check
**File**: `ggbot.py:1188-1211`
```python
async def run_once(user_id: str, config_id: str, timeframe: str):
    # NO PERMISSION CHECK - goes straight to execution
    result = await orchestrator.run_autonomous_cycle(config_id, user_id)
```
**Impact**: Bots run after subscription lapses, users accrue debt.

#### Gap 2: Agent LLM Calls Not Tracked
**Evidence**: `grep log_llm_activity agent/` returns no files.
**Impact**: Agent conversations use LLMs without cost tracking - 100% revenue leakage.

#### Gap 3: No Idempotency on Stripe Meter Events
**File**: `billing/stripe_meter_reporter.py:114-120`
```python
event = stripe.billing.MeterEvent.create(
    event_name=STRIPE_EVENT_NAME,
    payload={"stripe_customer_id": customer_id, "value": value}
    # MISSING: identifier for deduplication
)
```
**Impact**: Crash after Stripe call but before `mark_as_reported()` → double billing.

#### Gap 4: No Credit Depletion Handling
**Webhook events handled** (`ggbot.py:4184-4193`):
- ✅ `checkout.session.completed`
- ✅ `customer.subscription.updated`
- ✅ `customer.subscription.deleted`
- ✅ `invoice.payment_failed`
- ❌ `billing.credit_balance.depleted` - NOT HANDLED

**Impact**: Bots run until invoice fails, then user has debt.

#### Gap 5: NOWPayments Webhook Lacks Idempotency
**File**: `ggbot.py:4665-4800`
No check for duplicate `order_id` processing.
**Impact**: Webhook retry → double credit grants.

#### Gap 6: No Real-Time Usage Visibility
- Usage only shows "unreported" (resets at midnight)
- No per-bot cost display in frontend
- No running totals

---

## Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PM2 Services                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────────────────────┐    │
│  │    ggbot        │    │      account-monitor            │    │
│  │  (API + Sched)  │    │  (Accounts + Usage Watchdog)    │    │
│  └────────┬────────┘    └────────────────┬────────────────┘    │
│           │                              │                      │
│           │ LLM call                     │ Every 60s            │
│           ▼                              ▼                      │
│  ┌─────────────────┐           ┌─────────────────────┐         │
│  │ decision/       │           │ UsageMonitor class  │         │
│  │ engine_v2.py    │           │ - Check credits     │         │
│  │                 │           │ - Pause depleted    │         │
│  │ +10 lines:      │           │ - Cache summaries   │         │
│  │ Redis INCR      │           │ - Send alerts       │         │
│  └────────┬────────┘           └─────────────────────┘         │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Redis                               │   │
│  │  usage:user:{id}:{period}    usage:config:{id}:{period} │   │
│  │  usage:summary:{id}          (cached summaries)          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Redis Key Structure

```
# User-level counters (updated on every LLM call)
usage:user:{user_id}:{YYYY-MM}          # Monthly user spend
usage:user:{user_id}:total              # All-time user spend (optional)

# Config-level counters (updated on every LLM call)
usage:config:{config_id}:{YYYY-MM}      # Monthly bot spend
usage:config:{config_id}:{YYYY-MM-DD}   # Daily bot spend (90-day TTL)

# Cached summaries (updated every 5 min by account-monitor)
usage:summary:{user_id}                 # JSON with usage + credits + net balance

# Idempotency tracking
nowpayments:processed:{order_id}        # Prevents duplicate crypto credit grants
```

### Design Principles

1. **Minimal ggbot.py changes** - Only 2 lines to mount router
2. **Redis for speed** - O(1) reads, no aggregation queries
3. **Account Monitor as watchdog** - Leverages existing infrastructure
4. **Proactive enforcement** - Pause before debt accrues
5. **Graceful degradation** - Redis failures don't break billing (activities table is source of truth)

---

## Implementation Plan

### Phase 1: Redis Counter Foundation (3-4 hours)

**Goal**: Add real-time usage counters updated on every LLM call.

#### 1.1 Add Redis Increment to Decision Engine

**File**: `decision/engine_v2.py`
**Location**: Inside `_log_llm_activity` method (around line 840)

```python
# After the existing log_llm_activity_safe() call, add:
try:
    import redis
    from datetime import datetime

    redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
    period = datetime.utcnow().strftime("%Y-%m")
    day = datetime.utcnow().strftime("%Y-%m-%d")

    # Atomic increments - fast and non-blocking
    pipe = redis_client.pipeline()
    pipe.incrbyfloat(f"usage:user:{user_id}:{period}", float(platform_cost_usd))
    pipe.incrbyfloat(f"usage:config:{config_id}:{period}", float(platform_cost_usd))
    pipe.incrbyfloat(f"usage:config:{config_id}:{day}", float(platform_cost_usd))
    pipe.expire(f"usage:config:{config_id}:{day}", 90 * 24 * 3600)  # 90 day TTL
    pipe.execute()
except Exception as e:
    logger.warning(f"Failed to update Redis usage counters: {e}")
    # Non-fatal - activities table is source of truth
```

**Lines added to ggbot.py ecosystem**: ~15 lines in decision engine

#### 1.2 Backfill Script for Existing Data

**File**: `scripts/backfill_usage_counters.py` (NEW)

```python
"""
Backfill Redis usage counters from activities table.
Run once after deploying the Redis counter feature.

Usage: python scripts/backfill_usage_counters.py [--dry-run]
"""
import redis
from datetime import datetime
from core.common.db import get_db_connection

def backfill_counters(dry_run=False):
    redis_client = redis.from_url(os.getenv('REDIS_URL'))
    current_period = datetime.utcnow().strftime("%Y-%m")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get usage by user for current period
            cur.execute("""
                SELECT user_id, SUM(platform_cost_usd) as total
                FROM activities
                WHERE created_at >= date_trunc('month', NOW())
                AND platform_cost_usd IS NOT NULL
                GROUP BY user_id
            """)
            for user_id, total in cur.fetchall():
                key = f"usage:user:{user_id}:{current_period}"
                if dry_run:
                    print(f"Would set {key} = {total}")
                else:
                    redis_client.set(key, str(float(total)))

            # Get usage by config for current period
            cur.execute("""
                SELECT config_id,
                       SUM(platform_cost_usd) as total,
                       DATE(created_at) as day,
                       SUM(platform_cost_usd) as daily_total
                FROM activities
                WHERE created_at >= date_trunc('month', NOW())
                AND platform_cost_usd IS NOT NULL
                GROUP BY config_id, DATE(created_at)
            """)
            # ... similar logic for config counters
```

---

### Phase 2: Usage Monitor in Account Monitor (4-5 hours)

**Goal**: Add usage watchdog to existing account-monitor PM2 service.

#### 2.1 Create UsageMonitor Class

**File**: `core/monitoring/usage_monitor.py` (NEW)

```python
"""
Usage Monitor - Watches credit balances and enforces limits.
Integrated into account-monitor PM2 service.
"""
import json
import redis
import stripe
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from dataclasses import dataclass

from core.common.db import get_db_connection
from core.common.logger import logger


@dataclass
class BalanceStatus:
    user_id: str
    credits_available: Decimal
    period_usage: Decimal
    net_balance: Decimal
    is_low: bool  # < 20% remaining
    is_depleted: bool  # <= 0


class UsageMonitor:
    """
    Monitors usage and enforces credit limits.
    Designed to run alongside UniversalAccountMonitor.
    """

    def __init__(self, redis_url: str = None):
        self.redis = redis.from_url(redis_url or 'redis://localhost:6379')
        self.check_interval = 60  # seconds
        self.last_check = 0
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

    async def should_check(self) -> bool:
        """Rate limit checks to every 60 seconds."""
        now = time.time()
        if now - self.last_check >= self.check_interval:
            self.last_check = now
            return True
        return False

    async def check_all_active_users(self) -> dict:
        """Check credit status for all users with active bots."""
        stats = {"checked": 0, "paused": 0, "warned": 0}

        active_users = await self._get_users_with_active_bots()

        for user_id in active_users:
            result = await self._check_user_credits(user_id)
            stats["checked"] += 1
            if result == "paused":
                stats["paused"] += 1
            elif result == "warned":
                stats["warned"] += 1

        if stats["paused"] > 0 or stats["warned"] > 0:
            logger.info(f"Usage check: {stats}")

        return stats

    async def _check_user_credits(self, user_id: str) -> str:
        """Check single user's credit status. Returns: 'ok', 'warned', 'paused'"""

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
        usage = Decimal(self.redis.get(usage_key) or "0")

        # Get credits from Stripe
        credits = await self._get_stripe_credits(user_id)

        net = credits - usage

        return BalanceStatus(
            user_id=user_id,
            credits_available=credits,
            period_usage=usage,
            net_balance=net,
            is_low=credits > 0 and net < credits * Decimal("0.2"),  # < 20% remaining
            is_depleted=net <= 0
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
                return Decimal(str(summary.balances[0].available_balance.monetary.value / 100))
            return Decimal("0")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe credit balance error for {user_id}: {e}")
            return Decimal("0")

    async def _get_stripe_customer_id(self, user_id: str) -> Optional[str]:
        """Get Stripe customer ID from database."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT stripe_customer_id FROM user_profiles WHERE user_id = %s",
                    (user_id,)
                )
                result = cur.fetchone()
                return result[0] if result else None

    async def _get_users_with_active_bots(self) -> List[str]:
        """Get list of user IDs with active bots."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT user_id
                    FROM configurations
                    WHERE state = 'active'
                """)
                return [row[0] for row in cur.fetchall()]

    async def _pause_all_user_bots(self, user_id: str, reason: str):
        """Pause all active bots for a user."""
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
            # Notify scheduler via Redis pub/sub
            for config_id, config_name in paused:
                self.redis.publish("bot_lifecycle", json.dumps({
                    "action": "pause",
                    "config_id": config_id,
                    "user_id": user_id,
                    "reason": reason
                }))

            logger.warning(f"Paused {len(paused)} bots for user {user_id}: {reason}")

    async def _notify_user(self, user_id: str, notification_type: str, balance: BalanceStatus):
        """Send notification to user (placeholder - implement with email/push)."""
        # TODO: Implement with Resend email or push notification
        logger.info(f"Notification [{notification_type}] for {user_id}: credits=${balance.credits_available}, usage=${balance.period_usage}")

    async def cache_usage_summaries(self):
        """
        Pre-compute usage summaries for fast API reads.
        Called every 5 minutes.
        """
        period = datetime.utcnow().strftime("%Y-%m")

        # Get all users with usage this period
        keys = self.redis.keys(f"usage:user:*:{period}")

        for key in keys:
            try:
                user_id = key.decode().split(":")[2]
                usage = Decimal(self.redis.get(key) or "0")
                credits = await self._get_stripe_credits(user_id)

                summary = {
                    "period": period,
                    "usage_usd": float(usage),
                    "credits_usd": float(credits),
                    "net_balance_usd": float(credits - usage),
                    "updated_at": datetime.utcnow().isoformat()
                }

                self.redis.setex(
                    f"usage:summary:{user_id}",
                    300,  # 5 minute TTL
                    json.dumps(summary)
                )
            except Exception as e:
                logger.error(f"Error caching summary for key {key}: {e}")
```

#### 2.2 Integrate into Account Monitor

**File**: `scripts/account_monitor.py`
**Add to existing main loop**:

```python
from core.monitoring.usage_monitor import UsageMonitor

async def main():
    account_monitor = UniversalAccountMonitor(...)
    usage_monitor = UsageMonitor()

    cache_counter = 0

    while True:
        # Existing account monitoring (every 5 seconds)
        await account_monitor.check_all_accounts()

        # Usage monitoring (every 60 seconds)
        if await usage_monitor.should_check():
            await usage_monitor.check_all_active_users()

        # Cache summaries (every 5 minutes = 60 iterations at 5s)
        cache_counter += 1
        if cache_counter >= 60:
            await usage_monitor.cache_usage_summaries()
            cache_counter = 0

        await asyncio.sleep(5)
```

---

### Phase 3: API Endpoints (2-3 hours)

**Goal**: Create usage API endpoints in new file, minimal ggbot.py impact.

#### 3.1 Create Usage API Router

**File**: `api/usage.py` (NEW)

```python
"""
Usage & Billing API Endpoints
Provides real-time usage visibility from Redis counters.
"""
import json
import redis
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from core.auth.dependencies import get_current_user_v2, AuthenticatedUser
from core.config.service import config_service

router = APIRouter(prefix="/api/v2/usage", tags=["usage"])

redis_client = redis.from_url('redis://localhost:6379')


@router.get("/me")
async def get_my_usage(current_user: AuthenticatedUser = Depends(get_current_user_v2)):
    """
    Get current user's usage summary.
    Returns cached summary (updated every 5min) or live Redis counters.
    """
    user_id = str(current_user.user_id)

    # Try cached summary first
    cached = redis_client.get(f"usage:summary:{user_id}")
    if cached:
        return json.loads(cached)

    # Fallback to direct Redis read
    period = datetime.utcnow().strftime("%Y-%m")
    usage = float(redis_client.get(f"usage:user:{user_id}:{period}") or 0)

    return {
        "period": period,
        "usage_usd": usage,
        "credits_usd": None,  # Requires Stripe call - use cached summary
        "net_balance_usd": None,
        "cached": False
    }


@router.get("/config/{config_id}")
async def get_config_usage(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Get specific bot's usage - instant from Redis."""

    # Verify ownership
    config = await config_service.get_config(config_id, str(current_user.user_id))
    if not config:
        raise HTTPException(404, "Configuration not found")

    period = datetime.utcnow().strftime("%Y-%m")
    day = datetime.utcnow().strftime("%Y-%m-%d")

    period_usage = float(redis_client.get(f"usage:config:{config_id}:{period}") or 0)
    today_usage = float(redis_client.get(f"usage:config:{config_id}:{day}") or 0)

    return {
        "config_id": config_id,
        "config_name": config.config_name,
        "period": period,
        "period_usage_usd": period_usage,
        "today_usage_usd": today_usage
    }


@router.get("/breakdown")
async def get_usage_breakdown(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Get usage breakdown by bot for current user."""
    user_id = str(current_user.user_id)
    configs = await config_service.list_configs(user_id)

    period = datetime.utcnow().strftime("%Y-%m")

    breakdown = []
    for config in configs:
        usage = float(redis_client.get(f"usage:config:{config.config_id}:{period}") or 0)
        breakdown.append({
            "config_id": config.config_id,
            "config_name": config.config_name,
            "state": config.state,
            "period_usage_usd": usage
        })

    # Sort by usage descending
    breakdown.sort(key=lambda x: x["period_usage_usd"], reverse=True)

    return {
        "period": period,
        "breakdown": breakdown,
        "total_usage_usd": sum(b["period_usage_usd"] for b in breakdown)
    }
```

#### 3.2 Mount Router in ggbot.py

**File**: `ggbot.py`
**Add near other router imports** (~line 50):

```python
from api.usage import router as usage_router
```

**Add near other router includes** (~line 300):

```python
app.include_router(usage_router)
```

**Total lines added to ggbot.py: 2**

---

### Phase 4: Idempotency & Security Fixes (2-3 hours)

**Goal**: Fix the identified security/billing gaps.

#### 4.1 Stripe Meter Event Idempotency

**File**: `billing/stripe_meter_reporter.py`
**Modify `report_to_stripe` function**:

```python
def report_to_stripe(user_id: str, stripe_customer_id: str, total_cost: Decimal, report_date: str) -> bool:
    """Report usage to Stripe with idempotency."""
    try:
        value = str(total_cost)

        # Create idempotency identifier to prevent double billing
        identifier = f"{user_id}:{report_date}:{hash(str(total_cost))}"

        event = stripe.billing.MeterEvent.create(
            event_name=STRIPE_EVENT_NAME,
            payload={
                "stripe_customer_id": stripe_customer_id,
                "value": value,
            },
            identifier=identifier  # Stripe deduplicates based on this
        )

        logger.info(f"Reported ${value} to Stripe (id={identifier})")
        return True
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error: {e}")
        return False
```

#### 4.2 NOWPayments Webhook Idempotency

**File**: `ggbot.py` - NOWPayments webhook handler
**Add at start of handler, after signature verification**:

```python
# Check for duplicate processing
order_id = body_dict.get("order_id", "")
processed_key = f"nowpayments:processed:{order_id}"

if redis_client.get(processed_key):
    logger.info(f"NOWPayments order {order_id} already processed, ignoring duplicate")
    return {"status": "duplicate"}

# Mark as processing (with 24h TTL to handle retries)
redis_client.setex(processed_key, 86400, "processing")

# ... rest of webhook handler ...

# After successful credit grant creation:
redis_client.setex(processed_key, 86400 * 30, "completed")  # Keep for 30 days
```

#### 4.3 Agent LLM Tracking

**File**: `agent/run_agent.py` (or wherever agent LLM calls happen)
**TODO**: Investigate agent architecture and add cost tracking.

This requires more investigation - the agent uses Claude SDK directly. Options:
1. Wrap Claude SDK calls with our logging
2. Add callback/hook to capture usage
3. Estimate costs based on message length

---

### Phase 5: Frontend Integration (3-4 hours)

**Goal**: Display usage in user dashboard.

#### 5.1 Update UserProfile Dropdown

**File**: `frontend/app/forge/components/layout/UserProfile.tsx`

```tsx
// Add usage fetch alongside credit balance
const [usageSummary, setUsageSummary] = useState<UsageSummary | null>(null)

useEffect(() => {
  const fetchUsage = async () => {
    if (userProfile?.subscription_tier === 'usage_based') {
      try {
        const summary = await apiClient.getUsageSummary()
        setUsageSummary(summary)
      } catch (err) {
        console.error('Failed to fetch usage:', err)
      }
    }
  }
  fetchUsage()
}, [userProfile?.subscription_tier])

// In render, replace simple credit display:
{isUsageBased && usageSummary && (
  <div className="mt-2 space-y-1">
    <div className="flex justify-between text-xs">
      <span className="text-[var(--text-muted)]">Credits</span>
      <span>${usageSummary.credits_usd?.toFixed(2) ?? '—'}</span>
    </div>
    <div className="flex justify-between text-xs">
      <span className="text-[var(--text-muted)]">Used</span>
      <span>-${usageSummary.usage_usd.toFixed(2)}</span>
    </div>
    <div className="flex justify-between text-xs font-medium">
      <span className="text-[var(--text-muted)]">Balance</span>
      <span className={usageSummary.net_balance_usd < 5 ? 'text-amber-500' : 'text-emerald-500'}>
        ${usageSummary.net_balance_usd?.toFixed(2) ?? '—'}
      </span>
    </div>
  </div>
)}
```

#### 5.2 Add API Client Methods

**File**: `frontend/lib/api.ts`

```typescript
async getUsageSummary(): Promise<UsageSummary> {
  const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/usage/me`)
  if (!response.ok) throw new Error('Failed to fetch usage')
  return response.json()
}

async getConfigUsage(configId: string): Promise<ConfigUsage> {
  const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/usage/config/${configId}`)
  if (!response.ok) throw new Error('Failed to fetch config usage')
  return response.json()
}

async getUsageBreakdown(): Promise<UsageBreakdown> {
  const response = await this.authenticatedFetch(`${this.baseUrl}/api/v2/usage/breakdown`)
  if (!response.ok) throw new Error('Failed to fetch usage breakdown')
  return response.json()
}
```

#### 5.3 Add Per-Bot Cost to BotRail (Optional)

Show cost in bot cards in the rail.

---

## Testing Plan

### Unit Tests
- [ ] UsageMonitor.get_balance_status returns correct values
- [ ] Redis counter increments work atomically
- [ ] API endpoints return expected format

### Integration Tests
- [ ] LLM call → Redis counter increment → API returns updated value
- [ ] Credits depleted → bots paused → user notified
- [ ] Backfill script correctly populates counters

### Manual Testing
- [ ] Create bot, run decisions, verify counters update
- [ ] Deplete credits, verify bots pause automatically
- [ ] Check frontend displays usage correctly
- [ ] Verify Stripe meter events have idempotency identifiers

---

## Deployment Plan

1. **Deploy Phase 1** (Redis counters)
   - Add code to decision engine
   - Run backfill script
   - Verify counters updating

2. **Deploy Phase 2** (Usage Monitor)
   - Deploy usage_monitor.py
   - Update account_monitor.py
   - Restart account-monitor PM2 service

3. **Deploy Phase 3** (API)
   - Add api/usage.py
   - Mount router in ggbot.py
   - Restart ggbot PM2 service

4. **Deploy Phase 4** (Idempotency)
   - Update stripe_meter_reporter.py
   - Update NOWPayments webhook
   - Deploy during off-peak

5. **Deploy Phase 5** (Frontend)
   - Update components
   - Deploy to Vercel

---

## Files Changed Summary

| File | Change Type | Lines |
|------|-------------|-------|
| `decision/engine_v2.py` | Modify | +15 |
| `core/monitoring/usage_monitor.py` | **NEW** | ~200 |
| `api/usage.py` | **NEW** | ~100 |
| `scripts/backfill_usage_counters.py` | **NEW** | ~80 |
| `scripts/account_monitor.py` | Modify | +15 |
| `billing/stripe_meter_reporter.py` | Modify | +5 |
| `ggbot.py` | Modify | +2 (router mount) |
| `ggbot.py` | Modify | +10 (NOWPayments idempotency) |
| `frontend/lib/api.ts` | Modify | +20 |
| `frontend/.../UserProfile.tsx` | Modify | +30 |

**Total ggbot.py impact: ~12 lines** (vs 200+ if we didn't use account-monitor)

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| User can see current spend | ❌ No | ✅ Yes |
| Per-bot cost visible | ❌ No | ✅ Yes |
| Bots pause when credits depleted | ❌ No | ✅ Yes |
| Scheduler checks permissions | ❌ No | ✅ Yes |
| Usage updates | Daily | Real-time |
| API response time for usage | ~200ms (SQL) | <10ms (Redis) |

---

## Open Questions

1. **Agent LLM tracking** - Need to investigate Claude SDK integration
2. **Notification method** - Email via Resend? Push? In-app?
3. **Low balance threshold** - 20% of credits or fixed $5?
4. **Grace period** - Allow small negative balance before pause?

---

## Related Documentation

- `DOCS/completed/METERED_BILLING_IMPLEMENTATION.md` - Current billing system
- `DOCS/completed/CREDIT_PACKS.md` - Credit packs implementation
- `DOCS/UNIFIED_ACCOUNT_MONITORING.md` - Account monitor architecture
- `billing/stripe_meter_reporter.py` - Daily meter reporting
- `core/domain/user_profile.py` - Permission system
