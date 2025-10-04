"""
Close Symphony position.
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

SYMPHONY_API_KEY = os.getenv("SYMPHONY_API_KEY")
SYMPHONY_BASE_URL = "https://api.symphony.io"
AGENT_ID = "22b35152-f3a5-4b21-8a0f-04691c155e33"
BATCH_ID = "c2890a4e-d808-4b45-ad1f-cb5be52fd406"


async def close_trade(agent_id: str, batch_id: str):
    """Close a batch trade on Symphony."""
    url = f"{SYMPHONY_BASE_URL}/agent/batch-close"

    headers = {
        "x-api-key": SYMPHONY_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "agentId": agent_id,
        "batchId": batch_id
    }

    print(f"🔴 Closing batch: {batch_id}")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"\n✅ Trade closed successfully!")
                print(f"   Successful: {data['successful']}")
                print(f"   Skipped: {data.get('skipped', 0)}")
                print(f"   Failed: {data['failed']}")
                print(f"\nFull response:")
                print(data)
                return data
            else:
                error_text = await response.text()
                print(f"\n❌ Error {response.status}: {error_text}")
                return None


if __name__ == "__main__":
    asyncio.run(close_trade(AGENT_ID, BATCH_ID))
