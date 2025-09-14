# ggbot Development Guide

## Project Overview

ggbots is an autonomous AI trading platform with a three-agent architecture: Extraction → Decision → Trading. It combines browser automation, advanced reasoning LLMs, and sophisticated execution engines to create autonomous trading agents that operate 24/7.

the platform is called ggbots, NOT GGBots. the repo is called ggbot (without the s) which is fine, but the platform itself is called ggbots.ai, and to clarify, NO capital GG. It's lowercase gg, always. 

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
# Status and logs (V2 system)
pm2 status
pm2 logs ggbot          # Main V2 orchestrator
pm2 restart ggbot       # Restart after code changes
```

## Architecture Overview

### Core Agent Pipeline
```
Market Data → Extraction Agent → Decision Agent → Trading Agent → Exchange
     ↑              ↓               ↓              ↓           ↓
   Sources     Market Analysis   AI Reasoning   Execution   Results
```

### Module Structure
- **`ggbot.py`** - Main V2 orchestrator with APScheduler and WebSocket
- **`extraction/v2/`** - Pure Python technical analysis using pandas-ta
- **`decision/engine_v2.py`** - GPT-5 reasoning with user customization  
- **`trading/paper/`** - Supabase paper trading with position management
- **`core/`** - Config system, database connections, scheduler utils
- **`frontend/dashboard-v2/`** - Real-time React dashboard
- **`tests/`** - Comprehensive test suite with end-to-end validation

## Development Guidelines

### Code Style
- **Import order**: stdlib → third-party → local modules
- **Naming**: snake_case (variables/functions), PascalCase (classes), UPPER_SNAKE_CASE (constants)
- **Indentation**: 4 spaces
- **Type hints**: Follow PEP 484 where possible
- **Error handling**: Use specific exceptions, log with `core.common.logger`

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

## Testing Guidelines

**CRITICAL**: Always check with user before running any tests. NEVER run a test without checking in with the user first, incase we need to restart servers or just for any reason at all.

### Test Categories
- **Unit tests**: Individual module components
- **Integration tests**: End-to-end pipeline validation (`tests/test_trading_flow_simple.py`)
- **MCP tests**: Tool connectivity and reliability
- **API tests**: Endpoint functionality

### Key Infrastructure Components

**V2 Orchestrator (`ggbot.py`)**
- FastAPI server with APScheduler integration
- WebSocket real-time status broadcasting  
- Multi-user isolation with authentication

**Configuration System**
- Supabase `configurations` table with JSONB config_data
- Config-ID architecture enables multiple bots per user
- V2 templates with llm_config and subscription tiers

**Database Layer**
- Multi-user isolation with `user_id` + `config_id` architecture
- Paper trading tables: `paper_accounts`, `paper_trades`
- Decision audit trail in `decisions` table

## CRITICAL RULES

### Security Requirements
**ABSOLUTE RULE**: NEVER, NEVER, NEVER HARDCODE SECRETS OR CREDENTIALS. ALWAYS USE .env variables. UNDER NO CIRCUMSTANCES SHOULD YOU EVER HARDCODE SECRETS OF ANY SORT EVER. IF YOU PUT CREDENTIALS INTO ANY FILE, EVER, YOU WILL IMMEDIATELY BE TERMINATED.

### Development Approach
- You need to be methodical. Slow. Think hard. Ask questions. Don't make assumptions. 
- We're working with very new tools with changing documentation. 
- ANY TIME you think it might be helpful to look at the latest documentation, just say so! We'll find it for you and provide it.

### Environment Variables
```bash
# Database (Supabase)
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=xxx

# LLM APIs
OPENAI_API_KEY=xxx
DEEPSEEK_API_KEY=xxx

# Hummingbot Integration
HBOT_USERNAME=xxx
HBOT_PASSWORD=xxx
HUMMINGBOT_API_URL=http://localhost:8888
```

## Production Context

### Live Systems
- **ggShot Integration**: Processes 140+ crypto pairs with Telegram integration
- **API Endpoints**: Main backend at `https://ggbots-api.nightingale.business`
- **Frontend**: Next.js app at `https://ggbot-app.vercel.app`


### Risk Management
- Position sizing based on AI confidence scoring
- Real-time monitoring with automatic position adjustment
- User-defined guardrails for leverage and exposure limits

## Troubleshooting

### Common Issues
- **MCP connection failures**: Use exponential backoff with async context managers
- **Symbol mapping**: Internal symbols auto-convert to exchange format
- **Virtual environment**: Always activate before running Python commands
- **PM2 processes**: Check `pm2 status` if services aren't responding

### Log Files
- Application logs: `logs/ggbot.log` (rotated, compressed)
- PM2 logs: `pm2 logs [service-name]`

## Documentation References 
- **Architecture**: `README.md`
- **Current Status**: `ACTIVE.md`, `TODO.md`
- We deploy our frontend to vercel by pushing to git. We do not use localhost. You can test builds locally to see if they compile, but when it comes to seeing console logs, you will need to ask the user to share them. The user will access the deployed frontend on vercel. Any changes you make if you want them tested will need to be doen via this method of pushing to git and having the user share the console logs with you.