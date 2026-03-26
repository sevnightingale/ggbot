"""
Virtuals DGClaw Arena API Endpoints

Phase 2: Any user can join the arena. Pre-created pool of lite Virtuals agents,
assigned on demand. Trades routed via claw REST API (no EOA needed).
"""

import asyncio
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
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
    wallet_address: str  # User's wallet they'll send USDC from (Base chain)

class SetBotRequest(BaseModel):
    config_id: str

class WithdrawRequest(BaseModel):
    amount: float


# =========================================================================
# Helpers
# =========================================================================

async def _get_user_arena_agent(user_id: str) -> Optional[Dict[str, Any]]:
    """Load the user's assigned arena agent with decrypted claw API key."""
    return await VaultManager.get_arena_credential_by_user(user_id)


async def _get_user_arena_agent_basic(user_id: str) -> Optional[Dict[str, Any]]:
    """Load user's arena agent without vault decryption (basic info only)."""
    row = await db_fetch_one("""
        SELECT id, wallet_address, agent_name, token_symbol,
               user_wallet_address, status, assigned_at
        FROM arena_agents
        WHERE assigned_user_id = %s AND status = 'assigned'
    """, (user_id,))
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
    }


# =========================================================================
# Endpoints
# =========================================================================

@router.post("/join")
async def join_arena(
    body: JoinRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Assign an available arena agent from the pool to this user.

    The user provides their wallet address (used for withdrawals later).
    Returns the agent's wallet address for the user to send USDC to.
    """
    user_id = current_user.user_id

    # Check if user already has an agent
    existing = await _get_user_arena_agent_basic(user_id)
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
                        status = 'assigned',
                        assigned_at = NOW(),
                        user_wallet_address = %s
                    WHERE id = %s
                """, (user_id, body.wallet_address, agent_id))

                conn.commit()

        _log.info(f"Assigned arena agent {agent_name} to user {user_id[:8]}")

        return {
            "status": "joined",
            "wallet_address": wallet_address,
            "agent_name": agent_name,
            "token_symbol": token_symbol,
            "message": f"Send USDC (Base chain) to {wallet_address}. Bridge fee is ~$1.",
        }

    except HTTPException:
        raise
    except Exception as e:
        _log.error(f"Failed to assign arena agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to join arena")


@router.get("/status")
async def get_arena_status(
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Get the user's arena status: balance, positions, active bot, wallet.
    """
    user_id = current_user.user_id

    agent = await _get_user_arena_agent(user_id)
    if not agent:
        return {"status": "not_joined"}

    client = ClawAPIClient(agent['claw_api_key'])
    wallet = agent['wallet_address']

    # Fetch balance, positions, and active bot in parallel
    wallet_balance_task = asyncio.create_task(_safe_wallet_balance(client))
    dgclaw_account_task = asyncio.create_task(_safe_dgclaw_account(client, wallet))
    dgclaw_positions_task = asyncio.create_task(_safe_dgclaw_positions(client, wallet))
    active_bot_task = asyncio.create_task(_get_active_arena_bot(user_id))

    wallet_balance = await wallet_balance_task
    dgclaw_account = await dgclaw_account_task
    positions = await dgclaw_positions_task
    active_bot = await active_bot_task

    dgclaw_balance = dgclaw_account.get('balance', 0) if dgclaw_account else 0

    return {
        "status": "joined",
        "agent_name": agent['agent_name'],
        "token_symbol": agent.get('token_symbol'),
        "wallet_address": wallet,
        "user_wallet_address": agent.get('user_wallet_address'),
        "wallet_balance_usdc": wallet_balance,
        "dgclaw_balance": dgclaw_balance,
        "positions": positions,
        "active_bot": active_bot,
    }


@router.post("/check-deposit")
async def check_deposit(
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    User clicks "I sent it" — check wallet balance and trigger perp_deposit.

    Retries up to 3 times with 5s delays if balance is zero (network delay).
    Keeps $1 in wallet for ACP transaction fees.
    """
    user_id = current_user.user_id

    agent = await _get_user_arena_agent(user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="No arena agent assigned")

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
            "message": "No USDC detected in agent wallet. It may take a few minutes for the transfer to confirm. Please try again shortly.",
        }

    # Keep $1 for ACP fees, deposit the rest
    reserve = 1.0
    min_deposit = 5.0

    if balance <= reserve + min_deposit:
        # Not enough to deposit after reserving for fees
        if balance < min_deposit:
            return {
                "status": "insufficient",
                "balance": balance,
                "message": f"Balance ${balance:.2f} is below the $5 minimum deposit.",
            }
        # Deposit everything if barely above minimum (user can add more for fees later)
        deposit_amount = balance - reserve
    else:
        deposit_amount = balance - reserve

    _log.info(f"Triggering perp_deposit: ${deposit_amount:.2f} (wallet balance: ${balance:.2f})")

    result = await client.deposit_to_dgclaw(deposit_amount)

    if result.get('status') == 'success':
        return {
            "status": "deposited",
            "amount_sent": deposit_amount,
            "effective_amount": round(deposit_amount - 1, 2),  # ~$1 bridge fee
            "message": f"Deposited ${deposit_amount:.0f} USDC. After bridge fee (~$1), expect ~${deposit_amount - 1:.0f} in your DGClaw account.",
        }
    else:
        _log.error(f"Deposit failed for user {user_id[:8]}: {result}")
        return {
            "status": "error",
            "balance": balance,
            "reason": result.get('reason', 'Deposit failed'),
        }


@router.post("/set-bot")
async def set_arena_bot(
    body: SetBotRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Select which bot drives arena trades. Only one bot per user.
    """
    user_id = current_user.user_id

    # Verify user has an arena agent
    agent = await _get_user_arena_agent_basic(user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="No arena agent assigned")

    # Verify the config belongs to this user
    config = await db_fetch_one("""
        SELECT config_id, config_name FROM configurations
        WHERE config_id = %s AND user_id = %s
    """, (body.config_id, user_id))

    if not config:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Disable arena on all user's bots, then enable on selected one
    await db_execute("""
        UPDATE configurations SET arena_enabled = false
        WHERE user_id = %s AND arena_enabled = true
    """, (user_id,))

    await db_execute("""
        UPDATE configurations SET arena_enabled = true
        WHERE config_id = %s AND user_id = %s
    """, (body.config_id, user_id))

    _log.info(f"User {user_id[:8]} set arena bot to {body.config_id[:8]}")

    return {
        "status": "success",
        "config_id": body.config_id,
        "config_name": config[1],
    }


@router.post("/withdraw")
async def withdraw_from_arena(
    body: WithdrawRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Withdraw USDC from DGClaw back to the user's wallet.

    Bridges: Hyperliquid -> Arbitrum -> Base. Minimum $2.
    Recipient is the wallet address stored during /join.
    """
    user_id = current_user.user_id

    agent = await _get_user_arena_agent(user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="No arena agent assigned")

    recipient = agent.get('user_wallet_address')
    if not recipient:
        raise HTTPException(
            status_code=400,
            detail="No withdrawal address on file. Please contact support."
        )

    if body.amount < 2:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is $2")

    client = ClawAPIClient(agent['claw_api_key'])

    _log.info(f"Withdrawing ${body.amount:.2f} for user {user_id[:8]} to {recipient}")
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
async def get_arena_leaderboard(
    current_user: AuthenticatedUser = Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    Get DGClaw arena leaderboard, enriched with ggbots user info where matched.
    """
    import aiohttp

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

    # Enrich with ggbots agent names where wallet addresses match
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
# Async helpers (for parallel fetching)
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

async def _get_active_arena_bot(user_id: str) -> Optional[Dict[str, Any]]:
    """Get the user's arena-enabled bot config."""
    row = await db_fetch_one("""
        SELECT config_id, config_name, config_data->>'selected_pair' as symbol
        FROM configurations
        WHERE user_id = %s AND arena_enabled = true
        LIMIT 1
    """, (user_id,))
    if not row:
        return None
    return {
        'config_id': row[0],
        'config_name': row[1],
        'symbol': row[2],
    }
