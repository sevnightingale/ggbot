# Resend Email Integration Guide

## Current Status (2025-10-11)

**✅ Phase 1 Complete - Welcome Emails**
- Welcome emails automatically sent to new users on signup
- 189/261 existing users synced to Resend audience
- Contact management fully operational

**📋 Phase 2 Pending - Additional Notifications**
- Trade notification templates ready (not yet integrated)
- Signal alert templates ready (not yet integrated)
- Generic notification templates ready (not yet integrated)

**Integration Points for Phase 2:**
- Trade notifications: Hook into `trading/paper/supabase_service.py` after trade execution
- Signal alerts: Hook into `decision/engine_v2.py` for high-confidence signals
- See "Automation Integration" section below for implementation examples

---

## Overview

ggbots now integrates with Resend for automated email notifications and user contact management. This integration enables:

- **Contact Syncing**: Automatic sync of Supabase users to Resend audiences
- **Welcome Emails**: Automated onboarding emails for new users
- **Trade Notifications**: Real-time alerts when bots execute trades
- **Signal Alerts**: High-confidence trading signal notifications
- **Generic Notifications**: Flexible system for any notification type

## Setup

### 1. Environment Configuration

**✅ Already configured** in `.env`:
```bash
RESEND_API_KEY=<configured>
RESEND_AUDIENCE_ID=4498393a-db21-4a63-8d69-1f56e3f2c52c
```

### 2. Audience Setup

**✅ Already completed** - Using existing "General" audience in Resend dashboard.

If you need to create a new audience or check existing ones:

```bash
# List existing audiences
python scripts/sync_resend_contacts.py --list-audiences

# Create a new audience (if needed)
python scripts/sync_resend_contacts.py --create-audience --audience-name "ggbots Users"
```

### 3. User Sync Status

**✅ Initial sync completed** - 189 out of 261 users successfully synced to Resend audience.

72 users failed due to Resend's rate limit (2 req/sec). To retry failed syncs:

```bash
# Activate environment
source .venv/bin/activate

# Re-run sync (will update existing, add missing)
python scripts/sync_resend_contacts.py
```

This will:
- Skip already-synced users
- Attempt to sync previously failed users
- Report updated statistics

## Usage

### Python Service API

#### Contact Management

```python
from core.services.resend_service import resend_service

# Add a contact
resend_service.add_contact(
    email="user@example.com",
    first_name="Jane",
    last_name="Doe"
)

# Sync single user from Supabase
resend_service.sync_user_to_resend(
    user_id="user-uuid",
    email="user@example.com"
)

# Sync all users
stats = resend_service.sync_all_users_to_resend()
print(f"Synced {stats['success_count']}/{stats['total']} users")
```

#### Send Emails

```python
from core.services.resend_service import resend_service

# Welcome email
resend_service.send_welcome_email(
    user_email="user@example.com",
    first_name="Jane"
)

# Trade notification
resend_service.send_trade_notification(
    user_email="user@example.com",
    trade_data={
        "symbol": "BTC/USD",
        "side": "BUY",
        "size": 0.1,
        "price": 45000.00,
        "confidence": 0.82,
        "config_name": "My Trading Bot"
    }
)

# Signal alert
resend_service.send_signal_alert(
    user_email="user@example.com",
    signal_data={
        "symbol": "ETH/USD",
        "direction": "LONG",
        "confidence": 0.78,
        "indicators": ["RSI oversold", "MACD bullish cross", "Volume spike"],
        "reasoning": "Strong bullish momentum with confirming indicators"
    }
)

# Generic notification
resend_service.send_generic_notification(
    user_email="user@example.com",
    title="System Update",
    message="<p>We've upgraded our AI models for better performance.</p>",
    action_text="Learn More",
    action_url="https://app.ggbots.ai/updates",
    notification_type="info"
)
```

## Email Templates

### Available Templates

1. **Welcome Email** (`core/email_templates/welcome_email.py`)
   - Sent to new users after signup
   - Includes getting started steps
   - Links to dashboard and docs

2. **Trade Notification** (`core/email_templates/trade_notification.py`)
   - Real-time trade execution alerts
   - Shows symbol, side, size, price, confidence
   - Links to position details

3. **Signal Alert** (`core/email_templates/signal_alert.py`)
   - High-confidence trading signals
   - Includes AI reasoning and indicators
   - Confidence-based badge colors

4. **Generic Notification** (`core/email_templates/generic_notification.py`)
   - Flexible template for any notification
   - Supports custom actions/buttons
   - Multiple notification types (info, success, warning, error)

### Template Structure

All templates extend the base template (`core/email_templates/base_template.py`) which provides:
- Consistent ggbots branding
- Responsive design
- Gradient header
- Professional styling
- Footer with links and unsubscribe

### Customizing Templates

Templates are simple Python functions that return `(subject, html)` tuples:

```python
def create_my_template(data):
    content = f"""
        <h2>My Custom Email</h2>
        <p>Content here: {data['field']}</p>
    """

    subject = "My Subject"
    return subject, render_email(content, subject)
```

## Automation Integration

### Welcome Email on Signup ✅ ACTIVE

**Already integrated** in `core/services/user_service.py` at line 61-74.

Welcome emails automatically send when new users sign up via the `get_or_create_profile()` method:

```python
# From core/services/user_service.py (ALREADY IMPLEMENTED)
self._log.info(f"Created new user profile for {user_id}")

# Send welcome email and sync to Resend (async, don't block on failure)
try:
    from core.services.resend_service import resend_service

    # Sync user to Resend audience
    resend_service.sync_user_to_resend(user_id, email)

    # Send welcome email
    resend_service.send_welcome_email(email)

    self._log.info(f"Sent welcome email to {email}")
except Exception as email_error:
    # Don't fail user creation if email fails
    self._log.warning(f"Failed to send welcome email to {email}: {email_error}")
```

### Trade Notifications ⏳ READY (Not Yet Integrated)

**Integration point**: `trading/paper/supabase_service.py` after trade execution

Example implementation:

```python
from core.services.resend_service import resend_service

async def after_trade_execution(user_id: str, trade_data: dict):
    """Called after a trade is executed."""

    # Get user email from database
    email = get_user_email(user_id)

    # Send notification
    resend_service.send_trade_notification(email, trade_data)
```

### Signal Alerts ⏳ READY (Not Yet Integrated)

**Integration point**: `decision/engine_v2.py` for high-confidence signals

Example implementation:

```python
from core.services.resend_service import resend_service

async def on_high_confidence_signal(user_id: str, signal_data: dict):
    """Called when a high-confidence signal is detected."""

    # Only notify if confidence is above threshold
    if signal_data["confidence"] >= 0.75:
        email = get_user_email(user_id)
        resend_service.send_signal_alert(email, signal_data)
```

## Testing

### Test Suite

Run the comprehensive test suite:

```bash
source .venv/bin/activate
python scripts/test_resend.py
```

This tests:
- Audience operations (list, create, get)
- Contact operations (create, read, update, delete)
- User sync functionality

### Manual Testing

Test individual operations:

```python
from core.services.resend_service import resend_service

# List audiences
audiences = resend_service.list_audiences()
for aud in audiences:
    print(f"{aud['name']}: {aud['id']}")

# Test contact creation
resend_service.add_contact(
    email="test@example.com",
    first_name="Test",
    last_name="User"
)

# Test email sending
resend_service.send_welcome_email("test@example.com", "Test")
```

## Utility Scripts

### `scripts/sync_resend_contacts.py`

Comprehensive sync utility:

```bash
# Create audience and sync
python scripts/sync_resend_contacts.py --create-audience

# Just sync (requires RESEND_AUDIENCE_ID in .env)
python scripts/sync_resend_contacts.py

# List existing audiences
python scripts/sync_resend_contacts.py --list-audiences

# Create with custom name
python scripts/sync_resend_contacts.py --create-audience --audience-name "Production Users"
```

### `scripts/test_resend.py`

Test suite for Resend integration:

```bash
python scripts/test_resend.py
```

## Important Notes

### Email Sender Domain

The default sender is `noreply@message.ggbots.ai`. The domain `message.ggbots.ai` must be:
1. Verified in Resend
2. Configured with DNS records (SPF, DKIM, DMARC)
3. Or use a different verified sender email

If using a different domain, update in `resend_service.py`:

```python
def send_email(self, to, subject, html, from_email="noreply@yourdomain.com"):
    # ...
```

### Rate Limits

Resend has rate limits on the free tier. Monitor usage and upgrade as needed:
- Free: 100 emails/day
- Pro: 50,000 emails/month

### User Preferences

Consider adding email preferences to `user_profiles` table:

```sql
ALTER TABLE user_profiles
ADD COLUMN email_notifications_enabled BOOLEAN DEFAULT TRUE,
ADD COLUMN email_trade_alerts BOOLEAN DEFAULT TRUE,
ADD COLUMN email_signal_alerts BOOLEAN DEFAULT TRUE;
```

Then check preferences before sending:

```python
def should_send_email(user_id, email_type):
    profile = get_user_profile(user_id)

    if not profile.email_notifications_enabled:
        return False

    if email_type == "trade" and not profile.email_trade_alerts:
        return False

    return True
```

## Next Steps

### Phase 1 (Complete)
- ✅ Created audience and configured environment
- ✅ Synced 189/261 users to Resend
- ✅ Integrated welcome emails on signup
- ✅ Tested functionality with test suite

### Phase 2 (Future Work)
1. **Retry Failed User Syncs**: Re-run `sync_resend_contacts.py` to sync remaining 72 users
2. **Integrate Trade Notifications**:
   - Add call to `resend_service.send_trade_notification()` in trading service after execution
   - Determine which trades should trigger emails (all? winning only? configurable per user?)
3. **Integrate Signal Alerts**:
   - Add call to `resend_service.send_signal_alert()` in decision engine
   - Set confidence threshold (75%? 80%? user-configurable?)
4. **User Preferences** (optional):
   - Add email notification preferences to `user_profiles` table
   - Allow users to opt-in/out of different notification types
5. **Monitor & Optimize**:
   - Track email delivery metrics in Resend dashboard
   - Monitor rate limits and usage
   - Gather user feedback on email frequency/content

## Troubleshooting

### "No RESEND_AUDIENCE_ID configured"

Create an audience first:
```bash
python scripts/sync_resend_contacts.py --create-audience
```

Then add the ID to `.env`.

### "Failed to send email"

Check:
1. RESEND_API_KEY is valid
2. Sender domain is verified in Resend
3. Check Resend dashboard for detailed error logs

### "Contact not found"

Sync the user first:
```python
resend_service.sync_user_to_resend(user_id, email)
```

### Import Errors

Ensure virtual environment is activated:
```bash
source .venv/bin/activate
```

## Support

For Resend-specific issues:
- Resend Docs: https://resend.com/docs
- Resend Dashboard: https://resend.com/dashboard

For ggbots integration issues:
- Check logs in `logs/ggbot.log`
- Review this guide
- Contact dev team
