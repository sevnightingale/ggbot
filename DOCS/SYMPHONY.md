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
