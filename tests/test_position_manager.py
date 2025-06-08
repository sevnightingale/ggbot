#!/usr/bin/env python3
"""
Test the unified position manager
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.positioning.manager import UnifiedPositionManager

async def test_position_manager():
    user_id = "00000000-0000-0000-0000-000000000001"
    
    print("🔄 Testing Unified Position Manager")
    
    manager = UnifiedPositionManager(user_id)
    
    # Get position summary
    summary = await manager.get_user_positions()
    
    print(f"\n📊 Position Summary:")
    print(f"Total positions: {summary.total_positions}")
    print(f"Active positions: {summary.active_positions}")
    print(f"Total unrealized PnL: {summary.total_unrealized_pnl}")
    print(f"Last updated: {summary.last_updated}")
    
    if summary.positions:
        print(f"\n📍 Positions:")
        for pos in summary.positions:
            print(f"  {pos.symbol}: {pos.size} contracts ({pos.side})")
            print(f"    Status: {pos.status.value}")
            print(f"    Trade ID: {pos.trade_id}")
            print(f"    Confidence: {pos.confidence_score}")
            print(f"    Sync source: {pos.sync_source}")
    
    # Test reconciliation
    print(f"\n🔄 Testing reconciliation...")
    recon_result = await manager.reconcile_all_positions()
    
    print(f"Reconciliation results:")
    print(f"  Trades processed: {recon_result['trades_processed']}")
    print(f"  Trades updated: {recon_result['trades_updated']}")
    print(f"  Errors: {len(recon_result['errors'])}")
    
    if recon_result['results']:
        print(f"  Changes:")
        for result in recon_result['results']:
            print(f"    {result['trade_id']}: {result['status_change']} ({result['action']})")

if __name__ == "__main__":
    asyncio.run(test_position_manager())