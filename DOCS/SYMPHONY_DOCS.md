# Overview

# ​Symphony API Documentation

​
Symphony API Documentation
Note: There is currently a activation requirement of completing 5 trades in
order to become a activated agent which allows you to accept subscribers and
start earning fees

## ​Overview

​
Overview
Developers can create fully autonomous AI agents that execute trades through Symphony’s execution network. Each user receives a
Symphony smart account
at sign-up and maintains full custody over their funds at all times. Agents can only perform actions explicitly authorized by the user via delegated signing. Each user will deposit funds into their Symphony smart account (automatically generated for them at sign-up). ONLY the AI agent created by the user will have permission to act on behalf of this smart account, and ONLY for specific trading actions.
Currently Available features:
- Perpetuals Trading
Perpetuals Trading
- Spot Trading
Spot Trading
Coming Soon Features:
- Prediction Markets
Prediction Markets
- Yield Markets
Yield Markets

# Register an Agentic Fund

## ​Register an Agentic Fund

​
Register an Agentic Fund
Learn how to register your first AI fund and configure it for trading on Symphony.
Select the
Create Agentic Fund
button on the top right corner of the page.
Select
Continue
on the disclaimer modal.
Enter the AI fund’s name and description. You can update the details at any time. Upload a profile image for your AI fund (PNG, JPG, GIF, WEBP - max 5MB). Additionally, the
Autosubscribe
box is checked by default. Autosubscribe allows the AI fund to automatically execute trades on your behalf using the wallet associated with your Symphony account. Select the tooltip to learn more about autosubscribe.
Select the AI fund type you wish to create. This determines if your AI fund will trade Perpetuals, Swaps, or Yields. (Note: More products coming soon!). Once selected click
continue
to move to the next step.
Select the fee structure you wish to use for your AI fund. You can update the fee structure at any time. This option is currently coming soon!
Your AI fund is now created! You can view it by clicking the
View My Agentic Funds
button.

# Fund your wallet

## ​Fund Your Wallet

​
Fund Your Wallet
Learn how to deposit USDC into your Symphony wallet for agentic trading.
Navigate to the top right corner of the portal and click the blue square with the first letter of your email.
Click on the
Deposit
button.
Select the chain and asset you wish to deposit (ONLY USDC is currently supported for agentic trading collateral).
Select your preferred deposit method and follow the instructions to deposit.
Confirm your deposit by checking your USDC balance beneath the
Deposit
button.

# Generate API Key

## ​Generate API Key

​
Generate API Key
Create and manage API keys to enable programmatic trading with your agents.

### ​Creating an API Key

​
Creating an API Key
Navigate to the
API Key
page.
Click the
Create API Key
button.
Read the instructions and confirm by clicking the
Create API Key
button.
Copy your new API key and save it in a secure location (you will not be able to access it after you leave this popup).

### ​Rotating an API Key

​
Rotating an API Key
If you fear your API key has been compromised, or if you would like to rotate your API key for other security reasons, you may do so at any time.
- Navigate to the API Keys page.
Navigate to the
API Keys
page.
- Find the API key that you would like to rotate.
Find the API key that you would like to rotate.
- Click the Rotate button under actions.
Click the
Rotate
button under actions.
Read the warning and confirm by clicking the
Rotate
button. Your previous API key will be revoked and a new one will be generated.

# Spot Trading Guide

> Complete guide to spot trading on Symphony

<Note>
  Spot Trading is currently only active on Monad and eligible for trading
  rewards. User's should start with \$MON as their collateral asset
</Note>

## Spot Trading Guide

Complete guide to executing spot trades using the Symphony API.

## Executing a Spot Trade

This endpoint executes a token swap on behalf of all users subscribed to an agent. The swap amount per user is determined by the `weight` parameter (percentage of their balance). The system uses **intelligent DEX routing** to automatically select the best protocol.

### Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="tokenIn" type="string" required>
  The input token symbol (e.g., "MON", "USDC")
</ParamField>

<ParamField body="tokenOut" type="string" required>
  The output token symbol (e.g., "USDC", "MON")
</ParamField>

<ParamField body="weight" type="number" required>
  The percentage of user's balance to swap (0-100)
</ParamField>

<ParamField body="intentOptions" type="object">
  Optional intent configuration object

  <Expandable title="intentOptions properties">
    * `desiredProtocol` (string, optional): Desired protocol for the swap (e.g.,
      "kuru")
  </Expandable>
</ParamField>

### Response

<ResponseField name="message" type="string">
  Status message
</ResponseField>

<ResponseField name="batchId" type="string">
  Batch identifier for this swap operation
</ResponseField>

<ResponseField name="successful" type="number">
  Number of successful swaps
</ResponseField>

<ResponseField name="failed" type="number">
  Number of failed swaps
</ResponseField>

<ResponseField name="results" type="array">
  Array of swap results for each user

  <Expandable title="results">
    <ResponseField name="smartAccount" type="string">
      User's smart account address
    </ResponseField>

    <ResponseField name="result" type="object">
      Swap execution result

      <Expandable title="result">
        <ResponseField name="success" type="boolean">
          Whether the swap was successful
        </ResponseField>

        <ResponseField name="executeTxHash" type="string">
          Transaction hash for execution
        </ResponseField>

        <ResponseField name="explorerUrl" type="string">
          Explorer URL for the transaction
        </ResponseField>
      </Expandable>
    </ResponseField>
  </Expandable>
</ResponseField>

### Behavior

* Will swap for all subscribers of the agent
* If some swaps fail they will not affect the other swaps

### Authentication

Symphony API Key

### Headers

When using Symphony API key, include the following header:

* `x-api-key`: Symphony API key

<RequestExample>
  ```json  theme={null}
  {
    "agentId": "e8a54723-6485-41b9-91d7-7bdfd61ba621",
    "tokenIn": "MON",
    "tokenOut": "0x350035555e10d9afaf1566aaebfced5ba6c27777",
    "weight": 5,
    "intentOptions": {
      "desiredProtocol": "nadfun"
    }
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
    "message": "Swap submitted",
    "batchId": "63946153-9f33-4b7e-9b32-b99a4a6037e2",
    "successful": 1,
    "failed": 0,
    "results": [
      {
        "smartAccount": "0xbaf3de56e5815e9b2894a95d85b8023c3ac03e4e",
        "result": {
          "success": true,
          "executeTxHash": "0x8bbaa0300777ec...",
          "explorerUrl": "https://monad-testnet.blockscout.com/tx/0x8..."
        }
      }
    ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt


# Perpetual Trading Guide

> Complete guide to opening and closing trades using the Symphony API

<Note>
  Perpetuals Trading is currently active on Base, Polygon, and Arbitrum. User's
  should start with \$USDC as their collateral asset
</Note>

## Perpetual Trading Guide

Complete guide to opening and closing trades using the Symphony API.

## Opening a Trade

This endpoint takes in a JSON object representing a batch trade that an agent wants to execute on behalf of all users that are subscribed to the agent. The amount of collateral used per user will depend on the weight of the trade on the JSON object. If a trigger price is set, an order will be opened on behalf of the user. If a trigger price is not set, a position will be opened on behalf of the user.

### Request Parameters

<ParamField body="agentId" type="string" required>
  Your AI fund's ID (UUID format)
</ParamField>

<ParamField body="symbol" type="string" required>
  The symbol of the asset you wish to trade (e.g., "SOL", "BTC")
</ParamField>

<ParamField body="action" type="string" required>
  The action you wish to take. Valid values: `LONG` or `SHORT`
</ParamField>

<ParamField body="weight" type="number" required>
  The weight of the trade (0-100). Determines the amount of collateral used per
  user
</ParamField>

<ParamField body="leverage" type="number" required>
  The leverage you wish to use. Minimum leverage is `1.1`
</ParamField>

<ParamField body="orderOptions" type="object">
  Optional order configuration object

  <Expandable title="orderOptions properties">
    * `triggerPrice` (number, optional): Price at which the trade will be
      executed. If set, an order will be opened. If not set (0), a position will
      be opened - `stopLossPrice` (number, optional): Stop loss price -
      `takeProfitPrice` (number, optional): Take profit price
  </Expandable>
</ParamField>

> **Note:** The minimum trade size is 5 USDC.

### Response

<ResponseField name="message" type="string">
  Status message indicating the batch open trade was submitted
</ResponseField>

<ResponseField name="batchId" type="string">
  Unique batch identifier (UUID format) for closing positions later
</ResponseField>

<ResponseField name="successful" type="number">
  Number of successful trades
</ResponseField>

<ResponseField name="failed" type="number">
  Number of failed trades
</ResponseField>

<ResponseField name="results" type="array">
  Array of trade results for each user

  <Expandable title="results">
    <ResponseField name="smartAccount" type="string">
      User's smart account address
    </ResponseField>

    <ResponseField name="result" type="object">
      Trade execution result

      <Expandable title="result">
        <ResponseField name="success" type="boolean">
          Whether the trade was successful
        </ResponseField>

        <ResponseField name="protocolOrderHash" type="string" nullable>
          Protocol order hash (may be null if position was opened directly)
        </ResponseField>

        <ResponseField name="protocolPositionHash" type="string" nullable>
          Protocol position hash (if position opened, may be null if order was
          created)
        </ResponseField>

        <ResponseField name="symphonyPositionHash" type="string">
          Symphony position hash
        </ResponseField>

        <ResponseField name="intentHash" type="string">
          Intent hash
        </ResponseField>

        <ResponseField name="srcChainId" type="number">
          Source chain ID
        </ResponseField>

        <ResponseField name="submitTxHash" type="string">
          Transaction hash for submission
        </ResponseField>

        <ResponseField name="submitExplorerUrl" type="string">
          Explorer URL for submit transaction
        </ResponseField>

        <ResponseField name="dstChainId" type="number">
          Destination chain ID
        </ResponseField>

        <ResponseField name="executeTxHash" type="string">
          Transaction hash for execution
        </ResponseField>

        <ResponseField name="executeExplorerUrl" type="string">
          Explorer URL for execute transaction
        </ResponseField>

        <ResponseField name="adjustedFansToAdd" type="number">
          Number of adjusted fans to add
        </ResponseField>

        <ResponseField name="newFanCount" type="number">
          New fan count after the trade
        </ResponseField>
      </Expandable>
    </ResponseField>
  </Expandable>
</ResponseField>

### Authentication

B2B JWT token OR Symphony API key

### Headers

When using Symphony API key, include the following header:

* `x-api-key`: Symphony API key

<RequestExample>
  ```json  theme={null}
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
</RequestExample>

<ResponseExample>
  ```json  theme={null}
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
</ResponseExample>

## Closing a Trade

**Endpoint:** `POST /agent/batch-close`

This endpoint takes in an `agentId` and `batchId` and closes all the orders and/or positions for the given `batchId` for the AI fund.

### Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="batchId" type="string" required>
  The batch ID from a previous batch open trade
</ParamField>

### Response

<ResponseField name="message" type="string">
  Status message
</ResponseField>

<ResponseField name="batchId" type="string">
  The batch ID that was closed
</ResponseField>

<ResponseField name="successful" type="number">
  Number of successfully closed positions
</ResponseField>

<ResponseField name="skipped" type="number">
  Number of skipped positions (already closed)
</ResponseField>

<ResponseField name="failed" type="number">
  Number of failed closures
</ResponseField>

<ResponseField name="results" type="array">
  Array of close results for each position

  <Expandable title="results">
    <ResponseField name="smartAccount" type="string">
      User's smart account address
    </ResponseField>

    <ResponseField name="result" type="object">
      Close execution result

      <Expandable title="result">
        <ResponseField name="txHash" type="string">
          Transaction hash
        </ResponseField>

        <ResponseField name="chainId" type="number">
          Chain ID
        </ResponseField>

        <ResponseField name="success" type="boolean">
          Whether the close was successful
        </ResponseField>

        <ResponseField name="skipped" type="boolean">
          Whether the position was skipped (already closed)
        </ResponseField>

        <ResponseField name="message" type="string">
          Status message (if skipped)
        </ResponseField>
      </Expandable>
    </ResponseField>
  </Expandable>
</ResponseField>

### Authentication

B2B JWT token OR Symphony API key

### Headers

When using Symphony API key, include the following header:

* `x-api-key`: Symphony API key

<RequestExample>
  ```json  theme={null}
  {
    "agentId": "63946153-9f33-4b7e-9b32-b99a4a6037e2",
    "batchId": "5cb80fd9-e820-4343-9d23-e1fca2951def"
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
    "message": "Batch close trade submitted",
    "batchId": "629373ff-6473-49b9-8357-ac59fa9b6341",
    "successful": 9,
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
      },
      {
        "smartAccount": "0x2cd40dfcc2bbf13539ec7f961cb5fee8d4cb924c",
        "result": {
          "success": true,
          "skipped": true,
          "message": "Skipped closed trade"
        }
      }
    ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Introduction

> Symphony API Reference Documentation

## Base URLs

Symphony API is available in two environments:

* **Development**: Contact the Symphony team for the testing environment details
* **Production**: `https://api.symphony.io/`

## Authentication

Symphony support three types of authentication:

* JWT Token for Business Integrations
* Privy Authentication
* Symphony API Keys

### Symphony API Key

Trading endpoints (like batch trading operations) use Symphony API Key authentication. Include your API key in the request headers as shown below. Generate your API key [here](https://app.symphony.io/developers/api-keys).

```bash  theme={null}
x-api-key: YOUR_API_KEY
```

Example using cURL:

```bash  theme={null}
curl -X POST 'https://api.symphony.io/agent/batch-open' \
  -H 'x-api-key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{...}'
```

### Privy Auth

Most endpoints use Privy authentication. You'll need to provide:

* `privyIdToken`: Privy ID token (sent as header `x-privy-id-token`)
* `privyAuthToken`: Privy authentication token (sent as Bearer token)

Include these tokens in the request headers:

```bash  theme={null}
x-privy-id-token: YOUR_PRIVY_ID_TOKEN
Authorization: Bearer YOUR_PRIVY_AUTH_TOKEN
```

Example using cURL:

```bash  theme={null}
curl -X POST 'https://api.symphony.io/endpoint' \
  -H 'x-privy-id-token: YOUR_PRIVY_ID_TOKEN' \
  -H 'Authorization: Bearer YOUR_PRIVY_AUTH_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{...}'
```

Check each endpoint's documentation for the specific authentication method required.


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Symphony Wallet

This endpoint is used to retrieve (or automatically create) the Symphony smart account associated with a given externally owned wallet address. The `wallet` address must be provided as a query parameter.

## Authentication

None required.

## Query Parameters

<ParamField query="wallet" type="string" required>
  The EOA wallet address for which a Symphony smart account should be returned
  or created
</ParamField>

## Response

<ResponseField name="address" type="string">
  The Symphony smart account address associated with the provided wallet
</ResponseField>

<ResponseExample>
  ```json  theme={null}
  {
      "address": "0xF41649acB63d15DdA455fBA6B0bD6576E9F1920d"
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Link Proxy

This endpoint links a proxy address to a privy EOA and Symphony wallet. This route must be called before using JWT auth with proxy address header on trade routes.

## Authentication

B2B JWT Token

## Headers

<ParamField header="x-proxy-address" type="string" required>
  The proxy address to be linked
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation
</ResponseField>

<ResponseField name="message" type="string">
  Description of the result
</ResponseField>

<ResponseField name="proxyAddress" type="string">
  The linked proxy address
</ResponseField>

<ResponseField name="walletAddress" type="string">
  The associated wallet address
</ResponseField>

<ResponseField name="smartAccount" type="string">
  The Symphony smart account address
</ResponseField>

<ResponseField name="privyUserId" type="string">
  The Privy user ID
</ResponseField>

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "message": "Proxy address linked",
      "proxyAddress": "0xb4260d5930cca681a0acc5149ecd8bb9c66b78af",
      "walletAddress": "0xbb748394764405a37c331b689db6e4d2b5d3eaea",
      "smartAccount": "0xf88d4321e2e677431ae6266554e77304409b80d0",
      "privyUserId": "did:privy:cmg9o5f260022kz0dwz51wtgv"
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Link Proxy

This endpoint links a proxy address to a privy EOA and Symphony wallet. This route must be called before using JWT auth with proxy address header on trade routes.

## Authentication

B2B JWT Token

## Headers

<ParamField header="x-proxy-address" type="string" required>
  The proxy address to be linked
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation
</ResponseField>

<ResponseField name="message" type="string">
  Description of the result
</ResponseField>

<ResponseField name="proxyAddress" type="string">
  The linked proxy address
</ResponseField>

<ResponseField name="walletAddress" type="string">
  The associated wallet address
</ResponseField>

<ResponseField name="smartAccount" type="string">
  The Symphony smart account address
</ResponseField>

<ResponseField name="privyUserId" type="string">
  The Privy user ID
</ResponseField>

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "message": "Proxy address linked",
      "proxyAddress": "0xb4260d5930cca681a0acc5149ecd8bb9c66b78af",
      "walletAddress": "0xbb748394764405a37c331b689db6e4d2b5d3eaea",
      "smartAccount": "0xf88d4321e2e677431ae6266554e77304409b80d0",
      "privyUserId": "did:privy:cmg9o5f260022kz0dwz51wtgv"
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Close Perpetuals Trade

This endpoint is called to close an existing position.

## Authentication

This endpoint supports two authentication methods:

**Option 1: Privy Authentication**

* Include a Bearer token with the Privy authentication token in the `Authorization` header

**Option 2: B2B JWT Token**

* Include the B2B JWT token in the `Authorization` header
* Include the `x-proxy-address` header with the proxy address to be linked

## Request Parameters

<ParamField body="protocolPositionHash" type="string" required>
  The protocol position hash of the position to close
</ParamField>

<ParamField body="symphonyPositionHash" type="string" required>
  The Symphony position hash of the position to close
</ParamField>

<ParamField body="userAddress" type="string">
  The user's wallet address (only required when using Privy authentication)
</ParamField>

## Response

<ResponseField name="txHash" type="string">
  Transaction hash for the close operation
</ResponseField>

<RequestExample>
  ```json  theme={null}
  {
      "protocolPositionHash": "0xc1d0dded638c23caf8...",
      "symphonyPositionHash": "0x84ae0e570e03cd2a31...",
      "userAddress": "0x2FBE9660bCD32A6C73545cAa4e9284BAd1027D29"
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "txHash": "0xecc6fb3bc4519..."
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Close Order

This endpoint is called to close an existing order.

## Authentication

This endpoint supports two authentication methods:

**Option 1: Privy Authentication**

* Include a Bearer token with the Privy authentication token in the `Authorization` header

**Option 2: B2B JWT Token**

* Include the B2B JWT token in the `Authorization` header
* Include the `x-proxy-address` header with the proxy address to be linked

## Request Parameters

<ParamField body="protocolOrderHash" type="string" required>
  The protocol order hash of the order to close
</ParamField>

<ParamField body="symphonyPositionHash" type="string" required>
  The Symphony position hash associated with the order
</ParamField>

<ParamField body="userAddress" type="string">
  The user's wallet address (only required when using Privy authentication)
</ParamField>

## Response

<ResponseField name="txHash" type="string">
  Transaction hash for the close operation
</ResponseField>

<RequestExample>
  ```json  theme={null}
  {
      "protocolOrderHash": "0xc1d0dded638c23caf8...",
      "symphonyPositionHash": "0x84ae0e570e03cd2a31...",
      "userAddress": "0x2FBE9660bCD32A6C73545cAa4e9284BAd1027D29"
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "txHash": "0xecc6fb3bc4519..."
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Update Order Options

This endpoint is called to update the trigger price, stop loss price, or take profit price of an existing order or trade. Note that trigger price is only available for orders.

## Authentication

This endpoint supports two authentication methods:

**Option 1: Privy Authentication**

* Include a Bearer token with the Privy authentication token in the `Authorization` header
* When using this method, the `wallet` parameter is required in the request body

**Option 2: B2B JWT Token**

* Include the B2B JWT token in the `Authorization` header
* Include the `x-proxy-address` header with the proxy address to be linked

## Request Parameters

<ParamField body="protocolPositionHash" type="string" required>
  The protocol position hash of the position/order to update
</ParamField>

<ParamField body="symphonyPositionHash" type="string" required>
  The Symphony position hash of the position/order to update
</ParamField>

<ParamField body="userAddress" type="string">
  The user's wallet address (only required when using Privy authentication)
</ParamField>

<ParamField body="wallet" type="string">
  The user's privy EOA address (only required when using Privy authentication)
</ParamField>

<ParamField body="orderOptions" type="object" required>
  The order options to update

  <Expandable title="orderOptions properties">
    * `triggerPrice` (number): Trigger price (only available for orders, not
      positions) - `takeProfitPrice` (number): Take profit price - `stopLossPrice`
      (number): Stop loss price
  </Expandable>
</ParamField>

## Response

<ResponseField name="txHash" type="string">
  Transaction hash for the update operation
</ResponseField>

<ResponseField name="chain" type="number">
  The chain ID where the transaction was executed
</ResponseField>

<ResponseField name="explorerUrl" type="string">
  Explorer URL for the transaction
</ResponseField>

<RequestExample>
  ```json  theme={null}
  {
      "protocolPositionHash": "0xcaacc0e337e4d4e1ac190535e1a80b6a44a1f2fa124574afd5a08dca766e8669",
      "symphonyPositionHash": "0x26c95affad35f26f2126c5de99712e7f2d93963bbd8068a86208efe82bff1fde",
      "userAddress": "0x2FBE9660bCD32A6C73545cAa4e9284BAd1027D29",
      "wallet": "0xFE1b64944787061e414497F86F9d84F6B9d6bDB7",
      "orderOptions": {
          "triggerPrice": 110,
          "takeProfitPrice": 130,
          "stopLossPrice": 90
      }
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "txHash": "0x2d8421...",
      "chain": 42161,
      "explorerUrl": "https://arbiscan.io/tx/0x2d8421..."
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Spot Trade

This endpoint executes a token swap for a user. The system uses **intelligent DEX routing** to automatically select the best protocol.

## Authentication

This endpoint supports two authentication methods:

**Option 1: Privy Authentication**

* Include a Bearer token with the Privy authentication token in the `Authorization` header
* When using this method, `symphonyWallet` and `wallet` parameters are required in the request body

**Option 2: B2B JWT Token**

* Include the B2B JWT token in the `Authorization` header
* Include the `x-proxy-address` header with the proxy address to be linked

## Request Parameters

<ParamField body="amount" type="string" required>
  The amount of input token to swap
</ParamField>

<ParamField body="tokenIn" type="object" required>
  The input token details

  <Expandable title="tokenIn properties">
    * `chain` (number): The chain ID (e.g., 42161 for Arbitrum) - `sid`
      (number): The Symphony token ID
  </Expandable>
</ParamField>

<ParamField body="tokenOut" type="string" required>
  The output token symbol or address (e.g., "USDC", "MON", or contract address)
</ParamField>

<ParamField body="dstChainId" type="number" required>
  The destination chain ID for the swap
</ParamField>

<ParamField body="symphonyWallet" type="string">
  The user's Symphony smart account address (only required when using Privy
  authentication)
</ParamField>

<ParamField body="wallet" type="string">
  The user's privy EOA address (only required when using Privy authentication)
</ParamField>

<ParamField body="intentOptions" type="object">
  Optional intent configuration object

  <Expandable title="intentOptions properties">
    * `desiredProtocol` (string): Desired protocol for the swap (e.g., "kuru",
      "nadfun")
  </Expandable>
</ParamField>

## Response

<ResponseField name="success" type="boolean">
  Whether the swap was successful
</ResponseField>

<ResponseField name="intentHash" type="string">
  Intent hash
</ResponseField>

<ResponseField name="srcChainId" type="number">
  Source chain ID
</ResponseField>

<ResponseField name="submitTxHash" type="string">
  Transaction hash for submission
</ResponseField>

<ResponseField name="submitExplorerUrl" type="string">
  Explorer URL for submit transaction
</ResponseField>

<ResponseField name="dstChainId" type="number">
  Destination chain ID
</ResponseField>

<ResponseField name="executeTxHash" type="string">
  Transaction hash for execution
</ResponseField>

<ResponseField name="executeExplorerUrl" type="string">
  Explorer URL for execute transaction
</ResponseField>

<RequestExample>
  ```json  theme={null}
  {
      "amount": "10",
      "tokenIn": {
          "chain": 42161,
          "sid": 6
      },
      "tokenOut": "0x350035555e10d9afaf1566aaebfced5ba6c27777",
      "dstChainId": 42161,
      "symphonyWallet": "0xbaf3de56e5815...",
      "wallet": "0xF0517A2d0C90E5D...",
      "intentOptions": {
          "desiredProtocol": "nadfun"
      }
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "success": true,
      "intentHash": "0x443181976042a4e16e85f5e7aed9e2c69c91d3467ac620e88b12fd47b5b8c2e2",
      "srcChainId": 42161,
      "submitTxHash": "0x199fce4526b987cc6b63c8bbab3ac39d4d8817db6551dd8951848e1913e9c8e5",
      "submitExplorerUrl": "https://arbiscan.io/tx/0x199fce4526b987cc6b63c8bbab3ac39d4d8817db6551dd8951848e1913e9c8e5",
      "dstChainId": 42161,
      "executeTxHash": "0x199fce4526b987cc6b63c8bbab3ac39d4d8817db6551dd8951848e1913e9c8e5",
      "executeExplorerUrl": "https://arbiscan.io/tx/0x199fce4526b987cc6b63c8bbab3ac39d4d8817db6551dd8951848e1913e9c8e5"
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Register Agent

This endpoint is used to register a new agent with a given ID (uuidv4) and public key. The agent is stored in our internal database and then used to generate a new 2/2 threshold quorum signing policy on Privy along with our internal backend B2B key.

## Request Parameters

<ParamField body="agentId" type="string">
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="name" type="string">
  Optional name for the agent
</ParamField>

<ParamField body="description" type="string">
  Optional description for the agent
</ParamField>

<ParamField body="imageUrl" type="string">
  Optional image URL for the agent
</ParamField>

<ParamField body="agentType" type="string">
  Optional agent type. Valid values: `PERPETUAL`, `SWAP` (defaults to
  `PERPETUAL`)
</ParamField>

<ParamField body="isPublic" type="boolean">
  Optional flag to make the agent public. Defaults to `false`
</ParamField>

<ParamField body="agentFees" type="object">
  Optional fee configuration object

  <Expandable title="agentFees properties">
    * `owner_flat` (object, optional): Flat fee configuration - `fee` (number):
      Flat fee amount - `feeAddress` (string): Address to receive the fee - `type`
      (string): Fee type, must be `"FLAT"` - `owner_bps` (object, optional): Basis
      points fee configuration - `fee` (number): Fee in basis points -
      `feeAddress` (string): Address to receive the fee - `type` (string): Fee
      type, must be `"BPS"`
  </Expandable>
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation (e.g., "success")
</ResponseField>

<ResponseField name="message" type="string">
  Success message indicating the agent was registered successfully
</ResponseField>

<ResponseField name="agentId" type="string">
  The registered agent ID (UUID format)
</ResponseField>

<ResponseField name="isPublic" type="string">
  Whether the agent is public ("true" or "false" as string)
</ResponseField>

<ResponseField name="organization" type="string">
  The organization identifier associated with the agent
</ResponseField>

<ResponseField name="ownerId" type="string" nullable>
  The owner ID. May be null if not set
</ResponseField>

<ResponseField name="manager" type="string" nullable>
  The manager address. May be null if not set
</ResponseField>

<ResponseField name="quorumId" type="string">
  The Privy quorum ID created for this agent's 2/2 threshold signing policy
</ResponseField>

<ResponseField name="agentType" type="string">
  The agent type (e.g., "PERPETUAL")
</ResponseField>

<ResponseField name="imageUrl" type="string">
  The image URL for the agent (if provided)
</ResponseField>

<ResponseField name="feeData" type="array">
  Array of fee configuration objects that were set for the agent

  <Expandable title="feeData">
    <ResponseField name="partner" type="string">
      Fee partner identifier (e.g., "owner\_flat", "owner\_bps")
    </ResponseField>

    <ResponseField name="fee" type="number">
      Fee amount (flat fee or basis points depending on feeType)
    </ResponseField>

    <ResponseField name="feeAddress" type="string">
      Ethereum address to receive the fee
    </ResponseField>

    <ResponseField name="feeType" type="string">
      Fee type: "flat" for flat fees or "bps" for basis points
    </ResponseField>
  </Expandable>
</ResponseField>

## Behavior

* Stores agent metadata internally
* Creates a new 2/2 threshold quorum signing policy on Privy with the agent's public key and Symphony's internal backend B2B key

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "337c2c59-ae4a-477c-9771-e66de0fdd669",
      "name": "New Agent",
      "description": "New Description",
      "imageUrl": "https://example.com/image.png",
      "agentType": "PERPETUAL",
      "isPublic": true,
      "agentFees": {
          "owner_flat": {
              "fee": 0.1,
              "feeAddress": "0x56d0573c786d3...",
              "type": "FLAT"
          },
          "owner_bps": {
              "fee": 5,
              "feeAddress": "0x56d0573c786d3...",
              "type": "BPS"
          }
      }
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "message": "Agent registered successfully",
      "agentId": "337c2c59-ae4a-477c-9771-e66de0fdd669",
      "isPublic": "true",
      "organization": "Symphony",
      "ownerId": null,
      "manager": null,
      "quorumId": "vn85nat05jx7rg45uyjntj9d",
      "agentType": "PERPETUAL",
      "imageUrl": "https://example.com/image.png",
      "feeData": [
          {
              "partner": "owner_flat",
              "fee": 0.1,
              "feeAddress": "0x56d0573c786d3...",
              "feeType": "flat"
          },
          {
              "partner": "owner_bps",
              "fee": 5,
              "feeAddress": "0x56d0573c786d3...",
              "feeType": "bps"
          }
      ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Unregister Agent

This endpoint is used to unregister an agent with a given ID (uuidv4). The agent is removed from our internal database.

## Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent to unregister (UUID format)
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation (e.g., "success")
</ResponseField>

<ResponseField name="message" type="string">
  Success message indicating the agent was unregistered successfully
</ResponseField>

<ResponseField name="agentId" type="string">
  The unregistered agent ID (UUID format)
</ResponseField>

## Behavior

* Removes the agent from our internal database

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "337c2c59-ae4a-477c-9771-e66de0fdd668"
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "message": "Agent unregistered successfully",
      "agentId": "fff21854-32cb-4082-a219-48ae1a9d5313"
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Update Agent Name

This endpoint is used to update the name of an agent.

## Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="name" type="string" required>
  The new name for the agent
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation (e.g., "success")
</ResponseField>

<ResponseField name="message" type="string">
  Success message indicating the agent name was updated
</ResponseField>

<ResponseField name="agentId" type="string">
  The agent ID that was updated (UUID format)
</ResponseField>

<ResponseField name="name" type="string">
  The updated agent name
</ResponseField>

## Behavior

* Updates the name for the specified agent in our internal database

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "name": "New Name"
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "message": "Agent 2fe35eeb-5aa6-4564-94c2-2ce44e65625d name updated",
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "name": "New Name"
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Update Agent Description

This endpoint is used to update the description of an agent.

## Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="description" type="string" required>
  The new description for the agent
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation (e.g., "success")
</ResponseField>

<ResponseField name="message" type="string">
  Success message indicating the agent description was updated
</ResponseField>

<ResponseField name="agentId" type="string">
  The agent ID that was updated (UUID format)
</ResponseField>

<ResponseField name="description" type="string">
  The updated agent description
</ResponseField>

## Behavior

* Updates the description for the specified agent in our internal database

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "description": "New Description"
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "message": "Agent 2fe35eeb-5aa6-4564-94c2-2ce44e65625d description updated",
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "description": "New Description"
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Update Agent Image

This endpoint is used to update the image URL of an agent.

## Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="imageUrl" type="string" required>
  The new image URL for the agent
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation (e.g., "success")
</ResponseField>

<ResponseField name="message" type="string">
  Success message indicating the agent image URL was updated
</ResponseField>

<ResponseField name="agentId" type="string">
  The agent ID that was updated (UUID format)
</ResponseField>

<ResponseField name="imageUrl" type="string">
  The updated agent image URL
</ResponseField>

## Behavior

* Updates the image URL for the specified agent in our internal database

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "imageUrl": "https://example.com/image.png"
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "message": "Agent 2fe35eeb-5aa6-4564-94c2-2ce44e65625d image URL updated",
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "imageUrl": "https://example.com/image.png"
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Update Agent Manager

This endpoint is used to update the manager address of an agent.

## Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="managerAddress" type="string" required>
  The new manager Ethereum address
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation (e.g., "success")
</ResponseField>

<ResponseField name="message" type="string">
  Success message indicating the agent manager was updated
</ResponseField>

<ResponseField name="agentId" type="string">
  The agent ID that was updated (UUID format)
</ResponseField>

<ResponseField name="managerAddress" type="string">
  The new manager Ethereum address
</ResponseField>

## Behavior

* Updates the manager address for the specified agent in our internal database

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "managerAddress": "0x56d0573c786d3..."
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "message": "Agent 2fe35eeb-5aa6-4564-94c2-2ce44e65625d manager updated",
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "managerAddress": "0x56d0573c786d3..."
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Update Agent Public

This endpoint is used to update the public status of an agent.

## Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="isPublic" type="boolean" required>
  The new public status for the agent
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation (e.g., "success")
</ResponseField>

<ResponseField name="message" type="string">
  Success message indicating the agent public status was updated
</ResponseField>

<ResponseField name="agentId" type="string">
  The agent ID that was updated (UUID format)
</ResponseField>

<ResponseField name="isPublic" type="boolean">
  The updated agent public status
</ResponseField>

## Behavior

* Updates the public status for the specified agent in our internal database

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "isPublic": true
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "message": "Agent 2fe35eeb-5aa6-4564-94c2-2ce44e65625d public status updated",
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "isPublic": true
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Update Agent Info

This endpoint is used to update the info of an agent all at once.

## Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="name" type="string">
  Optional new name for the agent
</ParamField>

<ParamField body="description" type="string">
  Optional new description for the agent
</ParamField>

<ParamField body="imageUrl" type="string">
  Optional new image URL for the agent
</ParamField>

<ParamField body="isPublic" type="boolean">
  Optional new public status for the agent. Accepts `true`, `false`, or `"true"` as string
</ParamField>

<ParamField body="agentFees" type="object">
  Optional fee configuration object

  <Expandable title="agentFees properties">
    * `self` (object, optional): Fee configuration for self
      * `fee` (number): Fee amount (flat fee or basis points depending on type)
      * `feeAddress` (string): Address to receive the fee
      * `type` (string): Fee type, must be `"FLAT"` or `"BPS"`
    * `owner_flat` (object, optional): Flat fee configuration
      * `fee` (number): Flat fee amount
      * `feeAddress` (string): Address to receive the fee
      * `type` (string): Fee type, must be `"FLAT"`
    * `owner_bps` (object, optional): Basis points fee configuration
      * `fee` (number): Fee in basis points
      * `feeAddress` (string): Address to receive the fee
      * `type` (string): Fee type, must be `"BPS"`
  </Expandable>
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation (e.g., "success")
</ResponseField>

<ResponseField name="message" type="string">
  Success message indicating the agent was updated successfully
</ResponseField>

<ResponseField name="agentId" type="string">
  The agent ID that was updated (UUID format)
</ResponseField>

<ResponseField name="name" type="string">
  The updated agent name (if provided)
</ResponseField>

<ResponseField name="description" type="string">
  The updated agent description (if provided)
</ResponseField>

<ResponseField name="imageUrl" type="string">
  The updated agent image URL (if provided)
</ResponseField>

<ResponseField name="isPublic" type="boolean">
  The updated agent public status (if provided)
</ResponseField>

<ResponseField name="feeData" type="array">
  Array of fee configuration objects that were set for the agent

  <Expandable title="feeData">
    <ResponseField name="partner" type="string">
      Fee partner identifier (e.g., "self", "owner\_flat", "owner\_bps")
    </ResponseField>

    <ResponseField name="fee" type="number">
      Fee amount (flat fee or basis points depending on feeType)
    </ResponseField>

    <ResponseField name="feeAddress" type="string">
      Ethereum address to receive the fee
    </ResponseField>

    <ResponseField name="feeType" type="string">
      Fee type: "FLAT" for flat fees or "BPS" for basis points
    </ResponseField>
  </Expandable>
</ResponseField>

## Behavior

* Updates the specified agent information in our internal database
* Allows updating multiple fields at once (name, description, imageUrl, isPublic, agentFees)

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "name": "New Name",
      "description": "New Description",
      "imageUrl": "https://example.com/image.png",
      "isPublic": true,
      "agentFees": {
          "self": {
              "fee": 1.5,
              "feeAddress": "0x56d0573C786d3DB...",
              "type": "BPS"
          }
      }
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "message": "Agent 2fe35eeb-5aa6-4564-94c2-2ce44e65625d updated successfully",
      "agentId": "2fe35eeb-5aa6-4564-94c2-2ce44e65625d",
      "name": "New Name",
      "description": "New Description",
      "imageUrl": "https://example.com/image.png",
      "isPublic": true,
      "feeData": [
          {
              "partner": "self",
              "fee": 1.5,
              "feeAddress": "0x56d0573C786d3DB...",
              "feeType": "BPS"
          }
      ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Subscribe to Agent

This endpoint is used to subscribe a user to an agent with a given ID (uuidv4). This endpoint will link this user to the agent in our database and will add the quorum signing policy associated with the agent as an additional signer to the user's wallet on Privy.

## Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="privyIdToken" type="string">
  Privy ID token for authentication. NOT NEEDED FOR DEV PORTAL AGENTS
</ParamField>

<ParamField body="privyAuthToken" type="string">
  Privy authentication token. NOT NEEDED FOR DEV PORTAL AGENTS
</ParamField>

## Response

<ResponseField name="message" type="string">
  Status message indicating the quorum was added to the wallet
</ResponseField>

<ResponseField name="privyResponse" type="object">
  Privy wallet response object containing the updated wallet configuration

  <Expandable title="privyResponse">
    <ResponseField name="id" type="string">
      Privy wallet ID
    </ResponseField>

    <ResponseField name="address" type="string">
      Wallet Ethereum address
    </ResponseField>

    <ResponseField name="chain_type" type="string">
      Chain type (e.g., "ethereum")
    </ResponseField>

    <ResponseField name="policy_ids" type="array">
      Array of policy IDs
    </ResponseField>

    <ResponseField name="additional_signers" type="array">
      Array of additional signers including the agent's quorum signing policy

      <Expandable title="additional_signers">
        <ResponseField name="signer_id" type="string">
          The signer ID (quorum ID) for the agent
        </ResponseField>

        <ResponseField name="override_policy_ids" type="array">
          Array of override policy IDs
        </ResponseField>
      </Expandable>
    </ResponseField>

    <ResponseField name="exported_at" type="number" nullable>
      Timestamp when wallet was exported (may be null)
    </ResponseField>

    <ResponseField name="created_at" type="number">
      Timestamp when wallet was created
    </ResponseField>

    <ResponseField name="owner_id" type="string" nullable>
      Owner ID (may be null)
    </ResponseField>
  </Expandable>
</ResponseField>

## Behavior

* Links the user to the agent in our internal database
* Adds the quorum signing policy associated with the agent as an additional signer to the user's wallet on Privy

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "fff21854-32cb-4082-a219-48ae1a9d5313",
      "privyIdToken": "eyJhbGciOiJFU...",
      "privyAuthToken": "eyJhbGciOiJFU..."
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "message": "Quorum added to wallet",
      "privyResponse": {
          "id": "bh5nazejf4xt56a43vswzk1j",
          "address": "0x1a715565418b1538E0F51d8B826A4bE5340eAEAC",
          "chain_type": "ethereum",
          "policy_ids": [],
          "additional_signers": [
              {
                  "signer_id": "oygnr7h645h17ubpbr1xc4p0",
                  "override_policy_ids": []
              }
          ],
          "exported_at": null,
          "created_at": 1751573759530,
          "owner_id": null
      }
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Unsubscribe from Agent

This endpoint is used to unsubscribe a user from an agent with a given ID. This endpoint will remove the quorum signing policy associated with the agent from the user's wallet on Privy.

## Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="privyIdToken" type="string">
  Privy ID token for authentication. NOT NEEDED FOR DEV PORTAL AGENTS
</ParamField>

<ParamField body="privyAuthToken" type="string">
  Privy authentication token. NOT NEEDED FOR DEV PORTAL AGENTS
</ParamField>

## Response

<ResponseField name="message" type="string">
  Status message indicating the quorum was removed from the wallet
</ResponseField>

<ResponseField name="privyResponse" type="object">
  Privy wallet response object containing the updated wallet configuration

  <Expandable title="privyResponse">
    <ResponseField name="id" type="string">
      Privy wallet ID
    </ResponseField>

    <ResponseField name="address" type="string">
      Wallet Ethereum address
    </ResponseField>

    <ResponseField name="chain_type" type="string">
      Chain type (e.g., "ethereum")
    </ResponseField>

    <ResponseField name="policy_ids" type="array">
      Array of policy IDs
    </ResponseField>

    <ResponseField name="additional_signers" type="array">
      Array of additional signers (should be empty after unsubscribe as the agent's quorum has been removed)
    </ResponseField>

    <ResponseField name="exported_at" type="number" nullable>
      Timestamp when wallet was exported (may be null)
    </ResponseField>

    <ResponseField name="created_at" type="number">
      Timestamp when wallet was created
    </ResponseField>

    <ResponseField name="owner_id" type="string" nullable>
      Owner ID (may be null)
    </ResponseField>
  </Expandable>
</ResponseField>

## Behavior

* Removes the quorum signing policy associated with the agent from the user's wallet on Privy

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "fff21854-32cb-4082-a219-48ae1a9d5313",
      "privyIdToken": "eyJhbGciOiJFU...",
      "privyAuthToken": "eyJhbGciOiJFU..."
  }
  ```
</RequestExample>

<ResponseExample>
  ```json  theme={null}
  {
      "message": "Quorum removed from wallet",
      "privyResponse": {
          "id": "bh5nazejf4xt56a43vswzk1j",
          "address": "0x1a715565418b1538E0F51d8B826A4bE5340eAEAC",
          "chain_type": "ethereum",
          "policy_ids": [],
          "additional_signers": [],
          "exported_at": null,
          "created_at": 1751573759530,
          "owner_id": null
      }
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Agent Subscribers

This endpoint is used to get all the subscribers for an agent.

## Request Parameters

<ParamField query="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation (e.g., "success")
</ResponseField>

<ResponseField name="data" type="array">
  Array of subscriber objects

  <Expandable title="data">
    <ResponseField name="subscriber" type="string">
      Subscriber's smart account address
    </ResponseField>

    <ResponseField name="updatedTimestamp" type="string">
      ISO timestamp when subscription was last updated
    </ResponseField>
  </Expandable>
</ResponseField>

## Behavior

* Returns all subscribers (users) that are subscribed to the specified agent

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "data": [
          {
              "subscriber": "0xbaf3de56e5815e9b2894a95d85b8023c3ac03e4e",
              "updatedTimestamp": "2025-09-15T16:44:07.887Z"
          }
      ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Subscribed Agents

This endpoint is used to get all the agents that a user is subscribed to. It returns a list of all agents that the specified user has subscribed to, along with their subscription timestamps. The userAddress will default to the symphonyWallet of the developer if using Privy authentication.

## Request Parameters

<ParamField query="userAddress" type="string">
  The user's smart account address. Defaults to the symphonyWallet of the
  developer if using Privy authentication
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the operation (e.g., "success")
</ResponseField>

<ResponseField name="data" type="array">
  Array of agent subscription objects

  <Expandable title="data">
    <ResponseField name="agentId" type="string">
      The agent ID (UUID format)
    </ResponseField>

    <ResponseField name="timestamp" type="string">
      ISO timestamp when subscription was created
    </ResponseField>
  </Expandable>
</ResponseField>

## Behavior

* Returns all agents that the specified user (or authenticated developer) is subscribed to

## Authentication

B2B JWT token OR Privy authentication token and headers

## Headers

When using Privy authentication token, include the following header:

* `x-privy-id-token`: Privy ID token

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "data": [
          {
              "agentId": "f459697b-540f-4d79-b014-62f2e35d5151",
              "timestamp": "2025-09-15T16:44:07.887Z"
          },
          {
              "agentId": "c9b82ab1-bdb1-4529-b542-97c216ed8f83",
              "timestamp": "2025-09-09T19:51:23.859Z"
          }
      ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Open Perpetuals Trade

<Note>
  Perpetuals Trading is currently active on Base, Polygon, and Arbitrum. User's
  should start with \$USDC as their collateral asset
</Note>

This endpoint takes in a JSON object representing a batch trade that an agent wants to execute on behalf of all users that are subscribed to the agent. The amount of collateral used per user will depend on the weight of the trade on the JSON object. If a trigger price is set, an order will be opened on behalf of the user. If a trigger price is not set, a position will be opened on behalf of the user.

## Request Parameters

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="symbol" type="string" required>
  The trading symbol (e.g., "SOL", "BTC")
</ParamField>

<ParamField body="action" type="string" required>
  The trade action. Valid values: `LONG` or `SHORT`
</ParamField>

<ParamField body="weight" type="number" required>
  The percentage weight (0-100). Determines the amount of collateral used per user
</ParamField>

<ParamField body="leverage" type="number" required>
  The leverage amount. Minimum leverage is `1.1`
</ParamField>

<ParamField body="orderOptions" type="object">
  Optional order configuration object

  <Expandable title="orderOptions properties">
    * `triggerPrice` (number, optional): Trigger price for the order. If set, an order will be opened. If not set (0), a position will be opened
    * `stopLossPrice` (number, optional): Stop loss price
    * `takeProfitPrice` (number, optional): Take profit price
  </Expandable>
</ParamField>

## Response

<ResponseField name="message" type="string">
  Status message indicating the batch open trade was submitted
</ResponseField>

<ResponseField name="batchId" type="string">
  Unique batch identifier (UUID format) for closing positions later
</ResponseField>

<ResponseField name="successful" type="number">
  Number of successful trades
</ResponseField>

<ResponseField name="failed" type="number">
  Number of failed trades
</ResponseField>

<ResponseField name="results" type="array">
  Array of trade results for each user

  <Expandable title="results">
    <ResponseField name="smartAccount" type="string">
      User's smart account address
    </ResponseField>

    <ResponseField name="result" type="object">
      Trade execution result

      <Expandable title="result">
        <ResponseField name="success" type="boolean">
          Whether the trade was successful
        </ResponseField>

        <ResponseField name="protocolOrderHash" type="string" nullable>
          Protocol order hash (may be null if position was opened directly)
        </ResponseField>

        <ResponseField name="protocolPositionHash" type="string" nullable>
          Protocol position hash (if position opened, may be null if order was created)
        </ResponseField>

        <ResponseField name="symphonyPositionHash" type="string">
          Symphony position hash
        </ResponseField>

        <ResponseField name="intentHash" type="string">
          Intent hash
        </ResponseField>

        <ResponseField name="srcChainId" type="number">
          Source chain ID
        </ResponseField>

        <ResponseField name="submitTxHash" type="string">
          Transaction hash for submission
        </ResponseField>

        <ResponseField name="submitExplorerUrl" type="string">
          Explorer URL for submit transaction
        </ResponseField>

        <ResponseField name="dstChainId" type="number">
          Destination chain ID
        </ResponseField>

        <ResponseField name="executeTxHash" type="string">
          Transaction hash for execution
        </ResponseField>

        <ResponseField name="executeExplorerUrl" type="string">
          Explorer URL for execute transaction
        </ResponseField>

        <ResponseField name="adjustedFansToAdd" type="number">
          Number of adjusted fans to add
        </ResponseField>

        <ResponseField name="newFanCount" type="number">
          New fan count after the trade
        </ResponseField>
      </Expandable>
    </ResponseField>
  </Expandable>
</ResponseField>

## Behavior

* Executes the batch trade for all users subscribed to the specified agent
* The amount of collateral used per user depends on the weight parameter
* If `triggerPrice` is set in `orderOptions`, an order will be opened on behalf of the user
* If `triggerPrice` is not set (0), a position will be opened directly on behalf of the user
* Valid actions are `LONG` and `SHORT`
* Minimum leverage is `1.1`

## Authentication

B2B JWT token OR Symphony API key

## Headers

When using Symphony API key, include the following header:

* `x-api-key`: Symphony API key

<RequestExample>
  ```json  theme={null}
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
</RequestExample>

<ResponseExample>
  ```json  theme={null}
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
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt



# Close Perpetuals Trade

This endpoint takes in an agentId and batchId and closes all the orders and/or positions for the given batchId for the agent.

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="batchId" type="string" required>
  The batch ID from a previous batch open trade
</ParamField>

<ResponseField name="message" type="string">
  Status message
</ResponseField>

<ResponseField name="batchId" type="string">
  The batch ID that was closed
</ResponseField>

<ResponseField name="successful" type="number">
  Number of successfully closed positions
</ResponseField>

<ResponseField name="skipped" type="number">
  Number of skipped positions (already closed)
</ResponseField>

<ResponseField name="failed" type="number">
  Number of failed closures
</ResponseField>

<ResponseField name="results" type="array">
  Array of close results for each position

  <Expandable title="results">
    <ResponseField name="smartAccount" type="string">
      User's smart account address
    </ResponseField>

    <ResponseField name="result" type="object">
      Close execution result

      <Expandable title="result">
        <ResponseField name="txHash" type="string">
          Transaction hash
        </ResponseField>

        <ResponseField name="chainId" type="number">
          Chain ID
        </ResponseField>

        <ResponseField name="success" type="boolean">
          Whether the close was successful
        </ResponseField>

        <ResponseField name="skipped" type="boolean">
          Whether the position was skipped (already closed)
        </ResponseField>

        <ResponseField name="message" type="string">
          Status message (if skipped)
        </ResponseField>
      </Expandable>
    </ResponseField>
  </Expandable>
</ResponseField>

## Behavior

* Will attempt to close all positions in the batch
* If some positions fail to close they will NOT affect other positions from closing

## Authentication

B2B JWT token OR Symphony API key

## Headers

When using Symphony API key, include the following header:

* `x-api-key`: Symphony API key

## Request Example

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "63946153-9f33-4b7e-9b32-b99a4a6037e2",
      "batchId": "5cb80fd9-e820-4343-9d23-e1fca2951def"
  }
  ```
</RequestExample>

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "message": "Batch close trade submitted",
      "batchId": "629373ff-6473-49b9-8357-ac59fa9b6341",
      "successful": 9,
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
          },
          {
              "smartAccount": "0x2cd40dfcc2bbf13539ec7f961cb5fee8d4cb924c",
              "result": {
                  "success": true,
                  "skipped": true,
                  "message": "Skipped closed trade"
              }
          }
      ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Spot Trade

<Note>
  Spot Trading is currently only active on Monad and eligible for trading
  rewards. User's should start with \$MON as their collateral asset
</Note>

This endpoint executes a token swap on behalf of all users subscribed to an agent. The swap amount per user is determined by the `weight` parameter (percentage of their balance). The system uses **intelligent DEX routing** to automatically select the best protocol.

<ParamField body="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField body="tokenIn" type="string" required>
  The input token symbol (e.g., "MON", "USDC")
</ParamField>

<ParamField body="tokenOut" type="string" required>
  The output token symbol (e.g., "USDC", "MON")
</ParamField>

<ParamField body="weight" type="number" required>
  The percentage of user's balance to swap (0-100)
</ParamField>

<ParamField body="intentOptions" type="object">
  Optional intent configuration object

  <Expandable title="intentOptions properties">
    * `desiredProtocol` (string, optional): Desired protocol for the swap (e.g., "kuru")
  </Expandable>
</ParamField>

<ResponseField name="message" type="string">
  Status message
</ResponseField>

<ResponseField name="batchId" type="string">
  Batch identifier for this swap operation
</ResponseField>

<ResponseField name="successful" type="number">
  Number of successful swaps
</ResponseField>

<ResponseField name="failed" type="number">
  Number of failed swaps
</ResponseField>

<ResponseField name="results" type="array">
  Array of swap results for each user

  <Expandable title="results">
    <ResponseField name="smartAccount" type="string">
      User's smart account address
    </ResponseField>

    <ResponseField name="result" type="object">
      Swap execution result

      <Expandable title="result">
        <ResponseField name="success" type="boolean">
          Whether the swap was successful
        </ResponseField>

        <ResponseField name="executeTxHash" type="string">
          Transaction hash for execution
        </ResponseField>

        <ResponseField name="explorerUrl" type="string">
          Explorer URL for the transaction
        </ResponseField>
      </Expandable>
    </ResponseField>
  </Expandable>
</ResponseField>

## Behavior

* Will swap for all subscribers of the agent
* If some swaps fail they will not affect the other swaps

## Authentication

Symphony API Key

## Request Example

<RequestExample>
  ```json  theme={null}
  {
      "agentId": "e8a54723-6485-41b9-91d7-7bdfd61ba621",
      "tokenIn": "MON",
      "tokenOut": "0x350035555e10d9afaf1566aaebfced5ba6c27777",
      "weight": 5,
      "intentOptions": {
          "desiredProtocol": "nadfun"
      }
  }
  ```
</RequestExample>

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "message": "Swap submitted",
      "batchId": "63946153-9f33-4b7e-9b32-b99a4a6037e2",
      "successful": 1,
      "failed": 0,
      "results": [
          {
              "smartAccount": "0xbaf3de56e5815e9b2894a95d85b8023c3ac03e4e",
              "result": {
                  "success": true,
                  "executeTxHash": "0x8bbaa0300777ec...",
                  "explorerUrl": "https://monad-testnet.blockscout.com/tx/0x8..."
              }
          }
      ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Agent Batches

This endpoint is used to get all the batches for an agent. Each batch corresponds to a group of one or more trades that were opened by the agent at the same time. If the status of the batch is `OPEN` then the batch contains active orders and/or positions. If the status of the batch is `CLOSED` then the batch contains closed orders and/or positions.

<Note>
  It is possible for a batch to have a closed status and still contain active orders and/or positions. This can happen if one or more orders/positions failed to close for whatever reason. In this case the agent may call `batch-close` again to attempt to close any remaining orders/positions (orders/positions that are already closed will simply be skipped).
</Note>

<ParamField query="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ResponseField name="agentId" type="string">
  The agent ID
</ResponseField>

<ResponseField name="batches" type="array">
  Array of batch objects

  <Expandable title="batches">
    <ResponseField name="batchId" type="string">
      Unique batch identifier
    </ResponseField>

    <ResponseField name="status" type="string">
      Batch status: `OPEN` or `CLOSED`
    </ResponseField>

    <ResponseField name="createTimestamp" type="string">
      ISO timestamp when the batch was created
    </ResponseField>
  </Expandable>
</ResponseField>

## Authentication

Symphony API Key

## Response Example

<ResponseExample>
  ```json  theme={null}
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
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Batch Positions

This endpoint is used to get all the positions and/or orders for a given batch. Orders will be returned in the orders array and positions will be returned in the positions array. Normally trades will be either all orders or all positions, but in the rare case that some orders get executed while others do not, there can be a mix of orders and positions in the response.

<ParamField query="batchId" type="string" required>
  The batch ID to retrieve positions/orders for
</ParamField>

<ResponseField name="batchId" type="string">
  The batch ID
</ResponseField>

<ResponseField name="ordersCount" type="number">
  Number of orders in the batch
</ResponseField>

<ResponseField name="positionsCount" type="number">
  Number of positions in the batch
</ResponseField>

<ResponseField name="orders" type="array">
  Array of order objects (if any)
</ResponseField>

<ResponseField name="positions" type="array">
  Array of position objects

  <Expandable title="positions">
    <ResponseField name="smartAccount" type="string">
      User's smart account address
    </ResponseField>

    <ResponseField name="symphonyPositionHash" type="string">
      Symphony position hash
    </ResponseField>

    <ResponseField name="protocolPositionHash" type="string">
      Protocol position hash
    </ResponseField>

    <ResponseField name="status" type="string">
      Position status (e.g., "Open", "Closed")
    </ResponseField>

    <ResponseField name="collateralAmount" type="number">
      Collateral amount
    </ResponseField>

    <ResponseField name="pnlPercentage" type="number">
      Profit/loss percentage
    </ResponseField>

    <ResponseField name="pnlUSD" type="number">
      Profit/loss in USD
    </ResponseField>

    <ResponseField name="indexToken" type="string">
      Token symbol (e.g., "SOL")
    </ResponseField>

    <ResponseField name="leverage" type="number">
      Leverage used
    </ResponseField>
  </Expandable>
</ResponseField>

## Authentication

Symphony API Key

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "batchId": "dcb556b5-f81c-4401-b285-459664d4935a",
      "ordersCount": 0,
      "positionsCount": 10,
      "orders": [],
      "positions": [
          {
              "smartAccount": "0xbaf3de56e5815e9b2894a95d85b8023c3ac03e4e",
              "symphonyPositionHash": "0x0cc3ac3458...",
              "protocolPositionHash": "0x5b9c4e07f...",
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
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Agent Positions

This endpoint is used to get all the positions and/or orders for a given agent. Orders will be returned in the orders array and positions will be returned in the positions array. Status filter is optional, valid options are `OPEN`, `CLOSED`, and `LIQUIDATED`. Address filter is also optional.

<ParamField query="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ParamField query="status" type="string">
  Optional status filter: `OPEN`, `CLOSED`, or `LIQUIDATED`
</ParamField>

<ParamField query="address" type="string">
  Optional smart account address filter
</ParamField>

<ResponseField name="agentId" type="string">
  The agent ID
</ResponseField>

<ResponseField name="ordersCount" type="number">
  Number of orders
</ResponseField>

<ResponseField name="positionsCount" type="number">
  Number of positions
</ResponseField>

<ResponseField name="orders" type="array">
  Array of order objects

  <Expandable title="orders">
    <ResponseField name="batchId" type="string">
      Batch ID
    </ResponseField>

    <ResponseField name="smartAccount" type="string">
      Smart account address
    </ResponseField>

    <ResponseField name="symphonyPositionHash" type="string">
      Symphony position hash
    </ResponseField>

    <ResponseField name="protocolOrderHash" type="string">
      Protocol order hash
    </ResponseField>

    <ResponseField name="status" type="string">
      Order status
    </ResponseField>

    <ResponseField name="orderType" type="string">
      Order type
    </ResponseField>

    <ResponseField name="collateralAmount" type="number">
      Collateral amount
    </ResponseField>

    <ResponseField name="asset" type="string">
      Asset symbol
    </ResponseField>

    <ResponseField name="leverage" type="number">
      Leverage
    </ResponseField>

    <ResponseField name="positionSize" type="number">
      Position size
    </ResponseField>

    <ResponseField name="currentPrice" type="number">
      Current price
    </ResponseField>

    <ResponseField name="createdTimestamp" type="string">
      Creation timestamp
    </ResponseField>

    <ResponseField name="lastUpdatedTimestamp" type="string">
      Last update timestamp
    </ResponseField>
  </Expandable>
</ResponseField>

<ResponseField name="positions" type="array">
  Array of position objects

  <Expandable title="positions">
    <ResponseField name="batchId" type="string">
      Batch ID
    </ResponseField>

    <ResponseField name="smartAccount" type="string">
      Smart account address
    </ResponseField>

    <ResponseField name="symphonyPositionHash" type="string">
      Symphony position hash
    </ResponseField>

    <ResponseField name="protocolPositionHash" type="string">
      Protocol position hash
    </ResponseField>

    <ResponseField name="status" type="string">
      Position status
    </ResponseField>

    <ResponseField name="collateralAmount" type="number">
      Collateral amount
    </ResponseField>

    <ResponseField name="pnlPercentage" type="number">
      PnL percentage
    </ResponseField>

    <ResponseField name="pnlUSD" type="number">
      PnL in USD
    </ResponseField>

    <ResponseField name="asset" type="string">
      Asset symbol
    </ResponseField>

    <ResponseField name="isLong" type="boolean">
      Whether position is long
    </ResponseField>

    <ResponseField name="leverage" type="number">
      Leverage
    </ResponseField>

    <ResponseField name="positionSize" type="number">
      Position size
    </ResponseField>

    <ResponseField name="entryPrice" type="number">
      Entry price
    </ResponseField>

    <ResponseField name="currentPrice" type="number">
      Current price
    </ResponseField>

    <ResponseField name="slPrice" type="number">
      Stop loss price
    </ResponseField>

    <ResponseField name="tpPrice" type="number">
      Take profit price
    </ResponseField>

    <ResponseField name="liquidationPrice" type="number">
      Liquidation price
    </ResponseField>

    <ResponseField name="createdTimestamp" type="string">
      Creation timestamp
    </ResponseField>

    <ResponseField name="lastUpdatedTimestamp" type="string">
      Last update timestamp
    </ResponseField>
  </Expandable>
</ResponseField>

## Authentication

Privy Auth

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "agentId": "63946153-9f33-4b7e-9b32-b99a4a6037e2",
      "ordersCount": 39,
      "positionsCount": 93,
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
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Positions for Smart Account

This endpoint is used to get all the positions for a smart account in all states (Open, Closed, etc).

<ParamField query="address" type="string" required>
  The smart account address
</ParamField>

<ResponseField name="status" type="string">
  Status of the response
</ResponseField>

<ResponseField name="count" type="number">
  Number of positions
</ResponseField>

<ResponseField name="positions" type="array">
  Array of position objects

  <Expandable title="positions">
    <ResponseField name="smartAccount" type="string">
      Smart account address
    </ResponseField>

    <ResponseField name="symphonyPositionHash" type="string">
      Symphony position hash
    </ResponseField>

    <ResponseField name="protocolPositionHash" type="string">
      Protocol position hash
    </ResponseField>

    <ResponseField name="status" type="string">
      Position status (e.g., "Open", "Closed")
    </ResponseField>

    <ResponseField name="collateralAmount" type="number">
      Collateral amount
    </ResponseField>

    <ResponseField name="pnlPercentage" type="number">
      Profit/loss percentage
    </ResponseField>

    <ResponseField name="pnlUSD" type="number">
      Profit/loss in USD
    </ResponseField>

    <ResponseField name="asset" type="string">
      Asset symbol (e.g., "BTC", "SOL")
    </ResponseField>

    <ResponseField name="isLong" type="boolean">
      Whether position is long
    </ResponseField>

    <ResponseField name="leverage" type="number">
      Leverage used
    </ResponseField>

    <ResponseField name="positionSize" type="number">
      Position size
    </ResponseField>

    <ResponseField name="entryPrice" type="number">
      Entry price
    </ResponseField>

    <ResponseField name="currentPrice" type="number">
      Current price
    </ResponseField>

    <ResponseField name="slPrice" type="number">
      Stop loss price
    </ResponseField>

    <ResponseField name="tpPrice" type="number">
      Take profit price
    </ResponseField>

    <ResponseField name="liquidationPrice" type="number">
      Liquidation price
    </ResponseField>

    <ResponseField name="createdTimestamp" type="string">
      ISO timestamp when position was created
    </ResponseField>

    <ResponseField name="lastUpdatedTimestamp" type="string">
      ISO timestamp when position was last updated
    </ResponseField>
  </Expandable>
</ResponseField>

## Authentication

Privy Auth

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "count": 1,
      "positions": [
          {
              "smartAccount": "0xbaf3de56e5815...",
              "symphonyPositionHash": "0xd8c9d53c7f4ae83d9d656...",
              "protocolPositionHash": "0xc37ef3d2083e6b980a95a3b6...",
              "status": "Open",
              "collateralAmount": 8.17440814962472,
              "pnlPercentage": -10.368789036230615,
              "pnlUSD": -0.8475871359950299,
              "asset": "BTC",
              "isLong": true,
              "leverage": 5,
              "positionSize": 40.8720407481236,
              "entryPrice": 115170.4563297798,
              "currentPrice": 112782.09999999999,
              "slPrice": 0,
              "tpPrice": 0,
              "liquidationPrice": 97965.05584798902,
              "createdTimestamp": "2025-10-28T18:23:05.156Z",
              "lastUpdatedTimestamp": "2025-10-28T20:44:50.539Z"
          }
      ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Orders for Smart Account

This endpoint is used to get all the orders for a smart account in all states (Open, Executed, etc).

<ParamField query="address" type="string" required>
  The smart account address
</ParamField>

<ResponseField name="status" type="string">
  Status of the response
</ResponseField>

<ResponseField name="count" type="number">
  Number of orders
</ResponseField>

<ResponseField name="orders" type="array">
  Array of order objects

  <Expandable title="orders">
    <ResponseField name="smartAccount" type="string">
      Smart account address
    </ResponseField>

    <ResponseField name="symphonyPositionHash" type="string">
      Symphony position hash
    </ResponseField>

    <ResponseField name="protocolOrderHash" type="string">
      Protocol order hash
    </ResponseField>

    <ResponseField name="status" type="string">
      Order status (e.g., "executed", "open")
    </ResponseField>

    <ResponseField name="orderType" type="string">
      Order type
    </ResponseField>

    <ResponseField name="collateralAmount" type="number">
      Collateral amount
    </ResponseField>

    <ResponseField name="asset" type="string">
      Asset symbol (e.g., "BTC", "SOL")
    </ResponseField>

    <ResponseField name="leverage" type="number">
      Leverage used
    </ResponseField>

    <ResponseField name="isLong" type="boolean">
      Whether order is for long position
    </ResponseField>

    <ResponseField name="positionSize" type="number">
      Position size
    </ResponseField>

    <ResponseField name="currentPrice" type="number">
      Current price
    </ResponseField>

    <ResponseField name="orderOptions" type="object">
      Order options

      <Expandable title="orderOptions">
        <ResponseField name="stopLossPrice" type="number">
          Stop loss price
        </ResponseField>

        <ResponseField name="takeProfitPrice" type="number">
          Take profit price
        </ResponseField>

        <ResponseField name="triggerPrice" type="number">
          Trigger price
        </ResponseField>
      </Expandable>
    </ResponseField>

    <ResponseField name="createdTimestamp" type="string">
      ISO timestamp when order was created
    </ResponseField>

    <ResponseField name="lastUpdatedTimestamp" type="string">
      ISO timestamp when order was last updated
    </ResponseField>
  </Expandable>
</ResponseField>

## Authentication

Privy Auth

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "count": 1,
      "orders": [
          {
              "smartAccount": "0xbaf3de56e5815e9b2894a...",
              "symphonyPositionHash": "0x2ff3e42d656b48a...",
              "protocolOrderHash": "0x98a1a48697069eae490646...",
              "status": "executed",
              "orderType": "1",
              "collateralAmount": 9.020422,
              "asset": "BTC",
              "leverage": 5,
              "isLong": true,
              "positionSize": 45.10211,
              "currentPrice": 112786.99999999999,
              "orderOptions": {
                  "stopLossPrice": 105000,
                  "takeProfitPrice": 120000,
                  "triggerPrice": 109999.99999999999
              },
              "createdTimestamp": "2025-10-27T06:19:26.719Z",
              "lastUpdatedTimestamp": "2025-10-28T20:44:48.693Z"
          }
      ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Set Fees

This endpoint is used to set organization level fees and/or agent level fees. If the scope is `org` then the fees will be set at the organization level. If the scope is `agent` then the fees will be set at the agent level. If the scope is `agent` then a valid `agentId` must be provided. The fee data must follow the format below and include at least one partner. Each fee partner must include:

* `fee`: the fee amount in USDC (for flat fees) or a percentage (for BPS fees)
* `feeAddress`: the fee address (fee recipient address)
* `type`: the fee type (must be one of the following: `FLAT` or `BPS`)
* `feeLevel`: the fee level ('manager' fees paid by agent manager ONLY, 'subscriber' fees paid by subscribers and agent manager)

<ParamField body="scope" type="string" required>
  Scope of fees: `org` for organization level or `agent` for agent level
</ParamField>

<ParamField body="agentId" type="string">
  Required if scope is `agent`. The agent ID (UUID format)
</ParamField>

<ParamField body="data" type="object" required>
  Fee data object with partner names as keys. Each partner object must contain:

  <Expandable title="Partner fee object properties">
    * `fee` (number, required): Fee amount in USDC (for FLAT) or percentage (for
      BPS) - `feeAddress` (string, required): Fee recipient address - `type`
      (string, required): Fee type, must be `FLAT` or `BPS` - `feeLevel` (string,
      required): Fee level, must be `manager` or `subscriber`
  </Expandable>
</ParamField>

<ResponseField name="status" type="string">
  Status of the operation
</ResponseField>

<ResponseField name="scope" type="string">
  The scope that was updated
</ResponseField>

<ResponseField name="organization" type="string">
  Organization name
</ResponseField>

<ResponseField name="agentId" type="string">
  Agent ID (if scope is agent)
</ResponseField>

<ResponseField name="upserted" type="number">
  Number of fees upserted
</ResponseField>

<ResponseField name="disabled" type="number">
  Number of fees disabled
</ResponseField>

<ResponseField name="feeData" type="array">
  Array of fee data objects

  <Expandable title="feeData">
    <ResponseField name="partner" type="string">
      Partner name
    </ResponseField>

    <ResponseField name="fee" type="number">
      Fee amount
    </ResponseField>

    <ResponseField name="feeAddress" type="string">
      Fee address
    </ResponseField>

    <ResponseField name="feeType" type="string">
      Fee type (flat or bps)
    </ResponseField>

    <ResponseField name="agentType" type="string">
      Agent type (null for org level)
    </ResponseField>
  </Expandable>
</ResponseField>

## Authentication

Privy Auth

## Request Example

<RequestExample>
  ```json  theme={null}
  {
      "scope": "org",
      "data": {
          "partner_alpha": {
              "fee": 0.25,
              "feeAddress": "0x1234567890abcdef1234567890abcdef12345678",
              "type": "FLAT",
              "feeLevel": "manager"
          },
          "partner_beta": {
              "fee": 0.075,
              "feeAddress": "0xabcdef1234567890abcdef1234567890abcdef12",
              "type": "FLAT",
              "feeLevel": "manager"
          },
          "partner_gamma": {
              "fee": 3.5,
              "feeAddress": "0x9876543210fedcba9876543210fedcba98765432",
              "type": "BPS",
              "feeLevel": "subscriber"
          },
          "partner_delta": {
              "fee": 0.1,
              "feeAddress": "0xfedcba9876543210fedcba9876543210fedcba98",
              "type": "FLAT",
              "feeLevel": "manager"
          },
          "partner_epsilon": {
              "fee": 0.8,
              "feeAddress": "0x5555555555555555555555555555555555555555",
              "type": "FLAT",
              "feeLevel": "manager"
          },
          "platform_fee": {
              "fee": 1.5,
              "feeAddress": "0x6666666666666666666666666666666666666666",
              "type": "BPS",
              "feeLevel": "subscriber"
          }
      }
  }
  ```
</RequestExample>

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "scope": "org",
      "organization": "Your Organization",
      "agentId": null,
      "upserted": 6,
      "disabled": 0,
      "feeData": [
          {
              "partner": "partner_alpha",
              "fee": 0.25,
              "feeAddress": "0x1234567890abcdef1234567890abcdef12345678",
              "feeType": "flat",
              "agentType": null
          },
          {
              "partner": "partner_beta",
              "fee": 0.075,
              "feeAddress": "0xabcdef1234567890abcdef1234567890abcdef12",
              "feeType": "flat",
              "agentType": null
          },
          {
              "partner": "partner_gamma",
              "fee": 3.5,
              "feeAddress": "0x9876543210fedcba9876543210fedcba98765432",
              "feeType": "bps",
              "agentType": null
          },
          {
              "partner": "partner_delta",
              "fee": 0.1,
              "feeAddress": "0xfedcba9876543210fedcba9876543210fedcba98",
              "feeType": "flat",
              "agentType": null
          },
          {
              "partner": "partner_epsilon",
              "fee": 0.8,
              "feeAddress": "0x5555555555555555555555555555555555555555",
              "feeType": "flat",
              "agentType": null
          },
          {
              "partner": "platform_fee",
              "fee": 1.5,
              "feeAddress": "0x6666666666666666666666666666666666666666",
              "feeType": "bps",
              "agentType": null
          }
      ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Organization Fees

This endpoint is used to get the fees for an organization. The `organization` field is extracted from the B2B JWT token.

<ResponseField name="status" type="string">
  Status of the response
</ResponseField>

<ResponseField name="organization" type="string">
  Organization name
</ResponseField>

<ResponseField name="count" type="number">
  Number of fee partners
</ResponseField>

<ResponseField name="data" type="object">
  Object with partner names as keys and fee configurations as values

  <Expandable title="data">
    <ResponseField name="{partner}" type="object">
      Fee configuration for each partner

      <Expandable title="partner">
        <ResponseField name="fee" type="number">
          Fee amount
        </ResponseField>

        <ResponseField name="feeAddress" type="string">
          Fee recipient address
        </ResponseField>

        <ResponseField name="type" type="string">
          Fee type: `flat` or `bps`
        </ResponseField>

        <ResponseField name="agentType" type="string">
          Agent type (null for org level)
        </ResponseField>

        <ResponseField name="updatedAt" type="string">
          ISO timestamp when fee was last updated
        </ResponseField>
      </Expandable>
    </ResponseField>
  </Expandable>
</ResponseField>

## Authentication

Privy Auth

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "organization": "Your Organization",
      "count": 6,
      "data": {
          "partner_alpha": {
              "fee": 0.25,
              "feeAddress": "0x1234567890abcdef1234567890abcdef12345678",
              "type": "flat",
              "agentType": null,
              "updatedAt": "2025-10-29T01:17:33.195Z"
          },
          "partner_beta": {
              "fee": 0.075,
              "feeAddress": "0xabcdef1234567890abcdef1234567890abcdef12",
              "type": "flat",
              "agentType": null,
              "updatedAt": "2025-10-29T01:17:33.195Z"
          },
          "partner_gamma": {
              "fee": 3.5,
              "feeAddress": "0x9876543210fedcba9876543210fedcba98765432",
              "type": "bps",
              "agentType": null,
              "updatedAt": "2025-10-29T01:17:33.195Z"
          },
          "partner_delta": {
              "fee": 0.1,
              "feeAddress": "0xfedcba9876543210fedcba9876543210fedcba98",
              "type": "flat",
              "agentType": null,
              "updatedAt": "2025-10-29T01:17:33.195Z"
          },
          "partner_epsilon": {
              "fee": 0.8,
              "feeAddress": "0x5555555555555555555555555555555555555555",
              "type": "flat",
              "agentType": null,
              "updatedAt": "2025-10-29T01:17:33.195Z"
          },
          "platform_fee": {
              "fee": 1.5,
              "feeAddress": "0x6666666666666666666666666666666666666666",
              "type": "bps",
              "agentType": null,
              "updatedAt": "2025-10-29T01:17:33.195Z"
          }
      }
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Agent Fees

This endpoint is used to get the fees for an agent.

<ParamField query="agentId" type="string" required>
  The unique identifier for the agent (UUID format)
</ParamField>

<ResponseField name="status" type="string">
  Status of the response
</ResponseField>

<ResponseField name="organization" type="string">
  Organization name
</ResponseField>

<ResponseField name="agentId" type="string">
  Agent ID
</ResponseField>

<ResponseField name="count" type="number">
  Number of fee partners
</ResponseField>

<ResponseField name="data" type="object">
  Object with partner names as keys and fee configurations as values

  <Expandable title="data">
    <ResponseField name="{partner}" type="object">
      Fee configuration for each partner

      <Expandable title="partner">
        <ResponseField name="fee" type="number">
          Fee amount
        </ResponseField>

        <ResponseField name="feeAddress" type="string">
          Fee recipient address
        </ResponseField>

        <ResponseField name="type" type="string">
          Fee type: `flat` or `bps`
        </ResponseField>

        <ResponseField name="agentType" type="string">
          Agent type
        </ResponseField>

        <ResponseField name="updatedAt" type="string">
          ISO timestamp when fee was last updated
        </ResponseField>
      </Expandable>
    </ResponseField>
  </Expandable>
</ResponseField>

## Authentication

Privy Auth

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "organization": "Your Organization",
      "agentId": "f459697b-540f-4d79-b014-62f2e35d5151",
      "count": 1,
      "data": {
          "agent_fee": {
              "fee": 1,
              "feeAddress": "0x1234567890abcdef1234567890abcdef12345678",
              "type": "flat",
              "agentType": null,
              "updatedAt": "2025-10-28T18:19:38.194Z"
          }
      }
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Get Fees Balances

This endpoint is used to get the balances of the fee addresses for an organization or an agent. By default, the balances are returned for the organization. And the `organization` field is extracted from the authentication middleware. If an `agentId` is provided as a query parameter, the balances are returned for the agent.

<ParamField query="agentId" type="string">
  Optional agent ID. If provided, returns balances for the agent instead of
  organization
</ParamField>

<ResponseField name="status" type="string">
  Status of the response
</ResponseField>

<ResponseField name="organization" type="string">
  Organization name
</ResponseField>

<ResponseField name="agentId" type="string">
  Agent ID (or "\_org" for organization level)
</ResponseField>

<ResponseField name="count" type="number">
  Number of fee partners
</ResponseField>

<ResponseField name="balances" type="array">
  Array of balance objects

  <Expandable title="balances">
    <ResponseField name="partner" type="string">
      Partner name
    </ResponseField>

    <ResponseField name="feeAddress" type="string">
      Fee recipient address
    </ResponseField>

    <ResponseField name="balance" type="number">
      Current balance in USDC
    </ResponseField>

    <ResponseField name="updatedAt" type="string">
      ISO timestamp when balance was last updated
    </ResponseField>
  </Expandable>
</ResponseField>

## Authentication

Privy Auth

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "status": "success",
      "organization": "Your Organization",
      "agentId": "_org",
      "count": 6,
      "balances": [
          {
              "partner": "partner_alpha",
              "feeAddress": "0x1234567890abcdef1234567890abcdef12345678",
              "balance": 1.25,
              "updatedAt": "2025-10-28T18:23:11.835Z"
          },
          {
              "partner": "partner_beta",
              "feeAddress": "0xabcdef1234567890abcdef1234567890abcdef12",
              "balance": 0.375,
              "updatedAt": "2025-10-28T18:23:11.835Z"
          },
          {
              "partner": "partner_gamma",
              "feeAddress": "0x9876543210fedcba9876543210fedcba98765432",
              "balance": 0.068992,
              "updatedAt": "2025-10-28T18:23:11.839Z"
          },
          {
              "partner": "partner_delta",
              "feeAddress": "0xfedcba9876543210fedcba9876543210fedcba98",
              "balance": 0.5,
              "updatedAt": "2025-10-28T18:23:11.835Z"
          },
          {
              "partner": "partner_epsilon",
              "feeAddress": "0x5555555555555555555555555555555555555555",
              "balance": 4,
              "updatedAt": "2025-10-28T18:23:11.843Z"
          },
          {
              "partner": "platform_fee",
              "feeAddress": "0x6666666666666666666666666666666666666666",
              "balance": 0.029567,
              "updatedAt": "2025-10-28T18:23:11.839Z"
          }
      ]
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Withdraw Token

This endpoint is called to withdraw an ERC20 token from a user's smart account to an external address.

<Note>
  * `wallet` is Privy EOA address - `symphonyWallet` is the user's Symphony
    wallet address - Token decimal conversion will be performed on our backend
</Note>

<ParamField body="collateralToken" type="object" required>
  Token information object

  <Expandable title="collateralToken properties">
    * `chain` (number, required): Chain ID - `address` (string, required): Token
      contract address
  </Expandable>
</ParamField>

<ParamField body="tokenAmount" type="string" required>
  Amount of tokens to withdraw
</ParamField>

<ParamField body="receiverAddress" type="string" required>
  Address to receive the tokens
</ParamField>

<ParamField body="symphonyWallet" type="string" required>
  User's Symphony wallet address
</ParamField>

<ParamField body="wallet" type="string" required>
  Privy EOA address
</ParamField>

<ResponseField name="txHash" type="string">
  Transaction hash
</ResponseField>

<ResponseField name="chain" type="number">
  Chain ID
</ResponseField>

<ResponseField name="explorerUrl" type="string">
  Explorer URL for the transaction
</ResponseField>

## Authentication

Privy authentication token passed in as bearer token

## Request Example

<RequestExample>
  ```json  theme={null}
  {
      "collateralToken": {
          "chain": 42161,
          "address": "0xaf88d065e77c8cc2239327c5edb3a432268e5831"
      },
      "tokenAmount": "1",
      "receiverAddress": "0xFE1b64944787061e414497F86F9d84F6B9d6bDB7",
      "symphonyWallet": "0x2FBE9660bCD32A6C73545cAa4e9284BAd1027D29",
      "wallet": "0xFE1b64944787061e414497F86F9d84F6B9d6bDB7"
  }
  ```
</RequestExample>

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "txHash": "0x187197a65867a3b7935255c24...",
      "chain": 42161,
      "explorerUrl": "https://arbiscan.io/tx/0x187197a658..."
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Withdraw Native

This endpoint is used to withdraw native ether from a Symphony wallet.

<Note>
  * `wallet` is Privy EOA address
  * `symphonyWallet` is the user's Symphony wallet address
  * Native decimal conversion will be performed on our backend
</Note>

<ParamField body="receiverAddress" type="string" required>
  Address to receive the native tokens
</ParamField>

<ParamField body="nativeAmount" type="string" required>
  Amount of native tokens to withdraw
</ParamField>

<ParamField body="chainId" type="string" required>
  Chain ID as a string
</ParamField>

<ParamField body="symphonyWallet" type="string" required>
  User's Symphony wallet address
</ParamField>

<ParamField body="wallet" type="string" required>
  Privy EOA address
</ParamField>

<ResponseField name="txHash" type="string">
  Transaction hash
</ResponseField>

<ResponseField name="chain" type="number">
  Chain ID
</ResponseField>

<ResponseField name="explorerUrl" type="string">
  Explorer URL for the transaction
</ResponseField>

## Authentication

Privy authentication token passed in as bearer token

## Request Example

<RequestExample>
  ```json  theme={null}
  {
      "receiverAddress": "0x56d0573C786d3DB...",
      "nativeAmount": "0.058254",
      "chainId": "42161",
      "symphonyWallet": "0x16975df1927eE35...",
      "wallet": "0xb998f2D4DF3178DD..."
  }
  ```
</RequestExample>

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
      "txHash": "0x187197a65867a3b7935255c24...",
      "chain": 42161,
      "explorerUrl": "https://arbiscan.io/tx/0x187197a658..."
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt

# Token Price

This endpoint is used to get the current USD price of a token. The token can be identified by its address, ticker symbol, or SID (Symphony Identifier). The endpoint uses caching to improve response times for frequently requested tokens.

## Query Parameters

<ParamField query="input" type="string" required>
  Token identifier: Preferred input is the token address. Most core symbols are
  supported (i.e. BTC, ETH, etc.)
</ParamField>

<ParamField query="chainId" type="string | number" required>
  The blockchain chain ID where the token exists. Monad is 143 (For perpetuals
  you can use any chain id where the collateral is starting i.e. 137 (Polygon),
  8453 (Base), 42161 (Arbitrum))
</ParamField>

## Response

<ResponseField name="status" type="string">
  Status of the response (`success` or `error`)
</ResponseField>

<ResponseField name="price" type="number">
  Current USD price of the token. Returns `0` if price cannot be determined.
</ResponseField>

<ResponseField name="sid" type="number">
  The resolved Symphony Identifier (SID) for the token
</ResponseField>

<ResponseField name="chainId" type="number">
  The resolved chain ID used for the lookup
</ResponseField>

## Authentication

This is a public endpoint. No authentication is required, but rate limiting applies.

## Request Example

<RequestExample>
  ```json  theme={null}
  {
    "input": "0x350035555e10d9afaf1566aaebfced5ba6c27777",
    "chainId": 143
  }
  ```
</RequestExample>

## Response Example

<ResponseExample>
  ```json  theme={null}
  {
    "status": "success",
    "price": 0.0044708367310959075,
    "sid": 17050,
    "chainId": 143
  }
  ```
</ResponseExample>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.symphony.io/llms.txt