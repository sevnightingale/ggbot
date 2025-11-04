# 🚀 ACTIVE - ggbots System Status

**Last Updated**: 2025-11-04 13:58:21 UTC (Auto-updated by status_check.py)
**System Health**: 🟢 HEALTHY

## 📊 Live Platform Metrics

### Users & Subscriptions
- **Total Users**: 258
- **Pro Users (ggbase)**: 3 (2 active subscriptions)
- **Free Users**: 255
- **Users with Bots**: 252 (97.7%)

### Bot Statistics
- **Total Bots**: 377
- **Active Bots**: 3 (0.8%)
  - Paper Trading: 2
  - Live Trading: 0
- **Inactive Bots**: 374
- **Avg Bots per User**: 1.5

### Trading Activity
- **Total Trades (All Time)**: 5,452
  - Wins: 1,635
  - Losses: 3,817
  - Platform Win Rate: 29.99%
  - Total P&L: $-16,000.65
- **Recent Activity**:
  - Last 24 hours: 0 trades
  - Last 7 days: 980 trades
  - Last 30 days: 4178 trades

### Open Positions
- **Open Positions**: 0
- **Unique Symbols**: 0
- **Total Exposure**: $0.00
- **Unrealized P&L**: $0.00

### Account Balances (Paper Trading)
- **Average Balance**: $9,926.33
- **Lowest Balance**: $3,905.05
- **Highest Balance**: $10,420.76

### Top Trading Symbols (Active Bots)

- **ADA/USDT**: 1 bots
- **BTC/USDT**: 1 bots
- **DASH/USDT**: 1 bots

### Decision Activity (24h)

- **wait**: 22 decisions (avg confidence: 22.0%)
- **exit**: 1 decisions (avg confidence: 85.0%)

### System Health
- **Decisions (last hour)**: 1
- **Status**: 🟢 HEALTHY

## 🖥️ System Resources

### PM2 Services

| Service | Status | CPU | Memory | Uptime | Restarts |
|---------|--------|-----|--------|--------|----------|
| signal-listener | 🟢 online | 0% | 16MB | 9h 58m | 34 |
| x-bot | 🟢 online | 0% | 18MB | 9h 58m | 34 |
| error-alerts | 🟢 online | 0% | 17MB | 9h 58m | 41 |
| market-data-ws | 🟢 online | 1.9% | 23MB | 9h 58m | 36 |
| ggbot | 🟢 online | 1.7% | 259MB | 1h 57m | 91 |
| agent-bb2560fd-b053-464f-8a58-8e254e4d36fa | 🟢 online | 0% | 63MB | 1h 57m | 7 |

### VM Resources

- **Disk**: 35G / 78G (46%)
- **Memory**: 2.0Gi / 3.8Gi
- **CPU Load**: 0.15 / 0.23 / 0.18 (1m/5m/15m)

### Infrastructure Services

- **Redis**: 🟢 connected (Memory: 10.36M)
- **Supabase PostgreSQL**: 🟢 connected (Remote managed service)

---

## 🌐 API Access Points

### Production Endpoints
| Service | URL | Status | Purpose |
|---------|-----|--------|---------|
| **V2 Orchestrator** | `https://ggbots-api.nightingale.business` | ✅ | Main backend API |
| **Frontend** | `https://ggbot-app.vercel.app` | ✅ | Next.js application |

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

**Agent Management** (Phase 4a)
- `POST /api/v2/agent/{config_id}/start` - Start agent in strategy_definition or autonomous mode
- `POST /api/v2/agent/{config_id}/stop` - Stop agent and cleanup Redis queues
- `POST /api/v2/agent/{config_id}/message` - Send message to agent via Redis queue
- `GET /api/v2/agent/{config_id}/poll-response` - Poll for agent responses (non-blocking)
- `GET /api/v2/agent/{config_id}/status` - Get agent process status

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

**Stripe Subscription Management**
- `POST /api/v2/create-checkout-session` - Create Stripe checkout session
- `POST /api/v2/stripe-webhook` - Handle Stripe webhook events
- `POST /api/v2/create-portal-session` - Create Stripe billing portal session

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
- **Telegram Publishing**: Signal broadcasting to user channels (APPROVED/REJECTED status)
- **REST API**: 30+ endpoints for bot control, positions, analytics

### **market-data-ws Service**
- **Real-time Binance WebSocket**: Live prices for 100 symbols × 7 timeframes (700 datasets)
- **Redis Cache**: Sub-millisecond price access (~1s freshness)
- **Position P&L Updates**: Real-time unrealized P&L calculations
- **Liquidation Monitoring**: Automatic position liquidation when losses exceed margin

### **signal-listener Service**
- **ggShot Integration**: External signal validation from Telegram
- **AI Confidence Evaluation**: Validates signals using user-defined strategies
- **Service Authentication**: Dedicated `/api/v2/signal-validation` endpoint
- **Multi-timeframe Storage**: Latest signal per timeframe for autonomous context
- **Premium Gating**: ggBase subscription enforcement

### **x-bot Service**
- **Platform Status Tweets**: Automated updates on @ggbots_ai
- **Engagement Monitoring**: Twitter community interaction

### **error-alerts Service**
- **Error Monitoring**: Catches and reports system errors
- **Telegram Alerts**: Real-time notifications to admin channels

### **Market Intelligence**
**32 data points across 7 categories (8 Grok-powered sources LIVE):**
- **Technical Analysis** (21 indicators): RSI, MACD, Bollinger Bands, volume, momentum, trend
- **Trading Signals** (1 source): ggShot AI-filtered signals (premium)
- **On-Chain Analytics** (2 live): BTC TVL, whale activity
- **Derivatives & Leverage** (2 rates): BTC/ETH funding rates
- **Sentiment & Social** (1 live): Twitter sentiment analysis
- **News & Regulatory** (1 live): Crypto news aggregation
- **Macro Economics** (4 live): VIX, DXY, CPI, NFP

### **Trading Modes**
- **Paper Trading**: Virtual $10k accounts, risk-free testing
- **Live Trading**: Symphony.io integration (premium feature, ggBase required)
- **AsterDEX Trading**: Decentralized futures (33 symbols, up to 20x leverage, competition-ready)

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
| **6379** | Redis | Localhost | WebSocket cache, live prices, scheduler idempotency |

### System Ports
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| **22** | SSH | Public | Remote access |
| **80** | HTTP | Public | Web server |
| **443** | HTTPS | Public | Secure web server |

---

## 🔄 Background Tasks

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

# Logs
pm2 logs ggbot
pm2 logs market-data-ws

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

### Pro Plan Features ($29/month)
| Feature | Free Plan | Pro Plan |
|---------|-----------|----------|
| **Active Bots** | 1 bot | 10 bots |
| **Analysis Frequency** | 1 hour minimum | 5 minutes minimum |
| **AI Models** | Default Model | Frontier Reasoning Models (GPT-5, Claude Opus 4, Grok 4, DeepSeek R1) |
| **Live Trading** | ❌ | ✅ (Symphony.io integration) |
| **Telegram Publishing** | ❌ | ✅ |
| **Priority Support** | ❌ | ✅ |

### Stripe Integration
**Backend API Endpoints** (`/api/v2/`):
- `POST /create-checkout-session` - Create Stripe Checkout with 14-day free trial
- `POST /stripe-webhook` - Handle subscription events (HMAC verified)
- `POST /create-portal-session` - Stripe billing portal for self-service management
- `GET /me` - User profile with subscription status

**Frontend Components**:
- `<UpgradeModal>` - Pricing modal with monthly/annual toggle
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

**Last Updated**: 2025-11-04 13:58:22 UTC

---

### `activities` (14 columns)

**Primary Key**: `activity_id`

**Foreign Keys**:
- `config_id` → `configurations(config_id)`

**Indexes**:
- `idx_activities_config_time` on (config_id, created_at)
- `idx_activities_decision` on (decision_id)
- `idx_activities_priority` on (config_id, priority, created_at)
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
| `trade_id` | uuid | ✓ |  |
| `trade_type` | text | ✓ |  |
| `decision_id` | uuid | ✓ |  |
| `related_symbol` | text | ✓ |  |
| `priority` | integer |  | 2 |
| `importance` | integer |  | 5 |
| `created_at` | timestamp with time zone |  | now() |

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

### `configurations` (10 columns)

**Primary Key**: `config_id`

**Indexes**:
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
| `trading_mode` | character varying(20) | ✓ | 'paper'::character varying |

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

### `user_profiles` (15 columns)

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
- `is_ggbase_tier` - Check if user has ggbase subscription.
- `is_premium_user` - Check if user has any premium subscription.
- `has_active_subscription` - Check if user has active subscription.
- `subscription_expired` - Check if subscription has expired.
- `can_use_premium_features` - Check if user can access premium features.
- `requires_own_llm_keys` - Check if user must provide their own LLM API keys.
- `can_publish_telegram_signals` - Check if user can publish signals to Telegram.
- `can_use_signal_validation` - Check if user can use signal validation mode.
- `can_use_live_trading` - Check if user can use Symphony live trading.
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

**Last Updated**: 2025-11-04 13:58:22 UTC

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
