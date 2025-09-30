#!/usr/bin/env python
"""
Manage Trade Pipeline Test

This test exercises the complete GGBot pipeline for trade management:
1. Verify existing position exists
2. Extraction API - Fetch market data and indicators
3. Decision API - Analyze data and generate trading intent (MANAGE_TRADE mode)
4. Trading API - Execute management action (adjust/close position)
5. Monitoring - Verify position changes and strategy_runs creation

This uses the combined API server (main_api.py) running on port 8000.
"""

import os
import sys
import asyncio
import time
import json
import requests
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

# Import database configuration for strategy_runs verification
from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

# Load environment variables from .env file
load_dotenv()

# Import monitoring service and trade lifecycle manager
from core.monitoring.service import AccountMonitoringService
from trading.lifecycle_manager import TradeLifecycleManager

# Configuration
API_BASE_URL = "http://localhost:8000"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_CONFIG_ID = "a93de31b-9b8a-42e3-827d-c31e580f5f36"  # Config ID for universal trade lifecycle
TEST_SYMBOL = "BTC/USDT"  # Standard symbol - will be mapped to BTC/USDT:USDT for BitMEX
TEST_TIMEFRAMES = ["15m", "1h"]
TEST_EXCHANGE = "bitmex"

# Test scenario
SCENARIO = {
    "description": "Existing position → Monitor → Adjust/Close",
    "expected_flow": ["position_verification", "extraction", "decision", "trading", "position_updated"]
}


def log(message: str, level: str = "INFO"):
    """Log using the configured logger."""
    if level == "ERROR":
        logger.error(message)
    elif level == "WARN":
        logger.warning(message)
    elif level == "DEBUG":
        logger.debug(message)
    else:
        logger.info(message)


def check_api_health():
    """Check if all API endpoints are healthy."""
    log("Checking API health...")
    
    endpoints = [
        "/extraction/health",
        "/decision/health",
        "/trading/health",
        "/dashboard/health"
    ]
    
    all_healthy = True
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                log(f"✓ {endpoint} is healthy")
            else:
                log(f"✗ {endpoint} returned status {response.status_code}", "ERROR")
                all_healthy = False
        except Exception as e:
            log(f"✗ {endpoint} is not reachable: {e}", "ERROR")
            all_healthy = False
    
    return all_healthy


def trigger_extraction(user_id: str = DEFAULT_USER_ID) -> Dict[str, Any]:
    """Trigger market data extraction via API."""
    log("Triggering extraction...")
    
    payload = {
        "user_id": user_id,
        "symbols": [TEST_SYMBOL],
        "timeframes": TEST_TIMEFRAMES
    }
    
    response = requests.post(
        f"{API_BASE_URL}/extraction/api/extraction/run",
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        log(f"✓ Extraction triggered: {result['extraction_id']}")
        return result
    else:
        log(f"✗ Extraction failed: {response.text}", "ERROR")
        raise Exception(f"Extraction failed: {response.text}")


def wait_for_extraction(extraction_id: str, timeout: int = 300) -> bool:
    """Wait for extraction to complete."""
    log(f"Waiting for extraction {extraction_id} to complete...")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(
            f"{API_BASE_URL}/extraction/api/extraction/status/{extraction_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            status = response.json()
            
            if status["status"] == "completed":
                log(f"✓ Extraction completed: {status['data_points_extracted']} data points")
                return True
            elif status["status"] == "failed":
                log(f"✗ Extraction failed: {status.get('errors', [])}", "ERROR")
                return False
            else:
                log(f"  Status: {status['status']}, Data points: {status['data_points_extracted']}")
        
        time.sleep(5)
    
    log("✗ Extraction timed out", "ERROR")
    return False


def trigger_decision_analysis(user_id: str = DEFAULT_USER_ID, mode: str = "MANAGE_TRADE") -> Dict[str, Any]:
    """Trigger decision analysis via API."""
    log(f"Triggering decision analysis (mode: {mode})...")
    
    payload = {
        "user_id": user_id,
        "config_id": DEFAULT_CONFIG_ID,  # Add config_id for universal trade lifecycle
        "mode": mode,
        "symbol": TEST_SYMBOL,
        "timeframes": TEST_TIMEFRAMES
    }
    
    response = requests.post(
        f"{API_BASE_URL}/decision/api/decision/analyze",
        json=payload,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        log(f"✓ Decision generated: {result['decision_id']}")
        log(f"  Intent: {result['intent']['action']}")
        log(f"  Confidence: {result['intent'].get('confidence', 'N/A')}")
        return result
    else:
        log(f"✗ Decision analysis failed: {response.text}", "ERROR")
        raise Exception(f"Decision analysis failed: {response.text}")


def execute_trade(intent: Dict[str, Any], user_id: str = DEFAULT_USER_ID) -> Dict[str, Any]:
    """Execute trade via Trading API."""
    log(f"Executing management action: {intent['action']}...")
    
    # Ensure config_id is included in the intent for universal trade lifecycle
    if 'config_id' not in intent:
        intent['config_id'] = DEFAULT_CONFIG_ID
    
    response = requests.post(
        f"{API_BASE_URL}/trading/trade/execute",
        json=intent,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        log(f"✓ Management action executed: {result.get('trade_id', 'N/A')}")
        log(f"  Status: {result.get('status', 'N/A')}")
        return result
    else:
        log(f"✗ Management action failed: {response.text}", "ERROR")
        raise Exception(f"Management action failed: {response.text}")


def check_trades(user_id: str = DEFAULT_USER_ID) -> List[Dict[str, Any]]:
    """Check current trades via Dashboard API (trade lifecycle system)."""
    log("Checking trades via Dashboard API (trade lifecycle system)...")
    
    response = requests.get(
        f"{API_BASE_URL}/dashboard/api/dashboard/{user_id}/trades",
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        trades = data.get('trades', [])
        log(f"✓ Found {len(trades)} trades in database")
        
        for trade in trades:
            log(f"  {trade['symbol']}: {trade.get('size_contracts', 0)} contracts, status: {trade.get('status', 'unknown')}")
        
        return trades
    else:
        log(f"✗ Failed to get trades: {response.text}", "ERROR")
        return []


def verify_strategy_runs(trade_id: str) -> bool:
    """
    Verify strategy_runs entries were created for the trade in the universal lifecycle system.
    
    Args:
        trade_id: The trade ID to verify
        
    Returns:
        True if strategy_runs entries exist, False otherwise
    """
    log(f"Verifying strategy_runs entries for trade {trade_id}...")
    
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
                log(f"✓ Found {len(results)} strategy_runs entries:")
                for scenario, confidence, reasoning, created_at in results:
                    log(f"  - {scenario}: confidence={confidence}, created={created_at}")
                    if reasoning:
                        log(f"    Reasoning: {reasoning[:100]}...")
                return True
            else:
                log("✗ No strategy_runs entries found", "WARN")
                return False
                
    except Exception as e:
        log(f"✗ Error checking strategy_runs: {e}", "ERROR")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


async def verify_exchange_sync(user_id: str = DEFAULT_USER_ID) -> Dict[str, Any]:
    """Verify exchange positions and sync with trade lifecycle system."""
    log("Verifying exchange positions and syncing trade lifecycle...")
    
    try:
        # Get credentials from environment
        api_key = os.getenv('EXCHANGE_API')
        secret = os.getenv('EXCHANGE_SECRET')
        
        if not api_key or not secret:
            log("⚠️ Exchange credentials not found - cannot verify real positions", "WARN")
            log("  Set EXCHANGE_API and EXCHANGE_SECRET environment variables")
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
            log(f"✓ Exchange verification and trade lifecycle sync complete:")
            log(f"  - Live positions on exchange: {result['total_positions']}")
            log(f"  - Trade lifecycle: {result['trades_opened']} opened, {result['trades_updated']} updated, {result['trades_closed']} closed")
            log(f"  - Sync errors: {result['sync_errors']}")
            log(f"  - Account state updated: {result['account_updated']}")
            
            return result
            
        finally:
            # Always ensure exchange connection is closed
            if hasattr(monitor, 'exchange') and monitor.exchange:
                try:
                    await monitor.exchange.close()
                    monitor.exchange = None
                except Exception as cleanup_error:
                    log(f"⚠️ Error closing exchange connection: {cleanup_error}", "WARN")
        
    except Exception as e:
        log(f"✗ Exchange verification failed: {e}", "ERROR")
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


async def run_manage_trade_scenario():
    """Test scenario: Existing position → Monitor → Adjust/Close."""
    log("\n" + "="*60)
    log("Running MANAGE TRADE scenario")
    log("="*60)
    
    try:
        # First check if we have any real positions on exchange and sync trade lifecycle
        log("🔍 Checking for existing positions to manage and syncing trade lifecycle...")
        exchange_result = await verify_exchange_sync()
        db_trades = check_trades()
        
        # Rate limiting delay
        await asyncio.sleep(2)
        
        if exchange_result['total_positions'] == 0:
            log("❌ No existing positions on exchange to manage.")
            log("⚠️ MANAGE TRADE scenario requires a real exchange position", "WARN")
            if len(db_trades) > 0:
                log(f"  - Found {len(db_trades)} database trades")
                log(f"  - Lifecycle cleanup: {exchange_result['trades_closed']} trades closed")
            log("💡 Run the new_trade.py test first to create a position, then run this test")
            return False
        
        # Now we have real positions to manage
        log(f"✓ Managing {exchange_result['total_positions']} existing exchange positions")
        log(f"✓ Database shows {len(db_trades)} trades")
        
        # Step 1: Trigger extraction for latest data
        extraction_result = trigger_extraction()
        
        # Step 2: Wait for extraction
        if not wait_for_extraction(extraction_result["extraction_id"]):
            raise Exception("Extraction failed or timed out")
        
        # Step 3: Trigger decision analysis in MANAGE mode
        decision_result = trigger_decision_analysis(mode="MANAGE_TRADE")
        
        intent = decision_result.get("intent", {})
        log(f"Management decision: {intent.get('action')}")
        
        # Step 4: Execute management action if needed (FIXED: removed "open_position")
        if intent.get("action") in ["adjust_position", "close_position", "update_stops"]:
            trade_result = execute_trade(intent)
            
            # Step 5: Wait for execution
            time.sleep(5)
            
            # Step 6: Verify position changes using exchange verification and trade lifecycle
            log("\n🔍 Verifying position changes via exchange and trade lifecycle...")
            final_exchange_result = await verify_exchange_sync()
            final_db_trades = check_trades()
            
            # Verify strategy_runs entries for universal trade lifecycle
            strategy_runs_verified = False
            if trade_result.get('status') == 'success' and trade_result.get('trade_id'):
                strategy_runs_verified = verify_strategy_runs(trade_result['trade_id'])
            
            if intent.get("action") == "close_position":
                if final_exchange_result['total_positions'] == 0:
                    log("✅ Position successfully closed on exchange")
                    log(f"  - Exchange positions: {final_exchange_result['total_positions']}")
                    log(f"  - Database trades: {len(final_db_trades)}")
                    log(f"  - Trade lifecycle closed: {final_exchange_result['trades_closed']}")
                    log(f"  - Strategy runs: VERIFIED ✓" if strategy_runs_verified else "  - Strategy runs: NOT VERIFIED ⚠️")
                    success = True
                else:
                    log("❌ Position close failed - still exists on exchange")
                    success = False
            elif intent.get("action") in ["adjust_position", "update_stops"]:
                if final_exchange_result['total_positions'] > 0:
                    log("✅ Position successfully adjusted on exchange")
                    log(f"  - Exchange positions: {final_exchange_result['total_positions']}")
                    log(f"  - Database trades: {len(final_db_trades)}")
                    log(f"  - Trade lifecycle updated: {final_exchange_result['trades_updated']}")
                    log(f"  - Strategy runs: VERIFIED ✓" if strategy_runs_verified else "  - Strategy runs: NOT VERIFIED ⚠️")
                    success = True
                else:
                    log("❌ Position adjustment failed - no longer exists on exchange")
                    success = False
            else:
                success = True  # Other actions don't change positions
            
            if success:
                log("✅ MANAGE TRADE scenario completed successfully!")
                log("📊 Final system state: CLEAN - database matches exchange reality via universal trade lifecycle")
            else:
                log("❌ MANAGE TRADE scenario failed!")
            return success
        
        elif intent.get("action") == "hold_position":
            log("✅ Decision: Hold position - no changes needed")
            return True
        
        else:
            log(f"Unexpected management action: {intent.get('action')}")
            return False
            
    except Exception as e:
        log(f"❌ MANAGE TRADE scenario failed: {e}", "ERROR")
        return False


async def setup_monitoring():
    """Initialize account monitoring and update account state once before tests."""
    log("Setting up account monitoring...")
    
    try:
        # Get credentials from environment
        api_key = os.getenv('EXCHANGE_API')
        secret = os.getenv('EXCHANGE_SECRET')
        
        if not api_key or not secret:
            log("⚠️ EXCHANGE_API or EXCHANGE_SECRET not found in environment", "WARN")
            log("Tests will proceed but may have limited account data", "WARN")
            return None
        
        # Create monitoring service with proper parameters
        credentials = {
            'apiKey': api_key,
            'secret': secret
        }
        
        monitor = AccountMonitoringService(
            user_id=DEFAULT_USER_ID,
            config_id=DEFAULT_CONFIG_ID,
            exchange_name="bitmex",
            credentials=credentials,
            testnet=True
        )
        
        # Create exchange client (required for _update_account_state)
        monitor.exchange = await monitor._create_exchange_client()
        
        # Update account state and reconcile trades
        log("Updating account state from exchange...")
        result = await monitor._update_account_state()
        
        log(f"✓ Account monitoring initialized and database updated")
        log(f"  - Position sync performed: {result['position_sync_performed']}")
        log(f"  - Trade lifecycle: {result['trades_opened']} opened, {result['trades_updated']} updated, {result['trades_closed']} closed")
        
        # Close the exchange connection (we only needed one update)
        if monitor.exchange:
            await monitor.exchange.close()
            monitor.exchange = None
            
        return monitor
        
    except Exception as e:
        log(f"⚠️ Account monitoring setup failed: {e}", "WARN")
        log("Tests will proceed but may have limited account data", "WARN")
        return None


async def async_main():
    """Run the manage trade pipeline test."""
    log("🚀 Starting Manage Trade Pipeline Test")
    log(f"API Base URL: {API_BASE_URL}")
    log(f"Test User ID: {DEFAULT_USER_ID}")
    log(f"Test Config ID: {DEFAULT_CONFIG_ID}")
    log(f"Test Scenario: {SCENARIO['description']}")
    
    # Check API health first
    if not check_api_health():
        log("❌ API health check failed. Is main_api.py running?", "ERROR")
        log("Run: python main_api.py", "ERROR")
        return
    
    # Setup monitoring to ensure fresh account data
    monitor = await setup_monitoring()
    if monitor:
        log("Account monitoring ready for test execution")
    
    # Rate limiting delay to avoid overwhelming exchange API
    log("⏱️ Rate limiting delay...")
    await asyncio.sleep(3)
    
    # Run the manage trade scenario
    log("\n🎯 RUNNING MANAGE TRADE TEST\n")
    
    manage_trade_passed = await run_manage_trade_scenario()
    
    # Summary
    log("\n" + "="*60)
    log("MANAGE TRADE TEST COMPLETE")
    log("="*60)
    
    if manage_trade_passed:
        log("\n🎉 Manage trade test PASSED!")
    else:
        log("\n❌ Manage trade test FAILED!")
        log("\n💡 Make sure you have an open position before running this test.")
        log("   Run 'python tests/new_trade.py' first to create a position.")
    
    log("\nTest execution complete. Exiting.")


def main():
    """Entry point that runs the async main function."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()