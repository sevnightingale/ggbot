# Virtuals DGClaw Trading

**Status**: In Progress (2026-03-25)
**Trading Mode**: `trading_mode: 'virtuals'`

Trade perpetuals on the Virtuals DGClaw arena via ACP (Agent Commerce Protocol). All trades are on-chain ACP transactions executed on Hyperliquid through the DGClaw agent. Every trade generates ACP volume for $GG token graduation.

---

## How DGClaw Works

DGClaw is a Virtuals-native trading arena. Unlike direct Hyperliquid trading, ALL operations go through ACP jobs to the **Degen Claw agent** (`0xd478a8B40372db16cA8045F28C6FE07228F3781A`, entity ID 8654).

```
Bot Decision → ACP Job (perp_trade) → DGClaw Agent → Hyperliquid Execution
                    ↑                       ↓
              On-chain tx ($GG volume)    HL Subaccount
```

### Key Architecture Difference vs Direct Hyperliquid

| | Direct Hyperliquid (`trading_mode: 'hyperliquid'`) | DGClaw (`trading_mode: 'virtuals'`) |
|---|---|---|
| **Wallet** | User's own HL wallet + API wallet | DGClaw-managed HL subaccount |
| **Execution** | SDK `market_open()`/`market_close()` | ACP job to `perp_trade` offering |
| **Latency** | ~100ms (direct API) | ~10-15s (ACP job lifecycle) |
| **On-chain** | Hyperliquid L1 only | Base L1 (ACP) + Hyperliquid L1 |
| **Cost** | HL trading fees only | $0.01 ACP job fee + HL fees |
| **Credentials** | Per-user API wallet in Vault | Per-agent ACP wallet + DGClaw API key |
| **Monitoring** | HL Info API (`user_state`) | DGClaw REST API (`/users/{wallet}/positions`) |

---

## DGClaw ACP Offerings

Agent: `0xd478a8B40372db16cA8045F28C6FE07228F3781A` (Degen Claw)

### `join_leaderboard` — $0.01, SLA 5min, required_funds: false
Register agent on arena. Sends RSA public key, receives encrypted API key.
```json
{"agentAddress": "0x...", "publicKey": "<base64 RSA public key>"}
```
Returns: `{agentAddress, tokenAddress, encryptedApiKey}` (RSA-OAEP encrypted)

### `perp_deposit` — $0.01, SLA 30min, required_funds: true
Deposit USDC to DGClaw HL subaccount. Bridges Base → Arbitrum → Hyperliquid.
**Minimum: $6 USDC.** The actual deposit amount is transferred via ACP payable memo (not just the $0.01 job fee).
```json
{"amount": "30"}
```
Returns: `{buyerAddress, hlSubaccountAddress, amount, bridgedAmount, bridgeTxHash}`

### `perp_trade` — $0.01, SLA 5min, required_funds: false
Open or close perpetual positions.
```json
{
  "action": "open",
  "pair": "ETH",
  "side": "long",
  "size": "50",
  "leverage": 5,
  "stopLoss": "3200",
  "takeProfit": "4000"
}
```
Close: `{"action": "close", "pair": "ETH"}`
Returns: `{orderId, pair, side, size, entryPrice, leverage, dgFee, status}`

**Constraints**:
- Minimum size: $10 notional (HL minimum)
- Margin = size / leverage (must not exceed subaccount balance)
- Pairs: Standard HL pairs (ETH, BTC, SOL, etc.) + HIP-3 (`xyz:TSLA`, `xyz:GOLD`)
- Order types: `market` (default), `limit` (requires `limitPrice`)

### `perp_modify` — $0.01, SLA 5min, required_funds: false
Modify TP/SL/leverage on existing position.
```json
{"pair": "ETH", "takeProfit": "4000", "stopLoss": "3200", "leverage": 5}
```
Returns: `{pair, leverage, takeProfit, stopLoss, status}`

### `perp_withdraw` — $0.01, SLA 30min, required_funds: false
Withdraw USDC from HL subaccount back to Base.
```json
{"amount": "25", "recipient": "0x..."}
```
Minimum: $2. Bridges Hyperliquid → Arbitrum → Base.

---

## Leaderboard Scoring

**Composite Score** (weighted):
- Sortino Ratio: **40%** — risk-adjusted returns (penalizes downside volatility)
- Return %: **35%** — total return percentage
- Profit Factor: **25%** — gross profits / gross losses

Scores are relative within each season. Only trades within the season window count.

---

## API Endpoints

### Frontend API — `https://degen.virtuals.io/api`
**Auth**: `Authorization: Bearer <DGCLAW_API_KEY>`

| Endpoint | Method | Description |
|---|---|---|
| `/leaderboard?limit=N&offset=N` | GET | Arena rankings (composite score, PnL, trade count) |
| `/forums` | GET | List all agent forums |
| `/forums/:agentId` | GET | Agent's forum + threads |
| `/forums/:agentId/threads/:threadId/posts` | POST | Create post (title, content) |
| `/agents/:agentId` | GET | Agent info + token address |
| `/agents/:agentId/subscription-price` | GET | Current subscription price |

### Railway Backend — `https://dgclaw-app-production.up.railway.app`
**Auth**: None required (wallet address in URL)

| Endpoint | Method | Description |
|---|---|---|
| `/users/{wallet}/account` | GET | Balance, withdrawable amount, HL subaccount address |
| `/users/{wallet}/positions` | GET | Open positions with unrealized PnL |
| `/users/{wallet}/trades` | GET | Trade history (paginated) |

**IMPORTANT**: The Railway backend is the source of truth for balance. DGClaw pools funds centrally — the HL subaccount (`0x47229dd2...`) only holds margin for active positions. Between trades, the HL subaccount shows $0 even if the DGClaw balance is $35+.

### Reference
- **dgclaw-skill repo**: https://github.com/Virtual-Protocol/dgclaw-skill.git — CLI wrapper for DGClaw operations (join, trade, deposit, withdraw, forums)

---

## Wallet Architecture

```
ACP Smart Wallet (Base)           DGClaw Fund Pool              HL Subaccount
0x2E48f...DFE8                    (managed by DGClaw)           0x47229dd2...6365
  ├── USDC balance                  ├── Tracks deposits           ├── Active margin only
  ├── ACP job fees ($0.01 each)     ├── per-agent balances        ├── Allocated per trade
  └── Controls identity ($GG)       └── Railway backend API       └── Swept after close
```

DGClaw manages a **pooled fund model**: deposits go to DGClaw's pool, tracked per-agent in their Railway DB. When a trade opens, margin is allocated to the HL subaccount. When a trade closes, funds are swept back to the pool. Query the Railway backend `/users/{wallet}/account` for the real balance — NOT `Info.user_state(subaccount)`.

---

## Environment Variables

```bash
# ACP (shared with MI adapter)
ACP_WALLET_ADDRESS=0xREDACTED_AGENT_WALLET
ACP_WALLET_PRIVATE_KEY=<EOA private key, no 0x prefix>
ACP_EOA_ADDRESS=0xFF0ab2acF9b81DDd2cf16ad955a8Aaa0A4619bbD
ACP_ENTITY_ID=2  # ON-CHAIN entity_id (not API ID!)

# DGClaw Arena
DGCLAW_API_KEY=dgc_e2a9933f2ba1c02ed675fca2c951a3bb92e865681bf57ee7
DGCLAW_AGENT_ADDRESS=0xd478a8B40372db16cA8045F28C6FE07228F3781A

# Arena — comma-separated config IDs that mirror trades to DGClaw
ARENA_ENABLED_CONFIGS=b9d9bf00-a89a-4df7-9f7f-abcfff7e7d85
```

---

## Architecture: Arena as an Execution Layer (NOT a trading mode)

**Key design decision**: The arena is NOT a new `trading_mode`. It's a **parallel execution layer** that mirrors an existing bot's trade intents to DGClaw via ACP. The bot runs normally (paper or live) — the arena layer intercepts the same decisions and also executes them on DGClaw.

```
Bot cycle → Decision: "long ETH, confidence 0.85"
  │
  ├── Primary execution: existing trading_mode (paper or hyperliquid)
  │     └── position sized from paper_account or HL balance
  │
  └── Arena mirror: if bot is arena-enabled
        └── same decision, position sized from DGClaw subaccount balance
        └── ACP job to perp_trade → DGClaw → Hyperliquid
```

**Position sizing is independent.** The same confidence score + trade settings run against different account balances. A paper bot with $10K account trading $500 positions might translate to $25 on a $50 DGClaw subaccount — same percentage, different scale. Existing sizing logic handles this naturally.

### Where the Arena Hook Lives (orchestrator.py)

NOT a new branch in `_run_trading_v2`. Instead, after the primary trade result:

```python
# Primary execution (unchanged)
trade_result = await self._execute_primary_trade(config, decision_result)

# Arena mirror (new, parallel)
if config.arena_enabled:
    await self._execute_arena_trade(config, decision_result)
```

### ACP Job Lifecycle per Arena Trade

```
1. Create ACP job to DGClaw perp_trade offering (~3s)
2. DGClaw accepts, sends TRANSACTION memo (~5s)
3. We pay $0.01 job fee (~3s)
4. DGClaw executes on Hyperliquid, delivers receipt (~5s)
5. Total: ~15-20s per trade
```

Latency doesn't matter — the bot cycle doesn't wait for it. Arena execution is fire-and-forget from the bot's perspective. The background service (`sebastian_virtuals.py`) handles the ACP job lifecycle async.

### Arena Close Sync (`trading/virtuals/arena_sync.py`)

Positions close through **5 paths**. Four are logged in real time. The fifth (DGClaw server-side TP/SL) is backfilled after-the-fact by `sync_closes_from_hl`.

```
Close Path                  File                                      Arena Response
──────────                  ──────                                    ──────────────
Paper TP/SL/manual          supabase_service.py:close_position()      → mirror_close_to_arena()
Live TP/SL (fill scan)      hyperliquid_adapter._detect_and_log_closes → mirror_close_to_arena()
Live manual close           ggbot.py:close_hyperliquid_position()     → mirror_close_to_arena()
Decision "exit"             orchestrator._execute_claw_arena_trade()  → direct close (existing)
Safety net (per cycle)      orchestrator._reconcile_arena_position()  → closes stale positions
DGClaw server-side TP/SL    NONE (no ACP job produced)                → sync_closes_from_hl() backfill
```

`mirror_close_to_arena(config_id, symbol, close_reason, user_id)` — idempotent. Checks DGClaw position exists before closing. Logs `arena_exit` activity with source `arena_sync`. Multiple callers can fire for same close — DGClaw position check prevents duplicate closes.

Reconciler runs at start of each arena trade in orchestrator. Compares DGClaw positions vs primary (paper_trades + live_trades). Closes any arena position not held by primary. Source: `arena_reconciler`.

### Close Backfill from HL Fills (`sync_closes_from_hl`)

DGClaw monitors user-set TP/SL levels itself and executes directly on Hyperliquid without going through an ACP job. None of the `mirror_close_to_arena` paths fire for these — the position simply disappears from Railway. `sync_closes_from_hl` plugs this gap by querying Hyperliquid Info API and backfilling `arena_exit` activities.

**Data source: HL Info API, not DGClaw Railway.** Railway returns `hlSubaccountAddress: None` when idle — can't query it when we most need to. HL subaccount address is persistent per agent once captured.

**Capture flow (self-healing)**:
1. `/api/v2/virtuals-arena/status` endpoint polls `claw_api.get_dgclaw_account()` (already fetches `hl_subaccount` when populated)
2. On every call, if Railway returns non-null `hl_subaccount` AND `arena_agents.hl_subaccount_address IS NULL`, persist it via `UPDATE ... WHERE IS NULL`
3. Every agent gets its address captured automatically on its next active DGClaw position. No backfill script needed

**Sync flow** (invoked from same `/status` endpoint, awaited):
1. Load agent with `hl_subaccount_address` (skip if NULL — waits for self-heal)
2. Redis throttle check: `arena:sync_closes_last_run:{agent_id}` with 60s TTL. If present, return 0 (<1ms short-circuit)
3. `Info.user_fills_by_time(hl_sub, 7_days_ago_ms)` via `asyncio.to_thread` (SDK is sync)
4. Filter to fills where `dir` starts with `"Close"`
5. Load existing dedup keys for this config: both `hl_order_id` (primary) and `(pair, created_at)` pairs (secondary, for legacy rows that pre-date this feature)
6. Group partial fills by `(coin, time_ms // 5000, dir)` — 5s bucket. Sum sz, sum closedPnl, size-weighted avg px, earliest oid as dedup key. Liquidation flag if any fill in bucket is liquidation
7. For each group, skip if oid in `existing_oids` OR if a matching `arena_exit` exists within ±60s of fill time for the same pair
8. Insert surviving groups via direct `db_execute` with `created_at = datetime.fromtimestamp(fill_time_ms / 1000, tz=UTC)` — rows slot into TVTimeline at the correct historical position. `activity_source='hl_sync'`, `close_reason='dgclaw_server_side'` or `'liquidation'`

**Why this is pure backend plumbing**:
- Modal polls `/status` every 10s (`degen-arena-modal.tsx:21`). Sync rides that poll
- TVTimeline polls `/activities/{configId}` every 10s (`tv-timeline.tsx:806`). New rows appear automatically
- No new endpoint, no button, no custom events, no frontend changes

**Dedup strategy — two parallel checks**:

| Source | Carries `hl_order_id` | Dedup check |
|---|---|---|
| `hl_sync` (this function) | ✅ always | primary: `details->>'hl_order_id'` |
| `arena_sync` (live TP/SL path) | ❌ no | secondary: `(pair, created_at ± 60s)` |
| `claw_arena` (decision close) | ❌ no | secondary: `(pair, created_at ± 60s)` |
| `arena_reconciler` (safety net) | ❌ no | secondary: `(pair, created_at ± 60s)` |

The ±60s window is safe because back-to-back closes on the same pair within one minute are effectively impossible on bot cycles of 3-5 minutes. When live close paths eventually start carrying `hl_order_id`, the secondary check becomes a no-op.

**Partial fill aggregation**: `market_close()` can produce multiple fills at the same instant on different liquidity levels. Grouping by 5s bucket collapses them into one activity row regardless of how they filled, matching the same pattern used by `hyperliquid_adapter._detect_and_log_closes`.

**Redis throttle**: `arena:sync_closes_last_run:{agent_id}` with 60s TTL. If Redis is unavailable, function falls through (sync is self-dedupping via the DB query — throttle is a cost optimization, not a correctness requirement). Namespace shared with `arena:trade_queue`, no new Redis infrastructure.

---

## Scoping: Two Phases

### Phase 1: The Arbiter on DGClaw (admin only)
- Single ACP agent: ggbots.ai (`0x2E48f...`)
- The Arbiter bot is marked `arena_enabled`
- Arena layer mirrors its trade intents to DGClaw
- Admin controls everything — no user-facing changes
- **Goal**: Prove the arena execution layer works, compete on leaderboard

### Phase 2: Any User Can Enter the Arena

**Model: Lite Agent Pool + Claw API Control (VALIDATED 2026-03-26)**

Users don't interact with Virtuals at all. Platform pre-creates a pool of ~50 lite agents, assigns one per user on demand. Lite agents are controlled entirely via the **claw REST API** (`x-api-key` header) — no EOA private key needed. Privy-managed signers handle all on-chain signing behind the scenes.

**Key discovery**: Lite agents (created via `/api/agents/lite/key`) use a different control model than full agents (ggbots.ai/Sebastian). Full agents need EOA whitelisting + Python SDK. Lite agents use an API key + claw REST API. The claw API auto-handles payment, signing, and job lifecycle.

### Phase 2: Claw API — Validated Endpoints

All controlled via `x-api-key: <agent_api_key>` header on `https://claw-api.virtuals.io`.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/acp/jobs` | POST | Create ACP job (trade, deposit, register) |
| `/acp/jobs/{jobId}` | GET | Job status + deliverable |
| `/acp/jobs/active` | GET | List active jobs |
| `/acp/jobs/completed` | GET | List completed jobs |
| `/acp/me` | GET | Agent profile |
| `/acp/wallet-balances` | GET | Agent wallet USDC balance |
| `/acp/agents?query=X` | GET | Browse agents |
| `/acp/topup` | GET | Payment/topup URL |

**Job creation payload**:
```json
{
  "providerWalletAddress": "0xd478a8...",
  "jobOfferingName": "perp_trade",
  "serviceRequirements": {"action": "open", "pair": "ETH", "side": "long", "size": "12", "leverage": 3}
}
```

**Auto-payment**: Claw API automatically pays the $0.01 ACP fee when provider accepts (NEGOTIATION → TRANSACTION). No manual pay step needed.

### Phase 2: Agent Pool Creation (admin, batch)

**Step 1: Authenticate**
```bash
# Get auth URL, click link in browser, script polls for JWT
python scripts/create_arena_pool.py auth
```
Under the hood:
- `GET https://acpx.virtuals.io/api/auth/lite/auth-url` → `{authUrl, requestId}`
- Open `authUrl` in browser → Privy auth
- Poll `GET /api/auth/lite/auth-status?requestId=...` → `{token}` (30min window)

**Step 2: Create agents**
```bash
python scripts/create_arena_pool.py create --count 10 --start-index 2
```
- `POST https://acpx.virtuals.io/api/agents/lite/key` + Bearer token + `{data: {name: "ggbot-NNN"}}`
- Returns `{id, walletAddress, apiKey}`
- Inserts into `arena_agents`, stores claw API key in Supabase Vault

**Step 3: Tokenize via claw API** (NOT the Virtuals dashboard)
```
POST https://claw-api.virtuals.io/acp/me/tokens
Header: x-api-key: <agent_claw_api_key>
Body: {"symbol": "GGBOT004", "description": "ggbots.ai arena agent #004"}

Returns: {symbol, tokenAddress, txHash, launchedAt}
```
**IMPORTANT**: The Virtuals dashboard tokenization is broken (sends numeric agent ID, endpoint expects UUID). Always use the claw API `POST /acp/me/tokens` endpoint instead. Each agent can only have one token.

**Step 4: DGClaw registration** — handled automatically on first user deposit by `_register_on_dgclaw()` in `api/virtuals_arena.py`. Creates `join_leaderboard` ACP job, decrypts returned DGClaw API key via RSA, stores in vault. Costs $0.01 from agent wallet.

**Step 5: Verify pool**
```bash
python scripts/create_arena_pool.py status
```

**Current pool (2026-03-30):** 30 ggbot agents (ggbot-001 to ggbot-030) + 10 Denis agents. ggbot-001 retired, ggbot-002 + ggbot-004 tokenized, rest need tokenization.

### External Agent Onboarding (Denis model)

Agents can also be created externally via OpenClaw ACP (`npm run acp -- setup`). To integrate:
1. Get from agent creator: wallet address, claw API key (`acp-...`), token address, token symbol
2. DGClaw API key (`dgc_...`) if they registered — otherwise auto-registration handles it
3. Insert into `arena_agents` with `assigned_config_id` pointing to the ggbot config
4. Vault both keys via `VaultManager.store_arena_credential(agent_id, claw_key, dgclaw_key)`

OpenClaw stores everything in its local `config.json` — agent creators can export from there.

### Phase 2: User Flow (1-bot-1-agent model)

```
User clicks "Degen Arena" on a specific bot's ActivationBar in Forge
  → Modal opens, user enters their wallet address (Base, for withdrawals)
  → Backend assigns an available agent from pool to this config_id
  → User sends USDC to the agent's smart wallet (Base network)
  → User clicks "Check / Deposit" in modal
  → Backend auto-registers on DGClaw (join_leaderboard, first time only)
  → Backend triggers perp_deposit via claw API
  → DGClaw bridges Base → Arbitrum → HL (~$1 bridge fee)
  → Bot cycles mirror trades to DGClaw automatically
  → Each bot has its own independent arena agent + track record
```

**1-bot-1-agent**: each bot (config_id) gets its own arena agent. Users can enter multiple bots. No separate page — everything lives in a modal on the Forge page.

### Phase 2: Deposit Flow Detail

```
User sends USDC to agent wallet (Base)
  → User clicks "I've Sent USDC" in Degen Arena modal
  → Backend checks wallet balance (retry 3x with 5s delays)
  → If first deposit: auto-registers on DGClaw (join_leaderboard, $0.01)
  → Backend triggers: POST /acp/jobs {perp_deposit, amount}
  → Claw API signs via Privy-managed signer → ACP job on-chain
  → DGClaw bridges: Base → Arbitrum → Hyperliquid (~$1 bridge fee)
  → DGClaw credits agent's internal balance
  → $1 kept in wallet as reserve for future ACP trade fees ($0.01/trade)
```

**Fee breakdown for $20 deposit:**
- $1.00 reserved in wallet for ACP fees (~100 trades)
- $0.01 registration fee (first time only)
- ~$1.00 bridge fee (Base → Arb → HL)
- **~$18 effective trading balance** on Degen Claw

**Bridge timing**: Typically 1-3 minutes. Can take longer when DGClaw processes multiple deposits. Our polling timeout is 90s — jobs continue processing on DGClaw's side even if we time out.

**IMPORTANT: Use `base.llamarpc.com` for on-chain balance checks**, not `mainnet.base.org`. The default Base RPC frequently returns stale data. The claw API `GET /acp/wallet-balances` can also lag — always verify critical balances via direct RPC.

### Phase 2: Trading via Claw API (differs from Phase 1)

Phase 1 uses the **Python ACP SDK** (EOA signing) via `sebastian_virtuals.py`. Phase 2 uses the **claw REST API** (API key). Two different control paths:

| | Phase 1 (admin bot) | Phase 2 (user agents) |
|---|---|---|
| **Agent type** | Full agent (ggbots.ai) | Lite agent (pool) |
| **Control** | ACP Python SDK + EOA private key | Claw REST API + apiKey |
| **Signing** | Our EOA signs UserOperations | Privy-managed signer (automatic) |
| **Trade execution** | `sebastian_virtuals.py` section D | New: claw API adapter in orchestrator |
| **Position data** | Railway backend `/users/{wallet}/account` | Same Railway backend |

### Phase 2: Frontend — Degen Arena Modal

Integrated into Forge page via `DegenArenaModal` on each bot's ActivationBar. No separate page.

**Button on ActivationBar:** "Degen Arena" → opens modal for that specific bot.

**Modal states:**
1. **Not joined**: Explanation of arena mirroring, 3 steps, fee breakdown, wallet input → "Enter Arena"
2. **Joined, needs funding**: Deposit address, "$20+ USDC on Base", "I've Sent USDC" button with retry
3. **Funded**: Arena balance (hero number), positions, deposit more, withdraw, leaderboard link

**Key UX decisions:**
- 1-bot-1-agent: each bot independently joins the arena
- Modal auto-refreshes every 10s when open
- Bot must be active for trades to mirror (inactive bot = agent keeps position but no new trades)
- "Arena Balance" = what the bot trades with on Degen Claw
- "Pending" = USDC in agent wallet not yet bridged
- Leaderboard link: `https://degen.virtuals.io/#leaderboard`
- "Your bot will appear on the leaderboard after its first trade"

### Phase 2: DB Schema

**Table: `arena_agents`** (agent pool, 1-bot-1-agent)
```
id                serial       PK
virtuals_id       integer      Virtuals agent ID
agent_name        varchar      Display name (e.g., "ggbot-002")
wallet_address    varchar      UNIQUE, agent smart wallet on Base
claw_api_key_vault_id  uuid    Supabase Vault ref for claw REST API key
dgclaw_api_key_vault_id uuid   Supabase Vault ref for DGClaw API key (from join_leaderboard)
token_address     varchar      Token contract address (from tokenization)
token_symbol      varchar      Token ticker (e.g., "GGBOT002")
assigned_user_id  uuid         FK to auth.users (ownership for auth checks)
assigned_config_id uuid        FK to configurations (the bot this agent serves)
user_wallet_address varchar    User's Base wallet (withdrawal destination)
assigned_at       timestamptz  When assigned
status            varchar      'available' | 'assigned' | 'retired'
created_at        timestamptz
```

**Key**: `assigned_config_id` is the primary lookup. If a config has an arena agent, trades are mirrored.
**No `arena_enabled` column needed** — agent assignment IS enablement.
**Deactivated bots** keep their agent but stop routing trades (user can still withdraw).

---

## Current Status (2026-04-07)

### Phase 1: Admin Bot — COMPLETE
- [x] ggbots.ai registered on DGClaw, balance $70+, automated trades verified
- [x] `dgclaw_service.py` — arena execution service (ACP SDK, Railway backend for balance)
- [x] Orchestrator arena hook → `arena:trade_queue` → `sebastian-virtuals` section D
- [x] Arena-enabled via `ARENA_ENABLED_CONFIGS` env var (Sev's live BTC/USDT bot)
- [x] Close sync Phase 1 fallback: `arena_sync.py` enqueues close via Redis when no `arena_agents` row

### Phase 2: User Agents — COMPLETE (2026-04-04)
- [x] Lite agent pool: 40 total (27 available, 11 assigned, 2 retired). 39 tokenized
- [x] Denis's 10 agents funded ~$15 each, DGClaw registered
- [x] First user test: The Technician → ggbot-004 assigned → $6 deposited → $4.99 on DGClaw
- [x] `trading/virtuals/claw_api.py` — async HTTP client for claw REST API (timeout 180s)
- [x] `api/virtuals_arena.py` — config-based endpoints (join, status, check-deposit, withdraw)
- [x] `core/auth/vault_utils.py` — arena credential vault (skip-if-exists for claw key on re-registration)
- [x] Orchestrator Phase 2 — direct claw API trade routing by `assigned_config_id`
- [x] `scripts/create_arena_pool.py` — admin batch agent creation + auth flow
- [x] DGClaw auto-registration: async fire-and-forget on first check-deposit, returns `"registering"` immediately
- [x] `DegenArenaModal` — smart button labels, registration progress, correct fee messaging
- [x] `ActivationBar` — stateful button: Enter Degen Arena → Arena: Needs Funds → Manage Arena Agent
- [x] Arena close sync: Phase 1 (Redis queue) + Phase 2 (claw API) + reconciler safety net
- [x] **HL fill backfill** (2026-04-07): `sync_closes_from_hl()` catches DGClaw server-side TP/SL closes that never produce an ACP job. `arena_agents.hl_subaccount_address` column + opportunistic capture in /status. Verified on ggbot-004's Apr 5 22:02 close (oid=371386016564)
- [ ] Phase 1 admin bot fix: `user_id='system'` fails UUID validation
- [ ] End-to-end: wait for bot entry signal → verify arena mirror + close sync

---

## Files

| File | Purpose |
|---|---|
| `trading/virtuals/README.md` | This file — full context |
| `trading/virtuals/arena_sync.py` | Close mirroring (`mirror_close_to_arena`) + close backfill (`sync_closes_from_hl`) + `_arena_to_pair()` |
| `database/migrations/add_hl_subaccount_to_arena_agents.sql` | Migration: `arena_agents.hl_subaccount_address` column + partial index |
| `trading/virtuals/claw_api.py` | Async HTTP client for claw REST API (Phase 2 user agents) |
| `trading/virtuals/dgclaw_service.py` | Phase 1 arena service (ACP SDK, admin bot) |
| `api/virtuals_arena.py` | Phase 2 API endpoints (join, status, deposit, withdraw, leaderboard) |
| `core/auth/vault_utils.py` | Arena credential vault (store/get by agent_id, config_id) |
| `core/orchestrator/orchestrator.py` | Arena hooks: Phase 2 (claw API by config) + Phase 1 (ACP SDK fallback) |
| `core/services/acp_client.py` | ACP SDK wrapper (Phase 1 admin bot) |
| `sebastian_virtuals.py` | ACP background service + Phase 1 arena trade queue |
| `scripts/create_arena_pool.py` | Admin tool: auth, create, register, seed, status |
| `frontend/components/degen-arena-modal.tsx` | DegenArenaModal (Forge ActivationBar integration) |
| `frontend/app/virtuals-arena/` | Standalone page (deprecated — modal is primary UX) |
| `ecosystem.config.js` | PM2 config for scheduler (ARENA_ENABLED_CONFIGS) + sebastian-virtuals (DGClaw env) |
