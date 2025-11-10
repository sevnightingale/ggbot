# Metered Billing Implementation Plan

**Status**: Planning
**Created**: 2025-11-08
**Target**: Complete pricing model overhaul with usage-based billing

---

## Executive Summary

Complete platform pricing overhaul from freemium (Free + $29 Pro) to pure usage-based + premium subscription model:

- **Usage Tier**: Pay-as-you-go, charged monthly based on LLM token consumption with 70% markup
- **Premium Tier**: $100/month subscription unlocks agents + includes base usage allowance + premium features
- **No Free Tier**: All users pay for consumption, low barrier to test (estimated $2-5 for minimal usage)
- **Billing**: Post-paid monthly with $20 threshold for mid-cycle invoicing

---

## Pricing Model Design

### Usage Tier (All Users)

**Pricing Formula**:
```
User Cost = (Provider Token Cost × 1.70) per token
```

**70% Markup Covers**:
- Market intelligence costs ($195/month Grok sources)
- Infrastructure (servers, Redis, PostgreSQL, PM2)
- Profit margin

**Billing Mechanics**:
- User adds credit card at signup (required)
- Platform tracks token consumption in real-time
- Usage reported to Stripe throughout billing cycle
- Stripe invoices at **end of month** OR **$20 threshold**, whichever comes first
- Failed payment = bots pause until resolved

**Example Monthly Costs** (estimates):
- Minimal testing (DeepSeek, 1 bot, 1h frequency): $3-5/month
- Medium usage (GPT-4, 3 bots, 15m frequency): $20-30/month
- Heavy usage (GPT-5, 5 bots, 5m frequency): $60-100/month

**User Controls**:
- Real-time usage dashboard showing current month spend
- Email alerts at $10, $20, $50 milestones
- Optional hard cap: user sets max monthly spend (e.g., $50), bots pause when hit
- Usage estimator shows "Estimated $X-Y/month" based on config settings

### Premium Tier ($100/month)

**Core Feature**: Agent access (strategy builder + autonomous trading agents)

**Additional Premium Features** (TBD):
- Base usage allowance included (e.g., $20-30 worth of tokens free per month)
- Priority support
- Telegram signal publishing
- Advanced market intelligence (future premium data sources)
- Early access to new features

**Billing**:
- Fixed $100/month recurring charge (separate Stripe line item)
- Usage charges continue to accrue on top
- Total monthly invoice: $100 + usage overages
- Example: $100 (sub) + $47.23 (usage) = $147.23

**NOT Premium** (Available to Usage Tier):
- Live trading (Symphony, AsterDEX) - anyone can connect
- Signal validation mode
- Paper trading
- All market intelligence currently available

---

## LLM Provider Strategy: OpenRouter

### Current Architecture
- Direct API integration with 4 providers: OpenAI, Anthropic, DeepSeek, XAI
- Separate credential management per provider
- Different API response formats
- Inconsistent token tracking methods

### Proposed: OpenRouter Centralization

**OpenRouter** provides unified API for 200+ models with consistent response format.

**Advantages**:
- ✅ Single API key management (no per-provider credentials)
- ✅ Standardized response format with token usage
- ✅ Automatic fallback routing (if model unavailable)
- ✅ Built-in rate limiting and error handling
- ✅ Transparent pricing pass-through

**Token Tracking Compatibility**:
- OpenRouter returns usage data in OpenAI-compatible format:
  ```json
  {
    "usage": {
      "prompt_tokens": 150,
      "completion_tokens": 75,
      "total_tokens": 225
    }
  }
  ```
- Also includes cost data: `"total_cost": 0.00234`
- We can validate our markup calculation against OpenRouter's reported cost

**Migration Path**:
1. Add OpenRouter as provider option alongside existing direct integrations
2. Test token tracking accuracy (compare direct API vs OpenRouter)
3. Gradually migrate models to OpenRouter
4. Eventually deprecate direct integrations (keep as fallback)

**Research Needed**:
- ✅ Verify all current models available via OpenRouter
- ✅ Test token usage reporting accuracy
- ✅ Compare latency (direct API vs OpenRouter proxy)
- ✅ Confirm cost transparency (can we see per-model pricing?)

---

## Technical Architecture

### Phase 1: Token Tracking Infrastructure

**Database Schema** (`token_usage` table):
```sql
CREATE TABLE token_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    config_id UUID REFERENCES configurations(config_id),

    -- LLM metadata
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'openrouter', etc.
    model VARCHAR(100) NOT NULL,    -- 'gpt-4', 'claude-opus-4', etc.

    -- Token consumption
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,

    -- Cost calculation
    provider_cost_usd NUMERIC(10, 6) NOT NULL,  -- Raw provider cost
    platform_cost_usd NUMERIC(10, 6) NOT NULL,  -- With 70% markup
    markup_percentage NUMERIC(5, 2) DEFAULT 70.00,

    -- Context
    execution_type VARCHAR(50),  -- 'extraction', 'decision', 'agent_chat', 'signal_validation'
    decision_id UUID REFERENCES decisions(decision_id),

    -- Billing
    stripe_reported BOOLEAN DEFAULT FALSE,
    stripe_reported_at TIMESTAMP WITH TIME ZONE,
    billing_period VARCHAR(7),  -- 'YYYY-MM' for easy aggregation

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_token_usage_user_period ON token_usage(user_id, billing_period);
CREATE INDEX idx_token_usage_config ON token_usage(config_id, created_at);
CREATE INDEX idx_token_usage_stripe_pending ON token_usage(user_id, stripe_reported, created_at)
    WHERE stripe_reported = FALSE;
CREATE INDEX idx_token_usage_billing_period ON token_usage(billing_period, created_at);
```

**Model Pricing Table** (`llm_model_pricing`):
```sql
CREATE TABLE llm_model_pricing (
    pricing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,

    -- Per-token costs (in USD per 1K tokens)
    input_cost_per_1k NUMERIC(10, 6) NOT NULL,
    output_cost_per_1k NUMERIC(10, 6) NOT NULL,

    -- Metadata
    effective_date DATE NOT NULL,
    deprecated_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    source_url TEXT,  -- Link to pricing page
    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(provider, model, effective_date)
);

-- Example data
INSERT INTO llm_model_pricing (provider, model, input_cost_per_1k, output_cost_per_1k, effective_date, source_url)
VALUES
    ('openai', 'gpt-4', 0.030, 0.060, '2025-01-01', 'https://openai.com/pricing'),
    ('openai', 'gpt-5', 0.050, 0.100, '2025-01-01', 'https://openai.com/pricing'),
    ('anthropic', 'claude-opus-4', 0.015, 0.075, '2025-01-01', 'https://anthropic.com/pricing'),
    ('deepseek', 'deepseek-chat', 0.0005, 0.002, '2025-01-01', 'https://deepseek.com/pricing');
```

**Token Tracking Service** (`core/services/token_tracking_service.py`):
```python
class TokenTrackingService:
    """Service for tracking LLM token usage and calculating costs."""

    async def record_usage(
        self,
        user_id: str,
        config_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        execution_type: str,
        decision_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record token usage and calculate costs with markup.

        Returns:
            {
                "usage_id": "...",
                "provider_cost_usd": 0.00234,
                "platform_cost_usd": 0.00398,  # With 70% markup
                "markup_applied": 70.0
            }
        """
        # Get current pricing for model
        pricing = await self._get_model_pricing(provider, model)

        # Calculate raw provider cost
        input_cost = (input_tokens / 1000) * pricing['input_cost_per_1k']
        output_cost = (output_tokens / 1000) * pricing['output_cost_per_1k']
        provider_cost = input_cost + output_cost

        # Apply 70% markup
        platform_cost = provider_cost * 1.70

        # Store in database
        usage_id = await self._insert_usage_record(...)

        return {
            "usage_id": usage_id,
            "provider_cost_usd": provider_cost,
            "platform_cost_usd": platform_cost,
            "markup_applied": 70.0
        }

    async def get_current_month_spend(self, user_id: str) -> Decimal:
        """Get total spend for current billing period."""
        current_period = datetime.now().strftime('%Y-%m')

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(platform_cost_usd), 0)
                    FROM token_usage
                    WHERE user_id = %s AND billing_period = %s
                """, (user_id, current_period))
                return cur.fetchone()[0]

    async def get_unreported_usage(self, user_id: str) -> List[Dict]:
        """Get usage not yet reported to Stripe."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        usage_id,
                        platform_cost_usd,
                        created_at
                    FROM token_usage
                    WHERE user_id = %s
                      AND stripe_reported = FALSE
                    ORDER BY created_at
                """, (user_id,))
                return cur.fetchall()
```

**LLM Client Wrapper** (modify all decision/agent/extraction LLM calls):
```python
# Before (current)
response = await llm_client.generate_completion(prompt)

# After (with tracking)
response = await llm_client.generate_completion(prompt)

# Track token usage
await token_tracking_service.record_usage(
    user_id=user_id,
    config_id=config_id,
    provider=response['provider'],
    model=response['model'],
    input_tokens=response['usage']['prompt_tokens'],
    output_tokens=response['usage']['completion_tokens'],
    execution_type='decision',
    decision_id=decision_id
)
```

**Integration Points** (every LLM call needs tracking):
- ✅ `decision/engine_v2.py` - Decision generation
- ✅ `extraction/v2/` - Market intelligence (if using LLMs)
- ✅ `agent/run_agent.py` - Agent conversations
- ✅ `signals/listener_service.py` - Signal validation

---

### Phase 2: Stripe Metered Billing Setup

**Product Configuration in Stripe**:
```
Product: "ggbots Usage-Based Billing"
Price: Metered billing
  - Billing period: Monthly
  - Usage aggregation: Sum
  - Unit: "USD spent"
  - Unit price: $1.00 per unit

Example: User consumes $47.23 → report quantity=47.23 → Stripe charges $47.23
```

**Subscription Creation** (on user signup):
```python
async def create_metered_subscription(user_id: str, email: str):
    """Create Stripe subscription with metered usage."""

    # Get or create Stripe customer
    customer = stripe.Customer.create(
        email=email,
        metadata={'user_id': user_id}
    )

    # Create subscription with metered line item
    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[{
            'price': os.getenv('STRIPE_METERED_PRICE_ID'),
        }],
        billing_thresholds={
            'amount_gte': 2000  # Invoice at $20 threshold (in cents)
        },
        metadata={
            'user_id': user_id,
            'subscription_type': 'usage_based'
        }
    )

    # Store in database
    await user_service.update_stripe_info(
        user_id=user_id,
        stripe_customer_id=customer.id,
        stripe_subscription_id=subscription.id,
        subscription_tier='usage_based'
    )
```

**Usage Reporting Job** (hourly background task):
```python
async def report_usage_to_stripe():
    """
    Aggregate unreported token usage and send to Stripe.
    Run every hour via APScheduler.
    """
    # Get all users with unreported usage
    users_with_usage = await get_users_with_unreported_usage()

    for user_id in users_with_usage:
        # Get unreported usage
        unreported = await token_tracking_service.get_unreported_usage(user_id)

        if not unreported:
            continue

        # Sum total cost
        total_cost = sum(row['platform_cost_usd'] for row in unreported)

        # Get subscription item ID
        subscription_item_id = await get_stripe_subscription_item_id(user_id)

        # Report to Stripe (quantity = dollars spent)
        timestamp = int(time.time())
        idempotency_key = f"usage-{user_id}-{timestamp}"

        stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=int(total_cost * 100) / 100,  # Round to 2 decimals
            timestamp=timestamp,
            action='set',  # or 'increment'
            idempotency_key=idempotency_key
        )

        # Mark as reported
        await token_tracking_service.mark_as_reported(
            usage_ids=[row['usage_id'] for row in unreported],
            reported_at=datetime.now()
        )

        logger.info(f"Reported ${total_cost:.2f} usage for user {user_id}")
```

**Webhook Handlers** (update existing):
```python
@app.post("/api/v2/stripe-webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""

    # Existing events: checkout.session.completed, subscription.updated, etc.

    # New events to handle:
    if event_type == 'invoice.payment_succeeded':
        await handle_usage_invoice_paid(event['data']['object'])

    elif event_type == 'invoice.payment_failed':
        await handle_usage_payment_failed(event['data']['object'])

    elif event_type == 'customer.subscription.updated':
        # Check if threshold was hit (mid-cycle invoice)
        await handle_threshold_invoice(event['data']['object'])

async def handle_usage_payment_failed(invoice):
    """Pause all bots when payment fails."""
    user_id = invoice['metadata']['user_id']

    # Mark user as payment_failed
    await user_service.mark_payment_failed(user_id)

    # Stop all active bots
    configs = await config_service.get_user_configs(user_id)
    for config in configs:
        if config['state'] == 'active':
            await stop_bot(config['config_id'], user_id)

    # Send email notification
    await email_service.send_payment_failed_notification(user_id, invoice['amount_due'] / 100)
```

---

### Phase 3: Premium Subscription ($100/month)

**Database Schema Updates**:
```sql
-- Update user_profiles to track premium subscription separately
ALTER TABLE user_profiles
    ADD COLUMN premium_subscription_id VARCHAR(100),
    ADD COLUMN premium_tier_active BOOLEAN DEFAULT FALSE,
    ADD COLUMN premium_base_allowance_usd NUMERIC(10, 2) DEFAULT 0.00,
    ADD COLUMN premium_base_allowance_used_usd NUMERIC(10, 2) DEFAULT 0.00;
```

**Stripe Product**:
```
Product: "ggbots Pro - Agent Access"
Price: $100/month (recurring, NOT metered)
Features:
  - Agent creation unlocked
  - $30 base usage allowance included
  - Priority support
  - Early access to new features
```

**Combined Subscription** (user can upgrade from usage-based):
```python
async def upgrade_to_premium(user_id: str):
    """Add premium tier to existing usage-based subscription."""

    # Get existing subscription
    subscription = await get_stripe_subscription(user_id)

    # Add premium line item
    stripe.Subscription.modify(
        subscription.id,
        items=[
            {'id': subscription.items.data[0].id},  # Keep metered item
            {'price': os.getenv('STRIPE_PREMIUM_PRICE_ID')}  # Add fixed $100 item
        ]
    )

    # Update database
    await user_service.activate_premium_tier(user_id)
```

**Base Allowance Logic**:
```python
async def calculate_billable_usage(user_id: str, period: str) -> Decimal:
    """
    Calculate billable usage after applying premium base allowance.

    Example:
        Total usage: $47.23
        Premium allowance: $30.00
        Billable: $17.23 (only this gets metered)
    """
    profile = await user_service.get_profile(user_id)

    total_usage = await token_tracking_service.get_period_spend(user_id, period)

    if profile.premium_tier_active:
        allowance = profile.premium_base_allowance_usd
        billable = max(0, total_usage - allowance)
    else:
        billable = total_usage

    return billable
```

**Permission Updates**:
```python
# core/domain/user_profile.py

@property
def can_use_agents(self) -> bool:
    """Check if user can create and use agents."""
    return self.premium_tier_active

@property
def remaining_base_allowance(self) -> Decimal:
    """Get remaining base usage allowance for current month."""
    if not self.premium_tier_active:
        return Decimal('0.00')

    return max(0, self.premium_base_allowance_usd - self.premium_base_allowance_used_usd)
```

---

### Phase 4: Usage Estimator

**Estimation Service** (`core/services/usage_estimator.py`):
```python
class UsageEstimator:
    """Estimate monthly costs based on bot configuration."""

    async def estimate_monthly_cost(
        self,
        config: BotConfigV2
    ) -> Dict[str, Any]:
        """
        Estimate monthly cost for a bot configuration.

        Returns:
            {
                "estimated_low": 15.23,
                "estimated_high": 28.45,
                "executions_per_month": 1440,
                "avg_tokens_per_execution": 2500,
                "breakdown": {
                    "extraction": 5.00,
                    "decision": 20.00,
                    "total": 25.00
                }
            }
        """
        # Calculate monthly executions
        frequency = config.decision.analysis_frequency
        executions_per_month = self._calc_executions(frequency)  # e.g., 5m = 8640/month

        # Estimate tokens per execution
        avg_tokens = await self._estimate_tokens_per_execution(config)

        # Get model pricing
        model = config.llm_config.provider
        pricing = await self._get_model_pricing(model)

        # Calculate cost
        cost_per_execution = (avg_tokens / 1000) * pricing['avg_cost_per_1k']
        monthly_cost = cost_per_execution * executions_per_month

        # Apply 70% markup
        platform_cost = monthly_cost * 1.70

        # Add variance (+/- 25%)
        estimated_low = platform_cost * 0.75
        estimated_high = platform_cost * 1.25

        return {
            "estimated_low": round(estimated_low, 2),
            "estimated_high": round(estimated_high, 2),
            "executions_per_month": executions_per_month,
            "avg_tokens_per_execution": avg_tokens,
            "model": model
        }

    async def _estimate_tokens_per_execution(self, config: BotConfigV2) -> int:
        """
        Estimate tokens consumed per bot execution.

        Method 1: Use historical averages for similar configs
        Method 2: Calculate from prompt templates + market data size
        """
        # Get historical data
        similar_configs = await self._find_similar_configs(config)
        if similar_configs:
            avg_tokens = await self._get_avg_tokens_for_configs(similar_configs)
            return avg_tokens

        # Fallback: estimate from templates
        # Extraction: ~500 tokens (market data is mostly JSON, not counted as input)
        # Decision prompt: ~2000 tokens (system prompt + market data formatting + user strategy)
        # Decision output: ~300 tokens

        return 2800  # Reasonable default

    def _calc_executions(self, frequency: str) -> int:
        """Calculate monthly executions from analysis frequency."""
        freq_map = {
            '5m': 8640,   # 288 per day × 30
            '15m': 2880,  # 96 per day × 30
            '30m': 1440,  # 48 per day × 30
            '1h': 720,    # 24 per day × 30
            '4h': 180,    # 6 per day × 30
            '1d': 30      # 1 per day × 30
        }
        return freq_map.get(frequency, 720)  # Default to 1h
```

**API Endpoint**:
```python
@app.post("/api/v2/estimate-cost")
async def estimate_cost(
    config: BotConfigV2,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Estimate monthly cost for bot configuration.

    Request: Bot config (can be unsaved draft)
    Response: {
        "estimated_low": 15.23,
        "estimated_high": 28.45,
        "note": "Actual costs may vary based on market conditions and trade frequency"
    }
    """
    estimator = UsageEstimator()
    estimate = await estimator.estimate_monthly_cost(config)

    return {
        **estimate,
        "note": "Actual costs may vary based on market conditions and trade frequency"
    }
```

**Frontend Integration**:
```typescript
// Real-time cost estimator in bot config UI
const [costEstimate, setCostEstimate] = useState<{low: number, high: number} | null>(null)

useEffect(() => {
  // Debounce config changes
  const timer = setTimeout(async () => {
    const estimate = await apiClient.estimateCost(currentConfig)
    setCostEstimate(estimate)
  }, 1000)

  return () => clearTimeout(timer)
}, [currentConfig.llm_config.provider, currentConfig.decision.analysis_frequency])

// Display in UI
<div className="cost-estimate">
  <InfoIcon />
  <span>Estimated cost: ${costEstimate.low} - ${costEstimate.high}/month</span>
</div>
```

---

### Phase 5: Usage Dashboard

**Backend API Endpoints**:
```python
@app.get("/api/v2/usage/current-month")
async def get_current_month_usage(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get current month's usage breakdown.

    Response: {
        "total_spend": 47.23,
        "billing_period": "2025-11",
        "days_in_period": 8,
        "estimated_month_end": 176.11,
        "breakdown_by_bot": [...],
        "breakdown_by_model": [...],
        "next_invoice_date": "2025-12-01",
        "hard_cap": 100.00,
        "hard_cap_remaining": 52.77
    }
    """
    current_period = datetime.now().strftime('%Y-%m')

    # Get total spend
    total_spend = await token_tracking_service.get_current_month_spend(current_user.user_id)

    # Get breakdown by bot
    breakdown_by_bot = await get_usage_by_config(current_user.user_id, current_period)

    # Get breakdown by model
    breakdown_by_model = await get_usage_by_model(current_user.user_id, current_period)

    # Estimate month-end spend (linear projection)
    days_elapsed = datetime.now().day
    days_in_month = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
    estimated_month_end = total_spend * (days_in_month / days_elapsed)

    # Get hard cap
    profile = await user_service.get_profile(current_user.user_id)
    hard_cap = profile.usage_hard_cap_usd

    return {
        "total_spend": float(total_spend),
        "billing_period": current_period,
        "days_in_period": days_elapsed,
        "estimated_month_end": float(estimated_month_end),
        "breakdown_by_bot": breakdown_by_bot,
        "breakdown_by_model": breakdown_by_model,
        "next_invoice_date": ...,
        "hard_cap": float(hard_cap) if hard_cap else None,
        "hard_cap_remaining": float(hard_cap - total_spend) if hard_cap else None
    }

@app.get("/api/v2/usage/history")
async def get_usage_history(
    months: int = Query(6, le=12),
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Get historical usage for past N months.

    Response: [
        {"period": "2025-11", "total_spend": 47.23, "executions": 1440},
        {"period": "2025-10", "total_spend": 62.18, "executions": 2100},
        ...
    ]
    """
    history = await token_tracking_service.get_usage_history(
        current_user.user_id,
        months=months
    )
    return history

@app.post("/api/v2/usage/set-hard-cap")
async def set_hard_cap(
    hard_cap: Optional[float] = None,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Set monthly spending hard cap.

    Request: {"hard_cap": 100.00}  (null to disable)
    """
    await user_service.set_usage_hard_cap(current_user.user_id, hard_cap)
    return {"hard_cap": hard_cap, "status": "updated"}
```

**Frontend Component** (`frontend/components/UsageDashboard.tsx`):
```typescript
export function UsageDashboard() {
  const [usage, setUsage] = useState<CurrentMonthUsage | null>(null)
  const [history, setHistory] = useState<UsageHistory[]>([])

  // Fetch current month
  useEffect(() => {
    apiClient.getCurrentMonthUsage().then(setUsage)
  }, [])

  // Fetch history
  useEffect(() => {
    apiClient.getUsageHistory(6).then(setHistory)
  }, [])

  return (
    <div className="usage-dashboard">
      {/* Current Month Spend (Big Number) */}
      <div className="current-spend">
        <h2>Current Month</h2>
        <div className="amount">${usage.total_spend.toFixed(2)}</div>
        <div className="subtitle">
          {usage.days_in_period} days elapsed
          • Est. month-end: ${usage.estimated_month_end.toFixed(2)}
        </div>

        {/* Hard Cap Progress Bar */}
        {usage.hard_cap && (
          <div className="hard-cap-bar">
            <div
              className="progress"
              style={{width: `${(usage.total_spend / usage.hard_cap) * 100}%`}}
            />
            <span>${usage.hard_cap_remaining.toFixed(2)} remaining of ${usage.hard_cap} cap</span>
          </div>
        )}
      </div>

      {/* Breakdown by Bot (Pie Chart) */}
      <div className="breakdown-bots">
        <h3>Spend by Bot</h3>
        <PieChart data={usage.breakdown_by_bot} />
      </div>

      {/* Breakdown by Model (Bar Chart) */}
      <div className="breakdown-models">
        <h3>Spend by Model</h3>
        <BarChart data={usage.breakdown_by_model} />
      </div>

      {/* Historical Trend (Line Chart) */}
      <div className="historical-trend">
        <h3>6-Month Trend</h3>
        <LineChart data={history} />
      </div>

      {/* Hard Cap Settings */}
      <div className="hard-cap-settings">
        <h3>Spending Limit</h3>
        <input
          type="number"
          value={hardCap ?? ''}
          onChange={(e) => setHardCap(parseFloat(e.target.value))}
          placeholder="No limit"
        />
        <button onClick={saveHardCap}>Save Limit</button>
        <p className="help-text">
          Bots will pause when this limit is reached. Leave blank for no limit.
        </p>
      </div>

      {/* Download Invoices */}
      <div className="invoices">
        <h3>Past Invoices</h3>
        <button onClick={() => openStripeBillingPortal()}>
          View & Download Invoices
        </button>
      </div>
    </div>
  )
}
```

---

### Phase 6: Alerts & Safeguards

**Email Alerts** (Resend integration):
```python
# core/services/alert_service.py

class UsageAlertService:
    """Service for sending usage alerts to users."""

    ALERT_THRESHOLDS = [10, 20, 50, 100]  # USD

    async def check_and_send_alerts(self, user_id: str):
        """
        Check current spend and send alerts at milestones.
        Run hourly via background job.
        """
        current_spend = await token_tracking_service.get_current_month_spend(user_id)

        # Get last alert sent
        last_alert = await self._get_last_alert_threshold(user_id)

        # Find next threshold
        for threshold in self.ALERT_THRESHOLDS:
            if current_spend >= threshold and (last_alert is None or last_alert < threshold):
                # Send alert
                await self._send_usage_alert(user_id, threshold, current_spend)

                # Record alert sent
                await self._record_alert_sent(user_id, threshold)

                break

    async def _send_usage_alert(self, user_id: str, threshold: float, current_spend: Decimal):
        """Send usage alert email."""
        profile = await user_service.get_profile(user_id)

        # Estimate month-end
        days_elapsed = datetime.now().day
        days_in_month = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
        estimated_month_end = current_spend * (days_in_month / days_elapsed)

        await resend_service.send_email(
            to=profile.email,
            template='usage_alert',
            context={
                'threshold': threshold,
                'current_spend': float(current_spend),
                'estimated_month_end': float(estimated_month_end),
                'days_elapsed': days_elapsed,
                'dashboard_url': f"{os.getenv('FRONTEND_URL')}/usage"
            }
        )
```

**Hard Cap Enforcement** (background job every 5 minutes):
```python
async def enforce_hard_caps():
    """
    Check all users with hard caps and pause bots if exceeded.
    Run every 5 minutes via APScheduler.
    """
    users_with_caps = await get_users_with_hard_caps()

    for user in users_with_caps:
        current_spend = await token_tracking_service.get_current_month_spend(user.user_id)

        if current_spend >= user.usage_hard_cap_usd:
            # Hard cap exceeded - pause all bots
            logger.warning(f"User {user.user_id} exceeded hard cap: ${current_spend} >= ${user.usage_hard_cap_usd}")

            # Get all active bots
            configs = await config_service.get_user_configs(user.user_id)
            for config in configs:
                if config['state'] == 'active':
                    await stop_bot(config['config_id'], user.user_id)

            # Mark user as hard cap exceeded
            await user_service.mark_hard_cap_exceeded(user.user_id)

            # Send notification
            await email_service.send_hard_cap_exceeded_notification(
                user.user_id,
                current_spend,
                user.usage_hard_cap_usd
            )
```

**Database Schema for Alerts**:
```sql
CREATE TABLE usage_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    billing_period VARCHAR(7) NOT NULL,
    threshold_usd NUMERIC(10, 2) NOT NULL,
    current_spend_usd NUMERIC(10, 2) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, billing_period, threshold_usd)
);

-- Add to user_profiles
ALTER TABLE user_profiles
    ADD COLUMN usage_hard_cap_usd NUMERIC(10, 2),
    ADD COLUMN hard_cap_exceeded BOOLEAN DEFAULT FALSE;
```

---

## User Experience Flows

### New User Signup
1. User signs up via Supabase Auth
2. **Redirect to payment setup**: "Add payment method to start using ggbots"
3. Stripe Checkout (setup mode, $0 charge)
4. Create metered subscription on success
5. Redirect to bot creation: "Create your first bot - estimated $3-5/month"
6. User configures bot (sees live cost estimate)
7. Save & activate bot
8. Bot runs, tokens consumed, dashboard shows "$0.47 spent this month"

### Existing User Testing Platform
1. User with low budget wants to test
2. Creates bot with:
   - Model: DeepSeek (cheapest)
   - Frequency: 1h (low frequency)
   - Symbols: BTC/USDT (single symbol)
3. Cost estimator shows: "Estimated $2-4/month"
4. Runs for 1 week
5. Usage dashboard: "$1.23 spent (7 days) - Est. month-end: $5.29"
6. Total invoice at month-end: $5.29

### Power User Scaling Up
1. User wants to test multiple strategies
2. Creates 5 bots:
   - 2 with GPT-5, 5m frequency (expensive, high frequency)
   - 2 with Claude Opus 4, 15m frequency (medium)
   - 1 with DeepSeek, 1h frequency (cheap, low frequency)
3. Cost estimator shows: "Total estimated $60-90/month"
4. Day 3: Alert email "You've spent $10 this month"
5. Day 7: Alert email "You've spent $25 - Est. month-end: $107"
6. Day 10: Hits $20 threshold → mid-cycle invoice for $20
7. Day 20: Alert email "You've spent $50"
8. Day 30: Final invoice for $67.23 (total $87.23 for month)
9. User reviews breakdown: GPT-5 bots consumed 70% of spend

### Premium Tier Upgrade
1. User wants to create agents
2. Clicks "Create Agent" → blocked: "Upgrade to Pro to unlock agents"
3. Clicks "Upgrade to Pro" → Stripe Checkout for $100/month
4. Subscription updated: now has 2 line items (metered + $100 fixed)
5. Agent creation unlocked
6. Usage continues to accrue (but first $30 covered by base allowance)
7. Month-end invoice: $100 (Pro) + $17.23 (usage over allowance) = $117.23

### Hard Cap Protection
1. User sets hard cap: $50/month
2. Creates 3 bots, runs for 2 weeks
3. Day 14: Current spend $48.67
4. Day 15: Bot execution pushes spend to $50.12
5. Background job detects hard cap exceeded
6. **All bots automatically paused**
7. Email sent: "Your bots have been paused - $50 spending limit reached"
8. User can:
   - Raise hard cap in settings
   - Wait for next billing cycle (bots auto-resume)
   - Review usage breakdown to optimize costs

---

## Migration Strategy

### Existing Users (258 total, 3 Pro)

**No Automated Migration** (user will handle manually):
- User will communicate pricing changes to existing users
- Existing Pro users ($29/month): TBD by user (grandfather? convert?)
- Existing free users: TBD by user (grace period? forced upgrade?)

**Technical Requirements** (support manual migration):
```python
# Admin script to convert user to new model
async def migrate_user_to_metered(user_id: str, preserve_pro: bool = False):
    """
    Migrate existing user to metered billing model.

    Args:
        user_id: User to migrate
        preserve_pro: If True, keep existing Pro subscription alongside metered
    """
    # Get current subscription
    profile = await user_service.get_profile(user_id)

    if not profile.stripe_customer_id:
        # New customer - create metered subscription
        await create_metered_subscription(user_id, profile.email)
    else:
        # Existing customer - modify subscription
        subscription_id = profile.stripe_subscription_id

        if preserve_pro:
            # Add metered item to existing Pro subscription
            stripe.Subscription.modify(
                subscription_id,
                items=[
                    {'id': ...},  # Keep existing Pro item
                    {'price': os.getenv('STRIPE_METERED_PRICE_ID')}  # Add metered
                ]
            )
        else:
            # Replace Pro with metered
            stripe.Subscription.modify(
                subscription_id,
                items=[
                    {'id': ..., 'deleted': True},  # Remove Pro item
                    {'price': os.getenv('STRIPE_METERED_PRICE_ID')}  # Add metered
                ]
            )

    logger.info(f"Migrated user {user_id} to metered billing (preserve_pro={preserve_pro})")
```

### Database Schema Updates

**New Tables**:
- `token_usage` (metered billing records)
- `llm_model_pricing` (pricing reference)
- `usage_alerts` (alert history)

**Updated Tables**:
```sql
-- user_profiles
ALTER TABLE user_profiles
    ADD COLUMN premium_subscription_id VARCHAR(100),
    ADD COLUMN premium_tier_active BOOLEAN DEFAULT FALSE,
    ADD COLUMN premium_base_allowance_usd NUMERIC(10, 2) DEFAULT 0.00,
    ADD COLUMN premium_base_allowance_used_usd NUMERIC(10, 2) DEFAULT 0.00,
    ADD COLUMN usage_hard_cap_usd NUMERIC(10, 2),
    ADD COLUMN hard_cap_exceeded BOOLEAN DEFAULT FALSE;

-- No changes to configurations or other tables
```

---

## Testing Strategy

### Phase 1: Token Tracking Accuracy
- ✅ Run 100 test bot executions across all models
- ✅ Verify token counts match LLM API responses
- ✅ Verify cost calculations match model pricing
- ✅ Test 70% markup applied correctly
- ✅ Verify database storage and retrieval

### Phase 2: Stripe Integration
- ✅ Test subscription creation (dev mode)
- ✅ Test usage reporting (send test records)
- ✅ Verify Stripe invoices generate correctly
- ✅ Test billing threshold (trigger $20 mid-cycle invoice)
- ✅ Test webhook handling (payment success/failure)

### Phase 3: Cost Estimator
- ✅ Compare estimates vs actual costs for 10 configs
- ✅ Verify estimates within 25% variance
- ✅ Test all frequency settings (5m, 15m, 30m, 1h, 4h, 1d)
- ✅ Test all LLM models

### Phase 4: Hard Cap Enforcement
- ✅ Set hard cap $10, run bot until exceeded
- ✅ Verify bots pause automatically
- ✅ Verify email notification sent
- ✅ Verify bots resume after cap raised

### Phase 5: End-to-End Flow
- ✅ New user signup → add payment → create bot → run 1 week → verify invoice
- ✅ Existing user upgrade to Premium → verify $100 charge + usage
- ✅ User hits $20 threshold → verify mid-cycle invoice

---

## OpenRouter Research Checklist

Before implementing LLM provider migration:

- [ ] **Model Availability**: Verify all current models available
  - [ ] GPT-4, GPT-5
  - [ ] Claude Haiku 4.5, Sonnet 4.5, Opus 4
  - [ ] DeepSeek R1
  - [ ] Grok 4

- [ ] **Token Tracking**: Test response format
  - [ ] Confirm `usage` object present in all responses
  - [ ] Verify `prompt_tokens`, `completion_tokens`, `total_tokens` accuracy
  - [ ] Check if `total_cost` field available

- [ ] **Pricing Transparency**:
  - [ ] Verify per-model pricing visible in OpenRouter docs
  - [ ] Compare OpenRouter rates vs direct API rates
  - [ ] Calculate OpenRouter markup vs our 70% markup

- [ ] **Performance**:
  - [ ] Latency test: Direct API vs OpenRouter proxy
  - [ ] Acceptable latency threshold: <500ms overhead

- [ ] **Reliability**:
  - [ ] Fallback routing: Does OpenRouter auto-retry failed models?
  - [ ] Rate limiting: How does OpenRouter handle rate limits?
  - [ ] Error handling: Are provider-specific errors passed through?

- [ ] **Cost Implications**:
  - [ ] Does OpenRouter charge extra fees beyond model costs?
  - [ ] Are there volume discounts available?

---

## Launch Checklist

### Pre-Launch
- [ ] Complete Phases 1-6 implementation
- [ ] Test all flows in Stripe test mode
- [ ] Create pricing page on ggbots.ai
- [ ] Draft user communication email
- [ ] Prepare support docs/FAQ
- [ ] Set up monitoring/alerting for billing errors

### Launch Day
- [ ] Switch Stripe to live mode
- [ ] Deploy backend with metered billing
- [ ] Deploy frontend with usage dashboard
- [ ] Send user communication email
- [ ] Monitor for billing issues
- [ ] Be available for user support

### Post-Launch (Week 1)
- [ ] Monitor token tracking accuracy
- [ ] Monitor Stripe usage reporting
- [ ] Monitor user signups and payment success rate
- [ ] Gather user feedback on pricing
- [ ] Adjust hard cap defaults if needed
- [ ] Monitor cost estimator accuracy

### Post-Launch (Month 1)
- [ ] Review first month's invoices
- [ ] Analyze user spending patterns
- [ ] Optimize cost estimator based on actual data
- [ ] Refine premium tier features based on feedback
- [ ] Consider OpenRouter migration if direct API issues

---

## Open Questions

1. **OpenRouter Migration Timeline**:
   - Implement immediately or after metered billing stabilizes?
   - Recommendation: After Phase 1-2, before full launch

2. **Premium Base Allowance Amount**:
   - $20, $30, or $50 included with $100/month?
   - Recommendation: $30 (30% of subscription price)

3. **Free Trial Period**:
   - Offer 7-day trial with $10 credit?
   - Or no trial, just low barrier to test?
   - Recommendation: No trial, emphasize "$2-5 to test fully"

4. **Model Pricing Updates**:
   - How often to sync model pricing table?
   - Manual updates or automated?
   - Recommendation: Manual updates quarterly, automated alerts for price changes

5. **Currency Support**:
   - USD only or support other currencies?
   - Recommendation: USD only initially, expand later

6. **Tax Handling**:
   - Enable Stripe Tax for automatic tax calculation?
   - Recommendation: Yes, enable Stripe Tax

---

## Success Metrics

### Financial
- **Revenue per user**: Target $30-50 average
- **Churn rate**: <10% monthly
- **Failed payment rate**: <5%
- **Hard cap hit rate**: <15% of users

### Technical
- **Token tracking accuracy**: >99%
- **Stripe reporting success rate**: >99.9%
- **Billing error rate**: <0.1%
- **Cost estimator variance**: <25% from actual

### User Experience
- **Signup completion rate**: >80%
- **Payment method addition rate**: >70%
- **Usage dashboard engagement**: >40% weekly active users
- **Hard cap adoption**: >30% of users set caps

---

## Timeline Estimate

**Total: 7-10 days** (assuming full-time work)

- Phase 1: Token Tracking - 2 days
- Phase 2: Stripe Metered Billing - 1 day
- Phase 3: Premium Subscription - 0.5 days
- Phase 4: Usage Estimator - 1.5 days
- Phase 5: Usage Dashboard - 1 day
- Phase 6: Alerts & Safeguards - 0.5 days
- OpenRouter Research - 0.5 days
- Testing & QA - 1.5 days
- Launch Prep - 0.5 days

**Recommended Approach**: Ship Phases 1-3 first (core billing), then iterate on Phases 4-6 (UX improvements)

---

## Next Steps

1. **Confirm strategy** with user (this document)
2. **Research OpenRouter** (model availability, token tracking, pricing)
3. **LLM pricing research** (get current rates for all models)
4. **Start Phase 1**: Token tracking infrastructure
5. **Iterate** based on testing and feedback
