"""
Test script for Active Bot Monitor

Simple test to verify the monitoring service works with the ggShot-Pro bot.
Run this to test the monitoring without WebSocket integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from core.monitoring.active_bot_monitor import ActiveBotMonitor, register_bot_handler
from core.monitoring.bot_types.ggshot_bot import GGShotBotHandler


async def test_monitoring():
    """Test the monitoring service with ggShot bot."""
    print("🧪 Testing Universal Active Bot Monitor")
    print("=" * 50)
    
    # Create monitor instance
    monitor = ActiveBotMonitor()
    
    # Register ggShot bot handler
    register_bot_handler('ggshot', GGShotBotHandler)
    
    print("✅ Registered ggShot bot handler")
    
    # Get active bots
    active_configs = await monitor.get_active_bot_configs()
    
    print(f"📊 Found {len(active_configs)} active bot configurations:")
    for config in active_configs:
        print(f"   - {config['config_type']}: {config['config_name']} ({config['config_id'][:8]})")
    
    if not active_configs:
        print("❌ No active bots found. Make sure ggShot-Pro is marked as active in config_instances.")
        return
    
    print("\n🔄 Running single monitoring cycle...")
    
    # Test single monitoring cycle
    monitoring_tasks = []
    for bot_config in active_configs:
        task = monitor.monitor_single_bot(bot_config)
        monitoring_tasks.append(task)
    
    if monitoring_tasks:
        results = await asyncio.gather(*monitoring_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Error monitoring bot {i}: {result}")
            else:
                print(f"✅ Successfully monitored bot {i}")
    
    print("\n✅ Test completed successfully!")
    print("\n💡 To run continuous monitoring, use: monitor.start_monitoring()")


if __name__ == "__main__":
    asyncio.run(test_monitoring())