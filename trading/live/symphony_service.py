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
import time
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass

from core.common.logger import logger
from core.common.db import get_db_connection
from core.common.activity_logger import log_activity_safe
from core.auth.vault_utils import VaultManager
from core.symbols import UniversalSymbolStandardizer


@dataclass
class CachedResponse:
    """Cached API response with expiration."""
    data: Any
    expires_at: float  # Unix timestamp


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
        # Reusable HTTP session to prevent inotify/aiodns leaks
        self._session: Optional[aiohttp.ClientSession] = None

        # Response cache to reduce API calls
        # Key: "method:agent_id" or "method:agent_id:param"
        # Value: CachedResponse with data and expiration
        self._cache: Dict[str, CachedResponse] = {}
        self._cache_ttl = 10  # seconds - positions/batches cache lifetime
        self._cache_hits = 0
        self._cache_misses = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create reusable HTTP session."""
        if self._session is None or self._session.closed:
            # Create session with timeout config
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session. Call on shutdown."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get cached response if not expired."""
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() < cached.expires_at:
                self._cache_hits += 1
                return cached.data
            # Expired - remove from cache
            del self._cache[cache_key]
        self._cache_misses += 1
        return None

    def _set_cached(self, cache_key: str, data: Any, ttl: Optional[float] = None):
        """Cache response with TTL."""
        ttl = ttl or self._cache_ttl
        self._cache[cache_key] = CachedResponse(
            data=data,
            expires_at=time.time() + ttl
        )

    def invalidate_cache(self, pattern: Optional[str] = None):
        """
        Invalidate cache entries.

        Args:
            pattern: If provided, only invalidate keys containing this string.
                    If None, invalidate all cache entries.
        """
        if pattern is None:
            self._cache.clear()
        else:
            keys_to_remove = [k for k in self._cache if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "cached_entries": len(self._cache)
        }

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
                # Access dict structure properly: config.trading is a dict
                risk_mgmt = config.trading.get("risk_management", {})

                if not stop_loss:
                    stop_loss_pct = risk_mgmt.get("default_stop_loss_percent")
                    if stop_loss_pct:
                        # Calculate SL price based on side
                        if action == "long":
                            stop_loss = entry_price * (1 - stop_loss_pct / 100.0)
                        elif action == "short":
                            stop_loss = entry_price * (1 + stop_loss_pct / 100.0)

                        if stop_loss:
                            self._log.info(f"Applied default stop loss: ${stop_loss:.2f} ({stop_loss_pct}%)")

                if not take_profit:
                    take_profit_pct = risk_mgmt.get("default_take_profit_percent")
                    if take_profit_pct:
                        # Calculate TP price based on side
                        if action == "long":
                            take_profit = entry_price * (1 + take_profit_pct / 100.0)
                        elif action == "short":
                            take_profit = entry_price * (1 - take_profit_pct / 100.0)

                        if take_profit:
                            self._log.info(f"Applied default take profit: ${take_profit:.2f} ({take_profit_pct}%)")

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

            # Step 10: Log trade_entry activity for timeline
            try:
                from trading.paper.live_price_service import LivePriceService
                price_service = LivePriceService()
                market_price = await price_service.get_current_price(symbol)
                entry_price = market_price.mid
            except Exception as e:
                self._log.warning(f"Failed to get entry price for activity log: {e}")
                entry_price = None

            log_activity_safe(
                config_id=config_id,
                user_id=user_id,
                activity_type='trade_entry',
                activity_source='symphony_service',
                summary=f"Opened {action} {symbol} ({weight:.1f}% @ {leverage}x)",
                details={
                    'symbol': symbol,
                    'side': action.lower(),
                    'entry_price': float(entry_price) if entry_price else None,
                    'weight_percent': float(weight),
                    'leverage': float(leverage),
                    'stop_loss': float(stop_loss) if stop_loss else None,
                    'take_profit': float(take_profit) if take_profit else None,
                    'confidence': confidence
                },
                trade_id=batch_id,
                trade_type='symphony',
                related_symbol=symbol,
                importance=9
            )

            self._log.info(f"Symphony trade executed successfully: batch_id={batch_id}")
            return {
                "status": "success",
                "batch_id": batch_id,
                "symbol": symbol,
                "action": action
            }

        except Exception as e:
            self._log.error(f"Symphony trade execution failed: {type(e).__name__}: {e}")
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

            # Step 4: Get position details before closing (for activity logging)
            position_details = None
            try:
                batch_data = await self._get_batch_positions(api_key, batch_id)
                positions = batch_data.get('positions', [])
                if positions:
                    # Get the first position in the batch
                    position_details = positions[0]
            except Exception as e:
                self._log.warning(f"Failed to get position details before close: {e}")

            # Step 5: Call Symphony API to close position
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

            # Step 6: Update live_trades table
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE live_trades
                        SET closed_at = NOW()
                        WHERE batch_id = %s
                    """, (batch_id,))
                    conn.commit()

            # Step 7: Log trade_exit activity for timeline
            if position_details:
                symbol = self.standardizer.from_symphony(position_details.get('asset', ''))
                entry_price = position_details.get('entryPrice', 0)
                exit_price = position_details.get('currentPrice', 0)
                pnl = position_details.get('pnlUSD', 0)
                size_usd = position_details.get('positionSize', 0)
                leverage = position_details.get('leverage', 1)
                side = 'long' if position_details.get('isLong') else 'short'

                # Calculate P&L percentage and duration
                pnl_pct = (pnl / size_usd * 100) if size_usd > 0 else 0

                # Parse timestamps if available
                duration_seconds = None
                if position_details.get('createdTimestamp') and position_details.get('lastUpdatedTimestamp'):
                    try:
                        from datetime import datetime
                        created = datetime.fromisoformat(position_details['createdTimestamp'].replace('Z', '+00:00'))
                        closed = datetime.fromisoformat(position_details['lastUpdatedTimestamp'].replace('Z', '+00:00'))
                        duration_seconds = (closed - created).total_seconds()
                    except Exception as e:
                        self._log.warning(f"Failed to calculate duration: {e}")

                log_activity_safe(
                    config_id=str(config_id),
                    user_id=str(user_id),
                    activity_type='trade_exit',
                    activity_source='symphony_service',
                    summary=f"Closed {symbol}: {'+' if pnl > 0 else ''}{pnl:.2f} ({pnl_pct:.1f}%)",
                    details={
                        'symbol': symbol,
                        'side': side,
                        'entry_price': float(entry_price),
                        'exit_price': float(exit_price),
                        'pnl': float(pnl),
                        'pnl_pct': pnl_pct,
                        'close_reason': reason,
                        'duration_seconds': duration_seconds,
                        'size_usd': float(size_usd),
                        'leverage': float(leverage)
                    },
                    trade_id=batch_id,
                    trade_type='symphony',
                    related_symbol=symbol,
                    importance=9
                )
            else:
                # Log minimal exit activity if we couldn't get position details
                log_activity_safe(
                    config_id=str(config_id),
                    user_id=str(user_id),
                    activity_type='trade_exit',
                    activity_source='symphony_service',
                    summary=f"Closed position (batch {batch_id[:8]}...)",
                    details={'close_reason': reason},
                    trade_id=batch_id,
                    trade_type='symphony',
                    importance=9
                )

            self._log.info(f"Symphony position closed successfully: batch_id={batch_id}")

            # Publish exit notification to Telegram
            if position_details and reason != 'account_reset':
                try:
                    from signals.publishing_service import publish_exit_to_telegram

                    # Get bot name from config
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT config_name FROM configurations WHERE config_id = %s", (config_id,))
                            result = cur.fetchone()
                            bot_name = result[0] if result else 'ggbot'

                    await publish_exit_to_telegram(
                        config_id=str(config_id),
                        user_id=str(user_id),
                        exit_data={
                            'bot_name': bot_name,
                            'symbol': symbol,
                            'side': side,
                            'entry_price': float(entry_price),
                            'exit_price': float(exit_price),
                            'pnl': float(pnl),
                            'pnl_pct': pnl_pct,
                            'close_reason': reason,
                            'duration_seconds': duration_seconds or 0
                        }
                    )
                except Exception as e:
                    self._log.warning(f"Failed to publish exit to Telegram: {e}")

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
            # Symphony returns: {asset, isLong, entryPrice, currentPrice, pnlUSD, collateralAmount, ...}
            # We need: {symbol, side, entry_price, current_price, unrealized_pnl, collateral, ...}
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
                        'pnl_percentage': symphony_pos.get('pnlPercentage', 0),
                        'opened_at': symphony_pos.get('createdTimestamp'),  # Use Symphony's timestamp, not our DB
                        'size_usd': symphony_pos.get('positionSize', 0),  # Symphony uses positionSize (notional)
                        'collateral': symphony_pos.get('collateralAmount', 0),  # Actual margin/collateral used
                        'leverage': symphony_pos.get('leverage', 1),
                        'stop_loss': symphony_pos.get('slPrice', 0) if symphony_pos.get('slPrice', 0) > 0 else None,
                        'take_profit': symphony_pos.get('tpPrice', 0) if symphony_pos.get('tpPrice', 0) > 0 else None,
                        'liquidation_price': symphony_pos.get('liquidationPrice', 0) if symphony_pos.get('liquidationPrice', 0) > 0 else None,
                        'status': symphony_pos.get('status', 'Open')
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
        Calculate position weight: confidence × max_margin_percent (clamped 0.1-100%).

        Weight represents the percentage of account to use as margin/collateral.
        """
        sizing = config.trading.get("position_sizing", {})
        max_pct = sizing.get("max_margin_percent", 20.0)
        weight = confidence * max_pct

        # Clamp to 0.1-100 range
        weight = max(0.1, min(weight, 100.0))

        self._log.info(f"Calculated weight: {weight:.1f}% (confidence={confidence:.3f}, max_margin={max_pct}%)")
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
            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    batch_id = data.get('batchId')
                    successful = data.get('successful', 0)
                    failed = data.get('failed', 0)

                    # CRITICAL: Check if any trades actually executed
                    if successful == 0:
                        # Trade was NOT actually executed - Symphony created batch but nothing happened
                        results = data.get('results', [])
                        error_details = []
                        for r in results:
                            result = r.get('result', {})
                            if not result.get('success'):
                                error_details.append(f"{r.get('smartAccount', 'unknown')}: {result}")

                        self._log.error(
                            f"Symphony batch created but 0 trades executed! "
                            f"batch_id={batch_id}, failed={failed}, details={error_details}"
                        )
                        return None

                    # Invalidate positions cache since we just opened a new position
                    self.invalidate_cache(f"positions:{agent_id}")
                    self._log.info(f"Symphony position opened: batch_id={batch_id}, successful={successful}, failed={failed}")
                    return batch_id
                else:
                    error_text = await response.text()
                    self._log.error(f"Symphony API error {response.status}: {error_text}")
                    return None
        except asyncio.TimeoutError:
            self._log.error(f"Symphony API timeout after {self.timeout}s")
            return None
        except Exception as e:
            self._log.error(f"Symphony API request failed: {type(e).__name__}: {e}")
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
            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    successful = data.get('successful', 0)
                    skipped = data.get('skipped', 0)
                    failed = data.get('failed', 0)

                    # CRITICAL: Check if close actually succeeded
                    # skipped > 0 is also OK (means position was already closed)
                    if successful == 0 and skipped == 0:
                        results = data.get('results', [])
                        error_details = []
                        for r in results:
                            result = r.get('result', {})
                            if not result.get('success') and not result.get('skipped'):
                                error_details.append(f"{r.get('smartAccount', 'unknown')}: {result}")

                        self._log.error(
                            f"Symphony batch close failed! "
                            f"batch_id={batch_id}, failed={failed}, details={error_details}"
                        )
                        return False

                    # Invalidate positions cache since we just closed a position
                    self.invalidate_cache(f"positions:{agent_id}")
                    self._log.info(f"Symphony position closed: batch_id={batch_id}, successful={successful}, skipped={skipped}, failed={failed}")
                    return True
                else:
                    error_text = await response.text()
                    self._log.error(f"Symphony close error {response.status}: {error_text}")
                    return False
        except Exception as e:
            self._log.error(f"Symphony close request failed: {type(e).__name__}: {e}")
            return False

    async def _get_symphony_positions(
        self,
        api_key: str,
        agent_id: str,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query Symphony API for all open positions.

        Args:
            api_key: Symphony API key
            agent_id: Symphony agent ID
            use_cache: If True, return cached response if available (default True)

        Returns list of position dicts.
        """
        cache_key = f"positions:{agent_id}"

        # Check cache first (unless explicitly bypassed)
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                self._log.debug(f"Cache HIT for positions:{agent_id[:8]}...")
                return cached

        url = f"{self.base_url}/agent/positions"

        headers = {
            "x-api-key": api_key
        }

        params = {
            "agentId": agent_id
        }

        try:
            session = await self._get_session()
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    all_positions = data.get('positions', [])

                    # Filter to only truly open positions (exclude "Closed" status)
                    open_positions = [
                        p for p in all_positions
                        if p.get('status', '').lower() != 'closed' and p.get('entryPrice', 0) > 0
                    ]

                    # Cache the result
                    self._set_cached(cache_key, open_positions)

                    self._log.info(f"Retrieved {len(open_positions)} open positions from Symphony ({len(all_positions)} total including closed)")
                    return open_positions
                elif response.status == 429:
                    # Rate limited - cache empty response with 60s backoff to prevent hammering
                    self._log.error(f"Symphony positions rate limited (429) - backing off 60s")
                    self._set_cached(cache_key, [], ttl=60)
                    return []
                else:
                    error_text = await response.text()
                    self._log.error(f"Symphony positions error {response.status}: {error_text}")
                    return []
        except Exception as e:
            self._log.error(f"Symphony positions request failed: {type(e).__name__}: {e}")
            return []

    async def _get_symphony_batches(
        self,
        api_key: str,
        agent_id: str,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query Symphony API for all batches (trade history).

        Args:
            api_key: Symphony API key
            agent_id: Symphony agent ID
            use_cache: If True, return cached response if available (default True)

        Returns list of batch dicts with status, timestamp, etc.
        """
        cache_key = f"batches:{agent_id}"

        # Check cache first
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                self._log.debug(f"Cache HIT for batches:{agent_id[:8]}...")
                return cached

        url = f"{self.base_url}/agent/batches"

        headers = {
            "x-api-key": api_key
        }

        params = {
            "agentId": agent_id
        }

        try:
            session = await self._get_session()
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    batches = data.get('batches', [])

                    # Cache the result
                    self._set_cached(cache_key, batches)

                    self._log.info(f"Retrieved {len(batches)} batches from Symphony")
                    return batches
                elif response.status == 429:
                    # Rate limited - cache empty response with 60s backoff
                    self._log.error(f"Symphony batches rate limited (429) - backing off 60s")
                    self._set_cached(cache_key, [], ttl=60)
                    return []
                else:
                    error_text = await response.text()
                    self._log.error(f"Symphony batches error {response.status}: {error_text}")
                    return []
        except Exception as e:
            self._log.error(f"Symphony batches request failed: {type(e).__name__}: {e}")
            return []

    async def _get_batch_positions(
        self,
        api_key: str,
        batch_id: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Query Symphony API for positions in a specific batch.

        Args:
            api_key: Symphony API key
            batch_id: Symphony batch ID
            use_cache: If True, return cached response if available (default True)
                      Closed batch data never changes, so longer cache TTL is used.

        Returns dict with positions and orders arrays.
        """
        cache_key = f"batch_positions:{batch_id}"

        # Check cache first - use longer TTL for batch positions (5 minutes)
        # since closed batch data is immutable
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        url = f"{self.base_url}/agent/batch-positions"

        headers = {
            "x-api-key": api_key
        }

        params = {
            "batchId": batch_id
        }

        try:
            session = await self._get_session()
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Cache with 5-minute TTL (closed batch data is immutable)
                    self._set_cached(cache_key, data, ttl=300)
                    return data
                elif response.status == 429:
                    # Rate limited - cache empty response with 60s backoff
                    self._log.error(f"Symphony batch-positions rate limited (429) - backing off 60s")
                    self._set_cached(cache_key, {}, ttl=60)
                    return {}
                else:
                    error_text = await response.text()
                    self._log.error(f"Symphony batch-positions error {response.status}: {error_text}")
                    return {}
        except Exception as e:
            self._log.error(f"Symphony batch-positions request failed: {type(e).__name__}: {e}")
            return {}
