"""
Claw REST API Client — Control lite Virtuals agents via HTTP.

Lite agents (created via /api/agents/lite/key) are controlled entirely
through the claw API at https://claw-api.virtuals.io using an x-api-key
header. The Privy-managed signer handles all on-chain ACP transaction
signing automatically — no EOA private key needed.

This is the Phase 2 control path for user arena agents, replacing the
Phase 1 ACP SDK + EOA approach used for the admin bot (ggbots.ai).
"""

import asyncio
from typing import Dict, Any, Optional

import aiohttp

from core.common.logger import logger


class ClawAPIClient:
    """Control a lite Virtuals agent via the claw REST API."""

    BASE_URL = "https://claw-api.virtuals.io"
    DGCLAW_AGENT = "0xd478a8B40372db16cA8045F28C6FE07228F3781A"
    DGCLAW_BACKEND = "https://dgclaw-app-production.up.railway.app"

    # ACP job polling
    MAX_POLL_TIME = 180  # seconds (DGClaw can be slow, especially deposits/bridges)
    POLL_INTERVAL = 5    # seconds

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._log = logger.bind(component="claw_api")

    # =========================================================================
    # Trading
    # =========================================================================

    async def create_trade(
        self,
        pair: str,
        side: str,
        size: float,
        leverage: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Open a position on DGClaw via ACP perp_trade.

        Args:
            pair: HL bare name (e.g., "ETH", "BTC")
            side: "long" or "short"
            size: USD notional position size
            leverage: Leverage multiplier
            stop_loss: Optional SL price
            take_profit: Optional TP price

        Returns:
            {job_id, status, receipt} or {status: "error", reason}
        """
        requirements = {
            "action": "open",
            "pair": pair,
            "side": side,
            "size": str(round(size, 2)),
            "leverage": leverage,
        }
        if stop_loss:
            requirements["stopLoss"] = str(stop_loss)
        if take_profit:
            requirements["takeProfit"] = str(take_profit)

        return await self._execute_dgclaw_job("perp_trade", requirements)

    async def close_trade(self, pair: str) -> Dict[str, Any]:
        """Close a position on DGClaw via ACP perp_trade action=close."""
        return await self._execute_dgclaw_job("perp_trade", {
            "action": "close",
            "pair": pair,
        })

    # =========================================================================
    # Deposits / Withdrawals
    # =========================================================================

    async def deposit_to_dgclaw(self, amount: float) -> Dict[str, Any]:
        """
        Deposit USDC to DGClaw via ACP perp_deposit.

        Bridges Base → Arbitrum → Hyperliquid. ~$1 bridge fee.
        Minimum deposit: $5 USDC.
        """
        return await self._execute_dgclaw_job("perp_deposit", {
            "amount": str(int(amount)),
        })

    async def withdraw_from_dgclaw(self, amount: float, recipient: str) -> Dict[str, Any]:
        """
        Withdraw USDC from DGClaw via ACP perp_withdraw.

        Bridges Hyperliquid → Arbitrum → Base. Minimum: $2.
        """
        return await self._execute_dgclaw_job("perp_withdraw", {
            "amount": str(int(amount)),
            "recipient": recipient,
        })

    # =========================================================================
    # Account Queries
    # =========================================================================

    async def get_wallet_balance(self) -> float:
        """Get USDC balance of the agent's smart wallet on Base."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/acp/wallet-balances",
                headers={"x-api-key": self._api_key},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                for token in data.get("data", []):
                    symbol = token.get("tokenMetadata", {}).get("symbol")
                    if symbol == "USDC":
                        bal_hex = token.get("tokenBalance", "0x0")
                        decimals = token.get("tokenMetadata", {}).get("decimals", 6)
                        return int(bal_hex, 16) / (10 ** decimals)
                return 0.0

    async def get_dgclaw_account(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """
        Get DGClaw balance + account info from Railway backend.

        DGClaw pools funds centrally. This is the source of truth for balance,
        not the HL subaccount (which only holds active margin).
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.DGCLAW_BACKEND}/users/{wallet_address}/account",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    acct = data.get("data", {})
                    return {
                        "balance": float(acct.get("hlBalance", 0)),
                        "hl_subaccount": acct.get("hlSubaccountAddress"),
                    }
            except Exception as e:
                self._log.error(f"DGClaw account query failed: {e}")
                return None

    async def get_dgclaw_positions(self, wallet_address: str) -> list:
        """Get open positions from DGClaw Railway backend."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.DGCLAW_BACKEND}/users/{wallet_address}/positions",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return data.get("data", [])
            except Exception as e:
                self._log.error(f"DGClaw positions query failed: {e}")
                return []

    async def get_dgclaw_trades(self, wallet_address: str) -> list:
        """Get trade history from DGClaw Railway backend."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.DGCLAW_BACKEND}/users/{wallet_address}/trades",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return data.get("data", [])
            except Exception as e:
                self._log.error(f"DGClaw trades query failed: {e}")
                return []

    # =========================================================================
    # Internal
    # =========================================================================

    async def _execute_dgclaw_job(
        self, offering_name: str, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an ACP job to DGClaw and poll until completion.

        The claw API handles payment automatically when DGClaw accepts
        (NEGOTIATION → TRANSACTION is auto-paid by Privy-managed signer).
        """
        # Create job
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/acp/jobs",
                headers={
                    "x-api-key": self._api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "providerWalletAddress": self.DGCLAW_AGENT,
                    "jobOfferingName": offering_name,
                    "serviceRequirements": requirements,
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                result = await resp.json()
                if resp.status not in (200, 201):
                    return {
                        "status": "error",
                        "reason": f"Job creation failed: {result}",
                    }

                job_id = result.get("data", {}).get("jobId")
                if not job_id:
                    return {"status": "error", "reason": "No jobId returned"}

        self._log.info(f"ACP job {job_id} created: {offering_name}")

        # Poll until complete
        import time
        start = time.time()

        while (time.time() - start) < self.MAX_POLL_TIME:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/acp/jobs/{job_id}",
                    headers={"x-api-key": self._api_key},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    data = (await resp.json()).get("data", {})
                    phase = data.get("phase", "unknown")

                    if phase == "COMPLETED":
                        deliverable = data.get("deliverable")
                        self._log.info(f"Job {job_id}: completed")
                        return {
                            "status": "success",
                            "job_id": job_id,
                            "receipt": deliverable,
                        }

                    elif phase == "REJECTED":
                        reason = ""
                        for memo in data.get("memos", []):
                            if memo.get("nextPhase") == "REJECTED":
                                reason = memo.get("content", "")
                        self._log.warning(f"Job {job_id}: rejected — {reason}")
                        return {
                            "status": "error",
                            "reason": f"DGClaw rejected: {reason}",
                            "job_id": job_id,
                        }

            await asyncio.sleep(self.POLL_INTERVAL)

        self._log.error(f"Job {job_id}: timed out after {self.MAX_POLL_TIME}s")
        return {
            "status": "error",
            "reason": f"Timed out after {self.MAX_POLL_TIME}s",
            "job_id": job_id,
        }
