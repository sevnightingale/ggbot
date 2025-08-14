#!/usr/bin/env python3
"""
Universal Bot Monitoring Service Runner

PM2 service entry point for continuous bot monitoring.
Runs the universal active bot monitor with proper service lifecycle.
"""

import asyncio
import signal
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from core.monitoring.active_bot_monitor import ActiveBotMonitor
from core.monitoring.bot_types.ggshot_bot import GGShotBotHandler
from core.common.logger import logger


class BotMonitoringService:
    """
    Service wrapper for the Universal Bot Monitor.
    
    Handles service lifecycle, signal handling, and graceful shutdown.
    """
    
    def __init__(self):
        """Initialize the monitoring service."""
        self.monitor = ActiveBotMonitor()
        self.running = False
        
        # Register available bot handlers
        self.register_handlers()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.bind(module="bot_monitor_service").info(
            "🤖 Universal Bot Monitoring Service initialized"
        )
    
    def register_handlers(self):
        """Register all available bot type handlers."""
        # Register ggShot handler for both 'decision' and 'ggshot' config types
        self.monitor.register_bot_handler('decision', GGShotBotHandler)
        self.monitor.register_bot_handler('ggshot', GGShotBotHandler)
        
        logger.bind(module="bot_monitor_service").info(
            "Registered bot handlers: decision, ggshot"
        )
        
        # TODO: Register other handlers as they're developed
        # self.monitor.register_bot_handler('demo', DemoBotHandler)
        # self.monitor.register_bot_handler('rsi_momentum', RSIMomentumBotHandler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.bind(module="bot_monitor_service").info(
            f"Received signal {signum}, shutting down gracefully..."
        )
        self.running = False
    
    async def start_service(self):
        """Start the monitoring service."""
        logger.bind(module="bot_monitor_service").info(
            "🚀 Starting Universal Bot Monitoring Service"
        )
        
        self.running = True
        
        try:
            # Start the monitoring loop
            await self.run_monitoring_loop()
        except Exception as e:
            logger.bind(module="bot_monitor_service").error(
                f"Service crashed: {str(e)}"
            )
            raise
        finally:
            logger.bind(module="bot_monitor_service").info(
                "🛑 Universal Bot Monitoring Service stopped"
            )
    
    async def run_monitoring_loop(self):
        """Run the main monitoring loop with error recovery."""
        consecutive_errors = 0
        max_errors = 5
        
        while self.running:
            try:
                # Get active bots
                active_configs = await self.monitor.get_active_bot_configs()
                
                if not active_configs:
                    logger.bind(module="bot_monitor_service").debug(
                        "No active bots found - waiting for activation"
                    )
                else:
                    logger.bind(module="bot_monitor_service").debug(
                        f"Monitoring {len(active_configs)} active bots"
                    )
                    
                    # Monitor each active bot
                    monitoring_tasks = []
                    for bot_config in active_configs:
                        task = self.monitor.monitor_single_bot(bot_config)
                        monitoring_tasks.append(task)
                    
                    # Run all monitoring tasks concurrently
                    if monitoring_tasks:
                        await asyncio.gather(*monitoring_tasks, return_exceptions=True)
                
                # Cleanup handlers for inactive bots
                await self.monitor.cleanup_inactive_handlers(active_configs)
                
                # Reset error counter on successful cycle
                consecutive_errors = 0
                
                # Wait before next poll
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                consecutive_errors += 1
                
                logger.bind(module="bot_monitor_service").error(
                    f"Error in monitoring loop ({consecutive_errors}/{max_errors}): {str(e)}"
                )
                
                # If too many consecutive errors, crash the service
                if consecutive_errors >= max_errors:
                    logger.bind(module="bot_monitor_service").critical(
                        f"Too many consecutive errors ({max_errors}), crashing service"
                    )
                    raise
                
                # Exponential backoff on errors
                wait_time = min(60, 5 * (2 ** consecutive_errors))
                logger.bind(module="bot_monitor_service").info(
                    f"Waiting {wait_time}s before retry..."
                )
                await asyncio.sleep(wait_time)


async def main():
    """Main service entry point."""
    try:
        # Create and start service
        service = BotMonitoringService()
        await service.start_service()
        
    except KeyboardInterrupt:
        logger.bind(module="bot_monitor_service").info(
            "Service interrupted by user"
        )
    except Exception as e:
        logger.bind(module="bot_monitor_service").critical(
            f"Service failed to start: {str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    # Set up proper event loop for the service
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass