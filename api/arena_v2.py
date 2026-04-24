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
import json
import os
import time
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
    store_arena_v2_forum_thread_id,
    store_arena_v2_hl_api_wallet,
)
from core.common.db import db_execute, db_fetch_all, db_fetch_one
from core.common.logger import logger
from core.services.acp_node_client import acp_node_post
from core.services.base_rpc import get_usdc_balance as get_base_usdc_balance
from core.services.config_service import config_service

router = APIRouter(prefix="/api/v2/arena", tags=["arena-v2"])

ACP_SERVER_URL = "https://api.acp.virtuals.io"
JWT_TTL_SEC = 25 * 60
REQUEST_ID_TTL_SEC = 10 * 60
DEPLOY_STATE_TTL_SEC = 30 * 60

DEPOSIT_MIN_USDC = 10.0      # User-facing minimum. DGClaw protocol minimum is $6; we enforce $10 for headroom.
ACP_FEE_RESERVE = 1.0        # USDC kept on-chain (Base) for join-leaderboard / future ACP fees

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

def _deposit_progress_key(config_id: str) -> str:
    """Redis key for async deposit stage tracking."""
    return f"arena_v2:deposit_progress:{config_id}"


# ============================================================================
# Deposit stages — string constants shared with frontend
# ============================================================================
# Frontend reads these via /status.deposit_progress.stage to render the
# progress UI. Order in the UI progression: starting → depositing → hl_setup
# → leaderboard → complete (or failed at any stage).
STAGE_STARTING = "starting"
STAGE_DEPOSITING = "depositing"               # ACP perp_deposit job in flight
STAGE_HL_SETUP = "hl_setup"                   # userSetAbstraction + approveAgent
STAGE_LEADERBOARD = "leaderboard"             # join_leaderboard ACP job
STAGE_COMPLETE = "complete"
STAGE_FAILED = "failed"

DEPOSIT_PROGRESS_TTL_SEC = 2 * 60 * 60        # 2h — retry window


def _write_progress(config_id: str, stage: str, message: str, **extra: Any) -> None:
    """Persist deposit stage/status to Redis so /status can surface it."""
    payload = {
        "stage": stage,
        "message": message,
        "updated_at": int(time.time()),
        **extra,
    }
    _redis.setex(_deposit_progress_key(config_id), DEPOSIT_PROGRESS_TTL_SEC, json.dumps(payload))


def _read_progress(config_id: str) -> Optional[Dict[str, Any]]:
    raw = _redis.get(_deposit_progress_key(config_id))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


# ============================================================================
# Helpers
# ============================================================================

def _get_jwt(user_id: str) -> Optional[str]:
    return _redis.get(_jwt_key(user_id))


def _generate_p256_keypair() -> tuple[str, str]:
    """
    P-256 keypair for Privy signer registration.
    Returns (base64-PKCS8-DER-private, base64-SPKI-DER-public).

    Both must be base64-wrapped DER bytes — PEM-wrapping the private key and
    then base64'ing the whole PEM text was silently rejected by Privy with
    "Invalid wallet authorization private key". Privy's docstring is explicit:
    "base64-encoded PKCS8-formatted private key, with no PEM headers."
    See @privy-io/node/src/lib/cryptography.ts::importPKCS8PrivateKey.
    """
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    priv_der = priv.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_spki_der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return (
        base64.b64encode(priv_der).decode("ascii"),
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
    """Thin wrapper so traceback-logging can wrap the whole flow."""
    logger.info(
        f"arena_v2 deploy-live ENTER: user={current_user.user_id[:8]} "
        f"source={body.source_config_id[:8]} name={body.agent_name!r}"
    )
    try:
        return await _deploy_live_impl(body, current_user)
    except HTTPException:
        raise
    except Exception:
        import traceback as _tb
        logger.error(
            f"arena_v2 deploy-live unhandled exception:\n{_tb.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="deploy-live failed (see ggbot.log for traceback)",
        )


async def _deploy_live_impl(
    body: DeployLiveRequest,
    current_user: AuthenticatedUser,
) -> DeployLiveResponse:
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

    # Load source config through config_service — the same path Duplicate uses,
    # so we get a validated BotConfigV2 object with all fields normalized.
    source_cfg = await config_service.get_config(body.source_config_id, current_user.user_id)
    if not source_cfg:
        raise HTTPException(404, "Source config not found (or not owned by you)")
    if source_cfg.trading_mode != "paper":
        raise HTTPException(
            400,
            f"Can only deploy from paper bots; source is trading_mode='{source_cfg.trading_mode}'",
        )

    agent_name = body.agent_name or f"{source_cfg.config_name or 'ggbot'} (live)"
    logger.info(f"arena_v2 deploy-live STEP1: source loaded, agent_name={agent_name!r}")

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

    logger.info("arena_v2 deploy-live STEP2: calling Virtuals POST /agents")
    resp = _create_agent(agent_name)
    logger.info(
        f"arena_v2 deploy-live STEP2 done: status={resp.status_code} body={resp.text[:300]}"
    )

    # Parse Virtuals' error shape: {"message": str | [str], "statusCode": int}
    def _virtuals_error_detail(r: requests.Response) -> str:
        try:
            j = r.json() or {}
            msg = j.get("message")
            if isinstance(msg, list):
                return "; ".join(str(x) for x in msg)
            return str(msg or r.text[:200])
        except Exception:
            return r.text[:200]

    # Retry only if the error looks like a name collision — NOT for agent-limit,
    # role rejection, or any other 400 where changing the name won't help.
    if resp.status_code == 409 or (
        resp.status_code == 400
        and "name" in _virtuals_error_detail(resp).lower()
        and ("already" in _virtuals_error_detail(resp).lower()
             or "exists" in _virtuals_error_detail(resp).lower()
             or "taken" in _virtuals_error_detail(resp).lower())
    ):
        retry_name = f"{agent_name}-{uuid.uuid4().hex[:4]}"
        logger.info(f"arena_v2 deploy-live STEP2 retry with suffix: {retry_name}")
        resp = _create_agent(retry_name)
        if resp.status_code in (200, 201):
            agent_name = retry_name

    if resp.status_code not in (200, 201):
        detail = _virtuals_error_detail(resp)
        # Surface the real Virtuals error back to the UI so the user knows
        # exactly what to fix (e.g. "Agent limit of 10 reached" → delete some
        # agents on app.virtuals.io).
        raise HTTPException(
            status_code=400 if resp.status_code < 500 else 502,
            detail=f"Virtuals rejected agent create: {detail}",
        )

    payload = resp.json() or {}
    agent = payload.get("data") or payload
    virtuals_agent_id = str(agent.get("id") or "")
    wallet_address = agent.get("walletAddress")

    # Privy wallet ID lives inside walletProviders[] — one entry per chain.
    # We want the EVM Privy wallet; Solana is irrelevant for HL trading.
    wallet_id: Optional[str] = None
    for provider_entry in agent.get("walletProviders") or []:
        if (
            provider_entry.get("provider") == "PRIVY"
            and provider_entry.get("chainType") == "EVM"
        ):
            wallet_id = (provider_entry.get("metadata") or {}).get("walletId")
            if wallet_id:
                break

    if not virtuals_agent_id or not wallet_address or not wallet_id:
        raise HTTPException(
            502,
            f"Agent response missing required fields "
            f"(id={bool(virtuals_agent_id)}, walletAddress={bool(wallet_address)}, "
            f"evmPrivyWalletId={bool(wallet_id)}): {json.dumps(agent)[:300]}",
        )

    # ------------------------------------------------------------------
    # 2. Duplicate source config → trading_mode='virtuals' via the canonical
    #    config_service.create_config() path (same as Duplicate button).
    #    This runs validation + normalization via BotConfigV2.to_jsonb().
    # ------------------------------------------------------------------
    duplicated_config_data = {
        "config_type": source_cfg.config_type,
        "schema_version": source_cfg.schema_version,
        "selected_pair": source_cfg.selected_pair,
        "extraction": source_cfg.extraction,
        "decision": source_cfg.decision,
        "trading": source_cfg.trading,
        "llm_config": source_cfg.llm_config,
        "telegram_integration": source_cfg.telegram_integration or {},
        "agent_strategy": source_cfg.agent_strategy,
    }

    logger.info("arena_v2 deploy-live STEP3: calling config_service.create_config")
    new_cfg = await config_service.create_config(
        user_id=current_user.user_id,
        config_name=agent_name,
        config_data=duplicated_config_data,
        trading_mode="virtuals",
    )
    if not new_cfg:
        raise HTTPException(
            500, "Failed to duplicate source config (validation rejected or DB write failed)"
        )
    new_config_id = new_cfg.config_id
    logger.info(f"arena_v2 deploy-live STEP3 done: new_config_id={new_config_id[:8]}")

    # ------------------------------------------------------------------
    # 3. P-256 keypair + Vault storage
    # ------------------------------------------------------------------
    logger.info("arena_v2 deploy-live STEP4: generating P-256 keypair")
    priv_b64, pub_b64 = _generate_p256_keypair()
    agent_record_id = str(uuid.uuid4())
    vault_name = f"arena_v2_signer_{agent_record_id}"
    logger.info("arena_v2 deploy-live STEP4: create_vault_secret")
    signer_vault_id = await create_vault_secret(vault_name, priv_b64)
    if not signer_vault_id:
        raise HTTPException(500, "Failed to stash signer key in Vault")
    logger.info(f"arena_v2 deploy-live STEP4 done: signer_vault_id={signer_vault_id[:8]}")

    # ------------------------------------------------------------------
    # 4. Insert arena_agents_v2 row
    # ------------------------------------------------------------------
    logger.info("arena_v2 deploy-live STEP5: INSERT arena_agents_v2")
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
    logger.info("arena_v2 deploy-live STEP5 done")

    # ------------------------------------------------------------------
    # 5. Signer registration URL (popup 2)
    # ------------------------------------------------------------------
    logger.info("arena_v2 deploy-live STEP6: POST /agents/{id}/signer")
    signer_resp = requests.post(
        f"{ACP_SERVER_URL}/agents/{virtuals_agent_id}/signer",
        headers=headers,
        timeout=30,
    )
    logger.info(f"arena_v2 deploy-live STEP6 done: status={signer_resp.status_code}")
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
    Wait for the user to approve the Privy signer in popup 2.

    Once Virtuals reports signer.status=completed, the modal advances to the
    Funding state. We deliberately do NOT call HL setup actions here —
    Hyperliquid rejects userSetAbstraction and approveAgent on a zero-balance
    wallet ("Must deposit before performing actions"). Those run later inside
    /check-deposit, post-bridge, when HL can see the account.
    """
    raw = _redis.get(_deploy_key(requestId))
    if not raw:
        raise HTTPException(404, "Deploy request not found or expired")
    state = json.loads(raw)
    if state["user_id"] != current_user.user_id:
        raise HTTPException(403, "Deploy request not owned by this session")

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

    # Signer approved. The agent is provisioned — now it's the user's turn to
    # fund the Arbitrum wallet. Return completed so DeployLiveModal advances
    # to the Funding stage; HL setup + API-wallet authorization happen inside
    # /check-deposit once bridging has credited the HL unified account.
    return {
        "status": "completed",
        "config_id": state["new_config_id"],
        "agent_wallet_address": state["agent_wallet_address"],
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

    Returns agent details, Base wallet USDC balance, and HL account/positions
    via hyperliquid Info API. Safe to poll.
    """
    if not await _verify_ownership(config_id, current_user.user_id):
        raise HTTPException(404, "Bot not found")

    creds = await get_arena_v2_credential(config_id)
    if not creds:
        return {"status": "not_deployed"}

    wallet = creds["agent_wallet_address"]

    base_balance = await get_base_usdc_balance(wallet)

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

    # Include DGClaw-side pooled balance if the agent has joined the leaderboard
    # (hlBalance lives on DGClaw's backend, not on HL directly — DGClaw pools funds).
    dgclaw_balance: Optional[float] = None
    if is_leaderboard_joined:
        try:
            dgclaw_resp = requests.get(
                f"https://dgclaw-app-production.up.railway.app/users/{wallet}/account",
                timeout=5,
            )
            if dgclaw_resp.status_code == 200:
                dgclaw_data = (dgclaw_resp.json() or {}).get("data", {}) or {}
                dgclaw_balance = float(dgclaw_data.get("hlBalance", 0) or 0)
        except Exception as e:
            logger.debug(f"arena_v2 status: DGClaw balance fetch failed for {wallet[:10]}: {e}")

    return {
        "status": "active" if is_authorized else "provisioning",
        "agent_name": creds["agent_name"],
        "agent_wallet_address": wallet,
        "virtuals_agent_id": creds["virtuals_agent_id"],
        "base_usdc_balance": base_balance,
        "hl_account_value": hl_account_value,
        "hl_withdrawable": hl_withdrawable,
        "hl_positions": hl_positions,
        "hl_api_wallet_authorized": is_authorized,
        "leaderboard_joined": is_leaderboard_joined,
        "dgclaw_balance": dgclaw_balance,
        "deposit_progress": _read_progress(config_id),
    }


class CheckDepositRequest(BaseModel):
    config_id: str
    amount: float              # USDC to deposit; must be >= DEPOSIT_MIN_USDC


def _extract_forum_thread_id(deliverable: Any) -> Optional[str]:
    """
    DGClaw's deliverable schemas aren't documented — check several plausible
    field names + nested locations. Returns None if nothing matches.
    """
    if not isinstance(deliverable, dict):
        return None
    for key in ("forumThreadId", "forum_thread_id", "threadId", "thread_id"):
        v = deliverable.get(key)
        if v:
            return str(v)
    # Some providers nest under e.g. "metadata" or "data"
    for outer in ("metadata", "data", "details"):
        inner = deliverable.get(outer)
        if isinstance(inner, dict):
            nested = _extract_forum_thread_id(inner)
            if nested:
                return nested
    return None


async def _get_dgclaw_hl_balance(wallet: str) -> Optional[float]:
    """Query DGClaw's Railway backend for the agent's pooled hlBalance.
    Returns None on error; 0 if account doesn't exist yet."""
    try:
        import asyncio as _a
        def _sync() -> Optional[float]:
            resp = requests.get(
                f"https://dgclaw-app-production.up.railway.app/users/{wallet}/account",
                timeout=5,
            )
            if resp.status_code == 404:
                return 0.0
            if resp.status_code != 200:
                return None
            data = (resp.json() or {}).get("data", {}) or {}
            return float(data.get("hlBalance", 0) or 0)
        return await _a.to_thread(_sync)
    except Exception as e:
        logger.debug(f"arena_v2 _get_dgclaw_hl_balance failed for {wallet[:10]}: {e}")
        return None


async def _run_deposit_flow(
    config_id: str,
    agent_record_id: str,
    creds: Dict[str, Any],
    amount: float,
) -> None:
    """
    Background task: perp_deposit → HL setup → leaderboard, with idempotent
    skip-if-already-done logic at every step. Writes progress to Redis so the
    frontend can poll /status.deposit_progress for stage + message.

    Never raises — any exception is captured into a STAGE_FAILED progress row.
    """
    wallet = creds["agent_wallet_address"]
    sidecar_base = {
        "agentWalletAddress": wallet,
        "agentWalletId": creds["wallet_id"],
        "signerPrivateKey": creds["signer_private_key"],
    }

    try:
        # ---- 1. perp_deposit (skip if DGClaw already has this agent's funds) ----
        existing_dgclaw = await _get_dgclaw_hl_balance(wallet)
        if existing_dgclaw and existing_dgclaw > 0:
            logger.info(
                f"arena_v2 deposit_flow: skipping perp_deposit — DGClaw already shows "
                f"${existing_dgclaw:.2f} for {wallet[:10]}"
            )
        else:
            _write_progress(
                config_id, STAGE_DEPOSITING,
                f"Depositing ${amount:.2f} via DGClaw (bridge Base → Arbitrum → Hyperliquid, ~2–5 min)…",
                amount=amount,
            )
            logger.info(
                f"arena_v2 deposit_flow: firing perp_deposit ${amount:.2f} "
                f"agent={creds['virtuals_agent_id']}"
            )
            deposit_resp = await acp_node_post(
                "/deposit",
                {**sidecar_base, "amountUsdc": f"{amount:.2f}"},
                timeout_seconds=1850,
            )
            if deposit_resp.get("_httpStatus") != 200 or not deposit_resp.get("success"):
                _write_progress(
                    config_id, STAGE_FAILED,
                    "Deposit failed during DGClaw bridge. Your USDC is still on Base — you can retry.",
                    stage_failed=STAGE_DEPOSITING,
                    detail=deposit_resp,
                )
                return

            # Best-effort forum thread id extraction from deposit deliverable
            thread_id = _extract_forum_thread_id(deposit_resp.get("deliverable"))
            if thread_id:
                await store_arena_v2_forum_thread_id(agent_record_id, thread_id)

        # ---- 2. HL setup (skip if HL API wallet key already in vault) ----
        if creds.get("hl_api_wallet_key"):
            logger.info(
                f"arena_v2 deposit_flow: skipping HL setup — api_wallet_key already stored "
                f"for {agent_record_id[:8]}"
            )
        else:
            _write_progress(
                config_id, STAGE_HL_SETUP,
                "Activating your Hyperliquid account and authorizing the trading API wallet…",
            )
            # Short pause for HL to index the deposit (if we just did one)
            import asyncio as _a
            await _a.sleep(10)

            unified = await acp_node_post("/setup-hl-unified-account", sidecar_base, timeout_seconds=60)
            if unified.get("_httpStatus") != 200 or not unified.get("success"):
                _write_progress(
                    config_id, STAGE_FAILED,
                    "Hyperliquid account activation failed. The deposit succeeded — you can retry to finish setup.",
                    stage_failed=STAGE_HL_SETUP, sub_stage="unified_account",
                    detail=unified, hint="HL may not have indexed the deposit yet — wait 30s and retry.",
                )
                return

            hl_agent_name = (creds["agent_name"] or "ggbots")[:16]
            authz = await acp_node_post(
                "/authorize-hl-api-wallet",
                {**sidecar_base, "agentName": hl_agent_name},
                timeout_seconds=60,
            )
            if authz.get("_httpStatus") != 200 or not authz.get("success"):
                _write_progress(
                    config_id, STAGE_FAILED,
                    "Hyperliquid API wallet authorization failed. Retry to finish setup.",
                    stage_failed=STAGE_HL_SETUP, sub_stage="authorize_api_wallet",
                    detail=authz,
                )
                return

            api_wallet_key = authz.get("apiWalletPrivateKey")
            if not api_wallet_key:
                _write_progress(
                    config_id, STAGE_FAILED,
                    "Setup partially complete — missing API wallet key. Contact support.",
                    stage_failed=STAGE_HL_SETUP, sub_stage="authorize_api_wallet",
                )
                return

            hl_vault_id = await store_arena_v2_hl_api_wallet(agent_record_id, api_wallet_key)
            if not hl_vault_id:
                _write_progress(
                    config_id, STAGE_FAILED,
                    "Setup partially complete — key storage failed. Retry to complete.",
                    stage_failed=STAGE_HL_SETUP, sub_stage="vault_write",
                )
                return

            await db_execute(
                "UPDATE arena_agents_v2 SET status='active', updated_at=NOW() WHERE id = %s AND status='provisioning'",
                (agent_record_id,),
            )

        # ---- 3. leaderboard join (skip if dgclaw_api_key already in vault) ----
        if creds.get("dgclaw_api_key"):
            logger.info(
                f"arena_v2 deposit_flow: skipping leaderboard — already joined "
                f"for {agent_record_id[:8]}"
            )
        else:
            _write_progress(
                config_id, STAGE_LEADERBOARD,
                "Registering your agent on the DegenClaw leaderboard…",
            )
            leaderboard_resp = await acp_node_post(
                "/join-leaderboard", sidecar_base, timeout_seconds=620,
            )
            if leaderboard_resp.get("_httpStatus") == 200 and leaderboard_resp.get("success"):
                api_key = leaderboard_resp.get("dgclawApiKey")
                if api_key:
                    await store_arena_v2_dgclaw_key(agent_record_id, api_key)
                # Extract forum thread id from leaderboard deliverable as fallback
                if not creds.get("dgclaw_forum_thread_id"):
                    fallback_thread = (
                        leaderboard_resp.get("forumThreadId")
                        or _extract_forum_thread_id(leaderboard_resp.get("deliverable"))
                    )
                    if fallback_thread:
                        await store_arena_v2_forum_thread_id(agent_record_id, fallback_thread)
            else:
                # Leaderboard is nice-to-have — log but don't fail the whole flow.
                logger.warning(
                    f"arena_v2 deposit_flow: leaderboard join failed (non-fatal) {leaderboard_resp}"
                )

        _write_progress(
            config_id, STAGE_COMPLETE,
            "Your bot is live and trading on Hyperliquid. You're on the DegenClaw leaderboard.",
        )
        logger.info(f"arena_v2 deposit_flow: COMPLETE for {agent_record_id[:8]}")

    except Exception as e:
        logger.exception(f"arena_v2 deposit_flow: unhandled exception for {agent_record_id[:8]}")
        _write_progress(
            config_id, STAGE_FAILED,
            f"Unexpected error: {type(e).__name__}. Retry to continue.",
            error=str(e),
        )


@router.post("/check-deposit")
async def check_deposit(
    body: CheckDepositRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Kick off the deposit-and-setup flow asynchronously. Fast validation runs
    synchronously (amount, balance, idempotency detection). The long-running
    pieces (perp_deposit ACP job ~2-5min, HL setup, leaderboard) run in a
    background task that writes progress to Redis. Frontend polls /status to
    read `deposit_progress.stage` and render appropriate UI.

    Safely idempotent:
      - Skips perp_deposit if DGClaw already has funds for this agent
      - Skips HL setup if api_wallet_key is already stored
      - Skips leaderboard if dgclaw_api_key is already stored
      - Rejects with `already_in_progress` if another flow is mid-way
    """
    if not await _verify_ownership(body.config_id, current_user.user_id):
        raise HTTPException(404, "Bot not found")

    creds = await get_arena_v2_credential(body.config_id)
    if not creds:
        raise HTTPException(404, "No virtuals agent deployed for this config")

    # -----------------------------------------------------------------
    # Check if a flow is already in progress — prevent double-click / retry race.
    # Allow retry only if previous progress is STAGE_COMPLETE or STAGE_FAILED.
    # -----------------------------------------------------------------
    existing_progress = _read_progress(body.config_id)
    if existing_progress and existing_progress.get("stage") not in (STAGE_COMPLETE, STAGE_FAILED, None):
        return {
            "status": "already_in_progress",
            "current_stage": existing_progress.get("stage"),
            "current_message": existing_progress.get("message"),
            "message": "A deposit is already in flight. Check /status to watch progress.",
        }

    # -----------------------------------------------------------------
    # Idempotency: if already fully active + leaderboard joined, nothing to do.
    # -----------------------------------------------------------------
    if creds.get("hl_api_wallet_key") and creds.get("dgclaw_api_key"):
        existing_dgclaw_balance = await _get_dgclaw_hl_balance(creds["agent_wallet_address"])
        # Only short-circuit if we don't actually need to deposit more funds
        if existing_dgclaw_balance and existing_dgclaw_balance > 0:
            _write_progress(body.config_id, STAGE_COMPLETE, "Already fully set up and funded.")
            return {
                "status": "already_complete",
                "message": "Your bot is already live and funded.",
                "dgclaw_balance": existing_dgclaw_balance,
            }

    # -----------------------------------------------------------------
    # Fast validation — amount floor + Base balance (only if we actually need to deposit).
    # If HL is already funded via DGClaw, we skip perp_deposit entirely and
    # still let the user retry to finish HL setup + leaderboard without
    # re-funding. In that case amount + balance checks don't apply.
    # -----------------------------------------------------------------
    dgclaw_balance = await _get_dgclaw_hl_balance(creds["agent_wallet_address"])
    skipping_deposit = dgclaw_balance is not None and dgclaw_balance > 0

    if not skipping_deposit:
        if body.amount < DEPOSIT_MIN_USDC:
            return {
                "status": "amount_too_low",
                "minimum": DEPOSIT_MIN_USDC,
                "requested": body.amount,
                "message": f"Minimum deposit is ${DEPOSIT_MIN_USDC:.0f} USDC.",
            }
        base_balance = await get_base_usdc_balance(creds["agent_wallet_address"])
        if base_balance is None:
            return {"status": "rpc_error", "message": "Could not read Base USDC balance — try again shortly."}
        max_depositable = round(base_balance - ACP_FEE_RESERVE, 2)
        if body.amount > max_depositable:
            return {
                "status": "insufficient",
                "balance": base_balance, "requested": body.amount,
                "reserve": ACP_FEE_RESERVE, "max_depositable": max_depositable,
                "message": (
                    f"Balance ${base_balance:.2f} — after ${ACP_FEE_RESERVE:.2f} ACP-fee reserve, "
                    f"max depositable is ${max_depositable:.2f}. Send more USDC to "
                    f"{creds['agent_wallet_address']} on Base."
                ),
            }

    # -----------------------------------------------------------------
    # Kick off background task. Initial progress row so the UI can show
    # "Starting..." immediately on the next /status poll.
    # -----------------------------------------------------------------
    initial_message = (
        "Finishing Hyperliquid setup (deposit already made)…"
        if skipping_deposit
        else f"Starting deposit of ${body.amount:.2f}…"
    )
    _write_progress(body.config_id, STAGE_STARTING, initial_message, amount=body.amount)

    import asyncio as _a
    _a.create_task(_run_deposit_flow(body.config_id, creds["agent_record_id"], creds, body.amount))

    return {
        "status": "in_progress",
        "stage": STAGE_STARTING,
        "skipping_deposit": skipping_deposit,
        "message": initial_message,
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
