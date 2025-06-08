#!/usr/bin/env python3
"""
Account Monitoring Diagnostic Test

This script checks the account monitoring system to diagnose discrepancies between:
- Exchange positions/orders
- Database trades
- Monitoring service interpretation
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.monitoring.service import AccountMonitoringService
from core.monitoring.adapters import BitMEXAdapter
from core.common.logger import logger
from core.common.db import get_db_connection
import ccxt.async_support as ccxt


# Test configuration
USER_ID = "00000000-0000-0000-0000-000000000001"
CONFIG_ID = "a93de31b-9b8a-42e3-827d-c31e580f5f36"
EXCHANGE = "bitmex"


def log(message: str, data: Any = None):
    """Simple logging wrapper for clean output."""
    print(f"\n{'='*60}")
    print(f"🔍 {message}")
    if data is not None:
        print(f"{'='*60}")
        if isinstance(data, list):
            for i, item in enumerate(data):
                print(f"\n[{i}] {item}")
        elif isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}: {value}")
        else:
            print(data)
    print(f"{'='*60}")


async def check_exchange_directly():
    """Check exchange positions and orders using direct CCXT connection."""
    log("DIRECT EXCHANGE CHECK (via CCXT)")
    
    try:
        # Get credentials from environment
        api_key = os.getenv('EXCHANGE_API')
        api_secret = os.getenv('EXCHANGE_SECRET')
        
        if not api_key or not api_secret:
            log("ERROR: Missing EXCHANGE_API or EXCHANGE_SECRET environment variables")
            return None, None
        
        # Create exchange connection
        exchange = ccxt.bitmex({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'testnet': True
            }
        })
        
        # Load markets
        await exchange.load_markets()
        log("Connected to BitMEX testnet")
        
        # Fetch positions
        positions = await exchange.fetch_positions()
        log(f"Raw positions from exchange ({len(positions)} found):", positions)
        
        # Fetch open orders
        orders = await exchange.fetch_open_orders()
        log(f"Raw open orders from exchange ({len(orders)} found):", orders)
        
        # Close connection
        await exchange.close()
        
        return positions, orders
        
    except Exception as e:
        log(f"ERROR in direct exchange check: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def check_monitoring_service():
    """Check what the monitoring service sees and trigger account state update."""
    log("MONITORING SERVICE CHECK")
    
    try:
        # Initialize monitoring service with correct parameters
        credentials = {
            'apiKey': os.getenv('EXCHANGE_API'),
            'secret': os.getenv('EXCHANGE_SECRET')
        }
        
        service = AccountMonitoringService(
            user_id=USER_ID,
            config_id=CONFIG_ID,
            exchange_name=EXCHANGE,
            credentials=credentials
        )
        
        # Create exchange client first
        service.exchange = await service._create_exchange_client()
        
        # Update account state (this is what we want to test!)
        log("Triggering account state update via monitoring service...")
        await service._update_account_state()
        
        # Get cached account state
        account_state = service.get_cached_account_state()
        log("Account state after monitoring update:", account_state)
        
        # Check what positions the adapter processed
        adapter = service.adapter
        if isinstance(adapter, BitMEXAdapter):
            log("Using BitMEXAdapter")
            
            # Get raw positions that were processed
            try:
                raw_positions = await service.exchange.fetch_positions()
                log(f"Raw positions fetched by monitoring service ({len(raw_positions)} total)")
                
                # Show what positions were processed for lifecycle
                lifecycle_positions = await adapter.get_positions_for_lifecycle(service.exchange)
                log(f"Positions processed by lifecycle manager ({len(lifecycle_positions)} found):", lifecycle_positions)
                
            except Exception as e:
                log(f"ERROR fetching positions via adapter: {e}")
        
        # Clean up
        await service.close()
        
        return account_state
        
    except Exception as e:
        log(f"ERROR in monitoring service check: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_database_trades():
    """Check trades in the database."""
    log("DATABASE TRADES CHECK")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all trades for user
            cursor.execute("""
                SELECT trade_id, symbol, size_contracts, trade_status, 
                       opened_at, closed_at, entry_price,
                       stop_loss, take_profit, collateral_amount, leverage
                FROM trades
                WHERE user_id = %s
                ORDER BY opened_at DESC
                LIMIT 10
            """, (USER_ID,))
            
            trades = cursor.fetchall()
            log(f"Found {len(trades)} trades in database")
            
            for i, trade in enumerate(trades):
                log(f"Trade {i+1}:", dict(trade))
            
            # Get trade orders
            cursor.execute("""
                SELECT to_ord.*, t.symbol as trade_symbol, t.trade_status
                FROM trade_orders to_ord
                LEFT JOIN trades t ON to_ord.trade_id = t.trade_id
                WHERE to_ord.exchange = %s
                ORDER BY to_ord.created_at DESC
                LIMIT 20
            """, (EXCHANGE,))
            
            orders = cursor.fetchall()
            log(f"Found {len(orders)} orders in database")
            
            for i, order in enumerate(orders):
                log(f"Order {i+1}:", dict(order))
            
            return trades, orders
            
    except Exception as e:
        log(f"ERROR in database check: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def check_lifecycle_sync():
    """Check trade lifecycle sync status."""
    log("TRADE LIFECYCLE SYNC CHECK")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get open trades
            cursor.execute("""
                SELECT trade_id, symbol, size_contracts, trade_status,
                       opened_at, entry_price, stop_loss, take_profit
                FROM trades
                WHERE user_id = %s AND trade_status = 'open'
                AND exchange = %s
            """, (USER_ID, EXCHANGE))
            
            open_trades = cursor.fetchall()
            log(f"Open trades in database: {len(open_trades)}")
            
            for trade in open_trades:
                log(f"Open trade {trade['trade_id']}:", dict(trade))
                
                # Check orders for this trade
                cursor.execute("""
                    SELECT exchange_order_id, order_type, side, price, 
                           status, is_risk_order, risk_type
                    FROM trade_orders
                    WHERE trade_id = %s
                """, (trade['trade_id'],))
                
                trade_orders = cursor.fetchall()
                log(f"Orders for trade {trade['trade_id']} ({len(trade_orders)} found):", 
                    [dict(o) for o in trade_orders])
            
            return open_trades
            
    except Exception as e:
        log(f"ERROR in lifecycle sync check: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run all diagnostic checks."""
    print("\n" + "="*80)
    print("🔍 ACCOUNT MONITORING DIAGNOSTIC TEST")
    print("="*80)
    print(f"User ID: {USER_ID}")
    print(f"Config ID: {CONFIG_ID}")
    print(f"Exchange: {EXCHANGE}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # 1. Direct exchange check
    positions, orders = await check_exchange_directly()
    
    # 2. Monitoring service check
    account_state = await check_monitoring_service()
    
    # 3. Database check
    db_trades, db_orders = check_database_trades()
    
    # 4. Lifecycle sync check
    open_trades = check_lifecycle_sync()
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    if positions is not None:
        active_positions = [p for p in positions if p['contracts'] != 0]
        print(f"✓ Exchange positions: {len(active_positions)} active")
        for pos in active_positions:
            print(f"  - {pos['symbol']}: {pos['contracts']} contracts @ {pos['markPrice']}")
    else:
        print("✗ Failed to fetch exchange positions")
    
    if orders is not None:
        print(f"✓ Exchange orders: {len(orders)} open")
        for order in orders:
            print(f"  - {order['symbol']} {order['side']} {order['amount']} @ {order['price']} ({order['type']})")
    else:
        print("✗ Failed to fetch exchange orders")
    
    if db_trades is not None:
        open_db_trades = [t for t in db_trades if t['trade_status'] == 'open']
        print(f"✓ Database trades: {len(db_trades)} total, {len(open_db_trades)} open")
    else:
        print("✗ Failed to fetch database trades")
    
    if account_state:
        print(f"✓ Monitoring service: Last updated {account_state.get('updated_at', 'Unknown')}")
    else:
        print("✗ Monitoring service check failed")
    
    print("\n" + "="*80)
    print("✅ Diagnostic test complete")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())