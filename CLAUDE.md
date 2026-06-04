# ggbot Development Guide

**For architecture**: See `README.md`
**For current status**: See `ACTIVE.md` *(local working notes, not published)*.
**For session orientation**: `CLAUDE.local.md` *(gitignored)* carries the project-system manifest; tasks and plans live in the project tracker.

This guide covers development workflow, code patterns, and critical rules specific to this codebase.

---

## Essential Commands

### Environment Setup (CRITICAL)
```bash
# Navigate and activate virtual environment - ALWAYS DO THIS FIRST
cd /home/sev/ggbot
source /home/sev/ggbot/.venv/bin/activate
# Prompt should show: (.venv) sev@ggbot-vm:~/ggbot$

# Install dependencies
pip install -r requirements.txt

# Frontend setup
cd frontend && npm install
```

### Development Commands
```bash
# V2 Orchestrator (Main API server)
python ggbot.py

# Frontend
cd frontend && npm run dev     # Development
cd frontend && npx tsc --noEmit  # Type-check only (use instead of build)
cd frontend && npm run lint    # Lint check

# IMPORTANT: Do NOT run `npm run build` locally — Web3 dependencies (wagmi, viem,
# RainbowKit) cause OOM crashes on the VM. Use `npx tsc --noEmit` for type-checking
# and let Vercel handle production builds via git push.

# Testing (ALWAYS confirm with user before running)
python -m tests.test_name
python -m pytest tests/
```

### Process Management (PM2)
```bash
# Status and logs
pm2 status
pm2 logs ggbot              # API server (HTTP/SSE only)
pm2 logs ggbot-scheduler    # Bot execution (APScheduler + reconcile loop)
pm2 logs market-data-ws     # WebSocket market data cache

# Restart after code changes
pm2 restart ggbot           # API changes
pm2 restart ggbot-scheduler # Orchestrator/scheduler/decision/extraction changes

# Project-scoped operations — all 5 ggbot services live in PM2 namespace 'gg'
# (other projects on this VM share the PM2 daemon; never use `pm2 restart all`)
pm2 stop gg                 # Stop all ggbot services
pm2 restart gg              # Restart all ggbot services
pm2 start gg                # Start all ggbot services (if registered)

# Cold start — registers processes from the eco file (after pm2 delete / fresh daemon)
pm2 start ecosystem.config.js && pm2 save

# After any deliberate change to what-should-be-running, persist the boot snapshot
pm2 save
```

---

## Workflow Orchestration

1. **Plan Mode for Non-Trivial Tasks** — Use plan mode for 3+ step tasks or architectural decisions. If something goes sideways mid-implementation, STOP and re-plan immediately — don't keep pushing.
2. **Autonomous Bug Fixing** — When given a bug report: check `pm2 logs`, trace the error, find root cause, fix it. Don't ask Sev to read logs for you. Zero hand-holding.
3. **Verification Before Done** — Never mark complete without proving it works. Run `npx tsc --noEmit` for frontend, run relevant tests, check `pm2 logs` after restart. Demonstrate correctness.
4. **Minimal Impact** — Make every change as simple as possible. Touch only what's necessary. Find root causes — no temporary fixes or workarounds.
5. **Self-Improvement Loop** — After corrections from Sev, update the relevant docs (CLAUDE.md conventions, module READMEs, CLAUDE.local.md pitfalls) to prevent the same mistake.

---

## Development Guidelines

### Code Style
- **Import order**: stdlib → third-party → local modules
- **Naming**: snake_case (variables/functions), PascalCase (classes), UPPER_SNAKE_CASE (constants)
- **Indentation**: 4 spaces
- **Type hints**: Follow PEP 484 where possible
- **Error handling**: Use specific exceptions, log with `core.common.logger`

### Documentation Style

**CHANGELOG.md - Telegraphic Style (CRITICAL)**:
- Omit articles (a, an, the) and conjunctions where possible
- Maintain specificity: include file references, error details, technical accuracy
- Target 3-8 lines per entry for recent work, 1-3 lines for older entries
- Example: "WebSocket cache 3 candles, bots need 100 → RSI failed" NOT "The WebSocket cache had 3 candles but the bots requested 100 which caused RSI to fail"
- See CHANGELOG.md header for complete guidelines

### Logging Pattern

**File**: `core/common/logger.py` — Loguru with dynamic format functions

**Format**: `{timestamp} | {level} | {module}:{function}:{line} [{context}] - {message}`
- Context tag `[run=...,cfg=...,uid=...]` appears only when fields are bound
- `config_id` and `user_id` truncated to first 8 chars; `run_id` is 6 hex chars
- No context = no brackets (clean output for non-bot log lines)

**Log levels** (what goes where):
- **DEBUG**: Happy-path detail (cache hits, candle fetches, storage confirmations, per-timeframe results)
- **INFO**: Meaningful state transitions (cycle start/complete, permission checks, LLM calls, decision results, free run tracking)
- **WARNING**: Recoverable issues (non-critical fetch failures, permission blocks)
- **ERROR**: Failures requiring attention (extraction/decision/trading failures, unexpected exceptions)

**Binding context** (bot cycle correlation):
```python
from core.common.logger import logger

# Simple binding — config_id/user_id appear in context tag
logger.bind(config_id=config_id).info("Decision completed")

# In bot cycle — run_id threads from run_once() through entire chain
# All log lines in one cycle share the same run_id for grep correlation
logger.bind(config_id=config_id, run_id=run_id).info("Starting cycle")

# In DecisionEngineV2 — use _log_bind() helper (auto-includes config_id + run_id)
self._log_bind().info("Routing to opportunity analysis")
self._log_bind(symbol=symbol).error("Market data fetch failed")
```

**Key rule**: Demote to DEBUG unless the log represents a **state transition** or **error**. If a log line fires every cycle for every bot and says "doing X" rather than "X changed/failed", it's DEBUG.

### Database Access

**V2 uses Supabase for all database operations**. Use direct PostgreSQL connections via `core.common.db` for V2 orchestrator.

```python
# ASYNC context (scheduler bot cycles) — ALWAYS use async helpers
# Runs psycopg2 in thread pool, never blocks the event loop
from core.common.db import db_fetch_one, db_fetch_all, db_execute

row = await db_fetch_one("SELECT * FROM table WHERE id = %s", (id,))
rows = await db_fetch_all("SELECT * FROM table")
await db_execute("INSERT INTO table (...) VALUES (%s)", (val,))

# For sync functions called from async code, wrap the call:
await asyncio.to_thread(some_sync_function, arg1, arg2)

# SYNC context (API endpoints, monitors) — use get_db_connection directly
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM table")
        results = cur.fetchall()
```

**CRITICAL**: In the scheduler process, NEVER use bare `get_db_connection()` in async code — it blocks the event loop and causes bot deadlocks at candle boundaries. Always use `db_fetch_one`/`db_fetch_all`/`db_execute` or `asyncio.to_thread()`.

### Two-Process Architecture
```
ggbot.py (API only)          ggbot_scheduler.py (bot execution)
  - HTTP/SSE endpoints          - APScheduler jobs
  - "Run Now" execution         - Reconcile loop (10s DB poll)
  - Writes state to DB          - Reads state from DB
  - Stays fast always           - Handles LLM-heavy bot cycles
```
Orchestrator class lives in `core/orchestrator/orchestrator.py`, shared by both processes.
Start/stop: API writes `state='active'/'inactive'` → scheduler detects within 10s.

### V2 Data Flow Pattern
```python
# V2 orchestrator sequential execution pattern (core/orchestrator/orchestrator.py)
extraction_result = await self._run_extraction_v2(...)
decision_result = await self._run_decision_v2(config, extraction_result)
trading_result = await self._run_trading_v2(config, decision_result)
```

---

## Permission & Gating System

**Single source of truth**: `can_activate_bots` on `UserProfile` (`core/domain/user_profile.py:116`). This is the only real permission. All other `can_use_*` properties (`can_use_premium_features`, `can_use_live_trading`, `can_publish_telegram_signals`, `can_use_signal_validation`, `is_premium_user`) are **deprecated aliases** that return `can_activate_bots`. Do not create new feature-specific permission properties.

```python
@property
def can_activate_bots(self) -> bool:
    return (
        self.subscription_tier in [PREPAID, USAGE_BASED, PRO] and
        self.has_active_subscription and
        not self.subscription_expired
    )
```

### Two-Layer Gating Model

**Layer 1 — Activation gate** (inline, synchronous):
- `start_bot` endpoint (`ggbot.py:2905`): checks `can_activate_bots` → 403 if false. PREPAID tier also checks `get_user_credit_balance() > 0` → 402 if empty.
- Orchestrator `run_autonomous_cycle` (`core/orchestrator/orchestrator.py:136`): re-checks `can_activate_bots` per run. Exceptions: free first run (`!first_run_used`) and free manual runs (`free_runs_remaining > 0`). If permission lost mid-lifecycle, auto-sets bot `state='inactive'` and scheduler drops the job within 10s.
- **Does NOT re-check credit balance per run** — this is intentional. Credit enforcement is Layer 2.

**Layer 2 — Async credit enforcement** (out-of-band, polling):
- `core/monitoring/usage_monitor.py` runs inside the `account-monitor` PM2 service, polling every 60s.
- **PREPAID users** (crypto/credit-purchase tier): hard-pauses bots when `net_balance <= 0` by flipping `state='inactive'`. Worst-case overage window: ~70s (60s check + 10s reconcile).
- **USAGE_BASED users** (Stripe metered): soft — notifies on low/depleted but lets bots keep running (overage billed via Stripe). Only hard-pauses on subscription `past_due`.
- Writes pause reason to Redis `bot:pause_reason:{config_id}` (24h TTL) for frontend display.
- LLM cost accrual flows into `activities.platform_cost_usd` (prepaid, all-time) or Redis `usage:user:{uid}:{YYYY-MM}` (usage-based, monthly) — monitor subtracts from credit pool.

### Adding New Features

New premium-gated features should check `can_activate_bots` directly — do not add new `can_use_*` properties. If frontend needs to know about a capability, expose `can_activate_bots` via `/api/v2/me` and gate UI on that.

```python
# Backend
if not profile.can_activate_bots:
    raise HTTPException(403, "Subscription required")

# Frontend (frontend/lib/permissions.tsx)
if (!userProfile.can_activate_bots) return <UpgradePrompt />
```

---

## Testing Guidelines

**CRITICAL**: Always check with user before running any tests. NEVER run a test without checking in with the user first, in case we need to restart servers or just for any reason at all.

### Test Categories
- **Unit tests**: Individual module components
- **Integration tests**: End-to-end pipeline validation (`tests/test_trading_flow_simple.py`)
- **MCP tests**: Tool connectivity and reliability
- **API tests**: Endpoint functionality

---

## CRITICAL RULES

### Security Requirements
**ABSOLUTE RULE**: NEVER, NEVER, NEVER HARDCODE SECRETS OR CREDENTIALS. ALWAYS USE .env variables. UNDER NO CIRCUMSTANCES SHOULD YOU EVER HARDCODE SECRETS OF ANY SORT EVER. IF YOU PUT CREDENTIALS INTO ANY FILE, EVER, YOU WILL IMMEDIATELY BE TERMINATED.

### Truthfulness and Data Integrity
**ABSOLUTE RULE**: NEVER LIE. NEVER MAKE UP DATA. NEVER FABRICATE ANSWERS.
- If a query fails, SAY IT FAILED. Don't make up results.
- If you see errors, STOP and report the errors. Don't continue with fabricated analysis.
- If you don't have data, SAY YOU DON'T HAVE IT. Don't guess or infer.
- If something doesn't work, ADMIT IT IMMEDIATELY. Don't pretend it worked.
- HONESTY ABOVE ALL ELSE. The user needs to trust your output completely.
- If you catch yourself about to present analysis based on failed queries, STOP IMMEDIATELY.

### Database Query Requirements
**ABSOLUTE RULE**: FOR SUPABASE DATABASE QUERIES, ALWAYS USE THE SUPABASE SKILL.
- NEVER use psql commands directly (they don't work with Supabase remote connections)
- NEVER use mcp__postgres__query (it doesn't work with Supabase)
- ALWAYS use `Skill(command="supabase-db-query")` to activate the Supabase skill
- After activating the skill, use heredoc syntax with `core.common.db.get_db_connection()`
- The skill provides the correct method and examples
- If you catch yourself about to use psql or postgres MCP, STOP and use the Supabase skill instead

### Development Approach
- You need to be methodical. Slow. Think hard. Ask questions. Don't make assumptions.
- We're working with very new tools with changing documentation.
- ANY TIME you think it might be helpful to look at the latest documentation, just say so! We'll find it for you and provide it.
- Always restart servers after code changes when needed (check with user)

### Frontend Deployment
- We deploy frontend to Vercel by pushing to git. We do not use localhost for user testing.
- **NEVER run `npm run build` locally** — Web3 dependencies cause OOM and crash the VM. Use `npx tsc --noEmit` for type-checking instead.
- The user will access the deployed frontend on Vercel. Any changes you make if you want them tested will need to be done via this method of pushing to git and having the user share the console logs with you.

---

## Troubleshooting

### Common Issues
- **MCP connection failures**: Use exponential backoff with async context managers
- **Symbol mapping**: Internal symbols auto-convert to exchange format
- **Virtual environment**: Always activate before running Python commands
- **PM2 processes**: Check `pm2 status` if services aren't responding
- **Frontend errors**: Ask user to share Vercel console logs

### Log Files
- Application logs: `logs/ggbot.log` (rotated, compressed)
- PM2 logs: `pm2 logs [service-name]`
- WebSocket service: `pm2 logs market-data-ws`

---

## Documentation Structure

Published docs:
- **README.md** - Architecture overview and platform capabilities
- **ROADMAP.md** - Forward-looking platform direction
- **CHANGELOG.md** - Complete history of features, fixes, and improvements
- **CLAUDE.md** - This file - development workflow and code patterns

Local working notes (on-disk only, not published):
- **CLAUDE.local.md** - Project-system manifest (session orientation, pitfalls)
- **ACTIVE.md** - Current production status, services, ports, commands (regenerate via `scripts/status_check.py --update`)

Tasks and planning docs live in the project tracker (see CLAUDE.local.md), not in repo files.

## Documentation Quick Reference by Topic

**Before investigating issues, consult the relevant module README:**

| Issue Type | Primary Documentation |
|------------|----------------------|
| Trading mode behavior (paper/hyperliquid) | `trading/README.md` |
| Position sizing, P&L calculations | `trading/README.md` |
| Data extraction, indicators, preprocessors | `extraction/v2/README.md` |
| Market intelligence, Grok sources | `market_intelligence/README.md` |
| Decision engine, LLM prompts | `decision/README.md` |
| Updating LLM models/tiers | `decision/llm_providers/MODEL_UPDATE.md` |
| Frontend components, SSE, bot rail | `frontend/README.md` |
| SEO, blog, OG images, content strategy | `frontend/SEO.md` |
| Nansen API, smart money data, MCP setup | `DOCS/NANSEN.md` |
| Database design rationale | `DOCS/DATABASE_CONTEXT.md` |
| Database schema questions | `ACTIVE.md` (Database Schema section; local working notes) |
| API endpoint behavior | `ACTIVE.md` (Core API Endpoints section; local working notes) |

**Rule of Thumb**: If you're about to make an assumption about how a module works, read its README first.

---

**Remember**: The platform is called **ggbots** (lowercase gg, always). The repo is called **ggbot** (without the s). Platform is at **ggbots.ai**.
