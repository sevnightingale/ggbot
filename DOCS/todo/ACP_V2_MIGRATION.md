# ACP v2 Migration + Live Trading Unification

> 🚨 **2026-04-24 — THIS DOC IS PARTIALLY SUPERSEDED.** Read [ACP_V2_SESSION_HANDOFF.md](ACP_V2_SESSION_HANDOFF.md) first. Key discoveries from a full day of live-testing:
>
> - The whole `/bridge-usdc-to-hl` approach is architecturally wrong. Deposits are ACP `perp_deposit` jobs, not on-chain bridges from the agent wallet.
> - DGClaw's provider agent is still on ACP v1 (`--legacy` flag). Our v2 SDK ↔ v1 provider interop is unverified.
> - User USDC must land on Base chain, not Arbitrum. Virtuals' Alchemy paymaster is Base-only.
> - Work is paused mid-pivot. User must choose between Option A (fix v2 path), B (revert to lite-agent pool), or C (ship existing HL self-custody + defer v2).
>
> The sections below describe the plan-as-designed, which is still valuable reference, but should NOT be executed without first reading the handoff doc.

## Current Status (2026-04-22, PRE-PIVOT)

**🟡 IN PROGRESS** — Phase 0 gate passed, Phase 1 partially shipped.

| Milestone | Status | Notes |
|-----------|--------|-------|
| Phase 0 gate | ✅ PASSED | Adapter compat verified against Privy-provisioned wallet |
| Pre-Phase-2 passive plumbing | ✅ SHIPPED | Commit `41df6fb` — `'virtuals'` accepted as trading_mode enum |
| Phase 1 acp-node scaffold | ⚠️ PARTIAL | Commits `c1c6615` + `011dbee` — 3/6 routes live |
| Phase 1 Python backend | 🟡 Not started | `arena_agents_v2` migration + `api/arena_v2.py` + Vault methods |
| Phase 2+3 atomic release | 🟡 Not started | |
| Phase 4 DB-gated cleanup | 🟡 Not started | |

### Key plan corrections after Phase 0 research

1. **Public key format** — original plan didn't specify; first attempt used raw X9.62 uncompressed point (`BC...` base64), got 500 on signer approve. Privy requires base64-SPKI-DER (`MFkw...`). Fixed in `api/acp_v2_test.py:_generate_p256_keypair`.
2. **acp-node brought forward** — original plan deferred the Node sidecar to Phase 4 (for Sebastian's marketBrief provider only). Moved to Phase 1 because user-side CLI setup ("run dgclaw-skill locally") is terrible UX; sidecar automates all Privy-signed HL operations.
3. **Signing layer unified** — plan originally implied we'd reverse-engineer Privy's session-signer API. Instead we use `PrivyAlchemyEvmProviderAdapter` from `@virtuals-protocol/acp-node-v2` directly — same abstraction acp-cli uses. ~20 lines of `privy-sign.ts` instead of custom protocol work.
4. **DGClaw setup is 8 steps, not 4** — `dgclaw-skill/references/api.md` exposed leaderboard-join (ACP buyer job), USDC deposit bridge, forum posting. Added to Phase 1 acp-node + Phase 2+3 orchestrator hooks.
5. **AI Council reasoning channel is forum posts** — `POST https://degen.virtuals.io/api/forums/:agentId/threads/:threadId/posts`. Adds `forum-post` sidecar route + orchestrator hook in Phase 2+3 (alongside existing dojo/arena mirror hooks).
6. **`sebastian-virtuals` stays running in Phase 1+** — confirmed via code read that only Section C (ACP buyer monitor for Otto/BlackSwan) is load-bearing. `sebastian-virtuals` deletion deferred to Phase 4 when v1 arena mirror dies; not replaced by acp-node (different responsibilities).

See `TODO.md` → ACP v2 section for the current actionable checklist.

---

## Original Plan (below, preserved for context)

**Status**: 🔴 HIGH PRIORITY — Virtuals mandating v2 registry migration. v1 Python SDK (`virtuals-acp==0.3.23`) cannot drive v2-migrated agents. All ggbots-owned agents show "Upgrade Now" banner on app.virtuals.io.

**Scope**: Migrate from v1 ACP-mirror architecture to v2 direct-HL-via-agent-wallet. Introduce `trading_mode='virtuals'` as the canonical live-trading mode. "Deploy Live Version" becomes the standard path for turning paper bots into live bots. Keep legacy `trading_mode='hyperliquid'` (single self-custody slot per user) as a fallback for crypto-native users. Reuse the existing per-bot arena button + modal UX — no new navigation surfaces.

**Related**:
- Virtuals migration doc: `whitepaper.virtuals.io/acp/acp-concepts-terminologies-and-architecture/migrate-existing-agents`
- Node SDK: `github.com/Virtual-Protocol/acp-node-v2` (Sebastian provider only)
- CLI reference: `github.com/Virtual-Protocol/openclaw-acp`
- DGClaw-skill: `github.com/Virtual-Protocol/dgclaw-skill` (HL unified account + API wallet setup)
- [NOTE.md](../../NOTE.md) — v1→v2 concept reference

---

## Context

### Why this change is needed

- Virtuals forced migration — all agent pages show "Upgrade Now" banner
- Our Python SDK is v1; no Python v2 SDK planned. Node SDK (`@virtuals-protocol/acp-node-v2`) is the only v2 path
- v2 redesigns DGClaw: agents trade **directly on Hyperliquid through the Virtuals-provisioned Privy wallet**. No ACP-job queue, no claw API trade intermediary. DGClaw becomes a leaderboard + AI Pot overlay that reads HL state by wallet address
- The existing `_execute_claw_arena_trade` / `_enqueue_arena_trade` mirror pattern is obsolete — in v2 the agent *is* the trader

### The architectural shift (why this is actually simpler than it sounds)

**Current (v1):** bot runs in its primary trading mode (paper / hyperliquid) → decision is made → orchestrator *also* mirrors the trade to DGClaw via ACP job queue or claw API. Two execution paths per trade. ~500 lines of `trading/virtuals/` code.

**New (v2):** a ggbot is *either* paper, hyperliquid self-custody (legacy), *or* virtuals (new live trading path). The virtuals bot has a Virtuals-provisioned wallet that is simultaneously a Privy smart wallet on Base and an HL master account. Trades go direct to HL via the agent's API wallet. DGClaw reads the wallet's HL state for leaderboard. **No mirroring. No parallel execution. One trade, one path.**

### What this unlocks

- **Multi-wallet per user**: each virtuals bot has its own isolated Privy-provisioned wallet + HL master account. User-connected EOA no longer constrains bot count
- **"Deploy Live Version"** (replaces "Promote to Live"): duplicates a paper bot as a new `trading_mode='virtuals'` bot. Unlimited live bots per user in virtuals mode
- **DGClaw arena participation**: automatic for virtuals bots. Leaderboard presence, AI Pot eligibility, token burns — organic growth mechanic
- **Monitoring works unchanged**: HL Info API is wallet-address-driven and public. `HyperliquidAccountAdapter.get_current_snapshot()` works on any HL wallet — including Privy-provisioned ones (to be verified in Phase 0b)

### Custody trade-off (explicit, surfaced to users)

We accept a **custodial-but-revocable** model for virtuals bots:
- We generate + store per-agent signer private keys in Supabase Vault
- Users can revoke our signer at any time via Virtuals dashboard → instant lockout
- Alternative (non-custodial) requires 3+ signing popups per bot setup — rejected for UX
- Transparent in product copy: "ggbots holds a signing key you can revoke anytime"
- **The existing `trading_mode='hyperliquid'` path remains available** for crypto-native users who want pure self-custody (1 live bot per user, unchanged flow)

### Trading mode matrix

| Mode | Provisioning | Custody | Multi-bot | Arena | Notes |
|------|--------------|---------|-----------|-------|-------|
| `paper` | Local config only | n/a | Yes | No | Unchanged |
| `hyperliquid` | User connects own wallet | Non-custodial | No (1/user) | No | Legacy path, kept for crypto-natives. No new bots here. |
| `virtuals` | Virtuals agent + Privy wallet, provisioned by ggbots | Custodial-revocable | Yes (N/user) | Yes (automatic) | New canonical live-trading path |

---

## Phase 0a: Popup UX Validation (first gate)

**Purpose**: Prove the 2-popup flow actually works before committing to integration. De-risks the entire migration.

### Test Page

`frontend/app/test/acp-v2/page.tsx` — standalone, unlinked from main nav, admin-only gate (redirect non-admin users).

### Popups tested in isolation

**Popup 1 — Virtuals auth (once per user):**
- Button "Connect Virtuals"
- Frontend → backend `POST /auth-start` → returns `{authUrl, requestId}`
- Opens `authUrl` via `window.open()` (NOT iframe — Virtuals sets `X-Frame-Options: SAMEORIGIN`)
- Frontend polls `/auth-poll?requestId=X` every 2s
- Backend polls `acpx.virtuals.io/api/auth/lite/auth-status?requestId=X`
- On success: returns JWT, stored in Redis keyed on requestId (10-min TTL)
- Display truncated JWT + "connected ✓" state
- **Verify**: popup auto-close behavior, branding, total duration

**Popup 2 — Add-signer approval (once per agent):**
- Button "Create Test Agent + Signer" (gated on popup 1 completion)
- Backend creates agent via `POST acpx.virtuals.io/api/agents/lite/key` → returns `{id, walletAddress, apiKey}`
- Backend generates P-256 signer keypair locally (store private key in Vault, public key sent to Virtuals)
- Backend calls `add-signer-with-url` equivalent → returns `signerUrl + requestId`
- Frontend opens `signerUrl` in popup
- Frontend polls backend → backend polls Virtuals for signer status
- On completion: signer registered, all credentials stored
- **Verify**: popup auto-close, public key display, approval UX

### Backend endpoints (admin-only)

New file: `api/acp_v2_test.py`

- `POST /api/v2/acp-test/auth-start` → `{authUrl, requestId}`
- `GET /api/v2/acp-test/auth-poll?requestId=X` → `{status, jwt?}`
- `POST /api/v2/acp-test/agent-create` → `{agent, signerUrl, signerRequestId}`
- `GET /api/v2/acp-test/signer-poll?requestId=X` → `{status, agent?}`

Auth: `ADMIN_USER_ID` check (same pattern as `api/admin.py`). Non-admin returns 403.

### Success criteria

- Both popups complete without manual intervention (no copy-paste, no dev-tools tricks)
- Popup auto-closes cleanly OR we have a clear "click to close" fallback pattern
- End-to-end setup completes in under 30 seconds
- Agent + signer visible on app.virtuals.io after flow completes
- No DB changes, no Vault writes outside test scope, no integration with production bots

### Gate decision

If Phase 0a fails:
- Popups clunky / don't auto-close → fallback to redirect + callback URL flow
- Browser blocks popups consistently → consider CLI subprocess on backend or cooperative iframe workaround
- Setup takes too long or fails mid-flow → pause migration, reconsider approach

**Do NOT proceed to Phase 0b or Phase 1 until Phase 0a passes.**

---

## Phase 0b: Monitoring Compatibility Validation (second gate)

**Purpose**: Verify our existing `HyperliquidAccountAdapter` + SSE dashboard pipeline works against Virtuals-provisioned Privy wallets. The risk: Privy smart wallets *may* be ERC-4337-style contract wallets with edge-case HL behavior (e.g., around `withdrawable`, spot-perp unified account semantics). HL's Info API is wallet-address-driven and theoretically agnostic, but we must prove it.

### Why this is a separate gate (not assumed to work)

Current monitoring stack (`core/monitoring/adapters/hyperliquid_adapter.py`):
- `info.user_state(wallet)` → `marginSummary`, `assetPositions`, `withdrawable` (hyperliquid_adapter.py:85)
- `info.user_fills_by_time(wallet, ms)` → fill history with `closedPnl` (hyperliquid_adapter.py:292)
- Takes **only the wallet address** as input — no key, no signer
- Produces provider-agnostic `AccountSnapshot` consumed by SSE (`core/sse/dashboard_data.py`)

High confidence this Just Works for v2 wallets, but we must verify before building Phase 1 against an assumption.

### Test flow (extends Phase 0a test page)

Gated on Phase 0a completion. On the same admin-only test page, add a "Verify Monitoring" button that runs against the agent wallet from Phase 0a:

1. **Fund test**: user sends $5-10 USDC to the agent wallet on Base (or we fund from a reserve)
2. **Bridge + deposit to HL**: use dgclaw-skill equivalents (`activate-unified-account`, bridge if needed) so the wallet has balance on HL
3. **Execute minimal test trade**: $5 of ETH long at market, using the agent's API wallet credentials
4. **Query `info.user_state(agent_wallet)`**: verify response shape matches what the adapter expects. Log full JSON for visual inspection.
5. **Query `info.user_fills_by_time(agent_wallet, recent)`**: verify the test trade fill is present with correct `coin`, `sz`, `px`, `dir`
6. **Close position**: market close, verify `closedPnl` appears in subsequent `user_fills_by_time` query
7. **Invoke `HyperliquidAccountAdapter.get_current_snapshot(test_config_id)`** directly against the agent wallet: verify returns a complete `AccountSnapshot` with `account_value`, `unrealized_pnl`, `positions`, trade stats populated
8. **Dump snapshot JSON** next to a reference snapshot from an existing v1 HL bot for visual comparison

### Backend endpoints (admin-only, additive to Phase 0a)

- `POST /api/v2/acp-test/verify-monitoring-trade` → executes $5 ETH test trade via agent wallet
- `GET /api/v2/acp-test/verify-monitoring-snapshot?wallet=X` → runs adapter, returns AccountSnapshot JSON + raw HL responses

### Success criteria

- All 3 HL Info API queries return structurally correct data
- `AccountSnapshot` object populates completely (no zero/null where it shouldn't be)
- Fill data contains `closedPnl` after close (verifies realized P&L path)
- Visual diff vs. reference snapshot shows no semantic mismatches

### Gate decision

If Phase 0b fails:
- Shape mismatch on Privy wallet → narrow: is it contract-wallet semantics or something else?
- `withdrawable` behaves differently → doc it, adapt adapter if feasible
- If adapter incompatibility is deep (e.g., assetPositions missing) → reconsider v2 migration; may need to wait for Privy/HL compatibility or use different wallet provider

**Do NOT proceed to Phase 1 until Phase 0b passes.**

---

## Phase 1: Backend Foundations

**Goal**: Build credential management and agent provisioning pipeline without touching production trading.

### New DB table: `arena_agents_v2`

Distinct from existing `arena_agents` (v1 table stays until Phase 5).

```sql
CREATE TABLE arena_agents_v2 (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL REFERENCES auth.users(id),
  config_id uuid REFERENCES configurations(config_id),
  virtuals_agent_id text NOT NULL,
  agent_name text NOT NULL,
  agent_wallet_address varchar(42) NOT NULL,
  wallet_id text NOT NULL,                      -- Privy wallet ID
  signer_private_key_vault_id uuid NOT NULL,
  api_key_vault_id uuid NOT NULL,
  hl_api_wallet_key_vault_id uuid,
  status text NOT NULL DEFAULT 'provisioning',  -- 'provisioning' | 'active' | 'retired'
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_arena_v2_user ON arena_agents_v2(user_id);
CREATE INDEX idx_arena_v2_config ON arena_agents_v2(config_id) WHERE config_id IS NOT NULL;
CREATE UNIQUE INDEX idx_arena_v2_config_unique
  ON arena_agents_v2(config_id) WHERE config_id IS NOT NULL AND status = 'active';
```

Migration file: `database/migrations/add_arena_agents_v2.sql`

### New backend endpoints

New file: `api/arena_v2.py` — production endpoints for the v2 flow.

- `POST /api/v2/arena/connect-start` — initiate Virtuals auth flow (popup 1) for current user
- `GET /api/v2/arena/connect-poll?requestId=X` — poll for JWT completion; store encrypted in user_profiles or Redis
- `POST /api/v2/arena/deploy-live` — body: `{source_config_id, agent_name?}`. Duplicates the paper config as a new `trading_mode='virtuals'` config. Returns `{new_config_id, signerUrl, signerRequestId}` for popup 2.
- `GET /api/v2/arena/deploy-poll?requestId=X` — poll signer approval + headless DGClaw setup (`activate-unified-account`, `add-api-wallet`). Returns `{status, config_id, agent_wallet_address}` when complete.

### Reused endpoints (existing `api/virtuals_arena.py`)

The per-bot management surface stays. We rewire the backing data source from v1 `arena_agents` → v2 `arena_agents_v2`, but keep the endpoint shape and URLs:

- `GET /api/v2/virtuals-arena/status?config_id=X` — wallet, balance, positions (reads `arena_agents_v2` for v2 bots)
- `POST /api/v2/virtuals-arena/check-deposit` — scan agent wallet for incoming USDC, auto-bridge
- `POST /api/v2/virtuals-arena/withdraw` — pull funds back to user's connected wallet
- `GET /api/v2/virtuals-arena/leaderboard` — DGClaw leaderboard data (unchanged)

The `/join` endpoint is deprecated — replaced by `/api/v2/arena/deploy-live`.

### New Vault methods

In `core/auth/vault_utils.py`:

- `store_arena_v2_credential(agent_record_id, signer_key, api_key, hl_api_key)` — stores all 3 keys, returns vault IDs
- `get_arena_v2_credential(config_id)` — fetches all credentials for a bot's trade execution
- Pattern: model on existing `store_arena_credential` at `core/auth/vault_utils.py:751-825`

**No changes to orchestrator or trading services in this phase.** Pure scaffolding.

---

## Phase 2: Live Trading Service Refactor (dependency injection)

**Goal**: Make `hyperliquid_service.py` credential-source-agnostic. Route `trading_mode='virtuals'` bots through the existing HL execution code with v2 credentials.

### Current state

`trading/live/hyperliquid_service.py:74-150` — `execute_trade_intent()` calls `VaultManager.get_hyperliquid_credential(user_id)` which reads from `user_profiles.hyperliquid_vault_id` + `user_profiles.hyperliquid_wallet_address`.

Orchestrator dispatch at `core/orchestrator/orchestrator.py:1424-1426` currently only has `'hyperliquid'` case (plus paper).

### Refactor

Extract credential fetching into a helper that switches on `config.trading_mode`:

- `trading_mode='hyperliquid'` → `VaultManager.get_hyperliquid_credential(user_id)` (existing, unchanged)
- `trading_mode='virtuals'` → `VaultManager.get_arena_v2_credential(config_id)` (new, per-bot)

Add `'virtuals'` case to orchestrator trading dispatch:

```python
if config.trading_mode == 'hyperliquid':
    trade_result = await hyperliquid_trading.execute_trade_intent(config, ..., creds_source='user_profiles')
elif config.trading_mode == 'virtuals':
    trade_result = await hyperliquid_trading.execute_trade_intent(config, ..., creds_source='arena_v2')
```

### Monitoring adapter update

`core/monitoring/adapters/hyperliquid_adapter.py:39-54` — `_get_wallet_address` currently reads from `user_profiles` via `VaultManager.get_hyperliquid_credential`. Update to check `config.trading_mode`:
- `'hyperliquid'` → user-level credential (unchanged)
- `'virtuals'` → per-config credential from `arena_agents_v2.agent_wallet_address`

### Zero-impact guarantee for legacy HL users

Existing hyperliquid bots (current ~2 live) continue on the `user_profiles` path unchanged. Virtuals bots are an additive path, same downstream HL execution code, different credential fetcher.

---

## Phase 3: "Deploy Live Version" UX (replaces Promote to Live, reuses arena button)

**Goal**: Rewire existing arena UX surfaces as the entry point for v2 live trading. Delete the 3-dot-menu "Promote to Live" button entirely. No new navigation surfaces.

### Why we reuse, not rebuild

The existing degen arena flow (button on ActivationBar → per-bot modal → wallet management → fund/withdraw/positions) is structurally *exactly* what Deploy Live Version needs. The only difference is what the button creates under the hood. Reusing means:
- ~850 lines of working code preserved
- Zero new navigation / menus / hidden features
- Existing status polling, wallet display, and deposit UX inherited for free
- Discovery is automatic — the button is already where users look

### Three button states on `ActivationBar`

The existing `ActivationBar` "Enter Degen Arena" button (`frontend/app/forge/components/monitor/ActivationBar.tsx:487-503`) becomes tri-state based on the selected bot's `trading_mode` + its linked agent's lifecycle:

| Bot state | Button label | Action |
|-----------|--------------|--------|
| `trading_mode='paper'` (no v2 agent yet) | **"Deploy Live Version"** | Opens `DeployLiveModal` in setup mode |
| `trading_mode='virtuals'` (agent provisioning / no funds) | **"Live Bot: Needs Funds"** | Opens modal in funding state |
| `trading_mode='virtuals'` (agent active + funded) | **"Manage Live Bot"** | Opens modal in management state |
| `trading_mode='hyperliquid'` (legacy self-custody) | (button hidden) | N/A — legacy path has its own pinned bot rail slot |

### Modal repurposing

Existing component: `frontend/components/degen-arena-modal.tsx` (608 lines).

**Rename & repurpose** → `frontend/components/DeployLiveModal.tsx`.

**Rewrite content for setup state** (replaces today's "join arena" flow):
- Explain: "Deploy a live version of this bot. A new ggbot will be created with the same strategy, trading real USDC on Hyperliquid via a dedicated Virtuals agent. Your paper bot stays untouched."
- Agent naming: field pre-populated from source config name + user-editable (see Open Questions)
- Connection check: if no Virtuals session → inline "Connect Virtuals" (popup 1) → session established
- Deploy button → triggers popup 2 (signer approval) + headless DGClaw setup
- Progress UI during headless steps (activate-unified-account, add-api-wallet)
- On complete → transitions to funding state with agent wallet address

**Funding state** (mostly kept from today):
- Agent wallet address + copy button (existing)
- "Send USDC on Base to this address" instructions (existing)
- "Check deposit" button (existing — hits `/api/v2/virtuals-arena/check-deposit`)
- Auto-bridge to HL on deposit (existing behavior)

**Management state** (kept from today, light edits):
- Arena balance display (existing)
- Open positions with live P&L (existing)
- Withdraw form (existing)
- **New**: "View on Degen Arena leaderboard" link — prominent, since arena participation is automatic
- **New**: agent name + "edit name" pencil (if Virtuals allows rename post-creation — verify)
- **Remove**: bot-must-be-active gate (lines 237-275) — deploy-live works on any paper bot regardless of state

### Wiring changes in `ActivationBar`

- `onDegenArena` handler renamed → `onDeployLive` / `onManageLiveBot` (same handler, different semantic)
- Button label logic updated to the 4-state table above
- Drop the arena status fetching (`fetchArenaStatus` at line 123) in favor of checking the bot's own `trading_mode` + linked `arena_agents_v2.status`
- Keep auto-polling to refresh balance + positions when modal is open

### "Promote to Live" deletion

- Remove "Promote to Live" menu item from bot rail 3-dot menu (`frontend/app/forge/components/layout/BotManagementMenu.tsx`, wherever rendered)
- Delete `POST /api/v2/bot/{config_id}/promote-to-live` endpoint (`ggbot.py:3050-3152`)
- Delete related frontend API client method (`frontend/lib/api.ts`)

### Settings page — Connect Virtuals section

`frontend/app/settings/page.tsx` — in the existing "Live Trading" section of `SettingsModal.tsx`, add a new subsection above the existing Hyperliquid subsection:

- **"Connect Virtuals"** — button triggers popup 1 if not connected. Shows "connected ✓" with session expiry timestamp when active. Disconnect button.
- Existing **"Connect Hyperliquid"** section stays verbatim — for crypto-native self-custody users.

Both sections are independent. Users can connect either, both, or neither.

### BotRail — no structural change

- Virtuals bots appear in the normal "Paper Bots" section (since they are user-level bots, just with `trading_mode='virtuals'`) — *OR* we add a small new "Live Bots" section between the pinned Hyperliquid slot and the Paper Bots list. **Decision needed** (see Open Questions).
- Existing "Hyperliquid ggbot" pinned slot (for legacy `trading_mode='hyperliquid'`) kept as-is. Rename label from "Live Trading" → "Hyperliquid ggbot" for clarity once virtuals mode exists.

### One-live-bot-per-user constraint

- `ggbot.py:2948-2962` constraint stays **only for `trading_mode='hyperliquid'`** (architectural: user's own wallet = single HL account = single bot)
- `trading_mode='virtuals'` has no limit — each bot gets its own Privy-provisioned wallet

---

## Phase 4: Admin Bot Migration + Sebastian Provider Migration + Cleanup

**Goal**: Migrate admin bot, migrate Sebastian to v2 Node sidecar, delete all v1 mirror code.

### Admin bot trade migration

- Admin bot: config `b9d9bf00-a89a-4df7-9f7f-abcfff7e7d85` ("Your Live ggbot", BTC/USDT, hyperliquid mode)
- On `degen.virtuals.io/dashboard` → click "Migrate" → closes open BTC long, transfers $58 USDC to new v2 wallet
- Manually deploy a new virtuals bot via Phase 3 flow, point at migrated agent
- Deactivate old `trading_mode='hyperliquid'` admin bot

### Sebastian marketBrief provider migration (ACP-only, NOT trading)

Sebastian is our ACP provider selling daily market conditions reports to other agents (Otto AI etc.). Currently v1 Python SDK.

- Current: `sebastian_virtuals.py` sections A/B/C + `core/services/acp_client.py` + `virtuals-acp==0.3.23`
- Target: new `acp-bridge/` Node sidecar using `@virtuals-protocol/acp-node-v2`
- Scope: **provider role only**, no trade execution (trades go direct-HL via Phase 2 refactor)
- Sidecar responsibilities:
  - Event-driven `agent.on("entry")` handler
  - `job.created` → read JSON schema of `marketBrief` offering, validate
  - `job.funded` → read latest `market_conditions` row from Postgres, call `session.submit(report)`
- Sebastian needs own v2 agent wallet + signer (separate from user agents)
- Location: `acp-bridge/` at repo root (~200-300 lines TypeScript)
- PM2 entry added to `ecosystem.config.js`, replacing `sebastian-virtuals`

### Code cleanup (after 1 week of stable Phase 3 in production)

**Delete outright — the entire mirror architecture:**
- `trading/virtuals/dgclaw_service.py` (v1 ACP-based trading)
- `sebastian_virtuals.py` (replaced by `acp-bridge/` Node sidecar)
- `core/services/acp_client.py` (v1 ACP Python SDK wrapper)
- `trading/virtuals/claw_api.py` trade methods (`create_trade`, `close_trade`, `get_dgclaw_positions`, etc.) — keep account-management methods if referenced elsewhere, or delete file entirely if not
- `_enqueue_arena_trade`, `_execute_claw_arena_trade`, `_reconcile_arena_position`, `_get_user_arena_agent`, `_arena_to_pair` in `core/orchestrator/orchestrator.py`
- `arena:trade_queue` Redis queue references
- Orchestrator mirror block at `core/orchestrator/orchestrator.py:255-263` (the `arena_agent = ...; if arena_agent: ...; elif self._is_arena_enabled(config): ...`) and equivalent at line 376 — deleted wholesale
- `is_public_performance` field logic (subsumed by `trading_mode='virtuals'`), unless kept as a separate leaderboard-visibility toggle — decide at time

**Simplify:**
- `trading/virtuals/arena_sync.py` — drastically smaller. Close detection happens via existing `hyperliquid_adapter._detect_and_log_closes`, no special arena close-sync paths

**Remove dependency:**
- `virtuals-acp==0.3.23` from `requirements.txt`

**Keep (for Phase 5):**
- Legacy `arena_agents` table until v1 users migrated
- `ArenaRegistrationModal` (S2 registration) — orthogonal to this migration

---

## Phase 5: Existing Arena Users Migration

Sebastian (the user) will handle this manually at the end of the migration. Out of scope for planning — mentioned here for completeness only.

---

## Critical Files

### Backend
- `api/acp_v2_test.py` — NEW (Phase 0a + 0b admin-only test endpoints)
- `api/arena_v2.py` — NEW (Phase 1+ production endpoints: connect-start, connect-poll, deploy-live, deploy-poll)
- `api/virtuals_arena.py` — MODIFIED (rewire data source to `arena_agents_v2`, deprecate `/join`)
- `core/auth/vault_utils.py` — add `store_arena_v2_credential` / `get_arena_v2_credential`
- `core/services/config_service.py` — add `'virtuals'` trading_mode enum value
- `core/orchestrator/orchestrator.py:1424-1426` — add `'virtuals'` dispatch case; delete mirror block at lines 255-263 + 376
- `trading/live/hyperliquid_service.py:74-150` — refactor credential source to be per-config
- `core/monitoring/adapters/hyperliquid_adapter.py:39-54` — update `_get_wallet_address` to check `trading_mode`
- `database/migrations/add_arena_agents_v2.sql` — NEW migration

### Frontend
- `frontend/app/test/acp-v2/page.tsx` — NEW (Phase 0a + 0b test page)
- `frontend/components/degen-arena-modal.tsx` → renamed `DeployLiveModal.tsx` — REPURPOSED (keep structure, rewrite setup-state content)
- `frontend/app/forge/components/monitor/ActivationBar.tsx:475-503` — MODIFIED (button label logic, rewire handlers)
- `frontend/app/forge/components/layout/BotManagementMenu.tsx` — MODIFIED (remove "Promote to Live" menu item)
- `frontend/components/VirtualsConnectButton.tsx` — NEW (Settings popup 1 handler)
- `frontend/components/SettingsModal.tsx:245-320` — MODIFIED (add "Connect Virtuals" subsection above Hyperliquid)
- `frontend/lib/api.ts:104` — add `'virtuals'` to `trading_mode` union type; add `deployLive()` client method; remove `promoteToLive()`

### Node sidecar (Phase 4 only, Sebastian)
- `acp-bridge/` — NEW directory with minimal Node service using `@virtuals-protocol/acp-node-v2`
- `ecosystem.config.js` — add PM2 entry

### Reused references
- `core/auth/vault_utils.py:751-825` — existing `store_arena_credential` pattern
- `api/virtuals_arena.py` — existing status/check-deposit/withdraw endpoints (rewired, not replaced)
- `frontend/components/degen-arena-modal.tsx` — existing modal structure (repurposed)
- `frontend/app/forge/components/monitor/ActivationBar.tsx` — existing button pattern (repurposed)
- `api/admin.py` — admin-only auth gate pattern for Phase 0 endpoints

---

## Verification

### Phase 0a
1. Visit `/test/acp-v2` as admin user
2. Click "Connect Virtuals" → popup opens → sign in → popup closes → "connected ✓" shown
3. Click "Create Test Agent" → popup opens for signer approval → approve → popup closes → agent details shown
4. Visit `app.virtuals.io/acp/agents` → verify test agent exists with wallet as owner + signer registered
5. Document: total time, popup behaviors, branding UX, any manual steps needed

### Phase 0b
1. After Phase 0a passes, on same test page, click "Verify Monitoring"
2. Fund agent wallet with $5-10 USDC on Base
3. Bridge to HL + execute test trade (auto-flow)
4. Click "Run Adapter" → dumps `AccountSnapshot` JSON + raw HL response JSON
5. Visually diff against reference snapshot from existing v1 HL bot
6. Close position, re-run adapter, verify `realized_pnl` flows correctly

### Phases 1-3
1. Create a test paper bot (any strategy)
2. Click "Deploy Live Version" on ActivationBar → goes through popup 2 (popup 1 already done in Settings)
3. Verify DB: new config_id with `trading_mode='virtuals'`, new `arena_agents_v2` row with all vault IDs + agent_wallet_address
4. Verify modal transitions to funding state with wallet address
5. Deposit $10 USDC to agent wallet → check-deposit → funds bridged to HL
6. Activate bot → wait one cycle → verify trade executes on HL (check `live_trades` table with `provider='hyperliquid'`, `config_id=new_config_id`)
7. Verify SSE dashboard shows correct metrics for the new live bot (equity, positions, trade history)
8. Check `degen.virtuals.io` leaderboard → verify agent appears
9. Close position → verify `live_trades` updated, `trade_exit` activity logged, SSE reflects closed state
10. Click "Manage Live Bot" on ActivationBar → verify modal shows management state with positions + withdraw

### Phases 4-5
- Admin bot migrated, trading continues without interruption through new pipeline
- Sebastian marketBrief provider serving requests via Node sidecar (verify via test ACP job from external agent)
- No `_execute_claw_arena_trade` or `_enqueue_arena_trade` callsites remain in orchestrator
- `arena:trade_queue` Redis key unused (can `DEL` after 1 week stable)

---

## Open Questions (to resolve during execution)

1. **Popup 2 auto-close behavior** — does Virtuals' signer-approval page auto-close, or does user need to manually close? Phase 0a answers directly.
2. **JWT session lifetime** — how long before user needs to re-Connect-Virtuals? Affects UX for returning users deploying new bots. If short-lived, Settings page needs session-refresh UX.
3. **Rate limits / fees** — does Virtuals impose per-agent creation limits for platforms creating at scale? Ask in Discord `discord.gg/virtualsio`.
4. **Gas costs** — actual cost to `activate-unified-account` + `add-api-wallet` per agent (Base gas + HL gas). Might be negligible; might matter at scale.
5. **Scoped delegation** — does v2 support scoped session keys (e.g., "sign only Hyperliquid trade messages, not USDC transfers")? If yes, could shift from custodial-revocable to pure non-custodial in a future phase. Ask Virtuals directly.
6. **Privy smart-wallet HL compatibility** — Phase 0b answers definitively. If any adapter mismatch, need to doc + patch in Phase 2.
7. **Agent naming strategy** — when creating a v2 agent per bot, what name goes on Virtuals? Options:
   - (a) Derive from bot config name (e.g., "BTC Scalper" → agent named "BTC Scalper")
   - (b) Bot config name + suffix ("BTC Scalper (ggbots)")
   - (c) User-editable at deploy time (default = bot name, user can override)
   - (d) Username + bot name ("sev's BTC Scalper")
   - **Recommendation**: (c) — pre-populate field with bot name, let user edit. Agents are semi-public on Virtuals; users should control branding. Also consider: names must be unique in Virtuals' registry — need to handle collision gracefully.
8. **BotRail placement for virtuals bots** — live virtuals bots mixed into "Paper Bots" section with a badge, or separated into their own "Live Bots" section? Recommend: mixed in with a "LIVE" badge like the existing pinned Hyperliquid slot uses.
9. **`is_public_performance` field fate** — subsumed by `trading_mode='virtuals'` (all virtuals bots are arena-public by design) or kept as a separate "opt out of leaderboard" toggle for privacy-conscious users? Defer to Phase 3.
10. **Agent rename post-creation** — does Virtuals allow renaming an agent after the initial `agents/lite/key` call? If not, Phase 3 management modal can't offer rename UI. Verify in Phase 0a.
11. **Legacy `arena_agents` table fate** — handled by Sebastian manually in Phase 5; out of scope for this plan.

---

## Effort Estimate

- Phase 0a: 1 day (test page + 4 endpoints + popup flows)
- Phase 0b: 0.5 day (monitoring verification — mostly just dumping data and comparing)
- Phase 1: 1-2 days (DB migration, production endpoints, Vault methods)
- Phase 2: 1 day (credential-source refactor, careful not to break existing HL path)
- Phase 3: 2-3 days (modal repurposing, ActivationBar wiring, Settings section, delete Promote-to-Live)
- Phase 4: 2-3 days (admin bot migration + Node sidecar for Sebastian + careful deletion)
- Phase 5: manual, handled by Sebastian

**Total focused dev work: ~7-10 days.**
