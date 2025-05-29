#!/usr/bin/env python
"""
End-to-End Pipeline Integration Test

This test exercises the complete GGBot pipeline via API calls:
1. Extraction API - Fetch market data and indicators
2. Decision API - Analyze data and generate trading intent
3. Trading API - Execute trade on exchange
4. Monitoring - Verify position updates

This uses the combined API server (main_api.py) running on port 8000.
"""

import os
import sys
import asyncio
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging before other imports
from core.common.logging_config import setup_logging
log_file = setup_logging()

# Load environment variables from .env file
load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:8000"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_SYMBOL = "BTC/USDT"  # Standard symbol - will be mapped to BTC/USDT:USDT for BitMEX
TEST_TIMEFRAMES = ["15m", "1h"]
TEST_EXCHANGE = "bitmex"

# Test scenarios
SCENARIOS = {
    "new_trade": {
        "description": "No positions → Entry signal → Execute trade",
        "expected_flow": ["extraction", "decision", "trading", "position_created"]
    },
    "manage_trade": {
        "description": "Existing position → Monitor → Adjust/Close",
        "expected_flow": ["extraction", "decision", "trading", "position_updated"]
    }
}


def log(message: str, level: str = "INFO"):
    """Simple logging function."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


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


def get_latest_market_data(user_id: str = DEFAULT_USER_ID) -> Dict[str, Any]:
    """Get the latest extracted market data."""
    log("Fetching latest market data...")
    
    response = requests.get(
        f"{API_BASE_URL}/extraction/api/extraction/latest/{user_id}",
        params={
            "symbol": TEST_SYMBOL,
            "timeframe": TEST_TIMEFRAMES[0],
            "data_type": "indicator_analysis"  # Get the full analysis with indicators
        },
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        # Extract indicators from the nested structure
        raw_data = data.get('data', {})
        indicators = raw_data.get('indicators', {})
        log(f"✓ Retrieved market data: {len(indicators)} indicators")
        return data
    else:
        log(f"✗ Failed to get market data: {response.text}", "ERROR")
        return {}


def trigger_decision_analysis(user_id: str = DEFAULT_USER_ID, mode: str = "auto") -> Dict[str, Any]:
    """Trigger decision analysis via API."""
    log(f"Triggering decision analysis (mode: {mode})...")
    
    payload = {
        "user_id": user_id,
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
    log(f"Executing trade: {intent['action']}...")
    
    response = requests.post(
        f"{API_BASE_URL}/trading/trade/execute",
        json=intent,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        log(f"✓ Trade executed: {result.get('trade_id', 'N/A')}")
        log(f"  Status: {result.get('status', 'N/A')}")
        return result
    else:
        log(f"✗ Trade execution failed: {response.text}", "ERROR")
        raise Exception(f"Trade execution failed: {response.text}")


def check_positions(user_id: str = DEFAULT_USER_ID) -> List[Dict[str, Any]]:
    """Check current positions via Dashboard API."""
    log("Checking positions...")
    
    response = requests.get(
        f"{API_BASE_URL}/dashboard/api/dashboard/{user_id}/positions",
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        # The dashboard API returns a dict with 'positions' key
        positions = data.get('positions', [])
        log(f"✓ Found {len(positions)} positions")
        
        for pos in positions:
            log(f"  {pos['symbol']}: {pos.get('size', pos.get('contracts', 0))} contracts @ {pos.get('entry_price', 'N/A')}")
        
        return positions
    else:
        log(f"✗ Failed to get positions: {response.text}", "ERROR")
        return []


def run_new_trade_scenario():
    """Test scenario: No positions → Entry signal → Execute trade."""
    log("\n" + "="*60)
    log("Running NEW TRADE scenario")
    log("="*60)
    
    try:
        # Step 1: Trigger extraction
        extraction_result = trigger_extraction()
        
        # Step 2: Wait for extraction to complete
        if not wait_for_extraction(extraction_result["extraction_id"]):
            raise Exception("Extraction failed or timed out")
        
        # Step 3: Get latest market data (verify extraction worked)
        market_data = get_latest_market_data()
        
        # Check nested structure: market_data.data.indicators
        raw_data = market_data.get('data', {}) if market_data else {}
        indicators = raw_data.get('indicators', {})
        
        if not market_data or not indicators:
            raise Exception("No market data available after extraction")
        
        # Step 4: Trigger decision analysis
        decision_result = trigger_decision_analysis(mode="NEW_TRADE")
        
        # Check if we got a trading intent
        intent = decision_result.get("intent", {})
        
        if intent.get("action") == "no_action":
            log("Decision: No trade opportunity found")
            return True
        
        # Step 5: Execute trade if we have an entry signal
        if intent.get("action") == "open_position":
            trade_result = execute_trade(intent)
            
            # Step 6: Wait for position to be created
            time.sleep(5)
            
            # Step 7: Verify position exists
            positions = check_positions()
            
            if positions:
                log("✅ NEW TRADE scenario completed successfully!")
                return True
            else:
                log("⚠️ Trade executed but no position found", "WARN")
                return False
        else:
            log(f"Unexpected intent action: {intent.get('action')}")
            return False
            
    except Exception as e:
        log(f"❌ NEW TRADE scenario failed: {e}", "ERROR")
        return False


def run_manage_trade_scenario():
    """Test scenario: Existing position → Monitor → Adjust/Close."""
    log("\n" + "="*60)
    log("Running MANAGE TRADE scenario")
    log("="*60)
    
    try:
        # First check if we have any positions
        positions = check_positions()
        
        if not positions:
            log("No existing positions to manage. Creating one first...")
            
            # Run new trade scenario to create a position
            if not run_new_trade_scenario():
                raise Exception("Failed to create initial position")
            
            # Check positions again
            positions = check_positions()
            
            if not positions:
                raise Exception("Still no positions after attempting to create one")
        
        # Now we have a position to manage
        log(f"Managing {len(positions)} existing positions")
        
        # Step 1: Trigger extraction for latest data
        extraction_result = trigger_extraction()
        
        # Step 2: Wait for extraction
        if not wait_for_extraction(extraction_result["extraction_id"]):
            raise Exception("Extraction failed or timed out")
        
        # Step 3: Trigger decision analysis in MANAGE mode
        decision_result = trigger_decision_analysis(mode="MANAGE_TRADE")
        
        intent = decision_result.get("intent", {})
        log(f"Management decision: {intent.get('action')}")
        
        # Step 4: Execute management action if needed
        if intent.get("action") in ["adjust_position", "close_position", "update_stops", "open_position"]:
            trade_result = execute_trade(intent)
            
            # Step 5: Wait for execution
            time.sleep(5)
            
            # Step 6: Verify position changes
            new_positions = check_positions()
            
            if intent.get("action") == "close_position" and not new_positions:
                log("✅ Position successfully closed")
            elif intent.get("action") in ["adjust_position", "update_stops"] and new_positions:
                log("✅ Position successfully adjusted")
            
            log("✅ MANAGE TRADE scenario completed successfully!")
            return True
        
        elif intent.get("action") == "hold_position":
            log("✅ Decision: Hold position - no changes needed")
            return True
        
        else:
            log(f"Unexpected management action: {intent.get('action')}")
            return False
            
    except Exception as e:
        log(f"❌ MANAGE TRADE scenario failed: {e}", "ERROR")
        return False


def run_error_scenario():
    """Test error handling in the pipeline."""
    log("\n" + "="*60)
    log("Running ERROR HANDLING scenario")
    log("="*60)
    
    try:
        # Test 1: Invalid user ID
        log("Test 1: Invalid user ID")
        try:
            trigger_extraction(user_id="invalid-user-id")
            log("⚠️ Expected error for invalid user ID but got success", "WARN")
        except Exception as e:
            log(f"✓ Correctly handled invalid user ID: {e}")
        
        # Test 2: Invalid symbol
        log("\nTest 2: Invalid symbol in decision")
        payload = {
            "user_id": DEFAULT_USER_ID,
            "mode": "NEW_TRADE",
            "symbol": "INVALID/PAIR",
            "timeframes": ["1h"]
        }
        
        response = requests.post(
            f"{API_BASE_URL}/decision/api/decision/analyze",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            log(f"✓ Correctly rejected invalid symbol: {response.status_code}")
        else:
            log("⚠️ Expected error for invalid symbol but got success", "WARN")
        
        # Test 3: Concurrent requests
        log("\nTest 3: Concurrent extraction requests")
        
        async def concurrent_extractions():
            tasks = []
            for i in range(3):
                payload = {
                    "user_id": DEFAULT_USER_ID,
                    "symbols": [TEST_SYMBOL],
                    "timeframes": TEST_TIMEFRAMES
                }
                tasks.append(
                    asyncio.create_task(
                        asyncio.to_thread(
                            requests.post,
                            f"{API_BASE_URL}/extraction/api/extraction/run",
                            json=payload,
                            timeout=30
                        )
                    )
                )
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 200)
            log(f"✓ {success_count}/3 concurrent requests succeeded")
        
        asyncio.run(concurrent_extractions())
        
        log("✅ ERROR HANDLING scenario completed!")
        return True
        
    except Exception as e:
        log(f"❌ ERROR HANDLING scenario failed: {e}", "ERROR")
        return False


def main():
    """Run all integration test scenarios."""
    log("🚀 Starting GGBot Pipeline Integration Tests")
    log(f"API Base URL: {API_BASE_URL}")
    log(f"Test User ID: {DEFAULT_USER_ID}")
    
    # Check API health first
    if not check_api_health():
        log("❌ API health check failed. Is main_api.py running?", "ERROR")
        log("Run: python main_api.py", "ERROR")
        return
    
    # Run test scenarios
    results = {
        "new_trade": False,
        "manage_trade": False,
        "error_handling": False
    }
    
    # Scenario 1: New Trade
    results["new_trade"] = run_new_trade_scenario()
    
    # Wait between scenarios
    time.sleep(10)
    
    # Scenario 2: Manage Trade
    results["manage_trade"] = run_manage_trade_scenario()
    
    # Wait between scenarios
    time.sleep(5)
    
    # Scenario 3: Error Handling
    results["error_handling"] = run_error_scenario()
    
    # Summary
    log("\n" + "="*60)
    log("TEST SUMMARY")
    log("="*60)
    
    for scenario, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        log(f"{scenario}: {status}")
    
    total_passed = sum(1 for passed in results.values() if passed)
    total_tests = len(results)
    
    log(f"\nTotal: {total_passed}/{total_tests} scenarios passed")
    
    if total_passed == total_tests:
        log("\n🎉 All integration tests passed!")
    else:
        log("\n❌ Some integration tests failed!")


if __name__ == "__main__":
    main()