"""
Market Maker Configuration

Risk parameters and settings for the market making engine.
"""

from decimal import Decimal
from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketMakerConfig:
    """Configuration for market making strategy."""

    # Trading pair
    symbol: str = "CHOG/USDC"

    # Position sizing
    order_size_usd: Decimal = Decimal("600")  # Size of each order in USD
    max_inventory_usd: Decimal = Decimal("10000")  # Total capital

    # Spread parameters (Avellaneda-Stoikov)
    base_spread_bps: Decimal = Decimal("30")  # 0.30% base spread when calm
    volatility_multiplier: Decimal = Decimal("6.0")  # Widen spread during volatility
    gamma: Decimal = Decimal("0.15")  # Inventory risk aversion (0-1, higher = more aggressive rebalancing)

    # Risk limits
    max_inventory_skew: Decimal = Decimal("0.35")  # Pause quoting if |skew| > 35%
    max_position_value_pct: Decimal = Decimal("0.8")  # Max 80% of capital in positions

    # Rebalancing
    rebalance_threshold_skew: Decimal = Decimal("0.25")  # Rebalance if skew > 25%
    rebalance_interval_seconds: int = 300  # Check rebalance every 5 minutes

    # Quote update frequency
    quote_interval_seconds: Decimal = Decimal("2.5")  # Update quotes every 2.5 seconds

    # Volatility calculation
    volatility_window_seconds: int = 60  # Calculate vol over last 60 seconds
    min_volatility: Decimal = Decimal("0.001")  # Minimum vol assumption (0.1%)

    # Safety
    emergency_stop_drawdown_pct: Decimal = Decimal("0.15")  # Stop if down 15%

    def __post_init__(self):
        """Convert string numbers to Decimal if needed."""
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)) and field_name.endswith(('_bps', '_pct', '_usd', '_multiplier', 'gamma', 'skew')):
                setattr(self, field_name, Decimal(str(value)))

    @property
    def base_spread(self) -> Decimal:
        """Convert basis points to decimal (30 bps = 0.003)."""
        return self.base_spread_bps / Decimal("10000")

    def get_min_order_size_usd(self) -> Decimal:
        """Minimum order size (10% of standard size)."""
        return self.order_size_usd * Decimal("0.1")


@dataclass
class MemecoinConfig(MarketMakerConfig):
    """Preset for volatile memecoin trading."""

    symbol: str = "CHOG/USDC"
    base_spread_bps: Decimal = Decimal("50")  # 0.50% wider spreads
    volatility_multiplier: Decimal = Decimal("8.0")  # React harder to vol
    gamma: Decimal = Decimal("0.25")  # More aggressive rebalancing
    max_inventory_skew: Decimal = Decimal("0.30")  # Tighter inventory limits
    quote_interval_seconds: Decimal = Decimal("2.0")  # Faster updates


@dataclass
class StablePairConfig(MarketMakerConfig):
    """Preset for stable pairs (low volatility)."""

    symbol: str = "USDC/USDT"
    base_spread_bps: Decimal = Decimal("5")  # 0.05% tight spreads
    volatility_multiplier: Decimal = Decimal("3.0")  # Less vol sensitivity
    gamma: Decimal = Decimal("0.05")  # Less aggressive rebalancing
    max_inventory_skew: Decimal = Decimal("0.50")  # Can handle more skew
    quote_interval_seconds: Decimal = Decimal("5.0")  # Slower updates
