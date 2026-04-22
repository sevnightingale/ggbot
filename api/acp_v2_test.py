"""
ACP v2 Migration — Admin-only Phase 0 test harness.

Single-gate validation of the Virtuals v2 flow end-to-end:
  1. OAuth (popup 1): GET /auth/cli/url -> poll /auth/cli/token
  2. Agent create:    POST /agents
  3. Signer approval (popup 2): POST /agents/{id}/signer -> poll status
  4. HL test trade:   open + close $5 ETH long via agent's API wallet
  5. Monitoring verify: HyperliquidAccountAdapter against the Privy-provisioned wallet

No production data touched. Sessions + transient keys live only in Redis with short TTLs.

References:
  - ACP v2 base URL: @virtuals-protocol/acp-node-v2/src/core/constants.ts
  - Endpoint surface: @virtuals-protocol/acp-cli/src/lib/api/{auth,agent}.ts
  - Signer URL + publicKey query-param pattern: @virtuals-protocol/acp-cli/src/commands/agent.ts
"""

import os
import base64
import asyncio
import requests
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import redis
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from core.auth.supabase_auth import AuthenticatedUser
from core.common.logger import logger
from api.admin import require_admin


router = APIRouter(prefix="/api/v2/acp-test", tags=["acp-v2-test"])

ACP_SERVER_URL = "https://api.acp.virtuals.io"

_redis = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True,
)

JWT_TTL_SEC = 25 * 60
REQUEST_ID_TTL_SEC = 10 * 60


def _jwt_key(admin_user_id: str) -> str:
    return f"acp_v2_test:jwt:{admin_user_id}"


def _request_key(request_id: str) -> str:
    return f"acp_v2_test:req:{request_id}"


def _signer_priv_key(admin_user_id: str, agent_id: str) -> str:
    return f"acp_v2_test:signer_priv:{admin_user_id}:{agent_id}"


def _get_jwt(admin_user_id: str) -> Optional[str]:
    return _redis.get(_jwt_key(admin_user_id))


def _generate_p256_keypair() -> tuple[str, str]:
    """
    Generate a fresh P-256 keypair for signer registration.

    Returns (private_key_pem_base64, public_key_spki_der_base64).

    Public key is emitted as SPKI-DER (SubjectPublicKeyInfo) base64 — the format
    Privy expects for signer registration. Raw uncompressed X9.62 point (0x04 prefix)
    causes 500 on the signer approve endpoint; SPKI wraps the same point in an
    AlgorithmIdentifier envelope (prefix bytes 30 59 30 13 06 07 2a 86 48 ce 3d 02 01 ...).
    Ref: https://docs.privy.io/api-reference/signers/authenticate

    The acp-cli ships a native binary (acp-cli-signer) that keeps private keys in the
    OS keychain. That pattern doesn't apply to a server — we keep the private key in
    Redis (Phase 0) or Vault (Phase 1+) and serve signing from the backend.
    """
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_spki_der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return (
        base64.b64encode(priv_pem).decode("ascii"),
        base64.b64encode(pub_spki_der).decode("ascii"),
    )


# ============================================================================
# Popup 1 — Virtuals OAuth
# ============================================================================

class AuthStartResponse(BaseModel):
    authUrl: str
    requestId: str


@router.post("/auth-start", response_model=AuthStartResponse)
async def auth_start(admin: AuthenticatedUser = Depends(require_admin)):
    """Begin Virtuals v2 CLI OAuth. Returns URL to open in popup."""
    resp = requests.get(f"{ACP_SERVER_URL}/auth/cli/url", timeout=10)
    if resp.status_code != 200:
        raise HTTPException(
            502,
            f"Virtuals auth-url failed: {resp.status_code} {resp.text[:200]}",
        )
    data = (resp.json() or {}).get("data") or {}
    auth_url = data.get("url")
    request_id = data.get("requestId")
    if not auth_url or not request_id:
        raise HTTPException(502, f"Virtuals auth response missing fields: {resp.text[:200]}")
    _redis.setex(_request_key(request_id), REQUEST_ID_TTL_SEC, admin.user_id)
    logger.info(
        f"acp-v2-test auth-start: admin={admin.user_id[:8]} requestId={request_id[:8]}"
    )
    return AuthStartResponse(authUrl=auth_url, requestId=request_id)


@router.get("/auth-poll")
async def auth_poll(
    requestId: str = Query(...),
    admin: AuthenticatedUser = Depends(require_admin),
) -> Dict[str, Any]:
    """Poll Virtuals for CLI token. Caches JWT in Redis on success."""
    owner = _redis.get(_request_key(requestId))
    if owner != admin.user_id:
        raise HTTPException(403, "requestId not owned by this admin session")
    resp = requests.get(
        f"{ACP_SERVER_URL}/auth/cli/token",
        params={"requestId": requestId},
        timeout=5,
    )
    if resp.status_code != 200:
        return {"status": "pending", "httpStatus": resp.status_code}
    data = (resp.json() or {}).get("data") or {}
    token = data.get("token") or data.get("accessToken")
    if not token:
        return {"status": "pending"}
    _redis.setex(_jwt_key(admin.user_id), JWT_TTL_SEC, token)
    wallet = data.get("walletAddress")
    logger.info(
        f"acp-v2-test auth-poll: admin={admin.user_id[:8]} token cached wallet={wallet}"
    )
    return {
        "status": "completed",
        "jwt_preview": f"{token[:12]}..." if token else None,
        "walletAddress": wallet,
    }


# ============================================================================
# Popup 2 — Agent Create + Signer Approval
# ============================================================================

class AgentCreateRequest(BaseModel):
    name: str
    description: Optional[str] = "Phase 0 test agent for ggbots ACP v2 migration"


class AgentCreateResponse(BaseModel):
    agent: Dict[str, Any]
    signerUrl: str
    signerRequestId: str
    publicKey: str


@router.post("/agent-create", response_model=AgentCreateResponse)
async def agent_create(
    body: AgentCreateRequest,
    admin: AuthenticatedUser = Depends(require_admin),
):
    """
    Create a Virtuals v2 agent and begin signer registration.

    1. POST /agents with Bearer JWT -> Agent (with Privy walletAddress)
    2. Generate P-256 keypair in-process, stash private key in Redis
    3. POST /agents/{id}/signer -> {url, requestId} for popup 2
    4. Append &publicKey=<base64> to URL (matches CLI at commands/agent.ts)
    """
    jwt = _get_jwt(admin.user_id)
    if not jwt:
        raise HTTPException(401, "Virtuals JWT missing or expired. Run auth-start first.")

    headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

    resp = requests.post(
        f"{ACP_SERVER_URL}/agents",
        headers=headers,
        json={"name": body.name, "description": body.description, "role": "HYBRID"},
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        raise HTTPException(
            502, f"Virtuals /agents failed: {resp.status_code} {resp.text[:300]}"
        )
    payload = resp.json() or {}
    agent = payload.get("data") or payload
    agent_id = agent.get("id")
    if not agent_id:
        raise HTTPException(502, f"Virtuals agent response missing id: {resp.text[:200]}")
    logger.info(
        f"acp-v2-test agent-create: admin={admin.user_id[:8]} agentId={agent_id} "
        f"wallet={agent.get('walletAddress')}"
    )

    priv_b64, pub_b64 = _generate_p256_keypair()
    _redis.setex(
        _signer_priv_key(admin.user_id, str(agent_id)),
        JWT_TTL_SEC,
        priv_b64,
    )

    resp2 = requests.post(
        f"{ACP_SERVER_URL}/agents/{agent_id}/signer",
        headers=headers,
        timeout=30,
    )
    if resp2.status_code not in (200, 201):
        raise HTTPException(
            502,
            f"Virtuals signer endpoint failed: {resp2.status_code} {resp2.text[:300]}",
        )
    sig_payload = resp2.json() or {}
    sig_data = sig_payload.get("data") or sig_payload
    sig_url = sig_data.get("url")
    sig_req_id = sig_data.get("requestId")
    if not sig_url or not sig_req_id:
        raise HTTPException(502, f"Signer response missing fields: {resp2.text[:200]}")

    sep = "&" if "?" in sig_url else "?"
    final_url = f"{sig_url}{sep}publicKey={pub_b64}"
    _redis.setex(_request_key(sig_req_id), REQUEST_ID_TTL_SEC, admin.user_id)
    logger.info(
        f"acp-v2-test agent-create: signer URL issued requestId={sig_req_id[:8]}"
    )

    return AgentCreateResponse(
        agent=agent,
        signerUrl=final_url,
        signerRequestId=sig_req_id,
        publicKey=pub_b64,
    )


@router.get("/signer-poll")
async def signer_poll(
    agentId: str = Query(...),
    requestId: str = Query(...),
    admin: AuthenticatedUser = Depends(require_admin),
) -> Dict[str, Any]:
    """Poll Virtuals signer endpoint until status=completed."""
    owner = _redis.get(_request_key(requestId))
    if owner != admin.user_id:
        raise HTTPException(403, "requestId not owned by this admin session")
    jwt = _get_jwt(admin.user_id)
    if not jwt:
        raise HTTPException(401, "Virtuals JWT missing or expired")
    headers = {"Authorization": f"Bearer {jwt}"}
    resp = requests.get(
        f"{ACP_SERVER_URL}/agents/{agentId}/signer",
        params={"requestId": requestId},
        headers=headers,
        timeout=5,
    )
    if resp.status_code != 200:
        return {"status": "pending", "httpStatus": resp.status_code}
    data = (resp.json() or {}).get("data") or {}
    status = data.get("status")
    logger.info(
        f"acp-v2-test signer-poll: admin={admin.user_id[:8]} agentId={agentId} status={status}"
    )
    return {"status": status or "pending"}


# ============================================================================
# Hyperliquid Verification
# ============================================================================

class VerifyTradeRequest(BaseModel):
    agentWalletAddress: str   # Privy-provisioned master wallet
    hlApiWalletKey: str       # API wallet privkey (signs; can't withdraw)


@router.post("/verify-trade")
async def verify_trade(
    body: VerifyTradeRequest,
    admin: AuthenticatedUser = Depends(require_admin),
) -> Dict[str, Any]:
    """Open + close a minimal ETH long through the agent's HL API wallet."""
    try:
        import eth_account
        from hyperliquid.exchange import Exchange
        from hyperliquid.utils import constants

        wallet = eth_account.Account.from_key(body.hlApiWalletKey)
        exchange = Exchange(
            wallet,
            constants.MAINNET_API_URL,
            account_address=body.agentWalletAddress,
        )

        try:
            exchange.update_leverage(3, "ETH", is_cross=True)
        except Exception as lev_err:
            logger.warning(f"acp-v2-test verify-trade leverage set warning: {lev_err}")

        test_size = 0.01
        open_result = exchange.market_open("ETH", True, test_size, slippage=0.05)
        logger.info(f"acp-v2-test verify-trade open: {open_result}")

        if open_result.get("status") != "ok":
            return {"status": "failed", "stage": "open", "detail": open_result}

        statuses = open_result.get("response", {}).get("data", {}).get("statuses", [])
        entry_price = None
        fill_error = None
        for s in statuses:
            if "filled" in s:
                entry_price = float(s["filled"]["avgPx"])
                break
            if "error" in s:
                fill_error = s["error"]
                break
        if fill_error:
            return {"status": "failed", "stage": "fill", "detail": fill_error}
        if entry_price is None:
            return {"status": "failed", "stage": "fill", "detail": statuses}

        await asyncio.sleep(2)
        close_result = exchange.market_close("ETH")
        logger.info(f"acp-v2-test verify-trade close: {close_result}")

        close_status = "unknown"
        if close_result:
            close_status = close_result.get("status", "unknown")
            for cs in close_result.get("response", {}).get("data", {}).get("statuses", []):
                if "error" in cs:
                    close_status = f"error: {cs['error']}"
                    break

        return {
            "status": "success",
            "entry_price": entry_price,
            "close_status": close_status,
        }
    except Exception as e:
        logger.error(f"acp-v2-test verify-trade failed: {e}")
        return {"status": "failed", "stage": "exception", "detail": str(e)}


@router.get("/verify-snapshot")
async def verify_snapshot(
    wallet: str = Query(...),
    admin: AuthenticatedUser = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Query HL Info API against the agent wallet and project the shape
    HyperliquidAccountAdapter.get_current_snapshot consumes. Lets us diff
    Privy-wallet responses against reference v1 HL bot snapshots.
    """
    try:
        from hyperliquid.info import Info
        from hyperliquid.utils import constants

        info = Info(constants.MAINNET_API_URL, skip_ws=True)
        user_state = info.user_state(wallet)
        fills = info.user_fills_by_time(wallet, 0)

        margin = user_state.get("marginSummary", {}) or {}
        positions = user_state.get("assetPositions", []) or []

        processed = {
            "account_value": float(margin.get("accountValue", 0) or 0),
            "total_margin_used": float(margin.get("totalMarginUsed", 0) or 0),
            "total_ntl_pos": float(margin.get("totalNtlPos", 0) or 0),
            "total_raw_usd": float(margin.get("totalRawUsd", 0) or 0),
            "withdrawable": float(user_state.get("withdrawable", 0) or 0),
            "open_position_count": len(positions),
            "fill_count": len(fills),
            "first_closed_pnl": None,
        }
        for f in fills:
            if "closedPnl" in f:
                processed["first_closed_pnl"] = float(f["closedPnl"])
                break

        return {
            "status": "success",
            "wallet": wallet,
            "processed": processed,
            "raw_user_state": user_state,
            "raw_fills_sample": fills[:5],
            "fills_total": len(fills),
        }
    except Exception as e:
        logger.error(f"acp-v2-test verify-snapshot failed: {e}")
        raise HTTPException(502, f"Snapshot query failed: {str(e)}")


# ============================================================================
# Session helpers (status + reset)
# ============================================================================

@router.get("/session-status")
async def session_status(admin: AuthenticatedUser = Depends(require_admin)) -> Dict[str, Any]:
    """Show whether a Virtuals JWT is cached for this admin."""
    jwt = _get_jwt(admin.user_id)
    ttl = _redis.ttl(_jwt_key(admin.user_id)) if jwt else -1
    return {
        "connected": bool(jwt),
        "jwt_preview": (jwt[:12] + "...") if jwt else None,
        "ttl_seconds": ttl if ttl and ttl > 0 else None,
    }


@router.post("/session-reset")
async def session_reset(admin: AuthenticatedUser = Depends(require_admin)) -> Dict[str, Any]:
    """Clear cached JWT (test-only escape hatch)."""
    _redis.delete(_jwt_key(admin.user_id))
    return {"status": "cleared"}
