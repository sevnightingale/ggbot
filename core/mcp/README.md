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
    └── crypto-indicators-mcp/  # Crypto Indicators MCP server
```

## Setup and Dependencies

To use the MCP integration, you'll need:

1. **Node.js and npm**: Required for running MCP servers
2. **Python MCP SDK**: Install with `pip install mcp`
3. **CCXT MCP**: Install globally with `npm install -g @lazydino/ccxt-mcp`
4. **Crypto Indicators MCP**: Clone from GitHub and install dependencies:
   ```
   git clone https://github.com/kukapay/crypto-indicators-mcp.git ~/ggbot/core/mcp/servers/crypto-indicators-mcp
   cd ~/ggbot/core/mcp/servers/crypto-indicators-mcp
   npm install
   ```

## Credential Management

The system uses a flexible credential provider architecture for exchange API credentials:

### Credential Providers

- **EnvCredentialProvider**: Uses environment variables (for development)
  - EXCHANGE_NAME: Name of the exchange (e.g., "bitmex")
  - EXCHANGE_API: API key
  - EXCHANGE_SECRET: API secret

- **DbCredentialProvider**: Will use encrypted database storage (for production - future implementation)

### Dynamic Account Configuration

Rather than hardcoding API credentials in configuration files, we dynamically generate temporary configuration files with the necessary credentials at runtime. This approach:

1. Improves security by not storing API keys in configuration files
2. Allows for per-user credentials in a multi-user environment
3. Simplifies credential rotation and management

## Configuration

MCP configuration is stored in the central configuration system. Example configuration:

```json
{
  "mcp": {
    "ccxt": {
      "enabled": true,
      "config_path": "core/config/ccxt-accounts.json",
      "default_exchange": "binance"
    },
    "indicators": {
      "enabled": true,
      "script_path": "core/mcp/servers/crypto-indicators-mcp/index.js",
      "exchange_name": "binance"
    }
  }
}
```

## Exploring MCP Capabilities

### Discovering Available Indicators

To explore the available tools/indicators in the Crypto Indicators MCP:

```python
import asyncio
from core.mcp.indicators import IndicatorsMCPClient

async def explore_indicators():
    client = IndicatorsMCPClient()
    await client.connect()
    
    # Get all tools from the MCP
    tools = await client.session.get_tools()
    
    # Print the names and descriptions
    for tool in tools:
        print(f"Name: {tool['name']}")
        print(f"Description: {tool.get('description', 'No description')}")
        print(f"Parameters: {tool.get('parameters', {})}")
        print("-" * 50)
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(explore_indicators())
```

### Finding Exchange Capabilities

To explore the CCXT MCP and available exchanges:

```python
import asyncio
from core.mcp.ccxt import CCXTMCPClient

async def explore_exchanges():
    client = CCXTMCPClient()
    await client.connect()
    
    # Get all available exchanges
    exchanges = await client.get_exchange_ids()
    print(f"Total exchanges: {len(exchanges)}")
    print(f"Examples: {', '.join(exchanges[:10])}")
    
    # Get available tools
    tools = await client.session.get_tools()
    print("\nAvailable operations:")
    for tool in tools:
        print(f"- {tool['name']}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(explore_exchanges())
```

## Usage Examples

### CCXT MCP with Dynamic Credentials

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
    
    # Fetch OHLCV data
    ohlcv = await client.fetch_ohlcv('bitmex', 'BTC/USDT', timeframe='1h', limit=10)
    print(f"Got {len(ohlcv)} candles")
    
    # Disconnect when done
    await client.disconnect()
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
    print(f"RSI: {rsi['values'][-1]}")
    
    # Calculate MACD
    macd = await client.calculate_macd(prices)
    print(f"MACD line: {macd['macdLine'][-1]}")
    
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

Two test scripts are provided to verify the functionality of both MCPs:

### Testing CCXT MCP

To test the CCXT MCP with your exchange credentials:

```bash
# Set environment variables 
export EXCHANGE_NAME="bitmex"
export EXCHANGE_API="your_api_key"
export EXCHANGE_SECRET="your_api_secret"

# Run the test
cd /home/sev/ggbot
python -m tests.test_ccxt_mcp
```

This test will verify:
- Connection to the CCXT MCP server
- Dynamic credential management
- Basic operations (fetch ticker, OHLCV data)
- Error handling

### Testing Crypto Indicators MCP

To test the Crypto Indicators MCP:

```bash
cd /home/sev/ggbot
python -m tests.test_indicators_mcp
```

This test will verify:
- Connection to the Crypto Indicators MCP server
- Available indicators
- Core indicator calculations (RSI, MACD, Bollinger Bands)
- Comparison with pandas-ta implementations

## Troubleshooting

If you encounter issues with MCP connectivity:

1. Check that Node.js and npm are installed
2. Verify MCP servers are installed correctly
3. Check that environment variables are set correctly (EXCHANGE_NAME, EXCHANGE_API, EXCHANGE_SECRET)
4. Check configuration paths are correct
5. Look for error logs from MCP servers

## Implementation Status and TODO Items

The MCP integration is partially implemented. Here's the current status and remaining tasks:

### Completed
- [x] Basic MCP client infrastructure with connection management
- [x] CCXT MCP client with core functionality (ticker, OHLCV)
- [x] Crypto Indicators MCP client with basic indicators (RSI, MACD, Bollinger Bands)
- [x] Credential provider architecture with environment-based implementation
- [x] Dynamic account configuration for CCXT MCP
- [x] Basic DataSource implementations for both MCPs
- [x] Test scripts for verifying functionality

### TODO Items for Developers

1. **Expand Indicator Methods**
   - [ ] Analyze the Crypto Indicators MCP server to identify all available indicators
   - [ ] Implement additional indicator methods in `indicators.py` (stochastic, ATR, etc.)
   - [ ] Add comprehensive indicator documentation with parameters and examples

   Example of how to add a new indicator method to `indicators.py`:
   
   ```python
   async def calculate_stochastic(
       self,
       high_prices: List[float],
       low_prices: List[float],
       close_prices: List[float],
       k_period: int = 14,
       d_period: int = 3,
       smooth_k: int = 1
   ) -> Dict[str, Any]:
       """
       Calculate Stochastic Oscillator.
       
       Args:
           high_prices: List of high prices
           low_prices: List of low prices
           close_prices: List of closing prices
           k_period: %K period
           d_period: %D period (moving average of %K)
           smooth_k: Smoothing for %K
           
       Returns:
           Dictionary containing k_values and d_values
       """
       if not self.is_connected or not self.session:
           await self.connect()
           
       try:
           result = await self.session.call_tool(
               'calculateStochastic',
               {
                   'high': high_prices,
                   'low': low_prices,
                   'close': close_prices,
                   'kPeriod': k_period,
                   'dPeriod': d_period,
                   'smoothK': smooth_k
               }
           )
           return result
       except Exception as e:
           self._log.error(f"Error calculating Stochastic: {str(e)}")
           raise MCPError(f"Error calculating Stochastic: {str(e)}")
   ```

2. **Complete DataSource Implementations**
   - [ ] Implement all required DataSource methods in `indicators_mcp_datasource.py`
   - [ ] Add `get_latest_data`, `get_current_price`, `get_supported_timeframes`, and `get_supported_symbols`
   - [ ] Enhance error handling with proper retry mechanisms

3. **Integration Enhancements**
   - [ ] Create an integrated workflow that uses both MCPs together
   - [ ] Implement efficient caching for MCP results to reduce API calls
   - [ ] Build strategy integrations that leverage the indicators MCP

4. **Production Readiness**
   - [ ] Implement database schema for securely storing user credentials
   - [ ] Complete the DbCredentialProvider implementation with proper encryption
   - [ ] Add stress testing and performance optimization for MCP servers
   - [ ] Create monitoring tools for MCP server health and usage

5. **Documentation and Examples**
   - [ ] Create a comprehensive API reference for both MCPs
   - [ ] Document all available indicators with their parameters
   - [ ] Provide end-to-end example workflows for different use cases

## Future Enhancements

1. Implement database credential storage with proper encryption
2. Add support for multiple user accounts
3. Improve error recovery and retry mechanisms
4. Add support for additional exchanges and features
5. Create a containerized deployment model for MCP servers
6. Implement a caching layer to reduce redundant MCP calls
7. Add performance metrics and monitoring for MCP servers