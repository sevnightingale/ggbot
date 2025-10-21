# Hummingbot API Documentation

**Base URL**: `http://localhost:8888`  
**Authentication**: HTTP Basic Auth  
- Username: `$HBOT_USERNAME` (set in your .env)
- Password: `$HBOT_PASSWORD` (set in your .env)

**Version**: 1.0.1

---

## Docker Management

### GET /docker/running
**Is Docker Running**

Check if Docker daemon is running.

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/docker/running
```

---

### GET /docker/available-images/
**Available Images**

Get available Docker images matching the specified name.

**Parameters:**
- image_name (query)

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/docker/available-images/
```

---

### GET /docker/active-containers
**Active Containers**

Get all currently active (running) Docker containers.

**Parameters:**
- name_filter (query)

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/docker/active-containers
```

---

### GET /docker/exited-containers
**Exited Containers**

Get all exited (stopped) Docker containers.

**Parameters:**
- name_filter (query)

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/docker/exited-containers
```

---

### POST /docker/clean-exited-containers
**Clean Exited Containers**

Remove all exited Docker containers to free up space.

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/docker/clean-exited-containers
```

---

### POST /docker/remove-container/{container_name}
**Remove Container**

Remove a Hummingbot container and optionally archive its bot data.

**Parameters:**
- container_name (path)*
- archive_locally (query)
- s3_bucket (query)

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/docker/remove-container/{container_name}
```

---

### POST /docker/stop-container/{container_name}
**Stop Container**

Stop a running Docker container.

**Parameters:**
- container_name (path)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/docker/stop-container/{container_name}
```

---

### POST /docker/start-container/{container_name}
**Start Container**

Start a stopped Docker container.

**Parameters:**
- container_name (path)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/docker/start-container/{container_name}
```

---

### POST /docker/pull-image/
**Pull Image**

Initiate Docker image pull as background task.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/docker/pull-image/
```

---

### GET /docker/pull-status/
**Get Pull Status**

Get status of all pull operations.

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/docker/pull-status/
```

---

## Account Management

### GET /accounts/
**List Accounts**

Get a list of all account names in the system.

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/accounts/
```

---

### GET /accounts/{account_name}/credentials
**List Account Credentials**

Get a list of all connectors that have credentials configured for a specific account.

**Parameters:**
- account_name (path)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/accounts/{account_name}/credentials
```

---

### POST /accounts/add-account
**Add Account**

Create a new account with default configuration files.

**Parameters:**
- account_name (query)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/accounts/add-account
```

---

### POST /accounts/delete-account
**Delete Account**

Delete an account and all its associated credentials.

**Parameters:**
- account_name (query)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/accounts/delete-account
```

---

### POST /accounts/delete-credential/{account_name}/{connector_name}
**Delete Credential**

Delete a specific connector credential for an account.

**Parameters:**
- account_name (path)*
- connector_name (path)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/accounts/delete-credential/{account_name}/{connector_name}
```

---

### POST /accounts/add-credential/{account_name}/{connector_name}
**Add Credential**

Add or update connector credentials (API keys) for a specific account and connector.

**Parameters:**
- account_name (path)*
- connector_name (path)*

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/accounts/add-credential/{account_name}/{connector_name}
```

---

## Connectors

### GET /connectors/
**Available Connectors**

Get a list of all available connectors.

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/connectors/
```

---

### GET /connectors/{connector_name}/config-map
**Get Connector Config Map**

Get configuration fields required for a specific connector.

**Parameters:**
- connector_name (path)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/connectors/{connector_name}/config-map
```

---

### GET /connectors/{connector_name}/trading-rules
**Get Trading Rules**

Get trading rules for a connector, optionally filtered by trading pairs.

**Parameters:**
- connector_name (path)*
- trading_pairs (query)

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/connectors/{connector_name}/trading-rules
```
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/connectors/kucoin_perpetual/trading-rules?trading_pairs=ZEUS-USDT
---

### GET /connectors/{connector_name}/order-types
**Get Supported Order Types**

Get order types supported by a specific connector.

**Parameters:**
- connector_name (path)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/connectors/{connector_name}/order-types
```

---

## Portfolio Management

### POST /portfolio/state
**Get Portfolio State**

Get the current state of all or filtered accounts portfolio.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/portfolio/state
```

---

### POST /portfolio/history
**Get Portfolio History**

Get the historical state of all or filtered accounts portfolio with pagination.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/portfolio/history
```

---

### POST /portfolio/distribution
**Get Portfolio Distribution**

Get portfolio distribution by tokens with percentages across all or filtered accounts.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/portfolio/distribution
```

---

### POST /portfolio/accounts-distribution
**Get Accounts Distribution**

Get portfolio distribution by accounts with percentages.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/portfolio/accounts-distribution
```

---

## Trading Operations

### POST /trading/orders
**Place Trade**

Place a buy or sell order using a specific account and connector.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/trading/orders
```

---

### POST /trading/{account_name}/{connector_name}/orders/{client_order_id}/cancel
**Cancel Order**

Cancel a specific order by its client order ID.

**Parameters:**
- account_name (path)*
- connector_name (path)*
- client_order_id (path)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/trading/{account_name}/{connector_name}/orders/{client_order_id}/cancel
```

---

### POST /trading/positions
**Get Positions**

Get current positions across all or filtered perpetual connectors.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/trading/positions
```

---

### POST /trading/orders/active
**Get Active Orders**

Get active (in-flight) orders across all or filtered accounts and connectors.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/trading/orders/active
```

---

### POST /trading/orders/search
**Get Orders**

Get historical order data across all or filtered accounts from the database/registry.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/trading/orders/search
```

---

### POST /trading/trades
**Get Trades**

Get trade history across all or filtered accounts with complex filtering.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/trading/trades
```

---

### POST /trading/{account_name}/{connector_name}/position-mode
**Set Position Mode**

Set position mode for a perpetual connector.

**Parameters:**
- account_name (path)*
- connector_name (path)*

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/trading/{account_name}/{connector_name}/position-mode
```

---

### GET /trading/{account_name}/{connector_name}/position-mode
**Get Position Mode**

Get current position mode for a perpetual connector.

**Parameters:**
- account_name (path)*
- connector_name (path)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/trading/{account_name}/{connector_name}/position-mode
```

---

### POST /trading/{account_name}/{connector_name}/leverage
**Set Leverage**

Set leverage for a specific trading pair on a perpetual connector.

**Parameters:**
- account_name (path)*
- connector_name (path)*

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/trading/{account_name}/{connector_name}/leverage
```

---

## Bot Orchestration

### GET /bots/
**Get All Bots**

Get all bot instances (running and stopped) with their current status.

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/bots/
```

---

### POST /bots/create
**Create Bot**

Create a new Hummingbot instance with specified configuration.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/bots/create
```

---

### POST /bots/{bot_name}/start
**Start Bot**

Start a stopped Hummingbot instance.

**Parameters:**
- bot_name (path)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/bots/{bot_name}/start
```

---

### POST /bots/{bot_name}/stop
**Stop Bot**

Stop a running Hummingbot instance.

**Parameters:**
- bot_name (path)*

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST -H "Content-Type: application/json" http://localhost:8888/bots/{bot_name}/stop
```

---

### DELETE /bots/{bot_name}
**Delete Bot**

Delete a Hummingbot instance and optionally archive its data.

**Parameters:**
- bot_name (path)*
- archive_locally (query)
- s3_bucket (query)

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X DELETE -H "Content-Type: application/json" http://localhost:8888/bots/{bot_name}
```

---

## Market Data

### POST /market-data/prices
**Get Real-Time Prices**

Get current prices for trading pairs from an exchange.

**Requires request body**

Request body example:
```json
{
  "connector_name": "binance",
  "trading_pairs": ["BTC-USDT", "ETH-USDT"]
}
```

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST \
  -H "Content-Type: application/json" \
  -d '{"connector_name": "binance", "trading_pairs": ["BTC-USDT"]}' \
  http://localhost:8888/market-data/prices
```

---

### POST /market-data/candles
**Get Candles**

Get candlestick/OHLCV data for trading pairs.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST \
  -H "Content-Type: application/json" \
  -d '{"connector_name": "binance", "trading_pair": "BTC-USDT", "interval": "15m"}' \
  http://localhost:8888/market-data/candles
```

---

### POST /market-data/order-book
**Get Order Book**

Get order book data for a trading pair.

**Requires request body**

```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST \
  -H "Content-Type: application/json" \
  -d '{"connector_name": "binance", "trading_pair": "BTC-USDT"}' \
  http://localhost:8888/market-data/order-book
```


---

## Example Usage


Here are some practical examples:

### Check if Docker is running
```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/docker/running
```

### List all available accounts
```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/accounts/
```

### Get all available connectors
```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD http://localhost:8888/connectors/
```

### Get real-time market prices
```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST \
  -H "Content-Type: application/json" \
  -d '{"connector_name": "binance", "trading_pairs": ["BTC-USDT", "ETH-USDT", "SOL-USDT"]}' \
  http://localhost:8888/market-data/prices
```

### Get portfolio state (requires JSON body)
```bash
curl -u $HBOT_USERNAME:$HBOT_PASSWORD -X POST \
  -H "Content-Type: application/json" \
  -d '{"accounts": [], "connectors": []}' \
  http://localhost:8888/portfolio/state
```

---

**Note**: Replace `{parameter}` placeholders with actual values when making requests. Parameters marked with `*` are required.