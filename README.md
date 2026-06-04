<p align="center">
  <img src="frontend/public/ggbots_logo.svg" alt="ggbots" width="320" />
</p>

<h3 align="center">Autonomous AI trading agents that trade like you</h3>

<p align="center">
  <a href="https://ggbots.ai"><strong>ggbots.ai</strong></a> · Live in production — real-money execution on Hyperliquid, 24/7
</p>

---

**ggbots** is a full-stack platform for creating, customizing, and deploying autonomous AI trading agents. Users describe their strategy in natural language; the platform turns it into a bot that gathers market intelligence, reasons over it with frontier LLMs, and executes trades on a fixed schedule aligned to candle boundaries — on a simulated paper account or live on Hyperliquid with non-custodial API wallets.

Designed, built, and operated end-to-end by a single engineer: Python backend, Next.js frontend, real-time data infrastructure, LLM orchestration, billing, and production operations.

<!-- TODO: screenshots — add Forge dashboard + activity timeline captures to docs/img/ -->
<!-- ![Forge dashboard](docs/img/forge-dashboard.png) -->

---

## How It Works

Every bot is a `configuration` record executing a three-stage pipeline on its own cadence (5m → 1d):

```
Market Data → Extraction → Decision → Trading → Exchange
     ↑              ↓          ↓          ↓         ↓
   Sources     Analysis   AI Reasoning  Execution  Results
```

**🔍 [Extraction](extraction/)** — Market Intelligence Gathering
- 21 preprocessors with pandas-ta integration (12x performance improvement over baseline)
- Catalog-driven universal data layer, WebSocket-first (3x–3000x faster than REST polling)
- Binance WebSocket cache streaming 100 symbols × 7 timeframes into Redis
- Multi-timeframe analysis: 5m, 15m, 30m, 1h, 4h, 1d

**🧠 [Decision](decision/)** — LLM Trading Reasoning
- Multi-LLM routing via OpenRouter (Claude, GPT, Grok, Gemini, DeepSeek) with per-tier model selection, plus bring-your-own-key direct provider support
- Template-based prompt system: opportunity analysis for new trades, position management for open ones
- Natural-language strategy definition injected into every decision
- Confidence scoring drives position sizing; volume confirmation and risk guardrails constrain the LLM

**⚡ [Trading](trading/)** — Precision Execution
- **Paper engine** — professional-grade simulation on live market prices, realistic spreads and taker fees, isolated $10K accounts per strategy
- **Hyperliquid live engine** — non-custodial DEX execution via the API-wallet model (the platform can trade but provably cannot withdraw), 228 perp markets, up to 50x leverage
- 3-second position monitoring with automatic take-profit/stop-loss execution
- Full audit trail: every decision, trade, and account snapshot persisted

### Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                            │
│                 (Forge dashboard + real-time UI)                │
├─────────────────────────────────────────────────────────────────┤
│   API Process (ggbot.py)        Scheduler Process               │
│   FastAPI + SSE streams         APScheduler + reconcile loop    │
│              ┌─────────────┬─────────────┬─────────────┐        │
│              │ Extraction  │ Decision    │ Trading     │        │
│              │    V2       │ Engine V2   │ Paper + HL  │        │
├──────────────┼─────────────┼─────────────┼─────────────┼────────┤
│                   Core Infrastructure                           │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐      │
│  │ WebSocket   │ Monitoring  │ Config Mgmt │ Database    │      │
│  │ Prices      │ & Alerts    │             │ (Supabase)  │      │
└──┴─────────────┴─────────────┴─────────────┴─────────────┴──────┘
```

---

## Engineering Highlights

- **Two-process architecture** — HTTP/SSE API and bot execution run as separate processes sharing one orchestrator class, with the database as the sole interface between them. The API stays fast no matter how heavy the LLM workload gets; a 10-second reconcile loop picks up state changes.
- **Zero-drift autonomous scheduling** — APScheduler jobs aligned to exchange candle boundaries, Redis-based idempotency preventing duplicate trades across restarts, automatic job reconciliation from database state.
- **Real-time everywhere** — Server-Sent Events stream dashboard state to the frontend; Binance WebSocket feeds keep prices sub-millisecond-fresh in Redis; position P&L updates every 3 seconds without touching Postgres on the hot path.
- **Database IO engineering** — position prices moved from per-tick Postgres batch updates to Redis hashes with Postgres fallback; dashboard query rewritten from sequential scans to LATERAL joins (253ms → 25ms); tiered snapshot retention with batched deletes.
- **36 market-intelligence data points across 7 categories** — news, social sentiment, on-chain analytics, derivatives positioning, and more, routed through a catalog-driven gateway so new sources are config, not code.
- **Non-custodial live trading** — Hyperliquid integration built on the API-wallet model: users keep custody, agents get protocol-enforced trade-only permissions. EIP-712 signing flows handled in-browser.
- **Usage-based billing** — Stripe metered subscriptions plus prepaid credit packs (card and crypto via NOWPayments), with per-decision LLM cost accrual and an out-of-band enforcement monitor.
- **Observability as a feature** — structured logging with per-cycle correlation IDs threaded through the entire extraction → decision → trading chain; error-alert service pushes production exceptions straight to Telegram.

---

## 📁 Repository Structure

| Directory | Purpose |
|-----------|---------|
| **api/** | FastAPI endpoint modules (activities, paper trading, public stats, admin) |
| **core/** | Shared infrastructure — auth, config, domain models, scheduler, symbols, monitoring, SSE |
| **extraction/** | Market data extraction with 21 preprocessors |
| **decision/** | LLM decision engine, prompt templates, provider routing |
| **trading/** | Paper and Hyperliquid live execution engines |
| **market_intelligence/** | Catalog-driven market data orchestrator (36 data points) |
| **billing/** | Metered billing, Stripe + crypto payments, credit grants |
| **frontend/** | Next.js 15 application (Forge dashboard) |
| **database/** | Schema and migrations |
| **tests/** | Integration and unit test suite |
| **scripts/** | Operational utilities (status checks, backfills, model verification) |

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.10 / FastAPI** | REST API + SSE streaming |
| **APScheduler** | Autonomous bot scheduling with candle alignment |
| **pandas-ta** | Technical indicators (21 preprocessors) |
| **PostgreSQL (Supabase)** | Main application database + auth |
| **Redis** | Price cache, idempotency, queues, hot-path P&L |
| **Loguru** | Structured logging with bound correlation context |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 15 / React 19** | App Router, Server Components |
| **TypeScript** | End-to-end type safety |
| **Tailwind CSS** | Styling |
| **Zustand** | State management |
| **Recharts** | Performance charts |
| **Vercel** | Deployment with git-based CI/CD |

### AI / LLM
| Layer | Detail |
|-------|--------|
| **OpenRouter** | Unified routing across Anthropic, OpenAI, xAI, Google, DeepSeek |
| **Tier system** | Economy / standard / premium model selection per provider family |
| **BYOK** | Direct provider integration for users bringing their own API keys |

### Trading & Data
| Service | Purpose |
|---------|---------|
| **Hyperliquid** | Live DEX perp trading — 228 markets, API-wallet custody model |
| **Binance WebSocket** | Real-time price streaming (100 symbols × 7 timeframes) |
| **CCXT** | Multi-exchange market data |
| **Stripe + NOWPayments** | Card and crypto billing |

### Infrastructure
| Service | Purpose |
|---------|---------|
| **PM2** | 5 production processes: API, scheduler, market-data WebSocket, account monitor, error alerts |
| **Supabase** | Managed Postgres, auth, encrypted secrets vault |
| **Vercel** | Frontend hosting |

---

## 📚 Deep Dives

Each major module ships with full architecture documentation:

| Module | Contents |
|--------|----------|
| **[extraction/v2/README.md](extraction/v2/README.md)** | 21 preprocessors, performance engineering, API docs |
| **[market_intelligence/README.md](market_intelligence/README.md)** | 36 data points, 7 categories, orchestrator architecture |
| **[decision/README.md](decision/README.md)** | Template system, opportunity analysis + position management |
| **[trading/README.md](trading/README.md)** | Paper & live engines, Hyperliquid integration internals |
| **[billing/README.md](billing/README.md)** | Metered billing, credit packs, usage enforcement |
| **[frontend/README.md](frontend/README.md)** | Forge architecture, SSE integration, component system |
| **[frontend/SEO.md](frontend/SEO.md)** | SEO infrastructure, blog system, OG image generation |
| **[DOCS/DATABASE_CONTEXT.md](DOCS/DATABASE_CONTEXT.md)** | Database architecture decisions and rationale |
| **[DOCS/](DOCS/)** | Design docs, shipped-feature write-ups, integration guides |

---

## 🗺️ Roadmap

See **[ROADMAP.md](ROADMAP.md)** for where the platform is headed — HIP-3 instruments (equities, commodities, indices), LLM-driven mid-trade position management, expanded market intelligence, and more.

---

<p align="center">
  Built and operated by <a href="https://github.com/sevnightingale">@sevnightingale</a> · <a href="https://ggbots.ai">ggbots.ai</a>
</p>
