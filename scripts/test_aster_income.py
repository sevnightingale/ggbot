#!/usr/bin/env python3
"""Test AsterDEX income history endpoint"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService
from datetime import datetime, timezone

async def main():
    service = AsterDEXV3LiveTradingService()

    # Query realized P&L from bot start (Nov 3, 2025)
    start_time_ms = int(datetime(2025, 11, 3, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)

    print(f"Fetching income history (REALIZED_PNL) from {datetime.fromtimestamp(start_time_ms/1000, tz=timezone.utc)}...")
    income_records = await service.get_income_history(
        income_type="REALIZED_PNL",
        start_time=start_time_ms,
        limit=1000
    )

    if not income_records:
        print("No income records returned")
        return

    print(f"\n=== REALIZED P&L RECORDS ===")
    print(f"Total records: {len(income_records)}")

    # Calculate cumulative P&L
    cumulative = 0
    print(f"\n=== P&L HISTORY (all records) ===")
    for i, record in enumerate(income_records):
        income_time_ms = record.get('time', 0)
        income_time = datetime.fromtimestamp(income_time_ms / 1000, tz=timezone.utc) if income_time_ms else None
        income_amount = float(record.get('income', 0))
        cumulative += income_amount

        symbol = record.get('symbol', 'N/A')
        asset = record.get('asset', 'N/A')

        print(f"{i+1}. {income_time} | {symbol} | P&L: ${income_amount:.4f} | Cumulative: ${cumulative:.4f}")

    print(f"\n=== SUMMARY ===")
    print(f"Total P&L records: {len(income_records)}")
    print(f"Final cumulative P&L: ${cumulative:.4f}")

    # Compare to userTrades
    print(f"\n=== COMPARISON WITH userTrades ===")
    user_trades = await service.get_user_trades(limit=1000)
    if user_trades:
        pnl_trades = [t for t in user_trades if float(t.get('realizedPnl', 0)) != 0]
        trades_cumulative = sum(float(t.get('realizedPnl', 0)) for t in user_trades)
        print(f"userTrades endpoint: {len(pnl_trades)} trades with P&L, cumulative: ${trades_cumulative:.4f}")
        print(f"income endpoint: {len(income_records)} P&L records, cumulative: ${cumulative:.4f}")
        print(f"Difference: {len(income_records) - len(pnl_trades)} missing records recovered!")

if __name__ == "__main__":
    asyncio.run(main())
