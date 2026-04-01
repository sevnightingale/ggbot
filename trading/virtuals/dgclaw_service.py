"""
DGClaw Arena Service — Execute trades on Virtuals DGClaw arena via ACP.

Mirrors bot trade decisions to DGClaw, where every trade is an on-chain ACP
transaction that generates $GG volume. All operations go through ACP jobs to
the Degen Claw agent, which executes on Hyperliquid.

All methods are synchronous (ACP SDK is sync). Callers use asyncio.to_thread().

Architecture:
    Bot Decision → Redis queue → sebastian_virtuals → this service
    → ACP job (perp_trade) → DGClaw agent → Hyperliquid execution
"""

import os
import time
from typing import Dict, Any, Optional

from core.common.logger import logger
from core.common.activity_logger import log_activity_safe
from core.services.acp_client import get_acp_client, ACPClientError
from core.symbols.standardizer import UniversalSymbolStandardizer


class DGClawArenaService:
    """
    Execute trades on the DGClaw arena via ACP.

    DGClaw is a Virtuals-native trading arena on Hyperliquid.
    All trades go through ACP jobs to the Degen Claw agent.
    Account data comes from DGClaw's Railway backend (not HL Info API —
    DGClaw pools funds centrally, HL subaccount only holds active margin).
    """

    # Degen Claw agent on Virtuals
    DGCLAW_AGENT = os.getenv(
        "DGCLAW_AGENT_ADDRESS",
        "0xd478a8B40372db16cA8045F28C6FE07228F3781A"
    )

    # DGClaw backend for account/position queries
    DGCLAW_BACKEND = "https://dgclaw-app-production.up.railway.app"

    # DGClaw/HL minimum position size
    MIN_NOTIONAL_USD = 10

    # ACP job polling config
    MAX_POLL_TIME = 90   # seconds
    POLL_INTERVAL = 5    # seconds between polls

    def __init__(self):
        self._acp_client = get_acp_client()
        self._log = logger.bind(component="dgclaw_arena")
        self._standardizer = UniversalSymbolStandardizer()

    # =========================================================================
    # Public API
    # =========================================================================

    def execute_arena_trade(self, trade_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mirror a bot's trade decision to DGClaw.

        Runs the full ACP job lifecycle synchronously (~20-50s).

        Args:
            trade_intent: Dict with keys:
                - action: "long" or "short"
                - symbol: Trading pair (any format, e.g. "BTC-USDT", "ETH/USDT")
                - confidence: 0.0-1.0
                - config_id: Bot config ID (for logging)
                - leverage: Leverage multiplier (default 3)
                - max_margin_percent: Max margin as % of account (default 20)
                - stop_loss_price: Optional SL price
                - take_profit_price: Optional TP price

        Returns:
            {status, job_id, receipt} on success
            {status: "error", reason: str} on failure
        """
        action = trade_intent.get("action", "")
        symbol = trade_intent.get("symbol", "")
        confidence = trade_intent.get("confidence", 0.5)
        config_id = trade_intent.get("config_id", "unknown")
        user_id = trade_intent.get("user_id")
        leverage = trade_intent.get("leverage", 3)
        max_margin_pct = trade_intent.get("max_margin_percent", 20)

        self._log.info(
            f"Arena trade: {action.upper()} {symbol} "
            f"(confidence={confidence:.2f}, leverage={leverage}x)"
        )

        # Step 1: Convert symbol to HL bare name (e.g., "ETH")
        pair = self._to_pair(symbol)
        if not pair:
            return {"status": "error", "reason": f"Cannot convert symbol: {symbol}"}

        # Step 2: Normalize action to DGClaw side
        if action in ("long", "enter_long", "enter"):
            side = "long"
        elif action in ("short", "enter_short"):
            side = "short"
        else:
            return {"status": "error", "reason": f"Unknown trade action: {action}"}

        # Step 3: Get subaccount balance and calculate position size
        account = self.get_arena_account()
        if not account:
            return {"status": "error", "reason": "Failed to query DGClaw subaccount"}

        balance = account["account_value"]
        if balance <= 0:
            return {"status": "error", "reason": "DGClaw subaccount has zero balance"}

        size_usd = self._calculate_arena_size(
            confidence=confidence,
            leverage=leverage,
            max_margin_pct=max_margin_pct,
            account_value=balance,
            available_margin=account["available_margin"],
        )

        if size_usd < self.MIN_NOTIONAL_USD:
            self._log.warning(
                f"Arena size ${size_usd:.2f} below minimum ${self.MIN_NOTIONAL_USD}, skipping"
            )
            return {
                "status": "skipped",
                "reason": f"Position size ${size_usd:.2f} below ${self.MIN_NOTIONAL_USD} minimum",
            }

        self._log.info(
            f"Arena sizing: ${size_usd:.2f} notional "
            f"(balance=${balance:.2f}, margin=${size_usd/leverage:.2f})"
        )

        # Step 4: Build perp_trade payload
        payload = {
            "action": "open",
            "pair": pair,
            "side": side,
            "size": str(round(size_usd, 2)),
            "leverage": leverage,
        }

        # Add SL/TP if provided
        sl = trade_intent.get("stop_loss_price")
        tp = trade_intent.get("take_profit_price")
        if sl:
            payload["stopLoss"] = str(sl)
        if tp:
            payload["takeProfit"] = str(tp)

        # Step 5: Execute via ACP
        result = self._execute_acp_trade(payload, config_id)

        # Step 6: Log activity
        if result.get("status") == "success":
            self._log_arena_activity(
                config_id=config_id,
                user_id=user_id,
                action=f"arena_open_{side}",
                summary=f"Arena: {side.upper()} {pair} ${size_usd:.0f} @ {leverage}x",
                details={
                    "pair": pair,
                    "side": side,
                    "size_usd": size_usd,
                    "leverage": leverage,
                    "acp_job_id": result.get("job_id"),
                    "receipt": result.get("receipt"),
                },
            )

        return result

    def close_arena_position(self, pair: str) -> Dict[str, Any]:
        """
        Close an existing position on DGClaw.

        Args:
            pair: HL bare name (e.g., "ETH", "BTC")

        Returns:
            {status, job_id, receipt} or {status: "error", reason}
        """
        self._log.info(f"Arena close: {pair}")

        payload = {
            "action": "close",
            "pair": pair,
        }

        result = self._execute_acp_trade(payload, config_id="arena_close")

        if result.get("status") == "success":
            self._log_arena_activity(
                config_id="arena_close",
                action="arena_close",
                summary=f"Arena: CLOSE {pair}",
                details={
                    "pair": pair,
                    "acp_job_id": result.get("job_id"),
                    "receipt": result.get("receipt"),
                },
            )

        return result

    def get_arena_account(self) -> Optional[Dict[str, Any]]:
        """
        Query DGClaw Railway backend for account balance + positions.

        DGClaw pools funds centrally — the HL subaccount only holds margin
        for active positions. The Railway backend tracks the real balance.

        Returns:
            {account_value, available_margin, positions: [...]}
            or None on failure
        """
        import requests

        wallet = os.getenv(
            "ACP_WALLET_ADDRESS",
            "0xREDACTED_AGENT_WALLET"
        )
        backend = self.DGCLAW_BACKEND

        try:
            # Get balance from DGClaw backend
            acct_resp = requests.get(
                f"{backend}/users/{wallet}/account", timeout=10
            )
            acct_resp.raise_for_status()
            acct_data = acct_resp.json().get("data", {})

            balance = float(acct_data.get("hlBalance", 0))

            # Get open positions
            pos_resp = requests.get(
                f"{backend}/users/{wallet}/positions", timeout=10
            )
            pos_resp.raise_for_status()
            positions_raw = pos_resp.json().get("data", [])

            positions = []
            total_margin_used = 0.0
            for p in positions_raw:
                margin = float(p.get("margin", 0))
                total_margin_used += margin
                positions.append({
                    "coin": p.get("pair", p.get("coin", "unknown")),
                    "side": p.get("side", "unknown"),
                    "size_usd": float(p.get("size", 0)),
                    "entry_price": float(p.get("entryPrice", 0)),
                    "leverage": int(p.get("leverage", 1)),
                    "unrealized_pnl": float(p.get("unrealizedPnl", 0)),
                    "margin_used": margin,
                })

            available = balance - total_margin_used

            self._log.debug(
                f"DGClaw account: ${balance:.2f} balance, "
                f"${total_margin_used:.2f} in use, ${available:.2f} available, "
                f"{len(positions)} positions"
            )

            return {
                "account_value": balance,
                "total_margin_used": total_margin_used,
                "available_margin": available,
                "positions": positions,
            }

        except Exception as e:
            self._log.error(f"Failed to query DGClaw account: {e}")
            return None

    # =========================================================================
    # Internal
    # =========================================================================

    def _execute_acp_trade(
        self, payload: Dict[str, Any], config_id: str
    ) -> Dict[str, Any]:
        """
        Execute a trade via ACP job to DGClaw's perp_trade offering.

        Handles the full ACP lifecycle:
        initiate → poll (accept → pay → wait → collect receipt)
        """
        from virtuals_acp.models import ACPJobPhase

        try:
            # Initiate ACP job
            self._log.info(f"Initiating ACP perp_trade: {payload}")
            job_id = self._acp_client.buy_from_offering(
                agent_address=self.DGCLAW_AGENT,
                offering_name="perp_trade",
                service_requirement=payload,
            )
            self._log.info(f"ACP job {job_id} initiated for DGClaw trade")

        except ACPClientError as e:
            self._log.error(f"Failed to initiate DGClaw trade: {e}")
            return {"status": "error", "reason": f"ACP initiation failed: {e}"}

        # Poll job lifecycle
        start = time.time()
        paid = False
        memo_delay_done = False

        while (time.time() - start) < self.MAX_POLL_TIME:
            try:
                job = self._acp_client.get_job(job_id)
                phase = ACPJobPhase(job.phase) if isinstance(job.phase, int) else job.phase

                if phase == ACPJobPhase.REQUEST:
                    # Waiting for DGClaw to accept
                    self._log.debug(f"Job {job_id}: waiting for DGClaw accept")

                elif phase == ACPJobPhase.NEGOTIATION and not paid:
                    # DGClaw accepted — pay $0.01 fee
                    # Brief delay for on-chain memo to be indexed (avoids
                    # "No negotiation memo" race on ~80% of attempts)
                    if not memo_delay_done:
                        memo_delay_done = True
                        time.sleep(3)
                    self._log.info(f"Job {job_id}: DGClaw accepted, paying...")
                    try:
                        self._acp_client.pay_job(job)
                        paid = True
                        self._log.info(f"Job {job_id}: paid")
                    except ACPClientError as e:
                        if "memo" in str(e).lower():
                            self._log.debug(f"Job {job_id}: memo not ready, will retry next poll")
                        else:
                            self._log.error(f"Job {job_id}: payment failed: {e}")
                            return {
                                "status": "error",
                                "reason": f"Payment failed: {e}",
                                "job_id": job_id,
                            }

                elif phase == ACPJobPhase.TRANSACTION:
                    # Waiting for DGClaw to execute on HL
                    self._log.debug(f"Job {job_id}: waiting for DGClaw execution")

                elif phase in (ACPJobPhase.EVALUATION, ACPJobPhase.COMPLETED):
                    # Trade executed — collect receipt
                    self._log.info(f"Job {job_id}: collecting trade receipt")
                    try:
                        receipt = self._acp_client.get_deliverable(job)
                        self._log.info(
                            f"Job {job_id}: trade receipt: {receipt}"
                        )
                        return {
                            "status": "success",
                            "job_id": job_id,
                            "receipt": receipt,
                        }
                    except ACPClientError as e:
                        self._log.warning(
                            f"Job {job_id}: receipt collection failed (non-fatal): {e}"
                        )
                        return {
                            "status": "success",
                            "job_id": job_id,
                            "receipt": None,
                            "note": f"Receipt collection failed: {e}",
                        }

                elif phase in (ACPJobPhase.REJECTED, ACPJobPhase.EXPIRED):
                    reason = getattr(job, "rejection_reason", "") or phase.name
                    self._log.warning(f"Job {job_id}: {phase.name} — {reason}")
                    return {
                        "status": "error",
                        "reason": f"DGClaw {phase.name}: {reason}",
                        "job_id": job_id,
                    }

            except ACPClientError as e:
                self._log.warning(f"Job {job_id}: poll error (retrying): {e}")

            time.sleep(self.POLL_INTERVAL)

        # Timeout
        self._log.error(f"Job {job_id}: timed out after {self.MAX_POLL_TIME}s")
        return {
            "status": "error",
            "reason": f"ACP job timed out after {self.MAX_POLL_TIME}s",
            "job_id": job_id,
        }

    def _calculate_arena_size(
        self,
        confidence: float,
        leverage: int,
        max_margin_pct: float,
        account_value: float,
        available_margin: float,
    ) -> float:
        """
        Calculate USD position size for DGClaw arena.

        Same formula as HyperliquidLiveTradingService._calculate_position_size()
        but outputs USD notional (DGClaw takes USD size, not base asset qty).

        Args:
            confidence: AI confidence score (0.0-1.0)
            leverage: Leverage multiplier
            max_margin_pct: Max margin as % of account value
            account_value: Total DGClaw subaccount value
            available_margin: Available margin after existing positions

        Returns:
            USD notional position size
        """
        # margin = confidence × max_margin_percent × account_value
        margin = confidence * (max_margin_pct / 100.0) * account_value
        size_usd = margin * leverage

        # Safety cap: don't exceed 90% of available margin
        # (more conservative than HL's 95% — shared admin subaccount)
        max_margin = available_margin * 0.90
        if margin > max_margin:
            self._log.warning(
                f"Arena margin ${margin:.2f} exceeds 90% of available ${available_margin:.2f}, reducing"
            )
            margin = max_margin
            size_usd = margin * leverage

        self._log.debug(
            f"Arena sizing: confidence={confidence:.2f}, "
            f"max_margin={max_margin_pct}%, margin=${margin:.2f}, "
            f"leverage={leverage}x → size=${size_usd:.2f}"
        )

        return round(size_usd, 2)

    def _to_pair(self, symbol: str) -> Optional[str]:
        """
        Convert any symbol format to HL bare name (e.g., "ETH").

        DGClaw uses the same pair names as Hyperliquid.
        """
        # Try all known formats
        formats = ["ccxt", "platform", "ggshot", "hyperliquid"]
        for fmt in formats:
            if self._standardizer.is_supported(symbol, fmt):
                hl = self._standardizer.to_hyperliquid(symbol, fmt)
                if hl:
                    return hl

        # Fallback: if it looks like a bare name already (e.g., "ETH"), use it
        if symbol.isalpha() and len(symbol) <= 6:
            return symbol.upper()

        self._log.warning(f"Cannot convert symbol to HL pair: {symbol}")
        return None

    def _log_arena_activity(
        self,
        config_id: str,
        action: str,
        summary: str,
        details: Dict[str, Any],
        user_id: str = None,
    ):
        """Log arena trade as an activity."""
        try:
            log_activity_safe(
                config_id=config_id,
                user_id=user_id,
                activity_type=action,
                activity_source="dgclaw_arena",
                summary=summary,
                details=details,
                importance=5,
            )
        except Exception as e:
            self._log.debug(f"Failed to log arena activity: {e}")
