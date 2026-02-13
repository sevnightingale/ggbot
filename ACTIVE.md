# 🚀 ACTIVE - ggbots System Status

**Last Updated**: 2026-02-13 06:36:52 UTC (Auto-updated by status_check.py)
**System Health**: 🟢 HEALTHY

## 📊 Live Platform Metrics

### Users & Subscriptions
- **Total Users**: 316
- **Prepaid Users**: 19 (19 active subscriptions)
- **Free Users**: 291
- **Users with Bots**: 306 (96.8%)

### Bot Statistics
- **Total Bots**: 473
- **Active Bots**: 24 (5.1%)
  - Paper: 23
  - Symphony (Live): 0
  - Aster (DEX): 0
- **Inactive Bots**: 449
- **Avg Bots per User**: 1.5

### Trading Activity
- **Total Trades (All Time)**: 7,136
  - Wins: 2,342
  - Losses: 4,794
  - Platform Win Rate: 32.82%
  - Total P&L: $105,637.64
- **Recent Activity**:
  - Last 24 hours: 65 trades
  - Last 7 days: 1001 trades
  - Last 30 days: 2031 trades

### Open Positions
- **Open Positions**: 10
- **Unique Symbols**: 2
- **Total Exposure**: $243,249.52
- **Unrealized P&L**: $3,693.68

### Account Balances (Paper Trading)
- **Average Balance**: $10,223.29
- **Lowest Balance**: $831.03
- **Highest Balance**: $126,965.26

### Top Trading Symbols (Active Bots)

- **BTC/USDT**: 17 bots
- **SOL/USDT**: 4 bots
- **ETH/USDT**: 3 bots

### Decision Activity (24h)

- **wait**: 1253 decisions (avg confidence: 41.9%)
- **enter**: 78 decisions (avg confidence: 70.4%)
- **exit**: 38 decisions (avg confidence: 73.8%)

### System Health
- **Decisions (last hour)**: 46
- **Status**: 🟢 HEALTHY

## 🖥️ System Resources

### PM2 Services

| Service | Status | CPU | Memory | Uptime | Restarts |
|---------|--------|-----|--------|--------|----------|
| signal-listener | 🟢 online | 0% | 11MB | 3d 19h | 2 |
| error-alerts | 🟢 online | 0% | 19MB | 3d 19h | 2 |
| ggbot | 🟢 online | 5.6% | 318MB | 1h 59m | 11 |
| account-monitor | 🟢 online | 0.7% | 25MB | 1d 23h | 4 |
| sebastian-bot | 🟢 online | 0.4% | 29MB | 3d 19h | 2 |
| market-data-ws | 🟢 online | 0.9% | 20MB | 3d 19h | 2 |

### VM Resources

- **Disk**: 54G / 78G (70%)
- **Memory**: 1.9Gi / 3.8Gi
- **CPU Load**: 0.28 / 0.29 / 0.30 (1m/5m/15m)

### Infrastructure Services

- **Redis**: 🟢 connected (Memory: 22.04M)
- **Supabase PostgreSQL**: 🟢 connected (Remote managed service)

---

## 🌐 API Access Points

### Production Endpoints
| Service | URL | Status | Purpose |
|---------|-----|--------|---------|
| **V2 Orchestrator** | `https://ggbots-api.nightingale.business` | ✅ | Main backend API |
| **Frontend** | `https://ggbot-app.vercel.app` | ✅ | Next.js application |
| **Timeline Viewer** | `aster.ggbots.ai` | ✅ | AI consciousness timeline - chart shows bot's subjective awareness moments |

### Core API Endpoints

**Bot Configuration Management**
- `POST /api/v2/config` - Create new bot configuration
- `GET /api/v2/config` - List all user's bot configurations
- `GET /api/v2/config/{config_id}` - Get specific bot configuration
- `PUT /api/v2/config/{config_id}` - Update bot configuration
- `DELETE /api/v2/config/{config_id}` - Delete bot configuration

**Bot Control & Scheduling**
- `POST /api/v2/bot/{config_id}/start` - Start autonomous bot with scheduling
- `POST /api/v2/bot/{config_id}/stop` - Stop bot and remove scheduler jobs
- `POST /api/v2/bot/{config_id}/reset-account` - Reset paper trading account to $10k
- `GET /api/v2/scheduler/status` - Active scheduled jobs per user
- `POST /api/v2/scheduler/reconcile` - Reconcile scheduler state (admin)
- `GET /api/v2/bot/{config_id}/status` - Real-time bot status

**Bot Metrics & Data**
- `GET /api/v2/bot/{config_id}/metrics` - Performance metrics (win rate, P&L, etc.)
- `GET /api/v2/bot/{config_id}/positions` - Current open positions
- `GET /api/v2/bot/{config_id}/trades` - Trade history
- `GET /api/v2/bot/{config_id}/account` - Account balance and stats
- `GET /api/v2/bot/{config_id}/decisions` - Decision history
- `GET /api/dashboard-stream` - SSE stream with unified paper + live data

**Symbol Validation**
- `GET /api/v2/symbols/supported` - Get all 141 supported trading symbols
- `GET /api/v2/symbols/search/{query}` - Search symbols by base currency

**Signal Processing**
- `POST /api/v2/signal-validation/{config_id}` - Service-to-service signal validation endpoint
- `POST /api/v2/orchestrate/{config_id}` - General orchestration endpoint
- `POST /api/v2/test/signal-publishing/{config_id}` - Test Telegram signal publishing
- Signal listener service (PM2 background process with service authentication)

**Agent Management** (Production - Phase 4a Complete)
- `POST /api/v2/agent/{config_id}/start` - Start agent in strategy_definition or autonomous mode
- `POST /api/v2/agent/{config_id}/stop` - Stop agent and cleanup Redis queues
- `POST /api/v2/agent/{config_id}/message` - Send message to agent via Redis queue
- `GET /api/v2/agent/{config_id}/poll-response` - Poll for agent responses (non-blocking)
- `GET /api/v2/agent/{config_id}/status` - Get agent process status
- `POST /api/v2/agent/execute-trade` - Agent trade execution with position size/leverage overrides
- `GET /api/v2/agent/positions/{config_id}` - Get open positions (paper/aster/symphony routing)
- `GET /api/v2/agent/account/{config_id}` - Get account status and performance metrics
- `POST /api/v2/agent/positions/{trade_id}/close` - Close position (supports all trading modes)
- `POST /api/v2/agent/trade-observations` - Record post-trade reflection
- `POST /api/v2/agent/trade-observations/query` - Query past trade observations
- `POST /api/v2/agent/query-market-data` - Query market data with category structure

**Activity Timeline & Monitoring**
- `GET /api/v2/activities/{config_id}` - Get all activities (trades, queries, thoughts, waits)
- `GET /api/v2/snapshots/{config_id}/balance-series` - Get AI consciousness timeline (activities-only, Redis-cached equity)
- `GET /api/v2/activities/{config_id}/metadata` - Get bot metadata (name, symbols, status)

**Public Arena Endpoints** (no auth required)
- `GET /api/v2/public/arena/performance` - Competition leaderboard (is_public_performance bots only)
- `GET /api/v2/public/arena/{config_id}/balance-series` - Public bot equity timeline
- `GET /api/v2/public/arena/{config_id}/activities` - Public bot activity events
- `GET /api/v2/public/arena/{config_id}/metadata` - Public bot metadata

**Arena Betting** (USX staking on bots, public — wallet = identity)
- `POST /api/v2/arena/pledge` - Record USX bet after on-chain tx (no auth, validates wallet + tx_hash format)
- `GET /api/v2/arena/pledges` - List user's bets with bot names and amounts (auth required)

**AI Assistant** (Production)
- `POST /api/v2/assistant/chat` - Universal AI assistant for bot configuration (Claude Haiku function calling)
- 3 tools: query_available_data, load_full_config, update_full_config
- Bot-type aware (agent, scheduled, signal_validation), conversation history, deep merge config updates
- Inline chat panel in Configure tab (500px fixed height, markdown rendering, auto-save integration)

**User Management**
- `GET /api/v2/user/profile` - User profile with subscription details
- `GET /api/v2/me` - Current user profile (includes permissions)
- `GET /api/v2/user/indicators` - Available technical indicators
- `GET /api/v2/data-sources-with-points` - Market intelligence data sources
- `POST /api/v2/user/llm-credentials` - Store custom LLM API keys
- `GET /api/v2/user/llm-credentials` - List stored LLM credentials
- `GET /api/v2/user/llm-credentials/{credential_name}` - Get specific credential
- `DELETE /api/v2/user/llm-credentials/{credential_name}` - Remove credential

**Symphony Live Trading**
- `POST /api/v2/symphony/setup` - Store Symphony API credentials
- `GET /api/v2/symphony/status` - Check connection status
- `POST /api/v2/symphony/disconnect` - Remove credentials & disable live bots
- `GET /api/v2/positions/live/{config_id}` - Query Symphony positions
- `POST /api/v2/positions/live/{batch_id}/close` - Close live position
- `POST /api/v2/config/duplicate-as-live` - Duplicate paper bot as live bot
- `GET /api/v2/account/live/{config_id}` - Account metrics from Symphony
- `GET /api/v2/trades/live/{config_id}` - Trade history from Symphony

**AsterDEX Trading**
- `POST /api/v2/agent/execute-trade` - Agent trade execution with position size/leverage overrides
- Note: Aster uses .env credentials (Pro API Web3 ECDSA), frontend UI pending

**Hyperliquid Live Trading**
- `POST /api/v2/hyperliquid/setup` - Store API wallet key + wallet address
- `GET /api/v2/hyperliquid/status` - Connection status + live balance/positions
- `POST /api/v2/hyperliquid/disconnect` - Remove credentials, set bots to paper mode
- `POST /api/v2/hyperliquid/test-trade` - Open 0.01 ETH long → close (mainnet test)
- `GET /api/v2/bot/{config_id}/positions` - Open positions (routes to Hyperliquid if trading_mode='hyperliquid')
- `GET /api/v2/bot/{config_id}/account` - Account metrics from Hyperliquid Info API
- `POST /api/v2/positions/hyperliquid/{batch_id}/close` - Close position with ownership verification

**Stripe Subscription Management**
- `POST /api/v2/create-checkout-session` - Create Stripe checkout session
- `POST /api/v2/stripe-webhook` - Handle Stripe webhook events
- `POST /api/v2/create-portal-session` - Create Stripe billing portal session

**Admin Dashboard** (Production, restricted to ADMIN_USER_ID)
- `GET /api/v2/admin/stats` - Platform stats (users, bots, trades, P&L, health)
- `GET /api/v2/admin/services` - PM2 services, VM resources, Redis status
- `GET /api/v2/admin/logs/summary` - Log level counts (hours parameter)
- `GET /api/v2/admin/billing` - 30-day billing overview with token usage
- `GET /api/v2/admin/users` - List users (search by email, pagination)
- `GET /api/v2/admin/users/{user_id}` - User detail with configs + accounts
- `PATCH /api/v2/admin/users/{user_id}` - Update subscription tier/status
- `GET /api/v2/admin/users/{user_id}/configs` - Get user configurations
- `PATCH /api/v2/admin/configs/{config_id}` - Update config fields
- `POST /api/v2/admin/bots/{config_id}/start` - Start bot (admin override)
- `POST /api/v2/admin/bots/{config_id}/stop` - Stop bot (admin override)
- `POST /api/v2/admin/bots/{config_id}/reset-account` - Reset paper account to $10k
- `GET /api/v2/admin/bots/equity-comparison` - Bot performance comparison (equity curves)
- Frontend: 4 pages (/admin, /admin/users, /admin/users/[user_id], /admin/bots-comparison)

---

## 📊 System Architecture

### PM2 Modules
| Module | Status | Purpose |
|--------|--------|---------|
| pm2-logrotate | ✅ Installed | Automated log rotation and compression (10MB rotation, 5 files max) |

---


## ⚡ Current Capabilities

### **ggbot Service** (V2 Orchestrator)
- **Complete E2E Pipeline**: Extraction → Decision → Trading
- **Autonomous Scheduler**: Zero-drift execution at candle boundaries (5m/15m/30m/1h/4h/1d)
- **Redis Idempotency**: Prevents duplicate trades across restarts
- **Real-time Rescheduling**: Auto-updates when users change configurations
- **Startup Reconciliation**: Restores active bots automatically
- **Paper Trading**: $10k isolated accounts per config with 3-second position monitoring
- **Symphony Live Trading**: Real-money trading via Symphony.io (100 compatible symbols)
- **AsterDEX Trading**: Decentralized futures with Web3 auth (33 symbols, up to 20x leverage, dynamic position sizing)
- **Hyperliquid Live Trading**: Non-custodial DEX perps (228 markets, up to 50x, API wallets, retry logic)
- **Telegram Publishing**: Signal broadcasting to user channels (APPROVED/REJECTED status, "Live on Hyperliquid" tag)
- **REST API**: 30+ endpoints for bot control, positions, analytics

### **account-monitor Service**
- **Universal Account Monitoring**: Unified monitoring for paper, Symphony, Aster, and Hyperliquid trading accounts
- **5-Second Check Intervals**: Continuous monitoring with on-change detection
- **Redis Equity Cache**: Total equity cached every 5s for instant activity logging (30s TTL)
- **Historical Snapshots**: 5-minute heartbeat storage in account_snapshots table
- **Agent Watchdog**: Auto-restarts stale agent bots (>24h inactive) every 5 minutes via PM2
- **Adapter Pattern**: Clean architecture for multiple trading mode data sources
- **Documentation**: Complete implementation guide in DOCS/UNIFIED_ACCOUNT_MONITORING.md

### **market-data-ws Service**
- **Real-time Binance WebSocket**: Live prices for 100 symbols × 7 timeframes (700 datasets)
- **Redis Cache**: Sub-millisecond price access (~1s freshness)
- **Position P&L Updates**: Real-time unrealized P&L calculations
- **Liquidation Monitoring**: Automatic position liquidation when losses exceed margin

### **signal-listener Service**
- **ggShot Integration**: Receives live trading signals from ggShot Telegram bot
- **Database Storage**: All signals stored in `market_data` table as JSONB (`data_points->>'ggshot_signal'`)
- **Historical Data**: 1,829+ signals with 70 days of history (seeded + live updates)
- **Signal Structure**: Direction, entry zone, stop loss, take profit targets, confidence scores
- **Multi-timeframe Support**: Signals for 5m, 15m, 30m, 1h, 4h, 1d timeframes
- **AI Confidence Evaluation**: Routes signals to signal_validation bots for AI filtering
- **Agent Access**: Agents and scheduled bots can query ggshot signals via MCP market data tool
- **Service Authentication**: Dedicated `/api/v2/signal-validation` endpoint with service auth
- **Premium Gating**: ggBase subscription enforcement for signal validation mode

### **x-bot Service**
- **Platform Status Tweets**: Automated updates on @ggbots_ai
- **Engagement Monitoring**: Twitter community interaction

### **error-alerts Service**
- **Error Monitoring**: Tails `logs/ggbot.log` for ERROR/CRITICAL lines via `tail -F`
- **Telegram Alerts**: Real-time notifications to admin error channel
- **Rate Limiting**: 60s cooldown per error pattern, deduplication via recent_errors deque
- **Log Format Compatible**: Parses `' | '` (maxsplit=2) then `' - '` (maxsplit=1) — context tags stay in location portion
- **File**: `core/monitoring/error_alert_service.py`

### **Logging System**

**File**: `core/common/logger.py` — Loguru with dynamic format functions

**Log Format**:
```
2026-02-11 08:05:32 | INFO     | decision.engine_v2:make_decision:282 [run=a3f,cfg=b09a8d0e] - Starting decision...
2026-02-11 08:05:32 | INFO     | ggbot:run_once:1353 - Plain log line (no context)
```

- Context tag `[run=...,cfg=...,uid=...]` only appears when fields are bound
- `config_id`/`user_id` truncated to 8 chars; `run_id` is 6 hex chars
- **run_id** generated in `run_once()`, threads through entire bot cycle for grep correlation

**Log Levels**:
| Level | Purpose | Examples |
|-------|---------|---------|
| DEBUG | Happy-path detail | Cache hits, candle fetches, storage confirmations |
| INFO | State transitions | Cycle start/complete, LLM calls, decision results, permission checks |
| WARNING | Recoverable issues | Non-critical fetch failures, permission blocks |
| ERROR | Failures needing attention | Extraction/decision/trading failures, unexpected exceptions |

**Consumers** (must remain compatible with format changes):
| Consumer | File | Parsing Method |
|----------|------|---------------|
| error-alerts | `core/monitoring/error_alert_service.py:194` | `split(' \| ', maxsplit=2)` then `split(' - ', maxsplit=1)` |
| admin logs/summary | `api/admin.py:326` | `split(' \| ')` → counts by level in `parts[1]` |

**Debugging Commands**:
```bash
# Follow a single bot cycle by run_id
grep "run=a3f" logs/ggbot.log

# Find all errors for a config
grep "\[cfg=b09a8d0e\]" logs/ggbot.log | grep ERROR

# Count log volume by level
grep -c "| INFO " logs/ggbot.log
grep -c "| DEBUG " logs/ggbot.log
grep -c "| ERROR " logs/ggbot.log

# Tail live logs
pm2 logs ggbot --lines 50
```

### **Metered Billing System** (Production Live - 2025-11-16)
- **Stripe Billing Meters**: Tracks LLM usage costs with 70% markup
- **Actual Cost Billing**: Uses OpenRouter's actual `usage.cost` for tier-accurate pricing (economy/standard/premium)
- **Daily Reporting**: APScheduler job runs midnight UTC, aggregates unreported activities
- **Activity Logging**: All LLM calls tracked with provider/platform costs, tokens (input/output/reasoning)
- **Meter Aggregation**: Real-time event reporting, Stripe aggregates for billing period
- **Weekly Invoicing**: Usage-based subscriptions billed weekly (configurable)
- **Documentation**: Complete guide in DOCS/completed/METERED_BILLING_IMPLEMENTATION.md

### **Market Intelligence**
**32 data points across 7 categories (hybrid: 4 Perplexity macro + 4 Grok Twitter/on-chain sources LIVE):**
- **Technical Analysis** (21 indicators): RSI, MACD, Bollinger Bands, volume, momentum, trend
- **Trading Signals** (1 source): ggShot AI-filtered signals (1,829+ stored in database, 70 days history, live updates)
- **On-Chain Analytics** (2 live): BTC TVL, whale activity
- **Derivatives & Leverage** (2 rates): BTC/ETH funding rates
- **Sentiment & Social** (1 live): Twitter sentiment analysis
- **News & Regulatory** (1 live): Crypto news aggregation
- **Macro Economics** (4 live): VIX, DXY, CPI, NFP

### **Trading Modes**
- **Paper Trading**: Virtual $10k accounts, risk-free testing
- **Live Trading**: Symphony.io integration (premium feature, ggBase required)
- **AsterDEX Trading**: Decentralized futures (33 symbols, up to 20x leverage, competition-ready)
- **Hyperliquid Live Trading**: Non-custodial DEX perps (228 markets, up to 50x, API wallet model, USDC on Arbitrum)

### **Rei Decision Engine** (Experimental - 2026-01-27)
- **Purpose**: Alternative decision engine using Rei Core (reilabs.org) instead of OpenRouter LLMs
- **How it works**: Extraction runs normally → raw numerical data sent to Rei API (Float64 precision) → structured JSON decision returned → trading engine executes
- **Key advantage**: Inference-time learning — Rei evolves reasoning patterns from trade outcomes without retraining. No LLM tokenization loss on numerical data.
- **Feedback loop**: Trade outcomes (P&L, duration, close reason) automatically reported to Rei for learning
- **Config**: Set `rei_enabled: true` in bot's `config_data` JSONB to route decisions through Rei
- **Test bot**: "The Nightingale" (config_id: `4060437e-b39e-4c51-a2a9-b35cf698ed64`) — BTC/USDT paper trading
- **Files**: `decision/rei_engine.py` (engine), `core/services/rei_service.py` (API client)
- **Docs**: `DOCS/REI_DOCS.md` (Rei platform documentation)

---

## 🔌 Complete Port Reference

### Application Ports
| Port | Service | Protocol | Access | Purpose |
|------|---------|----------|--------|---------|
| **8000** | V2 Orchestrator (ggbot.py) | HTTP | Public | Complete V2 API server with E2E pipeline |
| **8080** | code-server | HTTP | Public | VSCode in browser (development environment) |

### Database Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **Remote** | Supabase PostgreSQL | HTTPS/SSL | Main application database (managed) |
| **6379** | Redis | Localhost | WebSocket cache, live prices, equity cache, scheduler idempotency |

### System Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **22** | SSH | Public | Remote access |
| **80** | HTTP | Public | Web server |
| **443** | HTTPS | Public | Secure web server |

---

## 🔄 Background Tasks

- **Universal Account Monitoring**: ✅ ACTIVE (5s checks, Redis equity cache, 5min snapshots for all trading modes)
- **Position Monitoring**: ✅ ACTIVE (3-second cycles monitoring 120+ configs with open positions)
- **Autonomous Trading**: ✅ ACTIVE (scheduled bot execution across multiple timeframes with APScheduler)
- **Signal Processing**: ✅ ACTIVE (ggShot signal validation and telegram publishing)
- **Log Rotation**: ✅ ACTIVE (pm2-logrotate with 10MB rotation, 5 file retention, compression)
- **Disk Space Monitoring**: ✅ ACTIVE (automated checks every 6 hours)
- **Process Cleanup**: Every 5min (terminated processes)
- **Cache Cleanup**: Every hour (old statuses/decisions)

---

## 🔧 Quick Commands

```bash
# Service status
pm2 list
pm2 monit

# Logs — live tail
pm2 logs ggbot
pm2 logs market-data-ws

# Logs — trace a single bot cycle (replace run_id)
grep "run=a3f" logs/ggbot.log

# Logs — errors for a specific config
grep "\[cfg=b09a8d0e\]" logs/ggbot.log | grep ERROR

# Logs — volume check
wc -l logs/ggbot.log

# Disk space monitoring
/home/sev/ggbot/scripts/disk_monitor.sh

# E2E Testing
python -m tests.test_full_e2e_integration

# Resources
htop
df -h
```

---

## 💳 Stripe Subscription System

### Subscription Tiers
| Feature | Free | Usage-Based |
|---------|------|-------------|
| **Base Price** | $0/month | $0/month |
| **Bot Activation** | ❌ Browse only | ✅ Unlimited |
| **LLM Usage** | N/A | Pay-per-use (1.70× markup) |
| **Analysis Frequency** | N/A | Any (5m to 1w) |
| **AI Models** | N/A | All 7 Frontier Models |
| **Reasoning Tiers** | N/A | Economy/Standard/Premium |
| **Live Trading** | ❌ | ✅ (Symphony.io, AsterDEX) |
| **Telegram Publishing** | ❌ | ✅ |
| **Billing** | N/A | Weekly invoicing |

**Typical Costs** (based on real usage data):
- Budget: <$2/month (1-2 bots, hourly, economy reasoning)
- Active Trader: $10-35/month (3-5 bots, 15-30min, standard reasoning)
- Power User: $50-150/month (5-10 bots, 5-15min, premium reasoning)

**Cost varies 30× between reasoning tiers**: Economy (~$0.003), Standard (~$0.01), Premium (~$0.04-0.09) per decision

### Stripe Integration
**Backend API Endpoints** (`/api/v2/`):
- `POST /create-checkout-session` - Create Stripe Checkout (usage-based plan)
- `POST /stripe-webhook` - Handle subscription events (HMAC verified)
- `POST /create-portal-session` - Stripe billing portal for self-service management
- `GET /me` - User profile with subscription status
- `GET /billing/usage` - Current unreported usage with model breakdown (deprecated, use /usage/me)
- `GET /billing/usage/breakdown` - Per-bot and daily usage breakdown (deprecated, use /usage/breakdown)

**Real-Time Usage API** (`/api/v2/usage/`) - NEW:
- `GET /usage/me` - User usage summary (Redis-cached, includes credits + net balance)
- `GET /usage/config/{config_id}` - Per-bot usage (instant from Redis)
- `GET /usage/breakdown` - All bots usage breakdown (sorted by cost)
- `GET /usage/history/{config_id}?days=30` - Daily usage history (90-day max)

**Credit Packs**:
- `POST /credits/purchase` - Create Stripe Checkout for credit pack
- `POST /credits/crypto-checkout` - Create NOWPayments invoice for crypto payment
- `GET /credits/balance` - Get Stripe credit balance
- `POST /webhooks/nowpayments` - IPN callback for crypto payments (HMAC verified, idempotent)

**Metered Billing System** (Production Live):
- Daily meter reporting via APScheduler (midnight UTC)
- Meter ID: `mtr_61TcMoxbXUvKBLQG741J9gH6H6LiHGyW`
- Event Name: `llm_tokens_usd`
- All LLM calls tracked with tokens and costs in `activities` table
- 70% markup applied: `platform_cost_usd = provider_cost_usd × 1.70`
- Weekly/monthly invoicing with real-time Stripe Billing Meters aggregation
- Real-time Redis counters updated on every LLM call (usage visibility)
- Usage Monitor in account-monitor service (credit watchdog, auto-pause on depletion)

**Frontend Components**:
- `<UpgradeModal>` - Pricing modal with usage-based and PRO plans
- `<PermissionGate>` - Premium feature gates
- `<UserProfile>` - Subscription badge with upgrade/billing buttons

**Early Adopter Promotion**:
- Coupon code: `EARLY50` (50% off for 6 months)

---

**Telegram Community**: https://t.me/+ndI762EkfcszZTUx

---

## 📚 Documentation References

- **New Claude Code Instances**: `GO.md` - Start here for onboarding procedure
- **Architecture Overview**: `README.md` - Platform architecture and getting started
- **Current Status**: This file (ACTIVE.md) - Production system status and operational reference
- **Roadmap & Tasks**: `TODO.md` - Current development tasks and priorities
- **Complete History**: `CHANGELOG.md` - All completed features, fixes, and improvements

## 📊 Database Schema

**Auto-generated schema reference** - Updated automatically by `scripts/status_check.py`

**For architectural context and design decisions**, see [DOCS/DATABASE_CONTEXT.md](DOCS/DATABASE_CONTEXT.md).

**Last Updated**: 2026-02-13 06:36:53 UTC

---

### `account_snapshots` (28 columns)

**Primary Key**: `snapshot_id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`

**Indexes**:
- `_deprecated_idx_snapshots_config_time` on (config_id, timestamp)
- `_deprecated_idx_snapshots_heartbeat` on (config_id, timestamp, is_heartbeat)
- `idx_snapshots_latest` on (config_id, timestamp)
- `idx_snapshots_mode_time` on (trading_mode, timestamp)
- `idx_snapshots_timestamp` on (timestamp)
- `idx_snapshots_user_time` on (user_id, timestamp)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `snapshot_id` | uuid |  | gen_random_uuid() |
| `config_id` | uuid |  |  |
| `user_id` | uuid |  |  |
| `trading_mode` | character varying(20) |  |  |
| `timestamp` | timestamp with time zone |  | now() |
| `current_balance` | numeric | ✓ |  |
| `available_balance` | numeric | ✓ |  |
| `margin_used` | numeric | ✓ |  |
| `total_pnl` | numeric |  |  |
| `realized_pnl` | numeric | ✓ |  |
| `unrealized_pnl` | numeric | ✓ |  |
| `total_trades` | integer |  | 0 |
| `win_trades` | integer |  | 0 |
| `loss_trades` | integer |  | 0 |
| `win_rate` | numeric | ✓ |  |
| `open_positions` | integer |  | 0 |
| `position_value` | numeric | ✓ |  |
| `total_exposure` | numeric | ✓ |  |
| `avg_win` | numeric | ✓ |  |
| `avg_loss` | numeric | ✓ |  |
| `largest_win` | numeric | ✓ |  |
| `largest_loss` | numeric | ✓ |  |
| `sharpe_ratio` | numeric | ✓ |  |
| `max_drawdown` | numeric | ✓ |  |
| `raw_data` | jsonb | ✓ |  |
| `balance_change_pct` | numeric | ✓ |  |
| `is_heartbeat` | boolean | ✓ | false |
| `created_at` | timestamp with time zone |  | now() |

### `activities` (26 columns)

**Primary Key**: `activity_id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`

**Indexes**:
- `idx_activities_billing` on (user_id, created_at, stripe_reported)
- `idx_activities_chart_data` on (config_id, created_at, account_balance)
- `idx_activities_config_billing` on (config_id, created_at)
- `idx_activities_config_time` on (config_id, created_at)
- `idx_activities_decision` on (decision_id)
- `idx_activities_platform_cost` on (platform_cost_usd)
- `idx_activities_symbol` on (config_id, related_symbol, created_at)
- `idx_activities_trade` on (trade_id)
- `idx_activities_type` on (config_id, activity_type, created_at)
- `idx_activities_user` on (user_id, created_at)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `activity_id` | uuid |  | gen_random_uuid() |
| `config_id` | uuid |  |  |
| `user_id` | uuid |  |  |
| `activity_type` | text |  |  |
| `activity_source` | text |  |  |
| `summary` | text |  |  |
| `details` | jsonb |  | '{}'::jsonb |
| `trade_id` | text | ✓ |  |
| `trade_type` | text | ✓ |  |
| `decision_id` | uuid | ✓ |  |
| `related_symbol` | text | ✓ |  |
| `importance` | integer |  | 5 |
| `created_at` | timestamp with time zone |  | now() |
| `provider` | character varying(50) | ✓ |  |
| `model` | character varying(100) | ✓ |  |
| `thinking_mode` | boolean | ✓ |  |
| `input_tokens` | integer | ✓ |  |
| `output_tokens` | integer | ✓ |  |
| `reasoning_tokens` | integer | ✓ |  |
| `provider_cost_usd` | numeric | ✓ |  |
| `platform_cost_usd` | numeric | ✓ |  |
| `stripe_reported` | boolean | ✓ | false |
| `stripe_reported_at` | timestamp with time zone | ✓ |  |
| `account_balance` | numeric | ✓ |  |
| `account_pnl` | numeric | ✓ |  |
| `total_equity` | numeric | ✓ |  |

### `agent_sessions` (5 columns)

**Primary Key**: `config_id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`

**Indexes**:
- `idx_agent_sessions_last_active` on (last_active_at)
- `idx_agent_sessions_session_id` on (session_id)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `config_id` | uuid |  |  |
| `session_id` | character varying(255) |  |  |
| `last_active_at` | timestamp without time zone | ✓ | now() |
| `created_at` | timestamp without time zone | ✓ | now() |
| `updated_at` | timestamp without time zone | ✓ | now() |

### `arena_pledges` (12 columns)

**Primary Key**: `id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`

**Indexes**:
- `arena_pledges_tx_hash_key` on (tx_hash)
- `idx_arena_pledges_config` on (config_id)
- `idx_arena_pledges_pledged_at` on (pledged_at)
- `idx_arena_pledges_user` on (user_id)
- `idx_arena_pledges_wallet` on (wallet_address)

**Unique Constraints**: `tx_hash`

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | uuid |  | gen_random_uuid() |
| `user_id` | uuid | ✓ |  |
| `wallet_address` | text |  |  |
| `config_id` | uuid | ✓ |  |
| `usx_amount` | numeric |  |  |
| `susx_amount` | numeric | ✓ |  |
| `tx_hash` | text |  |  |
| `pledged_at` | timestamp with time zone | ✓ | now() |
| `competition_id` | uuid | ✓ |  |
| `prize_amount` | numeric | ✓ |  |
| `claimed_at` | timestamp with time zone | ✓ |  |
| `unstaked_at` | timestamp with time zone | ✓ |  |

### `bot_telegram_channels` (6 columns)

**Primary Key**: `config_id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`

**Indexes**:
- `idx_bot_telegram_channels_chat_id` on (telegram_chat_id)
- `idx_bot_telegram_channels_enabled` on (enabled)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `config_id` | uuid |  |  |
| `telegram_chat_id` | bigint |  |  |
| `channel_name` | character varying(100) | ✓ |  |
| `enabled` | boolean | ✓ | true |
| `created_at` | timestamp with time zone | ✓ | now() |
| `updated_at` | timestamp with time zone | ✓ | now() |

### `configurations` (17 columns)

**Primary Key**: `config_id`

**Indexes**:
- `idx_configurations_is_public_performance` on (is_public_performance)
- `idx_configurations_public` on (is_public_performance)
- `idx_configurations_state` on (state)
- `idx_configurations_type` on (config_type)
- `idx_configurations_user_id` on (user_id)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `config_id` | uuid |  | uuid_generate_v4() |
| `user_id` | uuid |  |  |
| `config_type` | character varying(50) |  |  |
| `config_name` | character varying(100) | ✓ |  |
| `config_data` | jsonb |  |  |
| `created_at` | timestamp with time zone |  | now() |
| `updated_at` | timestamp with time zone |  | now() |
| `state` | text |  | 'inactive'::text |
| `symphony_agent_id` | character varying(255) | ✓ |  |
| `trading_mode` | character varying(20) |  | 'paper'::character varying |
| `is_public_performance` | boolean | ✓ | false |
| `profile_image_url` | text | ✓ |  |
| `description` | text | ✓ |  |
| `first_run_used` | boolean | ✓ | false |
| `free_runs_remaining` | integer | ✓ | 3 |
| `arena_registered_at` | timestamp with time zone | ✓ |  |
| `initial_equity` | numeric | ✓ |  |

### `data_points` (11 columns)

**Primary Key**: `data_point_id`

**Foreign Keys**:
- `source_id` → `data_sources(source_id)`

**Indexes**:
- `data_points_source_id_name_key` on (source_id, name)
- `idx_data_points_name` on (name)
- `idx_data_points_premium` on (requires_premium, enabled)
- `idx_data_points_source` on (source_id, enabled, sort_order)

**Unique Constraints**: `source_id`, `name`

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `data_point_id` | uuid |  | gen_random_uuid() |
| `source_id` | uuid |  |  |
| `name` | character varying(50) |  |  |
| `display_name` | character varying(100) |  |  |
| `description` | text | ✓ |  |
| `config_values` | ARRAY |  |  |
| `requires_premium` | boolean | ✓ | false |
| `enabled` | boolean | ✓ | true |
| `sort_order` | integer | ✓ | 0 |
| `created_at` | timestamp with time zone | ✓ | now() |
| `updated_at` | timestamp with time zone | ✓ | now() |

### `data_sources` (9 columns)

**Primary Key**: `source_id`

**Indexes**:
- `data_sources_name_key` on (name)
- `idx_data_sources_enabled` on (enabled, sort_order)
- `idx_data_sources_premium` on (enabled, requires_premium)

**Unique Constraints**: `name`

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `source_id` | uuid |  | gen_random_uuid() |
| `name` | character varying(50) |  |  |
| `display_name` | character varying(100) |  |  |
| `description` | text | ✓ |  |
| `enabled` | boolean | ✓ | true |
| `requires_premium` | boolean | ✓ | false |
| `sort_order` | integer | ✓ | 0 |
| `created_at` | timestamp with time zone | ✓ | now() |
| `updated_at` | timestamp with time zone | ✓ | now() |

### `decisions` (13 columns)

**Primary Key**: `decision_id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`
- `parent_decision_id` → `decisions(decision_id)`

**Indexes**:
- `idx_decisions_action_status` on (action, status)
- `idx_decisions_confidence` on (confidence)
- `idx_decisions_created_by` on (created_by)
- `idx_decisions_parent` on (parent_decision_id)
- `idx_decisions_symbol_created` on (symbol, created_at)
- `idx_decisions_user_config` on (user_id, config_id)
- `idx_decisions_user_id_created` on (user_id, created_at)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `decision_id` | uuid |  | uuid_generate_v4() |
| `user_id` | uuid |  |  |
| `config_id` | uuid | ✓ |  |
| `symbol` | character varying(20) |  |  |
| `action` | character varying(20) |  |  |
| `status` | character varying(20) | ✓ |  |
| `confidence` | numeric |  |  |
| `reasoning` | text | ✓ |  |
| `prompt` | text | ✓ |  |
| `decision_data` | jsonb | ✓ |  |
| `parent_decision_id` | uuid | ✓ |  |
| `created_at` | timestamp with time zone |  | now() |
| `created_by` | text | ✓ | 'decision_engine_v2'::text |

### `live_trades` (9 columns)

**Primary Key**: `batch_id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`
- `decision_id` → `decisions(decision_id)`

**Indexes**:
- `idx_live_trades_config` on (config_id)
- `idx_live_trades_open` on (config_id, closed_at)
- `idx_live_trades_provider` on (config_id, provider)
- `idx_live_trades_provider_open` on (config_id, closed_at, provider)
- `idx_live_trades_symbol` on (config_id, closed_at, symbol)
- `live_trades_decision_id_unique` on (decision_id)

**Unique Constraints**: `decision_id`

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `batch_id` | character varying(255) |  |  |
| `config_id` | uuid |  |  |
| `decision_id` | uuid | ✓ |  |
| `created_at` | timestamp without time zone |  | now() |
| `closed_at` | timestamp without time zone | ✓ |  |
| `provider` | character varying(20) |  | 'symphony'::character varying |
| `stop_loss_order_id` | character varying(50) | ✓ |  |
| `take_profit_order_id` | character varying(50) | ✓ |  |
| `symbol` | character varying(20) | ✓ |  |

### `llm_models` (16 columns)

**Primary Key**: `model_id`

**Indexes**:
- `idx_llm_models_enabled` on (enabled, sort_order)
- `idx_llm_models_provider` on (provider)
- `llm_models_openrouter_model_id_key` on (openrouter_model_id)

**Unique Constraints**: `openrouter_model_id`

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `model_id` | character varying(50) |  |  |
| `display_name` | character varying(100) |  |  |
| `provider` | character varying(50) |  |  |
| `openrouter_model_id` | character varying(100) |  |  |
| `supports_thinking` | boolean |  | true |
| `enabled` | boolean |  | true |
| `max_context_tokens` | integer |  |  |
| `context_display` | character varying(20) |  |  |
| `pricing_input_per_1m` | numeric |  |  |
| `pricing_output_per_1m` | numeric |  |  |
| `cost_per_decision_standard` | numeric |  |  |
| `cost_per_decision_thinking` | numeric |  |  |
| `description` | text | ✓ |  |
| `sort_order` | integer |  |  |
| `created_at` | timestamp with time zone |  | now() |
| `updated_at` | timestamp with time zone |  | now() |

### `logs` (6 columns)

**Primary Key**: `log_id`

**Indexes**:
- `idx_logs_level_timestamp` on (log_level, timestamp)
- `idx_logs_user_timestamp` on (user_id, timestamp)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `log_id` | integer |  | nextval('logs_log_id_seq'::reg |
| `user_id` | uuid | ✓ |  |
| `module` | character varying(100) | ✓ |  |
| `log_level` | character varying(10) |  |  |
| `message` | text |  |  |
| `timestamp` | timestamp with time zone |  | now() |

### `market_data` (9 columns)

**Primary Key**: `id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`

**Indexes**:
- `idx_market_data_config_symbol` on (config_id, symbol)
- `idx_market_data_updated_at` on (updated_at)
- `idx_market_data_user_symbol_timeframe` on (user_id, symbol, timeframe, updated_at)
- `market_data_unique_per_config` on (user_id, config_id, symbol, timeframe)

**Unique Constraints**: `user_id`, `config_id`, `symbol`, `timeframe`

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | integer |  | nextval('market_data_id_seq':: |
| `user_id` | uuid |  |  |
| `config_id` | uuid | ✓ |  |
| `symbol` | character varying(20) |  |  |
| `timeframe` | character varying(10) |  |  |
| `data_points` | jsonb | ✓ |  |
| `raw_data` | jsonb |  |  |
| `updated_at` | timestamp with time zone |  | now() |
| `data_source` | uuid | ✓ |  |

### `paper_accounts` (13 columns)

**Primary Key**: `account_id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`

**Indexes**:
- `idx_paper_accounts_user` on (user_id)
- `paper_accounts_config_id_key` on (config_id)

**Unique Constraints**: `config_id`

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `account_id` | uuid |  | uuid_generate_v4() |
| `user_id` | uuid |  |  |
| `config_id` | uuid |  |  |
| `initial_balance` | numeric |  | 10000.00 |
| `current_balance` | numeric |  | 10000.00 |
| `total_pnl` | numeric |  | 0.00 |
| `open_positions` | integer |  | 0 |
| `total_trades` | integer |  | 0 |
| `win_trades` | integer |  | 0 |
| `loss_trades` | integer |  | 0 |
| `created_at` | timestamp with time zone |  | now() |
| `updated_at` | timestamp with time zone |  | now() |
| `last_reset_at` | timestamp with time zone | ✓ |  |

### `paper_orders` (9 columns)

**Primary Key**: `order_id`

**Foreign Keys**:
- `trade_id` → `paper_trades(trade_id)`

**Indexes**:
- `idx_paper_orders_filled_at` on (filled_at)
- `idx_paper_orders_trade` on (trade_id)
- `idx_paper_orders_user` on (user_id)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `order_id` | uuid |  | uuid_generate_v4() |
| `user_id` | uuid |  |  |
| `trade_id` | uuid |  |  |
| `order_type` | character varying(20) |  |  |
| `side` | character varying(10) |  |  |
| `filled_price` | numeric |  |  |
| `size` | numeric |  |  |
| `fees` | numeric |  | 0.00 |
| `filled_at` | timestamp with time zone |  | now() |

### `paper_trades` (22 columns)

**Primary Key**: `trade_id`

**Foreign Keys**:
- `account_id` → `paper_accounts(account_id)`
- `config_id` → `configurations(config_id)`
- `decision_id` → `decisions(decision_id)`

**Indexes**:
- `idx_paper_trades_account` on (account_id)
- `idx_paper_trades_close_reason` on (close_reason)
- `idx_paper_trades_config_status` on (config_id, status, opened_at)
- `idx_paper_trades_decision` on (decision_id)
- `idx_paper_trades_status` on (status)
- `idx_paper_trades_symbol_opened` on (symbol, opened_at)
- `idx_paper_trades_user_config` on (user_id, config_id)
- `idx_paper_trades_user_status` on (user_id, status, opened_at)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `trade_id` | uuid |  | uuid_generate_v4() |
| `user_id` | uuid |  |  |
| `account_id` | uuid |  |  |
| `config_id` | uuid |  |  |
| `decision_id` | uuid | ✓ |  |
| `symbol` | character varying(20) |  |  |
| `side` | character varying(10) |  |  |
| `entry_price` | numeric |  |  |
| `current_price` | numeric | ✓ |  |
| `size_usd` | numeric |  |  |
| `leverage` | integer |  | 1 |
| `unrealized_pnl` | numeric | ✓ |  |
| `realized_pnl` | numeric | ✓ |  |
| `status` | character varying(20) |  | 'open'::character varying |
| `stop_loss` | numeric | ✓ |  |
| `take_profit` | numeric | ✓ |  |
| `confidence_score` | numeric | ✓ |  |
| `opened_at` | timestamp with time zone |  | now() |
| `closed_at` | timestamp with time zone | ✓ |  |
| `margin_used` | numeric | ✓ |  |
| `close_reason` | character varying(50) | ✓ |  |
| `liquidation_price` | numeric | ✓ |  |

### `stripe_webhooks` (11 columns)

**Primary Key**: `webhook_id`

**Indexes**:
- `idx_stripe_webhooks_customer` on (stripe_customer_id)
- `idx_stripe_webhooks_event_id` on (stripe_event_id)
- `idx_stripe_webhooks_event_type` on (event_type)
- `idx_stripe_webhooks_processed` on (processed, created_at)
- `idx_stripe_webhooks_retry` on (processed, retry_count)
- `idx_stripe_webhooks_subscription` on (stripe_subscription_id)
- `stripe_webhooks_stripe_event_id_key` on (stripe_event_id)

**Unique Constraints**: `stripe_event_id`

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `webhook_id` | uuid |  | gen_random_uuid() |
| `stripe_event_id` | character varying(100) |  |  |
| `event_type` | character varying(50) |  |  |
| `stripe_customer_id` | character varying(100) | ✓ |  |
| `stripe_subscription_id` | character varying(100) | ✓ |  |
| `event_data` | jsonb |  |  |
| `processed` | boolean | ✓ | false |
| `processed_at` | timestamp with time zone | ✓ |  |
| `error_message` | text | ✓ |  |
| `retry_count` | integer | ✓ | 0 |
| `created_at` | timestamp with time zone | ✓ | now() |

### `trade_observations` (14 columns)

**Primary Key**: `observation_id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`
- `trade_id` → `paper_trades(trade_id)`

**Indexes**:
- `idx_trade_observations_config` on (config_id)
- `idx_trade_observations_config_importance_created` on (config_id, importance, created_at)
- `idx_trade_observations_config_type_created` on (config_id, observation_type, created_at)
- `idx_trade_observations_importance` on (importance)
- `idx_trade_observations_trade` on (trade_id)
- `idx_trade_observations_type` on (observation_type)
- `idx_trade_observations_user` on (user_id)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `observation_id` | uuid |  | gen_random_uuid() |
| `config_id` | uuid |  |  |
| `user_id` | uuid |  |  |
| `trade_id` | uuid | ✓ |  |
| `observation_type` | text |  |  |
| `what_went_well` | text | ✓ |  |
| `what_went_wrong` | text | ✓ |  |
| `predictive_data_points` | jsonb | ✓ |  |
| `decision_review` | text | ✓ |  |
| `trade_pnl` | numeric | ✓ |  |
| `trade_duration_minutes` | integer | ✓ |  |
| `importance` | integer | ✓ | 5 |
| `created_at` | timestamp with time zone | ✓ | now() |
| `batch_id` | character varying(255) | ✓ |  |

### `user_llm_credentials` (7 columns)

**Primary Key**: `id`

**Indexes**:
- `idx_user_llm_credentials_provider` on (user_id, provider)
- `idx_user_llm_credentials_user_id` on (user_id)
- `user_llm_credentials_user_id_credential_name_key` on (user_id, credential_name)

**Unique Constraints**: `user_id`, `credential_name`

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | uuid |  | gen_random_uuid() |
| `user_id` | uuid |  |  |
| `credential_name` | text |  |  |
| `provider` | text |  |  |
| `vault_secret_id` | uuid |  |  |
| `created_at` | timestamp with time zone | ✓ | now() |
| `updated_at` | timestamp with time zone | ✓ | now() |

### `user_profiles` (20 columns)

**Primary Key**: `user_id`

**Indexes**:
- `idx_user_profiles_paid_data_points` on (paid_data_points)
- `idx_user_profiles_stripe` on (stripe_customer_id)
- `idx_user_profiles_subscription` on (subscription_tier, subscription_status)
- `idx_user_profiles_telegram` on (telegram_user_id)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `user_id` | uuid |  |  |
| `subscription_tier` | USER-DEFINED | ✓ | 'free'::subscription_tier |
| `subscription_status` | USER-DEFINED | ✓ | 'active'::subscription_status |
| `subscription_expires_at` | timestamp with time zone | ✓ |  |
| `stripe_customer_id` | character varying(100) | ✓ |  |
| `stripe_subscription_id` | character varying(100) | ✓ |  |
| `telegram_user_id` | bigint | ✓ |  |
| `telegram_username` | character varying(50) | ✓ |  |
| `telegram_chat_id` | bigint | ✓ |  |
| `monthly_signal_count` | integer | ✓ | 0 |
| `created_at` | timestamp with time zone | ✓ | now() |
| `updated_at` | timestamp with time zone | ✓ | now() |
| `paid_data_points` | ARRAY | ✓ | ARRAY[]::text[] |
| `symphony_vault_id` | uuid | ✓ |  |
| `symphony_smart_account` | character varying(42) | ✓ |  |
| `aster_vault_id` | uuid | ✓ |  |
| `aster_user_wallet` | character varying(42) | ✓ |  |
| `aster_wallet` | character varying(42) | ✓ |  |
| `hyperliquid_wallet_address` | character varying(42) | ✓ |  |
| `hyperliquid_vault_id` | uuid | ✓ |  |

---

## 🎯 Domain Models & Business Logic

**Note**: Domain models add business logic, validation, and computed properties on top of database tables.

**For schema design context**, see [DOCS/DATABASE_CONTEXT.md](DOCS/DATABASE_CONTEXT.md).

---

### `UserProfile` (core/domain/user_profile.py)

**Purpose**: User profile entity extending Supabase authentication with business model.

**Fields**:
- `user_id: str`
- `subscription_tier: SubscriptionTier`
- `subscription_status: SubscriptionStatus`
- `created_at: datetime`
- `updated_at: datetime`
- `subscription_expires_at: Optional[datetime]`
- `stripe_customer_id: Optional[str]`
- `stripe_subscription_id: Optional[str]`
- `telegram_user_id: Optional[int]`
- `telegram_username: Optional[str]`
- ... and 3 more fields

**Business Logic (@property methods)**:
- `is_free_tier` - Check if user is on free tier.
- `is_pro_tier` - Check if user has pro subscription.
- `is_prepaid_tier` - Check if user is on prepaid (credit pack) tier.
- `requires_credit_check` - Check if user requires hard credit balance check before LLM calls.

Prepaid users MUST have credits available before any LLM call.
Usage-based users are billed for overage, so no hard check needed.
- `has_active_subscription` - Check if user has active subscription.
- `subscription_expired` - Check if subscription has expired.
- `can_activate_bots` - MASTER PERMISSION: Check if user can activate/run bots.

This is the single source of truth for all paid features.
True for PREPAID, USAGE_BASED, and PRO tiers with active subscriptions.
- `can_use_agents` - Check if user can create and use agents (PRO tier only).
- `is_premium_user` - DEPRECATED: Use can_activate_bots instead.
- `can_use_premium_features` - DEPRECATED: Use can_activate_bots instead.
- `requires_own_llm_keys` - DEPRECATED: Platform provides LLM keys for all paid users.
- `can_publish_telegram_signals` - DEPRECATED: Use can_activate_bots instead.
- `can_use_signal_validation` - DEPRECATED: Use can_activate_bots instead.
- `can_use_live_trading` - DEPRECATED: Use can_activate_bots instead.
- `has_telegram_integration` - Check if user has Telegram integration configured.
- `has_stripe_integration` - Check if user has Stripe customer record.

---

### `DecisionData` (core/domain/decision.py)

**Purpose**: Flexible decision context storage (replaces decision_data JSONB field).

**Fields**:
- `trade_id: Optional[str]`
- `stop_loss_price: Optional[float]`
- `take_profit_price: Optional[float]`
- `position_size: Optional[float]`
- `entry_price: Optional[float]`
- `signal_source: Optional[str]`
- `signal_quality: Optional[float]`
- `validation_criteria: Optional[Dict[str, Any]]`
- `current_pnl: Optional[float]`
- `position_duration: Optional[int]`
- ... and 2 more fields

---

### `Decision` (core/domain/decision.py)

**Purpose**: Unified decision entity representing all AI decision-making in the system.

**Fields**:
- `decision_id: str`
- `user_id: str`
- `symbol: Symbol`
- `action: DecisionAction`
- `confidence: Confidence`
- `reasoning: Optional[str]`
- `created_at: datetime`
- `config_id: Optional[str]`
- `status: Optional[DecisionStatus]`
- `prompt: Optional[str]`
- ... and 3 more fields

**Business Logic (@property methods)**:
- `is_actionable` - Check if this decision represents an actionable trade signal.
- `is_entry_signal` - Check if this is an entry signal (BUY).
- `is_exit_signal` - Check if this is an exit signal (SELL).
- `is_wait_signal` - Check if this is a wait decision.
- `is_approved` - Check if decision was approved (for signal validation).
- `is_rejected` - Check if decision was rejected.
- `has_parent` - Check if this decision is linked to a parent decision.
- `is_high_confidence` - Check if decision meets high confidence threshold.
- `is_user_config_based` - Check if decision is based on user configuration (vs. system signals).
- `is_system_signal` - Check if decision is from system signals (e.g., ggShot).

---

### `PriceLevel` (core/domain/position.py)

**Purpose**: Value object representing a price level with timestamp.

**Fields**:
- `price: Decimal`
- `timestamp: datetime`

**Business Logic (@property methods)**:
- `age_seconds` - Get age of this price level in seconds.

---

### `PositionMetrics` (core/domain/position.py)

**Purpose**: Value object containing position performance metrics.

**Fields**:
- `unrealized_pnl: Money`
- `unrealized_pnl_pct: Decimal`
- `realized_pnl: Money`
- `total_pnl: Money`
- `max_profit: Money`
- `max_loss: Money`
- `current_risk_reward_ratio: Optional[Decimal]`
- `time_in_position_hours: float`

**Business Logic (@property methods)**:
- `is_profitable` - Check if position is currently profitable.
- `is_losing` - Check if position is currently losing money.

---

### `Position` (core/domain/position.py)

**Purpose**: Entity representing a trading position with full lifecycle management.

**Fields**:
- `trade_id: str`
- `config_id: str`
- `symbol: Symbol`
- `side: PositionSide`
- `status: PositionStatus`
- `size_usd: Money`
- `leverage: Decimal`
- `collateral_amount: Money`
- `entry_price: PriceLevel`
- `current_price: Optional[PriceLevel]`
- ... and 10 more fields

**Business Logic (@property methods)**:
- `is_active` - Check if position is currently active.
- `is_pending` - Check if position is pending execution.
- `is_closed` - Check if position has been closed.
- `time_in_position` - Get time spent in position.

---

### `Indicator` (core/domain/market_data.py)

**Purpose**: Value object representing a single technical indicator.

**Fields**:
- `name: str`
- `timeframe: str`
- `value: Any`
- `calculation_time: datetime`
- `metadata: Dict[str, Any]`

**Business Logic (@property methods)**:
- `indicator_key` - Get standardized indicator key (e.g., 'RSI_1h').
- `age_seconds` - Get age of indicator in seconds.

---

### `VolumeData` (core/domain/market_data.py)

**Purpose**: Value object for volume analysis data.

**Fields**:
- `current_volume: Decimal`
- `average_volume: Decimal`
- `volume_ratio: Decimal`
- `timeframe: str`
- `period_used: int`
- `timestamp: datetime`

**Business Logic (@property methods)**:
- `volume_increase_pct` - Get volume increase percentage above average.
- `confidence_level` - Get volume confidence level based on ggShot criteria.

---

### `PriceData` (core/domain/market_data.py)

**Purpose**: Value object for current price information.

**Fields**:
- `symbol: Symbol`
- `price: Decimal`
- `timestamp: datetime`
- `source: DataSource`
- `bid: Optional[Decimal]`
- `ask: Optional[Decimal]`
- `volume_24h: Optional[Decimal]`

**Business Logic (@property methods)**:
- `age_seconds` - Get age of price data in seconds.
- `spread` - Get bid-ask spread if available.

---

### `MarketDataSnapshot` (core/domain/market_data.py)

**Purpose**: Entity representing a complete market data snapshot for a symbol.

**Fields**:
- `id: str`
- `symbol: Symbol`
- `data_source: DataSource`
- `extracted_at: datetime`
- `indicators: Dict[str, Indicator]`
- `price_data: Optional[PriceData]`
- `volume_data: Optional[VolumeData]`
- `raw_data: Dict[str, Any]`
- `extraction_config: Dict[str, Any]`
- `processing_time_ms: Optional[int]`

**Business Logic (@property methods)**:
- `age_seconds` - Get age of this market data snapshot in seconds.
- `freshness_level` - Get overall freshness level of this snapshot.

---

### `DataSource` (core/domain/data_source.py)

**Purpose**: Data source entity for categorizing extraction sources.

**Fields**:
- `source_id: str`
- `name: str`
- `display_name: str`
- `enabled: bool`
- `requires_premium: bool`
- `sort_order: int`
- `created_at: datetime`
- `updated_at: datetime`
- `description: Optional[str]`

---

### `DataPoint` (core/domain/data_source.py)

**Purpose**: Data point entity representing specific indicators/signals within a data source.

**Fields**:
- `data_point_id: str`
- `source_id: str`
- `name: str`
- `display_name: str`
- `config_values: list[str]`
- `enabled: bool`
- `requires_premium: bool`
- `sort_order: int`
- `created_at: datetime`
- `updated_at: datetime`
- ... and 1 more fields

**Business Logic (@property methods)**:
- `is_premium` - Check if this data point requires premium access.
- `is_available` - Check if this data point is available for use.

---

### `DataSourceWithPoints` (core/domain/data_source.py)

**Purpose**: Composite entity containing a data source with its associated data points.

**Fields**:
- `source: DataSource`
- `data_points: list[DataPoint]`

---

## ⚙️ Configuration Structure (config_data JSONB)

**Canonical source**: `core/config/models.py` (BotConfig Pydantic model)

**Auto-generated** - Updated automatically by `scripts/status_check.py`

**Last Updated**: 2026-02-13 06:36:53 UTC

---

**Purpose**: Complete GGBot configuration model.

### Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `schema_version` | str | 1.0 | Configuration schema version |
| `selected_pair` | Optional[str] |  | Trading pair to analyze |
| `extraction` | Optional[ExtractionConfig] |  | Extraction module configuration |
| `decision` | Optional[DecisionConfig] |  | Decision module configuration |
| `llm_config` | Optional[LLMConfig] |  | LLM provider and API key configuration |
| `trading` | TradingConfig |  | Trading module configuration |
| `telegram_integration` | Optional[TelegramIntegrationConfig] |  | Telegram integration configuration |
| `agent_strategy` | Optional[AgentStrategy] |  | Agent strategy configuration |

**Full validation rules**: See `core/config/models.py` for complete Pydantic model with field validators.

---
