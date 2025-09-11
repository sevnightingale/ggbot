"""
Scheduled Decision Runner

Runs the decision module on a schedule, checking for new market data
and generating trading decisions.
"""
import asyncio
import argparse
import signal
import sys
from datetime import datetime

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from decision.decision_main import run_decision_process


class ScheduledDecisionRunner:
    def __init__(self, user_id: str = DEFAULT_USER_ID, interval: int = 300):
        self.user_id = user_id
        self.interval = interval  # seconds
        self.running = False
        
    async def run_once(self):
        """Run decision process once."""
        try:
            logger.bind(user_id=self.user_id).info("Running decision process...")
            
            # Run the decision process
            intent = await run_decision_process(user_id=self.user_id)
            
            if intent.get("action") != "error":
                logger.bind(user_id=self.user_id).info(
                    f"Decision generated: {intent.get('action')} "
                    f"with confidence {intent.get('confidence', 0)}"
                )
            else:
                logger.bind(user_id=self.user_id).error(
                    f"Decision error: {intent.get('error')}"
                )
                
        except Exception as e:
            logger.bind(user_id=self.user_id).error(
                f"Error in decision process: {str(e)}"
            )
    
    async def run_continuous(self):
        """Run decision process continuously."""
        self.running = True
        
        logger.bind(user_id=self.user_id).info(
            f"Starting continuous decision runner (interval: {self.interval}s)"
        )
        
        while self.running:
            start_time = datetime.utcnow()
            
            # Run decision process
            await self.run_once()
            
            # Calculate time to next run
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            sleep_time = max(0, self.interval - elapsed)
            
            if sleep_time > 0 and self.running:
                logger.bind(user_id=self.user_id).info(
                    f"Sleeping {sleep_time:.1f}s until next run"
                )
                await asyncio.sleep(sleep_time)
    
    def stop(self):
        """Stop the continuous runner."""
        self.running = False
        logger.bind(user_id=self.user_id).info("Stopping decision runner")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run scheduled decision process")
    parser.add_argument(
        "--user-id",
        default=DEFAULT_USER_ID,
        help="User ID to run decisions for"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Interval between runs in seconds (default: 300)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously instead of once"
    )
    
    args = parser.parse_args()
    
    # Create runner
    runner = ScheduledDecisionRunner(
        user_id=args.user_id,
        interval=args.interval
    )
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        runner.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    if args.continuous:
        await runner.run_continuous()
    else:
        await runner.run_once()


if __name__ == "__main__":
    asyncio.run(main())