# Work Session Plan — 2026-03-07

3 parallel Claude Code instances. Organized to minimize file overlap.

---

## CC1: Live Trading Audit (this instance)

**Goal**: Investigate Sev's live ggbot (1 week running), find duplicate close activity bug, verify full trade lifecycle integrity.

**Approach**: Read-only investigation. DB queries + log analysis + code review. Produces findings report, then fixes if needed.

**Tasks**:
1. Query `live_trades`, `activities`, and Hyperliquid fill history for Sev's live bot
2. Identify duplicate close activities — likely double-logging from `hyperliquid_service.close_position()` AND `hyperliquid_adapter` auto-detect
3. Verify P&L accuracy: compare activity-logged P&L vs actual fills vs account snapshots
4. Review entry/exit lifecycle completeness
5. Fix root cause of duplicates if confirmed

**Files touched**:
- Read-only: `trading/live/hyperliquid_service.py`, `core/monitoring/adapters/hyperliquid_adapter.py`, `core/common/activity_logger.py`
- Possible edits: `hyperliquid_adapter.py` OR `hyperliquid_service.py` (one of the two close-logging paths)

**No overlap with**: CC2 (backend API files), CC3 (frontend files)

---

## CC2: Backend Bug Fixes

**Goal**: Fix two backend bugs — Live Config 404 + Strategy Advisor timeframe collapse.

**Tasks**:
1. **Live Config 404**: Fix validation in `config_service.py` to allow updates on unconfigured live bot slots (empty `config_data`). May also adjust auto-create at `ggbot.py:1588-1590` to seed minimal config.
2. **Strategy Advisor Timeframe Collapse**: Add system prompt guardrail in `api/assistant.py` to prevent Haiku from sending `timeframes` in extraction updates. Add code guard in `update_full_config()` to preserve existing timeframes during deep merge.

**Files touched**:
- `core/services/config_service.py` (validation logic, lines 143-165)
- `ggbot.py` (only lines 1583-1590, live slot auto-create)
- `api/assistant.py` (system prompt + `update_full_config()` + `deep_merge()`)

**No overlap with**: CC1 (trading/monitoring files), CC3 (frontend files)

**Onboarding prompt**: "Read GO.md, then work on these two bugs from TODO.md:
1. Live Config 404 — see DOCS/todo/COMMUNITY_FIXES_MAR2026.md section 1. Root cause: live bot slot created with empty config_data at ggbot.py:1588-1590, validation fails in config_service.py:143-165.
2. Strategy Advisor Timeframe Collapse — see DOCS/todo/COMMUNITY_FIXES_MAR2026.md section 2. Root cause: deep_merge in api/assistant.py:569-577 replaces lists (timeframes), and system prompt doesn't warn Haiku to preserve them.
Only touch: config_service.py, ggbot.py (lines 1583-1590 ONLY), api/assistant.py. Do NOT touch frontend or trading/ files."

---

## CC3: Frontend Pre-Launch UX (Credits vs Funds)

**Goal**: Add clear UX messaging that separates trading funds (Hyperliquid deposit) from bot credits (LLM decisions) before $GG launch on March 10.

**Tasks**:
1. **ActivationBar**: When live bot activation is blocked by missing LLM credits, show explicit message distinguishing trading funds from bot credits. Include link to credit purchase.
2. **HL Setup Flow**: Add info card in `LiveTradingModalContent.tsx` after successful connection explaining the dual funding model.
3. **Optional**: Surface cost estimator more prominently during HL setup completion.

**Files touched**:
- `frontend/app/forge/components/monitor/ActivationBar.tsx`
- `frontend/components/hyperliquid/LiveTradingModalContent.tsx`
- Possibly `frontend/components/SettingsModal.tsx` (if adding info there too)

**No overlap with**: CC1 (trading/monitoring files), CC2 (backend Python files)

**Onboarding prompt**: "Read GO.md, then work on Credits vs Trading Funds UX from TODO.md — see DOCS/todo/COMMUNITY_FIXES_MAR2026.md section 3. New users confuse Hyperliquid deposit (trading funds) with LLM credits (bot decision costs). Add clear messaging in ActivationBar.tsx and LiveTradingModalContent.tsx. Only touch frontend/ files. Do NOT touch any Python backend files."

---

## File Overlap Matrix

| File Zone | CC1 | CC2 | CC3 |
|-----------|-----|-----|-----|
| `trading/live/`, `core/monitoring/adapters/` | WRITE | - | - |
| `core/services/config_service.py` | - | WRITE | - |
| `ggbot.py` (lines 1583-1590 only) | - | WRITE | - |
| `api/assistant.py` | - | WRITE | - |
| `frontend/` | - | - | WRITE |
| DB queries (read-only) | READ | - | - |

Zero write conflicts between any pair.

---

## After All Three Complete

- Update TODO.md (check off completed items)
- Update CHANGELOG.md
- Restart relevant PM2 services: `pm2 restart ggbot` (CC2 changes), `pm2 restart account-monitor` (if CC1 changes adapter)
- Frontend: git push for Vercel deploy (CC3 changes)
- Sev: test live config update, test advisor, verify ActivationBar messaging


