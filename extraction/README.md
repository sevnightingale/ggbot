# Extraction Module

The Extraction Module automates data gathering from multiple sources including TradingView (for ggShot signals), CCXT MCP for market data, and Crypto Indicators MCP for technical analysis. It uses Model Context Protocols (MCPs) with LLM integration to provide sophisticated market analysis and stores this data for use by the Decision Module.

## Architecture

The Extraction Module uses a hybrid architecture:

1. **DataSource Interface**: A common interface for all standard data sources
2. **Specialized Sources**: Complex sources (like TradingView) have their own extraction scripts
3. **ExtractionManager**: Coordinates all sources and handles database storage
4. **MCP Integration**: Uses Model Context Protocols to interact with external services

### Directory Structure

```
extraction/
├── interfaces/           # Abstract interfaces for data sources and indicators
│   ├── data_source.py    # DataSource abstract base class
│   └── indicator_computer.py # IndicatorComputer abstract base class
├── sources/              # Data source implementations
│   ├── ccxt_mcp/         # CCXT MCP data source for exchange data
│   ├── indicators_mcp/   # Indicators MCP data source for technical analysis
│   ├── third_party/      # Third-party data provider integrations
│   └── tradingview/      # TradingView-specific extraction code
├── indicators/           # Technical indicator implementations
│   ├── crypto_indicators_mcp.py # Implementation using Crypto Indicators MCP
│   └── indicators_mcp_llm.py # LLM integration with Indicators MCP
├── utils.py              # Utility functions for database operations
└── extraction_main.py    # Main entry point for the extraction process
```

## Data Sources

### CCXT MCP

The CCXT MCP data source provides cryptocurrency market data through the MCP protocol:

- Historical OHLCV data for multiple timeframes
- Access to multiple exchanges and trading pairs
- Standardized interface for consistent data format

### TradingView

The TradingView data source uses browser automation to extract ggShot signals:

- Uses Browser-Use with Playwright for browser automation
- Extracts visual signals using GPT-4o Vision
- Processes indicator data into a structured report

## Technical Indicators via MCP

The module uses Crypto Indicators MCP with LLM integration to calculate and interpret technical indicators:

- **Indicators Calculation**: Uses MCP tools to calculate various technical indicators
- **LLM Selection**: Uses LLM to select appropriate indicators for market conditions
- **Natural Language Interpretation**: LLM interprets indicator values and provides market analysis
- **Available Indicators**:
  - Relative Strength Index (RSI)
  - Moving Average Convergence Divergence (MACD)
  - Bollinger Bands
  - Simple and Exponential Moving Averages
  - And many more available through the MCP server

## Usage

### Basic Usage

```python
from extraction.extraction_main import ExtractionManager, extract_mcp_indicators
import asyncio

# Option 1: Create an extraction manager with MCP support
manager = ExtractionManager(use_mcp=True, use_llm=True)

# Extract market data using CCXT MCP
data_entries = manager.extract_market_data(
    symbol="BTC/USDT",
    timeframe="1d",
    data_source_name="ccxt_mcp",
    days_of_history=60
)

# Option 2: Use the direct MCP indicators function (recommended)
# This uses the LLM-MCP integration to calculate and interpret indicators
async def run_extraction():
    results = await extract_mcp_indicators(
        symbols=["BTC/USDT", "ETH/USDT"],
        timeframes=["1d", "4h", "1h"],
        use_llm=True,
        llm_model="gpt-4o-mini"
    )
    return results

# Run with asyncio
results = asyncio.run(run_extraction())
```

### Command Line Usage

You can run extraction directly from the command line:

```bash
# Extract indicators using MCP with LLM integration
python -m extraction.scheduled_extraction --indicators --symbols=BTC/USDT --timeframes=1d,4h,1h --llm-model=gpt-4o-mini
```

### Scheduled Extraction

For production use, the included script `run_scheduled_extraction.sh` is designed to be run via cron:

```bash
# Run scheduled extraction every 15 minutes
*/15 * * * * cd /path/to/ggbot && ./extraction/run_scheduled_extraction.sh >> /home/sev/ggbot/logs/extraction.log 2>&1
```

This script handles market data updates and indicator calculation automatically.

## Database Storage

Extracted data is stored in the `market_data` table with the following fields:

- `user_id`: UUID of the user the data belongs to
- `symbol`: Trading pair symbol (e.g., 'BTC/USDT')
- `timeframe`: Chart timeframe (e.g., '15m', '1h', '4h')
- `source`: Data source name (e.g., 'indicators_mcp', 'tradingview')
- `data_type`: Type of data (e.g., 'indicator_values', 'report')
- `raw_data`: JSONB field containing raw data and LLM interpretations
- `indicators`: JSONB field with indicator values or interpretation references
- `updated_at`: Timestamp of the last update

## Adding New MCP Tools

To add support for new MCP indicators:

1. Ensure the tool is available on the MCP server:
   - Check the tools list using `get_available_tools()` method
   - Verify the tool name and parameter format

2. Update the LLM prompt to guide the LLM to use the new tool:
   - Update the tool selection prompt with examples of the new tool
   - Explain the indicators in the instruction context for better selection

3. Ensure proper interpretation:
   - Update interpretation prompts to handle the new indicator type
   - Test with different market conditions to verify interpretation quality

## Current Implementation Status

- [x] Define DataSource and IndicatorComputer interfaces
- [x] Implement CCXT MCP data source for exchange data
- [x] Implement Crypto Indicators MCP for technical analysis
- [x] Implement LLM integration for indicator selection and interpretation
- [x] Implement database storage utilities
- [x] Create the ExtractionManager
- [x] Integrate with TradingView extraction script
- [x] Implement scheduling for regular data updates
- [x] Fix MCP naming conventions (using snake_case)
- [x] Implement proper MCP result handling
- [x] Store LLM interpretations in the database
- [ ] Add support for batch indicator calculations
- [ ] Implement more sophisticated LLM prompting for complex market analysis

## Scheduled Execution

The extraction process is automated with a shell script and cron job:

1. `run_scheduled_extraction.sh`: A shell script that handles:
   - Initial data loading (runs once with `--init`)
   - Regular updates (runs with `--update` on schedule)
   - Indicator calculation (runs with `--indicators`)

2. Operation Modes:
   - **Initialize Mode** (`--init`): Loads historical OHLCV data
   - **Update Mode** (`--update`): Fetches only new data since the last update
   - **Indicator Mode** (`--indicators`): Calculates technical indicators using MCP

3. Cron Setup:
   - The script runs every 15 minutes via cron
   - Logs are written to `/home/sev/ggbot/logs/extraction.log`

## Data Flow

1. **Data Collection**:
   - System fetches data from CCXT MCP or TradingView
   - MCP provides standardized interfaces for consistent data handling

2. **Indicator Calculation**:
   - LLM selects appropriate indicators based on market context
   - MCP tools calculate indicator values for the requested timeframe
   - LLM interprets the results to provide market analysis

3. **Storage**:
   - Both indicator values and LLM interpretations are stored
   - Database maintains historical record for each symbol and timeframe
   - Interpretations provide actionable insights for the Decision Module

This approach leverages the strengths of both MCPs and LLMs to provide sophisticated technical market analysis with natural language interpretations.