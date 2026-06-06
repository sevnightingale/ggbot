# CHANGELOG - ggbots Platform

Complete history of features, fixes, and improvements. For upcoming work see ROADMAP.md.

**WRITING STYLE**: Telegraphic style. Omit articles (a, an, the). Include file references, technical accuracy. Target 3-8 lines recent entries, 1-3 lines older entries.

---

## 2026-06-06 - Database Migration: Supabase → Self-Hosted PostgreSQL 17 + App-Managed Vault

Root cause: Supabase free-tier 402 `exceed_db_size_quota` (DB 1,850MB vs 500MB cap) blocked REST API + Auth since Jun 4 22:19 UTC. Resolution: full app-data migration to local PG17; Supabase retained for auth + bot-avatars storage only ($0/mo end state).

**Infra**: PGDG postgresql-17 on VM (lean config: 128MB shared_buffers, UTC, scram, localhost-only), role `ggbot_app`, REVOKE PUBLIC, systemd ordering PG-before-PM2, swap 2→4GB, Redis maxmemory 256MB volatile-lru. `uuid-ossp` + `pgcrypto` installed into `extensions` schema (Supabase dump qualifies defaults as `extensions.uuid_generate_v4()` — fresh PG17 lacks schema → 5 hottest tables failed first restore; reset + re-restore clean, 0 errors).

**Data**: archive dump 236MB via session pooler (PG14 client can't dump PG17 server — PGDG client required). 19 tables restored: row counts exact, content checksums identical (incl 194K activities + 161K decisions via order-independent sum-of-row-hashes — `md5(string_agg)` hit Supabase statement_timeout), enum labels+order verified, sequences ahead. 10 auth.users FKs dropped, 17 intra-public FKs kept. Profile backfill: email column + 36 missing profiles → 397/397 with email.

**Vault**: Supabase Vault (non-portable pgsodium crypto) → local `vault_secrets` table, Fernet/MultiFernet (`GGBOT_VAULT_KEY`, key_version column for rotation). Only ggbot's 5 `hyperliquid_*` secrets migrated (60 `arena_*` DGClaw secrets untouched, $81 recovery dependency); UUIDs preserved → pointer columns unchanged. GATE A: all 5 local-decrypts byte-identical to source.

**Code** (`core/auth/local_vault.py` new): `get_database_url()` → DATABASE_URL/DB_*, fail-loud, pool 50→30 + reset-on-broken-connection; 21 PostgREST sites → raw SQL (supabase_service 13, account_repository 5, supabase_storage 3) with exact return-shape parity; `auth.users` → `user_profiles.email` at 9 sites (admin last_sign_in_at dropped); SERVICE_AUTH_TOKEN split from SUPABASE_SERVICE_KEY; supabase-py + 5 sibling packages removed; app imports verified with supabase packages hard-blocked.

**Cutover**: live HL bot held inactive; all 5 services clean boot 0 restarts; E2E cycle verified: extraction → market_data local upsert → MI (6 points) → grok decision (enter 0.58) → paper trade long BTC @ $60,895.89, 41s, 0 errors. JWT auth verified via minted HS256 token. HL credentials verified read-only (`user_state` $108.11). Supabase truncated FK-closed set → 69MB → 402 lifts. error-alerts pipeline proven live (Telegram delivery).

**Ops**: nightly encrypted backups (gpg AES256, key separate from .env, `pg_restore -l` integrity check, 7d+4w retention) cron 04:30 UTC; disk >85% alert cron; rclone installed for weekly R2 offsite (`r2:ggbot-db-backups`, pending credentials). Rollback = reverse-restore from archive dump (acknowledged one-way).

---

## 2026-06-04 - PM2 Namespace `gg` for Project-Scoped Service Operations

All 5 services assigned `namespace: 'gg'` in `ecosystem.config.js` — enables `pm2 stop/start/restart gg` scoped to ggbot only. VM's PM2 daemon shared with unrelated projects → `pm2 restart all` unsafe. Namespace fixed at registration: stale stopped entries deleted from daemon, re-registered via eco-file cold start (`pm2 start ecosystem.config.js && pm2 save`). Namespace start/stop/delete verified on PM2 6.0.14. CLAUDE.md documents scoped ops + `pm2 save` snapshot discipline. Services resumed post OpenRouter top-up: all 5 online 0 restarts, `/health` 200, scheduler re-registered 6 bots at correct cadences, 0 errors. First post-resume cycle (17:00 UTC) verified end-to-end: 3 decisions on grok-4.3, paper long BTC/USDT @ $63,538 executed — first completed decision→trade chain since ~May 17 outage.

---

## 2026-06-04 - Platform Streamlining: Consolidated Around Core Trading Paths

Platform consolidated around its two production trading modes — paper + Hyperliquid-direct live. Retired exploratory subsystems not part of core product: contest/leaderboard system, third-party agent-marketplace bridge, alternate-DEX adapter, standalone research agent, social-signal publisher. ~36K lines removed across backend, frontend, DB, env, docs. Config types 3→1 (`scheduled_trading`); trading modes → `paper|hyperliquid`.

**Removed (code)**: marketplace sidecar, `trading/virtuals/`, `core/arena/`, `agent/`, `signals/`, `x_bot/`, rei engine, symphony/aster services + adapters, related API modules + endpoints in `ggbot.py`, signal_validation routing in orchestrator + engine_v2. `resolve_hl_credentials()` reduced to hyperliquid-only.

**Removed (frontend)**: retired app routes + components (arena/dojo surfaces, deploy modals, staking libs), related hooks/methods in queries.ts + api.ts, retired subdomain routing in middleware, stale landing banners. Also excised two orphaned components calling nonexistent `/api/v2/trades/live` — pre-existing dead path. `npx tsc --noEmit` clean.

**DB migration** (applied): retired-feature tables dropped (7), 6 configurations cols + 5 user_profiles cols dropped, CHECKs narrowed to `('paper','hyperliquid')`, `live_trades.provider` default → hyperliquid, orphaned vault secrets + stale data_sources rows deleted (audit-exported first). 8 obsolete migration files removed.

**Process/env/deps**: `ecosystem.config.js` → exactly 5 services (ggbot, ggbot-scheduler, market-data-ws, account-monitor, error-alerts). `.env`: 45 dead keys removed (backed up first). requirements.txt: removed virtuals-acp, web3, Telethon, tweepy (eth-account/eth-utils kept — HL SDK deps).

**🔴 Pre-existing break fixed**: `hyperliquid-python-sdk==0.22.0` IndexError in `Info()` spot-meta parsing vs HL's current API — API couldn't boot on ANY branch. Upgraded → 0.23.0, all 9 used SDK methods verified present.

**🔴 Second pre-existing break fixed**: ALL active bots use `model=grok`; OpenRouter delisted `grok-3-mini`/`grok-4-fast`/`grok-4.20-beta` → every decision 404'd since ~May 17. Per MODEL_UPDATE.md: economy+standard → `x-ai/grok-4.3` ($1.25/$2.50, 1M ctx), premium → `x-ai/grok-4.20` (2M ctx); `llm_models` DB row updated.

**Post-drop SQL audit critical catch**: `config_service.py` INSERT/SELECT×2/UPDATE still named dropped `symphony_agent_id` column — every config create/load/update would crash (invisible to import checks). Excised 21 refs; proven via live list_configs/get_config smoke test.

**Docs**: README + module READMEs (trading, decision, MI, extraction, frontend, SEO) updated; 15 dead planning/feature docs deleted. Verified: `import ggbot` + `import ggbot_scheduler` exit 0; residual greps clean.

**Boot verification (all 5 services)**: online 0 restarts, `/health` 200, market-data-ws storing candles, scheduler re-registered 6 bots at correct cadences, account-monitor writing paper+hyperliquid snapshots (HL SDK 0.23.0 live against mainnet), error-alerts delivering. Live 15m cycle verified end-to-end through extraction → MI (5 points, 4 categories) → decision routing → model resolution.

---

## 2026-04-30 - DGClaw v2 Bridge SLA Pitfall + ggbots.ai V2 Live

**Root cause of $81 stranded** (jobs `1003504368` $75, `1003504898` $6):
- DGClaw `perp_deposit` offering returns `slaMinutes: 30`. On-chain `expiredAt` defaults to that. When DGClaw bridge relayer is backlogged, job hits TRANSACTION (funds already moved to v2 aggregator), then auto-EXPIRES at 30min before deliverable memo — DGClaw's reconciliation skips expired jobs, funds strand in `0x09aea4b2...` aggregator. `claimBudget` reverts (funds left ACP escrow within seconds; recovery requires DGClaw manual credit).
- v2 fund flow on Base traced on-chain: buyer → ACP v2 contract `0xa6c9ba86...` → DGClaw v2 intake EOA `0x9bda49389b29fa4e204ed9de8f3d7d06f84da171` → v2 aggregator smart-contract `0x09aea4b2242abc8bb4bb78d537a67a245a7bec64`. NOT `0xd478a8B4...` (v1 provider, drained and idle). Watching v1 was misleading.
- **Fix**: `acp-node/src/routes/deposit.ts:28` overrides `expiredAt` to `Date.now() + 4*60*60*1000`. Verified — $6 deposit during the same DGClaw slowdown bridged + credited in 40min instead of stranding.

**ggbots.ai V2 migration complete + activated**:
- New V2 wallet `0xREDACTED_AGENT_WALLET` (agent UUID `019da9f3-9dd8-7d0e-b2ce-8f4febb75a15`), $GG token preserved.
- Vault stores user-provided migration P-256 PKCS8 PEM key (sha `a8e1b085...`); `.env ACP_V2_SIGNER_PRIVATE_KEY` is stale (different sha) but only `sebastian_virtuals.py` consumes it.
- Deployed as `ggbots.ai (live)` config `d2cc864a-9efa-4b21-b4fe-7010886e0549` with cloned Arbiter A strategy. `trading_mode='virtuals'`, `state='active'`, HL spot $9.98 (after $6 successful deposit). HL API wallet `0xREDACTED_API_WALLET` authorized + vaulted, unified margin activated. First decision recorded 20:03 UTC (SHORT BTC/USDT conf 0.65).

**Legacy v1 mirror confirmed dead**:
- `sebastian-virtuals` PM2 process firing `perp_trade` ACP jobs from `0x2E48...` legacy wallet → DGClaw rejects with `"Please upgrade to v2"` (e.g., job `1003510502` at 20:04 UTC). Mirror service should be stopped — it's burning gas on rejected jobs.

**Diagnostic routes added** (`acp-node/src/routes/`):
- `check-job.ts` — POST `{jobIds[]}` returns phase + memos[] for stranded-job forensics. Reads `getJob()` via `LegacyBuyerAdapter`.
- `check-offering.ts` — POST `{providerAddress}` dumps DGClaw offering metadata (slaMinutes, priceType, requirementSchema).

**Files**:
- EDIT: `acp-node/src/routes/deposit.ts` (4h `JOB_EXPIRY_MS` constant + matching `OVERALL_TIMEOUT_MS`)
- NEW: `acp-node/src/routes/check-job.ts`, `acp-node/src/routes/check-offering.ts`
- EDIT: `acp-node/src/index.ts` (register new routes)
- EDIT: `trading/virtuals/README.md`, `CHANGELOG.md`, `TODO.md`

---

## 2026-04-24 - ACP v2 Migration: Full Lifecycle Operational (deposit → trade → close)

End-to-end verified on `Contrarian test 2` (config `784abb6e...`, agent `0x0b3af4d7...`): deploy → tokenize → deposit → HL setup → leaderboard join → direct HL trade (0.0048 ETH @ $2310.20 → closed @ $2309.50) → spot balance preserved.

**LegacyBuyerAdapter compat layer** (`acp-node/src/lib/compat/`):
- Ports `@Virtual-Protocol/acp-cli`'s v1/v2 bridge — v2 Privy adapter signs, v1 contract target. Official supported pattern, same code path acp-cli uses with `--legacy` flag.
- `legacyContractBridge.ts` (187 lines): `BaseAcpContractClient` impl routing v2 `PrivyAlchemyEvmProviderAdapter.sendCalls` to the v1 ACP contract. Includes JobCreated event decoder for jobId retrieval.
- `legacyBuyerAdapter.ts` (146 lines): high-level buyer API — `getAgent`, `createJob`, `fundJob`, `completeJob`. Wraps v1 `AcpClient` internally.
- Deps: adds `@virtuals-protocol/acp-node@^0.3.0-beta.40` alongside existing `-v2@^0.0.5`.

**Deposit flow** (`acp-node/src/routes/deposit.ts` rewrite, 230 lines):
- v2 SDK → v1 DGClaw interop via `LegacyBuyerAdapter.createJob({offeringName:'perp_deposit'})` instead of `AcpAgent.createJobFromOffering` (which fails silently against v1 providers — jobs land on v2 contract that DGClaw's indexer doesn't watch).
- 5-phase poll: REQUEST → NEGOTIATION (auto-fund on memo) → TRANSACTION → EVALUATION (auto-complete) → COMPLETED. Reads `job.getDeliverable()` (method, not property — v1 SDK gotcha).
- Verified: $10 Base USDC → $8.99 HL spot in 1:37 total (~$0.01 DGClaw bridge fee + ~$1 wallet reserve).

**Leaderboard flow** (`acp-node/src/routes/join-leaderboard.ts` rewrite):
- Same LegacyBuyerAdapter pattern, RSA keypair preserved for DGClaw's encrypted API key deliverable. 30-min `expiredAt` override (DGClaw's advertised 5min SLA insufficient).
- Memo-propagation race fix: on NEGOTIATION phase, `payAndAcceptRequirement` throws "No notification memo found" if called before DGClaw's requirement memo lands — retry 10s backoff up to 6x.
- **Tokenization gate discovered**: `dgclaw-skill/scripts/dgclaw.sh` requires agent tokenized before `join_leaderboard` delivers. Untokenized agents paid $0.01 → stuck at TRANSACTION forever (DGClaw takes fee, never delivers). Three expired jobs burned $0.03 before discovery.

**Async + idempotent `/check-deposit`** (`api/arena_v2.py` rewrite):
- Returns `{status:"in_progress"}` immediately after fast validation, spawns `asyncio.create_task(_run_deposit_flow)` background task. Solves nginx 5min `proxy_read_timeout` silently killing frontend HTTP during 2-30min deposit flows.
- Redis progress tracking: `arena_v2:deposit_progress:{config_id}` JSON with stage/message, 2h TTL. Stages: `starting` → `depositing` → `hl_setup` → `leaderboard` → `complete | failed`.
- Idempotent retry: skips `perp_deposit` if DGClaw already shows balance, skips HL setup if `hl_api_wallet_key` vaulted, skips leaderboard if `dgclaw_api_key` vaulted. Safe to hit Deposit again at any failure point.
- Rejects `already_in_progress` if a flow is mid-way (prevents double-click race).

**v2 architecture clarification** (the key insight):
- DGClaw's `perp_deposit` lands USDC on the agent's HL **spot** account (not perp).
- Unified margin account activated via `setup-hl-unified-account` auto-uses spot USDC as perp collateral — no manual `usdClassTransfer` needed.
- v2 agents trade DIRECTLY on Hyperliquid via their authorized API wallet (not through DGClaw's ACP `perp_trade` — that 403s for v2 "leaderboard" API keys which are read-only).
- Existing `hyperliquid_service` already routes virtuals-mode bots correctly via `resolve_hl_credentials(trading_mode='virtuals')` — no orchestrator refactor needed.

**Frontend** (`DeployLiveModal.tsx` + `api.ts` + `ActivationBar.tsx`):
- New `processing` stage with animated 4-step stepper + "ok to close" messaging + retry-from-last-stage button on failure.
- Fund stage splits: wallet address first (Step 1/2), amount input appears only after Base balance ≥ minimum (Step 2/2).
- `ActivationBar.v2Funded = dgclaw_balance > 0 || hl_account_value > 0` (was only checking HL main which is $0 while funds pool on DGClaw). Poll every 30s.
- `/status` always fetches `dgclaw_balance` from DGClaw Railway backend (was gated on leaderboard_joined — hid balance exactly when users needed it).

**Bug fixes shipped this session**:
- HL `approveAgent` rejects >16-char "extra agent name" — truncate `creds["agent_name"][:16]`
- Orphan `arena_agents_v2` stuck-in-provisioning cleanup via atomic SQL (DB + vault secret + config row deletion)
- 2-bot frontend confusion: same `agent_name` across two different `config_name` rows surfaces as duplicate rail entries

**Files**:
- NEW: `acp-node/src/lib/compat/legacyContractBridge.ts`, `acp-node/src/lib/compat/legacyBuyerAdapter.ts`, `acp-node/src/routes/deposit.ts` (rewritten), `acp-node/src/routes/join-leaderboard.ts` (rewritten), `core/services/base_rpc.py`, `database/migrations/extend_valid_trading_mode_virtuals.sql`
- EDIT: `api/arena_v2.py`, `core/auth/vault_utils.py` (+`store_arena_v2_forum_thread_id`), `core/orchestrator/orchestrator.py` (exit forum-post hook), `frontend/components/DeployLiveModal.tsx`, `frontend/lib/api.ts`, `frontend/app/forge/components/monitor/ActivationBar.tsx`, `acp-node/package.json`, `acp-node/src/index.ts`
- DELETE: `acp-node/src/routes/bridge-usdc-to-hl.ts` (dead Arbitrum bridge path)

**Commits**: `34bfbca` → `a9ac981` → `e003324` → `f721db0` over ~16 hours.

**Polish pass** (later same day, commit `6a56748`):
- **forum_thread_id capture** (`api/arena_v2.py:_fetch_forum_thread_from_public_api`): walks `https://degen.virtuals.io/api/forums` newest-first, matches by agent name, prefers DISCUSSION thread (SIGNALS gated). Third fallback after deliverable parse. Backfilled live agent to thread `923`; unblocks `_post_virtuals_forum_entry` hook for AI Council posts.
- **Tokenization gate** (`arena_v2.py:_fetch_virtuals_token_address`): probes `https://api.acp.virtuals.io/agents/wallet/{wallet}` → `chains[0].tokenAddress` (public endpoint despite SDK `authedFetch`). `/status` does Redis-gated probe (60s) when `token_address IS NULL`, persists once tokenized. `DeployLiveModal` hard-blocks deposit with amber banner + deep link to `app.virtuals.io/agents/{uuid}` when `is_tokenized === false`.
- **HL subaccount opportunistic capture**: `/status` reads `hlSubaccountAddress` from DGClaw Railway response when exposed (only during active positions), one-shot persist via `store_arena_v2_hl_subaccount`. Mirrors v1 pattern in `api/virtuals_arena.py:299`. Powers future v2 close-sync from HL fills.
- **Schema**: `database/migrations/arena_v2_add_token_and_subaccount.sql` adds `token_address` + `hl_subaccount_address` to `arena_agents_v2` with partial indexes.
- **Cleanup**: orphan test config `c1bc37da...` + its `arena_agents_v2` row + vault signer secret deleted.
- **Tuition**: ~$0.05 burned in expired leaderboard jobs during debugging (acceptable).

---

## 2026-04-22 - ACP v2 Migration: Phase 0 GATE PASSED + Phase 1 Scaffolding

**Phase 0 gate harness** (`api/acp_v2_test.py` 8 admin-only routes + `frontend/app/test/acp-v2/`):
- Popup 1 OAuth: `GET api.acp.virtuals.io/auth/cli/url` → poll `/auth/cli/token`; JWT cached 25min Redis
- Popup 2 agent+signer: `POST /agents` (Bearer JWT, `role="HYBRID"`) → P-256 keypair → `POST /agents/{id}/signer` → URL with `&publicKey=<base64>` appended (matches `acp-cli/src/commands/agent.ts`)
- `verify-trade` (HL open+close via agent API wallet) + `verify-snapshot` (`info.user_state` shape diff vs v1 HL bot)
- ACP v2 base URL pinned `https://api.acp.virtuals.io` (source: `@virtuals-protocol/acp-node-v2/src/core/constants.ts`)
- Admin gate via `api/admin.py:require_admin`; frontend server layout mirrors `/admin/layout.tsx`

**SPKI-DER pubkey fix** (`api/acp_v2_test.py:_generate_p256_keypair`):
- Raw X9.62 uncompressed point → 500 on signer approve. Privy expects base64-SPKI-DER (`docs.privy.io/api-reference/signers/authenticate`).
- Swap `Encoding.X962 + UncompressedPoint` → `Encoding.DER + SubjectPublicKeyInfo`. Output now 91 bytes base64 `MFkwEwYHKoZI...` prefix. Signer approve succeeds.

**Gate result**: snapshot against Privy-provisioned wallet returned structurally valid shape (zero balances expected for unfunded). `HyperliquidAccountAdapter` fully compatible — adapter compat verified. Full trade verification deferred to Phase 1 (automated by acp-node).

**Pre-Phase-2 passive plumbing** (5 files, commit `41df6fb`):
- `ggbot.py:399` validation + `config_service.py:291` initial_equity + `BotRail.tsx:72` paper filter + `api.ts:104` trading_mode union + `RiskAcknowledgmentModal.tsx:17` prop type widened. Zero behavior change; Phase 2+3 can now ship atomically without enum-gate surprises.

**Phase 1 acp-node scaffold** (`acp-node/` new directory, commits `c1c6615` + `011dbee`):
- PM2 TypeScript sidecar (Node 22 + Fastify + TSX). Deps: `@privy-io/node`, `@virtuals-protocol/acp-node-v2`, `viem`, `fastify`
- `src/lib/privy-sign.ts` — wraps `PrivyAlchemyEvmProviderAdapter.create({walletAddress, walletId, signerPrivateKey, privyAppId})` + `adapter.signTypedData(chainId, typedData)`. Base64-PEM signer key decoded before pass. Same abstraction acp-cli uses; no bespoke Privy protocol work.
- 3 live routes: `POST /setup-hl-unified-account` (ports `dgclaw-skill/scripts/activate-unified.ts`), `POST /authorize-hl-api-wallet` (ports `add-api-wallet.ts`), `POST /withdraw-from-hl` (HL `withdraw3` action for Manage Live Bot modal)
- Shared-secret `X-Service-Auth` guard, `/health` unauthed, listens `127.0.0.1:3101`
- `ecosystem.config.js` PM2 entry added. `sebastian-virtuals` stays running alongside in Phase 1+ (deletion gated on Phase 4 v1 arena mirror cleanup).

**AI Council reasoning mechanism discovered** (`dgclaw-skill/references/api.md`):
- Forum posts at `POST https://degen.virtuals.io/api/forums/:agentId/threads/:threadId/posts` (markdown body). AI Council reads these alongside on-chain HL fills when picking Monday top-10 allocations.
- Our bots already generate reasoning (`decisions.reasoning`, `activities.llm_thought`). Need orchestrator hook in Phase 2+3 to fire on entry/exit decisions + new `acp-node/src/routes/forum-post.ts`.

**Phase 1 remaining sidecar routes** (not yet implemented):
- `bridge-usdc-to-hl` — `adapter.sendTransaction()` for Arbitrum USDC → HL bridge (`0x2df1c51e09aecf9cacb7bc98cb1742757f163df7`). MVP users can deposit Arbitrum-direct.
- `join-leaderboard` — ACP v2 buyer job flow (DegenClaw agent `0xd478a8B40372db16cA8045F28C6FE07228F3781A`, $0.01 fee). Requires `AcpAgent` class. Verify whether actually required — AI Council reads on-chain fills regardless.
- `forum-post` — auth mechanism TBD (JWT vs ACP-signed). Feeds AI Council.

**Plan decisions locked in** (`DOCS/todo/ACP_V2_MIGRATION.md`, `/home/sev/.claude/plans/acp-v2-migration-foamy-bunny.md`):
- Phase 0a/0b collapsed → single combined gate
- `sebastian-virtuals` stays on v1, deletion gated on Phase 4 (NOT replaced by acp-node — different responsibilities)
- CredentialResolver helper pattern (not creds-threading)
- DB-gated Phase 4 cleanup (`SELECT COUNT(*) FROM arena_agents WHERE status='assigned' = 0`)
- MVP deposit path: Arbitrum-direct (not DGClaw's `perp_deposit` ACP job)
- Agent naming user-editable with default = bot config name, collision retry-suffix

---

## 2026-04-07 - Activity Log Export (Forge → Download)

**Feature**: Users can download bot's activity log as a plain JSON file for offline review/analysis. Fills gap — existing `GET /activities/{config_id}` hard-caps at 1000 rows, unusable for bots past p90 (2,363 activities).

**Backend** (`api/activities.py:export_activities`):
- New endpoint `GET /api/v2/activities/{config_id}/export?start_time=...&end_time=...`
- Owner-only (403 if `config.user_id != current_user.user_id`), 90-day max range, 50k row cap
- Uses existing `idx_activities_config_billing(config_id, created_at)` — ASC ordered
- Excludes 10 billing/token cols (`provider`, `model`, `*_tokens`, `*_cost_usd`, `stripe_reported*`, `thinking_mode`, `user_id`). Keeps 15 incl full `details` JSONB (LLM thoughts, action, confidence, SL/TP)
- Returns plain JSON via `Response(content=json.dumps(..., indent=2))` — `application/json` + `Content-Disposition: attachment; filename="{slug}_activities_{start}_to_{end}.json"`. No gzip (`.gz` is unfriendly UX, especially Windows)
- Verified against `b523154c-...` (GiGi Chefin): 576 rows / 24h → 1.5 MB pretty-printed JSON

**Frontend** (`ActivityExportModal.tsx` new, `tv-timeline.tsx`, `forge/page.tsx`):
- New `ActivityExportModal` using existing `components/ui/modal.tsx` primitives (sm size)
- 4 quick presets (24h/7d/30d/90d) + two `<input type="datetime-local">` with UTC normalization on send
- Validation: end > start, ≤ now, ≤ 90 days. Inline error messages + disabled Download button
- `TVTimeline` gets new `isOwner?: boolean` prop — download icon button absolute top-right of chart container (z-10) when true
- Forge Monitor caller passes `isOwner`, public `/view/{config_id}` (uses `TVTimelineStandalone`) untouched
- Download handler: `fetch` with `Authorization: Bearer`, blob → `URL.createObjectURL` → invisible anchor click → revoke

**Test suite verified 7 scenarios** (owner 200 / not-owner 403 / no-auth 401 / >90d 400 / end<start 400 / 404 / invalid timestamp 400)

**Unrelated doc fix**: `ACTIVE.md` + `frontend/README.md` — stale `aster.ggbots.ai` Timeline Viewer URL → `ggbot-app.vercel.app/view/{config_id}` (was polluting fresh Claude onboarding context)

---

## 2026-04-07 - DGClaw Arena: Backfill Exits from HL Fills

**Gap**: DGClaw server-side TP/SL closes execute directly on Hyperliquid without producing an ACP job. None of the 4 `mirror_close_to_arena` paths fire → no `arena_exit` activity. Evidence on ggbot-004: 4 HL round-trips, only 3 matching activities. Apr 5 22:02 BTC close at $67,651 (oid=371386016564) was invisible to users.

**Schema** (`database/migrations/add_hl_subaccount_to_arena_agents.sql`):
- New column `arena_agents.hl_subaccount_address VARCHAR(42)` + partial index. Captured opportunistically in `/status` when Railway exposes `hlSubaccountAddress` (only during active positions). Self-heals — every agent populated on next active trade. ggbot-004 seeded directly via SQL.

**Sync Function** (`trading/virtuals/arena_sync.py:sync_closes_from_hl`):
- Queries `Info.user_fills_by_time(subaccount, 7d)`, filters to Close fills, groups partial fills by `(coin, 5s_bucket, dir)`, size-weighted avg price, sum pnl, liquidation flag if any fill liquidated.
- Dual dedup — primary by `details->>'hl_order_id'`, secondary by `(pair, created_at ± 60s)` to catch existing rows from live close paths (arena_sync/claw_arena/arena_reconciler) that don't carry the HL oid.
- Direct `db_execute` with historical `created_at = fill_time` — rows slot into TVTimeline at correct position, not "now". `activity_source='hl_sync'`, `close_reason='dgclaw_server_side'` or `'liquidation'`.
- Redis 60s throttle (`arena:sync_closes_last_run:{agent_id}`) — hot /status poll path short-circuits <1ms. HL query fires at most once per minute per modal session.

**Wiring** (`api/virtuals_arena.py:get_arena_status`):
- Opportunistic hl_subaccount capture on every `/status` call (`UPDATE ... WHERE hl_subaccount_address IS NULL`).
- Invokes `sync_closes_from_hl` awaited (not fire-and-forget) so next modal tick sees fresh data without racing. Wrapped in try/except.
- **Zero frontend changes** — rides existing 10s poll loops on `degen-arena-modal.tsx:21` and `tv-timeline.tsx:806`. No new endpoint, no button, no event listeners.

**Verified end-to-end against production**: first run inserted exactly 1 row (Apr 5 22:02:55 BTC close, oid=371386016564, historical created_at). 3 subsequent runs returned 0 (dedup + throttle). Throttle key TTL confirmed 60s. arena_exit breakdown by source for Technician: arena_sync=3, claw_arena=1, arena_reconciler=1, hl_sync=1.

---

## 2026-04-04 - DGClaw Arena: Audit + Bug Fixes + Modal UX

**Vault Bug** (`core/auth/vault_utils.py`):
- `store_arena_credential` crashed on DGClaw registration — `vault.create_secret()` tried re-creating existing claw key, unique constraint violation silently dropped dgclaw_api_key. Fix: skip claw secret if already stored, only create dgclaw secret.

**Arena Close Sync** (`trading/virtuals/arena_sync.py`):
- Phase 1 admin bot (ARENA_ENABLED_CONFIGS env var) had no `arena_agents` row → `mirror_close_to_arena()` silently skipped all closes. Added Phase 1 fallback: enqueue close to `arena:trade_queue` via Redis for `sebastian-virtuals`. Both Phase 1 + Phase 2 close paths now covered.

**Check-Deposit Flow** (`api/virtuals_arena.py`):
- Registration (30-120s) now fire-and-forget via `asyncio.create_task`, returns `{"status": "registering"}` immediately. No HTTP timeout.
- Min deposit $5→$6 (matches DGClaw actual minimum). Smart reserve: $0.10 for tight balances ($6-$8), $1.00 for $8+.
- Status endpoint returns `is_registered` boolean.

**Frontend Modal** (`degen-arena-modal.tsx`, `ActivationBar.tsx`, `api.ts`):
- "+$X pending" → "+$X in wallet" (funds not in transit, just sitting).
- Smart button labels: "Register & Deposit" / "Deposit to Arena" / "Deposit More" / "Check Balance" based on state.
- Registration spinner shown when `is_registered=false` + wallet has funds.
- Fee messaging: "$10+ recommended, $6 minimum", "~$1 bridge fee" (was "$20 minimum", "~$2 fee").
- ActivationBar stateful: "Enter Degen Arena" → "Arena: Needs Funds" → "Manage Arena Agent" (green success tint).

**Audit findings**: ACP SDK (`virtuals-acp==0.3.23`) confirmed working — EIP-7702 error on Apr 2 was transient RPC issue, not SDK breakage. Denis SZN2 bots correctly waiting (ADX ~10, no trend on ETH). Closed orphaned admin DGClaw BTC short ($67,121→$67,019).

---

## 2026-04-02 - The Dojo: Phase 4 (1v1 Matches)

**Match System** (`core/arena/matches.py` — NEW, ~500 lines):
- `dojo_matches` table: 26 columns, 5 indexes (partial on active status). Dual-reference: original config IDs for Elo, instance config IDs for paper accounts
- `create_challenge()` — House Bot auto-accept + auto-start. User-vs-user path built with 24h expiry (ready for future)
- `start_match()` — creates `config_type='dojo_match'` instance configs + $10k paper accounts, snapshots strategy, records Elo baselines
- `complete_match()` — composite scoring on match instances, Elo update on originals, archive instances
- `forfeit_match()` — opponent wins, Elo adjusts (score 0 vs 1), archive
- `process_dojo_matches()` — scheduler job (5min): complete expired, start accepted, expire stale challenges
- Match instance config_data copies source bot's trading/decision settings for correct mirror trade execution

**Mirror Service** (`core/arena/dojo_mirror.py` — NEW, ~230 lines):
- `mirror_trade_to_dojo()` — copy-trade user bot entries to match instance paper accounts via `SupabasePaperTradingService`
- `mirror_close_to_dojo()` — idempotent close on match instances, queries by original config_id (no cascade risk)
- `dispatch_house_bot_signal()` — broadcasts House Bot entry signals to IDLE match accounts (derived from open position count)
- Orchestrator hooks at both autonomous + signal-driven paths (alongside DGClaw mirror)
- Close path hooks in 3 files: `supabase_service.py` (paper TP/SL), `ggbot.py` (HL manual), `hyperliquid_adapter.py` (HL fill detection)

**Lock System** (`ggbot.py`, `api/paper_trading.py`):
- `_check_dojo_lock()` helper — 7 endpoints guarded: config edit, stop, run now, reset, delete, HL close, paper close
- SSE enrichment: `dojo_locked` via EXISTS subquery on `idx_dojo_matches_active_lock` partial index
- Config list enrichment: `dojo_locked` + `dojo_matches_active` array with opponent name, format, ends_at

**Scheduler** (`ggbot_scheduler.py`):
- `dojo_match_lifecycle` — IntervalTrigger(5min), processes match state transitions
- `weekly_rolling_elo` — CronTrigger(Sun midnight UTC), Swiss-system Elo update

**API Endpoints** (`ggbot.py`, `api/public.py`):
- `GET /dojo/can-enter/{config_id}` — entry gate (active? paper? no positions? not locked?)
- `POST /dojo/challenge` — issue challenge (body: config_id, opponent_config_id, format)
- `POST /dojo/match/{id}/forfeit` — forfeit active match
- `GET /dojo/matches/{config_id}` — paginated match history
- `GET /dojo/stats/{config_id}` — aggregate W/L/D stats
- `GET /dojo/active/{config_id}` — active/pending matches
- `GET /public/dojo/match/{id}` — shareable match detail

**Frontend** (`DojoTab.tsx` rewrite, `DojoLockBanner.tsx` — NEW, 5 components modified):
- DojoTab: challenge UI with inline format picker (Blitz/Rapid/Standard), active match cards with forfeit confirmation, match history with expandable composite breakdown, W/L/D record in header
- DojoLockBanner: brass-accent banner on Configure tab showing opponent, format, time remaining
- Lock states: ActivationBar (disable stop/run), PositionsTable (disable close), BotManagementMenu (disable delete/reset)
- Elo badge moved from BotRail → ActivationBar (next to bot name, paper bots only)

**Bugfixes** (caught in audit):
- `close_position` kwargs: mirror was passing `(config_id, user_id, close_reason)` — actual signature is `(trade_id, reason)`. Fixed
- Match instance config_data: was empty shell, `execute_trade` needs `trading.leverage` etc. Now copies source bot's trading/decision settings
- House Bot Elo: reset from 1500 → 1200 (inflated starting Elo is misleading)

---

## 2026-04-01 - The Dojo: Phases 1-3 (Foundation, Elo Engine, House Bots)

**Phase 1: Foundation** (`core/arena/dojo_public.py`, `core/sse/dashboard_data.py`, `ggbot.py`, frontend):
- DB migration: `dojo_visible`, `elo_rating`, `is_house_bot` columns on `configurations`
- Forward guards: `config_type != 'dojo_match'` filter added to `config_service.list_configs()` and `dashboard_data.py` CTE
- Public endpoints: `GET /api/v2/public/dojo/bots`, `GET /api/v2/public/dojo/stats`
- Visibility toggle: `PUT /api/v2/config/{id}/dojo-visibility`
- Frontend: `EloTierBadge` shared component (6 tiers: Novice→Grandmaster), Elo badge on ActivationBar (paper bots), `'dojo'` tab in TabNavigation + MobileNav (paper bots only), `DojoTab` shell with visibility toggle

**Phase 2: Elo Engine** (`core/arena/elo.py`, `ggbot.py`):
- `elo_history` table + index. Stores all rating changes with reason, match reference, details JSONB
- `calculate_sortino_ratio()` — downside-only volatility, handles all edge cases (empty, all-positive, single trade)
- `calculate_composite_score()` — PnL + Sortino + max drawdown + win rate, format-specific weights (Blitz: PnL 60%, Standard: balanced 40/25/20/15), sigmoid normalization to 0-1
- `update_elo()` — standard formula, K-factor scaling (K=32 new, K=24 mid, K=16 established+high)
- `weekly_rolling_update()` — Swiss-system: trailing 7d scores, pair adjacent by rank, update Elo
- `GET /api/v2/dojo/elo-history/{config_id}` — paginated, auth-required
- Frontend: `DojoTab` rating history section with change indicators

**Phase 3: House Bots** (`decision/engine_v2.py`, `core/services/config_service.py`):
- `awareness_level` routing in `_handle_autonomous_trading()` — `low` = Signal Mode (opportunity analysis only, no position management). Used by House Bots. `medium` = default behavior (unchanged)
- `is_house_bot` added to `BotConfigV2` model, `get_config()`, `list_configs()` queries + dict construction
- 3 House Bot configs created: The Arbiter (Standard/4h), The Arbiter: Rapid (1h), The Arbiter: Blitz (15m). All BTC/USDT, `awareness_level: 'low'`, Elo 1200, inactive until tuned
- `GET /api/v2/public/dojo/house-bots` endpoint
- Frontend: DojoTab House Bots section with format labels, Elo badges, disabled Challenge buttons

**Planning Doc**: [DOCS/todo/DOJO.md](DOCS/todo/DOJO.md) — full design (790 lines). Phase 4 (1v1 Matches) pending.

---

## 2026-04-01 - ACP Agent Intelligence + Error Alerting + Frontend Fixes

**ACP Agent Adapter Fix** (`market_intelligence/gateway.py`, `adapters/acp/`):
- `ACPAgentAdapter` import broken since deployment — `ACP` → snake_case → `a_c_p_agent` (wrong). Added `ACP` → `Acp` special case in gateway `_adapter_name_to_module()`
- Renamed `acp_agent_adapter.py` → `acp_agent.py` to match gateway naming convention
- Added `_format_agentic_intelligence_data()` to `decision/engine_v2.py` — ACP agent deliverables were fetched but silently dropped at prompt formatting

**Third-Party ACP Agents** (`catalog_mapping.py`, DB seed):
- Discovered via `browse_agents()`: Otto AI (`0xe5B38F...`), Wolfpack (`0xbaC206...`), BlackSwan (`0x0aFE3b...`)
- Test purchases verified: Otto delivers markdown crypto news + bull/bear score ($0.01, ~19s). BlackSwan delivers risk flare status with 5K+ datapoints ($0.01, ~19s)
- Wolfpack disabled — requires Base token contract address, not compatible with perp trading
- Consolidated: removed `ggbots_acp` data point (self-consumption). Sebastian direct Redis read is sole ggbots source
- DB: 3 new data_points seeded under `agentic_intelligence` (39 total active data points, 8 categories)

**Frontend Model Selection Bug** (`frontend/app/forge/components/configure/StrategyEditor.tsx`):
- `handleModelChange()` only updated `model` field, left `provider` stale from previous selection
- User config had `provider: 'deepseek'` + `model: 'qwen'` → "Model Not Exist" error from DeepSeek API
- Fix: always reset `provider: 'openrouter'` on model change (all platform-key models route through OpenRouter)

**Bot Activation Validation** (`ggbot.py`):
- Added `selected_pair` check in `start_bot` endpoint — prevents bots from being activated without trading pair
- Matches existing frontend guard in `ActivationBar.tsx:186` (`hasStrategy` check)

**Transient Error Threshold** (`core/monitoring/error_alert_service.py`):
- SSL/connection errors now accumulate in 5-minute sliding window. Alert only after 3+ occurrences (real outage vs one-off blip)
- Format: `[3x in 5min] SSL connection has been closed unexpectedly`

**Arena/Landing Page Updates** (frontend):
- `/arena` page: replaced Season 2 competition UI with "Season 2 Postponed" + DGClaw directions
- Landing: Season 2 banner → "Degen Arena — LIVE" banner linking to DGClaw leaderboard
- Features CTA → "Build your bot in Forge". Footer → "Degen Arena" external link
- Forge: removed Season 2 announcement banner

**Documentation**: README.md updated (Hyperliquid/DGClaw, removed Symphony/Aster refs, PM2 services, LLM models). CLAUDE.md doc reference table updated. MI README updated (39 data points, ACP agents, directory structure). OK.md SOP rewritten (index-driven review).

---

## 2026-04-01 - Arena Pool Tokenization + Close Mirroring

**Pool Tokenization** (26 agents):
- Dispersed $1 USDC to each agent wallet via EOA (`0xFF0ab...`) on Base, then tokenized via `POST /acp/me/tokens` on claw API
- ggbot-005 through ggbot-030 now tokenized (GGBOT005-GGBOT030), ggbot-003 retired (tokenization conflict)
- Pool: 28 available, 10 assigned (Denis SZN2), 2 retired. All Denis agents funded ~$15 each on DGClaw

**Arena Close Mirroring** (`trading/virtuals/arena_sync.py` — NEW):
- Root cause: arena only mirrored opens + decision closes. Paper TP/SL, live TP/SL, manual closes bypassed arena
- `mirror_close_to_arena()` — idempotent function checks DGClaw position exists before closing. Safe for duplicate calls
- Hook 1: `trading/paper/supabase_service.py:close_position()` — covers paper TP/SL/liquidation/manual
- Hook 2: `core/monitoring/adapters/hyperliquid_adapter.py:_detect_and_log_closes()` — covers live TP/SL fills
- Hook 3: `ggbot.py:close_hyperliquid_position()` — covers live manual close
- Fix: orchestrator close path now logs `arena_exit` activity (was returning before activity logging)

**Arena Reconciler** (`core/orchestrator/orchestrator.py:_reconcile_arena_position()`):
- Safety net: before each arena trade, compares DGClaw positions vs primary (paper/live). Closes stale arena positions
- Activity types: `arena_exit` with sources `arena_sync`, `claw_arena`, `arena_reconciler`

---

## 2026-03-28 - Production Fixes: Candle Cache, ACP Adapter, Prompt Consistency

**Error log audit** covering 16h of production logs. Five issues identified, all fixed.

**WebSocket candle cache 200→300** (`core/services/websocket_market_data_service.py`, `market_intelligence/adapters/market_data/redis_websocket.py`):
- EMA200 (shipped 2026-03-21) needs 250 candles; WS cache only stored 200 → every bot cycle fell back to Binance REST
- Hundreds of daily warnings eliminated. Also reduces blast radius of Binance REST outages (e.g., 08:01 UTC cascade: 34 extraction failures when REST also timed out)
- Redis key changed `:200`→`:300`; old keys TTL away naturally

**ACP adapter KeyError fix** (`market_intelligence/catalog/data_types/acp/acp_agent.yaml`, `market_intelligence/orchestrator.py`):
- `acp_agent.yaml` had no `query_params` schema → `validate_params()` returned empty dict → `build_cache_key()` failed formatting `{agent_name}` → 14 errors/day
- Added `query_params` section (agent_name, agent_address, offering_name, service_requirement)
- Also fixed `_replace_param_templates()` to recurse into nested dicts — `{config_id}` inside ACP `service_requirement.bot_id` was unreplaced (literal string)

**Opportunity analysis prompt consistency** (`decision/prompts/opportunity_analysis.py`):
- ggRapid bot outputting only `wait` despite reasoning concluding "sufficient confluence for long/short" with SL/TP prices
- LLM reasoning-action disconnect: model builds trade case then hedges at ACTION line
- Added CRITICAL instruction: ACTION must match REASONING conclusion. If confluence found, output trade action

**Stale MI source names** (DB fix, 2 configs):
- Saa Moja: `on_chain_analytics` → `onchain_analytics` (source renamed, config not migrated)
- The Analyst: `sentiment.sentiment` → `sentiment_social.twitter_sentiment`

---

## 2026-03-26 - DGClaw Arena Phase 1 + Phase 2 Validation

**Architecture Doc**: [trading/virtuals/README.md](trading/virtuals/README.md)

Arena is parallel execution layer — bot trades normally (paper/live), same decision also mirrors to DGClaw via ACP. Every arena trade = on-chain ACP transaction = $GG volume.

**Phase 2 Validation — Lite Agent Pool Model**:
- Discovered lite agents use **claw REST API** (`x-api-key` header) instead of EOA/SDK signing
- Privy-managed signer handles on-chain transactions automatically via `https://claw-api.virtuals.io`
- Full programmatic flow proven: create agent → tokenize → fund → register DGClaw → deposit → trade
- Test agent `ggbots-arena-test-001` (GGBOT001): created, funded $6, registered, deposited $4.99 to HL, opened ETH long $12 @ 3x
- Key endpoints: `POST /acp/jobs` (create), `GET /acp/jobs/{id}` (poll), `GET /acp/wallet-balances`
- Agent pool model viable: batch-create ~50 lite agents per auth session (30min JWT), tokenize on dashboard, assign to users on demand
- No user-side Virtuals interaction needed — user just sends USDC to assigned agent wallet

**DGClaw Arena Service** (`trading/virtuals/dgclaw_service.py`, new):
- `execute_arena_trade()` — full ACP job lifecycle (initiate → pay → poll → receipt, ~20-50s)
- `close_arena_position()` — close via ACP `perp_trade` action=close
- `get_arena_account()` — queries DGClaw Railway backend (`dgclaw-app-production.up.railway.app`)
- Position sizing: `confidence × max_margin% × balance × leverage`, 90% safety cap, $10 min
- Payment retry on "No negotiation memo" (timing issue — memo not ready on first poll)

**Orchestrator Arena Hook** (`core/orchestrator/orchestrator.py`):
- `_is_arena_enabled()` — checks `ARENA_ENABLED_CONFIGS` env var (comma-separated config IDs)
- `_enqueue_arena_trade()` — LPUSH to `arena:trade_queue` (fire-and-forget, never blocks bot cycle)
- Hooks in both `_run_autonomous_trading_cycle()` and `_run_signal_validation_cycle()`

**Sebastian-Virtuals Section D** (`sebastian_virtuals.py`):
- `process_arena_trades()` — RPOP from `arena:trade_queue`, dispatches to dgclaw_service
- `DGClawArenaService` initialized on startup alongside ACP client
- Max 3 trades per 30s poll cycle

**Key Discovery — DGClaw Fund Management**:
- DGClaw pools funds centrally, NOT per-HL-subaccount. Subaccount only holds active margin.
- HL Info API shows $0 between trades (misleading). Railway backend has real balance.
- API: `/users/{wallet}/account`, `/users/{wallet}/positions`, `/users/{wallet}/trades`
- Reference: https://github.com/Virtual-Protocol/dgclaw-skill.git

**Config**: Sev's live HL bot (`b9d9bf00...`) as admin arena bot. $35.79 DGClaw balance. PM2: removed `sebastian-chrome` (245MB), started `sebastian-virtuals` with DGClaw env vars.

---

## 2026-03-26 - Async DB Migration: Eliminate Bot Execution Deadlocks

**Root cause**: 2026-03-24 19:00 UTC, 20/37 bots permanently hung. Sync psycopg2 `get_db_connection()` blocked asyncio event loop when 29+ bots fired at candle boundary. APScheduler `max_instances=1` prevented recovery → bots stuck until manual restart.

**Async DB helpers** (`core/common/db.py`):
- Added `db_fetch_one`, `db_fetch_all`, `db_execute`, `db_execute_returning` — wrap sync queries in `asyncio.to_thread()`
- `get_db_connection()` unchanged for sync callers (API, monitors)

**20 call sites migrated across 6 hot-path files**:
- `core/orchestrator/orchestrator.py` — 4 sites (subscription check, stale cleanup, position lookups)
- `decision/engine_v2.py` — 10 sites (6 DB calls + 4 activity logger wraps via `asyncio.to_thread(lambda: ...)`)
- `market_intelligence/orchestrator.py` — 1 site (`_check_permission`, called 4-12x per cycle)
- `market_intelligence/adapters/signals/ggshot_adapter.py` — 2 sites
- `market_intelligence/adapters/internal/market_conditions.py` — 1 site
- `core/scheduler/bot_runner.py` — reconcile loop DB query wrapped

**Scheduler hardening** (`core/scheduler/bot_runner.py`, `ggbot_scheduler.py`):
- `asyncio.wait_for(cycle, timeout=300)` — kills hung cycles, frees APScheduler slot, deletes Redis idempotency key for retry
- `ThreadPoolExecutor(max_workers=32)` as default executor
- `Semaphore(30)` — concurrency cap with headroom for connection pool (maxconn=50)
- TCP keepalive on connection pool (`keepalives_idle=30`) — prevents Supabase PgBouncer from closing idle connections

**Single-flight pattern** (`market_intelligence/gateway.py`):
- Class-level `_inflight: Dict[str, asyncio.Lock]` prevents thundering herd on cache misses
- When 40 bots request same Grok data simultaneously, only first triggers API call; rest wait and read cache
- Reduces peak Grok API calls from ~320 (40 bots × 8 data points) to ~12 unique calls per boundary
- Verified working: "Cache hit after lock wait" entries in logs for funding_rate and Grok data

**LLM model updates** (`decision/llm_providers/openrouter_provider.py`, `llm_models` DB):
- Claude standard: `sonnet-4.5` → `sonnet-4.6` (same $3/$15, 1M context)
- Claude premium: `opus-4.5` → `opus-4.6` (same $5/$25, now 1M context vs 200K)
- Grok premium: `grok-4` → `grok-4.20-beta` ($2/$6 vs $3/$15, 2M context vs 256K)

**Result**: 16:00 4h mega-boundary (40+ bots): 36 completed, 2 timed out (slow Kimi LLM, not infra). Non-peak boundaries: 28-30/30 complete in 28-47s. Zero permanent hangs.

**Capacity**: ~100 bots with zero changes. Tuning knobs: semaphore (30→50), ThreadPool (32→48), pool maxconn (50→80). Asyncpg migration at 300+ bots.

---

## 2026-03-24 - ACP Agent Intelligence: Buyer + Provider Infrastructure

**Planning Doc**: [DOCS/todo/ACP_AGENT_INTELLIGENCE.md](DOCS/todo/ACP_AGENT_INTELLIGENCE.md)

**Agent Registration** (revised from Sebastian → $GG token agent):
- ggbots.ai registered as Hybrid agent linked to $GG token (`isVirtualAgent: true`)
- Smart wallet `0x2E48f...`, Sebastian wallet `0xDAD56...` as separate provider
- On-chain entity_id is **2** (not API ID 40623) — SDK validates signer via `signers(entity_id, wallet)` on `SingleSignerValidationModule`
- First live ACP transactions: Otto AI crypto_news ($0.01) + self-consumption ggbots→Sebastian ($0.07)

**ACP Client** (`core/services/acp_client.py`):
- Singleton wrapper, dual-client: buyer (ggbots.ai wallet) + provider (Sebastian wallet)
- Lazy init from env vars, polling mode (`skip_socket_connection=True`)
- Buyer: `buy_from_offering()`, `pay_job()`, `get_deliverable()` — full job lifecycle
- Provider: `get_pending_provider_jobs()`, `accept_job()`, `deliver_job()`
- Agent discovery cache in Redis (`acp:agent:{address}`, 1hr TTL)

**MI Adapter** (`market_intelligence/adapters/acp/acp_agent_adapter.py`):
- Cache-first: reads Redis, never blocks bot cycle on ACP
- Cache miss → enqueues job to `acp:job_queue` (Redis list), skips gracefully
- Dedup via `acp:pending:{agent}:{hash}` markers (SET NX, 600s TTL)
- Catalog YAML at `market_intelligence/catalog/data_types/acp/acp_agent.yaml`

**Background Service** (`sebastian_virtuals.py`):
- PM2 service `sebastian-virtuals` with 30s poll loop
- Provider: polls pending jobs → reads market_conditions from DB → delivers
- Buyer queue: pops from `acp:job_queue` → initiates ACP jobs on-chain
- Buyer monitor: polls active jobs → pay/collect/cache deliverables in Redis

**Catalog + Routing**:
- `gateway.py`: added `'acp'` category routing
- `catalog_mapping.py`: `ggbots_acp` entry active, Otto/Wolfpack/BlackSwan commented (pending address discovery)
- DB seed: `ggbots_acp` data point under `agentic_intelligence` source

**Known Issue**: Self-consumption evaluate reverts with `OnlyCounterParty()` because both wallets share same EOA/entity_id. Fix: create separate EOA for Sebastian.

---

## 2026-03-21 - Extraction Enrichment: Multi-Period MAs + Channel Price Levels + BB Fix

**Preprocessor Summary Gaps** (user report: SZN2 bots hitting PARSE_FAIL):
- Channel indicators (Donchian, BB, Keltner) only showed `%pos`/`%B` — missing actual price levels
- EMA only computed period-20 — no EMA50/EMA200 available to strategies
- BB preprocessor never wired up — `calculate_bollinger_bands()` bypassed advanced preprocessor entirely

**Multi-Period EMA/SMA** (`extraction/v2/indicators.py`):
- `calculate_ema()` / `calculate_sma()` now compute 20/50/200 in single pass
- Summary: `EMA20=2102.57 (falling), EMA50=2107.19 (falling), EMA200=2123.37 (rising). Price below all. Death cross (50<200)`
- Golden/death cross detection (50 vs 200) included automatically
- Graceful degradation: 100 candles → EMA20+50 only, 250+ → all three
- Values stored in `result['current']['ema20']`, `ema50`, `ema200`
- Smart limits (`smart_limits.py`) bumped from 100→250 candles for EMA/SMA

**Channel Summary Enrichment** (`extraction/v2/preprocessors/`):
- `donchian.py`: `Donchian %pos=23%, Upper=2113.43, Mid=2103.49, Lower=2093.54`
- `bbands.py`: `BB %B=0.19 (near lower), Upper=2110.75, Mid=2102.95, Lower=2095.16`
- `keltner.py`: `Keltner %pos=29% (lower channel), Upper=2113.20, Mid=2102.57, Lower=2091.94`

**BB Preprocessor Wire-Up** (`extraction/v2/indicators.py`):
- `calculate_bollinger_bands()` now routes through advanced preprocessor (was legacy fallback, no `summary`)
- Cleaned up 3 duplicate BB dispatch branches → 1 canonical `"bbands"` case
- All bots using `"BB"` now get enriched summary with squeeze detection, walking bands, patterns

**Stripe Fix**: Usage-based price ID inactive since ~Jan 22 (`price_1SSz0E...` → `price_1SsU8V...`). New pay-as-you-go checkouts broken ~2 months. Existing subscribers unaffected. `.env` updated.

---

## 2026-03-21 - Market Conditions: Sebastian AI Research Agent Integration

New MI data source: daily cross-market intelligence report produced by Sebastian (personal AI research agent). Covers equities, bonds, commodities, crypto, monetary policy, geopolitics, dominant narratives. First report: Iran war / energy crisis macro regime assessment.

**Supabase Table** (`database/migrations/add_market_conditions_table.sql`):
- `market_conditions` — 10 columns: `regime` (jsonb), `domains` (jsonb), `narratives` (jsonb), `synthesis` (text), `data_quality` (jsonb), `raw_tables` (jsonb). Indexed on `generated_at DESC`

**API Endpoints** (`ggbot.py:3458-3580`):
- `GET /api/v2/market-conditions/latest` — Sebastian reads previous report for temporal context
- `POST /api/v2/market-conditions` — Sebastian writes new report after daily research pass
- Dedicated `SEBASTIAN_API_KEY` auth (independent of Supabase/admin auth)

**MI Adapter** (`market_intelligence/adapters/internal/market_conditions.py`):
- `MarketConditionsAdapter` — reads Redis cache first, falls back to Supabase query
- Formats for LLM: domain summaries, narrative bullets, synthesis paragraph
- Freshness: warns >26h, rejects >48h. Confidence 0.85 base, decays with age

**Pipeline Wiring**:
- Catalog: `catalog/data_types/internal/market_conditions.yaml`
- Mapping: `('market_conditions', 'daily_brief')` → `MarketConditionsAdapter`, `global: True`
- Gateway: `market_conditions` routes to `internal` adapter category (`gateway.py:307`)
- DB seed: `data_sources` + `data_points` rows (free tier, auto-populates in frontend bot builder)

**Context**: Part of ACP Agent Intelligence initiative ($GG graduation). Sebastian produces daily market conditions → consumed by bots via MI pipeline → later wrapped as ACP provider agent for Virtuals ecosystem.

---

## 2026-03-20 - Business Analytics: Status Check + Admin API + Dashboard

**Status Check Business Metrics** (`scripts/status_check.py`):
- `get_business_metrics()` — 9 queries: revenue (monthly/MTD/30d), conversion funnel, cohort conversion (Jan+), DAU/WAU/MAU, retention, LTV by tier, power users, live trading, growth
- `print_business_report()` — formatted console output for business section
- `update_active_md()` now renders "Business Metrics" section (revenue, funnel, engagement, HL stats)
- Quiet mode includes `Rev(30d)` + `DAU/WAU/MAU` for monitoring

**Admin Analytics API** (`api/admin.py`):
- `GET /api/v2/admin/analytics` — returns all business metrics as JSON, same data as status check
- Revenue: monthly breakdown, MTD, projected, 30d MRR proxy, margin %
- Funnel: signup → bot creation → ran bot → active → paid (with %)
- Cohorts: per-month signups vs paid (post-monetization Jan+)
- Engagement: DAU/WAU/MAU, stickiness ratios, power users (4+/8wk)
- Retention: 30d+ cohort active in 7d/30d
- LTV: by tier (users, total rev, avg/max), overall avg
- Live trading: HL connected, active bots, volume, P&L

**Admin Analytics Dashboard** (`frontend/app/admin/analytics/page.tsx`):
- KPI cards: all-time revenue, 30d revenue, MTD projected, avg LTV
- Revenue stacked bar chart (cost + margin by month, Recharts)
- Conversion funnel visualization (horizontal bars with %)
- Engagement panel: DAU/WAU/MAU, stickiness, power users, retention
- Cohort conversion table (monthly signups vs paid, color-coded %)
- Growth chart: monthly signup bars (pre-monetization gray, post-Jan blue)
- LTV table by tier, live trading stats grid, revenue detail table
- Nav link added to main admin page (`frontend/app/admin/page.tsx`)

**Investor Metrics Doc** (`DOCS/business/INVESTOR_METRICS_2026_03_19.md`):
- One-page briefing: revenue, funnel, engagement, LTV, CAC analysis, growth catalysts
- Key metric: 22.4% signup-to-paid post-monetization (4-5x B2C SaaS avg)

---

## 2026-03-17 - Bot State v1 + OHLCV Cache Fix + HL Position Fix

**OHLCV Stale Cache Bug** (`market_intelligence/cache/manager.py`, `catalog/data_types/market_data/ohlcv.yaml`):
- MI gateway cached OHLCV data 1 hour (`mi:candles:*` TTL 3600s), masking real-time WebSocket cache (`ws:candles:*`)
- 30m bots saw identical prices across 2-3 consecutive cycles (user report)
- Fix: `ttl: 0` in ohlcv.yaml, `cache/manager.py` skips set/get when `ttl <= 0`
- Existed since Universal Data Layer (Oct 2025, commit `6ddb347`)

**Bot State v1: Account Performance → Monitor + Redis** (`market_intelligence/adapters/internal/account_performance.py`, `core/monitoring/universal_account_monitor.py`):
- Root cause: `AccountPerformanceAdapter` ran sync DB queries (`psycopg2` pool, maxconn=20) in async bot pipeline → `pool.getconn()` blocked event loop → deadlock when 16+ bots fire at 1h boundary → APScheduler `max_instances=1` prevented recovery → bots permanently stuck
- Fix: account-monitor (separate PM2 process) pre-computes stats every 5 min → `acct_perf:{config_id}` Redis key (600s TTL). Adapter reads from Redis (sub-ms, no DB)
- New fields: `consecutive_wins`, `consecutive_losses`, `hours_since_last_trade`, `drawdown_duration_hours`, `largest_win_pct`, `largest_loss_pct`
- HL deposit-immune metrics: `equity_change_pct` uses `total_pnl / initial_equity * 100`, drawdown from `MAX(total_pnl)` series
- Catalog TTL → 0 (no gateway double-cache)
- 9 bots across 4 users were stuck (1h frequency primarily affected)

**HL Cross-Margin liquidationPx Fix** (`trading/live/hyperliquid_service.py:1086`):
- `pos.get("liquidationPx", 0)` returned `None` (key exists as null for cross-margin) → `float(None)` crash
- Dashboard SSE fired error every 6 seconds per HL user
- Fix: `pos.get("liquidationPx") or 0` — `or` coalesces explicit `None` to default

---

## 2026-03-17 - Deposit/Withdrawal Detection + TWR % Chart Toggle

**Deposit/Withdrawal Activity Detection** (`core/monitoring/adapters/hyperliquid_adapter.py`):
- `_detect_and_log_transfers()` queries `user_non_funding_ledger_updates()` (1hr lookback), filters `deposit`/`withdraw` types
- Dedup via `_logged_transfers: Set[str]` keyed by tx hash (same pattern as `_logged_closes`)
- Logs `deposit`/`withdrawal` activity types via `log_activity_safe()`, importance 8
- Backfill script (`scripts/backfill_deposit_activities.py`) — populated 11 historical transfers across 3 users

**TWR Percentage Chart Mode** (`api/snapshots.py`, `core/domain/metrics_calculator.py`):
- `?display=pct` query param on both `balance-series` and `performance-series` endpoints
- `AccountMetricsCalculator.calculate_twr()` — chains sub-period returns around deposit/withdrawal flows, returns cumulative TWR %
- Deposits/withdrawals don't inflate return — only trading P&L counts

**Frontend $ / % Toggle** (`frontend/components/tv-timeline.tsx`):
- `DisplayMode` state (`dollar` | `pct`), brass pill toggle next to mode selector
- Pct mode: Y-axis `X.XX%` format, 0% dashed baseline price line, `pct_series` parsing
- Deposit/withdrawal markers: brass arrowUp/arrowDown with `+$N`/`-$N` text labels
- `activity-modal.tsx` — added deposit (💰) and withdrawal (💸) to `getActivityTypeInfo()`

**Dashboard Performance Fix** (`core/sse/dashboard_data.py:199-207`):
- HL bots: `performance_pct = total_pnl / initial_equity * 100` (deposit-immune)
- Paper/other bots: unchanged `(current_equity - initial_equity) / initial_equity * 100`

---

## 2026-03-13 - Decision Engine Cache Removal + Light Mode Timeframe Fix

**Decision Engine Stale Config Bug** (`core/orchestrator/orchestrator.py`):
- `_decision_engines` LRU cache caused 14-hour stale strategy execution — scheduler process cached `DecisionEngineV2` instances, never refreshed `self.config` after DB updates
- Root cause: two-process architecture (API + scheduler) meant `invalidate_engines()` only cleared API process cache, scheduler never notified
- Fix: removed `_decision_engines` cache, `MAX_DECISION_ENGINES`, `invalidate_engines()` method entirely. `_get_decision_engine()` now creates fresh engine each cycle (2 DB queries, trivial cost)
- Removed dead `invalidate_engines()` calls from `ggbot.py:741` and `api/assistant.py:651`
- Extraction engine cache (`_extraction_engines`) unchanged — stateless, keyed by user_id, no stale-config risk

**Light Mode Timeframe Button Contrast** (`frontend/app/forge/components/configure/MarketDataSelector.tsx`):
- Per-indicator and global timeframe selector buttons had inverted visual states in light mode
- Selected: `bg-*/20` + `border-*/30` barely visible on light parchment background
- Fix: selected → `bg-*/30` + full-opacity border; unselected → `bg-transparent` (no competing fill)

**NOWPayments Webhook Fix** (`.env`):
- `API_BASE_URL` was `localhost:8000` after env var rename (commit `890a598`), causing IPN callbacks to fail silently
- Fixed to `https://ggbots-api.nightingale.business`; manually granted $10 credit for one completed payment (Walter)

**Hyperliquid Signing Fixes** (`frontend/components/hyperliquid/LiveTradingModalContent.tsx`):
- v-value normalization: `if (v < 27) v += 27` — some wallets return 0/1 instead of 27/28
- Chain validation: added Arbitrum network check + auto-switch before EIP-712 signing (prevents "Unable to recover signer" on wrong chain)

**Credits Display Fixes** (`frontend/app/forge/components/layout/UserProfile.tsx`):
- "This week" label → "This month" (backend returns monthly data from Redis `usage:user:{id}:YYYY-MM`)
- Added "Used" line alongside "Balance" for prepaid/usage_based users (was hidden when `credits_usd > 0`)

---

## 2026-03-10 - ggArena Season 2 — Phase A: Arena Page Update

**Planning Doc**: [DOCS/todo/ARENA_SEASON2.md](DOCS/todo/ARENA_SEASON2.md) (Phase B pending)

Season 2 Training Grounds launched. Arena page now defaults to S2 view with S1 results accessible via toggle.

**S2 Phase System** (`ArenaWithStaking.tsx:17-74`):
- `S2_DATES` constants (training Mar 10, registration Apr 1-6, competition Apr 7-28)
- `getS2Phase()` — client-side phase computation from `Date.now()`, 60s polling
- `getPhaseDayProgress()` — "Day N/22" progress for current phase
- Phase-dependent hero subtitle, CTA button text, countdown targets

**Timeline Visualization** (`ArenaWithStaking.tsx:460-520`):
- 4-node horizontal timeline: Training → Registration → Competition → Results
- Current phase highlighted with accent + pulse animation, past phases checkmarked
- `CountdownTimer` reused with `getCountdownTarget()` for next phase transition

**Season Toggle** (`ArenaWithStaking.tsx:279`):
- `seasonView` state: `'s2'` (default) or `'s1'`
- S1 leaderboard (Top3, Autonomous, Overall) wrapped in `seasonView === 's1'` guards — code untouched
- S1 hero shows "Back to Season 2" link, S2 hero shows "View Season 1 Results →"

**Rules + How It Works** (`ArenaWithStaking.tsx:948-1055`):
- 10 numbered rules in brass-accent card (entry, registration lock, 18/21 activity, $GG prizes)
- "How It Works" unhidden, updated: Build → Register → Compete → Win

**Other Changes**:
- SEO metadata updated for S2 (`layout.tsx`)
- Forge banner → "Season 2 — Training Grounds Open", new `arena-s2-banner-dismissed` localStorage key (`forge/page.tsx`)
- ActivationBar arena button title updated to S2, stays hidden until Phase B (`ActivationBar.tsx`)

---

## 2026-03-07 - Account Performance as MI Data Source (Statefulness Phase 2a)

Community-requested (Denis @ Buidler Labs). Bots now see their own trading history — win rate, drawdown, recent trades — as market intelligence data. User checks "Trading History" checkbox → adapter queries internal DB → data flows into LLM prompt alongside VIX, funding rates, etc. No new toggles or concepts.

**New Adapter** (`market_intelligence/adapters/internal/account_performance.py`):
- `AccountPerformanceAdapter` — queries `paper_accounts`/`paper_trades` (paper) or `live_trades`/`account_snapshots` (HL)
- Returns: equity, drawdown from peak, win rate, avg win/loss %, last 10 trades with P&L % and close reason
- Per-config routing via `{config_id}` template in `_replace_param_templates` (new, alongside `{symbol}`)
- 5-min Redis cache (`intel:account_perf:{config_id}`), $0/query (internal DB only)

**Pipeline Integration** (`orchestrator.py`, `catalog_mapping.py`, `gateway.py`):
- Orchestrator passes `config_id` + `trading_mode` to template replacement (~5 lines)
- Gateway routes `account_performance` adapter to `internal` category (1 line)
- Catalog YAML auto-discovered via `rglob` in `catalog/data_types/internal/`
- DB seed: `data_sources` + `data_points` rows (free tier, auto-populates in frontend)

**LLM sees**: `ACCOUNT PERFORMANCE: Account down 15.5% from peak. 5W 7L (41.7% win rate). Last 5: SHORT BTC -2.3% (SL, 4h ago)...`
User strategy can reference: "If drawdown >20%, reduce size by half" or "After 3 consecutive losses, wait one cycle."

---

## 2026-03-07 - Position Management: Statefulness Phase 1 + HL Fixes

Enriched position management prompt with statefulness fields and fixed 3 data gaps for Hyperliquid live trading. All changes in `decision/engine_v2.py`.

**Phase 1 Statefulness** (`_format_position_data_for_llm`):
- `bars_in_trade` — derived from `duration / TIMEFRAME_SECONDS[analysis_frequency]`. LLM sees "4.2 hours (1 bars at 4h)" vs "80.5 hours (20 bars at 4h)" — distinguishes fresh from stale positions
- `max_drawdown` — Redis key `trade:max_drawdown:{trade_id}` (7-day TTL). Each cycle compares current P&L% to stored worst, updates if lower. Rendered as `(worst: -8.3%)` only when meaningfully different from current P&L — gives LLM recovery context

**HL Position Management Fixes** (`_get_active_position` HL builder + formatter):
- SL/TP computed from `entry_price * (1 ± risk_management.default_stop_loss_percent)` — was `None` ("None set") even though orders exist on exchange
- Leverage rendered as `(10x leverage)` after position type — was invisible to LLM for both paper and HL
- Side normalized: `buy→long`, `sell→short` mapping — paper used `BUY`, HL used `LONG`, now consistent
- Paper query now includes `pt.leverage` column

---

## 2026-03-07 - Configurable Timeframes + Strategy Advisor Fix

Timeframes now explicitly configurable. Previously: archetypes set 1 TF, toggling any indicator in MarketDataSelector silently reset to all 7, Strategy Advisor could collapse TFs via `deep_merge()` list replacement. 407/506 bots had 1 TF, 75 had 7 — jump was accidental.

**Timeframe Picker UI** (`frontend/.../MarketDataSelector.tsx`):
- Collapsible "Timeframes" section below indicator grid, shows count or "All (7)"
- 8 toggle buttons: All + 7 individual TFs. Min 1 TF enforced (last one disabled)
- Only applies to `technical_analysis` — MI categories (sentiment, funding, macro) are Grok-based and don't use timeframes
- Indicator toggle now preserves existing category timeframes instead of overwriting with all 7

**Backend Defaults** (`frontend/lib/archetypes.ts`, `api/assistant.py`):
- All 3 archetypes (Contrarian, Compass, Arbiter) default to all 7 TFs (was single TF each)
- AI config creation (`CONFIG_CREATION_PROMPT_TEMPLATE`) example + guideline #7: always use all 7 unless user requests fewer
- Strategy Advisor rule #9: preserve existing timeframes unless intentionally changing, state changes explicitly

**Activity Modal** (`frontend/components/activity-modal.tsx`):
- Market query activities show TF list ("5m, 15m, 1h, 4h") instead of just count ("4")

---

## 2026-03-07 - Market Intelligence: USDT Dominance + MOVE Index

Community-requested by Denis @ Buidler Labs. Two new macro data points under Macro Economics category.

**USDT Dominance** — New `CoinGeckoGlobalAdapter` (`market_intelligence/adapters/macro/coingecko_global.py`):
- Fetches `data.market_cap_percentage.usdt` from CoinGecko `/global` endpoint. $0/query (free tier)
- Thresholds: >10% risk-off (bearish), 6-10% neutral, <6% risk-on (bullish)
- Also captures total crypto market cap and 24h change
- New catalog YAML (`catalog/data_types/macro/coingecko_global.yaml`), 4hr cache

**MOVE Index (Bond Volatility)** — New Grok prompt template (`grok_agentic.py`):
- ICE BofA MOVE Index via web search. ~$0.005/query, 4hr cache
- Thresholds: <80 low stress (bullish), 80-120 moderate, >120 high stress (bearish), >150 extreme

**Wiring**: Gateway routing added `CoinGecko` → `Coingecko` special case + `'coingecko'` macro category detection (`gateway.py`). Two catalog mapping entries (`catalog_mapping.py`). Two DB rows in `data_points` (both free, enabled). Total: 35 data points across 6 categories.

---

## 2026-03-07 - Fix: Stale Market Data in LLM Prompts

**Bug**: Config changes (timeframe removal, indicator edits) left orphaned `market_data` rows in DB. Decision engine (`engine_v2.py:485-490`) queried `WHERE config_id AND symbol` with no timeframe filter — stale rows from previous configs injected into LLM prompts. ROBBOT had 42-hour-old 5m data with 9 wrong indicators reaching LLM every cycle. 14/312 bots affected, 26 stale rows total.

**Fix A — Decision engine filter** (`decision/engine_v2.py:484-508`): `_get_fresh_market_data()` now extracts configured timeframes from `self.config.extraction` and adds `AND timeframe = ANY(%s)` to query. Falls back to unfiltered for bots without timeframe config.

**Fix B — Extraction cleanup** (`core/orchestrator/orchestrator.py:765-781`): After extraction completes, `DELETE FROM market_data WHERE timeframe != ALL(configured_timeframes)` removes orphaned rows. Logged as info when rows deleted, wrapped in try/except (non-critical).

**One-time cleanup**: Deleted 26 stale rows across 14 bots.

---

## 2026-03-07 - Audit: Live Trading Integration (4 Bug Fixes)

Full audit of Sev's live Hyperliquid bot (config `b9d9bf00`, 18 days, 11 trades). Found and fixed 4 bugs across dual close-logging paths.

**Schema Migration** (`live_trades`):
- Added 6 columns: `side`, `entry_price`, `exit_price`, `size_usd`, `leverage`, `realized_pnl`
- Backfilled all 11 trades from Hyperliquid `user_fills_by_time` API
- P&L now stored per-trade (same pattern as `paper_trades`) — snapshot reads `SUM(realized_pnl)` instead of recomputing from fills API

**Bug 1: Duplicate Close Activities** (`core/monitoring/adapters/hyperliquid_adapter.py`):
- Two independent paths logged `trade_exit`: `hyperliquid_service.close_position()` (decision-triggered) AND `hyperliquid_adapter._detect_and_log_closes()` (fill-scan safety net)
- Fix: cross-source dedup — adapter checks `activities` table for recent service-logged exit before logging its own

**Bug 2: Partial Fill P&L** (`core/monitoring/adapters/hyperliquid_adapter.py`):
- `market_close()` produces multiple fills at same timestamp. Adapter processed individual fills, logging P&L for one partial instead of aggregate
- Fix: group fills by `(coin, fill_time)`, sum quantities and compute weighted-average exit price before logging

**Bug 3: Fill Window Drift** (`core/monitoring/adapters/hyperliquid_adapter.py`):
- `get_current_snapshot()` called `user_fills_by_time()` with hardcoded 7-day window — trades older than 7 days disappeared from stats, pre-bot fills polluted P&L
- Fix: replaced fills API call with `SELECT SUM(realized_pnl) FROM live_trades WHERE config_id = %s`. Eliminated one API call per 5s snapshot cycle. Win/loss/total/avg stats also from `live_trades`

**Bug 4: Duration Timezone** (`trading/live/hyperliquid_service.py`):
- `live_trades.created_at` is naive `timestamp`, `datetime.now(timezone.utc)` is aware — subtraction raises `TypeError` caught silently by bare `except`, duration always 0.0s
- Fix: `.replace(tzinfo=timezone.utc)` for naive datetimes before arithmetic

**Adapter Rewrite** (`core/monitoring/adapters/hyperliquid_adapter.py`):
- `_detect_and_log_closes()`: complete rewrite — fill aggregation, cross-source dedup, writes `exit_price`/`realized_pnl` to `live_trades`
- `get_current_snapshot()`: trade stats section reads from `live_trades` table (total/wins/losses/pnl/avg_win/avg_loss/largest)

**Service Updates** (`trading/live/hyperliquid_service.py`):
- `_save_trade_record()`: expanded to store entry data (side, entry_price, size_usd, leverage)
- `_mark_trade_closed()`: expanded to store exit data (exit_price, realized_pnl)

**Verified**: `live_trades` SUM ($-9.06) matches Hyperliquid fills exactly. $1.57 gap to balance delta ($-10.63) = expected funding fees over 18 days.

---

## 2026-03-07 - Credits vs Trading Funds UX Redesign

Pre-$GG launch UX fix: new users confused Hyperliquid deposit (trading funds) with LLM credits (bot decision costs). Redesigned billing UX across 6 frontend components.

**UserProfile Dropdown** (`frontend/app/forge/components/layout/UserProfile.tsx`):
- "Credits" section renamed "AI Credits" with subtitle "Powers your bot decisions"
- "Hyperliquid" section renamed "Trading Funds" with subtitle "Your capital on Hyperliquid"
- "Manage Billing" removed from dropdown (moved into Settings Modal)
- "Add Credits" button renamed "Add AI Credits". Dropdown widened `w-56` to `w-64`

**Settings Modal** (`frontend/components/SettingsModal.tsx`):
- Full redesign as billing hub. Two sections: "AI Credits" (required for all bots) + "Live Trading" (optional, labeled separate from credits)
- AI Credits section: plan badge, usage/balance breakdown, inline "Add AI Credits" + "Open Stripe" buttons
- Free users see subscribe CTA with "$1/week" anchor. Live Trading section labeled "(Optional)"

**ActivationBar** (`frontend/app/forge/components/monitor/ActivationBar.tsx`):
- Credit exhaustion banner: "AI credits depleted" + live traders see "Your Hyperliquid trading funds are safe"

**LiveTradingModalContent** (`frontend/components/hyperliquid/LiveTradingModalContent.tsx`):
- After HL connection, info card for users without subscription: "Almost ready to trade live — you also need AI credits for decisions"

**UpgradeModal** (`frontend/components/UpgradeModal.tsx`):
- HL-connected users see callout: "This covers AI decisions only. Your Hyperliquid trading funds are separate."

**AddCreditsModal** (`frontend/components/AddCreditsModal.tsx`):
- Title: "Add AI Credits". Description: "AI credits pay for your bot's decisions."

---

## 2026-03-07 - Fix: Live Config 404 on Update

**Bug**: PUT `/api/v2/config/{id}` returned 404 for Hyperliquid live bot configs. Live slot auto-created with empty `config_data={}` during HL setup (`ggbot.py:1590`). `validate()` in `config_service.py:156` rejected empty `selected_pair` → `update_config()` returned `None` → 404. Blocked all direct edits on unconfigured live bots.

**Fix** (`core/services/config_service.py:155-159`): Early return in `validate()` when `trading_mode == 'hyperliquid'` and no `selected_pair` — treats unconfigured live bots as "setup mode". Activation already gated separately by ActivationBar (requires `selected_pair` before activate/run). Same pattern as existing agent config early-return.

---

## 2026-03-04 - Database IO Optimization: Redis Position Tracking + Dashboard Query Fix

**Problem**: Supabase disk IO hitting limits. Two root causes: (1) `paper_trades` position monitor writing ~230K ephemeral price updates/day to Postgres, (2) dashboard SSE query consuming 98% of total DB execution time due to unfiltered CTEs and seq scans on 406K-row `account_snapshots`.

**Part 1: Position Prices → Redis** (`trading/paper/supabase_service.py`):
- `update_position_prices()` now writes `current_price`/`unrealized_pnl` to Redis hashes (`position:prices:{trade_id}`, 30s TTL) instead of batch SQL UPDATE
- Per-config aggregate PnL cached at `position:pnl:{config_id}` for quick equity lookups
- Added `enrich_positions_from_redis()` helper + `get_config_unrealized_pnl()` — used by 6 reader locations
- Readers updated: `dashboard_data.py`, `ggbot.py` (positions + account endpoints), `engine_v2.py`, `activity_logger.py`, `paper_adapter.py`
- All readers fall back gracefully to Postgres values on Redis miss
- Result: **0 UPDATE/day on paper_trades** (was ~230K/day)

**Part 2: Snapshot Retention** (`core/monitoring/snapshot_retention.py`, `ggbot_scheduler.py`):
- Tiered retention: 0-7d full resolution, 7-30d hourly, 30d+ daily
- Batched DELETEs (10K/batch) to avoid long transactions
- Scheduled daily at 3am UTC via APScheduler
- Initial cleanup: 713K → 406K rows (307K deleted)

**Part 3: Dashboard Query Optimization** (`core/sse/dashboard_data.py`):
- `latest_activities` CTE was scanning ALL 97K activities globally — added `INNER JOIN bot_configs` to filter to user's configs only. **1,525ms → 7ms (203x faster)**
- `account_summaries` CTE rewritten from `DISTINCT ON` (seq scan on 406K rows) to `LATERAL` join — forces `idx_snapshots_latest` index use, one seek per config. **834ms → 13ms (65x faster)**
- New indexes: `idx_activities_equity_latest` (partial, `WHERE total_equity IS NOT NULL`), `idx_decisions_config_created` (`config_id, created_at DESC`)
- Full dashboard query: **253ms → 25ms mean (10x faster)**

---

## 2026-03-04 - Code Quality Fixes + Dead Code Removal

**Dead Code Removal** (`ggbot.py`, -618 lines):
- Removed all Symphony endpoints (setup/status/disconnect, positions, account metrics, trade history) — integration BLOCKED, API returns 404s
- Removed all Aster endpoints (setup/status/disconnect, positions) — integration BLOCKED
- Removed Symphony/Aster branches from agent trade execution, config creation validation, symbol compatibility checks
- Removed `symphony_agent_id` from ConfigCreateRequest/ConfigUpdateRequest models
- `ggbot.py`: 4802 → 4185 lines. Total reduction from original monolith: 6204 → 4185 (-32%)

**Bug Fix** (`ggbot.py`):
- `get_scheduler_status` total active bots query missing `OR config_type IS NULL` — legacy rows invisible in count. Now consistent with reconcile loop and per-user query.

**Import Cleanup** (`ggbot.py:1-98`):
- Organized imports into stdlib/third-party/local blocks, alphabetized. Removed 4 inline `import re`, 3 inline `import traceback`, 1 duplicate `import os`. Updated module docstring.

**Logging** (`ggbot.py`):
- Replaced 3x `import traceback; traceback.print_exc()` with `exc_info=True` on logger.error() — tracebacks now route through Loguru pipeline instead of bypassing to stderr.

**Constants** (`ggbot.py:95-98`):
- `PAPER_INITIAL_BALANCE` (was literal `10000.0` in 10 places), `CREDIT_PURCHASE_MIN_CENTS`/`MAX_CENTS` (was duplicated in 2 endpoints), `API_BASE_URL` (was hardcoded production domain in IPN callback).

**Frontend** (`frontend/app/layout.tsx`):
- Added Virtual Protocol site verification meta tag.

---

## 2026-03-01 - Orchestrator Refactor Phase 2: Scheduler Separation

**Planning Doc**: [DOCS/completed/ORCHESTRATOR_REFACTOR.md](DOCS/completed/ORCHESTRATOR_REFACTOR.md)

**Problem**: Frontend hung 5-10min at every hourly candle close. Single `ggbot.py` process ran both API server and APScheduler — 13+ bots firing simultaneously starved event loop, blocking all HTTP requests.

**Architecture Change** — split monolith into two PM2 processes:
- `ggbot` (API-only): HTTP/SSE, "Run Now", fast always
- `ggbot-scheduler` (scheduler-only): APScheduler, bot execution, Stripe meter cron
- Database is sole communication channel — no Redis pub/sub, no new infrastructure

**New Files**:
- `core/orchestrator/orchestrator.py` — GGBotOrchestrator class + OrchestrationResult extracted from ggbot.py (~1000 lines moved)
- `core/scheduler/bot_runner.py` — `run_once()`, `add_bot_job()`, `remove_bot_job()` + new `reconcile_loop()` (polls DB every 10s, diffs with scheduler jobs)
- `core/scheduler/utils.py` — added `calculate_next_run()` (computes next fire time without scheduler instance) + `extract_timeframe_from_config()` (moved from ggbot.py)
- `ggbot_scheduler.py` — thin entry point, creates scheduler + orchestrator, enters reconcile loop

**Modified Files**:
- `ggbot.py` — removed ~1400 lines (orchestrator class, scheduler code). Start/stop/update/delete endpoints write DB state only. `get_scheduler_status` queries DB instead of APScheduler. 6204→4802 lines
- `core/sse/dashboard_data.py` — replaced `from ggbot import get_next_run_from_scheduler, has_scheduler_job` with `calculate_next_run()` from utils
- `ecosystem.config.js` — added `ggbot-scheduler` PM2 entry (1G max memory, same env vars)

**How start/stop works now**: User presses Start → API sets `state='active'` → returns immediately with calculated `next_run` → scheduler detects new active bot within 10s → adds APScheduler job. Stop is reverse. Handles all edge cases: timeframe change, delete, crash recovery.

---

## 2026-03-01 - Virtuals 60 Days Application Draft + NOWPayments Integration Guide

**Virtuals 60 Days** (`NOTE.md`):
- Platform token application for Virtuals 60 Days framework — Core Idea, What It Does, How It Works, Why, Roadmap, Token Utility, Tokenomics sections
- Cross-referenced with `ggbots-voice-guide.md` for tone/brand alignment
- Season 1 data (The Arbiter +45% autonomous, 44 bots, 21 days) integrated as proof point
- Trade37 Championship in Future Vision (AI vs Human in-person competition)

**NOWPayments Guide** (`DOCS/NOWPAYMENTS_INTEGRATION_GUIDE.md`):
- Standalone integration guide extracted from production `ggbot.py` implementation
- Covers: invoice creation, HMAC-SHA512 webhook verification (sorted compact JSON gotcha), idempotency via Redis, order_id encoding pattern, payment status reference

---

## 2026-02-26 - Cumulative Bot Cost Tracking + Activity Cost Display + Cost Estimation

**Per-Bot Lifetime Cost** (`decision/engine_v2.py`, `api/usage.py`, `ActivationBar.tsx`):
- New Redis key `usage:config:total:{config_id}` — incremented on every LLM call, no TTL
- `/api/v2/usage/config/{id}` returns `total_usage_usd` (all-time bot cost)
- ActivationBar shows "$X.XX total" next to daily cost
- Backfill script (`scripts/backfill_prepaid_cumulative.py`) now includes per-config cumulative keys — 92 configs, $584.88 total

**Activity Cost Display** (`api/activities.py`, `activity-modal.tsx`):
- Activities API returns `platform_cost_usd` per activity (column added to SELECT)
- Activity modal `LLMThoughtContent` shows "Cost: $0.XXXX" on LLM thought activities

**Cost Estimation for New Bots** (`frontend/lib/cost-estimation.ts`, `ActivationBar.tsx`, `UpgradeModal.tsx`):
- Extracted `MODEL_TIER_COSTS` + `FREQUENCY_TO_DECISIONS` to shared `lib/cost-estimation.ts`
- ActivationBar daily cost slot: shows "~$X.XX/day est." for new bots (no usage data), switches to actual avg once bot has run
- UpgradeModal imports from shared util (was duplicated)

---

## 2026-02-26 - Hyperliquid Trade Close Fixes + Account Stats + Live Strategy Tuning

**Trade Close Activity Logging** (`trading/live/hyperliquid_service.py`):
- `close_position()` now snapshots position via Info API BEFORE `market_close()` — captures entry_price, side, size, leverage, unrealized_pnl
- Extracts exit price from `market_close()` fill data (`statuses[].filled.avgPx`)
- Computes realized P&L from actual prices, duration from `live_trades.created_at`
- Activity details now match paper trading format: entry_price, exit_price, pnl, pnl_pct, side, size_usd, leverage, duration_seconds
- Telegram exit notifications enriched with real P&L and side (was hardcoded `pnl: 0`, `side: 'unknown'`)

**Adapter Close Detection** (`core/monitoring/adapters/hyperliquid_adapter.py`):
- Auto-close activities now include derived entry_price (`entry = exit ± pnl/size`), pnl_pct, size_usd, duration
- `bot_symbols` query: removed `closed_at IS NULL` filter — closed trade symbols now match fills for realized P&L
- Fill aggregation: groups by timestamp to count trades, not individual partial fills (8 fills from 1 `market_close` = 1 trade)

**Account Endpoint** (`ggbot.py`):
- `/bot/{config_id}/account` for Hyperliquid: replaced hardcoded zeros with `account_snapshots` data (total_trades, win_trades, win_rate, realized_pnl)
- Added `initial_equity` lookup + `performance_percent` calculation (was 0.0)

**Live Strategy Tuning** (config_data update, `b9d9bf00`):
- Softened regime anchor: removed "Do NOT exit for 4H pullback within intact 1D regime"; added "3+ domains reversed = exit, regime gets voice not veto"
- Lowered counter-trend bar: "exceptional evidence" → "strong confluence (3+ domains)"; penalty -0.12/-0.08 → -0.08/-0.05
- Added profit protection: when meaningfully profitable, burden of proof flips — need reasons to stay, not reasons to leave

---

## 2026-02-17 - Hyperliquid Phase 5: Single Live Bot Slot + Strategy Versioning + Equity Tracking

**Planning Doc**: [DOCS/completed/SINGLE_LIVE_BOT_SLOT.md](DOCS/completed/SINGLE_LIVE_BOT_SLOT.md)

**Single Live Bot Slot** (`ggbot.py`, `BotRail.tsx`, `BotCreationModal.tsx`, `ConfigureLayout.tsx`):
- Replaced multi-live-bot model with one permanent live config per user, auto-created during HL setup
- `POST /api/v2/bot/{config_id}/promote-to-live` — copies paper bot strategy to live slot with version tracking
- Paper-only bot creation (blocked `trading_mode='hyperliquid'` in `create_config`)
- Removed allocation validation + unique symbol enforcement from `start_bot`
- BotRail: pinned live slot with 4 states (not connected / no strategy / promoted / disconnected)
- Disconnect preserves live slot (`state='inactive'`, not converted to paper)

**Equity Tracking** (`hyperliquid_adapter.py`, `account_snapshot.py`, `dashboard_data.py`, `page.tsx`):
- Adapter returns `current_balance=account_value` (was `None` in multi-bot model)
- `total_equity = current_balance + unrealized_pnl` for Hyperliquid (same formula as paper)
- ActivationBar/PerformanceChart show real equity, not cumulative P&L
- SSE dashboard enrichment merges HL API data with DB snapshots

**Strategy Versioning** (`ggbot.py`, `activity_logger.py`, `tv-timeline.tsx`, `ActivationBar.tsx`):
- `strategy_updated` activity logged on promote-to-live (with version number + config snapshot)
- `strategy_updated` activity logged on config edits via batched save (changed fields tracked)
- `bot_created` activity logged during HL setup auto-creation
- TV timeline: square marker for strategy updates, gear icon in activity modal
- `initial_equity` fallback in `get_latest_snapshot()` for new bots without snapshots

**Bug Fixes** (discovered during live testing):
- `config_service.py`: `data["selected_pair"]` → `data.get("selected_pair", "")` — empty live bot config crashed `from_dict`
- `ggbot.py:start_bot`: missing `from core.common.db import get_db_connection` import
- `ActivationBar.tsx`: guard `temp-` IDs from API calls during duplication
- `BotManagementMenu.tsx`: standardized promote confirmation as inline popover (was browser `confirm()`)
- `account-monitor` PM2 process: 6-day stale code caused NULL `current_balance` in snapshots

**15 files changed across 3 workstreams** — backend, frontend, monitoring.

---

## 2026-02-13 - Vercel Build Fix (CVE-2026-0969) + Frontend Cleanup + Arena Filter

**Vercel Deployment Blocker** (`frontend/package.json`):
- `next-mdx-remote` 5.0.0 → 6.0.0 — fixes CVE-2026-0969 (XSS via JS in MDX). v6 adds `blockJS`/`blockDangerousJS` defaults; transparent for pure-markdown blog.
- `next` 15.5.7 → 15.5.11, `eslint-config-next` aligned — fixes `@next/swc` version mismatch warning
- Browserslist DB updated (1.0.30001721 → 1.0.30001769)
- `npm audit fix` — 2 high severity → 0 vulnerabilities

**React Hook Warnings** (`components/BotImageUpload.tsx`, `components/UpgradeModal.tsx`):
- `BotImageUpload`: `resizeImage` moved to module scope (pure utility), `handleUpload` wrapped in `useCallback`, `handleDrop` deps fixed
- `UpgradeModal`: `FREQUENCY_LABELS` moved to module scope (static lookup table, was recreating identity each render)

**Arena Leaderboard** (`components/arena/ArenaWithStaking.tsx`):
- Filter `total_trades > 0` on `rankedBots` — excludes bots that never traded (stuck at $10k). Cascades to podium, autonomous leaderboard, overall leaderboard, hero/footer count text.

---

## 2026-02-11 - Hyperliquid Phase 4 + 4.5: Polish, Error Handling, Position Tracking Fixes

**Planning Doc**: [DOCS/todo/HYPERLIQUID_INTEGRATION.md](DOCS/todo/HYPERLIQUID_INTEGRATION.md)

**Error Handling** (`trading/live/hyperliquid_service.py`):
- Error classifier: `_classify_error()` categorizes insufficient_balance, rate_limit, credentials_expired
- Retry logic: 2 retries with exponential backoff (1s → 2s) for rate limits + network errors
- Fill error extraction: checks `statuses[]` for errors (top-level "ok" ≠ filled)
- Zero-balance detection: `_calculate_position_size()` returns 0.0, caller rejects with clear message

**Telegram Publishing** (`signals/publishing_service.py`, `ggbot.py`):
- Exit notifications added to `close_position()` — same pattern as Symphony
- `live_tag` field threads through orchestrator → publishing service for "Live on Hyperliquid" badge
- Entry messages already worked (mode-agnostic), just needed `live_tag` enrichment

**Position Tracking Fixes** (`hyperliquid_service.py`, `dashboard_data.py`):
- `_close_stale_trades()` — closes old `live_trades` before new insert (position flip handling)
- Dashboard enrichment: `current_price` from LivePriceService (was None), `opened_at` from `live_trades.created_at` (was None)
- `trade_id=batch_id` in `log_activity_safe()` — activity timeline can now link entries to trades
- SL/TP trigger order logging: detailed params + response statuses for debugging

**DB Constraints**:
- `valid_trading_mode` on `configurations`: added 'hyperliquid'
- `account_snapshots_trading_mode_check`: added 'hyperliquid'

**Documentation** (`trading/README.md`, `ACTIVE.md`):
- Full Hyperliquid section in trading/README.md (architecture, trust model, error table, endpoints)
- ACTIVE.md: Hyperliquid in trading modes, bot stats, capabilities, API endpoints, user_profiles schema

---

## 2026-02-09 - Hyperliquid Phase 3: Dashboard Monitoring + Account Adapter

**Planning Doc**: [DOCS/todo/HYPERLIQUID_INTEGRATION.md](DOCS/todo/HYPERLIQUID_INTEGRATION.md)

**Summary**: Hyperliquid positions and P&L now flow through dashboard SSE. Per-bot P&L tracking via symbol attribution (shared wallet, per-bot cumulative P&L). Same pattern as Symphony — chart shows "Cumulative P&L" from $0.

**New: HyperliquidAccountAdapter** (`core/monitoring/adapters/hyperliquid_adapter.py`):
- Queries `Info.user_state()` (118ms) for account balance, margin, positions
- Cross-references `live_trades` to attribute positions to specific bots by symbol
- Computes per-bot realized P&L from `user_fills_by_time()` (77ms)
- Detects closed positions via fill history, logs `trade_exit` activities
- Caches wallet address per user_id to avoid repeated Vault lookups

**Backend** (`ggbot.py`, `dashboard_data.py`, `account_snapshot.py`, `universal_account_monitor.py`):
- `POST /api/v2/positions/hyperliquid/{batch_id}/close` — close with ownership verification
- `/bot/{config_id}/account` + `/positions` handle `trading_mode='hyperliquid'`
- SSE CTE: added `UNION ALL` for Hyperliquid `live_trades` in `open_positions`
- `_enrich_live_positions_and_accounts()` fetches real positions from Info API, groups by user_id
- `total_equity` property: returns `total_pnl` for all live modes (per-bot cumulative P&L)
- `UniversalAccountMonitor`: 4 adapters (paper/symphony/aster/hyperliquid)

**Frontend** (`PerformanceChart.tsx`, `PositionsTable.tsx`):
- `source: 'hyperliquid'` triggers cumulative P&L mode (start at $0, title: "Cumulative P&L")
- Position close routing via `/api/v2/positions/hyperliquid/{batch_id}/close`

**Info API Exploration** (`scripts/tests/test_hyperliquid_info_api.py`):
- 12 endpoints tested: user_state, open_orders, frontend_open_orders, user_fills, user_fills_by_time, all_mids, candles_snapshot, meta_and_asset_ctxs, portfolio, user_fees, user_funding_history, user_non_funding_ledger_updates, extra_agents, user_rate_limit
- Latency: 73-258ms range. 228 perp markets, 512 mids (includes spot), 10,435 req/min cap

**CLAUDE.md**: Added `npx tsc --noEmit` as type-check command; documented OOM risk with `npm run build` (Web3 deps)

---

## 2026-02-09 - Hyperliquid Phase 2: Forge Integration (Live Trading)

**Planning Doc**: [DOCS/todo/HYPERLIQUID_INTEGRATION.md](DOCS/todo/HYPERLIQUID_INTEGRATION.md)

**Summary**: Replaced Symphony/Aster with "Live Trading" (powered by Hyperliquid) across Forge. Users can create live bots, manage funds, and activate with credential + unique-symbol enforcement.

**Backend** (`ggbot.py`):
- `/api/v2/user/profile` returns `hyperliquid_connected` (DB check for non-null wallet address)
- `start_bot` endpoint: Hyperliquid credential check + unique symbol enforcement per active bot (prevents position netting conflicts)

**New Components**:
- `LiveTradingSetupModal.tsx` — modal wrapper with `next/dynamic` SSR-disabled import
- `LiveTradingModalContent.tsx` — full Web3 flow (connect wallet, deposit, authorize, manage funds, test trade, disconnect) extracted from `HyperliquidSetup.tsx`

**Modified Frontend** (10 files):
- `SettingsModal.tsx` — replaced ~300 lines Symphony/Aster with "Live Trading" section (connected status + manage funds, or setup CTA)
- `BotCreationModal.tsx` — 2 trading modes (Paper + Live Trading); opens setup modal for unconfigured users; removed `symphonyAgentId`
- `page.tsx` — updated `TradingMode` to `'paper' | 'hyperliquid'`, removed symphony references
- `TradeSettings.tsx` — allocation indicator bar showing margin distribution across live bots
- `ActivationBar.tsx` — added `'hyperliquid'` to `isLiveTrading` check
- `UserProfile.tsx` — live trading balance display in dropdown
- `permissions.tsx` — added `refreshProfile()` to context for real-time state updates after connect/disconnect
- `RiskAcknowledgmentModal.tsx` — accepts `'hyperliquid'` trading mode
- `api.ts` — `hyperliquid_connected` on `UserProfile`, `'hyperliquid'` on `BotConfiguration.trading_mode`
- `ConfigureLayout.tsx` — passes `allBots` through to TradeSettings for allocation calculation

---

## 2026-02-03 - SSE Dashboard Query Optimization (Denormalize initial_equity)

**Purpose**: Eliminate expensive `DISTINCT ON` scan of activities table in dashboard SSE query.

**Problem**: Dashboard query ran every 5s per user, included `first_activities` CTE that scanned entire activities table to find first `total_equity` per bot. Accounted for ~80% of DB time.

**Solution**: Denormalize `initial_equity` onto `configurations` table.

**Database** (`configurations` table):
- Added `initial_equity NUMERIC` column
- Backfilled 478 existing bots using reset-aware query (respects `last_reset_at`)
- Arena bots correctly use $10,000 post-reset baseline

**Code Changes**:
- `core/sse/dashboard_data.py` - Removed `first_activities` CTE, now uses `bc.initial_equity`
- `trading/paper/supabase_service.py:731-755` - `reset_account()` sets `initial_equity = 10000`
- `core/services/config_service.py:253-264` - New bots created with `initial_equity = 10000`
- `core/config/repository.py:129-132` - New bots created with `initial_equity = 10000`
- `core/common/db.py:187-191` - New bots created with `initial_equity = 10000`
- `core/config/insert_config.py`, `import_user_config.py` - Same

**Note**: Arena leaderboard (`api/public.py`) unaffected - uses separate query with `COMPETITION_START` filter and `paper_accounts.initial_balance`.

**Additional Indexes**:
- `idx_configurations_is_public_performance` - btree on `is_public_performance` (16 KB) - Arena filter
- `idx_activities_platform_cost` - btree on `platform_cost_usd` - Billing query optimization (21% faster)

**Arena Query Optimization** (`api/public.py`):
- Problem: Arena query took 9.7s due to JSONB extraction (`config_data->...`) for 81k rows
- Root cause: JSONB fields extracted inside DISTINCT ON, so 81k extractions instead of 30
- Fix: Split into two queries - (1) bot metadata with JSONB (30 rows), (2) hourly snapshots without JSONB (7k rows)
- Also: Downsample to hourly using `DISTINCT ON`, increased cache TTL 60s → 300s
- Result: **9.7s → 0.46s (21x faster)** 🚀

---

## 2026-02-02 - Billing Fixes + Memory Leak Fix + DB Indexes

**Purpose**: Fix prepaid credit tracking bug, failed payment handling, memory leak, and slow queries.

**Database Indexes** (Arena query optimization):
- Added `idx_configurations_state` - btree on `state` column (16 KB)
- Added `idx_snapshots_timestamp` - btree on `timestamp` column (3.6 MB)
- Arena leaderboard query was 8.4s average, should improve significantly

**Prepaid Balance Bug** (`core/monitoring/usage_monitor.py`, `api/admin.py`):
- Bug: Prepaid users showed incorrect balance because Stripe Credit Grants only decrease when applied to invoices (prepaid users never get invoices)
- Fix: `get_balance_status()` now uses all-time `SUM(platform_cost_usd) FROM activities` for prepaid tier instead of monthly Redis counter
- Admin page (`api/admin.py:717-739`) also fixed - calculates `available = total_purchased - total_usage_cost` for prepaid users
- `cache_usage_summaries()` also fixed - UserProfile dropdown now shows correct balance for prepaid users
- Added `_get_total_purchased_from_stripe()` helper to sum all Credit Grant amounts

**$10 Spending Cap** (`ggbot.py`, `scripts/add_billing_thresholds.py`):
- Added `billing_thresholds.amount_gte = 1000` to all usage_based subscriptions
- Stripe auto-generates invoice when usage hits $10, limiting bad debt exposure
- Script updated 7 existing subscriptions

**Payment Failure Handling** (`ggbot.py:4757-4860`):
- Enhanced `handle_payment_failed()` webhook handler
- Now pauses ALL user's bots on payment failure (not just subscription)
- Sends email notification via Resend
- Publishes to Redis for real-time UI updates

**Memory Leak Fix** (`ggbot.py:314-334`, `:833-854`, `:1006-1022`):
- Bug: `_extraction_engines` and `_decision_engines` dicts grew unbounded (300MB → 1GB over hours)
- Fix: LRU eviction using `OrderedDict` with `MAX_EXTRACTION_ENGINES=30`, `MAX_DECISION_ENGINES=50`
- Oldest engines evicted with proper cleanup (`ExtractionEngineV2.cleanup()` disconnects data client)

---

## 2026-01-30 - SEO Infrastructure + Blog Launch + Keyword Research
Sitemap, robots.txt, OG images (Playwright), Twitter cards, PWA icons, JSON-LD schema. Blog infra with MDX, RSS feed, first article "What is Vibe Trading?". 4-tier keyword strategy, Q1 content calendar. See `frontend/SEO.md`.

---

## 2026-01-30 - Performance: Remove UX Delays + Refactor Planning
Removed 6 `asyncio.sleep()` calls (13s/cycle saved). New `DOCS/todo/ORCHESTRATOR_REFACTOR.md` — root cause: psycopg2 sync blocking, not architecture. 4-phase plan replaces over-engineered 7-phase.

---

## 2026-01-30 - Infrastructure: Supabase Pooler + Mobile Touch Fix
Supabase disk IO exhausted → upgraded compute, switched to Pooler (`pooler.supabase.com`). 46ms connect, 7ms queries. Mobile touch fix: `mousedown`→`pointerdown` for 3-dot menu.

---

## 2026-01-30 - Landing Page Quick Wins + Webapp Testing Skill
SocialProof component (live stats), CTAs after Process/Features sections, shadow removal, Telegram FAQ link, header Sign Up. Playwright webapp-testing skill installed.

---

## 2026-01-30 - Enriched Preprocessor Summaries
All 21 preprocessors updated with conditional signals (divergence, crossovers, squeeze, acceleration). Token-neutral — signals only appear when detected. `⚠️` warnings, `✓` confirmations.

---

## 2026-01-29 - Rei Compact Format + Behavior Prompt
Payload ~22KB→~7KB via `to_compact()` on all 21 preprocessors + timeframe filtering. Universal compact schema ~400 bytes/indicator. Strategy file `trading/strategies/rei_core.md`.

---

## 2026-01-28 - Rei Scheduled Bot Engine (Experimental)
`decision/rei_engine.py` — alternative to LLM decisions. `rei_enabled` config flag routes to Rei API. Feedback loop reports trade outcomes for inference-time learning. Test bot: "The Nightingale".

---

## 2026-01-28 - Kimi K2.5 Model Update + LLM Update Workflow
Kimi standard/premium→k2.5. New `decision/llm_providers/MODEL_UPDATE.md` — systematic update checklist for 21 model×tier combinations.

---

## 2026-01-27 - Forge React Query + Arena Podium Fixes
`useDataSources()` (10min), `useBotList()`, `useLatestActivity()` (30s). Removed ~60 lines manual fetch boilerplate. Arena podium: `isFetching` spinner, inline legend, taller chart.

---

## 2026-01-27 - Frontend Performance & Arena Redesign
React Query at root (30s stale, 5min gc). Redis arena cache 60s. SVG sparklines, lightweight-charts podium. Bundle 212KB→168KB (44KB reduction). See [DOCS/completed/FRONTEND_PERFORMANCE_REACT_QUERY.md].

---

## 2026-01-27 - USX Arena Betting (Full Stack)
wagmi/viem/RainbowKit v2 on Scroll. BetModal: 6-step flow (approve→deposit→record). Public pledge endpoint (wallet=identity). sUSX preview, cooldown warning. See [DOCS/todo/USX_STAKING_MODAL.md].

---

## 2026-01-23 - Market Data Intelligence Update
ggShot soft-disabled (90+ days stale). Astrology indicators: `lunar_phase`, `mercury_status` under sentiment_social via Grok (~$0.005/query). See [DOCS/completed/MARKET_DATA_INTELLIGENCE_UPDATE.md].

---

## 2026-01-23 - Onboarding Tour & Strategy Advisor UX
5-step tutorial overlay post-first-bot. "Explain Strategy" + "Update Strategy" + "Analyze Performance" buttons. Border highlight, pointer-events pass-through, localStorage persistence.

---

## 2026-01-22 - Rei Integration Hardening
Opus 4.5→Haiku (follows instructions better). System prompt hardening: forbidden phrases, EXIT=immediate, ENTER≥50%. Confidence-based sizing (70% confidence = 70% max size). Timeout 60s→180s.

---

## 2026-01-22 - Telegram Publishing (Platform Bot)
PM2 `telegram-bot` service with /start, /chatid, /help commands. Entry + exit notifications with P&L display. Publishing service checks all paid tiers. See [DOCS/completed/TELEGRAM_PUBLISHING.md].

---

## 2026-01-21 - ggArena Season 1 Launch
`arena_reset.py` → 14 bots reset. `arena_registered_at` column. Competition start filter. Late registration with auto-reset. See [DOCS/completed/GGARENA_SEASON1_LAUNCH.md].

---

## 2026-01-21 - Unified Modal System
Unified `Modal` component (Framer Motion, responsive sizing, full-screen mobile, focus trap). Migrated 6 modals from 3 different systems. See [DOCS/completed/UNIFIED_MODAL_SYSTEM.md].

---

## 2026-01-21 - Prepaid Tier Implementation
Separate `prepaid` enum (was confusingly `usage_based`). Pre-LLM credit check (fail-closed). Meter reporter excludes prepaid. Usage monitor: hard block on depletion. See [DOCS/completed/PREPAID_TIER.md].

---

## 2026-01-20 - Onboarding Revamp & Free Test Runs
5-step typeform bot creation. 3 archetypes (Contrarian/Compass/Arbiter). Strategy generation via Haiku. Free test runs: `first_run_used` + `free_runs_remaining=3`. All models/frequencies unlocked for everyone. See [DOCS/completed/ONBOARDING_REVAMP.md].

---

## 2026-01-16 - Rei Agent Integration
Claude+Rei hybrid: Claude orchestrates, Rei reasons+learns. 3 MCP tools (query/consult/report). Session buffer for ~15-20KB market data. See [DOCS/completed/REI_AGENT_INTEGRATION.md].

---

## 2026-01-16 - Frontend Usage Display
`getUsageSummary()`, `getConfigUsage()` API methods. UserProfile: credit/metered adaptive display. ActivationBar: per-bot daily cost estimate with 5min refresh.

---

## 2026-01-15 - Real-Time Usage Tracking & Billing Hardening
Redis INCRBYFLOAT counters on every LLM call. UsageMonitor in account-monitor (60s checks, auto-pause on depletion). 4 usage API endpoints. Idempotency fixes for Stripe + NOWPayments. See [DOCS/completed/USAGE_BILLING_TRACKING.md].

---

## 2026-01-13 - Frontend Snappiness Phase 1
Optimistic updates for delete/duplicate/rename/reset (0ms perceived). Skeleton loading states. Bot switching skeleton (prevents stale flash).

---

## 2026-01-13 - Market Intelligence Cost Optimization
Fixed Grok cache key bug (all queries shared one key). Extended TTLs (VIX 15min→4hr, etc). $50/week→$7-10/week (80-86% reduction). Arena reset script.

---

## 2026-01-13 - Bot Analysis Framework + Platform Defaults
`core/services/performance_analyzer.py` — pattern correlation, confidence calibration, Haiku synthesis. Default SL/TP: 5%/10%→1.5%/3% (old defaults never triggered). LLM tier display names.

---

## 2026-01-13 - Strategy Advisor Fixes
f-string bug: unescaped `{...}` in prompt → Ellipsis format specifier error. Auto-scroll via `useRef` + `requestAnimationFrame`.

---

## 2026-01-08 - Credit Packs & Crypto Payments
Stripe credit packs ($10-$100) + NOWPayments crypto. Credit Grants auto-apply to invoices. HMAC-SHA512 IPN verification. See [DOCS/completed/CREDIT_PACKS.md].

---

## 2026-01-07 - ggArena Season 1 Launch Prep
Arena UX overhaul: isolated countdown timer, restructured bot details, varied CTAs, $2,500 prize breakdown. Registration endpoints + modal. nginx 502 fix (300s timeout, buffering off). APScheduler jitter 15s→30s.

---

## 2026-01-06 - Reasoning Tier Fix + Billing Accuracy
`reasoning_tier` field missing from Pydantic model → all bots ran standard tier. Billing switched to actual OpenRouter `usage.cost` (was static table). Netflix-style upgrade modal with real cost estimates.

---

## 2026-01-04 - Strategy Advisor Performance Analysis
`performance_analyzer.py` — universal pattern extraction, confidence calibration, exit classification. `/api/v2/assistant/analyze/{config_id}`. "Discuss with Advisor" sends report to chat.

---

## 2026-01-04 - Activity Modal Redesign
Centered modal with carousel navigation (swipe/arrows). Type-specific formatters. Structured REASONING format (KEY_SIGNAL/SUPPORTING/RISK/SUMMARY) in decision prompts.

---

## 2025-12-28 - Symphony Position Display Fix
SSE enrichment function existed but never called. Fixed source filter, added collateral/PnL/liquidation fields.

---

## 2025-12-27 - Error Log Fixes + Arena Timeline + TradeSettings Fix
binance_funding gateway pattern, WebSocket queue 100→1000, timeframe-aware Redis TTL. Arena 3 public endpoints. TradeSettings nested object data loss fix.

---

## 2025-12-19 - ggArena Bot Strategy Tuning
7 arena bots prepared. Action bias 0.55+ (was 0.75+). Regime gating: block longs against bearish 1H.

---

## 2025-12-17/18 - Bot Images + Arena Page + TV Timeline
Image upload, public leaderboard /arena, dual-mode timeline (Activity/Performance). Bot limit removed.

---

## 2025-12-15 - Account Metrics Standardization
`metrics_calculator.py` — single source of truth. 6 duplicate formula implementations → 1. `total_equity` column on activities.

---

## 2025-12-14 - Admin Dashboard Equity Fix + Bot Comparison
Removed margin_used double-counting. Bot equity comparison chart endpoint.

---

## 2025-12-10 - Position Sizing Simplification (BREAKING)
Confidence-based only. Deleted PositionSizingMethod enum. max_position_percent→max_margin_percent. Defaults: 5x leverage, 20% margin, 1.5% SL, 3% TP.

---

## 2025-12-05 - Admin Dashboard + Signal Filtering + Strategy Advisor
/admin with 13 endpoints. Symphony 100-symbol filter. Strategy character creation UX. Reasoning tiers (economy/standard/premium).

---

## 2025-12-04 - Unified Config Saving
Batched save: 40+ API calls → 1, 5s debounce. Symphony win_rate overflow fix.

---

## 2025-11-30 and earlier — Compressed Archive

**Nov 2025**: Activity timeline data visibility, balance tracking fixes, legal pages + AsterDEX integration (33 symbols), strategy advisor auto-save, universal AI assistant + metered billing (Stripe Meters), snapshot timeline + activities overhaul + universal account monitoring, metered billing infra, confidence sizing + OpenRouter UI, config system cleanup v2.2, agent session resumption, TradingView timeline + agent v4, ceremonial brutalism rebrand (obsidian/ivory/brass), agent Phase 4c autonomous trading, AsterDEX Phase 1, agent Phase 3 + maintenance mode, activity timeline viewer.

**Oct 2025**: Market intelligence LIVE (8 Grok sources, $195/mo→$7-10/wk after optimization), intelligence orchestrator, ggShot universal data (878 signals), hybrid price service (WebSocket+REST), Symphony integration + universal data layer, Resend email (189 users), trading fixes (position sizing, P&L double leverage), GPT-5 Responses API, Stripe monetization ($29/mo Pro).

**Pre-Oct 2025**: APScheduler zero-drift, signal validation, paper trading engine, frontend SSE, disk crisis (26GB Docker logs), multi-exchange failover.

---

**Documentation**: See README.md (architecture), ACTIVE.md (production status), TODO.md (roadmap)
