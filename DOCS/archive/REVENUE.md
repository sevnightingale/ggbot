# REVENUE.md - ggbots.ai Monetization Strategy

**Last Updated**: 2025-09-30
**Status**: Implementation Phase - Stripe Integration
**Payment Provider**: Stripe (2.9% + $0.30 per transaction)

---

## 🎯 **EXECUTIVE SUMMARY**

ggbots is an autonomous AI trading platform with a freemium business model. Users get basic AI trading bots for free, while Pro subscribers access reasoning-powered AI models, telegram automation, and signal processing frameworks.

**Revenue Streams**:
- Monthly subscriptions (Pro Plan) - Premium AI + automation infrastructure
- Partner referrals (ggShot TradingView indicator) - 40% commission on $100-1000/month subscriptions
- Future: Enterprise/institutional tiers
- Future: Marketplace for user-created trading strategies

---

## 🎨 **SUBSCRIPTION TIERS**

### ✅ **Free Plan**

**Core Trading Engine**:
- ✅ Paper trading with $10,000 virtual balance
- ✅ Technical analysis (21 indicators across 7 timeframes)
- ✅ Basic bot configuration and management
- ✅ Real-time position tracking and P&L monitoring
- ✅ Decision audit trail and reasoning transparency
- ✅ Manual bot triggers ("Run Once" functionality)

**Technical Indicators (All Free)**:
- **Momentum**: RSI, MACD, Stochastic, Williams %R, CCI, MFI, ROC, Aroon, Vortex, TRIX
- **Trend**: ADX, Parabolic SAR, EMA, SMA
- **Volatility**: Bollinger Bands, Keltner Channels, Donchian, ATR, BB Width
- **Volume**: OBV, VWAP

**Platform Limits**:
- ✅ 1 active trading bot
- ✅ Multi-timeframe analysis (1h, 4h, 1d, 1w minimum frequency)
- ✅ Real-time SSE dashboard updates
- ✅ Bot scheduling and automation (1h+ intervals)
- ✅ Bring-your-own LLM API keys
- ✅ Mobile-responsive interface

### 💎 **Pro Plan ($29/month or $279/year)**

**Key Features**:

- 💎 **Frontier reasoning models**: Tuned for market analysis and trading decisions - no API key management required

- 💎 **High frequency analysis**: Run your ggbots more often (down to 5m intervals) so you never miss an opportunity

- 💎 **Telegram publishing**: Receive your ggbot's decisions to use as signals for full autonomous trading

- 💎 **Multiple bots**: Up to 10 active ggbots so you can A/B test several strategies at once

**Additional Benefits**:
- Priority support
- Advanced analytics and performance metrics
- Early access to new features

---

## 💰 **PRICING STRATEGY**

### Current Tier Structure

| Feature | Free | Pro ($29/month) |
|---------|------|--------------------|
| Paper Trading | ✅ | ✅ |
| Technical Analysis (21 indicators) | ✅ | ✅ |
| Active Bots | 1 | **10** |
| Analysis Frequency | 1h minimum | **5m minimum** |
| LLM Models | Bring-your-own API keys | **Frontier reasoning models included** |
| Telegram Publishing | ❌ | **✅** |
| Advanced Analytics | ❌ | ✅ |
| Priority Support | ❌ | ✅ |

**Annual Pricing**: $279/year (save $69 - 20% discount)

**Trial Period**: 14 days (full access, no credit card required upfront)

**Early Adopter Promo**: 50% off first 3 months for first 100 subscribers

---

## 🔧 **STRIPE INTEGRATION - TECHNICAL IMPLEMENTATION**

### Why Stripe Checkout (Hosted)

**Decision Rationale**:
- ✅ **Fastest implementation** - Ships in 1 day vs 3-4 days for embedded forms
- ✅ **Battle-tested conversion** - Stripe's checkout is A/B tested for years
- ✅ **Zero PCI compliance burden** - Stripe handles all card data
- ✅ **Mobile-first** - Auto-handles Apple Pay, Google Pay, Link
- ✅ **Lower maintenance** - Stripe updates UI, we don't touch code
- ✅ **Built-in trial handling** - 14-day trial countdown, automatic conversion
- ✅ **Customer portal included** - Self-service subscription management

**User Journey**:
```
User clicks "Start 14-Day Trial" → Redirects to checkout.stripe.com →
Enters payment info on Stripe's page → Stripe processes payment →
Redirects to ggbot-app.vercel.app/success → Webhook updates database →
User has Pro access
```

---

## 📋 **IMPLEMENTATION ROADMAP**

### Phase 1: Stripe Dashboard Setup (1-2 hours)

**You'll complete these steps in Stripe Dashboard:**

#### Step 1: Access Products Section
1. Log into https://dashboard.stripe.com
2. Click **Products** in left sidebar
3. Click **+ Add product** button
product id: prod_T9eJWkbhMxlNKp

#### Step 2: Create Monthly Subscription Product
1. **Product name**: `ggbots.ai Pro Plan`
2. **Description**: `Premium AI trading bots with reasoning models, high-frequency analysis, and Telegram integration`
3. **Pricing**:
   - Click **+ Add another price**
   - **Price**: `$29.00 USD`
   - **Billing period**: `Monthly`
   - **Free trial**: `14 days`
4. Click **Save product**
5. **Copy the Price ID**: `` (looks like `price_1Abc123...`)
   - This will be your `STRIPE_PRICE_ID_MONTHLY` env var

#### Step 3: Create Annual Subscription Product
1. Same product: `ggbots.ai Pro Plan`
2. Click **+ Add another price** on the same product
3. **Pricing**:
   - **Price**: `$279.00 USD`
   - **Billing period**: `Yearly`
   - **Free trial**: `14 days`
4. Click **Save**
5. **Copy the Price ID**: ``
   - This will be your `STRIPE_PRICE_ID_ANNUAL` env var

#### Step 4: Create Promotional Coupon (Early Adopter)
1. Click **Coupons** in left sidebar
2. Click **+ New coupon**
3. **Coupon details**:
   - **Name**: `EARLY_ADOPTER`
   - **ID**: `early-50off-3mo` (optional custom ID)
   - **Discount type**: `Percentage`
   - **Percent off**: `50%`
   - **Duration**: `Repeating`
   - **Duration in months**: `3`
4. Click **Create coupon**
5. **Copy Coupon ID**: `early-50off-3mo`

#### Step 5: Get API Keys
1. Click **Developers** → **API keys** in left sidebar
2. **Test Mode** (use this first):
   - **Publishable key**: `pk_test_xxxxxxxxxxxxx` (starts with `pk_test_`)
   - **Secret key**: `sk_test_xxxxxxxxxxxxx` (starts with `sk_test_`)
   - Click **Reveal test key** and copy both
3. **Production Mode** (use after testing):
   - Toggle to "Live mode" in top-right
   - Copy **Publishable key** (`pk_live_xxx`) and **Secret key** (`sk_live_xxx`)

#### Step 6: Set Up Webhook
1. Click **Developers** → **Webhooks** in left sidebar
2. Click **+ Add endpoint**
3. **Endpoint URL**: `https://ggbots-api.nightingale.business/api/v2/stripe-webhook`
4. **Events to listen for**:
   - Click **+ Select events**
   - Search and select:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_failed`
5. Click **Add endpoint**
6. **Copy Webhook Signing Secret**: `whsec_xxxxxxxxxxxxx`
   - Click on the webhook you just created
   - Click **Reveal** under "Signing secret"
   - This will be your `STRIPE_WEBHOOK_SECRET` env var

#### Step 7: Configure Stripe Billing Portal
1. Click **Settings** → **Billing** → **Customer portal**
2. Enable the following features:
   - ✅ Allow customers to update payment methods
   - ✅ Allow customers to cancel subscriptions
   - ✅ Allow customers to view invoice history
3. **Cancellation behavior**:
   - Select: "Cancel at end of billing period"
   - This gives users access until their current period ends
4. Click **Save**

**Summary of values to save**:
```bash
# Test Mode (use first)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
STRIPE_PRICE_ID_MONTHLY=price_xxxxxxxxxxxxx
STRIPE_PRICE_ID_ANNUAL=price_xxxxxxxxxxxxx
STRIPE_COUPON_ID_EARLY_ADOPTER=early-50off-3mo

# Production Mode (use after testing)
STRIPE_SECRET_KEY_LIVE=sk_live_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY_LIVE=pk_live_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET_LIVE=whsec_xxxxxxxxxxxxx
```

---

### Phase 2: Database Schema (Already Complete ✅)

Your existing schema is **perfectly set up** for Stripe integration:

**Existing `user_profiles` table** (from `database/schema.md`):
```sql
CREATE TABLE public.user_profiles (
  user_id uuid NOT NULL,
  subscription_tier subscription_tier DEFAULT 'free'::subscription_tier,  -- 'free' or 'ggbase'
  subscription_status subscription_status DEFAULT 'active'::subscription_status,  -- 'active', 'cancelled', 'past_due'
  subscription_expires_at timestamp with time zone,
  stripe_customer_id character varying,  -- Stripe customer ID
  stripe_subscription_id character varying,  -- Stripe subscription ID
  telegram_user_id bigint,
  telegram_username character varying,
  telegram_chat_id bigint,
  monthly_signal_count integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  paid_data_points text[] DEFAULT ARRAY[]::text[],
  CONSTRAINT user_profiles_pkey PRIMARY KEY (user_id)
);
```

**Existing enums**:
```sql
CREATE TYPE subscription_tier AS ENUM ('free', 'ggbase');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'past_due');
```

**Note**: We'll use `'ggbase'` in the database (keeps compatibility), but display as "Pro Plan" in the UI.

**No database changes needed!** Your schema is ready.

---

### Phase 3: Backend Integration (4-6 hours)

#### Install Stripe SDK

```bash
cd /home/sev/ggbot
source .venv/bin/activate
pip install stripe==11.1.0
```

Add to `requirements.txt`:
```
stripe==11.1.0
```

#### Add Environment Variables to `.env`

```bash
# Stripe Configuration (Test Mode)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
STRIPE_PRICE_ID_MONTHLY=price_xxxxxxxxxxxxx
STRIPE_PRICE_ID_ANNUAL=price_xxxxxxxxxxxxx
STRIPE_COUPON_ID_EARLY_ADOPTER=early-50off-3mo

# Frontend URLs
FRONTEND_URL=https://ggbot-app.vercel.app
```

#### Implementation in `ggbot.py`

Add these endpoints to your existing `ggbot.py` file:

```python
import stripe
from fastapi import HTTPException, Request, Depends
from core.auth.supabase_auth import get_current_user_v2, AuthenticatedUser
from core.common.db import get_db_connection
from core.common.logger import logger
from pydantic import BaseModel

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Request models
class CheckoutRequest(BaseModel):
    plan: str  # 'monthly' or 'annual'
    coupon: Optional[str] = None  # Optional coupon code

# =============================================================================
# STRIPE ENDPOINTS
# =============================================================================

@app.post("/api/v2/create-checkout-session")
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Create Stripe Checkout session for Pro Plan upgrade.

    User flow:
    1. User clicks "Upgrade to Pro" button in frontend
    2. Frontend calls this endpoint
    3. This creates a Stripe Checkout session
    4. Frontend redirects user to Stripe's hosted checkout page
    5. After payment, Stripe redirects back to our success page
    6. Webhook updates user's subscription_tier in database
    """

    # Map plan to price ID
    price_ids = {
        'monthly': os.environ['STRIPE_PRICE_ID_MONTHLY'],
        'annual': os.environ['STRIPE_PRICE_ID_ANNUAL']
    }

    if request.plan not in price_ids:
        raise HTTPException(400, "Invalid plan. Must be 'monthly' or 'annual'")

    try:
        # Get or create Stripe customer
        customer_id = await get_or_create_stripe_customer(current_user.user_id, current_user.email)

        # Build checkout session params
        checkout_params = {
            'customer': customer_id,
            'mode': 'subscription',
            'line_items': [{
                'price': price_ids[request.plan],
                'quantity': 1
            }],
            'success_url': f"{os.environ['FRONTEND_URL']}/success?session_id={{CHECKOUT_SESSION_ID}}",
            'cancel_url': f"{os.environ['FRONTEND_URL']}/pricing",
            'client_reference_id': str(current_user.user_id),
            'subscription_data': {
                'trial_period_days': 14,
                'metadata': {
                    'user_id': str(current_user.user_id),
                    'plan': request.plan
                }
            },
            'metadata': {
                'user_id': str(current_user.user_id)
            },
            'allow_promotion_codes': True,  # Allow users to enter promo codes at checkout
        }

        # Add coupon if provided
        if request.coupon:
            checkout_params['discounts'] = [{
                'coupon': request.coupon
            }]

        # Create Stripe Checkout session
        session = stripe.checkout.Session.create(**checkout_params)

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created Stripe checkout session: {session.id} for plan: {request.plan}"
        )

        return {'checkout_url': session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(500, f"Payment system error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(500, "Internal server error")


@app.post("/api/v2/stripe-webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.

    Critical events:
    - checkout.session.completed: User completed payment, activate subscription
    - customer.subscription.updated: Subscription changed (renewal, etc)
    - customer.subscription.deleted: User cancelled subscription
    - invoice.payment_failed: Payment failed, mark as past_due

    Security:
    - Verifies webhook signature using Stripe SDK
    - Only processes events from Stripe (HMAC validation)
    """

    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.environ['STRIPE_WEBHOOK_SECRET']

    try:
        # Verify webhook signature (Stripe SDK handles HMAC validation)
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        logger.error("Invalid webhook payload")
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        raise HTTPException(400, "Invalid signature")

    # Log all webhook events for debugging
    logger.info(f"Received Stripe webhook: {event['type']}")

    # Handle different event types
    event_type = event['type']

    if event_type == 'checkout.session.completed':
        # User completed checkout and started subscription
        await handle_checkout_completed(event['data']['object'])

    elif event_type == 'customer.subscription.updated':
        # Subscription was updated (renewal, plan change, etc)
        await handle_subscription_updated(event['data']['object'])

    elif event_type == 'customer.subscription.deleted':
        # Subscription was cancelled
        await handle_subscription_deleted(event['data']['object'])

    elif event_type == 'invoice.payment_failed':
        # Payment failed, mark subscription as past_due
        await handle_payment_failed(event['data']['object'])

    return {'received': True}


@app.post("/api/v2/create-portal-session")
async def create_portal_session(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """
    Create Stripe billing portal session for subscription management.

    Allows users to:
    - Update payment method
    - Cancel subscription
    - View invoice history
    - Download receipts

    User remains on Stripe-hosted portal, then returns to our app.
    """

    # Get Stripe customer ID from database
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT stripe_customer_id
                FROM user_profiles
                WHERE user_id = %s
            """, (str(current_user.user_id),))
            result = cur.fetchone()

    if not result or not result[0]:
        raise HTTPException(404, "No active subscription found. Please upgrade first.")

    customer_id = result[0]

    try:
        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{os.environ['FRONTEND_URL']}/settings",
        )

        logger.bind(user_id=str(current_user.user_id)).info(
            f"Created billing portal session for customer: {customer_id}"
        )

        return {'portal_url': session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal session: {e}")
        raise HTTPException(500, f"Error accessing billing portal: {str(e)}")


# =============================================================================
# WEBHOOK HANDLERS (Internal functions)
# =============================================================================

async def handle_checkout_completed(session):
    """Handle successful checkout - activate Pro subscription."""
    user_id = session['metadata']['user_id']
    customer_id = session['customer']
    subscription_id = session['subscription']

    # Get subscription details to find trial end date
    subscription = stripe.Subscription.retrieve(subscription_id)
    trial_end = None
    if subscription.trial_end:
        from datetime import datetime
        trial_end = datetime.fromtimestamp(subscription.trial_end)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET subscription_tier = 'ggbase',
                    subscription_status = 'active',
                    stripe_customer_id = %s,
                    stripe_subscription_id = %s,
                    subscription_expires_at = %s,
                    updated_at = NOW()
                WHERE user_id = %s
            """, (customer_id, subscription_id, trial_end, user_id))
            conn.commit()

    logger.bind(user_id=user_id).info(
        f"Pro subscription activated. Customer: {customer_id}, Subscription: {subscription_id}"
    )


async def handle_subscription_updated(subscription):
    """Handle subscription updates (renewals, plan changes)."""
    subscription_id = subscription['id']
    customer_id = subscription['customer']
    status = subscription['status']

    # Map Stripe status to our status
    status_map = {
        'active': 'active',
        'canceled': 'cancelled',
        'past_due': 'past_due',
        'unpaid': 'past_due',
        'incomplete': 'past_due'
    }

    our_status = status_map.get(status, 'active')

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET subscription_status = %s,
                    updated_at = NOW()
                WHERE stripe_subscription_id = %s
            """, (our_status, subscription_id))
            conn.commit()

    logger.info(f"Subscription updated: {subscription_id}, status: {our_status}")


async def handle_subscription_deleted(subscription):
    """Handle subscription cancellation."""
    subscription_id = subscription['id']

    # Get cancellation date (end of current period)
    from datetime import datetime
    cancel_at = datetime.fromtimestamp(subscription['ended_at'])

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET subscription_tier = 'free',
                    subscription_status = 'cancelled',
                    subscription_expires_at = %s,
                    updated_at = NOW()
                WHERE stripe_subscription_id = %s
            """, (cancel_at, subscription_id))
            conn.commit()

    logger.info(f"Subscription cancelled: {subscription_id}, access until: {cancel_at}")


async def handle_payment_failed(invoice):
    """Handle failed payment - mark as past_due."""
    subscription_id = invoice['subscription']

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET subscription_status = 'past_due',
                    updated_at = NOW()
                WHERE stripe_subscription_id = %s
            """, (subscription_id,))
            conn.commit()

    logger.warning(f"Payment failed for subscription: {subscription_id}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_or_create_stripe_customer(user_id: str, email: str) -> str:
    """
    Get existing Stripe customer ID or create new customer.

    This ensures each user has exactly one Stripe customer record.
    """

    # Check database for existing customer
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT stripe_customer_id
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()

    if result and result[0]:
        return result[0]  # Customer already exists

    # Create new Stripe customer
    try:
        customer = stripe.Customer.create(
            email=email,
            metadata={'user_id': user_id}
        )

        # Save to database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET stripe_customer_id = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (customer.id, user_id))
                conn.commit()

        logger.bind(user_id=user_id).info(f"Created Stripe customer: {customer.id}")
        return customer.id

    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe customer: {e}")
        raise
```

**Total backend code**: ~250 lines (well-structured, includes comments)

---

### Phase 4: Feature Gating Integration (2-3 hours)

Your existing `UserProfile` domain model already has perfect feature gating! Let's integrate it:

#### Bot Creation Limit (1 bot free, 10 Pro)

Add to your bot creation endpoint in `ggbot.py`:

```python
@app.post("/api/v2/configs")
async def create_config(
    request: ConfigCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Create new bot configuration with tier-based limits."""

    # Load user profile to check subscription tier
    profile = await current_user.load_profile()

    # Count existing bots
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM configurations
                WHERE user_id = %s
            """, (str(current_user.user_id),))
            bot_count = cur.fetchone()[0]

    # Enforce bot limits
    if profile.is_free_tier and bot_count >= 1:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Bot limit reached",
                "message": "Free plan allows 1 bot. Upgrade to Pro for 10 bots.",
                "current_plan": "free",
                "bot_limit": 1,
                "current_bots": bot_count,
                "upgrade_url": "/pricing"
            }
        )

    if profile.is_ggbase_tier and bot_count >= 10:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Bot limit reached",
                "message": "Pro plan allows 10 bots. Contact support for enterprise.",
                "current_plan": "pro",
                "bot_limit": 10,
                "current_bots": bot_count
            }
        )

    # Proceed with bot creation...
    # (your existing logic)
```

#### Frequency Restriction (1h min free, 5m min Pro)

Add to your scheduler start endpoint:

```python
@app.post("/api/v2/configs/{config_id}/start")
async def start_scheduler(
    config_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Start bot scheduler with frequency validation."""

    # Get bot config
    config = await config_service.get_config(current_user.user_id, config_id)
    if not config:
        raise HTTPException(404, "Bot not found")

    # Load user profile
    profile = await current_user.load_profile()

    # Parse frequency (e.g., "5m", "1h", "4h")
    frequency = config.config_data.get('frequency', '1h')

    # Convert to minutes
    if frequency.endswith('m'):
        minutes = int(frequency[:-1])
    elif frequency.endswith('h'):
        minutes = int(frequency[:-1]) * 60
    else:
        raise HTTPException(400, "Invalid frequency format")

    # Enforce frequency limits
    if profile.is_free_tier and minutes < 60:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Frequency limit exceeded",
                "message": "Free plan requires 1h minimum interval. Upgrade to Pro for 5m intervals.",
                "current_plan": "free",
                "min_interval": "1h",
                "requested_interval": frequency,
                "upgrade_url": "/pricing"
            }
        )

    if profile.is_ggbase_tier and minutes < 5:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Frequency limit exceeded",
                "message": "Pro plan requires 5m minimum interval.",
                "current_plan": "pro",
                "min_interval": "5m",
                "requested_interval": frequency
            }
        )

    # Proceed with scheduler start...
    # (your existing logic)
```

#### Telegram Publishing Gate (Pro only)

Your `UserProfile` already has this! Just use it:

```python
# In your Telegram publishing logic
async def publish_to_telegram(decision, user_id):
    """Publish decision to Telegram (Pro feature)."""

    # Load user profile
    from core.services.user_service import UserService
    user_service = UserService()
    profile = await user_service.get_or_create_profile(user_id, email="")

    # Check if user can publish
    if not profile.can_publish_telegram_signals:
        logger.bind(user_id=user_id).warning(
            "User attempted Telegram publish without Pro subscription"
        )
        raise HTTPException(
            status_code=403,
            detail="Telegram publishing requires Pro subscription"
        )

    # Proceed with publishing...
```

#### Signal Validation Gate (Pro only)

```python
@app.post("/api/v2/signal-validation")
async def validate_signal(
    signal_data: dict,
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
):
    """Validate external signals (Pro feature)."""

    # Load profile and check access
    profile = await current_user.load_profile()

    if not profile.can_use_signal_validation:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Premium feature required",
                "message": "Signal validation requires Pro subscription",
                "feature": "signal_validation",
                "upgrade_url": "/pricing"
            }
        )

    # Proceed with validation...
```

---

### Phase 5: Frontend Integration (3-4 hours)

#### Pricing Page Component

Create `frontend/app/pricing/page.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function PricingPage() {
  const { token, user } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<'monthly' | 'annual'>('monthly');

  const handleUpgrade = async (selectedPlan: 'monthly' | 'annual') => {
    if (!token) {
      router.push('/login');
      return;
    }

    setLoading(true);

    try {
      const res = await fetch('https://ggbots-api.nightingale.business/api/v2/create-checkout-session', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          plan: selectedPlan,
          // Optional: include early adopter coupon
          // coupon: 'early-50off-3mo'
        })
      });

      if (!res.ok) {
        throw new Error('Failed to create checkout session');
      }

      const { checkout_url } = await res.json();

      // Redirect to Stripe Checkout
      window.location.href = checkout_url;

    } catch (error) {
      console.error('Checkout error:', error);
      alert('Failed to start checkout. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600">
            Start with a 14-day free trial. No credit card required.
          </p>
        </div>

        {/* Plan Toggle */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-lg p-1 inline-flex">
            <button
              onClick={() => setPlan('monthly')}
              className={`px-6 py-2 rounded-md ${
                plan === 'monthly'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setPlan('annual')}
              className={`px-6 py-2 rounded-md ${
                plan === 'annual'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600'
              }`}
            >
              Annual <span className="text-sm">(Save 20%)</span>
            </button>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Free Plan */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Free Plan</h3>
            <div className="mb-6">
              <span className="text-4xl font-bold">$0</span>
              <span className="text-gray-600">/forever</span>
            </div>

            <ul className="space-y-3 mb-8">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>1 active ggbot</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Hourly analysis intervals</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Bring-your-own LLM API keys</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>21 technical indicators</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Paper trading with $10K balance</span>
              </li>
            </ul>

            <button
              disabled
              className="w-full py-3 px-6 rounded-lg bg-gray-300 text-gray-600 font-semibold cursor-not-allowed"
            >
              Current Plan
            </button>
            <p className="text-center text-gray-500 text-xs mt-2">
              Perfect for testing the platform
            </p>
          </div>

          {/* Pro Plan */}
          <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg shadow-xl p-8 text-white relative">
            <div className="absolute top-0 right-0 bg-yellow-400 text-gray-900 text-xs font-bold px-3 py-1 rounded-bl-lg rounded-tr-lg">
              MOST POPULAR
            </div>

            <h3 className="text-2xl font-bold mb-2">Pro Plan</h3>
            <div className="mb-6">
              {plan === 'monthly' ? (
                <>
                  <span className="text-4xl font-bold">$29</span>
                  <span className="text-blue-100">/month</span>
                </>
              ) : (
                <>
                  <span className="text-4xl font-bold">$279</span>
                  <span className="text-blue-100">/year</span>
                  <div className="text-sm text-yellow-300 mt-1">
                    Save $69 (20% off)
                  </div>
                </>
              )}
            </div>

            <ul className="space-y-4 mb-8">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-yellow-300 mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <div>
                  <strong className="block">Frontier reasoning models</strong>
                  <span className="text-sm text-blue-100">Tuned for market analysis and trading decisions</span>
                </div>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-yellow-300 mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <div>
                  <strong className="block">High frequency analysis</strong>
                  <span className="text-sm text-blue-100">Run your ggbots more often so you never miss an opportunity</span>
                </div>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-yellow-300 mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <div>
                  <strong className="block">Telegram publishing</strong>
                  <span className="text-sm text-blue-100">Receive your ggbot's decisions to use as signals for full autonomous trading</span>
                </div>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-yellow-300 mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <div>
                  <strong className="block">Multiple bots</strong>
                  <span className="text-sm text-blue-100">Up to 10 active ggbots so you can A/B test several strategies at once</span>
                </div>
              </li>
            </ul>

            <button
              onClick={() => handleUpgrade(plan)}
              disabled={loading}
              className="w-full py-3 px-6 rounded-lg bg-white text-blue-600 font-bold hover:bg-gray-100 transition disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Start 14-Day Free Trial'}
            </button>

            <p className="text-center text-blue-100 text-sm mt-4">
              No credit card required • Cancel anytime
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### Success Page

Create `frontend/app/success/page.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SuccessPage() {
  const router = useRouter();
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          router.push('/dashboard');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome to Pro! 🎉
        </h1>

        <p className="text-gray-600 mb-6">
          Your 14-day free trial has started. Enjoy all premium features!
        </p>

        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-900">
            <strong>What's unlocked:</strong>
          </p>
          <ul className="text-sm text-blue-800 mt-2 space-y-1">
            <li>✓ Frontier reasoning models tuned for trading</li>
            <li>✓ High frequency analysis (5m intervals)</li>
            <li>✓ Telegram publishing for autonomous trading</li>
            <li>✓ Up to 10 ggbots for A/B testing strategies</li>
          </ul>
        </div>

        <p className="text-gray-500 text-sm">
          Redirecting to dashboard in {countdown} seconds...
        </p>
      </div>
    </div>
  );
}
```

#### Settings Page - Manage Subscription

Add to your existing `frontend/app/settings/page.tsx`:

```typescript
const handleManageSubscription = async () => {
  try {
    const res = await fetch('https://ggbots-api.nightingale.business/api/v2/create-portal-session', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!res.ok) {
      throw new Error('Failed to access billing portal');
    }

    const { portal_url } = await res.json();
    window.location.href = portal_url;

  } catch (error) {
    console.error('Portal error:', error);
    alert('Failed to access billing portal');
  }
};

// In your JSX:
<div className="bg-white rounded-lg shadow p-6">
  <h3 className="text-lg font-semibold mb-4">Subscription</h3>

  {user?.subscription_tier === 'ggbase' ? (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="font-medium text-gray-900">Pro Plan</p>
          <p className="text-sm text-gray-600">$29/month or $279/year</p>
        </div>
        <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
          Active
        </span>
      </div>

      <button
        onClick={handleManageSubscription}
        className="w-full py-2 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
      >
        Manage Subscription
      </button>

      <p className="text-xs text-gray-500 mt-2">
        Update payment method, cancel subscription, or view invoices
      </p>
    </div>
  ) : (
    <div>
      <p className="text-gray-600 mb-4">You're on the Free plan</p>
      <button
        onClick={() => router.push('/pricing')}
        className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        Upgrade to Pro
      </button>
    </div>
  )}
</div>
```

#### Dashboard - Subscription Badge

Add to `frontend/app/dashboard/page.tsx`:

```typescript
// In header/nav area:
{user?.subscription_tier === 'ggbase' && (
  <span className="px-3 py-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-bold rounded-full">
    PRO
  </span>
)}
```

---

### Phase 6: Testing (2-3 hours)

#### Test with Stripe CLI (Local Testing)

Install Stripe CLI:
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Or download from: https://stripe.com/docs/stripe-cli
```

Forward webhooks to local:
```bash
stripe listen --forward-to localhost:8000/api/v2/stripe-webhook
```

Trigger test events:
```bash
# Test successful payment
stripe trigger checkout.session.completed

# Test subscription update
stripe trigger customer.subscription.updated

# Test cancellation
stripe trigger customer.subscription.deleted
```

#### Manual Testing Flow

1. **Test Monthly Subscription**:
   - Go to `/pricing`
   - Click "Start 14-Day Trial" (Monthly)
   - Use test card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
   - Complete checkout
   - Verify redirect to `/success`
   - Check database: `subscription_tier` should be `'ggbase'`

2. **Test Annual Subscription**:
   - Repeat with Annual plan
   - Test card: `4242 4242 4242 4242`

3. **Test Feature Gating**:
   - As free user: Try to create 2nd bot → should fail
   - As free user: Try to set 30m frequency → should fail
   - As Pro user: Create 10 bots → should succeed
   - As Pro user: Set 5m frequency → should succeed

4. **Test Billing Portal**:
   - Go to `/settings`
   - Click "Manage Subscription"
   - Verify redirect to Stripe portal
   - Test updating payment method
   - Test cancelling subscription
   - Verify cancellation updates database

5. **Test Coupon**:
   - At checkout, enter coupon code: `early-50off-3mo`
   - Verify 50% discount applied

---

### Phase 7: Go Live (1 hour)

1. **Switch to Live Keys**:
   ```bash
   # Update .env
   STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
   STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx  # Create new webhook in live mode
   ```

2. **Update Webhook in Stripe Dashboard**:
   - Switch to Live mode in Stripe
   - Add webhook: `https://ggbots-api.nightingale.business/api/v2/stripe-webhook`
   - Select same events as test mode
   - Copy new webhook secret

3. **Deploy Backend**:
   ```bash
   pm2 restart ggbot
   ```

4. **Deploy Frontend**:
   ```bash
   git add .
   git commit -m "Add Stripe subscription integration"
   git push  # Vercel auto-deploys
   ```

5. **Test with Real Card**:
   - Use your own card
   - Complete checkout
   - Immediately cancel (to avoid charges during testing)
   - Verify everything works

---

## 🎯 **SUBSCRIPTION STATE MANAGEMENT**

### How State Syncs Between Stripe & Supabase

**Your architecture is elegant** - here's how it works:

#### On Signup (No Payment Yet)
```
User signs up → Supabase creates auth.users record →
Backend creates user_profiles record with:
  subscription_tier = 'free'
  subscription_status = 'active'
  stripe_customer_id = NULL
```

#### On Checkout Completed
```
User clicks "Upgrade" → Redirects to Stripe →
User enters payment → Stripe processes →
Webhook fires: checkout.session.completed →
Backend updates user_profiles:
  subscription_tier = 'ggbase'
  subscription_status = 'active'
  stripe_customer_id = 'cus_xxx'
  stripe_subscription_id = 'sub_xxx'
  subscription_expires_at = trial_end_date
```

#### On Trial End (Auto-charges)
```
Stripe auto-charges card →
Webhook fires: customer.subscription.updated →
Backend updates:
  subscription_status = 'active'
  subscription_expires_at = next_billing_date
```

#### On Payment Failure
```
Stripe payment fails →
Webhook fires: invoice.payment_failed →
Backend updates:
  subscription_status = 'past_due'
(User loses Pro access immediately)
```

#### On Cancellation
```
User cancels via portal →
Webhook fires: customer.subscription.deleted →
Backend updates:
  subscription_tier = 'free'
  subscription_status = 'cancelled'
  subscription_expires_at = end_of_period
(User keeps access until period ends)
```

### Frontend Subscription Check

**Your existing auth already handles this!**

The `AuthenticatedUser` class loads profile:
```python
# In core/auth/supabase_auth.py
async def is_premium_user(self) -> bool:
    """Check if user has premium subscription."""
    profile = await self.load_profile()
    return profile.can_use_premium_features if profile else False
```

**Frontend can check**:
```typescript
// Fetch user profile
const res = await fetch('/api/v2/me', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const profile = await res.json();

// Check tier
if (profile.subscription_tier === 'ggbase') {
  // Show Pro features
}

// Or check specific capability
if (profile.can_use_premium_features) {
  // Allow Telegram publishing
}
```

Add this endpoint to `ggbot.py`:
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
        "can_publish_telegram_signals": profile.can_publish_telegram_signals,
        "has_stripe_integration": profile.has_stripe_integration,
        "subscription_expires_at": profile.subscription_expires_at.isoformat() if profile.subscription_expires_at else None
    }
```

---

## 🔒 **SECURITY & BEST PRACTICES**

### Webhook Security
✅ **Stripe SDK verifies signatures** - prevents fake webhooks
✅ **HTTPS only** - webhooks only work over HTTPS
✅ **Idempotency** - safe to process same webhook multiple times

### Data Privacy
✅ **Never store card numbers** - Stripe handles all card data
✅ **PCI compliance** - you're automatically compliant (Stripe is PCI Level 1)
✅ **Supabase RLS** - users can only see their own data

### Testing Safety
✅ **Test mode first** - use test keys until verified
✅ **Webhook signatures** - always verify in production
✅ **Error handling** - graceful failures with user feedback

---

## 📊 **MONITORING & ANALYTICS**

### Stripe Dashboard
- View MRR (Monthly Recurring Revenue)
- Track churn rate
- See failed payments
- Download customer list

### Custom Analytics (Future)
Add to your database:
```sql
CREATE TABLE subscription_events (
  event_id uuid PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id),
  event_type varchar(50),  -- 'upgrade', 'downgrade', 'cancel', 'reactivate'
  from_tier varchar(20),
  to_tier varchar(20),
  created_at timestamp DEFAULT NOW()
);
```

Track conversions:
```python
# In webhook handlers
await log_subscription_event(
    user_id=user_id,
    event_type='upgrade',
    from_tier='free',
    to_tier='ggbase'
)
```

---

## 🎉 **SUCCESS METRICS**

### Launch Goals (First 30 Days)
- [ ] 10 Pro subscribers (MRR: $290)
- [ ] <5% churn rate
- [ ] 90%+ free-to-trial conversion
- [ ] 0 webhook failures

### Growth Targets (First 90 Days)
- [ ] 100 Pro subscribers (MRR: $2,900)
- [ ] 50% free-to-paid conversion from trials
- [ ] $10K+ ARR

---

## 📚 **APPENDIX**

### Environment Variables Checklist

```bash
# Required for Stripe Integration
STRIPE_SECRET_KEY=sk_test_xxx  # Then sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_ID_MONTHLY=price_xxx
STRIPE_PRICE_ID_ANNUAL=price_xxx
STRIPE_COUPON_ID_EARLY_ADOPTER=early-50off-3mo
FRONTEND_URL=https://ggbot-app.vercel.app

# Existing (already configured)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
DATABASE_URL=postgresql://xxx
```

### Stripe Test Cards

```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
Requires authentication: 4000 0025 0000 3155
```

### Useful Stripe CLI Commands

```bash
# Listen for webhooks locally
stripe listen --forward-to localhost:8000/api/v2/stripe-webhook

# Trigger test events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.deleted

# View recent events
stripe events list --limit 10

# Get customer info
stripe customers retrieve cus_xxx

# Cancel subscription
stripe subscriptions cancel sub_xxx
```

---

**Implementation Status**: Ready to start Phase 1 (Stripe Dashboard Setup)
**Estimated Total Time**: 10-14 hours (spread over 2-3 days)
**Next Action**: Complete Stripe Dashboard setup and provide API keys

**Questions?** Review this doc and let me know when you have your Stripe API keys ready!
