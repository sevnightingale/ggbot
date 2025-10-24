"""
Test script to query Symphony API and extract dashboard metrics.

This script demonstrates:
1. What data we can get from Symphony API
2. How to map it to our dashboard metrics
3. What's missing and what workarounds we need

Run with:
    cd /home/sev/ggbot
    source .venv/bin/activate
    python scripts/test_symphony_metrics.py --user-id <UUID> --config-id <UUID>
"""

import asyncio
import aiohttp
import argparse
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, '/home/sev/ggbot')

from core.auth.vault_utils import VaultManager
from core.common.db import get_db_connection
from core.symbols import UniversalSymbolStandardizer


class SymphonyMetricsTest:
    """Test Symphony API and extract dashboard metrics."""

    def __init__(self):
        self.base_url = "https://api.symphony.io"
        self.timeout = 30
        self.standardizer = UniversalSymbolStandardizer()

    async def run_test(self, user_id: str, config_id: str):
        """Run comprehensive test of Symphony data for dashboard metrics."""

        print("\n" + "="*80)
        print("SYMPHONY METRICS TEST - Dashboard Data Extraction")
        print("="*80)

        # Step 1: Get Symphony credentials
        print("\n[1/6] Getting Symphony credentials from Vault...")
        credentials = await VaultManager.get_symphony_credential(user_id)
        if not credentials:
            print("❌ No Symphony credentials found for user")
            return

        api_key = credentials['api_key']
        smart_account = credentials.get('smart_account', 'N/A')
        print(f"✅ API key: {api_key[:8]}... (length: {len(api_key)})")
        print(f"✅ Smart account: {smart_account}")

        # Step 2: Get Symphony agent ID from config
        print("\n[2/6] Loading bot configuration...")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT symphony_agent_id, trading_mode, config_name
                    FROM configurations
                    WHERE config_id = %s
                """, (config_id,))
                result = cur.fetchone()

                if not result:
                    print(f"❌ Configuration not found: {config_id}")
                    return

                symphony_agent_id, trading_mode, config_name = result

        print(f"✅ Bot: {config_name}")
        print(f"✅ Trading mode: {trading_mode}")
        print(f"✅ Symphony agent ID: {symphony_agent_id}")

        if trading_mode != 'live':
            print("⚠️  This is a paper trading bot, not live")
            print("   Symphony API calls will still work if credentials are set")

        # Step 3: Query Symphony positions (basic endpoint)
        print("\n[3/6] Querying Symphony /agent/positions endpoint...")
        positions = await self._get_positions(api_key, symphony_agent_id)

        print(f"\n📊 Positions Response:")
        print(json.dumps(positions, indent=2))

        # Step 4: Query Symphony account summary (advanced endpoint)
        print("\n[4/6] Querying Symphony /agent/all-positions endpoint...")
        if smart_account and smart_account != 'N/A':
            account_summary = await self._get_account_summary(api_key, smart_account)

            print(f"\n📊 Account Summary Response:")
            print(json.dumps(account_summary, indent=2))
        else:
            print("⚠️  No smart account address configured - skipping account summary")
            account_summary = None

        # Step 5: Extract dashboard metrics
        print("\n[5/6] Extracting Dashboard Metrics...")
        metrics = self._extract_dashboard_metrics(positions, account_summary)

        print(f"\n📈 DASHBOARD METRICS:")
        print("-" * 80)
        for key, value in metrics.items():
            print(f"{key:.<40} {value}")

        # Step 6: Map to frontend format
        print("\n[6/6] Mapping to Frontend Format...")
        frontend_data = self._map_to_frontend(metrics, positions)

        print(f"\n🎨 FRONTEND DATA STRUCTURE:")
        print("-" * 80)
        print(json.dumps(frontend_data, indent=2))

        # Analysis and recommendations
        print("\n" + "="*80)
        print("ANALYSIS & RECOMMENDATIONS")
        print("="*80)

        self._print_analysis(positions, account_summary, frontend_data)

    async def _get_positions(self, api_key: str, agent_id: str) -> Dict[str, Any]:
        """Query Symphony /agent/positions endpoint."""
        url = f"{self.base_url}/agent/positions"
        headers = {"x-api-key": api_key}
        params = {"agentId": agent_id, "status": "OPEN"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved {data.get('positionsCount', 0)} positions, {data.get('ordersCount', 0)} orders")
                        return data
                    else:
                        error_text = await response.text()
                        print(f"❌ Symphony API error {response.status}: {error_text}")
                        return {}
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return {}

    async def _get_account_summary(self, api_key: str, user_address: str) -> Optional[Dict[str, Any]]:
        """Query Symphony /agent/all-positions endpoint for account summary."""
        url = f"{self.base_url}/agent/all-positions"
        params = {"userAddress": user_address}

        try:
            async with aiohttp.ClientSession() as session:
                # Note: This endpoint doesn't require x-api-key header
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved account summary")
                        return data
                    else:
                        error_text = await response.text()
                        print(f"❌ Account summary error {response.status}: {error_text}")
                        return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None

    def _extract_dashboard_metrics(self, positions_data: Dict[str, Any], account_summary: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract dashboard metrics from Symphony responses."""

        metrics = {}

        # From account summary (if available)
        if account_summary and account_summary.get('success'):
            summary = account_summary['data']['accountSummary']

            metrics['Total Equity'] = f"${summary.get('totalEquity', 0):.2f}"
            metrics['Initial Capital'] = f"${summary.get('initialCapital', 0):.2f}"
            metrics['Total P&L'] = f"${summary.get('totalPnl', 0):.2f}"
            metrics['Total Realized P&L'] = f"${summary.get('totalRealizedPnl', 0):.2f}"
            metrics['Total Unrealized P&L'] = f"${summary.get('totalUnrealizedPnl', 0):.2f}"
            metrics['Available Balance'] = f"${summary.get('availableBalance', 0):.2f}"
            metrics['Margin Used'] = f"${summary.get('marginUsed', 0):.2f}"
            metrics['Total Volume'] = f"${summary.get('totalVolume', 0):.2f}"
            metrics['Total Fees Paid'] = f"${summary.get('totalFeesPaid', 0):.2f}"

            # Trade counts
            metrics['Open Positions Count'] = summary.get('openPositionsCount', 0)
            metrics['Closed Positions Count'] = summary.get('closedPositionsCount', 0)
            metrics['Liquidated Positions Count'] = summary.get('liquidatedPositionsCount', 0)
            metrics['Total Trades'] = summary.get('totalTrades', 0)

            # Performance metrics
            perf = summary.get('performance', {})
            metrics['ROI'] = f"${perf.get('roi', 0):.2f}"
            metrics['ROI Percent'] = f"{perf.get('roiPercent', 0):.2f}%"
            metrics['Average Trade Size'] = f"${perf.get('averageTradeSize', 0):.2f}"

            # Calculate win rate (if we have closed positions)
            # NOTE: Symphony doesn't provide win/loss breakdown directly
            metrics['Win Rate'] = "N/A (not provided by Symphony)"

        else:
            # Fallback: Extract from positions only
            positions = positions_data.get('positions', [])

            total_pnl = sum(p.get('pnlUSD', 0) for p in positions)
            total_collateral = sum(p.get('collateralAmount', 0) for p in positions)

            metrics['Open Positions Count'] = len(positions)
            metrics['Total Unrealized P&L'] = f"${total_pnl:.2f}"
            metrics['Total Margin Used'] = f"${total_collateral:.2f}"
            metrics['Note'] = "Limited metrics without account summary"

        return metrics

    def _map_to_frontend(self, metrics: Dict[str, Any], positions_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map Symphony data to frontend Account interface."""

        # Extract positions
        positions = positions_data.get('positions', [])

        # Map each position to frontend format
        mapped_positions = []
        for pos in positions:
            mapped_positions.append({
                'trade_id': pos.get('batchId', 'unknown'),
                'symbol': self.standardizer.from_symphony(pos.get('asset', 'BTC')),
                'side': 'long' if pos.get('isLong') else 'short',
                'entry_price': pos.get('entryPrice', 0),
                'current_price': pos.get('currentPrice', 0),
                'unrealized_pnl': pos.get('pnlUSD', 0),
                'size_usd': pos.get('positionSize', 0),
                'leverage': pos.get('leverage', 1),
                'status': pos.get('status', 'unknown'),
                'opened_at': pos.get('createdTimestamp', ''),
                'stop_loss': pos.get('slPrice'),
                'take_profit': pos.get('tpPrice')
            })

        # Map account metrics to frontend Account interface
        # This is what PerformanceChart expects
        account = {
            'current_balance': None,  # Need to extract from metrics
            'total_pnl': None,
            'total_trades': None,
            'win_trades': None,  # ⚠️ NOT PROVIDED BY SYMPHONY
            'loss_trades': None,  # ⚠️ NOT PROVIDED BY SYMPHONY
            'open_positions': len(positions),
            'portfolio_return_pct': None,
            'win_rate': None  # ⚠️ CANNOT CALCULATE WITHOUT WIN/LOSS BREAKDOWN
        }

        return {
            'account': account,
            'positions': mapped_positions,
            'raw_metrics': metrics,
            'warnings': [
                'Symphony does not provide win/loss trade breakdown',
                'Cannot calculate win rate without historical trade outcomes',
                'Need to query /agent/batches and /agent/batch-positions for full trade history'
            ]
        }

    def _print_analysis(self, positions_data: Dict, account_summary: Optional[Dict], frontend_data: Dict):
        """Print analysis and recommendations."""

        print("\n✅ AVAILABLE FROM SYMPHONY:")
        print("-" * 80)
        available = [
            "✓ Total equity (current balance)",
            "✓ Total P&L (realized + unrealized)",
            "✓ Total realized P&L",
            "✓ Total unrealized P&L",
            "✓ Open positions count",
            "✓ Closed positions count (from account summary)",
            "✓ Total trades count (from account summary)",
            "✓ ROI percentage",
            "✓ Individual position details (entry, current, P&L)",
            "✓ Fees paid",
            "✓ Volume traded"
        ]
        for item in available:
            print(f"  {item}")

        print("\n❌ NOT AVAILABLE FROM SYMPHONY:")
        print("-" * 80)
        missing = [
            "✗ Win trades count (need to query historical batches)",
            "✗ Loss trades count (need to query historical batches)",
            "✗ Win rate percentage (need to calculate from batch history)",
            "✗ Equity curve data points (need historical balance snapshots)",
            "✗ Trade close reasons (Symphony doesn't track this)",
            "✗ Decision IDs linkage (we store this in live_trades table)"
        ]
        for item in missing:
            print(f"  {item}")

        print("\n💡 RECOMMENDATIONS:")
        print("-" * 80)
        recommendations = [
            "1. For current balance: Use totalEquity from account summary",
            "2. For total trades: Use totalTrades from account summary",
            "3. For open positions: Query /agent/positions (OPEN status)",
            "4. For closed positions: Query /agent/batches, then /agent/batch-positions for each",
            "5. For win rate: Must iterate through closed batches and check pnlUSD > 0",
            "6. For equity curve: Store periodic balance snapshots in our DB",
            "7. For trade history: Query all batches + positions and cache in live_trades_history table"
        ]
        for item in recommendations:
            print(f"  {item}")

        print("\n🔧 IMPLEMENTATION PLAN:")
        print("-" * 80)
        implementation = [
            "1. Create get_live_account_metrics() endpoint:",
            "   - Query /agent/all-positions for account summary",
            "   - Extract totalEquity, totalPnl, totalTrades, roiPercent",
            "   - Return in same format as paper trading account",
            "",
            "2. Create get_live_trade_history() endpoint:",
            "   - Query /agent/batches to get all batch IDs",
            "   - For each batch, query /agent/batch-positions",
            "   - Filter closed positions, calculate win/loss from pnlUSD",
            "   - Return in same format as paper trade history",
            "",
            "3. Update dashboard to route based on trading_mode:",
            "   - If live: Call get_live_account_metrics()",
            "   - If paper: Call existing get_account_metrics()",
            "   - Unified response format enables code reuse",
            "",
            "4. Cache Symphony data to reduce API calls:",
            "   - Store balance snapshots for equity curve",
            "   - Store closed positions in live_trades_history table",
            "   - Refresh on bot SSE updates"
        ]
        for item in implementation:
            print(f"  {item}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test Symphony API metrics extraction')
    parser.add_argument('--user-id', required=True, help='User UUID')
    parser.add_argument('--config-id', required=True, help='Bot configuration UUID')

    args = parser.parse_args()

    tester = SymphonyMetricsTest()
    await tester.run_test(args.user_id, args.config_id)

    print("\n" + "="*80)
    print("Test complete!")
    print("="*80 + "\n")


if __name__ == '__main__':
    asyncio.run(main())
