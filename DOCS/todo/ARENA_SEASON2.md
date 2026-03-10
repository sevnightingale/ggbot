# ggArena Season 2 — Design & Implementation Plan

**Status**: PLANNING
**Owner**: Sev
**Timeline**: March 10 - April 28, 2026
**Linked TODO section**: `## ggArena Season 2 + $GG Launch`

---

## Season Structure

```
TRAINING GROUNDS          REGISTRATION            COMPETITION              RESULTS
(edit freely)             (enter → lock)          (all reset to $10k)      ($GG prizes)
|────── 3 weeks ──────────|─── 1 week ────────────|────── 3 weeks ─────────|
Mar 10                    Apr 1                   Apr 7                    Apr 28
```

### Phase 1: Training Grounds (Mar 10 – Mar 31)
- Users create bots, tweak strategies, test indicators — business as usual
- Arena page updated with S2 timeline, rules, countdown to registration
- Season 1 results archived in a "Past Seasons" section
- No registration possible yet

### Phase 2: Registration (Apr 1 – Apr 6)
- Users can register any active bot for Season 2
- **Registration = immediate config lock** — no more edits to strategy, indicators, timeframes, trade settings
- Users can **unregister** during this week to unlock their bot and keep tweaking
- Registered bots still run normally during this week (trades don't count — reset on Apr 7)
- Registration closes Apr 6 23:59 UTC

### Phase 3: Competition (Apr 7 – Apr 28)
- All registered bots reset to $10,000 at Apr 7 00:00 UTC
- Bots remain locked — no edits, no unregistration
- Scoring: **Pure P&L %** (final balance vs $10k starting)
- Bots must be active for **at least 18 of 21 days** to be prize-eligible
- Bots with <18 active days still appear on leaderboard but marked ineligible
- Users still pay for bot usage (credits or usage-based subscription)

### Phase 4: Results (Apr 28+)
- Competition ends Apr 28 23:59 UTC
- Final scores snapshot taken
- Prize pool distributed from $GG token launch proceeds
- Results archived for future reference

---

## Rules (User-Facing)

1. **Entry**: Any active paper trading bot. Must have active subscription (usage-based or credits).
2. **Registration**: April 1-6. Once registered, your bot's strategy is locked.
3. **Unregister**: Allowed during registration week only. Unlocks your bot for editing.
4. **Starting Balance**: All bots reset to $10,000 on April 7.
5. **Scoring**: Highest P&L % wins. Final balance at April 28 23:59 UTC.
6. **Activity Requirement**: Bot must be active for at least 18 of 21 competition days. Bots below this threshold appear on leaderboard but are **ineligible for prizes**.
7. **No Edits During Competition**: Strategy, indicators, timeframes, and trade settings are frozen.
8. **Multiple Bots**: Users may enter multiple bots.
9. **Costs**: Users pay for their own bot's LLM usage (credits or subscription).
10. **Prize Pool**: Funded by $GG token launch proceeds. Exact amounts TBD based on token performance.

---

## Technical Design

### Option A: Separate Registration Table (RECOMMENDED)

New `arena_seasons` + `arena_registrations` tables. Clean separation from S1, extensible for future seasons.

```sql
CREATE TABLE arena_seasons (
    season_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,              -- "Season 2"
    training_start TIMESTAMPTZ NOT NULL,
    registration_start TIMESTAMPTZ NOT NULL,
    registration_end TIMESTAMPTZ NOT NULL,
    competition_start TIMESTAMPTZ NOT NULL,
    competition_end TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'training',  -- training, registration, competition, completed
    prize_description TEXT,                  -- "Funded by $GG token launch"
    rules_url TEXT,                          -- link to rules page
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE arena_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id INT REFERENCES arena_seasons(season_id),
    config_id UUID REFERENCES configurations(config_id),
    user_id UUID NOT NULL,
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    unregistered_at TIMESTAMPTZ,            -- NULL = still registered
    starting_balance NUMERIC DEFAULT 10000,
    final_balance NUMERIC,                  -- snapshot at competition end
    final_pnl NUMERIC,                      -- snapshot at competition end
    final_pnl_pct NUMERIC,                  -- (final - 10000) / 10000 * 100
    active_days INT,                        -- calculated at competition end
    eligible BOOLEAN DEFAULT TRUE,          -- false if < 18 active days
    rank INT,                               -- final leaderboard position
    UNIQUE(season_id, config_id)
);
```

**Config locking logic**: On every `PUT /config/{config_id}`, check:
```python
# In config update endpoint
registration = get_active_registration(config_id)
if registration and registration.unregistered_at is None:
    raise HTTPException(400, "Bot is locked for ggArena Season 2. Unregister to edit.")
```

**Advantages**:
- S1 data untouched (`is_public_performance` stays as-is)
- Clean season-level metadata (dates, status, rules)
- Per-registration tracking (balance snapshots, eligibility, rank)
- Easy to query "all S2 bots" without conflating with S1
- Future seasons trivial to add

**Disadvantages**:
- 2 new tables
- Need to seed S1 data if we want it queryable in same format (optional — S1 can stay as legacy)

### Option B: Extend Existing Schema

Add `arena_season INT` + `arena_locked_at TIMESTAMPTZ` columns to `configurations`. Reuse `is_public_performance` for leaderboard visibility.

**Advantages**: No new tables, simpler.
**Disadvantages**: Mixes season data into configs table, harder to query per-season, no clean place for season metadata, harder to track per-season results.

### Recommendation: Option A

The separate table is cleaner and we're already on Season 2 — this will scale.

---

## API Changes

### New Endpoints
- `POST /api/v2/arena/season/{season_id}/register` — Register bot for season
- `POST /api/v2/arena/season/{season_id}/unregister` — Unregister (registration week only)
- `GET /api/v2/arena/season/{season_id}/leaderboard` — S2 leaderboard
- `GET /api/v2/arena/season/{season_id}/status` — Season phase, dates, countdown
- `GET /api/v2/arena/seasons` — List all seasons with status

### Modified Endpoints
- `PUT /api/v2/config/{config_id}` — Add arena lock check
- `POST /api/v2/bot/{config_id}/start` — Allow (bot needs to run)
- `POST /api/v2/bot/{config_id}/stop` — Allow (but counts against 18-day requirement)

### Legacy Endpoints (S1 — keep working)
- `GET /api/v2/public/arena/performance` — S1 leaderboard (rename or version?)
- `POST /api/v2/bot/{config_id}/arena/register` — S1 registration (deprecated)

---

## Active Days Calculation

"Active day" = bot was in `active` state AND made at least 1 decision on that date.

```sql
SELECT COUNT(DISTINCT DATE(created_at)) as active_days
FROM decisions
WHERE config_id = %s
  AND created_at >= '2026-04-07T00:00:00Z'
  AND created_at < '2026-04-28T23:59:59Z'
```

Alternative: track state transitions. Simpler to just count decision days — if the bot made a decision, it was active.

---

## Frontend Changes

### Arena Page — Immediate (Training Grounds)
- Update hero: "Season 2" branding, training grounds countdown → registration countdown
- Add timeline visualization showing all 4 phases with current phase highlighted
- Add rules section (clear, numbered list)
- $GG token context — prize pool tied to token performance
- "Past Seasons" section — link to S1 results (same leaderboard, archived view)

### Arena Page — Registration Week
- "Register Bot" button appears (replaces countdown)
- Registration modal: select bot, confirm lock, enter
- Registered bots shown with "Locked" badge
- Unregister option available

### Arena Page — Competition
- Live leaderboard (same as S1 but reading from `arena_registrations` join)
- Locked/eligible badges on each bot
- No registration possible
- Countdown to competition end

### Forge — Config Locking UI
- If bot is registered: show banner "Locked for ggArena Season 2"
- Disable all edit controls (strategy, indicators, timeframes, trade settings)
- Show "Unregister to edit" button (registration week only)
- During competition: no unregister option, just "Locked" state

---

## Implementation Order

### Phase A: Arena Page Update (NOW — Training Grounds is live)
1. Update hero section with S2 branding + timeline
2. Add rules section
3. Add "Past Seasons" / S1 results section
4. Update countdown targets

### Phase B: Database + API (Before Apr 1)
1. Create `arena_seasons` + `arena_registrations` tables
2. Seed Season 2 row with dates
3. Build register/unregister endpoints
4. Add config lock check to PUT /config
5. Build S2 leaderboard endpoint

### Phase C: Registration UI (Before Apr 1)
1. New registration modal (select bot, confirm lock)
2. Registered bot badges in Forge
3. Config lock UI (disabled controls + banner)

### Phase D: Competition Operations (Apr 7)
1. Bulk reset script (like S1 but reads from `arena_registrations`)
2. Close registration window
3. Verify all bots locked + active

### Phase E: Results (Apr 28)
1. Snapshot final balances into `arena_registrations`
2. Calculate active days + eligibility
3. Set ranks
4. Results page

---

## Open Questions

1. **S1 leaderboard API**: Keep `/api/v2/public/arena/performance` as-is for S1? New endpoint for S2?
2. **$GG staking**: Does USX betting carry over to S2? Replace with $GG? Or remove betting for now?
3. **Telegram announcement**: Automated announcement when competition starts?
4. **Bot naming**: Should registered bots require a public name/description for the leaderboard?

---

## REVISION HISTORY

- 2026-03-10: Initial design based on discussion with Sev
