# Community Feedback Fixes — March 2026

Consolidated planning doc for 4 issues surfaced in Telegram group (2026-03-07).

---

## 1. Live Config 404 Bug [HIGH — user-facing blocker]

**Reporter**: fr4nk05
**Symptom**: PUT `/api/v2/config/{config_id}` returns 404 for live bot configs.

**Root Cause**: Live bot slot auto-created at `ggbot.py:1588-1590` with `config_data = json.dumps({})`.
When `config_service.update_config()` loads this via `from_dict()`:
- Empty config_data -> `selected_pair = ""`
- `validate()` at `config_service.py:156` fails: `"selected_pair is required"`
- Returns `None` -> endpoint raises 404

Paper configs work because they're created via the full bot creation wizard (populated config_data).

**Fix**: Seed live slot with minimal valid config_data on creation. The live slot is always configured
via promote-to-live (copies paper bot strategy) or manual edit — but it must survive validation
in the intermediate "empty" state.

**Option A (recommended)**: Skip non-agent validation when config has no `selected_pair` yet AND
the update is adding one. Essentially: if existing config has empty `selected_pair`, allow the
update through without validating the *existing* state — validate the *result* instead.

**Option B**: Create live slot with a default `selected_pair` (e.g. "BTC/USDT") and stub
extraction/decision. Simpler but creates a "fake" config that might confuse the user.

**Option C**: Add an "unconfigured" concept to validation — skip validation entirely for configs
with empty `config_data`. Risk: could allow invalid saves.

**Recommendation**: Option A — validate the *merged result*, not the existing config. The current
code builds the merged `BotConfigV2` object and then validates it. The problem is that the merge
still produces an empty `selected_pair` when the user's update doesn't include one. This is
actually correct behavior (you shouldn't be able to save a config without a pair). The real fix
is that the *promote-to-live* flow should be the primary path for configuring the live slot.

**Simplest fix**: When validate() sees `selected_pair` is empty AND `trading_mode == 'hyperliquid'`,
treat it as valid (live bots start unconfigured and get strategy via promote). This unblocks
partial updates (like changing LLM model) on an already-promoted live bot too, since promoted
bots WILL have `selected_pair`.

Wait — re-reading the bug: fr4nk05 was trying to update the live config directly (not via
promote). The promote flow copies everything. If the user is editing a live bot that was
already promoted, it would have `selected_pair`. If it was never promoted, the config is empty.

**Actual simplest fix**: The empty live slot should not block updates that ADD valid data. The
issue is that `update_config()` validates BEFORE checking what changed. Fix `validate()` to be
lenient for hyperliquid configs that haven't been promoted yet (no `selected_pair`), OR fix
`update_config()` to only validate fields that are being changed.

**Files**: `ggbot.py:1588-1590` (creation), `core/services/config_service.py:143-165` (validation)
**Effort**: ~30min

---

## 2. Strategy Advisor Timeframe Collapse [MEDIUM] ✅ COMPLETED 2026-03-07

**Reporter**: Sev (observed), confirmed in Telegram group
**Symptom**: Strategy Advisor rewrites extraction config, collapsing multi-timeframe indicators
to a single timeframe without warning.

**Root Cause (two-part)**:

**Part A — deep_merge list replacement** (`api/assistant.py:569-577`):
`deep_merge()` recursively merges dicts but REPLACES non-dict values (including lists).
When Haiku sends `{"extraction": {"selected_data_sources": {"technical_analysis": {"timeframes": ["1h"]}}}}`,
the merge walks dicts until it hits `timeframes` (a list) and overwrites entirely.
`["5m","15m","1h","4h","1d"]` -> `["1h"]`.

**Part B — no system prompt guardrail**:
System prompt at `assistant.py:225-234` shows extraction structure with timeframes array but
doesn't warn Haiku to preserve existing timeframes. Haiku sees "update extraction" and sends
the full extraction block as it understands it — with only the timeframe it's thinking about.

**Fix (belt + suspenders)**:
1. **Prompt fix**: Add rule to system prompt: "NEVER include `timeframes` in extraction updates
   unless the user explicitly asks to change timeframes. Timeframes are user-configured and must
   be preserved. Only modify `data_points` within data sources."
2. **Code fix**: In `update_full_config()`, before deep_merge, detect if the update would
   overwrite `timeframes` and preserve the existing value. Special-case for known list fields
   that should be append-only or user-controlled.

**Files**: `api/assistant.py` (system prompt + deep_merge/update_full_config)
**Effort**: ~1-2hr

---

## 3. Credits vs Live Trading Funds UX [$GG LAUNCH — 3 days] COMPLETED 2026-03-07

**Reporter**: fr4nk05
**Symptom**: New user deposited $10 to Hyperliquid, expected that to cover everything. Couldn't
activate bot — no LLM credits. Estimated costs at "$72-132/week" (likely looking at premium tier).
No tutorial found.

**Analysis**: Two separate funding concepts exist with no clear explanation:
- **Trading funds**: USDC deposited to Hyperliquid (the bot trades with this)
- **LLM credits**: Platform credits or subscription (pays for AI decisions)

The ActivationBar shows estimated daily cost, but only AFTER a bot is configured. During the
HL setup flow, there's no mention of LLM credits being a separate requirement.

**Fix (scoped for 3-day deadline)**:
1. **ActivationBar enhancement**: When a live bot can't activate due to missing credits,
   show explicit message: "Bot needs LLM credits to run. Your Hyperliquid deposit is for
   trading — bot decisions are billed separately." Link to upgrade/credit purchase.
2. **HL setup flow**: Add a brief info card after successful HL connection:
   "Your trading funds are ready. To activate your bot, you'll also need LLM credits
   for AI decisions (~$X/day depending on settings)."
3. **Cost estimator visibility**: The UpgradeModal already has cost estimates. Surface the
   per-decision cost more prominently in the HL setup completion screen.

**Not in scope for launch**: Full tutorial/getting-started blog (already on SEO TODO).

**Files**: `frontend/app/forge/components/monitor/ActivationBar.tsx`, possibly
`frontend/app/forge/components/hyperliquid/LiveTradingModalContent.tsx`
**Effort**: ~1-2hr

---

## 4. Position Statefulness Toggle [MEDIUM — extends existing TODO]

**Reporter**: denisigin
**Existing TODO**: "Enhanced Position Statefulness" under Market Intelligence Expansion (~2-3hr)

**Current state**: Scheduled bots carry forward position context per cycle:
- Entry reasoning, confidence, entry price, holding time, unrealized P&L, SL/TP
- No arbitrary state persistence between cycles

**Denis's request**: Persistent state variables across cycles:
- `PeakEquity` — highest account equity seen (for drawdown-based rules)
- `ConsecutiveLosses` — loss streak counter (for cooldown logic)
- `CooldownRemaining` — cycles to skip after streak (deterministic state machine)

**Phased approach**:

### Phase 1: Enrich position management prompt (existing TODO, 2-3hr)
Add computed fields to position context that DecisionEngineV2 sends to the LLM:
- `bars_in_trade` — how many cycles this position has been open
- `max_drawdown_during_trade` — worst unrealized P&L seen (track via Redis)
- `avg_entry` — for future DCA support

These are derived from existing data, no new persistence needed.

### Phase 2: User-defined persistent state (new scope, 4-6hr)
- New `bot_state` JSONB column on `configurations` (or separate `bot_state` table)
- Toggle: `enable_persistent_state: true` in config_data (opt-in, not default)
- DecisionEngineV2 reads state at cycle start, LLM can update it via structured output
- Prompt engineering: LLM must reliably read/write JSON state variables
- Guardrails: max state size (e.g. 4KB), schema validation, audit trail

### Why opt-in toggle matters:
Existing bots have strategies tuned to current context window. Adding PeakEquity or
ConsecutiveLosses changes what the LLM sees, potentially altering behavior. Opt-in ensures
no regressions for existing users.

**Files**: `decision/engine_v2.py`, `core/services/config_service.py`, possibly
`trading/paper/supabase_service.py` (for Redis-tracked max drawdown)
**Effort**: Phase 1: 2-3hr, Phase 2: 4-6hr

---

## Priority Order

1. **Live config 404** — fix immediately (blocking real user)
2. **Credits vs funds UX** — before $GG launch (3 days)
3. **Advisor timeframe collapse** — next sprint (data-loss bug but workaround exists)
4. **Position statefulness Phase 1** — next sprint (enhancement, not bug)
5. **Position statefulness Phase 2** — backlog (needs design validation)
