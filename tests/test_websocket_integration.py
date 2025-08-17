#!/usr/bin/env python3
"""
WebSocket Integration Test
Tests the complete bot monitoring WebSocket flow
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

# Test configuration
USER_ID = "00000000-0000-0000-0000-000000000001"  # ggShot user
WS_URL = f"ws://localhost:8000/ws/bot-status/{USER_ID}"
API_URL = "http://localhost:8000"

def print_status(message, status="INFO"):
    """Pretty print status messages"""
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "DATA": "\033[95m"
    }
    reset = "\033[0m"
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{colors.get(status, '')}{timestamp} [{status}] {message}{reset}")

async def test_websocket_connection():
    """Test WebSocket connection and monitor bot status updates"""
    
    print_status("Starting WebSocket Integration Test", "INFO")
    print_status(f"Connecting to: {WS_URL}", "INFO")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print_status("WebSocket connected successfully!", "SUCCESS")
            
            # Send initial heartbeat
            await websocket.send("heartbeat")
            print_status("Sent heartbeat", "INFO")
            
            # Track received messages
            message_count = 0
            bot_updates = {}
            last_heartbeat = time.time()
            
            # Listen for messages for 60 seconds
            timeout = 60
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    msg_type = data.get('type', 'unknown')
                    
                    if msg_type == 'heartbeat_ack':
                        print_status("Received heartbeat acknowledgment", "SUCCESS")
                        
                    elif msg_type == 'heartbeat':
                        print_status("Received server heartbeat", "INFO")
                        
                    elif msg_type == 'bot_status_update':
                        config_id = data.get('config_id', 'unknown')
                        bot_name = data.get('bot_name', 'Unknown Bot')
                        status = data.get('status', {})
                        
                        phase = status.get('phase', 'unknown')
                        color = status.get('color', 'gray')
                        message_text = status.get('message', 'No message')
                        context = status.get('context', {})
                        
                        # Track unique bots
                        if config_id not in bot_updates:
                            bot_updates[config_id] = {
                                'name': bot_name,
                                'updates': 0,
                                'phases': set()
                            }
                        
                        bot_updates[config_id]['updates'] += 1
                        bot_updates[config_id]['phases'].add(phase)
                        
                        # Display the update
                        print_status(f"Bot Update #{message_count}", "DATA")
                        print(f"  Bot: {bot_name} ({config_id[:8]}...)")
                        print(f"  Phase: {phase} ({color})")
                        print(f"  Message: {message_text}")
                        
                        if context:
                            if context.get('symbol'):
                                print(f"  Symbol: {context['symbol']}")
                            if context.get('confidence'):
                                print(f"  Confidence: {context['confidence']}%")
                            if context.get('direction'):
                                print(f"  Direction: {context['direction']}")
                            if context.get('entryPrice'):
                                print(f"  Entry Price: ${context['entryPrice']}")
                        print()
                        
                    else:
                        print_status(f"Received unknown message type: {msg_type}", "WARNING")
                    
                    # Send periodic heartbeat to keep connection alive
                    if time.time() - last_heartbeat > 20:
                        await websocket.send("heartbeat")
                        print_status("Sent keepalive heartbeat", "INFO")
                        last_heartbeat = time.time()
                        
                except asyncio.TimeoutError:
                    # No message received in 5 seconds
                    elapsed = int(time.time() - start_time)
                    remaining = timeout - elapsed
                    if remaining > 0:
                        print_status(f"Waiting for messages... ({remaining}s remaining)", "INFO")
                    
                    # Send heartbeat to keep connection alive
                    await websocket.send("heartbeat")
                    
            # Print summary
            print_status("=" * 60, "INFO")
            print_status("WebSocket Test Summary", "SUCCESS")
            print(f"  Total messages received: {message_count}")
            print(f"  Unique bots monitored: {len(bot_updates)}")
            
            for config_id, info in bot_updates.items():
                print(f"\n  Bot: {info['name']} ({config_id[:8]}...)")
                print(f"    Updates received: {info['updates']}")
                print(f"    Phases observed: {', '.join(info['phases'])}")
            
            if message_count == 0:
                print_status("No bot status updates received!", "WARNING")
                print_status("Possible issues:", "WARNING")
                print("  1. No active bots in the database")
                print("  2. Bot monitoring task not running")
                print("  3. WebSocket broadcast not working")
            else:
                print_status(f"Test completed successfully! Received {message_count} messages", "SUCCESS")
                
    except websockets.exceptions.WebSocketException as e:
        print_status(f"WebSocket error: {e}", "ERROR")
    except Exception as e:
        print_status(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()

async def check_active_bots():
    """Check for active bots via API"""
    import aiohttp
    
    print_status("Checking active bots via API...", "INFO")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/agent/api/bots") as response:
                if response.status == 200:
                    bots = await response.json()
                    active_count = sum(1 for bot in bots if bot.get('status') == 'active')
                    print_status(f"Found {len(bots)} total bots, {active_count} active", "SUCCESS")
                    
                    for bot in bots:
                        if bot.get('status') == 'active':
                            name = bot.get('config_name', 'Unknown')
                            config_id = bot.get('config_id', 'unknown')
                            print(f"  • {name} ({config_id[:8]}...) - ACTIVE")
                else:
                    print_status(f"API returned status {response.status}", "ERROR")
                    
    except Exception as e:
        print_status(f"Failed to check bots via API: {e}", "ERROR")

async def main():
    """Run all tests"""
    print_status("=" * 60, "INFO")
    print_status("GGBot WebSocket Integration Test", "INFO")
    print_status("=" * 60, "INFO")
    print()
    
    # First check what bots are available
    await check_active_bots()
    print()
    
    # Then test WebSocket connection
    await test_websocket_connection()

if __name__ == "__main__":
    asyncio.run(main())