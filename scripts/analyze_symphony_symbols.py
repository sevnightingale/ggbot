"""
Analyze Symphony-compatible symbols and recommend diversified portfolios.
"""

import sys
sys.path.insert(0, '/home/sev/ggbot')

from core.symbols.registry import SYMBOL_REGISTRY
from collections import defaultdict

# Market cap estimates (approximate, for categorization)
MARKET_CAPS = {
    # Blue Chip / Large Cap ($10B+)
    "btc": ("Blue Chip", "$1.9T", "Store of Value / Digital Gold"),
    "eth": ("Blue Chip", "$450B", "Smart Contracts / L1"),
    "bnb": ("Blue Chip", "$90B", "Exchange Token"),
    "sol": ("Blue Chip", "$80B", "High-Performance L1"),
    "xrp": ("Blue Chip", "$140B", "Payments"),
    "ada": ("Blue Chip", "$35B", "L1 / Research-Driven"),
    "avax": ("Blue Chip", "$15B", "L1 / Enterprise"),
    "dot": ("Blue Chip", "$10B", "Interoperability"),
    "link": ("Blue Chip", "$15B", "Oracles"),
    "ltc": ("Blue Chip", "$10B", "Payments / OG Crypto"),

    # Mid Cap ($1B-10B)
    "arb": ("Mid Cap", "$8B", "L2 Scaling / Ethereum"),
    "op": ("Mid Cap", "$5B", "L2 Scaling / Ethereum"),
    "near": ("Mid Cap", "$6B", "L1 / Sharding"),
    "icp": ("Mid Cap", "$5B", "L1 / Internet Computer"),
    "inj": ("Mid Cap", "$3B", "DeFi / DEX"),
    "tia": ("Mid Cap", "$2B", "Modular Blockchain"),
    "sei": ("Mid Cap", "$1.5B", "Trading-Focused L1"),
    "apt": ("Mid Cap", "$4B", "L1 / Move Language"),
    "ondo": ("Mid Cap", "$2B", "RWA / DeFi"),
    "render": ("Mid Cap", "$3B", "GPU Rendering / AI Compute"),
    "fil": ("Mid Cap", "$3B", "Decentralized Storage"),
    "grt": ("Mid Cap", "$2B", "Indexing / The Graph"),
    "atom": ("Mid Cap", "$3B", "Interoperability / Cosmos"),
    "doge": ("Mid Cap", "$15B", "Memecoin OG"),
    "hbar": ("Mid Cap", "$4B", "Enterprise / Hashgraph"),

    # Small Cap ($100M-1B)
    "pyth": ("Small Cap", "$800M", "Oracle / Low-Latency"),
    "jup": ("Small Cap", "$900M", "Solana DEX Aggregator"),
    "pendle": ("Small Cap", "$600M", "Yield Trading / DeFi"),
    "ena": ("Small Cap", "$700M", "Synthetic Dollar / DeFi"),
    "wld": ("Small Cap", "$1.2B", "Identity / AI"),
    "strk": ("Small Cap", "$900M", "L2 / StarkNet"),
    "gmx": ("Small Cap", "$800M", "Perp DEX"),
    "dydx": ("Small Cap", "$600M", "Perp DEX"),
    "fet": ("Small Cap", "$500M", "AI Agents"),
    "tao": ("Small Cap", "$3B", "AI / Neural Networks"),
    "jto": ("Small Cap", "$400M", "Solana Liquid Staking"),
    "wif": ("Small Cap", "$2B", "Memecoin / Solana"),
    "ethfi": ("Small Cap", "$300M", "Liquid Staking"),
    "ens": ("Small Cap", "$700M", "Domain Names"),
    "ldo": ("Small Cap", "$2B", "Liquid Staking / Lido"),
}

# Market segments
SEGMENTS = {
    # Layer 1 Blockchains
    "btc": "L1 - Bitcoin", "eth": "L1 - Ethereum", "sol": "L1 - Solana",
    "ada": "L1 - Cardano", "avax": "L1 - Avalanche", "dot": "L1 - Polkadot",
    "near": "L1 - Near", "icp": "L1 - Internet Computer", "apt": "L1 - Aptos",
    "sei": "L1 - Sei", "atom": "L1 - Cosmos", "tia": "L1 - Celestia (Modular)",

    # Layer 2 Scaling
    "arb": "L2 - Arbitrum", "op": "L2 - Optimism", "strk": "L2 - StarkNet",

    # DeFi
    "aave": "DeFi - Lending", "cake": "DeFi - DEX", "gmx": "DeFi - Perp",
    "dydx": "DeFi - Perp", "pendle": "DeFi - Yield", "inj": "DeFi - DEX",
    "ondo": "DeFi - RWA", "ena": "DeFi - Stablecoin", "ldo": "DeFi - Liquid Staking",
    "ethfi": "DeFi - Liquid Staking", "jto": "DeFi - Liquid Staking",
    "jup": "DeFi - DEX Aggregator",

    # Infrastructure
    "link": "Infra - Oracles", "pyth": "Infra - Oracles",
    "fil": "Infra - Storage", "grt": "Infra - Indexing",
    "render": "Infra - GPU", "hbar": "Infra - Hashgraph",

    # AI & Compute
    "fet": "AI - Agents", "tao": "AI - Neural Networks",
    "render": "AI - GPU Rendering",

    # Memecoins
    "doge": "Meme - OG", "wif": "Meme - Solana",

    # Gaming & Metaverse
    "gala": "Gaming", "sand": "Metaverse", "mana": "Metaverse",

    # Payments
    "xrp": "Payments", "ltc": "Payments",

    # Other
    "bnb": "Exchange Token", "wld": "Identity / AI",
    "ens": "Domain Names",
}


def analyze_symphony_symbols():
    """Analyze and categorize Symphony-compatible symbols."""

    # Get all Symphony-compatible symbols
    symphony_symbols = [
        key for key, data in SYMBOL_REGISTRY.items()
        if data.get("symphony_compatible", False)
    ]

    print("\n" + "=" * 80)
    print("SYMPHONY-COMPATIBLE SYMBOLS ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Symphony-Compatible: {len(symphony_symbols)} symbols")

    # Categorize by market cap
    by_cap = defaultdict(list)
    for symbol in symphony_symbols:
        if symbol in MARKET_CAPS:
            cap_tier, market_cap, description = MARKET_CAPS[symbol]
            by_cap[cap_tier].append((symbol.upper(), market_cap, description))

    print(f"\nCategorized: {sum(len(v) for v in by_cap.values())} / {len(symphony_symbols)}")
    print(f"  Blue Chip: {len(by_cap['Blue Chip'])}")
    print(f"  Mid Cap: {len(by_cap['Mid Cap'])}")
    print(f"  Small Cap: {len(by_cap['Small Cap'])}")
    print(f"  Uncategorized: {len(symphony_symbols) - sum(len(v) for v in by_cap.values())}")

    # Categorize by segment
    by_segment = defaultdict(list)
    for symbol in symphony_symbols:
        if symbol in SEGMENTS:
            segment = SEGMENTS[symbol].split(" - ")[0]  # Get category prefix
            by_segment[segment].append(symbol.upper())

    print(f"\nBy Market Segment:")
    for segment in sorted(by_segment.keys()):
        print(f"  {segment}: {len(by_segment[segment])} symbols")

    return by_cap, by_segment


def recommend_portfolios():
    """Recommend diversified symbol portfolios."""

    print("\n" + "=" * 80)
    print("RECOMMENDED DIVERSIFIED PORTFOLIOS")
    print("=" * 80)

    # Portfolio 1: Conservative (Blue Chip Heavy)
    print("\n📊 Portfolio 1: CONSERVATIVE (Blue Chip Focus)")
    print("-" * 80)
    conservative = [
        ("BTC", "Blue Chip", "$1.9T", "Store of Value - 40% allocation"),
        ("ETH", "Blue Chip", "$450B", "Smart Contracts - 30% allocation"),
        ("SOL", "Blue Chip", "$80B", "High-Performance L1 - 15% allocation"),
        ("BNB", "Blue Chip", "$90B", "Exchange Token - 5% allocation"),
        ("LINK", "Blue Chip", "$15B", "Oracles - 5% allocation"),
        ("AVAX", "Blue Chip", "$15B", "Enterprise L1 - 5% allocation"),
    ]

    for symbol, tier, mcap, description in conservative:
        print(f"  {symbol:8} | {tier:10} | {mcap:8} | {description}")

    print(f"\n  Risk Profile: Low-Medium")
    print(f"  Diversification: 6 assets across 3 segments (L1s, Exchange, Oracles)")
    print(f"  Volatility: Lower than market average")

    # Portfolio 2: Balanced
    print("\n\n📊 Portfolio 2: BALANCED (Mixed Cap & Sectors)")
    print("-" * 80)
    balanced = [
        ("BTC", "Blue Chip", "$1.9T", "L1 - Store of Value"),
        ("ETH", "Blue Chip", "$450B", "L1 - Smart Contracts"),
        ("SOL", "Blue Chip", "$80B", "L1 - High Performance"),
        ("ARB", "Mid Cap", "$8B", "L2 - Ethereum Scaling"),
        ("INJ", "Mid Cap", "$3B", "DeFi - Decentralized Exchange"),
        ("RENDER", "Mid Cap", "$3B", "AI - GPU Rendering"),
        ("PYTH", "Small Cap", "$800M", "Infra - Low-Latency Oracles"),
        ("PENDLE", "Small Cap", "$600M", "DeFi - Yield Trading"),
        ("TAO", "Small Cap", "$3B", "AI - Neural Networks"),
        ("DOGE", "Mid Cap", "$15B", "Meme - Cultural Hedge"),
    ]

    for symbol, tier, mcap, description in balanced:
        print(f"  {symbol:8} | {tier:10} | {mcap:8} | {description}")

    print(f"\n  Risk Profile: Medium")
    print(f"  Diversification: 10 assets across 5 segments (L1, L2, DeFi, AI, Meme)")
    print(f"  Allocation: 60% Blue Chip, 30% Mid Cap, 10% Small Cap")

    # Portfolio 3: Aggressive Growth
    print("\n\n📊 Portfolio 3: AGGRESSIVE GROWTH (Small/Mid Cap Heavy)")
    print("-" * 80)
    aggressive = [
        ("ETH", "Blue Chip", "$450B", "L1 - Foundation 30%"),
        ("ARB", "Mid Cap", "$8B", "L2 - Ethereum Scaling"),
        ("OP", "Mid Cap", "$5B", "L2 - Optimistic Rollup"),
        ("SEI", "Mid Cap", "$1.5B", "L1 - Trading-Focused"),
        ("INJ", "Mid Cap", "$3B", "DeFi - Perps & DEX"),
        ("GMX", "Small Cap", "$800M", "DeFi - Perps Leader"),
        ("PENDLE", "Small Cap", "$600M", "DeFi - Yield Innovation"),
        ("PYTH", "Small Cap", "$800M", "Infra - Oracle"),
        ("TAO", "Small Cap", "$3B", "AI - Bittensor"),
        ("JUP", "Small Cap", "$900M", "DeFi - Solana DEX"),
        ("WIF", "Small Cap", "$2B", "Meme - High Beta"),
        ("STRK", "Small Cap", "$900M", "L2 - StarkNet"),
    ]

    for symbol, tier, mcap, description in aggressive:
        print(f"  {symbol:8} | {tier:10} | {mcap:8} | {description}")

    print(f"\n  Risk Profile: High")
    print(f"  Diversification: 12 assets across 5 segments (L1, L2, DeFi, AI, Meme)")
    print(f"  Allocation: 30% Blue Chip, 40% Mid Cap, 30% Small Cap")
    print(f"  Volatility: Higher than market, potential for outsized gains")

    # Portfolio 4: Sector Rotation (Thematic)
    print("\n\n📊 Portfolio 4: AI & INFRASTRUCTURE THEME")
    print("-" * 80)
    thematic = [
        ("ETH", "Blue Chip", "$450B", "L1 - Smart Contract Foundation"),
        ("LINK", "Blue Chip", "$15B", "Infra - Oracle Standard"),
        ("RENDER", "Mid Cap", "$3B", "AI - GPU Rendering Network"),
        ("FIL", "Mid Cap", "$3B", "Infra - Decentralized Storage"),
        ("GRT", "Mid Cap", "$2B", "Infra - Data Indexing"),
        ("PYTH", "Small Cap", "$800M", "Infra - Real-Time Oracles"),
        ("TAO", "Small Cap", "$3B", "AI - Decentralized ML"),
        ("FET", "Small Cap", "$500M", "AI - Autonomous Agents"),
    ]

    for symbol, tier, mcap, description in thematic:
        print(f"  {symbol:8} | {tier:10} | {mcap:8} | {description}")

    print(f"\n  Risk Profile: Medium-High")
    print(f"  Diversification: 8 assets focused on AI & Infrastructure")
    print(f"  Theme: Beneficiaries of increasing AI compute & data demand")

    # Portfolio 5: DeFi Focused
    print("\n\n📊 Portfolio 5: DeFi ECOSYSTEM")
    print("-" * 80)
    defi = [
        ("ETH", "Blue Chip", "$450B", "DeFi Base Layer"),
        ("AAVE", "Mid Cap", "$5B", "DeFi - Lending Protocol"),
        ("ARB", "Mid Cap", "$8B", "L2 - DeFi Scaling"),
        ("INJ", "Mid Cap", "$3B", "DeFi - DEX & Derivatives"),
        ("GMX", "Small Cap", "$800M", "DeFi - Perps Trading"),
        ("DYDX", "Small Cap", "$600M", "DeFi - Perps Trading"),
        ("PENDLE", "Small Cap", "$600M", "DeFi - Yield Trading"),
        ("JUP", "Small Cap", "$900M", "DeFi - DEX Aggregator"),
        ("LDO", "Small Cap", "$2B", "DeFi - Liquid Staking"),
        ("ONDO", "Mid Cap", "$2B", "DeFi - Real World Assets"),
    ]

    for symbol, tier, mcap, description in defi:
        print(f"  {symbol:8} | {tier:10} | {mcap:8} | {description}")

    print(f"\n  Risk Profile: Medium-High")
    print(f"  Diversification: 10 assets across DeFi sub-sectors")
    print(f"  Segments: Lending, DEX, Perps, Yield, Staking, RWA")

    print("\n" + "=" * 80)
    print("USAGE RECOMMENDATIONS")
    print("=" * 80)
    print("""
Conservative Portfolio:
  - Best for: Testing new strategies with lower risk
  - Liquidity: Highest - all blue chips have deep liquidity
  - Correlation: Lower correlation to risky alts

Balanced Portfolio:
  - Best for: Most users - good risk/reward balance
  - Diversification: Broad exposure to all major sectors
  - Use case: Multi-strategy bots with different risk profiles

Aggressive Growth:
  - Best for: High conviction plays on emerging narratives
  - Volatility: Expect 2-3x more volatility than BTC
  - Use case: Momentum/trend-following strategies

AI & Infrastructure:
  - Best for: Thematic plays on long-term trends
  - Correlation: Lower correlation to general crypto market
  - Use case: Longer timeframes (4h, 1d candles)

DeFi Ecosystem:
  - Best for: Trading DeFi narratives and rotations
  - Correlation: Higher inter-asset correlation during DeFi seasons
  - Use case: Sector rotation strategies
""")


if __name__ == "__main__":
    # Analyze symbols
    analyze_symphony_symbols()

    # Show portfolio recommendations
    recommend_portfolios()

    print("\n✅ Analysis complete!")
    print("=" * 80)
