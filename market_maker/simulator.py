"""
Market Maker Simulator

Run the market making engine with mock orderbook data.
"""

import asyncio
import time
from decimal import Decimal
from typing import Optional

from .engine import MarketMakerEngine
from .orderbook import MockOrderbookGenerator
from .config import MarketMakerConfig, MemecoinConfig


class MarketMakerSimulator:
    """Simulate market making with mock orderbook data."""

    def __init__(self, config: MarketMakerConfig, verbose: bool = True):
        self.config = config
        self.verbose = verbose

        # Create engine with initial balanced position
        initial_price = Decimal("0.001")
        self.engine = MarketMakerEngine(config, initial_token_price=initial_price)

        # Create mock orderbook generator
        self.orderbook_gen = MockOrderbookGenerator(
            symbol=config.symbol,
            base_price=Decimal("0.001"),  # $0.001 for CHOG
            base_spread_bps=Decimal("40"),  # 0.40% natural spread
            volatility_pct=Decimal("2.0"),
            levels=10
        )

        self.running = False
        self.iteration = 0

    async def run(self, duration_seconds: int = 60, updates_per_second: float = 0.5):
        """
        Run simulation for specified duration.

        Args:
            duration_seconds: How long to run simulation
            updates_per_second: How many orderbook updates per second (0.5 = every 2 seconds)
        """
        self.running = True
        start_time = time.time()

        print(f"\n{'='*100}")
        print(f"MARKET MAKER SIMULATION START")
        print(f"Symbol: {self.config.symbol} | Duration: {duration_seconds}s | Update Rate: {updates_per_second}/s")
        print(f"Config: Base Spread: {self.config.base_spread_bps}bps | Gamma: {self.config.gamma} | Order Size: ${self.config.order_size_usd}")
        print(f"{'='*100}\n")

        try:
            while self.running and (time.time() - start_time) < duration_seconds:
                self.iteration += 1

                # Generate new orderbook
                orderbook = self.orderbook_gen.generate()

                # Update engine
                status = self.engine.update_quotes(orderbook)

                # Log
                if self.verbose:
                    status_line = self.engine.get_status_line(status)
                    print(f"[{self.iteration:04d}] {status_line}")

                # Simulate market events
                if self.iteration == 20:
                    print("\n⚡ SIMULATING VOLATILE PERIOD (news event)")
                    self.orderbook_gen.simulate_volatile_period()

                if self.iteration == 35:
                    print("✅ VOLATILITY CALMING DOWN\n")
                    self.orderbook_gen.restore_calm()

                # Sleep until next update
                await asyncio.sleep(1.0 / updates_per_second)

        except KeyboardInterrupt:
            print("\n\nSimulation interrupted by user")

        finally:
            self.running = False
            self._print_summary(status)

    def _print_summary(self, final_status: dict):
        """Print final summary statistics."""
        print(f"\n{'='*100}")
        print("SIMULATION SUMMARY")
        print(f"{'='*100}")
        print(f"Total Duration: {self.iteration} iterations")
        print(f"Total Trades: {final_status['total_trades']}")
        print(f"Total Volume: ${self.engine.state.total_volume_usd:.2f}")
        print(f"Final P&L: ${final_status['pnl']:.2f} ({final_status['pnl_pct']:+.2f}%)")
        print(f"Final Balance: {final_status['token_balance']:.2f} tokens + ${final_status['usdc_balance']:.2f} USDC")
        print(f"Final Value: ${final_status['total_value_usd']:.2f}")
        print(f"Final Skew: {final_status['inventory_skew']:+.3f}")
        print(f"Final Mid Price: ${final_status['mid_price']:.6f}")
        print(f"{'='*100}\n")


async def run_simulation(
    config: Optional[MarketMakerConfig] = None,
    duration_seconds: int = 60,
    updates_per_second: float = 0.5
):
    """
    Convenience function to run a simulation.

    Args:
        config: Market maker config (defaults to MemecoinConfig)
        duration_seconds: How long to run
        updates_per_second: Update frequency
    """
    if config is None:
        config = MemecoinConfig()

    simulator = MarketMakerSimulator(config, verbose=True)
    await simulator.run(duration_seconds, updates_per_second)


if __name__ == "__main__":
    # Run simulation from command line
    asyncio.run(run_simulation(duration_seconds=120, updates_per_second=0.5))
