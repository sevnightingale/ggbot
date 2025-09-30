# Testing Strategy with Real Components

## 1. LLMService Test

Test file: tests/trading/test_llm_service.py

Purpose: Test the LLM service with real LLM API calls.

What will be tested:
- Real calls to OpenAI/Anthropic API
- Processing of mock intents into actual API requests
- Parsing of real API responses into tool calls
- Error handling with actual API timeouts/errors
- Retry mechanisms with real-world conditions

Mocked components:
- Only the intent from Decision Module

Status: ✅ Implemented and working

## 2. LLMValidationService Test

Test file: tests/trading/test_llm_validation_service.py

Purpose: Test validation against real exchange constraints.

What will be tested:
- Real LLM MCP interaction
- Actual tool schema validation
- Real symbol mapping for BitMEX testnet
- Actual precision handling for order sizes/prices
- Real-world risk checks against exchange limits
- Integration with the real TradeCompiler

Mocked components:
- Database interactions for validation context

Status: ✅ Implemented and working

## 3. ExecutionService - Simple Order Test

Test file: tests/trading/test_execution_service_simple.py

Purpose: Test basic order execution functionality on BitMEX testnet.

What will be tested:
- Real connection to BitMEX testnet via MCP
- Actual order execution with minimum contract size (100)
- Proper symbol mapping for BitMEX (BTC/USD → BTC/USD:BTC)
- Setting leverage via order parameters
- Verifying order execution through MCP response

Mocked components:
- Trade registration and position monitoring

Implementation details:
- Uses direct approach with minimal setup
- Focuses only on the order execution component
- Verifies actual order creation on BitMEX
- Includes proper cleanup of positions

Status: ✅ Implemented and working

## 4. Trade Status Monitoring Test

Test file: tests/trading/test_position_monitoring.py (to be created)

Purpose: Test retrieving trade/position status from BitMEX testnet.

What will be tested:
- Real-time position status querying
- Using LLM to determine optimal tools for position monitoring
- Handling exchange-specific position status formats
- Monitoring position changes over time
- Event emission for position updates

Implementation approach:
- Leverage the same LLM approach as in the LLMValidationService test
- Provide the LLM with available MCP tools (instead of guessing them)
- Let LLM determine which tools are best for retrieving position data
- Use prompts focused on retrieving position information rather than trade execution
- Integrate with ExecutionService's position monitoring capabilities

Key components:
- Use the same MCP client/adapter setup that works in the simple execution test
- Create a prompt template for querying position status
- Include context about the specific exchange and symbol
- Process LLM output into actual MCP tool calls
- Parse and validate position information from MCP responses

Mocked components:
- Database updates for position tracking
- Trade record registration

Status: 🔄 Planned

## 5. End-to-End Trading Flow Test

Test file: tests/trading/test_trading_flow.py

Purpose: Test the complete trading flow with BitMEX testnet.

What will be tested:
- Full flow from mock decision to actual position
- Real LLM interaction for tool generation
- Actual validation against exchange constraints
- Real execution on BitMEX testnet
- Complete error handling across the entire flow
- Position verification and monitoring

Mocked components:
- Only the trade intent from Decision Module
- Database interactions for trade records

Implementation Considerations:
1. Test Account Setup:
   - Use a dedicated BitMEX testnet account for testing
   - Keep very small position sizes (100 contracts minimum)
   - Include cleanup steps to close positions after tests
2. API Credentials:
   - Store test API keys in environment variables
   - Use testnet flags to ensure we're not touching real funds
3. Test Structure:
   - Use pytest for all tests
   - Create shared fixtures for BitMEX testnet connection
   - Implement careful teardown procedures
4. Safety Measures:
   - Add maximum position size limits in tests
   - Include position verification before any test
   - Implement automatic position closure in teardown

Status: 🔄 Planned after individual component tests are complete

## Test Infrastructure and Setup

### PM2 for MCP Server Management

We're using PM2 to manage the CCXT MCP server as a persistent process:

```javascript
module.exports = {
  apps : [{
    name   : "ccxt-mcp-server",
    script : "/home/sev/ggbot/core/mcp/servers/ccxt_mcp_server.py",
    interpreter: "python",
    env: {
      "EXCHANGE_NAME": "bitmex",
      "TESTNET": "1",
    },
    watch: false,
    max_memory_restart: "200M",
    log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    args: "--config /home/sev/ggbot/core/config/ccxt-accounts.json"
  }]
}
```

PM2 commands:
- Start: `pm2 start ecosystem.config.js`
- Check status: `pm2 status`
- Restart after code changes: `pm2 restart ccxt-mcp-server --update-env`
- View logs: `pm2 logs ccxt-mcp-server`

### Key Testing Fixes

1. Session-wide MCP Client:
   - Using a single MCP client shared across tests instead of creating new connections
   - Includes proper teardown and finalizers to clean up resources

2. Proper Symbol Mapping:
   - Updating from older mappings (XBTUSD) to current BitMEX format (BTC/USD:BTC)
   - Storing complete mappings in trading/exchanges/bitmex_symbol_mappings.py

3. BitMEX Contract Size:
   - Updating tests to use minimum contract size of 100 (BitMEX requirement)
   - Including leverage parameters directly in order creation

4. Environment Variables:
   ```bash
   export EXCHANGE_API="your_bitmex_testnet_api_key"
   export EXCHANGE_SECRET="your_bitmex_testnet_secret"
   export TRADING_LLM_API_KEY="your_openai_api_key"  # or ANTHROPIC_API_KEY for Claude
   ```

5. Test Execution Process:
   ```bash
   # First activate the virtual environment
   cd /home/sev/ggbot && source .venv/bin/activate
   
   # Run tests from simplest to most complex
   python -m tests.trading.test_llm_service
   python -m tests.trading.test_llm_validation_service
   python -m tests.trading.test_execution_service_simple
   python -m tests.trading.test_position_monitoring  # TBD
   python -m tests.trading.test_trading_flow  # TBD
   ```

## Trade Status Monitoring Test - Detailed Design

The proposed Trade Status Monitoring Test will combine our successful approaches from the LLMValidationService test and the ExecutionService Simple test to create a specialized test for position monitoring:

1. Test Structure:
   - Similar to LLMValidationService test structure
   - Uses the same MCP client setup from ExecutionService Simple test
   - Includes fixtures for creating test positions to monitor

2. LLM Prompt Strategy:
   - Create a specialized prompt for querying position status
   - Include context about the exchange, the symbol, and what information we need
   - Let the LLM dynamically decide which MCP tools to use

3. Test Flow:
   - Create a real position on BitMEX testnet (similar to simple execution test)
   - Pass the available tools list to the LLM with a monitoring prompt
   - Let the LLM generate tool calls for retrieving position data
   - Execute those tool calls through the MCP client
   - Parse and validate the position information
   - Close the test position

4. Key Verifications:
   - Confirm that the LLM can correctly identify which tools to use
   - Verify that the tools return actual position data
   - Check that the data format can be parsed by our position monitoring code
   - Ensure we can extract key metrics like position size, entry price, etc.

5. Implementation Notes:
   - Will use the same successful connection pattern from the Simple Execution test
   - Will reuse relevant parts from the LLMValidationService test
   - Will focus on the ExecutionService position monitoring methods
   - Will implement specific position cleanup to ensure tests don't leave open positions