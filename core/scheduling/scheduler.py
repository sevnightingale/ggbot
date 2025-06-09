"""
GGBot Autonomous Scheduler

Provides scheduled execution of the extraction → decision → trading webhook chain
for autonomous trading operation. Designed for single-config prototype with
frontend start/stop control.
"""

import asyncio
import os
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID


class GGBotScheduler:
    """
    Autonomous scheduler for GGBot trading operations.
    
    Manages scheduled extraction jobs that trigger the complete webhook chain:
    Extraction → Decision → Trading
    
    Features:
    - Single config support for prototype
    - Frontend start/stop control
    - APScheduler with AsyncIO integration
    - Comprehensive error handling and logging
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.scheduler = AsyncIOScheduler()
        self.extraction_webhook_url = f"{base_url}/extraction/webhooks/trigger-extraction"
        self.is_running = False
        self.job_id = "extraction_job"
        
        # Default configuration for single-config prototype
        self.default_config_id = "a93de31b-9b8a-42e3-827d-c31e580f5f36"
        self.default_user_id = DEFAULT_USER_ID
        self.default_symbols = ["BTC/USDT"]
        self.default_timeframes = ["15m"]
        
        # HTTP client for webhook calls
        self.client = httpx.AsyncClient(timeout=180.0)
        
        # Set up scheduler event listeners
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        
        logger.info("GGBotScheduler initialized", 
                   base_url=base_url, 
                   config_id=self.default_config_id)
    
    def initialize(self):
        """Initialize the scheduler (but don't start jobs)."""
        try:
            self.scheduler.start()
            logger.info("✅ Scheduler initialized and ready (no jobs scheduled)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize scheduler: {e}")
            return False
    
    def start_autonomous_mode(self) -> Dict[str, Any]:
        """
        Start autonomous trading mode by scheduling extraction jobs.
        
        Returns:
            Status dictionary with success/failure information
        """
        try:
            if self.is_running:
                return {
                    "status": "already_running",
                    "message": "Autonomous mode is already active",
                    "job_id": self.job_id
                }
            
            # Add the extraction job to run every 15 minutes
            self.scheduler.add_job(
                func=self._trigger_extraction_webhook,
                trigger="interval",
                minutes=15,
                id=self.job_id,
                name="Autonomous Extraction Job",
                replace_existing=True,
                max_instances=1  # Prevent overlapping executions
            )
            
            self.is_running = True
            
            logger.info("🚀 Autonomous mode STARTED", 
                       interval="15 minutes",
                       config_id=self.default_config_id,
                       symbols=self.default_symbols,
                       timeframes=self.default_timeframes)
            
            return {
                "status": "started",
                "message": "Autonomous trading mode activated",
                "job_id": self.job_id,
                "interval": "15 minutes",
                "next_run": self._get_next_run_time()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to start autonomous mode: {e}")
            return {
                "status": "error",
                "message": f"Failed to start: {str(e)}"
            }
    
    def stop_autonomous_mode(self) -> Dict[str, Any]:
        """
        Stop autonomous trading mode by removing scheduled jobs.
        
        Returns:
            Status dictionary with success/failure information
        """
        try:
            if not self.is_running:
                return {
                    "status": "already_stopped", 
                    "message": "Autonomous mode is not currently running"
                }
            
            # Remove the extraction job
            self.scheduler.remove_job(self.job_id)
            self.is_running = False
            
            logger.info("🛑 Autonomous mode STOPPED")
            
            return {
                "status": "stopped",
                "message": "Autonomous trading mode deactivated",
                "job_id": self.job_id
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to stop autonomous mode: {e}")
            return {
                "status": "error",
                "message": f"Failed to stop: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status.
        
        Returns:
            Comprehensive status information
        """
        try:
            scheduler_state = "running" if self.scheduler.running else "stopped"
            job_count = len(self.scheduler.get_jobs())
            
            status_info = {
                "scheduler_state": scheduler_state,
                "autonomous_mode": "active" if self.is_running else "inactive",
                "job_count": job_count,
                "config_id": self.default_config_id,
                "symbols": self.default_symbols,
                "timeframes": self.default_timeframes
            }
            
            if self.is_running:
                status_info["next_run"] = self._get_next_run_time()
            
            return {
                "status": "healthy",
                "scheduler": status_info
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting scheduler status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _trigger_extraction_webhook(self):
        """
        Trigger the extraction webhook to start the autonomous trading chain.
        
        This initiates the complete flow:
        Extraction (90s delay) → Decision → Trading
        """
        try:
            webhook_payload = {
                "user_id": self.default_user_id,
                "config_id": self.default_config_id,
                "symbols": self.default_symbols,
                "timeframes": self.default_timeframes
            }
            
            logger.info("🔄 Triggering autonomous extraction webhook",
                       payload=webhook_payload)
            
            response = await self.client.post(
                self.extraction_webhook_url,
                json=webhook_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                extraction_id = result.get('extraction_id')
                
                logger.info("✅ Autonomous extraction triggered successfully",
                           extraction_id=extraction_id,
                           status=result.get('status'))
            else:
                logger.error("❌ Extraction webhook failed",
                           status_code=response.status_code,
                           response_text=response.text)
                
        except Exception as e:
            logger.error(f"❌ Error triggering extraction webhook: {e}")
    
    def _get_next_run_time(self) -> Optional[str]:
        """Get the next scheduled run time for the extraction job."""
        try:
            job = self.scheduler.get_job(self.job_id)
            if job and job.next_run_time:
                return job.next_run_time.isoformat()
            return None
        except:
            return None
    
    def _job_executed(self, event):
        """Handle successful job execution."""
        job_id = event.job_id
        logger.info(f"✅ Scheduled job completed successfully: {job_id}")
    
    def _job_error(self, event):
        """Handle job execution errors."""
        job_id = event.job_id
        exception = event.exception
        logger.error(f"❌ Scheduled job failed: {job_id}, error: {exception}")
    
    async def shutdown(self):
        """Gracefully shutdown the scheduler and cleanup resources."""
        try:
            if self.is_running:
                self.stop_autonomous_mode()
            
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
            
            await self.client.aclose()
            
            logger.info("🔄 Scheduler shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during scheduler shutdown: {e}")


# Global scheduler instance for main_api.py integration
_scheduler_instance: Optional[GGBotScheduler] = None


def get_scheduler() -> GGBotScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        base_url = os.getenv("SCHEDULER_BASE_URL", "http://localhost:8000")
        _scheduler_instance = GGBotScheduler(base_url)
    return _scheduler_instance


async def initialize_scheduler() -> bool:
    """Initialize the global scheduler instance."""
    scheduler = get_scheduler()
    return scheduler.initialize()


async def shutdown_scheduler():
    """Shutdown the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance:
        await _scheduler_instance.shutdown()
        _scheduler_instance = None