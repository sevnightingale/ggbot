#!/usr/bin/env python
"""
Test the AccountMonitoringService with BitMEX testnet.

This test creates a monitoring service, runs it for a short period,
and verifies that it correctly updates the database with account state.
"""

import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.monitoring.service import AccountMonitoringService
from core.common.logger import logger
from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
import psycopg2
import uuid


async def test_monitoring_service():
    """Test the account monitoring service."""
    
    print("=" * 80)
    print("Account Monitoring Service Test")
    print("=" * 80)
    
    # Test configuration
    user_id = str(uuid.uuid4())
    config_id = str(uuid.uuid4())
    exchange_name = "bitmex"
    
    # Create test user and config first
    await create_test_data(user_id, config_id)
    
    credentials = {
        'apiKey': os.environ.get('EXCHANGE_API'),
        'secret': os.environ.get('EXCHANGE_SECRET')
    }
    
    if not credentials['apiKey'] or not credentials['secret']:
        print("ERROR: Missing EXCHANGE_API or EXCHANGE_SECRET environment variables")
        return
    
    print(f"User ID: {user_id}")
    print(f"Config ID: {config_id}")
    print(f"Exchange: {exchange_name}")
    print(f"API Key: {credentials['apiKey'][:8]}... (hidden)")
    print()
    
    # Create monitoring service with shorter interval for testing
    service = AccountMonitoringService(
        user_id=user_id,
        config_id=config_id,
        exchange_name=exchange_name,
        credentials=credentials,
        monitoring_interval=10,  # 10 seconds for testing
        testnet=True
    )
    
    try:
        # Start monitoring
        print("Starting monitoring service...")
        await service.start_monitoring()
        print("✓ Monitoring started")
        print()
        
        # Let it run for 3 updates (30 seconds)
        print("Running for 30 seconds (3 updates)...")
        for i in range(3):
            print(f"\nUpdate {i + 1} at {datetime.now().isoformat()}")
            
            # Wait for update
            await asyncio.sleep(10)
            
            # Get latest state from database
            state = await service.get_latest_state()
            
            if state:
                print(f"✓ Database updated at {state['updated_at']}")
                print(f"  Equity: {state['equity']:.8f} BTC")
                print(f"  Available Margin: {state['available_margin']:.8f} BTC")
                print(f"  Used Margin: {state['used_margin']:.8f} BTC")
                print(f"  Positions: {len(state['position_data'])}")
                
                # Show position details if any
                if state['position_data']:
                    for pos in state['position_data']:
                        print(f"    - {pos['symbol']}: {pos['contracts']} contracts, "
                              f"PNL: {pos.get('unrealized_pnl', 0):.8f}")
            else:
                print("✗ No data in database yet")
        
        print("\n" + "=" * 80)
        print("Test completed successfully!")
        
        # Show final state details
        final_state = await service.get_latest_state()
        if final_state:
            print("\nFinal account state:")
            print(json.dumps({
                'equity': final_state['equity'],
                'available_margin': final_state['available_margin'],
                'used_margin': final_state['used_margin'],
                'position_count': len(final_state['position_data']),
                'updated_at': final_state['updated_at'].isoformat()
            }, indent=2))
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Stop monitoring
        print("\nStopping monitoring service...")
        await service.stop_monitoring()
        print("✓ Monitoring stopped")
        
        # Clean up test data from database
        print("\nCleaning up test data...")
        await cleanup_test_data(user_id, config_id)


async def create_test_data(user_id: str, config_id: str):
    """Create test user and configuration in database."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    
    try:
        with conn.cursor() as cursor:
            # Create test user
            cursor.execute(
                "INSERT INTO users (user_id, username, email) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (user_id, 'test_user', 'test@example.com')
            )
            
            # Create test configuration
            cursor.execute("""
                INSERT INTO configurations (config_id, user_id, config_type, config_name, config_data)
                VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, (config_id, user_id, 'monitoring', 'test_config', '{}'))
            
            conn.commit()
            print("✓ Test data created")
    
    except Exception as e:
        print(f"Error creating test data: {e}")
        conn.rollback()
    
    finally:
        conn.close()


async def cleanup_test_data(user_id: str, config_id: str):
    """Clean up test data from database."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    
    try:
        with conn.cursor() as cursor:
            # Delete test data in reverse order of creation
            cursor.execute(
                "DELETE FROM account_states WHERE user_id = %s AND config_id = %s",
                (user_id, config_id)
            )
            cursor.execute(
                "DELETE FROM configurations WHERE config_id = %s",
                (config_id,)
            )
            cursor.execute(
                "DELETE FROM users WHERE user_id = %s",
                (user_id,)
            )
            conn.commit()
            print("✓ Test data cleaned up")
    
    except Exception as e:
        print(f"Error cleaning up: {e}")
        conn.rollback()
    
    finally:
        conn.close()


async def test_error_handling():
    """Test error handling with invalid credentials."""
    print("\n" + "=" * 80)
    print("Testing Error Handling")
    print("=" * 80)
    
    # Create service with invalid credentials
    service = AccountMonitoringService(
        user_id=str(uuid.uuid4()),
        config_id=str(uuid.uuid4()),
        exchange_name="bitmex",
        credentials={
            'apiKey': 'invalid_key',
            'secret': 'invalid_secret'
        },
        monitoring_interval=5,
        testnet=True
    )
    
    try:
        print("Starting monitoring with invalid credentials...")
        await service.start_monitoring()
        
        # Wait a bit to see error handling
        await asyncio.sleep(10)
        
    except Exception as e:
        print(f"✓ Expected error: {e}")
    
    finally:
        await service.stop_monitoring()
    
    print("✓ Error handling test completed")


async def main():
    """Run all tests."""
    # Configure logging
    import logging
    logger.configure(handlers=[{"sink": sys.stdout, "level": logging.INFO}])
    
    # Run main test
    await test_monitoring_service()
    
    # Optionally test error handling
    # await test_error_handling()


if __name__ == "__main__":
    asyncio.run(main())