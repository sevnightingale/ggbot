# API Extraction Refactor Planning Document

**Created:** 2026-01-07
**Purpose:** Separate FastAPI endpoints from APScheduler orchestration to prevent 502 errors during bot execution cycles
**Target:** Split `ggbot.py` (4345 lines) into two independent processes

---

## Table of Contents
1. [Problem Statement](#problem-statement)
2. [Current State Analysis](#current-state-analysis)
3. [Proposed Architecture](#proposed-architecture)
4. [Migration Strategy](#migration-strategy)
5. [Risk Assessment](#risk-assessment)
6. [Implementation Phases](#implementation-phases)
7. [Testing Strategy](#testing-strategy)

---

## Problem Statement

### Current Issue
- **Monolith:** `ggbot.py` contains both FastAPI API server AND APScheduler bot execution
- **Event Loop Blocking:** When bots trigger at hour/half-hour marks, long-running LLM calls (10-30s) block the asyncio event loop
- **User Impact:** API endpoints return 502 errors during bot execution, breaking frontend dashboard updates
- **Production Evidence:** SSE streams disconnect, bot activation/deactivation fails during cycle execution

### Root Cause
```python
# Lines 1188-1221: APScheduler job execution runs in same process as FastAPI
async def run_once(user_id: str, config_id: str, timeframe: str):
    async with execution_semaphore:  # Limits concurrent bot executions
        result = await orchestrator.run_autonomous_cycle(config_id, user_id)  # BLOCKS EVENT LOOP
```

The `execution_semaphore` (line 1183, limit=50) was meant to prevent overload, but it doesn't prevent event loop starvation when LLM calls monopolize async execution.

---

## Current State Analysis

### File Structure
**Total Lines:** 4345
**Key Components:**

#### 1. **FastAPI Application Setup** (Lines 1-310)
- **Imports:** Lines 1-105
  - FastAPI, Pydantic, APScheduler, Redis, Stripe, database, services
- **Pydantic Models:** Lines 108-200
  - `ConfigCreateRequest`, `ConfigUpdateRequest`, `SignalOrchestrationRequest`, `OrchestrationResult`
- **Lifespan Manager:** Lines 202-285
  - Database connectivity test
  - APScheduler startup/shutdown
  - MonitoringService startup/shutdown
  - Active bot reconciliation
- **FastAPI App Creation:** Lines 287-310
  - Router inclusions (8 routers from `api/` directory)

#### 2. **GGBotOrchestrator Class** (Lines 312-1177)
- **Core Trading Logic:** Extraction → Decision → Trading pipeline
- **Methods:**
  - `run_autonomous_cycle()`: Main entry point (line 326)
  - `_run_autonomous_trading_cycle()`: Traditional bot flow (line 390)
  - `_run_signal_validation_cycle()`: Signal validation flow (line 481)
  - `_run_extraction_v2()`: Market data + indicators (line 799)
  - `_run_decision_v2()`: LLM decision making (line 955)
  - `_run_trading_v2()`: Execute trades (paper/symphony/aster) (line 1005)
- **Dependencies:**
  - ConfigService, LLMService, PaperTradingService, SymphonyService, AsterService
  - ExtractionEngineV2, DecisionEngineV2
  - Database connections, Redis, MCP tools

#### 3. **APScheduler Integration** (Lines 1180-1388)
- **Global Scheduler:** Line 1182 - `scheduler = AsyncIOScheduler()`
- **Execution Semaphore:** Line 1183 - `execution_semaphore = asyncio.Semaphore(50)`
- **Scheduled Job Functions:**
  - `run_once()`: Job executor with Redis idempotency (line 1188)
  - `add_bot_job()`: Schedule bot (line 1223)
  - `remove_bot_job()`: Unschedule bot (line 1252)
  - `reconcile_active_bots()`: Startup reconciliation (line 1269)
  - `extract_timeframe_from_config()`: Parse timeframe from config (line 1308)
  - `get_next_run_from_scheduler()`: Query next execution (line 1341)
  - `has_scheduler_job()`: Check if job exists (line 1369)

#### 4. **FastAPI Endpoints** (Lines 1391-4318)

##### **Core Endpoints** (Lines 1391-1506)
- `GET /` - Root (line 1392)
- `GET /health` - Health check (line 1409)
- `GET /api/dashboard-stream` - SSE stream (line 1419)

##### **Configuration Management** (Lines 1508-1947)
- `POST /api/v2/config` - Create bot (line 1509)
- `GET /api/v2/config` - List configs (line 1692)
- `GET /api/v2/config/{config_id}` - Get config (PUBLIC) (line 1706)
- `GET /api/v2/configs/{config_id}/strategy` - Get agent strategy (PUBLIC) (line 1764)
- `PUT /api/v2/config/{config_id}` - Update config (line 1819)
- `DELETE /api/v2/config/{config_id}` - Delete config (line 1914)

##### **Orchestration Endpoints** (Lines 1949-2072)
- `POST /api/v2/orchestrate/{config_id}` - Run bot cycle (line 1950)
- `POST /api/v2/signal-validation/{config_id}` - Service-to-service signal validation (line 1989)
- `POST /api/v2/test/signal-publishing/{config_id}` - Test Telegram publishing (line 2026)

##### **Symbols API** (Lines 2074-2157)
- `GET /api/v2/symbols/supported` - Get 141 supported symbols (line 2075)
- `GET /api/v2/symbols/search/{query}` - Search symbols (line 2108)

##### **User Management** (Lines 2161-2298)
- `GET /api/v2/user/profile` - User profile (line 2162)
- `GET /api/v2/user/indicators` - Available indicators (line 2187)
- `GET /api/v2/data-sources-with-points` - Data sources catalog (line 2201)

##### **LLM Models & Credentials** (Lines 2300-2481)
- `GET /api/v2/llm-models` - Available LLM models (line 2300)
- `POST /api/v2/user/llm-credentials` - Store credential (line 2369)
- `GET /api/v2/user/llm-credentials` - List credentials (line 2407)
- `GET /api/v2/user/llm-credentials/{credential_name}` - Get credential (line 2429)
- `DELETE /api/v2/user/llm-credentials/{credential_name}` - Delete credential (line 2456)

##### **Billing & Usage** (Lines 2483-2674)
- `GET /api/v2/billing/usage` - Current usage (line 2484)
- `GET /api/v2/billing/usage/breakdown` - Detailed breakdown (line 2570)

##### **Symphony Live Trading** (Lines 2676-2805)
- `POST /api/v2/symphony/setup` - Store credentials (line 2677)
- `GET /api/v2/symphony/status` - Check connection (line 2739)
- `POST /api/v2/symphony/disconnect` - Disconnect account (line 2768)

##### **Aster DEX Trading** (Lines 2807-2947)
- `POST /api/v2/aster/setup` - Store credentials (line 2807)
- `GET /api/v2/aster/status` - Check connection (line 2879)
- `POST /api/v2/aster/disconnect` - Disconnect account (line 2910)

##### **Position Management** (Lines 2949-3122)
- `GET /api/v2/positions/live/{config_id}` - Symphony positions (line 2949)
- `POST /api/v2/positions/live/{batch_id}/close` - Close Symphony position (line 2986)
- `GET /api/v2/positions/aster/{config_id}` - Aster positions (PUBLIC) (line 3036)
- `POST /api/v2/positions/aster/{order_id}/close` - Close Aster position (line 3082)

##### **Account Metrics** (Lines 3124-3209)
- `GET /api/v2/account/live/{config_id}` - Symphony account metrics (line 3124)
- `GET /api/v2/trades/live/{config_id}` - Symphony trade history (line 3173)

##### **Bot Data Endpoints** (Lines 3212-3561)
- `GET /api/v2/bot/{config_id}/metrics` - Performance metrics (line 3213)
- `GET /api/v2/bot/{config_id}/positions` - Open positions (line 3283)
- `GET /api/v2/bot/{config_id}/trades` - Trade history (line 3328)
- `GET /api/v2/bot/{config_id}/account` - Account summary (line 3376)
- `GET /api/v2/bot/{config_id}/decisions` - Decision history (line 3486)

##### **Agent Execution** (Lines 3563-3674)
- `POST /api/v2/agent/execute-trade` - Agent trade execution (service-to-service) (line 3564)

##### **Bot Lifecycle** (Lines 3676-3957)
- `POST /api/v2/bot/{config_id}/start` - Start bot (adds APScheduler job) (line 3677)
- `POST /api/v2/bot/{config_id}/stop` - Stop bot (removes APScheduler job) (line 3743)
- `POST /api/v2/bot/{config_id}/reset-account` - Reset paper account (line 3797)
- `GET /api/v2/scheduler/status` - Scheduler status (line 3842)
- `POST /api/v2/scheduler/reconcile` - Manual reconciliation (line 3884)
- `GET /api/v2/bot/{config_id}/status` - Bot status (line 3921)

##### **Stripe Integration** (Lines 3959-4153)
- `POST /api/v2/create-checkout-session` - Checkout (line 3971)
- `POST /api/v2/stripe-webhook` - Webhook handler (line 4046)
- `POST /api/v2/create-portal-session` - Billing portal (line 4087)
- `GET /api/v2/me` - Current user profile (line 4127)

#### 5. **Webhook Handlers & Helpers** (Lines 4155-4317)
- `handle_checkout_completed()`: Line 4159
- `handle_subscription_updated()`: Line 4199
- `handle_subscription_deleted()`: Line 4230
- `handle_payment_failed()`: Line 4253
- `get_or_create_stripe_customer()`: Line 4276

#### 6. **Application Entry Point** (Lines 4319-4345)
- HTTP exception handler: Line 4319
- Development mode override: Line 4332
- Uvicorn server startup: Line 4337

---

### External API Routers (Included in App)
Located in `api/` directory (lines 295-309):
1. `api/paper_trading.py` - Paper trading endpoints
2. `api/agent.py` - Agent endpoints
3. `api/activities.py` - Activity timeline endpoints
4. `api/snapshots.py` - Account snapshot endpoints
5. `api/assistant.py` - AI assistant endpoints
6. `api/admin.py` - Admin endpoints
7. `api/public.py` - Public competition endpoints

**Critical:** These routers are ALREADY modular and will move to API server unchanged.

---

### Shared Dependencies (Critical Coupling Points)

#### **Services (Singleton Instances)**
```python
# Lines 91-95
from core.services.config_service import config_service  # Global singleton
from core.services.user_service import user_service      # Global singleton
from core.services.llm_service import llm_service        # Global singleton
```

#### **Database**
```python
# Line 215-220: Lifespan startup
from core.common.db import get_db_connection
```
- All endpoints use direct PostgreSQL connections
- APScheduler jobs use same connection pool

#### **Redis**
```python
# Lines 1196-1197: run_once() job function
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(redis_url, decode_responses=True)
```
- Idempotency keys for bot executions
- Potential communication channel between processes

#### **Orchestrator Instance**
```python
# Line 1180: Global orchestrator
orchestrator = GGBotOrchestrator()
```
- Used by `/api/v2/orchestrate` endpoint (line 1958)
- Used by APScheduler `run_once()` (line 1211)
- **CRITICAL COUPLING POINT**

#### **Scheduler Instance**
```python
# Line 1182: Global scheduler
scheduler = AsyncIOScheduler()
```
- Used by bot lifecycle endpoints:
  - `/api/v2/bot/{config_id}/start` (line 3712)
  - `/api/v2/bot/{config_id}/stop` (line 3773)
  - `/api/v2/scheduler/status` (line 3842)

---

## Proposed Architecture

### Two Independent Processes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ggbot-api.py (Port 8000)                      │
│                                                                         │
│  FastAPI Application (All HTTP Endpoints)                              │
│  ├─ Health checks, user management, config CRUD                        │
│  ├─ Bot lifecycle (start/stop) - writes to DB + Redis                  │
│  ├─ Manual orchestration (/api/v2/orchestrate) - direct execution      │
│  ├─ SSE dashboard stream                                               │
│  ├─ Stripe webhooks & billing                                          │
│  └─ External routers (api/*.py)                                        │
│                                                                         │
│  Communicates with Scheduler via:                                      │
│  ├─ Database (configurations.state = 'active'/'inactive')              │
│  └─ Redis pub/sub (optional: "bot_lifecycle" channel)                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (Shared DB + Redis)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ggbot-scheduler.py (No HTTP Server)                │
│                                                                         │
│  APScheduler Background Service                                        │
│  ├─ Polls DB for active bots every 30s                                 │
│  ├─ Manages CronTrigger jobs per bot                                   │
│  ├─ Executes GGBotOrchestrator.run_autonomous_cycle()                  │
│  ├─ Redis idempotency (prevents duplicate executions)                  │
│  └─ Listens to Redis pub/sub for instant job add/remove                │
│                                                                         │
│  Runs in infinite loop:                                                │
│  while True:                                                            │
│    scheduler.tick()  # Process scheduled jobs                          │
│    check_redis_commands()  # Instant updates                           │
│    await asyncio.sleep(1)                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Communication Mechanisms

#### **1. Database-Driven Polling (Primary)**
```sql
-- API writes to DB
UPDATE configurations SET state = 'active' WHERE config_id = ?;

-- Scheduler polls DB every 30s
SELECT config_id, user_id, config_type, config_data
FROM configurations
WHERE state = 'active';
```

**Pros:**
- Simple, no new infrastructure
- Reliable (DB is source of truth)
- Already implemented reconciliation logic (line 1269)

**Cons:**
- 30s delay for job activation/deactivation
- Constant DB polling overhead

#### **2. Redis Pub/Sub (Instant Updates, Optional)**
```python
# ggbot-api.py: When user clicks "Start Bot"
redis_client.publish('bot_lifecycle', json.dumps({
    'action': 'start',
    'user_id': user_id,
    'config_id': config_id,
    'timeframe': '1h'
}))

# ggbot-scheduler.py: Background listener
async def redis_listener():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe('bot_lifecycle')
    async for message in pubsub.listen():
        if message['type'] == 'message':
            event = json.loads(message['data'])
            if event['action'] == 'start':
                add_bot_job(event['user_id'], event['config_id'], event['timeframe'])
```

**Pros:**
- Instant job updates (no 30s delay)
- Reduces DB polling

**Cons:**
- Adds Redis pub/sub complexity
- Requires error handling for missed messages

#### **3. Hybrid Approach (Recommended)**
- **Redis pub/sub** for instant updates (best UX)
- **DB polling** as fallback (ensures consistency)
- Scheduler reconciles from DB every 5 minutes

---

### File Structure After Refactor

```
/home/sev/ggbot/
├── ggbot-api.py              (NEW: FastAPI server, ~2000 lines)
├── ggbot-scheduler.py        (NEW: APScheduler service, ~500 lines)
├── core/
│   └── orchestrator/
│       ├── __init__.py
│       ├── orchestrator.py   (EXTRACTED: GGBotOrchestrator, ~900 lines)
│       ├── scheduler.py      (EXTRACTED: APScheduler logic, ~300 lines)
│       └── lifecycle.py      (NEW: Shared lifecycle functions)
├── api/                      (UNCHANGED: All routers move to ggbot-api.py)
│   ├── paper_trading.py
│   ├── agent.py
│   ├── activities.py
│   ├── snapshots.py
│   ├── assistant.py
│   ├── admin.py
│   └── public.py
└── ACTIVE.md                 (UPDATE: Document two processes)
```

---

## Migration Strategy

### Phase 1: Extract Orchestrator Class (Low Risk)
**Goal:** Move `GGBotOrchestrator` to separate module without changing behavior

**Steps:**
1. Create `/home/sev/ggbot/core/orchestrator/` directory
2. Extract `GGBotOrchestrator` (lines 312-1177) → `core/orchestrator/orchestrator.py`
3. Update imports in `ggbot.py`:
   ```python
   from core.orchestrator.orchestrator import GGBotOrchestrator
   orchestrator = GGBotOrchestrator()
   ```
4. Run integration tests (no behavior change)

**Files Modified:**
- `ggbot.py` (remove class definition, add import)
- `core/orchestrator/orchestrator.py` (NEW)

**Risk:** Low - Pure code movement, no logic changes

---

### Phase 2: Extract Scheduler Logic (Medium Risk)
**Goal:** Separate APScheduler functions into reusable module

**Steps:**
1. Extract scheduler functions (lines 1188-1388) → `core/orchestrator/scheduler.py`:
   - `run_once()`
   - `add_bot_job()`
   - `remove_bot_job()`
   - `reconcile_active_bots()`
   - `extract_timeframe_from_config()`
   - `get_next_run_from_scheduler()`
   - `has_scheduler_job()`

2. Move scheduler instance creation to module:
   ```python
   # core/orchestrator/scheduler.py
   scheduler = AsyncIOScheduler()
   execution_semaphore = asyncio.Semaphore(50)
   ```

3. Update imports in `ggbot.py`:
   ```python
   from core.orchestrator.scheduler import (
       scheduler, add_bot_job, remove_bot_job,
       reconcile_active_bots, get_next_run_from_scheduler, has_scheduler_job
   )
   ```

**Files Modified:**
- `ggbot.py` (remove functions, add imports)
- `core/orchestrator/scheduler.py` (NEW)

**Risk:** Medium - Scheduler startup in lifespan needs careful testing

---

### Phase 3: Create Lifecycle Communication Module (Medium Risk)
**Goal:** Shared functions for bot lifecycle (used by both processes)

**Steps:**
1. Create `core/orchestrator/lifecycle.py`:
   ```python
   import redis.asyncio as redis
   import json
   from typing import Dict, Any

   async def notify_scheduler_start_bot(user_id: str, config_id: str, timeframe: str):
       """Notify scheduler to start a bot (via Redis pub/sub)."""
       redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
       redis_client = redis.from_url(redis_url, decode_responses=True)
       try:
           await redis_client.publish('bot_lifecycle', json.dumps({
               'action': 'start',
               'user_id': user_id,
               'config_id': config_id,
               'timeframe': timeframe
           }))
       finally:
           await redis_client.aclose()

   async def notify_scheduler_stop_bot(user_id: str, config_id: str, timeframe: str):
       """Notify scheduler to stop a bot (via Redis pub/sub)."""
       redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
       redis_client = redis.from_url(redis_url, decode_responses=True)
       try:
           await redis_client.publish('bot_lifecycle', json.dumps({
               'action': 'stop',
               'user_id': user_id,
               'config_id': config_id,
               'timeframe': timeframe
           }))
       finally:
           await redis_client.aclose()

   async def get_bot_next_run(user_id: str, config_id: str) -> str | None:
       """Get next run time from DB (fallback when scheduler not accessible)."""
       from core.common.db import get_db_connection
       with get_db_connection() as conn:
           with conn.cursor() as cur:
               cur.execute("""
                   SELECT next_run_at FROM configurations
                   WHERE config_id = %s AND user_id = %s
               """, (config_id, user_id))
               result = cur.fetchone()
               return result[0].isoformat() if result and result[0] else None
   ```

2. Add `next_run_at` column to `configurations` table:
   ```sql
   ALTER TABLE configurations ADD COLUMN next_run_at TIMESTAMPTZ;
   ```

3. Update scheduler to write next_run_at to DB:
   ```python
   # In add_bot_job() after scheduler.add_job()
   job = scheduler.get_job(job_id)
   if job and job.next_run_time:
       from core.common.db import get_db_connection
       with get_db_connection() as conn:
           with conn.cursor() as cur:
               cur.execute("""
                   UPDATE configurations
                   SET next_run_at = %s
                   WHERE config_id = %s
               """, (job.next_run_time, config_id))
               conn.commit()
   ```

**Files Modified:**
- `core/orchestrator/lifecycle.py` (NEW)
- `core/orchestrator/scheduler.py` (update to write next_run_at)
- Database schema (add next_run_at column)

**Risk:** Medium - Requires DB migration, Redis pub/sub setup

---

### Phase 4: Split into Two Processes (High Risk)
**Goal:** Create independent API and scheduler processes

#### **4A. Create ggbot-scheduler.py**

```python
"""
GGBot Scheduler Service

Background process that manages scheduled bot executions via APScheduler.
Runs independently from the API server to prevent event loop blocking.
"""

import asyncio
import os
from datetime import datetime, timezone

from core.common.logger import logger
from core.orchestrator.scheduler import (
    scheduler,
    add_bot_job,
    remove_bot_job,
    reconcile_active_bots
)

# Redis pub/sub for instant job updates
import redis.asyncio as redis


async def redis_lifecycle_listener():
    """Listen for bot lifecycle events from API server."""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url, decode_responses=True)

    pubsub = redis_client.pubsub()
    await pubsub.subscribe('bot_lifecycle')

    logger.info("🎧 Redis lifecycle listener started")

    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    event = json.loads(message['data'])
                    action = event.get('action')
                    user_id = event.get('user_id')
                    config_id = event.get('config_id')
                    timeframe = event.get('timeframe')

                    if action == 'start':
                        logger.info(f"🚀 Redis event: Starting bot {config_id} ({timeframe})")
                        add_bot_job(user_id, config_id, timeframe)
                    elif action == 'stop':
                        logger.info(f"🛑 Redis event: Stopping bot {config_id} ({timeframe})")
                        remove_bot_job(user_id, config_id, timeframe)

                except Exception as e:
                    logger.error(f"Failed to process Redis lifecycle event: {e}")

    except asyncio.CancelledError:
        logger.info("Redis lifecycle listener cancelled")
        await pubsub.unsubscribe('bot_lifecycle')
        await redis_client.aclose()
    except Exception as e:
        logger.error(f"Redis lifecycle listener error: {e}")


async def db_reconciliation_loop():
    """Reconcile active bots from DB every 5 minutes (fallback mechanism)."""
    logger.info("📊 Database reconciliation loop started")

    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            logger.info("🔄 Running database reconciliation...")
            await reconcile_active_bots()

        except asyncio.CancelledError:
            logger.info("Database reconciliation loop cancelled")
            break
        except Exception as e:
            logger.error(f"Database reconciliation error: {e}")


async def main():
    """Main scheduler service entry point."""
    logger.info("🚀 Starting GGBot Scheduler Service")

    # Start APScheduler
    scheduler.start()
    logger.info("✅ APScheduler started")

    # Initial reconciliation
    await reconcile_active_bots()
    logger.info("✅ Initial bot reconciliation complete")

    # Start background tasks
    redis_task = asyncio.create_task(redis_lifecycle_listener())
    reconcile_task = asyncio.create_task(db_reconciliation_loop())

    logger.info("🟢 GGBot Scheduler Service ready")

    try:
        # Keep service running
        await asyncio.gather(redis_task, reconcile_task)
    except KeyboardInterrupt:
        logger.info("🔄 Shutting down scheduler service...")
        redis_task.cancel()
        reconcile_task.cancel()
        scheduler.shutdown(wait=False)
        logger.info("✅ Scheduler service stopped")


if __name__ == "__main__":
    asyncio.run(main())
```

#### **4B. Create ggbot-api.py**

1. Copy all endpoint definitions from `ggbot.py`
2. Remove APScheduler startup from lifespan (keep DB, monitoring)
3. Update bot lifecycle endpoints to use `lifecycle.notify_scheduler_*()`:

```python
# In /api/v2/bot/{config_id}/start endpoint
@app.post("/api/v2/bot/{config_id}/start")
async def start_bot(config_id: str, current_user: AuthenticatedUser = Depends(get_current_user_v2)):
    # ... validation ...

    # Update state in DB (source of truth)
    await config_service.set_bot_state(config_id, current_user.user_id, 'active')

    # Notify scheduler via Redis (instant update)
    from core.orchestrator.lifecycle import notify_scheduler_start_bot
    await notify_scheduler_start_bot(current_user.user_id, config_id, timeframe)

    # Get next_run from DB (written by scheduler)
    from core.orchestrator.lifecycle import get_bot_next_run
    next_run = await get_bot_next_run(current_user.user_id, config_id)

    return {
        "status": "started",
        "config_id": config_id,
        "timeframe": timeframe,
        "next_run": next_run
    }
```

4. Keep manual orchestration endpoint (for "Run Now" button):
```python
@app.post("/api/v2/orchestrate/{config_id}")
async def run_orchestration(config_id: str, ...):
    """Manual execution (bypasses scheduler)."""
    from core.orchestrator.orchestrator import GGBotOrchestrator
    orchestrator = GGBotOrchestrator()  # Create instance per request
    result = await orchestrator.run_autonomous_cycle(config_id, user_id)
    return result
```

#### **4C. Update PM2 Configuration**

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'ggbot-api',
      script: 'ggbot-api.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        ENABLE_SCHEDULER: 'false'  // Disable scheduler in API process
      }
    },
    {
      name: 'ggbot-scheduler',
      script: 'ggbot-scheduler.py',
      interpreter: '/home/sev/ggbot/.venv/bin/python',
      cwd: '/home/sev/ggbot',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '4G'  // Higher memory for LLM calls
    },
    {
      name: 'market-data-ws',
      script: 'market_data/websocket_cache.py',
      // ... existing config ...
    }
  ]
};
```

**Files Created:**
- `ggbot-api.py` (~2000 lines)
- `ggbot-scheduler.py` (~200 lines)

**Files Modified:**
- `ecosystem.config.js`
- `ACTIVE.md` (document two processes)

**Files Deprecated:**
- `ggbot.py` (keep as reference, rename to `ggbot-monolith.py.bak`)

**Risk:** High - Complete process separation, requires careful testing

---

## Risk Assessment

### Critical Risks

#### **1. Event Loop Deadlock (High Impact, Medium Probability)**
**Risk:** If API and scheduler share same Redis connection pool, pub/sub blocking could freeze both.

**Mitigation:**
- Use separate Redis client instances per process
- Test with high bot concurrency (50+ bots executing)
- Monitor Redis connection count

#### **2. Job Duplication (High Impact, Low Probability)**
**Risk:** Race condition where both DB reconciliation and Redis pub/sub add same job.

**Mitigation:**
- APScheduler's `replace_existing=True` prevents duplicates (line 1242)
- Redis idempotency keys in `run_once()` (line 1202)
- Database `state` column is source of truth

#### **3. Scheduler Crash = No Bot Execution (High Impact, Low Probability)**
**Risk:** If scheduler process crashes, all bots stop running.

**Mitigation:**
- PM2 auto-restart with exponential backoff
- Health check endpoint in scheduler (simple HTTP server on port 8001)
- Alert monitoring via `/health` endpoint
- Database reconciliation on restart recovers all jobs

#### **4. API Can't Query Scheduler State (Medium Impact, Medium Probability)**
**Risk:** After split, API can't call `scheduler.get_job()` to show next_run time.

**Mitigation:**
- Scheduler writes `next_run_at` to DB (Phase 3)
- API reads from DB instead of querying scheduler directly
- Trade-off: Next run time may be 1-2 seconds stale (acceptable)

#### **5. Manual Orchestration Blocks API (Medium Impact, Medium Probability)**
**Risk:** "Run Now" button still executes in API process, could block event loop.

**Mitigation:**
- Keep execution semaphore (limit concurrent manual runs)
- Add timeout (30s max for manual executions)
- Future: Move to background task queue (Celery/RQ)

### Medium Risks

#### **6. Redis Pub/Sub Message Loss (Low Impact, High Probability)**
**Risk:** If scheduler is restarting during bot start/stop, Redis message is lost.

**Mitigation:**
- Database polling fallback (every 5 minutes)
- User sees "Bot starting..." but may take up to 5 min to actually start
- Document in UI: "Changes may take up to 5 minutes to apply"

#### **7. Database Connection Pool Exhaustion (Medium Impact, Low Probability)**
**Risk:** Two processes sharing same PostgreSQL server, connection limits.

**Mitigation:**
- Current limit: 100 connections (check `psql -c 'SHOW max_connections'`)
- API uses ~20 connections, scheduler uses ~10
- Monitor with `pg_stat_activity`

#### **8. Monitoring Service Conflict (Low Impact, Low Probability)**
**Risk:** MonitoringService runs in API process (line 252), expects scheduler to exist.

**Mitigation:**
- Keep MonitoringService in API only (it monitors positions, not scheduler)
- Or run in scheduler process if it needs to interact with jobs

### Low Risks

#### **9. Deployment Complexity (Low Impact, High Probability)**
**Risk:** Need to coordinate deployment of two processes.

**Mitigation:**
- PM2 handles multi-process management
- Deploy sequence: 1) Scheduler, 2) API (minimizes downtime)
- Rollback: Restart old monolith `ggbot.py`

---

## Implementation Phases

### Phase 1: Extract Orchestrator (Week 1)
**Estimated Effort:** 4 hours
**Risk:** Low

**Tasks:**
- [ ] Create `/home/sev/ggbot/core/orchestrator/` directory
- [ ] Move `GGBotOrchestrator` class to `orchestrator.py`
- [ ] Update imports in `ggbot.py`
- [ ] Run integration tests (`tests/test_trading_flow_simple.py`)
- [ ] Deploy to staging (verify no regressions)

**Success Criteria:**
- All tests pass
- Manual "Run Now" works
- Scheduled bots execute normally

---

### Phase 2: Extract Scheduler Logic (Week 1-2)
**Estimated Effort:** 6 hours
**Risk:** Medium

**Tasks:**
- [ ] Create `core/orchestrator/scheduler.py`
- [ ] Move all APScheduler functions
- [ ] Update imports in `ggbot.py`
- [ ] Test scheduler startup/shutdown in lifespan
- [ ] Test bot start/stop endpoints

**Success Criteria:**
- Scheduler reconciliation works on startup
- Bot lifecycle endpoints functional
- Next run times display correctly

---

### Phase 3: Add Lifecycle Communication (Week 2)
**Estimated Effort:** 8 hours
**Risk:** Medium

**Tasks:**
- [ ] Create `core/orchestrator/lifecycle.py`
- [ ] Add `next_run_at` column to `configurations` table
- [ ] Implement Redis pub/sub functions
- [ ] Update scheduler to write `next_run_at` to DB
- [ ] Test Redis message passing

**Success Criteria:**
- Redis pub/sub working (start/stop bot)
- `next_run_at` populated in DB
- Fallback to DB polling works

---

### Phase 4: Create Scheduler Process (Week 3)
**Estimated Effort:** 10 hours
**Risk:** High

**Tasks:**
- [ ] Create `ggbot-scheduler.py`
- [ ] Implement Redis listener
- [ ] Implement DB reconciliation loop
- [ ] Test standalone execution
- [ ] Add health check endpoint

**Success Criteria:**
- Scheduler runs independently
- Bots execute on schedule
- Redis events processed
- DB reconciliation works

---

### Phase 5: Create API Process (Week 3-4)
**Estimated Effort:** 12 hours
**Risk:** High

**Tasks:**
- [ ] Create `ggbot-api.py`
- [ ] Remove scheduler from lifespan
- [ ] Update bot lifecycle endpoints (use `lifecycle.notify_*`)
- [ ] Update `/api/v2/scheduler/status` (read from DB)
- [ ] Test all endpoints

**Success Criteria:**
- API starts without scheduler
- Bot start/stop triggers Redis events
- Manual orchestration works
- SSE stream functional

---

### Phase 6: Integration Testing (Week 4)
**Estimated Effort:** 16 hours
**Risk:** High

**Tasks:**
- [ ] Update PM2 configuration
- [ ] Deploy both processes to staging
- [ ] Stress test: 50+ concurrent bots
- [ ] Test bot lifecycle (start/stop/delete)
- [ ] Test manual orchestration during scheduled execution
- [ ] Monitor event loop responsiveness
- [ ] Verify no 502 errors during bot execution
- [ ] Test scheduler crash recovery
- [ ] Test API crash recovery

**Success Criteria:**
- No 502 errors during peak bot execution
- API responsive <100ms during bot cycles
- Scheduler recovers all jobs after restart
- API continues serving during scheduler restart

---

### Phase 7: Production Deployment (Week 5)
**Estimated Effort:** 8 hours
**Risk:** Medium

**Tasks:**
- [ ] Update `ACTIVE.md` documentation
- [ ] Create rollback plan (revert to monolith)
- [ ] Deploy to production (off-peak hours)
- [ ] Monitor logs for 24 hours
- [ ] Verify all active bots running
- [ ] Check user dashboards for anomalies

**Success Criteria:**
- Zero downtime deployment
- All active bots continue running
- No user reports of errors
- API latency improved during bot execution

---

## Testing Strategy

### Unit Tests
```bash
# Test orchestrator extraction
python -m pytest tests/unit/test_orchestrator.py

# Test scheduler functions
python -m pytest tests/unit/test_scheduler.py

# Test lifecycle communication
python -m pytest tests/unit/test_lifecycle.py
```

### Integration Tests
```bash
# Test full trading flow
python -m pytest tests/test_trading_flow_simple.py

# Test bot lifecycle
python -m pytest tests/integration/test_bot_lifecycle.py
```

### Load Tests
```python
# tests/load/test_concurrent_bots.py
import asyncio
import httpx

async def test_50_concurrent_bots():
    """Simulate 50 bots executing simultaneously."""
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(50):
            task = client.post(
                f"http://localhost:8000/api/v2/orchestrate/{config_ids[i]}",
                headers={"Authorization": f"Bearer {tokens[i]}"}
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert: No 502 errors
        for result in results:
            assert not isinstance(result, httpx.HTTPStatusError)
            assert result.status_code in [200, 201]
```

### Manual Testing Checklist
- [ ] Start 10 bots via UI, verify all scheduled
- [ ] Stop 5 bots via UI, verify jobs removed
- [ ] Click "Run Now" during scheduled execution
- [ ] Delete bot config, verify job cleaned up
- [ ] Restart scheduler process, verify bots resume
- [ ] Restart API process, verify scheduler unaffected
- [ ] Kill scheduler process, verify API continues serving
- [ ] Monitor SSE stream during bot execution burst

---

## Rollback Plan

### If Issues Detected in Phase 4-7

**Step 1:** Stop new processes
```bash
pm2 stop ggbot-api
pm2 stop ggbot-scheduler
```

**Step 2:** Restore monolith
```bash
# Rename backup
mv ggbot-monolith.py.bak ggbot.py

# Start monolith
pm2 start ecosystem.config.js --only ggbot
```

**Step 3:** Verify recovery
```bash
# Check active bots
curl http://localhost:8000/api/v2/scheduler/status

# Trigger manual run
curl -X POST http://localhost:8000/api/v2/orchestrate/{config_id}
```

**Step 4:** Database cleanup (if needed)
```sql
-- Reset next_run_at if added in Phase 3
UPDATE configurations SET next_run_at = NULL;
```

**Expected Recovery Time:** 5 minutes

---

## Success Metrics

### Performance Improvements
- **API Latency (p99):** <100ms during bot execution (currently: 3-10s)
- **502 Errors:** 0 during peak bot hours (currently: 10-20/hour)
- **SSE Stream Stability:** 99.9% uptime (currently: 95%)

### Operational Metrics
- **Scheduler Uptime:** 99.9%
- **Job Execution Success Rate:** >98% (no regression)
- **Deployment Downtime:** <5 minutes

### User Experience
- **Bot Start/Stop Latency:** <5 seconds (instant with Redis pub/sub)
- **Dashboard Responsiveness:** No freezing during bot execution
- **Next Run Accuracy:** Within 2 seconds of actual execution

---

## Open Questions

1. **Should manual orchestration (`/api/v2/orchestrate`) move to scheduler?**
   - Pro: Fully isolates LLM calls from API
   - Con: Adds latency for "Run Now" button (HTTP → Redis → execution)
   - **Decision:** Keep in API for now, move to task queue later (Phase 8)

2. **Should MonitoringService run in API or Scheduler?**
   - Currently in API (line 252)
   - Purpose: Monitor open positions, update prices
   - **Decision:** Keep in API (doesn't interact with scheduler)

3. **What's the migration path for existing active bots?**
   - On first deploy, scheduler will reconcile from DB (line 257)
   - No action needed from users
   - **Decision:** Automatic migration via `reconcile_active_bots()`

4. **Should we add a health check HTTP server to scheduler?**
   - Pro: Easy monitoring with existing tools
   - Con: Adds HTTP server overhead to background process
   - **Decision:** Yes, simple `/health` endpoint on port 8001

5. **How to handle scheduled job conflicts during deployment?**
   - If deploying at hour mark (e.g., 14:00), jobs may execute twice
   - Redis idempotency keys prevent duplicate execution (line 1202)
   - **Decision:** Deploy during off-peak hours (03:00 UTC)

---

## Timeline Summary

| Phase | Description | Effort | Risk | Week |
|-------|-------------|--------|------|------|
| 1 | Extract Orchestrator | 4h | Low | 1 |
| 2 | Extract Scheduler | 6h | Med | 1-2 |
| 3 | Lifecycle Communication | 8h | Med | 2 |
| 4 | Scheduler Process | 10h | High | 3 |
| 5 | API Process | 12h | High | 3-4 |
| 6 | Integration Testing | 16h | High | 4 |
| 7 | Production Deploy | 8h | Med | 5 |

**Total Estimated Effort:** 64 hours (8 working days)
**Recommended Timeline:** 5 weeks (accounting for testing, buffer)

---

## Appendix: Critical Code Sections

### A. Current Monolith Execution Flow
```python
# Line 1188: APScheduler job function (runs in same event loop as API)
async def run_once(user_id: str, config_id: str, timeframe: str):
    async with execution_semaphore:  # Semaphore(50)
        result = await orchestrator.run_autonomous_cycle(config_id, user_id)
        # ^^ This blocks for 10-30 seconds during LLM calls
```

### B. Proposed Scheduler Process Flow
```python
# ggbot-scheduler.py: Independent process, no HTTP server
async def main():
    scheduler.start()
    await reconcile_active_bots()

    redis_task = asyncio.create_task(redis_lifecycle_listener())
    reconcile_task = asyncio.create_task(db_reconciliation_loop())

    await asyncio.gather(redis_task, reconcile_task)
    # ^^ Runs forever, no HTTP requests to block
```

### C. Proposed API Bot Start Flow
```python
# ggbot-api.py: Bot start endpoint (instant response)
@app.post("/api/v2/bot/{config_id}/start")
async def start_bot(config_id: str, ...):
    # 1. Update DB (source of truth)
    await config_service.set_bot_state(config_id, user_id, 'active')

    # 2. Notify scheduler via Redis (instant)
    await notify_scheduler_start_bot(user_id, config_id, timeframe)

    # 3. Read next_run from DB (written by scheduler)
    next_run = await get_bot_next_run(user_id, config_id)

    return {"status": "started", "next_run": next_run}
    # ^^ Returns in <50ms, no scheduler interaction
```

---

## Conclusion

This refactor addresses the root cause of 502 errors by isolating long-running bot executions from the API event loop. The proposed architecture uses battle-tested patterns (APScheduler in dedicated process, Redis pub/sub for IPC, database as source of truth) and provides a clear migration path with minimal risk.

**Recommendation:** Proceed with phased implementation, starting with low-risk extractions (Phase 1-2) and validating thoroughly before full process separation (Phase 4-7).

**Next Steps:**
1. Review this document with team
2. Approve architecture and timeline
3. Create feature branch: `refactor/api-scheduler-split`
4. Begin Phase 1 (Extract Orchestrator)
