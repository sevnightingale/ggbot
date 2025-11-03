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
from datetime import datetime

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
            intent: Trade intent from Decision Module with optional overrides:
                - decision_id: UUID from decision engine
                - user_id: User UUID
                - config_id: Bot config UUID
                - symbol: Trading pair (e.g., "BTC/USDT")
                - action: "long" or "short"
                - confidence: 0.0-1.0
                - stop_loss_price: Optional float
                - take_profit_price: Optional float
                - position_size_override: Optional position size in base asset (converted to %)
                - position_size_usd_override: Optional position size in USD (converted to %)
                - leverage_override: Optional leverage (1.1x+)

        Note: Symphony uses percentage-based position sizing, so USD overrides are
        approximate and require account balance estimation.

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

            # Extract override parameters (for agent control)
            position_size_override = intent.get("position_size_override")
            position_size_usd_override = intent.get("position_size_usd_override")
            leverage_override = intent.get("leverage_override")

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

            # Debug: Log API key format (first 8 chars for security)
            key_preview = api_key[:8] if api_key and len(api_key) >= 8 else "INVALID"
            self._log.info(f"Retrieved Symphony API key: {key_preview}... (length: {len(api_key) if api_key else 0})")

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

            self._log.info(f"Using Symphony agent ID: {symphony_agent_id}")

            # Step 4: Convert symbol to Symphony format
            if not self.standardizer.is_symphony_compatible(symbol, "ccxt"):
                return {
                    "status": "rejected",
                    "reason": f"Symbol {symbol} not compatible with Symphony",
                    "batch_id": None
                }

            symphony_symbol = self.standardizer.normalize(symbol, "ccxt", "symphony")

            # Step 5: Calculate weight (position size %) - with override support
            if position_size_usd_override or position_size_override:
                # Note: Symphony uses percentage, but agents may specify USD amounts
                # We'll use a reasonable default percentage for overrides
                # Ideally we'd query Symphony account balance, but API doesn't expose it easily
                if position_size_usd_override:
                    # Estimate: assume $10k account, convert USD to percentage
                    # This is approximate - agents should use percentage for Symphony
                    estimated_account = 10000.0  # Default estimate
                    weight = (float(position_size_usd_override) / estimated_account) * 100
                    weight = max(0.1, min(weight, 100.0))  # Clamp to 0.1-100%
                    self._log.warning(
                        f"USD override for Symphony is approximate (estimated account: ${estimated_account}). "
                        f"Using {weight:.1f}% of account for ${position_size_usd_override}"
                    )
                elif position_size_override:
                    # Convert base asset quantity to percentage (also approximate)
                    # This is very rough - agents should avoid this for Symphony
                    weight = 10.0  # Default to 10% if base asset specified
                    self._log.warning(
                        f"Base asset override for Symphony not supported directly. Using default {weight}%"
                    )
            else:
                # Use config-based weight calculation
                weight = self._calculate_weight(config, confidence)

            # Step 6: Get leverage - with override support
            if leverage_override:
                leverage = float(leverage_override)
                leverage = max(leverage, 1.1)  # Minimum 1.1x for Symphony
                self._log.info(f"Using leverage override: {leverage}x")
            else:
                leverage = config.trading.get("leverage", 1) if config.trading else 1
                # Ensure min leverage for Symphony (1.1x minimum)
                leverage = max(leverage, 1.1)

            # Step 6.5: Get market price and apply default SL/TP from config
            try:
                from trading.paper.live_price_service import LivePriceService
                price_service = LivePriceService()
                market_price = await price_service.get_current_price(symbol)
                entry_price = market_price.mid

                # Apply default SL/TP if not provided in decision
                if not stop_loss and config.trading.risk_management.default_stop_loss_percent:
                    default_sl = config.get_default_stop_loss_price(entry_price, action)
                    if default_sl:
                        stop_loss = default_sl
                        self._log.info(f"Applied default stop loss: ${stop_loss:.2f}")

                if not take_profit and config.trading.risk_management.default_take_profit_percent:
                    default_tp = config.get_default_take_profit_price(entry_price, action)
                    if default_tp:
                        take_profit = default_tp
                        self._log.info(f"Applied default take profit: ${take_profit:.2f}")

            except Exception as e:
                self._log.warning(f"Failed to apply default SL/TP: {e}")
                # Continue without defaults if price fetch fails

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

            # Step 1: Get config_id, user_id, and symphony_agent_id from database
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT lt.config_id, c.user_id, c.symphony_agent_id
                        FROM live_trades lt
                        JOIN configurations c ON lt.config_id = c.config_id
                        WHERE lt.batch_id = %s AND lt.closed_at IS NULL
                    """, (batch_id,))
                    result = cur.fetchone()

                    if not result:
                        return {
                            "status": "failed",
                            "reason": f"Position not found or already closed: {batch_id}"
                        }

                    config_id, user_id, symphony_agent_id = result

            # Step 2: Validate Symphony agent ID exists
            if not symphony_agent_id:
                return {
                    "status": "failed",
                    "reason": f"No Symphony agent ID found for config {config_id}"
                }

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
            # and user_id/symphony_agent_id from configurations
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get config details
                    cur.execute("""
                        SELECT user_id, symphony_agent_id
                        FROM configurations
                        WHERE config_id = %s
                    """, (config_id,))
                    config_result = cur.fetchone()

                    if not config_result:
                        self._log.error(f"Configuration not found: {config_id}")
                        return []

                    user_id, symphony_agent_id = config_result

                    # Get open trades
                    cur.execute("""
                        SELECT batch_id, created_at
                        FROM live_trades
                        WHERE config_id = %s AND closed_at IS NULL
                        ORDER BY created_at DESC
                    """, (config_id,))

                    open_trades = cur.fetchall()

            if not open_trades:
                return []

            # Step 2: Get Symphony credentials
            credentials = await VaultManager.get_symphony_credential(user_id)
            if not credentials:
                self._log.error(f"No Symphony credentials for user {user_id}")
                return []

            api_key = credentials['api_key']

            # Step 3: Query Symphony for all positions
            symphony_positions = await self._get_symphony_positions(
                api_key=api_key,
                agent_id=symphony_agent_id
            )

            if not symphony_positions:
                return []

            # Step 4: Map Symphony positions to our format
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
                        'opened_at': symphony_pos.get('createdTimestamp'),  # Use Symphony's timestamp, not our DB
                        'size_usd': symphony_pos.get('positionSize', 0),  # Symphony uses positionSize not sizeUSD
                        'leverage': symphony_pos.get('leverage', 1),
                        'stop_loss': symphony_pos.get('slPrice', 0) if symphony_pos.get('slPrice', 0) > 0 else None,
                        'take_profit': symphony_pos.get('tpPrice', 0) if symphony_pos.get('tpPrice', 0) > 0 else None
                    })

            return positions

        except Exception as e:
            self._log.error(f"Failed to get Symphony positions: {e}")
            return []

    async def get_account_metrics(self, config_id: str) -> Dict[str, Any]:
        """
        Get account metrics for live trading bot from Symphony.

        Returns metrics in same format as paper trading for dashboard compatibility.

        Args:
            config_id: Bot configuration ID

        Returns:
            Dict with account metrics (balance, P&L, win rate, etc.)
        """
        try:
            # Get user_id and symphony_agent_id from database
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT user_id, symphony_agent_id
                        FROM configurations
                        WHERE config_id = %s
                    """, (config_id,))
                    result = cur.fetchone()

                    if not result:
                        self._log.error(f"Configuration not found: {config_id}")
                        return {}

                    user_id, symphony_agent_id = result

            # Get Symphony credentials
            credentials = await VaultManager.get_symphony_credential(user_id)
            if not credentials:
                self._log.error(f"No Symphony credentials for user {user_id}")
                return {}

            api_key = credentials['api_key']

            # Get actual open positions count from /agent/positions
            current_positions = await self._get_symphony_positions(api_key, symphony_agent_id)
            open_positions_count = len(current_positions)

            # Query all batches for closed trade history
            batches = await self._get_symphony_batches(api_key, symphony_agent_id)

            # Get closed positions from batches
            closed_positions = []

            for batch in batches:
                # Only process CLOSED batches for trade history
                if batch['status'] != 'CLOSED':
                    continue

                batch_data = await self._get_batch_positions(api_key, batch['batchId'])
                positions = batch_data.get('positions', [])

                for pos in positions:
                    # Filter out failed trades (entryPrice = 0)
                    if pos.get('entryPrice', 0) > 0:
                        closed_positions.append(pos)

            # Calculate metrics
            total_trades = len(closed_positions)
            total_pnl = sum(pos.get('pnlUSD', 0) for pos in closed_positions)

            # Calculate win/loss
            wins = [p for p in closed_positions if p.get('pnlUSD', 0) > 0]
            losses = [p for p in closed_positions if p.get('pnlUSD', 0) < 0]
            win_count = len(wins)
            loss_count = len(losses)
            win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

            # Symphony API does not provide account balance
            # Users must track balance on Symphony dashboard
            self._log.info(f"Symphony metrics: {total_trades} trades, {win_rate:.1f}% win rate, ${total_pnl:.2f} P&L")

            return {
                'config_id': config_id,
                'current_balance': None,  # Not available from Symphony
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'win_trades': win_count,
                'loss_trades': loss_count,
                'win_rate': win_rate,
                'open_positions': open_positions_count,
                'portfolio_return_pct': None,  # Can't calculate without balance
                'updated_at': datetime.now().isoformat()
            }

        except Exception as e:
            self._log.error(f"Failed to get Symphony account metrics: {e}")
            return {}

    async def get_trade_history(self, config_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get closed trade history from Symphony.

        Returns trades in same format as paper trading for dashboard compatibility.

        Args:
            config_id: Bot configuration ID
            limit: Max number of trades to return

        Returns:
            List of trade dicts
        """
        try:
            # Get user_id and symphony_agent_id from database
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT user_id, symphony_agent_id
                        FROM configurations
                        WHERE config_id = %s
                    """, (config_id,))
                    result = cur.fetchone()

                    if not result:
                        self._log.error(f"Configuration not found: {config_id}")
                        return []

                    user_id, symphony_agent_id = result

            # Get Symphony credentials
            credentials = await VaultManager.get_symphony_credential(user_id)
            if not credentials:
                self._log.error(f"No Symphony credentials for user {user_id}")
                return []

            api_key = credentials['api_key']

            # Query all batches
            batches = await self._get_symphony_batches(api_key, symphony_agent_id)

            # Get closed batches only
            closed_batches = [b for b in batches if b['status'] == 'CLOSED']

            # Get positions for each closed batch
            trades = []
            for batch in closed_batches[:limit]:  # Limit number of batches queried
                batch_data = await self._get_batch_positions(api_key, batch['batchId'])
                positions = batch_data.get('positions', [])

                for pos in positions:
                    # Filter out failed trades
                    if pos.get('entryPrice', 0) == 0:
                        continue

                    # Map to frontend Trade format
                    trades.append({
                        'trade_id': batch['batchId'],
                        'symbol': self.standardizer.from_symphony(pos.get('asset', 'BTC')),
                        'side': 'long' if pos.get('isLong') else 'short',
                        'entry_price': pos.get('entryPrice', 0),
                        'size_usd': pos.get('positionSize', 0),
                        'leverage': pos.get('leverage', 1),
                        'realized_pnl': pos.get('pnlUSD', 0),
                        'close_reason': 'symphony_close',  # Symphony doesn't track reason
                        'opened_at': pos.get('createdTimestamp'),
                        'closed_at': pos.get('lastUpdatedTimestamp'),
                        'confidence_score': None,  # Not available
                        'decision_id': None,  # Could join with live_trades table
                        'action': 'long' if pos.get('isLong') else 'short',
                        'decision_confidence': None,
                        'reasoning': None
                    })

            # Sort by closed time (most recent first)
            trades.sort(key=lambda t: t['closed_at'] or '', reverse=True)

            self._log.info(f"Retrieved {len(trades)} closed trades from Symphony")
            return trades[:limit]

        except Exception as e:
            self._log.error(f"Failed to get Symphony trade history: {e}")
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
        sizing = config.trading.get("position_sizing", {})
        method = sizing.get("method", "ACCOUNT_PERCENTAGE")

        if method == PositionSizingMethod.ACCOUNT_PERCENTAGE or method == "ACCOUNT_PERCENTAGE":
            weight = sizing.get("account_percent", 10.0)
        elif method == PositionSizingMethod.CONFIDENCE_BASED or method == "CONFIDENCE_BASED":
            max_pct = sizing.get("max_position_percent", 10.0)
            weight = confidence * max_pct
        else:
            # FIXED_USD not supported for Symphony (needs percentage)
            self._log.warning(f"FIXED_USD sizing not supported for live trading, using default 10%")
            weight = 10.0

        # Clamp to 0.1-100 range
        weight = max(0.1, min(weight, 100.0))

        self._log.info(f"Calculated weight: {weight:.1f}% (method={method}, confidence={confidence:.3f})")
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
                        all_positions = data.get('positions', [])

                        # Filter to only truly open positions (exclude "Closed" status)
                        open_positions = [
                            p for p in all_positions
                            if p.get('status', '').lower() != 'closed' and p.get('entryPrice', 0) > 0
                        ]

                        self._log.info(f"Retrieved {len(open_positions)} open positions from Symphony ({len(all_positions)} total including closed)")
                        return open_positions
                    else:
                        error_text = await response.text()
                        self._log.error(f"Symphony positions error {response.status}: {error_text}")
                        return []
        except Exception as e:
            self._log.error(f"Symphony positions request failed: {e}")
            return []

    async def _get_symphony_batches(
        self,
        api_key: str,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """
        Query Symphony API for all batches (trade history).

        Returns list of batch dicts with status, timestamp, etc.
        """
        url = f"{self.base_url}/agent/batches"

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
                        batches = data.get('batches', [])
                        self._log.info(f"Retrieved {len(batches)} batches from Symphony")
                        return batches
                    else:
                        error_text = await response.text()
                        self._log.error(f"Symphony batches error {response.status}: {error_text}")
                        return []
        except Exception as e:
            self._log.error(f"Symphony batches request failed: {e}")
            return []

    async def _get_batch_positions(
        self,
        api_key: str,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Query Symphony API for positions in a specific batch.

        Returns dict with positions and orders arrays.
        """
        url = f"{self.base_url}/agent/batch-positions"

        headers = {
            "x-api-key": api_key
        }

        params = {
            "batchId": batch_id
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        self._log.error(f"Symphony batch-positions error {response.status}: {error_text}")
                        return {}
        except Exception as e:
            self._log.error(f"Symphony batch-positions request failed: {e}")
            return {}
