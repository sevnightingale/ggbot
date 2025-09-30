#!/usr/bin/env python3
"""
Simple V2 API test - Phase 7
Tests basic endpoints that work without database records
"""
import os
import requests

def test_v2_api_basic():
    """Test basic V2 API endpoints."""
    
    print("🧪 Testing V2 API - Basic Endpoints")
    print("=" * 40)
    
    base_url = "http://localhost:8001"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root: {data.get('name')} v{data.get('version')}")
        else:
            print(f"❌ Root failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root failed: {e}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data.get('status')}")
        else:
            print(f"❌ Health failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health failed: {e}")
    
    # Test config list (will fail due to auth, but we can see the error)
    try:
        response = requests.get(f"{base_url}/api/v2/config")
        print(f"📋 Config list: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"❌ Config list failed: {e}")
    
    print("\n🎯 Next steps:")
    print("1. Start V2 server: DEVELOPMENT_MODE=true python ggbot.py")
    print("2. Test frontend connection to V2 API")
    print("3. Add auth headers in Phase 5")

if __name__ == "__main__":
    test_v2_api_basic()