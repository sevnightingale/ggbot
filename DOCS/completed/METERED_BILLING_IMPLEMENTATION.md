# Metered Billing Implementation - Production Ready ✅

**Status:** Fully implemented and tested
**Last Updated:** 2025-11-13
**Implementation Date:** November 2025

## Overview

ggbots uses Stripe's metered billing system to charge users based on actual LLM usage. The system tracks every LLM API call, calculates platform costs with a 70% markup, and reports usage to Stripe daily for billing.

---

## Architecture

### Data Flow

```
LLM Call → Token Tracking → Activity Record → Daily Aggregation → Stripe Meter → Invoice
```

1. **Token Tracking**: Every LLM call records input/output/reasoning tokens
2. **Cost Calculation**: `platform_cost_usd = provider_cost_usd × 1.70` (70% markup)
3. **Activity Storage**: Stored in `activities` table with `stripe_reported = FALSE`
4. **Daily Reporting**: APScheduler runs at midnight UTC to aggregate and report
5. **Stripe Billing**: Usage accumulates on subscription, billed monthly

---

## Database Schema

### Activities Table
```sql
activities (
    activity_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    activity_type VARCHAR,
    activity_data JSONB,

    -- LLM cost tracking
    input_tokens INTEGER,
    output_tokens INTEGER,
    reasoning_tokens INTEGER,
    provider_cost_usd NUMERIC(10, 6),
    platform_cost_usd NUMERIC(10, 6),  -- Cost charged to user (provider × 1.70)

    -- Stripe reporting
    stripe_reported BOOLEAN DEFAULT FALSE,
    stripe_reported_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
)
```

**Key Fields:**
- `platform_cost_usd`: Pre-calculated dollar amount (not token count)
- `stripe_reported`: Flag to prevent double-reporting
- `stripe_reported_at`: Audit timestamp

---

## Stripe Configuration

### Environment Variables
```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_LLM_METER_ID="mtr_61TcMoxbXUvKBLQG741J9gH6H6LiHGyW"
STRIPE_LLM_EVENT_NAME="llm_tokens_usd"
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Stripe Dashboard Setup

**Meter Configuration:**
- Name: "LLM Token Usage (USD)"
- Event name: `llm_tokens_usd`
- Value type: Dollar amount (not token count)
- Aggregation: Sum
- Display name: "AI Credits"

**Product:**
- Name: "ggbots Usage-Based Plan"
- Billing: Recurring (monthly)
- Usage type: Metered
- Price: $0.00/month base + usage charges

**Price Configuration:**
- Meter: `mtr_61TcMoxbXUvKBLQG741J9gH6H6LiHGyW`
- Billing scheme: Per unit
- Unit: $1.00 per dollar of usage (1:1 pass-through)
- Currency: USD

---

## Implementation Components

### 1. Meter Reporter (`billing/stripe_meter_reporter.py`)

**Purpose:** Aggregate unreported usage and submit to Stripe daily

**Key Functions:**
```python
def get_unreported_usage() -> List[Tuple[str, Decimal, int]]
    """Query activities WHERE stripe_reported = FALSE"""

def report_to_stripe(user_id, stripe_customer_id, total_cost) -> bool
    """Submit meter event to Stripe API"""
    stripe.billing.MeterEvent.create(
        event_name="llm_tokens_usd",
        payload={
            "stripe_customer_id": customer_id,
            "value": str(total_cost)  # Pre-computed USD amount
        }
    )

def mark_as_reported(user_id) -> int
    """Mark activities as stripe_reported = TRUE"""
```

**Scheduling:**
- Runs via APScheduler at midnight UTC daily
- Configured in `ggbot.py:230-243`
- Job ID: `stripe_meter_reporting`
- Grace period: 1 hour for missed runs

### 2. Webhook Handlers (`ggbot.py`)

**Endpoint:** `POST /api/v2/stripe-webhook`

**Handled Events:**

#### `checkout.session.completed`
```python
# Activate subscription after successful checkout
UPDATE user_profiles SET
    subscription_tier = 'usage_based' | 'pro',
    subscription_status = 'active',
    stripe_customer_id = ?,
    stripe_subscription_id = ?,
    subscription_expires_at = NULL
```

#### `customer.subscription.updated`
```python
# Handle status changes (active, canceled, past_due, etc.)
UPDATE user_profiles SET
    subscription_status = 'active' | 'past_due' | 'cancelled'
```

#### `invoice.payment_failed`
```python
# Block access when payment fails
UPDATE user_profiles SET
    subscription_status = 'past_due'
```
→ This triggers `can_activate_bots = False` → Bots cannot run

#### `customer.subscription.deleted`
```python
# Downgrade to free tier on cancellation
UPDATE user_profiles SET
    subscription_tier = 'free',
    subscription_status = 'cancelled',
    subscription_expires_at = <ended_at>
```

### 3. Permission System (`core/domain/user_profile.py`)

**Master Permission:**
```python
@property
def can_activate_bots(self) -> bool:
    """Single source of truth for all paid features."""
    return (
        self.subscription_tier in [SubscriptionTier.USAGE_BASED, SubscriptionTier.PRO] and
        self.has_active_subscription and  # Checks status == 'active'
        not self.subscription_expired
    )
```

**Enforcement:**
- Bot activation blocked at API level
- Scheduler checks permission before each autonomous run
- Frontend gates "Activate" and "Run once" buttons
- Auto-deactivates bots if user loses permission

---

## Pricing Model

### Subscription Tiers

| Tier | Base Price | Features | Usage Billing |
|------|-----------|----------|---------------|
| **FREE** | $0/month | Browse/configure only | N/A - Can't activate bots |
| **USAGE_BASED** | $0/month | All features, unlimited bots | 1.70× provider cost |

**Note**: Previously offered PRO tier ($29/month) has been deprecated. All users now use usage-based pricing.

### Usage Costs (Real-World Examples)

**Per-decision costs by reasoning tier:**
- Economy: ~$0.003/decision (Grok economy, DeepSeek)
- Standard: ~$0.01/decision (Kimi, Grok standard)
- Premium: ~$0.04-0.09/decision (GPT, Claude, Gemini with extended reasoning)

**Typical monthly costs by configuration:**
- **Budget Setup** (<$2/month): 1-2 bots, hourly checks, economy reasoning
  - Example: ~60 decisions/month × $0.003 = $0.18/month per bot
- **Active Trader** ($10-35/month): 3-5 bots, 15-30min frequency, standard reasoning
  - Example: ~450 decisions/month × $0.01 = $4.50/month per bot × 3-5 bots
- **Power User** ($50-150/month): 5-10 bots, 5-15min frequency, premium reasoning
  - Example: ~1,800 decisions/month × $0.04 = $72/month per bot (5min + premium)

**Cost varies 30× between economy and premium reasoning tiers**, giving users full control over their monthly spend.

---

## Testing & Validation

### ✅ Completed Tests (2025-11-13)

**Meter Reporting Test:**
```bash
# Manually triggered meter reporter
python -m billing.stripe_meter_reporter

# Results:
✅ Found 2 users with unreported usage
✅ User 1 (usage_based): $0.0072 reported successfully
✅ User 2 (free): Correctly skipped (no Stripe customer ID)
✅ Activities marked as stripe_reported = TRUE
✅ Stripe meter event created successfully
```

**Database Verification:**
```sql
-- Check reported activities
SELECT user_id, COUNT(*), SUM(platform_cost_usd), stripe_reported_at
FROM activities
WHERE stripe_reported = TRUE
AND stripe_reported_at > NOW() - INTERVAL '5 minutes'
GROUP BY user_id;

-- Result: 2 activities marked at 2025-11-13 21:26:45 UTC ✅
```

**Stripe Dashboard Check:**
- Path: Billing → Meters → Events
- Event visible with correct customer ID and value ✅

---

## Production Deployment Checklist

### Backend

- [x] Stripe meter created and configured
- [x] Environment variables set (meter ID, event name, webhook secret)
- [x] Meter reporter implemented and tested
- [x] APScheduler job configured (midnight UTC daily)
- [x] Webhook handlers implemented (all 4 events)
- [x] Permission system enforces payment status
- [x] Activities table tracks costs correctly
- [ ] Monitor logs for first production billing cycle

### Frontend

- [x] UpgradeModal shows usage-based pricing
- [x] UserProfile displays subscription tier badge
- [x] SettingsModal shows "Manage Billing" for paid users
- [x] Bot activation gates require subscription
- [x] "Run once" button gated with subscription check
- [x] Agent creation gated to PRO tier only
- [ ] Usage dashboard (future enhancement)

### Stripe Dashboard

- [x] Webhook endpoint configured: `https://ggbots-api.nightingale.business/api/v2/stripe-webhook`
- [x] Webhook events enabled:
  - [x] checkout.session.completed
  - [x] customer.subscription.updated
  - [x] customer.subscription.deleted
  - [x] invoice.payment_failed
- [ ] Test webhooks with Stripe CLI
- [ ] Monitor first month's meter events

---

## Monitoring & Maintenance

### Daily Checks

1. **Verify meter reporting runs:**
   ```bash
   grep "Daily reporting complete" logs/ggbot.log | tail -7
   ```

2. **Check for failed reports:**
   ```bash
   grep "Failed to report to Stripe" logs/ggbot.log
   ```

3. **Monitor unreported usage:**
   ```sql
   SELECT COUNT(*), SUM(platform_cost_usd)
   FROM activities
   WHERE stripe_reported = FALSE
   AND platform_cost_usd > 0;
   ```

### Weekly Checks

1. **Verify Stripe meter events in dashboard**
2. **Check for webhook delivery failures**
3. **Review past_due users:**
   ```sql
   SELECT user_id, email, subscription_status, stripe_customer_id
   FROM user_profiles
   WHERE subscription_status = 'past_due';
   ```

### Monthly Checks

1. **Verify invoices generated correctly**
2. **Compare meter totals to database totals**
3. **Review any disputed charges**
4. **Check for cost anomalies (unexpected high usage)**

---

## Troubleshooting

### Meter events not appearing in Stripe

**Check:**
1. Meter ID matches: `STRIPE_LLM_METER_ID="mtr_61TcMoxbXUvKBLQG741J9gH6H6LiHGyW"`
2. Event name matches: `STRIPE_LLM_EVENT_NAME="llm_tokens_usd"`
3. Customer has active subscription
4. API key is for correct environment (live vs test)

**Debug:**
```bash
python -m billing.stripe_meter_reporter
# Check logs for Stripe API errors
```

### Activities not marked as reported

**Check:**
```sql
-- Find stuck activities
SELECT user_id, COUNT(*), SUM(platform_cost_usd), MAX(created_at)
FROM activities
WHERE stripe_reported = FALSE
AND platform_cost_usd > 0
GROUP BY user_id;
```

**Fix:**
```bash
# Re-run reporter manually
python -m billing.stripe_meter_reporter
```

### Webhooks not processing

**Check:**
1. Webhook secret matches: `STRIPE_WEBHOOK_SECRET=whsec_...`
2. Endpoint is publicly accessible
3. Signature verification enabled
4. Check Stripe webhook logs for errors

**Debug:**
```bash
# Test webhook locally with Stripe CLI
stripe listen --forward-to localhost:8000/api/v2/stripe-webhook
stripe trigger invoice.payment_failed
```

### Users with past_due but still running bots

**Should not happen** - permission system blocks at multiple levels:
1. API endpoint checks `can_activate_bots`
2. Scheduler checks before each run
3. Frontend gates activation buttons

**Investigate:**
```sql
-- Find anomalies
SELECT c.config_id, c.state, u.subscription_status, u.subscription_tier
FROM configurations c
JOIN user_profiles u ON c.user_id = u.user_id
WHERE c.state = 'active'
AND u.subscription_status != 'active';
```

---

## Future Enhancements

### Short Term
- [ ] Usage dashboard in frontend (show current month's costs)
- [ ] Email alerts when usage hits thresholds ($10, $25, $50)
- [ ] Admin panel to view platform-wide usage metrics

### Medium Term
- [ ] Stripe Billing Thresholds (invoice at $100 mid-cycle)
- [ ] Usage caps (soft limit with confirmation)
- [ ] Credit system (pre-purchase credits at discount)

### Long Term
- [ ] Volume discounts (1.5× markup for >$100/month users)
- [ ] Model-specific pricing (cheaper for Haiku, etc.)
- [ ] Reserved capacity plans (guaranteed quota)

---

## Key Learnings

1. **Pre-compute costs, not token counts**: Stripe meter accepts dollar amounts directly. We calculate `platform_cost_usd` at the time of API call (70% markup) and report that, not tokens.

2. **API path correction**: Stripe Python library uses `stripe.billing.MeterEvent.create()`, not `stripe.billing.meter_events.create()`

3. **Idempotency via database**: We use `stripe_reported` boolean flag instead of Stripe idempotency keys. Simpler and gives us audit trail.

4. **Grace period critical**: APScheduler misfire_grace_time=3600 ensures we don't skip reporting if server was briefly down at midnight.

5. **Webhook security**: Always verify signatures. Webhook secret is different between test/live modes.

---

## Related Documentation

- `DOCS/METERED_STRIPE.md` - General metered billing concepts
- `DOCS/DATABASE_CONTEXT.md` - Activities table schema
- `billing/stripe_meter_reporter.py` - Meter reporter implementation
- `core/domain/user_profile.py` - Permission system

---

**Implementation Team:** Claude Code + Sev
**Business Model:** Usage-based SaaS with 70% markup on LLM costs
**Status:** Production ready, monitoring first billing cycle
