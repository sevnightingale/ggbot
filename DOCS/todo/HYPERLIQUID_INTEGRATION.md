# Hyperliquid Live Trading Integration

**Created**: 2026-02-08
**Updated**: 2026-02-09
**Purpose**: Replace Symphony/Aster with non-custodial Hyperliquid perpetual futures trading
**Priority**: P1 — Core product feature, replaces blocked Symphony integration

---

## Executive Summary

**The Goal**: Users connect their Ethereum wallet in ggbots, deposit USDC to Hyperliquid, authorize ggbots to trade on their behalf, and their AI bot trades real perpetual futures — all without leaving ggbots.

**Why Hyperliquid**:
- Non-custodial: Protocol-enforced "API wallets" can trade but CANNOT withdraw
- 291 perpetual markets (vs Symphony's 100, Aster's 33)
- Official Python SDK (`hyperliquid-python-sdk`)
- Deepest DEX liquidity ($7.3B+ open interest, $3.35T total volume)
- Up to 50x leverage, SL/TP native, testnet available
- No KYC, no account creation — Ethereum wallet IS the account

**Key Architecture Decision**: User wallet + API wallet model. ggbots never holds user funds. Hyperliquid cryptographically enforces that API wallets cannot withdraw.

**Replaces**: Symphony (pivoting, blocked API) and Aster (limited symbols, not preferred)

---

## Architecture

### Trust Model

```
User's Wallet (MetaMask, Coinbase, etc.)
  └── OWNS funds on Hyperliquid
  └── CAN deposit, withdraw, trade
  └── Signs one-time ApproveAgent transaction

ggbots API Wallet (generated keypair)
  └── CAN trade on behalf of user (market/limit/SL/TP)
  └── CAN set leverage, manage positions
  └── CANNOT withdraw funds (protocol-enforced)
  └── CANNOT transfer funds
  └── Private key stored in Supabase Vault
```

### User Flow

```
ONE-TIME SETUP (user does 3 things):
  1. Connect wallet (RainbowKit — reuse Arena infra)
  2. Deposit USDC to Hyperliquid (transfer on Arbitrum → bridge contract)
  3. Sign "Authorize ggbots" (ApproveAgent — creates API wallet)

THEN AUTOMATED FOREVER:
  4. Bot runs extraction → decision → trading (existing pipeline)
  5. Backend signs Hyperliquid orders with API wallet key
  6. User monitors in ggbots dashboard (existing UI)
  7. User withdraws from Hyperliquid anytime (only they can)
```

### Data Flow

```
Decision Engine (existing)
         ↓ trade intent
HyperliquidLiveTradingService (NEW)
         ↓ constructs order
Hyperliquid Python SDK (exchange.market_open / order / market_close)
         ↓ signs with API wallet key from Vault
Hyperliquid API (https://api.hyperliquid.xyz)
         ↓ executes on-chain
live_trades table (existing, provider='hyperliquid')
         ↓ dashboard enrichment
SSE stream → frontend (existing pattern)
```

---

## Existing Infrastructure We Reuse

| Component | Status | Notes |
|-----------|--------|-------|
| Web3 wallet connect (wagmi v2, RainbowKit v2) | ✅ Built for Arena | Same flow, different chain action |
| `live_trades` table with `provider` column | ✅ Exists | Add `provider='hyperliquid'` |
| `execute_trade_intent()` interface pattern | ✅ Paper/Symphony/Aster all use it | Same interface |
| Supabase Vault for credential storage | ✅ Used for Symphony keys | Store API wallet private key |
| Dashboard SSE enrichment pattern | ✅ `_enrich_live_positions_and_accounts()` | Add Hyperliquid adapter |
| Position monitoring service | ✅ account-monitor PM2 service | Add Hyperliquid adapter |
| `user_profiles` table | ✅ Has symphony/aster wallet columns | Add hyperliquid columns |
| Frontend PositionsTable with source routing | ✅ Handles paper/symphony/aster | Add 'hyperliquid' source |

---

## Technical Details (Verified Against Docs + SDK Source)

### Hyperliquid Python SDK

**Install**: `pip install hyperliquid-python-sdk`
**Source**: https://github.com/hyperliquid-dex/hyperliquid-python-sdk

Key methods verified in `exchange.py`:

```python
# Create API wallet (user signs in browser, we store the key)
exchange.approve_agent(name="ggbots-v1")
# Returns: (response, agent_private_key)

# Initialize exchange with API wallet
exchange = Exchange(
    wallet=agent_private_key,
    base_url="https://api.hyperliquid.xyz",
    account_address="0xUSER_MAIN_WALLET"
)

# Trading
exchange.market_open("BTC", is_buy=True, sz=0.001, slippage=0.05)
exchange.market_close("BTC")
exchange.order("ETH", is_buy=False, sz=0.1, limit_px=3500,
               order_type={"limit": {"tif": "GTC"}})

# Trigger orders (SL/TP)
exchange.order("BTC", is_buy=False, sz=0.001, limit_px=95000,
               order_type={"trigger": {"triggerPx": "95000", "isMarket": True, "tpsl": "sl"}})

# Leverage
exchange.update_leverage(10, "BTC", is_cross=True)
```

### API Wallet Limits
- 1 unnamed + 3 named API wallets per account
- Nonces tracked per signer (independent of master)
- Recommendation: Don't reuse API wallet addresses; generate fresh on new setup

### Deposits (Bridge2)
- Contract: `0x2df1c51e09aecf9cacb7bc98cb1742757f163df7` (Arbitrum)
- Token: USDC on Arbitrum
- Minimum: $5 USDC
- Speed: <1 minute
- Method: Standard ERC-20 transfer to bridge contract
- Also supports: `batchedDepositWithPermit` (EIP-712)

### Withdrawals
- User signs message on Hyperliquid (no Arbitrum tx)
- Validators process on Arbitrum side
- Funds arrive in 3-4 minutes
- Only master wallet can withdraw (NOT API wallet)

### Rate Limits
- REST: 1,200 requests/min (weight-based)
- Per-account: 10,000 initial buffer + 1 per $1 USDC traded
- Open orders: 1,000 base (up to 5,000 with volume)
- WebSocket: 100 connections, 1,000 subscriptions per IP

### Testnet
- URL: `https://api.hyperliquid-testnet.xyz`
- Same API, same SDK, just swap base_url
- Free test funds available

### Symbol Coverage
- 291 perpetual markets (per CoinGecko Feb 2026)
- All majors + altcoins + memecoins
- Recently added: US equities, commodities (gold, silver) via HIP-3

---

## Implementation Plan

### Phase 1: Backend Trading Service (~12-16 hours)

**Goal**: ggbots can execute trades on Hyperliquid given an API wallet key.

#### 1a. HyperliquidLiveTradingService

**New file**: `trading/live/hyperliquid_service.py`

Implements same interface as `SupabasePaperTradingService` and `SymphonyLiveTradingService`:

```python
class HyperliquidLiveTradingService:
    async def execute_trade_intent(self, intent: dict) -> dict
    async def close_position(self, user_id: str, config_id: str, symbol: str) -> dict
    async def get_open_positions(self, user_id: str) -> list
    async def get_account_summary(self, user_id: str) -> dict
    async def get_trade_history(self, user_id: str, config_id: str) -> list
```

Key implementation details:
- Retrieve API wallet key from Supabase Vault using user_id
- Initialize `Exchange` with API wallet key + user's master wallet address
- Convert ggbots symbol format (BTC/USDT) to Hyperliquid format (BTC)
- Apply config defaults (leverage, SL/TP, position sizing)
- Save to `live_trades` table with `provider='hyperliquid'`

**Position sizing with shared accounts**: All of a user's Hyperliquid bots share one account balance. Each bot's `max_margin_percent` (existing field in `core/config/schemas.py`) defines what share of the account that bot can use. Before sizing, query Hyperliquid Info API for available margin, then apply: `margin = confidence × max_margin_percent × available_balance`. The sum of `max_margin_percent` across all user's live Hyperliquid bots must not exceed 100% — enforced at config save time (backend + frontend validation).

#### 1b. Orchestrator Routing

**File**: `ggbot.py` (existing `_run_trading_v2()`)

Add routing for `trading_mode='hyperliquid'`:
```python
if config.trading_mode == 'hyperliquid':
    service = HyperliquidLiveTradingService()
    result = await service.execute_trade_intent(intent)
```

**Account allocation validation**: When saving a bot config with `trading_mode='hyperliquid'`, query all other Hyperliquid-mode bots for the same user and verify that the sum of `max_margin_percent` values (including the new/updated bot) does not exceed 100%. Reject the save with a clear error if exceeded. This uses the existing `max_margin_percent` field — no new config fields needed.

#### 1c. Symbol Mapping

**File**: `core/symbols/registry.py`

Add Hyperliquid compatibility flags (similar to `symphony_compatible`, `aster_compatible`).
Hyperliquid uses plain names: "BTC", "ETH", "SOL" (no /USDT suffix).

#### 1d. Database

```sql
-- Add to user_profiles
ALTER TABLE user_profiles
ADD COLUMN hyperliquid_wallet_address VARCHAR(42),
ADD COLUMN hyperliquid_vault_id UUID;  -- Supabase Vault reference for API wallet key

-- Add to live_trades (provider='hyperliquid' already supported by schema)
-- No schema changes needed
```

#### 1e. Testing on Testnet

- Use testnet URL for all development
- Write integration test: create order → verify → close
- Test SL/TP trigger orders
- Test position sizing calculations
- Verify API wallet cannot call withdrawal methods

---

### Phase 1.5: Frontend Setup Page + Mainnet Test ✅ COMPLETE (2026-02-09)

**Goal**: Isolated `/hyperliquid` page for complete setup flow + mainnet verification.

**Result**: Verified end-to-end — $10 USDC deposit → authorize → test trade (0.01 ETH @ $2,071.90) → close.

#### Files Created

| File | Purpose |
|------|---------|
| `frontend/lib/hyperliquid-config.ts` | Arbitrum wagmi config, EIP-712 domain/types, USDC + bridge addresses |
| `frontend/components/hyperliquid/HyperliquidSetup.tsx` | Main component (~550 lines): wallet connect, deposit, withdraw, authorize, status, test trade |
| `frontend/app/hyperliquid/page.tsx` | Route with `dynamic()` import, SSR disabled |
| `frontend/app/hyperliquid/layout.tsx` | Metadata only |

#### Files Modified

| File | Changes |
|------|---------|
| `frontend/lib/api.ts` | Added `setupHyperliquid`, `getHyperliquidStatus`, `disconnectHyperliquid`, `testHyperliquidTrade` |
| `ggbot.py` | Added 4 endpoints: `POST /setup`, `GET /status`, `POST /disconnect`, `POST /test-trade` under `/api/v2/hyperliquid/` |

#### Key Technical Decisions & Lessons

**Separate wagmi config**: Arena uses Scroll chain, Hyperliquid uses Arbitrum. Each page gets its own `WagmiProvider` + `QueryClient` to avoid chain conflicts. Cannot share a single wagmi config across chains.

**EIP-712 signing chainId**: The Python SDK uses `0x66eee` (421614) as `signatureChainId`, but viem (browser) enforces that the EIP-712 domain `chainId` must match the connected wallet's active chain. Since the user is on Arbitrum (42161), we must use `0xa4b1` (42161) for both the domain and the `signatureChainId` in the action payload. Hyperliquid accepts any signatureChainId — their comment: *"signatureChainId is the chain used by the wallet to sign and can be any chain."*

**Deposit flow**: On-chain ERC-20 `transfer()` of USDC to Hyperliquid bridge contract (`0x2df1c51e09aecf9cacb7bc98cb1742757f163df7`). Uses wagmi's `useWriteContract` + `useWaitForTransactionReceipt`. Costs Arbitrum gas (~$0.01). Min $5.

**Withdrawal flow**: Off-chain EIP-712 signed message (`withdraw3` action type) POSTed to Hyperliquid REST API. Zero gas. Uses `useSignTypedData` with the same domain as authorize. Funds arrive on Arbitrum in ~3-4 minutes.

**market_open response gotcha**: Top-level `status: "ok"` does NOT mean the order was filled. Must check `response.data.statuses[]` for `"filled"` objects (success) or `"error"` strings (rejection). Initial test with 0.001 ETH silently failed — likely below minimum notional. 0.01 ETH works reliably.

**MetaMask display**: The `verifyingContract: 0x0000...` shows as "null:0x0..." in MetaMask — this is cosmetic only, correct for Hyperliquid's off-chain signing pattern.

#### Backend Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v2/hyperliquid/setup` | POST | Store API wallet key + wallet address, verify account exists via `user_state()` |
| `/api/v2/hyperliquid/status` | GET | Return connection status + live balance/positions from Hyperliquid Info API |
| `/api/v2/hyperliquid/disconnect` | POST | Delete Vault secret, null profile columns, set all HL bots to paper mode |
| `/api/v2/hyperliquid/test-trade` | POST | Open 0.01 ETH long at 3x, wait 2s, close. Returns entry price + close status |

---

### Phase 2: Forge Integration (~6-10 hours)

**Goal**: Users can select `trading_mode='hyperliquid'` in the Forge bot configuration UI.

#### 2a. Trading Mode Selector

**File**: `frontend/app/forge/components/configure/TradeSettings.tsx`

Add `hyperliquid` option alongside `paper`/`symphony`/`aster`:
- Check Hyperliquid connection status via `/api/v2/hyperliquid/status`
- If not connected, show link to `/hyperliquid` setup page
- If connected, show account balance + allocation indicator
- **Account allocation indicator**: Show how much of the user's Hyperliquid account is already allocated across other live bots (e.g., "60% allocated to other bots, 40% available"). Warn if `max_margin_percent` would push total over 100%.

#### 2b. Activation Gate

Bot activation (`can_activate_bots`) already gates all live trading. Additional check: require valid Hyperliquid credentials before allowing `trading_mode='hyperliquid'` bots to activate. If credentials are missing/invalid, show clear error with link to setup page.

---

### Phase 3: Dashboard Integration (~6-8 hours)

**Goal**: Hyperliquid positions and P&L appear in existing dashboard.

#### 3a. Account Monitor Adapter

**New file**: `core/monitoring/adapters/hyperliquid_adapter.py`

Following existing adapter pattern (`paper_adapter.py`, `symphony_adapter.py`):
- Query Hyperliquid Info API for positions, account state
- Calculate margin_used, unrealized_pnl, total_equity
- Feed into `account_snapshots` table

#### 3b. SSE Dashboard Enrichment

**File**: `core/sse/dashboard_data.py`

Add Hyperliquid branch to `_enrich_live_positions_and_accounts()`:
- Query open positions from Hyperliquid Info API
- Format into standard position schema (same as Symphony enrichment)
- Tag with `source: 'hyperliquid'`

#### 3c. Frontend Position/Trade Display

**Files**:
- `PositionsTable.tsx` — Add 'hyperliquid' source type, close button routing
- `api.ts` — Add Hyperliquid position/trade API methods
- Activity timeline — Works automatically via `activities` table

---

### Phase 4: Polish + Production (~4-6 hours)

#### 4a. Error Handling
- Insufficient balance on Hyperliquid
- API wallet expired/deregistered
- Symbol not available
- Rate limit handling
- Network errors with retry

#### 4b. Telegram Publishing
- Trade entry/exit notifications (reuse existing pattern)
- Include "Live on Hyperliquid" tag

#### 4c. Agent Support
- Add Hyperliquid as trading mode for agent bots
- Agent can use `position_size_usd_override` and `leverage_override`
- MCP tools for Hyperliquid position queries

#### 4d. Documentation
- Update `trading/README.md` with Hyperliquid section
- Update `ACTIVE.md` with new trading mode
- Update `frontend/README.md` with wallet connection components

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hyperliquid API changes | Low | Medium | Pin SDK version, monitor changelog |
| User loses wallet access | Medium | High | Clear warnings, support docs |
| Testnet behavior differs from mainnet | Low | Low | Final smoke test on mainnet |
| Rate limits hit with many users | Low | Low | Per-user exchange instances, caching |
| Arbitrum USDC bridge delay | Low | Low | Show "pending" status, <1min typical |
| API wallet key compromised | Low | Medium | Vault encryption, can only trade (not withdraw) |
| Hyperliquid downtime | Low | High | Graceful degradation, paper trading fallback |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time from wallet connect to first trade | <5 minutes |
| Trade execution latency (intent → Hyperliquid) | <2 seconds |
| Position update freshness in dashboard | <5 seconds |
| Symbols available for live trading (launch) | ~100 (existing candle-supported symbols) |
| Symbols available for live trading (after expansion) | 291+ (all Hyperliquid perps + equities + commodities) |
| User setup steps | 3 (connect, deposit, authorize) |

---

## Estimated Timeline

| Phase | Effort | Status |
|-------|--------|--------|
| Phase 1: Backend service | ~8 hours | ✅ COMPLETE (2026-02-08) |
| Phase 1.5: Frontend setup + mainnet test | ~4 hours | ✅ COMPLETE (2026-02-09) |
| Phase 2: Forge integration | 6-10 hours | ✅ COMPLETE (2026-02-09) |
| Phase 3: Dashboard integration | 6-8 hours | ✅ COMPLETE (2026-02-09) |
| Phase 4: Polish + production | 4-6 hours | ✅ COMPLETE (2026-02-11) |
| **Total** | **~28-36 hours** | |

Phase 2 and Phase 3 can be developed in parallel.
Phase 1.5 was originally scoped as a manual test but evolved into the full frontend setup page (deposit, withdraw, authorize, test trade) — pulling forward most of the planned Phase 2 wallet/deposit work.

---

## Future Enhancements (Post-Launch)

These features build on top of the core Hyperliquid integration (Phases 1-4). Detailed planning will be done when we arrive at each step.

### Symbol & Candle Expansion

**Goal**: Unlock Hyperliquid's full 291+ market catalog including US equities (AAPL, TSLA, etc.) and commodities (gold, silver) added via HIP-3.

**Why it's separate**: Our current candle pipeline (`WebSocketMarketDataService`) streams from Binance WebSocket and only covers ~100 crypto symbols. Binance doesn't list equities or commodities, so we need a new data source.

**Approach**:
- Add `HyperliquidCandleAdapter` to `market_intelligence/adapters/market_data/` — fetches OHLCV directly from Hyperliquid's Info API
- Route candle requests by asset class: crypto → existing Binance pipeline, equities/commodities → Hyperliquid adapter
- Extend symbol registry with `hyperliquid_only` flag for assets not on Binance
- Update paper trading engine to support these new symbols (paper trading currently uses Binance prices)
- Consider whether these new asset classes need different default timeframes or indicator configs

### Strategy Marketplace (Copy Trading)

**Goal**: Users with consistently profitable bots can publish their strategy. Other users subscribe and their Hyperliquid accounts automatically mirror the same trades, sized relative to their own balance.

**Key concepts**:
- **Creator**: Publishes a bot strategy on the marketplace, sets subscription pricing
- **Subscriber**: Pays subscription, connects their own Hyperliquid wallet + API wallet, trades are automatically mirrored
- **Revenue split**: Creator gets a cut, ggbots takes platform fee (Stripe Connect for payouts)
- **Trade fan-out**: When a creator's bot signals a trade, the intent is replicated to all subscriber accounts with position sizing relative to each subscriber's balance

**Database additions**:
- `strategy_listings` table — published strategies, pricing, description, performance stats
- `strategy_subscriptions` table — who subscribes to what, billing status
- `strategy_trades` table — tracks fan-out execution per subscriber

**Considerations**:
- Each subscriber still needs their own Hyperliquid API wallet (ggbots trades on their behalf independently)
- Position sizing naturally scales — `confidence × max_margin_percent × subscriber_balance`
- Latency budget: creator trade → fan-out to N subscribers should add minimal delay
- Performance metrics (win rate, P&L, drawdown) must be verifiable from on-chain Hyperliquid data
- Regulatory: copy-trading where user controls their own funds (non-custodial) is generally the safest model, but jurisdiction-dependent — consult legal before launch

---

## References

- [Hyperliquid API Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)
- [Hyperliquid Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
- [Hyperliquid API Wallets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets)
- [Hyperliquid Exchange Endpoint](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint)
- [Hyperliquid Bridge2](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/bridge2)
- [Hyperliquid Rate Limits](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits)
- [Hyperliquid Testnet](https://api.hyperliquid-testnet.xyz)
- Existing ggbots patterns: `trading/live/symphony_service.py`, `trading/live/aster_service_v3.py`
