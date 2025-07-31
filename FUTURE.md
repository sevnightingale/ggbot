# GGBots Future Roadmap

## 🎯 Core Features Overview

- **Secure User API Keys** – Accept exchange credentials on the frontend, transmit via HTTPS/JWT, AES-encrypt at rest, and spin each bot in an isolated container
- **Decision Engine Refactoring** – Split 1587-line monolithic decision/engine.py into focused modules for maintainability and testing
- **Shared Market-Data Cache** – One canonical table plus pre-compute jobs eliminate duplicate API calls and rate-limit grief
- **Multi-Exchange + Arbitrage** – CCXT abstraction for spot, futures, and DEXs, with a spread-sniper that fires atomic cross-venue orders
- **Advanced Order & Portfolio Suite** – Iceberg, TWAP/VWAP, OCO, position-sized copy trading, draw-down guards, and global risk caps
- **Strategy Marketplace** – User-published templates, revenue-share leaderboards, back-tester, and one-click copy trading
- **Machine-Learning Pipeline** – Feature engineering, online A/B, RL agents, and regime detection that retunes parameters on the fly
- **Micro-Services & Scaling** – Extraction, decision, trading, dashboard, and agent-control pods in Kubernetes with Redis, TimescaleDB, and Celery queues
- **Monitoring & Safety Mesh** – Prometheus, Grafana, distributed tracing, order-reconciliation, circuit breakers, kill switches, and multi-channel alerts
- **Compliance & Security Stack** – KYC/AML, audit trails, 2FA, HSM-backed key vault, IP whitelists, and multi-sig on fat trades
- **Symbol-Specific / Multi-Asset Engine** – Per-symbol mode detection, fully parallel extraction-decision-execution loops, ready for portfolio logic
- **Client Order-ID Reconciliation** – Bullet-proof audit trail, duplicate detection, and automatic fail/retry logic
- **Multi-Source Extraction Manager** – Plug-in loaders for TradingView, Yahoo Finance, news, on-chain, Telegram, etc., with data-fusion hooks
- **DevOps & CI/CD** – Git-driven tests, blue/green deploys, auto-rollbacks, and sandbox load tests
- **Concurrent Indicator Extraction** – Fire async tasks per symbol/timeframe/indicator, slashing latency from ~18s to ~2–3s
- **Autonomous Scheduler & Webhooks** – Cron/APS jobs chain extraction → decision → execution → monitoring 24/7 with emergency fallbacks

---

## 📋 Detailed Implementation Plans

### 🔐 Secure User API Keys

**Problem:** Currently using shared test keys; need secure per-user credential management.

**Solution Components:**
- **Transport:** HTTPS POST from frontend, JWT session check
- **Encryption:** AES-256 via `cryptography.Fernet`; master key in HSM/Vault, rotated quarterly
- **Schema:** `exchange_credentials(id, user_id, exchange, api_key_enc, secret_enc, passphrase_enc, created_at, last_used)` indexed on `user_id`
- **Isolation:** Every ggbot gets its own container/pod, temp configs wiped on exit; no cross-tenant env-vars
- **Regulatory:** Audit trail records who decrypted, when, and why

**Priority:** 🔥 **Critical** – No keys, no product

---

### 📦 Decision Engine Refactoring

**Problem:** `decision/engine.py` is 1587 lines of mixed responsibilities: database ops, prompt generation, LLM parsing, and business logic all in one class.

**Solution:** Split into focused modules:
- `decision/data_layer.py` – Database operations (market data, accounts, trades)
- `decision/prompt_builder.py` – Prompt generation with template system
- `decision/response_parser.py` – LLM response parsing and validation  
- `decision/volume_analyzer.py` – Volume confirmation analysis
- `decision/core_engine.py` – Streamlined orchestration logic
- `decision/intent_creator.py` – Trading intent generation

**Benefits:** Easier testing, cleaner separation of concerns, reduced cognitive load for maintenance

**Priority:** 🔥 **High** – Current size makes debugging and feature additions painful

---

### 🗃️ Shared Market-Data Cache

**Problem:** 100 users requesting RSI on BTC/USDT 1h triggered 100 identical API hits.

**Solution:**
- Central `market_data_shared` table `(symbol, timeframe, source, extracted_at UNIQUE)` with descending index
- Smart fetch: Query cache → if stale > 1-candle, hit vendor → store once
- Background workers monitor hot symbols, pre-extract at each close, prune after retention window

**Impact:** 🚀 Cuts paid-API cost by >80% at scale and makes indicator queries instant

---

### 🌐 Multi-Exchange + Arbitrage

**Components:**
- **CCXT Wrapper:** Normalize symbols, decimal precisions, and special order params
- **Venue Features:** Spot + futures (Binance), compliance flags (Coinbase), Web3 routers (Uniswap, Pancake)
- **Cross-venue Engine:** Subscribe to price feeds, calculate latency-adjusted spread; if spread > threshold, submit atomic OCO pair
- **Fail-safes:** Per-exchange rate-limit trackers, hedge legs if one side partially fills

---

### 🎯 Advanced Order & Portfolio Suite

**Features:**
- **Execution Algos:** Iceberg, TWAP, VWAP, smart-order routing, liquidity seekers
- **Order Safety:** Trailing stops, portfolio-wide stop-loss, correlation caps
- **Rebalancing:** Risk parity, target-weight, volatility scaling
- **Copy-Trade Sizing:** Follower size = leader size × equity ratio, bounded by follower risk rules

**Impact:** 💪 Moves ggbots from "signal shooter" to "institution-grade execution desk"

---

### 🏪 Strategy Marketplace

**Components:**
- **Templates:** JSON-based param sets with code snippets; versioned like git
- **Revenue Share:** 70% creator / 30% platform; enforced in-app accounting
- **Back-test & Walk-forward:** Simulate over raw exchange data, Monte Carlo run-ups, separate in/out sample
- **Leaderboards:** Sharpe, Sortino, max draw-down, live vs back-test delta

---

### 🤖 Machine-Learning Pipeline

**Data Flow:** Raw ticks → feature cookers → feature store → model zoo (sklearn, XGBoost, PyTorch)

**Components:**
- **Online A/B:** Shadow-run new models, compare live P&L before promotion
- **Reinforcement Agents:** Policy-gradient bots trading micro-futures
- **Regime Detector:** ATR, VIX proxies, and volume/RSI trends feed a classifier; switches strategy presets dynamically

---

### 🏗️ Micro-Services & Scaling

**Service Split:**
- Extraction (5001), Decision (5002), Trading (5000), Dashboard (5003), Agent-Control (5004)

**Orchestration:** Kubernetes + service mesh; HPA on CPU / queue depth

**Infrastructure:** Redis cache; TimescaleDB partitions; Celery/RabbitMQ task bus; dedicated read replicas for analytics

**Benefit:** Strong isolation = one service crash ≠ system outage

---

### 🛡️ Monitoring & Safety Mesh

**Metrics:** Prometheus counters, histograms, and Grafana dashboards; per-user cut

**Safety Systems:**
- **Order Reconciliation:** Poll `client_order_id`, mark stale > 5 min as failed
- **Circuit Breakers:** Daily loss > 5%, rapid-loss cluster, API error burst
- **Kill Switches:** Soft (block new trades), hard (pause automation), emergency (close all)
- **Alerts:** Discord (info→critical), email (critical+), SMS (emergency)

**Warning:** ⚠️ Miss this layer and you'll blow up accounts—non-negotiable

---

### 📜 Compliance & Security Stack

**Components:**
- KYC/AML provider plug-in, automatic SAR reports
- Audit-trail table joins orders ↔ decisions ↔ credentials ↔ user-sessions
- Hardware Security Module (or Vault + KMS) for master keys
- 2FA, IP whitelist, device fingerprint on login
- Multi-sig policy: trades > $100k require second device confirmation

---

### 🔄 Symbol-Specific / Multi-Asset Engine

**Old Bug:** Global mode detection meant BTC open = ETH stuck in MANAGE mode

**Fix:** API now requires symbol, queries open trades per symbol, spawns `asyncio.gather` tasks per asset

**Future:** Portfolio-aware optimizer (cross-asset correlation, capital weighting)

---

### 🧾 Client Order-ID Reconciliation

**Components:**
- Index on `trade_orders(client_order_id)` for O(1) look-ups
- Reconciliation service loops: DB → exchange `fetch_order_by_client_id` → bulk-update statuses
- Audit view `v_complete_trade_audit` links `strategy_runs` → `trades` → `orders` for forensic digs
- Alert on duplicates, stale pending, missing TP/SL

---

### 📡 Multi-Source Extraction Manager

**Sources:** TradingView, Yahoo Finance, News feeds, On-chain, Telegram, plus current MCP indicators

**Components:**
- `ExtractionManager` factory loads plug-ins by config; stores source tag + data_type in same `market_data` schema
- Data fusion: weighted reliability scores, conflict resolution, feature-store write-through
- Migration path: single-source call now but flipping to manager only requires two lines swapped

---

### 🛠️ DevOps & CI/CD

**Pipeline:** Lint → unit tests → integration (docker-compose) → load (Locust) → coverage gate → build image → blue/green K8s deploy

**Features:**
- **Rollbacks:** Health-check fail triggers automated revert within 30s
- **Secrets:** Vault sidecar injects env-vars at pod start; never shipped in images

---

### ⚡ Concurrent Indicator Extraction

**Current State:** Sequential loop (symbol × timeframe × indicator) burns ~18s for 3×3 matrix

**Solution:** Async gather shrinks to slowest request (~2–3s)

**Implementation:** Hybrid throttling obeys exchange rate-limits and MCP capacity caps

**Impact:** Gains matter most once multi-indicator configs arrive

---

### ⏱️ Autonomous Scheduler & Webhooks

**Flow:** Cron/Scheduler → Extraction webhook → on-complete Decision webhook → on-complete Trading webhook → Monitoring update

**Safety Features:**
- **Fault Handling:** Retries with exponential back-off, dead-letter queue, idempotent handles
- **Safety Checks:** Pre-trade confidence > 0.7, max daily trades, risk fit; else trade blocked and alert fired
- **Monitoring Loop:** 30s account polls, TP/SL trigger checks, emergency stop logic

---

## 📝 Additional Optimizations

### Infrastructure
- **TimescaleDB Partitions:** Monthly partitioning + compression jobs to keep `market_data` slim
- **Redis Decision-Cache:** TTL = 1 candle for back-testing speed-ups
- **Geo Read Replicas:** EU + US replicas cut cross-ocean latency for global users
- **Async DB Pooling:** SQLAlchemy QueuePool; avoid N+1 queries

### User Experience
- **Mobile-Friendly Dashboard:** Drag-and-drop widgets, TradingView charts, live P&L feed
- **Adaptive Learning Rollbacks:** If new model under-performs baseline by > 5% over 100 trades, auto-revert

### Advanced Features
- **Sector-Rotation & Cross-Pair Arb:** Pencilled for post-MVP but schema already supports