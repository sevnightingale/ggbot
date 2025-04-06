(.venv) sev@ggbot-vm:~/ggbot$ python -m extraction.test_yfinance
=== Testing YFinanceDataSource ===
Supported symbols: ['BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 'SOL-USD', 'DOGE-USD', 'MATIC-USD', 'DOT-USD', 'AVAX-USD']
Supported timeframes: ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1mo']
Current price of BTC-USD: $79234.67
2025-04-06 19:51:07 | INFO     | User: 00000000-0000-0000-0000-000000000001 | extraction.sources.yfinance.yfinance_datasource:get_historical_data:126 - Fetching BTC-USD 1d data from 2025-03-07 19:51:07.755353 to 2025-04-06 19:51:07.755353
YF.download() has changed argument auto_adjust default to True

Historical data for BTC-USD (1d):
Shape: (31, 5)
Date range: 2025-03-07 00:00:00 to 2025-04-06 00:00:00

Column structure:
Type: <class 'pandas.core.indexes.multi.MultiIndex'>
Multi-index columns:
  ('Close', 'BTC-USD')
  ('High', 'BTC-USD')
  ('Low', 'BTC-USD')
  ('Open', 'BTC-USD')
  ('Volume', 'BTC-USD')

First 5 rows:
Price              Close  ...       Volume
Ticker           BTC-USD  ...      BTC-USD
Date                      ...             
2025-03-07  86742.671875  ...  65945677657
2025-03-08  86154.593750  ...  18206118081
2025-03-09  80601.039062  ...  30899345977
2025-03-10  78532.000000  ...  54061099422
2025-03-11  82862.210938  ...  54702837196

[5 rows x 5 columns]

=== Testing PandasTAIndicators ===

Available indicators:
['SMA_20', 'SMA_50', 'SMA_200', 'EMA_9', 'EMA_21', 'EMA_55', 'RSI_14', 'MACD_12_26', 'MACDh_12_26', 'MACDs_12_26', 'BBL_20_2', 'BBM_20_2', 'BBU_20_2', 'BBB_20_2', 'BBP_20_2']

Indicator parameters:
{
  "sma": {
    "windows": [
      20,
      50,
      200
    ]
  },
  "ema": {
    "windows": [
      9,
      21,
      55
    ]
  },
  "rsi": {
    "length": 14
  },
  "macd": {
    "fast": 12,
    "slow": 26,
    "signal": 9
  },
  "bbands": {
    "length": 20,
    "std": 2
  }
}
2025-04-06 19:51:07 | WARNING  | User: 00000000-0000-0000-0000-000000000001 | extraction.indicators.pandas_ta_indicators:compute_indicators:146 - MACD calculation returned empty result
2025-04-06 19:51:07 | WARNING  | User: 00000000-0000-0000-0000-000000000001 | extraction.indicators.pandas_ta_indicators:compute_indicators:173 - Bollinger Bands calculation returned empty result

Data with indicators:
Shape: (31, 12)

First 5 rows (indicators only):
Price              Close  ... RSI_14
Ticker           BTC-USD  ...       
Date                      ...       
2025-03-07  86742.671875  ...   None
2025-03-08  86154.593750  ...   None
2025-03-09  80601.039062  ...   None
2025-03-10  78532.000000  ...   None
2025-03-11  82862.210938  ...   None

[5 rows x 12 columns]

=== Testing Database Format Conversion ===

Preparing data for database format...
DataFrame shape: (31, 12)
Column structure: <class 'pandas.core.indexes.multi.MultiIndex'>
Multi-index columns before conversion:
  ('Close', 'BTC-USD')
  ('High', 'BTC-USD')
  ('Low', 'BTC-USD')
  ('Open', 'BTC-USD')
  ('Volume', 'BTC-USD')
  ('SMA_20', '')
  ('SMA_50', '')
  ('SMA_200', '')
  ('EMA_9', '')
  ('EMA_21', '')
  ('EMA_55', '')
  ('RSI_14', '')

Converting to database format...

Database entries (31 rows):
First entry:
{
  "user_id": "00000000-0000-0000-0000-000000000001",
  "source": "yfinance",
  "symbol": "BTC-USD",
  "timeframe": "1d",
  "data_type": "price_data",
  "raw_data": {
    "open": 89963.28125,
    "high": 91191.046875,
    "low": 84717.6796875,
    "close": 86742.671875,
    "volume": 65945677657.0
  },
  "indicators": {},
  "updated_at": "2025-03-07 00:00:00"
}
(.venv) sev@ggbot-vm:~/ggbot$ 