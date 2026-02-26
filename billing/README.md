# Billing Module

Real-time usage tracking, metered billing via Stripe, and credit management for the ggbots platform.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           BILLING FLOW                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  LLM Call (decision/engine_v2.py)                                       │
│       │                                                                  │
│       ├──→ activities table (source of truth)                           │
│       │         └── platform_cost_usd, stripe_reported flag             │
│       │                                                                  │
│       └──→ Redis counters (real-time visibility)                        │
│                 ├── usage:user:{id}:{YYYY-MM}                           │
│                 ├── usage:config:{id}:{YYYY-MM}                         │
│                 └── usage:config:{id}:{YYYY-MM-DD}                      │
│                                                                          │
│  Daily Meter Reporter (billing/stripe_meter_reporter.py)                │
│       │                                                                  │
│       └──→ Stripe Billing Meter API                                     │
│                 └── Aggregates unreported usage → meter events          │
│                                                                          │
│  Usage Monitor (core/monitoring/usage_monitor.py)                       │
│       │                                                                  │
│       ├──→ Checks credit balance vs usage (every 60s)                   │
│       ├──→ Pauses bots when credits depleted                            │
│       └──→ Caches usage summaries (every 5min)                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
billing/
├── README.md                    # This file
├── __init__.py
└── stripe_meter_reporter.py     # Daily usage aggregation to Stripe

api/
└── usage.py                     # Real-time usage API endpoints

core/monitoring/
└── usage_monitor.py             # Credit watchdog + summary caching

scripts/
└── backfill_usage_counters.py   # One-time Redis backfill from activities
```

---

## Subscription Tiers

| Tier | DB Value | Description | Billing | Bot Stops When |
|------|----------|-------------|---------|----------------|
| `FREE` | `free` | Trial users | None | N/A (can't run bots) |
| `PREPAID` | `prepaid` | Credit pack users | None (prepaid) | Credits exhausted |
| `USAGE_BASED` | `usage_based` | Pay-as-you-go | Stripe metered (weekly) | Never (just billed) |
| `PRO` | `pro` | Premium subscription | $29/mo + metered | Never |

**Cost Formula**: `platform_cost_usd = provider_cost_usd × 1.70` (70% markup)

### $10 Spending Cap (Usage-Based)

To limit bad debt exposure, usage_based subscriptions have a **$10 billing threshold**:

1. When usage hits $10, Stripe automatically generates an invoice
2. Invoice is charged to customer's payment method
3. If payment succeeds: User continues, counter resets
4. If payment fails: User marked `past_due`, all bots paused, email sent

**Implementation**:
- Stripe `billing_thresholds.amount_gte = 1000` on all usage_based subscriptions
- `invoice.payment_failed` webhook pauses bots via `handle_payment_failed()`
- UsageMonitor provides backup check for missed webhooks

**Max bad debt exposure**: $10 (vs unlimited previously)

### PREPAID vs USAGE_BASED

| Aspect | PREPAID | USAGE_BASED |
|--------|---------|-------------|
| Stripe subscription | NO | YES (metered) |
| Credit Grants | YES | OPTIONAL |
| Meter reporting | NO | YES |
| Hard-block on depletion | YES (before LLM call) | NO (soft pause after) |
| Invoice at end of period | NO | YES |

**PREPAID flow**: User buys credits → tier set to `prepaid` → pre-LLM credit check → bot pauses when $0 → no invoice ever.

**USAGE_BASED flow**: User subscribes → metered billing → credits apply as discounts → invoice for net usage.

---

## Stripe Integration

### Environment Variables

```bash
STRIPE_SECRET_KEY=sk_live_xxx         # Stripe API key
STRIPE_LLM_METER_ID=mtr_xxx           # Billing meter ID
STRIPE_LLM_EVENT_NAME=llm_tokens_usd  # Meter event name
STRIPE_PRICE_ID_USAGE=price_xxx       # $0/mo usage-based price
STRIPE_WEBHOOK_SECRET=whsec_xxx       # Webhook signature verification
```

### Billing Meter

**Meter ID**: `mtr_61TcMoxbXUvKBLQG741J9gH6H6LiHGyW`
**Event Name**: `llm_tokens_usd`
**Aggregation**: Sum of cent values per billing period

**Price Configuration** (updated 2026-01-22):
- **Current Price**: `price_1SsU8VJ9gH6H6LiHvuJy6LxP` ($0.01 per cent)
- **Legacy Price**: `price_1SSz0EJ9gH6H6LiH7SBooW80` ($1.00 per unit - ARCHIVED)

**Why cents?** Stripe truncates meter values to integers. With $1/unit, a user with $0.72 usage would be billed $0 (floor(0.72) = 0 units). With $0.01/cent, they're correctly billed $0.72 (72 cents × $0.01).

### Daily Meter Reporting

`billing/stripe_meter_reporter.py` runs daily at midnight UTC via APScheduler:

1. Query `activities` table for unreported usage (`stripe_reported = FALSE`)
2. **Exclude prepaid users** (JOIN filter: `subscription_tier != 'prepaid'`)
3. Aggregate by user
4. Send meter events to Stripe (with idempotency key)
5. Mark activities as reported

```python
# Idempotency key format (prevents double billing)
identifier = f"{user_id}:{report_date}:{hash(value)}"
```

**Note**: Prepaid users are excluded at two levels:
1. Activity logged with `stripe_reported=TRUE` (never enters queue)
2. Meter reporter query JOINs user_profiles to exclude `prepaid` tier

### Credit Grants

Users prepay for credits via:
- **Stripe Checkout** (card payments)
- **NOWPayments** (crypto payments)

Credits apply automatically to metered billing via Stripe Credit Grants API.

---

## Redis Usage Counters

### Key Structure

```
# User-level (updated on every LLM call)
usage:user:{user_id}:{YYYY-MM}           # Monthly user spend

# Config-level (updated on every LLM call)
usage:config:{config_id}:{YYYY-MM}       # Monthly bot spend
usage:config:{config_id}:{YYYY-MM-DD}    # Daily bot spend (90-day TTL)
usage:config:total:{config_id}            # All-time bot spend (no TTL)

# Cached summaries (updated every 5min by usage monitor)
usage:summary:{user_id}                   # JSON: usage + credits + net balance

# Credit notification state (prevents spam)
credit_state:{user_id}                    # "ok" | "low" | "depleted" (90-day TTL)

# Bot pause tracking (for frontend UX)
bot:pause_reason:{config_id}              # Reason bot was paused (24h TTL)
                                          # Values: "prepaid_credits_exhausted", "payment_failed"

# Idempotency tracking
nowpayments:processed:{order_id}          # Prevents duplicate crypto credit grants
```

### Update Location

`decision/engine_v2.py:880-895` - Inside `_log_llm_activity()`:

```python
# Atomic increments after logging to activities table
pipe = redis_client.pipeline()
pipe.incrbyfloat(f"usage:user:{self.user_id}:{period}", float(platform_cost))
pipe.incrbyfloat(f"usage:config:{self.config_id}:{period}", float(platform_cost))
pipe.incrbyfloat(f"usage:config:{self.config_id}:{day}", float(platform_cost))
pipe.expire(f"usage:config:{self.config_id}:{day}", 90 * 24 * 3600)
if is_prepaid:
    pipe.incrbyfloat(f"usage:prepaid:{self.user_id}", float(platform_cost))
pipe.incrbyfloat(f"usage:config:total:{self.config_id}", float(platform_cost))
pipe.execute()
```

---

## Usage Monitor

`core/monitoring/usage_monitor.py` runs inside the `account-monitor` PM2 service.

### Features

| Feature | Interval | Description |
|---------|----------|-------------|
| Credit check | 60s | Check balance for users with active bots |
| Bot pause | On depletion | Auto-pause bots when credits exhausted |
| Low balance warning | 60s | Log warning when <20% credits remaining |
| Summary caching | 5min | Pre-compute usage summaries for fast API |

### Balance Status Logic

```python
is_low = (credits > 0) and (net < credits * 0.2 or net < 5)
is_depleted = (net <= 0) and (credits > 0)
```

### Balance Calculation (All Tiers)

**Both prepaid and usage_based tiers use Redis monthly counter** for usage tracking:

| Component | Source | Why |
|-----------|--------|-----|
| Credits | Stripe Credit Balance API | Total credits purchased |
| Usage | Redis `usage:user:{id}:{YYYY-MM}` | Real-time, matches decision engine |

**Why Redis for all tiers** (updated 2026-02-04): The activities table can have incomplete records due to async logging, while Redis is updated synchronously during LLM calls. Using Redis ensures UsageMonitor and decision engine see identical usage values.

**Why Stripe balance is unreliable for usage**: Stripe Credit Grants only decrease when applied to invoices. Prepaid users never get invoices, so Stripe always reports full credit amount as "available" even after usage.

**Fix Location**: `get_balance_status()` in `usage_monitor.py` uses Redis for both tiers.

### Bot Pause Flow

When UsageMonitor detects depleted credits:

1. **Database**: Sets `state = 'inactive'` on all user's active bots
2. **Redis**: Stores pause reason: `bot:pause_reason:{config_id}` = `"prepaid_credits_exhausted"` (24h TTL)
3. **Pub/Sub**: Publishes to `bot_lifecycle` channel (for real-time SSE updates)
4. **Email**: Sends depletion notification to user

**Scheduler Enforcement** (`ggbot.py:run_once()`):

When APScheduler fires for a bot, `run_once()` checks state BEFORE executing:

```python
state = await config_service.get_bot_state(config_id, user_id)
if state != 'active':
    logger.info(f"Skipping execution - state is '{state}', removing scheduler job")
    remove_bot_job(user_id, config_id, timeframe)
    return
```

This ensures paused bots don't execute even if the scheduler job wasn't removed yet.

### Email Notification Logic

**State-based notifications** prevent spam by tracking user credit state in Redis:

| State | Trigger | Notification |
|-------|---------|--------------|
| `ok` → `low` | Balance < 20% or < $5 | Low balance email (once) |
| `low` → `depleted` | Balance ≤ $0 | Depleted email (once) |
| `ok` → `depleted` | Sudden depletion | Depleted email (once) |

**Key features:**
- Redis key: `credit_state:{user_id}` → `"ok"` | `"low"` | `"depleted"`
- Notifications only sent on **state transitions** (not repeatedly)
- State persists across service restarts (90-day TTL)
- State cleared automatically when credits are added → enables future alerts

**Credit state cleared by:**
- `handle_checkout_completed()` in ggbot.py (Stripe card payments)
- `nowpayments_webhook()` in ggbot.py (Crypto payments)

---

## API Endpoints

### `GET /api/v2/usage/me`

Current user's usage summary (cached or live).

**Response:**
```json
{
  "period": "2026-01",
  "usage_usd": 12.34,
  "credits_usd": 50.00,
  "net_balance_usd": 37.66,
  "updated_at": "2026-01-15T10:30:00Z",
  "cached": true
}
```

### `GET /api/v2/usage/config/{config_id}`

Specific bot's usage (instant from Redis).

**Response:**
```json
{
  "config_id": "uuid",
  "config_name": "BTC Scalper",
  "period": "2026-01",
  "period_usage_usd": 5.67,
  "today_usage_usd": 0.89,
  "total_usage_usd": 42.15
}
```

### `GET /api/v2/usage/breakdown`

Usage breakdown by all user's bots.

**Response:**
```json
{
  "period": "2026-01",
  "breakdown": [
    {"config_id": "uuid", "config_name": "BTC Scalper", "state": "active", "period_usage_usd": 8.50},
    {"config_id": "uuid", "config_name": "ETH Bot", "state": "paused", "period_usage_usd": 3.84}
  ],
  "total_usage_usd": 12.34
}
```

### `GET /api/v2/usage/history/{config_id}?days=30`

Daily usage history for a bot (max 90 days).

**Response:**
```json
{
  "config_id": "uuid",
  "config_name": "BTC Scalper",
  "history": [
    {"date": "2026-01-15", "usage_usd": 0.89},
    {"date": "2026-01-14", "usage_usd": 1.23}
  ]
}
```

---

## Credit Packs

### Stripe (Card) Flow

1. User selects amount ($10, $25, $50, $100)
2. Frontend calls `POST /api/v2/credits/purchase`
3. Backend creates Stripe Checkout session
4. User completes payment
5. Webhook `checkout.session.completed` triggers Credit Grant creation

### NOWPayments (Crypto) Flow

1. User selects amount
2. Frontend calls `POST /api/v2/credits/crypto-checkout`
3. Backend creates NOWPayments invoice with order_id
4. User pays in crypto
5. IPN callback triggers Credit Grant creation (with idempotency)

**Order ID Format** (4 parts for uniqueness):
```
credits_{user_id}_{amount_cents}_{timestamp}

Example: credits_b29178ce-9205-4e86-a0f9-5b7dfab29e35_1000_1770177090
         └─────┘ └──────────────────────────────────┘ └──┘ └────────┘
         prefix          user UUID                   $10   unix timestamp
```

### Idempotency

NOWPayments webhook (`ggbot.py:nowpayments_webhook`):

```python
# Check for duplicate processing
processed_key = f"nowpayments:processed:{order_id}"
if redis_client.get(processed_key):
    return {"status": "duplicate"}
redis_client.setex(processed_key, 86400, "processing")

# Parse order_id (supports 3 or 4 parts)
parts = order_id.split("_")
user_id = parts[1]
amount_cents = int(parts[2])
# parts[3] is optional timestamp (ignored, used for uniqueness)

# ... create Stripe Credit Grant ...
redis_client.setex(processed_key, 86400 * 30, "completed")
```

---

## Scripts

### Backfill Usage Counters

Run once after deploying to populate Redis from existing `activities` data:

```bash
cd /home/sev/ggbot && source .venv/bin/activate

# Preview
python scripts/backfill_usage_counters.py --dry-run

# Execute
python scripts/backfill_usage_counters.py
```

### Manual Meter Report

Force meter reporting (normally runs at midnight UTC):

```bash
python -m billing.stripe_meter_reporter
```

---

## Database Tables

### `activities` (source of truth)

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | UUID | Owner |
| `config_id` | UUID | Bot (nullable for agent) |
| `platform_cost_usd` | DECIMAL | Billable cost (after markup) |
| `provider_cost_usd` | DECIMAL | Raw LLM cost |
| `stripe_reported` | BOOLEAN | Sent to Stripe meter |
| `input_tokens` | INT | LLM input tokens |
| `output_tokens` | INT | LLM output tokens |

### `user_profiles`

| Column | Type | Description |
|--------|------|-------------|
| `stripe_customer_id` | TEXT | Stripe customer ID |
| `stripe_subscription_id` | TEXT | Stripe subscription ID (NULL for prepaid) |
| `subscription_tier` | TEXT | `free`, `prepaid`, `usage_based`, `pro` |
| `subscription_status` | TEXT | `active`, `canceled`, etc. |

---

## Troubleshooting

### Usage Not Updating

1. Check Redis connection: `redis-cli PING`
2. Verify counters exist: `redis-cli KEYS "usage:user:*"`
3. Check decision engine logs for Redis errors
4. Run backfill script if counters missing

### Credit Balance Wrong

1. Check Stripe dashboard for Credit Grants
2. Verify `stripe_customer_id` in user_profiles
3. Check usage monitor logs for Stripe API errors
4. **Verify Redis counter matches config counters**: User-level counter should equal sum of their config counters
5. If counters diverged, fix with: `redis_client.set(f"usage:user:{user_id}:{period}", sum_of_config_counters)`

### Bots Not Pausing on Depletion

1. Verify account-monitor PM2 service running: `pm2 status account-monitor`
2. Check logs: `pm2 logs account-monitor`
3. Verify user has `credits > 0` (depletion only triggers if user HAD credits)
4. Check Redis usage counter matches what decision engine sees
5. After pausing, verify `run_once()` state check is working: look for "Skipping execution" log

### Crypto Payments Not Adding Credits

1. Check NOWPayments dashboard for payment status (must be "finished")
2. Check Redis for idempotency key: `redis-cli GET nowpayments:processed:{order_id}`
3. If stuck at "processing", webhook failed - manually create Credit Grant
4. Check ggbot logs for "Invalid order_id format" errors
5. Verify order_id has correct format: `credits_{user_id}_{amount_cents}_{timestamp}`

### Double Billing

1. Check `identifier` field in Stripe meter events
2. Verify `stripe_reported` flag in activities table
3. Check for duplicate meter reporter runs

---

## Frontend Integration

### UserProfile Dropdown (`frontend/.../UserProfile.tsx`)

Adaptive display based on billing model:

```typescript
// Credit pack users (credits > 0)
🪙 Credits    $50.00
   Used       -$12.34
   Balance    $37.66  // amber if < $5

// Depleted prepaid user
⚠️ Credits depleted — bots paused  // red warning

// Metered users (credits = 0)
🪙 This week  $12.34
```

**API**: `getUsageSummary()` → `GET /api/v2/usage/me`

### Credit Warning Banner (`frontend/.../ActivationBar.tsx`)

When a bot is paused due to credit exhaustion, shows amber warning:

```typescript
// Bot with pause_reason === 'prepaid_credits_exhausted'
┌────────────────────────────────────────────────────────┐
│ ⚠️ Bot paused — your prepaid credits have run out  [Add Credits] │
└────────────────────────────────────────────────────────┘
```

**Data source**: SSE dashboard data includes `pause_reason` from Redis for inactive bots.

**Implementation**: `BotConfiguration.pause_reason` field populated by `_fetch_pause_reasons_for_bots()` in `core/sse/dashboard_data.py`.

### ActivationBar Cost Display (`frontend/.../ActivationBar.tsx`)

Three cost indicators:

```typescript
// Total all-time cost (from usage:config:total:{id})
🪙 $42.15 total

// Daily cost — actual avg when usage exists, estimate for new bots
🪙 ~$0.35/day       // actual: period_usage / days_elapsed
🪙 ~$14.52/day est.  // estimate: model × tier × frequency (from lib/cost-estimation.ts)

// Day 1 of month fallback
🪙 $0.89 today
```

**Cost estimation** (`frontend/lib/cost-estimation.ts`): Shared `MODEL_TIER_COSTS` and `FREQUENCY_TO_DECISIONS` tables. `estimateDailyCost(configData)` returns predicted daily cost from model, tier, frequency. Used by ActivationBar (pre-activation) and UpgradeModal (paywall).

**Activity cost**: `platform_cost_usd` returned per activity from `/api/v2/activities/{config_id}`. Displayed as "Cost: $0.XXXX" in activity modal `LLMThoughtContent`.

**API**: `getConfigUsage(configId)` → `GET /api/v2/usage/config/{id}`

**Refresh**: Every 5 minutes via `setInterval`

### API Client Methods (`frontend/lib/api.ts`)

```typescript
// User-level summary
apiClient.getUsageSummary(): Promise<{
  period: string
  usage_usd: number
  credits_usd: number | null
  net_balance_usd: number | null
  cached: boolean
}>

// Per-bot usage
apiClient.getConfigUsage(configId): Promise<{
  config_id: string
  config_name: string
  period: string
  period_usage_usd: number
  today_usage_usd: number
  total_usage_usd: number
}>
```

---

## Related Documentation

- `DOCS/completed/METERED_BILLING_IMPLEMENTATION.md` - Original billing setup
- `DOCS/completed/CREDIT_PACKS.md` - Credit packs implementation
- `DOCS/completed/USAGE_BILLING_TRACKING.md` - Usage tracking planning doc
- `core/monitoring/README.md` - Account monitor architecture
- `frontend/README.md` - Frontend usage display implementation
