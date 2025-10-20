"""
Symphony Live Trading Service

Thin wrapper around Symphony.io API for executing live trades.
Follows the same interface pattern as SupabasePaperTradingService.

Key responsibilities:
- Execute trade intents via Symphony API
- Close positions via Symphony API
- Query open positions from Symphony
- Save minimal audit trail to live_trades table
- Idempotency protection (prevent duplicate trades)

NOT responsible for:
- Position monitoring (Symphony handles)
- Balance tracking (Symphony handles)
- Risk management (Symphony handles)
- P&L calculation (Symphony handles)
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from decimal import Decimal

from core.common.logger import logger
from core.common.db import get_db_connection
from core.auth.vault_utils import VaultManager
from core.symbols import UniversalSymbolStandardizer
from core.config.models import PositionSizingMethod


class SymphonyLiveTradingService:
    """
    Symphony.io live trading service with minimal surface area.

    Symphony is the source of truth for all position data (P&L, prices, status).
    We only store batch_id linkage for audit trail.
    """

    def __init__(self):
        """Initialize Symphony service."""
        self.base_url = "https://api.symphony.io"
        self.timeout = 30  # seconds
        self.settlement_wait = 3  # seconds - wait for Symphony to settle trade
        self.standardizer = UniversalSymbolStandardizer()
        self._log = logger.bind(component="symphony_service")

    async def execute_trade_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute live trade via Symphony API.

        Args:
            intent: Trade intent from Decision Module with:
                - decision_id: UUID from decision engine
                - user_id: User UUID
                - config_id: Bot config UUID
                - symbol: Trading pair (e.g., "BTC/USDT")
                - action: "long" or "short"
                - confidence: 0.0-1.0
                - stop_loss_price: Optional float
                - take_profit_price: Optional float

        Returns:
            Execution result with:
                - status: "success" | "failed" | "rejected"
                - batch_id: Symphony batch ID (if successful)
                - reason: Error message (if failed)
        """
        try:
            # Extract intent data
            config_id = intent["config_id"]
            user_id = intent["user_id"]
            symbol = intent["symbol"]
            action = intent["action"]
            confidence = intent["confidence"]
            decision_id = intent.get("decision_id")
            stop_loss = intent.get("stop_loss_price")
            take_profit = intent.get("take_profit_price")

            self._log.info(f"Executing Symphony live trade: {action.upper()} {symbol} (confidence={confidence:.3f})")

            # Step 1: Check idempotency - prevent duplicate trades on network timeouts
            if decision_id:
                existing_batch = await self._check_existing_trade(decision_id)
                if existing_batch:
                    self._log.info(f"Trade already executed for decision {decision_id}, batch_id={existing_batch}")
                    return {
                        "status": "already_executed",
                        "batch_id": existing_batch,
                        "reason": "Trade already executed (idempotency protection)"
                    }

            # Step 2: Get Symphony credentials from Vault
            credentials = await VaultManager.get_symphony_credential(user_id)
            if not credentials:
                self._log.error(f"No Symphony credentials found for user {user_id}")
                return {
                    "status": "failed",
                    "reason": "Symphony account not connected. Please connect in Settings.",
                    "batch_id": None
                }

            api_key = credentials['api_key']

            # Step 3: Load configuration to get Symphony agent ID
            from core.services.config_service import config_service
            config = await config_service.get_config(config_id, user_id)
            if not config:
                return {
                    "status": "failed",
                    "reason": f"Configuration not found: {config_id}",
                    "batch_id": None
                }

            symphony_agent_id = config.symphony_agent_id
            if not symphony_agent_id:
                self._log.error(f"No symphony_agent_id set for config {config_id}")
                return {
                    "status": "failed",
                    "reason": "Symphony agent ID not configured for this bot",
                    "batch_id": None
                }

            # Step 4: Convert symbol to Symphony format
            if not self.standardizer.is_symphony_compatible(symbol):
                return {
                    "status": "rejected",
                    "reason": f"Symbol {symbol} not compatible with Symphony",
                    "batch_id": None
                }

            symphony_symbol = self.standardizer.to_symphony(symbol)

            # Step 5: Calculate weight (position size %) from config
            weight = self._calculate_weight(config, confidence)

            # Step 6: Get leverage from config
            leverage = config.trading.leverage if config.trading else 1
            # Ensure min leverage for Symphony (1.1x minimum)
            leverage = max(leverage, 1.1)

            # Step 7: Call Symphony API to open position
            batch_id = await self._open_symphony_position(
                api_key=api_key,
                agent_id=symphony_agent_id,
                symbol=symphony_symbol,
                action=action.upper(),  # "LONG" or "SHORT"
                weight=weight,
                leverage=leverage,
                stop_loss_price=stop_loss,
                take_profit_price=take_profit
            )

            if not batch_id:
                return {
                    "status": "failed",
                    "reason": "Symphony API call failed",
                    "batch_id": None
                }

            # Step 8: Wait for settlement (3 seconds)
            self._log.info(f"Waiting {self.settlement_wait}s for Symphony trade to settle...")
            await asyncio.sleep(self.settlement_wait)

            # Step 9: Save audit trail to live_trades table
            await self._save_live_trade_record(
                batch_id=batch_id,
                config_id=config_id,
                decision_id=decision_id
            )

            self._log.info(f"Symphony trade executed successfully: batch_id={batch_id}")
            return {
                "status": "success",
                "batch_id": batch_id,
                "symbol": symbol,
                "action": action
            }

        except Exception as e:
            self._log.error(f"Symphony trade execution failed: {e}")
            return {
                "status": "error",
                "reason": str(e),
                "batch_id": None
            }

    async def close_position(self, batch_id: str, reason: str = "manual") -> Dict[str, Any]:
        """
        Close a live position via Symphony API.

        Args:
            batch_id: Symphony batch ID to close
            reason: Close reason for logging

        Returns:
            Close result with status
        """
        try:
            self._log.info(f"Closing Symphony position: batch_id={batch_id}, reason={reason}")

            # Step 1: Get config_id and user_id from live_trades
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id FROM live_trades
                        WHERE batch_id = %s AND closed_at IS NULL
                    """, (batch_id,))
                    result = cur.fetchone()

                    if not result:
                        return {
                            "status": "failed",
                            "reason": f"Position not found or already closed: {batch_id}"
                        }

                    config_id = result[0]

            # Step 2: Load config to get user_id and symphony_agent_id
            from core.services.config_service import config_service
            config = await config_service.get_config(config_id)
            if not config:
                return {
                    "status": "failed",
                    "reason": f"Configuration not found: {config_id}"
                }

            user_id = config.user_id
            symphony_agent_id = config.symphony_agent_id

            # Step 3: Get Symphony credentials
            credentials = await VaultManager.get_symphony_credential(user_id)
            if not credentials:
                return {
                    "status": "failed",
                    "reason": "Symphony credentials not found"
                }

            api_key = credentials['api_key']

            # Step 4: Call Symphony API to close position
            success = await self._close_symphony_position(
                api_key=api_key,
                agent_id=symphony_agent_id,
                batch_id=batch_id
            )

            if not success:
                return {
                    "status": "failed",
                    "reason": "Symphony API close call failed"
                }

            # Step 5: Update live_trades table
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE live_trades
                        SET closed_at = NOW()
                        WHERE batch_id = %s
                    """, (batch_id,))
                    conn.commit()

            self._log.info(f"Symphony position closed successfully: batch_id={batch_id}")
            return {
                "status": "success",
                "batch_id": batch_id,
                "reason": reason
            }

        except Exception as e:
            self._log.error(f"Failed to close Symphony position: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }

    async def get_open_positions(self, config_id: str) -> List[Dict[str, Any]]:
        """
        Get open positions for a config from Symphony.

        Args:
            config_id: Bot configuration ID

        Returns:
            List of open positions with Symphony data
        """
        try:
            # Step 1: Get batch_ids for open positions from live_trades
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT batch_id, created_at
                        FROM live_trades
                        WHERE config_id = %s AND closed_at IS NULL
                        ORDER BY created_at DESC
                    """, (config_id,))

                    open_trades = cur.fetchall()

            if not open_trades:
                return []

            # Step 2: Load config to get user_id and symphony_agent_id
            from core.services.config_service import config_service
            config = await config_service.get_config(config_id)
            if not config:
                self._log.error(f"Configuration not found: {config_id}")
                return []

            user_id = config.user_id
            symphony_agent_id = config.symphony_agent_id

            # Step 3: Get Symphony credentials
            credentials = await VaultManager.get_symphony_credential(user_id)
            if not credentials:
                self._log.error(f"No Symphony credentials for user {user_id}")
                return []

            api_key = credentials['api_key']

            # Step 4: Query Symphony for all positions
            symphony_positions = await self._get_symphony_positions(
                api_key=api_key,
                agent_id=symphony_agent_id
            )

            if not symphony_positions:
                return []

            # Step 5: Map Symphony positions to our format
            # Symphony returns: {asset, isLong, entryPrice, currentPrice, pnlUSD, ...}
            # We need: {symbol, side, entry_price, current_price, unrealized_pnl, ...}
            positions = []
            for batch_id, created_at in open_trades:
                # Find matching Symphony position by batch_id
                symphony_pos = next((p for p in symphony_positions if p.get('batchId') == batch_id), None)
                if symphony_pos:
                    positions.append({
                        'batch_id': batch_id,
                        'symbol': self.standardizer.from_symphony(symphony_pos['asset']),
                        'side': 'long' if symphony_pos['isLong'] else 'short',
                        'entry_price': symphony_pos.get('entryPrice', 0),
                        'current_price': symphony_pos.get('currentPrice', 0),
                        'unrealized_pnl': symphony_pos.get('pnlUSD', 0),
                        'opened_at': created_at,
                        'size_usd': symphony_pos.get('sizeUSD', 0),
                        'leverage': symphony_pos.get('leverage', 1)
                    })

            return positions

        except Exception as e:
            self._log.error(f"Failed to get Symphony positions: {e}")
            return []

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _check_existing_trade(self, decision_id: str) -> Optional[str]:
        """Check if trade already executed for this decision (idempotency)."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT batch_id FROM live_trades
                        WHERE decision_id = %s
                    """, (decision_id,))
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            self._log.error(f"Failed to check existing trade: {e}")
            return None

    def _calculate_weight(self, config, confidence: float) -> float:
        """
        Calculate position weight (percentage 0-100) from config.

        Uses existing position sizing logic:
        - ACCOUNT_PERCENTAGE: Use account_percent directly
        - CONFIDENCE_BASED: confidence * max_position_percent
        - FIXED_USD: Not supported for live trading (returns default 10%)
        """
        sizing = config.trading.position_sizing

        if sizing.method == PositionSizingMethod.ACCOUNT_PERCENTAGE:
            weight = sizing.account_percent or 10.0
        elif sizing.method == PositionSizingMethod.CONFIDENCE_BASED:
            max_pct = sizing.max_position_percent or 10.0
            weight = confidence * max_pct
        else:
            # FIXED_USD not supported for Symphony (needs percentage)
            self._log.warning(f"FIXED_USD sizing not supported for live trading, using default 10%")
            weight = 10.0

        # Clamp to 0.1-100 range
        weight = max(0.1, min(weight, 100.0))

        self._log.info(f"Calculated weight: {weight:.1f}% (method={sizing.method}, confidence={confidence:.3f})")
        return weight

    async def _save_live_trade_record(
        self,
        batch_id: str,
        config_id: str,
        decision_id: Optional[str]
    ) -> None:
        """Save audit trail to live_trades table."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO live_trades (batch_id, config_id, decision_id, created_at)
                        VALUES (%s, %s, %s, NOW())
                    """, (batch_id, config_id, decision_id))
                    conn.commit()
        except Exception as e:
            self._log.error(f"Failed to save live trade record: {e}")
            # Don't fail the trade if database save fails

    # =========================================================================
    # Symphony API Methods
    # =========================================================================

    async def _open_symphony_position(
        self,
        api_key: str,
        agent_id: str,
        symbol: str,
        action: str,
        weight: float,
        leverage: float,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> Optional[str]:
        """
        Call Symphony API to open position.

        Returns batch_id on success, None on failure.
        """
        url = f"{self.base_url}/agent/batch-open"

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "agentId": agent_id,
            "symbol": symbol,
            "action": action,  # "LONG" or "SHORT"
            "weight": weight,
            "leverage": leverage,
            "orderOptions": {
                "triggerPrice": 0,  # Execute immediately at market
                "stopLossPrice": stop_loss_price or 0,
                "takeProfitPrice": take_profit_price or 0
            }
        }

        self._log.info(f"Opening Symphony position: {action} {symbol} @ {weight:.1f}% weight, {leverage}x leverage")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        batch_id = data.get('batchId')
                        self._log.info(f"Symphony position opened: batch_id={batch_id}")
                        return batch_id
                    else:
                        error_text = await response.text()
                        self._log.error(f"Symphony API error {response.status}: {error_text}")
                        return None
        except asyncio.TimeoutError:
            self._log.error(f"Symphony API timeout after {self.timeout}s")
            return None
        except Exception as e:
            self._log.error(f"Symphony API request failed: {e}")
            return None

    async def _close_symphony_position(
        self,
        api_key: str,
        agent_id: str,
        batch_id: str
    ) -> bool:
        """
        Call Symphony API to close position.

        Returns True on success, False on failure.
        """
        url = f"{self.base_url}/agent/batch-close"

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "agentId": agent_id,
            "batchId": batch_id
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._log.info(f"Symphony position closed: batch_id={batch_id}, successful={data.get('successful')}")
                        return True
                    else:
                        error_text = await response.text()
                        self._log.error(f"Symphony close error {response.status}: {error_text}")
                        return False
        except Exception as e:
            self._log.error(f"Symphony close request failed: {e}")
            return False

    async def _get_symphony_positions(
        self,
        api_key: str,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """
        Query Symphony API for all open positions.

        Returns list of position dicts.
        """
        url = f"{self.base_url}/agent/positions"

        headers = {
            "x-api-key": api_key
        }

        params = {
            "agentId": agent_id
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        positions = data.get('positions', [])
                        self._log.info(f"Retrieved {len(positions)} open positions from Symphony")
                        return positions
                    else:
                        error_text = await response.text()
                        self._log.error(f"Symphony positions error {response.status}: {error_text}")
                        return []
        except Exception as e:
            self._log.error(f"Symphony positions request failed: {e}")
            return []
