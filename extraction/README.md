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

Extraction behavior is controlled by user configuration stored in the database using **string-based indicators** with explicit timeframe specification:

```json
{
  "extraction": {
    "sources": {
      "crypto_indicators_mcp": {
        "enabled": true,
        "indicators": [
          "Aroon_1d",
          "BollingerBandsWidth_1d", 
          "Vortex_1h",
          "VWAP_1h",
          "RSI_30m",
          "RSI_4h",
          "DonchianChannel_200_1h",
          "BollingerBands_1h",
          "ATR_1h"
        ],
        "llm_interpretation": false,
        "llm_model": "gpt-4o-mini"
      }
    }
  }
}
```

### Configuration Options

#### String-Based Indicator System
- **config_id**: Configuration UUID that determines which indicators to extract
- **Dynamic symbols**: Symbols are determined by the extraction request (e.g., from ggShot signals)
- **No global timeframes**: Each indicator specifies its own timeframe

#### Crypto Indicators MCP Source
- **enabled**: Whether to use this source
- **indicators**: List of string-based indicators with explicit timeframes (e.g., `["RSI_1h", "RSI_4h", "Aroon_1d"]`)
- **llm_interpretation**: Whether to use LLM for analytical interpretation
- **llm_model**: LLM model for interpretation (default: `"gpt-4o-mini"`)

#### String-Based Indicator Format
Indicators now use explicit timeframe specification:
- `RSI_1h` - RSI on 1-hour timeframe
- `RSI_4h` - RSI on 4-hour timeframe
- `Aroon_1d` - Aroon on daily timeframe
- `DonchianChannel_200_1h` - Donchian Channel with 200-period on 1-hour timeframe

#### Available Indicators
The system supports 58 indicators through MCP metadata mapping, organized by category:

**Trend Indicators (25)**: SMA, EMA, MACD, Parabolic SAR, Aroon, etc.
**Momentum Indicators (9)**: RSI, Stochastic, Williams %R, CCI, etc.
**Volatility Indicators (11)**: Bollinger Bands, ATR, Keltner Channels, etc.
**Volume Indicators (9)**: OBV, VWAP, Money Flow Index, etc.

All indicators support string-based specification with timeframes:
- `RSI_1h`, `RSI_4h`, `RSI_1d`
- `BollingerBands_1h`, `BollingerBandsWidth_1d`
- `DonchianChannel_200_1h` (with period embedded)

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

Extracted data is stored in the `market_data` table using the **config_id + symbol** pattern:

### String-Based Indicator Storage
Stored in `indicators` JSONB field with string keys:
```json
{
  "RSI_1h": "meta=None content=[TextContent(type='text', text='[45.98,52.19,...]')]",
  "RSI_4h": "meta=None content=[TextContent(type='text', text='[67.23,58.45,...]')]",
  "Aroon_1d": "meta=None content=[TextContent(type='text', text='{\"up\":[100,85,...], \"down\":[25,40,...]}')]",
  "VWAP_1h": "meta=None content=[TextContent(type='text', text='[0.0247,0.0248,...]')]"
}
```

### Database Lookup Pattern
- **NEW**: `WHERE config_id = %s AND symbol = %s`
- **OLD**: ~~`WHERE symbol = %s AND timeframe = %s`~~ (deprecated)

### Storage Efficiency
- Single row per (config_id, symbol) combination
- All indicators for a symbol stored together
- No cross-product explosion of symbol × timeframe × indicator
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

## Autonomous Webhook Integration ✅

### Webhook Endpoint: `/webhooks/trigger-extraction`

The extraction module provides a webhook endpoint for autonomous trading pipeline integration.

#### **Endpoint Details**
```
POST /extraction/webhooks/trigger-extraction
```

#### **Request Payload**
```json
{
  "user_id": "00000000-0000-0000-0000-000000000001",
  "config_id": "e249bb49-0455-4596-9657-09bf9e14ca14",
  "symbols": ["NKN/USDT"],
  "timeframes": ["1h"]
}
```

**Note**: The `timeframes` field is kept for API compatibility but ignored. Indicators specify their own timeframes via string-based format.

#### **Response Format**
```json
{
  "status": "success",
  "extraction_id": "uuid-string",
  "message": "Extraction started in background"
}
```

#### **Autonomous Chain Behavior**

1. **Pre-Extraction Monitoring**: Refreshes account state from exchange before extraction
2. **Config-Driven Extraction**: Uses config_id to determine which string-based indicators to extract
3. **Efficient Grouping**: Groups indicators by timeframe for batch processing (e.g., all 1h indicators together)
4. **MCP Tool Calls**: Direct calls to crypto-indicators-mcp server for each indicator
5. **String-Based Storage**: Stores with indicator string keys (e.g., "RSI_1h", "Aroon_1d")
6. **Auto-Chaining**: Automatically triggers Decision webhook after successful extraction

#### **Timing Strategy**
The 90-second delay ensures all configured indicators have time to complete:
- Multiple timeframes (15m, 1h, 4h)
- Multiple indicators (RSI, MACD, Bollinger Bands, etc.)
- MCP server processing time and network latency
- Exchange API rate limiting

#### **Integration with Decision Module**
```python
# After extraction completion
if data_points > 0:
    await trigger_decision_webhook(user_id, symbols, timeframes, config_id)
```

The webhook passes the exact symbol used in extraction to ensure data compatibility with the decision module.

## Current Implementation Status

- [x] **Configuration-driven architecture**: ExtractionManager reads user settings
- [x] **MCP metadata integration**: Direct tool calls using pre-generated metadata  
- [x] **Crypto Indicators MCP source**: Full implementation with analytical focus
- [x] **Database integration**: Stores raw data and interpretations
- [x] **Legacy compatibility**: Supports both new and old extraction methods
- [x] **Environment variable loading**: Reads from .env file at project root
- [x] **Analytical LLM interpretation**: Focus on data analysis, not trading advice
- [x] **Command line interface**: Both configuration-driven and legacy modes
- [x] **Autonomous webhook integration**: Full webhook chain support for autonomous trading
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

## Future Optimization: Universal Extraction System

### Current Inefficiency
The current system extracts data per-user configuration, leading to duplicate API calls and storage:
- User A wants BTC/USDT 15m RSI → Extract & store with user_id A
- User B wants BTC/USDT 15m RSI → Extract same data again & store with user_id B
- Market data table grows linearly with user count even for identical data

### Proposed Universal System
Extract data once per symbol+timeframe combination with ALL available indicators, then serve filtered results based on user preferences.

#### Key Files Requiring Changes

1. **extraction/extraction_main.py**
   - `ExtractionManager` class: Currently initializes with user_id, loads user-specific config
   - `extract_mcp_indicators()` function: Accepts user_id parameter, stores with user_id
   - Would need new `UniversalExtractionManager` class without user dependency

2. **extraction/sources/crypto_indicators_mcp.py**
   - `CryptoIndicatorsMCPSource.__init__()`: Takes user_id and user config
   - `extract()` method: Uses user-specific indicator list from config
   - Would need to extract ALL indicators from metadata instead of config subset

3. **extraction/api.py**
   - `run_extraction_task()`: Reads user config, passes user_id throughout
   - `trigger_decision_webhook()`: Passes single symbol from user config
   - Would need smart query endpoint that checks freshness before extraction

4. **extraction/utils.py**
   - `store_market_data_entries()`: Requires user_id for every entry
   - Database queries all include user_id in WHERE clauses
   - Would need universal storage without user_id requirement

5. **core/config/config_main.py**
   - `get_configuration()`: Returns user-specific extraction settings
   - User configs define what to extract (symbols, indicators)
   - Would become filter preferences rather than extraction instructions

#### Architecture Changes

1. **Universal Extraction Manager**
   - Location: New class in `extraction/extraction_main.py`
   - Purpose: Extract ALL indicators for given symbol+timeframe
   - No user_id dependency, uses complete indicator list from MCP metadata
   - Single source of truth for what indicators are available

2. **Smart Query Service**
   - Location: New module `extraction/smart_query.py`
   - Purpose: Check data freshness before triggering extraction
   - Logic: Query market_data by (symbol, timeframe), check updated_at
   - Freshness threshold: Configurable, default 15 minutes
   - Only triggers universal extraction if data is stale

3. **User Filter Service**  
   - Location: New module `extraction/user_filter.py`
   - Purpose: Filter universal data based on user preferences
   - Reads user config to determine which indicators they want
   - Returns subset of universal data matching user preferences

#### Data Flow Transformation

**Current Flow:**
```
User Config → ExtractionManager → Extract User's Indicators → Store with user_id → Decision Module
```

**Universal Flow:**
```
Decision Request → Smart Query → [If Stale] → Universal Extraction (ALL indicators)
                                ↓
                          [If Fresh] → Filter by User Config → Decision Module
```

#### Critical Implementation Details

1. **Indicator List Source**
   - Current: `config.get('indicators', ['RSI'])` from user config
   - Universal: `get_available_indicators()` from `core/mcp/metadata/__init__.py`
   - Must extract ALL available indicators regardless of user preferences

2. **Database Queries**
   - Current: All queries include `WHERE user_id = %s`
   - Universal: Query by `(symbol, timeframe, source)` only
   - Freshness check: `WHERE symbol = %s AND timeframe = %s AND updated_at > NOW() - INTERVAL '15 minutes'`

3. **Backwards Compatibility**
   - Keep existing user_id based system during transition
   - Use feature flag or config switch to enable universal mode
   - Parallel tables: `market_data` (user-specific) and `universal_market_data`

4. **Concurrency Handling**
   - Multiple requests for same stale data shouldn't trigger multiple extractions
   - Need extraction lock/queue per symbol+timeframe combination
   - Consider Redis or database locks for coordination

5. **Configuration Changes**
   - User configs no longer drive extraction, only filtering
   - Need global config for universal extraction behavior (timeouts, retries)
   - Consider per-symbol extraction settings for popular vs rare pairs

#### Migration Considerations

1. **No Data Migration Needed** (prototype phase)
   - Start fresh with universal schema
   - Old user-specific data can be archived or deleted

2. **API Compatibility**
   - Existing endpoints continue working with adapter layer
   - New endpoints for universal extraction management
   - Gradual transition of decision module to use smart queries

3. **Performance Optimization**
   - Index on `(symbol, timeframe, updated_at DESC)` for freshness queries
   - Consider partitioning by timeframe for large datasets
   - Cache recent queries in Redis for sub-second responses

#### Benefits Beyond Efficiency

- **Data Consistency**: All users analyzing same underlying data
- **Reduced Latency**: Fresh data served from cache, no extraction wait
- **Better Resource Usage**: MCP server handles fewer concurrent connections
- **Simplified Debugging**: One extraction log to review instead of per-user logs
- **Cost Predictability**: API costs based on unique pairs, not user count

#### Implementation Priority
This optimization becomes critical when:
- User count exceeds 10-20 active traders
- API rate limits become a bottleneck
- Database storage costs become significant
- Data consistency across users becomes important

For prototype validation, current per-user extraction is sufficient and simpler to reason about.











Analysis: ggShot Indicator Extraction Flow

  Based on my analysis of the codebase, here's the complete flow for the crypto
   indicators MCP system:

  Complete Indicator Inventory

  Total Available: 58 Indicators (not 78 as initially thought)

  The indicators are organized into 4 categories:
  - Trend Indicators: 25 (SMA, EMA, MACD, Parabolic SAR, etc.)
  - Momentum Indicators: 9 (RSI, Stochastic, Williams %R, etc.)
  - Volatility Indicators: 11 (Bollinger Bands, ATR, Keltner Channels, etc.)
  - Volume Indicators: 9 (OBV, VWAP, Money Flow Index, etc.)

  Data Flow Architecture

  1. Configuration → 2. MCP Connection → 3. CCXT Data Fetch → 4. Indicator
  Calculation → 5. LLM Interpretation → 6. Database Storage

  Key Finding: You're correct - it uses direct CCXT calls with LLM only for 
  interpretation, not selection.

  Detailed Flow Breakdown

  1. Indicator Selection (extraction/extraction_main.py:106-120)

  # Indicators determined by config, NOT by LLM
  selected_indicators = mcp_source_config.get('indicators', ['RSI'])  # Default
   to RSI
  - Config ID e249bb49-0455-4596-9657-09bf9e14ca14 controls which indicators to
   use
  - Current config only specifies ['RSI']
  - No LLM involvement in indicator selection

  2. User-Friendly Name Mapping (core/mcp/metadata/__init__.py:114-141)

  # Maps friendly names like "RSI" to "calculate_relative_strength_index"
  mapping = {
      "RSI": "calculate_relative_strength_index",
      "MACD": "calculate_moving_average_convergence_divergence",
      "SMA": "calculate_simple_moving_average",
      # ... 72 total mappings
  }

  3. MCP Tool Execution (extraction/extraction_main.py:142-182)

  # Direct call to MCP server for calculation
  result = await mcp_client.session.call_tool(mcp_tool_name, params)
  - Direct CCXT connection: MCP server uses Node.js + CCXT + indicatorts
  library
  - Real-time data: Fetches OHLCV from Binance (or configured exchange)
  - Parameters: Symbol, timeframe, indicator-specific settings (period=14 for
  RSI)

  4. Raw Data Processing (crypto-indicators-mcp/indicators/*.js)

  // Example: RSI calculation in momentumIndicators.js
  const result = relativeStrengthIndex(asset.closings, { period });
  return { content: [{ type: "text", text: JSON.stringify(result) }] };
  - CCXT → Indicator Library: Raw OHLCV data processed by technical indicators
  library
  - Returns: JSON array of indicator values (not just current value)

  5. LLM Interpretation Only (extraction/extraction_main.py:186-238)

  interpretation_prompt = f"""
  Analyze the raw indicator data for {symbol} on the {timeframe} timeframe:
  {json.dumps(indicator_results, indent=2)}

  Your task is to extract and summarize the key information:
  1. For each indicator, identify the CURRENT VALUE 
  2. Describe the RECENT TREND based on historical data
  3. Note any significant levels or patterns

  Focus only on objective data analysis. Do NOT make trading recommendations.
  """
  - LLM Role: Extract current values, trends, and patterns from raw data
  - No Strategy Decisions: LLM only interprets, doesn't select or recommend
  - Structured Output: JSON format with current_value, trend, key_observations

  6. Database Storage (extraction/extraction_main.py:250-280)

  market_data_entry = {
      "raw_data": {
          "indicators": indicator_results,        # Raw MCP output
          "interpretation": interpretation_data,  # LLM analysis
          "selected_indicators": selected_indicators
      },
      "indicators": indicator_results  # Also in indicators column
  }



rsi
bbands
adx
aroon
atr
bbwidth
cci
