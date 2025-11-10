#!/usr/bin/env python3
"""
Minimal test script to verify session ID capture from Claude Agent SDK.
Tests the session capture pattern without executing trading logic.
"""

import asyncio
import os
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def test_session_capture():
    """Test session ID capture with minimal SDK setup."""

    print("=== Testing Claude SDK Session Capture ===\n")

    # Minimal options - no MCP server, no tools
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-5-20250929",
        max_turns=5  # Limit to 5 turns to avoid cost
    )

    print("1. Creating SDK client...")
    async with ClaudeSDKClient(options=options) as client:
        print("2. Client created successfully")

        print("3. Sending test query...")
        await client.query("Hello, can you hear me?")

        print("4. Listening for messages...\n")

        message_count = 0
        session_id = None

        async for message in client.receive_messages():
            message_count += 1
            msg_type = type(message).__name__

            print(f"[Message {message_count}] Type: {msg_type}")

            # Check for type attribute
            if hasattr(message, 'type'):
                print(f"  ├─ message.type = '{message.type}'")

                if hasattr(message, 'subtype'):
                    print(f"  ├─ message.subtype = '{message.subtype}'")

                if hasattr(message, 'session_id'):
                    print(f"  └─ message.session_id = '{message.session_id[:20]}...'")
                    session_id = message.session_id
                else:
                    print(f"  └─ No session_id attribute")

                # Try to capture from system init message
                if message.type == 'system' and hasattr(message, 'subtype') and message.subtype == 'init':
                    if hasattr(message, 'session_id'):
                        session_id = message.session_id
                        print(f"\n✅ SUCCESS: Captured session ID from system init message!")
                        print(f"   Session ID: {session_id[:20]}...")
                        break
                    else:
                        print(f"\n⚠️  WARNING: Found system init message but no session_id attribute!")

            else:
                print(f"  └─ No 'type' attribute")

                # Check if it's a SystemMessage instance
                if msg_type == 'SystemMessage':
                    print(f"     (But is a SystemMessage instance)")
                    print(f"     Available attributes: {dir(message)}")

            # Stop after 10 messages to avoid costs
            if message_count >= 10:
                print(f"\n⏹️  Stopping after {message_count} messages (cost control)")
                break

        print("\n=== Test Complete ===")

        if session_id:
            print(f"✅ Session ID captured: {session_id[:30]}...")
            return session_id
        else:
            print("❌ Failed to capture session ID")
            print("\nPossible issues:")
            print("  1. SDK doesn't send init message in receive_messages()")
            print("  2. Session ID is exposed differently (e.g., client.session_id)")
            print("  3. Need to check SDK source code or different message iterator")
            return None

if __name__ == "__main__":
    asyncio.run(test_session_capture())
