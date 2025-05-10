# MCP Integration for ggbots

This directory contains the integration code for Model Context Protocols (MCPs) used by the ggbots platform. MCPs provide standardized interfaces for accessing trading-related services, such as technical indicators and exchange interactions.

## Overview

The ggbots platform integrates with two primary MCPs:

1. **CCXT MCP**: Provides a standardized interface for interacting with cryptocurrency exchanges for market data retrieval and trade execution.
2. **Crypto Indicators MCP**: Offers technical indicators and analysis tools for market data.

## Directory Structure

```
core/mcp/
├── __init__.py          # Package initialization
├── client.py            # Base MCP client functionality
├── session.py           # MCP session management
├── exceptions.py        # Custom exception classes
├── config.py            # Configuration utilities
├── ccxt.py              # CCXT MCP specific client
├── indicators.py        # Crypto Indicators MCP specific client
├── dynamic_account.py   # Dynamic account configuration manager
├── README.md            # This file
└── servers/             # Directory containing MCP server code
    ├── ccxt_mcp_server.py         # CCXT MCP server implementation
    ├── indicators_mcp_server.py   # Indicators MCP server implementation
    └── crypto-indicators-mcp/     # Crypto Indicators MCP dependencies
```

## Current Testing Configuration

For testing and development, we use a simplified credential management approach:

1. **Environment Variables**: Primary source for exchange credentials
   - EXCHANGE_NAME: Name of the exchange (e.g., "bitmex")
   - EXCHANGE_API: API key
   - EXCHANGE_SECRET: API secret
   - EXCHANGE_PASSWORD: Password (required for some exchanges)

2. **Configuration Files**: Used for non-credential settings
   - User Configuration: Located in `core/config/users/{user_id}.json`
   - Default Configuration: Located in `core/config/default_config.json`

This configuration system is suitable for testing and development but will be replaced with a database-backed system for production.

## Setup and Dependencies

To use the MCP integration, you'll need:

1. **Python Dependencies**:
   ```bash
   pip install mcp ccxt
   ```

2. **Node.js and npm**: Required for running MCP servers

3. **Crypto Indicators MCP**: Clone from GitHub and install dependencies:
   ```bash
   git clone https://github.com/kukapay/crypto-indicators-mcp.git ~/ggbot/core/mcp/servers/crypto-indicators-mcp
   cd ~/ggbot/core/mcp/servers/crypto-indicators-mcp
   npm install
   ```

## Trading Pair Conventions

Different exchanges use different naming conventions for trading pairs. We handle this with a mapping system in `ccxt_mcp_server.py`:

```python
EXCHANGE_SYMBOL_MAP = {
    'bitmex': {
        'BTC/USD': 'XBT/USD',
        'BTC/USDT': 'XBT/USDT',
        'ETH/USD': 'ETH/USDT:USDT'
    }
}
```

This allows the LLM to use standardized pair names (e.g., "BTC/USD") while ensuring the correct exchange-specific format is used when making API calls.

## Credential Management

The system uses a simplified credential management approach for development:

### Credential Sources

- **Environment Variables**: Primary source for development/testing
  - EXCHANGE_NAME: Name of the exchange (e.g., "bitmex")
  - EXCHANGE_API: API key
  - EXCHANGE_SECRET: API secret
  - EXCHANGE_PASSWORD: Password (required for some exchanges)

- **Fallback Values**: Hardcoded test credentials as a last resort (BitMEX testnet only)

### Production Credential Management (Future)

For production, we'll implement proper secure credential management:

1. **Database Storage**: Store encrypted credentials in PostgreSQL
2. **Encryption**: Use Fernet symmetric encryption for API keys/secrets
3. **User Isolation**: Maintain separate credentials per user
4. **Key Rotation**: Regular rotation of encryption keys

## Configuration System

The configuration system follows a layered approach:

1. **Environment Variables**: Primary source for credentials (for development)
2. **User JSON Files**: Used for non-credential settings
3. **Default Configuration**: Used when user-specific config is not available

### Setting Up User Configuration

For testing with specific exchanges, configure the user file as follows:

```json
"mcp": {
  "ccxt": {
    "enabled": true,
    "default_exchange": "bitmex"
  },
  "indicators": {
    "enabled": true,
    "script_path": "core/mcp/servers/crypto-indicators-mcp/index.js",
    "exchange_name": "bitmex"
  }
}
```

## Usage Examples

### CCXT MCP with Direct Credentials

```python
from core.mcp.ccxt import CCXTMCPClient

async def example():
    # Initialize client with specific exchange ID
    # This automatically uses credentials from environment variables
    client = CCXTMCPClient(exchange_id="bitmex")
    
    # Connect to server
    await client.connect()
    
    # Fetch ticker data
    ticker = await client.fetch_ticker('bitmex', 'BTC/USDT')
    print(f"BTC/USDT price: {ticker['last']}")
    
    # Disconnect when done
    await client.disconnect()
```

### Using MCP Clients as Context Managers

```python
async def example():
    # Use as a context manager for automatic connection management
    async with CCXTMCPClient() as session:
        # Fetch ticker using the session directly
        ticker = await session.call_tool(
            'fetch_ticker',
            {
                'exchange_id': 'binance',
                'symbol': 'BTC/USDT'
            }
        )
        
        print(f"BTC/USDT price: {ticker['last']}")
    
    # No need to call disconnect() - context manager handles it
```

### CCXT DataSource Integration

```python
from extraction.sources.exchange_api.ccxt_mcp_datasource import CCXTMCPDataSource
from extraction.interfaces.data_source import DataTimeframe

async def example():
    # Use as a context manager
    async with CCXTMCPDataSource(exchange_id="bitmex") as datasource:
        # Fetch ticker
        ticker = await datasource.get_ticker("BTC/USDT")
        
        # Fetch OHLCV data with enum timeframe
        candles = await datasource.get_ohlcv(
            "BTC/USDT", 
            DataTimeframe.HOUR_1, 
            limit=100
        )
```

### Crypto Indicators MCP

```python
from core.mcp.indicators import IndicatorsMCPClient

async def example():
    # Initialize client
    client = IndicatorsMCPClient()
    
    # Connect to server
    await client.connect()
    
    # Calculate RSI
    prices = [100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 108.0]
    rsi = await client.calculate_rsi(prices, period=14)
    print(f"RSI: {rsi['rsi'][-1]}")
    
    # Disconnect when done
    await client.disconnect()
```

## DataSource Integration

Both MCPs are integrated into the Extraction module as DataSource implementations:

- `extraction/sources/exchange_api/ccxt_mcp_datasource.py`
- `extraction/sources/indicators_mcp/indicators_mcp_datasource.py`

These can be used to fetch market data and compute indicators as part of the extraction pipeline.

## Error Handling

All MCP operations include proper error handling with custom exception classes:

- `MCPError`: Base exception for MCP-related errors
- `MCPConnectionError`: When connection to MCP server fails
- `MCPTimeoutError`: When MCP operations time out
- `MCPToolError`: When MCP tool calls fail
- `CredentialNotFoundError`: When required API credentials are not found

## Testing

Several test scripts are provided to verify the functionality of both MCPs:

### Testing MCP Connection Management

To test the base MCP connection functionality:

```bash
cd /home/sev/ggbot
python -m tests.minimal_mcp_test
```

### Testing CCXT MCP

To test the CCXT MCP client:

```bash
# Set environment variables
export EXCHANGE_NAME="bitmex"
export EXCHANGE_API="your_api_key"
export EXCHANGE_SECRET="your_api_secret"

# Run the test
cd /home/sev/ggbot
python -m tests.test_ccxt_mcp_simple
```

### Testing Crypto Indicators MCP

To test the Crypto Indicators MCP:

```bash
cd /home/sev/ggbot
python -m tests.test_indicators_mcp_simple
```

### Testing LLM-MCP Integration

To test the LLM integration with MCP:

```bash
cd /home/sev/ggbot
python -m tests.test_llm_mcp_integration
```

This integration test demonstrates:
- LLM deciding which CCXT MCP tools to call based on user questions
- Making API calls to cryptocurrency exchanges via CCXT MCP
- Handling exchange-specific trading pair formatting
- Processing and interpreting the results

## Implementation Status

The MCP integration has been significantly improved with a streamlined approach. Here's the current status:

### Completed
- [x] Dedicated MCP server files for both Indicators and CCXT
- [x] Consistent snake_case naming conventions for all tools and parameters
- [x] Improved client implementations with proper async context management
- [x] Robust error handling and reconnection strategies
- [x] Enhanced test scripts to verify functionality
- [x] Support for user-specific configurations
- [x] Clean separation of server and client components
- [x] Proper context manager support with async __aenter__ and __aexit__
- [x] Resource cleanup in error scenarios
- [x] Simplified credential management for development
- [x] Trading pair name mapping for exchange-specific formats
- [x] Working LLM-MCP integration for question answering

### Next Implementation Steps
- [ ] Test Crypto Indicators MCP with market data
- [ ] Implement Decision Agent with basic trading strategy
- [ ] Test complete end-to-end flow: Extraction → Decision → Trading
- [ ] Execute test trades on BitMEX testnet

### Technical Debt and Production Improvements
- [ ] **Server Lifecycle Management**: Run MCP servers as persistent processes with PM2
- [ ] **Credential Security**: Implement DbCredentialProvider with proper encryption
- [ ] **Transport Mechanism**: Switch to "Streamable HTTP" transport for production
- [ ] **Error Handling and Resilience**: Implement exponential backoff and circuit breakers
- [ ] **Monitoring and Observability**: Add structured logging and metrics collection
- [ ] **Resource Management**: Implement connection pooling and query throttling
- [ ] **Caching Layer**: Add Redis for frequently accessed data
- [ ] **Multi-User Isolation**: Implement proper multi-tenancy with resource isolation

## Development Guidelines

When working with the MCP integration, follow these guidelines:

1. **Naming Conventions**: Always use `snake_case` for tool names and parameters.

2. **Error Handling**: Use the `call_with_retry` pattern to handle transient connection issues.

3. **Connection Management**: Use async context managers (`async with client as ...`) to ensure proper connection cleanup.

4. **Testing**: Run the test scripts before making changes and after implementation to ensure compatibility.

5. **Server Scripts**: If you modify server scripts, make sure to update the corresponding client methods.

6. **Resource Cleanup**: Always ensure resources are properly cleaned up, especially when errors occur.

## Troubleshooting

If you encounter issues with MCP connectivity:

1. Check that Node.js and npm are installed
2. Verify MCP servers are installed correctly
3. Check that environment variables are set correctly (EXCHANGE_NAME, EXCHANGE_API, EXCHANGE_SECRET)
4. Check configuration paths are correct
5. Look for error logs from MCP servers
6. Check for proper connection handling in the client code

Common connection issues and solutions:

- **"Error exiting session context"**: This is usually a cleanup warning that doesn't affect functionality
- **"Failed to connect to MCP server"**: Check that the server executable exists at the specified path
- **"Session initialization failed"**: The MCP server might be running on a different protocol version
- **"'NoneType' object has no attribute 'get'"**: Check that credentials are properly set in environment variables