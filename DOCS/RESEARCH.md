Here’s a crisp, opinionated review. Short version: your direction is right (Option B), but switch to **CronTrigger-based, cadence-first scheduling**, add **idempotency**, **startup reconciliation**, **distributed single-leader** protection, and **timeframe-aware misfire/jitter**. Your current date-reschedule loop will drift and can stall after downtime.

# Verdict

* ✅ Keep: APScheduler 3.11, candle alignment philosophy, WS status hooks, 3-bot/user limit, V2 orchestrator entrypoint.
* ❌ Change now: (1) date-trigger self-rescheduling; (2) weekly/daily time calc; (3) 30s misfire; (4) in-memory `active_bots`; (5) manual DB cleanup; (6) lack of duplicate-run guards; (7) no HA plan.

# Highest-impact fixes (do these first)

1. **Use CronTrigger, not date→reschedule loop.**
   Cadence must not depend on task duration. Cron avoids drift and “skip-a-candle” after long runs.

   * 5m: `CronTrigger(minute="*/5", second=30, timezone="UTC")`
   * 15m: `minute="0,15,30,45", second=30`
   * 30m: `minute="0,30", second=30`
   * 1h: `minute=0, second=30`
   * 4h: `hour="0,4,8,12,16,20", minute=0, second=30`
   * 1d: `hour=0, minute=0, second=30`
   * 1w (crypto): **confirm with your data source**; common practice is **Mon 00:00 UTC**, but some feeds use **Sun 00:00 UTC**. Make it a per-exchange setting.
   * Add **`jitter=5-15` seconds** to spread load and avoid thundering herd.

2. **Add idempotency keyed by candle.**
   Every autonomous cycle should carry `(config_id, timeframe, close_ts)` and the orchestrator must ensure it executes at most once (persist a “seen/executed” row or Redis key TTL). This makes duplicates harmless (crashes, retries, HA).

3. **Timeframe-aware misfire grace (not 30s flat).**

   * 5m: 120s
   * 15m: 180s
   * 30m/1h: 300s
   * 4h+: 600–900s
     Rationale: network hiccups, queueing, cold starts.

4. **Startup reconciliation (self-heal).**
   On process start, **rebuild jobs from persisted bot configs**, not from `active_bots` memory. Scan configs where autonomous mode is on and (re)attach proper CronTriggers. Without this, any bot is silently “off” after a long downtime (your date jobs would’ve been skipped).

5. **Single leader / HA.**
   APScheduler’s SQLAlchemy job store is **not** a distributed lock. If you run two app instances with the scheduler enabled, both will fire. Pick one:

   * Run scheduler in a **singleton** process (e.g., one deployment with a **DB advisory lock** to self-elect leader).
   * Or implement a minimal **Postgres advisory lock** around each fire (lock by `(config_id, close_ts)`), which still benefits from idempotency.

6. **Persist bot registry; don’t mutate the jobs table.**

   * `active_bots` must be a DB/Redis record (user\_id→{configs}) so it survives restarts and powers the reconciliation.
   * **Remove** the manual “delete from apscheduler\_jobs…” cleanup. APScheduler manages its own rows; your query risks nuking live jobs. If you need history, write **your own run\_log** table and log per execution there.

# Specific bugs / correctness issues

* **Weekly calc bug** in `get_next_candle_close`: On Mon 14:00 UTC, it computes the *past* midnight. Your guard `if days_until_monday == 0 and now.hour == 0 and now.minute < interval_minutes:` is always true for 1w (10080) at 00\:xx and doesn’t handle later Monday hours—leading to “past run\_date → immediate/misfire.” If you keep helper math, always `while next_close <= now: next_close += delta`.
* **Drift** with date+reschedule: if a 5m job overruns to T+7m, your `now`-based next calculation will schedule at T+10m, **skipping a candle**. Cron fixes this by anchoring to the cadence.
* **Hardcoded delay (30s)**: Some venues/data paths need longer for final OHLCV availability. Make this **per exchange + timeframe**, e.g., 30–90s; optionally probe readiness (e.g., check last closed candle timestamp before running).
* **Job IDs**: Use `f"bot:{user_id}:{config_id}"` to avoid any cross-tenant collision.
* **Health “running\_jobs”**: Counting jobs with `next_run_time` ≠ None is not “running.” Track live executions via APScheduler event listeners and your own counters.

# Proposed skeleton (Cron + idempotency + HA)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")

def cron_for(timeframe: str, second: int):
    m = {
        "5m":  "*/5", "15m": "0,15,30,45", "30m": "0,30",
        "1h":  "0",   "4h":  None,         "1d":  None,  "1w": None
    }
    if timeframe == "4h":
        return CronTrigger(hour="0,4,8,12,16,20", minute=0, second=second, timezone=UTC)
    if timeframe == "1d":
        return CronTrigger(hour=0, minute=0, second=second, timezone=UTC)
    if timeframe == "1w":
        # make this configurable per exchange: "mon" vs "sun"
        return CronTrigger(day_of_week="mon", hour=0, minute=0, second=second, timezone=UTC)
    if (mm := m.get(timeframe)) is None:
        raise ValueError(f"Unsupported timeframe {timeframe}")
    return CronTrigger(minute=mm, second=second, timezone=UTC)

async def schedule_bot(config_id: str, user_id: str, timeframe: str, delay_s: int, misfire_s: int, jitter_s: int):
    trig = cron_for(timeframe, second=delay_s)
    scheduler.add_job(
        func=run_once,
        trigger=trig,
        id=f"bot:{user_id}:{config_id}",
        args=[config_id, user_id, timeframe],
        max_instances=1,
        misfire_grace_time=misfire_s,
        coalesce=True,
        jitter=jitter_s,
        replace_existing=True,
    )

async def run_once(config_id, user_id, timeframe):
    close_ts = compute_last_closed_candle_ts(timeframe)  # from the SAME data source you trade on
    key = f"idemp:{config_id}:{timeframe}:{close_ts}"
    if await redis.setnx(key, "1"):
        await redis.expire(key, 7 * 24 * 3600)
        await ws.broadcast(user_id, {"type":"bot_status_update","config_id":config_id,"status":"running"})
        try:
            await orchestrator.run_autonomous_cycle(config_id, user_id, close_ts=close_ts)
            await ws.broadcast(user_id, {"type":"bot_status_update","config_id":config_id,"status":"completed"})
        except Exception as e:
            await ws.broadcast(user_id, {"type":"bot_status_update","config_id":config_id,"status":"error","error":str(e)})
    # else: duplicate fire; safely ignored
```

**Leader election (simple Postgres advisory lock):**

```python
# on startup
with pg_connection() as conn:
    got_lock = conn.execute("SELECT pg_try_advisory_lock(42)").scalar()
if not got_lock:
    log.info("Another leader active; scheduler disabled in this instance")
else:
    scheduler.start()
```

# Resource & concurrency notes

* You’re on AsyncIO. Prefer running the orchestrator **as async**; avoid shifting to threadpool unless you have CPU-bound work.
* Add a **global concurrency semaphore** (e.g., 50) around orchestration to cap bursts at candle boundaries.
* Expose Prometheus: `executions_total`, `executions_failed_total`, `exec_latency_seconds` (Histogram), `missed_runs_total`, `ws_broadcast_latency_ms`.

# WebSocket & UX

* Send `next_fire_at` (from Cron’s `get_next_fire_time`) on every status event so the UI is always correct, even after restarts.
* Include `close_ts` in the message so users see which candle was processed.

# Testing upgrades

* Make time calc functions accept `now: datetime` for deterministic tests.
* Add **property tests**: for any `now`, next fire time is in the future and within `(interval + delay]`.
* Add **HA tests**: simulate two schedulers; confirm idempotency + advisory lock prevent double trades.

# Config/data alignment (important)

* **Align to your data provider’s candle boundaries** (exchange or aggregator). Don’t assume weekly = Mon 00:00 UTC universally. Derive `close_ts` from “last closed candle” API and drive idempotency off that.

# Remove / adjust

* ❌ Manual deletion from `apscheduler_jobs` — risky and unnecessary.
* ❌ `active_bots` in memory as source of truth — persist instead.
* ⚠️ `misfire_grace_time=30` — raise per table above.

# Final recommendation

Adopt **Option B** but implement with **CronTrigger + idempotency + startup reconciliation + leader election**, not date-rescheduling. This gives you **zero drift, safe HA, clean recovery, and predictable cadence**, which is exactly what trading bots need.
