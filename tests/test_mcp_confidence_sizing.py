#!/usr/bin/env python3
"""
Test script for confidence-based position sizing across all trading modes.

Usage:
    python test_mcp_confidence_sizing.py [mode]

    mode: paper (default), aster, or symphony

Example:
    python test_mcp_confidence_sizing.py paper
"""

import asyncio
import sys
from agent.service_client import GGBotAPIClient
from core.common.db import get_db_connection
from core.common.logger import logger

# Configuration
CONFIG_ID = "bb2560fd-b053-464f-8a58-8e254e4d36fa"
USER_ID = "00000000-0000-0000-0000-000000000000"
API_BASE_URL = "http://localhost:8000"

async def get_current_balance(mode: str) -> float:
    """Query current account balance for the trading mode."""
    if mode == "paper":
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT current_balance
                    FROM paper_accounts
                    WHERE config_id = %s
                """, (CONFIG_ID,))
                result = cur.fetchone()
                return float(result[0]) if result else 0.0
    else:
        # For live modes, would query from exchange
        return 1000.0  # Placeholder

async def test_execute_trade(client: GGBotAPIClient, test_case: dict, mode: str, balance: float):
    """Execute a single trade test case."""
    print(f"\n{'='*80}")
    print(f"TEST: Confidence {test_case['confidence']:.1f} ({test_case['label']})")
    print(f"{'='*80}")

    # Calculate expected values
    max_pct = 25.0
    leverage = 20
    expected_margin = test_case['confidence'] * (max_pct / 100) * balance
    expected_position = expected_margin * leverage
    expected_risk_pct = (expected_margin / balance) * 100

    print(f"\nExpected Calculations:")
    print(f"  Balance: ${balance:.2f}")
    print(f"  Confidence: {test_case['confidence']:.1f}")
    print(f"  Expected Margin: ${expected_margin:.2f} ({expected_risk_pct:.1f}% of balance)")
    print(f"  Expected Position: ${expected_position:.2f} (margin × {leverage}x)")

    # Execute trade
    print(f"\nExecuting trade...")
    try:
        result = await client.execute_trade(
            config_id=CONFIG_ID,
            symbol=test_case['symbol'],
            side=test_case['side'],
            confidence=test_case['confidence'],
            stop_loss_price=test_case['stop_loss'],
            take_profit_price=test_case['take_profit']
        )

        if result.get('status') == 'success':
            trade = result.get('trade', {})

            # Check if trade actually succeeded
            if trade.get('status') == 'failed':
                print(f"\n❌ TRADE FAILED: {trade.get('reason', 'Unknown error')}")
                return False

            # Extract actual values
            actual_position = trade.get('size_usd', 0)
            actual_margin = trade.get('margin_used', 0)
            actual_leverage = trade.get('leverage', 0)

            print(f"\n✅ TRADE EXECUTED")
            print(f"  Trade ID: {trade.get('trade_id', 'N/A')}")
            print(f"  Entry Price: ${trade.get('entry_price', 'N/A')}")
            print(f"  Actual Position: ${actual_position:.2f}")
            print(f"  Actual Margin: ${actual_margin:.2f}")
            print(f"  Actual Leverage: {actual_leverage}x")

            # Validation
            margin_diff = abs(actual_margin - expected_margin)
            position_diff = abs(actual_position - expected_position)

            margin_match = margin_diff < 0.10  # Within $0.10
            position_match = position_diff < 2.00  # Within $2.00
            leverage_match = actual_leverage == leverage

            print(f"\nValidation:")
            print(f"  Margin match: {'✅ PASS' if margin_match else '❌ FAIL'} (diff: ${margin_diff:.2f})")
            print(f"  Position match: {'✅ PASS' if position_match else '❌ FAIL'} (diff: ${position_diff:.2f})")
            print(f"  Leverage match: {'✅ PASS' if leverage_match else '❌ FAIL'} ({actual_leverage} vs {leverage})")

            return margin_match and position_match and leverage_match
        else:
            print(f"\n❌ API ERROR: {result.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        logger.error(f"Trade execution failed: {e}")
        return False

async def run_tests(mode: str):
    """Run all test cases for the specified trading mode."""
    print(f"\n{'#'*80}")
    print(f"# CONFIDENCE-BASED POSITION SIZING TEST")
    print(f"# Mode: {mode.upper()}")
    print(f"{'#'*80}")

    # Initialize API client
    client = GGBotAPIClient(user_id=USER_ID, base_url=API_BASE_URL)

    # Get current balance
    balance = await get_current_balance(mode)
    print(f"\nCurrent {mode} balance: ${balance:.2f}")

    # Define test cases
    test_cases = [
        {
            'label': 'Very Low Confidence',
            'confidence': 0.2,
            'symbol': 'BTC/USDT',
            'side': 'long',
            'stop_loss': 95000,
            'take_profit': 105000
        },
        {
            'label': 'Medium Confidence',
            'confidence': 0.5,
            'symbol': 'BTC/USDT',
            'side': 'short',
            'stop_loss': 110000,
            'take_profit': 95000
        },
        {
            'label': 'High Confidence',
            'confidence': 0.8,
            'symbol': 'BTC/USDT',
            'side': 'long',
            'stop_loss': 100000,
            'take_profit': 110000
        }
    ]

    # Run tests
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'*'*80}")
        print(f"* TEST CASE {i}/{len(test_cases)}")
        print(f"{'*'*80}")

        passed = await test_execute_trade(client, test_case, mode, balance)
        results.append({
            'case': test_case['label'],
            'confidence': test_case['confidence'],
            'passed': passed
        })

        # Wait between tests to avoid rate limiting
        if i < len(test_cases):
            print("\n⏳ Waiting 2 seconds before next test...")
            await asyncio.sleep(2)

    # Summary
    print(f"\n\n{'#'*80}")
    print(f"# TEST SUMMARY")
    print(f"{'#'*80}\n")

    total = len(results)
    passed = sum(1 for r in results if r['passed'])

    print(f"{'Test Case':<30} {'Confidence':<15} {'Result':<10}")
    print(f"{'-'*55}")
    for result in results:
        status = '✅ PASS' if result['passed'] else '❌ FAIL'
        print(f"{result['case']:<30} {result['confidence']:<15.1f} {status:<10}")

    print(f"\n{'-'*55}")
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! Confidence-based sizing working correctly for {mode} mode.")
        return 0
    else:
        print(f"\n⚠️  SOME TESTS FAILED. Review results above.")
        return 1

async def cleanup_test_trades(mode: str):
    """Optional: Close all test trades created during testing."""
    print(f"\n{'='*80}")
    print("CLEANUP: Closing test trades...")
    print(f"{'='*80}\n")

    if mode == "paper":
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get open trades
                cur.execute("""
                    SELECT trade_id, symbol, side, size_usd
                    FROM paper_trades
                    WHERE config_id = %s
                    AND status = 'open'
                    ORDER BY opened_at DESC
                """, (CONFIG_ID,))

                trades = cur.fetchall()

                if not trades:
                    print("No open test trades to close.")
                    return

                print(f"Found {len(trades)} open trades:")
                for trade in trades:
                    print(f"  - {trade[0][:8]}... {trade[1]} {trade[2]} ${trade[3]:.2f}")

                response = input("\nClose these trades? (y/n): ")
                if response.lower() == 'y':
                    client = GGBotAPIClient(user_id=USER_ID, base_url=API_BASE_URL)
                    for trade in trades:
                        trade_id = trade[0]
                        result = await client.close_position(
                            config_id=CONFIG_ID,
                            position_id=trade_id
                        )
                        if result.get('status') == 'success':
                            print(f"  ✅ Closed {trade_id[:8]}...")
                        else:
                            print(f"  ❌ Failed to close {trade_id[:8]}...")
                else:
                    print("Skipping cleanup.")

def main():
    """Main entry point."""
    # Parse arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "paper"

    if mode not in ["paper", "aster", "symphony"]:
        print(f"Error: Invalid mode '{mode}'. Use: paper, aster, or symphony")
        sys.exit(1)

    # Run tests
    try:
        exit_code = asyncio.run(run_tests(mode))

        # Offer cleanup
        if mode == "paper":
            cleanup = input("\nRun cleanup to close test trades? (y/n): ")
            if cleanup.lower() == 'y':
                asyncio.run(cleanup_test_trades(mode))

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
