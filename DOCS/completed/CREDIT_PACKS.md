# Credit Packs & Crypto Payments

**Status**: ✅ COMPLETE
**Created**: 2026-01-08
**Completed**: 2026-01-08

---

## Overview

Allow users to prepay for usage credits via Stripe (card) or NOWPayments (crypto). Credits apply automatically to metered billing via Stripe Credit Grants.

---

## Core Insight

**Credits = prepayment for usage-based billing.**

The user must be on `usage_based` tier for credits to work (Credit Grants apply to metered subscriptions). This means:

| User State | Action When Buying Credits |
|------------|---------------------------|
| `free` tier | Create subscription + purchase credits |
| `usage_based` tier | Just purchase credits |
| Credits run out | Nothing - billed normally for overage |

**The elegant solution**: Both "pay as you go" and "prepay credits" end with user on `usage_based` tier. Credits are just prepayment.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED BILLING FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Free User                         Usage-Based User             │
│  ─────────                         ────────────────             │
│  UpgradeModal opens                UserProfile dropdown         │
│        ↓                                  ↓                     │
│  Two options:                       "Add Credits" button        │
│  • Pay as you go                          ↓                     │
│  • Prepay credits                   Credit picker               │
│        ↓                                  ↓                     │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  Credit Picker                                      │        │
│  │  [$10] [$25] [$50] [$100]                          │        │
│  │  [💳 Card]  [🪙 Crypto]                            │        │
│  └─────────────────────────────────────────────────────┘        │
│        │                                  │                     │
│        ▼                                  ▼                     │
│   ┌─────────┐                      ┌─────────────┐              │
│   │ Stripe  │                      │ NOWPayments │              │
│   │Checkout │                      │   Widget    │              │
│   └────┬────┘                      └──────┬──────┘              │
│        │                                  │                     │
│        ▼                                  ▼                     │
│   Webhook                            IPN Callback               │
│   checkout.session.completed         payment_status: finished   │
│        │                                  │                     │
│        └──────────────┬───────────────────┘                     │
│                       ▼                                         │
│            ┌─────────────────────┐                              │
│            │ Ensure user has:    │                              │
│            │ 1. Stripe customer  │                              │
│            │ 2. usage_based sub  │                              │
│            │ 3. Credit Grant     │                              │
│            └─────────────────────┘                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## UI/UX Design

### UpgradeModal (Free Users)

When a free user tries to activate a bot:

```
┌─────────────────────────────────────────┐
│  🤖 Activate {Bot Name}             ✕   │
├─────────────────────────────────────────┤
│                                         │
│  Your bot will trade 24/7 while you     │
│  sleep. Choose how to pay:              │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  📊 Pay as you go               │    │
│  │  Billed monthly for usage       │    │
│  │  ~$5-15/month typical           │    │
│  │            [Continue →]         │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  💰 Prepay credits              │    │
│  │  Buy credits, use until empty   │    │
│  │  Never expires • Card or Crypto │    │
│  │                                 │    │
│  │  [$10] [$25] [$50] [$100]       │    │
│  │                                 │    │
│  │  [💳 Card]    [🪙 Crypto]       │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ✓ No base fee  ✓ Cancel anytime       │
└─────────────────────────────────────────┘
```

### UserProfile Dropdown (Usage-Based Users)

```
┌────────────────────────────────────┐
│  John Doe                          │
│  john@example.com                  │
│  ┌──────────────────────────────┐  │
│  │ Usage-Based                   │  │
│  └──────────────────────────────┘  │
├────────────────────────────────────┤
│  💰 Credits: $12.50               │
│  📊 This period: $8.42            │
├────────────────────────────────────┤
│  ⚙️  Settings                      │
│  ➕ Add Credits                    │  ← Opens credit picker
│  📋 Manage Billing                 │
│  🚪 Log out                        │
└────────────────────────────────────┘
```

### Add Credits Picker (Modal/Popover)

```
┌─────────────────────────────────┐
│  Add Credits                ✕   │
├─────────────────────────────────┤
│                                 │
│  Current balance: $12.50        │
│                                 │
│  [$10] [$25] [$50] [$100]       │
│                                 │
│  [💳 Card]    [🪙 Crypto]       │
│                                 │
│  Credits never expire           │
└─────────────────────────────────┘
```

---

## Implementation

### Backend

**1. Credit Purchase Endpoint**

```python
@app.post("/api/v2/credits/purchase")
async def purchase_credits(request: CreditPurchaseRequest, current_user: AuthenticatedUser):
    """Create Stripe Checkout for credit purchase."""
    amount_cents = request.amount  # 1000 = $10

    # Get or create Stripe customer
    customer_id = get_or_create_stripe_customer(current_user.user_id)

    # Check if user needs subscription
    needs_subscription = not has_usage_based_subscription(current_user.user_id)

    if needs_subscription:
        # Checkout with subscription + one-time credit payment
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode='subscription',
            line_items=[
                {'price': USAGE_BASED_PRICE_ID},  # $0 subscription
                {'price_data': {...}, 'quantity': 1}  # One-time credit pack
            ],
            metadata={'type': 'credit_purchase', 'amount': amount_cents, 'user_id': str(current_user.user_id)},
            ...
        )
    else:
        # Just one-time payment for credits
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode='payment',
            line_items=[{'price_data': {..., 'unit_amount': amount_cents}, 'quantity': 1}],
            metadata={'type': 'credit_purchase', 'amount': amount_cents, 'user_id': str(current_user.user_id)},
            ...
        )

    return {'checkout_url': session.url}
```

**2. Credit Balance Endpoint**

```python
@app.get("/api/v2/credits/balance")
async def get_credit_balance(current_user: AuthenticatedUser):
    """Get user's credit balance from Stripe."""
    customer_id = get_stripe_customer_id(current_user.user_id)
    if not customer_id:
        return {'available_usd': 0, 'ledger_usd': 0}

    summary = stripe.billing.CreditBalanceSummary.retrieve(
        customer=customer_id,
        filter={'type': 'applicability_scope', 'applicability_scope': {'price_type': 'metered'}}
    )

    balance = summary.balances[0] if summary.balances else None
    return {
        'available_usd': (balance.available.monetary.value / 100) if balance else 0,
        'ledger_usd': (balance.ledger.monetary.value / 100) if balance else 0
    }
```

**3. Webhook Handler Update**

```python
async def handle_checkout_completed(session):
    """Handle checkout completion - subscription OR credits."""
    metadata = session.get('metadata', {})

    if metadata.get('type') == 'credit_purchase':
        # Credit purchase
        user_id = metadata['user_id']
        amount_cents = int(metadata['amount'])
        customer_id = session['customer']

        # Create credit grant
        stripe.billing.CreditGrant.create(
            customer=customer_id,
            name=f"${amount_cents/100:.0f} Credit Pack",
            applicability_config={'scope': {'price_type': 'metered'}},
            category='paid',
            amount={'type': 'monetary', 'monetary': {'value': amount_cents, 'currency': 'usd'}}
        )

        # Ensure user is on usage_based tier
        ensure_usage_based_tier(user_id, customer_id, session.get('subscription'))

    else:
        # Regular subscription upgrade (existing logic)
        ...
```

**4. NOWPayments Create Invoice Endpoint**

```python
@app.post("/api/v2/credits/crypto-checkout")
async def create_crypto_checkout(request: CreditPurchaseRequest, current_user: AuthenticatedUser):
    """Create NOWPayments invoice for crypto credit purchase."""
    import httpx

    amount_usd = request.amount / 100  # Convert cents to dollars

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.nowpayments.io/v1/invoice",
            headers={
                "x-api-key": os.environ["PAYMENTS_API_KEY"],
                "Content-Type": "application/json"
            },
            json={
                "price_amount": amount_usd,
                "price_currency": "usd",
                "order_id": f"credits_{current_user.user_id}",
                "order_description": f"${amount_usd:.0f} Credit Pack",
                "ipn_callback_url": f"{os.environ['API_URL']}/api/v2/webhooks/nowpayments",
                "success_url": f"{os.environ['FRONTEND_URL']}/credits/success",
                "cancel_url": f"{os.environ['FRONTEND_URL']}/forge"
            }
        )
        data = response.json()

    return {"invoice_url": data["invoice_url"]}
```

**5. NOWPayments IPN Webhook**

```python
@app.post("/api/v2/webhooks/nowpayments")
async def nowpayments_webhook(request: Request):
    """Handle NOWPayments IPN callback."""
    import hmac
    import hashlib

    # 1. Verify HMAC-SHA512 signature (per NOWPayments docs)
    signature = request.headers.get("x-nowpayments-sig")
    body = await request.body()
    body_dict = json.loads(body)

    # Sort keys and create signature
    sorted_body = json.dumps(body_dict, separators=(',', ':'), sort_keys=True)
    expected_sig = hmac.new(
        os.environ["PAYMENTS_IPN_KEY"].encode(),
        sorted_body.encode(),
        hashlib.sha512
    ).hexdigest()

    if signature != expected_sig:
        logger.warning("NOWPayments webhook signature mismatch")
        raise HTTPException(403, "Invalid signature")

    # 2. Check payment status
    if body_dict.get("payment_status") != "finished":
        return {"status": "ignored"}  # Payment not complete yet

    # 3. Extract user_id from order_id (format: "credits_{user_id}")
    order_id = body_dict.get("order_id", "")
    if not order_id.startswith("credits_"):
        logger.error(f"Invalid order_id format: {order_id}")
        raise HTTPException(400, "Invalid order_id")

    user_id = order_id.replace("credits_", "")
    amount_usd = float(body_dict.get("price_amount", 0))
    amount_cents = int(amount_usd * 100)

    # 4. Ensure user has Stripe setup + usage_based subscription
    customer_id = get_or_create_stripe_customer(user_id)
    ensure_usage_based_subscription(user_id, customer_id)

    # 5. Create Stripe Credit Grant
    stripe.billing.CreditGrant.create(
        customer=customer_id,
        name=f"${amount_usd:.0f} Credit Pack (Crypto)",
        applicability_config={'scope': {'price_type': 'metered'}},
        category='paid',
        amount={'type': 'monetary', 'monetary': {'value': amount_cents, 'currency': 'usd'}}
    )

    logger.info(f"Crypto credit purchase: user={user_id}, amount=${amount_usd}")
    return {"status": "success"}
```

### Frontend

**1. Update UpgradeModal.tsx**

Add second payment option for prepaid credits:
- Keep existing "Pay as you go" flow
- Add credit pack selector with amount buttons
- Add Card/Crypto payment method toggle
- Card → calls `/api/v2/credits/purchase` → redirects to Stripe Checkout
- Crypto → calls `/api/v2/credits/crypto-checkout` → redirects to NOWPayments invoice

**2. Update UserProfile.tsx**

Add to dropdown:
- Credit balance display (fetch from `/api/v2/credits/balance`)
- Current period usage (fetch from `/api/v2/billing/usage`)
- "Add Credits" button → opens credit picker modal

**3. Create CreditPicker Component**

Simple component used by both UpgradeModal and UserProfile:
- Amount buttons: $10, $25, $50, $100 (or custom input for Stripe only)
- Payment method: Card | Crypto
- Card → Stripe Checkout redirect
- Crypto → NOWPayments invoice redirect (new tab or same window)

**4. Create Success Page**

Simple `/credits/success` page:
- "Payment received! Credits will appear shortly."
- Auto-redirect to /forge after 3 seconds
- Or poll `/api/v2/credits/balance` and show when updated

---

## NOWPayments Setup

**Already done**:
- [x] Account created
- [x] API keys in .env: `PAYMENTS_IPN_KEY`, `PAYMENTS_API_KEY`, `PAYMENTS_PUBLIC_API_KEY`

**Still needed**:
- [ ] Set IPN Secret Key in Payment Settings (for webhook signature verification)
- [ ] Whitelist our server IP for API calls (if required)

**Note**: We use the **Create Invoice API** instead of static widgets. This allows dynamic amounts and user identification via `order_id`.

---

## Files to Modify

| File | Changes |
|------|---------|
| `ggbot.py` | Add `/credits/purchase`, `/credits/balance`, `/credits/crypto-checkout`, `/webhooks/nowpayments` |
| `ggbot.py` | Update `handle_checkout_completed` for credit purchases |
| `ggbot.py` | Add helper functions: `get_or_create_stripe_customer()`, `ensure_usage_based_subscription()` |
| `frontend/components/UpgradeModal.tsx` | Add credit pack option alongside pay-as-you-go |
| `frontend/app/forge/components/layout/UserProfile.tsx` | Add balance display + "Add Credits" |
| `frontend/components/CreditPicker.tsx` | New - amount selector + payment method |
| `frontend/app/credits/success/page.tsx` | New - success page after payment |
| `frontend/lib/api.ts` | Add `purchaseCredits()`, `cryptoCheckout()`, `getCreditBalance()` |

---

## Implementation Order

**Phase 1: Backend (Stripe)**
1. [ ] Helper: `get_or_create_stripe_customer()` function
2. [ ] Helper: `ensure_usage_based_subscription()` function
3. [ ] Endpoint: `GET /api/v2/credits/balance`
4. [ ] Endpoint: `POST /api/v2/credits/purchase` (Stripe Checkout)
5. [ ] Update: `handle_checkout_completed` for credit purchases

**Phase 2: Backend (Crypto)**
6. [ ] Endpoint: `POST /api/v2/credits/crypto-checkout` (NOWPayments invoice)
7. [ ] Endpoint: `POST /api/v2/webhooks/nowpayments` (IPN handler)

**Phase 3: Frontend**
8. [ ] Component: `CreditPicker.tsx`
9. [ ] Update: `UpgradeModal.tsx` with prepay credits option
10. [ ] Update: `UserProfile.tsx` dropdown with balance + Add Credits
11. [ ] Page: `/credits/success` confirmation page
12. [ ] API: Add methods to `api.ts`

**Phase 4: Testing**
13. [ ] Test: Stripe credit purchase (new user → subscription + credits)
14. [ ] Test: Stripe credit purchase (existing user → just credits)
15. [ ] Test: Crypto credit purchase end-to-end
16. [ ] Test: Balance display and usage in dropdown

---

## Testing Checklist

**Stripe Path**:
- [ ] Free user → prepay credits → becomes usage_based with credits
- [ ] Free user → pay as you go → becomes usage_based (no credits)
- [ ] Usage_based user → add credits → credits added
- [ ] Credit balance displays correctly in dropdown
- [ ] Credits apply to next invoice (run bot, verify)

**Crypto Path**:
- [ ] Create invoice returns valid invoice_url
- [ ] User redirected to NOWPayments, can select crypto
- [ ] IPN webhook receives callback after payment
- [ ] Signature verification passes
- [ ] Credit grant created with correct amount
- [ ] Free user via crypto → subscription + credits created

**Edge Cases**:
- [ ] IPN received multiple times (idempotency)
- [ ] IPN with status != "finished" ignored
- [ ] Invalid signature rejected

---

## Success Criteria

- Users can prepay for credits via card or crypto
- Credits never expire
- Credits automatically apply to metered usage
- Balance visible in user dropdown
- Both free and existing users can purchase
