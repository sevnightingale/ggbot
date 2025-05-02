
For additional context, here are the READMEs copy pasted from the github repos for the two mentioned MCP servers: 

----

Crypto Indicators MCP Server README.md (https://github.com/kukapay/crypto-indicators-mcp):

Crypto Indicators MCP Server
An MCP server providing a range of cryptocurrency technical analysis indicators and strategies, empowering AI trading agents to efficiently analyze market trends and develop robust quantitative strategies.

License Node.js Status

Features
Technical Indicators: 50+ indicators across trend, momentum, volatility, and volume categories.
Trading Strategies: Corresponding strategies outputting signals: -1 (SELL), 0 (HOLD), 1 (BUY).
Flexible Data Source: Defaults to Binance, configurable to any ccxt-supported exchange.
Modular Design: Indicators and strategies are categorized for easy maintenance.
Installation
Prerequisites
Node.js (v18.x or higher)
npm (v8.x or higher)
Steps
Clone the Repository:

git clone https://github.com/kukapay/crypto-indicators-mcp.git
cd crypto-indicators-mcp
Install Dependencies:

npm install
Configure MCP Client: To use this server with an MCP client like Claude Desktop, add the following to your config file (or equivalent):

 {
   "mcpServers": {
     "crypto-indicators-mcp": {
       "command": "node",
       "args": ["path/to/crypto-indicators-mcp/index.js"],
       "env": {
         "EXCHANGE_NAME": "binance"
       }
     }
   }
 }   
Available Tools
Trend Indicators
calculate_absolute_price_oscillator: Measures the difference between two EMAs to identify trend strength (APO).
calculate_aroon: Identifies trend changes and strength using high/low price extremes (Aroon).
calculate_balance_of_power: Gauges buying vs. selling pressure based on price movement (BOP).
calculate_chande_forecast_oscillator: Predicts future price movements relative to past trends (CFO).
calculate_commodity_channel_index: Detects overbought/oversold conditions and trend reversals (CCI).
calculate_double_exponential_moving_average: Smooths price data with reduced lag for trend detection (DEMA).
calculate_exponential_moving_average: Weights recent prices more heavily for trend analysis (EMA).
calculate_mass_index: Identifies potential reversals by measuring range expansion (MI).
calculate_moving_average_convergence_divergence: Tracks momentum and trend direction via EMA differences (MACD).
calculate_moving_max: Computes the maximum price over a rolling period (MMAX).
calculate_moving_min: Computes the minimum price over a rolling period (MMIN).
calculate_moving_sum: Calculates the sum of prices over a rolling period (MSUM).
calculate_parabolic_sar: Provides stop-and-reverse points for trend following (PSAR).
calculate_qstick: Measures buying/selling pressure based on open-close differences (Qstick).
calculate_kdj: Combines stochastic and momentum signals for trend analysis (KDJ).
calculate_rolling_moving_average: Applies a rolling EMA for smoother trend tracking (RMA).
calculate_simple_moving_average: Averages prices over a period to identify trends (SMA).
calculate_since_change: Tracks the time since the last significant price change.
calculate_triple_exponential_moving_average: Reduces lag further than DEMA for trend clarity (TEMA).
calculate_triangular_moving_average: Weights middle prices more for smoother trends (TRIMA).
calculate_triple_exponential_average: Measures momentum with triple smoothing (TRIX).
calculate_typical_price: Averages high, low, and close prices for a balanced trend view.
calculate_volume_weighted_moving_average: Incorporates volume into moving averages for trend strength (VWMA).
calculate_vortex: Identifies trend direction and strength using true range (Vortex).
Momentum Indicators
calculate_awesome_oscillator: Measures market momentum using midline crossovers (AO).
calculate_chaikin_oscillator: Tracks accumulation/distribution momentum (CMO).
calculate_ichimoku_cloud: Provides a comprehensive view of support, resistance, and momentum (Ichimoku).
calculate_percentage_price_oscillator: Normalizes MACD as a percentage for momentum (PPO).
calculate_percentage_volume_oscillator: Measures volume momentum via EMA differences (PVO).
calculate_price_rate_of_change: Tracks price momentum as a percentage change (ROC).
calculate_relative_strength_index: Identifies overbought/oversold conditions via momentum (RSI).
calculate_stochastic_oscillator: Compares closing prices to ranges for momentum signals (STOCH).
calculate_williams_r: Measures momentum relative to recent high-low ranges (Williams %R).
Volatility Indicators
calculate_acceleration_bands: Frames price action with dynamic volatility bands (AB).
calculate_average_true_range: Measures market volatility based on price ranges (ATR).
calculate_bollinger_bands: Encloses price action with volatility-based bands (BB).
calculate_bollinger_bands_width: Quantifies volatility via band width changes (BBW).
calculate_chandelier_exit: Sets trailing stop-losses based on volatility (CE).
calculate_donchian_channel: Tracks volatility with high/low price channels (DC).
calculate_keltner_channel: Combines ATR and EMA for volatility bands (KC).
calculate_moving_standard_deviation: Measures price deviation for volatility (MSTD).
calculate_projection_oscillator: Assesses volatility relative to projected prices (PO).
calculate_true_range: Calculates daily price range for volatility analysis (TR).
calculate_ulcer_index: Quantifies downside volatility and drawdowns (UI).
Volume Indicators
calculate_accumulation_distribution: Tracks volume flow to confirm price trends (AD).
calculate_chaikin_money_flow: Measures buying/selling pressure with volume (CMF).
calculate_ease_of_movement: Assesses how easily prices move with volume (EMV).
calculate_force_index: Combines price and volume for momentum strength (FI).
calculate_money_flow_index: Identifies overbought/oversold via price-volume (MFI).
calculate_negative_volume_index: Tracks price changes on lower volume days (NVI).
calculate_on_balance_volume: Accumulates volume to predict price movements (OBV).
calculate_volume_price_trend: Combines volume and price for trend confirmation (VPT).
calculate_volume_weighted_average_price: Averages prices weighted by volume (VWAP).
Trend Strategies
calculate_absolute_price_oscillator_strategy: Generates buy/sell signals from APO crossovers (APO Strategy).
calculate_aroon_strategy: Signals trend reversals using Aroon crossovers (Aroon Strategy).
calculate_balance_of_power_strategy: Issues signals based on BOP thresholds (BOP Strategy).
calculate_chande_forecast_oscillator_strategy: Predicts reversals with CFO signals (CFO Strategy).
calculate_kdj_strategy: Combines KDJ lines for trend-based signals (KDJ Strategy).
calculate_macd_strategy: Uses MACD crossovers for trading signals (MACD Strategy).
calculate_parabolic_sar_strategy: Signals trend direction with PSAR shifts (PSAR Strategy).
calculate_typical_price_strategy: Generates signals from typical price trends.
calculate_volume_weighted_moving_average_strategy: Issues signals based on VWMA crossovers (VWMA Strategy).
calculate_vortex_strategy: Signals trend direction with Vortex crossovers (Vortex Strategy).
Momentum Strategies
calculate_momentum_strategy: Issues signals based on momentum direction.
calculate_awesome_oscillator_strategy: Signals momentum shifts with AO crossovers (AO Strategy).
calculate_ichimoku_cloud_strategy: Generates signals from Ichimoku cloud positions (Ichimoku Strategy).
calculate_rsi2_strategy: Signals overbought/oversold with RSI thresholds (RSI Strategy).
calculate_stochastic_oscillator_strategy: Uses stochastic crossovers for signals (STOCH Strategy).
calculate_williams_r_strategy: Signals momentum reversals with Williams %R (Williams %R Strategy).
Volatility Strategies
calculate_acceleration_bands_strategy: Signals breakouts with acceleration bands (AB Strategy).
calculate_bollinger_bands_strategy: Issues signals from Bollinger Band breaches (BB Strategy).
calculate_projection_oscillator_strategy: Signals volatility shifts with PO (PO Strategy).
Volume Strategies
calculate_chaikin_money_flow_strategy: Signals volume pressure with CMF (CMF Strategy).
calculate_ease_of_movement_strategy: Issues signals based on EMV trends (EMV Strategy).
calculate_force_index_strategy: Signals momentum with force index shifts (FI Strategy).
calculate_money_flow_index_strategy: Signals overbought/oversold with MFI (MFI Strategy).
calculate_negative_volume_index_strategy: Signals trends with NVI changes (NVI Strategy).
calculate_volume_weighted_average_price_strategy: Issues signals from VWAP crossovers (VWAP Strategy).
Usage Examples
Example 1: Calculate MACD Indicator
Input (Natural Language Prompt):

Calculate the MACD for BTC/USDT on a 1-hour timeframe with fast period 12, slow period 26, signal period 9, and fetch 100 data points.
Output:

{"macd": [...], "signal": [...], "histogram": [...]}
Example 2: Calculate RSI Strategy
Input (Natural Language Prompt):

Give me the RSI strategy signals for ETH/USDT on a 4-hour timeframe with a period of 14 and 50 data points.
Output:

[-1, 0, 1, 0, ...]
License
This project is licensed under the MIT License - see the LICENSE file for details.

About
An MCP server providing a range of cryptocurrency technical analysis indicators and strategies.

Resources
 Readme
License
 MIT license
 Activity
Stars
 18 stars
Watchers
 1 watching
Forks
 11 forks
Report repository
Releases
No releases published
Packages
No packages published
Languages
JavaScript
100.0%
Footer
© 2025 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Docs
Contact
Manage


----


CCTX README.md (https://github.com/lazy-dinosaur/ccxt-mcp):

CCXT MCP Server
npm version npm downloads GitHub stars License: MIT

한국어 버전(Korean version)

CCXT MCP Server is a server that allows AI models to interact with cryptocurrency exchange APIs through the Model Context Protocol (MCP). This server uses the CCXT library to provide access to more than 100 cryptocurrency exchanges and their trading capabilities.

🚀 Quick Start
# Install the package globally
npm install -g @lazydino/ccxt-mcp

# Run with default settings
ccxt-mcp

# or run without installation
npx @lazydino/ccxt-mcp
Installation and Usage
Global Installation
# Install the package globally
npm install -g @lazydino/ccxt-mcp
Running with npx
You can run it directly without installation:

# Using default settings
npx @lazydino/ccxt-mcp

# Using custom configuration file
npx @lazydino/ccxt-mcp --config /path/to/config.json
View help:

npx @lazydino/ccxt-mcp --help
Configuration
Registering the MCP Server in Claude Desktop
Open Claude Desktop Settings:

Go to the Settings menu in the Claude Desktop app
Find the "MCP Servers" section
Add a New MCP Server:

Click the "Add Server" button
Server name: ccxt-mcp
Command: npx @lazydino/ccxt-mcp
Additional arguments (optional): --config /path/to/config.json
Save and Test the Server:

Save the settings
Test the connection with the "Test Connection" button
Configuration Methods - Two Options
Option 1: Include Account Information Directly in Claude Desktop Settings (Basic Method)
This method includes CCXT account information directly in the Claude Desktop settings file (claude_desktop_config.json):

{
  "mcpServers": {
    "ccxt-mcp": {
      "command": "npx",
      "args": ["-y", "@lazydino/ccxt-mcp"],
      "accounts": [
        {
          "name": "bybit_main",
          "exchangeId": "bybit",
          "apiKey": "YOUR_API_KEY",
          "secret": "YOUR_SECRET_KEY",
          "defaultType": "spot"
        },
        {
          "name": "bybit_futures",
          "exchangeId": "bybit",
          "apiKey": "YOUR_API_KEY",
          "secret": "YOUR_SECRET_KEY",
          "defaultType": "swap"
        }
      ]
    }
  }
}
Using this method, you don't need a separate configuration file. All settings are integrated into the Claude Desktop configuration file.

Option 2: Using a Separate Configuration File (Advanced Method)
To separate account information into a separate configuration file, set up as follows:

Create a Separate Configuration File (e.g., ccxt-accounts.json):
{
  "accounts": [
    {
      "name": "bybit_main",
      "exchangeId": "bybit",
      "apiKey": "YOUR_API_KEY",
      "secret": "YOUR_SECRET_KEY",
      "defaultType": "spot"
    },
    {
      "name": "bybit_futures",
      "exchangeId": "bybit",
      "apiKey": "YOUR_API_KEY",
      "secret": "YOUR_SECRET_KEY",
      "defaultType": "swap"
    }
  ]
}
Important: The configuration file must contain an accounts array at the root level, as shown above.

Specify the Configuration File Path in Claude Desktop Settings:
{
  "mcpServers": {
    "ccxt-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@lazydino/ccxt-mcp",
        "--config",
        "/path/to/ccxt-accounts.json"
      ]
    }
  }
}
Note: When using a separate configuration file with the --config option, the server will look for the accounts array directly in the root of the JSON file, not in mcpServers.ccxt-mcp.accounts path.

Running with External Configuration File from Command Line:
# Using custom configuration file
npx @lazydino/ccxt-mcp --config /path/to/ccxt-accounts.json
You can find an example configuration file at examples/config-example.json in the repository.

Reasons to Use a Separate Configuration File:

Prevents recursive reference issues
Separates sensitive information like API keys
Easier multi-environment configuration (development, testing, production)
Improved configuration file version control
Key Features
Market Information Retrieval:

List exchanges
View market information by exchange
Get price information for specific symbols
View order book information for specific symbols
Search historical OHLCV data
Trading Functions:

Create market/limit orders
Cancel orders and check status
View account balances
Check trading history
Trading Analysis:

Daily/weekly/monthly performance analysis
Win rate calculation (last 7 days, 30 days, all time)
Average profit/loss ratio (R-multiple)
Maximum consecutive loss/profit series analysis
Asset variation tracking
Comprehensive performance metrics
Trade pattern recognition
Period-based return calculations
Position Management:

Capital ratio trading (e.g., enter with 5% of account capital)
Futures market leverage setting (1-100x)
Dynamic position sizing (volatility-based)
Split buy/sell strategy implementation
Risk Management:

Technical indicator-based stop loss setting (e.g., lowest point among 10 candles on 5-minute chart)
Volatility-based stop loss/take profit (ATR multiples)
Maximum allowable loss limit (daily/weekly)
Dynamic take profit setting (trailing profit)
How It Works
User <--> AI Model(Claude/GPT) <--> MCP Protocol <--> CCXT MCP Server <--> Cryptocurrency Exchange API
User: Requests like "Tell me the Bitcoin price" or "Buy Ethereum on my Binance account"
AI Model: Understands user requests and determines which MCP tools/resources to use
MCP Protocol: Standardized communication between AI and CCXT MCP server
CCXT MCP Server: Communicates with cryptocurrency exchange APIs using the CCXT library
Exchange API: Provides actual data and executes trade orders
Using with AI Models
When registered with Claude Desktop, you can make the following types of requests to AI models:

Cautions and Recommended Prompts
When using AI models, consider the following cautions and use the prompt below for effective trading:

Your goal is to execute trades using the ccxt tools as much as possible
Cautions:
- Accurately identify whether it's a futures market or spot market before proceeding with trades
- If there's no instruction about percentage of capital or amount to use, always calculate and execute trades using the entire available capital
Notes:

AI models sometimes confuse futures trading with spot trading.
Without clear guidance on trading capital size, AI might get confused.
Using the above prompt helps clearly communicate your trading intentions.
Basic Query Examples
Check and compare the current Bitcoin price on binance and coinbase.
Advanced Trading Query Examples
Position Management

Open a long position on BTC/USDT futures market in my Bybit account (bybit_futures) with 5% of capital using 10x leverage.
Enter based on moving average crossover strategy and set stop loss at the lowest point among the 12 most recent 5-minute candles.
Performance Analysis

Analyze my Binance account (bybit_main) trading records for the last 7 days and show me the win rate, average profit, and maximum consecutive losses.
Detailed Trading Analytics

Analyze my trading performance on the bybit_futures account for BTC/USDT over the last 30 days. Calculate win rate, profit factor, and identify any patterns in my winning trades.
Show me the monthly returns for my bybit_main account over the past 90 days and identify my best and worst trading months.
Analyze my consecutive wins and losses on my bybit_futures account and tell me if I have any psychological patterns affecting my trading after losses.
Development
Building from Source
# Clone repository
git clone https://github.com/lazy-dinosaur/ccxt-mcp.git

# Navigate to project directory
cd ccxt-mcp

# Install dependencies
npm install

# Build
npm run build
🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

📄 License
Distributed under the MIT License. See the LICENSE file for more information.

❤️ Support
If you find this project useful, please consider giving it a ⭐️ on GitHub!