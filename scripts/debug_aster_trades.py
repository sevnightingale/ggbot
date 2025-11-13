#!/usr/bin/env python3
"""Debug script to check Aster trades data"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService
from datetime import datetime, timezone

async def main():
    service = AsterDEXV3LiveTradingService()
    print("Fetching trades from AsterDEX...")
    trades = await service.get_user_trades(limit=1000)

    if not trades:
        print("No trades returned from API")
        return

    total_count = len(trades)
    pnl_trades = [t for t in trades if float(t.get('realizedPnl', 0)) != 0]
    pnl_count = len(pnl_trades)

    print(f"\n=== ASTER TRADES SUMMARY ===")
    print(f"Total trades returned: {total_count}")
    print(f"Trades with non-zero P&L: {pnl_count}")
    print(f"Trades with zero P&L: {total_count - pnl_count}")

    if trades:
        first_time_ms = trades[0].get('time', 0)
        last_time_ms = trades[-1].get('time', 0)
        first_time = datetime.fromtimestamp(first_time_ms / 1000, tz=timezone.utc) if first_time_ms else None
        last_time = datetime.fromtimestamp(last_time_ms / 1000, tz=timezone.utc) if last_time_ms else None

        print(f"First trade time: {first_time}")
        print(f"Last trade time: {last_time}")

        if first_time and last_time:
            duration = last_time - first_time
            print(f"Time range covered: {duration.days} days")

    if pnl_trades:
        print(f"\n=== TRADES WITH P&L (first 15) ===")
        for i, t in enumerate(pnl_trades[:15]):
            trade_time_ms = t.get('time', 0)
            trade_time = datetime.fromtimestamp(trade_time_ms / 1000, tz=timezone.utc) if trade_time_ms else None
            pnl = float(t.get('realizedPnl', 0))
            print(f"{i+1}. {trade_time} | {t.get('symbol')} | P&L: ${pnl:.4f}")

        # Calculate cumulative P&L
        cumulative = 0
        print(f"\n=== CUMULATIVE P&L PROGRESSION ===")
        for i, t in enumerate(pnl_trades):
            cumulative += float(t.get('realizedPnl', 0))
            if i < 10 or i >= len(pnl_trades) - 5:  # Show first 10 and last 5
                trade_time_ms = t.get('time', 0)
                trade_time = datetime.fromtimestamp(trade_time_ms / 1000, tz=timezone.utc) if trade_time_ms else None
                pnl = float(t.get('realizedPnl', 0))
                print(f"{i+1}. {trade_time} | Trade P&L: ${pnl:.4f} | Cumulative: ${cumulative:.4f}")
            elif i == 10:
                print("... (middle trades omitted) ...")

        print(f"\nFinal cumulative P&L: ${cumulative:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
