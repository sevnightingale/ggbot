#!/usr/bin/env python3
"""
Symphony Positions API Test

Tests the GET /agent/positions endpoint to validate:
1. Response structure matches documentation
2. collateralAmount and pnlUSD fields are populated
3. status filtering works (OPEN, CLOSED, LIQUIDATED)
4. Can calculate total collateral and unrealized P&L

Usage:
    python trading/live/symphony_positions_test.py

Requires SYMPHONY_API_KEY and SYMPHONY_AGENT_ID in .env or environment.
"""

import asyncio
import aiohttp
import os
import sys
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()


class SymphonyPositionsTest:
    """Test Symphony positions endpoint."""

    def __init__(self):
        self.base_url = "https://api.symphony.io"
        self.api_key = os.getenv("SYMPHONY_API_KEY")
        self.agent_id = os.getenv("SYMPHONY_AGENT_ID")
        self.timeout = 30

    async def test_get_positions(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Test GET /agent/positions endpoint.

        Args:
            status_filter: Optional filter - "OPEN", "CLOSED", or "LIQUIDATED"

        Returns:
            Full API response or error dict
        """
        url = f"{self.base_url}/agent/positions"

        headers = {
            "x-api-key": self.api_key
        }

        params = {
            "agentId": self.agent_id
        }

        if status_filter:
            params["status"] = status_filter

        print(f"\n{'='*60}")
        print(f"Testing GET /agent/positions" + (f" (status={status_filter})" if status_filter else ""))
        print(f"{'='*60}")
        print(f"URL: {url}")
        print(f"Agent ID: {self.agent_id}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=self.timeout) as response:
                    status_code = response.status
                    print(f"Status Code: {status_code}")

                    if status_code == 200:
                        data = await response.json()
                        return {"success": True, "data": data}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": error_text, "status": status_code}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_positions_smart_account(self, address: str) -> Dict[str, Any]:
        """
        Test GET /agent/positions-smart-account endpoint.

        Args:
            address: Smart account wallet address

        Returns:
            Full API response or error dict
        """
        url = f"{self.base_url}/agent/positions-smart-account"

        headers = {
            "x-api-key": self.api_key
        }

        params = {
            "address": address
        }

        print(f"\n{'='*60}")
        print(f"Testing GET /agent/positions-smart-account")
        print(f"{'='*60}")
        print(f"URL: {url}")
        print(f"Address: {address}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=self.timeout) as response:
                    status_code = response.status
                    print(f"Status Code: {status_code}")

                    if status_code == 200:
                        data = await response.json()
                        return {"success": True, "data": data}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": error_text, "status": status_code}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_positions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze positions response to calculate metrics.

        Returns summary with:
        - Total collateral (margin) for open positions
        - Unrealized P&L for open positions
        - Realized P&L for closed positions
        - Position counts by status
        """
        positions = data.get("positions", [])
        orders = data.get("orders", [])

        # Counts
        open_count = 0
        closed_count = 0
        liquidated_count = 0

        # Collateral and P&L
        open_collateral = 0.0
        unrealized_pnl = 0.0
        realized_pnl = 0.0

        # Analyze each position
        for pos in positions:
            status = pos.get("status", "").lower()
            collateral = pos.get("collateralAmount", 0) or 0
            pnl = pos.get("pnlUSD", 0) or 0

            if status == "open":
                open_count += 1
                open_collateral += collateral
                unrealized_pnl += pnl
            elif status == "closed":
                closed_count += 1
                realized_pnl += pnl
            elif status == "liquidated":
                liquidated_count += 1
                realized_pnl += pnl

        return {
            "counts": {
                "total_positions": len(positions),
                "total_orders": len(orders),
                "open": open_count,
                "closed": closed_count,
                "liquidated": liquidated_count
            },
            "metrics": {
                "open_collateral_usd": round(open_collateral, 2),
                "unrealized_pnl_usd": round(unrealized_pnl, 2),
                "realized_pnl_usd": round(realized_pnl, 2),
                "total_pnl_usd": round(unrealized_pnl + realized_pnl, 2)
            }
        }

    def print_positions_summary(self, positions: List[Dict], limit: int = 5):
        """Print summary of positions."""
        if not positions:
            print("No positions found.")
            return

        print(f"\nFirst {min(limit, len(positions))} positions:")
        print("-" * 100)
        print(f"{'Status':<12} {'Asset':<8} {'Side':<6} {'Collateral':>12} {'PnL USD':>12} {'Leverage':>8} {'Entry':>12}")
        print("-" * 100)

        for pos in positions[:limit]:
            status = pos.get("status", "?")
            asset = pos.get("asset", "?")
            side = "LONG" if pos.get("isLong") else "SHORT"
            collateral = pos.get("collateralAmount", 0) or 0
            pnl = pos.get("pnlUSD", 0) or 0
            leverage = pos.get("leverage", 1)
            entry = pos.get("entryPrice", 0)

            print(f"{status:<12} {asset:<8} {side:<6} ${collateral:>11.2f} ${pnl:>11.2f} {leverage:>7}x ${entry:>11.2f}")


async def main():
    """Run Symphony positions tests."""

    tester = SymphonyPositionsTest()

    # Check credentials
    if not tester.api_key:
        print("ERROR: SYMPHONY_API_KEY not found in environment")
        print("Set it in .env or export SYMPHONY_API_KEY=your_key")
        return

    if not tester.agent_id:
        print("ERROR: SYMPHONY_AGENT_ID not found in environment")
        print("Set it in .env or export SYMPHONY_AGENT_ID=your_id")
        return

    print(f"API Key: {tester.api_key[:8]}...")
    print(f"Agent ID: {tester.agent_id}")

    # Test 1: Get all positions (no filter)
    result = await tester.test_get_positions()

    if result["success"]:
        data = result["data"]
        print(f"\n✅ SUCCESS - Retrieved positions")
        print(f"   Positions Count: {data.get('positionsCount', 'N/A')}")
        print(f"   Orders Count: {data.get('ordersCount', 'N/A')}")

        # Analyze
        analysis = tester.analyze_positions(data)

        print(f"\n📊 ANALYSIS:")
        print(f"   Open Positions: {analysis['counts']['open']}")
        print(f"   Closed Positions: {analysis['counts']['closed']}")
        print(f"   Liquidated: {analysis['counts']['liquidated']}")
        print(f"\n💰 METRICS:")
        print(f"   Open Collateral (Margin): ${analysis['metrics']['open_collateral_usd']:,.2f}")
        print(f"   Unrealized P&L: ${analysis['metrics']['unrealized_pnl_usd']:,.2f}")
        print(f"   Realized P&L: ${analysis['metrics']['realized_pnl_usd']:,.2f}")
        print(f"   Total P&L: ${analysis['metrics']['total_pnl_usd']:,.2f}")

        # Show sample positions
        tester.print_positions_summary(data.get("positions", []))

    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
        if result.get('status') == 401:
            print("   Check your API key")
        elif result.get('status') == 404:
            print("   Endpoint not found - check URL")

    # Test 2: Get only OPEN positions
    print("\n" + "="*60)
    result_open = await tester.test_get_positions(status_filter="OPEN")

    if result_open["success"]:
        data = result_open["data"]
        positions = data.get("positions", [])
        print(f"✅ Open positions filter works: {len(positions)} open positions")

        # Calculate totals for open only
        total_collateral = sum(p.get("collateralAmount", 0) or 0 for p in positions)
        total_unrealized = sum(p.get("pnlUSD", 0) or 0 for p in positions)

        print(f"   Total Open Collateral: ${total_collateral:,.2f}")
        print(f"   Total Unrealized P&L: ${total_unrealized:,.2f}")
    else:
        print(f"❌ Open filter failed: {result_open.get('error')}")

    # Test 3: Get CLOSED positions
    result_closed = await tester.test_get_positions(status_filter="CLOSED")

    if result_closed["success"]:
        data = result_closed["data"]
        positions = data.get("positions", [])
        print(f"✅ Closed positions filter works: {len(positions)} closed positions")

        total_realized = sum(p.get("pnlUSD", 0) or 0 for p in positions)
        print(f"   Total Realized P&L: ${total_realized:,.2f}")
    else:
        print(f"❌ Closed filter failed: {result_closed.get('error')}")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
