# Extraction Module

The Extraction Module automates data gathering from multiple sources including TradingView (for ggShot signals), YFinance, and exchange APIs. It fetches and computes historical indicators using various tools and stores this data for use by the Decision Module.

## Architecture

The Extraction Module uses a hybrid architecture:

1. **DataSource Interface**: A common interface for all standard data sources
2. **Specialized Sources**: Complex sources (like TradingView) have their own extraction scripts
3. **ExtractionManager**: Coordinates all sources and handles database storage
4. **IndicatorComputer Interface**: A common interface for all indicator calculation methods

### Directory Structure

```
extraction/
├── interfaces/           # Abstract interfaces for data sources and indicators
│   ├── data_source.py    # DataSource abstract base class
│   └── indicator_computer.py # IndicatorComputer abstract base class
├── sources/              # Data source implementations
│   ├── yfinance/         # YFinance data source
│   ├── exchange_api/     # Direct exchange API data collection
│   ├── third_party/      # Third-party data provider integrations
│   └── tradingview/      # TradingView-specific extraction code
├── indicators/           # Technical indicator implementations
│   └── pandas_ta_indicators.py # Implementation using pandas-ta
├── utils.py              # Utility functions for database operations
└── extraction_main.py    # Main entry point for the extraction process
```

## Data Sources

### YFinance

The YFinance data source provides price data for crypto and stock pairs from Yahoo Finance. It supports:

- Historical OHLCV data for multiple timeframes
- Multiple cryptocurrencies and trading pairs
- Technical indicators through pandas-ta

### TradingView 

The TradingView data source uses browser automation to extract ggShot signals:

- Uses Browser-Use with Playwright for browser automation
- Extracts visual signals using GPT-4o Vision
- Processes indicator data into a structured report

## Technical Indicators

The module uses pandas-ta to calculate common technical indicators:

- Simple Moving Average (SMA): 20, 50, 200 periods
- Exponential Moving Average (EMA): 9, 21, 55 periods
- Relative Strength Index (RSI): 14 periods
- Moving Average Convergence Divergence (MACD): 12, 26, 9 parameters
- Bollinger Bands: 20 periods, 2 standard deviations

## Usage

### Basic Usage

```python
from extraction.extraction_main import ExtractionManager

# Create an extraction manager
manager = ExtractionManager()

# Extract data for a specific symbol and timeframe
data_entries = manager.extract_market_data(
    symbol="BTC-USD",
    timeframe="1d",
    data_source_name="yfinance",  # or "tradingview"
    days_of_history=60            # Get 60 days of data
)
```

### Command Line Usage

You can also run extraction directly from the command line:

```bash
python -m extraction.extraction_main --symbols BTC-USD ETH-USD --timeframes 1d 4h 1h --sources yfinance
```

### Scheduled Extraction

For production use, the included script `run_scheduled_extraction.sh` is designed to be run via cron:

```bash
# Run scheduled extraction every 15 minutes
*/15 * * * * cd /path/to/ggbot && ./extraction/run_scheduled_extraction.sh >> /home/sev/ggbot/logs/extraction.log 2>&1
```

This script handles initial data loading, updates, and indicator calculation automatically.

## Database Storage

Extracted data is stored in the `market_data` table with the following fields:

- `user_id`: UUID of the user the data belongs to
- `symbol`: Trading pair symbol (e.g., 'BTC-USD')
- `timeframe`: Chart timeframe (e.g., '15m', '1h', '4h')
- `source`: Data source name (e.g., 'yfinance', 'tradingview')
- `data_type`: Type of data (e.g., 'price_data', 'report')
- `raw_data`: JSONB field with raw price data (OHLCV)
- `indicators`: JSONB field with computed indicators
- `updated_at`: Timestamp of the last update

## Adding New Data Sources

To add a new data source:

1. For standard sources:
   - Implement the `DataSource` interface in a new class
   - Register it with the `ExtractionManager`

2. For specialized sources:
   - Create a dedicated extraction script
   - Update the `ExtractionManager.extract_market_data` method to handle the new source

## Current Implementation Status

- [x] Define DataSource and IndicatorComputer interfaces
- [x] Implement YFinanceDataSource
- [x] Implement PandasTAIndicators
- [x] Implement database storage utilities
- [x] Create the ExtractionManager
- [x] Integrate with TradingView extraction script
- [x] Implement scheduling for regular data updates
- [x] Fix database storage to maintain complete historical data
- [x] Ensure proper indicator calculations on historical data
- [ ] Add support for exchange API data sources
- [ ] Implement additional indicator sets

## Scheduled Execution

The extraction process is automated with a shell script and cron job:

1. `run_scheduled_extraction.sh`: A shell script that handles:
   - Initial data loading (runs once with `--init`)
   - Regular updates (runs with `--update` on schedule)
   - Indicator calculation on all historical data

2. Operation Modes:
   - **Initialize Mode** (`--init`): Loads up to 2 years of historical data for daily/hourly timeframes
   - **Update Mode** (`--update`): Fetches only new data since the last update
   - **Indicator Mode** (`--indicators`): Recalculates technical indicators on all stored data

3. Cron Setup:
   - The script runs every 15 minutes via cron
   - Logs are written to `/home/sev/ggbot/logs/extraction.log`
   - The `.initialized` flag prevents re-initialization

## Data Flow

1. **Data Collection**: 
   - System fetches data from yfinance or TradingView
   - Only new data since last update is fetched to minimize API calls

2. **Storage**:
   - Data is stored in PostgreSQL with timestamps as candle times
   - Multiple records per symbol and timeframe are maintained
   - Each record has an `updated_at` timestamp matching the candle time

3. **Indicator Calculation**:
   - All historical data for a symbol/timeframe is loaded into a DataFrame
   - pandas-ta calculates indicators using the complete dataset
   - Results are stored back in the database in the `indicators` field

This approach ensures complete historical context for accurate indicator calculation while minimizing redundant data fetching.