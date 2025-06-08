# GGBot Universal Trade Lifecycle Testing Context

## Overview
This document contains all the context needed to run and troubleshoot the new Universal Trade Lifecycle Management System tests. We just completed a major refactor from a phantom-trade reconciliation system to a position-based trade lifecycle system.

## What We Just Finished Building

### Universal Trade Lifecycle Management System
- **Old System**: Complex phantom-trade reconciliation with aggregation logic
- **New System**: Simple position-based lifecycle where exchange positions drive trade state
- **Key Principle**: Exchange is the single source of truth - database tracks what exchange shows

### Key Components:
1. **trades table**: Now tracks position-based lifecycle (open/closed)
2. **strategy_runs table**: Audit trail of all trading decisions with scenarios (TRADE_ENTRY, TRADE_MANAGEMENT, TRADE_EXIT)
3. **trade_orders table**: Detailed order tracking including TP/SL orders
4. **trades_legacy view**: Backward compatibility for decision module

## Test Files Structure

### 1. `tests/new_trade.py` 
Tests the NEW_TRADE pipeline:
- No existing positions
- Extraction � Decision (NEW_TRADE mode) � Trading � Verification
- Should create:
  - New position on exchange
  - Trade record in database
  - strategy_runs entry with TRADE_ENTRY scenario

### 2. `tests/manage_trade.py`
Tests the MANAGE_TRADE pipeline:
- Requires existing position (run new_trade.py first)
- Extraction � Decision (MANAGE_TRADE mode) � Trading � Verification
- Should create:
  - strategy_runs entry with TRADE_MANAGEMENT scenario
  - Position adjustments or closure

## Critical Configuration

### Config ID Architecture
- **PRIMARY KEY**: Everything uses `config_id = "a93de31b-9b8a-42e3-827d-c31e580f5f36"`
- **User ID**: `"00000000-0000-0000-0000-000000000001"` (default test user)
- **Symbol**: `"BTC/USDT"` (will be mapped to exchange-specific format)
- **Exchange**: `"bitmex"` testnet

### Environment Requirements (.env file)
```
EXCHANGE_API=your_bitmex_testnet_api_key
EXCHANGE_SECRET=your_bitmex_testnet_secret
DECISION_LLM_API_KEY=your_deepseek_api_key
TESTNET=1
```

## API Flow

### 1. Extraction API
- Endpoint: `POST /extraction/api/extraction/run`
- Fetches RSI indicators via crypto-indicators-mcp
- Stores in market_data table
- Returns extraction_id for status polling

### 2. Decision API  
- Endpoint: `POST /decision/api/decision/analyze`
- **CRITICAL**: Must include `config_id` in payload
- Determines mode (NEW_TRADE/MANAGE_TRADE) based on existing trades
- Uses trades_legacy view for backward compatibility
- Stores decisions in strategy_runs table

### 3. Trading API
- Endpoint: `POST /trading/trade/execute`
- **CRITICAL**: Intent must include `config_id`
- Creates trade record and strategy_runs entry
- Uses LLM to interpret intent and generate CCXT tool calls

### 4. Dashboard API
- Endpoint: `GET /dashboard/api/dashboard/{user_id}/trades`
- Uses trades_legacy view with field mappings
- Returns all user trades (not filtered by config_id currently)

## Key Files and Their Roles

### Database Migrations
- `database/0012_universal_trade_lifecycle.sql` - Core system transformation
- `database/0013_enhanced_trade_lifecycle.sql` - Added config_id, TP/SL tracking, strategy_runs

### Core Services
- `core/monitoring/service.py` - AccountMonitoringService syncs exchange state
- `trading/lifecycle_manager.py` - TradeLifecycleManager handles position�trade sync
- `trading/engine.py` - TradeManager creates trades and strategy_runs

### Decision Module
- `decision/engine.py` - Uses trades_legacy view, stores in strategy_runs
- `decision/api.py` - Updated to accept config_id parameter

### Test Utilities
- `verify_strategy_runs()` - Checks audit trail was created
- `verify_exchange_sync()` - Syncs exchange positions with database

## Common Issues and Solutions

### 1. Missing Config ID
**Issue**: TradeLifecycleManager created without config_id
**Fix**: Pass DEFAULT_CONFIG_ID as third parameter
```python
lifecycle_manager = TradeLifecycleManager(user_id, "bitmex", DEFAULT_CONFIG_ID)
```

### 2. No Strategy Runs Created
**Issue**: Trade created but no audit trail
**Cause**: config_id not passed through the pipeline
**Fix**: Ensure config_id in decision intent and trading execution

### 3. Decision API Error
**Issue**: "Configuration 'default' not found"
**Fix**: Pass config_id directly instead of relying on config_name

### 4. No Exchange Position
**Issue**: manage_trade.py fails with no position
**Fix**: Run new_trade.py first to create a position

## Test Execution Flow

### NEW_TRADE Test:
1. **Health Check**: Verify all APIs running
2. **Setup Monitoring**: Initialize exchange connection, sync account state
3. **Extraction**: Fetch BTC/USDT indicators (RSI)
4. **Decision**: Analyze in NEW_TRADE mode (no existing positions)
5. **Trading**: Execute trade if decision says enter
6. **Verification**:
   - Exchange has real position
   - Database has trade record  
   - strategy_runs has TRADE_ENTRY
   - Trade lifecycle synced

### MANAGE_TRADE Test:
1. **Position Check**: Verify existing position exists
2. **Extraction**: Get latest market data
3. **Decision**: Analyze in MANAGE_TRADE mode with position context
4. **Trading**: Execute management action (hold/adjust/close)
5. **Verification**:
   - Position changes reflected on exchange
   - strategy_runs has TRADE_MANAGEMENT entry

## Database Queries for Troubleshooting

```sql
-- Check trades
SELECT * FROM trades WHERE user_id = '00000000-0000-0000-0000-000000000001' AND status = 'open';

-- Check strategy runs
SELECT * FROM strategy_runs WHERE config_id = 'a93de31b-9b8a-42e3-827d-c31e580f5f36' ORDER BY created_at;

-- Check market data
SELECT * FROM market_data WHERE user_id = '00000000-0000-0000-0000-000000000001' ORDER BY updated_at DESC LIMIT 5;

-- Check account state
SELECT * FROM account_states WHERE user_id = '00000000-0000-0000-0000-000000000001' ORDER BY updated_at DESC LIMIT 1;

-- Verify config exists
SELECT * FROM configurations WHERE config_id = 'a93de31b-9b8a-42e3-827d-c31e580f5f36';
```

## Running the Tests

```bash
# Setup
cd /home/sev/ggbot
source .venv/bin/activate

# Make sure API server is running (separate terminal)
python main_api.py

# Run tests in order
python tests/new_trade.py    # Creates position
python tests/manage_trade.py  # Manages position
```

## Expected Success Output

### new_trade.py Success:
```
 NEW TRADE scenario completed successfully!
  - Real exchange positions: 1
  - Database trades: 1
  - Trade lifecycle: 1 opened, 0 updated
  - Strategy runs: VERIFIED 
  - Sync errors: 0
=� Final system state: CLEAN - database matches exchange reality via universal trade lifecycle
```

### manage_trade.py Success:
```
 MANAGE TRADE scenario completed successfully!
  - Exchange positions: 1 (or 0 if closed)
  - Database trades: 1
  - Trade lifecycle updated: 1 (or closed: 1)
  - Strategy runs: VERIFIED 
=� Final system state: CLEAN - database matches exchange reality via universal trade lifecycle
```

## Key Architecture Decisions

1. **Config-Centric**: Everything keys off config_id, not user_id
2. **Position-Based**: One trade per exchange position (no phantom trades)
3. **Audit Trail**: Every decision stored in strategy_runs with full context
4. **Universal Exchange Support**: Adapters handle exchange differences
5. **Backward Compatibility**: trades_legacy view for smooth migration

## Recent Changes Made

1. **Split Tests**: Separated pipeline test into new_trade.py and manage_trade.py
2. **Fixed Config Flow**: Added config_id to all API payloads
3. **Fixed TradeLifecycleManager**: Now properly passes config_id
4. **Enhanced Verification**: Added strategy_runs checking
5. **Updated APIs**: Decision API now accepts config_id directly

## Future Work (in FUTURE.md)

- Symbol-specific mode detection (currently global)
- Multi-symbol parallel pipelines
- Portfolio-aware decision making
- Microservices separation

## Debugging Tips

1. **Check Logs**: `tail -f logs/ggbot.log`
2. **Verify Exchange**: BitMEX testnet UI should show real positions
3. **Database State**: Use SQL queries above to verify data
4. **API Health**: All endpoints should return 200 OK
5. **Config Flow**: Trace config_id through all API calls

## Test Philosophy

- **Exchange Reality First**: Database should reflect what's on exchange
- **No Phantom Trades**: If exchange has no position, database shouldn't either
- **Complete Audit Trail**: Every action recorded in strategy_runs
- **Config Isolation**: Each config is independent trading strategy

The system is designed to be simple, reliable, and exchange-driven. The tests verify this architecture works end-to-end.

## Additional Important Context

### Symbol Mapping
- Test uses `BTC/USDT` but BitMEX expects `BTC/USDT:USDT` 
- Symbol mapping handled automatically in trading/exchanges/bitmex/symbol_mappings.py

### Decision Strategy
The current decision strategy (in config) is aggressive:
```
"Always enter trades based on RSI position relative to 50. If RSI is above 50, enter a SHORT position. If RSI is below 50, enter a LONG position."
```
This ensures a trade is always entered for testing purposes.

### MCP Servers
- CCXT MCP Server: Handles exchange operations (must be running)
- Indicators MCP Server: Provides RSI calculations (must be running)
- Started via ecosystem.config.js with `pm2 start core/config/ecosystem.config.js`

### Test Isolation
- Tests are now separate files to avoid mode detection complexity
- In production, symbol-specific mode detection will be implemented
- Current approach is sufficient for single-symbol prototype

### Known Limitations
1. Dashboard API returns all trades (not filtered by config_id)
2. Mode detection is global (not per-symbol) 
3. Single symbol focus (BTC/USDT) for prototype

### Session Notes
- We completed a major refactor from phantom-trade reconciliation to position-based lifecycle
- The PLAN.md phases are all complete
- Tests were split from single pipeline_integration_test.py to new_trade.py and manage_trade.py
- Config flow was the main challenge - ensuring config_id propagates through all services

### Critical Fixes Applied
1. **TradeLifecycleManager**: Fixed missing config_id parameter (line 355 in tests)
2. **Decision API**: Updated to accept config_id directly (not just config_name)
3. **Test Payloads**: Added config_id to all API requests
4. **Manage Actions**: Removed "open_position" from manage_trade valid actions

### Test Dependencies
- The tests import directly from core modules (not just APIs)
- Uses psycopg2 for direct database verification
- Relies on dotenv for environment variable loading
- Uses AccountMonitoringService for exchange sync

### Troubleshooting Checklist
1. ✅ MCP servers running? (`pm2 list`)
2. ✅ API server running? (`python main_api.py`)
3. ✅ Environment variables loaded? (check .env file)
4. ✅ Database clean? (no stale trades/positions)
5. ✅ Exchange credentials valid? (testnet API keys)
6. ✅ Virtual environment activated? (`source .venv/bin/activate`)

### What Success Looks Like
- Exchange shows real position matching database
- strategy_runs table has complete audit trail
- No phantom trades or orphaned records
- Clean logs with clear decision reasoning

This context should provide everything needed to understand and troubleshoot the Universal Trade Lifecycle system tests.





● Issues Analysis & Prioritized Fix Plan

  🔍 ISSUES IDENTIFIED:

  1. Database Schema Mismatch (CRITICAL)

  - Issue: Code references trade_status but database has status
   column
  - Issue: Code references decision_id but trades table doesn't
   have this column
  - Error Location:
    - trading/db.py:288 - Query uses trade_status
    - trading/db.py:73 - Insert tries to use decision_id
  - Root Cause: Database schema migration incomplete or code
  not updated

  2. Position Sizing Logic (WORKING CORRECTLY)

  - Status: ✅ NOT AN ISSUE - Working as designed
  - Analysis:
    - Confidence 0.65 → 3.5% risk → $2,413 collateral → $24,134
   position
    - Emergency cap applied → $10,000 position → $1,000
  collateral @ 10x
    - This is correct behavior protecting against excessive
  risk

  3. Trade Lifecycle Sync Errors (MODERATE)

  - Issue: dictionary update sequence element #0 has length 36;
   2 is required
  - Location: trading/lifecycle_manager.py:79, 102
  - Impact: Position sync failing, preventing proper audit
  trail

  4. Missing Strategy Runs (HIGH)

  - Issue: No entries created in strategy_runs table
  - Impact: Missing decision audit trail despite successful
  trade execution
  - Related: Likely caused by database schema issues

  5. MCP Session Cleanup Warnings (LOW)

  - Issue: Async cleanup errors during MCP disconnection
  - Impact: Non-critical, doesn't affect functionality

  ---
  🎯 PRIORITIZED FIX PLAN:

  PRIORITY 1 (CRITICAL) - Database Schema Fixes

  Fix 1A: Update trades table column references

  -- Current database has 'status', but code expects 
  'trade_status'
  -- Option 1: Add alias in queries
  -- Option 2: Update database to match code expectations

  Fix 1B: Handle decision_id column

  -- strategy_runs table has decision_id, but trades table 
  doesn't
  -- Need to determine if trades should reference decision_id 
  or handle differently

  Files to modify:
  - trading/db.py - Update column mappings
  - Verify all database queries match actual schema

  PRIORITY 2 (HIGH) - Strategy Runs Creation

  Fix 2A: Ensure strategy_runs entries are created

  - Root Cause: Likely the database schema issues preventing
  proper insert
  - Investigation needed: Check if decision engine is calling
  strategy_runs creation
  - Files: decision/engine.py, trading/engine.py

  PRIORITY 3 (MODERATE) - Trade Lifecycle Sync

  Fix 3A: Fix position sync data format issue

  - Issue: Dictionary format mismatch during position mapping
  - Location: trading/lifecycle_manager.py
  - Investigation: Check position data structure vs expected
  format

  PRIORITY 4 (LOW) - MCP Cleanup

  Fix 4A: Improve async session cleanup

  - Files: core/mcp/client.py, core/mcp/session.py
  - Impact: Cosmetic warnings only

  ---
  🔧 IMMEDIATE ACTION PLAN:

  Step 1: Database Schema Audit

  -- Compare actual schema vs code expectations
  -- Identify all column name mismatches
  -- Check if recent migrations were properly applied

  Step 2: Fix Column References

  - Update trading/db.py to use correct column names
  - Test with simple trade creation

  Step 3: Verify Strategy Runs Flow

  - Trace decision → trading pipeline
  - Ensure strategy_runs table gets populated

  Step 4: Test End-to-End

  - Run test again after fixes
  - Verify audit trail completeness

  The core issue is database schema synchronization - once
  fixed, the strategy runs and lifecycle sync should work
  properly.


---

After troubleshooting for a bit, we created a separate test, tests/check_acc.py to isolate exchange-database sync issues, which we successfully resolved:

● Bash(source .venv/bin/activate && python tests/check_acc.py)
  ⎿ ===================================================================
    =============
    🔍 ACCOUNT MONITORING DIAGNOSTIC TEST
    ===================================================================
    =============
    User ID: 00000000-0000-0000-0000-000000000001
    … +136 lines (ctrl+r to expand)

● 🎉 SUCCESS! THE FIX WORKED!

  What Just Happened:

  Looking at the logs, MY FIX WORKED PERFECTLY!

  Key Success Indicators:

  1. ✅ Position Sync Worked:
  Position sync completed: 0 opened, 0 updated, 1 closed
  2. ✅ Trade was Closed:
  Closed trade 0541ae38-e82f-4ce3-a955-b72484cc2ec4 for BTC/USD
  3. ✅ Database Now Correct:
    - Before: trade_status: open
    - After: trade_status: closed with closed_at: 2025-06-07 
  09:15:39.927821
  4. ✅ Open Trades Count Fixed:
    - Before: Open trades in database: 1
    - After: Open trades in database: 0
  5. ✅ Summary Shows Perfect Sync:
    - Exchange positions: 0 active ✅
    - Exchange orders: 0 open ✅
    - Database trades: 3 total, 0 open ✅

  What My Fix Did:

  1. Position Filtering Fix: I removed the filter in
  normalize_position_for_lifecycle() that was skipping 0-contract
  positions
  2. The monitoring service now sees: Both BTC and ETH positions with
  contracts: 0.0
  3. The lifecycle manager processes: The 0-contract BTC position and
  realizes the corresponding database trade should be closed
  4. Result: Perfect synchronization between exchange and database!

  The System Now Works As Intended:

  - ✅ When exchange shows 0 positions → Database shows 0 open trades
  - ✅ Position-based trade lifecycle management working correctly
  - ✅ Manual position closures properly detected and synced

  The core issue is RESOLVED! The monitoring service can now properly
  detect when positions are manually closed and update the database
  accordingly.

  