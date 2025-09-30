#!/usr/bin/env python3
"""
Test script for V2 API integration - Phase 7
"""
import os
import asyncio
import requests
from core.services.config_service import config_service
from core.services.user_service import user_service

async def test_v2_api_integration():
    """Test the V2 API endpoints for Phase 7 integration."""
    
    print("🧪 Testing V2 API Integration - Phase 7")
    print("=" * 50)
    
    # Set development mode for mock authentication
    os.environ["DEVELOPMENT_MODE"] = "true"
    
    # First ensure user profile exists
    print("\n1. Creating test user profile...")
    try:
        user_id = "00000000-0000-0000-0000-000000000000"  # Real Supabase user ID
        # Get or create user profile
        profile = await user_service.get_or_create_profile(user_id, email="user@example.com")
        print(f"✅ User profile ready: {profile.user_id} (tier: {profile.subscription_tier.value})")
    except Exception as e:
        print(f"⚠️ User profile setup: {e}")
    
    # Test configuration creation
    print("\n2. Testing config creation...")
    try:
        # Create a test configuration using the service directly
        config = await config_service.create_config(
            user_id=user_id,  # Use the real Supabase user ID
            config_name="Test Bot - V2 Integration",
            config_data={
                "selected_pair": "BTC/USDT",
                "extraction": {
                    "indicators": ["RSI", "MACD", "EMA"],
                    "timeframe": "1h"
                },
                "decision": {
                    "system_prompt": "You are analyzing {SYMBOL}",
                    "user_prompt": "Based on RSI and MACD, make trading decision"
                },
                "trading": {
                    "execution_mode": "paper",
                    "leverage": 3,
                    "position_sizing": {
                        "method": "account_percentage",
                        "account_percent": 5.0
                    }
                }
            }
        )
        
        if config:
            print(f"✅ Config created: {config.config_id}")
            print(f"   Name: {config.config_name}")
            print(f"   Pair: {config.selected_pair}")
            
            # Test API endpoints via HTTP
            base_url = "http://localhost:8001"
            
            print("\n3. Testing HTTP endpoints...")
            
            # Test config list endpoint
            response = requests.get(f"{base_url}/api/v2/config")
            if response.status_code == 200:
                configs_data = response.json()
                print(f"✅ Config list: {configs_data.get('count', 0)} configs found")
            else:
                print(f"❌ Config list failed: {response.status_code}")
            
            # Test bot data endpoints
            config_id = config.config_id
            
            # Test metrics endpoint
            response = requests.get(f"{base_url}/api/v2/bot/{config_id}/metrics")
            if response.status_code == 200:
                metrics = response.json()
                print(f"✅ Bot metrics: {metrics.get('status')}")
            else:
                print(f"❌ Bot metrics failed: {response.status_code}")
            
            # Test positions endpoint
            response = requests.get(f"{base_url}/api/v2/bot/{config_id}/positions")
            if response.status_code == 200:
                positions = response.json()
                print(f"✅ Bot positions: {len(positions.get('positions', []))} positions")
            else:
                print(f"❌ Bot positions failed: {response.status_code}")
            
            # Test trades endpoint
            response = requests.get(f"{base_url}/api/v2/bot/{config_id}/trades")
            if response.status_code == 200:
                trades = response.json()
                print(f"✅ Bot trades: {len(trades.get('trades', []))} trades")
            else:
                print(f"❌ Bot trades failed: {response.status_code}")
                
        else:
            print("❌ Failed to create test config")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_v2_api_integration())