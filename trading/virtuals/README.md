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

```
1. Sev opens https://acpx.virtuals.io/api/auth/lite/auth-url → authUrl
2. Sev authenticates in browser → polls until JWT token returned (30min window)
3. Script loops 50 times:
   POST /api/agents/lite/key + Bearer token + {name: "ggbots-arena-NNN"}
   → {id, name, walletAddress, apiKey}
   → Store in arena_agents table
4. Tokenize each agent on Virtuals dashboard (manual — assign ticker)
5. For each agent: POST /acp/jobs with join_leaderboard + RSA public key
   → Decrypt returned encryptedApiKey → DGClaw API key
6. All 50 agents registered on DGClaw, each with own API key
```

When pool runs low, Sev authenticates again and tops up. ~10min admin task.

**Validated test** (2026-03-26): Created `ggbots-arena-test-001`, tokenized as GGBOT001, funded $6, registered on DGClaw, deposited $4.99 to HL, opened ETH long $12 @ 3x — all programmatically via claw API.

### Phase 2: User Flow

```
User clicks "Join Virtuals Arena" on /virtuals-arena page
  → Backend assigns unassigned agent from pool (ggbots-arena-017)
  → User sends $25 USDC to agent's smart wallet address (Base network)
  → Backend detects deposit via claw API (GET /acp/wallet-balances)
  → Backend triggers perp_deposit via claw API (POST /acp/jobs)
  → DGClaw bridges Base → Arbitrum → HL, credits agent (~$21 after bridge fees)
  → User picks which bot drives the arena
  → Bot cycles create trades via claw API (POST /acp/jobs with perp_trade)
  → User appears on DGClaw leaderboard individually
```

**No Virtuals login, no MetaMask signing, no wallet setup.** User just sends USDC and picks a bot.

### Phase 2: Deposit Flow Detail

```
User sends USDC to agent wallet (Base)
  → Claw API detects balance (GET /acp/wallet-balances)
  → Backend triggers: POST /acp/jobs {perp_deposit, amount: "25"}
  → Claw API signs via Privy-managed signer → ACP job on-chain
  → DGClaw bridges: Base → Arbitrum → Hyperliquid (~17% bridge fee)
  → DGClaw credits agent's internal balance
  → $0.01 ACP fee auto-paid from agent wallet
```

No platform float — user's USDC goes from agent wallet → DGClaw. We control via API key.

**Bridge fee note**: $6 deposit → $4.99 received (~17% fee). Users need to know effective deposit is less. $25 deposit → ~$21 effective.

### Phase 2: Trading via Claw API (differs from Phase 1)

Phase 1 uses the **Python ACP SDK** (EOA signing) via `sebastian_virtuals.py`. Phase 2 uses the **claw REST API** (API key). Two different control paths:

| | Phase 1 (admin bot) | Phase 2 (user agents) |
|---|---|---|
| **Agent type** | Full agent (ggbots.ai) | Lite agent (pool) |
| **Control** | ACP Python SDK + EOA private key | Claw REST API + apiKey |
| **Signing** | Our EOA signs UserOperations | Privy-managed signer (automatic) |
| **Trade execution** | `sebastian_virtuals.py` section D | New: claw API adapter in orchestrator |
| **Position data** | Railway backend `/users/{wallet}/account` | Same Railway backend |

### Phase 2: Frontend — `/virtuals-arena` page

Separate from existing ggArena. Dedicated page with:
- DGClaw leaderboard (from `GET /api/leaderboard`)
- User's arena status (balance, positions from Railway backend)
- Bot selector (which of their bots drives the arena agent)
- Entry: display agent wallet address for USDC deposit (Base network)
- Position monitoring (open positions, PnL, trade history)

### Phase 2: DB Schema

**New table: `arena_agents`** (agent pool)
```
agent_id          varchar      PK — Virtuals agent ID
agent_name        varchar      Display name (e.g., "ggbots-arena-017")
wallet_address    varchar      Agent smart wallet on Base
claw_api_key      varchar      Claw API key for agent control (encrypted)
dgclaw_api_key    varchar      DGClaw API key (encrypted, from join_leaderboard)
token_address     varchar      Token contract address (from tokenization)
token_symbol      varchar      Token ticker (e.g., "GGBOT017")
assigned_user_id  uuid         FK to user_profiles (NULL = unassigned)
assigned_at       timestamptz  When user was assigned this agent
status            varchar      'available' | 'assigned' | 'retired'
created_at        timestamptz
```

**`configurations` column**: `arena_enabled` boolean — which bot drives the user's arena agent.

**`user_profiles` columns**: `arena_agent_id` FK to arena_agents (shortcut lookup).

### Phase 2: Remaining Questions
- Can user change which bot drives the arena mid-season?
- What happens to arena positions when bot is deactivated?
- Deposit detection: poll agent wallet balance on claw API, or webhook?
- Withdrawal flow: user requests, POST /acp/jobs with perp_withdraw, USDC back to user wallet
- Agent pool replenishment: automated alert when pool < 10 available?
- Tokenization: can it be automated via API, or always manual dashboard?
- Bridge fee UX: show estimated effective deposit amount before user sends

---

## Current Status (2026-03-25)

### Completed
- [x] ggbots.ai registered on DGClaw, deposited $36, first trade, leaderboard #12
- [x] `dgclaw_service.py` — arena execution service (open/close via ACP SDK, account via Railway)
- [x] Orchestrator arena hook → `arena:trade_queue` → `sebastian-virtuals` section D
- [x] Arena-enabled via `ARENA_ENABLED_CONFIGS` env var (Sev's live HL bot)
- [x] Discovered Railway backend (`dgclaw-app-production.up.railway.app`) for real balance
- [x] **Phase 2 validation (2026-03-26)**: Full programmatic flow proven with lite agent
  - Created `ggbots-arena-test-001` via lite API (claw API key control, no EOA needed)
  - Tokenized as GGBOT001 on dashboard
  - Funded $6, registered on DGClaw (join_leaderboard → RSA decrypt → API key)
  - Deposited $4.99 to HL via perp_deposit
  - Opened ETH long $12 @ 3x via perp_trade
  - All via claw REST API with `x-api-key` header — zero SDK/EOA involvement

### Phase 1: Remaining
- [ ] Verify automated arena trade end-to-end (restart services, wait for bot cycle)
- [ ] Position monitoring dashboard/logging
- [ ] Keep ACP wallet funded (need USDC buffer for $0.01/trade fees)

### Phase 2: Any User Can Enter
- [ ] Virtuals auth flow (auth-url → poll → agent creation)
- [ ] Entry ticket purchase (Stripe/credits → platform deposits USDC)
- [ ] `/arena` frontend page (leaderboard, positions, bot selection)
- [ ] Per-user DGClaw registration + agent storage in user_profiles

---

## Files

| File | Purpose |
|---|---|
| `trading/virtuals/__init__.py` | Package init |
| `trading/virtuals/README.md` | This file — full context |
| `trading/virtuals/dgclaw_service.py` | Arena execution service (open/close via ACP, account via Railway backend) |
| `core/services/acp_client.py` | ACP SDK wrapper (buyer + provider) |
| `core/orchestrator/orchestrator.py` | Arena hook: `_is_arena_enabled()` + `_enqueue_arena_trade()` |
| `sebastian_virtuals.py` | ACP background service + section D arena trades |
| `ecosystem.config.js` | PM2 config for scheduler (ARENA_ENABLED_CONFIGS) + sebastian-virtuals (DGClaw env) |
