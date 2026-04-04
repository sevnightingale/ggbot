"""
Virtuals DGClaw Arena API Endpoints

1-bot-1-agent model: each bot (config_id) can independently join the arena.
Agents assigned from a pre-created pool, controlled via claw REST API.
"""

import asyncio
import base64
import time
from typing import Dict, Any, Optional

import aiohttp
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from core.common.logger import logger
from core.common.db import get_db_connection, db_fetch_one, db_fetch_all, db_execute
from core.auth.supabase_auth import get_current_user_v2, AuthenticatedUser
from core.auth.vault_utils import VaultManager
from trading.virtuals.claw_api import ClawAPIClient

router = APIRouter(prefix="/api/v2/virtuals-arena", tags=["virtuals-arena"])

_log = logger.bind(component="virtuals_arena_api")


# =========================================================================
# Request Models
# =========================================================================

class JoinRequest(BaseModel):
    config_id: str
    wallet_address: str  # User's wallet for withdrawals (Base chain)

class CheckDepositRequest(BaseModel):
    config_id: str

class WithdrawRequest(BaseModel):
    config_id: str
    amount: float


# =========================================================================
# Helpers
# =========================================================================

async def _get_config_arena_agent(config_id: str) -> Optional[Dict[str, Any]]:
    """Load the arena agent assigned to a bot config, with decrypted claw API key."""
    return await VaultManager.get_arena_credential_by_config(config_id)


async def _get_config_arena_agent_basic(config_id: str) -> Optional[Dict[str, Any]]:
    """Load arena agent for a config without vault decryption (basic info only)."""
    row = await db_fetch_one("""
        SELECT id, wallet_address, agent_name, token_symbol,
               user_wallet_address, status, assigned_at,
               dgclaw_api_key_vault_id IS NOT NULL as is_registered
        FROM arena_agents
        WHERE assigned_config_id = %s AND status = 'assigned'
    """, (config_id,))
    if not row:
        return None
    return {
        'agent_id': row[0],
        'wallet_address': row[1],
        'agent_name': row[2],
        'token_symbol': row[3],
        'user_wallet_address': row[4],
        'status': row[5],
        'assigned_at': row[6].isoformat() if row[6] else None,
        'is_registered': row[7],
    }


async def _verify_config_ownership(config_id: str, user_id: str) -> bool:
    """Verify that a config belongs to the authenticated user."""
    row = await db_fetch_one(
        "SELECT 1 FROM configurations WHERE config_id = %s AND user_id = %s",
        (config_id, user_id)
    )
    return bool(row)


async def _register_on_dgclaw(agent_id: int, wallet: str, claw_api_key: str) -> bool:
    """
    Register an arena agent on DGClaw via join_leaderboard.

    Generates RSA keypair, sends public key, decrypts returned DGClaw API key,
    stores it in vault. Costs $0.01 ACP fee from agent wallet.

    Returns True if registered successfully.
    """
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization, hashes

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode('utf-8')

    _log.info(f"Registering agent {agent_id} on DGClaw (join_leaderboard)...")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{ClawAPIClient.BASE_URL}/acp/jobs",
            headers={"x-api-key": claw_api_key, "Content-Type": "application/json"},
            json={
                "providerWalletAddress": ClawAPIClient.DGCLAW_AGENT,
                "jobOfferingName": "join_leaderboard",
                "serviceRequirements": {
                    "agentAddress": wallet,
                    "publicKey": pub_pem,
                },
            },
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            result = await resp.json()
            if resp.status not in (200, 201):
                _log.error(f"DGClaw join_leaderboard failed: {resp.status} {result}")
                return False

            job_id = result.get("data", {}).get("jobId")
            if not job_id:
                _log.error("No jobId returned from join_leaderboard")
                return False

        _log.info(f"DGClaw join job {job_id} created, polling...")

        start = time.time()
        while (time.time() - start) < 120:
            await asyncio.sleep(5)
            async with session.get(
                f"{ClawAPIClient.BASE_URL}/acp/jobs/{job_id}",
                headers={"x-api-key": claw_api_key},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as poll_resp:
                data = (await poll_resp.json()).get("data", {})
                phase = data.get("phase", "unknown")

                if phase == "COMPLETED":
                    deliverable = data.get("deliverable")
                    _log.info(f"DGClaw registration complete for agent {agent_id}")

                    dgclaw_key = None
                    if isinstance(deliverable, dict):
                        encrypted = deliverable.get("encryptedApiKey")
                        if encrypted:
                            try:
                                dgclaw_key = private_key.decrypt(
                                    base64.b64decode(encrypted),
                                    padding.OAEP(
                                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                        algorithm=hashes.SHA256(),
                                        label=None,
                                    )
                                ).decode('utf-8')
                            except Exception as e:
                                _log.error(f"Failed to decrypt DGClaw API key: {e}")

                    if dgclaw_key:
                        await VaultManager.store_arena_credential(
                            agent_id, claw_api_key, dgclaw_key
                        )
                        _log.info(f"DGClaw API key stored for agent {agent_id}")
                    return True

                elif phase == "REJECTED":
                    reason = ""
                    for memo in data.get("memos", []):
                        if memo.get("nextPhase") == "REJECTED" or memo.get("status") == "REJECTED":
                            reason = memo.get("signedReason", memo.get("content", ""))
                    _log.error(f"DGClaw registration rejected for agent {agent_id}: {reason}")
                    return False

    _log.error(f"DGClaw registration timed out for agent {agent_id}")
    return False


async def _is_registered_on_dgclaw(agent_id: int) -> bool:
    """Check if agent has a DGClaw API key (= registered)."""
    row = await db_fetch_one(
        "SELECT dgclaw_api_key_vault_id FROM arena_agents WHERE id = %s",
        (agent_id,)
    )
    return bool(row and row[0])


# =========================================================================
# Endpoints
# =========================================================================

@router.post("/join")
async def join_arena(
    body: JoinRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Assign an arena agent to a specific bot (config_id).

    Each bot gets its own arena agent. User provides their wallet address
    for withdrawals. Returns the agent wallet to send USDC to.
    """
    user_id = current_user.user_id

    if not await _verify_config_ownership(body.config_id, user_id):
        raise HTTPException(status_code=404, detail="Bot not found")

    # Check if this config already has an arena agent
    existing = await _get_config_arena_agent_basic(body.config_id)
    if existing:
        return {
            "status": "already_joined",
            "wallet_address": existing['wallet_address'],
            "agent_name": existing['agent_name'],
            "token_symbol": existing['token_symbol'],
        }

    # Assign an available agent (atomic SELECT FOR UPDATE)
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, wallet_address, agent_name, token_symbol
                    FROM arena_agents
                    WHERE status = 'available'
                    ORDER BY id
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                """)
                agent = cur.fetchone()

                if not agent:
                    raise HTTPException(
                        status_code=503,
                        detail="No arena agents available. Please try again later."
                    )

                agent_id, wallet_address, agent_name, token_symbol = agent

                cur.execute("""
                    UPDATE arena_agents
                    SET assigned_user_id = %s,
                        assigned_config_id = %s,
                        status = 'assigned',
                        assigned_at = NOW(),
                        user_wallet_address = %s
                    WHERE id = %s
                """, (user_id, body.config_id, body.wallet_address, agent_id))

                conn.commit()

        _log.info(f"Assigned arena agent {agent_name} to config {body.config_id[:8]}")

        return {
            "status": "joined",
            "wallet_address": wallet_address,
            "agent_name": agent_name,
            "token_symbol": token_symbol,
        }

    except HTTPException:
        raise
    except Exception as e:
        _log.error(f"Failed to assign arena agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to join arena")


@router.get("/status")
async def get_arena_status(
    config_id: str = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Get arena status for a specific bot.
    """
    if not await _verify_config_ownership(config_id, current_user.user_id):
        raise HTTPException(status_code=404, detail="Bot not found")

    agent = await _get_config_arena_agent(config_id)
    if not agent:
        return {"status": "not_joined"}

    client = ClawAPIClient(agent['claw_api_key'])
    wallet = agent['wallet_address']

    # Fetch balance, positions in parallel
    wallet_balance_task = asyncio.create_task(_safe_wallet_balance(client))
    dgclaw_account_task = asyncio.create_task(_safe_dgclaw_account(client, wallet))
    dgclaw_positions_task = asyncio.create_task(_safe_dgclaw_positions(client, wallet))

    wallet_balance = await wallet_balance_task
    dgclaw_account = await dgclaw_account_task
    positions = await dgclaw_positions_task

    dgclaw_balance = dgclaw_account.get('balance', 0) if dgclaw_account else 0

    # Check registration status (dgclaw_api_key_vault_id set = registered)
    is_registered = await _is_registered_on_dgclaw(agent['agent_id'])

    return {
        "status": "joined",
        "agent_name": agent['agent_name'],
        "token_symbol": agent.get('token_symbol'),
        "wallet_address": wallet,
        "user_wallet_address": agent.get('user_wallet_address'),
        "wallet_balance_usdc": wallet_balance,
        "dgclaw_balance": dgclaw_balance,
        "is_registered": is_registered,
        "positions": positions,
    }


@router.post("/check-deposit")
async def check_deposit(
    body: CheckDepositRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Check wallet balance and trigger deposit for a specific bot's arena agent.

    Retries up to 3 times with 5s delays if balance is zero (network delay).
    Registers on DGClaw automatically on first deposit.
    Keeps $1 in wallet for ACP transaction fees.
    """
    if not await _verify_config_ownership(body.config_id, current_user.user_id):
        raise HTTPException(status_code=404, detail="Bot not found")

    agent = await _get_config_arena_agent(body.config_id)
    if not agent:
        raise HTTPException(status_code=404, detail="No arena agent assigned to this bot")

    client = ClawAPIClient(agent['claw_api_key'])

    # Retry logic: USDC may not have arrived yet
    balance = 0.0
    for attempt in range(3):
        balance = await client.get_wallet_balance()
        if balance > 0:
            break
        if attempt < 2:
            _log.debug(f"Check-deposit attempt {attempt + 1}: balance $0, retrying in 5s")
            await asyncio.sleep(5)

    if balance <= 0:
        return {
            "status": "no_funds",
            "message": "No USDC detected yet. It may take a few minutes to confirm. Try again shortly.",
        }

    # Register on DGClaw if not yet registered (first deposit triggers this)
    if not await _is_registered_on_dgclaw(agent['agent_id']):
        _log.info(f"Agent {agent['agent_id']} not registered on DGClaw, starting background registration...")
        # Fire-and-forget: registration takes 30-120s, don't block the HTTP response
        asyncio.create_task(_register_on_dgclaw(
            agent['agent_id'], agent['wallet_address'], agent['claw_api_key']
        ))
        return {
            "status": "registering",
            "balance": balance,
            "message": "Registering your agent on Degen Claw. This takes about 30 seconds — we'll update automatically.",
        }

    # DGClaw minimum is $6 — need at least $6 in wallet
    min_deposit = 6.0

    if balance < min_deposit:
        return {
            "status": "insufficient",
            "balance": balance,
            "message": f"Balance ${balance:.2f} is below the ${min_deposit:.0f} minimum deposit. Send at least ${min_deposit:.0f} USDC.",
        }

    # Reserve for ACP trade fees ($0.01 per trade)
    # For tight balances ($6-$7), use smaller reserve to maximize deposit
    if balance < 8:
        reserve = 0.10  # Minimal reserve — user can top up later
    else:
        reserve = 1.0  # Standard reserve (~100 trades)

    deposit_amount = balance - reserve

    _log.info(f"Triggering perp_deposit: ${deposit_amount:.2f} (wallet: ${balance:.2f}, reserve: ${reserve:.2f})")

    result = await client.deposit_to_dgclaw(deposit_amount)

    if result.get('status') == 'success':
        receipt = result.get('receipt', {})
        bridged = float(receipt.get('bridgedAmount', deposit_amount - 1))
        return {
            "status": "deposited",
            "amount_sent": deposit_amount,
            "effective_amount": round(bridged, 2),
            "message": f"Deposited ${deposit_amount:.0f} USDC. After bridge fee, ${bridged:.2f} arrived in DGClaw.",
        }
    else:
        _log.error(f"Deposit failed: {result}")
        return {
            "status": "error",
            "balance": balance,
            "reason": result.get('reason', 'Deposit failed. DGClaw may be temporarily unavailable — try again in a few minutes.'),
        }


@router.post("/withdraw")
async def withdraw_from_arena(
    body: WithdrawRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Withdraw USDC from DGClaw back to the user's wallet.
    """
    if not await _verify_config_ownership(body.config_id, current_user.user_id):
        raise HTTPException(status_code=404, detail="Bot not found")

    agent = await _get_config_arena_agent(body.config_id)
    if not agent:
        raise HTTPException(status_code=404, detail="No arena agent assigned to this bot")

    recipient = agent.get('user_wallet_address')
    if not recipient:
        raise HTTPException(status_code=400, detail="No withdrawal address on file.")

    if body.amount < 2:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is $2")

    client = ClawAPIClient(agent['claw_api_key'])

    _log.info(f"Withdrawing ${body.amount:.2f} to {recipient}")
    result = await client.withdraw_from_dgclaw(body.amount, recipient)

    if result.get('status') == 'success':
        return {
            "status": "success",
            "amount": body.amount,
            "recipient": recipient,
            "job_id": result.get('job_id'),
        }
    else:
        return {
            "status": "error",
            "reason": result.get('reason', 'Withdrawal failed'),
        }


@router.get("/leaderboard")
async def get_arena_leaderboard() -> Dict[str, Any]:
    """
    Get DGClaw arena leaderboard, enriched with ggbots info.
    Public endpoint — no auth required.
    """
    leaderboard_url = "https://dgclaw-app-production.up.railway.app/leaderboard"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                leaderboard_url,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return {"entries": [], "error": f"Leaderboard unavailable (HTTP {resp.status})"}
                data = await resp.json()
                entries = data.get("data", data) if isinstance(data, dict) else data
    except Exception as e:
        _log.error(f"Leaderboard fetch failed: {e}")
        return {"entries": [], "error": "Leaderboard unavailable"}

    if isinstance(entries, list) and entries:
        wallet_addresses = [e.get("walletAddress", e.get("wallet", "")) for e in entries if isinstance(e, dict)]
        if wallet_addresses:
            placeholders = ','.join(['%s'] * len(wallet_addresses))
            rows = await db_fetch_all(f"""
                SELECT wallet_address, agent_name, token_symbol
                FROM arena_agents
                WHERE wallet_address IN ({placeholders})
            """, tuple(wallet_addresses))

            ggbots_map = {r[0]: {'agent_name': r[1], 'token_symbol': r[2]} for r in rows} if rows else {}
            for entry in entries:
                wallet = entry.get("walletAddress", entry.get("wallet", ""))
                if wallet in ggbots_map:
                    entry["ggbots_agent"] = ggbots_map[wallet]

    return {"entries": entries if isinstance(entries, list) else []}


# =========================================================================
# Async helpers
# =========================================================================

async def _safe_wallet_balance(client: ClawAPIClient) -> float:
    try:
        return await client.get_wallet_balance()
    except Exception as e:
        _log.debug(f"Wallet balance check failed: {e}")
        return 0.0

async def _safe_dgclaw_account(client: ClawAPIClient, wallet: str) -> Optional[Dict]:
    try:
        return await client.get_dgclaw_account(wallet)
    except Exception as e:
        _log.debug(f"DGClaw account check failed: {e}")
        return None

async def _safe_dgclaw_positions(client: ClawAPIClient, wallet: str) -> list:
    try:
        return await client.get_dgclaw_positions(wallet)
    except Exception as e:
        _log.debug(f"DGClaw positions check failed: {e}")
        return []
