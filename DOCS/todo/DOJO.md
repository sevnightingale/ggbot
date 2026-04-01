# The Dojo — Design & Implementation Plan

**Status**: PLANNING
**Owner**: Sev
**Created**: 2026-03-26
**Updated**: 2026-04-01
**Context**: Chess.com-inspired competitive environment for AI trading bots. Always-on — not tied to Arena seasons.

---

## Vision

The Dojo is where AI trading bots train, spar, and earn ratings. It reframes the bot-testing experience using **chess-inspired mechanics**: ELO ratings, 1v1 matches with time controls, and House Bots to challenge.

The Dojo is **built into the Forge** as a third tab alongside Monitor and Configure. Your ggbot IS your strategy — it has an ELO, a match record, and a tier badge. No separate "archetype" entity. External competitions (Virtuals Degen Arena, future ggArena seasons) are destinations you graduate to.

**Public leaderboard** at `/dojo` (lightweight scoreboard + spectating). All match functionality lives inside the Forge.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ELO lives on | The ggbot itself (`configurations.elo_rating`) | No separate entity. Bot = strategy = has rating. |
| Where Dojo lives | Third tab in Forge + public leaderboard at `/dojo` | Keeps testing inside the iteration loop. No context-switching. |
| Match execution (user bots) | **Copy-trade** from running bot (not full clone) | Zero additional LLM cost. Same pattern as DGClaw shadow trading. |
| Match execution (House Bots) | **Decision oracle + stateless consumer** | House Bot runs opportunity-only mode (never holds positions). Match accounts consume entry signals independently, exit only via TP/SL. Single House Bot serves unlimited matches, zero marginal cost. |
| Dojo tab eligibility | Paper bots only | Live bots (Hyperliquid) trade real money — lock system would be dangerous. No Dojo tab on live bots. |
| Match isolation | Fresh $10k account, mirrors only trades that occur during match window | Standardized conditions. Pre-existing positions ignored. |
| Bot lock during match | Full lock: no edits, no manual close, no stop, no reset, no delete | Competitive integrity. Forfeit is the only escape hatch. |
| Entry gate | Must be active + zero open positions to enter | Clean starting state. No partial trade contamination. |
| Visibility | Opt-out (`dojo_visible` default true) | Populates leaderboard from day 1. |
| Concurrent matches | No per-user or per-bot limits | Users can play as much as they want. |
| Config versioning | Future feature — matches auto-snapshot config for the record | Legitimate need but separate problem. |

---

## 1. Match Execution Model

### Copy-Trade (User Bots)

When a user's bot enters a match, the match account **mirrors the bot's real decisions** — zero additional LLM cost.

```
User's Bot (running, paying for LLM as normal)
  │
  ├── Decision: ENTER LONG BTC 20% margin
  │     ├── → User's paper account (existing, normal)
  │     └── → Match account ($10k, proportional sizing)
  │
  ├── Decision: WAIT
  │     └── (no trade to copy)
  │
  ├── Decision: EXIT
  │     ├── → User's paper account
  │     └── → Match account (close mirrored position)
```

**Mirror hook location**: `core/orchestrator/orchestrator.py` — same spot as the existing DGClaw arena mirror (lines 255-263). After the decision+trading step, one additional call:

```python
# After existing arena mirror logic (~line 263)
await self._mirror_to_dojo_matches(config, decision_result, trading_result)
```

**Close mirror**: All close paths (paper TP/SL, live TP/SL, manual close, reconciler) already call `arena_sync.mirror_close_to_arena()`. Add parallel `dojo_mirror.mirror_close_to_dojo()` with the same fire-and-forget, idempotent pattern.

**Proportional sizing**: The mirror copies trade parameters (symbol, side, % of account, leverage) but recalculates dollar amounts relative to the match's $10k account. If the original bot uses 20% margin, the match uses 20% of its own balance.

**Only complete trade cycles count**: The match starts clean ($10k, zero positions). Pre-existing positions on the original bot are ignored. The first mirrored action is the first entry that happens after the match begins. If the bot exits a position that the match doesn't hold — no-op.

### House Bots — Decision Oracle Model

House Bots operate differently from user bots. A House Bot **never holds positions**. It runs in **opportunity-analysis-only mode** — every cycle, it scans the market and outputs entry decisions (or "wait"). It never enters position management mode.

This means a single House Bot instance can serve unlimited concurrent matches with zero marginal cost.

```
The Arbiter (single instance, opportunity-only, no positions)
  │
  ├── Cycle: WAIT
  ├── Cycle: WAIT
  ├── Cycle: ENTER LONG BTC, SL -3%, TP +6%    ← signal broadcast
  ├── Cycle: WAIT                                (no position to manage)
  ├── Cycle: ENTER SHORT ETH, SL -2%, TP +5%   ← signal broadcast
  ├── ...

Match Account A ($10k, started 3 days ago):
  State machine:
    IDLE → hears ENTER LONG BTC → open position, set TP/SL → IN_POSITION
    IN_POSITION → ignores all signals → TP hits → IDLE
    IDLE → hears ENTER SHORT ETH → open position, set TP/SL → IN_POSITION

Match Account B ($10k, started today):
  State machine:
    IDLE → hears ENTER SHORT ETH → open position, set TP/SL → IN_POSITION
    (missed the BTC entry — wasn't active yet. Catches future entries.)
```

**Match account state machine:**

```
IDLE (no position)
  → House Bot signals "enter" → open position with TP/SL → IN_POSITION

IN_POSITION
  → Ignore all House Bot signals (waiting for TP/SL)
  → TP triggers → position closed → IDLE
  → SL triggers → position closed → IDLE
```

**Why this works:**
1. **One House Bot serves all matches** — no fresh instances, no duplicate LLM cost
2. **No position timing conflicts** — each match account tracks its own state independently
3. **No "open position" entry gate for House Bot challenges** — the House Bot itself never holds positions
4. **Deterministic exits** — TP/SL only, no LLM "should I hold?" decisions. Results reflect pure entry quality.
5. **Existing TP/SL monitor handles exits** — paper trading monitor already auto-executes TP/SL every 3 seconds

**Implementation**: The House Bot config uses `decision.awareness_level: 'low'` (Signal Mode). This is the first use of a broader `awareness_level` system:

| Level | Name | Behavior |
|-------|------|----------|
| `low` | Signal Mode | Entry decisions + TP/SL only. No position management. Fire-and-forget. |
| `medium` | Position Aware | Entry + active position management (hold/exit). **Current default for all bots.** |
| `high` | State Aware | Everything in medium + persistent cross-cycle memory/observations. (Future: Bot State v2.) |

For the Dojo build, we only implement `low` (for House Bots). `medium` is the existing implicit behavior (no code change). `high` is future work (maps to "Bot State v2: LLM-Writable Memory" in TODO.md). The decision engine checks `awareness_level` and skips position management when `low`. Default is `medium` — zero migration needed for existing bots.

Later, `awareness_level` becomes a user-facing config option in the Forge — users can choose Signal Mode for simpler, cheaper, more deterministic bots. For now, only House Bots use it.

**After each House Bot decision cycle**, the mirror service checks: "Are there active Dojo matches against this House Bot where the match account is IDLE?" If yes and the decision is an entry, execute on those accounts.

### User-vs-User Matches

Both sides copy-trade from their respective running bots. Both free. Both start clean at $10k. Both mirrors are independent — each user's match account only sees their own bot's decisions.

---

## 2. Lock System

When a bot has any active Dojo match, it is **completely locked**.

### What Gets Locked

| Action | Status | Reason |
|--------|--------|--------|
| Edit strategy/indicators/settings | Blocked | Can't change what's being tested |
| Manual close trade | Blocked | No human intervention |
| Manual "Run Now" | Blocked | Can't game timing |
| Stop bot | Blocked | Must forfeit first — stopping kills copy-trade source |
| Reset account | Blocked | Would corrupt match source data |
| Delete bot | Blocked | Match needs the source bot |
| View Monitor/Configure/Dojo | Allowed | Read-only |
| Forfeit match | Allowed | Explicit escape hatch |

### Lock State Derivation

No new column needed. Derived from active matches:

```sql
SELECT EXISTS(
    SELECT 1 FROM dojo_matches
    WHERE status = 'active'
    AND (challenger_config_id = %s OR opponent_config_id = %s)
) as dojo_locked
```

Helper function in `core/arena/matches.py`:

```python
def is_dojo_locked(config_id: str) -> bool:
    """Check if a bot is locked due to active Dojo match(es)."""
```

### Backend Lock Guards

Every mutating endpoint checks `is_dojo_locked()`:

| Endpoint | Location | Guard |
|----------|----------|-------|
| `PUT /config/{config_id}` | ggbot.py ~line 657 | Extend existing arena lock check |
| `POST /bot/{config_id}/stop` | ggbot.py | New guard |
| `POST /bot/{config_id}/positions/{trade_id}/close` | ggbot.py | New guard |
| `POST /positions/hyperliquid/{batch_id}/close` | ggbot.py ~line 1907 | New guard |
| `POST /orchestrate/{config_id}` (Run Now) | ggbot.py | New guard |
| `POST /bot/{config_id}/reset-account` | ggbot.py | New guard |
| `DELETE /config/{config_id}` | ggbot.py | New guard |

Pattern (matches existing arena lock at line 659):

```python
if is_dojo_locked(config_id):
    raise HTTPException(400, "Bot is locked for an active Dojo match. Forfeit to unlock.")
```

### Frontend Lock UX

**BotRail** — lock badge on bot card (VIBE: brass border-left like live bot slot):
```
● BTC Momentum          ◆ 1,312
  [GPT] [BTC/USDT] [+5.2%]
  🔒 Dojo · Rapid · 4d left
```

**ActivationBar** — stop/run buttons disabled:
```
Normal:      [Stop Bot] [Run Now]
Dojo locked: [🔒 In Dojo Match] (tooltip: "Forfeit match to stop")
```

**Configure tab** — read-only with banner (VIBE: `bg-[var(--accent)]/10` border pattern, same as arena S2 banner at page.tsx line 1154):
```
┌─────────────────────────────────────────────────────┐
│ 🔒 Locked — Active Dojo Match (Rapid vs The Arbiter) │
│ [View Match]  [Forfeit Match]                        │
└─────────────────────────────────────────────────────┘
All edit controls: disabled state
```

**PositionsTable** — manual close button hidden when locked.

**BotManagementMenu** — delete and reset disabled. Duplicate still allowed (cloning a locked bot is fine).

### Entry Gate

Before starting a match, validate:

```python
# Pre-match validation
if bot.state != 'active':
    → "Activate your bot before entering a Dojo match."
if bot has open positions (paper_trades WHERE status='open' AND config_id=X):
    → "Close your active positions before entering the Dojo."
if is_dojo_locked(config_id):
    → "Bot is already in an active match."
```

### Forfeit

Explicit action: `POST /api/v2/dojo/match/{match_id}/forfeit`

- Opponent wins by forfeit
- ELO adjusts (forfeit = loss)
- Match accounts archived
- Lock released (unless other active matches remain)
- Confirmation modal with clear consequences

---

## 3. ELO Rating System

### Core Formula

Standard ELO with K-factor scaling:

```
Expected score:  E_A = 1 / (1 + 10^((R_B - R_A) / 400))
New rating:      R_A' = R_A + K * (S_A - E_A)
```

K-factor: K=32 (< 10 events), K=24 (10-30), K=16 (> 30 AND > 1600 ELO)

Starting ELO: **1200**

### Composite Match Score

| Factor | Weight | Metric |
|--------|--------|--------|
| **PnL %** | 40% | `(end_equity - start_equity) / start_equity * 100` |
| **Sortino Ratio** | 25% | `mean(returns) / std(negative_returns_only) * sqrt(period_days)` |
| **Max Drawdown** | 20% | Inverted: lower drawdown = higher score |
| **Win Rate** | 15% | `wins / total_trades` over match period |

**Why Sortino**: Only penalizes downside volatility. A bot with big wins and small losses gets rewarded. Upside volatility is a feature.

**Format-specific weights** (Sortino needs data):

| Factor | Standard (21d) | Rapid (7d) | Blitz (1d) |
|--------|---------------|------------|------------|
| PnL % | 40% | 45% | 60% |
| Sortino | 25% | 20% | 5% |
| Drawdown | 20% | 20% | 20% |
| Win Rate | 15% | 15% | 15% |

**Edge cases**: No trades by either → draw. One trades, other doesn't → non-trader scores 0. Forfeit → opponent wins.

### Rating Sources

**Rolling ELO** (passive, weekly): Sunday midnight UTC, composite scores for all active Dojo-visible bots over trailing 7 days. Swiss-system update.

**Match ELO** (active, per 1v1): Traditional two-player ELO on match completion.

### Tier System

| ELO | Tier | Color | Icon |
|-----|------|-------|------|
| < 1000 | Novice | White | ○ |
| 1000-1199 | Apprentice | Green | ● |
| 1200-1399 | Journeyman | Blue | ◆ |
| 1400-1599 | Expert | Purple | ★ |
| 1600-1799 | Master | Gold | ♛ |
| 1800+ | Grandmaster | Red | ♚ |

---

## 4. House Bots — The Arbiter Family

| House Bot | Format | Timeframe | Style |
|-----------|--------|-----------|-------|
| **The Arbiter** | Standard (21d) | 4h-1d | Patient, high-conviction |
| **The Arbiter: Rapid** | Rapid (7d) | 1h-4h | Medium frequency |
| **The Arbiter: Blitz** | Blitz (1d) | 5m-15m | Aggressive, scalping |

**Operational model** — Decision Oracle:
- `is_house_bot = true` on configurations
- Runs in **opportunity-analysis-only mode** (no position management)
- Outputs entry decisions with TP/SL every cycle — never holds positions itself
- Single instance per House Bot, serves unlimited concurrent matches
- Match accounts consume entry signals independently (see Section 1)
- ELO adjusts from match results against challengers

**Visibility & display**:
- Always visible on public `/dojo` and in Forge challenge UI
- Strategy partially revealed (model, symbol, frequency, indicators — NOT strategy text)
- Shows aggregate match record (W/L/D) and current ELO

**Creation**: Sev hand-tunes each variant. Key config differences from normal bots: `position_management: false` (or `exit_mode: 'tp_sl_only'`), appropriate timeframe per format.

---

## 5. 1v1 Matches

### Time Controls

| Format | Duration | Starts At |
|--------|----------|-----------|
| **Blitz** | 1 day | Next hour boundary |
| **Rapid** | 7 days | Next midnight UTC |
| **Standard** | 21 days | Next midnight UTC |

### Match Lifecycle

```
Challenge → [Accept] → Active → Complete → ELO Update
                          ↓
                       Forfeit (explicit user action)
```

1. **Challenge**: Pick opponent + format
   - House Bot: instant accept, start at next time boundary. No entry gate on House Bot side (it never holds positions).
   - User bot: opponent has 24h to accept or challenge expires. Both must pass entry gate.
2. **Validate**: Challenger bot must be active paper bot, no open positions, not already in same-format match with this opponent.
3. **Start**: Create match accounts ($10k each). User side: copy-trade begins, bot LOCKED. House Bot side: match account created in IDLE state, listens for House Bot entry signals. House Bots are never locked.
4. **Active**: User trades mirrored to match account. House Bot entries dispatched to IDLE match accounts. TP/SL executes on both sides via existing paper trading monitor.
5. **Complete**: Scheduler detects `ends_at < now`. Snapshot equity. Calculate composite scores. Update ELO on original bots. Archive match accounts. Release user's lock.
6. **Forfeit**: User explicitly forfeits → opponent (House Bot or user) wins, ELO adjusts, lock released.

---

## 6. Match History & Results

### Storage

The `result_details` JSONB column on `dojo_matches` stores the full breakdown:

```json
{
  "challenger": {
    "final_equity": 10520.00,
    "pnl_pct": 5.2,
    "sortino": 1.84,
    "max_drawdown_pct": 2.1,
    "win_rate": 0.667,
    "total_trades": 6,
    "composite_score": 0.72,
    "trades": [
      {
        "side": "long", "symbol": "BTC/USDT",
        "entry_time": "2026-03-14T09:00:00Z",
        "exit_time": "2026-03-15T17:00:00Z",
        "pnl": 180.00, "pnl_pct": 1.8
      }
    ]
  },
  "opponent": { ... },
  "config_snapshot_summary": {
    "model": "gpt", "symbol": "BTC/USDT", "frequency": "1h",
    "indicators": ["RSI", "MACD", "BB", "EMA"]
  }
}
```

The full config snapshot is in `challenger_config_snapshot` / `opponent_config_snapshot` JSONB columns. The `result_details` stores the human-readable summary. Match detail view renders from a single row — no joins.

### Dojo Tab Layout

```
┌── DOJO TAB ──────────────────────────────────────────┐
│                                                       │
│ BTC Momentum                          ◆ ELO 1,312    │
│ Journeyman · 14 matches · 8W-3L-1D · 61.5% WR       │
│                                                       │
│ ─── ENTER MATCH ──────────────────────────────────── │
│ Format:  [Blitz 1d] [Rapid 7d] [Standard 21d]        │
│ Opponent: The Arbiter ★1,487         [Change]         │
│                              [Start Match]            │
│ (or: 🔒 Locked — match in progress)                   │
│                                                       │
│ ─── ACTIVE MATCHES ──────────────────────────────── │
│ ┌───────────────────────────────────────────────────┐ │
│ │ You (1312) ⚔️ The Arbiter (1487)                  │ │
│ │ Rapid · 4d 12h left                               │ │
│ │ You: +3.2% ($10,320) | Arbiter: +1.8% ($10,180)  │ │
│ │                                     [Forfeit]     │ │
│ └───────────────────────────────────────────────────┘ │
│                                                       │
│ ─── MATCH HISTORY ───────────────────────────────── │
│ W  vs The Arbiter ★1,487   Rapid    +5.2% vs +2.1%  │
│    ELO: 1,280 → 1,312 (+32)        Mar 20           │
│    ▸ Click to expand full breakdown                   │
│                                                       │
│ L  vs ScalpKing ◆1,380     Blitz    -1.2% vs +0.8%  │
│    ELO: 1,305 → 1,280 (-25)        Mar 18           │
│                                                       │
│ W  vs The Arbiter ★1,450   Standard +12.1% vs +8.3% │
│    ELO: 1,268 → 1,305 (+37)        Feb 28           │
└──────────────────────────────────────────────────────┘
```

Expanded match detail shows: both sides' composite breakdown (PnL, Sortino, drawdown, win rate), individual trades with P&L, config snapshot summary, and ELO change.

### Match Results API

```
GET  /api/v2/dojo/matches/{config_id}?limit=20&offset=0  — Paginated history
GET  /api/v2/public/dojo/match/{match_id}                 — Single match (shareable URL)
GET  /api/v2/dojo/stats/{config_id}                       — Aggregate stats (W/L/D, avg PnL by format)
```

---

## 7. Database Schema

### New Columns

```sql
ALTER TABLE configurations ADD COLUMN dojo_visible BOOLEAN DEFAULT TRUE;
ALTER TABLE configurations ADD COLUMN elo_rating INTEGER DEFAULT 1200;
ALTER TABLE configurations ADD COLUMN is_house_bot BOOLEAN DEFAULT FALSE;
```

### New Tables

```sql
CREATE TABLE elo_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES configurations(config_id),
    elo_before INTEGER NOT NULL,
    elo_after INTEGER NOT NULL,
    change INTEGER NOT NULL,
    reason TEXT NOT NULL,        -- 'rolling_weekly', 'match_win', 'match_loss', 'match_draw', 'match_forfeit'
    match_id UUID,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_elo_history_config ON elo_history(config_id, created_at DESC);

CREATE TABLE dojo_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    format TEXT NOT NULL CHECK (format IN ('blitz', 'rapid', 'standard')),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'completed', 'cancelled', 'forfeit')),

    -- Original bots (ELO updated on these)
    challenger_config_id UUID NOT NULL REFERENCES configurations(config_id),
    opponent_config_id UUID NOT NULL REFERENCES configurations(config_id),
    challenger_user_id UUID NOT NULL,
    opponent_user_id UUID NOT NULL,

    -- Match instances (minimal configs for paper account tracking, config_type='dojo_match')
    -- User side: copy-trade destination, no scheduler job
    -- House Bot side: signal consumer with IDLE/IN_POSITION state, no scheduler job
    -- Both are just paper account containers — filtered out of bot rail
    challenger_instance_id UUID REFERENCES configurations(config_id),
    opponent_instance_id UUID REFERENCES configurations(config_id),

    -- Config snapshots (frozen strategy at match start)
    challenger_config_snapshot JSONB,
    opponent_config_snapshot JSONB,

    -- Timing
    challenge_expires_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,

    -- Results (populated on completion)
    challenger_end_equity NUMERIC,
    opponent_end_equity NUMERIC,
    challenger_composite_score NUMERIC,
    opponent_composite_score NUMERIC,
    winner_config_id UUID,          -- NULL for draw
    challenger_elo_before INTEGER,
    challenger_elo_after INTEGER,
    opponent_elo_before INTEGER,
    opponent_elo_after INTEGER,
    result_details JSONB,           -- full breakdown + trade list

    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_dojo_matches_status ON dojo_matches(status) WHERE status IN ('pending', 'active');
CREATE INDEX idx_dojo_matches_challenger ON dojo_matches(challenger_config_id);
CREATE INDEX idx_dojo_matches_opponent ON dojo_matches(opponent_config_id);
CREATE INDEX idx_dojo_matches_active_lock ON dojo_matches(status)
    WHERE status = 'active';  -- for is_dojo_locked() queries
```

---

## 8. API Endpoints

### Public

```
GET  /api/v2/public/dojo/bots              — All active, visible bots + ELO
GET  /api/v2/public/dojo/stats             — Aggregate stats
GET  /api/v2/public/dojo/leaderboard       — ELO-sorted rankings
GET  /api/v2/public/dojo/matches           — Active matches (spectating)
GET  /api/v2/public/dojo/match/{match_id}  — Single match result (shareable)
```

### Authenticated (Forge Dojo tab)

```
GET  /api/v2/dojo/can-enter/{config_id}    — Check: active? no positions? not locked?
POST /api/v2/dojo/challenge                — Issue challenge (body: config_id, opponent_id, format)
POST /api/v2/dojo/challenge/{id}/accept    — Accept challenge
POST /api/v2/dojo/challenge/{id}/cancel    — Cancel pending
POST /api/v2/dojo/match/{id}/forfeit      — Forfeit active match
GET  /api/v2/dojo/matches/{config_id}      — Match history for a bot
GET  /api/v2/dojo/stats/{config_id}        — Aggregate stats for a bot
GET  /api/v2/dojo/active/{config_id}       — Active matches for a bot
PUT  /api/v2/config/{id}/visibility        — Toggle dojo_visible
```

---

## 9. Backend Architecture

### Mirror Service: `core/arena/dojo_mirror.py`

Two mirror paths — one for user bots (copy-trade), one for House Bots (signal dispatch):

```python
async def mirror_trade_to_dojo(config_id, decision_result, trading_result):
    """Mirror a user bot's trade to its active Dojo match accounts.

    Called from orchestrator after trading step (same spot as DGClaw mirror).
    Fire-and-forget. Only mirrors actual trades, not wait/hold.
    Proportional sizing relative to match account balance.
    """

async def mirror_close_to_dojo(config_id, symbol):
    """Mirror a position close to Dojo match accounts.

    Called from all close paths (same pattern as arena_sync.py).
    Idempotent — checks if match account has the position.
    """

async def dispatch_house_bot_signal(config_id, decision_result):
    """Dispatch a House Bot's entry signal to all active match accounts in IDLE state.

    Called from orchestrator after House Bot decision step.
    Only dispatches entry signals (long/short), not wait.
    Each match account independently decides whether to consume:
    - IDLE state → execute entry with TP/SL on match account
    - IN_POSITION state → ignore (waiting for TP/SL to trigger)
    """
```

### Match Lifecycle: `core/arena/matches.py`

```python
def is_dojo_locked(config_id: str) -> bool:
    """Check if bot has active Dojo matches. Only applies to user bots."""

async def create_challenge(challenger_config_id, opponent_config_id, format):
    """Create match. House bot = auto-accept. User = pending (24h expiry)."""

async def start_match(match_id):
    """Create match accounts ($10k each).
    Both sides: minimal config (config_type='dojo_match') for paper account tracking.
    House bot side: match account starts in IDLE state, no scheduler job needed.
    Snapshot both configs. Set status='active'. Lock challenger (not House Bots)."""

async def complete_match(match_id):
    """Snapshot equity. Calculate composite scores (Sortino).
    Determine winner. Update ELO on originals. Archive match accounts."""

async def forfeit_match(match_id, forfeiting_user_id):
    """Opponent wins. ELO adjusts. Archive. Release lock."""

async def process_dojo_matches():
    """Scheduler job (every 5 min):
    - Start matches whose starts_at has passed
    - Complete matches whose ends_at has passed
    - Expire pending challenges past 24h"""
```

### ELO Engine: `core/arena/elo.py`

```python
def calculate_composite_score(config_id, start_time, end_time, format):
    """PnL + Sortino + drawdown + win rate, format-weighted."""

def calculate_sortino_ratio(daily_returns, period_days):
    """std(negative_returns_only) denominator."""

def update_elo(rating_a, rating_b, score_a, score_b, k_factor):
    """Standard ELO. Returns (new_a, new_b)."""

def weekly_rolling_update():
    """Swiss-system ELO for all active Dojo bots. Sundays midnight UTC."""
```

### Scheduler Jobs (in `ggbot_scheduler.py`)

```python
# Weekly rolling ELO
scheduler.add_job(weekly_rolling_elo, CronTrigger(day_of_week='sun', hour=0))

# Match lifecycle (start, complete, expire)
scheduler.add_job(process_dojo_matches, IntervalTrigger(minutes=5))
```

### Config List Enrichment

Add to the config list response (same pattern as arena_registration enrichment at ggbot.py line 485):

```python
{
    "config_id": "...",
    "elo_rating": 1312,
    "dojo_locked": true,
    "dojo_matches_active": [
        {
            "match_id": "abc-123",
            "opponent_name": "The Arbiter",
            "format": "rapid",
            "ends_at": "2026-04-08T00:00:00Z"
        }
    ]
}
```

---

## 10. Frontend Architecture

### Forge — Dojo Tab

`TabNavigation.tsx` type becomes `'monitor' | 'configure' | 'dojo'`.

**Paper bots only**: The `'dojo'` tab is only shown when the selected bot has `trading_mode = 'paper'`. Live bots (Hyperliquid) do not get a Dojo tab — the lock system would be dangerous on real-money positions (can't stop, can't close). The TabNavigation component checks `selectedBot.trading_mode` and conditionally renders the tab.

New component: `DojoTab.tsx` — renders when dojo tab active on a selected paper bot.

### Bot Rail

Each bot card gains ELO tier badge. When locked, shows lock indicator:

```
● BTC Momentum          ◆ 1,312        (normal)
● BTC Momentum          ◆ 1,312        (locked: brass border-left + 🔒 badge)
  🔒 Dojo · Rapid · 4d left
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `DojoTab` | Main container: ELO header, enter match, active matches, history |
| `EnterMatchPanel` | Format picker, opponent selector, start button |
| `ActiveMatchCard` | Live match: vs display, timer, scores, forfeit button |
| `MatchHistoryList` | Past matches: W/L/D rows, expandable detail |
| `MatchDetail` | Expanded: composite breakdown, trades, config snapshot |
| `ChallengeModal` | Opponent selection: House Bots + leaderboard search |
| `EloTierBadge` | Shared: colored badge with tier icon + number |
| `DojoLockBanner` | Configure tab: read-only banner with match info |

### Public `/dojo` Page

Lightweight, no Web3, no auth:

```
/dojo
├── Hero: "The Dojo — Where AI Traders Are Forged"
├── Stats: total bots, avg ELO, active matches
├── House Bots (The Arbiter family, ELO, match records)
├── Active Matches (spectating)
├── Leaderboard (ELO-sorted, tier badges)
├── CTA: "Build your bot → app.ggbots.ai"
└── Past Seasons toggle (S1 results)
```

### VIBE.md Alignment

- Border-based cards, no shadows
- Brass accent for active states, lock badges, tier highlights
- `font-mono` for ELO numbers, equity, timers
- `font-display` (Bodoni Moda) for section headers
- Semantic profit/loss colors for match scores
- Lock banner: `bg-[var(--accent)]/10 border-[var(--accent)]/20` (matches existing arena banner)
- Expandable cards: same pattern as S1 arena leaderboard

---

## 11. Implementation Phases

### Phase 1: Dojo Foundation
- Add `dojo_visible`, `elo_rating`, `is_house_bot` columns
- Public `/dojo/bots` + `/dojo/stats` endpoints
- `PUT /config/{id}/visibility` endpoint
- `EloTierBadge` shared component
- ELO badge on BotRail bot cards
- `'dojo'` tab in Forge TabNavigation (shell: ELO display, placeholder UI)
- Public `/dojo` page (leaderboard with placeholder 1200 ELO)
- S1 results via "Past Seasons" toggle

### Phase 2: ELO Engine
- `elo_history` table
- `core/arena/elo.py` (Sortino composite + ELO functions)
- Weekly rolling ELO scheduler job
- Real ELO values on leaderboard + bot rail
- ELO history in Dojo tab

### Phase 3: House Bots
- Sev creates/tunes The Arbiter configs (Standard, Rapid, Blitz)
- Mark `is_house_bot = true`
- Featured on public `/dojo` and in Forge challenge UI

### Phase 4: 1v1 Matches
- `dojo_matches` table
- `core/arena/dojo_mirror.py` — copy-trade mirror service
- `core/arena/matches.py` — full match lifecycle
- Mirror hook in orchestrator (alongside existing DGClaw mirror)
- Close mirror in all close paths (alongside `arena_sync`)
- Lock guards on all mutating endpoints
- Match lifecycle scheduler job
- `GET /dojo/can-enter/{config_id}` — entry gate check
- Challenge, accept, cancel, forfeit endpoints
- Match history + stats endpoints
- Frontend: DojoTab, EnterMatchPanel, ActiveMatchCard, MatchHistoryList, MatchDetail
- Frontend: ChallengeModal (House Bots + leaderboard)
- Frontend: DojoLockBanner on Configure tab
- Frontend: Lock states on ActivationBar, PositionsTable, BotManagementMenu
- Frontend: Active match spectating on public `/dojo`
- Public match detail endpoint (shareable URL)

---

## 12. Open Questions

### Resolved

1. **The Arbiter configs**: Arbiter exists as production bot. House Bot variants are **new separate configs** cloned from Arbiter's strategy/settings — original not modified. Sev tunes Rapid/Blitz variants.
2. **Arena page**: `/arena` stays as-is (S2 postponement + Degen Arena). Not touched for Dojo.
3. **Composite score visibility**: ELO change only in match summary. Full breakdown in expanded detail.
4. **Public `/dojo` page**: Separate new page, built after Forge Dojo tab is functional. Functionality-first.
5. **User-vs-user challenges**: Not at launch. House Bot challenges only for v1.
6. **House Bot symbols**: One symbol per House Bot. BTC/USDT for all three Arbiter variants in v1.

### Remaining

1. **Signal dispatch timing gap**: House Bot outputs once per cycle. Match account TP/SL can trigger between cycles, going IDLE with no signal until next cycle. Acceptable? (Inherent to cycle-based model.)
2. **`awareness_level` storage**: Add as field in `config_data.decision` JSONB? Or top-level column? JSONB is more consistent with existing config patterns.
3. **Match account cleanup**: Archived `dojo_match` configs accumulate. Retention policy needed? Or keep indefinitely (match history references them)?

---

## Revision History

- 2026-03-26: Initial design. Split from combined DOJO_AND_ARENA_S2.md. Sharpe → Sortino.
- 2026-03-27: Killed archetype entity. ELO on bots directly. Dojo as Forge third tab. Config snapshot per match.
- 2026-04-01: Copy-trade model (no duplicate LLM cost). Full lock system with entry gate and forfeit. Rich match history with composite breakdown. Traced full flow through existing codebase patterns (orchestrator mirror hook, arena_sync close pattern, config edit lock guard). House Bots revised: decision oracle model (opportunity-only, no positions, stateless signal dispatch to match accounts with IDLE/IN_POSITION state machine). Zero marginal cost per House Bot match. Dojo tab restricted to paper bots only (no live/Hyperliquid). Resolved open questions: House Bots cloned from existing Arbiter (not modifying original), BTC/USDT only for v1, no user-vs-user at launch, ELO-only display (composite detail on expand), public `/dojo` page deferred until Forge tab works.
