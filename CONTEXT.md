# GGBot End-to-End Implementation Plan

## Update: Phases 1, 2, and 3 Complete! ✅
- **Phase 1** (Create Trading API): Successfully completed with all endpoints working and documented in API.md
- **Phase 2** (Extraction Module Updates): Configuration-driven extraction system implemented with MCP metadata integration
- **Phase 3** (Database Integration): Database schema already complete - no updates needed

## Project Overview
GGBot is a cryptocurrency trading system with three main modules:
1. **Extraction**: Fetches market data and calculates technical indicators using MCP
2. **Decision**: Uses LLMs to analyze market data and generate trading intents  
3. **Trading**: Executes trades on exchanges based on decision intents

## Current State Assessment

### ✅ Completed and Working Modules

#### Decision Module (`/decision/`)
- **Status**: Fully implemented, tested, working
- **Key File**: `decision/engine.py` (700+ lines, complete implementation)
- **Test**: `python -m tests.test_decision_module` (passes)
- **Function**: Generates trading intents using LLM analysis of market data
- **Input**: Market data from database
- **Output**: Structured trading intents for Trading Module

#### Trading Module Core (`/trading/`)
- **Status**: Core engine complete, tested, missing API wrapper
- **Key Files**: 
  - `trading/engine/service/llm_service.py` (working)
  - `trading/engine/service/validation_service.py` (working)  
  - `trading/engine/service/execution_service.py` (working)
- **Test**: `python -m tests.trading.test_trading_flow_simple` (passes, full end-to-end)
- **Function**: Executes trades on BitMEX testnet
- **Status**: Complete with API endpoints working and documented

#### Extraction Module (`/extraction/`)
- **Status**: Fully implemented with configuration-driven architecture ✅
- **Key Files**: 
  - `extraction/extraction_main.py` (ExtractionManager class, configuration-driven)
  - `extraction/sources/crypto_indicators_mcp.py` (MCP metadata integration)
  - `extraction/scheduled_extraction.py` (updated for config-driven execution)
- **Test**: `python -m extraction.scheduled_extraction --user-id=00000000-0000-0000-0000-000000000001` (passes)
- **Function**: Configuration-driven market data extraction with analytical LLM interpretation
- **Features**: 
  - MCP metadata for direct tool calls
  - User configuration from database
  - Raw indicator data + analytical interpretation
  - Plugin architecture for multiple data sources

## Implementation Plan

### ✅ Phase 1: Create Trading API (COMPLETED)

**Status**: Successfully completed with all endpoints working and documented in API.md.

### ✅ Phase 2: Configuration-Driven Extraction Module (COMPLETED)

**Status**: Successfully implemented with the following achievements:

**Key Accomplishments**:
- ✅ **ExtractionManager**: Configuration-driven orchestrator that reads user settings from database
- ✅ **CryptoIndicatorsMCPSource**: Direct MCP tool calls using metadata, no LLM selection needed
- ✅ **Analytical LLM Integration**: Focused on data analysis rather than trading recommendations
- ✅ **Database Integration**: Stores both raw indicator time series and analytical interpretations
- ✅ **Plugin Architecture**: Easy to add new data sources without core changes
- ✅ **Environment Variable Loading**: Reads from .env file for proper API key access
- ✅ **Legacy Compatibility**: Supports both new config-driven and old extraction methods

**Test Results**: Configuration-driven extraction working with RSI analysis for BTC/USDT on 15m and 1h timeframes

### ✅ Phase 3: Database Integration (COMPLETED)

**Status**: Database schema already complete - no updates needed.

**Assessment**: PostgreSQL MCP confirmed that the `trades` table exists with all required fields and enhancements beyond the minimum requirements. The database is ready for trade persistence.

### 🎯 Phase 4: End-to-End Integration Testing (CURRENT PRIORITY)

**Objective**: Test the complete pipeline (Extraction → Decision → Trading) to ensure all modules work together seamlessly.

**Test Sequence**:
1. **Test Extraction**: Run configuration-driven MCP extraction, verify database storage
2. **Test Decision**: Run decision module, verify intent generation  
3. **Test Trading API**: Send intent to POST /trade/execute, verify execution
4. **Test Full Pipeline**: Run all three modules in sequence

**Test Commands**:
```bash
# 1. Test extraction (updated for configuration-driven approach)
python -m extraction.scheduled_extraction --user-id=00000000-0000-0000-0000-000000000001

# 2. Test decision (modify test to output intent JSON)
python -m tests.test_decision_module

# 3. Test trading API
curl -X POST http://localhost:5000/trade/execute -H "Content-Type: application/json" -d @test_intent.json

# 4. Test full pipeline integration
python -m tests.test_full_pipeline  # To be created
```



## Environment Configuration

**Required API Keys**:
- `EXTRACTION_LLM_API_KEY`: OpenAI API key for extraction module LLM interpretation
- `TRADING_LLM_API_KEY`: OpenAI API key for trading module LLM services
- `EXCHANGE_API`: BitMEX testnet API key
- `EXCHANGE_SECRET`: BitMEX testnet secret key
- `EXCHANGE_NAME`: Exchange name for MCP data fetching (e.g., "binance")

**Database**: PostgreSQL (already configured)
**MCP Servers**: Crypto Indicators MCP (already set up in `core/mcp/servers/`)

## Success Criteria

**Completed**:
1. ✅ **Trading API Working**: Can receive intent JSON and execute trades
2. ✅ **Configuration-Driven Extraction**: MCP extraction with analytical interpretation  
3. ✅ **Database Integration**: Schema ready for trade persistence

**Remaining**:
4. ⏳ **End-to-End Flow Testing**: Verify Extraction → Decision → Trading pipeline works seamlessly
5. ⏳ **Trade Persistence**: Verify trades are properly stored in database
6. ⏳ **Integration Test Suite**: Create automated tests for full pipeline

## Key Implementation Notes

- **All modules are now complete** - Trading API, Decision Engine, and Extraction Manager
- **Configuration-driven approach** - User settings drive extraction behavior
- **Analytical focus** - Extraction LLM interprets data, not trading decisions
- **Test frequently** using the existing working test files as reference
- **Use testnet only** for all trading operations

### Important: Semi-Structured Intent Design

The Trading Module uses an LLM to interpret intents, so strict Pydantic validation at the intent level is counterproductive. Instead:

1. **Intent Structure**: Should be semi-structured with required fields but flexible values
   - Required fields: action, symbol, some risk indication
   - Flexible values: "go long" vs "enter_long", "Bitcoin" vs "BTC/USD", "conservative" vs "5%"
   - The Trading LLM will interpret these variations

2. **Where Validation Happens**: Strict validation occurs at the tool call level (ValidationService), not at the intent input level

3. **API Design**: The POST /trade/execute endpoint should accept flexible JSON, not enforce strict Pydantic models on the intent

### Phase 5: Prompt Consistency Review (LOW PRIORITY)

**Objective**: Ensure Decision Module prompts align with Trading Module expectations

**Specific Actions**:
1. Review Decision Module prompts in `decision/engine.py`
2. Check what fields the Decision Module is instructed to output
3. Verify alignment with Trading Module's expected intent structure
4. Update the Intent model in `trading/engine/model/intent.py`:
   - Remove strict enum validators (lines 58-76)
   - Remove IntentAction and SizeType enums
   - Keep fields but make them flexible strings without validation
   - The Trading LLM will interpret variations like "go long" vs "enter_long"
5. Ensure both modules agree on required vs optional fields

**Note**: This is low priority because the current system works - the Trading LLM successfully interprets Decision Module outputs. This review is for optimization and consistency.

## Quick Reference

### Database Utilities
- **Connection**: Use `from core.common.db import get_db_connection`
- **Config**: Database settings in `core.common.config.py` (DB_HOST, DB_PORT, etc.)
- **Pattern**: Always use context managers for connections
```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(query, params)
```

### Logging Pattern
- **Import**: `from core.common.logger import logger`
- **Usage**: Always bind user_id for context
```python
logger.bind(user_id=user_id).info("Message")
logger.bind(user_id=user_id).error(f"Error: {str(e)}")
```

### Example Intent JSON (from Decision Module)
```json
{
    "decision_id": "550e8400-e29b-41d4-a716-446655440000",
    "action": "enter_long",
    "symbol": "BTC/USD",
    "exchange": "bitmex",
    "timeframe": "15m",
    "collateral_amount": 1000,
    "leverage": 10,
    "stop_loss_price": 100000,
    "take_profit_price": 120000,
    "confidence": 0.85,
    "reasoning": "Strong bullish signals on multiple timeframes"
}
```
Note: With semi-structured design, fields like "action" could be "go long", "buy", etc.

### MCP Server Locations
- **CCXT MCP**: `core/mcp/servers/ccxt_mcp_server.py`
- **Indicators MCP**: `core/mcp/servers/crypto-indicators-mcp/index.js`
- **Client Classes**: `core/mcp/ccxt.py`, `core/mcp/indicators.py`

### Error Handling Pattern
```python
# API endpoint error handling
try:
    result = await trading_engine.execute(intent)
    return {"status": "success", "data": result}
except MCPError as e:
    logger.bind(user_id=user_id).error(f"MCP error: {str(e)}")
    return {"status": "error", "error": "Exchange connection failed", "details": str(e)}
except ValidationError as e:
    return {"status": "error", "error": "Invalid trade parameters", "details": str(e)}
except Exception as e:
    logger.bind(user_id=user_id).error(f"Unexpected error: {str(e)}")
    return {"status": "error", "error": "Internal server error"}
```

### Common Imports Pattern
```python
# Standard pattern for trading module files
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.common.db import get_db_connection
from core.mcp.exceptions import MCPError
```

### Testing Credentials
- BitMEX Testnet: https://testnet.bitmex.com/
- Get testnet API keys from account settings
- Testnet uses fake Bitcoin for safe testing

This plan provides the exact files to modify, specific functions to reference, required environment variables, and test commands to validate each phase.