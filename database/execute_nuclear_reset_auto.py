#!/usr/bin/env python3
"""
Nuclear Reset Script - Auto Mode
Completely wipes all trading data for the default user to start fresh.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.common.db import get_db_connection
from core.common.logger import logger

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"

def nuclear_reset_auto():
    """Execute nuclear reset of all trading data automatically."""
    
    print("🚨 NUCLEAR RESET: This will DELETE ALL trading data!")
    print(f"🎯 Target User: {DEFAULT_USER_ID}")
    print("🤖 Auto-mode: Proceeding without confirmation...")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                
                # Show what we're about to delete
                print("\n📊 Current data to be deleted:")
                cursor.execute("SELECT COUNT(*) FROM trades WHERE user_id = %s", (DEFAULT_USER_ID,))
                trades_count = cursor.fetchone()[0]
                print(f"  - Trades: {trades_count}")
                
                cursor.execute("SELECT COUNT(*) FROM account_states WHERE user_id = %s", (DEFAULT_USER_ID,))
                account_states_count = cursor.fetchone()[0]
                print(f"  - Account States: {account_states_count}")
                
                cursor.execute("SELECT COUNT(*) FROM market_data WHERE user_id = %s", (DEFAULT_USER_ID,))
                market_data_count = cursor.fetchone()[0]
                print(f"  - Market Data: {market_data_count}")
                
                # Execute deletions
                print("\n🔥 Executing nuclear reset...")
                
                # 1. Delete trades
                cursor.execute("DELETE FROM trades WHERE user_id = %s", (DEFAULT_USER_ID,))
                deleted_trades = cursor.rowcount
                print(f"✅ Deleted {deleted_trades} trades")
                
                # 2. Delete account states
                cursor.execute("DELETE FROM account_states WHERE user_id = %s", (DEFAULT_USER_ID,))
                deleted_states = cursor.rowcount
                print(f"✅ Deleted {deleted_states} account states")
                
                # 3. Delete market data
                cursor.execute("DELETE FROM market_data WHERE user_id = %s", (DEFAULT_USER_ID,))
                deleted_market = cursor.rowcount
                print(f"✅ Deleted {deleted_market} market data records")
                
                # 4. Delete any reconciliation data if table exists
                try:
                    cursor.execute("DELETE FROM position_reconciliation WHERE user_id = %s", (DEFAULT_USER_ID,))
                    deleted_recon = cursor.rowcount
                    print(f"✅ Deleted {deleted_recon} reconciliation records")
                except Exception:
                    print("ℹ️  No position_reconciliation table found (expected)")
                
                # Commit all changes
                conn.commit()
                
                # Verify clean state
                print("\n🔍 Verifying clean state...")
                cursor.execute("SELECT COUNT(*) FROM trades WHERE user_id = %s", (DEFAULT_USER_ID,))
                remaining_trades = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM account_states WHERE user_id = %s", (DEFAULT_USER_ID,))
                remaining_states = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM market_data WHERE user_id = %s", (DEFAULT_USER_ID,))
                remaining_market = cursor.fetchone()[0]
                
                print(f"  - Remaining trades: {remaining_trades}")
                print(f"  - Remaining account states: {remaining_states}")
                print(f"  - Remaining market data: {remaining_market}")
                
                if remaining_trades == 0 and remaining_states == 0 and remaining_market == 0:
                    print("\n🎉 NUCLEAR RESET COMPLETE! Database is clean.")
                    logger.info("Nuclear reset completed successfully")
                    return True
                else:
                    print("⚠️  Warning: Some data may remain. Check manually.")
                    logger.warning("Nuclear reset incomplete - some data remains")
                    return False
    
    except Exception as e:
        print(f"❌ Error during nuclear reset: {e}")
        logger.error(f"Nuclear reset failed: {e}")
        return False

if __name__ == "__main__":
    success = nuclear_reset_auto()
    sys.exit(0 if success else 1)