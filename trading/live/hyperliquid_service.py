"""
Hyperliquid Live Trading Service

Uses hyperliquid-python-sdk with per-user API wallet credentials from Supabase Vault.
API wallets can trade but CANNOT withdraw (protocol-enforced).

Key responsibilities:
- Execute trade intents via Hyperliquid SDK
- Place separate stop-loss and take-profit trigger orders
- Close positions via SDK market_close
- Query open positions from Hyperliquid Info API
- Save audit trail to live_trades table (provider='hyperliquid')
- Idempotency protection (prevent duplicate trades)
- Telegram exit notifications (entry notifications handled by orchestrator)

SDK: hyperliquid-python-sdk
Authentication: Per-user API wallet private key from Vault
Rate Limits: 1,200 requests/min (measured ~10,400 actual)
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional

import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

from core.common.logger import logger
from core.common.db import get_db_connection
from core.common.activity_logger import log_activity_safe
from core.symbols.standardizer import UniversalSymbolStandardizer


# Known Hyperliquid error patterns for categorization
_INSUFFICIENT_MARGIN_PATTERNS = [
    "insufficient margin",
    "not enough margin",
    "margin exceeded",
    "account value too low",
    "insufficient balance",
]
_RATE_LIMIT_PATTERNS = [
    "rate limit",
    "too many requests",
    "429",
]
_AGENT_EXPIRED_PATTERNS = [
    "agent not found",
    "agent expired",
    "unauthorized agent",
    "not authorized",
    "invalid api wallet",
]


def _classify_error(error_str: str) -> str:
    """Classify a Hyperliquid error string into a category."""
    lower = error_str.lower()
    for pattern in _INSUFFICIENT_MARGIN_PATTERNS:
        if pattern in lower:
            return "insufficient_balance"
    for pattern in _RATE_LIMIT_PATTERNS:
        if pattern in lower:
            return "rate_limit"
    for pattern in _AGENT_EXPIRED_PATTERNS:
        if pattern in lower:
            return "credentials_expired"
    return "unknown"


class HyperliquidLiveTradingService:
    """
    Hyperliquid live trading service.

    Uses per-user API wallet credentials stored in Supabase Vault.
    Each user's main wallet authorizes an API wallet that can only trade (not withdraw).
    Saves trades to live_trades table with provider='hyperliquid'.
    """

    # Retry config for transient failures
    MAX_RETRIES = 2
    RETRY_DELAY_BASE = 1.0  # seconds, doubles each retry

    def __init__(self):
        """Initialize Hyperliquid service."""
        self._log = logger.bind(component="hyperliquid_service")
        self.standardizer = UniversalSymbolStandardizer()
        # Use mainnet by default; testnet can be configured per-user in future
        self.base_url = constants.MAINNET_API_URL
        self.settlement_wait = 2  # seconds

    async def _get_exchange(self, user_id: str) -> Optional[Exchange]:
        """
        Initialize Hyperliquid Exchange SDK with user's API wallet from Vault.

        The Exchange is initialized with:
        - wallet: The API wallet (signs transactions)
        - base_url: Hyperliquid API URL
        - account_address: The user's MAIN wallet address (where funds live)

        This tells the SDK "sign with API wallet, but trade on behalf of main wallet".

        Args:
            user_id: User UUID

        Returns:
            Exchange instance, or None if credentials not found
        """
        try:
            from core.auth.vault_utils import VaultManager
            credentials = await VaultManager.get_hyperliquid_credential(user_id)
            if not credentials:
                self._log.error(f"No Hyperliquid credentials found for user {user_id}")
                return None

            api_wallet_key = credentials['api_wallet_key']
            wallet_address = credentials['wallet_address']

            # Create the API wallet object from private key
            wallet = eth_account.Account.from_key(api_wallet_key)

            # Initialize Exchange: sign with API wallet, trade on main wallet's account
            exchange = Exchange(
                wallet,
                self.base_url,
                account_address=wallet_address
            )

            return exchange

        except Exception as e:
            self._log.error(f"Failed to initialize Hyperliquid Exchange for user {user_id}: {e}")
            return None

    async def _get_info(self, user_id: str) -> Optional[tuple]:
        """
        Initialize Hyperliquid Info SDK for querying account state.

        Returns:
            Tuple of (Info instance, wallet_address), or None if credentials not found
        """
        try:
            from core.auth.vault_utils import VaultManager
            credentials = await VaultManager.get_hyperliquid_credential(user_id)
            if not credentials:
                self._log.error(f"No Hyperliquid credentials found for user {user_id}")
                return None

            wallet_address = credentials['wallet_address']
            info = Info(self.base_url, skip_ws=True)

            return (info, wallet_address)

        except Exception as e:
            self._log.error(f"Failed to initialize Hyperliquid Info for user {user_id}: {e}")
            return None

    async def _check_existing_trade(self, decision_id: str) -> Optional[str]:
        """Check if trade already exists for this decision (idempotency protection)."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT batch_id FROM live_trades
                        WHERE decision_id = %s AND provider = 'hyperliquid'
                        LIMIT 1
                    """, (decision_id,))
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            self._log.error(f"Error checking existing trade: {e}")
            return None

    def _get_hyperliquid_symbol(self, symbol: str) -> Optional[str]:
        """
        Convert any symbol format to Hyperliquid bare name (e.g. "BTC").

        Auto-detects the input format and converts via registry.
        """
        formats_to_check = ["ccxt", "platform", "ggshot", "symphony", "hummingbot", "hyperliquid"]

        for format_type in formats_to_check:
            if self.standardizer.is_supported(symbol, format_type):
                hl_symbol = self.standardizer.to_hyperliquid(symbol, format_type)
                if hl_symbol:
                    return hl_symbol

        return None

    async def _calculate_position_size(
        self,
        config: Any,
        confidence: float,
        symbol: str,
        user_id: str
    ) -> float:
        """
        Calculate position quantity from config, confidence, and account state.

        Position sizing: confidence × max_margin_percent × total_account_value × leverage / price

        Args:
            config: Bot configuration with position sizing settings
            confidence: AI confidence score (0.0-1.0)
            symbol: Platform format symbol (e.g., "BTC-USDT")
            user_id: User UUID (for querying Hyperliquid account)

        Returns:
            Position quantity in base asset (e.g., 0.001 BTC)
        """
        try:
            # Step 1: Query Hyperliquid account state
            info_result = await self._get_info(user_id)
            if not info_result:
                self._log.warning("Could not query Hyperliquid account, using minimum quantity")
                return 0.001

            info, wallet_address = info_result
            user_state = info.user_state(wallet_address)

            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            total_margin_used = float(margin_summary.get("totalMarginUsed", 0))
            available = account_value - total_margin_used

            if account_value <= 0:
                self._log.error("Hyperliquid account has zero balance — cannot size position")
                return 0.0  # Signal to caller that position cannot be sized

            self._log.info(
                f"Hyperliquid account: ${account_value:.2f} total, "
                f"${total_margin_used:.2f} in use, ${available:.2f} available"
            )

            # Step 2: Calculate margin from config
            trading_config = config.trading or {}
            sizing_config = trading_config.get('position_sizing', {})
            leverage = trading_config.get('leverage', 1)
            max_pct = sizing_config.get('max_margin_percent', 20.0) / 100.0

            # Margin = confidence × max_margin_percent × total_account_value
            margin = confidence * max_pct * account_value
            position_size_usd = margin * leverage

            self._log.info(
                f"Target position: ${position_size_usd:.2f} "
                f"(confidence={confidence:.3f}, max_margin={max_pct*100:.1f}%, "
                f"margin=${margin:.2f}, leverage={leverage}x)"
            )

            # Step 3: Get current market price
            from trading.paper.live_price_service import LivePriceService
            price_service = LivePriceService()
            market_price = await price_service.get_current_price(symbol)
            asset_price = market_price.mid

            self._log.info(f"Current {symbol} price: ${asset_price:,.2f}")

            # Step 4: Convert USD to quantity
            quantity = position_size_usd / asset_price

            # Step 5: Apply minimum quantity
            min_quantity = 0.001
            if quantity < min_quantity:
                self._log.warning(
                    f"Calculated quantity {quantity:.6f} below minimum {min_quantity}, using minimum"
                )
                quantity = min_quantity

            # Step 6: Round to appropriate precision
            quantity = round(quantity, 4)

            # Step 7: Safety check — don't exceed 95% of available balance
            notional = quantity * asset_price
            margin_needed = notional / leverage if leverage > 0 else notional
            if margin_needed > available * 0.95:
                self._log.warning(
                    f"Margin ${margin_needed:.2f} exceeds 95% of available ${available:.2f}, reducing"
                )
                max_margin = available * 0.95
                max_notional = max_margin * leverage
                quantity = max_notional / asset_price
                quantity = round(quantity, 4)
                quantity = max(quantity, min_quantity)
                self._log.info(f"Reduced to {quantity} (${quantity * asset_price:.2f} notional)")

            self._log.info(
                f"Position sizing: {quantity} {symbol.split('-')[0] if '-' in symbol else symbol} "
                f"(${quantity * asset_price:.2f} notional / {leverage}x = "
                f"${quantity * asset_price / leverage:.2f} margin)"
            )

            return quantity

        except Exception as e:
            self._log.error(f"Error calculating position size: {e}", exc_info=True)
            self._log.warning("Falling back to minimum quantity (0.001)")
            return 0.001

    async def execute_trade_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute live trade via Hyperliquid SDK.

        Args:
            intent: Trade intent from Decision Module with optional overrides:
                - config_id: Bot configuration ID
                - user_id: User ID
                - symbol: Trading symbol (any format - auto-detected)
                - action: "long" or "short"
                - confidence: 0.0-1.0
                - decision_id: Optional decision UUID
                - stop_loss_price: Optional stop loss price
                - take_profit_price: Optional take profit price
                - position_size_override: Optional position size in base asset
                - position_size_usd_override: Optional position size in USD notional
                - leverage_override: Optional leverage (1-50x)

        Returns:
            Execution result with status, batch_id, etc.
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

            # Extract overrides
            position_size_override = intent.get("position_size_override")
            position_size_usd_override = intent.get("position_size_usd_override")
            leverage_override = intent.get("leverage_override")

            self._log.info(
                f"Executing Hyperliquid live trade: {action.upper()} {symbol} "
                f"(confidence={confidence:.3f})"
            )

            # Step 1: Idempotency check
            if decision_id:
                existing_batch = await self._check_existing_trade(decision_id)
                if existing_batch:
                    self._log.info(f"Trade already executed for decision {decision_id}")
                    return {
                        "status": "already_executed",
                        "batch_id": existing_batch,
                        "reason": "Trade already executed (idempotency protection)"
                    }

            # Step 2: Get Exchange instance (loads user's API wallet from Vault)
            exchange = await self._get_exchange(user_id)
            if not exchange:
                return {
                    "status": "failed",
                    "reason": "Hyperliquid credentials not configured",
                    "batch_id": None
                }

            # Step 3: Convert symbol to Hyperliquid format
            hl_symbol = self._get_hyperliquid_symbol(symbol)
            if not hl_symbol:
                return {
                    "status": "failed",
                    "reason": f"Symbol {symbol} is not supported on Hyperliquid",
                    "batch_id": None
                }
            self._log.info(f"Symbol resolved: {symbol} → {hl_symbol}")

            # Step 4: Load configuration
            from core.services.config_service import config_service
            config = await config_service.get_config(config_id, user_id)
            if not config:
                return {
                    "status": "failed",
                    "reason": f"Configuration not found: {config_id}",
                    "batch_id": None
                }

            # Step 5: Get leverage
            if leverage_override:
                leverage = int(leverage_override)
                leverage = max(1, min(leverage, 50))  # Hyperliquid supports up to 50x
                self._log.info(f"Using leverage override: {leverage}x")
            else:
                trading = config.trading if hasattr(config, 'trading') else {}
                leverage = trading.get("leverage", 10) if isinstance(trading, dict) else 10
                leverage = max(leverage, 1)

            # Step 6: Calculate quantity
            # Convert symbol to platform format for price service
            platform_symbol = self.standardizer.from_hyperliquid(hl_symbol) or symbol

            if position_size_override:
                quantity = float(position_size_override)
                self._log.info(f"Using position size override: {quantity} (base asset)")
            elif position_size_usd_override:
                from trading.paper.live_price_service import LivePriceService
                price_service = LivePriceService()
                market_price = await price_service.get_current_price(platform_symbol)
                asset_price = market_price.mid
                quantity = float(position_size_usd_override) / asset_price
                quantity = round(quantity, 4)
                self._log.info(
                    f"Using USD override: ${position_size_usd_override} = "
                    f"{quantity} at ${asset_price:,.2f}"
                )
            else:
                quantity = await self._calculate_position_size(
                    config, confidence, platform_symbol, user_id
                )

            # Validate minimum quantity
            min_quantity = 0.001
            if quantity <= 0:
                return {
                    "status": "failed",
                    "reason": "Insufficient balance on Hyperliquid. Deposit more USDC to trade.",
                    "error_category": "insufficient_balance",
                    "batch_id": None
                }
            if quantity < min_quantity:
                self._log.warning(
                    f"Quantity {quantity} below minimum {min_quantity}, adjusting to minimum"
                )
                quantity = min_quantity

            # Step 7: Set leverage on Hyperliquid
            try:
                exchange.update_leverage(leverage, hl_symbol, is_cross=True)
                self._log.info(f"Set leverage to {leverage}x cross for {hl_symbol}")
            except Exception as lev_err:
                self._log.warning(f"Failed to set leverage (may already be set): {lev_err}")

            # Step 8: Apply default SL/TP if not provided
            if not stop_loss or not take_profit:
                try:
                    from trading.paper.live_price_service import LivePriceService
                    price_service = LivePriceService()
                    market_price = await price_service.get_current_price(platform_symbol)
                    entry_price = market_price.mid

                    # Get SL/TP percentages from config risk_management
                    trading_config = config.trading if hasattr(config, 'trading') else {}
                    risk_config = trading_config.get('risk_management', {}) if isinstance(trading_config, dict) else {}
                    sl_pct = risk_config.get('default_stop_loss_percent', 2.0) / 100.0
                    tp_pct = risk_config.get('default_take_profit_percent', 3.0) / 100.0

                    if not stop_loss:
                        if action.lower() == "long":
                            stop_loss = entry_price * (1 - sl_pct)
                        else:
                            stop_loss = entry_price * (1 + sl_pct)
                        self._log.info(f"Applied default stop loss: ${stop_loss:.2f} ({sl_pct*100:.1f}%)")

                    if not take_profit:
                        if action.lower() == "long":
                            take_profit = entry_price * (1 + tp_pct)
                        else:
                            take_profit = entry_price * (1 - tp_pct)
                        self._log.info(f"Applied default take profit: ${take_profit:.2f} ({tp_pct*100:.1f}%)")

                except Exception as e:
                    self._log.warning(f"Failed to apply default SL/TP: {e}")

            # Step 9: Execute market order with retry for transient errors
            is_buy = action.lower() == "long"
            self._log.info(
                f"Placing market order: {'BUY' if is_buy else 'SELL'} {quantity} {hl_symbol}"
            )

            order_result = None
            last_error = None
            for attempt in range(self.MAX_RETRIES + 1):
                try:
                    order_result = exchange.market_open(
                        hl_symbol,
                        is_buy,
                        quantity,
                        slippage=0.05  # 5% slippage tolerance
                    )
                    break  # Success — exit retry loop
                except Exception as net_err:
                    last_error = str(net_err)
                    error_cat = _classify_error(last_error)
                    if error_cat == "rate_limit" and attempt < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY_BASE * (2 ** attempt)
                        self._log.warning(
                            f"Rate limited on attempt {attempt + 1}, retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue
                    elif error_cat in ("insufficient_balance", "credentials_expired"):
                        # Non-retryable — return immediately with clear message
                        self._log.error(f"Non-retryable error: {last_error}")
                        reason_map = {
                            "insufficient_balance": "Insufficient balance on Hyperliquid. Deposit more USDC or reduce position size.",
                            "credentials_expired": "API wallet expired or deregistered. Reconnect in Settings → Live Trading.",
                        }
                        return {
                            "status": "failed",
                            "reason": reason_map.get(error_cat, last_error),
                            "error_category": error_cat,
                            "batch_id": None
                        }
                    elif attempt < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY_BASE * (2 ** attempt)
                        self._log.warning(
                            f"Network error on attempt {attempt + 1}: {net_err}, retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        self._log.error(f"All {self.MAX_RETRIES + 1} attempts failed: {net_err}")
                        return {
                            "status": "failed",
                            "reason": f"Network error after {self.MAX_RETRIES + 1} attempts: {last_error}",
                            "error_category": "network",
                            "batch_id": None
                        }

            # Check top-level status
            if not order_result or order_result.get("status") != "ok":
                error_msg = str(order_result) if order_result else "No response"
                error_cat = _classify_error(error_msg)
                self._log.error(f"Market order failed: {error_msg}")
                reason_map = {
                    "insufficient_balance": "Insufficient balance on Hyperliquid. Deposit more USDC or reduce position size.",
                    "credentials_expired": "API wallet expired or deregistered. Reconnect in Settings → Live Trading.",
                }
                return {
                    "status": "failed",
                    "reason": reason_map.get(error_cat, f"Market order rejected: {error_msg}"),
                    "error_category": error_cat,
                    "batch_id": None
                }

            # Extract fill info — CRITICAL: top-level "ok" doesn't mean filled
            # Must check statuses[] for "filled" or "error"
            statuses = order_result.get("response", {}).get("data", {}).get("statuses", [])
            filled_info = None
            fill_error = None
            for status in statuses:
                if isinstance(status, dict) and "filled" in status:
                    filled_info = status["filled"]
                    break
                elif isinstance(status, str) and "error" in status.lower():
                    fill_error = status
                elif isinstance(status, dict) and "error" in status:
                    fill_error = status["error"]

            if fill_error:
                error_cat = _classify_error(str(fill_error))
                self._log.error(f"Order fill error: {fill_error}")
                reason_map = {
                    "insufficient_balance": "Insufficient margin for this trade. Deposit more USDC or reduce position size/leverage.",
                    "credentials_expired": "API wallet expired or deregistered. Reconnect in Settings → Live Trading.",
                }
                return {
                    "status": "failed",
                    "reason": reason_map.get(error_cat, f"Order rejected: {fill_error}"),
                    "error_category": error_cat,
                    "batch_id": None
                }

            if not filled_info:
                self._log.error(f"No fill confirmation in statuses: {statuses}")
                return {
                    "status": "failed",
                    "reason": "Order submitted but no fill confirmation received. Check Hyperliquid dashboard.",
                    "error_category": "no_fill",
                    "batch_id": None
                }

            entry_price = float(filled_info["avgPx"])
            filled_sz = float(filled_info["totalSz"])

            # Generate batch_id for tracking
            batch_id = str(uuid.uuid4())
            self._log.info(
                f"Market order filled: {filled_sz} {hl_symbol} @ ${entry_price:,.2f} "
                f"(batch_id={batch_id})"
            )

            # Step 10: Place SL/TP trigger orders
            sl_order_id = None
            tp_order_id = None

            if stop_loss:
                try:
                    sl_order_type = {
                        "trigger": {
                            "triggerPx": round(stop_loss, 2),
                            "isMarket": True,
                            "tpsl": "sl"
                        }
                    }
                    self._log.info(
                        f"Placing SL trigger: {hl_symbol} {'SELL' if is_buy else 'BUY'} "
                        f"{filled_sz} @ trigger=${stop_loss:.2f}"
                    )
                    sl_result = exchange.order(
                        hl_symbol,
                        not is_buy,  # Opposite side to close
                        filled_sz,
                        round(stop_loss, 2),  # limit_px (not used for market trigger, but required)
                        sl_order_type,
                        reduce_only=True
                    )
                    if sl_result.get("status") == "ok":
                        sl_statuses = sl_result.get("response", {}).get("data", {}).get("statuses", [])
                        for s in sl_statuses:
                            if isinstance(s, dict) and "resting" in s:
                                sl_order_id = str(s["resting"]["oid"])
                                break
                        if sl_order_id:
                            self._log.info(f"Stop-loss placed: oid={sl_order_id} @ ${stop_loss:.2f}")
                        else:
                            self._log.warning(f"SL order accepted but no resting oid. Statuses: {sl_statuses}")
                    else:
                        self._log.warning(f"Stop-loss order failed: {sl_result}")
                except Exception as e:
                    self._log.warning(f"Failed to place stop-loss: {e}", exc_info=True)

            if take_profit:
                try:
                    tp_order_type = {
                        "trigger": {
                            "triggerPx": round(take_profit, 2),
                            "isMarket": True,
                            "tpsl": "tp"
                        }
                    }
                    self._log.info(
                        f"Placing TP trigger: {hl_symbol} {'SELL' if is_buy else 'BUY'} "
                        f"{filled_sz} @ trigger=${take_profit:.2f}"
                    )
                    tp_result = exchange.order(
                        hl_symbol,
                        not is_buy,  # Opposite side to close
                        filled_sz,
                        round(take_profit, 2),
                        tp_order_type,
                        reduce_only=True
                    )
                    if tp_result.get("status") == "ok":
                        tp_statuses = tp_result.get("response", {}).get("data", {}).get("statuses", [])
                        for s in tp_statuses:
                            if isinstance(s, dict) and "resting" in s:
                                tp_order_id = str(s["resting"]["oid"])
                                break
                        if tp_order_id:
                            self._log.info(f"Take-profit placed: oid={tp_order_id} @ ${take_profit:.2f}")
                        else:
                            self._log.warning(f"TP order accepted but no resting oid. Statuses: {tp_statuses}")
                    else:
                        self._log.warning(f"Take-profit order failed: {tp_result}")
                except Exception as e:
                    self._log.warning(f"Failed to place take-profit: {e}", exc_info=True)

            # Step 11: Wait for settlement
            self._log.info(f"Waiting {self.settlement_wait}s for trade to settle...")
            await asyncio.sleep(self.settlement_wait)

            # Step 12: Close any existing open live_trades for this config+symbol
            # On Hyperliquid, opening opposite direction auto-flips the position.
            # Our DB needs to reflect that the old trade is closed.
            await self._close_stale_trades(config_id, platform_symbol)

            # Step 13: Save audit trail
            await self._save_trade_record(
                batch_id=batch_id,
                config_id=config_id,
                decision_id=decision_id,
                symbol=platform_symbol,
                sl_order_id=sl_order_id,
                tp_order_id=tp_order_id
            )

            # Step 14: Log activity
            notional_value = filled_sz * entry_price
            try:
                activity_type = 'trade_entry'
                log_activity_safe(
                    config_id=config_id,
                    user_id=user_id,
                    activity_type=activity_type,
                    activity_source='hyperliquid_service',
                    summary=f"Opened {action.lower()} {platform_symbol} at ${entry_price:,.2f}",
                    details={
                        'symbol': platform_symbol,
                        'side': action.lower(),
                        'entry_price': entry_price,
                        'quantity': filled_sz,
                        'size_usd': notional_value,
                        'leverage': leverage,
                        'stop_loss_price': stop_loss,
                        'take_profit_price': take_profit,
                        'stop_loss_order_id': sl_order_id,
                        'take_profit_order_id': tp_order_id,
                        'confidence': confidence
                    },
                    trade_id=batch_id,
                    trade_type='hyperliquid',
                    related_symbol=platform_symbol,
                    importance=9
                )
                self._log.info(f"Activity logged for trade {batch_id}")
            except Exception as e:
                self._log.warning(f"Failed to log activity (non-critical): {e}")

            # Get current account balance for response
            account_balance = 0.0
            try:
                info_result = await self._get_info(user_id)
                if info_result:
                    info, wallet_address = info_result
                    user_state = info.user_state(wallet_address)
                    account_balance = float(
                        user_state.get("marginSummary", {}).get("accountValue", 0)
                    )
            except Exception:
                pass

            return {
                "status": "executed",
                "trade_id": batch_id,
                "symbol": platform_symbol,
                "side": action.lower(),
                "entry_price": entry_price,
                "size_usd": notional_value,
                "size_contracts": filled_sz,
                "fees": 0.0,
                "confidence_score": confidence,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "account_balance": account_balance,
                "batch_id": batch_id,
                "stop_loss_order_id": sl_order_id,
                "take_profit_order_id": tp_order_id
            }

        except Exception as e:
            self._log.error(f"Error executing Hyperliquid trade: {e}", exc_info=True)
            return {
                "status": "failed",
                "reason": str(e),
                "batch_id": None
            }

    async def close_position(self, batch_id: str, user_id: str) -> Dict[str, Any]:
        """
        Close an open position by batch_id.

        Args:
            batch_id: Trade batch ID from live_trades
            user_id: User UUID (for loading credentials)

        Returns:
            Close result with status
        """
        try:
            # Step 1: Look up trade record
            trade_record = await self._get_trade_record(batch_id)
            if not trade_record:
                return {
                    "status": "failed",
                    "reason": f"Trade record not found for batch_id {batch_id}"
                }

            symbol = trade_record.get("symbol", "")
            config_id = trade_record.get("config_id")
            sl_order_id = trade_record.get("stop_loss_order_id")
            tp_order_id = trade_record.get("take_profit_order_id")

            # Convert to Hyperliquid symbol
            hl_symbol = self._get_hyperliquid_symbol(symbol)
            if not hl_symbol:
                return {
                    "status": "failed",
                    "reason": f"Could not resolve Hyperliquid symbol for {symbol}"
                }

            # Step 2: Get Exchange instance
            exchange = await self._get_exchange(user_id)
            if not exchange:
                return {
                    "status": "failed",
                    "reason": "Hyperliquid credentials not configured"
                }

            # Step 3: Cancel SL/TP orders if they exist
            if sl_order_id:
                try:
                    exchange.cancel(hl_symbol, int(sl_order_id))
                    self._log.info(f"Cancelled SL order {sl_order_id}")
                except Exception as e:
                    self._log.warning(f"Failed to cancel SL order {sl_order_id}: {e}")

            if tp_order_id:
                try:
                    exchange.cancel(hl_symbol, int(tp_order_id))
                    self._log.info(f"Cancelled TP order {tp_order_id}")
                except Exception as e:
                    self._log.warning(f"Failed to cancel TP order {tp_order_id}: {e}")

            # Step 4: Close position via market_close with retry
            self._log.info(f"Closing position: {hl_symbol}")
            close_result = None
            for attempt in range(self.MAX_RETRIES + 1):
                try:
                    close_result = exchange.market_close(hl_symbol)
                    break
                except Exception as net_err:
                    error_cat = _classify_error(str(net_err))
                    if error_cat == "rate_limit" and attempt < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY_BASE * (2 ** attempt)
                        self._log.warning(f"Rate limited on close attempt {attempt + 1}, retrying in {delay:.1f}s")
                        await asyncio.sleep(delay)
                        continue
                    elif attempt < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY_BASE * (2 ** attempt)
                        self._log.warning(f"Network error on close attempt {attempt + 1}: {net_err}, retrying in {delay:.1f}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        return {
                            "status": "failed",
                            "reason": f"Failed to close position after {self.MAX_RETRIES + 1} attempts: {net_err}"
                        }

            if not close_result or close_result.get("status") != "ok":
                error_msg = str(close_result) if close_result else "No response"
                self._log.error(f"Failed to close position: {error_msg}")
                return {
                    "status": "failed",
                    "reason": f"Failed to close position: {error_msg}"
                }

            # Step 5: Mark trade as closed
            await self._mark_trade_closed(batch_id)
            self._log.info(f"Position closed for {hl_symbol} (batch_id={batch_id})")

            # Step 6: Log activity
            try:
                log_activity_safe(
                    config_id=config_id,
                    user_id=user_id,
                    activity_type='trade_exit',
                    activity_source='hyperliquid_service',
                    summary=f"Closed {symbol} position",
                    details={
                        'symbol': symbol,
                        'close_reason': 'manual',
                        'batch_id': batch_id
                    },
                    trade_id=batch_id,
                    trade_type='hyperliquid',
                    related_symbol=symbol,
                    importance=9
                )
            except Exception as e:
                self._log.warning(f"Failed to log close activity (non-critical): {e}")

            # Step 7: Publish exit notification to Telegram
            try:
                from signals.publishing_service import publish_exit_to_telegram

                # Get bot name from config
                bot_name = 'ggbot'
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT config_name FROM configurations WHERE config_id = %s", (config_id,))
                            result = cur.fetchone()
                            bot_name = result[0] if result else 'ggbot'
                except Exception:
                    pass

                await publish_exit_to_telegram(
                    config_id=str(config_id),
                    user_id=str(user_id),
                    exit_data={
                        'bot_name': bot_name,
                        'symbol': symbol,
                        'side': 'unknown',  # Not tracked in live_trades
                        'pnl': 0,
                        'pnl_pct': 0,
                        'close_reason': 'manual',
                        'duration_seconds': 0,
                        'live_tag': 'Hyperliquid'
                    }
                )
            except Exception as e:
                self._log.warning(f"Failed to publish exit to Telegram (non-critical): {e}")

            return {
                "status": "success",
                "symbol": symbol,
                "batch_id": batch_id
            }

        except Exception as e:
            self._log.error(f"Error closing position: {e}", exc_info=True)
            return {
                "status": "failed",
                "reason": str(e)
            }

    async def get_open_positions(self, config_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Get open positions for a specific bot configuration.

        Queries Hyperliquid Info API for all positions, then cross-references
        with live_trades to find positions belonging to this config.
        """
        try:
            info_result = await self._get_info(user_id)
            if not info_result:
                return []

            info, wallet_address = info_result
            user_state = info.user_state(wallet_address)
            positions = user_state.get("assetPositions", [])

            # Get batch_ids from database for this config
            batch_id_map = {}  # symbol -> batch_id
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT symbol, batch_id
                            FROM live_trades
                            WHERE config_id = %s AND provider = 'hyperliquid' AND closed_at IS NULL
                        """, (config_id,))
                        for row in cur.fetchall():
                            db_symbol, db_batch_id = row
                            batch_id_map[db_symbol] = db_batch_id
            except Exception as e:
                self._log.error(f"Error querying batch_ids: {e}")

            open_positions = []
            for pos_wrapper in positions:
                pos = pos_wrapper.get("position", {})
                coin = pos.get("coin", "")
                szi = float(pos.get("szi", 0))

                if szi == 0:
                    continue

                # Convert Hyperliquid symbol to platform format for matching
                platform_symbol = self.standardizer.from_hyperliquid(coin) or f"{coin}-USDT"
                batch_id = batch_id_map.get(platform_symbol)

                open_positions.append({
                    "symbol": platform_symbol,
                    "side": "LONG" if szi > 0 else "SHORT",
                    "size": abs(szi),
                    "entry_price": float(pos.get("entryPx", 0)),
                    "unrealized_pnl": float(pos.get("unrealizedPnl", 0)),
                    "liquidation_price": float(pos.get("liquidationPx", 0)),
                    "leverage": int(float(pos.get("leverage", {}).get("value", 1))) if isinstance(pos.get("leverage"), dict) else int(float(pos.get("leverage", 1))),
                    "margin_type": "cross",
                    "batch_id": batch_id
                })

            self._log.debug(f"Found {len(open_positions)} open positions on Hyperliquid")
            return open_positions

        except Exception as e:
            self._log.error(f"Error getting open positions: {e}", exc_info=True)
            return []

    async def get_account_metrics(self, config_id: str, user_id: str) -> Dict[str, Any]:
        """Get account metrics from Hyperliquid."""
        try:
            info_result = await self._get_info(user_id)
            if not info_result:
                return {
                    "status": "failed",
                    "reason": "Could not query Hyperliquid account"
                }

            info, wallet_address = info_result
            user_state = info.user_state(wallet_address)

            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            total_margin_used = float(margin_summary.get("totalMarginUsed", 0))
            available = account_value - total_margin_used

            positions = await self.get_open_positions(config_id, user_id)
            total_unrealized_pnl = sum(pos.get("unrealized_pnl", 0) for pos in positions)

            return {
                "status": "success",
                "balance": account_value,
                "available_balance": available,
                "total_unrealized_pnl": total_unrealized_pnl,
                "positions_count": len(positions),
                "positions": positions
            }

        except Exception as e:
            self._log.error(f"Error getting account metrics: {e}", exc_info=True)
            return {
                "status": "failed",
                "reason": str(e)
            }

    async def _save_trade_record(
        self,
        batch_id: str,
        config_id: str,
        decision_id: Optional[str],
        symbol: str,
        sl_order_id: Optional[str],
        tp_order_id: Optional[str]
    ) -> None:
        """Save audit trail to live_trades table with provider='hyperliquid'."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO live_trades
                        (batch_id, config_id, decision_id, provider, stop_loss_order_id, take_profit_order_id, symbol, created_at)
                        VALUES (%s, %s, %s, 'hyperliquid', %s, %s, %s, NOW())
                    """, (batch_id, config_id, decision_id, sl_order_id, tp_order_id, symbol))
                    conn.commit()
                    self._log.info(f"Saved Hyperliquid trade record: {batch_id} for {symbol}")
        except Exception as e:
            self._log.error(f"Error saving trade record: {e}")

    async def _get_trade_record(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get trade record from live_trades table."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT batch_id, config_id, decision_id, stop_loss_order_id, take_profit_order_id, symbol, created_at
                        FROM live_trades
                        WHERE batch_id = %s AND provider = 'hyperliquid'
                        LIMIT 1
                    """, (batch_id,))
                    row = cur.fetchone()
                    if row:
                        return {
                            "batch_id": row[0],
                            "config_id": row[1],
                            "decision_id": row[2],
                            "stop_loss_order_id": row[3],
                            "take_profit_order_id": row[4],
                            "symbol": row[5],
                            "created_at": row[6]
                        }
                    return None
        except Exception as e:
            self._log.error(f"Error getting trade record: {e}")
            return None

    async def _close_stale_trades(self, config_id: str, symbol: str) -> None:
        """Close any existing open live_trades for this config+symbol.

        On Hyperliquid, opening a position when one already exists either
        adds to it (same direction) or flips it (opposite direction).
        Either way, the previous trade record should be closed so we
        only have one open record per config+symbol at a time.
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE live_trades
                        SET closed_at = NOW()
                        WHERE config_id = %s AND provider = 'hyperliquid'
                          AND symbol = %s AND closed_at IS NULL
                    """, (config_id, symbol))
                    closed_count = cur.rowcount
                    conn.commit()
                    if closed_count > 0:
                        self._log.info(
                            f"Closed {closed_count} stale live_trade(s) for {symbol} "
                            f"(config={config_id})"
                        )
        except Exception as e:
            self._log.warning(f"Failed to close stale trades (non-critical): {e}")

    async def _mark_trade_closed(self, batch_id: str) -> None:
        """Update live_trades record with closed_at timestamp."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE live_trades
                        SET closed_at = NOW()
                        WHERE batch_id = %s AND provider = 'hyperliquid'
                    """, (batch_id,))
                    conn.commit()
                    self._log.info(f"Marked trade {batch_id} as closed")
        except Exception as e:
            self._log.error(f"Error marking trade closed: {e}")
