"""
Market Maker Engine

Core Avellaneda-Stoikov market making logic.
"""

from decimal import Decimal
from dataclasses import dataclass
from typing import Optional, List, Tuple
import time
import math

from .orderbook import Orderbook
from .config import MarketMakerConfig


@dataclass
class Balance:
    """Current holdings."""
    token_amount: Decimal  # Amount of base token (e.g., CHOG)
    usdc_amount: Decimal   # Amount of quote currency (USDC)

    def total_value_usd(self, token_price: Decimal) -> Decimal:
        """Calculate total portfolio value in USD."""
        return self.token_amount * token_price + self.usdc_amount

    def inventory_skew(self, token_price: Decimal) -> Decimal:
        """
        Calculate inventory skew: -1 (all USDC) to +1 (all token).
        0 = perfectly balanced 50/50.
        """
        total_value = self.total_value_usd(token_price)
        if total_value == 0:
            return Decimal("0")

        token_value = self.token_amount * token_price
        # skew = (token_value / total_value) * 2 - 1
        # If token_value = 0%, skew = -1 (all USDC)
        # If token_value = 50%, skew = 0 (balanced)
        # If token_value = 100%, skew = +1 (all token)
        skew = (token_value / total_value) * Decimal("2") - Decimal("1")
        return skew


@dataclass
class Quote:
    """A market maker quote (bid or ask)."""
    side: str  # "buy" or "sell"
    price: Decimal
    size_usd: Decimal
    timestamp: float


@dataclass
class MarketMakerState:
    """Current state of the market maker."""
    balance: Balance
    active_quotes: List[Quote]
    recent_prices: List[Tuple[float, Decimal]]  # (timestamp, price)
    total_trades: int = 0
    total_volume_usd: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")

    def add_price_sample(self, timestamp: float, price: Decimal, max_samples: int = 100):
        """Add a price sample for volatility calculation."""
        self.recent_prices.append((timestamp, price))
        # Keep only recent samples
        if len(self.recent_prices) > max_samples:
            self.recent_prices = self.recent_prices[-max_samples:]

    def calculate_volatility(self, window_seconds: int = 60) -> Decimal:
        """
        Calculate realized volatility over recent window.
        Returns annualized volatility as a decimal (e.g., 0.02 = 2% vol).
        """
        if len(self.recent_prices) < 2:
            return Decimal("0.02")  # Default 2% if not enough data

        now = time.time()
        cutoff = now - window_seconds

        # Filter to window
        recent = [(t, p) for t, p in self.recent_prices if t >= cutoff]

        if len(recent) < 2:
            return Decimal("0.02")

        # Calculate log returns
        log_returns = []
        for i in range(1, len(recent)):
            prev_price = recent[i-1][1]
            curr_price = recent[i][1]
            if prev_price > 0:
                log_return = float((curr_price / prev_price).ln()) if hasattr(curr_price, 'ln') else math.log(float(curr_price / prev_price))
                log_returns.append(log_return)

        if not log_returns:
            return Decimal("0.02")

        # Calculate standard deviation
        mean_return = sum(log_returns) / len(log_returns)
        variance = sum((r - mean_return) ** 2 for r in log_returns) / len(log_returns)
        std_dev = math.sqrt(variance)

        # Annualize (assumes samples are ~per second)
        # std_per_second * sqrt(seconds_per_year)
        seconds_per_year = 365.25 * 24 * 60 * 60
        annualized_vol = Decimal(str(std_dev * math.sqrt(seconds_per_year)))

        return max(annualized_vol, Decimal("0.001"))  # Minimum 0.1% vol


class MarketMakerEngine:
    """
    Avellaneda-Stoikov market making engine.

    Key formulas:
    - Reservation price: r = mid_price - skew * gamma * volatility^2 * total_value
    - Optimal spread: delta = gamma * volatility^2 + (2/gamma) * ln(1 + gamma/k)
    - Bid price: r - delta/2
    - Ask price: r + delta/2
    """

    def __init__(self, config: MarketMakerConfig, initial_token_price: Decimal = Decimal("0.001")):
        self.config = config

        # Initialize state with 50/50 balance (balanced inventory)
        # Half of capital in USDC, half in tokens at current price
        initial_usdc = config.max_inventory_usd / Decimal("2")
        initial_token_value = config.max_inventory_usd / Decimal("2")
        initial_token_amount = initial_token_value / initial_token_price

        self.state = MarketMakerState(
            balance=Balance(
                token_amount=initial_token_amount,
                usdc_amount=initial_usdc,
            ),
            active_quotes=[],
            recent_prices=[]
        )

        self.last_rebalance = time.time()

    def compute_quotes(self, orderbook: Orderbook) -> Tuple[Optional[Quote], Optional[Quote]]:
        """
        Compute optimal bid and ask quotes using Avellaneda-Stoikov.

        Returns:
            (bid_quote, ask_quote) or (None, None) if we should pause quoting
        """
        mid_price = orderbook.mid_price
        now = time.time()

        # Update price history
        self.state.add_price_sample(now, mid_price)

        # Calculate current metrics
        total_value = self.state.balance.total_value_usd(mid_price)
        inventory_skew = self.state.balance.inventory_skew(mid_price)
        volatility = self.state.calculate_volatility(self.config.volatility_window_seconds)
        volatility = max(volatility, self.config.min_volatility)

        # Safety check: pause if too skewed
        if abs(inventory_skew) > self.config.max_inventory_skew:
            return None, None

        # Simplified market making spread calculation
        # Base spread + volatility adjustment
        spread = self.config.base_spread + self.config.volatility_multiplier * (volatility ** 2)
        spread = max(spread, self.config.base_spread)  # Never go below base
        spread = min(spread, Decimal("0.05"))  # Cap at 5% for safety

        # Inventory skew adjustment: tighten the side we want to trade on
        # Positive skew (too much token) → tighten ask, widen bid (encourage selling)
        # Negative skew (too much USDC) → tighten bid, widen ask (encourage buying)
        skew_factor = self.config.gamma * inventory_skew

        # Calculate asymmetric spreads
        bid_spread = spread * (Decimal("1") + skew_factor)
        ask_spread = spread * (Decimal("1") - skew_factor)

        # Ensure spreads stay positive and reasonable
        bid_spread = max(bid_spread, self.config.base_spread * Decimal("0.5"))
        ask_spread = max(ask_spread, self.config.base_spread * Decimal("0.5"))

        # Calculate bid and ask prices
        bid_price = mid_price * (Decimal("1") - bid_spread / Decimal("2"))
        ask_price = mid_price * (Decimal("1") + ask_spread / Decimal("2"))

        # Ensure bid < ask
        if bid_price >= ask_price:
            # Fallback to symmetric spread if something went wrong
            bid_price = mid_price * (Decimal("1") - spread / Decimal("2"))
            ask_price = mid_price * (Decimal("1") + spread / Decimal("2"))

        # Create quotes
        bid_quote = Quote(
            side="buy",
            price=bid_price,
            size_usd=self.config.order_size_usd,
            timestamp=now
        )

        ask_quote = Quote(
            side="sell",
            price=ask_price,
            size_usd=self.config.order_size_usd,
            timestamp=now
        )

        return bid_quote, ask_quote

    def check_fills(self, orderbook: Orderbook) -> List[str]:
        """
        Check if any of our quotes would have been filled.
        In a real system, this would be replaced by exchange fill notifications.

        In simulation: Use probabilistic fills based on how competitive our quotes are.

        Returns:
            List of fill descriptions
        """
        fills = []
        import random

        for quote in self.state.active_quotes:
            filled = False

            if quote.side == "buy":
                # We buy if market asks are at/below our bid
                if orderbook.best_ask.price <= quote.price:
                    filled = True
                # Probabilistic fill if we're close to best bid
                elif quote.price >= orderbook.best_bid.price * Decimal("0.995"):
                    # 50% chance of fill if we're within 0.5% of best bid
                    filled = random.random() < 0.5

                if filled:
                    fill_price = min(quote.price, orderbook.best_ask.price)
                    token_amount = quote.size_usd / fill_price
                    self.state.balance.token_amount += token_amount
                    self.state.balance.usdc_amount -= quote.size_usd
                    self.state.total_trades += 1
                    self.state.total_volume_usd += quote.size_usd
                    fills.append(f"BOUGHT {token_amount:.2f} @ {fill_price:.6f} (${quote.size_usd:.2f})")

            elif quote.side == "sell":
                # We sell if market bids are at/above our ask
                if orderbook.best_bid.price >= quote.price:
                    filled = True
                # Probabilistic fill if we're close to best ask
                elif quote.price <= orderbook.best_ask.price * Decimal("1.005"):
                    filled = random.random() < 0.5

                if filled:
                    fill_price = max(quote.price, orderbook.best_bid.price)
                    token_amount = quote.size_usd / fill_price

                    # Check if we have enough tokens to sell
                    if self.state.balance.token_amount >= token_amount:
                        self.state.balance.token_amount -= token_amount
                        self.state.balance.usdc_amount += quote.size_usd
                        self.state.total_trades += 1
                        self.state.total_volume_usd += quote.size_usd
                        fills.append(f"SOLD {token_amount:.2f} @ {fill_price:.6f} (${quote.size_usd:.2f})")

        return fills

    def update_quotes(self, orderbook: Orderbook) -> dict:
        """
        Main update loop: check fills, compute new quotes, update state.

        Returns:
            Status dict with current state
        """
        # Check if any quotes were filled
        fills = self.check_fills(orderbook)

        # Compute new quotes
        bid_quote, ask_quote = self.compute_quotes(orderbook)

        # Update active quotes
        self.state.active_quotes = []
        if bid_quote:
            self.state.active_quotes.append(bid_quote)
        if ask_quote:
            self.state.active_quotes.append(ask_quote)

        # Calculate current metrics
        mid_price = orderbook.mid_price
        total_value = self.state.balance.total_value_usd(mid_price)
        inventory_skew = self.state.balance.inventory_skew(mid_price)
        volatility = self.state.calculate_volatility(self.config.volatility_window_seconds)
        pnl = total_value - self.config.max_inventory_usd

        return {
            "timestamp": time.time(),
            "mid_price": mid_price,
            "total_value_usd": total_value,
            "pnl": pnl,
            "pnl_pct": (pnl / self.config.max_inventory_usd) * 100,
            "inventory_skew": inventory_skew,
            "volatility": volatility,
            "bid_quote": bid_quote,
            "ask_quote": ask_quote,
            "fills": fills,
            "total_trades": self.state.total_trades,
            "token_balance": self.state.balance.token_amount,
            "usdc_balance": self.state.balance.usdc_amount,
        }

    def should_rebalance(self) -> bool:
        """Check if we should execute a rebalancing trade."""
        now = time.time()
        if now - self.last_rebalance < self.config.rebalance_interval_seconds:
            return False

        # Check if skew is too high
        # Note: in simulation we'd need current price, skip for now
        return False

    def get_status_line(self, status: dict) -> str:
        """Format a concise status line for logging."""
        bid_str = f"{status['bid_quote'].price:.6f}" if status['bid_quote'] else "PAUSED"
        ask_str = f"{status['ask_quote'].price:.6f}" if status['ask_quote'] else "PAUSED"

        skew_str = f"{status['inventory_skew']:+.3f}"
        pnl_str = f"${status['pnl']:.2f} ({status['pnl_pct']:+.2f}%)"

        fills_str = f" | FILLS: {', '.join(status['fills'])}" if status['fills'] else ""

        return (
            f"Mid: {status['mid_price']:.6f} | "
            f"Quotes: {bid_str} / {ask_str} | "
            f"Skew: {skew_str} | "
            f"Vol: {status['volatility']:.4f} | "
            f"PnL: {pnl_str} | "
            f"Trades: {status['total_trades']}"
            f"{fills_str}"
        )
