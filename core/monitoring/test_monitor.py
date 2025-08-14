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
    
    # Register ggShot bot handler directly on the instance
    monitor.register_bot_handler('ggshot', GGShotBotHandler)
    
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
    
    # Test single monitoring cycle with detailed output
    for i, bot_config in enumerate(active_configs):
        try:
            config_id = bot_config['config_id']
            bot_type = bot_config['config_type']
            bot_name = bot_config.get('config_name', f"Bot {config_id[:8]}")
            
            print(f"\n🔍 Testing Bot {i+1}: {bot_type} - {bot_name}")
            print(f"   Config ID: {config_id}")
            
            # Test if handler exists
            handler = monitor.create_bot_handler(bot_config)
            if not handler:
                print(f"   ⚠️  No handler available for {bot_type}")
                continue
            
            # Test phase detection
            current_phase = await handler.detect_pipeline_phase()
            sub_phase = await handler.detect_sub_phase(current_phase)
            context_data = await handler.extract_context_data()
            status_message = await handler.generate_status_message(current_phase, sub_phase, context_data)
            
            # Display results
            color = monitor.get_phase_color(current_phase)
            print(f"   📊 Phase: {current_phase} ({sub_phase}) [{color}]")
            print(f"   💬 Message: \"{status_message}\"")
            if context_data:
                print(f"   🔧 Context: {context_data}")
            
            print(f"   ✅ Bot monitoring successful")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n✅ Test completed successfully!")
    print("\n💡 To run continuous monitoring, use: monitor.start_monitoring()")


if __name__ == "__main__":
    asyncio.run(test_monitoring())