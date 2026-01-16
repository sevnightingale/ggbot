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

| Tier | Description | Billing |
|------|-------------|---------|
| `free` | Trial users, limited features | No billing |
| `usage_based` | Pay-as-you-go | Stripe metered subscription |

**Cost Formula**: `platform_cost_usd = provider_cost_usd × 1.70` (70% markup)

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
**Aggregation**: Sum of USD values per billing period

### Daily Meter Reporting

`billing/stripe_meter_reporter.py` runs daily at midnight UTC via APScheduler:

1. Query `activities` table for unreported usage (`stripe_reported = FALSE`)
2. Aggregate by user
3. Send meter events to Stripe (with idempotency key)
4. Mark activities as reported

```python
# Idempotency key format (prevents double billing)
identifier = f"{user_id}:{report_date}:{hash(value)}"
```

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

# Cached summaries (updated every 5min by usage monitor)
usage:summary:{user_id}                   # JSON: usage + credits + net balance

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
  "today_usage_usd": 0.89
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
3. Backend creates NOWPayments invoice
4. User pays in crypto
5. IPN callback triggers Credit Grant creation (with idempotency)

### Idempotency

NOWPayments webhook (`ggbot.py:4710-4721`):

```python
# Check for duplicate processing
processed_key = f"nowpayments:processed:{order_id}"
if redis_client.get(processed_key):
    return {"status": "duplicate"}
redis_client.setex(processed_key, 86400, "processing")
# ... process payment ...
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
| `stripe_subscription_id` | TEXT | Stripe subscription ID |
| `subscription_tier` | TEXT | `free` or `usage_based` |
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

### Bots Not Pausing on Depletion

1. Verify account-monitor PM2 service running: `pm2 status account-monitor`
2. Check logs: `pm2 logs account-monitor`
3. Verify user has `credits > 0` (depletion only triggers if user HAD credits)

### Double Billing

1. Check `identifier` field in Stripe meter events
2. Verify `stripe_reported` flag in activities table
3. Check for duplicate meter reporter runs

---

## Related Documentation

- `DOCS/completed/METERED_BILLING_IMPLEMENTATION.md` - Original billing setup
- `DOCS/completed/CREDIT_PACKS.md` - Credit packs implementation
- `DOCS/completed/USAGE_BILLING_TRACKING.md` - Usage tracking planning doc
- `core/monitoring/README.md` - Account monitor architecture
