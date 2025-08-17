#!/usr/bin/env python3
"""
Test script to verify both active and inactive bot status updates
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_inactive_status():
    """Test that both active and inactive bots are sending status updates"""
    
    user_id = "00000000-0000-0000-0000-000000000001"
    ws_url = f"ws://localhost:8000/ws/bot-status/{user_id}"
    
    print("🔗 Testing Bot Status Updates (Active + Inactive)")
    print(f"🔌 Connecting to: {ws_url}")
    print("=" * 60)
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected! Listening for bot updates...")
            
            # Track received bots by phase
            bots_by_phase = {}
            message_count = 0
            
            # Listen for 30 seconds
            timeout = 30
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'bot_status_update':
                        message_count += 1
                        
                        # Extract bot info
                        bot_name = data.get('bot_name', 'Unknown Bot')
                        status = data.get('status', {})
                        phase = status.get('phase', 'unknown')
                        color = status.get('color', 'gray')
                        message_text = status.get('message', 'No message')
                        config_id = data.get('config_id', 'unknown')
                        
                        # Track by phase
                        if phase not in bots_by_phase:
                            bots_by_phase[phase] = []
                        
                        bot_info = {
                            'name': bot_name,
                            'config_id': config_id[:8],
                            'message': message_text,
                            'color': color
                        }
                        
                        # Only add if not already seen
                        if not any(b['config_id'] == bot_info['config_id'] for b in bots_by_phase[phase]):
                            bots_by_phase[phase].append(bot_info)
                        
                        # Print status update
                        emoji = {"inactive": "⚫", "idle": "🔵", "extraction": "🔵", "decision": "🟢", "trading": "🟠"}.get(phase, "⚪")
                        print(f"{emoji} {bot_name} ({config_id[:8]}): {phase} - {message_text}")
                        
                except asyncio.TimeoutError:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    if remaining > 0:
                        print(f"⏳ Waiting... ({int(remaining)}s remaining)")
                    
            # Print summary
            print("\n" + "=" * 60)
            print("📊 FINAL STATUS SUMMARY")
            print(f"📈 Total messages received: {message_count}")
            print(f"📋 Unique bot phases detected: {len(bots_by_phase)}")
            
            for phase, bots in bots_by_phase.items():
                emoji = {"inactive": "⚫", "idle": "🔵", "extraction": "🔵", "decision": "🟢", "trading": "🟠"}.get(phase, "⚪")
                print(f"\n{emoji} {phase.upper()} BOTS ({len(bots)} total):")
                for bot in bots:
                    print(f"   • {bot['name']} ({bot['config_id']}) - {bot['color']}")
                    print(f"     └─ {bot['message']}")
            
            # Verify we have both active and inactive states
            has_active = any(phase in ['idle', 'extraction', 'decision', 'trading'] for phase in bots_by_phase.keys())
            has_inactive = 'inactive' in bots_by_phase
            
            print(f"\n🎯 TEST RESULTS:")
            print(f"   ✅ Active bot status detected: {'YES' if has_active else 'NO'}")
            print(f"   ✅ Inactive bot status detected: {'YES' if has_inactive else 'NO'}")
            
            if has_active and has_inactive:
                print("   🌟 SUCCESS: Both active and inactive bot statuses are working!")
            elif has_active:
                print("   ⚠️  PARTIAL: Only active bot statuses detected")
            elif has_inactive:
                print("   ⚠️  PARTIAL: Only inactive bot statuses detected")
            else:
                print("   ❌ FAILED: No bot status updates received")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Bot Status Test - Active vs Inactive")
    print("Testing 5-phase system: inactive, idle, extraction, decision, trading\n")
    
    try:
        asyncio.run(test_inactive_status())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")