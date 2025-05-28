# GGBot Testing Documentation

## Current Test Coverage Analysis

### Working Tests by Module

#### Extraction Module
1. **tests/test_simplified_extraction.py**
   - Tests configuration-driven extraction with MCP indicators
   - Uses real OpenAI API and MCP services
   - Validates database storage of both raw data and LLM interpretations
   - Coverage: Good for isolated extraction functionality

#### Decision Module  
1. **tests/test_decision_module.py**
   - Tests decision-making using real market data from database
   - Integrates with multiple LLM providers (OpenAI, DeepSeek)
   - Tests multi-timeframe analysis (15m, 1h)
   - Coverage: Good for isolated decision logic

#### Trading Module
1. **tests/trading/test_llm_service.py**
   - Tests LLM → tool call generation
   - Uses mock tool schemas (not real MCP)
   - Extensive parameter normalization testing
   
2. **tests/trading/test_llm_validation_service.py**
   - Tests validation of LLM-generated tool calls
   - Uses real MCP server tools
   - Full flow: intent → LLM → validation
   
3. **tests/trading/test_trading_flow_simple.py** ⭐
   - **Most comprehensive test** - near end-to-end
   - Real BitMEX testnet integration
   - Account monitoring integration
   - Tests: intent → execution → monitoring → database
   
4. **tests/trading/test_trading_api.py**
   - Basic API endpoint validation
   - Uses FastAPI TestClient
   - Limited to endpoint existence, not functionality

#### Core/Infrastructure
1. **tests/test_ccxt_direct_monitoring.py**
   - Direct CCXT connection testing
   - BitMEX testnet account data exploration
   
2. **tests/test_account_monitoring_service.py**
   - Account monitoring with database persistence
   - Periodic polling and state updates

#### MCP Tests
1. **tests/test_mcp_integration.py**
   - CCXT + Indicators MCP integration
   - Session management patterns
   
2. **tests/test_mcp_metadata.py**
   - Metadata module for indicator mapping
   - Tool discovery validation

## Critical Gaps Identified

### 1. Missing API Endpoints
- **Extraction Module**: No REST API defined
- **Decision Module**: No REST API defined
- **Trading Module**: Has basic API but not fully tested with real functionality

### 2. No Full Pipeline Integration
- No test covers: Extraction → Decision → Trading
- No scheduling/orchestration tests
- No error propagation across modules

### 3. Incomplete Trading API Tests
- Endpoints exist but need real execution testing
- No tests for trade lifecycle management via API

## Recommended Approach for End-to-End Testing

### Phase 1: Create Missing APIs (Prerequisites)

Before we can test the full pipeline, we need:

1. **Extraction API** (`extraction/api.py`)
   ```python
   POST /extraction/run         # Trigger extraction for user
   GET  /extraction/status      # Check extraction status
   GET  /extraction/data        # Retrieve latest data
   ```

2. **Decision API** (`decision/api.py`)
   ```python
   POST /decision/analyze       # Trigger decision analysis
   GET  /decision/latest        # Get latest decision
   GET  /decision/history       # Get decision history
   ```

3. **Complete Trading API** (`trading/api.py`)
   ```python
   POST /trading/execute        # Execute trading decision
   GET  /trading/positions      # Get current positions
   GET  /trading/status         # Get trade status
   POST /trading/close          # Close position
   ```

### Phase 2: End-to-End Test Scenarios

#### Test 1: New Trade Full Pipeline
```
1. Trigger extraction via API
2. Wait for extraction completion
3. Trigger decision analysis
4. Receive trading intent
5. Execute trade via trading API
6. Monitor position establishment
7. Verify database state at each step
```

#### Test 2: Existing Trade Management
```
1. Start with existing position in DB
2. Trigger extraction for update
3. Decision module analyzes position
4. Generate management intent (adjust/close)
5. Execute management action
6. Verify position updates
```

### Phase 3: Pipeline Orchestration Options

We need to decide on orchestration approach:

1. **Option A: Coordinator Service**
   - New service that calls APIs in sequence
   - Handles retries and error propagation
   - Single entry point for full pipeline

2. **Option B: Event-Driven**
   - Each module publishes completion events
   - Next module triggered by events
   - More complex but more scalable

3. **Option C: Simple Cron + APIs**
   - Cron triggers extraction API
   - Extraction completion triggers decision
   - Decision completion triggers trading
   - Simplest to implement

## Technical Considerations from Existing Tests

### Key Patterns to Adopt
1. **Session-wide MCP clients** - Avoid connection issues
2. **PM2 for MCP servers** - Already in ecosystem.config.js
3. **Real service integration** - No mocks for e2e tests
4. **Database state verification** - Check state after each step
5. **Proper cleanup** - Close positions, clean test data

### BitMEX Specific Requirements
- 100 contract minimum orders
- Symbol mapping (BTC/USD → BTC/USD:BTC)
- Testnet for all testing
- Account monitoring for position tracking

### Environment Setup
Required environment variables:
```
TRADING_LLM_API_KEY=xxx
EXTRACTION_LLM_API_KEY=xxx
DEEPSEEK_API_KEY=xxx (optional)
CCXT_EXCHANGE=bitmex
CCXT_TESTNET=true
DATABASE_URL=postgresql://...
```

## Recommended Next Steps

1. **Immediate Priority**: Create API endpoints for extraction and decision modules
2. **Then**: Extend trading API tests to cover full functionality
3. **Finally**: Implement end-to-end pipeline tests

The existing `test_trading_flow_simple.py` is already very close to an end-to-end test. We could potentially:
- Extend it to include extraction and decision steps
- Or create a new `test_full_pipeline.py` that orchestrates all three modules

## Questions to Resolve

1. Should we create a coordinator service or use event-driven architecture?
2. Do we want synchronous or asynchronous pipeline execution?
3. How should we handle partial failures in the pipeline?
4. Should the pipeline be user-triggered or fully automated?

