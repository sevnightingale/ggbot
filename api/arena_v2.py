"""
ACP v2 Arena API — production Deploy Live Version endpoints.

Flow:
  1. Popup 1 (one-time per user, JWT lives in Redis):
        /connect-start → Virtuals OAuth URL
        /connect-poll  → JWT into Redis
  2. Popup 2 (per bot):
        /deploy-live  → create Virtuals agent, new config, signer URL
        /deploy-poll  → wait for signer approval, then headless HL setup
                        (setup-hl-unified-account + authorize-hl-api-wallet),
                        status='active' when complete
  3. Runtime:
        /status        → read-only balance/positions/state
        /check-deposit → Arbitrum USDC balance → bridge to HL → first-time
                         join-leaderboard for DGClaw registration
        /withdraw      → HL → agent wallet → optional forward to user address

Every Privy-signed action flows through the acp-node sidecar on localhost.
The Python backend never holds Privy session secrets at runtime — it only
holds the P-256 signer key in Vault and passes it to the sidecar per request.
"""

import base64
import copy
import json
import os
import uuid
from typing import Any, Dict, Optional

import redis
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.auth.supabase_auth import AuthenticatedUser, get_current_user_v2
from core.auth.vault_utils import (
    create_vault_secret,
    get_arena_v2_credential,
    get_vault_secret,
    store_arena_v2_dgclaw_key,
    store_arena_v2_hl_api_wallet,
)
from core.common.db import db_execute, db_fetch_all, db_fetch_one
from core.common.logger import logger
from core.services.acp_node_client import acp_node_post
from core.services.arbitrum_rpc import get_usdc_balance

router = APIRouter(prefix="/api/v2/arena", tags=["arena-v2"])

ACP_SERVER_URL = "https://api.acp.virtuals.io"
JWT_TTL_SEC = 25 * 60
REQUEST_ID_TTL_SEC = 10 * 60
DEPLOY_STATE_TTL_SEC = 30 * 60

HL_BRIDGE_MIN_USDC = 5.0
ACP_FEE_RESERVE = 1.0        # USDC kept on Arbitrum for join-leaderboard / future ACP fees

_redis = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True,
)


# ============================================================================
# Redis key helpers — keep namespacing tight so v2 state never collides with v1
# ============================================================================

def _jwt_key(user_id: str) -> str:
    return f"arena_v2:jwt:{user_id}"

def _req_key(request_id: str) -> str:
    return f"arena_v2:req:{request_id}"

def _deploy_key(signer_request_id: str) -> str:
    """Maps signer requestId → agent_record_id for deploy-poll."""
    return f"arena_v2:deploy:{signer_request_id}"


# ============================================================================
# Helpers
# ============================================================================

def _get_jwt(user_id: str) -> Optional[str]:
    return _redis.get(_jwt_key(user_id))


def _generate_p256_keypair() -> tuple[str, str]:
    """
    P-256 keypair for Privy signer registration.
    Returns (base64-PKCS8-PEM-private, base64-SPKI-DER-public).

    SPKI-DER is load-bearing — Privy rejects raw X9.62 uncompressed points
    with a generic 500 on the signer approve endpoint. See Phase 0 notes.
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


async def _verify_ownership(config_id: str, user_id: str) -> bool:
    row = await db_fetch_one(
        "SELECT 1 FROM configurations WHERE config_id = %s AND user_id = %s",
        (config_id, user_id),
    )
    return bool(row)


# ============================================================================
# Popup 1 — Virtuals OAuth
# ============================================================================

class ConnectStartResponse(BaseModel):
    authUrl: str
    requestId: str


@router.post("/connect-start", response_model=ConnectStartResponse)
async def connect_start(
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
):
    """Initiate popup 1 — Virtuals account OAuth."""
    try:
        resp = requests.get(f"{ACP_SERVER_URL}/auth/cli/url", timeout=10)
    except Exception as e:
        raise HTTPException(502, f"Virtuals auth-url request failed: {e}")

    if resp.status_code != 200:
        raise HTTPException(
            502, f"Virtuals auth-url failed: {resp.status_code} {resp.text[:200]}"
        )
    data = (resp.json() or {}).get("data") or {}
    url = data.get("url")
    request_id = data.get("requestId")
    if not url or not request_id:
        raise HTTPException(502, "Virtuals auth response missing fields")

    _redis.setex(_req_key(request_id), REQUEST_ID_TTL_SEC, current_user.user_id)
    logger.info(
        f"arena_v2 connect-start: user={current_user.user_id[:8]} requestId={request_id[:8]}"
    )
    return ConnectStartResponse(authUrl=url, requestId=request_id)


@router.get("/connect-poll")
async def connect_poll(
    requestId: str = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """Poll for Virtuals JWT. Caches in Redis on success."""
    owner = _redis.get(_req_key(requestId))
    if owner != current_user.user_id:
        raise HTTPException(403, "requestId not owned by this session")

    try:
        resp = requests.get(
            f"{ACP_SERVER_URL}/auth/cli/token",
            params={"requestId": requestId},
            timeout=5,
        )
    except Exception as e:
        return {"status": "pending", "error": str(e)}

    if resp.status_code != 200:
        return {"status": "pending", "httpStatus": resp.status_code}
    data = (resp.json() or {}).get("data") or {}
    token = data.get("token") or data.get("accessToken")
    if not token:
        return {"status": "pending"}

    _redis.setex(_jwt_key(current_user.user_id), JWT_TTL_SEC, token)
    logger.info(
        f"arena_v2 connect-poll: JWT cached for user={current_user.user_id[:8]}"
    )
    return {
        "status": "completed",
        "walletAddress": data.get("walletAddress"),
    }


@router.get("/connection-status")
async def connection_status(
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """Whether the user has an active Virtuals JWT (popup 1 completed)."""
    jwt = _get_jwt(current_user.user_id)
    ttl = _redis.ttl(_jwt_key(current_user.user_id)) if jwt else -1
    return {
        "connected": bool(jwt),
        "ttl_seconds": ttl if ttl and ttl > 0 else None,
    }


@router.post("/disconnect")
async def disconnect(
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """Clear the cached Virtuals JWT."""
    _redis.delete(_jwt_key(current_user.user_id))
    return {"status": "cleared"}


# ============================================================================
# Popup 2 — Deploy Live Version
# ============================================================================

class DeployLiveRequest(BaseModel):
    source_config_id: str
    agent_name: Optional[str] = None


class DeployLiveResponse(BaseModel):
    new_config_id: str
    agent_record_id: str
    virtuals_agent_id: str
    agent_wallet_address: str
    signerUrl: str
    signerRequestId: str


@router.post("/deploy-live", response_model=DeployLiveResponse)
async def deploy_live(
    body: DeployLiveRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
):
    """
    Kick off the Deploy Live Version flow for a paper bot.

    Steps:
      1. Duplicate source config → new trading_mode='virtuals' config (inactive)
      2. Create Virtuals agent via POST /agents → Privy wallet auto-provisioned
      3. Generate P-256 keypair, store signer key in Vault
      4. Insert arena_agents_v2 row (status='provisioning')
      5. Request signer URL from Virtuals → return to frontend for popup 2
    """
    jwt = _get_jwt(current_user.user_id)
    if not jwt:
        raise HTTPException(401, "Virtuals session missing or expired. Reconnect first.")

    source = await db_fetch_one(
        """
        SELECT user_id, config_data, config_type, config_name, trading_mode
        FROM configurations WHERE config_id = %s
        """,
        (body.source_config_id,),
    )
    if not source:
        raise HTTPException(404, "Source config not found")
    if str(source[0]) != current_user.user_id:
        raise HTTPException(403, "Config belongs to another user")
    if source[4] != "paper":
        raise HTTPException(
            400, f"Can only deploy from paper bots; source is trading_mode='{source[4]}'"
        )

    source_config_data = source[1] if isinstance(source[1], dict) else json.loads(source[1])
    source_type = source[2] or "scheduled_trading"
    source_name = source[3] or source_config_data.get("name") or "ggbot"

    agent_name = body.agent_name or source_name

    # ------------------------------------------------------------------
    # 1. Create Virtuals agent (one retry on name collision)
    # ------------------------------------------------------------------
    headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

    def _create_agent(name: str) -> requests.Response:
        return requests.post(
            f"{ACP_SERVER_URL}/agents",
            headers=headers,
            json={
                "name": name,
                "description": f"ggbots live bot: {name}",
                "role": "HYBRID",
            },
            timeout=30,
        )

    resp = _create_agent(agent_name)
    if resp.status_code in (400, 409):
        retry_name = f"{agent_name}-{uuid.uuid4().hex[:4]}"
        resp = _create_agent(retry_name)
        if resp.status_code in (200, 201):
            agent_name = retry_name
    if resp.status_code not in (200, 201):
        raise HTTPException(
            502, f"Virtuals agent create failed: {resp.status_code} {resp.text[:300]}"
        )

    payload = resp.json() or {}
    agent = payload.get("data") or payload
    virtuals_agent_id = str(agent.get("id") or "")
    wallet_address = agent.get("walletAddress")
    wallet_id = agent.get("walletId") or agent.get("privyWalletId")

    if not virtuals_agent_id or not wallet_address or not wallet_id:
        raise HTTPException(
            502,
            f"Agent response missing required fields (id/walletAddress/walletId): "
            f"{json.dumps(agent)[:300]}",
        )

    # ------------------------------------------------------------------
    # 2. Duplicate source config → trading_mode='virtuals'
    # ------------------------------------------------------------------
    new_config_id = str(uuid.uuid4())
    new_config_data = copy.deepcopy(source_config_data)
    new_config_data["trading_mode"] = "virtuals"
    new_config_data["name"] = agent_name

    await db_execute(
        """
        INSERT INTO configurations (
            config_id, user_id, config_type, config_name, config_data,
            trading_mode, initial_equity, state, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, 'virtuals', 0, 'inactive', NOW(), NOW())
        """,
        (
            new_config_id,
            current_user.user_id,
            source_type,
            agent_name,
            json.dumps(new_config_data),
        ),
    )

    # ------------------------------------------------------------------
    # 3. P-256 keypair + Vault storage
    # ------------------------------------------------------------------
    priv_b64, pub_b64 = _generate_p256_keypair()
    agent_record_id = str(uuid.uuid4())
    vault_name = f"arena_v2_signer_{agent_record_id}"
    signer_vault_id = await create_vault_secret(vault_name, priv_b64)
    if not signer_vault_id:
        raise HTTPException(500, "Failed to stash signer key in Vault")

    # ------------------------------------------------------------------
    # 4. Insert arena_agents_v2 row
    # ------------------------------------------------------------------
    await db_execute(
        """
        INSERT INTO arena_agents_v2 (
            id, user_id, config_id, virtuals_agent_id, agent_name,
            agent_wallet_address, wallet_id, signer_private_key_vault_id, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'provisioning')
        """,
        (
            agent_record_id,
            current_user.user_id,
            new_config_id,
            virtuals_agent_id,
            agent_name,
            wallet_address,
            wallet_id,
            signer_vault_id,
        ),
    )

    # ------------------------------------------------------------------
    # 5. Signer registration URL (popup 2)
    # ------------------------------------------------------------------
    signer_resp = requests.post(
        f"{ACP_SERVER_URL}/agents/{virtuals_agent_id}/signer",
        headers=headers,
        timeout=30,
    )
    if signer_resp.status_code not in (200, 201):
        raise HTTPException(
            502,
            f"Virtuals signer request failed: {signer_resp.status_code} "
            f"{signer_resp.text[:200]}",
        )
    sig_payload = signer_resp.json() or {}
    sig_data = sig_payload.get("data") or sig_payload
    sig_url = sig_data.get("url")
    sig_req_id = sig_data.get("requestId")
    if not sig_url or not sig_req_id:
        raise HTTPException(502, "Signer response missing fields")

    sep = "&" if "?" in sig_url else "?"
    final_signer_url = f"{sig_url}{sep}publicKey={pub_b64}"

    # Track this deploy flow in Redis for the /deploy-poll follow-up.
    _redis.setex(
        _deploy_key(sig_req_id),
        DEPLOY_STATE_TTL_SEC,
        json.dumps(
            {
                "agent_record_id": agent_record_id,
                "virtuals_agent_id": virtuals_agent_id,
                "new_config_id": new_config_id,
                "user_id": current_user.user_id,
                "agent_wallet_address": wallet_address,
                "agent_name": agent_name,
                "signer_vault_id": signer_vault_id,
                "signer_approved": False,
                "unified_done": False,
                "authorized_done": False,
            }
        ),
    )

    logger.info(
        f"arena_v2 deploy-live: user={current_user.user_id[:8]} "
        f"config={new_config_id[:8]} agent={virtuals_agent_id} wallet={wallet_address[:10]}"
    )

    return DeployLiveResponse(
        new_config_id=new_config_id,
        agent_record_id=agent_record_id,
        virtuals_agent_id=virtuals_agent_id,
        agent_wallet_address=wallet_address,
        signerUrl=final_signer_url,
        signerRequestId=sig_req_id,
    )


@router.get("/deploy-poll")
async def deploy_poll(
    requestId: str = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Drive the post-signer-approval headless setup.

    Transitions tracked in Redis (arena_v2:deploy:<signerRequestId>):
        signer_approved  → unified_done → authorized_done → active

    Each call checks Virtuals signer status; once approved, runs the HL
    setup actions in order via acp-node. Fully idempotent — a second call
    after completion returns status='completed' immediately.
    """
    raw = _redis.get(_deploy_key(requestId))
    if not raw:
        raise HTTPException(404, "Deploy request not found or expired")
    state = json.loads(raw)
    if state["user_id"] != current_user.user_id:
        raise HTTPException(403, "Deploy request not owned by this session")

    # ------------------------------------------------------------------
    # 1. Check Virtuals signer approval status (unless already approved)
    # ------------------------------------------------------------------
    if not state.get("signer_approved"):
        jwt = _get_jwt(current_user.user_id)
        if not jwt:
            return {"status": "error", "stage": "signer", "reason": "Virtuals JWT expired"}

        headers = {"Authorization": f"Bearer {jwt}"}
        try:
            sig_resp = requests.get(
                f"{ACP_SERVER_URL}/agents/{state['virtuals_agent_id']}/signer",
                params={"requestId": requestId},
                headers=headers,
                timeout=5,
            )
        except Exception as e:
            return {"status": "pending", "stage": "signer", "error": str(e)}

        sig_status = "pending"
        if sig_resp.status_code == 200:
            sig_status = (
                ((sig_resp.json() or {}).get("data") or {}).get("status") or "pending"
            )
        if sig_status != "completed":
            return {"status": "pending", "stage": "signer", "signerStatus": sig_status}

        state["signer_approved"] = True
        _redis.setex(_deploy_key(requestId), DEPLOY_STATE_TTL_SEC, json.dumps(state))
        logger.info(
            f"arena_v2 deploy-poll: signer approved agent={state['virtuals_agent_id']}"
        )

    # ------------------------------------------------------------------
    # 2. Fetch signer private key from Vault (needed for acp-node calls)
    # ------------------------------------------------------------------
    signer_priv = await get_vault_secret(state["signer_vault_id"])
    if not signer_priv:
        return {"status": "error", "stage": "vault", "reason": "signer key missing from vault"}

    sidecar_payload_base = {
        "agentWalletAddress": state["agent_wallet_address"],
        "agentWalletId": state["virtuals_agent_id"],    # Virtuals agent ID used as walletId during signing
        "signerPrivateKey": signer_priv,
    }

    # Privy wallet ID might actually be separate from agent ID. In the agent
    # response we captured both — the deployment row stores the Privy walletId.
    # Pull it fresh to be safe.
    row = await db_fetch_one(
        "SELECT wallet_id FROM arena_agents_v2 WHERE id = %s",
        (state["agent_record_id"],),
    )
    if row and row[0]:
        sidecar_payload_base["agentWalletId"] = row[0]

    # ------------------------------------------------------------------
    # 3. Activate HL unified account (EIP-712 userSetAbstraction)
    # ------------------------------------------------------------------
    if not state.get("unified_done"):
        unified = await acp_node_post(
            "/setup-hl-unified-account", sidecar_payload_base, timeout_seconds=60
        )
        if unified.get("_httpStatus") != 200 or not unified.get("success"):
            logger.warning(f"arena_v2 deploy-poll: unified-account failed {unified}")
            return {
                "status": "error",
                "stage": "unified_account",
                "detail": unified,
            }
        state["unified_done"] = True
        _redis.setex(_deploy_key(requestId), DEPLOY_STATE_TTL_SEC, json.dumps(state))
        logger.info(
            f"arena_v2 deploy-poll: HL unified account activated for "
            f"agent={state['virtuals_agent_id']}"
        )

    # ------------------------------------------------------------------
    # 4. Authorize HL API wallet (EIP-712 approveAgent) → store key
    # ------------------------------------------------------------------
    if not state.get("authorized_done"):
        payload = {**sidecar_payload_base, "agentName": state["agent_name"][:40]}
        authz = await acp_node_post(
            "/authorize-hl-api-wallet", payload, timeout_seconds=60
        )
        if authz.get("_httpStatus") != 200 or not authz.get("success"):
            logger.warning(f"arena_v2 deploy-poll: authorize-api-wallet failed {authz}")
            return {
                "status": "error",
                "stage": "authorize_api_wallet",
                "detail": authz,
            }

        api_wallet_key = authz.get("apiWalletPrivateKey")
        if not api_wallet_key:
            return {
                "status": "error",
                "stage": "authorize_api_wallet",
                "reason": "sidecar returned success but no apiWalletPrivateKey",
            }

        hl_vault_id = await store_arena_v2_hl_api_wallet(
            state["agent_record_id"], api_wallet_key
        )
        if not hl_vault_id:
            return {
                "status": "error",
                "stage": "authorize_api_wallet",
                "reason": "vault write failed for HL API wallet key",
            }

        state["authorized_done"] = True
        state["api_wallet_address"] = authz.get("apiWalletAddress")
        _redis.setex(_deploy_key(requestId), DEPLOY_STATE_TTL_SEC, json.dumps(state))
        logger.info(
            f"arena_v2 deploy-poll: HL API wallet authorized for "
            f"agent={state['virtuals_agent_id']}"
        )

    # ------------------------------------------------------------------
    # 5. Flip arena_agents_v2 to active
    # ------------------------------------------------------------------
    await db_execute(
        """
        UPDATE arena_agents_v2
        SET status = 'active', updated_at = NOW()
        WHERE id = %s AND status = 'provisioning'
        """,
        (state["agent_record_id"],),
    )

    return {
        "status": "completed",
        "config_id": state["new_config_id"],
        "agent_wallet_address": state["agent_wallet_address"],
        "api_wallet_address": state.get("api_wallet_address"),
        "agent_name": state["agent_name"],
    }


# ============================================================================
# Runtime — status / check-deposit / withdraw
# ============================================================================

@router.get("/status")
async def arena_v2_status(
    config_id: str = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Current state of a virtuals bot — used by DeployLiveModal + ActivationBar.

    Returns agent details, Arbitrum wallet balance, and HL account/positions
    via hyperliquid Info API. Safe to poll.
    """
    if not await _verify_ownership(config_id, current_user.user_id):
        raise HTTPException(404, "Bot not found")

    creds = await get_arena_v2_credential(config_id)
    if not creds:
        return {"status": "not_deployed"}

    wallet = creds["agent_wallet_address"]

    arbitrum_balance = await get_usdc_balance(wallet)

    # HL account state (reuse the info-only path to avoid touching the exchange).
    hl_account_value = None
    hl_withdrawable = None
    hl_positions: list = []
    try:
        from hyperliquid.info import Info
        from hyperliquid.utils import constants as hl_constants

        info = Info(hl_constants.MAINNET_API_URL, skip_ws=True)
        user_state = info.user_state(wallet) or {}
        margin = user_state.get("marginSummary", {}) or {}
        hl_account_value = float(margin.get("accountValue", 0) or 0)
        hl_withdrawable = float(user_state.get("withdrawable", 0) or 0)
        for wrapper in user_state.get("assetPositions", []) or []:
            pos = wrapper.get("position", {}) or {}
            szi = float(pos.get("szi", 0) or 0)
            if szi == 0:
                continue
            hl_positions.append(
                {
                    "coin": pos.get("coin"),
                    "size": szi,
                    "entry_price": float(pos.get("entryPx", 0) or 0),
                    "unrealized_pnl": float(pos.get("unrealizedPnl", 0) or 0),
                    "margin_used": float(pos.get("marginUsed", 0) or 0),
                }
            )
    except Exception as e:
        logger.warning(f"arena_v2 status HL info failed for {wallet}: {e}")

    is_authorized = bool(creds.get("hl_api_wallet_key"))
    is_leaderboard_joined = bool(creds.get("dgclaw_api_key"))

    return {
        "status": "active" if is_authorized else "provisioning",
        "agent_name": creds["agent_name"],
        "agent_wallet_address": wallet,
        "virtuals_agent_id": creds["virtuals_agent_id"],
        "arbitrum_usdc_balance": arbitrum_balance,
        "hl_account_value": hl_account_value,
        "hl_withdrawable": hl_withdrawable,
        "hl_positions": hl_positions,
        "hl_api_wallet_authorized": is_authorized,
        "leaderboard_joined": is_leaderboard_joined,
    }


class CheckDepositRequest(BaseModel):
    config_id: str


@router.post("/check-deposit")
async def check_deposit(
    body: CheckDepositRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Check Arbitrum USDC balance, bridge to HL, and (first time) join the
    DGClaw leaderboard. Keeps ACP_FEE_RESERVE on Arbitrum for ACP jobs.
    """
    if not await _verify_ownership(body.config_id, current_user.user_id):
        raise HTTPException(404, "Bot not found")

    creds = await get_arena_v2_credential(body.config_id)
    if not creds:
        raise HTTPException(404, "No virtuals agent deployed for this config")
    if not creds.get("hl_api_wallet_key"):
        raise HTTPException(400, "HL API wallet not yet authorized")

    wallet = creds["agent_wallet_address"]
    balance = await get_usdc_balance(wallet)
    if balance is None:
        return {
            "status": "rpc_error",
            "message": "Could not read Arbitrum USDC balance — try again shortly.",
        }
    if balance < HL_BRIDGE_MIN_USDC:
        return {
            "status": "insufficient",
            "balance": balance,
            "minimum": HL_BRIDGE_MIN_USDC,
            "message": (
                f"Balance ${balance:.2f} is below the ${HL_BRIDGE_MIN_USDC:.0f} "
                f"HL bridge minimum. Send USDC on Arbitrum to {wallet}."
            ),
        }

    sidecar_base = {
        "agentWalletAddress": wallet,
        "agentWalletId": creds["wallet_id"],
        "signerPrivateKey": creds["signer_private_key"],
    }

    # Reserve ACP_FEE_RESERVE for join-leaderboard and future ACP jobs
    reserve = ACP_FEE_RESERVE if balance > HL_BRIDGE_MIN_USDC + ACP_FEE_RESERVE else 0.1
    bridge_amount = round(balance - reserve, 2)
    bridge_resp = await acp_node_post(
        "/bridge-usdc-to-hl",
        {**sidecar_base, "amountUsdc": f"{bridge_amount:.2f}"},
        timeout_seconds=120,
    )
    if bridge_resp.get("_httpStatus") != 200 or not bridge_resp.get("success"):
        logger.warning(f"arena_v2 check-deposit: bridge failed {bridge_resp}")
        return {
            "status": "bridge_failed",
            "balance": balance,
            "detail": bridge_resp,
        }

    tx_hash = bridge_resp.get("txHash")
    logger.info(
        f"arena_v2 check-deposit: bridged ${bridge_amount:.2f} agent={wallet[:10]} tx={tx_hash}"
    )

    # First-time leaderboard registration (only if not yet joined).
    # Deliberately fire-and-forget so a slow ACP job doesn't block the user —
    # the status endpoint will surface leaderboard_joined once complete.
    leaderboard_result: Optional[Dict[str, Any]] = None
    if not creds.get("dgclaw_api_key"):
        leaderboard_resp = await acp_node_post(
            "/join-leaderboard", sidecar_base, timeout_seconds=180
        )
        if leaderboard_resp.get("_httpStatus") == 200 and leaderboard_resp.get("success"):
            api_key = leaderboard_resp.get("dgclawApiKey")
            if api_key:
                await store_arena_v2_dgclaw_key(creds["agent_record_id"], api_key)
                logger.info(
                    f"arena_v2 check-deposit: leaderboard joined agent={creds['virtuals_agent_id']}"
                )
            leaderboard_result = {"joined": bool(api_key)}
        else:
            leaderboard_result = {"joined": False, "detail": leaderboard_resp}
            logger.warning(f"arena_v2 check-deposit: leaderboard join failed {leaderboard_resp}")

    return {
        "status": "bridged",
        "balance_before": balance,
        "bridge_amount": bridge_amount,
        "reserve_kept": reserve,
        "tx_hash": tx_hash,
        "leaderboard": leaderboard_result,
    }


class WithdrawRequest(BaseModel):
    config_id: str
    amount: float
    destination: Optional[str] = None


@router.post("/withdraw")
async def withdraw(
    body: WithdrawRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """Withdraw USDC from HL → Arbitrum (agent wallet or user-provided dest)."""
    if not await _verify_ownership(body.config_id, current_user.user_id):
        raise HTTPException(404, "Bot not found")

    creds = await get_arena_v2_credential(body.config_id)
    if not creds:
        raise HTTPException(404, "No virtuals agent deployed for this config")

    if body.amount < 2:
        raise HTTPException(400, "Minimum withdrawal is $2")

    payload = {
        "agentWalletAddress": creds["agent_wallet_address"],
        "agentWalletId": creds["wallet_id"],
        "signerPrivateKey": creds["signer_private_key"],
        "amountUsdc": f"{body.amount:.2f}",
    }
    if body.destination:
        payload["destination"] = body.destination

    result = await acp_node_post("/withdraw-from-hl", payload, timeout_seconds=60)
    if result.get("_httpStatus") != 200 or not result.get("success"):
        logger.warning(f"arena_v2 withdraw failed: {result}")
        return {"status": "error", "detail": result}

    logger.info(
        f"arena_v2 withdraw: ${body.amount} agent={creds['agent_wallet_address'][:10]} "
        f"dest={body.destination or 'self'}"
    )
    return {
        "status": "success",
        "amount": body.amount,
        "destination": body.destination or creds["agent_wallet_address"],
    }


# ============================================================================
# Leaderboard — read-only passthrough so the modal can show rankings
# ============================================================================

@router.get("/leaderboard")
async def leaderboard() -> Dict[str, Any]:
    """Public leaderboard pass-through — enriched with ggbots names."""
    import aiohttp

    url = "https://dgclaw-app-production.up.railway.app/leaderboard"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {"entries": [], "error": f"Leaderboard unavailable (HTTP {resp.status})"}
                data = await resp.json()
    except Exception as e:
        logger.error(f"arena_v2 leaderboard fetch failed: {e}")
        return {"entries": [], "error": "Leaderboard unavailable"}

    entries = data.get("data", data) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        return {"entries": []}

    # Enrich with v2 agent names
    wallets = [
        e.get("walletAddress", e.get("wallet", ""))
        for e in entries
        if isinstance(e, dict)
    ]
    if wallets:
        placeholders = ",".join(["%s"] * len(wallets))
        rows = await db_fetch_all(
            f"""
            SELECT agent_wallet_address, agent_name
            FROM arena_agents_v2 WHERE agent_wallet_address IN ({placeholders})
            """,
            tuple(wallets),
        )
        name_map = {r[0]: r[1] for r in rows} if rows else {}
        for entry in entries:
            w = entry.get("walletAddress", entry.get("wallet", ""))
            if w in name_map:
                entry["ggbots_agent_name"] = name_map[w]

    return {"entries": entries}
