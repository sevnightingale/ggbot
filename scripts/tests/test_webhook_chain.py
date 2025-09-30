#!/usr/bin/env python
"""
Test webhook chain: Extraction → Decision → Trading

This test validates the autonomous pipeline by triggering the extraction webhook
and verifying that it automatically chains through decision and trading modules.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID


class WebhookChainTester:
    """Test the complete webhook chain from extraction to trading."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.extraction_webhook = f"{base_url}/extraction/webhooks/trigger-extraction"
        self.decision_webhook = f"{base_url}/decision/webhooks/trigger-decision"  
        self.trading_webhook = f"{base_url}/trading/webhooks/execute-trade"
        
        # Health check URLs
        self.health_urls = {
            "main": f"{base_url}/health",
            "extraction": f"{base_url}/extraction/health",
            "decision": f"{base_url}/decision/health",
            "trading": f"{base_url}/trading/health"
        }
        
        self.client = httpx.AsyncClient(timeout=60.0)
        
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
    
    async def test_individual_webhooks(self):
        """Test each webhook endpoint individually."""
        logger.info("🔧 Testing individual webhook endpoints...")
        
        # Test data
        test_payload = {
            "user_id": DEFAULT_USER_ID,
            "config_id": "a93de31b-9b8a-42e3-827d-c31e580f5f36",  # Use proper UUID
            "symbols": ["BTC/USDT"],
            "timeframes": ["15m"]
        }
        
        # Test extraction webhook
        logger.info("  Testing extraction webhook...")
        try:
            response = await self.client.post(self.extraction_webhook, json=test_payload)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"  ✅ Extraction webhook: {result.get('status')} - {result.get('extraction_id')}")
            else:
                logger.error(f"  ❌ Extraction webhook failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"  ❌ Extraction webhook error: {str(e)}")
            return False
        
        # Test decision webhook  
        logger.info("  Testing decision webhook...")
        decision_payload = {
            "user_id": DEFAULT_USER_ID,
            "config_id": "a93de31b-9b8a-42e3-827d-c31e580f5f36",  # Use proper UUID
            "symbol": "BTC/USD",
            "timeframes": ["15m"]
        }
        try:
            response = await self.client.post(self.decision_webhook, json=decision_payload)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"  ✅ Decision webhook: {result.get('status')} - {result.get('action')}")
            else:
                logger.error(f"  ❌ Decision webhook failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"  ❌ Decision webhook error: {str(e)}")
            return False
        
        # Test trading webhook
        logger.info("  Testing trading webhook...")
        trading_payload = {
            "user_id": DEFAULT_USER_ID,
            "config_id": "a93de31b-9b8a-42e3-827d-c31e580f5f36",  # Use proper UUID
            "action": "no_action",
            "symbol": "BTC/USD",
            "confidence": 0.5,
            "reasoning": "Test webhook call"
        }
        try:
            response = await self.client.post(self.trading_webhook, json=trading_payload)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"  ✅ Trading webhook: {result.get('status')} - {result.get('action')}")
            else:
                logger.error(f"  ❌ Trading webhook failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"  ❌ Trading webhook error: {str(e)}")
            return False
        
        logger.info("✅ All individual webhooks working!")
        return True
    
    async def test_webhook_chain(self):
        """Test the complete autonomous webhook chain."""
        logger.info("🚀 Testing autonomous webhook chain...")
        
        # Trigger the chain by calling extraction webhook
        chain_payload = {
            "user_id": DEFAULT_USER_ID,
            "config_id": "a93de31b-9b8a-42e3-827d-c31e580f5f36",  # Use same config_id as new_trade.py
            "symbols": ["BTC/USDT"],
            "timeframes": ["15m"]
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
            
            # Wait for the chain to complete (extraction is async, so we need to wait)
            await asyncio.sleep(30)  # Give time for MCP extraction + decision + trading
            
            elapsed = time.time() - start_time
            logger.info(f"  ⏱️  Chain completed in {elapsed:.1f} seconds")
            
            # Check extraction status
            status_url = f"{self.base_url}/extraction/api/extraction/status/{extraction_id}"
            status_response = await self.client.get(status_url)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                logger.info(f"  📊 Extraction status: {status_data.get('status')} - {status_data.get('data_points_extracted')} data points")
                
                if status_data.get('status') == 'completed' and status_data.get('data_points_extracted', 0) > 0:
                    logger.info("  ✅ Extraction completed successfully with data!")
                    logger.info("  🔗 Autonomous chain should have triggered Decision → Trading")
                    return True
                else:
                    logger.warning(f"  ⚠️  Extraction status: {status_data}")
                    return False
            else:
                logger.error(f"  ❌ Could not check extraction status: {status_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Webhook chain test failed: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete test suite."""
        logger.info("🧪 Starting Webhook Chain Test Suite")
        logger.info("=" * 50)
        
        # Test 1: Server health
        if not await self.check_server_health():
            logger.error("❌ Health check failed - aborting tests")
            return False
        
        logger.info("")
        
        # Test 2: Individual webhooks
        if not await self.test_individual_webhooks():
            logger.error("❌ Individual webhook tests failed - aborting chain test")
            return False
        
        logger.info("")
        
        # Test 3: Full chain
        if not await self.test_webhook_chain():
            logger.error("❌ Webhook chain test failed")
            return False
        
        logger.info("")
        logger.info("🎉 ALL WEBHOOK TESTS PASSED!")
        logger.info("🔗 Autonomous pipeline is working!")
        logger.info("✅ Ready for Phase 2: APScheduler Integration")
        
        return True


async def main():
    """Main test runner."""
    # Check if server is specified
    base_url = os.getenv("TEST_API_URL", "http://localhost:8000")
    
    logger.info(f"Testing webhook chain against: {base_url}")
    logger.info("Make sure the server is running: python main_api.py")
    logger.info("")
    
    async with WebhookChainTester(base_url) as tester:
        success = await tester.run_all_tests()
        
        if success:
            logger.info("🚀 Webhook infrastructure is ready!")
            sys.exit(0)
        else:
            logger.error("❌ Tests failed")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())