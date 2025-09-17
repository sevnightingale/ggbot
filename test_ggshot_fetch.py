#!/usr/bin/env python3
"""
Quick test script to check if we can fetch the latest ggShot signal.
This tests the _fetch_latest_ggshot_signal function from ggbot.py.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_ggshot_fetch():
    """Test fetching the latest ggShot signal."""
    print("🧪 Testing ggShot signal fetching...")

    try:
        # Import the orchestrator
        from ggbot import GGBotOrchestrator

        # Create orchestrator instance
        orchestrator = GGBotOrchestrator()

        print("📡 Attempting to fetch latest ggShot signal...")

        # Test the fetch function
        signal = await orchestrator._fetch_latest_ggshot_signal()

        print("✅ Successfully fetched ggShot signal!")
        print(f"   Symbol: {signal.symbol}")
        print(f"   Direction: {signal.direction}")
        print(f"   Timeframe: {signal.timeframe}")
        print(f"   Confidence: {signal.confidence}")
        print(f"   Source: {signal.source}")
        print(f"   Timestamp: {signal.timestamp}")
        print(f"   Reasoning: {signal.reasoning}")
        print(f"   Raw Message (first 100 chars): {signal.raw_message[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Failed to fetch ggShot signal: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Main test function."""
    print("=" * 60)
    print("🚀 ggShot Signal Fetching Test")
    print("=" * 60)

    success = await test_ggshot_fetch()

    print("=" * 60)
    if success:
        print("🎉 Test completed successfully!")
        print("✅ ggShot signal fetching is working")
    else:
        print("💥 Test failed!")
        print("❌ ggShot signal fetching needs debugging")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())