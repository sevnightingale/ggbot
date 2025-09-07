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
# Main API server
python main_api.py

# Individual modules
python extraction/run_extraction.py
python decision/run_api.py
python -m extraction.scheduled_extraction --update

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
# Start all services
pm2 start ecosystem.config.js

# Individual services
pm2 start ggbots-api
pm2 start ggshot-filter
pm2 start ccxt-mcp-server

# Status and logs
pm2 status
pm2 logs ggbots-api
```

## Architecture Overview

### Core Agent Pipeline
```
Market Data → Extraction Agent → Decision Agent → Trading Agent → Exchange
     ↑              ↓               ↓              ↓           ↓
   Sources     Market Analysis   AI Reasoning   Execution   Results
```

### Module Structure
- **`extraction/`** - Browser automation + technical indicators via MCP servers
- **`decision/`** - AI reasoning with DeepSeek R1/GPT-4 for trade decisions
- **`trading/`** - Hummingbot integration for professional execution
- **`core/`** - Shared infrastructure (MCP, config, database, scheduling)
- **`frontend/`** - Next.js multi-bot management interface
- **`ggshot/`** - Production signal processing (140+ crypto pairs, Telegram integration)
- **`database/`** - PostgreSQL schema with migrations
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

**Note**: Direct PostgreSQL connections via MCP are not available due to IPv6 connectivity issues with Supabase. Use the Supabase REST API or Python client instead. Credentials are stored in `.env` file.

```python
# Option 1: Direct PostgreSQL (when network allows)
from core.common.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM table")
        results = cur.fetchall()

# Option 2: Supabase REST API (recommended)
import os
import requests
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')

headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

response = requests.get(f'{url}/rest/v1/table_name', headers=headers)
data = response.json()
```

### MCP Integration Pattern
```python
from core.mcp.client import MCPClient
from core.mcp.session import create_indicators_session

async with create_indicators_session() as session:
    # Use snake_case for tool names
    result = await session.call_tool("calculate_rsi", {
        "symbol": "BTC/USDT",
        "timeframe": "15m"
    })
```

## Testing Guidelines

**CRITICAL**: Always check with user before running any tests. NEVER run a test without checking in with the user first, incase we need to restart servers or just for any reason at all.

### Test Categories
- **Unit tests**: Individual module components
- **Integration tests**: End-to-end pipeline validation (`tests/test_trading_flow_simple.py`)
- **MCP tests**: Tool connectivity and reliability
- **API tests**: Endpoint functionality

### Key Infrastructure Components

**MCP (Model Context Protocol) Servers**
- `core/mcp/servers/ccxt_mcp_server.py` - Exchange connectivity
- `core/mcp/servers/indicators_mcp_server.py` - Technical indicators
- Always use async context managers and snake_case naming for MCP connections

**Configuration System**
- JSON blob configuration in PostgreSQL `configurations` table
- Config-ID architecture enables multiple bots per user
- Templates in `core/config/`

**Database Layer**
- Multi-user isolation with `user_id` + `config_id` architecture
- Complete audit trail via `strategy_runs` table
- Universal trade lifecycle tracking in `trades` table

## CRITICAL RULES

### Security Requirements
**ABSOLUTE RULE**: NEVER, NEVER, NEVER HARDCODE SECRETS OR CREDENTIALS. ALWAYS USE .env variables. UNDER NO CIRCUMSTANCES SHOULD YOU EVER HARDCODE SECRETS OF ANY SORT EVER. IF YOU PUT CREDENTIALS INTO ANY FILE, EVER, YOU WILL IMMEDIATELY BE TERMINATED.

### Development Approach
- You need to be methodical. Slow. Think hard. Ask questions. Don't make assumptions. 
- We're working with very new tools with changing documentation. 
- ANY TIME you think it might be helpful to look at the latest documentation, just say so! We'll find it for you and provide it.

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://...

# LLM APIs
OPENAI_API_KEY=xxx
DEEPSEEK_API_KEY=xxx

# Exchange APIs (testnet)
BITMEX_API_KEY=xxx
BITMEX_SECRET=xxx
BITMEX_TESTNET=true
```

## Production Context

### Live Systems
- **ggShot Integration**: Processes 140+ crypto pairs with Telegram integration
- **API Endpoints**: Main backend at `https://ggbots-api.nightingale.business`
- **Frontend**: Next.js app at `https://ggbot-app.vercel.app`

### Symbol Mapping
- Internal format: `BTC/USDT`
- BitMEX format: `BTC/USDT:USDT` (handled automatically)
- Minimum order size: 100 contracts on BitMEX

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
- **Architecture**: `DOCS/OVERVIEW.md`, `DOCS/FLOW.md`
- **Current Status**: `DOCS/ACTIVE.md`
- **Testing**: `tests/TEST.md`
- **Module READMEs**: `extraction/README.md`, `decision/README.md`, etc.

When working with this codebase, prioritize understanding the three-agent pipeline flow and always respect the security requirements around credential management.