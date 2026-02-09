"""
Hyperliquid Info API — Comprehensive Data Exploration

Tests all read-only SDK methods against a real connected account.
No trades executed. Pure observation.

Usage:
    cd /home/sev/ggbot && source .venv/bin/activate
    python -m scripts.tests.test_hyperliquid_info_api
"""

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta

from hyperliquid.info import Info
from hyperliquid.utils import constants

from core.common.logger import logger
from core.auth.vault_utils import VaultManager
from core.common.db import get_db_connection


def fmt_usd(val):
    """Format a value as USD."""
    if val is None:
        return "N/A"
    return f"${float(val):,.2f}"


def fmt_pct(val):
    """Format a value as percentage."""
    if val is None:
        return "N/A"
    return f"{float(val) * 100:.2f}%"


def fmt_ts(ms_timestamp):
    """Format millisecond timestamp to readable datetime."""
    if ms_timestamp is None:
        return "N/A"
    return datetime.fromtimestamp(ms_timestamp / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


async def get_user_wallet() -> str:
    """Get the first connected Hyperliquid wallet address from DB."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, hyperliquid_wallet_address
                FROM user_profiles
                WHERE hyperliquid_wallet_address IS NOT NULL
                LIMIT 1
            """)
            row = cur.fetchone()
            if not row:
                raise RuntimeError("No Hyperliquid wallet connected in user_profiles")
            user_id, wallet = row
            print(f"  User ID: {user_id}")
            print(f"  Wallet:  {wallet}")
            return wallet


async def main():
    print("=" * 70)
    print("  HYPERLIQUID INFO API — DATA EXPLORATION")
    print("=" * 70)
    print()

    # --- Setup ---
    print("[1] SETUP — Connecting to Hyperliquid Info API...")
    wallet = await get_user_wallet()
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    print(f"  API URL: {constants.MAINNET_API_URL}")
    print(f"  WebSocket: skipped (read-only test)")
    print()

    # --- 1. user_state (Account + Positions) ---
    print("=" * 70)
    print("[2] USER STATE — Account Summary + Open Positions")
    print("=" * 70)
    t0 = time.time()
    user_state = info.user_state(wallet)
    elapsed = (time.time() - t0) * 1000
    print(f"  (latency: {elapsed:.0f}ms)")
    print()

    margin = user_state.get("marginSummary", {})
    cross_margin = user_state.get("crossMarginSummary", {})

    print("  marginSummary:")
    print(f"    accountValue:    {fmt_usd(margin.get('accountValue'))}")
    print(f"    totalMarginUsed: {fmt_usd(margin.get('totalMarginUsed'))}")
    print(f"    totalNtlPos:     {fmt_usd(margin.get('totalNtlPos'))}")
    print(f"    totalRawUsd:     {fmt_usd(margin.get('totalRawUsd'))}")
    print()
    print("  crossMarginSummary:")
    print(f"    accountValue:    {fmt_usd(cross_margin.get('accountValue'))}")
    print(f"    totalMarginUsed: {fmt_usd(cross_margin.get('totalMarginUsed'))}")
    print(f"    totalNtlPos:     {fmt_usd(cross_margin.get('totalNtlPos'))}")
    print(f"    totalRawUsd:     {fmt_usd(cross_margin.get('totalRawUsd'))}")
    print()
    print(f"  withdrawable:      {fmt_usd(user_state.get('withdrawable'))}")
    print()

    positions = user_state.get("assetPositions", [])
    print(f"  Open Positions: {len(positions)}")
    for pos_wrapper in positions:
        pos = pos_wrapper.get("position", {})
        szi = float(pos.get("szi", 0))
        if szi == 0:
            continue
        leverage = pos.get("leverage", {})
        lev_type = leverage.get("type", "?") if isinstance(leverage, dict) else "?"
        lev_val = leverage.get("value", "?") if isinstance(leverage, dict) else leverage

        print(f"    {pos.get('coin')}:")
        print(f"      Side:            {'LONG' if szi > 0 else 'SHORT'}")
        print(f"      Size:            {abs(szi)}")
        print(f"      Entry Price:     {fmt_usd(pos.get('entryPx'))}")
        print(f"      Position Value:  {fmt_usd(pos.get('positionValue'))}")
        print(f"      Margin Used:     {fmt_usd(pos.get('marginUsed'))}")
        print(f"      Unrealized PnL:  {fmt_usd(pos.get('unrealizedPnl'))}")
        print(f"      Return on Equity:{fmt_pct(pos.get('returnOnEquity'))}")
        print(f"      Liquidation Px:  {fmt_usd(pos.get('liquidationPx'))}")
        print(f"      Leverage:        {lev_val}x ({lev_type})")
    if not any(float(p.get("position", {}).get("szi", 0)) != 0 for p in positions):
        print("    (no open positions)")
    print()

    # --- 2. Open Orders (SL/TP) ---
    print("=" * 70)
    print("[3] OPEN ORDERS — Pending Stop-Loss / Take-Profit")
    print("=" * 70)
    t0 = time.time()
    open_orders = info.open_orders(wallet)
    elapsed = (time.time() - t0) * 1000
    print(f"  (latency: {elapsed:.0f}ms)")
    print(f"  Basic open orders: {len(open_orders)}")
    for order in open_orders[:10]:
        side_label = "BUY" if order.get("side") == "B" else "SELL"
        print(f"    {order.get('coin')} {side_label} {order.get('sz')} @ {order.get('limitPx')} (oid: {order.get('oid')})")
    print()

    t0 = time.time()
    frontend_orders = info.frontend_open_orders(wallet)
    elapsed = (time.time() - t0) * 1000
    print(f"  Frontend open orders (detailed): {len(frontend_orders)}")
    print(f"  (latency: {elapsed:.0f}ms)")
    for order in frontend_orders[:10]:
        side_label = "BUY" if order.get("side") == "B" else "SELL"
        trigger_info = ""
        if order.get("isTrigger"):
            trigger_info = f" | trigger @ {order.get('triggerPx')}"
        tpsl_info = ""
        if order.get("isPositionTpsl"):
            tpsl_info = " [TP/SL]"
        print(f"    {order.get('coin')} {side_label} {order.get('sz')} @ {order.get('limitPx')}"
              f" | {order.get('orderType', '?')}{trigger_info}{tpsl_info}"
              f" | reduceOnly={order.get('reduceOnly')} (oid: {order.get('oid')})")
    if not frontend_orders:
        print("    (no open orders)")
    print()

    # --- 3. User Fills (Trade History) ---
    print("=" * 70)
    print("[4] USER FILLS — Recent Trade History")
    print("=" * 70)

    # user_fills (all recent)
    t0 = time.time()
    all_fills = info.user_fills(wallet)
    elapsed = (time.time() - t0) * 1000
    print(f"  Total fills returned: {len(all_fills)}")
    print(f"  (latency: {elapsed:.0f}ms)")
    print()

    for fill in all_fills[:15]:
        closed_pnl = float(fill.get("closedPnl", 0))
        pnl_str = f" | PnL: {fmt_usd(closed_pnl)}" if closed_pnl != 0 else ""
        print(f"    {fmt_ts(fill.get('time'))} | {fill.get('coin')} {fill.get('dir')}"
              f" | {fill.get('sz')} @ {fmt_usd(fill.get('px'))}{pnl_str}"
              f" | hash: {fill.get('hash', '?')[:16]}...")
    print()

    # user_fills_by_time (last 24 hours)
    end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_time = end_time - (24 * 60 * 60 * 1000)  # 24 hours ago

    t0 = time.time()
    recent_fills = info.user_fills_by_time(wallet, start_time, end_time)
    elapsed = (time.time() - t0) * 1000
    print(f"  Fills in last 24h: {len(recent_fills)}")
    print(f"  (latency: {elapsed:.0f}ms)")

    # Also try with aggregation
    t0 = time.time()
    aggregated_fills = info.user_fills_by_time(wallet, start_time, end_time, aggregate_by_time=True)
    elapsed = (time.time() - t0) * 1000
    print(f"  Fills in last 24h (aggregated): {len(aggregated_fills)}")
    print(f"  (latency: {elapsed:.0f}ms)")
    print()

    # --- 4. All Mids (Current Prices) ---
    print("=" * 70)
    print("[5] ALL MIDS — Current Market Prices")
    print("=" * 70)
    t0 = time.time()
    all_mids = info.all_mids()
    elapsed = (time.time() - t0) * 1000
    print(f"  Total coins with mids: {len(all_mids)}")
    print(f"  (latency: {elapsed:.0f}ms)")
    print()

    # Show a few notable ones
    notable = ["BTC", "ETH", "SOL", "DOGE", "HYPE", "ARB", "OP", "AVAX"]
    for coin in notable:
        mid = all_mids.get(coin)
        if mid:
            print(f"    {coin:8s} {fmt_usd(mid)}")
    print(f"    ... and {len(all_mids) - len(notable)} more")
    print()

    # --- 5. Candle Data ---
    print("=" * 70)
    print("[6] CANDLE SNAPSHOT — ETH 1h candles (last 24h)")
    print("=" * 70)
    candle_end = int(datetime.now(timezone.utc).timestamp() * 1000)
    candle_start = candle_end - (24 * 60 * 60 * 1000)

    t0 = time.time()
    candles = info.candles_snapshot("ETH", "1h", candle_start, candle_end)
    elapsed = (time.time() - t0) * 1000
    print(f"  Candles returned: {len(candles)}")
    print(f"  (latency: {elapsed:.0f}ms)")
    print()

    print(f"  {'Time':>22s}  {'Open':>10s}  {'High':>10s}  {'Low':>10s}  {'Close':>10s}  {'Volume':>14s}  Trades")
    print(f"  {'-'*22}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*14}  {'-'*6}")
    for c in candles[-8:]:  # Show last 8 candles
        print(f"  {fmt_ts(c.get('t')):>22s}"
              f"  {fmt_usd(c.get('o')):>10s}"
              f"  {fmt_usd(c.get('h')):>10s}"
              f"  {fmt_usd(c.get('l')):>10s}"
              f"  {fmt_usd(c.get('c')):>10s}"
              f"  {fmt_usd(c.get('v')):>14s}"
              f"  {c.get('n', 0):>6d}")
    print()

    # Also test available intervals
    print("  Testing interval availability:")
    for interval in ["1m", "5m", "15m", "1h", "4h", "1d"]:
        try:
            test_candles = info.candles_snapshot("ETH", interval, candle_start, candle_end)
            print(f"    {interval:>4s}: {len(test_candles)} candles")
        except Exception as e:
            print(f"    {interval:>4s}: ERROR — {e}")
    print()

    # --- 6. Meta + Asset Contexts ---
    print("=" * 70)
    print("[7] META AND ASSET CONTEXTS — Market Info")
    print("=" * 70)
    t0 = time.time()
    meta_ctx = info.meta_and_asset_ctxs()
    elapsed = (time.time() - t0) * 1000
    print(f"  (latency: {elapsed:.0f}ms)")

    universe = meta_ctx[0].get("universe", []) if isinstance(meta_ctx, list) and len(meta_ctx) > 0 else []
    asset_ctxs = meta_ctx[1] if isinstance(meta_ctx, list) and len(meta_ctx) > 1 else []

    print(f"  Total perp markets: {len(universe)}")
    print()

    # Show top 5 by volume
    if asset_ctxs:
        # Pair universe with contexts
        paired = list(zip(universe, asset_ctxs))
        paired.sort(key=lambda x: float(x[1].get("dayNtlVlm", 0)), reverse=True)
        print(f"  Top 10 by 24h Volume:")
        print(f"  {'Coin':>8s}  {'Mid Price':>12s}  {'24h Volume':>16s}  {'Open Interest':>16s}  {'Funding':>10s}  MaxLev")
        print(f"  {'-'*8}  {'-'*12}  {'-'*16}  {'-'*16}  {'-'*10}  {'-'*6}")
        for asset_info, ctx in paired[:10]:
            name = asset_info.get("name", "?")
            max_lev = asset_info.get("maxLeverage", "?")
            mid_px = ctx.get("midPx") or ctx.get("markPx")
            day_vol = ctx.get("dayNtlVlm", "0")
            oi = ctx.get("openInterest", "0")
            funding = ctx.get("funding", "0")
            print(f"  {name:>8s}"
                  f"  {fmt_usd(mid_px):>12s}"
                  f"  {fmt_usd(day_vol):>16s}"
                  f"  {fmt_usd(oi):>16s}"
                  f"  {fmt_pct(funding):>10s}"
                  f"  {max_lev}x")
    print()

    # --- 7. Portfolio Performance ---
    print("=" * 70)
    print("[8] PORTFOLIO — Aggregate Performance")
    print("=" * 70)
    t0 = time.time()
    try:
        portfolio = info.portfolio(wallet)
        elapsed = (time.time() - t0) * 1000
        print(f"  (latency: {elapsed:.0f}ms)")
        print()
        # Print structure (it's a complex nested response)
        if isinstance(portfolio, dict):
            for key in portfolio:
                val = portfolio[key]
                if isinstance(val, (list, dict)):
                    print(f"  {key}: ({type(val).__name__}, {len(val)} items)")
                    # Show first item if list
                    if isinstance(val, list) and len(val) > 0:
                        print(f"    sample: {json.dumps(val[0], indent=2)[:300]}")
                else:
                    print(f"  {key}: {val}")
        else:
            print(f"  Raw response type: {type(portfolio).__name__}")
            print(f"  {json.dumps(portfolio, indent=2)[:500]}")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        print(f"  (latency: {elapsed:.0f}ms)")
        print(f"  ERROR: {e}")
    print()

    # --- 8. User Fees ---
    print("=" * 70)
    print("[9] USER FEES — Trading Fee Schedule")
    print("=" * 70)
    t0 = time.time()
    try:
        fees = info.user_fees(wallet)
        elapsed = (time.time() - t0) * 1000
        print(f"  (latency: {elapsed:.0f}ms)")
        print(f"  Maker rate (add):  {fees.get('userAddRate', '?')}")
        print(f"  Taker rate (cross):{fees.get('userCrossRate', '?')}")
        print(f"  Referral discount: {fees.get('activeReferralDiscount', '?')}")
        daily_vlm = fees.get('dailyUserVlm', [])
        print(f"  Daily volume entries: {len(daily_vlm)}")
        if daily_vlm:
            latest = daily_vlm[-1]
            print(f"    Latest: {latest.get('date')} — taker: {fmt_usd(latest.get('userCross'))}, maker: {fmt_usd(latest.get('userAdd'))}")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        print(f"  (latency: {elapsed:.0f}ms)")
        print(f"  ERROR: {e}")
    print()

    # --- 9. User Funding History (last 7 days) ---
    print("=" * 70)
    print("[10] USER FUNDING — Funding Payments (last 7 days)")
    print("=" * 70)
    funding_start = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp() * 1000)
    t0 = time.time()
    try:
        funding = info.user_funding_history(wallet, funding_start)
        elapsed = (time.time() - t0) * 1000
        print(f"  Funding entries: {len(funding)}")
        print(f"  (latency: {elapsed:.0f}ms)")
        for entry in funding[:5]:
            print(f"    {json.dumps(entry)[:200]}")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        print(f"  (latency: {elapsed:.0f}ms)")
        print(f"  ERROR: {e}")
    print()

    # --- 10. Non-Funding Ledger (deposits, withdrawals) ---
    print("=" * 70)
    print("[11] LEDGER — Non-Funding Updates (last 30 days)")
    print("=" * 70)
    ledger_start = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp() * 1000)
    t0 = time.time()
    try:
        ledger = info.user_non_funding_ledger_updates(wallet, ledger_start)
        elapsed = (time.time() - t0) * 1000
        print(f"  Ledger entries: {len(ledger)}")
        print(f"  (latency: {elapsed:.0f}ms)")
        for entry in ledger[:10]:
            delta = entry.get("delta", {})
            entry_type = delta.get("type", "?")
            amount = delta.get("usdc", "?")
            ts = entry.get("time", 0)
            print(f"    {fmt_ts(ts)} | {entry_type:20s} | {fmt_usd(amount)}")
            # Show extra detail if available
            if entry_type == "deposit":
                print(f"      hash: {delta.get('hash', 'N/A')}")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        print(f"  (latency: {elapsed:.0f}ms)")
        print(f"  ERROR: {e}")
    print()

    # --- 11. Extra Agents (API wallets) ---
    print("=" * 70)
    print("[12] EXTRA AGENTS — Authorized API Wallets")
    print("=" * 70)
    t0 = time.time()
    try:
        agents = info.extra_agents(wallet)
        elapsed = (time.time() - t0) * 1000
        print(f"  Authorized agents: {len(agents)}")
        print(f"  (latency: {elapsed:.0f}ms)")
        for agent in agents:
            valid_until = agent.get("validUntil", 0)
            expiry = datetime.fromtimestamp(valid_until / 1000, tz=timezone.utc) if valid_until > 0 else "permanent"
            print(f"    Name: {agent.get('name', '(unnamed)')}")
            print(f"    Address: {agent.get('address')}")
            print(f"    Valid Until: {expiry}")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        print(f"  (latency: {elapsed:.0f}ms)")
        print(f"  ERROR: {e}")
    print()

    # --- 12. Rate Limit ---
    print("=" * 70)
    print("[13] RATE LIMIT — Current Usage")
    print("=" * 70)
    t0 = time.time()
    try:
        rate_limit = info.user_rate_limit(wallet)
        elapsed = (time.time() - t0) * 1000
        print(f"  (latency: {elapsed:.0f}ms)")
        print(f"  {json.dumps(rate_limit, indent=2)}")
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        print(f"  (latency: {elapsed:.0f}ms)")
        print(f"  ERROR: {e}")
    print()

    # --- Summary ---
    print("=" * 70)
    print("  SUMMARY — Key Metrics for Phase 3 Dashboard")
    print("=" * 70)
    print()
    account_value = float(margin.get("accountValue", 0))
    total_margin = float(margin.get("totalMarginUsed", 0))
    withdrawable = float(user_state.get("withdrawable", 0))
    open_pos_count = sum(1 for p in positions if float(p.get("position", {}).get("szi", 0)) != 0)

    print(f"  Account Value (Total Equity): {fmt_usd(account_value)}")
    print(f"  Margin In Use:                {fmt_usd(total_margin)}")
    print(f"  Available (withdrawable):     {fmt_usd(withdrawable)}")
    print(f"  Open Positions:               {open_pos_count}")
    print(f"  Total Fills (all time):       {len(all_fills)}")
    print(f"  Fills (last 24h):             {len(recent_fills)}")
    print(f"  Open Orders (SL/TP):          {len(frontend_orders)}")
    print(f"  Perp Markets Available:       {len(universe)}")
    print()
    print("  Done!")


if __name__ == "__main__":
    asyncio.run(main())
