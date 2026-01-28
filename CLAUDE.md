# ggbot Development Guide

**For onboarding**: Read `GO.md` first for complete project context.
**For documentation updates**: Use `@OK.md` mid-session to update docs properly.
**For architecture**: See `README.md`
**For current status**: See `ACTIVE.md`

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
cd frontend && npm run build   # Production build
cd frontend && npm run lint    # Lint check

# Testing (ALWAYS confirm with user before running)
python -m tests.test_name
python -m pytest tests/
```

### Process Management (PM2)
```bash
# Status and logs
pm2 status
pm2 logs ggbot          # Main V2 orchestrator
pm2 logs market-data-ws # WebSocket market data cache
pm2 restart ggbot       # Restart after code changes
```

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
- See CHANGELOG.md header and GO.md "When Work is Completed" section for complete guidelines

### Logging Pattern
```python
from core.common.logger import logger

logger.bind(user_id="user_id").info("message")
logger.bind(user_id="user_id").error("error details")
```

### Database Access

**V2 uses Supabase for all database operations**. Use direct PostgreSQL connections via `core.common.db` for V2 orchestrator.

```python
# V2 standard - Direct Supabase PostgreSQL
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM table")
        results = cur.fetchall()

# For specific integrations - Supabase client
from trading.paper.supabase_service import SupabasePaperTradingService
service = SupabasePaperTradingService()
```

### V2 Data Flow Pattern
```python
# V2 orchestrator sequential execution pattern
extraction_result = await self._run_extraction_v2(...)
decision_result = await self._run_decision_v2(config, extraction_result)
trading_result = await self._run_trading_v2(config, decision_result)
```

---

## Permission System Pattern

**CRITICAL**: Premium feature permissions use @property methods on UserProfile, NOT standalone functions.

### Backend Pattern (core/domain/user_profile.py)
```python
@property
def can_use_live_trading(self) -> bool:
    """Check if user can use Symphony live trading."""
    return self.can_use_premium_features
```

### Usage in API Endpoints (ggbot.py)
```python
# Load profile
profile = await user_service.get_profile(user_id)

# Check permission directly on profile object
if profile.can_use_live_trading:
    # Execute premium feature
```

### Exposing to Frontend (/me endpoint)
```python
# In /api/v2/me endpoint response
{
    "can_use_premium_features": profile.can_use_premium_features,
    "can_publish_telegram_signals": profile.can_publish_telegram_signals,
    "can_use_signal_validation": profile.can_use_signal_validation,
    "can_use_live_trading": profile.can_use_live_trading  # Add new permissions here
}
```

### Frontend Integration (frontend/lib/permissions.tsx)
```typescript
// 1. Add to UserProfile interface
interface UserProfile {
  can_use_live_trading: boolean  // New permission
}

// 2. Add to canAccess switch
case 'live_trading':
  return userProfile.can_use_live_trading
```

**DO NOT create standalone permission functions** - always use @property methods on UserProfile class.

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
- You can test builds locally to see if they compile, but when it comes to seeing console logs, you will need to ask the user to share them.
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

- **GO.md** - Start here for onboarding procedure
- **OK.md** - Mid-session documentation update workflow (invoke with `@OK.md`)
- **README.md** - Architecture overview and platform capabilities
- **ACTIVE.md** - Current production status, services, ports, commands
- **TODO.md** - Current development tasks and roadmap
- **CHANGELOG.md** - Complete history of features, fixes, and improvements
- **CLAUDE.md** - This file - development workflow and code patterns

## Documentation Quick Reference by Topic

**Before investigating issues, consult the relevant module README:**

| Issue Type | Primary Documentation |
|------------|----------------------|
| Trading mode behavior (paper/symphony/aster) | `trading/README.md` |
| Position sizing, P&L calculations | `trading/README.md` |
| Data extraction, indicators, preprocessors | `extraction/v2/README.md` |
| Market intelligence, Grok sources | `market_intelligence/README.md` |
| Decision engine, LLM prompts | `decision/README.md` |
| Updating LLM models/tiers | `decision/llm_providers/MODEL_UPDATE.md` |
| Agent behavior, MCP tools, strategy | `agent/README.md` |
| Frontend components, SSE, bot rail | `frontend/README.md` |
| Database schema questions | `ACTIVE.md` (Database Schema section) |
| API endpoint behavior | `ACTIVE.md` (Core API Endpoints section) |

**Rule of Thumb**: If you're about to make an assumption about how a module works, read its README first.

---

**Remember**: The platform is called **ggbots** (lowercase gg, always). The repo is called **ggbot** (without the s). Platform is at **ggbots.ai**.
