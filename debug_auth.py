#!/usr/bin/env python3
"""Debug authentication values"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

username = os.getenv('HBOT_USERNAME', '').strip('"')
password = os.getenv('HBOT_PASSWORD', '').strip('"')

print(f"Raw HBOT_USERNAME: {repr(os.getenv('HBOT_USERNAME'))}")
print(f"Raw HBOT_PASSWORD: {repr(os.getenv('HBOT_PASSWORD'))}")
print(f"Cleaned username: {repr(username)}")
print(f"Cleaned password: {repr(password[:3])}***")
print(f"Username length: {len(username)}")
print(f"Password length: {len(password)}")

# Test auth manually 
import asyncio
import aiohttp

async def test_auth():
    try:
        auth = aiohttp.BasicAuth(username, password)
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout, auth=auth) as session:
            async with session.get("http://localhost:8888/connectors/") as response:
                print(f"Response status: {response.status}")
                if response.status == 200:
                    connectors = await response.json()
                    print(f"Found {len(connectors)} connectors")
                    print(f"KuCoin available: {'kucoin' in connectors}")
                else:
                    print(f"Error: {await response.text()}")
    except Exception as e:
        print(f"Connection error: {e}")

asyncio.run(test_auth())