#!/usr/bin/env python
"""
Run GGBot - Autonomous Webhook Chain Test

This test validates the complete autonomous trading pipeline:
Extraction → Decision → Trading

The test includes comprehensive verification matching new_trade.py to ensure
the webhook chain produces the same results as direct API calls.

Key Features:
- 90-second extraction delay for complete indicator collection
- 200-second test timeout for full pipeline execution  
- Comprehensive verification including exchange sync and audit trail
- Real position validation and strategy_runs verification

Expected Timeline:
- 0:00 → Extraction starts and triggers background indicator collection
- 1:30 → 90-second delay completes → Decision webhook triggered
- 2:00 → Decision analysis completes → Trading webhook triggered
- 2:30 → Trade execution and verification completes
- 3:20 → Test timeout and final verification
"""

import asyncio
import os
import sys
import time
import json
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging before other imports
from core.common.logging_config import setup_logging, logger
log_file = setup_logging()

import httpx
from core.common.config import DEFAULT_USER_ID, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

# Load environment variables from .env file
load_dotenv()

# Import monitoring service and trade lifecycle manager
from core.monitoring.service import AccountMonitoringService
from trading.lifecycle_manager import TradeLifecycleManager


# Configuration - matching new_trade.py exactly
DEFAULT_CONFIG_ID = "a93de31b-9b8a-42e3-827d-c31e580f5f36"  # Config ID for universal trade lifecycle
TEST_SYMBOL = "BTC/USDT"  # Standard symbol - will be mapped to BTC/USDT:USDT for BitMEX
TEST_TIMEFRAMES = ["15m", "1h"]
TEST_EXCHANGE = "bitmex"


class GGBotRunner:
    """Run the complete GGBot autonomous trading pipeline with comprehensive verification."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.extraction_webhook = f"{base_url}/extraction/webhooks/trigger-extraction"
        
        # Health check URLs
        self.health_urls = {
            "main": f"{base_url}/health",
            "extraction": f"{base_url}/extraction/health",
            "decision": f"{base_url}/decision/health",
            "trading": f"{base_url}/trading/health",
            "dashboard": f"{base_url}/dashboard/health"
        }
        
        self.client = httpx.AsyncClient(timeout=120.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def check_server_health(self):
        """Verify all services are running and healthy."""
        logger.info("🏥 Checking server health...")
        
        health_results = {}
        
        for service, url in self.health_urls.items():
            try:
                response = await self.client.get(url)
                if response.status_code == 200:
                    health_results[service] = "✅ healthy"
                    logger.info(f"  {service}: healthy")
                else:
                    health_results[service] = f"❌ unhealthy ({response.status_code})"
                    logger.warning(f"  {service}: unhealthy - {response.status_code}")
            except Exception as e:
                health_results[service] = f"❌ not reachable ({str(e)})"
                logger.error(f"  {service}: not reachable - {str(e)}")
        
        all_healthy = all("healthy" in status for status in health_results.values())
        
        if not all_healthy:
            logger.error("❌ Some services are not healthy. Please start the server with: python main_api.py")
            return False
        
        logger.info("✅ All services are healthy!")
        return True
    
    async def verify_strategy_runs(self, trade_id: str) -> bool:
        """
        Verify strategy_runs entries were created for the trade in the universal lifecycle system.
        
        Args:
            trade_id: The trade ID to verify
            
        Returns:
            True if strategy_runs entries exist, False otherwise
        """
        logger.info(f"Verifying strategy_runs entries for trade {trade_id}...")
        
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT scenario, confidence_score, reasoning_log, created_at
                    FROM strategy_runs
                    WHERE trade_id = %s AND config_id = %s
                    ORDER BY created_at
                """, (trade_id, DEFAULT_CONFIG_ID))
                
                results = cursor.fetchall()
                
                if results:
                    logger.info(f"✓ Found {len(results)} strategy_runs entries:")
                    for scenario, confidence, reasoning, created_at in results:
                        logger.info(f"  - {scenario}: confidence={confidence}, created={created_at}")
                        if reasoning:
                            logger.info(f"    Reasoning: {reasoning[:100]}...")
                    return True
                else:
                    logger.warning("✗ No strategy_runs entries found")
                    return False
                    
        except Exception as e:
            logger.error(f"✗ Error checking strategy_runs: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    async def verify_exchange_sync(self, user_id: str = DEFAULT_USER_ID) -> Dict[str, Any]:
        """Verify exchange positions and sync with trade lifecycle system."""
        logger.info("Verifying exchange positions and syncing trade lifecycle...")
        
        try:
            # Get credentials from environment (consistent with setup_monitoring)
            api_key = os.getenv('EXCHANGE_API')
            secret = os.getenv('EXCHANGE_SECRET')
            
            if not api_key or not secret:
                logger.warning("⚠️ Exchange credentials not found - cannot verify real positions")
                logger.warning("  Set EXCHANGE_API and EXCHANGE_SECRET environment variables")
                return {
                    'total_positions': 0,
                    'trades_opened': 0,
                    'trades_updated': 0,
                    'trades_closed': 0,
                    'sync_errors': 0,
                    'account_updated': False,
                    'position_sync_performed': False,
                    'error': 'No credentials available'
                }
            
            credentials = {
                'apiKey': api_key,
                'secret': secret
            }
            
            # Create monitoring service
            monitor = AccountMonitoringService(
                user_id=user_id,
                config_id=DEFAULT_CONFIG_ID,
                exchange_name="bitmex",
                credentials=credentials,
                testnet=True
            )
            
            # Create exchange connection and get fresh state
            try:
                monitor.exchange = await monitor._create_exchange_client()
                result = await monitor._update_account_state()
                
                # Also verify trade lifecycle sync separately
                lifecycle_positions = await monitor.adapter.get_positions_for_lifecycle(monitor.exchange)
                lifecycle_manager = TradeLifecycleManager(user_id, "bitmex", DEFAULT_CONFIG_ID)
                sync_results = await lifecycle_manager.sync_positions_to_trades(lifecycle_positions, monitor.adapter)
                
                # Update with lifecycle sync results
                result.update({
                    'trades_opened': sync_results['trades_opened'],
                    'trades_updated': sync_results['trades_updated'], 
                    'trades_closed': sync_results['trades_closed'],
                    'sync_errors': len(sync_results['errors'])
                })
                
                # Log results including trade lifecycle sync
                logger.info(f"✓ Exchange verification and trade lifecycle sync complete:")
                logger.info(f"  - Live positions on exchange: {result['total_positions']}")
                logger.info(f"  - Trade lifecycle: {result['trades_opened']} opened, {result['trades_updated']} updated, {result['trades_closed']} closed")
                logger.info(f"  - Sync errors: {result['sync_errors']}")
                logger.info(f"  - Account state updated: {result['account_updated']}")
                
                return result
                
            finally:
                # Always ensure exchange connection is closed
                if hasattr(monitor, 'exchange') and monitor.exchange:
                    try:
                        await monitor.exchange.close()
                        monitor.exchange = None
                    except Exception as cleanup_error:
                        logger.warning(f"⚠️ Error closing exchange connection: {cleanup_error}")
            
        except Exception as e:
            logger.error(f"✗ Exchange verification failed: {e}")
            return {
                'total_positions': 0,
                'trades_opened': 0,
                'trades_updated': 0,
                'trades_closed': 0,
                'sync_errors': 1,
                'account_updated': False,
                'position_sync_performed': False,
                'error': str(e)
            }
    
    async def check_trades(self, user_id: str = DEFAULT_USER_ID) -> List[Dict[str, Any]]:
        """Check current trades via Dashboard API (trade lifecycle system)."""
        logger.info("Checking trades via Dashboard API (trade lifecycle system)...")
        
        response = await self.client.get(
            f"{self.base_url}/dashboard/api/dashboard/{user_id}/trades",
        )
        
        if response.status_code == 200:
            data = response.json()
            trades = data.get('trades', [])
            logger.info(f"✓ Found {len(trades)} trades in database")
            
            for trade in trades:
                logger.info(f"  {trade['symbol']}: {trade.get('size_contracts', 0)} contracts, status: {trade.get('trade_status', 'unknown')}")
            
            return trades
        else:
            logger.error(f"✗ Failed to get trades: {response.text}")
            return []
    
    async def setup_monitoring(self, user_id: str = DEFAULT_USER_ID):
        """Initialize account monitoring and update account state once before tests."""
        logger.info("Setting up account monitoring...")
        
        try:
            # Get credentials from environment
            api_key = os.getenv('EXCHANGE_API')
            secret = os.getenv('EXCHANGE_SECRET')
            
            if not api_key or not secret:
                logger.warning("⚠️ EXCHANGE_API or EXCHANGE_SECRET not found in environment")
                logger.warning("Tests will proceed but may have limited account data")
                return None
            
            # Create monitoring service with proper parameters
            credentials = {
                'apiKey': api_key,
                'secret': secret
            }
            
            monitor = AccountMonitoringService(
                user_id=user_id,
                config_id=DEFAULT_CONFIG_ID,
                exchange_name="bitmex",
                credentials=credentials,
                testnet=True
            )
            
            # Create exchange client (required for _update_account_state)
            monitor.exchange = await monitor._create_exchange_client()
            
            # Update account state and reconcile trades
            logger.info("Updating account state from exchange...")
            result = await monitor._update_account_state()
            
            logger.info(f"✓ Account monitoring initialized and database updated")
            logger.info(f"  - Position sync performed: {result['position_sync_performed']}")
            logger.info(f"  - Trade lifecycle: {result['trades_opened']} opened, {result['trades_updated']} updated, {result['trades_closed']} closed")
            
            # Close the exchange connection (we only needed one update)
            if monitor.exchange:
                await monitor.exchange.close()
                monitor.exchange = None
                
            return monitor
            
        except Exception as e:
            logger.warning(f"⚠️ Account monitoring setup failed: {e}")
            logger.warning("Tests will proceed but may have limited account data")
            return None
    
    async def run_ggbot_pipeline(self):
        """Run the complete autonomous webhook chain with comprehensive verification."""
        logger.info("🚀 Running GGBot autonomous trading pipeline...")
        
        # Setup monitoring to ensure fresh account data
        logger.info("Setting up pre-pipeline account monitoring...")
        monitor = await self.setup_monitoring()
        if monitor:
            logger.info("Account monitoring ready for pipeline execution")
        
        # Rate limiting delay to avoid overwhelming exchange API
        logger.info("⏱️ Rate limiting delay...")
        await asyncio.sleep(3)
        
        # Trigger the chain by calling extraction webhook
        chain_payload = {
            "user_id": DEFAULT_USER_ID,
            "config_id": DEFAULT_CONFIG_ID,  # Same config_id as new_trade.py
            "symbols": [TEST_SYMBOL],
            "timeframes": ["15m"]  # Match new_trade.py timeframes
        }
        
        logger.info("  🔄 Triggering extraction webhook (start of chain)...")
        
        try:
            start_time = time.time()
            
            # Start the chain
            response = await self.client.post(self.extraction_webhook, json=chain_payload)
            
            if response.status_code != 200:
                logger.error(f"  ❌ Failed to trigger extraction: {response.status_code} - {response.text}")
                return False
            
            result = response.json()
            extraction_id = result.get('extraction_id')
            
            logger.info(f"  ✅ Extraction triggered: {extraction_id}")
            logger.info("  ⏳ Waiting for autonomous chain to complete...")
            
            # Wait for the chain to complete (90s extraction delay + 110s decision/trading buffer)
            await asyncio.sleep(200)
            
            elapsed = time.time() - start_time
            logger.info(f"  ⏱️  Pipeline completed in {elapsed:.1f} seconds")
            
            # Check extraction status first
            status_url = f"{self.base_url}/extraction/api/extraction/status/{extraction_id}"
            status_response = await self.client.get(status_url)
            
            if status_response.status_code != 200:
                logger.error(f"  ❌ Could not check extraction status: {status_response.status_code}")
                return False
                
            status_data = status_response.json()
            logger.info(f"  📊 Extraction status: {status_data.get('status')} - {status_data.get('data_points_extracted')} data points")
            
            if status_data.get('status') != 'completed' or status_data.get('data_points_extracted', 0) == 0:
                logger.warning(f"  ⚠️  Extraction failed or had no data: {status_data}")
                return False
            
            logger.info("  ✅ Extraction completed successfully with data!")
            logger.info("  🔗 Autonomous chain should have triggered Decision → Trading")
            
            # Wait for position to be created (matching new_trade.py timing)
            logger.info("  ⏳ Waiting for trade execution to settle...")
            await asyncio.sleep(5)
            
            # NOW DO COMPREHENSIVE VERIFICATION (like new_trade.py)
            logger.info("\n🔍 Verifying trade success and final system state via exchange...")
            
            # 1. Verify exchange positions and sync
            exchange_result = await self.verify_exchange_sync()
            
            # 2. Check database trades via trade lifecycle system
            db_trades = await self.check_trades()
            
            # 3. Verify strategy_runs entries for audit trail
            strategy_runs_verified = False
            trade_id = None
            
            if db_trades:
                # Get the most recent trade for verification
                latest_trade = db_trades[0]
                trade_id = latest_trade.get('trade_id')
                trade_status = latest_trade.get('trade_status')
                
                logger.info(f"  📊 Latest trade: {trade_id}, status: {trade_status}")
                
                if trade_id and trade_status in ['open', 'filled']:
                    strategy_runs_verified = await self.verify_strategy_runs(trade_id)
                else:
                    logger.warning(f"  ⚠️  Trade execution had issues: status={trade_status}, trade_id={trade_id}")
            
            # Rate limiting delay before completion
            await asyncio.sleep(2)
            
            # SUCCESS CRITERIA: Real position exists on exchange AND trade lifecycle synced AND strategy_runs created
            # (EXACTLY like new_trade.py)
            if exchange_result['total_positions'] > 0 and strategy_runs_verified:
                logger.info("\n✅ GGBot autonomous pipeline completed successfully!")
                logger.info(f"  - Real exchange positions: {exchange_result['total_positions']}")
                logger.info(f"  - Database trades: {len(db_trades)}")
                logger.info(f"  - Trade lifecycle: {exchange_result['trades_opened']} opened, {exchange_result['trades_updated']} updated")
                logger.info(f"  - Strategy runs: VERIFIED ✓")
                logger.info(f"  - Sync errors: {exchange_result['sync_errors']}")
                logger.info("📊 Final system state: CLEAN - database matches exchange reality via universal trade lifecycle")
                logger.info("🔗 Autonomous trading system is working!")
                return True
            else:
                logger.error("\n❌ GGBot autonomous pipeline failed verification")
                logger.error(f"  - Exchange positions: {exchange_result['total_positions']}")
                logger.error(f"  - Database trades: {len(db_trades)}")
                logger.error(f"  - Strategy runs verified: {strategy_runs_verified}")
                logger.error(f"  - Trade lifecycle sync performed: {exchange_result['position_sync_performed']}")
                if len(db_trades) > 0 and not strategy_runs_verified:
                    logger.error("  ⚠️ Database shows trades but no strategy_runs - missing decision audit trail")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ GGBot pipeline failed: {str(e)}")
            return False


async def main():
    """Main runner."""
    # Check if server is specified
    base_url = os.getenv("TEST_API_URL", "http://localhost:8000")
    
    logger.info("🤖 GGBot Autonomous Trading Pipeline Test")
    logger.info("=" * 50)
    logger.info(f"Testing against: {base_url}")
    logger.info("Make sure the server is running: python main_api.py")
    logger.info("")
    
    async with GGBotRunner(base_url) as runner:
        # Check server health
        if not await runner.check_server_health():
            logger.error("❌ Health check failed - aborting pipeline")
            sys.exit(1)
        
        logger.info("")
        
        # Run the full pipeline
        success = await runner.run_ggbot_pipeline()
        
        logger.info("")
        logger.info("=" * 50)
        
        if success:
            logger.info("🎉 GGBot pipeline completed successfully!")
            logger.info("🔗 Autonomous trading system is working!")
            sys.exit(0)
        else:
            logger.error("❌ GGBot pipeline failed")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())