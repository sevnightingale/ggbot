#!/usr/bin/env python
"""
Start account monitoring service for the default user.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

from core.common.logger import logger
from core.monitoring.service import AccountMonitoringService
from core.common.config import DEFAULT_USER_ID

async def main():
    """Start monitoring service for default user with unified config."""
    logger.info("Starting account monitoring service for default user...")
    
    # Get the unified config ID from database
    from core.common.db import get_db_connection
    
    config_id = None
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT config_id 
                FROM configurations 
                WHERE user_id = %s AND config_type = 'user'
                ORDER BY created_at DESC
                LIMIT 1
            """, (DEFAULT_USER_ID,))
            result = cursor.fetchone()
            if result:
                config_id = result[0]
    
    if not config_id:
        logger.error("No unified config found for default user")
        return
    
    logger.info(f"Using config_id: {config_id}")
    
    # Create monitoring service
    monitoring_service = AccountMonitoringService(
        user_id=DEFAULT_USER_ID,
        config_id=config_id,
        exchange_name="bitmex",
        credentials={
            'apiKey': os.environ.get('EXCHANGE_API'),
            'secret': os.environ.get('EXCHANGE_SECRET')
        },
        monitoring_interval=30,  # 30 seconds
        testnet=True
    )
    
    try:
        # Start monitoring
        logger.info("Starting monitoring...")
        await monitoring_service.start_monitoring()
        
        # Let it run and update the database
        logger.info("Monitoring started. Waiting for first update...")
        await asyncio.sleep(35)  # Wait for first update
        
        # Check if data was written
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*), MAX(updated_at)
                    FROM account_states 
                    WHERE user_id = %s
                """, (DEFAULT_USER_ID,))
                count, latest = cursor.fetchone()
                
                if count > 0:
                    logger.info(f"✅ Account monitoring working! {count} records, latest: {latest}")
                else:
                    logger.error("❌ No account state records created")
        
        # Keep running
        logger.info("Monitoring service running. Press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Stopping monitoring service...")
        
    finally:
        await monitoring_service.stop_monitoring()
        logger.info("Monitoring service stopped")

if __name__ == "__main__":
    asyncio.run(main())