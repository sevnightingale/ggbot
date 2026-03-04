# Orchestrator Refactor - Performance-First Approach

**Created**: 2026-01-30
**Updated**: 2026-01-30
**Purpose**: Fix API latency during bot execution through pragmatic, incremental improvements
**Supersedes**: API_EXTRACTION_REFACTOR.md (overly complex, doesn't address root cause)

---

## Executive Summary

**The Problem**: API endpoints return 502s and SSE streams disconnect when bots are executing.

**Root Cause Analysis**:
1. **Primary**: `psycopg2` is synchronous — DB queries block the entire event loop
2. **Secondary**: Single process runs both API server and scheduler
3. **Tertiary**: Code organization makes maintenance difficult (but doesn't affect performance)

**Key Insight**: Process separation alone won't fix the problem if the DB driver is still synchronous. The original plan focused on splitting processes but ignored that both processes would still use blocking DB calls.

---

## Table of Contents

1. [Why We're Doing This](#why-were-doing-this)
2. [Scale Considerations](#scale-considerations)
3. [The Real Bottlenecks](#the-real-bottlenecks)
4. [Phased Approach](#phased-approach)
5. [What True Elegance Looks Like](#what-true-elegance-looks-like)
6. [Implementation Details](#implementation-details)
7. [Success Metrics](#success-metrics)

---

## Why We're Doing This

### Current Symptoms
- API p99 latency: **3-10 seconds** during bot execution (target: <100ms)
- 502 errors: **10-20/hour** during peak (target: 0)
- SSE stream disconnects: **~5%** of streams (target: <0.1%)

### User Impact
- Dashboard freezes during candle close (when all bots fire)
- "Start Bot" button appears stuck
- Real-time position updates stop

### Business Impact
- Users lose trust in platform stability
- Support tickets increase during peak hours
- Churn risk for power users running multiple bots

---

## Scale Considerations

### Current Scale
- 35 active bots
- ~60 decisions/hour
- Single VM (4GB RAM)

### Near-Term Scale (6 months)
- 200+ active bots projected
- Multiple users with 5-10 bots each
- Need concurrent execution without blocking

### Long-Term Scale (12+ months)
- 1,000+ bots
- Need horizontal scaling
- Worker queue architecture

### What Breaks at Each Scale

| Scale | Bottleneck | Symptom |
|-------|------------|---------|
| **35 bots** | Sync DB + single process | Current 502s |
| **100 bots** | DB connection exhaustion | "too many connections" |
| **200 bots** | Event loop starvation | Complete API lockup |
| **500+ bots** | Single process limit | Can't scale further |

---

## The Real Bottlenecks

### Bottleneck #1: Synchronous Database Driver (Critical)

```python
# Current: psycopg2 is SYNCHRONOUS
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT ...")  # BLOCKS entire event loop
        results = cur.fetchall()   # Still blocking
```

**Impact**: Each 50ms DB query freezes ALL async operations. A bot cycle with 10 queries = 500ms where no other request can be processed.

**This is in README.md as using asyncpg but the actual code uses psycopg2.**

### Bottleneck #2: In-Memory Rate Limiting

```python
# Line 51 in ggbot.py
service_calls = defaultdict(list)  # Won't work across multiple instances
```

### Bottleneck #3: Single Process Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Single ggbot.py Process                  │
│                                                          │
│   API Server ←──────────── Event Loop ──────────→ Bots  │
│                              ↑                           │
│                         (contention)                     │
└─────────────────────────────────────────────────────────┘
```

### Bottleneck #4: Code Organization (Maintenance, Not Performance)

The 5,260-line monolith affects:
- Developer productivity (hard to navigate)
- Code review quality (hard to reason about)
- Testing isolation (hard to test billing without loading trading)

But it does NOT affect runtime performance directly.

---

## Phased Approach

### Quick Wins (Hours of Work) — DO FIRST

| Task | Impact | Effort | Risk |
|------|--------|--------|------|
| ~~Remove UX delays~~ | 13s saved per cycle | 10 min | None |
| Add timing logs | Find actual bottlenecks | 1 hour | None |
| Run multiple uvicorn workers | Better concurrency | 30 min | Low |
| Connection pooling audit | Prevent exhaustion | 1 hour | Low |

### Phase 1: Quick Wins (Complete)

- [x] Remove artificial UX delays (done 2026-01-30)
- [ ] Add timing instrumentation to identify actual slow points
- [ ] Verify connection pooling is properly configured

### Phase 2: Scheduler Separation (Days of Work)

**Goal**: API server never blocks on bot execution.

**Architecture**:
```
┌─────────────────────┐     ┌─────────────────────┐
│   API Server        │     │  Scheduler Process  │
│   (ggbot-api.py)    │     │  (ggbot-scheduler)  │
│                     │     │                     │
│   - HTTP endpoints  │     │  - APScheduler      │
│   - SSE streams     │     │  - Bot execution    │
│   - Fast responses  │◄───►│  - LLM calls        │
│                     │Redis│                     │
└─────────────────────┘     └─────────────────────┘
```

**Why This Helps**: Even with sync DB, the API process won't be blocked by LLM calls (which take 5-30 seconds).

**Tasks**:
- [ ] Extract scheduler to separate process
- [ ] Add Redis pub/sub for bot start/stop
- [ ] Update PM2 config for two processes
- [ ] Add health check endpoint to scheduler

**Estimated Effort**: 16-24 hours

### Phase 3: Async Database (Weeks of Work)

**Goal**: True async concurrency for all DB operations.

**Change**:
```python
# Before (blocks)
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT ...")

# After (yields)
async with pool.acquire() as conn:
    result = await conn.fetch("SELECT ...")
```

**Why This Matters**: This is the actual fix for the 502 problem. Without this, even process separation just moves the problem.

**Tasks**:
- [ ] Create `core/common/async_db.py` with asyncpg pool
- [ ] Migrate hot paths first (SSE stream, bot lifecycle)
- [ ] Gradually migrate all endpoints
- [ ] Remove psycopg2 when migration complete

**Estimated Effort**: 40-60 hours (significant change)

### Phase 4: Code Organization (Optional, Anytime)

**Goal**: Make the codebase elegant and maintainable.

**This can happen in parallel with Phases 2-3 or after.**

**Target Structure**:
```
ggbot/
├── ggbot.py                    # ~100 lines: app setup, router imports
├── api/
│   ├── billing.py              # Stripe endpoints (~400 lines)
│   ├── arena.py                # Competition endpoints (~300 lines)
│   ├── bot_lifecycle.py        # start/stop/reset (~200 lines)
│   ├── bot_data.py             # metrics/positions/trades (~300 lines)
│   ├── symphony.py             # Live trading endpoints (~200 lines)
│   └── dependencies.py         # Shared deps (get_user_config, etc.)
├── core/
│   └── orchestrator/
│       ├── orchestrator.py     # GGBotOrchestrator (~900 lines)
│       └── scheduler.py        # APScheduler functions (~200 lines)
├── webhooks/
│   ├── stripe.py               # Stripe webhook handlers
│   └── nowpayments.py          # Crypto webhook handlers
└── constants.py                # INITIAL_BALANCE = 10000.0, etc.
```

**Estimated Effort**: 8-16 hours (low risk, can be incremental)

### Phase 5: Worker Queue (Future, 500+ Bots)

**Goal**: Horizontal scaling for massive bot counts.

**Architecture**:
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ API Server 1 │     │ API Server 2 │     │ API Server N │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                     ┌──────▼──────┐
                     │ Redis Queue │
                     └──────┬──────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
│  Worker 1   │     │  Worker 2   │     │  Worker N   │
└─────────────┘     └─────────────┘     └─────────────┘
```

**When to Do This**: When you have 500+ bots and need to scale beyond a single VM.

---

## What True Elegance Looks Like

### Elegant Code Properties

1. **Single Responsibility**: Each file/class does ONE thing
2. **Obvious Intent**: Code reads like prose (`if profile.can_activate_bots:`)
3. **No Repetition**: Config ownership check appears once, not 15 times
4. **Consistent Patterns**: Same problem, same solution everywhere
5. **Appropriate Abstraction**: Not too abstract, not too concrete

### Elegant ggbot.py (Target State)

```python
"""GGBot V2 Orchestrator - Application Entry Point"""
from fastapi import FastAPI
from contextlib import asynccontextmanager

from api import billing, arena, bot_lifecycle, bot_data, config, symphony
from core.middleware import setup_middleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="GGBot V2", lifespan=lifespan)
setup_middleware(app)

# Mount all routers
app.include_router(config.router)
app.include_router(billing.router)
app.include_router(arena.router)
app.include_router(bot_lifecycle.router)
app.include_router(bot_data.router)
app.include_router(symphony.router)
```

**20 lines** that reveal the entire application structure.

### Elegant Dependency Pattern

```python
# api/dependencies.py
async def get_user_config(
    config_id: str,
    user: AuthenticatedUser = Depends(get_current_user_v2),
    service: ConfigService = Depends()
) -> BotConfigV2:
    """Validates config exists and belongs to user."""
    config = await service.get_config(config_id, user.user_id)
    if not config:
        raise HTTPException(404, "Configuration not found")
    return config

# Then every endpoint just uses it
@router.get("/api/v2/bot/{config_id}/metrics")
async def get_bot_metrics(config: BotConfigV2 = Depends(get_user_config)):
    # config is guaranteed to exist and belong to user
    ...
```

---

## Implementation Details

### Phase 2: Scheduler Separation (Recommended First)

**Why Phase 2 Before Phase 3?**
- Faster to implement (16-24h vs 40-60h)
- Immediate relief for the worst symptom (LLM blocking)
- Lower risk (no database driver change)
- Can be deployed incrementally

**Key Files to Create**:

1. **`ggbot-scheduler.py`** (~200 lines)
   - APScheduler instance
   - Redis pub/sub listener
   - DB reconciliation loop
   - No HTTP server

2. **`core/orchestrator/lifecycle.py`** (~100 lines)
   - `notify_scheduler_start_bot()`
   - `notify_scheduler_stop_bot()`
   - `get_bot_next_run()`

3. **Update `ggbot.py`**:
   - Remove APScheduler startup from lifespan
   - Update bot lifecycle endpoints to use lifecycle module
   - Keep `/api/v2/orchestrate` for "Run Now" (direct execution)

**Communication Pattern**:
```
API → Redis pub/sub → Scheduler (instant)
API → DB update → Scheduler polls (fallback, 5min)
Scheduler → DB write → API reads next_run (query)
```

### Phase 3: Async Database (Critical for Scale)

**Migration Strategy**:

1. Create `core/common/async_db.py`:
```python
import asyncpg
from typing import Optional

_pool: Optional[asyncpg.Pool] = None

async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=os.environ['DATABASE_URL'],
        min_size=5,
        max_size=20
    )

async def get_async_pool() -> asyncpg.Pool:
    if _pool is None:
        await init_pool()
    return _pool
```

2. Migrate hot paths first:
   - SSE dashboard stream (highest frequency)
   - Bot lifecycle endpoints (user-facing latency)
   - Position monitoring (background but critical)

3. Use feature flag for gradual rollout:
```python
USE_ASYNC_DB = os.getenv("USE_ASYNC_DB", "false").lower() == "true"

if USE_ASYNC_DB:
    result = await async_query(...)
else:
    result = sync_query(...)
```

---

## Success Metrics

### Phase 1 (Quick Wins)
- [x] UX delays removed (13s saved per cycle)
- [ ] Timing logs identify actual bottlenecks

### Phase 2 (Scheduler Separation)
- API p99 latency: <500ms during bot execution
- 502 errors: <5/hour during peak
- SSE stream uptime: >98%

### Phase 3 (Async Database)
- API p99 latency: <100ms during bot execution
- 502 errors: 0 during peak
- SSE stream uptime: >99.9%

### Phase 4 (Code Organization)
- ggbot.py: <200 lines
- All routers in separate files
- Config ownership check: 1 location (dependency)

### Phase 5 (Worker Queue)
- Support 1,000+ active bots
- Horizontal scaling via worker count
- No single point of failure

---

## Rollback Plan

### Phase 2 Rollback
```bash
# Stop new processes
pm2 stop ggbot-scheduler

# Restore monolith
pm2 restart ggbot

# Monolith still has scheduler code, will reconcile on startup
```

### Phase 3 Rollback
```bash
# Set feature flag
export USE_ASYNC_DB=false
pm2 restart ggbot
```

---

## FAQ

**Q: Why not just add more uvicorn workers?**

A: Workers don't help with sync DB — each worker has its own event loop, but psycopg2 blocks within each loop. You'd need N workers where N = number of concurrent DB queries, which doesn't scale.

**Q: Why not move manual orchestration to scheduler?**

A: "Run Now" needs to be synchronous for good UX. Users expect to see results immediately, not "your request has been queued." Keep it in API for now.

**Q: Why not use Celery?**

A: Celery adds significant complexity. For our scale (35-500 bots), APScheduler + Redis pub/sub is sufficient. Revisit when we need true horizontal scaling.

**Q: Should we migrate to asyncpg first?**

A: It's the "right" fix but it's a bigger change (40-60h). Scheduler separation gives faster relief (16-24h). Do Phase 2 first, then Phase 3.

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-30 | Prioritize scheduler separation over asyncpg | Faster relief, lower risk |
| 2026-01-30 | Keep code organization as optional/parallel | Doesn't affect performance |
| 2026-01-30 | Remove UX delays as quick win | 13s saved per cycle, zero risk |
| 2026-01-30 | Defer worker queue to 500+ bots | Overkill for current scale |

---

## Next Steps

1. **Immediately**: Restart ggbot to apply UX delay removal
2. **This Week**: Add timing instrumentation to identify bottlenecks
3. **Next Sprint**: Implement Phase 2 (scheduler separation)
4. **Following Sprint**: Begin Phase 3 (async database migration)
