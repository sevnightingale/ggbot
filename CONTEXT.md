# GGBot Implementation Context - Phase 2

## Current Status

GGBot is an automated cryptocurrency trading system with three core modules that communicate through a PostgreSQL database. All core APIs have been implemented and are ready for integration testing.

### What's Complete (Phase 1 - done)

1. **Extraction Module** - Collects market data and calculates indicators
   - API implemented at `extraction/api.py`
   - Fetches data via MCP servers (CCXT + Indicators)
   - Stores results in `market_data` table

2. **Decision Module** - Analyzes data and generates trading intents
   - API implemented at `decision/api.py`
   - Dual-mode operation (NEW_TRADE vs MANAGE_TRADE)
   - Stores decisions in `account_states` table (temporary)

3. **Trading Module** - Executes trades on exchange
   - API implemented at `trading/trades_main.py`
   - Full integration with BitMEX testnet via MCP
   - Updates `trades` table with results

4. **Supporting APIs**
   - Dashboard API at `core/api/dashboard_api.py`
   - Agent Control API at `core/api/agent_control_api.py`
   - WebSocket support for real-time updates

5. **Combined API Server**
   - All modules accessible via `main_api.py` on port 8000
   - Simplified deployment for prototype
   - Access at: http://localhost:8000/{module}/...

### What's Needed (Phase 2 - Current Focus)

1. **Connect Modules via APIs**
   - Currently modules read from database independently
   - Need to implement API calls between modules
   - Extraction � Decision � Trading flow

2. **Implement Triggers**
   - Set up cron jobs for scheduled execution
   - Add webhooks for event-driven flow (stretch goal)
   - Ensure proper sequencing of operations

3. **End-to-End Integration Tests**
   - Test complete pipeline: data extraction � decision � trade execution
   - Test both new trade and position management scenarios
   - Verify database state at each step

4. **Basic Monitoring**
   - Ensure monitoring service updates position data
   - Test dashboard API shows real-time updates
   - Verify agent control starts/stops modules

## Key Resources

### Documentation
- **PIPELINE.md** - Complete architecture and data flow
- **API.md** - All API endpoints and how to run them
- **TEST.md** - Testing strategy and working test scripts

### Working Test Examples
These scripts demonstrate the core business logic:
- `tests/test_simplified_extraction.py` - Extraction flow
- `tests/test_decision_module.py` - Decision generation
- `tests/trading/test_trading_flow_simple.py` - Near end-to-end trading

### Environment Setup
Required services:
- PostgreSQL database
- MCP servers running via PM2 (CCXT on 3000, Indicators on 3001)
- Environment variables in `.env` file

## Implementation Approach

### Phase 2 Tasks (Priority Order)

1. **Create Integration Test Script**
   - Use existing test examples as reference
   - Call APIs in sequence (not direct functions)
   - Verify data flow through pipeline

2. **Set Up Cron Jobs**
   - Extraction every 15 minutes
   - Decision every 5 minutes
   - Document in a `cron/README.md`

3. **Test Scenarios**
   - New trade: No positions � Entry signal � Execute trade
   - Manage trade: Existing position � Monitor � Adjust/Close
   - Error cases: Failed extraction, rejected trades, etc.

4. **API Communication**
   - All APIs now available at localhost:8000/{module}/...
   - Simple approach: Cron triggers each module independently
   - Better approach: Add webhook calls between modules
   - Example: POST to localhost:8000/decision/analyze after extraction

### Key Considerations

1. **Module Independence**
   - Each API runs as separate process
   - Communication only through HTTP/Database
   - No shared memory or direct imports

2. **Timing Issues**
   - Extraction might take 2-3 minutes
   - Decision should wait for fresh data
   - Monitor partial failures gracefully

3. **Database State**
   - `market_data` - Check for recent extractions
   - `trades` - Verify position lifecycle
   - `account_monitoring` - Confirm position updates

## Next Steps

1. Start the combined API server: `python main_api.py`
2. Create `tests/test_pipeline_integration.py`
3. Test the full flow using API calls to localhost:8000
4. Add proper error handling and logging
5. Set up cron jobs pointing to the combined API
6. Document the setup in `cron/README.md`

## Success Criteria

- [ ] Full pipeline executes via API calls only
- [ ] Cron jobs trigger modules on schedule  
- [ ] Dashboard shows real-time position updates
- [ ] Agent control can start/stop the bot
- [ ] All tests pass consistently

## Notes

- Keep it simple for prototype - cron jobs are fine
- Focus on happy path first, then error cases
- Use BitMEX testnet for all testing
- Default user ID: `00000000-0000-0000-0000-000000000001`

● Just a few quick things to check:

  1. Make sure the environment is ready:
    - Database is running
    - MCP servers are running via PM2
    - .env file has all the required keys
  2. The combined API approach means the fresh instance
  should start with:
  python main_api.py
  2. Not individual services!
  3. Success looks like:
    - One cron job triggers extraction
    - Another triggers decision
    - Decision automatically calls trading API when there's
   an intent
    - Dashboard shows real-time updates
  4. Keep it simple - focus on the happy path first, then
  error handling
