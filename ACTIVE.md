# 🚀 ACTIVE - ggbots System Status

**Last Updated**: 2025-10-27 (Agent Phase 2 complete)
**System Health**: 🟢 Production Live (257 users, 59 active bots)
**Project Status**: Live application with complete Stripe monetization and Symphony live trading

---

## 🎯 Current Development Focus

**Primary Objectives**:
- **Autonomous Trading Agent**: 🔄 Phase 2 COMPLETE (MCP server + 9 tools), Phase 3 in progress (Agent runner)
- **Market Intelligence Expansion**: ✅ **PHASE 1 PRODUCTION DEPLOYED!** - 8 new Grok-powered data sources LIVE (VIX, DXY, CPI, NFP, BTC TVL, whale activity, Twitter sentiment, crypto news)
- **Live Trading Polish**: Symphony integration refinement (trade queries, metrics, position display)

**Architecture Status**: V2 orchestrator complete, Intelligence Orchestrator **production deployed** with parallel query execution, GrokAgenticAdapter operational, Symphony live trading operational, Agent MCP server implemented with trade observations model


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
- `GET /api/v2/account/live/{config_id}` - Account metrics from Symphony
- `GET /api/v2/trades/live/{config_id}` - Trade history from Symphony
- `GET /api/dashboard-stream` - SSE stream with unified paper + live data

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

## 🗄️ Database Schema

### **Database Architecture Philosophy**

**Universal Data Layer Pattern**:
- `market_data` table stores ALL market intelligence (technical indicators, signals, news, sentiment)
- `data_sources` + `data_points` = metadata registry defining what's available
- **Intelligence Orchestrator**: Config-driven routing queries gateway based on `config.extraction.selected_data_sources`
- **Do NOT create new tables for new data types** - extend existing architecture
- See `database/schema.md` for complete schema documentation and `market_intelligence/README.md` for orchestrator details

**Example**: ggShot signals stored in `market_data` with `data_source='signals_group_chats'`
**Orchestrator**: Reads config → maps data points to catalog → queries MarketIntelligence gateway → returns aggregated results

---

### Core Tables (13 total)
| Table | Purpose |
|-------|---------|
| **user_profiles** | User accounts, subscription tier (free/ggbase), Stripe integration, Telegram settings |
| **user_llm_credentials** | Encrypted LLM API keys via Supabase Vault (OpenAI, DeepSeek, Anthropic, XAI) |
| **configurations** | Bot configs with `config_data` JSONB (symbol, timeframe, strategy, data sources) |
| **bot_telegram_channels** | Per-bot Telegram signal publishing configuration |
| **data_sources** | Market intelligence categories (7 total: Technical Analysis, Trading Signals, On-Chain Analytics, Derivatives & Leverage, Sentiment & Social, News & Regulatory, Macro Economics) |
| **data_points** | Specific indicators/signals within sources (24 total: 21 technical, 1 ggShot signal, 2 funding rates) |
| **decisions** | AI decision audit trail (action, confidence, reasoning, market_data snapshot) |
| **paper_accounts** | Isolated $10K paper trading accounts per config |
| **paper_trades** | Paper trade execution records (entry, exit, P&L, confidence) |
| **paper_orders** | Paper order fills (market/limit orders, fees) |
| **live_trades** | Symphony live trade batch tracking (links decision_id to Symphony batch_id) |
| **stripe_webhooks** | Stripe event log for subscription management (idempotent processing) |
| **logs** | System logging (module, level, message, user context) |

**Key Architecture Notes**:
- `data_sources` + `data_points`: Infrastructure complete, 3 sources populated (Technical Analysis, Trading Signals, Derivatives & Leverage), 4 planned categories ready for expansion
- `config_data` JSONB stores user selections: `extraction.selected_data_sources[source_name].data_points[]`
- All tables use Row Level Security (RLS) for multi-user isolation

**7 Market Intelligence Categories** (32 data points **LIVE IN PRODUCTION**):
1. **Technical Analysis** 🆓 (21 indicators) - Momentum, trend, volatility, volume analysis
2. **Trading Signals** 💎 (1 source: ggShot) - AI-filtered signals from expert sources (third-party subscription)
3. **On-Chain Analytics** 🆓 (2 live: BTC TVL, whale activity) - Grok-powered via web search, ~$0.015/query
4. **Derivatives & Leverage** 🆓 (2 rates: BTC/ETH funding) - Binance API, real-time, FREE
5. **Sentiment & Social** 🆓 (1 live: Twitter sentiment) - Grok-powered via X search + NLP, ~$0.06/query
6. **News & Regulatory** 🆓 (1 live: crypto news) - Grok-powered via web + X search, ~$0.015/query
7. **Macro Economics** 🆓 (4 live: VIX, DXY, CPI, NFP) - Grok-powered via web search, ~$0.0015-0.009/query

**GrokAgenticAdapter**: Universal intelligence via XAI's agentic API - handles all 8 Grok data sources with ONE adapter!
**Cost Economics**: ~$195/month platform cost = $0.76/user/month (257 users), scales to $0.20/user at 1000 users
**Performance**: Parallel query execution (~30s for all 8 data points), custom cache TTL per data point (10min to 24hrs)

---

## 🎨 Frontend Components (Forge)

### Configuration & Setup (`configure/`)
| Component | Purpose |
|-----------|---------|
| **MarketDataSelector** | Data sources/indicators selection UI with category tabs, search, premium gates |
| **SignalsConfiguration** | ggShot signals toggle, confidence threshold, processing mode settings |
| **StrategyEditor** | Custom strategy prompt editor with AI model selection |
| **TradeSettings** | Trading parameters (leverage, SL/TP, position sizing) |
| **ConfigTabs** | Tab navigation for configuration wizard steps |
| **ConfigureLayout** | Main configuration page layout wrapper |
| **SaveConfigBar** | Sticky save bar with validation status |

### Monitoring & Analytics (`monitor/`)
| Component | Purpose |
|-----------|---------|
| **PerformanceChart** | Cumulative P&L chart with paper/live mode support |
| **PositionsTable** | Open positions table with real-time P&L, manual close buttons |
| **DecisionFeed** | Live decision stream (ENTER/EXIT/WAIT) with reasoning |
| **MetricsBar** | Top-level metrics (total P&L, win rate, open positions) |
| **ActivationBar** | Bot activation controls with schedule display |
| **TradeHistoryModal** | Historical trades modal (last 50 trades, filters) |

### Layout & Navigation (`layout/`)
| Component | Purpose |
|-----------|---------|
| **BotRail** | Left sidebar with bot list, create button, settings |
| **BotManagementMenu** | Dropdown menu for duplicate/delete/settings actions |
| **Header** | Top header with branding, nav links, user profile |
| **TabNavigation** | Main tab navigation (Configure, Monitor, Settings) |
| **MobileNav** | Mobile-responsive navigation drawer |
| **UserProfile** | User profile dropdown with subscription badge, billing portal |

### Shared Utilities (`shared/`)
| Component | Purpose |
|-----------|---------|
| **LoadingSkeleton** | Loading state skeletons for async content |
| **EmptyState** | Empty state placeholders with CTAs |
| **ThemeToggle** | Dark/light mode toggle |

**Key Frontend Notes**:
- All components read from `/api/v2/data-sources-with-points` to populate UI dynamically
- Premium features gated via `usePermissions()` hook checking user profile
- Real-time updates via WebSocket (`/ws/bot-status/{user_id}`) and SSE (`/api/dashboard-stream`)

---

## ✅ Production-Ready Features

### **Autonomous Scheduler System**
- **Zero-drift execution** at candle boundaries (e.g., 09:35:30 for 5-minute bots)
- **Redis idempotency** prevents duplicate trades across restarts
- **Multi-timeframe support**: 5m, 15m, 30m, 1h, 4h, 1d
- **Real-time rescheduling** when users change bot configurations
- **Startup reconciliation** automatically restores active bots

### **Signal Validation & Intelligence System**
- **Dual-mode architecture**: Signal validation (push-based) + Autonomous trading context (pull-based)
- **ggShot integration**: 878 historical signals + real-time storage in market_data table
- **AI confidence evaluation** of external signals using user strategies
- **Multi-timeframe signals**: Latest signal per timeframe for autonomous decision context
- **Premium gating** through ggBase subscription tier (paid_data_points enforcement)
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
- **Default risk management** - SL/TP from config applied if decision doesn't provide them
- **Idempotency protection** - prevents duplicate trades on retry
- **Position management** - open, close, and query live positions
- **Dashboard integration** - SSE stream enriches live data from Symphony API
- **Unified UX** - PerformanceChart and PositionsTable support both modes
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
