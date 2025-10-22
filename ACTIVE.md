# 🚀 ACTIVE - ggbots System Status

**Last Updated**: 2025-10-22 (Documentation restructure - history moved to CHANGELOG.md)
**System Health**: 🟢 Production Live (225+ users, 100+ active bots)
**Project Status**: Live application with complete Stripe monetization and Symphony live trading

---

## 🎯 Current Development Focus

**Production Status**: Live platform with 225+ active users managing 100+ autonomous trading bots

**Primary Objectives**:
- **Live Trading Polish**: Symphony integration refinement (trade queries, metrics, position display)
- **User Experience**: Status messaging improvements, mobile responsiveness, API key management
- **System Reliability**: Error handling, monitoring, comprehensive testing

**Architecture Status**: V2 implementation complete, Symphony live trading operational

---

## 🌐 API Access Points

### Production Endpoints
| Service | URL | Status | Purpose |
|---------|-----|--------|---------|
| **V2 Orchestrator** | `https://ggbots-api.nightingale.business` | ✅ | Main backend API |
| **Frontend** | `https://ggbot-app.vercel.app` | ✅ | Next.js application |

### Core API Endpoints
**Bot Control & Scheduling**
- `POST /api/v2/bot/{config_id}/start` - Start autonomous bot with scheduling
- `POST /api/v2/bot/{config_id}/stop` - Stop bot and remove scheduler jobs
- `GET /api/v2/scheduler/status` - Active scheduled jobs per user
- `GET /api/v2/bot/{config_id}/status` - Real-time bot status
- `WS /ws/bot-status/{user_id}` - WebSocket for real-time updates

**Symbol Validation**
- `GET /api/v2/symbols/supported` - Get all 141 supported trading symbols
- `GET /api/v2/symbols/search/{query}` - Search symbols by base currency

**Signal Processing**
- `POST /api/v2/signal-validation/{config_id}` - Service-to-service signal validation endpoint
- `POST /api/v2/orchestrate/{config_id}` - General orchestration endpoint
- Signal listener service (PM2 background process with service authentication)

**Trading & Analytics**
- `GET /api/live-position-data` - Current positions with real-time P&L
- `POST /paper/execute` - Execute paper trades
- `GET /paper/positions/{config_id}` - Position tracking

**Symphony Live Trading**
- `POST /api/v2/symphony/setup` - Store Symphony API credentials
- `GET /api/v2/symphony/status` - Check connection status
- `POST /api/v2/symphony/disconnect` - Remove credentials & disable live bots
- `GET /api/v2/positions/live/{config_id}` - Query Symphony positions
- `POST /api/v2/positions/live/{batch_id}/close` - Close live position
- `POST /api/v2/config/duplicate-as-live` - Duplicate paper bot as live bot

---

## 📊 System Architecture

### Core Services (PM2)
| Service | Status | CPU | Memory | Purpose |
|---------|--------|-----|--------|---------|
| ggbot | 🟢 Online | 0% | ~205MB | V2 Orchestrator API server with integrated scheduler & telegram publishing |
| market-data-ws | 🟢 Online | 0% | ~140MB | Real-time WebSocket market data cache (100 symbols × 7 timeframes = 700 datasets) |
| signal-listener | 🟢 Online | 0% | ~62MB | External signal processing service (ggShot integration) |
| x-bot | 🟢 Online | 0% | ~41MB | X (Twitter) bot for @ggbots_ai - automated platform status tweets and engagement |
| error-alerts | 🟢 Online | 0% | ~20MB | Error monitoring and Telegram alert service |

### PM2 Modules
| Module | Status | Purpose |
|--------|--------|---------|
| pm2-logrotate | ✅ Installed | Automated log rotation and compression (10MB rotation, 5 files max) |

### Infrastructure Services
| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| Supabase PostgreSQL | 🟢 Online | Remote | Main application database (managed) |
| Redis | 🟢 Online | 6379 | WebSocket cache, live prices, scheduler idempotency |

---

## ✅ Production-Ready Features

### **Autonomous Scheduler System**
- **Zero-drift execution** at candle boundaries (e.g., 09:35:30 for 5-minute bots)
- **Redis idempotency** prevents duplicate trades across restarts
- **Multi-timeframe support**: 5m, 15m, 30m, 1h, 4h, 1d
- **Real-time rescheduling** when users change bot configurations
- **Startup reconciliation** automatically restores active bots

### **Signal Validation System**
- **Generic framework** supporting multiple signal sources (ggShot implemented)
- **AI confidence evaluation** of external signals using user strategies
- **Premium gating** through ggBase subscription tier
- **Service-to-service authentication** with dedicated `/api/v2/signal-validation` endpoint
- **Telegram publishing** to user-specified channels with APPROVED/REJECTED status
- **Complete V2 integration** using standard extraction → decision → trading flow

### **Paper Trading Engine**
- **Live WebSocket prices** from Binance (sub-millisecond Redis access, ~1s freshness)
- **$10,000 isolated accounts** per configuration
- **3-second position monitoring** ACTIVE (batch SQL updates for efficiency)
- **Liquidation system** - automatic position liquidation when losses exceed margin
- **Confidence-based position sizing**
- **Real-time updates** - position P&L calculated with live streaming prices

### **Symphony Live Trading**
- **Production-ready integration** for real-money trading via Symphony.io
- **100 compatible symbols** out of 141 total supported trading pairs
- **Encrypted credential storage** using Supabase Vault
- **Smart routing** - paper vs live mode per bot configuration
- **Idempotency protection** - prevents duplicate trades on retry
- **Position management** - open, close, and query live positions
- **Premium feature** - ggbase subscription required

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
