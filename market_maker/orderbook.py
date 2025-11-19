"""
Orderbook data structures and mock data generation.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Tuple
import random
import time


@dataclass
class OrderbookLevel:
    """A single price level in the orderbook."""
    price: Decimal
    size: Decimal  # Amount of base currency (e.g., CHOG)

    def __repr__(self):
        return f"{self.price:.6f} @ {self.size:.2f}"


@dataclass
class Orderbook:
    """Full orderbook with bids and asks."""
    symbol: str
    timestamp: float
    bids: List[OrderbookLevel]  # Sorted descending (best bid first)
    asks: List[OrderbookLevel]  # Sorted ascending (best ask first)

    @property
    def best_bid(self) -> OrderbookLevel:
        """Get best bid (highest buy price)."""
        if not self.bids:
            raise ValueError("No bids in orderbook")
        return self.bids[0]

    @property
    def best_ask(self) -> OrderbookLevel:
        """Get best ask (lowest sell price)."""
        if not self.asks:
            raise ValueError("No asks in orderbook")
        return self.asks[0]

    @property
    def mid_price(self) -> Decimal:
        """Calculate mid price."""
        return (self.best_bid.price + self.best_ask.price) / Decimal("2")

    @property
    def spread(self) -> Decimal:
        """Calculate bid-ask spread."""
        return self.best_ask.price - self.best_bid.price

    @property
    def spread_bps(self) -> Decimal:
        """Calculate spread in basis points."""
        return (self.spread / self.mid_price) * Decimal("10000")

    def get_depth(self, levels: int = 5) -> Tuple[List[OrderbookLevel], List[OrderbookLevel]]:
        """Get top N levels of bids and asks."""
        return self.bids[:levels], self.asks[:levels]

    def __repr__(self):
        bid_str = " | ".join(str(b) for b in self.bids[:3])
        ask_str = " | ".join(str(a) for a in self.asks[:3])
        return f"Book({self.symbol}): {bid_str} || {ask_str} | Mid: {self.mid_price:.6f} | Spread: {self.spread_bps:.1f}bps"


class MockOrderbookGenerator:
    """Generate realistic mock orderbook data for testing."""

    def __init__(
        self,
        symbol: str,
        base_price: Decimal = Decimal("0.001"),
        base_spread_bps: Decimal = Decimal("30"),
        volatility_pct: Decimal = Decimal("2.0"),
        levels: int = 10
    ):
        self.symbol = symbol
        self.base_price = base_price
        self.base_spread_bps = base_spread_bps
        self.volatility_pct = volatility_pct
        self.levels = levels

        # State for realistic price movement
        self.current_price = base_price
        self.last_update = time.time()
        self.trend = Decimal("0")  # -1 to 1

    def generate(self) -> Orderbook:
        """Generate a realistic orderbook snapshot."""
        now = time.time()

        # Simulate price drift (random walk with trend)
        time_delta = now - self.last_update
        drift = Decimal(str(random.gauss(0, 0.0001))) * Decimal(str(time_delta))
        trend_component = self.trend * Decimal("0.0001") * Decimal(str(time_delta))

        self.current_price = self.current_price * (Decimal("1") + drift + trend_component)
        self.current_price = max(self.current_price, Decimal("0.0001"))  # Floor

        # Occasionally shift trend
        if random.random() < 0.05:  # 5% chance per update
            self.trend = Decimal(str(random.uniform(-1, 1)))

        # Calculate spread
        spread_multiplier = Decimal(str(random.uniform(0.8, 1.5)))  # Spread varies
        spread_half = self.current_price * (self.base_spread_bps / Decimal("10000")) / Decimal("2") * spread_multiplier

        best_bid = self.current_price - spread_half
        best_ask = self.current_price + spread_half

        # Generate bids (descending from best bid)
        bids = []
        for i in range(self.levels):
            # Price deteriorates as we go deeper
            price_drop = best_bid * Decimal(str(0.001 * (i + 1)))  # 0.1% increments
            price = best_bid - price_drop

            # Size varies (more size at better prices generally)
            base_size = Decimal(str(random.uniform(500, 2000)))
            size_multiplier = Decimal(str(1 + random.uniform(0, 0.5) * i))  # Deeper = more size
            size = base_size * size_multiplier

            bids.append(OrderbookLevel(price, size))

        # Generate asks (ascending from best ask)
        asks = []
        for i in range(self.levels):
            price_rise = best_ask * Decimal(str(0.001 * (i + 1)))
            price = best_ask + price_rise

            base_size = Decimal(str(random.uniform(500, 2000)))
            size_multiplier = Decimal(str(1 + random.uniform(0, 0.5) * i))
            size = base_size * size_multiplier

            asks.append(OrderbookLevel(price, size))

        self.last_update = now

        return Orderbook(
            symbol=self.symbol,
            timestamp=now,
            bids=bids,
            asks=asks
        )

    def simulate_volatile_period(self):
        """Temporarily increase volatility (simulates news/event)."""
        self.volatility_pct *= Decimal("3")
        self.base_spread_bps *= Decimal("2")

    def restore_calm(self):
        """Return to normal volatility."""
        self.volatility_pct /= Decimal("3")
        self.base_spread_bps /= Decimal("2")
