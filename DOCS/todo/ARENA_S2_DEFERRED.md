# ggArena Season 2 — Deferred Plan

**Status**: DEFERRED — Virtuals Degen Arena ($100K/week) is the active competitive event. Revisit when timing is right.
**Owner**: Sev
**Created**: 2026-03-26
**Previous Plans**: [ARENA_SEASON2.md](ARENA_SEASON2.md) (original), [DOJO_AND_ARENA_S2.md](DOJO_AND_ARENA_S2.md) (combined, superseded)
**Active Focus**: [DOJO.md](DOJO.md) — The Dojo (always-on competitive environment)

---

## Context

Season 2 was originally planned for Apr 1-28, 2026. Virtuals Protocol launched the Degen Arena with $100K/week backing for AI trading agents. ggbots integrated with DGClaw for that competition. Running a self-hosted tournament with buy-in while Virtuals offers $100K/week externally doesn't make strategic sense right now.

The Dojo (ELO, 1v1 matches, House Bots) is being built as the always-on home base. Arena S2 can launch as a tournament within the Dojo when:
- The Dojo has an established user base with meaningful ELO ratings
- Virtuals Degen Arena winds down or ggbots wants its own event
- Entry package + referral system would drive meaningful growth

---

## Preserved Design (Ready to Build When Needed)

### Entry Package ($50-100)

One purchase per user, unlimited bots. Bundle:
- ~40% → Prize pool
- ~33% → LLM credits for competition
- ~13% → Webinar access (Sev's strategy-building sessions)
- ~13% → Referral commission reserve

No refunds. Credits added to existing balance. Webinar managed externally.

### Referral System

- Auto-generated or user-chosen referral codes
- Applied at checkout via URL param (`?ref=CODE`) or manual entry
- Referrer earns fixed $ per entry from referral reserve
- Scope: Arena entry fees only (not platform-wide)
- Cannot self-refer, one code per user

### Seat-Based Registration

Instead of fixed dates, Season 2 starts when seats fill:
- 50 max seats, 30 minimum to trigger
- At 30 seats: competition date announced (2 weeks out)
- Remaining seats available during prep window
- Creates scarcity + urgency, referral has clear driver

### Competition Mechanics

1. Buy entry package → `arena_entries` row
2. Register bots → `arena_registrations` rows (requires entry)
3. Config lock on registered bots
4. All bots reset to $10,000 at competition start
5. Scoring: composite score (PnL 40%, Sortino 25%, Drawdown 20%, Win Rate 15%)
6. Activity requirement: 18 of 21 days
7. ELO adjustments from final standings

### Database Tables (Not Yet Created)

```sql
-- Arena entry packages (per-user purchase)
CREATE TABLE arena_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id INTEGER NOT NULL,
    user_id UUID NOT NULL,
    stripe_payment_intent_id TEXT,
    stripe_checkout_session_id TEXT,
    amount_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'usd',
    credits_granted NUMERIC NOT NULL,
    webinar_access BOOLEAN DEFAULT TRUE,
    referral_code_used TEXT,
    referred_by_user_id UUID,
    referral_commission_cents INTEGER,
    status TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'refunded')),
    purchased_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(season_id, user_id)
);

-- Referral tracking
CREATE TABLE referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_user_id UUID NOT NULL,
    referred_user_id UUID NOT NULL,
    referral_code TEXT NOT NULL,
    campaign TEXT NOT NULL DEFAULT 'arena_s2',
    entry_id UUID REFERENCES arena_entries(id),
    commission_cents INTEGER,
    commission_type TEXT DEFAULT 'credits',
    paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign, referred_user_id)
);

-- user_profiles addition
ALTER TABLE user_profiles ADD COLUMN referral_code TEXT UNIQUE;
```

### API Endpoints (Not Yet Built)

```
POST /api/v2/arena/entry/checkout          — Stripe checkout for entry package
POST /api/v2/arena/entry/webhook           — Stripe webhook for completed purchase
GET  /api/v2/arena/entry/status            — User's entry status
GET  /api/v2/referral/code                 — Get/generate referral code
GET  /api/v2/referral/stats                — Referral count + commissions
```

### Existing Infrastructure (Already Built)

- `arena_registrations` table (exists, correct schema)
- `core/arena/seasons.py` (season constants + phase logic)
- Register/unregister endpoints in `ggbot.py` (lines 3038-3187)
- Config lock check on PUT /config (line 657-665)
- `scripts/arena_reset.py` (supports S2)
- Frontend: S1 leaderboard, countdown, rules section

---

## Revision History

- 2026-03-26: Extracted from combined plan. Arena S2 deferred in favor of Dojo-first approach + Virtuals Degen Arena.
