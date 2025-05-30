#!/usr/bin/env python3
"""
Quick fix to update user config to use Binance for indicators MCP instead of BitMEX.

BitMEX requires symbol mapping (BTC/USDT -> BTC/USDT:USDT) but for public indicator data,
Binance is more reliable and uses standard symbols directly.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.common.db import get_db_connection
from core.common.logger import logger

def fix_indicators_exchange():
    """Update default user config to use Binance for indicators MCP."""
    
    user_id = "00000000-0000-0000-0000-000000000001"
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Update the indicators exchange_name from bitmex to binance
                cursor.execute("""
                    UPDATE configurations 
                    SET config_data = jsonb_set(
                        config_data, 
                        '{mcp,indicators,exchange_name}', 
                        '"binance"'
                    ) 
                    WHERE user_id = %s 
                    AND config_name = 'default'
                """, (user_id,))
                
                rows_updated = cursor.rowcount
                conn.commit()
                
                if rows_updated > 0:
                    logger.info(f"✅ Updated indicators exchange_name to 'binance' for user {user_id}")
                    
                    # Verify the change
                    cursor.execute("""
                        SELECT config_data->'mcp'->'indicators'->'exchange_name' as exchange_name
                        FROM configurations 
                        WHERE user_id = %s AND config_name = 'default'
                    """, (user_id,))
                    
                    result = cursor.fetchone()
                    if result:
                        logger.info(f"✅ Verified: indicators exchange_name is now '{result[0]}'")
                    else:
                        logger.error("❌ Could not verify the update")
                else:
                    logger.warning("⚠️ No rows were updated - config may already be correct")
                    
    except Exception as e:
        logger.error(f"❌ Failed to update indicators exchange: {e}")
        raise

if __name__ == "__main__":
    fix_indicators_exchange()