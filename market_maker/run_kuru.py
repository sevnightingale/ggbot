"""
Run market maker on Kuru exchange with real orderbook data.

Usage:
    # Set environment variables:
    export KURU_API_KEY="your_api_key"
    export KURU_API_SECRET="your_api_secret"

    # Run:
    python -m market_maker.run_kuru
"""

import asyncio
import os
import time
from decimal import Decimal

from market_maker.engine import MarketMakerEngine
from market_maker.config import MemecoinConfig
from market_maker.exchanges.kuru import KuruAdapter


async def run_market_maker_on_kuru(
    symbol: str = "CHOG/USDC",
    max_inventory_usd: Decimal = Decimal("10000"),
    order_size_usd: Decimal = Decimal("600")
):
    """
    Run market maker on Kuru exchange.

    Args:
        symbol: Trading pair
        max_inventory_usd: Total capital to deploy
        order_size_usd: Size of each order
    """

    # Initialize Kuru adapter
    kuru = KuruAdapter(
        api_key=os.getenv("KURU_API_KEY"),
        api_secret=os.getenv("KURU_API_SECRET"),
        base_url=os.getenv("KURU_API_URL", "https://api.kuru.finance")
    )

    # Get initial balances to determine starting position
    balances = kuru.get_balances()
    base_currency = symbol.split("/")[0]  # "CHOG"
    quote_currency = symbol.split("/")[1]  # "USDC"

    print(f"\n{'='*100}")
    print(f"KURU MARKET MAKER - STARTING")
    print(f"{'='*100}")
    print(f"Symbol: {symbol}")
    print(f"Starting Balance: {balances.get(base_currency, 0)} {base_currency} + {balances.get(quote_currency, 0)} {quote_currency}")
    print(f"Order Size: ${order_size_usd}")
    print(f"{'='*100}\n")

    # Create config
    config = MemecoinConfig()
    config.symbol = symbol
    config.max_inventory_usd = max_inventory_usd
    config.order_size_usd = order_size_usd

    # Get initial orderbook to determine starting price
    initial_orderbook = kuru.get_orderbook(symbol)
    initial_price = initial_orderbook.mid_price

    # Create engine
    engine = MarketMakerEngine(config, initial_token_price=initial_price)

    # Track our active order IDs
    active_order_ids = []
    iteration = 0
    last_fill_check = time.time()

    try:
        while True:
            iteration += 1

            # 1. Fetch fresh orderbook
            orderbook = kuru.get_orderbook(symbol, depth=10)

            # 2. Check for fills every 5 seconds (or use WebSocket in production)
            now = time.time()
            if now - last_fill_check > 5:
                fills = kuru.get_fills(since=last_fill_check)
                if fills:
                    # Update engine state based on fills
                    for fill in fills:
                        print(f"[FILL] {fill.side.upper()} {fill.filled_size} @ {fill.filled_price} | Fee: ${fill.fee}")

                        # Update balances in engine
                        if fill.side == "buy":
                            engine.state.balance.token_amount += fill.filled_size
                            engine.state.balance.usdc_amount -= fill.filled_size * fill.filled_price
                        else:  # sell
                            engine.state.balance.token_amount -= fill.filled_size
                            engine.state.balance.usdc_amount += fill.filled_size * fill.filled_price

                        engine.state.total_trades += 1
                        engine.state.total_volume_usd += fill.filled_size * fill.filled_price

                last_fill_check = now

            # 3. Compute new quotes
            bid_quote, ask_quote = engine.compute_quotes(orderbook)

            # 4. Cancel all existing orders
            if active_order_ids:
                cancelled = kuru.cancel_all_orders(symbol)
                active_order_ids = []

            # 5. Place new orders
            new_order_ids = []

            if bid_quote:
                try:
                    response = kuru.place_limit_order(
                        symbol=symbol,
                        side="buy",
                        price=bid_quote.price,
                        size=bid_quote.size_usd / bid_quote.price  # Convert USD to token amount
                    )
                    if response.status == "open":
                        new_order_ids.append(response.order_id)
                except Exception as e:
                    print(f"[ERROR] Failed to place bid: {e}")

            if ask_quote:
                try:
                    response = kuru.place_limit_order(
                        symbol=symbol,
                        side="sell",
                        price=ask_quote.price,
                        size=ask_quote.size_usd / ask_quote.price
                    )
                    if response.status == "open":
                        new_order_ids.append(response.order_id)
                except Exception as e:
                    print(f"[ERROR] Failed to place ask: {e}")

            active_order_ids = new_order_ids

            # 6. Update state and log
            total_value = engine.state.balance.total_value_usd(orderbook.mid_price)
            inventory_skew = engine.state.balance.inventory_skew(orderbook.mid_price)
            pnl = total_value - config.max_inventory_usd
            pnl_pct = (pnl / config.max_inventory_usd) * 100

            bid_str = f"{bid_quote.price:.6f}" if bid_quote else "PAUSED"
            ask_str = f"{ask_quote.price:.6f}" if ask_quote else "PAUSED"

            print(
                f"[{iteration:04d}] "
                f"Mid: {orderbook.mid_price:.6f} | "
                f"Quotes: {bid_str} / {ask_str} | "
                f"Skew: {inventory_skew:+.3f} | "
                f"PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) | "
                f"Trades: {engine.state.total_trades}"
            )

            # 7. Sleep until next update (2.5 seconds)
            await asyncio.sleep(float(config.quote_interval_seconds))

    except KeyboardInterrupt:
        print("\n\nShutting down market maker...")

        # Cancel all orders
        kuru.cancel_all_orders(symbol)

        # Print final summary
        print(f"\n{'='*100}")
        print("FINAL SUMMARY")
        print(f"{'='*100}")
        print(f"Total Trades: {engine.state.total_trades}")
        print(f"Total Volume: ${engine.state.total_volume_usd:.2f}")

        final_balances = kuru.get_balances()
        print(f"Final Balance: {final_balances.get(base_currency, 0)} {base_currency} + {final_balances.get(quote_currency, 0)} {quote_currency}")

        final_orderbook = kuru.get_orderbook(symbol)
        final_value = engine.state.balance.total_value_usd(final_orderbook.mid_price)
        final_pnl = final_value - config.max_inventory_usd
        final_pnl_pct = (final_pnl / config.max_inventory_usd) * 100

        print(f"Final P&L: ${final_pnl:.2f} ({final_pnl_pct:+.2f}%)")
        print(f"{'='*100}\n")


if __name__ == "__main__":
    # Validate environment variables
    if not os.getenv("KURU_API_KEY"):
        print("ERROR: KURU_API_KEY not set")
        print("Set with: export KURU_API_KEY='your_key'")
        exit(1)

    if not os.getenv("KURU_API_SECRET"):
        print("ERROR: KURU_API_SECRET not set")
        print("Set with: export KURU_API_SECRET='your_secret'")
        exit(1)

    # Run market maker
    asyncio.run(run_market_maker_on_kuru(
        symbol="CHOG/USDC",
        max_inventory_usd=Decimal("10000"),
        order_size_usd=Decimal("600")
    ))
