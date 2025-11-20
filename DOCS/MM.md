# Market Maker Module - Summary

## What We Built

A **production-ready orderbook market making engine** using the Avellaneda-Stoikov model.

**Status**: ✅ Core logic complete, simulation tested
**Lines of Code**: ~900 lines (including exchange adapters)
**Compatible With**: Orderbook DEXs (Kuru, dYdX, Hyperliquid, etc.)
**NOT Compatible With**: AMM DEXs (nad.fun, Uniswap, etc.)

---

## Grok's Mistakes vs. Reality

### What Grok Said (WRONG ❌)
- "Symphony has a Python SDK with `from symphony import Agent`"
- "Use `agent.swap()` for spot trading"
- "There are local scripts running in loops"

### Reality ✅
- Symphony is 100% API-only (no SDK)
- Only has perp trading via `POST /agent/batch-open`
- No spot trading endpoints exist yet
- nad.fun is AMM-based (liquidity pools, not orderbooks)

---

## What Works Where

### ✅ Kuru (Orderbook DEX on Monad)
- **Type**: Central Limit Order Book (CLOB)
- **Our Module**: Perfect fit
- **What You Need**: Kuru API credentials when they launch
- **ETA**: Monday Nov 24 (Monad mainnet launch)

### ❌ nad.fun (AMM on Monad)
- **Type**: Automated Market Maker (liquidity pools)
- **Our Module**: Won't work
- **Alternative**: Just be a passive LP (provide liquidity, earn fees)
- **Why Different**: No limit orders, no active quoting

### 🤷 Symphony Spot (TBD)
- **Status**: Not launched yet
- **If Orderbook**: Our module works
- **If AMM/Pool**: Our module doesn't work
- **Wait for**: Vivaldi to clarify architecture

---

## File Structure

```
market_maker/
├── __init__.py          # Module exports
├── config.py            # Risk parameters (spreads, gamma, limits)
├── orderbook.py         # Orderbook data structures + mock generator
├── engine.py            # Core Avellaneda-Stoikov logic
├── simulator.py         # Test with mock data
├── run_kuru.py          # Production runner for Kuru
├── exchanges/
│   ├── base.py          # Abstract exchange interface
│   └── kuru.py          # Kuru adapter (template, needs API docs)
└── README.md            # Full documentation
```

---

## Simulation Results

**Test Run**: 60 iterations (2 minutes simulated time)

```
Performance:   +$19.63 (+0.20% profit)
Trades:        3 fills ($1,800 volume)
Strategy:      Successfully managed inventory skew
Spreads:       Widened during volatile period as expected
Final Skew:    -0.118 (slightly long USDC, correctly adjusted quotes)
```

**Key Observations**:
- Engine correctly tightened ask side when skew became negative (holding too much USDC)
- Volatility detection worked (spreads widened at iteration #20)
- No negative quotes after fix
- Inventory management functional

---

## What's Real vs. Mocked

### ✅ Production-Ready Logic
- Spread calculation (Avellaneda-Stoikov)
- Inventory skew math
- Volatility calculation (rolling std dev)
- Quote price formulas
- Balance tracking
- P&L calculation

### ❌ Needs Replacement for Production
1. **Orderbook source** → Replace `MockOrderbookGenerator` with `KuruAdapter.get_orderbook()`
2. **Fill detection** → Replace probabilistic fills with real exchange fill notifications
3. **Order placement** → Implement `place_limit_order()` using Kuru API
4. **Fee modeling** → Add actual maker/taker fees

### 🚨 Missing for Scale
1. **Rebalancing** - Market orders when skew exceeds threshold
2. **Adverse selection protection** - Pause if getting picked off
3. **Error handling** - Reconnect logic, order rejections
4. **Market impact** - Adjust size based on orderbook depth
5. **WebSocket integration** - Real-time fills (not REST polling)

---

## Next Steps for Kuru Launch

### Step 1: Get Kuru API Access
- Register on Kuru when they launch Monday
- Get API key + secret
- Read their API documentation

### Step 2: Update KuruAdapter
File: `market_maker/exchanges/kuru.py`

Update based on actual Kuru API:
- Authentication method (currently assumes HMAC-SHA256)
- Endpoint URLs (`/v1/orderbook/{symbol}` etc.)
- Request/response formats
- Symbol format ("CHOG-USDC" vs "CHOG/USDC")

### Step 3: Test with Small Size
```bash
export KURU_API_KEY="your_key"
export KURU_API_SECRET="your_secret"

# Start with small orders ($100-200)
python -m market_maker.run_kuru
```

### Step 4: Monitor & Iterate
Watch for:
- **Fill rate**: Getting trades? If not, spreads too wide
- **Inventory skew**: Staying balanced? If not, tighten opposite side
- **P&L after fees**: Making money? If not, reduce size or widen spreads
- **Adverse selection**: Getting filled on one side repeatedly? Pause and investigate

### Step 5: Scale Gradually
- Start: $100 orders, $2k total capital
- After 24h: $200 orders, $5k capital
- After 1 week: $500 orders, $10k capital
- Never exceed 5% of orderbook depth per order

---

## Key Risks

### 1. Impermanent Loss (Sort Of)
Not traditional IL (that's AMM-specific), but similar risk:
- Price moves up → you sell at low prices → miss gains
- Price moves down → you buy at high prices → catch falling knife

**Mitigation**: Volatility-based pause (stop quoting when vol spikes)

### 2. Adverse Selection
Informed traders hit your quotes before news becomes public.

**Signs**: 10+ consecutive fills on same side
**Mitigation**: Pause after N consecutive fills, widen spreads

### 3. Technical Failures
WebSocket disconnect, API down, order rejected.

**Mitigation**: Error handling, automatic reconnect, kill switch

### 4. Market Impact
Your orders move the market (especially on low-liquidity memecoins).

**Mitigation**: Keep orders < 1-2% of orderbook depth

---

## When to Use This

### ✅ Good Fit
- Orderbook-based DEXs (Kuru, dYdX, Hyperliquid)
- Moderate-to-high liquidity pairs (>$500k daily volume)
- Pairs with natural two-sided flow (not one-way dumps)
- When you can monitor it actively (not set-and-forget)

### ❌ Bad Fit
- AMM DEXs (nad.fun, Uniswap) - use passive LP instead
- Ultra-low liquidity (<$50k daily volume) - you ARE the market
- One-way markets (rug pulls, coordinated dumps)
- Set-and-forget automation - needs active monitoring

---

## Alternative: Passive LP on nad.fun

If you want exposure to $CHOG on nad.fun (AMM):

```solidity
// Just provide liquidity to the pool
provide_liquidity(
    token: "CHOG",
    amount_usdc: 5000,
    amount_chog: calculate_for_50_50_value(current_price)
)

// Earn 0.3% fee on all swaps
// Accept impermanent loss risk
// Zero active management needed
```

**Expected Return**: 0.3% * daily_volume / pool_size
**Risk**: Impermanent loss if price moves significantly
**Effort**: 5 minutes to set up, zero ongoing work

---

## Questions?

- **Technical**: See `market_maker/README.md`
- **Usage**: See `market_maker/run_kuru.py` for example
- **Config**: See `market_maker/config.py` for parameters
- **Testing**: Run `python -m market_maker.simulator`

**Ready to deploy once Kuru API is available! 🚀**
