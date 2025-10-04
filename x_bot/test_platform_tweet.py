#!/usr/bin/env python3
"""
One-time test script to manually post platform status tweet.
Run this to test the tweet without waiting for scheduled time.
"""

import asyncio
from dotenv import load_dotenv
from x_bot.utils.x_client import XClient
from x_bot.schedulers import platform_status

load_dotenv()


async def main():
    """Manually trigger platform status tweet."""
    print("=" * 60)
    print("Testing Platform Status Tweet")
    print("=" * 60)
    print()

    # Initialize X client
    x_client = XClient()

    # Test auth
    print("Testing authentication...")
    if not x_client.test_auth():
        print("❌ Authentication failed!")
        return

    print("✅ Authentication successful")
    print()

    # Post the tweet
    print("Posting platform status tweet...")
    await platform_status.post_platform_status(x_client)

    print()
    print("=" * 60)
    print("Done! Check @ggbots_ai on X")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
