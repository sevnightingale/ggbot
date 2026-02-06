# Nansen API / MCP Integration Guide

**Status**: Explored 2026-02-04, shut down to conserve credits. Re-enable when ready to integrate.
**API Credits**: 1,100 total (used ~6 for testing)
**Cost**: ~$0.001/credit ($1.10 total budget)
**MCP Server**: `https://mcp.nansen.ai/ra/mcp/`

---

## Quick Setup

```bash
# Add Nansen MCP to Claude Code
claude mcp add --transport http nansen https://mcp.nansen.ai/ra/mcp/ --header "NANSEN-API-KEY: <key>"

# Restart Claude Code after adding
# API key stored in .claude.json (project-level)
```

**Important**: Remove MCP when not in use to avoid accidental credit consumption:
```bash
claude mcp remove nansen
```

---

## Available MCP Tools (20 total)

### Token Analysis (10 tools)

| Tool | Description | Credit Cost | Value |
|------|-------------|-------------|-------|
| `token_discovery_screener` | Find trending tokens by volume, liquidity, smart money activity. Max 25 results, 5 chains per request. Supports filters: volume, liquidity, marketCap, netflow, sectors, smart money labels. | ~1/call | ⭐⭐⭐ |
| `token_current_top_holders` | Top 25 holders (whales, funds, exchanges) with 24h/7d/30d balance changes. Supports `onchain_tokens` and `perps` modes. Perps mode shows positions with entry/mark/liquidation prices. | ~1/call | ⭐⭐⭐ |
| `token_flows` | Hourly aggregated inflow/outflow by segment (whale, smart_money, exchange, public_figure, top_100_holders). More granular than `token_recent_flows_summary`. | ~1/call | ⭐⭐⭐ |
| `token_recent_flows_summary` | Quick total flows per 6 segments over lookback period (5m, 1h, 6h, 12h, 1d, 7d). Less granular but faster overview. Does NOT support Bitcoin or Hyperliquid. | ~1/call | ⭐⭐ |
| `token_dex_trades` | DEX trades for a specific token. Supports both onchain_tokens and perps modes. Filterable by action (buy/sell), smart money labels, trade value. | ~1/call | ⭐⭐ |
| `token_who_bought_sold` | Aggregated buyers/sellers on DEX only. Shows total bought/sold volume by address. Useful for finding who is accumulating or distributing. | ~1/call | ⭐⭐ |
| `token_transfers` | 25 most recent token transfers (DEX/CEX/non-exchange). Does NOT support native tokens (ETH, SOL). | ~1/call | ⭐ |
| `token_pnl_leaderboard` | Top 25 traders by P&L for a specific token. Shows realized/unrealized PnL, ROI, holdings, trade count. | ~1/call | ⭐⭐ |
| `token_quant_scores` | Risk/reward indicators (momentum, liquidity risk, concentration). Returned 404 in testing - may not have data for all tokens. | ~1/call | ⭐⭐⭐ |
| `token_ohlcv` | OHLCV price data with auto-resolution. Does NOT support Hyperliquid. Use for latest price (set from=5MIN_AGO, to=NOW). | ~1/call | ⭐ |

### Smart Money (2 tools)

| Tool | Description | Credit Cost | Value |
|------|-------------|-------------|-------|
| `smart_traders_and_funds_token_balances` | Aggregated smart trader & fund token holdings across chains. Excludes whales/large holders/influencers. Filterable by smart money label type. | ~1/call | ⭐⭐⭐ |
| `smart_traders_and_funds_perp_trades` | Recent Hyperliquid perp trades from smart traders & funds. Shows side, action (Open/Close/Add/Reduce), size, value. Sorted by value. | ~1/call | ⭐⭐⭐ |

### Wallet/Address Analysis (7 tools)

| Tool | Description | Credit Cost | Value |
|------|-------------|-------------|-------|
| `address_portfolio` | Full portfolio: tokens + DeFi + Hyperliquid perps. Modes: fast-mode-default, all, wallet_balances, defi, hyperliquid. Also supports entity lookup (e.g., "Binance"). | ~1/call | ⭐⭐ |
| `address_counterparties` | Top 25 addresses/entities with most interactions. Shows net value flow, top 3 tokens transferred. Useful for finding related wallets. | ~1/call | ⭐⭐ |
| `address_transactions` | 20 most recent transactions for an address. | ~1/call | ⭐ |
| `address_historical_balances` | Historical balance snapshots (1d to 2yr lookback). Supports entity lookup. | ~1/call | ⭐ |
| `address_related_addresses` | First funder, deployer, signers, multisig connections. Note: first funder from exchange withdrawal does NOT mean same entity. | ~1/call | ⭐ |
| `wallet_pnl_summary` | Aggregate realized P&L for a wallet (does NOT include unrealized). | ~1/call | ⭐⭐ |
| `wallet_pnl_for_token` | P&L stats for a specific token traded by a wallet. | ~1/call | ⭐ |

### Hyperliquid (1 tool)

| Tool | Description | Credit Cost | Value |
|------|-------------|-------------|-------|
| `hyperliquid_leaderboard` | Top perp traders by P&L/ROI/account value. Filterable by account value, P&L, ROI ranges. | ~1/call | ⭐⭐⭐ |

### Utility (3 tools)

| Tool | Description | Credit Cost | Value |
|------|-------------|-------------|-------|
| `general_search` | Search tokens, entities, addresses, ENS/SNS domains. Entry point for resolving addresses. Works on free tier. | ~1/call | ⭐⭐ |
| `transaction_lookup` | Decode a specific transaction hash with token transfers. | ~1/call | ⭐ |
| `growth_chain_rank` | Chain rankings by active addresses, transactions, gas fees, DEX volume. Timeframes: 7d, 30d, 365d. | ~1/call | ⭐ |
| `nansen_score_top_tokens` | Pre-scored buying recommendations. Performance Score >= 15 = buy threshold. Risk Score > 0 = low-medium risk. | ~1/call | ⭐⭐ |

---

## Supported Chains

arbitrum, avalanche, base, bnb, ethereum, hyperevm, iotaevm, linea, mantle, monad, near, optimism, plasma, polygon, ronin, scroll, sei, solana, sonic, sui, ton, tron, unichain, zksync

**Note**: Hyperliquid is a perps-only chain. Some endpoints don't support it (e.g., `token_ohlcv`, `token_recent_flows_summary`).

---

## Test Results (2026-02-04)

### Smart Money BTC Positioning (Hyperliquid Perps)

Query: `token_current_top_holders` with `mode=perps`, `tokenAddress=BTC`, `labelType=smart_money`

```
Galaxy Digital:      $22.1M SHORT @ $103,994 entry → +$11M unrealized profit
Smart Trader 0x71df: $20.1M SHORT @ $106,677 entry → +$10.2M unrealized profit
Smart Trader 0xfeec: $16.2M SHORT @ $106,094 entry → +$7.7M unrealized profit
Smart Trader 0x5d2f: $8.1M SHORT @ $111,499 entry → +$14.2M unrealized profit

Only 4 LONG positions in top 25, all underwater:
Smart Trader 0x4aab: $16.2M LONG @ $80,724 entry → -$1.6M unrealized loss
Smart Trader 0xe282: $7.3M LONG @ $85,138 entry → -$1.2M unrealized loss
```

**Signal at time of query**: Smart money overwhelmingly SHORT BTC (21 of 25 top positions).

### Hyperliquid Leaderboard (7-day)

Query: `hyperliquid_leaderboard` with 7-day range, $100K+ account value

```
#1  Abraxas Capital:     +$70.2M P&L (1.7% ROI, $21.3M account)
#2  Smart Trader 0x45d2: +$36.8M P&L (0.2% ROI, $19.2M account)
#3  Smart Trader 0x35d1: +$36.5M P&L (0.3% ROI, $23.3M account)
#4  Resolv USR:          +$33.5M P&L (0.6% ROI, $16.7M account)
#5  Fasanara Capital:    +$27.7M P&L (0.1% ROI, $22.2M account)
#6  Smart Trader 0x5d2f: +$26.6M P&L (2.2% ROI, $7.2M account)
#7  Galaxy Digital:      +$25.2M P&L (0.4% ROI, $27.9M account)
#8  Dex Trader 0xd475:   +$22.4M P&L
#9  Laurent Zeimes:      +$20.3M P&L (1.2% ROI, $35.7M account)
#10 Wintermute:          +$17.8M P&L
```

### Smart Money Token Holdings (Non-stablecoin)

Query: `smart_traders_and_funds_token_balances` on ethereum + solana, excluding stablecoins/native tokens

```
UNI:   $150.2M held by 33 smart money wallets (8.3% of supply)
ONDO:  $90.7M held by 21 smart money wallets (5.0% of supply)
WLD:   $78.3M held by 20 smart money wallets (4.3% of supply)
AAVE:  $70.7M held by 18 smart money wallets (3.9% of supply)
AXS:   $32.4M held by 20 smart money wallets
ENA:   $15.4M held by 16 smart money wallets
LDO:   $9.2M held by 18 smart money wallets

Memecoins appearing in smart money:
BUTTCOIN: $1.4M held by 23 wallets (26 days old)
PENGUIN:  $467K held by 21 wallets (19 days old)
WOJAK:    $330K held by 13 wallets (93 days old)
```

### Smart Money Perp Trades (Recent, by Value)

Query: `smart_traders_and_funds_perp_trades` sorted by value descending

```
$8.3M  BTC Long Close    (Smart Trader 0x9e2c, Jan 31)
$7.8M  BTC Long Reduce   (Smart Trader 0x9e2c, Feb 3)
$6.3M  ETH Short Close   (Smart Trader 0x3c36, Feb 1)
$6.0M  BTC Long Close    (Smart Trader 0xdf78, Feb 4)
$4.8M  BTC Short Add     (Smart Trader 0x99b1, Feb 1)
$3.8M  HYPE Long Open    (Smart Trader 0xf562, Jan 29)
```

---

## Integration Plan for ggbots

### Phase 1: Market Intelligence Data Points (Low Effort)

Add as new data sources in `market_intelligence/` alongside existing Grok sources:

| Data Point | Endpoint | Update Frequency | Use Case |
|------------|----------|-----------------|----------|
| `smart_money_btc_sentiment` | `token_current_top_holders` (perps) | Every 4h | Long/short ratio of smart money BTC positions |
| `smart_money_eth_sentiment` | `token_current_top_holders` (perps) | Every 4h | Long/short ratio of smart money ETH positions |
| `smart_money_perp_activity` | `smart_traders_and_funds_perp_trades` | Every 1h | Recent large smart money trades |
| `smart_money_accumulation` | `smart_traders_and_funds_token_balances` | Every 6h | What tokens smart money is holding |

**Estimated cost**: ~10-20 calls/day = 300-600 credits/month

### Phase 2: Token Discovery (Medium Effort)

| Data Point | Endpoint | Use Case |
|------------|----------|----------|
| `token_screener_smart_flow` | `token_discovery_screener` (smart money filter) | Find tokens with unusual smart money inflows |
| `token_top_holders` | `token_current_top_holders` | Whale concentration risk for any traded token |

### Phase 3: Copy Trading Signals (Higher Effort)

Track specific top-performing wallets from `hyperliquid_leaderboard` and mirror their trades. Would require:
- Periodic leaderboard polling
- Wallet-specific trade monitoring
- Position replication logic in trading engine

---

## Smart Money Labels

Labels used across Nansen endpoints:

| Label | Description |
|-------|-------------|
| `30D Smart Trader` | Profitable in last 30 days |
| `90D Smart Trader` | Profitable in last 90 days |
| `180D Smart Trader` | Profitable in last 180 days |
| `All Time Smart Trader` | Historically profitable |
| `Fund` | Known fund/institutional wallet |
| `Smart HL Perps Trader` | Smart trader on Hyperliquid perps |
| `Any Smart Money` | Includes all above |

### Holder Segment Types

| Segment | Description |
|---------|-------------|
| `whale` | Large individual holders |
| `public_figure` | Known personalities |
| `smart_money` | Labeled smart traders/funds |
| `top_100_holders` | Top 100 by balance |
| `exchange` | Exchange wallets |

---

## API Quirks & Limitations

1. **`token_quant_scores`**: Returned 404 for WBTC. May only have data for major tokens or require specific chain/address combos.

2. **`token_recent_flows_summary`**: Does NOT support Bitcoin or Hyperliquid chains.

3. **`token_ohlcv`**: Does NOT support Hyperliquid. Use for EVM chains and Solana only. Prices from `general_search` are delayed - always use `token_ohlcv` for accurate prices.

4. **`token_transfers`**: Does NOT support native tokens (SOL address `So11111111...`, ETH address `0xeeeeee...`).

5. **`token_discovery_screener`**: Max 5 chains per request. Can timeout with many chains - use 4 or fewer. `priceChange` is NOT a valid filter, only an `orderBy` field.

6. **`smart_traders_and_funds_token_balances`**: Using `labelType: smart_money` is NOT a good proxy for overall market view. Use only when explicitly needed.

7. **`address_related_addresses`**: First funder from exchange withdrawal does NOT mean same entity - only indicates funding source.

8. **Hyperliquid perps**: Shorts that are added show with negative sign (new short positions, not closed positions).

9. **Credit usage**: Each API call ≈ 1 credit. Monitor usage to avoid running out.

---

## Pricing Reference

| Tier | Credits | Cost | Notes |
|------|---------|------|-------|
| Free | 100 non-renewing | $0 | Only `general_search` works |
| Pro | 1,000 initial + top-ups | Varies | Full endpoint access |
| Per-Credit | Individual | $0.001/credit | Bulk discounts available |

**Our budget**: 1,100 credits (~$1.10). At 10-20 calls/day integration = ~2-4 months of light usage.

---

## References

- [Nansen API](https://www.nansen.ai/api)
- [Nansen Smart Money Dashboard](https://app.nansen.ai/smart-money)
- [Smart Money Tracking Guide](https://www.nansen.ai/guides/how-to-find-and-track-smart-money-wallets-in-crypto)
- [Nansen Token View](https://app.nansen.ai/token-god-mode)
