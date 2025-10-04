# Symphony Agent Portal

## Overview

The Symphony Agent Portal allows users to easily register agents that can autonomously and securely execute trades across different DeFi protocols. The portal allows users to register agents, enable/disable these agents to trade on their behalf, and expose API keys to submit trades directly to the Symphony infrastructure.

## Agentic Trading Instructions

1. [Register an agent](#registering-an-agent)
2. [Fund your Symphony wallet](#funding-your-symphony-wallet)
3. [Generate an API key](#generating-an-api-key)
4. [Start trading!](#trading)
5. [Sign Recall Message](#sign-message) (For Recall trading competition)

### Registering an Agent

1. Navigate to the `My Agents` page and click the `Register Agent` button in the top right corner.
   ![My Agents Tab](https://storage.googleapis.com/agent-portal-images/docs1.png)
2. Enter the agent's name and description. You can update these details at any time.
   ![Register Agent](https://storage.googleapis.com/agent-portal-images/docs3.png)
3. Check the `Autosubscribe` box to automatically subscribe to the agent upon creation.
   ![Autosubscribe](https://storage.googleapis.com/agent-portal-images/docs4.png)
4. Click the `Register Agent` button to create the agent.
   ![Register Agent](https://storage.googleapis.com/agent-portal-images/docs2.png)
5. Your new agent will now appear in the `My Agents` page.
   ![My Agents](https://storage.googleapis.com/agent-portal-images/docs5.png)

Subscribing to an agent will give the agent permission to trade on your behalf. You may subscribe to or unsubscribe from an agent at any time.

1. Navigate to the `My Agents` page.
   ![My Agents Tab](https://storage.googleapis.com/agent-portal-images/docs1.png)
2. Toggle the `Subscribe` or `Unsubscribe` button next to the agent you wish to give/remove permission to trade on your behalf.
   ![Subscribe/Unsubscribe](https://storage.googleapis.com/agent-portal-images/docs18.png)

### Funding your Symphony wallet

1. Navigate to the top right corner of the portal and click the blue square with the first letter of your email.
   ![Deposit](https://storage.googleapis.com/agent-portal-images/docs6.png)
2. Click on the `Deposit` button.
3. Select the chain and asset you wish to deposit (ONLY USDC is currently supported for agentic trading collateral).
   ![Deposit](https://storage.googleapis.com/agent-portal-images/docs7.png)
4. Select your preferred deposit method and follow the instructions to deposit.
   ![Deposit](https://storage.googleapis.com/agent-portal-images/docs8.png)
5. Confirm your deposit by checking your USDC balance beneath the `Deposit` button.
   ![Deposit](https://storage.googleapis.com/agent-portal-images/docs9.png)

### Generating an API key

1. Navigate to the `Generate Key` page.
   ![Generate Key Tab](https://storage.googleapis.com/agent-portal-images/docs10.png)
2. Click the `Create API Key` button.
   ![Create API Key](https://storage.googleapis.com/agent-portal-images/docs11.png)
3. Read the instructions and confirm by clicking the `Create API Key` button.
   ![Create API Key Warning](https://storage.googleapis.com/agent-portal-images/docs12.png)
4. Copy your new API key and save it in a secure location (you will not be able to access it after you leave this popup).
   ![New API Key](https://storage.googleapis.com/agent-portal-images/docs13.png)
5. Click `Done` to close the popup, you should now see your new API key prefix in the API key list.

If you fear your API key has been compromised, or if you would like to rotate your API key for other security reasons, you may do so at any time.

1. Navigate to the `Generate Key` page.
   ![Generate Key Tab](https://storage.googleapis.com/agent-portal-images/docs10.png)
2. Find the API key that you would like to rotate.
3. Click the `Rotate` button under actions.
   ![Rotate API Key](https://storage.googleapis.com/agent-portal-images/docs14.png)
4. Read the warning and confirm by clicking the `Rotate` button. You previous API key will be revoked and a new one will be generated.
   ![Rotate API Key Warning](https://storage.googleapis.com/agent-portal-images/docs15.png)
5. Copy your new API key and save it in a secure location (you will not be able to access it after you leave this popup).
   ![New API Key](https://storage.googleapis.com/agent-portal-images/docs16.png)
6. Click `Done` to close the popup, you should now see your new API key prefix in the API key list.

### Trading

#### Opening a trade:

`POST https://api.symphony.io/agent/batch-open`

This endpoint takes in a JSON object representing a batch trade that an agent wants to execute on behalf of all users that are subscribed to the agent. The endpoint returns a unique `batchId` that can be used to track and close all trades opened in this call.

Required fields:

Body parameters:

- `agentId`: Your agent's ID (copy from the top right corner of your agent on the `My Agents` page).
- `symbol`: The symbol of the asset you wish to trade. See our list of [supported assets](#supported-assets) below.
- `action`: The action you wish to take (`LONG` or `SHORT`).
- `weight`: The weight of the trade (greater than `0` but less than or equal to `100`).  
**The minimum trade size is 5 USDC. Please ensure that your account balance multiplied by the weight in the request body result in a trade size larger than 5 USDC.** 
- `leverage`: The leverage you wish to use for the trade (minimum `1.1`).

Optional fields:

Body parameters:

- `orderOptions`: An object containing the following fields:
    - `triggerPrice`: The price at which the trade will be executed (optional). If this price is set, the trade will be opened as an order until the price reaches the trigger price, at which point the order will be executed.
    - `stopLossPrice`: The price at which the trade will be closed if the price moves against you (optional, less than current price for LONG, greater than current price for SHORT).
    - `takeProfitPrice`: The price at which the trade will be closed if the price moves in your favor (optional, greater than current price for LONG, less than current price for SHORT).

Headers:

- `x-api-key`: Your Symphony API key

Sample request JSON:

```json
{
    "agentId": "63946153-9f33-4b7e-9b32-b99a4a6037e2",
    "symbol": "SOL",
    "action": "LONG",
    "weight": 100,
    "leverage": 2,
    "orderOptions": {
        "triggerPrice": 0,
        "stopLossPrice": 0,
        "takeProfitPrice": 0
    }
}
```

Sample response JSON:

```json
{
    "message": "Batch open trade submitted",
    "batchId": "eff6924e-e737-4243-8718-45fc402a342f",
    "successful": 1,
    "failed": 0,
    "results": [
        {
            "smartAccount": "0xbaf3de56e5815e9b2894a95d85b8023c3ac03e4e",
            "result": {
                "success": true,
                "protocolOrderHash": null,
                "protocolPositionHash": "0xbb2157e021fa9deb6c47b30d5a488a79f6ae4d1099d5e23839430bc6e95c1400",
                "symphonyPositionHash": "0x4ae95144f6b9521328e3c7d8563adbe1100e3b2747a03c7abe373e9829c965e6",
                "intentHash": "0x4fba175d1ec75a62a7996e98e4cc1c7ad282d35cbaa977d5b02638bafae9fff1",
                "srcChainId": 42161,
                "submitTxHash": "0x8bbaa0300777ec02ed962e5ea3cb48a1471ee0448de145c477b21595783026fb",
                "submitExplorerUrl": "https://arbiscan.io/tx/0x8bbaa0300777ec02ed962e5ea3cb48a1471ee0448de145c477b21595783026fb",
                "dstChainId": 42161,
                "executeTxHash": "0x8bbaa0300777ec02ed962e5ea3cb48a1471ee0448de145c477b21595783026fb",
                "executeExplorerUrl": "https://arbiscan.io/tx/0x8bbaa0300777ec02ed962e5ea3cb48a1471ee0448de145c477b21595783026fb",
                "adjustedFansToAdd": 3,
                "newFanCount": 897
            }
        }
    ]
}
```

#### Closing a trade:

`POST https://api.symphony.io/agent/batch-close`

This endpoint takes in an `agentId` and `batchId` and closes all the orders and/or positions for the given `batchId` for the agent.

Required fields:

Body parameters:

- `agentId`: Your agent's ID (copy from the top right corner of your agent on the `My Agents` page).
- `batchId`: The unique ID of the batch trade you wish to close (copy from the response of the `batch-open` endpoint).

Headers:

- `x-api-key`: Your Symphony API key

Sample request JSON:

```json
{
    "agentId": "63946153-9f33-4b7e-9b32-b99a4a6037e2",
    "batchId": "5cb80fd9-e820-4343-9d23-e1fca2951def"
}
```

Sample response JSON:

```json
{
    "message": "Batch close trade submitted",
    "batchId": "629373ff-6473-49b9-8357-ac59fa9b6341",
    "successful": 1,
    "skipped": 1,
    "failed": 0,
    "results": [
        {
            "smartAccount": "0xe1f8d0d7b845a2da77182325263285c88830adc0",
            "result": {
                "txHash": "0x3420de502a4dc...",
                "chainId": 42161,
                "success": true
            }
        }
    ]
}
```

#### Get agent positions:

`GET https://api.symphony.io/agent/positions?agentId={AGENT_ID}&status={STATUS}&address={address}`

This endpoint is used to get all the positions and/or orders for a given agent. Orders will be returned in the orders array and positions will be returned in the positions array.

Required fields:

Query parameters:

- `agentId`: Your agent's ID (copy from the top right corner of your agent on the `My Agents` page).

Optional fields:

Query parameters:

- `status`: The status of the positions/orders you wish to filter by (optional, valid options are `OPEN`, `CLOSED`, and `LIQUIDATED`).
- `address`: The address of the user you wish to filter by (optional).

Headers:

- `x-api-key`: Your Symphony API key

Sample response JSON:

```json
{
    "agentId": "63946153-9f33-4b7e-9b32-b99a4a6037e2",
    "ordersCount": 1,
    "positionsCount": 1,
    "orders": [
        {
            "batchId": "45868f93-0ca6-48b5-b400-c9f25a10c3aa",
            "smartAccount": "0x2cd40dfcc2bbf13539ec7f961cb5fee8d4cb924c",
            "symphonyPositionHash": "0x0c32ddda340b9361...",
            "protocolOrderHash": "0x7ed431f01...",
            "status": "Closed",
            "orderType": "1",
            "collateralAmount": 5.526025000000001,
            "asset": "SOL",
            "leverage": 2,
            "positionSize": 11.052050000000001,
            "currentPrice": 202.8123,
            "createdTimestamp": "2025-09-04T20:01:42.835Z",
            "lastUpdatedTimestamp": "2025-09-04T20:03:59.735Z"
        }
    ],
    "positions": [
        {
            "batchId": "1af5b0ef-f9f8-4265-a5b7-c4f868c29879",
            "smartAccount": "0x69225eb24a62061a372da1d422859357bae84a3b",
            "symphonyPositionHash": "0x3169fea13fd66db...",
            "protocolPositionHash": "0x9bb914196ee...",
            "status": "Closed",
            "collateralAmount": 5.523403843301999,
            "pnlPercentage": 0,
            "pnlUSD": 0,
            "asset": "SOL",
            "isLong": true,
            "leverage": 2,
            "positionSize": 11.046807686603998,
            "entryPrice": 203.3902293307,
            "currentPrice": 203.4264,
            "slPrice": 0,
            "tpPrice": 0,
            "liquidationPrice": 0,
            "createdTimestamp": "2025-09-04T20:33:28.051Z",
            "lastUpdatedTimestamp": "2025-09-04T20:32:30.536Z"
        }
    ]
}
```

#### Get agent performance:

`GET https://api.symphony.io/agent/all-positions?userAddress={USER_ADDRESS}`

This endpoint returns the account summary, performance, and `openPositions` array for a user’s address (the wallet address that is being funded for the agent to trade).

Required fields:

Query parameters:

- `userAddress`: The address of the user you wish to get performance for.

No headers are required for this endpoint.

Sample response JSON:

```json
{
    "success": true,
    "data": {
        "userAddress": "0xcfd8f4dcaad1576c0a0eb07d6e5f78a18595b353",
        "accountSummary": {
            "totalEquity": 53.28,
            "initialCapital": 54.99999999999999,
            "totalUnrealizedPnl": 0,
            "totalRealizedPnl": -0.2,
            "totalPnl": -0.21,
            "totalFeesPaid": 0.17,
            "availableBalance": 45.29,
            "marginUsed": 7.99,
            "totalVolume": 139.75,
            "totalTrades": 1,
            "accountStatus": "active",
            "openPositionsCount": 1,
            "closedPositionsCount": 1,
            "liquidatedPositionsCount": 0,
            "performance": {
                "roi": -1.72,
                "roiPercent": -3.12,
                "totalTrades": 1,
                "averageTradeSize": 49.99
            }
        },
        "openPositions": [
            {
                "protocolPositionHash": "0x624cbe78b...",
                "symphonyPositionHash": "0x7f1cad2e5...",
                "userAddress": "0xcfd8f4dcaad1576c0a0eb07d6e5f78a18595b353",
                "isLong": true,
                "leverage": 5,
                "positionSize": 39.9676787415,
                "entryPrice": 219.0172660544,
                "tpPrice": null,
                "slPrice": null,
                "currentPrice": 218.9938,
                "liquidationPrice": 187.8138221857251,
                "collateralAmount": 7.9935357483,
                "pnlPercentage": -0.053571243086810466,
                "pnlUSDValue": -0.004282236466952887,
                "asset": "SOL",
                "createdTimeStamp": "2025-09-10T02:29:27.043Z",
                "lastUpdatedTimestamp": "2025-09-10T02:31:08.526Z",
                "status": "Open"
            }
        ],
        "lastUpdated": "2025-09-10T02:31:10.922Z",
        "cacheExpiresAt": "2025-09-10T02:31:15.922Z"
    },
    "processingTime": 1266
}
```

#### Getting all batches for an agent:

`GET https://api.symphony.io/agent/batches?agentId={AGENT_ID}`

This endpoint is used to get all the batches for an agent. Each batch corresponds to a group of one or more trades that were opened by the agent at the same time. If the status of the batch is `OPEN` then the batch contains active orders and/or positions. If the status of the batch is `CLOSED` then the batch contains closed orders and/or positions.

Note: It is possible for a batch to have a closed status and still contain active orders and/or positions. This can happen if one or more orders/positions failed to close for whatever reason. In this case the agent may call `batch-close` again to attempt to close any remaining orders/positions (orders/positions that are already closed will simply be skipped).

Required fields:

Query parameters:

- `agentId`: Your agent's ID (copy from the top right corner of your agent on the `My Agents` page).

Headers:

- `x-api-key`: Your Symphony API key

Sample response JSON:

```json
{
    "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
    "batches": [
        {
            "batchId": "dcb556b5-f81c-4401-b285-459664d4935a",
            "status": "CLOSED",
            "createTimestamp": "2025-09-06T20:23:16.931Z"
        }
    ]
}
```

#### Get Positions for Batch

`GET https://api.symphony.io/agent/batch-positions?batchId={BATCH_ID}`

This endpoint is used to get all the positions and/or orders for a given batch. Orders will be returned in the orders array and positions will be returned in the positions array. Normally trades will be either all orders or all positions, but in the rare case that some orders get executed while others do not, there can be a mix of orders and positions in the response.

Required fields:

Query parameters:

- `batchId`: The unique ID of the batch trade you wish to get positions for (copy from the response of the `batch-open` endpoint).

Headers:

- `x-api-key`: Your Symphony API key

Sample response JSON:

```json
{
    "batchId": "dcb556b5-f81c-4401-b285-459664d4935a",
    "ordersCount": 0,
    "positionsCount": 1,
    "orders": [],
    "positions": [
        {
            "smartAccount": "0xbaf3de56e5815e9b2894a95d85b8023c3ac03e4e",
            "symphonyPositionHash": "0x0cc3ac3458a63be6c2bcbb42f8982315ce7585080a8d6b13a22af358d4cb25f1",
            "protocolPositionHash": "0x5b9c4e07fdb8c09f22ee6a55afd62ca49b3e0224a8eb070e49490d31c31d23b7",
            "status": "Open",
            "collateralAmount": 12.72294366114905,
            "pnlPercentage": 0.08712175486320987,
            "pnlUSD": 0.011084451787850575,
            "indexToken": "SOL",
            "leverage": 2
        }
    ]
}
```

#### Sign Message

`POST https://api.symphony.io/agent/sign-message`

This endpoint signs a message and returns the signature. The message is signed by the privy wallet associated with the developer who owns the API key.

Required fields:

Body parameters:

- `message`: The message to sign.

Headers:

- `x-api-key`: Your Symphony API key

Sample request JSON:

```json
{
    "message": "Hello, world!"
}
```

Sample response JSON:

```json
{
    "developerId": "5442a951-f4ad-49c4-866a-32483555941c",
    "wallet": "0x32e103bd21adeb4baa070eff73122bc37ce42bed",
    "symphonyWallet": "0xa5faf2170d5afbc1b024dbe3bdeb6e343fbb69c3",
    "message": "Hello, world!",
    "signature": "0xa788b5482804cd2274d21b316507f4..."
}
```

## Supported Assets

Currently, we support the following assets for agentic trading:

### Crypto

- BTC
- ETH
- BNB
- SOL
- XRP
- TON
- DOGE
- ADA
- SHIB
- AVAX
- TRX
- DOT
- LINK
- BCH
- NEAR
- LTC
- ICP
- UNI
- ETC
- RNDR
- HBAR
- PEPE
- APT
- IMX
- ATOM
- AR
- MNT
- FIL
- XLM
- GRT
- STX
- KAS
- OP
- WIF
- TAO
- ARB
- VET
- INJ
- AAVE
- ALGO
- BAT
- COMP
- MANA
- SNX
- YFI
- XTZ
- DASH
- NEO
- THETA
- ZRX
- SAND
- APE
- QNT
- RPL
- LDO
- CAKE
- FXS
- TWT
- DYDX
- GMX
- EGLD
- TIA
- FLOW
- GALA
- MINA
- ORDI
- ILV
- BLUR
- FET
- CFX
- BEAM
- SEI
- ROSE
- WOO
- ZIL
- GMT
- ASTR
- 1INCH
- FLOKI
- QTUM
- WLD
- MASK
- CELO
- LRC
- ENS
- MEME
- ANKR
- IOTX
- KSM
- RVN
- SKL
- SUPER
- JUP
- MANTA
- BONK
- PENDLE
- OSMO
- ALT
- UMA
- MAGIC
- API3
- STRK
- DYM
- NTRN
- PYTH
- SC
- PIXEL
- JTO
- STG
- BOME
- ETHFI
- METIS
- AEVO
- ONDO
- RON
- ENA
- ZEUS
- TNSR
- OMNI
- MERL
- SAGA
- NOT
- IO
- BRETT
- ATH
- ZRO
- ZK
- RATS
- PEOPLE
- TURBO
- SATS
- POPCAT
- MOG
- CORE
- JASMY
- MEW
- DEGEN
- AVAIL
- BANANA
- RARE
- NMR
- RSR
- SYN
- AUCTION
- ALICE
- SUN
- TRB
- DOGS
- SSV
- PONKE
- NEIRO
- MOODENG
- NEIROCTO
- RAY
- STORJ
- HOT
- GOAT
- BSV
- ARK
- CVC
- AERO
- POLYX
- HMSTR
- ZETA
- CKB
- CAT
- SUNDOG
- FLUX
- POL
- W
- PNUT
- ACT
- GRASS
- ZEN
- VIRTUAL
- SPX
- ACX
- CHILLGUY
- MOVE
- ME
- COW
- AVA
- PENGU
- FARTCOIN
- ZEREBRO
- AI16Z
- AIXBT
- BIO
- TRUMP
- MELANIA
- HYPE
- S
- ARC
- ARKM
- GRIFFAIN
- SWARMS
- PLUME
- VVV
- VINE
- TOSHI
- CHEEMS
- SOLV
- TST
- APU

### Stocks (NOTE: These assets are only tradeable during market hours EST)

- AAPL
- META
- GOOGL
- AMZN
- MSFT
- TSLA
- SNAP
- NVDA
- GME
- COIN
- SPY
- QQQ
- IWM
- DIA

---

# ggbots Platform Integration

## Overview

This section outlines the complete integration plan for bringing Symphony.io live trading capabilities into the ggbots platform. The integration will run in parallel with our existing paper trading system, allowing users to execute the same AI-driven strategies with real capital while maintaining our proven risk management framework.

## Architecture Design

### Simplified Execution Model

ggbots will support **two trading modes** per bot configuration:

1. **Paper Trading** - Simulated $10k accounts (current default)
2. **Live Trading** - Execute trades via Symphony.io with real capital

**Key Architectural Principles:**

- **Thin API Wrapper**: Symphony handles position lifecycle, we route AI decisions
- **Minimal Database**: Just credentials and audit trail, query Symphony for positions
- **No Duplication**: Symphony owns monitoring, risk, P&L calculation
- **Clean Separation**: Decision engine → trading router → Symphony or paper

### Integration Flow

```
AI Decision → Trading Router → Paper OR Live

Paper Path:
  → SupabasePaperTradingService
  → Supabase (paper_trades table)
  → Our monitoring service (3s intervals)

Live Path:
  → SymphonyLiveTradingService (thin wrapper)
  → Symphony API (batch-open/close)
  → Supabase (live_trades audit trail only)
  → Symphony handles monitoring/SL/TP
```

**Key Point:** For live trades, we just call Symphony API and save audit trail. Symphony owns the position lifecycle.

## Database Schema

### Simplified Approach

**Philosophy**: Symphony handles position monitoring, balance tracking, and risk management. We focus on decision-making and audit trail.

### New Tables

#### 1. `symphony_credentials`

Secure storage for Symphony API keys:

```sql
CREATE TABLE symphony_credentials (
    credential_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    config_id UUID REFERENCES configurations(config_id) ON DELETE CASCADE,

    -- Symphony.io Details
    agent_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255),
    api_key_encrypted TEXT NOT NULL,  -- Encrypted with application key
    smart_account_address VARCHAR(255),  -- User's Symphony wallet

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_validated_at TIMESTAMP,
    validation_error TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_symphony_credentials_user ON symphony_credentials(user_id);
CREATE INDEX idx_symphony_credentials_config ON symphony_credentials(config_id);
CREATE UNIQUE INDEX idx_symphony_credentials_agent ON symphony_credentials(agent_id, user_id);
```

#### 2. `live_trades`

Audit trail only - Symphony is source of truth for positions:

```sql
CREATE TABLE live_trades (
    trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    config_id UUID NOT NULL REFERENCES configurations(config_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    decision_id UUID REFERENCES decisions(decision_id) ON DELETE SET NULL,
    credential_id UUID NOT NULL REFERENCES symphony_credentials(credential_id) ON DELETE CASCADE,

    -- Symphony.io Tracking
    symphony_batch_id VARCHAR(255) NOT NULL UNIQUE,  -- For closing positions
    symphony_position_hash VARCHAR(255),
    symphony_protocol_position_hash VARCHAR(255),

    -- Trade Intent (what we asked Symphony to do)
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) CHECK (side IN ('long', 'short')) NOT NULL,
    requested_weight DECIMAL(5,2),  -- % of balance we requested
    requested_leverage INTEGER,
    requested_stop_loss DECIMAL(20,8),
    requested_take_profit DECIMAL(20,8),

    -- AI Decision Context
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    reasoning TEXT,

    -- Status Tracking
    status VARCHAR(20) CHECK (status IN ('submitted', 'open', 'closed', 'failed')) DEFAULT 'submitted',
    execution_error TEXT,  -- If Symphony rejected the trade

    -- Timestamps
    submitted_at TIMESTAMP DEFAULT NOW(),
    opened_at TIMESTAMP,     -- When Symphony confirmed open
    closed_at TIMESTAMP,     -- When Symphony confirmed closed
    last_synced_at TIMESTAMP -- Last time we synced with Symphony API
);

-- Indexes
CREATE INDEX idx_live_trades_user_id ON live_trades(user_id);
CREATE INDEX idx_live_trades_config_id ON live_trades(config_id);
CREATE INDEX idx_live_trades_status ON live_trades(status) WHERE status IN ('submitted', 'open');
CREATE INDEX idx_live_trades_symphony_batch ON live_trades(symphony_batch_id);
CREATE INDEX idx_live_trades_decision ON live_trades(decision_id);
```

**Note**: We don't store entry_price, current_price, P&L, etc. - we query Symphony API for real-time data.

## Missing Symphony API Endpoints

**Critical for MVP Integration:**

### 1. Account Balance Endpoint ❌

**Current Status**: Documented at `GET /agent/all-positions?userAddress={ADDRESS}` but returns 404.

**What We Need**:
```
GET /agent/balance?agentId={AGENT_ID}
Headers: x-api-key

Response:
{
  "agentId": "...",
  "smartAccount": "0x...",
  "balance": 245.50,
  "currency": "USDC",
  "availableBalance": 200.00,
  "marginUsed": 45.50
}
```

**Why**: We need to calculate position sizes (% of available balance) and validate sufficient funds before submitting trades.

**Workaround**: None currently - can't display balance to users or validate trades.

---

### 2. Batch Position Details ✅ (Partial)

**Current Status**: `GET /agent/batch-positions?batchId={BATCH_ID}` exists and works.

**What's Missing**: Entry price and timestamps in response.

**Enhanced Response Needed**:
```json
{
  "batchId": "...",
  "positions": [{
    "entryPrice": 122321.22,          // MISSING
    "entryTimestamp": "2025-10-04...", // MISSING
    "currentPrice": 122287.30,
    "pnlUSD": -0.0035,
    "status": "Open"
  }]
}
```

**Why**: Need entry price to calculate position sizing and display trade history accurately.

---

### 3. Webhook Support ❌

**What We Need**:
```
POST /agent/webhooks/configure
Headers: x-api-key

Body:
{
  "agentId": "...",
  "webhookUrl": "https://ggbots-api.nightingale.business/webhooks/symphony",
  "events": ["position.opened", "position.closed", "position.liquidated"]
}

Response:
{
  "webhookId": "...",
  "status": "active"
}
```

**Why**: Real-time notifications when positions open/close, eliminating need for constant polling.

**Workaround**: Poll `/agent/positions` every 30 seconds (not ideal).

---

### 4. Programmatic Account Creation ❌

**What We Need** (for future seamless onboarding):
```
POST /api/developer/create-account
Headers: x-symphony-partner-key  (ggbots partnership key)

Body:
{
  "email": "user@example.com",
  "referralSource": "ggbots"
}

Response:
{
  "developerId": "...",
  "wallet": "0x...",
  "symphonyWallet": "0x...",
  "initialSetupToken": "..."  // One-time token for wallet funding
}
```

**Why**: Enable one-click Symphony account creation from ggbots dashboard.

**Workaround**: Users manually create Symphony accounts (Option A in User Flow section).

---

## Service Layer Implementation

### Simplified SymphonyService

Thin API wrapper - Symphony handles position management, we handle decision-making:

```python
"""
Symphony.io Live Trading Service (Simplified)

Philosophy: Symphony owns position lifecycle, we own AI decisions.
"""

import aiohttp
from typing import Dict, List, Optional
from core.common.logger import logger
from core.common.db import get_db_connection


class SymphonyLiveTradingService:
    """Thin wrapper around Symphony API."""

    def __init__(self):
        self.base_url = "https://api.symphony.io"
        self._log = logger.bind(component="symphony_live")

    async def execute_trade_intent(self, intent: Dict) -> Dict:
        """Execute trade via Symphony API and save to audit trail."""

        # 1. Get credentials
        creds = await self._get_credentials(intent['config_id'])

        # 2. Calculate weight % from confidence
        # TODO: Once Symphony adds balance endpoint, we can validate available funds
        weight = intent['confidence'] * 100  # e.g., 75% confidence = 75% of balance

        # 3. Call Symphony API
        payload = {
            "agentId": creds['agent_id'],
            "symbol": self._to_symphony_symbol(intent['symbol']),  # BTC/USDT → BTC
            "action": intent['action'].upper(),
            "weight": weight,
            "leverage": intent.get('leverage', 1),
            "orderOptions": {
                "stopLossPrice": intent.get('stop_loss_price', 0),
                "takeProfitPrice": intent.get('take_profit_price', 0)
            }
        }

        result = await self._call_symphony("POST", "/agent/batch-open", payload, creds)

        # 4. Save audit trail
        await self._save_trade_record(intent, result)

        return {"status": "submitted", "batch_id": result['batchId']}

    async def close_position(self, batch_id: str, config_id: str) -> Dict:
        """Close position via Symphony API."""

        creds = await self._get_credentials(config_id)

        payload = {
            "agentId": creds['agent_id'],
            "batchId": batch_id
        }

        result = await self._call_symphony("POST", "/agent/batch-close", payload, creds)

        # Update audit trail
        await self._mark_trade_closed(batch_id)

        return {"status": "closed"}

    async def get_positions(self, config_id: str) -> List[Dict]:
        """Get live positions from Symphony API (not database)."""

        creds = await self._get_credentials(config_id)

        params = {"agentId": creds['agent_id'], "status": "OPEN"}
        result = await self._call_symphony("GET", "/agent/positions", params, creds)

        # Enrich with our audit trail data (AI reasoning, confidence, etc.)
        return await self._enrich_with_audit_data(result['positions'])
```

**That's it.** ~100 lines instead of ~1000. Symphony does the heavy lifting.

### Orchestrator Integration

Simple routing in `/home/sev/ggbot/ggbot.py`:

```python
async def _run_trading_v2(self, config, user_id, decision_result):
    """Route to paper or live trading based on config."""

    trading_mode = config.trading.get('mode', 'paper')

    if trading_mode == "live":
        return await self.symphony_trading.execute_trade_intent({
            "config_id": config.config_id,
            "user_id": user_id,
            "decision_id": decision_result["decision_id"],
            "symbol": decision_result["symbol"],
            "action": decision_result["action"],
            "confidence": decision_result["confidence"],
            "stop_loss_price": decision_result.get("stop_loss_price"),
            "take_profit_price": decision_result.get("take_profit_price"),
            "reasoning": decision_result.get("reasoning")
        })
    else:
        # Default to paper
        return await self.paper_trading.execute_trade_intent(...)
```

**Note**: Removed "both" mode - can add later if users want it.

## Configuration Schema

Add to bot config JSON:

```json
{
  "trading": {
    "mode": "paper",  // or "live"
    "symphony_credential_id": null  // FK to symphony_credentials table
  }
}
```

That's it. Keep it simple.

## User Account Flow

### Current Onboarding (Paper Trading)

1. User signs up on ggbots.ai
2. Creates first bot configuration
3. Paper account auto-created with $10k balance
4. Starts trading immediately

### Proposed Flow: Live Trading Integration

#### Option A: Manual Symphony Setup (Current Implementation Possible)

**User Steps:**

1. **Create Symphony Account**
   - User navigates to https://agent-portal.symphony.io
   - Creates account via Privy wallet connection
   - Deposits USDC into Symphony wallet

2. **Create Agent in Symphony**
   - Register new agent in Symphony portal
   - Enable auto-subscribe to allow agent to trade
   - Generate API key for programmatic access

3. **Connect to ggbots**
   - In ggbots Settings → Live Trading
   - Enter Symphony Agent ID
   - Enter Symphony API Key
   - Click "Validate & Connect"
   - ggbots tests connection and displays balance

4. **Enable Live Trading**
   - In bot configuration → Trading Settings
   - Toggle trading mode from "Paper" to "Live"
   - Save configuration

5. **Trading Begins**
   - Next scheduled run executes via Symphony
   - Positions visible in ggbots dashboard (queried from Symphony API)
   - Real P&L displayed from Symphony's data

**Pros:**
- ✅ Can implement immediately with current Symphony API
- ✅ Full control and transparency for users
- ✅ No custody risk (funds stay in user's Symphony account)

**Cons:**
- ❌ Cumbersome onboarding (5+ steps)
- ❌ User must manage two accounts (ggbots + Symphony)
- ❌ API key security concerns
- ❌ High friction for adoption

#### Option B: Integrated Symphony Account Creation (Requires Symphony API Enhancement)

**Desired Flow:**

1. **ggbots Initiates Setup**
   - User clicks "Enable Live Trading" in ggbots
   - ggbots shows "Connect Symphony Account" modal

2. **Seamless Account Creation**
   - ggbots calls `POST /api/symphony/create-developer-account` (NEW ENDPOINT NEEDED)
   - Request body: `{"userId": "ggbots-user-123", "email": "user@example.com"}`
   - Symphony creates developer account server-to-server
   - Returns: `{"developerId": "...", "wallet": "0x...", "symphonyWallet": "0x..."}`

3. **Automatic Agent Registration**
   - ggbots calls `POST /api/symphony/register-agent` (NEW ENDPOINT NEEDED)
   - Request body: `{"developerId": "...", "agentName": "ggbots-config-456", "autoSubscribe": true}`
   - Symphony creates agent and returns agent ID

4. **API Key Generation**
   - ggbots calls `POST /api/symphony/generate-api-key` (NEW ENDPOINT NEEDED)
   - Request body: `{"developerId": "...", "agentId": "..."}`
   - Symphony generates API key and returns it
   - ggbots encrypts and stores in `symphony_credentials` table

5. **Funding Instructions**
   - ggbots displays deposit address (Symphony wallet)
   - User deposits USDC via preferred method
   - ggbots polls Symphony balance endpoint
   - When balance > 0, enables live trading

6. **Trading Begins**
   - User sets trading mode to "Live"
   - ggbots executes trades via stored API credentials
   - Fully integrated experience

**Pros:**
- ✅ Seamless user experience (minimal friction)
- ✅ Single dashboard for everything
- ✅ Credentials managed securely by ggbots
- ✅ Higher adoption rate

**Cons:**
- ❌ Requires Symphony to build server-to-server account creation API
- ❌ Increased security responsibility for ggbots
- ❌ More complex integration

### Open Questions for Symphony Team

**Critical Questions to Resolve:**

1. **Account Creation API**
   - Does Symphony plan to support programmatic account creation?
   - Can we create sub-accounts on behalf of users?
   - What authentication would be required (OAuth, API key, etc.)?

2. **Agent Management**
   - Can we programmatically register agents via API?
   - Can we create multiple agents per developer account?
   - What are the limits on agents per account?

3. **API Key Management**
   - Can we generate API keys programmatically?
   - Do API keys have different permission scopes?
   - Can we rotate keys via API?

4. **Balance & Wallet Access**
   - Is there an API endpoint to check wallet balance?
   - Can we query deposit addresses programmatically?
   - How do we handle multi-currency deposits (if USDC on different chains)?

5. **Webhook Support**
   - Does Symphony support webhooks for position updates?
   - Can we get real-time notifications when positions close?
   - Are there webhooks for balance changes?

6. **Rate Limiting & Quotas**
   - What are the rate limits for batch-open/batch-close?
   - Are there daily trade limits per agent?
   - How many positions can be open simultaneously?

7. **Error Handling**
   - What happens if a trade fails due to insufficient balance?
   - How do we handle partial fills?
   - Is there a retry mechanism for failed trades?

8. **Custody & Security**
   - How are user funds custodied (self-custody vs. smart contract)?
   - What security measures protect API keys?
   - Can users withdraw funds directly from Symphony without ggbots?

**Recommended Next Steps:**

1. **Schedule Integration Call with Symphony**
   - Present Option A vs. Option B
   - Understand their API roadmap
   - Discuss feasibility of account creation endpoints

2. **Implement Option A as MVP**
   - Launch with manual Symphony setup
   - Gather user feedback on friction points
   - Validate demand for live trading

3. **Collaborate on Option B**
   - Work with Symphony to design server-to-server APIs
   - Conduct security audit of credential storage
   - Plan phased rollout

4. **Fallback Plan**
   - If Symphony cannot support Option B, explore Privy OAuth integration
   - Investigate direct smart contract interaction
   - Consider alternative live trading providers (Hummingbot direct, etc.)

## Frontend Integration

### Settings Page: Live Trading Configuration

Add new section to `/home/sev/ggbot/frontend/app/forge/components/configure/StrategyEditor.tsx`:

```tsx
{/* Live Trading Settings */}
<div className="space-y-4">
  <h3 className="text-lg font-medium">Live Trading (Symphony.io)</h3>

  {!symphonyConnected ? (
    <div className="border border-dashed border-gray-300 rounded-lg p-6">
      <p className="text-sm text-gray-600 mb-4">
        Connect your Symphony account to execute trades with real capital.
      </p>
      <button
        onClick={() => setShowSymphonyModal(true)}
        className="btn-primary"
      >
        Connect Symphony Account
      </button>
    </div>
  ) : (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium">Symphony Agent Connected</p>
          <p className="text-sm text-gray-500">
            Agent ID: {symphonyAgentId}
          </p>
          <p className="text-sm text-gray-500">
            Balance: ${symphonyBalance.toFixed(2)} USDC
          </p>
        </div>
        <button
          onClick={disconnectSymphony}
          className="text-sm text-red-600"
        >
          Disconnect
        </button>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">
          Trading Mode
        </label>
        <select
          value={configData?.trading?.mode || 'paper'}
          onChange={(e) => updateTradingMode(e.target.value)}
          className="input"
        >
          <option value="paper">Paper Trading Only</option>
          <option value="live">Live Trading Only</option>
          <option value="both">Paper + Live (Parallel)</option>
        </select>
      </div>

      {configData?.trading?.mode === 'live' ||
       configData?.trading?.mode === 'both' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
          <p className="text-sm text-yellow-800">
            <strong>Warning:</strong> Live trading uses real capital.
            Ensure your risk settings are appropriate.
          </p>
        </div>
      )}
    </div>
  )}
</div>
```

### Dashboard: Unified Position Display

Update `/home/sev/ggbot/frontend/app/forge/components/dashboard/PositionsTable.tsx`:

```tsx
export function PositionsTable({ positions }) {
  return (
    <table className="min-w-full">
      <thead>
        <tr>
          <th>Mode</th>  {/* NEW: Paper vs. Live indicator */}
          <th>Symbol</th>
          <th>Side</th>
          <th>Entry</th>
          <th>Current</th>
          <th>Size</th>
          <th>Leverage</th>
          <th>P&L</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {positions.map(pos => (
          <tr key={pos.trade_id}>
            <td>
              <span className={`badge ${pos.mode === 'live' ? 'badge-live' : 'badge-paper'}`}>
                {pos.mode === 'live' ? '🔴 LIVE' : '📄 PAPER'}
              </span>
            </td>
            {/* ... rest of row ... */}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

## MVP Implementation Plan

**Week 1-2: Core Integration**
1. Create 2 database tables (symphony_credentials, live_trades)
2. Build SymphonyService (~100 lines)
3. Add routing logic to orchestrator
4. Manual testing with $10 USDC

**Week 3: Frontend**
1. Symphony credentials form (agent ID + API key input)
2. Trading mode toggle (Paper/Live)
3. Live positions display (query Symphony API)

**Week 4: Beta**
1. Test with 3-5 users
2. Monitor for issues
3. Gather feedback

**Security:**
- Encrypt API keys with Fernet (Python `cryptography`)
- Store in `api_key_encrypted` column
- Row-level security on credentials table

**That's it.** 4 weeks to MVP with manual Symphony setup.

---

## Summary

**Simplified Integration Approach:**

We're not rebuilding paper trading for live - we're just routing AI decisions to Symphony's API and saving an audit trail.

**What Symphony Handles:**
- Position monitoring
- Balance tracking
- SL/TP execution
- P&L calculation
- Risk management

**What We Handle:**
- AI decision-making
- Confidence-based position sizing
- Credential security
- Audit trail
- Dashboard display (query Symphony API)

**Total Code:** ~300 lines (2 tables, 1 service, routing logic)

**MVP Timeline:** 4 weeks

**Next Steps:**

1. **Bring Missing Endpoints to Symphony Team:**
   - Balance endpoint (critical)
   - Entry price in batch details
   - Webhook support (nice-to-have)
   - Programmatic account creation (future)

2. **Implement MVP:**
   - Manual Symphony setup (Option A)
   - 2 database tables
   - Thin service wrapper
   - Basic frontend

3. **Beta Test:**
   - 3-5 users with small capital
   - Monitor for issues
   - Iterate based on feedback
