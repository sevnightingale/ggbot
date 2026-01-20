# Prepaid Tier Implementation Plan

**Status**: ✅ IMPLEMENTED
**Priority**: HIGH
**Estimated Effort**: 4-6 hours
**Created**: 2026-01-20
**Completed**: 2026-01-20

---

## Problem Statement

Currently, users who buy credit packs are placed on `usage_based` tier with metered billing. This creates confusion:

1. **User expectation**: "I prepaid $25, when it runs out my bot stops, I won't be charged"
2. **Actual behavior**: Metered billing + credit grants as discounts = user may be charged for overage

### Race Condition Issue
- Usage monitor pauses bots when credits deplete
- But there's a delay between LLM call and pause
- Overage usage gets reported to Stripe
- User gets charged for difference at end of billing period

---

## Solution: Separate Tiers

### Proposed Tier Structure

| Tier | Description | Billing | Bot Stops When |
|------|-------------|---------|----------------|
| `free` | Trial users | None | N/A (can't run bots) |
| `prepaid` | Credit pack users | None (prepaid credits) | Credits exhausted |
| `usage_based` | Pay-as-you-go | Stripe metered (weekly) | Never (just billed) |
| `pro` | Premium subscription | $29/mo + metered | Never |

### Key Differences: PREPAID vs USAGE_BASED

| Aspect | PREPAID | USAGE_BASED |
|--------|---------|-------------|
| Stripe subscription | NO | YES (metered) |
| Credit Grants | YES | OPTIONAL |
| Meter reporting | NO | YES |
| Hard-block on depletion | YES (before LLM call) | NO (soft pause after) |
| Invoice at end of period | NO | YES |

---

## Implementation Checklist

### Phase 1: Backend Domain Model

#### 1.1 Update SubscriptionTier enum
**File**: `core/domain/user_profile.py`

```python
class SubscriptionTier(Enum):
    FREE = "free"
    PREPAID = "prepaid"       # NEW: Credit pack users
    USAGE_BASED = "usage_based"
    PRO = "pro"
```

#### 1.2 Update permission checks
**File**: `core/domain/user_profile.py`

```python
@property
def can_activate_bots(self) -> bool:
    return (
        self.subscription_tier in [
            SubscriptionTier.PREPAID,      # ADD THIS
            SubscriptionTier.USAGE_BASED,
            SubscriptionTier.PRO
        ] and
        self.has_active_subscription and
        not self.subscription_expired
    )

@property
def is_prepaid_tier(self) -> bool:
    """Check if user is on prepaid (credit pack) tier."""
    return self.subscription_tier == SubscriptionTier.PREPAID

@property
def requires_credit_check(self) -> bool:
    """Check if user requires credit balance check before LLM calls."""
    return self.subscription_tier == SubscriptionTier.PREPAID
```

### Phase 2: Hard Credit Check (Pre-LLM)

#### 2.1 Add credit check before LLM call
**File**: `decision/engine_v2.py`

Before making LLM call, check if prepaid user has credits:

```python
async def _check_prepaid_credits(self) -> bool:
    """Check if prepaid user has sufficient credits. Returns True if OK to proceed."""
    profile = await user_service.get_profile(self.user_id)

    if not profile.is_prepaid_tier:
        return True  # Not prepaid, no check needed

    # Check credit balance
    credits = await self._get_stripe_credits(self.user_id)
    usage = await self._get_current_usage(self.user_id)

    if credits - usage <= 0:
        raise InsufficientCreditsError(
            f"Prepaid credits exhausted. Credits: ${credits:.2f}, Usage: ${usage:.2f}"
        )

    return True
```

Call this at start of `run_decision()`:
```python
async def run_decision(self, ...):
    # Hard credit check for prepaid users
    await self._check_prepaid_credits()

    # ... rest of decision logic
```

### Phase 3: Skip Meter Reporting for Prepaid

#### 3.1 Update meter reporter
**File**: `billing/stripe_meter_reporter.py`

```python
def get_unreported_usage() -> List[Tuple[str, Decimal, int]]:
    """Query activities table for unreported LLM usage (EXCLUDING prepaid users)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    a.user_id,
                    SUM(a.platform_cost_usd) as total_cost,
                    COUNT(*) as activity_count
                FROM activities a
                JOIN user_profiles up ON a.user_id = up.user_id
                WHERE a.stripe_reported = FALSE
                  AND a.platform_cost_usd IS NOT NULL
                  AND a.platform_cost_usd > 0
                  AND up.subscription_tier != 'prepaid'  -- EXCLUDE PREPAID
                GROUP BY a.user_id
                ORDER BY total_cost DESC
            """)
```

#### 3.2 Mark prepaid usage as "reported" (no reporting needed)
**File**: `decision/engine_v2.py`

For prepaid users, set `stripe_reported = TRUE` immediately (since we won't report it):

```python
# In _log_llm_activity()
stripe_reported = profile.is_prepaid_tier  # True for prepaid, False for others
```

### Phase 4: Update Usage Monitor

#### 4.1 Separate handling for prepaid vs usage_based
**File**: `core/monitoring/usage_monitor.py`

```python
async def _check_user_credits(self, user_id: str) -> str:
    profile = await user_service.get_profile(user_id)
    balance = await self.get_balance_status(user_id)

    if profile.is_prepaid_tier:
        # PREPAID: Hard block - this shouldn't happen if pre-LLM check works
        # But if it does, pause immediately
        if balance.net_balance <= 0:
            await self._pause_all_user_bots(user_id, reason="prepaid_credits_exhausted")
            await self._notify_user(user_id, "prepaid_depleted", balance)
            return "paused"
    else:
        # USAGE_BASED: Soft warning only (they'll be billed)
        if balance.is_low:
            await self._notify_user(user_id, "credits_low", balance)
            return "warned"

    return "ok"
```

### Phase 5: Credit Purchase Flow

#### 5.1 Update checkout webhook
**File**: `ggbot.py` (checkout.session.completed handler)

When user purchases a credit pack:
- Set `subscription_tier = 'prepaid'`
- Create Credit Grant
- DO NOT create Stripe subscription (no metered billing)

```python
if is_credit_purchase:
    # Create credit grant (existing logic)
    stripe.billing.CreditGrant.create(...)

    # Set tier to prepaid (NEW)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET subscription_tier = 'prepaid',
                    stripe_customer_id = %s,
                    updated_at = NOW()
                WHERE user_id = %s
                AND subscription_tier = 'free'  -- Only upgrade from free
            """, (customer_id, user_id))
```

#### 5.2 Handle upgrade from prepaid to usage_based
If prepaid user subscribes to metered billing:
- Keep existing credits (they'll apply as discounts)
- Change tier to `usage_based`
- Create metered subscription

### Phase 6: Frontend Updates

#### 6.1 Update permissions type
**File**: `frontend/lib/permissions.tsx`

```typescript
subscription_tier: 'free' | 'prepaid' | 'usage_based' | 'pro'
```

#### 6.2 Update UserProfile display
**File**: `frontend/app/forge/components/layout/UserProfile.tsx`

Show different UI for prepaid users:
```typescript
if (userProfile?.subscription_tier === 'prepaid') {
  // Show: Credits: $45.00, Used: $27.00, Remaining: $18.00
  // Show: "Add more credits" button
}
```

### Phase 7: Database Migration

**NO MIGRATION NEEDED!**

The database already has a `ggbase` enum value with 0 users. We'll repurpose it:
- `ggbase` in database = `PREPAID` in code
- Display to users as "Prepaid" or "Credit Pack"

This avoids complex ALTER TYPE operations on PostgreSQL enums.

```python
# In SubscriptionTier enum:
PREPAID = "ggbase"  # Maps to existing database enum value
```

---

## Stripe Dashboard Changes

### Required Actions

1. **NO subscription for prepaid users**
   - Prepaid users only have a Stripe Customer record
   - Credit Grants attached to customer
   - No subscription = no invoices

2. **Credit Grant Configuration**
   - Keep existing Credit Grant setup
   - Grants apply to metered usage (for usage_based users who also have credits)
   - For prepaid users, grants are tracked but not auto-applied (we track ourselves)

3. **Verify Meter Settings**
   - Meter should only aggregate usage_based/pro users
   - Backend filter ensures prepaid users aren't reported

---

## Files To Modify

| File | Changes |
|------|---------|
| `core/domain/user_profile.py` | Add PREPAID tier, `is_prepaid_tier`, `requires_credit_check` |
| `decision/engine_v2.py` | Add pre-LLM credit check, set `stripe_reported=True` for prepaid |
| `billing/stripe_meter_reporter.py` | Exclude prepaid users from meter reporting |
| `core/monitoring/usage_monitor.py` | Separate prepaid vs usage_based handling |
| `ggbot.py` | Update checkout webhook to set prepaid tier |
| `frontend/lib/permissions.tsx` | Add 'prepaid' to tier type |
| `frontend/app/forge/components/layout/UserProfile.tsx` | Prepaid-specific UI |
| `api/usage.py` | Return prepaid-specific balance info |

---

## Testing Plan

1. **Create prepaid user flow**
   - New user purchases $25 credit pack
   - Verify tier = 'prepaid'
   - Verify no Stripe subscription created
   - Verify Credit Grant created

2. **Run bot as prepaid user**
   - LLM calls should succeed while credits > 0
   - `stripe_reported` should be TRUE (no meter reporting)
   - Usage tracked in Redis/activities

3. **Credit depletion**
   - When credits hit 0, next LLM call should FAIL immediately
   - Error: "Prepaid credits exhausted"
   - Bot should be paused
   - Email notification sent

4. **No invoice for prepaid**
   - At end of billing period, prepaid user gets no invoice
   - No charges to card

5. **Upgrade path**
   - Prepaid user can subscribe to usage_based
   - Existing credits carry over as discounts

---

## Rollback Plan

If issues arise:
1. Revert tier checks in `can_activate_bots` to exclude PREPAID
2. Existing prepaid users would lose bot access until manually fixed
3. Credit Grants remain intact in Stripe

---

## Open Questions

1. **Should prepaid credits expire?**
   - Current: No expiration
   - Consider: 1 year expiration?

2. **Can prepaid user add more credits?**
   - Yes, they buy another credit pack
   - Credits stack

3. **What happens when prepaid user's credits run out mid-trade?**
   - Position management uses same LLM
   - Risk: Open position can't be managed
   - Mitigation: Reserve ~$1 for position management?

4. **Should we notify prepaid users at low balance?**
   - Yes, at 20% remaining
   - Email + in-app notification

---

## Success Metrics

- Zero prepaid users charged via Stripe invoice
- Clean separation: prepaid users never appear in meter events
- < 100ms latency added by pre-LLM credit check
- User confusion reduced (clear "prepaid" vs "pay as you go" messaging)
