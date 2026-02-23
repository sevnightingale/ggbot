# Single Live Bot Slot + Strategy Versioning + Equity Tracking

**Status**: COMPLETE (Phase A backend + Phase B frontend)
**Created**: 2026-02-17
**Planning Transcript**: `~/.claude/projects/-home-sev-ggbot/d118227d-3941-41aa-9c35-5d675d7d37c5.jsonl`

---

## Context

Hyperliquid is **cross-margin** — all positions share one margin pool. The current multi-live-bot model (allocation validation, unique symbol enforcement, per-bot P&L attribution) creates complexity that doesn't map to on-chain reality. A single live bot slot is both simpler and safer.

Additionally, the current Hyperliquid equity tracking uses PnL-only (not real account balance), which was a compromise for the multi-bot shared-account model. With a single live bot, we can switch to proper equity tracking using the real Hyperliquid account value.

**Three workstreams:**
1. **Single Live Bot Slot** — one permanent live config per user, "Promote to Live" from paper bots
2. **Strategy Versioning** — `strategy_updated` activity type with full config snapshots
3. **Equity Tracking** — switch from PnL-only to real account balance for Hyperliquid

---

## User Flow (UX)

The live trading slot is **always visible** in BotRail, regardless of Hyperliquid connection status.

```
BotRail Layout:
┌──────────────────────────────┐
│ ⚡ Live Trading Slot         │  ← always pinned at top
│   [state depends on setup]   │
├──────────────────────────────┤
│ ○ Paper Bot 1                │  ← normal paper bots below
│ ○ Paper Bot 2                │
│ + Create new bot             │
└──────────────────────────────┘
```

### State 1: Hyperliquid NOT connected
- Slot is **grayed out** with text: "Connect Hyperliquid to go live"
- Clicking the slot → opens Hyperliquid setup modal (Settings > Live Trading)
- No config exists in DB yet

### State 2: Hyperliquid connected, no strategy promoted yet
- Live bot config **created automatically** during `POST /api/v2/hyperliquid/setup`
- Slot shows: "Your Live ggbot" with text: "Promote a paper bot's strategy"
- Gold/accent styling, but bot is inactive and has no strategy
- Cannot be activated (no extraction/decision config)

### State 3: Strategy promoted
- Slot shows the live bot with its promoted strategy (symbol, timeframe, etc.)
- Can be activated via Start button
- 3-dot menu: Rename, Reset Stats (no Delete — permanent slot)

### State 4: Hyperliquid disconnected (after previous connection)
- Live bot config **preserved** in DB (`trading_mode='hyperliquid'`, `state='inactive'`)
- Slot shows grayed out: "Reconnect to resume live trading"
- Strategy preserved — reconnecting doesn't require re-promoting
- Credentials deleted from Vault, but config slot remains

---

## Workstream 1: Single Live Bot Slot

### Backend Changes (✅ COMPLETE)

**`ggbot.py` — Remove multi-bot infrastructure:**
- ✅ Removed allocation validation (sum of `max_margin_percent <= 100%`) from `create_config`
- ✅ Removed unique symbol enforcement from `start_bot`
- ✅ Fixed latent bug: `start_bot` used `config.to_jsonb().get('trading_mode')` which was always None (trading_mode is a table column, not in JSONB). Changed to `config.trading_mode`.

**`ggbot.py` — Block direct live bot creation:**
- ✅ `create_config` returns 400 for `trading_mode='hyperliquid'`: "Use 'Promote to Live' to set up live trading"

**`ggbot.py` — Modify `start_bot`:**
- ✅ Single-live-bot safety net: if another hyperliquid bot is already active, block with error
- Credential check preserved

**`ggbot.py` — `POST /api/v2/bot/{config_id}/promote-to-live`:**
- ✅ Auth: requires subscription (`can_activate_bots`) + Hyperliquid connected
- ✅ Validates source bot exists, belongs to user, is not already live
- ✅ Finds existing live bot via `SELECT config_id FROM configurations WHERE user_id = %s AND trading_mode = 'hyperliquid'`
- ✅ UPDATE only — copies `selected_pair`, `extraction`, `decision`, `llm_config`, `trading` from source
- ✅ Does NOT copy: `config_name`, `telegram_integration`, `agent_strategy`
- ✅ Source paper bot stays running (useful for live vs paper comparison)
- ✅ Logs `strategy_updated` activity (see Workstream 2)
- ✅ Returns the live bot's config_id, version number

**`ggbot.py` — `POST /api/v2/hyperliquid/setup` (✅ COMPLETE):**
- ✅ Auto-creates live bot config after storing credentials (idempotent)
- ✅ Returns `live_config_id` in response

**`core/auth/vault_utils.py` — Modify disconnect:**
- ✅ Keep `trading_mode='hyperliquid'` but set `state='inactive'`
- ✅ Do NOT convert to paper — preserves the slot and strategy
- On reconnect: bot is ready to reactivate without re-promoting

### Frontend Changes (✅ COMPLETE — Phase B)

**`BotRail.tsx` — Pinned Live Slot (always visible): ✅**
- ✅ Render live slot ABOVE the paper bot list, all 4 states implemented
- ✅ Gold/accent left border, Zap icon, LIVE pill badge
- ✅ 3-dot menu: Rename, Reset Stats (not Reset Account), no Duplicate, no Delete

**`BotManagementMenu.tsx` — "Promote to Live" action: ✅**
- ✅ Rocket icon action for paper bots, confirm dialog, refreshes bot list after success

**`BotCreationModal.tsx` — Remove Live Trading mode: ✅**
- ✅ Paper-only (5 steps → 4), removed LiveTradingSetupModal trigger

**`TradeSettings.tsx` — Remove allocation bar: ✅**
- ✅ Removed allocation indicator, `allBots`/`currentConfigId` props

**`ConfigureLayout.tsx`: ✅**
- ✅ Removed `allBots` prop pass-through

---

## Workstream 2: Strategy Versioning (✅ COMPLETE)

**`ggbot.py` — In `promote-to-live` endpoint:**
- ✅ After copying config, calls `log_activity_safe()` with `activity_type='strategy_updated'`
- ✅ Details payload: version number, source config info, full config snapshot, changed fields
- ✅ `strategy_updated` already exists in `ACTIVITY_TYPES` dict — no schema change needed

**Version numbering:**
- ✅ `SELECT COUNT(*) FROM activities WHERE config_id = %s AND activity_type = 'strategy_updated'` → next version
- First promote = v1, second = v2, etc.

**Design decisions:**
- `initial_equity` only set on first live bot creation (during HL setup)
- Subsequent promotes preserve trading history (no reset)
- The `strategy_updated` activity captures the switch point
- Future: "show performance since last strategy_update" button in TV timeline (uses equity from activity)

**Future**: Revert endpoint (`POST /api/v2/bot/{config_id}/revert-strategy/{activity_id}`) — data supports it, not in this PR.

---

## Workstream 3: Equity Tracking for Hyperliquid

### Backend — The Fix Chain (✅ COMPLETE)

**1. `core/monitoring/adapters/hyperliquid_adapter.py`:**
- ✅ `current_balance=account_value` (was `None`)
- ✅ `available_balance=withdrawable` (was `None`)

**2. `core/domain/account_snapshot.py`:**
- ✅ `total_equity` for hyperliquid uses `balance + unrealized_pnl` (same as paper)

**3. `core/common/activity_logger.py`:**
- ✅ `balance_field` for hyperliquid uses `COALESCE(current_balance + unrealized_pnl, current_balance)` (same as paper)

**4. `initial_equity`:**
- Set from real Hyperliquid account value during `POST /api/v2/hyperliquid/setup`
- Not updated on subsequent promotes (preserves chart starting point)

### Frontend — Remove PnL-Only Assumptions (✅ COMPLETE — Phase B)

**5. `frontend/app/forge/page.tsx`: ✅**
- ✅ Hyperliquid uses `current_balance + unrealized_pnl` (same as paper)

**6. `frontend/app/forge/components/monitor/ActivationBar.tsx`: ✅**
- ✅ Hyperliquid uses paper-style KPIs (Total Equity, Available, Unrealized)

**7. `frontend/app/forge/components/monitor/PerformanceChart.tsx`: ✅**
- ✅ Hyperliquid uses real equity chart (not PnL-only mode)

---

## Implementation Order

### Phase A: Backend (✅ COMPLETE)
1. ✅ Remove multi-bot validation from `ggbot.py`
2. ✅ Add `promote-to-live` endpoint with strategy versioning
3. ✅ Block live bot creation via `create_config`
4. ✅ Fix equity tracking chain (adapter → snapshot → activity_logger)
5. ✅ Modify vault_utils disconnect behavior
6. ✅ Auto-create live bot in `POST /api/v2/hyperliquid/setup`

### Phase B: Frontend (✅ COMPLETE)
1. ✅ BotRail live slot (4 states)
2. ✅ BotManagementMenu "Promote to Live" action
3. ✅ Remove BotCreationModal live mode
4. ✅ Remove TradeSettings allocation bar
5. ✅ Fix equity display (page.tsx, ActivationBar, PerformanceChart)
6. ✅ Wire up live bot state in page.tsx + LiveTradingSetupModal

---

## Files Summary

| File | Changes | Status |
|------|---------|--------|
| `ggbot.py` | Remove allocation+symbol checks, promote-to-live endpoint, block live creation, auto-create on setup | ✅ |
| `core/auth/vault_utils.py` | Disconnect keeps live slot (inactive, not paper) | ✅ |
| `core/monitoring/adapters/hyperliquid_adapter.py` | `current_balance` + `available_balance` from real API data | ✅ |
| `core/domain/account_snapshot.py` | `total_equity` uses real equity for hyperliquid | ✅ |
| `core/common/activity_logger.py` | `balance_field` uses equity formula for hyperliquid | ✅ |
| `frontend/app/forge/components/layout/BotRail.tsx` | Pinned live slot UI (4 states) | ✅ |
| `frontend/app/forge/components/layout/BotManagementMenu.tsx` | "Promote to Live" action | ✅ |
| `frontend/app/forge/components/modals/BotCreationModal.tsx` | Remove live trading mode | ✅ |
| `frontend/app/forge/page.tsx` | Live bot state, fix equity metrics, LiveTradingSetupModal | ✅ |
| `frontend/app/forge/components/configure/TradeSettings.tsx` | Remove allocation bar | ✅ |
| `frontend/app/forge/components/configure/ConfigureLayout.tsx` | Remove allBots prop pass-through | ✅ |
| `frontend/app/forge/components/monitor/ActivationBar.tsx` | Real equity KPIs for HL | ✅ |
| `frontend/app/forge/components/monitor/PerformanceChart.tsx` | Real equity chart for HL | ✅ |
| `frontend/app/forge/components/layout/MobileNav.tsx` | Pass through liveBot/HL props | ✅ |
| `frontend/lib/api.ts` | `promoteToLive()` method | ✅ |
