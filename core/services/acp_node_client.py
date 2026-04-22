"""
HTTP client for the acp-node PM2 sidecar.

The sidecar runs on 127.0.0.1:3101 and exposes Privy-signed HL operations:
  - /setup-hl-unified-account
  - /authorize-hl-api-wallet
  - /withdraw-from-hl
  - /bridge-usdc-to-hl
  - /join-leaderboard
  - /forum-post

All calls require an `X-Service-Auth` header matching ACP_NODE_SHARED_SECRET.
The shared secret is the only thing standing between a local attacker on the VM
and signing arbitrary Privy actions — never expose the sidecar beyond loopback.
"""

import os
from typing import Any, Dict, Optional

import aiohttp

from core.common.logger import logger

ACP_NODE_URL = os.getenv("ACP_NODE_URL", "http://127.0.0.1:3101")


def _shared_secret() -> str:
    secret = os.getenv("ACP_NODE_SHARED_SECRET")
    if not secret:
        raise RuntimeError(
            "ACP_NODE_SHARED_SECRET is not configured — cannot call acp-node sidecar"
        )
    return secret


async def acp_node_post(
    path: str,
    payload: Dict[str, Any],
    timeout_seconds: int = 180,
) -> Dict[str, Any]:
    """
    POST a JSON payload to the acp-node sidecar.

    Returns a dict containing the sidecar's response body plus a sentinel
    `_httpStatus` integer for the caller to inspect. Does not raise on non-2xx
    responses — the caller decides how to react based on the status.
    """
    headers = {
        "X-Service-Auth": _shared_secret(),
        "Content-Type": "application/json",
    }
    url = f"{ACP_NODE_URL.rstrip('/')}{path}"
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                try:
                    data: Dict[str, Any] = await resp.json()
                except Exception:
                    data = {"error": "non-JSON response", "body": await resp.text()}
                data["_httpStatus"] = resp.status
                return data
        except aiohttp.ClientError as e:
            logger.error(f"acp-node POST {path} failed: {e}")
            return {"error": "acp-node unreachable", "detail": str(e), "_httpStatus": 0}


async def acp_node_health() -> Optional[Dict[str, Any]]:
    """GET /health — no auth required. Returns None if unreachable."""
    url = f"{ACP_NODE_URL.rstrip('/')}/health"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(url) as resp:
                return await resp.json()
    except Exception as e:
        logger.warning(f"acp-node health check failed: {e}")
        return None
