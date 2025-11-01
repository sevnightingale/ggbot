# 🚀 ACTIVE - ggbots System Status

**Last Updated**: 2025-11-01 09:00:04 UTC (Auto-updated by status_check.py)
**System Health**: 🟢 HEALTHY

## 📊 Live Platform Metrics

### Users & Subscriptions
- **Total Users**: 258
- **Pro Users (ggbase)**: 3 (2 active subscriptions)
- **Free Users**: 255
- **Users with Bots**: 252 (97.7%)

### Bot Statistics
- **Total Bots**: 383
- **Active Bots**: 60 (15.7%)
  - Paper Trading: 60
  - Live Trading: 0
- **Inactive Bots**: 323
- **Avg Bots per User**: 1.5

### Trading Activity
- **Total Trades (All Time)**: 5,407
  - Wins: 1,619
  - Losses: 3,788
  - Platform Win Rate: 29.94%
  - Total P&L: $-16,040.97
- **Recent Activity**:
  - Last 24 hours: 189 trades
  - Last 7 days: 1582 trades
  - Last 30 days: 4243 trades

### Open Positions
- **Open Positions**: 25
- **Unique Symbols**: 4
- **Total Exposure**: $28,912.04
- **Unrealized P&L**: $140.27

### Account Balances (Paper Trading)
- **Average Balance**: $9,925.12
- **Lowest Balance**: $3,470.91
- **Highest Balance**: $10,420.76

### Top Trading Symbols (Active Bots)

- **BTC/USDT**: 47 bots
- **BNB/USDT**: 3 bots
- **SOL/USDT**: 2 bots
- **W/USDT**: 2 bots
- **HBAR/USDT**: 2 bots

### Decision Activity (24h)

- **wait**: 2438 decisions (avg confidence: 51.6%)
- **enter**: 193 decisions (avg confidence: 59.3%)
- **exit**: 92 decisions (avg confidence: 74.1%)

### System Health
- **Decisions (last hour)**: 55
- **Status**: 🟢 HEALTHY

## 🖥️ System Resources

### PM2 Services

| Service | Status | CPU | Memory | Uptime | Restarts |
|---------|--------|-----|--------|--------|----------|
| signal-listener | 🟢 online | 0% | 54MB | 2h 32m | 19 |
| x-bot | 🟢 online | 0.8% | 29MB | 2h 32m | 19 |
| error-alerts | 🟢 online | 0% | 28MB | 2h 32m | 26 |
| ggbot | 🟢 online | 76.1% | 226MB | 2h 32m | 150 |
| market-data-ws | 🟢 online | 0.3% | 170MB | 2h 32m | 21 |

### VM Resources

- **Disk**: 35G / 78G (45%)
- **Memory**: 2.7Gi / 3.8Gi
- **CPU Load**: 0.88 / 0.55 / 0.71 (1m/5m/15m)

### Infrastructure Services

- **Redis**: 🟢 connected (Memory: 10.97M)
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
