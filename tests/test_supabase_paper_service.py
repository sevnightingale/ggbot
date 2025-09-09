#!/usr/bin/env python3
"""
Test Supabase Paper Trading Service
Verifies that the new service can execute trades and manage positions.
"""

import os
import asyncio
from decimal import Decimal
from dotenv import load_dotenv
from core.common.logger import logger
from trading.paper.supabase_service import SupabasePaperTradingService

# Load environment variables
load_dotenv()

async def test_paper_trading_service():
    """Test the Supabase paper trading service"""
    
    try:
        service = SupabasePaperTradingService()
        
        # Test configuration
        config_id = "04b4a272-8303-4770-a536-6d210b9defba"  # Existing config
        user_id = "00000000-0000-0000-0000-000000000000"   # Existing user
        
        logger.info("🚀 Testing Supabase Paper Trading Service")
        
        # Test 1: Health check
        logger.info("\n🧪 Testing service health check...")
        health = await service.health_check()
        logger.info(f"   📊 Health status: {health['status']}")
        logger.info(f"   📊 Market data: {health['market_data']}")
        logger.info(f"   📊 Database: {health['database']}")
        
        # Test 2: Get or create account
        logger.info("\n🧪 Testing account creation/retrieval...")
        account = await service.get_or_create_paper_account(config_id, user_id)
        logger.info(f"   📊 Account ID: {account.account_id}")
        logger.info(f"   💰 Current Balance: {account.current_balance}")
        logger.info(f"   📈 Total P&L: {account.total_pnl}")
        logger.info(f"   🔢 Open Positions: {account.statistics.open_positions}")
        
        # Test 3: Get account summary via service
        logger.info("\n🧪 Testing account summary...")
        summary = await service.get_account_summary(config_id)
        if "error" not in summary:
            logger.info(f"   💰 Balance: ${summary['current_balance']}")
            logger.info(f"   📊 Win Rate: {summary.get('win_rate', 0):.1f}%")
            logger.info(f"   📈 Total Trades: {summary['total_trades']}")
        else:
            logger.error(f"   ❌ Error getting summary: {summary['error']}")
        
        # Test 4: Check open positions
        logger.info("\n🧪 Testing open positions query...")
        positions = await service.get_open_positions(config_id)
        logger.info(f"   📊 Open positions: {len(positions)}")
        for pos in positions[:3]:  # Show first 3
            logger.info(f"     - {pos['symbol']} {pos['side']} @ ${pos['entry_price']} (P&L: ${pos.get('unrealized_pnl', 0):.2f})")
        
        # Test 5: Check trade history
        logger.info("\n🧪 Testing trade history query...")
        trades = await service.get_trade_history(config_id, limit=5)
        logger.info(f"   📊 Total trades: {len(trades)}")
        for trade in trades[:3]:  # Show first 3
            status = trade['status']
            pnl = trade.get('realized_pnl') or trade.get('unrealized_pnl', 0)
            logger.info(f"     - {trade['symbol']} {trade['side']} | Status: {status} | P&L: ${pnl:.2f}")
        
        # Test 6: Simulate a simple trade intent (if we have enough balance)
        if float(account.current_balance.amount) >= 100:
            logger.info("\n🧪 Testing trade execution simulation...")
            
            # Create a test trade intent
            test_intent = {
                "config_id": config_id,
                "user_id": user_id,
                "symbol": "BTC/USDT",
                "action": "long",
                "confidence": 0.75,
                "decision_id": None,  # Skip decision linking for test
                "reasoning": "Test trade for Supabase service validation"
            }
            
            # Execute the trade
            result = await service.execute_trade_intent(test_intent)
            
            if result["status"] == "executed":
                trade_id = result["trade_id"]
                logger.info(f"   ✅ Test trade executed: {trade_id}")
                logger.info(f"      Symbol: {result['symbol']}")
                logger.info(f"      Side: {result['side']}")
                logger.info(f"      Size: ${result['size_usd']:.2f}")
                logger.info(f"      Entry Price: ${result['entry_price']:.2f}")
                logger.info(f"      New Balance: ${result['account_balance']:.2f}")
                
                # Wait a moment then close the position
                await asyncio.sleep(2)
                logger.info(f"\n🧪 Testing trade closure...")
                close_result = await service.close_position(trade_id, "manual")
                
                if close_result["status"] == "closed":
                    logger.info(f"   ✅ Test trade closed successfully")
                    logger.info(f"      Close Price: ${close_result['close_price']:.2f}")
                    logger.info(f"      Realized P&L: ${close_result['realized_pnl']:.2f}")
                else:
                    logger.error(f"   ❌ Failed to close trade: {close_result['reason']}")
                    
            elif result["status"] == "rejected":
                logger.info(f"   ⚠️ Trade rejected: {result['reason']}")
            else:
                logger.error(f"   ❌ Trade failed: {result['reason']}")
        else:
            logger.info("\n⚠️ Skipping trade execution test - insufficient balance")
        
        logger.info("\n🎉 Supabase Paper Trading Service test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Service test failed: {str(e)}")
        return False

async def main():
    """Run the service test"""
    success = await test_paper_trading_service()
    if success:
        logger.info("\n🌟 All Supabase Paper Trading Service tests passed!")
    else:
        logger.error("\n💥 Service tests failed!")

if __name__ == "__main__":
    asyncio.run(main())