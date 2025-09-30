"""
Test script for Extraction API endpoints.
"""
import asyncio
import time
from datetime import datetime
import requests
import json
from core.common.config import DEFAULT_USER_ID

BASE_URL = "http://localhost:5001"


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "extraction-api"
    print("✓ Health check passed")


def test_trigger_extraction():
    """Test triggering an extraction."""
    print("\nTesting extraction trigger...")
    
    # Trigger extraction for BTC/USDT
    payload = {
        "user_id": DEFAULT_USER_ID,
        "symbols": ["BTC/USDT"],
        "timeframes": ["15m"]
    }
    
    response = requests.post(f"{BASE_URL}/api/extraction/run", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "started"
    assert "extraction_id" in data
    
    extraction_id = data["extraction_id"]
    print(f"✓ Extraction triggered with ID: {extraction_id}")
    
    return extraction_id


def test_extraction_status(extraction_id):
    """Test checking extraction status."""
    print(f"\nChecking extraction status for ID: {extraction_id}")
    
    # Poll status until completed or timeout
    start_time = time.time()
    timeout = 30  # 30 seconds timeout
    
    while time.time() - start_time < timeout:
        response = requests.get(f"{BASE_URL}/api/extraction/status/{extraction_id}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"  Status: {data['status']}")
        
        if data["status"] == "completed":
            print(f"✓ Extraction completed with {data['data_points_extracted']} data points")
            return True
        elif data["status"] == "failed":
            print(f"✗ Extraction failed: {data['errors']}")
            return False
        
        time.sleep(2)  # Wait 2 seconds before next check
    
    print("✗ Extraction timed out")
    return False


def test_get_latest_data():
    """Test retrieving latest market data."""
    print("\nTesting latest data retrieval...")
    
    # Get latest indicator values for BTC/USDT 15m
    params = {
        "symbol": "BTC/USDT",
        "timeframe": "15m",
        "data_type": "indicator_values"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/extraction/latest/{DEFAULT_USER_ID}",
        params=params
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved data for {data['symbol']} {data['timeframe']}")
        print(f"  Created at: {data['created_at']}")
        
        # Check indicator data structure
        if "data" in data and isinstance(data["data"], dict):
            indicators = list(data["data"].keys())
            print(f"  Indicators: {', '.join(indicators[:5])}...")  # Show first 5
    elif response.status_code == 404:
        print("✗ No recent data found (run extraction first)")
    else:
        print(f"✗ Failed to retrieve data: {response.status_code}")


def test_get_latest_analysis():
    """Test retrieving latest analysis."""
    print("\nTesting latest analysis retrieval...")
    
    # Get latest analysis for BTC/USDT 15m
    params = {
        "symbol": "BTC/USDT",
        "timeframe": "15m",
        "data_type": "indicator_analysis"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/extraction/latest/{DEFAULT_USER_ID}",
        params=params
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved analysis for {data['symbol']} {data['timeframe']}")
        print(f"  Created at: {data['created_at']}")
        
        # Show first 200 chars of analysis
        if "analysis" in data:
            analysis = data["analysis"]
            print(f"  Analysis preview: {analysis[:200]}...")
    elif response.status_code == 404:
        print("✗ No recent analysis found (run extraction first)")
    else:
        print(f"✗ Failed to retrieve analysis: {response.status_code}")


def main():
    """Run all tests."""
    print("=== Extraction API Tests ===")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    
    try:
        # Test health check
        test_health_check()
        
        # Test extraction trigger and status
        extraction_id = test_trigger_extraction()
        
        # Wait a bit for extraction to start
        time.sleep(3)
        
        # Check extraction status
        completed = test_extraction_status(extraction_id)
        
        if completed:
            # Test data retrieval
            test_get_latest_data()
            test_get_latest_analysis()
        
        print("\n=== All tests completed ===")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to Extraction API")
        print("  Make sure the API is running: python -m extraction.api")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()