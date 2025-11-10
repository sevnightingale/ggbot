# Metered Billing Implementation Plan (Simplified)

**Status**: Planning
**Created**: 2025-11-08
**Updated**: 2025-11-10 (Added Phase 0: OpenRouter Migration)
**Target**: 6-day implementation (1 day OpenRouter + 5 days billing)

---

## Executive Summary

Complete platform pricing overhaul from freemium to usage-based billing with minimal complexity:

- **Phase 0 Prerequisite**: Migrate to OpenRouter (unified LLM API gateway) BEFORE billing
- **Usage Tier**: Pay-as-you-go, charged monthly based on LLM token consumption with 70% markup
- **Premium Tier**: $100/month subscription unlocks agents (no base allowance - keeps it simple)
- **No Free Tier**: All users pay for consumption, low barrier to test ($2-5 for minimal usage)
- **Billing**: Post-paid monthly with $20 threshold for mid-cycle invoicing via Stripe Meter
- **Per-Bot Tracking**: Essential for user value - see which bots cost what
- **Estimator**: Build AFTER launch based on real measured costs (Phase 6)

---

## Pricing Model

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
- Platform tracks token consumption per-call with per-bot detail
- Daily job aggregates usage and reports to Stripe Meter
- Stripe invoices at **end of month** OR **$20 threshold**, whichever comes first
- Failed payment = bots pause until resolved

**Example Monthly Costs** (estimates):
- Minimal testing (DeepSeek, 1 bot, 1h frequency): $3-5/month
- Medium usage (GPT-4, 3 bots, 15m frequency): $20-30/month
- Heavy usage (GPT-5, 5 bots, 5m frequency): $60-100/month

### Premium Tier ($100/month)

**Core Feature**: Agent access (strategy builder + autonomous trading agents)

**Additional Premium Features** (TBD):
- Priority support
- Telegram signal publishing
- Advanced market intelligence (future premium data sources)
- Early access to new features

**Billing**:
- Fixed $100/month recurring charge (separate from metered usage)
- Usage charges continue to accrue on top
- Total monthly invoice: $100 (sub) + $47.23 (usage) = $147.23
- **No base allowance included** (simplifies accounting, cleaner pricing)

**NOT Premium** (Available to Usage Tier):
- Live trading (Symphony, AsterDEX)
- Signal validation mode
- Paper trading
- All market intelligence currently available

---

## Stripe Meter Research Results

### The Constraint

**Stripe Meter cannot apply variable pricing based on event metadata.**

You can send metadata (model name, token counts), but Stripe won't apply different rates per model. All usage in one meter gets charged at the same fixed rate.

### Our Approach: Pre-Computed Costs (Option B)

**We calculate the dollar amount ourselves, Stripe aggregates and invoices.**

```python
# Calculate cost for each LLM call
input_cost = (input_tokens / 1000) * model_input_rate
output_cost = (output_tokens / 1000) * model_output_rate
total_cost = (input_cost + output_cost) * 1.70  # 70% markup

# Send to Stripe Meter as dollar amount
stripe.billing.meter_event.create(
    event_name="llm_usage_cost",
    payload={
        "stripe_customer_id": customer_id,
        "value": total_cost  # Already in dollars
    }
)
```

**Stripe Setup**:
- One meter: "LLM API Usage Cost"
- One price: $1.00 per unit (where 1 unit = $1)
- Stripe sums all events: 0.0234 + 0.0156 + 0.0891 + ... = monthly total
- Invoice shows: "LLM API Usage: $47.23"

**Advantages**:
- ✅ Simple Stripe setup (one meter, one price)
- ✅ Clean invoice (one line item)
- ✅ Full control over pricing logic (no Stripe product updates when rates change)
- ✅ Per-bot tracking still in our database
- ✅ Users see detailed breakdown in our UI, simplified invoice from Stripe

**Rejected Alternative**: Multiple meters per model/token type
- Would need 10+ subscription line items per user
- Complex Stripe management
- Cluttered invoices
- Hard to maintain

---

## Why OpenRouter First (Phase 0)

**OpenRouter is a unified API gateway for 200+ LLM models.**

### Current Architecture Problem
We maintain separate integrations for each provider:
- `decision/llm_providers/openai_provider.py`
- `decision/llm_providers/anthropic_provider.py`
- `decision/llm_providers/deepseek_provider.py`
- `decision/llm_providers/xai_provider.py`

Each has different:
- API response formats
- Token usage reporting
- Error handling
- Rate limiting

### OpenRouter Solution
**Single API, standardized responses:**
```python
# One client for all models
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Use any model with same interface
response = openrouter_client.chat.completions.create(
    model="openai/gpt-4",  # or anthropic/claude-opus-4, x-ai/grok-4
    messages=[...]
)

# Always standardized usage format
tokens = {
    'prompt_tokens': response.usage.prompt_tokens,
    'completion_tokens': response.usage.completion_tokens,
    'total_tokens': response.usage.total_tokens
}
```

### Benefits for Metered Billing

1. **Simplified Token Tracking**
   - All models return identical `usage` format
   - No provider-specific parsing logic
   - Token tracking wrapper becomes trivial

2. **Pricing Validation**
   - OpenRouter shows per-model costs
   - Verify our 70% markup calculations
   - May include cost data in API response

3. **One API Key**
   - Platform-managed (not per-user)
   - Simpler credential management
   - Better rate limiting

4. **Cleaner Codebase**
   - One provider class instead of 4+
   - Less maintenance burden
   - Easier to add new models

5. **Makes Phase 1 Easier**
   - Token tracking code is simpler
   - No need to handle different response formats
   - Standardized model names

### Migration Strategy

**Approach**: Keep old providers as fallback during migration
- Don't delete existing provider code immediately
- Run OpenRouter in parallel first
- Validate responses identical
- Gradually deprecate old providers

---

## Technical Architecture

### Phase 0: OpenRouter Migration (1 day)

**Goal**: Replace 4 separate LLM provider integrations with unified OpenRouter API

#### 0.1 Research & Validation

**Tasks**:
- [ ] Sign up for OpenRouter account
- [ ] Verify model availability:
  - [ ] `openai/gpt-4`
  - [ ] `openai/gpt-5` (or latest GPT model)
  - [ ] `anthropic/claude-opus-4`
  - [ ] `anthropic/claude-sonnet-4.5`
  - [ ] `anthropic/claude-haiku-4.5`
  - [ ] `deepseek/deepseek-chat`
  - [ ] `x-ai/grok-4` (or `x-ai/grok-beta`)

- [ ] Check pricing transparency:
  - [ ] Compare OpenRouter rates vs direct API rates
  - [ ] Calculate OpenRouter markup (if any)
  - [ ] Determine if we need to adjust our 70% markup

- [ ] Test API:
  - [ ] Create test script with 5 models
  - [ ] Verify `usage` object format (OpenAI-compatible)
  - [ ] Measure latency (acceptable if <500ms overhead)
  - [ ] Test error handling

**Deliverable**: Confirmation that all models available and token tracking works

#### 0.2 Implementation

**File**: `decision/llm_providers/openrouter_provider.py`

```python
"""OpenRouter unified LLM provider."""

import os
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from core.common.logger import logger


class OpenRouterProvider:
    """Unified provider for all LLM models via OpenRouter."""

    # Model name mapping (internal → OpenRouter format)
    MODEL_MAP = {
        'gpt-4': 'openai/gpt-4',
        'gpt-5': 'openai/gpt-5',  # Adjust based on OpenRouter's naming
        'claude-opus-4': 'anthropic/claude-opus-4',
        'claude-sonnet-4.5': 'anthropic/claude-sonnet-4.5',
        'claude-haiku-4.5': 'anthropic/claude-haiku-4.5',
        'deepseek-chat': 'deepseek/deepseek-chat',
        'grok-4': 'x-ai/grok-4',
    }

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self._log = logger.bind(component="openrouter_provider")

    async def generate(
        self,
        model: str,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion using OpenRouter.

        Args:
            model: Internal model name (e.g., 'gpt-4', 'claude-opus-4')
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature
            max_tokens: Maximum completion tokens
            **kwargs: Additional parameters

        Returns:
            {
                "content": "...",
                "model": "openai/gpt-4",  # OpenRouter model name
                "provider": "openrouter",
                "usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 75,
                    "total_tokens": 225
                }
            }
        """
        try:
            # Map internal model name to OpenRouter format
            openrouter_model = self.MODEL_MAP.get(model, model)

            # Make API call
            response = await self.client.chat.completions.create(
                model=openrouter_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            self._log.info(
                f"OpenRouter API call: model={openrouter_model}, "
                f"tokens={response.usage.total_tokens}"
            )

            return {
                "content": response.choices[0].message.content,
                "model": openrouter_model,
                "provider": "openrouter",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            self._log.error(f"OpenRouter API error: {e}")
            raise


# Singleton instance
openrouter_provider = OpenRouterProvider()
```

#### 0.3 Migration

**Files to Update**:

1. **decision/engine_v2.py**:
```python
# Before
from decision.llm_providers.factory import get_llm_provider
llm_provider = get_llm_provider(config.llm_provider)

# After
from decision.llm_providers.openrouter_provider import openrouter_provider
llm_provider = openrouter_provider
```

2. **agent/run_agent.py**:
```python
# Agent uses Claude SDK, but for any custom LLM calls:
from decision.llm_providers.openrouter_provider import openrouter_provider
```

3. **core/services/llm_service.py**:
```python
# Update to use OpenRouter instead of per-provider clients
# Keep old logic as fallback for now
```

**Tasks**:
- [ ] Update `decision/engine_v2.py` to use OpenRouter
- [ ] Update `agent/run_agent.py` if it has custom LLM calls
- [ ] Update `signals/listener_service.py` if it uses LLMs
- [ ] Add `OPENROUTER_API_KEY` to `.env`
- [ ] Keep old provider code (don't delete, just unused)

#### 0.4 Testing

**Test Script**: `scripts/test_openrouter.py`

```python
"""Test OpenRouter integration across all models."""

import asyncio
from decision.llm_providers.openrouter_provider import openrouter_provider

MODELS = [
    'gpt-4',
    'gpt-5',
    'claude-opus-4',
    'claude-sonnet-4.5',
    'deepseek-chat',
    'grok-4'
]

async def test_model(model: str):
    """Test one model."""
    messages = [
        {"role": "user", "content": "Say hello in exactly 5 words."}
    ]

    try:
        response = await openrouter_provider.generate(
            model=model,
            messages=messages,
            max_tokens=50
        )

        print(f"\n✅ {model}")
        print(f"   Content: {response['content'][:50]}...")
        print(f"   Tokens: {response['usage']['total_tokens']}")
        print(f"   Provider: {response['provider']}")

        return True

    except Exception as e:
        print(f"\n❌ {model}: {e}")
        return False

async def main():
    """Test all models."""
    print("Testing OpenRouter integration...\n")

    results = []
    for model in MODELS:
        success = await test_model(model)
        results.append((model, success))
        await asyncio.sleep(1)  # Rate limiting

    print("\n" + "="*50)
    print("RESULTS:")
    for model, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {model}")

    success_rate = sum(1 for _, s in results if s) / len(results)
    print(f"\nSuccess rate: {success_rate*100:.0f}%")

if __name__ == "__main__":
    asyncio.run(main())
```

**Run**:
```bash
cd /home/sev/ggbot
source .venv/bin/activate
python scripts/test_openrouter.py
```

**Validation**:
- [ ] All models return responses
- [ ] Token counts present in all responses
- [ ] No errors or timeouts
- [ ] Latency acceptable (<2s per call)

#### 0.5 Production Testing

**Tasks**:
- [ ] Run 3 real bot executions (decision engine)
- [ ] Verify decisions identical to old provider
- [ ] Check logs for any errors
- [ ] Measure latency impact

**If successful**:
- [ ] Update all configs to use OpenRouter by default
- [ ] Monitor for 24 hours
- [ ] Mark old providers as deprecated (but keep code)

**If issues**:
- [ ] Rollback to old providers
- [ ] Debug OpenRouter integration
- [ ] Re-test before proceeding to Phase 1

---

### Database Schema

**Token Usage Table** (per-call tracking with per-bot detail):
```sql
CREATE TABLE token_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    config_id UUID REFERENCES configurations(config_id),  -- Per-bot tracking

    -- LLM metadata
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'deepseek', 'xai'
    model VARCHAR(100) NOT NULL,    -- 'gpt-4', 'claude-opus-4', 'deepseek-chat', 'grok-4'

    -- Token consumption
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,

    -- Cost calculation (pre-computed with 70% markup)
    provider_cost_usd NUMERIC(10, 6) NOT NULL,  -- Raw provider cost
    platform_cost_usd NUMERIC(10, 6) NOT NULL,  -- With 70% markup
    markup_percentage NUMERIC(5, 2) DEFAULT 70.00,

    -- Context
    execution_type VARCHAR(50),  -- 'extraction', 'decision', 'agent_chat', 'signal_validation'
    decision_id UUID REFERENCES decisions(decision_id),

    -- Billing
    stripe_reported BOOLEAN DEFAULT FALSE,
    stripe_reported_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_token_usage_user_month ON token_usage(user_id, DATE_TRUNC('month', created_at));
CREATE INDEX idx_token_usage_config_date ON token_usage(config_id, created_at);
CREATE INDEX idx_token_usage_stripe_pending ON token_usage(user_id, stripe_reported, DATE(created_at))
    WHERE stripe_reported = FALSE;
CREATE INDEX idx_token_usage_billing_period ON token_usage(DATE(created_at), stripe_reported);
```

**Model Pricing Table** (our source of truth for cost calculations):
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

-- Current pricing (to be researched and populated)
INSERT INTO llm_model_pricing (provider, model, input_cost_per_1k, output_cost_per_1k, effective_date, source_url)
VALUES
    ('openai', 'gpt-4', 0.030, 0.060, '2025-01-01', 'https://openai.com/pricing'),
    ('openai', 'gpt-5', 0.050, 0.100, '2025-01-01', 'https://openai.com/pricing'),
    ('anthropic', 'claude-opus-4', 0.015, 0.075, '2025-01-01', 'https://anthropic.com/pricing'),
    ('anthropic', 'claude-sonnet-4.5', 0.003, 0.015, '2025-01-01', 'https://anthropic.com/pricing'),
    ('anthropic', 'claude-haiku-4.5', 0.001, 0.005, '2025-01-01', 'https://anthropic.com/pricing'),
    ('deepseek', 'deepseek-chat', 0.0005, 0.002, '2025-01-01', 'https://deepseek.com/pricing'),
    ('xai', 'grok-4', 0.005, 0.015, '2025-01-01', 'https://x.ai/pricing');
```

**User Profiles Updates** (for Premium tier):
```sql
ALTER TABLE user_profiles
    ADD COLUMN premium_subscription_id VARCHAR(100),
    ADD COLUMN premium_tier_active BOOLEAN DEFAULT FALSE;
```

---

### Phase 1: Token Tracking Infrastructure (2 days)

**Goal**: Track every LLM call with per-bot detail and pre-calculated costs

#### 1.1 Database Setup

**Tasks**:
- [ ] Create `token_usage` table with indexes
- [ ] Create `llm_model_pricing` table
- [ ] Run migration

**Migration Script** (`database/migrations/metered_billing_schema.sql`):
```sql
-- Create token_usage table
CREATE TABLE token_usage (
    -- [Full schema from above]
);

-- Create indexes
CREATE INDEX idx_token_usage_user_month ...;
CREATE INDEX idx_token_usage_config_date ...;
-- [All indexes from above]

-- Create llm_model_pricing table
CREATE TABLE llm_model_pricing (
    -- [Full schema from above]
);

-- Seed initial pricing data
INSERT INTO llm_model_pricing ...;
```

#### 1.2 Token Tracking Service

**File**: `core/services/token_tracking_service.py`

```python
"""Token tracking service for metered billing."""

from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from core.common.db import get_db_connection
from core.common.logger import logger


class TokenTrackingService:
    """Service for tracking LLM token usage and calculating costs."""

    def __init__(self):
        self._log = logger.bind(component="token_tracking")

    async def record_usage(
        self,
        user_id: str,
        config_id: Optional[str],
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        execution_type: str,
        decision_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record token usage and calculate costs with 70% markup.

        Args:
            user_id: User ID
            config_id: Bot configuration ID (if applicable)
            provider: LLM provider ('openai', 'anthropic', 'deepseek', 'xai')
            model: Model name ('gpt-4', 'claude-opus-4', etc.)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            execution_type: Context ('decision', 'agent_chat', 'extraction', etc.)
            decision_id: Optional decision ID for traceability

        Returns:
            {
                "usage_id": "...",
                "provider_cost_usd": 0.00234,
                "platform_cost_usd": 0.00398,  # With 70% markup
                "markup_applied": 70.0
            }
        """
        try:
            # Get current pricing for model
            pricing = await self._get_model_pricing(provider, model)

            # Calculate raw provider cost
            input_cost = (Decimal(input_tokens) / 1000) * pricing['input_cost_per_1k']
            output_cost = (Decimal(output_tokens) / 1000) * pricing['output_cost_per_1k']
            provider_cost = input_cost + output_cost

            # Apply 70% markup
            platform_cost = provider_cost * Decimal('1.70')

            # Store in database
            usage_id = await self._insert_usage_record(
                user_id=user_id,
                config_id=config_id,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                provider_cost=provider_cost,
                platform_cost=platform_cost,
                execution_type=execution_type,
                decision_id=decision_id
            )

            self._log.info(
                f"Tracked usage: user={user_id}, model={model}, "
                f"tokens={input_tokens + output_tokens}, cost=${platform_cost:.4f}"
            )

            return {
                "usage_id": usage_id,
                "provider_cost_usd": float(provider_cost),
                "platform_cost_usd": float(platform_cost),
                "markup_applied": 70.0
            }

        except Exception as e:
            self._log.error(f"Failed to record usage: {e}")
            # Don't fail the LLM call if tracking fails
            return {"error": str(e)}

    async def _get_model_pricing(self, provider: str, model: str) -> Dict[str, Decimal]:
        """Get current pricing for a model."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT input_cost_per_1k, output_cost_per_1k
                    FROM llm_model_pricing
                    WHERE provider = %s
                      AND model = %s
                      AND is_active = TRUE
                    ORDER BY effective_date DESC
                    LIMIT 1
                """, (provider, model))

                result = cur.fetchone()
                if not result:
                    raise ValueError(f"No pricing found for {provider}/{model}")

                return {
                    'input_cost_per_1k': Decimal(str(result[0])),
                    'output_cost_per_1k': Decimal(str(result[1]))
                }

    async def _insert_usage_record(self, **kwargs) -> str:
        """Insert usage record into database."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO token_usage (
                        user_id, config_id, provider, model,
                        input_tokens, output_tokens, total_tokens,
                        provider_cost_usd, platform_cost_usd,
                        execution_type, decision_id
                    ) VALUES (
                        %(user_id)s, %(config_id)s, %(provider)s, %(model)s,
                        %(input_tokens)s, %(output_tokens)s, %(total_tokens)s,
                        %(provider_cost)s, %(platform_cost)s,
                        %(execution_type)s, %(decision_id)s
                    )
                    RETURNING usage_id
                """, kwargs)

                usage_id = cur.fetchone()[0]
                conn.commit()
                return str(usage_id)

    async def get_current_month_spend(self, user_id: str) -> Decimal:
        """Get total spend for current billing period."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(platform_cost_usd), 0)
                    FROM token_usage
                    WHERE user_id = %s
                      AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_TIMESTAMP)
                """, (user_id,))
                return Decimal(str(cur.fetchone()[0]))

    async def get_per_bot_spend(self, user_id: str) -> list[Dict[str, Any]]:
        """Get current month spend breakdown by bot."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        c.config_id,
                        c.config_name,
                        COUNT(*) as executions,
                        SUM(tu.platform_cost_usd) as total_cost,
                        tu.model,
                        tu.provider
                    FROM token_usage tu
                    JOIN configurations c ON tu.config_id = c.config_id
                    WHERE tu.user_id = %s
                      AND DATE_TRUNC('month', tu.created_at) = DATE_TRUNC('month', CURRENT_TIMESTAMP)
                    GROUP BY c.config_id, c.config_name, tu.model, tu.provider
                    ORDER BY total_cost DESC
                """, (user_id,))

                results = cur.fetchall()
                return [{
                    'config_id': row[0],
                    'config_name': row[1],
                    'executions': row[2],
                    'total_cost': float(row[3]),
                    'model': row[4],
                    'provider': row[5]
                } for row in results]


# Singleton instance
token_tracking_service = TokenTrackingService()
```

#### 1.3 LLM Call Wrapper

**Integration Points** (wrap every LLM call):

```python
# decision/engine_v2.py
from core.services.token_tracking_service import token_tracking_service

async def generate_decision(...):
    # Make LLM call
    response = await llm_provider.generate(prompt)

    # Track usage
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

    return response
```

**Files to Update**:
- `decision/engine_v2.py` - Decision generation
- `agent/run_agent.py` - Agent conversations
- `signals/listener_service.py` - Signal validation
- Any extraction that uses LLMs (currently none, but future-proof)

#### 1.4 LLM Pricing Research

**Task**: Research current token rates for all models

**Models to Research**:
1. OpenAI GPT-4 (input/output rates)
2. OpenAI GPT-5 (input/output rates)
3. Anthropic Claude Opus 4 (input/output rates)
4. Anthropic Claude Sonnet 4.5 (input/output rates)
5. Anthropic Claude Haiku 4.5 (input/output rates)
6. DeepSeek R1 / deepseek-chat (input/output rates)
7. XAI Grok 4 (input/output rates)

**Deliverable**: Populated `llm_model_pricing` table with current rates and source URLs

---

### Phase 2: Stripe Metered Billing Setup (1 day)

**Goal**: Configure Stripe Meter and implement daily usage reporting

#### 2.1 Stripe Product Configuration

**Manual Steps in Stripe Dashboard**:

1. **Create Meter**:
   - Name: "LLM API Usage Cost"
   - Event name: `llm_usage_cost`
   - Aggregation: Sum
   - Value settings: Decimal (for dollar amounts)

2. **Create Price**:
   - Product: "ggbots Usage-Based Billing"
   - Pricing model: Usage-based
   - Meter: "LLM API Usage Cost"
   - Unit price: $1.00 per unit (where 1 unit = $1)
   - Billing period: Monthly

3. **Configure Billing Threshold**:
   - Set threshold: $20 USD
   - When usage charges reach $20, automatically invoice

4. **Save Price ID**:
   - Add to `.env`: `STRIPE_METERED_PRICE_ID=price_xxxxx`

#### 2.2 Subscription Creation (on Signup)

**File**: `ggbot.py` (add new endpoint)

```python
@app.post("/api/v2/create-metered-subscription")
async def create_metered_subscription(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Create Stripe subscription with metered usage.
    Called after user adds payment method during signup.
    """
    from core.common.db import get_db_connection

    try:
        # Get or create Stripe customer
        customer = await get_or_create_stripe_customer(
            current_user.user_id,
            current_user.email
        )

        # Create subscription with metered line item
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{
                'price': os.getenv('STRIPE_METERED_PRICE_ID'),
            }],
            billing_thresholds={
                'amount_gte': 2000  # $20 threshold (in cents)
            },
            metadata={
                'user_id': str(current_user.user_id),
                'subscription_type': 'usage_based'
            }
        )

        # Store in database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET stripe_customer_id = %s,
                        stripe_subscription_id = %s,
                        subscription_tier = 'usage_based',
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (customer.id, subscription.id, str(current_user.user_id)))
                conn.commit()

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created metered subscription: {subscription.id}"
        )

        return {
            'subscription_id': subscription.id,
            'status': subscription.status
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating subscription: {e}")
        raise HTTPException(500, f"Payment system error: {str(e)}")
```

#### 2.3 Daily Usage Reporting Job

**File**: `scripts/report_stripe_usage.py`

```python
"""
Daily job to report token usage to Stripe Meter.
Run via cron: 0 1 * * * (1am daily)
"""

import os
import asyncio
from datetime import datetime, timedelta
import stripe
from core.common.db import get_db_connection
from core.common.logger import logger

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


async def report_daily_usage():
    """Aggregate yesterday's usage and report to Stripe."""

    yesterday = (datetime.now() - timedelta(days=1)).date()
    logger.info(f"Reporting usage for {yesterday}")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get per-user totals for yesterday (unreported only)
            cur.execute("""
                SELECT
                    user_id,
                    SUM(platform_cost_usd) as total_cost,
                    COUNT(*) as event_count,
                    ARRAY_AGG(usage_id) as usage_ids
                FROM token_usage
                WHERE DATE(created_at) = %s
                  AND stripe_reported = FALSE
                GROUP BY user_id
            """, (yesterday,))

            results = cur.fetchall()
            logger.info(f"Found {len(results)} users with unreported usage")

            for user_id, total_cost, event_count, usage_ids in results:
                try:
                    # Get Stripe customer ID
                    cur.execute("""
                        SELECT stripe_customer_id
                        FROM user_profiles
                        WHERE user_id = %s
                    """, (user_id,))

                    customer_result = cur.fetchone()
                    if not customer_result or not customer_result[0]:
                        logger.warning(f"No Stripe customer for user {user_id}")
                        continue

                    stripe_customer_id = customer_result[0]

                    # Send to Stripe Meter
                    stripe.billing.meter_event.create(
                        event_name="llm_usage_cost",
                        payload={
                            "stripe_customer_id": stripe_customer_id,
                            "value": str(total_cost),  # Dollar amount as string
                        },
                        timestamp=int(datetime.now().timestamp())
                    )

                    # Mark as reported
                    cur.execute("""
                        UPDATE token_usage
                        SET stripe_reported = TRUE,
                            stripe_reported_at = NOW()
                        WHERE usage_id = ANY(%s)
                    """, (usage_ids,))

                    conn.commit()

                    logger.info(
                        f"Reported ${total_cost:.2f} for user {user_id} "
                        f"({event_count} LLM calls)"
                    )

                except stripe.error.StripeError as e:
                    logger.error(f"Stripe error for user {user_id}: {e}")
                    conn.rollback()
                except Exception as e:
                    logger.error(f"Error reporting usage for user {user_id}: {e}")
                    conn.rollback()


if __name__ == "__main__":
    asyncio.run(report_daily_usage())
```

**Cron Setup**:
```bash
# Add to crontab
0 1 * * * cd /home/sev/ggbot && source .venv/bin/activate && python scripts/report_stripe_usage.py
```

#### 2.4 Webhook Updates

**Update existing webhook handler** (`ggbot.py`):

```python
@app.post("/api/v2/stripe-webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""

    # Existing code for signature verification...

    event_type = event['type']

    # Existing handlers...

    # NEW: Handle usage invoice payment failures
    if event_type == 'invoice.payment_failed':
        await handle_usage_payment_failed(event['data']['object'])

    return {'received': True}


async def handle_usage_payment_failed(invoice):
    """Pause all bots when usage payment fails."""
    from core.common.db import get_db_connection

    # Get user from customer ID
    customer_id = invoice['customer']

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id FROM user_profiles
                WHERE stripe_customer_id = %s
            """, (customer_id,))

            result = cur.fetchone()
            if not result:
                logger.warning(f"No user found for customer {customer_id}")
                return

            user_id = result[0]

            # Mark as payment failed
            cur.execute("""
                UPDATE user_profiles
                SET subscription_status = 'past_due',
                    updated_at = NOW()
                WHERE user_id = %s
            """, (user_id,))
            conn.commit()

    # Stop all active bots
    configs = await config_service.get_user_configs(user_id)
    for config in configs:
        if config['state'] == 'active':
            await stop_bot(config['config_id'], user_id)

    logger.bind(user_id=user_id).warning(
        f"Payment failed - paused all bots. Amount due: ${invoice['amount_due'] / 100}"
    )

    # TODO: Send email notification
```

---

### Phase 3: Premium Subscription ($100/month) (0.5 days)

**Goal**: Add fixed $100/month subscription for agent access

#### 3.1 Database Schema

```sql
ALTER TABLE user_profiles
    ADD COLUMN premium_subscription_id VARCHAR(100),
    ADD COLUMN premium_tier_active BOOLEAN DEFAULT FALSE;
```

#### 3.2 Stripe Product

**Manual Steps in Stripe Dashboard**:

1. **Create Product**:
   - Name: "ggbots Pro - Agent Access"
   - Description: "Unlock autonomous trading agents"

2. **Create Price**:
   - Product: "ggbots Pro - Agent Access"
   - Pricing model: Recurring
   - Price: $100.00 USD
   - Billing period: Monthly

3. **Save Price ID**:
   - Add to `.env`: `STRIPE_PREMIUM_PRICE_ID=price_xxxxx`

#### 3.3 Upgrade Endpoint

**File**: `ggbot.py`

```python
@app.post("/api/v2/upgrade-to-premium")
async def upgrade_to_premium(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Add premium tier to existing usage-based subscription."""
    from core.common.db import get_db_connection

    # Get existing subscription
    profile = await user_service.get_profile(current_user.user_id)

    if not profile.stripe_subscription_id:
        raise HTTPException(400, "No active subscription found")

    try:
        # Add premium line item to existing subscription
        subscription = stripe.Subscription.modify(
            profile.stripe_subscription_id,
            items=[
                # Keep existing metered item (get from subscription.items)
                # Add premium fixed item
                {'price': os.getenv('STRIPE_PREMIUM_PRICE_ID')}
            ],
            proration_behavior='always_invoice'  # Charge immediately for upgrade
        )

        # Update database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET premium_tier_active = TRUE,
                        premium_subscription_id = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (subscription.id, str(current_user.user_id)))
                conn.commit()

        logger.bind(user_id=str(current_user.user_id)).info(
            "Upgraded to Premium tier"
        )

        return {
            'premium_active': True,
            'subscription_id': subscription.id
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error upgrading to premium: {e}")
        raise HTTPException(500, f"Upgrade failed: {str(e)}")
```

#### 3.4 Permission Updates

**File**: `core/domain/user_profile.py`

```python
@property
def can_use_agents(self) -> bool:
    """Check if user can create and use agents."""
    return self.premium_tier_active


@property
def can_use_premium_features(self) -> bool:
    """Check if user can access premium features."""
    return self.premium_tier_active and self.has_active_subscription
```

**File**: `ggbot.py` (update /me endpoint)

```python
@app.get("/api/v2/me")
async def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Get current user's profile with subscription info."""
    profile = await current_user.load_profile()

    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "subscription_tier": profile.subscription_tier.value,
        "subscription_status": profile.subscription_status.value,
        "can_use_premium_features": profile.can_use_premium_features,
        "can_use_agents": profile.can_use_agents,  # NEW
        "can_use_live_trading": profile.can_use_live_trading,
        # ... existing fields
    }
```

---

### Phase 4: Minimal UI (0.5 days)

**Goal**: Show current spend + per-bot breakdown

#### 4.1 Backend API

**File**: `ggbot.py`

```python
@app.get("/api/v2/usage/current-month")
async def get_current_month_usage(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Get current month's usage with per-bot breakdown."""
    from core.services.token_tracking_service import token_tracking_service

    # Get total spend
    total_spend = await token_tracking_service.get_current_month_spend(
        current_user.user_id
    )

    # Get per-bot breakdown
    per_bot = await token_tracking_service.get_per_bot_spend(
        current_user.user_id
    )

    # Calculate estimated month-end
    current_day = datetime.now().day
    days_in_month = calendar.monthrange(
        datetime.now().year,
        datetime.now().month
    )[1]
    estimated_month_end = float(total_spend) * (days_in_month / current_day) if current_day > 0 else 0

    return {
        "total_spend": float(total_spend),
        "days_elapsed": current_day,
        "estimated_month_end": estimated_month_end,
        "per_bot_breakdown": per_bot
    }
```

#### 4.2 Frontend Component

**File**: `frontend/app/forge/components/UsageDisplay.tsx`

```typescript
'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api'

interface BotUsage {
  config_id: string
  config_name: string
  executions: number
  total_cost: number
  model: string
  provider: string
}

interface CurrentMonthUsage {
  total_spend: number
  days_elapsed: number
  estimated_month_end: number
  per_bot_breakdown: BotUsage[]
}

export function UsageDisplay() {
  const [usage, setUsage] = useState<CurrentMonthUsage | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadUsage()
    // Refresh every 30 seconds
    const interval = setInterval(loadUsage, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadUsage = async () => {
    try {
      const data = await apiClient.getCurrentMonthUsage()
      setUsage(data)
    } catch (err) {
      console.error('Failed to load usage:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !usage) {
    return <div>Loading usage...</div>
  }

  return (
    <div className="space-y-4">
      {/* Current Month Total */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <h3 className="text-sm text-[var(--text-secondary)] mb-2">
          Current Month
        </h3>
        <div className="text-4xl font-bold text-[var(--text-primary)]">
          ${usage.total_spend.toFixed(2)}
        </div>
        <p className="text-sm text-[var(--text-muted)] mt-2">
          {usage.days_elapsed} days elapsed • Est. month-end: ${usage.estimated_month_end.toFixed(2)}
        </p>
      </div>

      {/* Per-Bot Breakdown */}
      {usage.per_bot_breakdown.length > 0 && (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
          <h3 className="text-sm text-[var(--text-secondary)] mb-4">
            Spend by Bot
          </h3>
          <div className="space-y-3">
            {usage.per_bot_breakdown.map(bot => (
              <div
                key={bot.config_id}
                className="flex items-center justify-between p-3 rounded-lg bg-[var(--bg-tertiary)]"
              >
                <div className="flex-1">
                  <div className="font-medium text-[var(--text-primary)]">
                    {bot.config_name}
                  </div>
                  <div className="text-xs text-[var(--text-muted)]">
                    {bot.model} • {bot.executions} runs
                  </div>
                </div>
                <div className="text-lg font-semibold text-[var(--text-primary)]">
                  ${bot.total_cost.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Link to Stripe Billing Portal */}
      <button
        onClick={async () => {
          const { portal_url } = await apiClient.createPortalSession()
          window.location.href = portal_url
        }}
        className="w-full p-3 rounded-lg border border-[var(--border)] hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
      >
        View Invoices & Payment Details →
      </button>
    </div>
  )
}
```

**Integration**: Add to Settings modal or create dedicated "Usage" tab

---

### Phase 5: Estimator Based on Real Data (1 day)

**Goal**: Build cost estimator AFTER launch using actual measured costs

#### 5.1 Collect Real Data

**Process**:
1. Launch metered billing (Phases 1-4 complete)
2. Run test bots for 24-48 hours with various configs:
   - GPT-5, 5m frequency, medium market data
   - GPT-5, 15m frequency, medium market data
   - GPT-4, 15m frequency, medium market data
   - Claude Opus 4, 15m frequency, medium market data
   - DeepSeek, 1h frequency, light market data
   - etc.

3. Query actual costs from database:
   ```sql
   SELECT
       model,
       config_data->>'decision'->>'analysis_frequency' as frequency,
       AVG(platform_cost_usd) as avg_cost_per_execution,
       COUNT(*) as sample_size
   FROM token_usage tu
   JOIN configurations c ON tu.config_id = c.config_id
   WHERE tu.created_at > NOW() - INTERVAL '48 hours'
   GROUP BY model, frequency
   ORDER BY model, frequency;
   ```

4. Build lookup table from results

#### 5.2 Estimator Service

**File**: `core/services/usage_estimator.py`

```python
"""Cost estimator based on real measured data."""

from typing import Dict, Any

# Populated from real bot runs (to be filled after testing)
DAILY_COST_LOOKUP = {
    ('gpt-5', '5m'): 3.20,    # $3.20 per day (actual measured)
    ('gpt-5', '15m'): 1.07,   # $1.07 per day
    ('gpt-4', '15m'): 0.64,   # $0.64 per day
    ('claude-opus-4', '15m'): 0.32,
    ('deepseek-chat', '1h'): 0.12,
    # ... add more as we collect data
}


class UsageEstimator:
    """Estimate costs based on real measured bot performance."""

    def estimate_daily_cost(
        self,
        model: str,
        frequency: str
    ) -> Dict[str, float]:
        """
        Estimate daily cost for a bot configuration.

        Returns:
            {
                "daily_cost": 2.50,
                "monthly_cost": 75.00,
                "based_on_data": True  # or False if interpolated
            }
        """
        # Direct lookup
        key = (model, frequency)
        if key in DAILY_COST_LOOKUP:
            daily_cost = DAILY_COST_LOOKUP[key]
            return {
                "daily_cost": daily_cost,
                "monthly_cost": daily_cost * 30,
                "based_on_data": True
            }

        # Interpolation logic for missing configs
        # (can be sophisticated or simple)
        estimated = self._interpolate_cost(model, frequency)

        return {
            "daily_cost": estimated,
            "monthly_cost": estimated * 30,
            "based_on_data": False
        }

    def _interpolate_cost(self, model: str, frequency: str) -> float:
        """Interpolate cost for configs we haven't tested."""
        # Simple heuristic: find similar model/frequency and adjust
        # This can be refined with more data
        return 1.50  # Placeholder


estimator_service = UsageEstimator()
```

#### 5.3 API Endpoint

```python
@app.post("/api/v2/estimate-cost")
async def estimate_cost(
    model: str,
    frequency: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Estimate daily/monthly cost for bot config."""
    from core.services.usage_estimator import estimator_service

    estimate = estimator_service.estimate_daily_cost(model, frequency)

    return estimate
```

#### 5.4 Frontend Integration

```typescript
// Real-time estimate in bot config UI
const [estimate, setEstimate] = useState<{daily: number, monthly: number} | null>(null)

useEffect(() => {
  const timer = setTimeout(async () => {
    if (currentModel && currentFrequency) {
      const est = await apiClient.estimateCost(currentModel, currentFrequency)
      setEstimate(est)
    }
  }, 500)  // Debounce

  return () => clearTimeout(timer)
}, [currentModel, currentFrequency])

// Display
{estimate && (
  <div className="text-sm text-[var(--text-secondary)]">
    Est. ${estimate.daily.toFixed(2)}/day (${estimate.monthly.toFixed(0)}/month)
  </div>
)}
```

---

## Timeline

**Total: 6 days** (assumes full-time focus)

- **Day 1**: Phase 0 (OpenRouter migration + testing)
- **Day 2-3**: Phase 1 (Token tracking + LLM pricing research)
- **Day 4**: Phase 2 (Stripe Meter setup + daily reporting)
- **Day 4.5**: Phase 3 (Premium subscription)
- **Day 5**: Phase 4 (Minimal UI)
- **Day 6**: Testing & deployment

**Phase 5 (Estimator)**: +1 day after 24-48 hours of live data collection

---

## Testing Strategy

### Phase 1: Token Tracking
- [ ] Run 50 test bot executions across all models
- [ ] Verify token counts match LLM API responses
- [ ] Verify cost calculations (check markup applied correctly)
- [ ] Verify database storage (all fields populated)

### Phase 2: Stripe Integration
- [ ] Test subscription creation (Stripe test mode)
- [ ] Manually trigger daily reporting job with test data
- [ ] Verify Stripe Meter events received
- [ ] Test billing threshold (send enough events to hit $20)
- [ ] Verify webhook handling (payment success/failure)

### Phase 3: Premium Tier
- [ ] Test upgrade flow (add fixed $100 item to subscription)
- [ ] Verify agent creation blocked without premium
- [ ] Verify agent creation allowed with premium

### Phase 4: UI
- [ ] Verify total spend calculation
- [ ] Verify per-bot breakdown
- [ ] Test Stripe billing portal link

### End-to-End
- [ ] New user: signup → add card → create bot → run for 1 day → verify invoice preview
- [ ] Existing user: upgrade to Premium → verify $100 charge
- [ ] Payment failure: decline card → verify bots paused

---

## Launch Checklist

### Pre-Launch
- [ ] Complete Phases 1-4 implementation
- [ ] Test all flows in Stripe test mode
- [ ] Verify no breaking changes to existing users
- [ ] Draft user communication email (pricing changes)
- [ ] Prepare FAQ/support docs
- [ ] Set up monitoring for billing errors

### Launch Day
- [ ] Switch Stripe to live mode (update API keys)
- [ ] Deploy backend with token tracking
- [ ] Deploy frontend with usage display
- [ ] Send user communication email
- [ ] Monitor logs for billing issues
- [ ] Be available for user support

### Post-Launch (Week 1)
- [ ] Monitor token tracking accuracy
- [ ] Monitor Stripe Meter event delivery
- [ ] Monitor user signups and payment success rate
- [ ] Gather user feedback on pricing
- [ ] Start collecting data for estimator (Phase 5)

### Post-Launch (Week 2-3)
- [ ] Run test bots for estimator data collection
- [ ] Build and deploy estimator (Phase 5)
- [ ] Refine estimates based on user feedback

---

## Open Questions

1. **OpenRouter Migration**: Implement immediately or after billing stabilizes?
   - Recommendation: After Phase 2, before Phase 5

2. **Currency Support**: USD only or support other currencies?
   - Recommendation: USD only initially

3. **Tax Handling**: Enable Stripe Tax?
   - Recommendation: Yes, enable Stripe Tax for automatic calculation

4. **Premium Features Beyond Agents**: What else should be premium-only?
   - Current: Just agents
   - TBD: Priority support, advanced data sources, etc.

5. **Existing Users**: Migration strategy for 258 users, 3 Pro subscribers?
   - User will handle manually (no automated migration)

---

## Success Metrics

### Financial
- **Revenue per user**: Target $30-50 average
- **Payment success rate**: >95%
- **Churn rate**: <10% monthly

### Technical
- **Token tracking accuracy**: >99%
- **Stripe event delivery**: >99.9%
- **Billing error rate**: <0.1%

### User Experience
- **Signup completion rate**: >80%
- **Payment method addition rate**: >70%
- **Usage dashboard engagement**: >40% weekly active users

---

## What We Cut (And Can Add Later)

**Not building initially** (add only if users request):
- ❌ Email usage alerts ($10, $20, $50 thresholds)
- ❌ Hard spending caps with auto-pause
- ❌ Detailed usage charts (pie, bar, line graphs)
- ❌ Base allowance with premium ($100 flat is simpler)
- ❌ Historical usage analytics beyond current month
- ❌ Per-execution cost breakdown

**Rationale**: Ship minimal billing, iterate based on real user feedback

---

## Next Steps

1. **Confirm plan** with user
2. **Research LLM pricing** for all models (populate pricing table)
3. **Start Phase 1**: Token tracking implementation
4. **Iterate** based on testing and user feedback
