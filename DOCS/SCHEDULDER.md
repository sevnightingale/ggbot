GGBot Scheduler — Prototype Plan (Cron + Idempotency, Single Instance)

Owner: Sev / Claude
Status: Ready to implement
Goal: Candle-aligned, zero-drift execution with duplicate-trade protection, minimal moving parts.

1) Scope & Non-Goals

In scope (prototype):

Single scheduler instance (one process/pod)

APScheduler in-memory (no job store)

CronTrigger cadence per timeframe (UTC), coalesce=True, max_instances=1

Timeframe-aware misfire grace + jitter (to avoid thundering herd)

Idempotency per (user_id, config_id, timeframe, close_ts)

Startup reconciliation from config DB (authoritative), not Redis

Minimal WebSocket status events (running, completed, error) including close_ts + next_fire_at

Optional global concurrency limit via async semaphore

Out of scope (for prototype):

Leader election / multi-instance HA

APScheduler SQLAlchemy job store

Complex metrics, auto-stop policies, job history, backfills

Weekly timeframe (unless you validate provider anchor)

2) Architecture Overview (prototype)
FastAPI (control endpoints)
        │
        ├─> Config DB (authoritative bot enables + timeframes)
        ├─> Redis (idempotency keys)
        │
APScheduler (in-memory, 1 instance)
  └─ CronTrigger jobs per bot (UTC + jitter + misfire grace)
        └─> Job function:
              1) compute close_ts (last closed candle)
              2) idempotency check (Redis SETNX)
              3) orchestrator.run_autonomous_cycle(config_id, user_id)
              4) WebSocketManager: status events {status, close_ts, next_fire_at}


Why this cut: zero drift (Cron), safe (idempotency), simple (no job store/HA), fast to iterate.

3) Timing & Cadence

Timezone: Always UTC (no DST surprises).

Delay: default 30s after close (tune per provider; 45s if needed).

Jitter: 15s (set on job; don’t randomize seconds in Cron).

Misfire grace (per job):

5m: 120s

15m: 180s

30m/1h: 300s

4h: 600s

1d: 900s

Coalesce: True (don’t catch up missed candles via scheduler).

Supported timeframes (prototype): 5m, 15m, 30m, 1h, 4h, 1d
(Defer 1w until you confirm provider’s week anchor)

Cron shapes (UTC):

5m → minute="*/5", second=30

15m → minute="0,15,30,45", second=30

30m → minute="0,30", second=30

1h → minute=0, second=30

4h → hour="0,4,8,12,16,20", minute=0, second=30

1d → hour=0, minute=0, second=30

4) Idempotency (must-have)

Key format: bot_exec:{user_id}:{config_id}:{timeframe}:{close_ts}

Redis SETNX + TTL (prototype approach):

On job start: SET key "executing" NX EX=<ttl> → if false, skip (already done/doing).

On success: SET key "completed" EX=<ttl> (idempotent).

TTL: ≥ 2× timeframe (e.g., 1d → 2–3 days).

Environment setup:
REDIS_URL="redis://localhost:6379"  # or your Redis instance

Benefits: Lightning fast, auto-expires, no database schema changes, perfect for ephemeral scheduling state.

5) Startup Reconciliation

On process start:

Query config DB for enabled/active bots (per user) + analysis_frequency.

For each active bot config:
- Extract timeframe from config.decision.analysis_frequency
- Call add_bot_job(scheduler, user_id, config_id, timeframe)
- Jobs will have unique IDs like "bot:{user_id}:{config_id}:{timeframe}"

Configuration database is the source of truth, not APScheduler or external state.

6) Minimal Scheduler Configuration
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")

MISFIRE = {
    "5m":120, "15m":180, "30m":300, "1h":300, "4h":600, "1d":900
}

def cron_for(tf: str) -> CronTrigger:
    if tf == "5m":  return CronTrigger(minute="*/5", second=30, timezone=UTC)
    if tf == "15m": return CronTrigger(minute="0,15,30,45", second=30, timezone=UTC)
    if tf == "30m": return CronTrigger(minute="0,30", second=30, timezone=UTC)
    if tf == "1h":  return CronTrigger(minute=0, second=30, timezone=UTC)
    if tf == "4h":  return CronTrigger(hour="0,4,8,12,16,20", minute=0, second=30, timezone=UTC)
    if tf == "1d":  return CronTrigger(hour=0, minute=0, second=30, timezone=UTC)
    raise ValueError(f"Unsupported timeframe: {tf}")

def add_bot_job(scheduler, user_id, config_id, timeframe, jitter=15):
    trigger = cron_for(timeframe)
    scheduler.add_job(
        func=run_once,  # defined below
        trigger=trigger,
        id=f"bot:{user_id}:{config_id}:{timeframe}",
        args=[user_id, config_id, timeframe],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=MISFIRE[timeframe],
        jitter=jitter,
    )


Close timestamp (last closed candle) — prototype computation:

from datetime import datetime, timezone

def last_closed_close_ts(tf: str, now=None) -> int:
    now = now or datetime.now(timezone.utc)
    t = int(now.timestamp())
    if tf == "5m":  s=300
    elif tf == "15m": s=900
    elif tf == "30m": s=1800
    elif tf == "1h":  s=3600
    elif tf == "4h":  s=14400
    elif tf == "1d":  s=86400
    else: raise ValueError(tf)
    return (t // s) * s  # end of last completed candle (Unix seconds)


Job body (Redis idempotency variant + semaphore):

import asyncio
import redis.asyncio as redis
import os
execution_semaphore = asyncio.Semaphore(50)  # optional global cap

async def run_once(user_id: str, config_id: str, timeframe: str):
    from ggbot import websocket_manager, orchestrator  # Import from main orchestrator

    close_ts = last_closed_close_ts(timeframe)
    key = f"bot_exec:{user_id}:{config_id}:{timeframe}:{close_ts}"

    # Redis client setup
    redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

    async with execution_semaphore:
        try:
            # Try to acquire idempotency lock
            if not await redis_client.set(key, "executing", ex=7*24*3600, nx=True):
                return  # already executing/executed

            job = scheduler.get_job(f"bot:{user_id}:{config_id}:{timeframe}")
            next_fire = job.next_run_time.isoformat() + "Z" if job and job.next_run_time else None
            await websocket_manager.broadcast_to_user(user_id, {"type":"bot_status_update","config_id":config_id,"status":"running","close_ts":close_ts,"next_fire_at":next_fire})

            try:
                result = await orchestrator.run_autonomous_cycle(config_id, user_id)
                await websocket_manager.broadcast_to_user(user_id, {"type":"bot_status_update","config_id":config_id,"status":"completed","close_ts":close_ts,"next_fire_at":next_fire})
                await redis_client.set(key, "completed", ex=7*24*3600)
            except Exception as e:
                await websocket_manager.broadcast_to_user(user_id, {"type":"bot_status_update","config_id":config_id,"status":"error","error":str(e),"close_ts":close_ts,"next_fire_at":next_fire})
                # leave key as "executing" to prevent retries on same candle
        finally:
            await redis_client.aclose()

7) Control Endpoints (minimal)
@app.post("/api/v2/bot/{config_id}/start")
async def start_bot(config_id: str, current_user: AuthenticatedUser = Depends(get_current_user_v2)):
    config = await config_service.get_config(config_id, current_user.user_id)
    if not config: return {"status": "error", "message": "Config not found"}
    tf = config.decision.get("analysis_frequency", "1h")
    # enforce per-user limit via config DB query (count enabled bots)
    add_bot_job(scheduler, current_user.user_id, config_id, tf)
    return {"status":"started","config_id":config_id,"timeframe":tf}

@app.post("/api/v2/bot/{config_id}/stop")
async def stop_bot(config_id: str, current_user: AuthenticatedUser = Depends(get_current_user_v2)):
    config = await config_service.get_config(config_id, current_user.user_id)
    if not config: return {"status": "error", "message": "Config not found"}
    tf = config.decision.get("analysis_frequency", "1h")
    try:
        scheduler.remove_job(f"bot:{current_user.user_id}:{config_id}:{tf}")
    except Exception:
        pass
    # TODO: mark disabled in config DB so reconciliation won't restore it
    return {"status":"stopped","config_id":config_id}

@app.get("/api/v2/scheduler/status")
async def status(current_user: AuthenticatedUser = Depends(get_current_user_v2)):
    # return next_run per user's jobs (derive from scheduler.get_jobs())
    user_jobs = [job for job in scheduler.get_jobs() if job.id.startswith(f"bot:{current_user.user_id}:")]
    return {"active_bots": len(user_jobs), "jobs": [{"id": job.id, "next_run": job.next_run_time} for job in user_jobs]}


WS payload (keep it small & useful):

{
  "type": "bot_status_update",
  "config_id": "cfg_123",
  "status": "running|completed|error",
  "close_ts": 1725744000,
  "next_fire_at": "2025-09-08T12:15:30Z",
  "error": "..." // only on error
}

8) Startup Sequence

Start FastAPI.

Create one APScheduler instance in-memory; scheduler.start().

Reconcile: read enabled bots from config DB and call add_bot_job(...) for each.

Log: number of jobs scheduled + first next fire time per timeframe.

Deployment note: Ensure only one instance has SCHEDULER_ENABLED=true. Others run API/WebSocket only.

9) Monitoring (prototype)

Logs (structured): job fired, idempotency acquired/skipped, orchestrator outcome, duration.

Counters (in-memory only, optional): executions, failures.

Readiness: simple health endpoint returning scheduler.running and job count.

(Full Prometheus + dashboards can wait until HA.)

10) Testing Plan

Unit

last_closed_close_ts() property tests: for random now, returned ts is ≤ now, aligned to timeframe modulus.

Cron cadence: for each timeframe, generate 10 successive next_fire_times via trigger and assert alignment minute/second.

Idempotency: simulate concurrent calls → only one proceeds.

Integration (local)

Boot with 3 bots/user → verify jobs exist, next fires aligned.

Kill process, restart → reconciliation restores jobs with same IDs and cadence.

Force misfire (sleep past trigger) → verify single coalesced run.

Manual

Wire to paper trading; confirm no duplicate orders when you spam run function or restart near boundaries.

11) Risks & Mitigations

Provider lag (>30s) → bump delay to 45–60s for short TFs; or add a quick “is candle closed?” probe before running.

Accidental multi-instance scheduling → gate by SCHEDULER_ENABLED, CI/CD policy: only one replica with scheduler enabled.

Clock skew → run containers with NTP-synced hosts; rely on UTC everywhere.

12) Upgrade Path (when ready)

Phase A (Ops hardening)

Add Prometheus metrics, structured run logs table.

Global concurrency limits tuned by telemetry.

Phase B (Persistence & HA)

Enable APScheduler SQLAlchemy job store.

Introduce leader election (Postgres advisory lock) + periodic re-election.

Keep idempotency (unchanged) to neutralize rare double fires during failover.

Phase C (Data alignment)

Compute close_ts from provider “last closed candle” API; fail early if freshness < expected.

Support weekly timeframe with configurable anchor (Mon/Sun) matched across Cron & idempotency.

13) Acceptance Criteria

Bots execute at candle close + delay (± jitter) with no drift.

No duplicate trades across restarts or concurrent triggers.

Restart restores all enabled bots without manual steps.

Single instance runs scheduler; others do not schedule.

Minimal, clear WS updates include close_ts and next_fire_at.

14) Work Breakdown

Redis Setup
Ensure Redis is running and REDIS_URL environment variable is configured

Scheduler Core (APScheduler in-memory)
Cron factory, misfire table, jitter, coalesce/max_instances

Idempotency
Redis SETNX with TTL - fast, ephemeral, no database schema changes

Job Function
Compute close_ts → Redis idempotency check → orchestrator → WebSocket

Reconciliation
Query existing configs; add jobs on boot; per-user bot limits

API Integration
Replace placeholder endpoints in ggbot.py with scheduler calls

Tests
Unit (timing/idempotency), integration (restarts, misfires), manual paper trading validation

That’s the whole plan—APScheduler yes, lightweight mode. Ship this; you won’t drift, you won’t double-trade, and you won’t drown in ops.