# Paper Trading Engine 2.0 + Pro Plan Launch - User Communication

**Launch Date**: TBD
**Version**: 2.0
**Type**: Major Platform Update + Monetization Launch

---

## Popup Notification Copy

### Version A: Custom Strategy Users (Bot Still Active)

```
🚀 Welcome to ggbots Pro!

Major Platform Upgrades:
✅ Paper Trading Engine 2.0
   • 5x more accurate leverage calculations
   • Manual position close button
   • Enhanced risk management

⚠️ Important: Your paper account has been reset to $10,000
Your bot configuration is preserved and will continue trading
with our most accurate engine yet.

✨ NEW: ggbots Pro Plan ($29/mo)
Unlock premium features:
• 10 active bots (vs 1 on free)
• 5-minute analysis (vs 1 hour)
• Frontier AI models (GPT-5, DeepSeek R1)
• Telegram signal publishing
• Priority support

🎁 Early Adopter Special: 50% OFF for 6 months
Use code EARLY50 at checkout

[Try Free for 14 Days] [Learn More] [Continue]
```

---

### Version B: Default Strategy Users (Bot Deactivated)

```
🚀 Welcome to ggbots Pro!

Your bot has been deactivated during our platform upgrade.

What's New:
✅ Paper Trading Engine 2.0
   • 5x more accurate leverage calculations
   • Manual position management
   • $10,000 paper account reset

✨ NEW: ggbots Pro Plan ($29/mo)
Unlock premium features:
• 10 active bots (vs 1 on free)
• 5-minute analysis (vs 1 hour)
• Frontier AI models (GPT-5, DeepSeek R1)
• Telegram signal publishing
• Priority support

🎁 Early Adopter Special: 50% OFF for 6 months
Use code EARLY50 at checkout

Next Steps:
1. Customize your trading strategy
2. Reactivate your bot
3. Start trading with our upgraded engine

[Configure Strategy] [Explore Pro Features]
```

---

## Email Communication (Optional)

### Subject Line Options:
1. "🚀 ggbots Pro is Live + Paper Trading Engine 2.0"
2. "Major Update: Introducing ggbots Pro ($29/mo, 50% off for early adopters)"
3. "Your ggbots account has been upgraded"

### Email Body:

```
Hi [User Name],

We're excited to announce two major updates to ggbots:

## 🚀 Paper Trading Engine 2.0

We've completely overhauled our paper trading system with:

✅ Accurate Leverage Calculations
Your leveraged positions now show realistic P&L. 5x leverage = 5x gains (and losses). This prepares you for real trading conditions.

✅ Manual Position Management
Close positions anytime with a single click. Take control when you need it.

✅ Enhanced Risk Management
Improved stop-loss and take-profit execution with correct leverage multipliers.

⚠️ IMPORTANT: Your paper account has been reset to $10,000 to ensure accurate simulation with the new engine.

[Custom Strategy Users Only:]
Your bot configuration is preserved and continues trading automatically.

[Default Strategy Users Only:]
Your bot was deactivated as part of this upgrade. Please customize your strategy and reactivate to continue trading.


## ✨ Introducing ggbots Pro

Take your trading to the next level with our new Pro plan:

| Feature | Free | Pro ($29/mo) |
|---------|------|--------------|
| Active Bots | 1 | 10 |
| Analysis Frequency | 1 hour min | 5 minutes min |
| AI Models | Basic | Frontier (GPT-5, R1) |
| Telegram Publishing | ❌ | ✅ |
| Priority Support | ❌ | ✅ |

🎁 **Early Adopter Offer**: Get 50% OFF for 6 months
Use code **EARLY50** at checkout
14-day free trial included


## What This Means for You

Your paper trading performance will now be accurate and realistic. The previous system didn't properly account for leverage, which means simulated P&L wasn't reflecting true trading outcomes.

With Engine 2.0, you're training with a professional-grade simulator that mirrors real market conditions.


## Ready to Upgrade?

[Try Pro Free for 14 Days] [View Full Comparison]

Questions? Join our Telegram community:
https://t.me/+ndI762EkfcszZTUx

Happy Trading,
The ggbots Team

---

P.S. This is your chance to lock in early adopter pricing at 50% off. The EARLY50 code gives you 6 months at just $14.50/month.
```

---

## In-App Notification Banner (Persistent)

```
🎉 ggbots Pro is live! Get 10 bots, 5-min analysis, and frontier AI models.
[50% OFF Early Adopter Pricing] Use code EARLY50
```

---

## Social Media Announcement (Optional)

### Twitter/X:
```
🚀 ggbots Pro is officially live!

✨ What's included:
• 10 active trading bots
• 5-minute analysis frequency
• Frontier AI models (GPT-5, DeepSeek R1)
• Telegram signal publishing
• Priority support

🎁 Early adopters: 50% OFF for 6 months
Code: EARLY50

Plus: Paper Trading Engine 2.0 with accurate leverage calculations and manual position management.

Try free for 14 days → [link]

#AlgoTrading #CryptoTrading #AITrading
```

---

## FAQ for Users

### Why was my paper account reset?

Our new Paper Trading Engine 2.0 includes critical fixes to leverage calculations. The previous system wasn't properly accounting for leverage multipliers, which meant simulated profits/losses didn't reflect realistic trading outcomes.

Rather than migrate incorrect data, we've reset all accounts to $10,000 to ensure everyone starts with accurate, realistic paper trading.

### Why was my bot deactivated?

Bots using the default strategy template were automatically deactivated during the upgrade. This gives you a fresh start to customize your strategy with our improved system.

Bots with custom strategies remained active and will continue trading with the upgraded engine.

### What happened to my trade history?

Your trade history has been archived and can be provided upon request. However, we recommend starting fresh with the new engine for the most accurate performance tracking.

### Do I need to upgrade to Pro?

No! The free plan still includes:
• 1 active bot
• Full paper trading access
• Basic AI models
• 1-hour minimum analysis frequency

Pro is for users who want to run multiple strategies simultaneously or need faster analysis cycles.

### How do I use the EARLY50 code?

During checkout, you'll see a "Promo Code" field. Enter **EARLY50** to receive 50% off for your first 6 months. This discount applies to both monthly ($14.50/mo) and annual ($139.50/yr) plans.

### What if I don't want to upgrade?

No problem! The free plan works great. The Paper Trading Engine 2.0 improvements apply to all users, free and Pro.

---

## Technical Notes for Support

### Reset Details:
- All paper accounts → $10,000 balance
- All open positions → closed (close_reason: 'system_reset_v2')
- Default strategy bots → state: 'inactive'
- Custom strategy bots → state: 'active' (unchanged)
- Backups created: `paper_*_backup_20251001` tables

### Default Strategy Pattern:
Configs matching: `config_data::text ILIKE '%RSI 1hr below 50%enter long%'`

### Pro Plan Features Gate:
- Check `user_profiles.subscription_tier` = 'ggbase'
- Enforce limits via frontend PermissionGate component
- Backend validation in bot activation endpoints

### Support Escalation:
- Users can't see trade history → We have backups
- Bot won't reactivate → Check config validation, subscription tier
- Billing issues → Stripe Customer Portal access via UserProfile

---

**Document Status**: Draft ready for approval
**Next Steps**:
1. Final approval on messaging
2. Schedule deployment window
3. Coordinate with frontend deployment
4. Monitor user feedback post-launch
