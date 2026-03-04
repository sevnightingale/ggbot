# NOWPayments Crypto Payments — Integration Guide

How to accept cryptocurrency payments using NOWPayments' hosted invoice flow with IPN (Instant Payment Notification) webhooks. Based on a production implementation handling real payments.

---

## How It Works

```
User clicks "Pay with Crypto"
    │
    ▼
Your backend creates an invoice via NOWPayments API
    │
    ▼
User is redirected to NOWPayments hosted payment page
    │  (they pick their crypto, send payment)
    ▼
NOWPayments sends IPN webhook to your server
    │  (HMAC-SHA512 signed, retried on failure)
    ▼
Your webhook handler verifies signature, processes payment
    │
    ▼
User redirected to your success_url
```

NOWPayments handles all the crypto complexity — wallet generation, blockchain monitoring, confirmations, exchange rate locking. You just create invoices and handle webhooks.

---

## Prerequisites

1. **NOWPayments account**: https://nowpayments.io — sign up and get approved
2. **API Key**: Settings → API Keys → generate one
3. **IPN Secret**: Settings → IPN → set a secret key (used for webhook signature verification)
4. **Publicly accessible webhook URL**: NOWPayments must be able to POST to your server

---

## Environment Variables

```bash
NOWPAYMENTS_API_KEY=your-api-key-here
NOWPAYMENTS_IPN_SECRET=your-ipn-secret-here
FRONTEND_URL=https://yourapp.com
```

---

## Step 1: Create Invoice Endpoint

When the user wants to pay with crypto, your backend creates a NOWPayments invoice and returns the payment URL.

```python
import httpx
import os
from datetime import datetime

@app.post("/api/crypto-checkout")
async def create_crypto_checkout(amount_usd: float, user_id: str):
    """Create a NOWPayments invoice for crypto payment."""

    api_key = os.environ["NOWPAYMENTS_API_KEY"]

    # Build a unique order_id that encodes everything you need
    # to process the payment later (webhook only gives you this string back)
    amount_cents = int(amount_usd * 100)
    timestamp = int(datetime.now().timestamp())
    order_id = f"order_{user_id}_{amount_cents}_{timestamp}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.nowpayments.io/v1/invoice",
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "price_amount": amount_usd,
                "price_currency": "usd",
                "order_id": order_id,
                "order_description": f"${amount_usd:.0f} Purchase",
                "ipn_callback_url": "https://yourapi.com/api/webhooks/nowpayments",
                "success_url": f"{os.environ['FRONTEND_URL']}/payment/success",
                "cancel_url": f"{os.environ['FRONTEND_URL']}/payment/cancel"
            },
            timeout=30.0
        )

        if response.status_code != 200:
            raise HTTPException(500, "Crypto payment service error")

        data = response.json()

    # Return the hosted payment page URL
    return {"invoice_url": data["invoice_url"]}
```

**Key points:**
- `price_currency` is always `"usd"` — NOWPayments handles the crypto conversion
- `order_id` is your lifeline — encode user_id and amount into it because the webhook only sends this string back to identify the payment
- `ipn_callback_url` must be publicly accessible (no localhost)
- `success_url` / `cancel_url` are where the user lands after paying or canceling

### Frontend

Redirect the user to the `invoice_url`:

```typescript
async function payWithCrypto(amountCents: number) {
    const response = await fetch('/api/crypto-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount_cents: amountCents })
    })
    const { invoice_url } = await response.json()
    window.location.href = invoice_url  // Redirect to NOWPayments
}
```

---

## Step 2: Webhook Handler

NOWPayments POSTs to your `ipn_callback_url` when payment status changes. The webhook fires multiple times as the payment progresses through statuses.

```python
import hmac
import hashlib
import json

@app.post("/api/webhooks/nowpayments")
async def nowpayments_webhook(request: Request):
    """Handle NOWPayments IPN callback."""

    ipn_secret = os.environ["NOWPAYMENTS_IPN_SECRET"]

    # --- 1. Verify HMAC-SHA512 signature ---
    signature = request.headers.get("x-nowpayments-sig")
    body = await request.body()

    body_dict = json.loads(body)

    # CRITICAL: NOWPayments signs the SORTED, compact JSON
    sorted_body = json.dumps(body_dict, separators=(',', ':'), sort_keys=True)
    expected_sig = hmac.new(
        ipn_secret.encode(),
        sorted_body.encode(),
        hashlib.sha512
    ).hexdigest()

    if signature != expected_sig:
        raise HTTPException(403, "Invalid signature")

    # --- 2. Check payment status ---
    payment_status = body_dict.get("payment_status")

    if payment_status != "finished":
        # Payment still processing — acknowledge but don't fulfill
        # Statuses: waiting, confirming, confirmed, sending, partially_paid, finished, failed, refunded, expired
        return {"status": "ignored", "reason": f"status is {payment_status}"}

    # --- 3. Idempotency check ---
    order_id = body_dict.get("order_id", "")

    processed_key = f"nowpayments:processed:{order_id}"
    existing = redis_client.get(processed_key)
    if existing:
        return {"status": "duplicate", "order_id": order_id}

    # Mark as processing immediately (24h TTL)
    redis_client.setex(processed_key, 86400, "processing")

    # --- 4. Parse order_id to extract your data ---
    # Format: "order_{user_id}_{amount_cents}_{timestamp}"
    parts = order_id.split("_")
    if len(parts) < 3 or parts[0] != "order":
        raise HTTPException(400, "Invalid order_id format")

    user_id = parts[1]
    amount_cents = int(parts[2])

    # --- 5. Fulfill the order ---
    # This is where you do your business logic:
    # - Grant credits
    # - Activate subscription
    # - Unlock content
    # - etc.

    fulfill_order(user_id, amount_cents)

    # --- 6. Mark as completed (30-day TTL for audit trail) ---
    redis_client.setex(processed_key, 86400 * 30, "completed")

    return {"status": "success"}
```

---

## Signature Verification — The Gotcha

This is the part that trips people up. NOWPayments uses HMAC-SHA512, but the input must be **sorted, compact JSON** — not the raw body bytes.

```python
# WRONG — signing raw body
expected_sig = hmac.new(secret, body, hashlib.sha512).hexdigest()

# CORRECT — signing sorted, compact JSON
sorted_body = json.dumps(body_dict, separators=(',', ':'), sort_keys=True)
expected_sig = hmac.new(secret.encode(), sorted_body.encode(), hashlib.sha512).hexdigest()
```

The `separators=(',', ':')` removes all whitespace. The `sort_keys=True` ensures deterministic ordering. Both are required — if either is wrong, every signature will fail.

---

## Payment Statuses

NOWPayments sends webhooks at each status transition:

| Status | Meaning | Action |
|--------|---------|--------|
| `waiting` | Invoice created, waiting for payment | Ignore |
| `confirming` | Payment detected, waiting for confirmations | Ignore |
| `confirmed` | Payment confirmed on blockchain | Ignore (wait for `finished`) |
| `sending` | NOWPayments processing | Ignore |
| `partially_paid` | User sent less than required | Ignore (or handle partial) |
| **`finished`** | **Payment complete** | **Fulfill the order** |
| `failed` | Payment failed | Log, notify user |
| `refunded` | Payment refunded | Reverse fulfillment |
| `expired` | Invoice expired (no payment received) | Log |

**Only fulfill on `finished`.** Everything else is intermediate.

---

## Idempotency — Why It Matters

NOWPayments retries webhooks if your server doesn't respond with 200. Without idempotency, a network timeout could cause you to grant credits twice.

The pattern:

```
1. Webhook arrives
2. Check Redis: "Have I processed this order_id before?"
   - YES → Return 200 immediately (duplicate)
   - NO  → Set "processing" flag in Redis (24h TTL)
3. Fulfill the order
4. Set "completed" flag in Redis (30-day TTL)
```

Two TTL stages:
- **"processing" (24h)**: Prevents duplicates during fulfillment. Short TTL so if your server crashes mid-processing, a retry after 24h can re-attempt.
- **"completed" (30d)**: Audit trail. You can check Redis to verify any order was processed.

---

## Order ID Design

The `order_id` is the only way to link a webhook back to a user. Design it carefully.

```
Format: {prefix}_{user_id}_{amount_cents}_{unix_timestamp}

Example: order_b29178ce-9205-4e86-a0f9-5b7dfab29e35_1000_1770177090
         └─────┘ └──────────────────────────────────┘ └──┘ └────────┘
         prefix          user UUID                   $10   unix ts
```

**Why encode amount in the order_id?** Because you should never trust the amount from the webhook body for fulfillment. Encode it in the order_id at creation time, then parse it back at fulfillment time. The webhook body tells you what the user *actually paid* in crypto — the order_id tells you what they *should have paid*.

**Why add a timestamp?** Uniqueness. If the same user buys the same amount twice, the order_ids must be different or idempotency will block the second purchase.

---

## Webhook Body (Example)

What NOWPayments sends to your IPN endpoint:

```json
{
    "payment_id": 5746839471,
    "invoice_id": 5746839470,
    "payment_status": "finished",
    "pay_address": "0x1234...abcd",
    "payin_extra_id": null,
    "price_amount": 10,
    "price_currency": "usd",
    "pay_amount": 0.003842,
    "actually_paid": 0.003842,
    "pay_currency": "eth",
    "order_id": "order_b29178ce_1000_1770177090",
    "order_description": "$10 Purchase",
    "purchase_id": "6234567890",
    "outcome_amount": 9.75,
    "outcome_currency": "usd"
}
```

Useful fields:
- `payment_status` — the only field that determines your action
- `order_id` — your encoded metadata
- `actually_paid` — what the user sent (in crypto)
- `pay_currency` — which crypto they used
- `outcome_amount` — what you receive after NOWPayments fees (in USD)

---

## Testing

### Sandbox Mode

NOWPayments has a sandbox environment:
- API: `https://api-sandbox.nowpayments.io/v1/invoice`
- Dashboard: `https://sandbox.nowpayments.io`

Use sandbox API key for testing. Payments are simulated — no real crypto needed.

### Manual Webhook Testing

If you need to test the webhook without making a real payment, send a POST with a valid signature:

```python
import hmac, hashlib, json, requests

ipn_secret = "your-ipn-secret"
body = {
    "payment_status": "finished",
    "order_id": "order_testuser_1000_1234567890",
    "price_amount": 10,
    "price_currency": "usd"
}

sorted_body = json.dumps(body, separators=(',', ':'), sort_keys=True)
sig = hmac.new(ipn_secret.encode(), sorted_body.encode(), hashlib.sha512).hexdigest()

requests.post(
    "http://localhost:8000/api/webhooks/nowpayments",
    json=body,
    headers={"x-nowpayments-sig": sig}
)
```

---

## Checklist

- [ ] NOWPayments account created and approved
- [ ] API key and IPN secret in environment variables
- [ ] Invoice creation endpoint working
- [ ] Webhook endpoint publicly accessible (not behind auth)
- [ ] HMAC-SHA512 signature verification with sorted compact JSON
- [ ] Idempotency via Redis (or database) to prevent double fulfillment
- [ ] Only fulfilling on `payment_status == "finished"`
- [ ] Order ID encodes user identity and amount
- [ ] Error handling for network timeouts, invalid signatures, malformed bodies
- [ ] Tested with sandbox before going live
