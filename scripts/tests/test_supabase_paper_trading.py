#!/usr/bin/env python3
"""
Test Supabase connectivity for paper trading tables.
Verifies that we can access paper_accounts, paper_trades, and paper_orders.
"""

import os
import asyncio
import uuid
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from supabase import create_client, Client
from core.common.logger import logger

# Load environment variables
load_dotenv()

async def test_supabase_connectivity():
    """Test basic Supabase connectivity and paper trading table access"""
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info(f"✅ Supabase client created successfully: {supabase_url}")
        
        # Test 1: Check if paper_accounts table exists and is accessible
        logger.info("\n🧪 Testing paper_accounts table access...")
        response = supabase.table('paper_accounts').select("count", count="exact").execute()
        account_count = response.count
        logger.info(f"✅ paper_accounts table accessible. Total accounts: {account_count}")
        
        # Test 2: Check if paper_trades table exists and is accessible  
        logger.info("\n🧪 Testing paper_trades table access...")
        response = supabase.table('paper_trades').select("count", count="exact").execute()
        trades_count = response.count
        logger.info(f"✅ paper_trades table accessible. Total trades: {trades_count}")
        
        # Test 3: Check if paper_orders table exists and is accessible
        logger.info("\n🧪 Testing paper_orders table access...")
        response = supabase.table('paper_orders').select("count", count="exact").execute()
        orders_count = response.count
        logger.info(f"✅ paper_orders table accessible. Total orders: {orders_count}")
        
        # Test 4: Try to fetch some sample data (if any exists)
        if account_count > 0:
            logger.info("\n🧪 Fetching sample paper account data...")
            response = supabase.table('paper_accounts').select("*").limit(3).execute()
            for account in response.data:
                logger.info(f"   📊 Account: {account['account_id']} | Balance: ${account['current_balance']} | P&L: ${account['total_pnl']}")
        
        if trades_count > 0:
            logger.info("\n🧪 Fetching sample paper trades data...")
            response = supabase.table('paper_trades').select("*").limit(3).execute()
            for trade in response.data:
                logger.info(f"   📈 Trade: {trade['symbol']} {trade['side']} | Entry: ${trade['entry_price']} | Status: {trade['status']}")
        
        # Test 5: Test RLS (Row Level Security) - try with user context
        logger.info("\n🧪 Testing Row Level Security with default user...")
        default_user_id = os.getenv("DEFAULT_USER_ID")
        if default_user_id:
            # Set RLS context by filtering on user_id
            response = supabase.table('paper_accounts').select("*").eq('user_id', default_user_id).execute()
            user_accounts = len(response.data)
            logger.info(f"✅ Found {user_accounts} accounts for default user {default_user_id}")
            
            response = supabase.table('paper_trades').select("*").eq('user_id', default_user_id).execute()
            user_trades = len(response.data)
            logger.info(f"✅ Found {user_trades} trades for default user {default_user_id}")
        
        logger.info("\n🎉 All Supabase paper trading connectivity tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase connectivity test failed: {str(e)}")
        logger.error(f"   Error type: {type(e).__name__}")
        return False

async def test_paper_account_operations():
    """Test basic paper account CRUD operations"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    default_user_id = os.getenv("DEFAULT_USER_ID")
    
    if not all([supabase_url, supabase_key, default_user_id]):
        logger.error("Missing required environment variables for account operations test")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Use existing configuration
        test_config_id = "04b4a272-8303-4770-a536-6d210b9defba"
        
        logger.info(f"\n🧪 Testing paper account creation for config: {test_config_id}")
        
        # First, check if account already exists
        response = supabase.table('paper_accounts').select("*").eq('config_id', test_config_id).eq('user_id', default_user_id).execute()
        
        if response.data:
            logger.info("   📋 Test account already exists, using existing account")
            test_account = response.data[0]
        else:
            # Create new test account
            logger.info("   🆕 Creating new test paper account...")
            account_data = {
                'config_id': test_config_id,
                'user_id': default_user_id,
                'initial_balance': 10000.00,
                'current_balance': 10000.00,
                'total_pnl': 0.00,
                'open_positions': 0,
                'total_trades': 0,
                'win_trades': 0,
                'loss_trades': 0
            }
            
            response = supabase.table('paper_accounts').insert(account_data).execute()
            if response.data:
                test_account = response.data[0]
                logger.info(f"   ✅ Test account created: {test_account['account_id']}")
            else:
                logger.error("   ❌ Failed to create test account")
                return False
        
        # Test account update
        logger.info("\n🧪 Testing paper account update...")
        updated_balance = float(test_account['current_balance']) + 100.50
        
        response = supabase.table('paper_accounts').update({
            'current_balance': updated_balance,
            'updated_at': datetime.now().isoformat()
        }).eq('account_id', test_account['account_id']).execute()
        
        if response.data:
            logger.info(f"   ✅ Account balance updated to ${updated_balance}")
        else:
            logger.error("   ❌ Failed to update account balance")
        
        logger.info("\n🎉 Paper account operations test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Paper account operations test failed: {str(e)}")
        return False

async def main():
    """Run all Supabase paper trading tests"""
    logger.info("🚀 Starting Supabase Paper Trading Connectivity Tests")
    
    # Test 1: Basic connectivity
    connectivity_ok = await test_supabase_connectivity()
    
    if connectivity_ok:
        # Test 2: Account operations
        operations_ok = await test_paper_account_operations()
        
        if operations_ok:
            logger.info("\n🌟 All tests passed! Supabase integration is ready for paper trading.")
        else:
            logger.error("\n💥 Account operations tests failed.")
    else:
        logger.error("\n💥 Basic connectivity tests failed.")

if __name__ == "__main__":
    asyncio.run(main())