#!/usr/bin/env python3
"""
Test script to verify performance polling from Aster and Symphony APIs.

Tests:
1. Aster: Query account balance, positions, calculate % performance
2. Symphony: Query all-positions, extract roiPercent
3. Verify both include unrealized P&L in their calculations

Usage:
    source .venv/bin/activate
    python scripts/test_performance_polling.py
"""

import asyncio
import os
import sys
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from trading.live.aster_service_v3 import AsterDEXV3LiveTradingService
import aiohttp

# Load environment variables
load_dotenv()

# ANSI colors for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_success(msg: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_info(key: str, value: any):
    """Print key-value pair"""
    print(f"{Colors.CYAN}{key:30}{Colors.END}: {Colors.BOLD}{value}{Colors.END}")


async def test_aster_performance():
    """Test Aster account performance polling"""
    print_section("ASTER DEX PERFORMANCE POLLING")

    try:
        # Get credentials from .env
        api_key = os.getenv('ASTER_BASIC_API_KEY')
        api_secret = os.getenv('ASTER_BASIC_SECRET_KEY')

        if not api_key or not api_secret:
            print_error("Missing ASTER_BASIC_API_KEY or ASTER_BASIC_SECRET_KEY in .env")
            return None

        print_info("API Key (first 8 chars)", api_key[:8] + "...")

        # Initialize service (loads credentials from environment)
        aster = AsterDEXV3LiveTradingService()

        # Query account data using direct API call
        print(f"\n{Colors.YELLOW}Querying Aster account...{Colors.END}")

        # Use service's internal method for generating signature
        import time
        import math

        nonce = math.trunc(time.time() * 1000000)
        params = {}

        signed_params = aster._generate_signature(params, nonce)

        url = f"https://fapi.asterdex.com/fapi/v3/account"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=signed_params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print_error(f"Aster API returned {resp.status}: {error_text}")
                    return None

                account = await resp.json()

        # Extract key data
        total_margin_balance = float(account.get('totalMarginBalance', 0))
        total_unrealized_profit = float(account.get('totalUnrealizedProfit', 0))
        total_wallet_balance = float(account.get('totalWalletBalance', 0))
        available_balance = float(account.get('availableBalance', 0))

        print_success("Successfully fetched Aster account data")
        print_info("Total Margin Balance", f"${total_margin_balance:.2f} (includes unrealized)")
        print_info("Total Unrealized P&L", f"${total_unrealized_profit:.2f}")
        print_info("Total Wallet Balance", f"${total_wallet_balance:.2f}")
        print_info("Available Balance", f"${available_balance:.2f}")

        # Get positions
        print(f"\n{Colors.YELLOW}Querying Aster positions...{Colors.END}")
        positions = await aster._get_position_risk()

        if positions is None:
            positions = []

        print_success(f"Found {len(positions)} open position(s)")

        for i, pos in enumerate(positions, 1):
            symbol = pos.get('symbol')
            position_amt = float(pos.get('positionAmt', 0))
            entry_price = float(pos.get('entryPrice', 0))
            mark_price = float(pos.get('markPrice', 0))
            unrealized = float(pos.get('unRealizedProfit', 0))
            leverage = pos.get('leverage', 'N/A')

            side = "LONG" if position_amt > 0 else "SHORT"

            print(f"\n{Colors.CYAN}Position {i}:{Colors.END}")
            print_info("  Symbol", symbol)
            print_info("  Side", side)
            print_info("  Entry Price", f"${entry_price:.4f}")
            print_info("  Mark Price", f"${mark_price:.4f}")
            print_info("  Leverage", f"{leverage}x")
            print_info("  Unrealized P&L", f"${unrealized:.2f}")

        # Calculate performance %
        # We need initial balance - let's assume it's stored in DB or config
        # For now, let's use wallet balance - unrealized as a rough estimate of initial
        initial_balance_estimate = total_wallet_balance - total_unrealized_profit

        if initial_balance_estimate > 0:
            performance_pct = ((total_margin_balance - initial_balance_estimate) / initial_balance_estimate) * 100

            print(f"\n{Colors.YELLOW}Performance Calculation:{Colors.END}")
            print_info("  Estimated Initial Balance", f"${initial_balance_estimate:.2f}")
            print_info("  Current Balance", f"${total_margin_balance:.2f}")
            print_info("  Performance", f"{performance_pct:+.2f}%")
        else:
            print_error("Cannot calculate performance - need initial balance from DB")
            performance_pct = None

        return {
            'success': True,
            'trading_mode': 'aster',
            'equity': total_margin_balance,
            'unrealized_pnl': total_unrealized_profit,
            'performance_pct': performance_pct,
            'positions_count': len(positions),
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        print_error(f"Aster query failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_symphony_performance():
    """Test Symphony account performance polling"""
    print_section("SYMPHONY PERFORMANCE POLLING")

    try:
        # Get user address - try .env first, then check for a Symphony config in DB
        user_address = os.getenv('SYMPHONY_USER_ADDRESS') or os.getenv('SYMPHONY_WALLET_ADDRESS')

        if not user_address:
            # Try to get from DB if there's an active Symphony config
            print(f"{Colors.YELLOW}No SYMPHONY_USER_ADDRESS in .env, checking database...{Colors.END}")
            from core.common.db import get_db_connection
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT config_data->>'user_wallet_address'
                            FROM configurations
                            WHERE trading_mode = 'symphony'
                            LIMIT 1
                        """)
                        result = cur.fetchone()
                        if result:
                            user_address = result[0]
                            print_success(f"Found Symphony wallet from DB: {user_address}")
            except Exception as e:
                print_error(f"Database query failed: {e}")

        if not user_address:
            print_error("No Symphony user address found (checked .env and database)")
            print(f"{Colors.YELLOW}Skipping Symphony test{Colors.END}")
            return None

        print_info("User Address", user_address)

        # Query performance data (public endpoint, no API key needed)
        print(f"\n{Colors.YELLOW}Querying Symphony all-positions...{Colors.END}")

        url = f"https://api.symphony.io/agent/all-positions"
        params = {"userAddress": user_address}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print_error(f"Symphony API returned {resp.status}: {error_text}")
                    return None

                response = await resp.json()

        if not response.get('success'):
            print_error("Symphony API returned success=false")
            return None

        data = response.get('data', {})
        account_summary = data.get('accountSummary', {})
        open_positions = data.get('openPositions', [])

        # Extract key data
        total_equity = float(account_summary.get('totalEquity', 0))
        initial_capital = float(account_summary.get('initialCapital', 0))
        total_unrealized_pnl = float(account_summary.get('totalUnrealizedPnl', 0))
        total_realized_pnl = float(account_summary.get('totalRealizedPnl', 0))
        total_pnl = float(account_summary.get('totalPnl', 0))
        available_balance = float(account_summary.get('availableBalance', 0))
        margin_used = float(account_summary.get('marginUsed', 0))

        performance = account_summary.get('performance', {})
        roi_percent = float(performance.get('roiPercent', 0))

        print_success("Successfully fetched Symphony account data")
        print_info("Total Equity", f"${total_equity:.2f} (includes unrealized)")
        print_info("Initial Capital", f"${initial_capital:.2f}")
        print_info("Total Unrealized P&L", f"${total_unrealized_pnl:.2f}")
        print_info("Total Realized P&L", f"${total_realized_pnl:.2f}")
        print_info("Total P&L", f"${total_pnl:.2f}")
        print_info("Available Balance", f"${available_balance:.2f}")
        print_info("Margin Used", f"${margin_used:.2f}")
        print_info("ROI Percent", f"{roi_percent:+.2f}%")

        print_success(f"Found {len(open_positions)} open position(s)")

        for i, pos in enumerate(open_positions, 1):
            symbol = pos.get('asset')
            is_long = pos.get('isLong')
            leverage = pos.get('leverage', 'N/A')
            entry_price = float(pos.get('entryPrice', 0))
            current_price = float(pos.get('currentPrice', 0))
            pnl_percentage = float(pos.get('pnlPercentage', 0))
            pnl_usd = float(pos.get('pnlUSDValue', 0))
            collateral = float(pos.get('collateralAmount', 0))

            side = "LONG" if is_long else "SHORT"

            print(f"\n{Colors.CYAN}Position {i}:{Colors.END}")
            print_info("  Symbol", symbol)
            print_info("  Side", side)
            print_info("  Entry Price", f"${entry_price:.4f}")
            print_info("  Current Price", f"${current_price:.4f}")
            print_info("  Leverage", f"{leverage}x")
            print_info("  Collateral", f"${collateral:.2f}")
            print_info("  Unrealized P&L", f"${pnl_usd:.2f} ({pnl_percentage:+.2f}%)")

        return {
            'success': True,
            'trading_mode': 'symphony',
            'equity': total_equity,
            'unrealized_pnl': total_unrealized_pnl,
            'performance_pct': roi_percent,
            'positions_count': len(open_positions),
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        print_error(f"Symphony query failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run tests for both services"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         PERFORMANCE POLLING TEST SCRIPT                    ║")
    print("║   Testing Aster and Symphony API performance queries       ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")

    # Test Aster
    aster_result = await test_aster_performance()

    # Test Symphony
    symphony_result = await test_symphony_performance()

    # Summary
    print_section("SUMMARY")

    if aster_result and aster_result['success']:
        print_success("Aster: Ready for polling")
        print_info("  Equity", f"${aster_result['equity']:.2f}")
        print_info("  Unrealized P&L", f"${aster_result['unrealized_pnl']:.2f}")
        if aster_result['performance_pct'] is not None:
            print_info("  Performance", f"{aster_result['performance_pct']:+.2f}%")
        print_info("  Open Positions", aster_result['positions_count'])
    else:
        print_error("Aster: Failed")

    print()

    if symphony_result and symphony_result['success']:
        print_success("Symphony: Ready for polling")
        print_info("  Equity", f"${symphony_result['equity']:.2f}")
        print_info("  Unrealized P&L", f"${symphony_result['unrealized_pnl']:.2f}")
        print_info("  Performance", f"{symphony_result['performance_pct']:+.2f}%")
        print_info("  Open Positions", symphony_result['positions_count'])
    else:
        print_error("Symphony: Failed")

    print(f"\n{Colors.BOLD}Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")

    # Verdict
    print_section("VERDICT")

    if aster_result and symphony_result:
        print_success("Both services working! Ready to implement polling service.")
        print(f"\n{Colors.YELLOW}Next steps:{Colors.END}")
        print("  1. Create performance_snapshots table")
        print("  2. Create PM2 background poller service")
        print("  3. Update balance-series API endpoint")
        print("  4. Update frontend to chart % performance")
    elif aster_result or symphony_result:
        print(f"{Colors.YELLOW}Partial success - one service working{Colors.END}")
    else:
        print_error("Both services failed - check credentials in .env")


if __name__ == '__main__':
    asyncio.run(main())
