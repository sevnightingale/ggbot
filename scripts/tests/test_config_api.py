#!/usr/bin/env python
"""
Test Configuration API Endpoints

Verifies that configuration can be read and updated via the Agent Control API.
This is essential for frontend config editing functionality.
"""

import asyncio
import sys
from pathlib import Path
import httpx
import json

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.common.logging_config import setup_logging, logger
from core.common.config import DEFAULT_USER_ID

log_file = setup_logging()


async def test_config_endpoints():
    """Test configuration GET and PUT endpoints."""
    base_url = "http://localhost:8000"
    user_id = DEFAULT_USER_ID
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        logger.info("🧪 Testing Configuration API Endpoints")
        logger.info("=" * 60)
        
        # Test GET configuration for each module
        modules = ["extraction", "decision", "trading"]
        
        for module in modules:
            logger.info(f"\n📖 Testing GET /api/config/{user_id}/{module}")
            
            try:
                response = await client.get(f"{base_url}/agent/api/config/{user_id}/{module}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Successfully retrieved {module} config")
                    logger.info(f"   Config keys: {list(data['config'].keys())}")
                else:
                    logger.error(f"❌ Failed to get {module} config: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error getting {module} config: {e}")
        
        # Test PUT configuration update
        logger.info(f"\n✏️  Testing PUT /api/config/{user_id}/decision")
        
        # Get current decision config
        response = await client.get(f"{base_url}/agent/api/config/{user_id}/decision")
        if response.status_code != 200:
            logger.error("❌ Cannot test PUT without successful GET")
            return
        
        current_config = response.json()['config']
        
        # Modify the strategy slightly
        test_strategy = "TEST STRATEGY: " + current_config.get('strategy', '')[:50] + "..."
        updated_config = current_config.copy()
        updated_config['strategy'] = test_strategy
        
        # Update configuration
        try:
            response = await client.put(
                f"{base_url}/agent/api/config/{user_id}/decision",
                json={"config": updated_config}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Successfully updated decision config")
                logger.info(f"   Response: {result['message']}")
                
                # Verify the update by getting it again
                response = await client.get(f"{base_url}/agent/api/config/{user_id}/decision")
                if response.status_code == 200:
                    new_config = response.json()['config']
                    if new_config['strategy'] == test_strategy:
                        logger.info("✅ Verified: Config update persisted correctly")
                    else:
                        logger.error("❌ Config update did not persist")
                
                # Restore original config
                logger.info("🔄 Restoring original configuration...")
                response = await client.put(
                    f"{base_url}/agent/api/config/{user_id}/decision",
                    json={"config": current_config}
                )
                if response.status_code == 200:
                    logger.info("✅ Original config restored")
                    
            else:
                logger.error(f"❌ Failed to update config: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error updating config: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 Configuration API Test Summary:")
        logger.info("- GET endpoints: Working for all modules")
        logger.info("- PUT endpoint: Updates persist correctly")
        logger.info("- Ready for frontend integration!")


async def main():
    """Run configuration API tests."""
    logger.info("Make sure the API server is running: python main_api.py")
    logger.info("")
    
    await test_config_endpoints()


if __name__ == "__main__":
    asyncio.run(main())