#!/usr/bin/env python3
"""
Test Paper Trading API Endpoints
Tests the new API endpoints that provide data for the dashboard.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, '/home/sev/ggbot')

from api.paper_trading import _calculate_daily_pnl, _calculate_trade_statistics
from trading.paper.supabase_service import SupabasePaperTradingService
from core.common.logger import logger

load_dotenv()

async def test_api_endpoints():
    """Test the paper trading API endpoint logic"""
    
    config_id = "04b4a272-8303-4770-a536-6d210b9defba"
    
    try:
        service = SupabasePaperTradingService()
        
        logger.info("🚀 Testing Paper Trading API Endpoints")
        
        # Test 1: Get account summary
        logger.info("\n🧪 Testing account summary...")
        account_summary = await service.get_account_summary(config_id)
        logger.info(f"   📊 Account summary: {account_summary}")
        
        # Test 2: Get trade history
        logger.info("\n🧪 Testing trade history...")
        trade_history = await service.get_trade_history(config_id, limit=100)
        logger.info(f"   📊 Found {len(trade_history)} trades")
        
        # Test 3: Calculate daily P&L
        logger.info("\n🧪 Testing daily P&L calculation...")
        daily_pnl = _calculate_daily_pnl(trade_history)
        logger.info(f"   📊 Daily P&L data points: {len(daily_pnl)}")
        for point in daily_pnl[:3]:  # Show first 3
            logger.info(f"     - {point['date']}: ${point['profit']:.2f} (daily: ${point['daily_pnl']:.2f})")
        
        # Test 4: Calculate trade statistics
        logger.info("\n🧪 Testing trade statistics calculation...")
        trade_stats = _calculate_trade_statistics(trade_history, account_summary)
        logger.info(f"   📊 Trade stats:")
        logger.info(f"     - Total trades: {trade_stats['totalTrades']}")
        logger.info(f"     - Win rate: {trade_stats['winRate']}%")
        logger.info(f"     - Total profit: ${trade_stats['totalProfit']:.2f}")
        logger.info(f"     - Avg duration: {trade_stats['avgTradeDuration']}")
        
        # Test 5: Get open positions
        logger.info("\n🧪 Testing open positions...")
        positions = await service.get_open_positions(config_id)
        logger.info(f"   📊 Open positions: {len(positions)}")
        
        # Test 6: Simulate API response structure
        logger.info("\n🧪 Testing API response format...")
        
        # Simulate /metrics endpoint
        if "error" not in account_summary:
            metrics_response = {
                "status": "success",
                "config_id": config_id,
                "metrics": {
                    "profit_loss_data": daily_pnl,
                    "trade_stats": trade_stats,
                    "account_balance": account_summary.get("current_balance", 0.0),
                    "total_pnl": account_summary.get("total_pnl", 0.0),
                    "initial_balance": account_summary.get("initial_balance", 10000.0)
                }
            }
            logger.info(f"   ✅ Metrics endpoint would return: balance=${metrics_response['metrics']['account_balance']:.2f}, P&L=${metrics_response['metrics']['total_pnl']:.2f}")
        
        # Simulate /positions endpoint  
        formatted_positions = []
        for pos in positions:
            entry_price = float(pos["entry_price"])
            current_price = float(pos.get("current_price", entry_price))
            size_usd = float(pos["size_usd"])
            side = pos["side"]
            
            size_contracts = size_usd / entry_price
            if side == "long":
                pnl = (current_price - entry_price) * size_contracts
            else:
                pnl = (entry_price - current_price) * size_contracts
            
            formatted_positions.append({
                "symbol": pos["symbol"],
                "direction": side.upper(),
                "pnl": round(pnl, 2),
                "positionSize": round(size_usd, 2)
            })
        
        logger.info(f"   ✅ Positions endpoint would return {len(formatted_positions)} positions")
        
        # Simulate /trades endpoint
        closed_trades = [t for t in trade_history if t["status"] == "closed"]
        logger.info(f"   ✅ Trades endpoint would return {len(closed_trades)} closed trades")
        
        logger.info("\n🎉 All API endpoint tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ API test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())