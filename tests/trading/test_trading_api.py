#!/usr/bin/env python
"""
Test script for the Trading API endpoints.

This script tests the basic functionality of the Trading API without
actually running the server.
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.trades_main import app, TradingIntent, create_trading_engine
from fastapi.testclient import TestClient

# Set test environment
os.environ["TESTNET"] = "1"
os.environ["EXCHANGE_NAME"] = "bitmex"


async def test_trading_engine_creation():
    """Test that we can create a trading engine."""
    print("Testing trading engine creation...")
    
    try:
        # Create a test trading engine
        engine = await create_trading_engine("test_user_123")
        print("✓ Trading engine created successfully")
        
        # Stop the engine
        await engine.stop()
        print("✓ Trading engine stopped successfully")
        
    except Exception as e:
        print(f"✗ Error creating trading engine: {e}")
        raise


def test_api_endpoints():
    """Test the API endpoints using TestClient."""
    print("\nTesting API endpoints...")
    
    # Create test client
    client = TestClient(app)
    
    # Test health endpoint
    print("\n1. Testing /health endpoint...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("   ✓ Health check passed")
    
    # Test intent validation
    print("\n2. Testing intent model validation...")
    test_intent = TradingIntent(
        action="enter_long",
        symbol="BTC/USD",
        collateral_amount=1000,
        leverage=10,
        reasoning="Test trade"
    )
    print(f"   Intent: {test_intent.model_dump()}")
    print("   ✓ Intent model validation passed")
    
    print("\nAll tests passed!")


def main():
    """Run all tests."""
    print("=== Trading API Test Suite ===")
    
    # Test async functions
    asyncio.run(test_trading_engine_creation())
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n=== All tests completed successfully! ===")


if __name__ == "__main__":
    main()