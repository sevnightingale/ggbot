# 🚀 ACTIVE - ggbots System Status

**Last Updated**: 2026-02-24 10:36:09 UTC (Auto-updated by status_check.py)
**System Health**: 🟢 HEALTHY

## 📊 Live Platform Metrics

### Users & Subscriptions
- **Total Users**: 321
- **Prepaid Users**: 20 (20 active subscriptions)
- **Free Users**: 295
- **Users with Bots**: 311 (96.9%)

### Bot Statistics
- **Total Bots**: 478
- **Active Bots**: 16 (3.3%)
  - Paper: 15
  - Symphony (Live): 0
  - Aster (DEX): 0
  - Hyperliquid (Live): 1
- **Inactive Bots**: 462
- **Avg Bots per User**: 1.5

### Trading Activity
- **Total Trades (All Time)**: 7,475
  - Wins: 2,497
  - Losses: 4,978
  - Platform Win Rate: 33.40%
  - Total P&L: $104,911.34
- **Recent Activity**:
  - Last 24 hours: 24 trades
  - Last 7 days: 155 trades
  - Last 30 days: 2175 trades

### Open Positions
- **Open Positions**: 9
- **Unique Symbols**: 3
- **Total Exposure**: $124,209.63
- **Unrealized P&L**: $3,278.97

### Account Balances (Paper Trading)
- **Average Balance**: $10,195.84
- **Lowest Balance**: $304.09
- **Highest Balance**: $126,965.26

### Top Trading Symbols (Active Bots)

- **BTC/USDT**: 13 bots
- **ETH/USDT**: 2 bots
- **SOL/USDT**: 1 bots

### Decision Activity (24h)

- **wait**: 318 decisions (avg confidence: 52.1%)
- **enter**: 24 decisions (avg confidence: 71.8%)
- **exit**: 10 decisions (avg confidence: 76.9%)

### System Health
- **Decisions (last hour)**: 13
- **Status**: 🟢 HEALTHY

## 🖥️ System Resources

### PM2 Services

| Service | Status | CPU | Memory | Uptime | Restarts |
|---------|--------|-----|--------|--------|----------|
| error-alerts | 🟢 online | 0% | 18MB | 6d 21h | 0 |
| ggbot | 🟢 online | 1.7% | 300MB | 1h 17m | 3 |
| account-monitor | 🟢 online | 0.5% | 24MB | 6d 21h | 0 |
| sebastian-chrome | 🟢 online | 0.3% | 116MB | 2h 3m | 4 |
| sebastian-bot | 🟢 online | 0.2% | 32MB | 5d 12h | 1 |
| market-data-ws | 🟢 online | 1.1% | 15MB | 6d 21h | 0 |
| sebastian-telegram | 🟢 online | 0% | 14MB | 5d 12h | 0 |

### VM Resources

- **Disk**: 58G / 78G (74%)
- **Memory**: 2.5Gi / 3.8Gi
- **CPU Load**: 0.93 / 0.53 / 0.40 (1m/5m/15m)

### Infrastructure Services

- **Redis**: 🟢 connected (Memory: 20.00M)
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

**Auto-generated** by `scripts/status_check.py` | **Updated**: 2026-02-24 10:36:10 UTC | **Design decisions**: [DOCS/DATABASE_CONTEXT.md](DOCS/DATABASE_CONTEXT.md)

**Conventions**: `?` = nullable, `=value` = non-obvious default, standard defaults (uuid, now(), 0, false) omitted

---

### account_snapshots (28 cols) | PK: snapshot_id | FK: config_id→configurations
Idx: idx_snapshots_latest(config_id, timestamp), idx_snapshots_mode_time(trading_mode, timestamp), idx_snapshots_timestamp(timestamp), idx_snapshots_user_time(user_id, timestamp)
snapshot_id uuid, config_id uuid, user_id uuid, trading_mode varchar(20), timestamp timestamptz
current_balance numeric?, available_balance numeric?, margin_used numeric?, total_pnl numeric, realized_pnl numeric?
unrealized_pnl numeric?, total_trades int, win_trades int, loss_trades int, win_rate numeric?, open_positions int
position_value numeric?, total_exposure numeric?, avg_win numeric?, avg_loss numeric?, largest_win numeric?
largest_loss numeric?, sharpe_ratio numeric?, max_drawdown numeric?, raw_data jsonb?, balance_change_pct numeric?
is_heartbeat bool?, created_at timestamptz

### activities (26 cols) | PK: activity_id | FK: config_id→configurations
Idx: idx_activities_billing(user_id, created_at, stripe_reported), idx_activities_chart_data(config_id, created_at, account_balance), idx_activities_config_billing(config_id, created_at), idx_activ...
activity_id uuid, config_id uuid, user_id uuid, activity_type text, activity_source text, summary text, details jsonb={}
trade_id text?, trade_type text?, decision_id uuid?, related_symbol text?, importance int=5, created_at timestamptz
provider varchar(50)?, model varchar(100)?, thinking_mode bool?, input_tokens int?, output_tokens int?
reasoning_tokens int?, provider_cost_usd numeric?, platform_cost_usd numeric?, stripe_reported bool?
stripe_reported_at timestamptz?, account_balance numeric?, account_pnl numeric?, total_equity numeric?

### agent_sessions (5 cols) | PK: config_id | FK: config_id→configurations
Idx: idx_agent_sessions_last_active(last_active_at), idx_agent_sessions_session_id(session_id)
config_id uuid, session_id varchar(255), last_active_at timestamp?, created_at timestamp?, updated_at timestamp?

### arena_pledges (12 cols) | PK: id | FK: config_id→configurations | UQ: tx_hash
Idx: arena_pledges_tx_hash_key(tx_hash), idx_arena_pledges_config(config_id), idx_arena_pledges_pledged_at(pledged_at), idx_arena_pledges_user(user_id), idx_arena_pledges_wallet(wallet_address)
id uuid, user_id uuid?, wallet_address text, config_id uuid?, usx_amount numeric, susx_amount numeric?, tx_hash text
pledged_at timestamptz?, competition_id uuid?, prize_amount numeric?, claimed_at timestamptz?, unstaked_at timestamptz?

### bot_telegram_channels (6 cols) | PK: config_id | FK: config_id→configurations
Idx: idx_bot_telegram_channels_chat_id(telegram_chat_id), idx_bot_telegram_channels_enabled(enabled)
config_id uuid, telegram_chat_id bigint, channel_name varchar(100)?, enabled bool?=true, created_at timestamptz?
updated_at timestamptz?

### configurations (17 cols) | PK: config_id
Idx: idx_configurations_is_public_performance(is_public_performance), idx_configurations_public(is_public_performance), idx_configurations_state(state), idx_configurations_type(config_type), idx_co...
config_id uuid, user_id uuid, config_type varchar(50), config_name varchar(100)?, config_data jsonb
created_at timestamptz, updated_at timestamptz, state text=inactive, symphony_agent_id varchar(255)?
trading_mode varchar(20)=paper' varying, is_public_performance bool?, profile_image_url text?, description text?
first_run_used bool?, free_runs_remaining int?=3, arena_registered_at timestamptz?, initial_equity numeric?

### data_points (11 cols) | PK: data_point_id | FK: source_id→data_sources | UQ: source_id,name
Idx: data_points_source_id_name_key(source_id, name), idx_data_points_name(name), idx_data_points_premium(requires_premium, enabled), idx_data_points_source(source_id, enabled, sort_order)
data_point_id uuid, source_id uuid, name varchar(50), display_name varchar(100), description text?, config_values ARRAY
requires_premium bool?, enabled bool?=true, sort_order int?, created_at timestamptz?, updated_at timestamptz?

### data_sources (9 cols) | PK: source_id | UQ: name
Idx: data_sources_name_key(name), idx_data_sources_enabled(enabled, sort_order), idx_data_sources_premium(enabled, requires_premium)
source_id uuid, name varchar(50), display_name varchar(100), description text?, enabled bool?=true
requires_premium bool?, sort_order int?, created_at timestamptz?, updated_at timestamptz?

### decisions (13 cols) | PK: decision_id | FK: config_id→configurations, parent_decision_id→decisions
Idx: idx_decisions_action_status(action, status), idx_decisions_confidence(confidence), idx_decisions_created_by(created_by), idx_decisions_parent(parent_decision_id), idx_decisions_symbol_created(...
decision_id uuid, user_id uuid, config_id uuid?, symbol varchar(20), action varchar(20), status varchar(20)?
confidence numeric, reasoning text?, prompt text?, decision_data jsonb?, parent_decision_id uuid?
created_at timestamptz, created_by text?=decision_engine_v2

### live_trades (9 cols) | PK: batch_id | FK: config_id→configurations, decision_id→decisions | UQ: decision_id
Idx: idx_live_trades_config(config_id), idx_live_trades_open(config_id, closed_at), idx_live_trades_provider(config_id, provider), idx_live_trades_provider_open(config_id, closed_at, provider), idx...
batch_id varchar(255), config_id uuid, decision_id uuid?, created_at timestamp, closed_at timestamp?
provider varchar(20)=symphony' varying, stop_loss_order_id varchar(50)?, take_profit_order_id varchar(50)?
symbol varchar(20)?

### llm_models (16 cols) | PK: model_id | UQ: openrouter_model_id
Idx: idx_llm_models_enabled(enabled, sort_order), idx_llm_models_provider(provider), llm_models_openrouter_model_id_key(openrouter_model_id)
model_id varchar(50), display_name varchar(100), provider varchar(50), openrouter_model_id varchar(100)
supports_thinking bool=true, enabled bool=true, max_context_tokens int, context_display varchar(20)
pricing_input_per_1m numeric, pricing_output_per_1m numeric, cost_per_decision_standard numeric
cost_per_decision_thinking numeric, description text?, sort_order int, created_at timestamptz, updated_at timestamptz

### logs (6 cols) | PK: log_id
Idx: idx_logs_level_timestamp(log_level, timestamp), idx_logs_user_timestamp(user_id, timestamp)
log_id int, user_id uuid?, module varchar(100)?, log_level varchar(10), message text, timestamp timestamptz

### market_data (9 cols) | PK: id | FK: config_id→configurations | UQ: user_id,config_id,symbol,timeframe
Idx: idx_market_data_config_symbol(config_id, symbol), idx_market_data_updated_at(updated_at), idx_market_data_user_symbol_timeframe(user_id, symbol, timeframe, updated_at), market_data_unique_per_...
id int, user_id uuid, config_id uuid?, symbol varchar(20), timeframe varchar(10), data_points jsonb?, raw_data jsonb
updated_at timestamptz, data_source uuid?

### paper_accounts (13 cols) | PK: account_id | FK: config_id→configurations | UQ: config_id
Idx: idx_paper_accounts_user(user_id), paper_accounts_config_id_key(config_id)
account_id uuid, user_id uuid, config_id uuid, initial_balance numeric, current_balance numeric, total_pnl numeric
open_positions int, total_trades int, win_trades int, loss_trades int, created_at timestamptz, updated_at timestamptz
last_reset_at timestamptz?

### paper_orders (9 cols) | PK: order_id | FK: trade_id→paper_trades
Idx: idx_paper_orders_filled_at(filled_at), idx_paper_orders_trade(trade_id), idx_paper_orders_user(user_id)
order_id uuid, user_id uuid, trade_id uuid, order_type varchar(20), side varchar(10), filled_price numeric, size numeric
fees numeric, filled_at timestamptz

### paper_trades (22 cols) | PK: trade_id | FK: account_id→paper_accounts, config_id→configurations, decision_id→decisions
Idx: idx_paper_trades_account(account_id), idx_paper_trades_close_reason(close_reason), idx_paper_trades_config_status(config_id, status, opened_at), idx_paper_trades_decision(decision_id), idx_pap...
trade_id uuid, user_id uuid, account_id uuid, config_id uuid, decision_id uuid?, symbol varchar(20), side varchar(10)
entry_price numeric, current_price numeric?, size_usd numeric, leverage int=1, unrealized_pnl numeric?
realized_pnl numeric?, status varchar(20)=open' varying, stop_loss numeric?, take_profit numeric?
confidence_score numeric?, opened_at timestamptz, closed_at timestamptz?, margin_used numeric?
close_reason varchar(50)?, liquidation_price numeric?

### stripe_webhooks (11 cols) | PK: webhook_id | UQ: stripe_event_id
Idx: idx_stripe_webhooks_customer(stripe_customer_id), idx_stripe_webhooks_event_id(stripe_event_id), idx_stripe_webhooks_event_type(event_type), idx_stripe_webhooks_processed(processed, created_at...
webhook_id uuid, stripe_event_id varchar(100), event_type varchar(50), stripe_customer_id varchar(100)?
stripe_subscription_id varchar(100)?, event_data jsonb, processed bool?, processed_at timestamptz?, error_message text?
retry_count int?, created_at timestamptz?

### trade_observations (14 cols) | PK: observation_id | FK: config_id→configurations, trade_id→paper_trades
Idx: idx_trade_observations_config(config_id), idx_trade_observations_config_importance_created(config_id, importance, created_at), idx_trade_observations_config_type_created(config_id, observation...
observation_id uuid, config_id uuid, user_id uuid, trade_id uuid?, observation_type text, what_went_well text?
what_went_wrong text?, predictive_data_points jsonb?, decision_review text?, trade_pnl numeric?
trade_duration_minutes int?, importance int?=5, created_at timestamptz?, batch_id varchar(255)?

### user_llm_credentials (7 cols) | PK: id | UQ: user_id,credential_name
Idx: idx_user_llm_credentials_provider(user_id, provider), idx_user_llm_credentials_user_id(user_id), user_llm_credentials_user_id_credential_name_key(user_id, credential_name)
id uuid, user_id uuid, credential_name text, provider text, vault_secret_id uuid, created_at timestamptz?
updated_at timestamptz?

### user_profiles (20 cols) | PK: user_id
Idx: idx_user_profiles_paid_data_points(paid_data_points), idx_user_profiles_stripe(stripe_customer_id), idx_user_profiles_subscription(subscription_tier, subscription_status), idx_user_profiles_te...
user_id uuid, subscription_tier enum?=free, subscription_status enum?=active, subscription_expires_at timestamptz?
stripe_customer_id varchar(100)?, stripe_subscription_id varchar(100)?, telegram_user_id bigint?
telegram_username varchar(50)?, telegram_chat_id bigint?, monthly_signal_count int?, created_at timestamptz?
updated_at timestamptz?, paid_data_points ARRAY?, symphony_vault_id uuid?, symphony_smart_account varchar(42)?
aster_vault_id uuid?, aster_user_wallet varchar(42)?, aster_wallet varchar(42)?, hyperliquid_wallet_address varchar(42)?
hyperliquid_vault_id uuid?

---

## 🎯 Domain Models & Business Logic

Business logic on top of DB tables. See [DOCS/DATABASE_CONTEXT.md](DOCS/DATABASE_CONTEXT.md) for design decisions.

---

### UserProfile (core/domain/user_profile.py) — User profile entity extending Supabase authentication with business model.
Fields: user_id: str, subscription_tier: SubscriptionTier, subscription_status: SubscriptionStatus, created_at: datetime, updated_at: datetime, sub...
@property: `is_free_tier` (Check if user is on free tier.) | `is_pro_tier` (Check if user has pro subscription.) | `is_prepaid_tier` (Check if user is on prepaid (credit pack) tier.) | `requires_credit_check` (Check if user requires hard credit balance check before L...) | `has_active_subscription` (Check if user has active subscription.) | `subscription_expired` (Check if subscription has expired.) | `can_activate_bots` (MASTER PERMISSION: Check if user can activate/run bots.) | `can_use_agents` (Check if user can create and use agents (PRO tier only).) | `is_premium_user` (DEPRECATED: Use can_activate_bots instead.) | `can_use_premium_features` (DEPRECATED: Use can_activate_bots instead.) | `requires_own_llm_keys` (DEPRECATED: Platform provides LLM keys for all paid users.) | `can_publish_telegram_signals` (DEPRECATED: Use can_activate_bots instead.) | `can_use_signal_validation` (DEPRECATED: Use can_activate_bots instead.) | `can_use_live_trading` (DEPRECATED: Use can_activate_bots instead.) | `has_telegram_integration` (Check if user has Telegram integration configured.) | `has_stripe_integration` (Check if user has Stripe customer record.)

### DecisionData (core/domain/decision.py) — Flexible decision context storage (replaces decision_data JSONB field).
Fields: trade_id: Optional[str], stop_loss_price: Optional[float], take_profit_price: Optional[float], position_size: Optional[float], entry_price:...

### Decision (core/domain/decision.py) — Unified decision entity representing all AI decision-making in the system.
Fields: decision_id: str, user_id: str, symbol: Symbol, action: DecisionAction, confidence: Confidence, reasoning: Optional[str], created_at: datet...
@property: `is_actionable` (Check if this decision represents an actionable trade sig...) | `is_entry_signal` (Check if this is an entry signal (BUY).) | `is_exit_signal` (Check if this is an exit signal (SELL).) | `is_wait_signal` (Check if this is a wait decision.) | `is_approved` (Check if decision was approved (for signal validation).) | `is_rejected` (Check if decision was rejected.) | `has_parent` (Check if this decision is linked to a parent decision.) | `is_high_confidence` (Check if decision meets high confidence threshold.) | `is_user_config_based` (Check if decision is based on user configuration (vs. sys...) | `is_system_signal` (Check if decision is from system signals (e.g., ggShot).)

### PriceLevel (core/domain/position.py) — Value object representing a price level with timestamp.
Fields: price: Decimal, timestamp: datetime
@property: `age_seconds` (Get age of this price level in seconds.)

### PositionMetrics (core/domain/position.py) — Value object containing position performance metrics.
Fields: unrealized_pnl: Money, unrealized_pnl_pct: Decimal, realized_pnl: Money, total_pnl: Money, max_profit: Money, max_loss: Money, current_risk...
@property: `is_profitable` (Check if position is currently profitable.) | `is_losing` (Check if position is currently losing money.)

### Position (core/domain/position.py) — Entity representing a trading position with full lifecycle management.
Fields: trade_id: str, config_id: str, symbol: Symbol, side: PositionSide, status: PositionStatus, size_usd: Money, leverage: Decimal, collateral_a...
@property: `is_active` (Check if position is currently active.) | `is_pending` (Check if position is pending execution.) | `is_closed` (Check if position has been closed.) | `time_in_position` (Get time spent in position.)

### Indicator (core/domain/market_data.py) — Value object representing a single technical indicator.
Fields: name: str, timeframe: str, value: Any, calculation_time: datetime, metadata: Dict[str, Any]
@property: `indicator_key` (Get standardized indicator key (e.g., 'RSI_1h').) | `age_seconds` (Get age of indicator in seconds.)

### VolumeData (core/domain/market_data.py) — Value object for volume analysis data.
Fields: current_volume: Decimal, average_volume: Decimal, volume_ratio: Decimal, timeframe: str, period_used: int, timestamp: datetime
@property: `volume_increase_pct` (Get volume increase percentage above average.) | `confidence_level` (Get volume confidence level based on ggShot criteria.)

### PriceData (core/domain/market_data.py) — Value object for current price information.
Fields: symbol: Symbol, price: Decimal, timestamp: datetime, source: DataSource, bid: Optional[Decimal], ask: Optional[Decimal], volume_24h: Option...
@property: `age_seconds` (Get age of price data in seconds.) | `spread` (Get bid-ask spread if available.)

### MarketDataSnapshot (core/domain/market_data.py) — Entity representing a complete market data snapshot for a symbol.
Fields: id: str, symbol: Symbol, data_source: DataSource, extracted_at: datetime, indicators: Dict[str, Indicator], price_data: Optional[PriceData]...
@property: `age_seconds` (Get age of this market data snapshot in seconds.) | `freshness_level` (Get overall freshness level of this snapshot.)

### DataSource (core/domain/data_source.py) — Data source entity for categorizing extraction sources.
Fields: source_id: str, name: str, display_name: str, enabled: bool, requires_premium: bool, sort_order: int, created_at: datetime, updated_at: dat...

### DataPoint (core/domain/data_source.py) — Data point entity representing specific indicators/signals within a data source.
Fields: data_point_id: str, source_id: str, name: str, display_name: str, config_values: list[str], enabled: bool, requires_premium: bool, sort_ord...
@property: `is_premium` (Check if this data point requires premium access.) | `is_available` (Check if this data point is available for use.)

### DataSourceWithPoints (core/domain/data_source.py) — Composite entity containing a data source with its associated data points.
Fields: source: DataSource, data_points: list[DataPoint]

---

## ⚙️ Configuration Structure (config_data JSONB)

Source: `core/config/models.py` | Auto-generated 2026-02-24 10:36:10 UTC

- `schema_version`: str=1.0 — Configuration schema version
- `selected_pair`: Optional[str] — Trading pair to analyze
- `extraction`: Optional[ExtractionConfig] — Extraction module configuration
- `decision`: Optional[DecisionConfig] — Decision module configuration
- `llm_config`: Optional[LLMConfig] — LLM provider and API key configuration
- `trading`: TradingConfig — Trading module configuration
- `telegram_integration`: Optional[TelegramIntegrationConfig] — Telegram integration configuration
- `agent_strategy`: Optional[AgentStrategy] — Agent strategy configuration

---
