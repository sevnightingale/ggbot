Quickstart
This guide demonstrates how to use Hummingbot API to add exchange credentials, view your portfolio, and place a market order.

Prerequisites¶
Hummingbot API installed and running (see Installation Guide)
Exchange API keys (e.g., Binance)
Python 3.7+ with hummingbot-api-client installed (optional)
Setup Python Client (Optional)¶
If you want to use the Python client for the examples below:

Install the Hummingbot API Client:


pip install hummingbot-api-client
Create a new Python file (e.g., hummingbot_api_demo.py):


touch hummingbot_api_demo.py
Add the following code to initialize the client:


import asyncio
from hummingbot_api_client import HummingbotAPIClient

# Create client instance
client = HummingbotAPIClient(
    base_url="http://localhost:8000",
    username="admin",
    password="admin"
)
To run any of the examples below, use:


python hummingbot_api_demo.py
List Available Exchanges¶
Get a list of all available exchange connectors. Note that spot and perpetual markets are separate connectors (e.g., hyperliquid for spot and hyperliquid_perpetual for perps).


curl
Python Client

curl -u admin:admin -X 'GET' \
  'http://localhost:8000/connectors/' \
  -H 'accept: application/json'

Response:


curl
Python Client

[
  "binance",
  "binance_perpetual",
  "hyperliquid",
  "hyperliquid_perpetual",
  "okx",
  "okx_perpetual",
]

Get Connector Configuration¶
Before adding credentials, check what configuration fields are required for your connector:


curl
Python Client

curl -u admin:admin -X 'GET' \
  'http://localhost:8000/connectors/hyperliquid/config-map' \
  -H 'accept: application/json'

Response:


curl
Python Client

[
  "hyperliquid_api_secret",
  "use_vault",
  "hyperliquid_api_key"
]

Add Exchange Credentials¶
Add your exchange credentials to the API. By default, only the master_account is created. You can add multiple accounts with different names if needed.

For Hyperliquid:

hyperliquid_api_secret: Your Hyperliquid public address or vault address
hyperliquid_api_key: Your API private key
use_vault: Set to true if using vault address, false for normal account

curl
Python Client

curl -X POST http://localhost:8000/accounts/add-credential/master_account/hyperliquid \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -d '{
    "hyperliquid_api_key": "0x1234...abcd",
    "hyperliquid_api_secret": "your-private-key",
    "use_vault": false
  }'

Response:


curl
Python Client

{
  "message": "Connector credentials added successfully,
}

View Your Portfolio¶
Check your portfolio balances across all connected exchanges:


curl
Python Client

curl -u admin:admin -X 'POST' \
  'http://localhost:8000/portfolio/state' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{}'

Response:


curl
Python Client

{
  "master_account": {
    "hyperliquid": [
      {
        "token": "USDC",
        "units": 100.00,
        "price": 1,
        "value": 100.00,
        "available_units": 100.00
      }
    ]
  }
}

Get Trading Rules¶
Before placing orders, fetch the trading rules for your intended trading pair to understand order size limits and price increments:


curl
Python Client

curl -u admin:admin -X 'GET' \
  'http://localhost:8000/connectors/hyperliquid/trading-rules?trading_pairs=HYPE-USDC' \
  -H 'accept: application/json'

Response:


curl
Python Client

{
  "HYPE-USDC": {
    "min_order_size": 0,
    "max_order_size": 1e+56,
    "min_price_increment": 0.0001,
    "min_base_amount_increment": 0.01,
    "min_quote_amount_increment": 1e-56,
    "min_notional_size": 0,
    "min_order_value": 0,
    "max_price_significant_digits": 1e+56,
    "supports_limit_orders": true,
    "supports_market_orders": true,
    "buy_order_collateral_token": "USDC",
    "sell_order_collateral_token": "USDC"
  }
}

Place a Limit Order¶
Execute a limit sell order for HYPE:


curl
Python Client

curl -u admin:admin -X 'POST' \
  'http://localhost:8000/trading/orders' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "account_name": "master_account",
  "connector_name": "hyperliquid",
  "trading_pair": "HYPE-USDC",
  "trade_type": "SELL",
  "amount": 1,
  "order_type": "LIMIT",
  "price": 47.1,
  "position_action": "OPEN"
}'

Geo-Restriction Error

If you receive an error like:


{
  "detail": "Failed to place trade: No order book exists for 'HYPE-USDC'."
}
This may indicate you are geo-restricted from trading on the exchange. Check your API logs for more details:

docker logs hummingbot-api
Complete Example¶
Here's a complete example that performs all three operations:


curl
Python Client

echo "🔑 Adding Exchange Account..."
curl -X POST "http://localhost:8000/accounts/add-account" \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -d '{"account_name": "master_account"}'

# Step 2: Add credentials for hyperliquid
curl -X POST "http://localhost:8000/accounts/add-credential/master_account/hyperliquid" \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -d '{
    "hyperliquid_api_key": "0x1234...abcd",
    "hyperliquid_api_secret": "your-arbitrum-private-key",
    "use_vault": false
  }'

# Wait for account sync
sleep 2

# Step 3: View portfolio
echo -e "\n\U0001F4CA Fetching Portfolio..."
curl -X POST "http://localhost:8000/portfolio/state" \
  -u "admin:admin" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{}'

# Step 4: Get trading rules for HYPE-USDC
echo -e "\n\U0001F4CF Getting Trading Rules..."
curl -X GET "http://localhost:8000/connectors/hyperliquid/trading-rules?trading_pairs=HYPE-USDC" \
  -u "admin:admin" \
  -H "accept: application/json"

# Step 5: Place limit order
echo -e "\n\U0001F4B1 Placing Limit Order..."
curl -X POST "http://localhost:8000/trading/orders" \
  -u "admin:admin" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "account_name": "master_account",
    "connector_name": "hyperliquid",
    "trading_pair": "HYPE-USDC",
    "trade_type": "SELL",
    "amount": 1,
    "order_type": "LIMIT",
    "price": 47.1,
    "position_action": "OPEN"
  }'

Next Steps¶
Now that you've completed the quickstart, explore more advanced features:

Bot Management: Deploy and manage multiple trading bots
Strategy Configuration: Configure and deploy trading strategies
Market Data: Access real-time and historical market data
Backtesting: Test your strategies with historical data
For the complete API reference, visit the API documentation when your API is running.