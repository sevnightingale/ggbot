# Market Maker Module

**Standalone Avellaneda-Stoikov market making engine for orderbook-based spot trading.**

## Overview

This module implements a professional market making strategy using the Avellaneda-Stoikov model. It's designed to provide liquidity on **orderbook-based** DEXs (like Kuru on Monad) by continuously quoting bid/ask limit orders while managing inventory risk.

**⚠️ IMPORTANT**: This is for **orderbook DEXs only** (Kuru, dYdX, Hyperliquid, etc.). It will **NOT** work on AMM-based DEXs (Uniswap, nad.fun, etc.) which use liquidity pools instead of limit orders.

### Key Features

- **Avellaneda-Stoikov Model**: Academic-grade optimal market making
- **Inventory Management**: Automatic skew adjustment to stay balanced
- **Volatility-Adaptive Spreads**: Widen spreads during volatile periods
- **Real-time P&L Tracking**: Monitor performance in real-time
- **Exchange-Agnostic**: Easy to plug in any exchange adapter

## Architecture

```
market_maker/
├── config.py          # Risk parameters and settings
├── orderbook.py       # Orderbook data structures + mock generator
├── engine.py          # Core Avellaneda-Stoikov logic
├── simulator.py       # Test with mock data
└── exchanges/         # (Future) Exchange adapters
    ├── kuru.py
    ├── symphony_spot.py
    └── base.py
```

## Quick Start

### 1. Run Simulation with Mock Data

```bash
cd /home/sev/ggbot
source .venv/bin/activate
python -m market_maker.simulator
```

This will run a 2-minute simulation with mock orderbook data.

### 2. Run from Python

```python
from market_maker import MarketMakerEngine, MarketMakerConfig, MockOrderbookGenerator
import asyncio

# Configure
config = MarketMakerConfig(
    symbol="CHOG/USDC",
    order_size_usd=Decimal("600"),
    base_spread_bps=Decimal("30"),  # 0.30%
    gamma=Decimal("0.15")
)

# Create engine
engine = MarketMakerEngine(config)

# Generate mock orderbook
orderbook_gen = MockOrderbookGenerator(symbol="CHOG/USDC")
orderbook = orderbook_gen.generate()

# Update quotes
status = engine.update_quotes(orderbook)
print(engine.get_status_line(status))
```

## How It Works

### Avellaneda-Stoikov Model

The engine uses the Avellaneda-Stoikov optimal market making framework:

1. **Reservation Price**: Adjust mid price based on inventory position
   ```
   r = mid_price - skew × gamma × volatility² × total_value
   ```

2. **Optimal Spread**: Base spread + volatility adjustment
   ```
   spread = base_spread + vol_multiplier × volatility²
   ```

3. **Quote Prices**:
   ```
   bid_price = r × (1 - spread/2)
   ask_price = r × (1 + spread/2)
   ```

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `order_size_usd` | $600 | Size of each bid/ask order |
| `base_spread_bps` | 30 bps (0.30%) | Minimum spread when calm |
| `gamma` | 0.15 | Inventory risk aversion (higher = more aggressive rebalancing) |
| `volatility_multiplier` | 6.0 | How much to widen spread during volatility |
| `max_inventory_skew` | 0.35 | Pause quoting if skew exceeds ±35% |

### Inventory Skew

Skew measures how imbalanced your inventory is:
- `-1.0`: 100% USDC (no token)
- `0.0`: Perfectly balanced 50/50
- `+1.0`: 100% token (no USDC)

The engine adjusts quotes to push inventory back toward 0.

## Configuration Presets

### Memecoin (High Volatility)
```python
from market_maker.config import MemecoinConfig

config = MemecoinConfig(
    symbol="CHOG/USDC",
    base_spread_bps=Decimal("50"),  # 0.50% wider
    gamma=Decimal("0.25"),  # More aggressive rebalancing
)
```

### Stable Pair (Low Volatility)
```python
from market_maker.config import StablePairConfig

config = StablePairConfig(
    symbol="USDC/USDT",
    base_spread_bps=Decimal("5"),  # 0.05% tight
    gamma=Decimal("0.05"),  # Less aggressive
)
```

## Simulation Output

```
[0001] Mid: 0.001000 | Quotes: 0.000985 / 0.001015 | Skew: +0.000 | Vol: 0.0200 | PnL: $0.00 (+0.00%) | Trades: 0
[0002] Mid: 0.001002 | Quotes: 0.000987 / 0.001017 | Skew: +0.050 | Vol: 0.0198 | PnL: $1.20 (+0.01%) | Trades: 1 | FILLS: SOLD 600.00 @ 0.001015 ($609.00)
...
```

**Columns**:
- `Mid`: Current mid price
- `Quotes`: Your bid / ask prices (or PAUSED if skew too high)
- `Skew`: Inventory imbalance (-1 to +1)
- `Vol`: Realized volatility (annualized)
- `PnL`: Profit/loss vs. starting capital
- `Trades`: Total fills
- `FILLS`: Real-time fill notifications

## Production Usage (Kuru Exchange)

Once Kuru launches on Monad with API access:

### 1. Get API Credentials
Register on Kuru and get API key + secret

### 2. Set Environment Variables
```bash
export KURU_API_KEY="your_api_key"
export KURU_API_SECRET="your_api_secret"
export KURU_API_URL="https://api.kuru.finance"  # or actual URL
```

### 3. Run Market Maker
```bash
cd /home/sev/ggbot
source .venv/bin/activate
python -m market_maker.run_kuru
```

### 4. Monitor Performance
Watch for:
- Fill rate (are you getting trades?)
- Inventory skew (staying balanced?)
- P&L (making money after fees?)
- Spread competitiveness (too wide = no fills, too tight = adverse selection)

### Exchange Adapter

The Kuru adapter (`market_maker/exchanges/kuru.py`) is a **template** that needs to be updated based on Kuru's actual API documentation:

- Authentication method (HMAC-SHA256 assumed)
- Endpoint paths (`/v1/orderbook/{symbol}` etc.)
- Request/response formats
- Symbol format ("CHOG-USDC" vs "CHOG/USDC" vs "CHOG_USDC")
- WebSocket endpoints for real-time fills

### 2. Add Rebalancing Logic

Implement market orders to rebalance when skew gets too high:

```python
def rebalance(self, current_price: Decimal):
    skew = self.state.balance.inventory_skew(current_price)
    if abs(skew) > self.config.rebalance_threshold_skew:
        # Execute market order to move toward 50/50
        pass
```

### 3. Integrate with ggbots

Optional: Add to ggbots UI for monitoring, or keep as standalone service.

## Testing

```bash
# Run quick test (60 seconds)
python -m market_maker.simulator

# Run longer test (5 minutes)
python -c "from market_maker.simulator import run_simulation; import asyncio; asyncio.run(run_simulation(duration_seconds=300))"

# Test with different configs
python -c "
from market_maker.simulator import run_simulation
from market_maker.config import StablePairConfig
import asyncio

config = StablePairConfig()
asyncio.run(run_simulation(config, duration_seconds=120))
"
```

## Performance Notes

- **Latency**: Currently simulated at 2-second updates. Real system should target sub-second.
- **Volatility Calculation**: Uses 60-second rolling window. Tune `volatility_window_seconds` for your market.
- **Spreads**: Default 30bps (0.30%) works for mid-liquidity tokens. Adjust for your market depth.

## FAQ

**Q: Why no LLM?**
A: Market making is pure math. LLMs would add cost and latency with no benefit.

**Q: Can this run on ggbots infrastructure?**
A: Yes, but it's designed as a standalone module. You can use ggbots database/logging, but the core loop is independent.

**Q: How does this compare to ggbots scheduled bots?**
A: Completely different. ggbots bots are directional (long/short) with 5min+ intervals. MM is market-neutral with 1-4 second updates.

**Q: Will this work for $CHOG on nad.fun?**
A: **No.** nad.fun is an AMM (like Uniswap), not an orderbook DEX. For AMM you provide liquidity to a pool, not place limit orders. This module is specifically for orderbook-based exchanges.

**Q: Will this work for $CHOG on Kuru?**
A: **Yes.** Kuru is an orderbook DEX on Monad. Once Kuru launches and provides API access, you can use this module by updating the `KuruAdapter` with their actual API endpoints.

**Q: What about Symphony spot trading?**
A: Depends. If Symphony launches orderbook-based spot trading (limit orders), yes. If it's AMM-based or pool-based, no.

## References

- [Avellaneda & Stoikov (2008)](https://www.math.nyu.edu/faculty/avellane/HighFrequencyTrading.pdf) - Original paper
- [Kuru DEX Docs](https://docs.kuru.finance) - (When available)
- [Symphony Spot API](https://docs.symphony.io) - (When available)
