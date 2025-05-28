"""
Test script for Decision API endpoints.
"""
import time
from datetime import datetime
import requests
import json
from core.common.config import DEFAULT_USER_ID

BASE_URL = "http://localhost:5002"


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "decision-api"
    print("✓ Health check passed")


def test_analyze_market():
    """Test market analysis endpoint."""
    print("\nTesting market analysis...")
    
    # Request analysis
    payload = {
        "user_id": DEFAULT_USER_ID,
        "mode": "auto",
        "symbol": "BTC/USDT",
        "timeframes": ["15m", "1h"]
    }
    
    response = requests.post(f"{BASE_URL}/api/decision/analyze", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "decision_id" in data
    assert "mode" in data
    assert "intent" in data
    
    decision_id = data["decision_id"]
    print(f"✓ Analysis triggered with ID: {decision_id}")
    
    return decision_id


def test_decision_status(decision_id):
    """Test checking decision status."""
    print(f"\nChecking decision status for ID: {decision_id}")
    
    # Poll status until completed or timeout
    start_time = time.time()
    timeout = 30  # 30 seconds timeout
    
    while time.time() - start_time < timeout:
        response = requests.get(f"{BASE_URL}/api/decision/status/{decision_id}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"  Status: {data['status']}")
        
        if data["status"] == "completed":
            print(f"✓ Decision completed")
            print(f"  Mode: {data.get('mode')}")
            print(f"  Action: {data.get('intent', {}).get('action')}")
            return True
        elif data["status"] == "failed":
            print(f"✗ Decision failed: {data.get('error')}")
            return False
        
        time.sleep(2)  # Wait 2 seconds before next check
    
    print("✗ Decision generation timed out")
    return False


def test_decision_history():
    """Test retrieving decision history."""
    print("\nTesting decision history...")
    
    response = requests.get(f"{BASE_URL}/api/decision/history/{DEFAULT_USER_ID}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved {len(data['decisions'])} decisions")
        print(f"  Total decisions: {data['total']}")
        
        # Show latest decision if any
        if data['decisions']:
            latest = data['decisions'][0]
            print(f"  Latest: {latest['mode']} - {latest['intent'].get('action', 'N/A')}")
            print(f"  Created: {latest['created_at']}")
    else:
        print(f"✗ Failed to retrieve history: {response.status_code}")


def test_current_decision():
    """Test retrieving current decision."""
    print("\nTesting current decision retrieval...")
    
    response = requests.get(f"{BASE_URL}/api/decision/current/{DEFAULT_USER_ID}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved current decision")
        print(f"  Mode: {data['mode']}")
        print(f"  Decision ID: {data['decision_id']}")
        
        if data['active_trade']:
            trade = data['active_trade']
            print(f"  Active Trade: {trade['symbol']}")
            print(f"  Entry: ${trade['entry_price']}")
            print(f"  P&L: ${trade['unrealized_pnl']}")
    elif response.status_code == 404:
        print("✗ No decisions found (generate one first)")
    else:
        print(f"✗ Failed to retrieve current decision: {response.status_code}")


def main():
    """Run all tests."""
    print("=== Decision API Tests ===")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    
    try:
        # Test health check
        test_health_check()
        
        # Test decision generation
        decision_id = test_analyze_market()
        
        # Wait a bit for processing
        time.sleep(3)
        
        # Check decision status
        completed = test_decision_status(decision_id)
        
        # Test history and current decision
        test_decision_history()
        test_current_decision()
        
        print("\n=== All tests completed ===")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to Decision API")
        print("  Make sure the API is running: python -m decision.run_api")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()