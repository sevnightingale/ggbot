#!/usr/bin/env python3
"""
Manual test of the trading module using the EGLD/USDT decision from the logs.
This will test the complete trading pipeline and check Hummingbot database results.
"""

import asyncio
import httpx
import json
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection settings for Hummingbot (port 5434)
HUMMINGBOT_DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'hummingbot',
    'user': 'admin',
    'password': 'admin'
}

# Recreate the trade intent that would have been sent for EGLD/USDT
EGLD_TRADE_INTENT = {
    "decision_id": "test-egld-manual-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
    "user_id": "00000000-0000-0000-0000-000000000001",
    "config_id": "e249bb49-0455-4596-9657-09bf9e14ca14",  # ggShot config
    "timestamp": "2025-08-04T09:01:10Z",
    "mode": "new",
    "symbol": "EGLD/USDT",
    "exchange": "binance",
    "confidence": 0.540,
    "action": "long",
    "stop_loss_price": 13.92,
    "take_profit_price": 14.67,
    "entry_price": 14.295,
    "reasoning": "EGLD/USDT LONG signal with 0.540 confidence - Manual test of trading module functionality",
    "ggshot_signal_validation": True,
    "signal_data": {
        "signal_id": "test-signal",
        "symbol": "EGLD/USDT",
        "signal_type": "ggshot",
        "created_at": "2025-08-04T09:01:10Z"
    },
    "original_signal": "EGLD/USDT LONG - Manual test signal for trading module verification",
    "decision_mode": "new",
    "metadata": {
        "test_run": True,
        "manual_test": True
    }
}

async def test_trading_module():
    """Send the trade intent to the trading module and verify results."""
    print("🚀 Starting manual test of trading module...")
    print(f"📊 Test trade intent for: {EGLD_TRADE_INTENT['symbol']} {EGLD_TRADE_INTENT['action'].upper()}")
    print(f"💰 Entry: ${EGLD_TRADE_INTENT['entry_price']}")
    print(f"🛡️ Stop Loss: ${EGLD_TRADE_INTENT['stop_loss_price']}")
    print(f"🎯 Take Profit: ${EGLD_TRADE_INTENT['take_profit_price']}")
    print(f"📈 Confidence: {EGLD_TRADE_INTENT['confidence']}")
    print()

    try:
        # Send trade intent to trading module
        print("📤 Sending trade intent to trading module...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8000/trading/webhooks/execute-trade",
                json=EGLD_TRADE_INTENT
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Trading module response successful!")
                print(f"📝 Response: {json.dumps(result, indent=2)}")
                trade_id = result.get('trade_id')
                
                # Wait a moment for trade to be processed
                print("\n⏱️ Waiting 5 seconds for trade processing...")
                await asyncio.sleep(5)
                
                # Check results in databases
                await check_ggbot_database(trade_id)
                await check_hummingbot_database()
                
            else:
                print(f"❌ Trading module request failed: {response.status_code}")
                print(f"📄 Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error testing trading module: {e}")

async def check_ggbot_database(trade_id):
    """Check the ggBot database for trade records."""
    print("\n🔍 Checking ggBot database for trade records...")
    
    try:
        # Connect to main ggBot database
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='ggbot',
            user='ggbot_user',
            password='ggbot_password',
            cursor_factory=RealDictCursor
        )
        
        with conn.cursor() as cur:
            # Check trades table
            print("📋 Checking trades table...")
            cur.execute("""
                SELECT trade_id, symbol, side, entry_price, stop_loss, take_profit, 
                       leverage, collateral_amount, trade_status, opened_at
                FROM trades 
                WHERE config_id = %s 
                ORDER BY opened_at DESC 
                LIMIT 5
            """, (EGLD_TRADE_INTENT['config_id'],))
            
            trades = cur.fetchall()
            if trades:
                print(f"✅ Found {len(trades)} recent trades:")
                for trade in trades:
                    print(f"   📊 {trade['symbol']} {trade['side']} - Status: {trade['trade_status']} - Entry: ${trade['entry_price']}")
                    if trade['trade_id'] == trade_id:
                        print(f"   🎯 ^^^ This is our test trade! ^^^")
            else:
                print("⚠️ No trades found in ggBot database")
            
            # Check strategy_runs table for decision audit trail
            print("\n📋 Checking strategy_runs table...")
            cur.execute("""
                SELECT strategy_run_id, scenario, confidence_score, reasoning_log, created_at
                FROM strategy_runs 
                WHERE config_id = %s 
                ORDER BY created_at DESC 
                LIMIT 3
            """, (EGLD_TRADE_INTENT['config_id'],))
            
            runs = cur.fetchall()
            if runs:
                print(f"✅ Found {len(runs)} recent strategy runs:")
                for run in runs:
                    print(f"   📈 {run['scenario']} - Confidence: {run['confidence_score']} - {run['created_at']}")
            else:
                print("⚠️ No strategy runs found")
                
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking ggBot database: {e}")

async def check_hummingbot_database():
    """Check the Hummingbot database for execution records."""
    print("\n🔍 Checking Hummingbot database for execution records...")
    
    try:
        # Connect to Hummingbot database
        conn = psycopg2.connect(**HUMMINGBOT_DB_CONFIG, cursor_factory=RealDictCursor)
        
        with conn.cursor() as cur:
            # Check what tables exist
            print("📋 Available Hummingbot tables:")
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            
            tables = cur.fetchall()
            for table in tables:
                print(f"   📄 {table['table_name']}")
            
            # Check for recent orders (common Hummingbot table)
            table_names = [t['table_name'] for t in tables]
            
            if 'orders' in table_names:
                print("\n📋 Checking orders table...")
                cur.execute("""
                    SELECT * FROM orders 
                    ORDER BY creation_timestamp DESC 
                    LIMIT 5
                """)
                orders = cur.fetchall()
                if orders:
                    print(f"✅ Found {len(orders)} recent orders:")
                    for order in orders[:3]:  # Show first 3
                        print(f"   📊 Order: {dict(order)}")
                else:
                    print("⚠️ No orders found")
            
            if 'trades' in table_names:
                print("\n📋 Checking Hummingbot trades table...")
                cur.execute("""
                    SELECT * FROM trades 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """)
                trades = cur.fetchall()
                if trades:
                    print(f"✅ Found {len(trades)} recent trades:")
                    for trade in trades[:3]:
                        print(f"   💱 Trade: {dict(trade)}")
                else:
                    print("⚠️ No trades found in Hummingbot database")
            
            if 'executors' in table_names:
                print("\n📋 Checking executors table...")
                cur.execute("""
                    SELECT * FROM executors 
                    ORDER BY timestamp DESC 
                    LIMIT 3
                """)
                executors = cur.fetchall()
                if executors:
                    print(f"✅ Found {len(executors)} recent executors:")
                    for executor in executors:
                        print(f"   ⚙️ Executor: {dict(executor)}")
                else:
                    print("⚠️ No executors found")
                    
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking Hummingbot database: {e}")
        print("💡 Note: Hummingbot database might use different table names or might not be initialized yet")

async def check_hummingbot_api_status():
    """Check if Hummingbot API is running and accessible."""
    print("\n🔍 Checking Hummingbot API status...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test basic API health
            response = await client.get(
                "http://localhost:15888/",
                auth=("admin", "admin")
            )
            
            if response.status_code == 200:
                print("✅ Hummingbot API is accessible on port 15888")
                
                # Check account balance for ggShot paper account
                try:
                    balance_response = await client.get(
                        "http://localhost:15888/paper-trade/balance/ggshot_paper_account",
                        auth=("admin", "admin")
                    )
                    
                    if balance_response.status_code == 200:
                        balance_data = balance_response.json()
                        print(f"💰 ggShot paper account balance: {balance_data}")
                    else:
                        print(f"⚠️ Could not get paper account balance: {balance_response.status_code}")
                        
                except Exception as balance_e:
                    print(f"⚠️ Error checking paper account balance: {balance_e}")
                    
            else:
                print(f"❌ Hummingbot API not accessible: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error checking Hummingbot API: {e}")

if __name__ == "__main__":
    print("🧪 Manual Trading Module Test")
    print("=" * 50)
    
    # Run all tests
    asyncio.run(check_hummingbot_api_status())
    asyncio.run(test_trading_module())
    
    print("\n✅ Manual test completed!")