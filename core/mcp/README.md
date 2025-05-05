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

## Usage Examples

### CCXT MCP

```python
from core.mcp.ccxt import CCXTMCPClient

async def example():
    # Initialize client
    client = CCXTMCPClient()
    
    # Connect to server
    async with client.connect() as session:
        # Fetch ticker data
        ticker = await client.fetch_ticker('binance', 'BTC/USDT')
        print(f"BTC/USDT price: {ticker['last']}")
        
        # Fetch OHLCV data
        ohlcv = await client.fetch_ohlcv('binance', 'BTC/USDT', timeframe='1h', limit=10)
        print(f"Got {len(ohlcv)} candles")
```

### Crypto Indicators MCP

```python
from core.mcp.indicators import IndicatorsMCPClient

async def example():
    # Initialize client
    client = IndicatorsMCPClient()
    
    # Connect to server
    async with client.connect() as session:
        # Calculate RSI
        prices = [100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 108.0]
        rsi = await client.calculate_rsi(prices, period=14)
        print(f"RSI: {rsi['values'][-1]}")
        
        # Calculate MACD
        macd = await client.calculate_macd(prices)
        print(f"MACD line: {macd['macdLine'][-1]}")
```

## DataSource Integration

Both MCPs are integrated into the Extraction module as DataSource implementations:

- `extraction/sources/ccxt_mcp/ccxt_mcp_datasource.py`
- `extraction/sources/indicators_mcp/indicators_mcp_datasource.py`

These can be used to fetch market data and compute indicators as part of the extraction pipeline.

## Error Handling

All MCP operations include proper error handling with custom exception classes:

- `MCPError`: Base exception for MCP-related errors
- `MCPConnectionError`: When connection to MCP server fails
- `MCPTimeoutError`: When MCP operations time out
- `MCPToolError`: When MCP tool calls fail

## Troubleshooting

If you encounter issues with MCP connectivity:

1. Check that Node.js and npm are installed
2. Verify MCP servers are installed correctly
3. Check configuration paths are correct
4. Look for error logs from MCP servers