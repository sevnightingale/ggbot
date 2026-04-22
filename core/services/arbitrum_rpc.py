"""
Minimal Arbitrum RPC helpers — used to read agent wallet USDC balances before
bridging to Hyperliquid. Intentionally uses the public RPC by default; pair
with an API-keyed RPC (Alchemy, Infura) via env if rate limiting becomes an issue.

Native USDC on Arbitrum: 0xaf88d065e77c8cC2239327C5EDb3A432268e5831 (6 decimals).
"""

import os
from typing import Optional

import aiohttp

from core.common.logger import logger

ARBITRUM_RPC_URL = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
USDC_ARBITRUM = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
USDC_DECIMALS = 6

# balanceOf(address) selector — keccak256("balanceOf(address)")[:4]
_BALANCE_OF_SELECTOR = "0x70a08231"


async def get_usdc_balance(wallet_address: str) -> Optional[float]:
    """
    Return the USDC balance on Arbitrum for a wallet in human units (6 decimals).
    Returns None on RPC failure.
    """
    clean = wallet_address.lower().removeprefix("0x").rjust(64, "0")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [
            {"to": USDC_ARBITRUM, "data": _BALANCE_OF_SELECTOR + clean},
            "latest",
        ],
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(ARBITRUM_RPC_URL, json=payload) as resp:
                data = await resp.json()
    except Exception as e:
        logger.warning(f"Arbitrum RPC USDC balance failed for {wallet_address}: {e}")
        return None

    hex_result = data.get("result")
    if not hex_result:
        return None

    try:
        raw = int(hex_result, 16)
    except ValueError:
        return None
    return raw / (10 ** USDC_DECIMALS)
