#!/usr/bin/env python3
"""
Simple live bot status test - shows real-time updates
"""

import asyncio
import websockets
import json
from datetime import datetime

async def listen_to_bot_status():
    """Connect and listen for bot status updates"""
    
    user_id = "00000000-0000-0000-0000-000000000001"
    ws_url = f"ws://localhost:8000/ws/bot-status/{user_id}"
    
    print(f"🔌 Connecting to WebSocket: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected! Listening for bot updates...")
            print("=" * 60)
            
            # Send initial heartbeat
            await websocket.send("heartbeat")
            
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if data.get('type') == 'bot_status_update':
                        # Extract bot info
                        bot_name = data.get('bot_name', 'Unknown Bot')
                        status = data.get('status', {})
                        phase = status.get('phase', 'unknown')
                        color = status.get('color', 'gray')
                        message_text = status.get('message', 'No message')
                        context = status.get('context', {})
                        
                        # Format timestamp
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        # Print the update
                        print(f"[{timestamp}] 🤖 {bot_name}")
                        print(f"   Phase: {phase} ({color})")
                        print(f"   Status: {message_text}")
                        
                        # Show context data if available
                        if context.get('symbol'):
                            print(f"   📊 Symbol: {context['symbol']}")
                        if context.get('confidence'):
                            print(f"   🎯 Confidence: {context['confidence']}%") 
                        if context.get('direction'):
                            print(f"   📈 Direction: {context['direction']}")
                        if context.get('timeSinceLastSignal'):
                            print(f"   ⏰ Last Signal: {context['timeSinceLastSignal']}")
                        
                        print()  # Empty line for readability
                        
                    elif data.get('type') == 'heartbeat':
                        print(f"💓 Server heartbeat at {datetime.now().strftime('%H:%M:%S')}")
                        
                except KeyboardInterrupt:
                    print("\n👋 Disconnecting...")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    print("🔴 LIVE Bot Status Monitor")
    print("Press Ctrl+C to exit\n")
    
    try:
        asyncio.run(listen_to_bot_status())
    except KeyboardInterrupt:
        print("\n✅ Disconnected successfully!")