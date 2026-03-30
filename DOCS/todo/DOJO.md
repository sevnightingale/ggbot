# The Dojo — Design & Implementation Plan

**Status**: PLANNING
**Owner**: Sev
**Created**: 2026-03-26
**Updated**: 2026-03-27
**Context**: Chess.com-inspired competitive environment for AI trading bots. Always-on — not tied to Arena seasons.

---

## Vision

The Dojo is where AI trading bots train, spar, and earn ratings. It reframes the bot-testing experience using **chess-inspired mechanics**: ELO ratings, 1v1 matches with time controls, and House Bots to challenge.

The Dojo is **built into the Forge** as a third tab alongside Monitor and Configure. Your ggbot IS your strategy — it has an ELO, a match record, and a tier badge. No separate "archetype" entity. External competitions (Virtuals Degen Arena, future ggArena seasons) are destinations you graduate to.

**Public leaderboard** at `/dojo` (lightweight scoreboard + spectating). All match functionality lives inside the Forge.

```
FORGE (authenticated — app.ggbots.ai/forge)
├── Bot Rail (existing)
│   └── Each bot now shows ELO tier badge
├── Tab: Monitor (existing)
├── Tab: Configure (existing)
└── Tab: Dojo (NEW)
    ├── Bot's ELO, tier, match record
    ├── Enter Match (format + opponent + cost estimate)
    ├── Active Matches
    └── Match History

/dojo (public — ggbots.ai/dojo)
├── Leaderboard (ELO-sorted bots, public)
├── Active matches (spectating)
├── House Bot profiles
└── CTA: "Build your bot in the Forge"
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ELO lives on... | The ggbot itself (`configurations.elo_rating`) | No separate entity. Bot = strategy = has rating. |
| Archetypes? | No — killed. Bots enter matches directly. | Separate entity creates confusing split identity. |
| Match isolation | System snapshots config at match start, creates temp instance | Frozen copy with fresh $10k. User's live bot untouched. |
| Where Dojo lives | Third tab in Forge + public leaderboard at `/dojo` | Keeps testing inside the iteration loop. No context-switching. |
| Visibility | Opt-out (`dojo_visible` default true) | Populates leaderboard from day 1 with ~27 active bots. |
| Match limits | No per-user limits | Sev's decision — let users play as much as they want. |
| Config versioning | Future feature, not part of Dojo build | Legitimate need (revert strategy) but separate problem. Auto-snapshot before each match provides partial coverage. |

---

## 1. Bot Display & Rankings

### Visibility Model

All active paper bots visible by default. Users can **opt out** via a toggle in bot settings (`dojo_visible = false`). This populates the Dojo from day 1 with all ~27 active bots.

### Bot Card Data (Public Leaderboard)

- Bot name, AI model, trading pair, frequency
- Current PnL % (relative to starting balance — NOT raw equity)
- Win rate, total trades
- ELO rating + tier badge
- Equity sparkline (7d or match-appropriate)
- Active match indicator (if in a 1v1)
- Match record (W/L/D)

### Privacy Boundaries (NOT Shown)

- User identity (name, email, profile)
- Strategy text (natural language instructions)
- Specific indicator configurations
- Raw account balance

### Sorting

Primary sort by ELO rating. Secondary sort by PnL %. Users can toggle between:
- ELO ranking (default)
- PnL % (trailing 7d, 30d, all-time)
- Win rate
- Most active (by trades)

---

## 2. ELO Rating System

### Core Formula

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

### Composite Match Score

Match outcomes use a **composite score** rather than pure PnL %. This rewards good strategy, not just lucky swings.

| Factor | Weight | Metric |
|--------|--------|--------|
| **PnL %** | 40% | `(end_equity - start_equity) / start_equity * 100` |
| **Sortino Ratio** | 25% | `mean(returns) / std(negative_returns_only) * sqrt(period_days)` — only penalizes downside volatility, rewards asymmetric returns |
| **Max Drawdown** | 20% | Inverted: lower drawdown = higher score |
| **Win Rate** | 15% | `wins / total_trades` over match period |

**Why Sortino over Sharpe**: Sharpe penalizes ALL volatility equally — a +5% day is treated as equally "risky" as a -5% day. Sortino only penalizes downside moves. A bot with big wins and small losses gets a mediocre Sharpe but an excellent Sortino. For trading bots, upside volatility is a feature, not a bug. Sortino rewards exactly the behavior we want: asymmetric returns with controlled downside.

**Weight adjustment by format** (Sortino needs sufficient data points):

| Factor | Standard (21d) | Rapid (7d) | Blitz (1d) |
|--------|---------------|------------|------------|
| PnL % | 40% | 45% | 60% |
| Sortino | 25% | 20% | 5% |
| Drawdown | 20% | 20% | 20% |
| Win Rate | 15% | 15% | 15% |

**Score calculation**: Each factor is normalized to 0-1 range relative to the opponent (in 1v1) or the field (in rolling). Weighted sum produces final score 0-1. In 1v1: score > 0.5 = win.

**Edge cases**:
- Neither bot trades during match → draw, no ELO change
- One bot trades, other doesn't → non-trading bot gets score 0 for PnL/win-rate, neutral for drawdown/Sortino
- Bot deactivated during match → forfeit, opponent wins

### Rating Sources

**Rolling ELO** (passive, weekly):
- Every Sunday midnight UTC, calculate composite scores for all active Dojo bots over trailing 7 days
- Rank all bots 1 to N by composite score
- Swiss-system ELO update: each bot compared against the field median, ELO adjusts based on rank vs expected rank
- Bots with < 7 days active get no rolling update that week

**Match ELO** (active, per 1v1):
- Traditional two-player ELO from explicit challenges
- Updates immediately when match completes

Both sources feed the same ELO number. A bot's rating reflects both passive performance and 1v1 results.

### Tier System

| ELO Range | Tier | Color | Icon |
|-----------|------|-------|------|
| < 1000 | Novice | White | ○ |
| 1000-1199 | Apprentice | Green | ● |
| 1200-1399 | Journeyman | Blue | ◆ |
| 1400-1599 | Expert | Purple | ★ |
| 1600-1799 | Master | Gold | ♛ |
| 1800+ | Grandmaster | Red | ♚ |

---

## 3. House Bots — The Arbiter Family

Platform-owned bots that serve as **benchmarks and sparring partners**. Each is optimized for a specific time format.

| House Bot | Format | Timeframe | Style | Target ELO |
|-----------|--------|-----------|-------|------------|
| **The Arbiter** | Standard (21d) | 4h-1d | Patient, high-conviction, few trades | ~1400+ |
| **The Arbiter: Rapid** | Rapid (7d) | 1h-4h | Medium frequency, balanced risk | ~1300+ |
| **The Arbiter: Blitz** | Blitz (1d) | 5m-15m | Aggressive, scalping-style | ~1200+ |

House bots:
- Flagged with `is_house_bot = true` on configurations table
- Always visible in Dojo (cannot be hidden)
- Featured in Dojo tab and on public `/dojo` page
- Strategy partially revealed (model, symbol, frequency, indicators — NOT the strategy text)
- Their ELO adjusts naturally from matches (making it meaningful: "I beat a 1450 House Bot")

**Creation**: Sev hand-tunes each variant. Rapid/Blitz may be variations of The Arbiter with adjusted timeframes, position sizing, and strategy prompts.

---

## 4. 1v1 Matches

### Time Controls

| Format | Duration | Starts At | Analogy |
|--------|----------|-----------|---------|
| **Blitz** | 1 day | Next hour boundary | Bullet chess |
| **Rapid** | 7 days | Next midnight UTC | Rapid chess |
| **Standard** | 21 days | Next midnight UTC | Classical chess |

### Match Isolation

When a match starts, the system:
1. **Snapshots** the bot's current `config_data` into `dojo_matches.config_snapshot`
2. **Creates a temporary configuration** from the snapshot (new config_id, `config_type = 'dojo_match'`)
3. **Creates a fresh $10k paper account** for the temp config
4. **Activates** the temp config in the scheduler — runs normally through the existing execution pipeline
5. When the match ends, the temp config is **deactivated and archived** (`state = 'archived'`)

The user's original bot is untouched. It keeps running, can be edited, etc. The match runs a frozen copy.

### Match Lifecycle

```
Challenge → Accept → Active → Complete → ELO Update
                       ↓
                    Forfeit (if bot deactivated)
```

1. **Challenge**: User selects opponent (House Bot or another user's bot) + format
   - Against House Bots: instant accept (always available)
   - Against users: opponent must accept within 24h or challenge expires
2. **Cost estimate shown**: "~$5.04 in credits (168 cycles @ 1h). You have $12.50."
   - Must have enough credits to cover estimated cost
3. **Start**: Temp configs created, fresh $10k accounts, both start at next time boundary
4. **Active**: Both temp bots run independently through the scheduler
5. **Complete**: At end time, scheduler job snapshots final equity, calculates composite scores, determines winner, updates ELO on the ORIGINAL bots
6. **Forfeit**: If either original bot is deleted, the other wins by forfeit. (Temp bots can't be manually stopped.)

### Match Limits

- House Bots can have unlimited concurrent challengers
- Cannot challenge the same bot in the same format while a match is active
- No per-user limits on total concurrent matches

---

## 5. Database Schema

### New Columns on Existing Tables

```sql
-- configurations: Dojo visibility + ELO + house bot flag
ALTER TABLE configurations ADD COLUMN dojo_visible BOOLEAN DEFAULT TRUE;
ALTER TABLE configurations ADD COLUMN elo_rating INTEGER DEFAULT 1200;
ALTER TABLE configurations ADD COLUMN is_house_bot BOOLEAN DEFAULT FALSE;
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
    reason TEXT NOT NULL,           -- 'rolling_weekly', 'match_win', 'match_loss', 'match_draw', 'match_forfeit'
    match_id UUID,                  -- references dojo_matches if from a match
    details JSONB,                  -- composite score breakdown, opponent info, etc.
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_elo_history_config ON elo_history(config_id, created_at DESC);

-- 1v1 matches
CREATE TABLE dojo_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    format TEXT NOT NULL CHECK (format IN ('blitz', 'rapid', 'standard')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'completed', 'cancelled', 'forfeit')),
    -- Participants (original bots — ELO updated on these)
    challenger_config_id UUID NOT NULL REFERENCES configurations(config_id),
    opponent_config_id UUID NOT NULL REFERENCES configurations(config_id),
    challenger_user_id UUID NOT NULL,
    opponent_user_id UUID NOT NULL,
    -- Temp instances (isolated match bots — created at match start)
    challenger_instance_id UUID REFERENCES configurations(config_id),
    opponent_instance_id UUID REFERENCES configurations(config_id),
    -- Config snapshots (frozen strategy at match start)
    challenger_config_snapshot JSONB,
    opponent_config_snapshot JSONB,
    -- Timing
    challenge_expires_at TIMESTAMPTZ,   -- NULL for house bot challenges (auto-accept)
    accepted_at TIMESTAMPTZ,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    -- Start snapshots (always $10k for both)
    challenger_start_equity NUMERIC DEFAULT 10000,
    opponent_start_equity NUMERIC DEFAULT 10000,
    -- End results
    challenger_end_equity NUMERIC,
    opponent_end_equity NUMERIC,
    challenger_composite_score NUMERIC,
    opponent_composite_score NUMERIC,
    winner_config_id UUID,             -- NULL for draw; references original config, not instance
    -- ELO deltas (on original bots)
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
```

---

## 6. API Endpoints

### Public (No Auth) — for `/dojo` leaderboard page

```
GET  /api/v2/public/dojo/bots          — All active, visible bots with performance + ELO
GET  /api/v2/public/dojo/stats         — Aggregate stats (total bots, avg ELO, matches today)
GET  /api/v2/public/dojo/bot/{id}      — Single bot detail (expanded card data)
GET  /api/v2/public/dojo/matches       — Recent/active matches (spectating)
GET  /api/v2/public/dojo/leaderboard   — ELO-sorted rankings with tier badges
```

### Authenticated — for Forge Dojo tab

```
POST /api/v2/dojo/challenge            — Issue a 1v1 challenge (body: config_id, opponent_id, format)
POST /api/v2/dojo/challenge/{id}/accept — Accept a challenge
POST /api/v2/dojo/challenge/{id}/cancel — Cancel pending challenge
GET  /api/v2/dojo/matches/{config_id}  — Match history for a specific bot
GET  /api/v2/dojo/active/{config_id}   — Active matches for a specific bot
GET  /api/v2/dojo/cost-estimate        — Estimate credit cost for a match (query: config_id, format)
PUT  /api/v2/config/{id}/visibility    — Toggle dojo_visible
```

---

## 7. Backend Architecture

### ELO Calculation Service

New module: `core/arena/elo.py`

```python
# core/arena/elo.py

def calculate_composite_score(config_id, start_time, end_time, format):
    """Calculate composite match score for a bot over a time period.

    Uses format-specific weights:
    - PnL %: primary outcome
    - Sortino ratio: rewards asymmetric returns (downside-only volatility)
    - Max drawdown (inverted): penalizes reckless equity curves
    - Win rate: decision quality
    """
    # Query trades, snapshots from the TEMP INSTANCE (not the original bot)
    # Calculate PnL %, Sortino, max drawdown, win rate
    # Apply format-specific weights
    # Return normalized 0-1 score

def calculate_sortino_ratio(daily_returns, period_days, risk_free_rate=0.0):
    """Sortino ratio — like Sharpe but only penalizes downside volatility.

    sortino = (mean_return - risk_free) / downside_deviation
    downside_deviation = std(returns where return < target)
    """

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
    # Validate: bot is active + visible, no duplicate active match
    # If opponent is house bot: auto-accept, set start time
    # If opponent is user bot: set expires_at = now + 24h, status = pending

async def start_match(match_id):
    """Called when match start time is reached (or on accept for house bots)."""
    # Snapshot both bots' config_data
    # Create temp configurations (config_type='dojo_match', state='active')
    # Create fresh $10k paper accounts for temp configs
    # Add temp configs to scheduler
    # Update match status = 'active'

async def complete_match(match_id):
    """Called by scheduler when match end time reached."""
    # Snapshot final equity from temp instances
    # Calculate composite scores (using Sortino)
    # Determine winner
    # Update ELO on ORIGINAL bots (not temp instances)
    # Record elo_history entries
    # Deactivate + archive temp configs

async def check_forfeits():
    """Called periodically — check if any active match has a deleted original bot."""
    # Query active matches where either original bot no longer exists
    # Forfeit: opponent wins, ELO adjusts, temp instances cleaned up
```

### Scheduler Jobs

Add to `ggbot_scheduler.py`:

```python
# Weekly rolling ELO (Sundays midnight UTC)
scheduler.add_job(weekly_rolling_elo, CronTrigger(day_of_week='sun', hour=0, minute=0))

# Match lifecycle checker (every 5 minutes)
# - Start matches whose start_at has passed
# - Complete matches whose ends_at has passed
# - Check for forfeits
scheduler.add_job(process_dojo_matches, IntervalTrigger(minutes=5))
```

---

## 8. Frontend Architecture

### Forge — Dojo Tab

The Dojo is a **third tab** in the Forge, alongside Monitor and Configure. `TabNavigation.tsx` type becomes `'monitor' | 'configure' | 'dojo'`.

When a bot is selected and the Dojo tab is active:

```
┌────────────────────────────────────────────────────┐
│ BTC Momentum                      ◆ ELO 1,312      │
│ Journeyman · 8W-3L-1D                              │
│                                                     │
│ ┌─ ENTER MATCH ───────────────────────────────────┐ │
│ │ Format:  [Blitz 1d] [Rapid 7d] [Standard 21d]  │ │
│ │ Opponent: The Arbiter ★1,487     [Change]       │ │
│ │ Est. cost: ~$5.04 (168 cycles)                  │ │
│ │ Your credits: $12.50 ✓                          │ │
│ │                              [Start Match]      │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ─ ACTIVE MATCHES ────────────────────────────────── │
│ ┌─────────────────────────────────────────────────┐ │
│ │ You (1312) ⚔️ The Arbiter (1487)                │ │
│ │ Rapid · 4d 12h remaining                        │ │
│ │ You: +3.2% ($10,320) | Arbiter: +1.8% ($10,180)│ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ─ MATCH HISTORY ─────────────────────────────────── │
│ W  vs The Arbiter     Rapid    +5.2% vs +2.1%      │
│    ELO: 1,280 → 1,312 (+32)   Mar 20               │
│ L  vs ScalpKing       Blitz    -1.2% vs +0.8%      │
│    ELO: 1,305 → 1,280 (-25)   Mar 18               │
│ W  vs The Arbiter     Standard +12.1% vs +8.3%     │
│    ELO: 1,268 → 1,305 (+37)   Feb 28               │
└────────────────────────────────────────────────────┘
```

### Bot Rail Addition

Each bot card in the rail gains an ELO tier badge:

```
Before:                           After:
● BTC Momentum                    ● BTC Momentum          ◆ 1,312
  [GPT] [BTC/USDT] [+5.2%]         [GPT] [BTC/USDT] [+5.2%]
  Frequency: 1h                     Frequency: 1h
```

### Public `/dojo` Page

Lightweight public page (no Web3, no auth complexity):

```
/dojo
├── Hero: "The Dojo — Where AI Traders Are Forged"
├── Stats: total bots, avg ELO, active matches
├── House Bots (The Arbiter family with ELO + match records)
├── Active Matches (spectating — who's fighting, current scores)
├── Leaderboard (ELO-sorted, tier badges, match records)
├── CTA: "Build your bot in the Forge → app.ggbots.ai"
└── Past Seasons toggle (S1 results)
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `DojoTab` | Forge | Main Dojo content when tab is active |
| `EnterMatchPanel` | Forge/Dojo | Format picker + opponent selector + cost estimate + start button |
| `ActiveMatchCard` | Forge/Dojo + Public | Live match display (vs framing, timer, scores) |
| `MatchHistoryList` | Forge/Dojo | Past matches with results + ELO changes |
| `ChallengeModal` | Forge/Dojo | Opponent selection (House Bots, leaderboard search) |
| `EloTierBadge` | Shared | Colored tier badge with icon — used in rail, cards, leaderboard |
| `DojoPublicPage` | Public /dojo | Leaderboard + spectating page |
| `DojoBotCard` | Public /dojo | Bot card with ELO, stats, match record |

---

## 9. Implementation Phases

### Phase 1: Dojo Foundation
**Scope**: ELO on bots, public leaderboard, Dojo tab shell in Forge

**Backend**:
- Add `dojo_visible`, `elo_rating`, `is_house_bot` columns to configurations
- `GET /api/v2/public/dojo/bots` endpoint (active + visible + paper bots with performance + ELO)
- `GET /api/v2/public/dojo/stats` endpoint
- `PUT /api/v2/config/{id}/visibility` endpoint

**Frontend**:
- Add `EloTierBadge` component (shared)
- Add ELO badge to BotRail bot cards
- Add `'dojo'` to TabNavigation type
- Dojo tab shell: shows bot's ELO, tier, placeholder match UI
- Public `/dojo` page: leaderboard with placeholder 1200 ELO
- S1 results accessible via "Past Seasons" on public page

**Dependencies**: None

### Phase 2: ELO Engine
**Scope**: Real ELO calculations, rolling weekly updates, history tracking

**Backend**:
- Create `elo_history` table
- `core/arena/elo.py` — Sortino-based composite score + ELO update functions
- Weekly rolling ELO scheduler job
- `GET /api/v2/public/dojo/leaderboard` with real ELO sorting

**Frontend**:
- Real ELO values replace placeholder 1200
- ELO history in Dojo tab (rating over time)
- Leaderboard sorts by real ELO

**Dependencies**: Phase 1

### Phase 3: House Bots
**Scope**: Create and deploy The Arbiter family

**Work**:
- Sev creates/tunes The Arbiter Standard config
- Create Rapid and Blitz variants
- Mark as `is_house_bot = true`
- Featured on public `/dojo` page and in Forge Dojo tab challenge UI

**Dependencies**: Phase 1

### Phase 4: 1v1 Matches
**Scope**: Match lifecycle with isolated instances, challenge flow, results

**Backend**:
- Create `dojo_matches` table
- `core/arena/matches.py` — full lifecycle (challenge → start → complete → ELO update)
- Match instance creation (temp config + fresh $10k account)
- Cost estimation endpoint
- Match lifecycle scheduler job (start, complete, forfeit checks)

**Frontend**:
- EnterMatchPanel in Dojo tab (format, opponent, cost, start)
- ChallengeModal (opponent selection from House Bots + leaderboard)
- ActiveMatchCard (live scores, timer)
- MatchHistoryList (past matches with results + ELO changes)
- Active matches on public `/dojo` page (spectating)

**Dependencies**: Phase 2 (ELO engine needed for match results)

---

## 10. Future Features (Not Part of Dojo Build)

### Config Versioning / Snapshots
Save bot configurations at a point in time, revert if updates perform worse. Similar to git commits for strategy. The Dojo already auto-snapshots configs for each match (`dojo_matches.config_snapshot`), but a user-facing "Save Snapshot" / "Revert to Snapshot" UI is a separate feature.

### Quick Match (Auto-Matchmaking)
Chess.com-style "Find Match" queue — matched by ELO ± 200. Requires critical mass of concurrent users. Ship with House Bots + Direct Challenges first, add when DAU > 20.

### A/B Testing Mode
Structured experimentation: run two bot configs simultaneously against the same House Bot, compare results side by side. The architecture supports this naturally (just two matches), but a dedicated UI comparing results would be valuable.

### Strategy Marketplace
Share/sell archetypes. Copy other users' strategies. Requires config versioning + permissions + possibly Stripe Connect.

---

## 11. Open Questions

1. **The Arbiter configs**: Does The Arbiter exist already as a running bot? Need to create Rapid/Blitz variants — Sev tunes these manually?

2. **Web3 cleanup**: The BetModal + wagmi/RainbowKit are still in the Arena code. The public `/dojo` page should NOT need Web3. Remove entirely? Significant bundle reduction.

3. **Composite score display**: Show the full breakdown (PnL%, Sortino, drawdown, win rate) in match results? Transparency builds trust but adds complexity.

4. **URL mapping**: `/arena` → redirect to `/dojo`? Or keep `/arena` for S1 results and `/dojo` is the new page?

5. **Mobile Forge**: The Dojo tab needs to work on mobile. The Forge already has `MobileNav.tsx` for tab switching. Match cards need a compact mobile layout.

6. **Temp config naming**: What should temp match instances be called? `"[Dojo] BTC Momentum vs The Arbiter"` or something invisible to the user?

7. **Match spectating data**: How much data do we expose on the public `/dojo` page for active matches? Just scores? Or live equity curves?

---

## Revision History

- 2026-03-26: Initial design from discussion (Sev + Claude Code session)
- 2026-03-26: Split from combined DOJO_AND_ARENA_S2.md — Dojo is now standalone focus. Arena S2 deferred. Replaced Sharpe with Sortino ratio.
- 2026-03-27: Major revision — killed archetype entity (ELO on bots directly), Dojo as third Forge tab (not separate page), match isolation via temp config instances, added config snapshot to matches, cost estimation, public `/dojo` as lightweight leaderboard only.
