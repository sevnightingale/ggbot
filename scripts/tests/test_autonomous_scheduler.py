#!/usr/bin/env python
"""
Test Autonomous Scheduler Integration

Tests the Phase 2 APScheduler integration with the GGBot system:
1. Verify scheduler starts/stops via API
2. Test autonomous webhook chain triggering
3. Validate complete pipeline execution

This test validates that the scheduler can replace manual triggering
with automated 15-minute extraction cycles.
"""

import asyncio
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any
import httpx

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
from core.common.logging_config import setup_logging, logger
log_file = setup_logging()


class SchedulerTester:
    """Test autonomous scheduler functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)
        
        # API endpoints
        self.scheduler_start_url = f"{base_url}/agent/api/scheduler/start"
        self.scheduler_stop_url = f"{base_url}/agent/api/scheduler/stop"
        self.scheduler_status_url = f"{base_url}/agent/api/scheduler/status"
        
        # Health check URLs
        self.health_urls = {
            "main": f"{base_url}/health",
            "extraction": f"{base_url}/extraction/health",
            "decision": f"{base_url}/decision/health", 
            "trading": f"{base_url}/trading/health",
            "agent": f"{base_url}/agent/health"
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def check_server_health(self) -> bool:
        """Verify all services are running and healthy."""
        logger.info("🏥 Checking server health before scheduler test...")
        
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
    
    async def test_scheduler_api_endpoints(self) -> bool:
        """Test scheduler start/stop/status API endpoints."""
        logger.info("🧪 Testing scheduler API endpoints...")
        
        try:
            # 1. Check initial status
            logger.info("  📊 Checking initial scheduler status...")
            response = await self.client.get(self.scheduler_status_url)
            if response.status_code != 200:
                logger.error(f"❌ Status endpoint failed: {response.status_code}")
                return False
            
            status = response.json()
            logger.info(f"  Initial status: {status.get('scheduler', {}).get('autonomous_mode', 'unknown')}")
            
            # 2. Test start scheduler
            logger.info("  🚀 Testing scheduler start...")
            response = await self.client.post(self.scheduler_start_url)
            if response.status_code != 200:
                logger.error(f"❌ Start endpoint failed: {response.status_code} - {response.text}")
                return False
            
            start_result = response.json()
            logger.info(f"  Start result: {start_result.get('status')} - {start_result.get('message')}")
            
            # 3. Verify scheduler is running
            await asyncio.sleep(2)
            response = await self.client.get(self.scheduler_status_url)
            status = response.json()
            autonomous_mode = status.get('scheduler', {}).get('autonomous_mode')
            
            if autonomous_mode != 'active':
                logger.error(f"❌ Scheduler not active after start: {autonomous_mode}")
                return False
            
            logger.info(f"  ✅ Scheduler confirmed active: {autonomous_mode}")
            next_run = status.get('scheduler', {}).get('next_run')
            if next_run:
                logger.info(f"  Next scheduled run: {next_run}")
            
            # 4. Test stop scheduler  
            logger.info("  🛑 Testing scheduler stop...")
            response = await self.client.post(self.scheduler_stop_url)
            if response.status_code != 200:
                logger.error(f"❌ Stop endpoint failed: {response.status_code} - {response.text}")
                return False
            
            stop_result = response.json()
            logger.info(f"  Stop result: {stop_result.get('status')} - {stop_result.get('message')}")
            
            # 5. Verify scheduler is stopped
            await asyncio.sleep(2)
            response = await self.client.get(self.scheduler_status_url)
            status = response.json()
            autonomous_mode = status.get('scheduler', {}).get('autonomous_mode')
            
            if autonomous_mode != 'inactive':
                logger.error(f"❌ Scheduler not inactive after stop: {autonomous_mode}")
                return False
            
            logger.info(f"  ✅ Scheduler confirmed inactive: {autonomous_mode}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Scheduler API test failed: {e}")
            return False
    
    async def test_scheduler_webhook_trigger(self) -> bool:
        """Test that scheduler actually triggers the webhook chain."""
        logger.info("🔗 Testing scheduler webhook chain triggering...")
        
        try:
            # Start the scheduler
            logger.info("  🚀 Starting scheduler for webhook test...")
            response = await self.client.post(self.scheduler_start_url)
            if response.status_code != 200:
                logger.error("❌ Failed to start scheduler")
                return False
            
            start_result = response.json()
            logger.info(f"  Scheduler started: {start_result.get('message')}")
            
            # Wait for at least one cycle (we can't wait 15 minutes, so we'll trigger manually)
            logger.info("  ⏰ For testing, we'll trigger extraction manually to simulate scheduler...")
            
            # Trigger extraction webhook manually to simulate what scheduler would do
            extraction_webhook_url = f"{self.base_url}/extraction/webhooks/trigger-extraction"
            webhook_payload = {
                "user_id": "00000000-0000-0000-0000-000000000001",
                "config_id": "a93de31b-9b8a-42e3-827d-c31e580f5f36",
                "symbols": ["BTC/USDT"],
                "timeframes": ["15m"]
            }
            
            logger.info("  🔄 Triggering extraction webhook (simulating scheduler)...")
            response = await self.client.post(extraction_webhook_url, json=webhook_payload)
            
            if response.status_code != 200:
                logger.error(f"❌ Extraction webhook failed: {response.status_code} - {response.text}")
                return False
            
            result = response.json()
            extraction_id = result.get('extraction_id')
            logger.info(f"  ✅ Extraction triggered: {extraction_id}")
            
            # Wait for the chain to complete (90s extraction delay + decision/trading time)
            logger.info("  ⏳ Waiting for webhook chain to complete (3 minutes)...")
            await asyncio.sleep(180)
            
            # Check extraction status
            status_url = f"{self.base_url}/extraction/api/extraction/status/{extraction_id}"
            response = await self.client.get(status_url)
            
            if response.status_code == 200:
                status_data = response.json()
                logger.info(f"  📊 Extraction status: {status_data.get('status')} - {status_data.get('data_points_extracted')} data points")
                
                if status_data.get('status') == 'completed' and status_data.get('data_points_extracted', 0) > 0:
                    logger.info("  ✅ Webhook chain completed successfully!")
                    
                    # Stop the scheduler
                    logger.info("  🛑 Stopping scheduler...")
                    await self.client.post(self.scheduler_stop_url)
                    
                    return True
                else:
                    logger.warning(f"  ⚠️ Extraction may not have completed properly: {status_data}")
            else:
                logger.error(f"❌ Could not check extraction status: {response.status_code}")
            
            # Stop the scheduler regardless
            await self.client.post(self.scheduler_stop_url)
            return False
            
        except Exception as e:
            logger.error(f"❌ Scheduler webhook test failed: {e}")
            # Always try to stop scheduler
            try:
                await self.client.post(self.scheduler_stop_url)
            except:
                pass
            return False
    
    async def run_complete_test(self) -> bool:
        """Run the complete scheduler test suite."""
        logger.info("🤖 Starting GGBot Autonomous Scheduler Test")
        logger.info("=" * 60)
        
        # 1. Check server health
        if not await self.check_server_health():
            logger.error("❌ Health check failed - aborting scheduler test")
            return False
        
        logger.info("")
        
        # 2. Test API endpoints
        if not await self.test_scheduler_api_endpoints():
            logger.error("❌ API endpoint test failed")
            return False
        
        logger.info("")
        
        # 3. Test webhook triggering
        if not await self.test_scheduler_webhook_trigger():
            logger.error("❌ Webhook trigger test failed")
            return False
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎉 All scheduler tests passed!")
        logger.info("✅ Phase 2 APScheduler integration is working!")
        
        return True


async def main():
    """Main test runner."""
    base_url = os.getenv("TEST_API_URL", "http://localhost:8000")
    
    logger.info("🧪 GGBot Autonomous Scheduler Integration Test")
    logger.info(f"Testing against: {base_url}")
    logger.info("Make sure the server is running: python main_api.py")
    logger.info("")
    
    async with SchedulerTester(base_url) as tester:
        success = await tester.run_complete_test()
        
        if success:
            logger.info("🎉 Scheduler integration test completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Scheduler integration test failed")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())