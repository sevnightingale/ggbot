# ACP v2 Migration — Session Handoff (2026-04-24)

**Status**: Work in progress. Mid-pivot after significant architectural discovery.
**Context**: Prior session exhausted Opus context after ~11 hours of debugging. This doc is the complete handoff for a fresh session.
**Primary reference**: [`/home/sev/.claude/plans/acp-v2-migration-foamy-bunny.md`](../../../.claude/plans/acp-v2-migration-foamy-bunny.md) — original plan
**Related doc**: [`ACP_V2_MIGRATION.md`](ACP_V2_MIGRATION.md) — earlier status, now partially superseded

---

## TL;DR — What a fresh session needs to know in 60 seconds

1. **The 3-week plan to migrate to ACP v2 is mostly built, and mostly wrong at the bridge step.**
2. **DGClaw agent is still on ACP v1** (`--legacy` flag required). Our v2 SDK is unproven against v1 providers.
3. **Deposits to HL are ACP buyer jobs (`perp_deposit`), NOT on-chain bridges we perform.** DGClaw's backend handles Base → Arbitrum → HL itself. My `/bridge-usdc-to-hl` sidecar route is dead architecture.
4. **User wallet chain: Base, not Arbitrum.** Agents live on Base (Virtuals' paymaster is Base-only). User USDC must land on Base for the deposit ACP job to find it.
5. **Parallel track already shipped and working**: Phase 2 lite-agent-pool (`arena_agents` table, `claw_api.py`, `api/virtuals_arena.py`). That path uses Virtuals' **claw REST API** (`x-api-key`) which auto-handles signing via Privy-managed signers.
6. **Unresolved architectural fork**: should we (a) keep the ACP v2 per-user-agent model and rewire the deposit step, (b) fall back to the lite-agent pool, or (c) ship the existing `hyperliquid` self-custody mode and skip v2 entirely?

Three options, all viable. **No code changes until this decision is made with the user.**

---

## Current system state (as of 2026-04-24 04:55 UTC)

### Database
One orphan `arena_agents_v2` row from today's stuck deploy attempt:

```
arena_agents_v2
─────────────────
id                   d4ef91a1-a328-4bb2-9640-7c641e390449
user_id              00000000-0000-0000-0000-000000000000  (Sev)
config_id            4534d709-9b55-4119-b1ab-e51cb324af26
virtuals_agent_id    019dbd94-f28b-7d58-8071-3e657b882477
agent_name           Sebastian's Strategist
agent_wallet_address 0xb94bbcbb8ea82d01045fea100515f87360032ed3
status               provisioning  ← stuck; signer approved but HL setup never completed
```

Corresponding `configurations` row:
- `config_id=4534d709`, `config_name="Sebastian's Strategist"`, `trading_mode='virtuals'`, `state='inactive'`
- This is a duplicate of a source paper bot — the duplication itself worked via `config_service.create_config()`.

### Virtuals accounts
Two involved:

| Account | Wallet | Orphan agents | Notes |
|---|---|---|---|
| Original (Google #1) | `0xREDACTED_TREASURY_WALLET` | 10 (all `isHidden: true`) | Quota maxed. Virtuals API has no DELETE; only way to recover is to DM them for purge. Draft message in prior conversation. |
| Sebastian.sidoh@gmail.com (new) | Unknown | 1 (`019dbd94` — Sebastian's Strategist, stuck in provisioning) | Used for today's deploy test. 9 slots remaining. |

### Stranded funds
`$10 USDC on Arbitrum at 0xb94bbcbb8ea82d01045fea100515f87360032ed3`. The same address is the agent's counterfactual address on Base too, but Virtuals' Alchemy paymaster policy doesn't support Arbitrum, so we can't sign outbound transfers from that wallet on Arbitrum via the provider adapter.
**Recovery options**: (a) wait for Virtuals to enable Arbitrum, (b) build a self-hosted relayer (Option 4 below), (c) leave stranded as an acceptable sunk cost.

### Redis
All `arena_v2:*` keys expired. No active deploy state.

### PM2 processes (all online as of session end)
`ggbot`, `ggbot-scheduler`, `acp-node`, `account-monitor`, `error-alerts`, `market-data-ws`, `sebastian-bot`, `sebastian-chrome`, `sebastian-telegram`, `sebastian-virtuals`.

### Git state (main branch, not pushed)
Uncommitted local edits to:
- `api/arena_v2.py` — diagnostic wrapper, config_service refactor, status-agnostic credential fetch, step logging, deploy-poll rewritten to skip HL setup, check-deposit given HL setup block that will never fire in current shape
- `acp-node/src/index.ts` — Node 18 `crypto` polyfill
- `acp-node/src/lib/privy-sign.ts` — PEM→DER fallback in decodeSignerKey
- `api/acp_v2_test.py` — P-256 keygen now DER
- `core/auth/vault_utils.py` — `get_arena_v2_credential` no longer filters by status='active'
- Plus the bridge route we now know is dead.

**Do NOT commit these changes as-is.** They're mid-pivot. A fresh session needs to decide the path forward first.

---

## Bugs found + fixed during session (preserved for reference)

| # | Bug | Root cause | Fix | File |
|---|---|---|---|---|
| 1 | Agent create 502 | Response shape: `walletId` lives in `walletProviders[].metadata`, not top-level | Extract from array | `api/arena_v2.py` |
| 2 | 500 on config duplication | Raw INSERT bypassing `config_service.create_config` validation | Route through service | `api/arena_v2.py` |
| 3 | `valid_trading_mode` CHECK violation | DB constraint didn't include `'virtuals'` (passive plumbing missed this) | `database/migrations/extend_valid_trading_mode_virtuals.sql` (applied) | DB |
| 4 | Privy "Invalid wallet authorization private key" | Key stored as base64(PEM) — Privy wants base64(DER) no headers | Swap `Encoding.PEM` → `Encoding.DER` in Python keygen; TS fallback for legacy rows | `api/arena_v2.py`, `api/acp_v2_test.py`, `acp-node/src/lib/privy-sign.ts` |
| 5 | Wallet blank in modal | `get_arena_v2_credential` filtered by `status='active'`; provisioning rows invisible | Query returns any non-retired status; `resolve_hl_credentials` checks status itself | `core/auth/vault_utils.py` |
| 6 | HL "Must deposit before performing actions" | Called `userSetAbstraction` + `approveAgent` on empty HL account | Moved HL setup from deploy-poll to check-deposit (post-bridge) | `api/arena_v2.py` |
| 7 | `crypto is not defined` on `sendCalls` | Node 18 lacks `crypto` global (Node 20+ feature) | Polyfill via `node:crypto.webcrypto` at entry | `acp-node/src/index.ts` |
| 8 | `wallet_prepareCalls` 400 on Arbitrum | **Not actually a bug** — Virtuals' paymaster is Base-only. Fundamental architecture mismatch | → Abandon on-chain bridge approach entirely | — |

Bug 8 is the big one. Everything prior was working around symptoms of the same root misunderstanding.

---

## THE KEY DISCOVERY — SKILL.md Step 6

From `dgclaw-skill/SKILL.md` and `trading/virtuals/README.md`:

```
Step 2 — Deposit USDC
Send USDC to your agent wallet on Base chain. Then deposit via ACP job:

acp client create-job --provider "0xd478a8B40372db16cA8045F28C6FE07228F3781A" \
  --offering-name "perp_deposit" --requirements '{"amount":"100"}' --legacy
acp client fund --job-id <jobId>
```

**Deposits are ACP jobs against DGClaw's provider agent, not on-chain bridges we perform.**

- Offering: `perp_deposit` ($0.01 fee, 30-min SLA, `required_funds: true`)
- Minimum: $6 USDC
- Bridge route: DGClaw's internal infra does Base → Arbitrum → HL
- `--legacy` flag: **DGClaw provider is still ACP v1**, not v2

This means:
- We never needed the Arbitrum paymaster
- We never needed cross-chain sendCalls
- We never needed on-chain bridge transactions at all

Everything about the `/bridge-usdc-to-hl` route — including the crypto polyfill we added — is architecturally unnecessary. It can be deleted.

Same pattern holds for `/join-leaderboard` ($0.01 ACP buyer job) and likely for forum interactions (v1-style ACP jobs against DGClaw).

---

## The three forks in the road

### Option A — Fix ACP v2 arena_v2 path, use ACP jobs for deposits/trades

**Scope**:
1. Delete `acp-node/src/routes/bridge-usdc-to-hl.ts` (dead)
2. Delete crypto polyfill (only needed for sendCalls, which we no longer do)
3. Add `acp-node/src/routes/deposit.ts` — creates + funds an ACP job with offering `perp_deposit`
4. Verify `/join-leaderboard` route works against v1 DGClaw provider from v2 SDK (needs live test; may require `@virtuals-protocol/acp-node` v1 dep alongside v2)
5. Rewrite `arena_v2.py` `check-deposit` endpoint — no more Arbitrum balance checks, no more bridge step; instead poll ACP job completion via SDK/claw API
6. Update DeployLiveModal: copy changes from "Send USDC on Arbitrum" to "Send USDC on Base chain"
7. Add Base USDC balance checking via public Base RPC (drop Arbitrum RPC helper, or keep as withdrawal-destination verification)
8. Test end-to-end on Sebastian.sidoh account (9 Virtuals slots remaining)

**Pros**:
- Each user/bot gets its own per-agent identity on Virtuals dashboard
- DeployLiveModal UX already built
- Matches Virtuals' canonical deploy flow (agent create + signer + leaderboard + deposit)

**Cons**:
- Still pioneering — v2 SDK + v1 DGClaw provider interaction not proven
- 10-agent account limit (Virtuals caps accounts at 10 agents; we already burned through 10 on Sev's first account)
- Every deploy attempt uses a quota slot if it gets partway through (orphans accumulate)

**Estimated effort**: 1–2 days focused work, assuming SDK v2 ↔ v1 provider interop works.

### Option B — Fall back to existing Phase 2 lite-agent pool

**Scope**:
1. Abandon `arena_agents_v2` table, delete arena_v2 code
2. Reuse existing `arena_agents` + `api/virtuals_arena.py` + `claw_api.py` (all working today)
3. Replace ActivationBar "Deploy Live Version" button with wiring to existing `joinArena` flow
4. Replace DeployLiveModal with the existing `DegenArenaModal` (already ships in repo)
5. Ensure lite-agent pool is populated (currently 40 agents — create more with `scripts/create_arena_pool.py` if needed)
6. Tear down the Phase 3 UX work (BotRail virtuals badge, tri-state button, SettingsModal Connect Virtuals, Promote-to-Live deletion may need partial revert)

**What works already**:
- Lite agents provisioned by admin via `scripts/create_arena_pool.py`
- Users assigned an agent when they click "Join Arena" on a bot
- `claw_api.py` handles deposit/trade/withdraw via Virtuals' Claw REST API (`x-api-key`, Privy-managed signer)
- DGClaw registration via `_register_on_dgclaw` — automatic on first deposit
- Close mirroring + sync via `arena_sync.py`
- Verified working on "The Technician" bot: assigned ggbot-004, $6 deposit, $4.99 on DGClaw

**Pros**:
- Zero new integration risk; all plumbing proven
- No per-user Virtuals account needed
- No 10-agent limit (pool is admin-controlled)
- User doesn't see Virtuals at all — one-click join

**Cons**:
- Agents are from a shared pool named `ggbot-001, ggbot-002, ...` — not user-branded
- Each new deploy consumes a pool slot (currently 27 available); need to keep pool topped up
- The BotRail "LIVE" badge + Deploy Live Version button is built for per-user agents; would need UX rework
- The user specifically asked for per-user agents in the ACP v2 migration plan — going back to pooled would be a strategic reversal

**Estimated effort**: 0.5–1 day to rewire frontend to use existing backend. Most work is deleting v2 scaffolding.

### Option C — Ship `trading_mode='hyperliquid'` self-custody, skip Virtuals v2 entirely

**Scope**:
1. Keep the ACP v2 work in repo but don't activate it on any user-facing surface
2. Mark the `"Deploy Live Version"` UX as disabled for now (or remove, using paper-only)
3. Rely on the existing Settings → "Connect Hyperliquid" flow (fully working, non-custodial, no per-agent complexity)
4. Users manually connect their own HL wallet, authorize an API wallet, and use `trading_mode='hyperliquid'` (1 live bot per user)

**Pros**:
- Zero new work. Already shipped and battle-tested.
- Non-custodial — users retain full control
- No dependency on Virtuals' infrastructure maturity

**Cons**:
- No per-bot independent HL accounts (1 live bot per user)
- No DGClaw leaderboard visibility for ggbots users
- Strategically, we lose the "bots auto-register on the arena" value prop

**Estimated effort**: 0 days. Just delete or hide the v2 UI.

### Hybrid option — A + C together

- Ship `hyperliquid` self-custody as the primary live-trading path today
- Continue work on ACP v2 (Option A) as a follow-on for "bots with their own wallet + leaderboard presence"
- When v2 is proven, add it as a second option alongside HL self-custody
- Users pick at deploy-time

This is probably the right long-term answer, but requires committing to the v2 investment even after today's setbacks.

---

## Concrete next steps (agnostic to which option)

### Immediate cleanup

1. **Revert the uncommitted local edits** back to `main` state, or split them into cherry-picked commits for what's genuinely useful:
   - Keep: Migration for `valid_trading_mode` (applied to DB, needs SQL file committed)
   - Keep: P-256 DER-encoding fix in Python keygen (defensible bugfix)
   - Keep: PEM→DER fallback in `decodeSignerKey` (backward-compat armor)
   - Drop: `/bridge-usdc-to-hl` route + crypto polyfill (dead architecture)
   - Drop: All the step-logging + traceback wrapper in `_deploy_live_impl` (was diagnostic scaffolding; replace with a clean handler once path is chosen)

2. **Clean up the orphan row in arena_agents_v2** (`d4ef91a1-a328-...`). Either:
   - Mark its status='retired' so it doesn't show in UI
   - Or delete the row + its `configurations` row outright (`4534d709-9b55-...`, and clean up the Vault entry for the signer key)

3. **Node 18 → 22 upgrade** (next task in this session — see below).

### If going Option A

See scope breakdown in Option A above. Key unknowns that need early validation:
- Does `@virtuals-protocol/acp-node-v2`'s `AcpAgent` class work against v1 provider agents?
- What's the response shape of an ACP job deliverable for `perp_deposit`? (we'll need to parse bridge tx hash out of it)

### If going Option B

See scope breakdown in Option B above. Key file touchpoints:
- `frontend/app/forge/components/monitor/ActivationBar.tsx` — rewire `deployButtonState` logic to use arena_agents rows not arena_agents_v2
- `frontend/components/DeployLiveModal.tsx` → replace with `DegenArenaModal`
- `frontend/components/VirtualsConnectButton.tsx` — delete (not needed for lite agents)
- `frontend/components/SettingsModal.tsx` — remove "Connect Virtuals" subsection
- Delete `api/arena_v2.py`, `database/migrations/add_arena_agents_v2.sql` rollback, etc.

### If going Option C

See Option C scope. Minimal work — just hide the new UX elements:
- `ActivationBar.tsx` — remove `deployButtonState` logic (revert to no tri-state button)
- `BotManagementMenu.tsx` — remove "Deploy Live Version" menu item
- `SettingsModal.tsx` — remove "Connect Virtuals" subsection (keep existing Hyperliquid flow)
- Delete or leave dormant all backend v2 scaffolding

---

## What's worth salvaging no matter which option wins

Code that's solid and not wasted:

- `database/migrations/add_arena_agents_v2.sql` — usable if Option A continues
- `database/migrations/extend_valid_trading_mode_virtuals.sql` — NEEDED for any option where `'virtuals'` stays as a trading_mode value (already applied to DB, just not committed to git)
- `acp-node/src/routes/setup-hl-unified.ts` — clean port of dgclaw-skill activate-unified
- `acp-node/src/routes/authorize-hl-api-wallet.ts` — clean port of add-api-wallet
- `acp-node/src/routes/withdraw-from-hl.ts` — clean port for HL→Arbitrum withdrawals
- `acp-node/src/lib/privy-sign.ts` — solid Privy EIP-712 signing abstraction
- `core/services/acp_node_client.py` — Python→sidecar HTTP client (reusable)
- `core/auth/vault_utils.py` additions (`create_vault_secret`, `get_vault_secret`, arena_v2 storers) — decent primitives
- `api/acp_v2_test.py` + `frontend/app/test/acp-v2/page.tsx` — Phase 0 admin gate, useful for future testing
- DeployLiveModal 4-stage UX, VirtualsConnectButton, SettingsModal Connect Virtuals — all salvageable for future per-user agent path

Dead code (safe to delete regardless of option):

- `acp-node/src/routes/bridge-usdc-to-hl.ts`
- `core/services/arbitrum_rpc.py` — no longer needed for bridge; maybe still useful as a generic helper
- Crypto polyfill in `acp-node/src/index.ts`

---

## Sequencing recommendation for fresh session

1. Get user's decision on Option A / B / C / A+C.
2. **If A or A+C**: start by porting the ACP `perp_deposit` job flow. Single clean replacement for the bridge route. Spend 1–2 hrs max — if v2 SDK can't talk to v1 DGClaw provider, pivot to **B**.
3. **If B**: mechanical deletion + rewiring, ~1 day.
4. **If C**: 1–2 hrs of cleanup, ship immediately.

Don't attempt "A and B in parallel" — the table schemas conflict (`arena_agents` vs `arena_agents_v2`) and the frontend code can't cleanly support both.

---

## Reference: known-good test vectors

For Phase 0 regression test (needs admin login):

- Admin test page: `/test/acp-v2`
- Admin user ID: pull from `api/admin.py` ADMIN_USER_ID
- HL test wallet: will be printed after `agent-create` + `authorize-api-wallet` flow
- Minimum trade: $5 notional ETH long, verified working previously

Production user on test: Sev (`user_id=00000000-0000-0000-0000-000000000000`)

---

## Environment notes

- Node 18.20.8 currently (EOL April 2025). Upgrade to 22 scheduled this session.
- Python 3.11.0rc1 in venv (release candidate from Sep 2022). Should bump to 3.11.9.
- PM2 6.0.6. Fine.
- `ACP_NODE_SHARED_SECRET` is in both `/home/sev/ggbot/.env` and `/home/sev/ggbot/acp-node/.env`. Don't regenerate.
- `PRIVY_APP_ID` defaulted to `cltsev9j90f67yhyw4sngtrpv` (Virtuals production).

---

## DO NOT let a fresh session

- Start coding Option A without confirming v2↔v1 SDK compat first
- Continue the `/bridge-usdc-to-hl` approach — dead architecture
- Burn more Virtuals account slots on speculative testing (Sev's main account is capped)
- Delete the polyfill without first deleting the bridge route that needs it
- Commit the mid-pivot code on main as-is

Ask the user which path, then execute.
