Must-fix risks (highest impact)

SSE robustness: Add event: types, id: (for resume), retry: and a heartbeat (:keepalive\n\n every 10–15s) so proxies and mobile radios don’t kill the stream. Set headers: Cache-Control: no-cache, Content-Type: text/event-stream, Connection: keep-alive, X-Accel-Buffering: no (Nginx).

Auth/tenancy: Do not trust /{user_id}. Authenticate the request and derive user_id server-side from the session/JWT. Otherwise one tab can read another user’s data.

DB load of “single query every 5s”: For 100+ users this becomes a thumper. Introduce a tiny cache layer (Redis keyed by dashboard:{user_id}) with 5s TTL. SSE reads from cache; background task refreshes it. This gives predictability and shields Postgres.

APScheduler in multi-instance: If you have >1 worker/pod, use a distributed lock (Redis SET NX EX or APScheduler’s SQL jobstores with misfire_grace_time) so one instance owns each job. Otherwise you’ll double-fire cycles.

Async DB driver + pooling: Your code is async. Use asyncpg (or SQLAlchemy 2.0 async) with a connection pool and pgbouncer. Don’t block the loop with sync psycopg2.

Ephemeral status lifecycle: Set explicit TTLs on Redis phase keys (e.g., 90–120s). Don’t rely on a cleanup task to run; crashes will otherwise leave zombie status.

Backpressure/crash safety in loops: All while True loops need try/except with jittered sleep on failure, and asyncio.CancelledError handling for clean shutdowns.

Design tweaks that will pay off
SSE stream contract (small but important)

Send typed events and ids; let the client resume via Last-Event-ID. Emit a heartbeat comment to keep the TCP alive.

Send diffs when you can (e.g., new decisions, changed positions) instead of full snapshots every tick. Keep the snapshot path as a fallback.

Server sketch (FastAPI/Starlette):

from fastapi import Depends, Response
from starlette.responses import StreamingResponse

@app.get("/api/dashboard-stream")
async def dashboard_stream(resp: Response, user=Depends(auth)):
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Content-Type"] = "text/event-stream"
    resp.headers["Connection"] = "keep-alive"
    resp.headers["X-Accel-Buffering"] = "no"

    async def gen():
        last_id = 0
        try:
            while True:
                data = await get_cached_dashboard_payload(user.id)  # Redis-backed
                last_id += 1
                yield f"id: {last_id}\n"
                yield "event: dashboard\n"
                yield f"data: {json.dumps(data, default=str)}\n\n"
                # Heartbeat
                yield f":keepalive {int(time.time())}\n\n"
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            return
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
    return StreamingResponse(gen())

Unified query: correctness & performance

Your CTE is fine conceptually, but:

Filter by user at the top and keep it through joins to guarantee row-level scoping.

json_agg returns null on empty sets—COALESCE to [] for client simplicity.

Per-bot decision limits: LIMIT 20 globally may starve some bots. Use a window:

recent_decisions AS (
  SELECT * FROM (
    SELECT d.*, ROW_NUMBER() OVER (PARTITION BY d.config_id ORDER BY d.created_at DESC) AS rn
    FROM decisions d
    JOIN bot_configs bc ON d.config_id = bc.config_id
    WHERE d.created_at > NOW() - INTERVAL '2 hours'
  ) s WHERE s.rn <= 5
)


Indexes you’ll want:

decisions (config_id, created_at DESC)

paper_trades (config_id, status, opened_at DESC)

paper_accounts (config_id) (unique)

configurations (user_id, state, config_id)

Consider a materialized view (per user) for the dashboard JSON if usage spikes, refreshed by a background task every 5s.

Direct Postgres vs Supabase SDK

I agree: pick Postgres. But don’t do raw sync psycopg inside async endpoints. Use:

asyncpg or SQLAlchemy 2.0 async core for composable SQL + typed results.

pgbouncer in transaction mode.

A read-only DB role for dashboard reads; RLS if you must (and if on Supabase PG).

Background services

position_monitor: If you scale horizontally, gate with a Redis leader lock so only one instance runs it (or partition by user shard).

Add jitter (sleep(3 + random.uniform(-0.3, 0.3))) to avoid thundering herd on exact seconds.

Wrap external calls (paper trading service) with timeouts + retries.

Execution status in Redis

Keys:

bot_execution:{config_id} -> JSON {phase, message, updated_at}, EX=120

Write helpers to atomically set status and publish a small Redis Pub/Sub event. Later you can wire SSE to Pub/Sub for true push, but keep the 5s poll as a baseline.

Frontend

Treat SSE payloads as authoritative; do optimistic UI for POSTs (flip spinners immediately) but reconcile on next SSE tick.

Implement resume via Last-Event-ID and show a “stale” badge if no dashboard event in >10s.

Keep one global EventSource and fan out to stores/components.

Migration & ops

Feature flag the SSE stream; canary to 5–10% of users.

Dual-run for a day: keep WS code dormant but togglable; log parity metrics (counts of bots/positions/decisions).

Load test: simulate 1k concurrent SSE clients, 5s ticks, measure DB QPS and tail latencies.

Observability you’ll want on day 1:

sse_connected_clients, sse_bytes_sent_total, sse_disconnects_total (by reason)

dashboard query latency p50/p95/p99

Redis hit ratio for dashboard:{user_id}

scheduler job runs, dedupe rate, job duration

Small correctness nits in your doc

“~20 SSE requests/sec for 100 users” → It’s ~100 persistent connections with 100 writes every 5s (i.e., 20 writes/sec on average). Clarify this for capacity planning.

Add COALESCE to your JSON aggregates to avoid null:

SELECT json_build_object(
  'bots', COALESCE((SELECT json_agg(bc.*) FROM bot_configs bc), '[]'::json),
  'positions', COALESCE((SELECT json_agg(op.*) FROM open_positions op), '[]'::json),
  'decisions', COALESCE((SELECT json_agg(rd.*) FROM recent_decisions rd), '[]'::json),
  'accounts', COALESCE((SELECT json_agg(ac.*) FROM account_summaries ac), '[]'::json),
  'timestamp', NOW()
);

Verdict

Green-light with edits. The architectural call—SSE + one unified data source + Redis for ephemeral status—is solid and will simplify your life. Shore up SSE reliability, DB load, and multi-instance scheduling, and you’ll get the reliability and UX you want without surprising infra costs.