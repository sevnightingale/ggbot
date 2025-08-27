#!/usr/bin/env python3
"""Debug HTTP headers and auth comparison"""

import os
import base64
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('HBOT_USERNAME', '').strip('"')
password = os.getenv('HBOT_PASSWORD', '').strip('"')

# What curl would send
curl_auth = base64.b64encode(f"{username}:{password}".encode()).decode()
print(f"Curl auth header: Basic {curl_auth}")

# Test manual header vs aiohttp BasicAuth
async def test_auth_methods():
    url = "http://localhost:8888/connectors/"
    
    # Method 1: aiohttp BasicAuth
    print("\n1. Testing aiohttp BasicAuth:")
    try:
        auth = aiohttp.BasicAuth(username, password)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=auth) as response:
                print(f"   Status: {response.status}")
                if response.status != 200:
                    print(f"   Error: {await response.text()}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 2: Manual Authorization header
    print("\n2. Testing manual Authorization header:")
    try:
        headers = {"Authorization": f"Basic {curl_auth}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    connectors = await response.json()
                    print(f"   ✅ SUCCESS! Found {len(connectors)} connectors")
                    return True
                else:
                    print(f"   Error: {await response.text()}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    return False

asyncio.run(test_auth_methods())