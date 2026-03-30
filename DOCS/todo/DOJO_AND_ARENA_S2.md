# The Dojo & ggArena Season 2 — Complete Design & Implementation Plan

**Status**: SUPERSEDED — Split into [DOJO.md](DOJO.md) (active) + [ARENA_S2_DEFERRED.md](ARENA_S2_DEFERRED.md) (shelved)
**Owner**: Sev
**Created**: 2026-03-26
**Note**: Retained for design discussion history. Do not use for implementation — see the split docs above.

---

## Vision

The Dojo is the always-on competitive environment where AI trading bots train, spar, and earn ratings. It reframes the bot-testing experience using **chess-inspired mechanics**: ELO ratings, 1v1 matches, time controls, and House Bots to challenge.

ggArena seasons become **tournaments within The Dojo** — periodic high-stakes competitions with buy-in entry packages, referral-driven growth, and seat-based triggers.

```
THE DOJO (always on)
├── Bot Rankings (all active bots, ELO-sorted)
├── House Bots (The Arbiter family — Standard, Rapid, Blitz)
├── 1v1 Matches (challenge house bots or other users)
├── ELO Rating Engine (composite score, tiers/belts)
└── ARENA SEASONS (periodic tournaments)
    ├── Entry Package (buy-in → prize pool + credits + webinar)
    ├── Referral System (earn commission per referral)
    ├── Seat-Based Registration (scarcity + urgency)
    └── Competition (21 days, locked strategies, $10k reset)
```

---

## Part 1: The Dojo — Always-On Competitive Environment

### 1.1 Bot Display & Rankings

**Visibility model**: All active paper bots visible by default. Users can **opt out** via a toggle in bot settings (`dojo_visible = false`). This populates the Dojo from day 1 with all ~27 active bots.

**Bot card data** (public, per bot):
- Bot name, AI model, trading pair, frequency
- Current equity, PnL %, win rate, total trades
- ELO rating + tier badge
- Equity sparkline (7d or match-appropriate)
- Active match indicator (if in a 1v1)

**Privacy boundaries** — NOT shown publicly:
- User identity (name, email, profile)
- Strategy text (natural language instructions)
- Specific indicator configurations
- Account balance (only PnL % relative to starting balance)

**Sorting**: Primary sort by ELO rating. Secondary sort by PnL %. Users can toggle.

### 1.2 ELO Rating System

#### Core Formula

Standard ELO with K-factor scaling:

```
Expected score:  E_A = 1 / (1 + 10^((R_B - R_A) / 400))
New rating:      R_A' = R_A + K * (S_A - E_A)
```

K-factor by experience:
- **K=32**: New bots (< 10 rated events)
- **K=24**: Established bots (10-30 events)
- **K=16**: High-rated bots (ELO > 1600 AND > 30 events)

Starting ELO: **1200** (chess convention)

#### Composite Match Score

Match outcomes use a **composite score** rather than pure PnL %. This rewards good strategy, not just lucky swings.

| Factor | Weight | Metric |
|--------|--------|--------|
| **PnL %** | 40% | `(end_equity - start_equity) / start_equity * 100` |
| **Sharpe Ratio** | 25% | `mean(daily_returns) / std(daily_returns) * sqrt(period_days)` |
| **Max Drawdown** | 20% | Inverted: lower drawdown = higher score |
| **Win Rate** | 15% | `wins / total_trades` over match period |

**Weight adjustment by format** (Sharpe needs sufficient data points):

| Factor | Standard (21d) | Rapid (7d) | Blitz (1d) |
|--------|---------------|------------|------------|
| PnL % | 40% | 45% | 60% |
| Sharpe | 25% | 20% | 5% |
| Drawdown | 20% | 20% | 20% |
| Win Rate | 15% | 15% | 15% |

**Score calculation**: Each factor is normalized to 0-1 range relative to the opponent (in 1v1) or the field (in rolling). Weighted sum produces final score 0-1. In 1v1: score > 0.5 = win.

**Edge cases**:
- Neither bot trades during match → draw, no ELO change
- One bot trades, other doesn't → non-trading bot gets score 0 for PnL/win-rate, neutral for drawdown/Sharpe
- Bot deactivated during match → forfeit, opponent wins

#### Rating Types

**Rolling ELO** (passive, weekly):
- Every Sunday midnight UTC, calculate composite scores for all active Dojo bots over trailing 7 days
- Rank all bots 1 to N by composite score
- Swiss-system ELO update: each bot compared against the field median, ELO adjusts based on rank vs expected rank
- Bots with < 7 days active get no rolling update that week

**Match ELO** (active, per 1v1):
- Traditional two-player ELO from explicit challenges
- Updates immediately when match completes

**Season ELO** (tournament):
- Arena competition final standings produce ELO adjustments
- Based on final composite score ranking among all participants

All three sources feed the same ELO number. A bot's rating reflects everything: passive performance, 1v1 results, and tournament history.

#### Tier System

| ELO Range | Tier | Color | Icon |
|-----------|------|-------|------|
| < 1000 | Novice | White | ○ |
| 1000–1199 | Apprentice | Green | ● |
| 1200–1399 | Journeyman | Blue | ◆ |
| 1400–1599 | Expert | Purple | ★ |
| 1600–1799 | Master | Gold | ♛ |
| 1800+ | Grandmaster | Red | ♚ |

### 1.3 House Bots — The Arbiter Family

Platform-owned bots that serve as **benchmarks and sparring partners**. Each is optimized for a specific time format.

| House Bot | Format | Timeframe | Style | Target ELO |
|-----------|--------|-----------|-------|------------|
| **The Arbiter** | Standard (21d) | 4h–1d | Patient, high-conviction, few trades | ~1400+ |
| **The Arbiter: Rapid** | Rapid (7d) | 1h–4h | Medium frequency, balanced risk | ~1300+ |
| **The Arbiter: Blitz** | Blitz (1d) | 5m–15m | Aggressive, scalping-style | ~1200+ |

House bots:
- Flagged with `is_house_bot = true` on configurations table
- Always visible in Dojo (cannot be hidden)
- Featured section at top of Dojo page
- Strategy partially revealed (model, symbol, frequency, indicators — NOT the strategy text)
- Their ELO adjusts naturally from matches (making it meaningful: "I beat a 1450 House Bot")

**Creation**: Sev hand-tunes each variant. Rapid/Blitz may be variations of The Arbiter with adjusted timeframes, position sizing, and strategy prompts.

### 1.4 1v1 Matches

#### Time Controls

| Format | Duration | Starts At | Analogy |
|--------|----------|-----------|---------|
| **Blitz** | 1 day | Next hour boundary | Bullet chess |
| **Rapid** | 7 days | Next midnight UTC | Rapid chess |
| **Standard** | 21 days | Next midnight UTC | Classical chess |

#### Match Lifecycle

```
Challenge → Accept → Active → Complete → ELO Update
                       ↓
                    Forfeit (if bot deactivated)
```

1. **Challenge**: User A selects opponent (House Bot or another user's bot) + format
   - Against House Bots: instant accept (always available)
   - Against users: opponent must accept within 24h or challenge expires
2. **Start**: Both bots' equity is snapshotted at start time
3. **Active**: Both bots run independently. No special handling — just normal bot cycles
4. **Complete**: At end time, scheduler job snapshots final equity, calculates composite scores, determines winner, updates ELO
5. **Forfeit**: If either bot is deactivated during match, the other wins by forfeit

#### Match Limits

- Max **3 active matches** per bot (prevents ELO gaming)
- Minimum **1 hour** between issuing challenges (no spam)
- House Bots can have unlimited concurrent challengers
- Cannot challenge the same bot in the same format while a match is active

---

## Part 2: ggArena Season 2 — The Grand Tournament

### 2.1 Entry Package

**One purchase per user** (not per bot). Includes:

| Component | Allocation | Description |
|-----------|-----------|-------------|
| Prize pool | ~40% | Funds the competition prizes |
| Credits | ~33% | LLM usage credits for bot execution during competition |
| Webinar | ~13% | Access to Sev's strategy-building training sessions |
| Referral reserve | ~13% | Funds referral commissions (flows to prize pool if no referral used) |

**Price**: $50–$100 (exact TBD, working number $75)

**Rules**:
- One entry per user, unlimited bots registered
- No refunds
- Credits are added to user's existing balance
- Webinar access is boolean flag (managed externally — Zoom/Discord)

**Example at $75 with 50 entries ($3,750 total)**:
- Prize pool: $1,500–$2,000
- Credits distributed: $1,250
- Webinar: $500 (platform revenue)
- Referral commissions: $500–$1,000

### 2.2 Referral System

Each user who purchases an entry package gets a **referral code**.

**Mechanics**:
- Referral code format: auto-generated (e.g., `GG-SEV-A3K9`) or user-chosen (e.g., `SEV`)
- Applied at checkout via URL param (`ggbots.ai/arena?ref=SEV`) or manual entry
- Referrer earns fixed $ amount per entry (from the referral reserve allocation)
- Commission tracked per referral, payable as platform credits or future consideration

**Scope**: Arena entry fees only (not platform-wide for now).

**Limits**:
- Cannot self-refer
- One referral code per user
- Referral tracked at purchase time, not retroactive

### 2.3 Seat-Based Registration

Instead of fixed dates, **Season 2 starts when seats fill**.

**Model**: Minimum + maximum seats with a trigger mechanism.

```
Seats available: 50
Minimum to launch: 30

Flow:
1. Dojo launches → seat counter visible ("0/50 seats filled")
2. Users buy entry packages → counter increments
3. At 30 seats → competition date announced (starts 2 weeks later)
4. Remaining 20 seats available during prep window
5. At 50 OR prep window closes → registration locks
6. Competition begins → 21 days
```

**Advantages**:
- No risk of launching with 5 participants
- Scarcity drives urgency ("Only 8 seats left!")
- Referral system has clear driver: "Help fill the seats"
- Flexible timing — competition starts when community is ready

**Display on Dojo page**:
```
┌──────────────────────────────────────────┐
│  🏆 ggArena Season 2                     │
│  ████████████████░░░░░  38/50 seats      │
│  Competition begins when 30+ seats fill   │
│  [Buy Entry Package — $75]               │
│  🔗 Your referral: GG-SEV-A3K9          │
└──────────────────────────────────────────┘
```

**Season config** (updated `core/arena/seasons.py`):
```python
SEASONS = {
    2: {
        'name': 'Season 2',
        'season_id': 2,
        'min_seats': 30,
        'max_seats': 50,
        'prep_window_days': 14,  # days between min-trigger and competition start
        'competition_days': 21,
        'entry_price_cents': 7500,  # $75
        'prize_description': 'Prize pool funded by entry fees.',
        # Dates set dynamically when min_seats hit:
        # 'registration_end', 'competition_start', 'competition_end'
    }
}
```

### 2.4 Competition Mechanics

Same core rules as original S2 plan, with Dojo integration:

1. **Entry**: Buy entry package → registered as S2 entrant
2. **Bot Registration**: Enter any active paper bots (unlimited per user)
3. **Config Lock**: Registered bots' strategy, indicators, timeframes, trade settings frozen
4. **Reset**: All registered bots reset to $10,000 at competition start
5. **Scoring**: Composite score (same as ELO match score), not just PnL %
6. **Activity**: Bot must be active ≥ 18 of 21 days for prize eligibility
7. **Unregister**: Allowed during prep window only (before competition starts)
8. **ELO Impact**: Final standings produce ELO adjustments for all participants

**Prize Distribution** (example with $1,500 pool):

| Place | Share | Amount |
|-------|-------|--------|
| 1st | 45% | $675 |
| 2nd | 25% | $375 |
| 3rd | 15% | $225 |
| 4th–5th | 5% each | $75 |
| 6th–10th | 1% each | $15 |

---

## Part 3: Database Schema

### New Columns on Existing Tables

```sql
-- configurations: Dojo visibility + ELO + house bot flag
ALTER TABLE configurations ADD COLUMN dojo_visible BOOLEAN DEFAULT TRUE;
ALTER TABLE configurations ADD COLUMN elo_rating INTEGER DEFAULT 1200;
ALTER TABLE configurations ADD COLUMN is_house_bot BOOLEAN DEFAULT FALSE;

-- user_profiles: referral code
ALTER TABLE user_profiles ADD COLUMN referral_code TEXT UNIQUE;
```

### New Tables

```sql
-- ELO history: tracks every rating change with reason
CREATE TABLE elo_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES configurations(config_id),
    elo_before INTEGER NOT NULL,
    elo_after INTEGER NOT NULL,
    change INTEGER NOT NULL,
    reason TEXT NOT NULL,           -- 'rolling_weekly', 'match_win', 'match_loss', 'match_draw', 'match_forfeit', 'season_result'
    match_id UUID,                  -- references dojo_matches if from a match
    season_id INTEGER,              -- references season if from tournament
    details JSONB,                  -- composite score breakdown, opponent info, etc.
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_elo_history_config ON elo_history(config_id, created_at DESC);

-- 1v1 matches
CREATE TABLE dojo_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    format TEXT NOT NULL CHECK (format IN ('blitz', 'rapid', 'standard')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'completed', 'cancelled', 'forfeit')),
    -- Participants
    challenger_config_id UUID NOT NULL REFERENCES configurations(config_id),
    opponent_config_id UUID NOT NULL REFERENCES configurations(config_id),
    challenger_user_id UUID NOT NULL,
    opponent_user_id UUID NOT NULL,
    -- Timing
    challenge_expires_at TIMESTAMPTZ,   -- NULL for house bot challenges (auto-accept)
    accepted_at TIMESTAMPTZ,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    -- Start snapshots
    challenger_start_equity NUMERIC,
    opponent_start_equity NUMERIC,
    -- End results
    challenger_end_equity NUMERIC,
    opponent_end_equity NUMERIC,
    challenger_composite_score NUMERIC,
    opponent_composite_score NUMERIC,
    winner_config_id UUID,             -- NULL for draw
    -- ELO deltas
    challenger_elo_before INTEGER,
    challenger_elo_after INTEGER,
    opponent_elo_before INTEGER,
    opponent_elo_after INTEGER,
    -- Metadata
    result_details JSONB,              -- full composite score breakdown
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_dojo_matches_status ON dojo_matches(status) WHERE status IN ('pending', 'active');
CREATE INDEX idx_dojo_matches_challenger ON dojo_matches(challenger_config_id, status);
CREATE INDEX idx_dojo_matches_opponent ON dojo_matches(opponent_config_id, status);

-- Arena entry packages (per-user purchase, not per-bot)
CREATE TABLE arena_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id INTEGER NOT NULL,
    user_id UUID NOT NULL,
    -- Payment
    stripe_payment_intent_id TEXT,
    stripe_checkout_session_id TEXT,
    amount_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'usd',
    -- Package components
    credits_granted NUMERIC NOT NULL,       -- credits added to user balance
    webinar_access BOOLEAN DEFAULT TRUE,
    -- Referral
    referral_code_used TEXT,                 -- code entered at checkout
    referred_by_user_id UUID,               -- who gets commission
    referral_commission_cents INTEGER,       -- amount earned by referrer
    -- Status
    status TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'refunded')),
    purchased_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(season_id, user_id)
);
CREATE INDEX idx_arena_entries_season ON arena_entries(season_id);
CREATE INDEX idx_arena_entries_referrer ON arena_entries(referred_by_user_id);

-- Referral tracking
CREATE TABLE referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_user_id UUID NOT NULL,
    referred_user_id UUID NOT NULL,
    referral_code TEXT NOT NULL,
    campaign TEXT NOT NULL DEFAULT 'arena_s2',   -- what the referral is for
    entry_id UUID REFERENCES arena_entries(id),  -- the purchase that triggered this
    commission_cents INTEGER,                    -- amount earned
    commission_type TEXT DEFAULT 'credits',       -- 'credits', 'cash', 'pending'
    paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign, referred_user_id)           -- one referral per user per campaign
);
CREATE INDEX idx_referrals_referrer ON referrals(referrer_user_id);
```

### Existing Table: `arena_registrations`

Already exists and works for per-bot registration. S2 flow:
1. User buys entry package → `arena_entries` row
2. User registers bots → `arena_registrations` rows (requires matching `arena_entries` row)
3. Config lock check queries `arena_registrations` (no change from current implementation)

---

## Part 4: API Endpoints

### Dojo Endpoints (Public)

```
GET  /api/v2/public/dojo/bots          — All active, visible bots with performance + ELO
GET  /api/v2/public/dojo/stats         — Aggregate stats (total bots, avg ELO, matches today)
GET  /api/v2/public/dojo/bot/{id}      — Single bot detail (expanded card data)
GET  /api/v2/public/dojo/matches       — Recent/active matches
GET  /api/v2/public/dojo/leaderboard   — ELO-sorted rankings with tier badges
```

### Dojo Endpoints (Authenticated)

```
POST /api/v2/dojo/challenge            — Issue a 1v1 challenge
POST /api/v2/dojo/challenge/{id}/accept — Accept a challenge
POST /api/v2/dojo/challenge/{id}/cancel — Cancel pending challenge
GET  /api/v2/dojo/my-matches           — Current user's active/recent matches
PUT  /api/v2/config/{id}/visibility    — Toggle dojo_visible
```

### Arena S2 Endpoints

```
GET  /api/v2/public/arena/season/current   — Season info + seat count + phase
POST /api/v2/arena/entry/checkout          — Create Stripe checkout for entry package
POST /api/v2/arena/entry/webhook           — Stripe webhook for completed purchase
GET  /api/v2/arena/entry/status            — User's entry status for current season
POST /api/v2/arena/season/{id}/register    — Register bot (requires entry)
POST /api/v2/arena/season/{id}/unregister  — Unregister bot (prep window only)
GET  /api/v2/public/arena/season/{id}/leaderboard — Live leaderboard
```

### Referral Endpoints

```
GET  /api/v2/referral/code             — Get user's referral code (auto-generate if none)
GET  /api/v2/referral/stats            — Referral count + commissions earned
```

---

## Part 5: Frontend Architecture

### Page Structure

The `/arena` route becomes the unified Dojo + Arena page:

```
/arena
├── Header (ggbots logo + Dojo branding + nav)
├── Hero ("The Dojo — Where AI Traders Are Forged")
├── Stats Bar (total bots, avg ELO, matches today, active tournament)
│
├── Section: House Bots
│   ├── The Arbiter (Standard) — card with [Challenge] button
│   ├── The Arbiter: Rapid — card with [Challenge] button
│   └── The Arbiter: Blitz — card with [Challenge] button
│
├── Section: Active Matches
│   └── Live 1v1 match cards (challenger vs opponent, time remaining, current scores)
│
├── Section: Dojo Rankings
│   └── Bot cards sorted by ELO (tier badge, PnL%, sparkline, match record)
│
├── Section: ggArena Season 2
│   ├── Entry package info + seat counter
│   ├── [Buy Entry Package] button
│   ├── Referral code display
│   └── Rules + prize structure
│
├── Section: Past Seasons
│   └── S1 results (existing leaderboard, toggle)
│
└── Footer
```

### Key Components (New or Modified)

| Component | Type | Purpose |
|-----------|------|---------|
| `DojoPage` | Page | Main container, replaces ArenaContent |
| `DojoBotCard` | Component | Bot card with ELO tier badge, sparkline, challenge button |
| `HouseBotSection` | Component | Featured House Bots with challenge CTA |
| `MatchCard` | Component | Active 1v1 match display (vs framing, timer, scores) |
| `ChallengeModal` | Component | Select format + confirm challenge |
| `EloTierBadge` | Component | Colored tier badge with icon |
| `SeatCounter` | Component | Progress bar for Arena entry seats |
| `EntryPackageModal` | Component | Purchase flow (Stripe checkout redirect) |
| `ReferralSection` | Component | User's referral code + stats |

### Forge Integration

When a bot is registered for an Arena season:
- Banner: "Locked for ggArena Season 2" (existing plan, unchanged)
- Disabled edit controls
- Unregister button during prep window only

New addition:
- Dojo visibility toggle in bot settings
- ELO rating display on bot card in Forge
- Active matches indicator

---

## Part 6: Backend Architecture

### ELO Calculation Service

New module: `core/arena/elo.py`

```python
# core/arena/elo.py

def calculate_composite_score(config_id, start_time, end_time, format):
    """Calculate composite match score for a bot over a time period."""
    # Query trades, snapshots, positions for the period
    # Calculate PnL %, Sharpe, max drawdown, win rate
    # Apply format-specific weights
    # Return normalized 0-1 score

def update_elo(winner_rating, loser_rating, k_factor=24, draw=False):
    """Standard ELO update for a match result."""
    # Returns (new_winner_rating, new_loser_rating)

def weekly_rolling_update():
    """Swiss-system ELO update for all active Dojo bots."""
    # Called by scheduler every Sunday midnight UTC
    # Ranks all bots by trailing-7d composite score
    # Updates ELO based on rank vs expected rank

def get_k_factor(config_id):
    """K-factor based on bot experience level."""
    # Count rated events from elo_history
    # K=32 for <10, K=24 for 10-30, K=16 for >30 AND >1600 ELO
```

### Match Lifecycle Service

New module: `core/arena/matches.py`

```python
# core/arena/matches.py

async def create_challenge(challenger_config_id, opponent_config_id, format):
    """Create a new match challenge."""
    # Validate: max 3 active, no duplicate, bot is active + visible
    # If opponent is house bot: auto-accept, set start time
    # If opponent is user bot: set expires_at = now + 24h, status = pending

async def accept_challenge(match_id, user_id):
    """Accept a pending challenge."""
    # Validate ownership, set start time based on format

async def complete_match(match_id):
    """Called by scheduler when match end time reached."""
    # Snapshot final equity
    # Calculate composite scores
    # Determine winner
    # Update ELO for both bots
    # Record elo_history entries

async def check_forfeits():
    """Called periodically — check if any active match has a deactivated bot."""
    # Query active matches where either bot.state != 'active'
    # Forfeit: opponent wins, ELO adjusts
```

### Scheduler Jobs

Add to `ggbot_scheduler.py`:

```python
# Weekly rolling ELO (Sundays midnight UTC)
scheduler.add_job(weekly_rolling_elo, CronTrigger(day_of_week='sun', hour=0, minute=0))

# Match completion checker (every 5 minutes)
scheduler.add_job(check_match_completions, IntervalTrigger(minutes=5))

# Forfeit checker (every 5 minutes, same job or combined)
scheduler.add_job(check_match_forfeits, IntervalTrigger(minutes=5))
```

---

## Part 7: Implementation Phases

### Phase 1: The Dojo Foundation
**Scope**: Public bot display, basic Dojo page, opt-out visibility

**Backend**:
- Add `dojo_visible` column to configurations
- Add `elo_rating` column (default 1200, display only initially)
- Add `is_house_bot` column
- `GET /api/v2/public/dojo/bots` endpoint (active + visible + paper bots with performance)
- `GET /api/v2/public/dojo/stats` endpoint
- `PUT /api/v2/config/{id}/visibility` endpoint

**Frontend**:
- Rebrand Arena page → The Dojo
- Bot ranking grid with ELO tier badges (placeholder 1200)
- House Bot section (The Arbiter, others as "Coming Soon")
- Preserve S1 results as "Past Seasons" toggle

**Dependencies**: None — can start immediately

### Phase 2: ELO Engine
**Scope**: Real ELO calculations, rolling weekly updates, history tracking

**Backend**:
- Create `elo_history` table
- `core/arena/elo.py` — composite score calculation + ELO update functions
- Weekly rolling ELO scheduler job
- `GET /api/v2/public/dojo/leaderboard` with real ELO sorting

**Frontend**:
- Real ELO values replace placeholder
- ELO history on expanded bot card (sparkline of rating over time)

**Dependencies**: Phase 1 (bots need to be displayed before ratings matter)

### Phase 3: House Bots
**Scope**: Create and deploy The Arbiter family

**Work**:
- Sev creates/tunes The Arbiter Standard config
- Create Rapid and Blitz variants (adjusted timeframe, sizing, strategy)
- Mark as `is_house_bot = true`
- Featured display on Dojo page

**Dependencies**: Phase 1 (display infrastructure)

### Phase 4: 1v1 Matches
**Scope**: Challenge system, match lifecycle, match display

**Backend**:
- Create `dojo_matches` table
- `core/arena/matches.py` — challenge/accept/complete/forfeit logic
- Challenge + accept + cancel endpoints
- Match completion scheduler job
- Forfeit detection job

**Frontend**:
- Challenge button on bot cards + House Bot section
- ChallengeModal (select format, confirm)
- Active match cards (vs display, timer, live scores)
- Match history on expanded bot card
- Incoming challenge notifications (could be simple polling or SSE)

**Dependencies**: Phase 2 (ELO engine needed for match results)

### Phase 5: Arena S2 Entry Package
**Scope**: Buy-in system with Stripe, seat counter, credits allocation

**Backend**:
- Create `arena_entries` table
- Stripe checkout integration for entry package
- Webhook handler for completed purchases
- Credit allocation on purchase
- Seat counter logic (min/max trigger)
- Season date computation (dynamic based on seat trigger)
- Entry status endpoint

**Frontend**:
- Entry package section on Dojo page
- Seat counter with progress bar
- Buy button → Stripe checkout
- Entry confirmation UI
- Webinar access indicator in user profile

**Dependencies**: Phase 1 (Dojo page exists). Independent of Phases 2-4.

### Phase 6: Referral System
**Scope**: Referral codes, tracking, commission display

**Backend**:
- Add `referral_code` column to user_profiles
- Create `referrals` table
- Auto-generate referral code on first request
- Track referral at entry package purchase
- Commission calculation
- Referral stats endpoint

**Frontend**:
- Referral code display + copy button
- Referral link with `?ref=CODE` parameter
- Stats: referrals count, commissions earned
- Apply referral code at checkout

**Dependencies**: Phase 5 (entry package purchase must exist)

### Phase 7: Arena S2 Competition
**Scope**: Registration flow, config lock, reset, leaderboard, results

**Backend**:
- Registration endpoint updates (require `arena_entries` row)
- Config lock enforcement (existing, may need updates)
- Competition start: bulk reset script execution
- Active days calculation
- Live leaderboard endpoint (composite score, not just PnL)
- Season ELO adjustments at competition end
- Results snapshot + prize allocation

**Frontend**:
- Bot registration UI in Forge (modal, lock badge)
- Live leaderboard during competition
- Results page post-competition
- ELO changes displayed

**Dependencies**: Phases 5 + 6 (entry + referral). Phase 2 for ELO impact.

---

## Part 8: Open Questions

1. **Entry package price**: $50, $75, or $100? Affects prize pool size and accessibility.

2. **Seat numbers**: 50 max / 30 min, or different? Consider current user base (350 users, 28 paid, ~10 DAU).

3. **Prize distribution**: Fixed tiers (top 10) or dynamic based on entries? What about non-cash prizes (e.g., free months, "Grandmaster" title)?

4. **Referral payout**: Credits only, or real money? If credits, what ratio?

5. **Webinar logistics**: Platform (Zoom? Discord?), schedule, recording access?

6. **The Arbiter configs**: Does The Arbiter exist already as a running bot? Need to create Rapid/Blitz variants — Sev tunes these manually?

7. **S1 staking/betting**: The BetModal + Web3 providers (wagmi/RainbowKit) are still in the Arena code. Remove entirely for the Dojo, or preserve for future use? If removing, the page gets significantly lighter (no Web3 bundle).

8. **Composite score display**: Show the full breakdown (PnL%, Sharpe, drawdown, win rate) to users, or just the final ELO? Transparency builds trust but adds complexity.

9. **Mobile**: Current Arena page is responsive. Dojo will have more data — ensure bot cards work well on mobile (collapsed by default, expandable).

10. **DGClaw Arena**: There's a separate Virtuals DGClaw arena integration in progress (`trading/virtuals/`). Should the Dojo acknowledge this or keep them completely separate? They serve different purposes (Dojo = engagement/ratings, DGClaw = on-chain ACP volume).

---

## Revision History

- 2026-03-26: Initial design from discussion (Sev + Claude Code session)
