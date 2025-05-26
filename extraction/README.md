# Extraction Module

The Extraction Module provides configuration-driven market data collection and technical analysis using Model Context Protocols (MCPs). It reads user-specific settings from the database and executes appropriate data sources to maximize the quality of market insights for the Decision Module.

## Architecture

The Extraction Module uses a configuration-driven architecture with clear separation of concerns:

1. **ExtractionManager**: Central orchestrator that reads user configuration and manages data sources
2. **Data Source Plugins**: Modular sources that implement specific data collection methods
3. **MCP Integration**: Direct tool calls using metadata for efficient indicator calculation
4. **Analytical LLM**: Interprets raw indicator data to extract maximum analytical value
5. **Database Storage**: Preserves both raw data and analytical insights

### Key Design Principles

- **Configuration-Driven**: All extraction behavior is controlled by user configuration stored in the database
- **Plugin Architecture**: Easy to add new data sources without modifying core logic
- **MCP Metadata**: Uses pre-generated tool metadata for direct, efficient indicator calls
- **Analytical Focus**: LLM interpretation focuses on data analysis, not trading recommendations
- **Data Preservation**: Stores both raw indicator output and analytical interpretation

### Directory Structure

```
extraction/
├── extraction_main.py          # ExtractionManager and legacy functions
├── scheduled_extraction.py     # Configuration-driven and legacy runners
├── interfaces/
│   ├── data_source.py          # DataSource abstract interface (legacy)
│   └── indicator_computer.py   # IndicatorComputer abstract interface (legacy)
├── sources/
│   ├── crypto_indicators_mcp.py # Configuration-driven MCP source
│   ├── ccxt_mcp/              # CCXT MCP data source
│   ├── indicators_mcp/        # Legacy MCP implementation
│   ├── tradingview/           # TradingView extraction (future)
│   └── yfinance/              # YFinance fallback (future)
├── indicators/                # Legacy indicator implementations
├── utils.py                   # Database storage utilities
└── README.md                  # This documentation
```

## Configuration-Driven Extraction

### User Configuration Format

Extraction behavior is controlled by user configuration stored in the database:

```json
{
  "symbols": ["BTC/USDT"],
  "timeframes": ["15m", "1h"],
  "sources": {
    "crypto_indicators_mcp": {
      "enabled": true,
      "indicators": ["RSI", "MACD", "BollingerBands"],
      "use_llm_selection": false,
      "llm_interpretation": true,
      "llm_model": "gpt-4o-mini"
    },
    "tradingview": {
      "enabled": false,
      "strategy": "ggshot_15m"
    },
    "yfinance": {
      "enabled": false
    }
  }
}
```

### Configuration Options

#### Global Settings
- **symbols**: List of trading pairs to analyze (e.g., `["BTC/USDT", "ETH/USDT"]`)
- **timeframes**: List of timeframes to extract (e.g., `["15m", "1h", "4h"]`)

#### Crypto Indicators MCP Source
- **enabled**: Whether to use this source
- **indicators**: List of user-friendly indicator names (e.g., `["RSI", "MACD"]`)
- **use_llm_selection**: If true, LLM selects indicators; if false, uses configured list
- **llm_interpretation**: Whether to use LLM for analytical interpretation
- **llm_model**: LLM model for interpretation (default: `"gpt-4o-mini"`)

#### Available Indicators
The system supports 50+ indicators through MCP metadata mapping:
- **RSI**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence  
- **BollingerBands**: Bollinger Bands
- **ATR**: Average True Range
- **Stochastic**: Stochastic Oscillator
- **Williams%R**: Williams %R
- **OBV**: On Balance Volume
- **And many more...**

## Technical Analysis Focus

### Raw Indicator Data
Each MCP call returns a complete time series (typically 100 data points) for the specified timeframe:
- **15m timeframe**: 100 RSI values covering ~25 hours of 15-minute candles
- **1h timeframe**: 100 RSI values covering ~4+ days of hourly candles

### Analytical Interpretation
The LLM provides data-focused analysis (NOT trading recommendations):

```json
{
  "current_state": "The current RSI value is approximately 64.47, indicating moderately strong bullish momentum",
  "trend_analysis": "The RSI has shown a general upward trend with notable peaks around 67-70",
  "key_levels": ["Resistance at 70 (overbought)", "Support at 30 (oversold)"],
  "pattern_analysis": "Recent consolidation between 50-65 suggests stability after volatile period",
  "data_quality": "High confidence in analysis with 100 data points",
  "analytical_insights": [
    "RSI shows healthy oscillation between extreme levels",
    "Recent correction from overbought levels indicates normal market behavior"
  ],
  "time_series_summary": "Progression from oversold (30) to current moderate levels (64) over recent period",
  "confidence_in_analysis": 0.85
}
```

## Usage

### Configuration-Driven Extraction (Recommended)

```python
from extraction.extraction_main import ExtractionManager
import asyncio

async def run_extraction():
    # Create manager - reads user config from database
    manager = ExtractionManager(user_id="your-user-id")
    
    # Initialize configured data sources
    await manager.initialize_sources()
    
    # Run extraction using user configuration
    results = await manager.extract_all()
    
    return results

# Run extraction
results = asyncio.run(run_extraction())
```

### Command Line Usage

```bash
# Configuration-driven extraction (default)
python -m extraction.scheduled_extraction --user-id=your-user-id

# Legacy mode with explicit parameters
python -m extraction.scheduled_extraction --legacy --symbols=BTC/USDT --timeframes=15m,1h

# Continuous mode (runs every 5 minutes)
python -m extraction.scheduled_extraction --user-id=your-user-id --continuous --interval=300
```

### Setting User Configuration

```python
from core.config.config_main import set_configuration

# Define extraction configuration
extraction_config = {
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "timeframes": ["15m", "1h", "4h"],
    "sources": {
        "crypto_indicators_mcp": {
            "enabled": True,
            "indicators": ["RSI", "MACD", "BollingerBands"],
            "llm_interpretation": True,
            "llm_model": "gpt-4o-mini"
        }
    }
}

# Save to database
set_configuration(user_id, "extraction", extraction_config)
```

## Environment Variables

Required environment variables:
```bash
# LLM API key for analytical interpretation
EXTRACTION_LLM_API_KEY=your_openai_api_key

# Exchange for MCP data fetching
EXCHANGE_NAME=binance
```

## Database Storage

Extracted data is stored in the `market_data` table:

### Raw Indicator Data
Stored in `indicators.results` JSONB field:
```json
{
  "results": {
    "RSI": "[0,0,45.98,52.19,44.64,...]"  // 100-point time series
  },
  "configured_indicators": ["RSI"]
}
```

### Analytical Interpretation
Stored in `raw_data.interpretation` JSONB field:
```json
{
  "interpretation": {
    "current_state": "RSI at 64.47, moderately bullish",
    "trend_analysis": "Upward trend with recent consolidation",
    "analytical_insights": ["Key insight 1", "Key insight 2"],
    "confidence_in_analysis": 0.85
  },
  "llm_model": "gpt-4o-mini",
  "config": {
    "use_llm_selection": false,
    "llm_interpretation": true
  }
}
```

## Adding New Data Sources

To add a new data source:

1. **Create Source Class**:
```python
# extraction/sources/new_source.py
class NewDataSource:
    def __init__(self, user_id: str, config: Dict[str, Any]):
        self.user_id = user_id
        self.config = config
    
    async def extract(self, symbols: List[str], timeframes: List[str]) -> Dict[str, Any]:
        # Implementation here
        pass
```

2. **Register in ExtractionManager**:
```python
# In extraction_main.py _create_source method
elif source_name == 'new_source':
    from extraction.sources.new_source import NewDataSource
    return NewDataSource(self.user_id, source_config)
```

3. **Update User Configuration**:
```json
{
  "sources": {
    "new_source": {
      "enabled": true,
      "custom_setting": "value"
    }
  }
}
```

## MCP Integration

### Direct Tool Calls
The system uses MCP metadata for direct tool calls without LLM selection:

```python
# Map user-friendly name to MCP tool name
mcp_tool_name = get_mcp_tool_name("RSI")  # -> "calculate_relative_strength_index"

# Get tool parameters from metadata
tool_info = get_tool_info(mcp_tool_name)

# Call MCP tool directly
result = await mcp_client.session.call_tool(mcp_tool_name, {
    "symbol": "BTC/USDT",
    "timeframe": "15m",
    "period": 14
})
```

### Tool Metadata
Tool metadata is stored in `core/mcp/metadata/`:
- `indicators_tools.json`: Complete tool definitions
- `indicator_name_mapping.json`: Name mappings
- `__init__.py`: Helper functions for tool lookup

## Current Implementation Status

- [x] **Configuration-driven architecture**: ExtractionManager reads user settings
- [x] **MCP metadata integration**: Direct tool calls using pre-generated metadata  
- [x] **Crypto Indicators MCP source**: Full implementation with analytical focus
- [x] **Database integration**: Stores raw data and interpretations
- [x] **Legacy compatibility**: Supports both new and old extraction methods
- [x] **Environment variable loading**: Reads from .env file at project root
- [x] **Analytical LLM interpretation**: Focus on data analysis, not trading advice
- [x] **Command line interface**: Both configuration-driven and legacy modes
- [ ] **TradingView source**: Implementation pending
- [ ] **YFinance source**: Implementation pending  
- [ ] **Multi-indicator analysis**: Cross-indicator pattern recognition
- [ ] **Real-time streaming**: WebSocket integration for live data

## Data Flow

1. **Configuration Loading**: ExtractionManager reads user settings from database
2. **Source Initialization**: Only enabled sources are initialized with their specific config
3. **MCP Tool Calls**: Direct calls using metadata mapping for efficiency
4. **Raw Data Collection**: Complete time series data (100 points) for each indicator
5. **Analytical Interpretation**: LLM analyzes raw data for patterns and insights
6. **Database Storage**: Both raw data and interpretations preserved for Decision Module
7. **Result Aggregation**: All source results combined for comprehensive market view

This configuration-driven approach provides maximum flexibility while maintaining clear separation between data extraction and trading decisions.