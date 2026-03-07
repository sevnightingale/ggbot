# Trading Engine

**Paper & Live Trading with Dashboard Integration**

The ggbots trading engine supports both paper trading (simulation) and live trading (real money) modes:

- **Paper Trading**: Realistic simulation using real-time market data with $10,000 isolated accounts and automated risk management
- **Live Trading**: Production trading via Symphony.io API integration with real-money execution

Both modes share the same decision engine, configuration system, and dashboard interface for seamless switching between simulation and live trading.

## Recent Updates (October 2025)

**Live Trading Launch (October 2025):**
1. **Symphony.io Integration**: Production-ready live trading with encrypted credential storage
2. **Unified Dashboard**: SSE stream enriched with Symphony data (positions, metrics, trade history)
3. **Smart Routing**: Automatic paper vs live mode routing based on `trading_mode` configuration
4. **Default SL/TP**: Config-based stop loss and take profit applied if decision doesn't provide them
5. **Position Management**: Real-time position tracking with accurate size, age, and SL/TP display
6. **Close Positions**: Manual position closing from dashboard for both paper and live modes

**Major architectural update**: The paper trading system has been migrated from direct PostgreSQL to Supabase integration with full dashboard connectivity and real-time data display.

### Key Changes Made:

**Paper Trading Engine 2.0 (October 2025):**
1. **Leverage Calculation Fix**: P&L now correctly applies leverage multiplier (5x leverage = 5x gains/losses)
2. **Margin-Based Reservations**: Account reserves margin (position_size/leverage + fees) instead of full position size
3. **Margin Release Fix**: Positions now release the correct reserved amount via new `margin_used` field
4. **Manual Position Close**: Users can manually close positions via API and frontend button
5. **Multi-Exchange Fallback**: Automatic failover across 5 exchanges for market data reliability
6. **Position Monitoring**: Real-time 3-second price updates with batch SQL optimization (99% reduction in API calls)
7. **Liquidation System**: Automatic position liquidation when losses exceed margin (realistic leveraged trading)

**Earlier Updates (September 2025):**
1. **Fixed Money Class**: Now properly handles negative amounts for trading losses (critical bug fix)
2. **Supabase Migration**: Complete migration from direct PostgreSQL to Supabase REST API
3. **Schema Alignment**: Cleaned up field mismatches between service and database schema
4. **Configuration Fix**: Fixed validation system to work with existing config types
5. **Dashboard Integration**: Full API endpoints and frontend components for real-time data

## Architecture Overview

### Paper Trading Flow
```
Decision Module → Supabase Paper Trading Service → WebSocket Market Data → Supabase DB
                          ↓                              ↓                     ↓
                  Trade Execution                  Real Prices         Position Tracking
                          ↓                              ↓                     ↓
                   Portfolio Mgmt                 7-sec Updates         P&L Calculation
                          ↓                              ↓                     ↓
              Dashboard API Endpoints ← REST API ← Background Monitor → Real-time UI
```

### Live Trading Flow
```
Decision Module → Symphony Trading Service → Symphony.io API → live_trades DB
                          ↓                          ↓                  ↓
                  Apply Config Defaults      Real Execution      Batch ID Tracking
                          ↓                          ↓                  ↓
                  Weight + Leverage          Position Open       Decision Linkage
                          ↓                          ↓                  ↓
              Dashboard SSE Stream ← Enrich with Symphony Data → Real-time UI
```

---

## Live Trading with Hyperliquid

**Production-ready non-custodial perpetual futures trading** via Hyperliquid DEX. Users connect their Ethereum wallet, deposit USDC, authorize an API wallet, and their AI bots trade 228 perpetual markets — all without custody risk.

### Key Features

- **Non-Custodial**: API wallets can trade but CANNOT withdraw (protocol-enforced by Hyperliquid)
- **228 Perp Markets**: Crypto, equities (AAPL, TSLA), commodities (gold, silver) via HIP-3
- **Up to 50x Leverage**: Flexible leverage per symbol
- **Zero KYC**: Ethereum wallet IS the account — no registration, no identity verification
- **Per-User API Wallets**: Each user's private key stored in Supabase Vault
- **Error Handling**: Retry logic for rate limits/network errors, clear messages for insufficient balance or expired credentials
- **Telegram Notifications**: Entry and exit signals published with "Live on Hyperliquid" tag

### Hyperliquid Integration Architecture

**Service Layer** (`trading/live/hyperliquid_service.py`):
```python
from trading.live.hyperliquid_service import HyperliquidLiveTradingService

service = HyperliquidLiveTradingService()

# Execute trade intent (same format as paper/Symphony/Aster)
result = await service.execute_trade_intent({
    "config_id": "uuid",
    "user_id": "uuid",
    "symbol": "BTC-USDT",
    "action": "long",
    "confidence": 0.75,
    "stop_loss_price": 95000,
    "take_profit_price": 105000
})
# Returns: {"status": "executed", "batch_id": "uuid", "entry_price": 98500.0}
```

**What Gets Applied from Config:**
1. **Position Sizing**: `confidence × max_margin_percent × total_account_value × leverage / price`
2. **Leverage**: `config.trading.leverage` (1-50x)
3. **Default SL/TP**: `config.trading.risk_management` defaults if not in decision
4. **Safety Cap**: Margin capped at 95% of available balance

**Execution Flow:**
1. Decision Module generates intent with confidence score
2. Service loads API wallet from Vault, initializes Exchange SDK
3. Queries Hyperliquid Info API for account balance
4. Calculates position size using config + confidence + balance
5. Sets leverage via `exchange.update_leverage()`
6. Places market order via `exchange.market_open()` with 5% slippage
7. Validates fill via `statuses[]` (top-level "ok" ≠ filled)
8. Places separate SL/TP trigger orders
9. Saves to `live_trades` table with `provider='hyperliquid'`
10. Retry logic: up to 2 retries for rate limits and network errors

**Error Handling:**
| Error | Category | User Message |
|-------|----------|-------------|
| Insufficient margin | `insufficient_balance` | "Deposit more USDC or reduce position size" |
| API wallet expired | `credentials_expired` | "Reconnect in Settings → Live Trading" |
| Rate limit | `rate_limit` | Automatic retry (2 attempts with exponential backoff) |
| Network error | `network` | Automatic retry, then "Network error after N attempts" |
| No fill confirmation | `no_fill` | "Check Hyperliquid dashboard" |

### Trust Model

```
User's Wallet (MetaMask, Coinbase, etc.)
  └── OWNS funds on Hyperliquid
  └── CAN deposit, withdraw, trade
  └── Signs one-time ApproveAgent transaction

ggbots API Wallet (generated keypair)
  └── CAN trade on behalf of user
  └── CAN set leverage, manage positions
  └── CANNOT withdraw funds (protocol-enforced)
  └── Private key stored in Supabase Vault
```

### Database Schema

**live_trades Table** (Shared with Symphony/Aster):
```sql
-- Key columns for Hyperliquid trades (provider='hyperliquid', batch_id is UUID)
-- Entry data written by hyperliquid_service._save_trade_record()
-- Exit data written by hyperliquid_service._mark_trade_closed() OR hyperliquid_adapter._detect_and_log_closes()
batch_id, config_id, decision_id, provider, symbol,
side,           -- 'long' | 'short'
entry_price,    -- fill price at entry
exit_price,     -- fill price at exit (NULL while open)
size_usd,       -- notional value
leverage,       -- 1-50x
realized_pnl,   -- per-trade P&L (NULL while open, set on close)
closed_at       -- NULL while open
```

**P&L Architecture**: Snapshot `total_pnl` = `SUM(realized_pnl) FROM live_trades`. Same pattern as `paper_trades`. No external API dependency for historical stats.

### Single Live Bot Slot (Phase 5)

**Model**: One permanent `trading_mode='hyperliquid'` config per user. Auto-created during Hyperliquid setup. Cannot be deleted — only deactivated on disconnect.

**Promote to Live**: Paper bot strategies copied to live slot via `POST /api/v2/bot/{config_id}/promote-to-live`. Logs `strategy_updated` activity with version number and config snapshot. Paper bot continues running for comparison.

**Equity Tracking**: Real account balance, not PnL-only.
- `total_equity = current_balance + unrealized_pnl` (same formula as paper)
- Adapter sets `current_balance = account_value` from `user_state.marginSummary`
- Dashboard shows Total Equity, Available Balance, Unrealized P&L (full equity view)

### Account Monitoring

**Adapter**: `core/monitoring/adapters/hyperliquid_adapter.py`
- Queries `Info.user_state()` for account data (118ms avg latency)
- Single live bot model: account balance = bot balance (`current_balance = account_value`)
- `total_equity = current_balance + unrealized_pnl` (same as paper mode)
- Trade stats (total/wins/losses/pnl/averages) from `live_trades` table — no fills API dependency
- Position close detection via fill monitoring with two safety paths:
  - **Primary**: `hyperliquid_service.close_position()` writes exit data to `live_trades` + logs activity
  - **Safety net**: `_detect_and_log_closes()` scans fills, aggregates partials by `(coin, fill_time)`, cross-source dedup checks `activities` table before logging

### API Endpoints

**Setup & Management** (under `/api/v2/hyperliquid/`):
- `POST /setup` — Store API wallet + wallet address, auto-create live bot config
- `GET /status` — Connection status + live balance/positions
- `POST /disconnect` — Remove credentials, preserve live slot as inactive
- `POST /test-trade` — Open 0.01 ETH long, close after 2s

**Trading**:
- `POST /api/v2/bot/{config_id}/execute` — Routes to Hyperliquid if `trading_mode='hyperliquid'`
- `POST /api/v2/bot/{config_id}/promote-to-live` — Copy paper strategy to live slot
- `GET /api/v2/bot/{config_id}/positions` — Open positions from Hyperliquid Info API
- `GET /api/v2/bot/{config_id}/account` — Account metrics
- `POST /api/v2/positions/hyperliquid/{batch_id}/close` — Close position

### Symbol Compatibility

**100 of 228 perp symbols** currently supported (limited by Binance candle pipeline).
Hyperliquid uses bare base names: "BTC", "ETH", "SOL" (no /USDT suffix).
See `core/symbols/registry.py` for `hyperliquid_compatible` flags.

### Frontend Integration

**Setup**: Settings modal → LiveTradingSetupModal (wagmi + RainbowKit on Arbitrum)
**BotRail**: Pinned live slot with 4 states — not connected, connected (no strategy), strategy promoted, disconnected (preserved slot). Gold accent, Zap icon, LIVE badge.
**Bot Creation**: Paper-only in BotCreationModal (live bot auto-created during HL setup)
**Promote to Live**: Paper bot 3-dot menu → "Promote to Live" with inline confirmation popover
**Dashboard**: ActivationBar + PerformanceChart show real equity (Total Equity, Available, Unrealized P&L)
**Positions**: PositionsTable routes close to `/api/v2/positions/hyperliquid/{batch_id}/close`
**Activation**: Credential check via VaultManager (no more per-symbol uniqueness gate)
**Strategy Versioning**: `strategy_updated` activities rendered as square markers on TV timeline chart

---

## Live Trading with Symphony.io

**Production-ready live trading** via Symphony.io API integration. Symphony is a non-custodial trading platform that executes trades on behalf of users using smart contracts.

### Key Features

- **Non-Custodial**: Users maintain control of funds via Symphony smart accounts
- **Real-Money Execution**: Trades execute on actual exchanges (Binance, OKX, etc.)
- **Encrypted Storage**: API credentials stored in Supabase Vault
- **Smart Routing**: Bot config `trading_mode: 'live'` automatically routes to Symphony
- **Unified Interface**: Same dashboard, same decision engine as paper trading
- **Position Tracking**: Real-time position data fetched from Symphony API
- **Default Risk Management**: SL/TP from config applied if decision doesn't provide them

### Symphony Integration Architecture

**Service Layer** (`trading/live/symphony_service.py`):
```python
from trading.live.symphony_service import SymphonyLiveTradingService

# Initialize service
symphony = SymphonyLiveTradingService()

# Execute trade intent (same format as paper trading)
result = await symphony.execute_trade_intent({
    "config_id": "uuid",
    "user_id": "uuid",
    "symbol": "BTC/USDT",
    "action": "long",
    "confidence": 0.75,
    "stop_loss_price": 108000,  # Optional - config defaults applied if not provided
    "take_profit_price": 115000
})
# Returns: {"status": "success", "batch_id": "symphony-batch-uuid"}
```

**What Gets Applied from Config:**
1. **Position Sizing**: `config.trading.position_sizing` (ACCOUNT_PERCENTAGE or CONFIDENCE_BASED)
2. **Leverage**: `config.trading.leverage` (min 1.1x for Symphony)
3. **Default SL**: `config.trading.risk_management.default_stop_loss_percent` (if not in decision)
4. **Default TP**: `config.trading.risk_management.default_take_profit_percent` (if not in decision)

**Execution Flow:**
1. Decision Module generates intent with confidence score
2. Symphony service fetches market price for SL/TP calculations
3. Config defaults applied if decision doesn't provide SL/TP
4. Weight calculated from confidence + config sizing strategy
5. Symphony API called with: symbol, action (LONG/SHORT), weight %, leverage, SL, TP
6. Trade settles (3-second wait) then batch_id saved to `live_trades` table
7. SSE dashboard stream enriches with Symphony position data

### Database Schema

**live_trades Table** (Lightweight Audit Trail):
```sql
CREATE TABLE live_trades (
    batch_id VARCHAR PRIMARY KEY,          -- Symphony's batch ID
    config_id UUID NOT NULL,               -- Which bot executed this
    decision_id UUID,                      -- Links to decisions table
    created_at TIMESTAMP NOT NULL,         -- When we opened it
    closed_at TIMESTAMP                    -- When we closed it (NULL if open)
);
```

**Design Philosophy**: Store only the linkage between our system and Symphony. Symphony is the source of truth for all position details (price, size, P&L, SL/TP, etc.). We query Symphony API in real-time for display.

### API Endpoints

**Trading Execution**:
- `POST /api/v2/bot/{config_id}/execute` - Execute trade (routes to Symphony if `trading_mode='live'`)

**Position Management**:
- `GET /api/v2/positions/live/{config_id}` - Get open positions from Symphony
- `POST /api/v2/positions/live/{batch_id}/close` - Close position via Symphony API

**Metrics & Analytics**:
- `GET /api/v2/account/live/{config_id}` - Account metrics from Symphony batches
- `GET /api/v2/trades/live/{config_id}` - Closed trade history from Symphony

**Dashboard Integration**:
- `GET /api/dashboard-stream` - SSE stream enriched with Symphony data for live bots

**Activity Timeline** (2025-11-13):
- `GET /api/v2/activities/{config_id}/balance-series` - P&L chart from Symphony trade history
- `GET /api/v2/activities/{config_id}/metadata` - Win rate, trades, P&L from Symphony API
- `GET /api/v2/activities/{config_id}` - Activity feed (universal, works for all modes)

### Symphony Data Enrichment

The SSE dashboard stream automatically enriches live bot data via `_enrich_live_positions_and_accounts()`:

**For Live Positions** (`core/sse/dashboard_data.py`):
```python
# Database returns placeholder with batch_id (NULL fields)
# Symphony API queried via get_open_positions() for full details:
{
    "position_id": "batch-uuid",
    "symbol": "BTC-USDT",
    "side": "long",
    "size_usd": 8.19,               # From Symphony positionSize (notional)
    "collateral": 7.45,             # From Symphony collateralAmount (actual margin)
    "entry_price": 86365.31,        # From Symphony entryPrice
    "current_price": 87684.59,      # From Symphony currentPrice
    "unrealized_pnl": 0.12,         # From Symphony pnlUSD
    "pnl_percentage": 1.68,         # From Symphony pnlPercentage
    "opened_at": "2025-12-17T10:04:50.432Z",  # Symphony createdTimestamp
    "stop_loss": 82058.49,          # From Symphony slPrice (if set)
    "take_profit": 95015.10,        # From Symphony tpPrice (if set)
    "liquidation_price": 29091.12,  # From Symphony liquidationPrice
    "leverage": 1.1,                # From Symphony leverage
    "status": "Open",               # From Symphony status (Open/Closed/Liquidated)
    "source": "symphony"            # Tags for frontend routing
}
```

**Key Fields** (from `/agent/positions` endpoint):
| Field | Symphony Field | Description |
|-------|---------------|-------------|
| `collateral` | `collateralAmount` | Actual margin used (divide size_usd by leverage) |
| `size_usd` | `positionSize` | Total notional position size |
| `pnl_percentage` | `pnlPercentage` | P&L as percentage |
| `liquidation_price` | `liquidationPrice` | Auto-liquidation price |
| `status` | `status` | Open, Closed, or Liquidated |

**For Account Metrics** (`core/monitoring/adapters/symphony_adapter.py`):
- Queries `/agent/positions` for open positions count
- Sums `collateralAmount` for total margin used (`margin_used` in account_snapshots)
- Queries `/agent/batches` for closed trade history
- Calculates win/loss, total P&L from batch results
- **Note**: Balance not available (users track on Symphony dashboard)

### Symbol Compatibility

**100 of 141 symbols** compatible with Symphony:
- **Compatible**: BTC, ETH, SOL, LINK, DOGE, AVAX, UNI, etc. (major pairs)
- **Not Compatible**: Some smaller altcoins
- Symphony compatibility checked before trade execution
- See `core/symbols/registry.py` for full compatibility mapping

---

## Live Trading with AsterDEX

**Production-ready decentralized futures trading** via AsterDEX v3 API. Built for the Vibe Trading Competition ($50,000 ASTER token prize).

### Key Features

- **Decentralized Futures**: Non-custodial perpetuals trading on blockchain
- **Web3 Authentication**: ECDSA signature-based authentication (no traditional API keys)
- **High Leverage**: Up to 20x leverage for maximizing competition volume
- **Real-Money Execution**: Mainnet trading with USDT/USDC collateral
- **Direct Credentials**: Stored in .env (Pro API private key model)
- **Smart Routing**: Bot config `trading_mode: 'aster'` automatically routes to AsterDEX
- **Unified Interface**: Same dashboard, same decision engine as paper/Symphony trading
- **Position Management**: Real-time position queries and market closes
- **Dynamic Position Sizing**: Respects config sizing methods with balance-aware calculations

### AsterDEX Integration Architecture

**Service Layer** (`trading/live/aster_service_v3.py`):
```python
from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService

# Initialize service
aster = AsterDEXV3LiveTradingService()

# Execute trade intent (same format as paper/Symphony trading)
result = await aster.execute_trade_intent({
    "config_id": "uuid",
    "user_id": "uuid",
    "symbol": "BTC-USDT",  # Platform format
    "action": "long",
    "confidence": 0.75,
    "stop_loss_price": 108000,  # Optional - defaults applied if not provided
    "take_profit_price": 115000
})
# Returns: {"status": "success", "batch_id": "7086939384"}  # AsterDEX order ID
```

**What Gets Applied from Config:**
1. **Position Sizing**: Queries AsterDEX account balance, calculates position size from config method (ACCOUNT_PERCENTAGE, CONFIDENCE_BASED, FIXED_USD)
2. **Leverage**: `config.trading.leverage` (default 10x for testing, up to 20x supported)
3. **Default SL/TP**: `config.trading.risk_management` defaults applied if not in decision
4. **Safety Caps**: Automatically reduces position if margin exceeds 95% of available balance

**Execution Flow:**
1. Decision Module generates intent with confidence score
2. Service validates symbol compatibility (33 symbols supported)
3. Queries AsterDEX account balance (USDT margin)
4. Calculates position size using config method + confidence + balance
5. Validates against minimums (0.001 BTC) and balance caps (95% max margin)
6. Converts symbol to Aster format (BTC-USDT → BTCUSDT)
7. Places market order with Web3 ECDSA signature
8. Optional: Places SL/TP conditional orders (STOP_MARKET, TAKE_PROFIT_MARKET)
9. Saves order ID to `live_trades` table with `provider='aster'`
10. Dashboard displays real-time position data

### Web3 Authentication

AsterDEX uses **blockchain-style authentication** instead of traditional HMAC:

**Authentication Flow:**
```python
# 1. Create sorted JSON string of parameters
params_json = '{"quantity":"0.001","side":"BUY","symbol":"BTCUSDT",...}'

# 2. ABI encode with user, signer, nonce
from eth_abi import encode
from web3 import Web3
encoded = encode(['string', 'address', 'address', 'uint256'],
                 [params_json, user_wallet, signer_wallet, nonce])

# 3. Keccak hash
keccak_hex = Web3.keccak(encoded).hex()

# 4. ECDSA sign with private key
from eth_account import Account
from eth_account.messages import encode_defunct
signable_msg = encode_defunct(hexstr=keccak_hex)
signed_message = Account.sign_message(signable_msg, private_key)
signature = '0x' + signed_message.signature.hex()

# 5. Include in request
params = {
    "user": "0x4a24...",      # Main wallet (holds funds)
    "signer": "0xD322...",    # Pro API agent wallet
    "nonce": 1730595234567890,  # Microsecond timestamp
    "signature": signature
}
```

**Three-Wallet System:**
- **User Wallet**: Your main ERC20 wallet (funds stored here)
- **Signer Wallet**: Pro API agent (authorized to trade, cannot withdraw)
- **Private Key**: ECDSA key for signer wallet (signs API requests)

### Dynamic Position Sizing

**Real-Time Balance Query:**
```python
# Queries AsterDEX account balance before each trade
balance_data = await service._get_account_balance()  # GET /fapi/v3/balance

# IMPORTANT: availableBalance is the account balance (source of truth)
# This includes wallet balance + unrealized P&L + cross-margin equity
usdt_balance = balance_data['USDT']['availableBalance']  # e.g., $206.80

# balance field is ONLY settled balance (excludes unrealized P&L)
settled_only = balance_data['USDT']['balance']  # e.g., $10.66

# Calculates position size based on config method using availableBalance
position_size_usd = config.get_position_size(confidence=0.75, balance=usdt_balance)
# Example: ACCOUNT_PERCENTAGE 10% of $206.80 → $20.68 position

# Converts to base asset quantity
quantity_btc = position_size_usd / btc_price  # e.g., 0.001 BTC minimum
```

**Balance Fields Explained:**
- **`crossWalletBalance`**: **TOTAL EQUITY** (settled balance + unrealized P&L). **This is the source of truth for charts/performance.**
- **`availableBalance`**: Free cash available for trading (not locked in positions)
- **`balance`**: Settled balance only (excludes unrealized P&L from open positions)
- **`crossUnPnl`**: Unrealized P&L from open positions

**Position Sizing Examples:**

| Config Method | Balance | Confidence | Leverage | Calculation | Margin Required |
|---------------|---------|------------|----------|-------------|-----------------|
| ACCOUNT_PERCENTAGE (10%) | $1,000 | 0.75 | 5x | $100 margin × 5x = $500 position | $100 |
| CONFIDENCE_BASED (15% max) | $1,000 | 0.80 | 10x | 0.8 × 15% × $1000 = $120 margin × 10x | $120 |
| FIXED_USD ($50) | $1,000 | 0.75 | 3x | $50 margin × 3x = $150 position | $50 |

**Safety Features:**
- Validates against AsterDEX minimums (0.001 BTC for BTCUSDT)
- Caps margin at 95% of available balance
- Falls back to minimum quantity if calculated size too small
- Adjusts quantity to fit balance constraints

### Agent Position Size Overrides

**NEW**: Agents can override position sizing for intelligent risk management:

```python
# Agent decides: "High conviction trade, use larger position"
intent = {
    "symbol": "BTC-USDT",
    "action": "long",
    "confidence": 0.95,
    "position_size_usd_override": 1000,  # NOTIONAL: $1000 total position size
    "leverage_override": 15,              # 15x leverage
    "stop_loss_price": 108000,
    "take_profit_price": 115000
}
# Result: $1000 position @ 15x leverage
#         Margin required: $1000 / 15 = $66.67 (actual capital at risk)

# Agent decides: "Uncertain market, use smaller position"
intent = {
    "symbol": "ETH-USDT",
    "action": "short",
    "confidence": 0.60,
    "position_size_usd_override": 100,   # NOTIONAL: $100 total position size
    "leverage_override": 2,               # 2x leverage (conservative)
    "stop_loss_price": 4100,
    "take_profit_price": 3900
}
# Result: $100 position @ 2x leverage
#         Margin required: $100 / 2 = $50 (actual capital at risk)
```

**IMPORTANT: `position_size_usd_override` is the TOTAL POSITION SIZE (notional), NOT the margin.**
- To calculate actual capital at risk: `margin = position_size_usd / leverage`
- Example: $1000 position with 10x leverage = $100 margin required
- Example: $500 position with 5x leverage = $100 margin required

**Override Validation:**
- Checks against available balance (95% max margin)
- Enforces exchange minimums (0.001 BTC)
- Clamps leverage to exchange limits (1-20x for Aster)
- Falls back to config sizing if override invalid

### Database Schema

**live_trades Table** (Shared with Symphony):
```sql
CREATE TABLE live_trades (
    batch_id VARCHAR PRIMARY KEY,          -- AsterDEX order ID (e.g., "7086939384")
    config_id UUID NOT NULL,               -- Which bot executed this
    decision_id UUID,                      -- Links to decisions table
    provider VARCHAR(20) NOT NULL,         -- 'aster' | 'symphony' | 'binance'
    stop_loss_order_id VARCHAR(50),        -- AsterDEX SL order ID (if placed)
    take_profit_order_id VARCHAR(50),      -- AsterDEX TP order ID (if placed)
    created_at TIMESTAMP NOT NULL,         -- When we opened it
    closed_at TIMESTAMP                    -- When we closed it (NULL if open)
);

-- Provider-aware indexes
CREATE INDEX idx_live_trades_provider ON live_trades(provider, config_id);
CREATE INDEX idx_live_trades_provider_open ON live_trades(provider, config_id, closed_at)
    WHERE closed_at IS NULL;
```

**Design Philosophy**: Multi-exchange support with shared table. `provider` field distinguishes between AsterDEX, Symphony, and future integrations (Binance, Bybit, dYdX).

### API Endpoints

**Trading Execution**:
- `POST /api/v2/bot/{config_id}/execute` - Execute trade (routes to Aster if `trading_mode='aster'`)
- `POST /api/v2/agent/execute-trade` - Agent execution with optional position size/leverage overrides

**Position Management**:
- `GET /api/v2/positions/aster/{config_id}` - Get open positions from AsterDEX API
- `POST /api/v2/positions/aster/{order_id}/close` - Close position via market order

**Metrics & Analytics**:
- `GET /api/v2/account/aster/{config_id}` - Account balance and position metrics
- `GET /api/v2/trades/aster/{config_id}` - Closed trade history

**Activity Timeline** (2025-11-13):
- `GET /api/v2/activities/{config_id}/balance-series` - P&L chart from Aster API + paper trades
- `GET /api/v2/activities/{config_id}/metadata` - Balance, win rate, trades from Aster API
- `GET /api/v2/activities/{config_id}` - Activity feed (universal, works for all modes)

### Symbol Compatibility

**33 of 142 symbols** compatible with AsterDEX:

**Multi-Exchange (available on BOTH Symphony AND Aster):**
```
AAVEUSDT    ADAUSDT     APEUSDT     APTUSDT     ARBUSDT
ATOMUSDT    AVAXUSDT    BCHUSDT     BNBUSDT     BTCUSDT
CAKEUSDT    DASHUSDT    DOGEUSDT    DOTUSDT     DYDXUSDT
ENAUSDT     ETCUSDT     ETHUSDT     GALAUSDT    INJUSDT
LINKUSDT    LTCUSDT     NEARUSDT    ONDOUSDT    OPUSDT
PYTHUSDT    SEIUSDT     SOLUSDT     TRXUSDT     WLDUSDT
XRPUSDT
```

**Aster-Only (not on Symphony):**
```
CRVUSDT     SUIUSDT
```

- AsterDEX compatibility checked before trade execution
- See `core/symbols/registry.py` for full compatibility mapping with `aster_compatible` flags
- Additional Aster symbols can be added to registry as needed

### Configuration Setup

**1. Environment Variables** (`.env`):
```bash
# AsterDEX Pro API Credentials (Web3 ECDSA)
ASTER_USER_WALLET=0xREDACTED_TREASURY_WALLET      # Main wallet (holds funds)
ASTER_WALLET_ADDRESS=0xREDACTED_TEST_WALLET  # Pro API signer wallet
ASTER_PRIVATE_KEY=0x573302a9...                                  # Pro API private key (ECDSA)
```

**2. Bot Configuration** (`configurations` table):
```json
{
    "trading_mode": "aster",                   // Routes to AsterDEX
    "trading": {
        "leverage": 10,                         // Up to 20x supported
        "position_sizing": {
            "method": "ACCOUNT_PERCENTAGE",     // Dynamic sizing
            "account_percent": 10.0             // 10% of balance per trade
        },
        "risk_management": {
            "default_stop_loss_percent": 1.5,   // Applied if decision doesn't provide
            "default_take_profit_percent": 3.0
        }
    }
}
```

### Testing & Validation

**Test Live Trade Execution**:
```bash
# Test full trade cycle (open + close)
python scripts/test_aster_live_trade.py --confirm

# Expected output:
# ✅ BTC-USDT LONG executed: 0.001 BTC @ $110,269.70 (Order: 7086939384)
# ✅ Position closed @ $110,197.16 (Order: 7087174440)
# P&L: -$0.07 (-0.066% price movement)
```

**Test Position Sizing**:
```bash
# Test dynamic sizing with different configs
python scripts/test_aster_position_sizing.py

# Expected output:
# Available balance: $9.84
# ACCOUNT_PERCENTAGE 10%: $0.98 target → 0.001 BTC (minimum)
# CONFIDENCE_BASED 15%: $1.48 target → 0.001 BTC (minimum)
# Safety cap: Margin $11.00 exceeds balance, reduced to 0.001 BTC
```

**Test Symphony Integration**:
```bash
# Close any open Aster positions
python scripts/close_aster_position.py --confirm

# Cross-reference compatible symbols
python scripts/cross_reference_aster_symbols.py
```

### Production Considerations

**Credential Security**:
- ✅ Stored in .env (not exposed in API responses)
- ✅ Web3 ECDSA signatures (no API key leakage)
- ✅ Signer wallet cannot withdraw funds (only trade)

**Competition Strategy**:
- **Objective**: Maximize trading volume for $50k ASTER prize
- **Approach**: 24/7 automated trading with AI decisions
- **Leverage**: Use higher leverage (10-15x) for competition volume
- **Multi-Symbol**: Deploy bots across multiple symbols (BTC, ETH, SOL)
- **Risk Management**: Tight SL/TP for quick exits and re-entries

**Error Handling**:
- Failed trades return graceful errors to decision engine
- Symbol validation prevents incompatible trades
- Balance checks prevent over-leveraged positions

**Rate Limits** (AsterDEX API):
- 2400 requests/minute (weight-based)
- 1200 orders/minute
- 300 orders/10 seconds
- Service respects limits with exponential backoff

**Known Limitations**:
- SL/TP conditional orders implemented but not tested live
- Dashboard enrichment pending (manual API queries for now)
- Frontend integration pending (Aster mode selector, credentials UI)

### Live Trading Results

**Mainnet Validation** (2025-11-02):
- ✅ Trade 1 (OPEN): 0.001 BTC LONG @ $110,269.70 (Order: 7086939384)
- ✅ Trade 2 (CLOSE): @ $110,197.16 (Order: 7087174440)
- P&L: -$0.07 (0.066% price movement)
- **Status**: Full integration operational on mainnet

---

### Configuration Setup

**1. Bot Configuration** (`configurations` table):
```json
{
    "trading_mode": "live",                    // Routes to Symphony
    "symphony_agent_id": "symphony-uuid",      // User's Symphony agent
    "trading": {
        "leverage": 1.5,
        "position_sizing": {
            "method": "CONFIDENCE_BASED",
            "max_position_percent": 10.0
        },
        "risk_management": {
            "default_stop_loss_percent": 1.5,   // Applied if decision doesn't provide
            "default_take_profit_percent": 3.0
        }
    }
}
```

**2. User Credentials** (Supabase Vault):
```python
# Stored encrypted in vault.secrets table
{
    "user_id": "uuid",
    "api_key": "sk_live_...",           // Symphony API key
    "smart_account": "0x..."            // Symphony smart account address
}
```

### Frontend Integration

**Smart Routing** (`PerformanceChart.tsx`, `PositionsTable.tsx`):
```typescript
// Detects live vs paper mode from account.source
const isLive = account?.source === 'live'

// Routes to correct endpoint
if (isLive) {
    const trades = await apiClient.getLiveTradeHistory(configId)
} else {
    const trades = await apiClient.getTradeHistoryWithDecisions(configId)
}

// Close position routing
const handleClose = async (positionId: string, source: 'paper' | 'live') => {
    if (source === 'live') {
        await fetch(`/api/v2/positions/live/${positionId}/close`, { method: 'POST' })
    } else {
        await apiClient.closePosition(configId, positionId)
    }
}
```

**Display Differences**:
- **Balance**: Shows "Track on Symphony" (not available from API)
- **Return %**: Shows "N/A" (can't calculate without balance)
- **Chart Title**: "Cumulative P&L" (instead of "Performance Chart")
- **Chart Y-axis**: Starts from $0, shows cumulative P&L from trades

### Testing & Validation

**Test Symphony Integration**:
```bash
# Test Symphony credentials
python scripts/test_symphony_metrics.py --user-id <uuid> --config-id <uuid>

# Expected output:
# ✅ Retrieved 0 open positions from Symphony
# ✅ Retrieved 5 batches from Symphony
# ✅ Symphony metrics: 1 trades, 0.0% win rate, $-0.00 P&L
```

**Test Live Trading Flow**:
```bash
# 1. Ensure bot is configured with trading_mode='live' and symphony_agent_id
# 2. Run bot's decision cycle
# 3. Decision generates intent → Symphony service executes
# 4. Check live_trades table for batch_id
# 5. Dashboard should show position in real-time
```

### Production Considerations

**Credential Security**:
- ✅ Encrypted storage via Supabase Vault
- ✅ Never logged or exposed in API responses
- ✅ User-specific isolation (users can only access their own credentials)

**Error Handling**:
- Symphony API failures return graceful errors to decision engine
- Failed trades don't break bot execution
- Dashboard SSE continues working if Symphony temporarily unavailable

**Rate Limits**:
- Symphony position queries cached in SSE (5-second intervals)
- Trade execution has 3-second settlement wait
- No aggressive polling - data fetched only when needed

**Cost Considerations**:
- Symphony charges transaction fees on live trades
- Users responsible for maintaining Symphony account balance
- No additional ggbots fees for live trading feature

---

## Core Components

### MarketDataAdapter (`trading/paper/market_data.py`)
Real-time market data via Binance WebSocket service with Redis caching.

**Features:**
- **Binance WebSocket**: Primary source for all 141 supported cryptocurrency pairs (via market-data-ws PM2 service)
- **Symbol Conversion**: Automatic translation between internal formats via UniversalSymbolStandardizer
- **Price Caching**: 30-second TTL for efficient API usage
- **Realistic Spreads**: 0.05% bid/ask spread simulation for paper trading
- **Batch Processing**: Multiple symbol price fetching for performance

**Key Methods:**
```python
# Get current market price with bid/ask spread
price = await adapter.get_current_price('BTC/USDT')
# Returns: MarketPrice(bid=111036.95, ask=111148.05, mid=111092.50)

# Get trading rules (min order size, tick size, etc.)
rules = await adapter.get_trading_rules('BTC/USDT')

# Batch price fetching for multiple symbols
prices = await adapter.get_multiple_prices(['BTC/USDT', 'ETH/USDT'])
```

### SupabasePaperTradingService (`trading/paper/supabase_service.py`)
**NEW**: Supabase-integrated core execution engine for paper trades.

### PaperTradingService (`trading/paper/service.py`)  
**LEGACY**: Original PostgreSQL-based service (kept for reference).

**Features:**
- **Account Management**: Isolated $10k account per config_id
- **Confidence-Based Sizing**: Position size = confidence × max_position_size (10% of balance)
- **Realistic Fees**: 0.06% taker fee on all trades
- **Risk Limits**: Max 5 positions, 10x leverage, position limits
- **Automated Risk Management**: Stop loss and take profit execution

**Trade Lifecycle:**
1. **Intent Processing**: Accepts Decision Module trade intents
2. **Market Data**: Fetches current price from WebSocket cache (Redis)
3. **Position Sizing**: Calculates size based on confidence score
4. **Execution**: Creates paper trade with realistic fill prices
5. **Monitoring**: Real-time P&L updates every 7 seconds
6. **Risk Management**: Automatic stop/take profit execution

**Key Methods (Supabase Service):**
```python
# Initialize Supabase service
from trading.paper.supabase_service import SupabasePaperTradingService
service = SupabasePaperTradingService()

# Execute trade from Decision Module intent
result = await service.execute_trade_intent(intent_dict)
# Returns: {"status": "executed", "trade_id": "uuid", "size_usd": 650.0}

# Close position manually or via triggers
result = await service.close_position(trade_id, reason='manual')

# Update all position prices (called by background task)
updated_count = await service.update_position_prices(config_id)

# Get account summary for dashboard
summary = await service.get_account_summary(config_id)

# Get open positions for dashboard  
positions = await service.get_open_positions(config_id)

# Get trade history
trades = await service.get_trade_history(config_id, limit=100)
```

### PositionManager (`trading/paper/positions.py`)
Advanced portfolio analytics and position tracking.

**Features:**
- **Portfolio Metrics**: Total P&L, win rate, exposure analysis
- **Risk Analytics**: Concentration risk, drawdown analysis, position limits
- **Performance Tracking**: Trade statistics, confidence score correlation
- **Position Suggestions**: AI-powered risk management recommendations

**Key Methods:**
```python
# Get comprehensive portfolio overview
portfolio = await manager.get_portfolio_summary(config_id)
# Returns: PortfolioSummary with balance, P&L, win rate, etc.

# Get detailed risk metrics
risk_metrics = await manager.get_position_risk_metrics(config_id)

# Performance analytics with trade breakdown
analytics = await manager.get_performance_analytics(config_id, days=30)
```

## Database Schema

### paper_accounts
Isolated trading accounts with $10,000 starting balance per config_id.
- **Isolation**: Each strategy gets independent paper account
- **Performance Tracking**: Win rate, total trades, cumulative P&L
- **Balance Management**: Real-time available balance updates

### paper_trades
Position tracking with real-time P&L calculation (V2.0 with leverage fixes).
- **Trade Lifecycle**: Open → monitoring → closed
- **Leverage Support**: Stores leverage multiplier and calculates correct P&L
- **Margin Tracking**: `margin_used` field tracks actual reserved amount for accurate release
- **Risk Management**: Stop loss and take profit levels with leveraged execution
- **Decision Integration**: Links to Decision Module via decision_id (ENTRY decision only)
- **Confidence Tracking**: Preserves AI confidence scores

**CRITICAL: Decision Linkage**
- `decision_id` stores the **ENTRY decision** that created the trade
- EXIT decisions UPDATE the trade row (closed_at, close_reason) but `decision_id` stays unchanged
- To trace exit execution: query `activities` table by time, NOT by joining decisions on decision_id
- `close_reason='position_management'` means "LLM exit decision executed" (not a separate monitoring system)

### paper_orders
Complete audit trail of all paper orders.
- **Order Types**: Market entry, stop loss, take profit
- **Fee Tracking**: Realistic 0.06% taker fees
- **Execution Records**: Fill prices, sizes, timestamps

## API Endpoints

**UPDATED**: All endpoints now use Supabase backend and are integrated into main API at `/api/v2/bot/*`.

### Dashboard Integration (V2.0)
- `GET /api/v2/bot/{config_id}/metrics` - Performance metrics with P&L data for dashboard charts
- `GET /api/v2/bot/{config_id}/positions` - Live positions formatted for dashboard tables (with correct leverage P&L)
- `GET /api/v2/bot/{config_id}/trades` - Closed trade history for dashboard
- `GET /api/v2/bot/{config_id}/account` - Account summary and statistics
- `POST /api/v2/bot/{config_id}/positions/{trade_id}/close` - **NEW**: Manually close any open position

### Legacy Paper Trading Endpoints (if still needed)
- `POST /paper/execute` - Execute trade from Decision Module intent
- `POST /paper/close/{trade_id}` - Close position manually
- `POST /paper/update-prices` - Trigger position price updates
- `GET /paper/positions/{config_id}` - Get open positions with real-time P&L
- `GET /paper/account/{config_id}` - Get account summary and performance
- `GET /paper/history/{config_id}` - Get closed trade history
- `GET /paper/health` - Service health check and diagnostics

### Dashboard Data Format
```json
{
  "status": "success",
  "config_id": "uuid",
  "metrics": {
    "profit_loss_data": [{"date": "2025-09-09", "profit": -0.30}],
    "trade_stats": {
      "totalTrades": 5,
      "winRate": 0.0,
      "totalProfit": -0.30
    },
    "account_balance": 9900.02,
    "total_pnl": -0.18,
    "initial_balance": 10000.0
  }
}
```

## Configuration

### Environment Variables
```bash
# Paper Trading Settings (uses WebSocket market data service)
REDIS_HOST="localhost"                 # Redis for WebSocket price cache
REDIS_PORT="6379"                      # Redis port

# Optional Configuration
PAPER_TRADING_URL="http://localhost:8000/paper/execute"  # Custom endpoint URL
```

### Service Configuration
```python
# PaperTradingService defaults
initial_balance = 10000.00      # $10k starting balance
max_position_pct = 0.10          # 10% max position size  
taker_fee = 0.0006              # 0.06% trading fee
max_leverage = 10               # Maximum leverage allowed
max_positions = 5               # Maximum concurrent positions
```

## Background Processing

### Position Monitoring (3-second intervals)
Automated real-time position management running as background task.

**Features:**
- **Price Updates**: Fetches current market prices every 3 seconds
- **P&L Calculation**: Updates unrealized P&L with correct leverage multiplier for all open positions
- **Risk Management**: Automatically triggers stop loss and take profit orders with leveraged P&L
- **Batch Optimization**: Single SQL query updates 100+ positions (99% reduction from individual HTTP requests)
- **Performance**: Reliable monitoring with ConnectionTerminated errors eliminated

**Automatic Execution:**
```python
# Liquidation Triggers (checked first - highest priority)
if side == "long" and current_price <= liquidation_price:
    await close_position(trade_id, "liquidation", current_price)

if side == "short" and current_price >= liquidation_price:
    await close_position(trade_id, "liquidation", current_price)

# Stop Loss Triggers
if side == "long" and current_price <= stop_loss:
    await close_position(trade_id, "stop_loss", current_price)

if side == "short" and current_price >= stop_loss:
    await close_position(trade_id, "stop_loss", current_price)

# Take Profit Triggers
if side == "long" and current_price >= take_profit:
    await close_position(trade_id, "take_profit", current_price)

if side == "short" and current_price <= take_profit:
    await close_position(trade_id, "take_profit", current_price)
```

## Integration with Decision Module

The paper trading engine integrates seamlessly with the existing Decision Module via the webhook pattern.

### Trade Intent Flow
```python
# Decision Module generates intent
intent = {
    "decision_id": "uuid",
    "user_id": "uuid", 
    "config_id": "uuid",
    "symbol": "BTC/USDT",
    "action": "long",           # or "short"
    "confidence": 0.75,         # 0.0 to 1.0
    "stop_loss_price": 108000,  # Optional
    "take_profit_price": 115000, # Optional
    "reasoning": "Strong breakout signal with volume confirmation"
}

# Paper trading executes automatically
# Position size: 0.75 × 10% × $10k = $750
# Entry: BTC @ $111,092 (mid-price from WebSocket cache)
# Result: 0.00675 BTC position with automated risk management
```

### Decision Module Integration (IMPORTANT FOR OTHER DEVELOPERS)

**UPDATED**: Decision Module should now use the new Supabase service:

```python
# NEW: Use Supabase service directly
from trading.paper.supabase_service import SupabasePaperTradingService

async def trigger_paper_trading(intent_dict):
    service = SupabasePaperTradingService()
    result = await service.execute_trade_intent(intent_dict)
    return result

# OR: Use REST API endpoint (if preferred)
paper_trading_url = "http://localhost:8000/api/v2/bot/{config_id}/execute"
response = await client.post(paper_trading_url, json=intent)
```

**Key Changes for Decision Module Developers:**
1. **New Service Class**: Use `SupabasePaperTradingService` instead of `PaperTradingService`
2. **Money Class Fixed**: Trading losses now work properly (negative P&L supported)
3. **Config Loading Fixed**: Existing configs with `config_type: 'autonomous_trading'` now load correctly
4. **Account Creation**: Paper accounts are auto-created on first trade execution
5. **Real-time Data**: All trades immediately appear in dashboard with live P&L updates

## Symbol Support

**All 141 cryptocurrency pairs** supported via Binance WebSocket:
- **Major Pairs**: BTC/USDT, ETH/USDT, SOL/USDT, etc.
- **Symbol Conversion**: Automatic format translation via UniversalSymbolStandardizer
- **Trading Rules**: Real-time min order sizes, tick sizes from exchange APIs

## Performance Characteristics

### Resource Usage
- **Memory**: ~15KB per update cycle (flat, no accumulation)
- **API Calls**: Minimal - prices cached in Redis from WebSocket stream
- **Database**: Simple UPDATE queries, indexed by trade_id
- **CPU**: Minimal for price comparisons and P&L calculations

### Execution Performance (V2.0)
- **Trade Execution**: <2 seconds from Decision Module intent to database
- **Position Updates**: Every 3 seconds for responsive risk management
- **Stop/Take Profit**: ≤3 second reaction time to market triggers with correct leverage
- **Batch Optimization**: 100+ positions updated in single SQL query
- **Concurrent Support**: 100+ positions across multiple strategies simultaneously

## Monitoring & Health Checks

### Service Health
```bash
# Check paper trading service health
curl http://localhost:8000/paper/health

# Response includes:
# - Market data adapter connectivity
# - Database connection status  
# - Cache statistics
# - Error diagnostics
```

### Position Monitoring
```sql
-- View real-time position summary
SELECT * FROM paper_trading_summary WHERE config_id = 'your-config-id';

-- Check background task performance
SELECT COUNT(*) as open_positions, 
       SUM(unrealized_pnl) as total_unrealized_pnl,
       AVG(confidence_score) as avg_confidence
FROM paper_trades 
WHERE status = 'open';
```

## Testing & Validation

### Connectivity Testing
```bash
# Test WebSocket market data service
pm2 status market-data-ws

# Test Redis price cache
redis-cli GET "price:BTCUSDT"

# Expected: Valid JSON with bid/ask/timestamp
```

### End-to-End Testing (UPDATED)
```bash
# Test Supabase service directly
python test_supabase_paper_service.py

# Test API endpoints
python test_paper_trading_api.py

# Test trade execution with real data
curl -X POST http://localhost:8000/api/v2/bot/{config_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "04b4a272-8303-4770-a536-6d210b9defba",
    "user_id": "00000000-0000-0000-0000-000000000000",
    "symbol": "BTC/USDT",
    "action": "long",
    "confidence": 0.75
  }'

# Check dashboard data
curl http://localhost:8000/api/v2/bot/{config_id}/metrics
curl http://localhost:8000/api/v2/bot/{config_id}/positions  
curl http://localhost:8000/api/v2/bot/{config_id}/account
```

### Current Testing Status (October 2025 - V2.0)
**✅ WORKING (Paper Trading Engine 2.0)**:
- Trade execution with correct leverage calculations (5x = 5x gains/losses)
- Margin-based balance reservations (position_size/leverage + fees)
- Manual position closing via API and frontend
- Account creation and accurate P&L tracking
- Supabase database integration with `margin_used` field
- Dashboard API endpoints with leveraged P&L display
- Background position monitoring (3-second intervals, batch SQL optimization)
- Stop loss and take profit execution with correct leverage
- Multi-exchange fallback (5 exchanges: kucoin→binance→okx→gate_io→ascend_ex)

**✅ TESTED (V2.0)**:
- Leverage P&L calculations: 5x leverage correctly multiplies gains/losses
- Margin reservations: $700 position at 5x reserves $140.84 (not $704.20)
- Position closing: Releases correct margin amount via `margin_used` field
- Balance reconciliation: All trades maintain correct balances with fees
- Manual close functionality: API and frontend button working
- Multiple test scenarios: 1x to 20x leverage all calculate correctly

## Production Deployment

### Startup Sequence (V2.0)
1. **Supabase Setup**: Ensure paper_accounts, paper_trades, paper_orders tables exist (with `margin_used` field)
2. **Environment Setup**: Configure SUPABASE_URL, SUPABASE_SERVICE_KEY, REDIS credentials
3. **Service Health**: Verify Supabase and WebSocket market data connectivity
4. **Background Task**: Position monitoring running at 3-second intervals with batch optimization
5. **API Endpoints**: Dashboard routes available at `/api/v2/bot/*` with leverage-corrected P&L

### Position Monitoring (ACTIVE)
**STATUS**: ✅ Running in production with batch SQL optimization

The position monitoring system updates all open positions every 3 seconds:
```python
# Automatically runs every 3 seconds as background task
updated_count = await service.update_position_prices()  # Updates all open positions
# Uses batch SQL: 100 positions = 1 query (99% reduction from 100 HTTP requests)
```

**Features**:
- Real-time P&L updates with correct leverage multiplier
- Automatic liquidation/SL/TP execution
- Batch SQL optimization for reliability
- Multi-exchange price fallback

### Monitoring
- **Position Updates**: Logged every ~30 seconds (consolidated logging)
- **Trade Events**: Stop/take profit executions logged immediately
- **Health Checks**: Service diagnostics via `/paper/health`
- **Performance**: Cache statistics and update metrics tracked

### Scaling Considerations
- **Multi-Strategy**: Each config_id gets isolated paper account
- **Resource Limits**: 7-second updates scale well to 100+ positions
- **API Rate Limits**: WebSocket stream eliminates REST API rate limit concerns
- **Database Performance**: Optimized indexes for position lookups

---

## Paper Trading Engine 2.0 Summary

The paper trading engine provides **professional-grade simulation** with real market data, automated risk management, and comprehensive performance analytics.

### V2.0 Key Improvements:
- ✅ **Accurate Leverage**: 5x leverage now shows 5x gains/losses (previously showed 1x)
- ✅ **Correct Margin**: Reserves position_size/leverage + fees (previously reserved full position size)
- ✅ **Manual Control**: Users can close positions anytime via frontend button
- ✅ **Reliable Monitoring**: 3-second updates with batch SQL (99% reduction in API calls)
- ✅ **Multi-Exchange**: Automatic failover across 5 exchanges for market data
- ✅ **Liquidation System**: Realistic position liquidation when losses exceed margin (critical for high leverage)

### Upcoming: Database Reset
All paper accounts will be reset to $10,000 as part of the V2.0 launch to ensure accurate simulation with the corrected leverage calculations. Bots with custom strategies will remain active; default strategy bots will be deactivated for user reconfiguration.

---

The paper trading engine integrates seamlessly with the ggbots platform while maintaining complete isolation between strategies and realistic trading conditions that prepare users for real trading.