"""
AsterDEX v3 Live Trading Service

Uses Web3 ECDSA authentication with Pro API (agent wallet).
Based on AsterDEX Futures API v3 documentation.

Authentication Flow:
1. Convert params to JSON string (sorted by key)
2. ABI encode: [json_str, user, signer, nonce]
3. Keccak hash the encoded bytes
4. ECDSA sign the hash with private key
5. Add user, signer, nonce, signature to request

Key responsibilities:
- Execute trade intents via AsterDEX v3 API
- Place separate stop-loss and take-profit orders
- Close positions via AsterDEX API
- Query open positions from AsterDEX
- Save audit trail to live_trades table (provider='aster')
- Idempotency protection (prevent duplicate trades)

API Documentation: https://fapi.asterdex.com (v3)
Authentication: Web3 ECDSA with agent wallet
Rate Limits: 2,400 REQUEST_WEIGHT/min, 1,200 ORDERS/min
"""

import os
import time
import json
import math
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

from core.common.logger import logger
from core.common.db import get_db_connection
from core.common.activity_logger import log_activity_safe
from core.config.models import PositionSizingMethod
from core.symbols.standardizer import UniversalSymbolStandardizer


class AsterDEXV3LiveTradingService:
    """
    AsterDEX v3 live trading service for Vibe Trading Competition.

    Uses Web3 ECDSA authentication with Pro API agent wallet.
    Saves trades to live_trades table with provider='aster'.
    """

    def __init__(self):
        """Initialize AsterDEX v3 service."""
        self.base_url = "https://fapi.asterdex.com"
        self.timeout = 30  # seconds
        self.settlement_wait = 2  # seconds
        self._log = logger.bind(component="aster_v3_service")

        # Load credentials from environment
        self.user = os.getenv("ASTER_USER_WALLET")  # Main wallet address (where funds are)
        self.signer = os.getenv("ASTER_WALLET_ADDRESS")  # API wallet address (Pro API)
        self.private_key = os.getenv("ASTER_PRIVATE_KEY")  # Private key for signing

        if not self.user or not self.signer or not self.private_key:
            self._log.error("Missing ASTER_USER_WALLET, ASTER_WALLET_ADDRESS, or ASTER_PRIVATE_KEY in environment")

    def _trim_dict(self, my_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert all values in dictionary to strings (required for signing).
        Handles nested dicts and lists.
        """
        for key in my_dict:
            value = my_dict[key]
            if isinstance(value, list):
                new_value = []
                for item in value:
                    if isinstance(item, dict):
                        new_value.append(json.dumps(self._trim_dict(item)))
                    else:
                        new_value.append(str(item))
                my_dict[key] = json.dumps(new_value)
                continue
            if isinstance(value, dict):
                my_dict[key] = json.dumps(self._trim_dict(value))
                continue
            my_dict[key] = str(value)
        return my_dict

    def _generate_signature(self, params: Dict[str, Any], nonce: int) -> Dict[str, Any]:
        """
        Generate Web3 ECDSA signature for AsterDEX v3 API.

        Steps:
        1. Convert all params to strings
        2. Add recvWindow and timestamp
        3. Create sorted JSON string
        4. ABI encode [json_str, user, signer, nonce]
        5. Keccak hash
        6. ECDSA sign with private key
        7. Add auth params to request

        Args:
            params: Request parameters
            nonce: Current timestamp in microseconds

        Returns:
            Parameters with user, signer, nonce, signature added
        """
        # Remove None values
        params = {key: value for key, value in params.items() if value is not None}

        # Add required fields
        params['recvWindow'] = 50000
        params['timestamp'] = int(round(time.time() * 1000))

        # Convert all to strings
        self._trim_dict(params)

        # Create sorted JSON string (no spaces, escaped quotes)
        json_str = json.dumps(params, sort_keys=True).replace(' ', '').replace("'", '"')

        # ABI encode
        encoded = encode(['string', 'address', 'address', 'uint256'],
                        [json_str, self.user, self.signer, nonce])

        # Keccak hash
        keccak_hex = Web3.keccak(encoded).hex()

        # ECDSA sign
        signable_msg = encode_defunct(hexstr=keccak_hex)
        signed_message = Account.sign_message(signable_message=signable_msg,
                                             private_key=self.private_key)
        signature = '0x' + signed_message.signature.hex()

        # Add auth parameters
        params['nonce'] = str(nonce)
        params['user'] = self.user
        params['signer'] = self.signer
        params['signature'] = signature

        return params

    def _to_aster_symbol(self, universal_symbol: str) -> str:
        """Convert BTC-USDT or BTC/USDT to BTCUSDT."""
        # Remove both dash and slash separators
        return universal_symbol.replace("-", "").replace("/", "")

    def _from_aster_symbol(self, aster_symbol: str) -> str:
        """Convert BTCUSDT to BTC/USDT."""
        if aster_symbol.endswith("USDT"):
            base = aster_symbol[:-4]
            return f"{base}/USDT"
        return aster_symbol

    def _is_aster_compatible(self, symbol: str) -> bool:
        """Check if symbol is compatible with AsterDEX."""
        if "/" not in symbol:
            return False
        base, quote = symbol.split("/")
        return quote == "USDT" and len(base) > 0

    async def _check_existing_trade(self, decision_id: str) -> Optional[str]:
        """Check if trade already exists (idempotency protection)."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT batch_id FROM live_trades
                        WHERE decision_id = %s AND provider = 'aster'
                        LIMIT 1
                    """, (decision_id,))
                    result = cur.fetchone()
                    return result[0] if result else None
        except Exception as e:
            self._log.error(f"Error checking existing trade: {e}")
            return None

    async def _calculate_weight(self, config: Any, confidence: float, symbol: str) -> float:
        """
        Calculate position quantity from config and account balance.

        Uses the bot's position sizing configuration to determine trade size:
        - ACCOUNT_PERCENTAGE: Fixed % of account per trade
        - CONFIDENCE_BASED: Confidence × max_position_percent
        - FIXED_USD: Fixed USD amount per trade

        Args:
            config: Bot configuration with position sizing settings
            confidence: AI confidence score (0.0-1.0)
            symbol: Platform format symbol (e.g., "BTC-USDT")

        Returns:
            Position quantity in base asset (e.g., 0.001 BTC)
        """
        try:
            # Step 1: Query Aster account info
            self._log.info("Querying AsterDEX account for position sizing...")
            account_data = await self._get_account_balance()
            if not account_data:
                self._log.warning("Could not query account, using minimum quantity")
                return 0.001

            # Extract account totals (all in USDT equivalent)
            wallet_balance = float(account_data.get("totalWalletBalance", 0))
            unrealized_pnl = float(account_data.get("totalUnrealizedProfit", 0))
            available_balance = float(account_data.get("availableBalance", 0))
            margin_balance = float(account_data.get("totalMarginBalance", 0))
            position_margin = float(account_data.get("totalPositionInitialMargin", 0))

            # Total account value = available + locked margin
            total_equity = available_balance + position_margin

            if total_equity <= 0:
                self._log.warning("No account equity found, using minimum quantity")
                return 0.001

            self._log.info(f"Account equity: ${total_equity:.2f} (available: ${available_balance:.2f}, in positions: ${position_margin:.2f}, wallet: ${wallet_balance:.2f}, unrealized: ${unrealized_pnl:.2f})")

            # Step 2: Calculate USD position size using config
            # This returns notional position size (margin × leverage)
            # Use total_equity (available + locked) as the base for sizing

            # Extract position sizing config from BotConfigV2
            trading_config = config.trading or {}
            sizing_config = trading_config.get('position_sizing', {})
            leverage = trading_config.get('leverage', 1)
            sizing_method = sizing_config.get('method', 'fixed_usd')

            # Calculate margin based on sizing method
            if sizing_method == 'fixed_usd':
                margin = sizing_config.get('fixed_amount_usd', 100.0)
            elif sizing_method == 'account_percentage':
                margin = total_equity * (sizing_config.get('account_percent', 5.0) / 100.0)
            elif sizing_method == 'confidence_based':
                max_pct = sizing_config.get('max_position_percent', 10.0) / 100.0
                margin = confidence * max_pct * total_equity
            else:
                # Fallback
                margin = confidence * 0.10 * total_equity

            # Position size = margin × leverage
            position_size_usd = margin * leverage

            self._log.info(f"Target position size: ${position_size_usd:.2f} (confidence={confidence:.3f}, method={sizing_method}, margin=${margin:.2f}, leverage={leverage}x)")

            # Step 3: Get current market price for the symbol
            # LivePriceService now handles both BTC-USDT and BTC/USDT formats automatically
            from trading.paper.live_price_service import LivePriceService
            price_service = LivePriceService()
            market_price = await price_service.get_current_price(symbol)
            asset_price = market_price.mid

            self._log.info(f"Current {symbol} price: ${asset_price:,.2f}")

            # Step 4: Convert USD position size to asset quantity
            # position_size already includes leverage, so just divide by price
            quantity = position_size_usd / asset_price

            # Step 5: Apply Aster minimum quantity (0.001 for BTC)
            # TODO: Read this from exchange filters dynamically
            min_quantity = 0.001
            if quantity < min_quantity:
                self._log.warning(
                    f"Calculated quantity {quantity:.6f} below minimum {min_quantity}, using minimum"
                )
                quantity = min_quantity

            # Step 6: Round to appropriate precision (3 decimals for BTC)
            # TODO: Read quantityPrecision from exchange filters dynamically
            quantity = round(quantity, 3)

            # Calculate actual margin that will be used
            trading = config.trading if hasattr(config, 'trading') else {}
            leverage = trading.get("leverage", 10) if isinstance(trading, dict) else 10
            leverage = max(leverage, 1)

            notional = quantity * asset_price
            margin = notional / leverage

            self._log.info(
                f"Position sizing: {quantity} {symbol.split('-')[0]} "
                f"(${notional:.2f} notional / {leverage}x = ${margin:.2f} margin)"
            )

            # Safety check: ensure margin doesn't exceed 95% of available balance
            if margin > available_balance * 0.95:
                self._log.warning(f"Margin ${margin:.2f} exceeds 95% of balance ${available_balance:.2f}, reducing")
                margin = available_balance * 0.95
                notional = margin * leverage
                quantity = notional / asset_price
                quantity = round(quantity, 3)
                self._log.info(f"Reduced to: {quantity} {symbol.split('-')[0]} (${notional:.2f} notional, ${margin:.2f} margin)")

            return quantity

        except Exception as e:
            self._log.error(f"Error calculating position size: {e}", exc_info=True)
            self._log.warning("Falling back to minimum quantity (0.001)")
            return 0.001

    async def execute_trade_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute live trade via AsterDEX v3 API.

        Args:
            intent: Trade intent from Decision Module with optional overrides:
                - config_id: Bot configuration ID
                - user_id: User ID
                - symbol: Trading symbol (any format - auto-detected: CCXT, platform, ggshot, symphony)
                - action: "long" or "short"
                - confidence: 0.0-1.0
                - decision_id: Optional decision UUID
                - stop_loss_price: Optional stop loss price
                - take_profit_price: Optional take profit price
                - position_size_override: Optional position size in base asset (e.g., 0.005 BTC)
                - position_size_usd_override: Optional position size in USD notional
                - leverage_override: Optional leverage (1-20x)

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

            # Extract override parameters (for agent control)
            position_size_override = intent.get("position_size_override")  # Base asset quantity
            position_size_usd_override = intent.get("position_size_usd_override")  # USD notional
            leverage_override = intent.get("leverage_override")  # 1-20x

            self._log.info(f"Executing AsterDEX v3 live trade: {action.upper()} {symbol} (confidence={confidence:.3f})")

            # Step 1: Check idempotency
            if decision_id:
                existing_batch = await self._check_existing_trade(decision_id)
                if existing_batch:
                    self._log.info(f"Trade already executed for decision {decision_id}")
                    return {
                        "status": "already_executed",
                        "batch_id": existing_batch,
                        "reason": "Trade already executed (idempotency protection)"
                    }

            # Step 2: Validate credentials
            if not self.user or not self.signer or not self.private_key:
                self._log.error("Missing AsterDEX v3 credentials")
                return {
                    "status": "failed",
                    "reason": "AsterDEX credentials not configured",
                    "batch_id": None
                }

            # Step 3: Auto-detect symbol format and validate AsterDEX compatibility
            standardizer = UniversalSymbolStandardizer()

            # Try different formats to find the symbol
            formats_to_check = ["ccxt", "platform", "ggshot", "symphony", "hummingbot"]
            symbol_found = False
            aster_symbol = None

            for format_type in formats_to_check:
                if standardizer.is_supported(symbol, format_type):
                    # Check if Aster-compatible
                    if not standardizer.is_aster_compatible(symbol, format_type=format_type):
                        self._log.error(f"Symbol {symbol} is not compatible with AsterDEX")
                        return {
                            "status": "failed",
                            "reason": f"Symbol {symbol} is not available on AsterDEX",
                            "batch_id": None
                        }

                    # Convert to Aster format (BTCUSDT)
                    all_formats = standardizer.get_all_formats(symbol, format_type)
                    if all_formats:
                        aster_symbol = all_formats.get("ggshot")  # AsterDEX uses ggshot format
                        symbol_found = True
                        self._log.info(f"Symbol detected as {format_type} format: {symbol} → {aster_symbol}")
                        break

            if not symbol_found or not aster_symbol:
                self._log.error(f"Symbol {symbol} not found in registry")
                return {
                    "status": "failed",
                    "reason": f"Symbol {symbol} is not supported",
                    "batch_id": None
                }

            # Step 5: Load configuration
            from core.services.config_service import config_service
            config = await config_service.get_config(config_id, user_id)
            if not config:
                return {
                    "status": "failed",
                    "reason": f"Configuration not found: {config_id}",
                    "batch_id": None
                }

            # Step 6: Calculate quantity - with override support for agents
            if position_size_override:
                # Direct quantity override (e.g., agent says "trade 0.005 BTC")
                quantity = float(position_size_override)
                self._log.info(f"Using position size override: {quantity} (base asset)")
            elif position_size_usd_override:
                # USD notional override (e.g., agent says "trade $500 worth")
                from trading.paper.live_price_service import LivePriceService
                price_service = LivePriceService()
                market_price = await price_service.get_current_price(symbol)
                asset_price = market_price.mid

                # Get leverage for calculation
                trading = config.trading if hasattr(config, 'trading') else {}
                temp_leverage = leverage_override if leverage_override else (trading.get("leverage", 10) if isinstance(trading, dict) else 10)

                # Convert USD to quantity (notional / price, no leverage adjustment needed here)
                quantity = float(position_size_usd_override) / asset_price
                quantity = round(quantity, 3)
                self._log.info(f"Using USD override: ${position_size_usd_override} = {quantity} at ${asset_price:,.2f}")
            else:
                # Use config-based position sizing
                quantity = await self._calculate_weight(config, confidence, symbol)

            # Validate minimum quantity
            min_quantity = 0.001  # Aster minimum for BTC
            if quantity < min_quantity:
                self._log.warning(f"Quantity {quantity} below minimum {min_quantity}, adjusting to minimum")
                quantity = min_quantity

            # Step 7: Get leverage - with override support
            if leverage_override:
                leverage = int(leverage_override)
                leverage = max(1, min(leverage, 20))  # Clamp to 1-20x
                self._log.info(f"Using leverage override: {leverage}x")
            else:
                trading = config.trading if hasattr(config, 'trading') else {}
                leverage = trading.get("leverage", 10) if isinstance(trading, dict) else 10
                leverage = max(leverage, 1)

            # Validate position against account balance
            account_data = await self._get_account_balance()
            if account_data:
                available_balance = float(account_data.get("availableBalance", 0))

                if available_balance > 0:
                    # Get current price for margin calculation
                    from trading.paper.live_price_service import LivePriceService
                    price_service = LivePriceService()
                    market_price = await price_service.get_current_price(symbol)
                    asset_price = market_price.mid

                    notional = quantity * asset_price
                    margin_required = notional / leverage
                    max_margin = available_balance * 0.95

                    if margin_required > max_margin:
                        self._log.warning(
                            f"Position requires ${margin_required:.2f} margin but only ${max_margin:.2f} available, "
                            f"reducing quantity"
                        )
                        # Reduce quantity to fit balance
                        max_notional = max_margin * leverage
                        quantity = max_notional / asset_price
                        quantity = round(quantity, 3)
                        quantity = max(quantity, min_quantity)  # Keep at minimum at least
                        self._log.info(f"Reduced to {quantity} (${quantity * asset_price:.2f} notional, ${margin_required:.2f} margin)")


            # Step 8: Apply default SL/TP if not provided
            if not stop_loss or not take_profit:
                try:
                    from trading.paper.live_price_service import LivePriceService
                    price_service = LivePriceService()
                    market_price = await price_service.get_current_price(symbol)
                    entry_price = market_price.mid

                    # Apply default SL/TP (2% and 3% for now)
                    if not stop_loss:
                        if action.lower() == "long":
                            stop_loss = entry_price * 0.98  # 2% below
                        else:
                            stop_loss = entry_price * 1.02  # 2% above
                        self._log.info(f"Applied default stop loss: ${stop_loss:.2f}")

                    if not take_profit:
                        if action.lower() == "long":
                            take_profit = entry_price * 1.03  # 3% above
                        else:
                            take_profit = entry_price * 0.97  # 3% below
                        self._log.info(f"Applied default take profit: ${take_profit:.2f}")

                except Exception as e:
                    self._log.warning(f"Failed to apply default SL/TP: {e}")

            # Step 8: Execute main order (MARKET)
            order_result = await self._place_market_order(
                symbol=aster_symbol,
                side="BUY" if action.lower() == "long" else "SELL",
                quantity=quantity,
                leverage=leverage
            )

            if not order_result or "orderId" not in order_result:
                return {
                    "status": "failed",
                    "reason": "Failed to place market order",
                    "batch_id": None
                }

            order_id = str(order_result["orderId"])
            self._log.info(f"Market order placed: {order_id}")

            # Step 9: Place stop-loss order
            sl_order_id = None
            if stop_loss:
                sl_result = await self._place_stop_loss_order(
                    symbol=aster_symbol,
                    side="SELL" if action.lower() == "long" else "BUY",
                    quantity=quantity,
                    stop_price=stop_loss
                )
                self._log.info(f"Stop-loss order response: {sl_result}")
                if sl_result and "orderId" in sl_result:
                    sl_order_id = str(sl_result["orderId"])
                    self._log.info(f"Stop-loss order placed: {sl_order_id}")
                else:
                    self._log.warning(f"Stop-loss order failed or returned no orderId")

            # Step 10: Place take-profit order
            tp_order_id = None
            if take_profit:
                tp_result = await self._place_take_profit_order(
                    symbol=aster_symbol,
                    side="SELL" if action.lower() == "long" else "BUY",
                    quantity=quantity,
                    stop_price=take_profit
                )
                self._log.info(f"Take-profit order response: {tp_result}")
                if tp_result and "orderId" in tp_result:
                    tp_order_id = str(tp_result["orderId"])
                    self._log.info(f"Take-profit order placed: {tp_order_id}")
                else:
                    self._log.warning(f"Take-profit order failed or returned no orderId")

            # Step 11: Wait for settlement
            self._log.info(f"Waiting {self.settlement_wait}s for trade to settle...")
            await asyncio.sleep(self.settlement_wait)

            # Step 12: Save audit trail
            await self._save_live_trade_record(
                batch_id=order_id,
                config_id=config_id,
                decision_id=decision_id,
                sl_order_id=sl_order_id,
                tp_order_id=tp_order_id,
                symbol=symbol  # Save universal symbol format
            )

            # Step 13: Log activity to timeline
            try:
                # Fetch entry price from current position (post-execution)
                from trading.paper.live_price_service import LivePriceService
                price_service = LivePriceService()
                price_data = await price_service.get_current_price(symbol)
                entry_price = price_data.mid

                # Calculate notional value
                notional_value = quantity * entry_price

                # Determine activity type
                activity_type = f"trade_entry_{action.lower()}"

                log_activity_safe(
                    config_id=config_id,
                    user_id=user_id,
                    activity_type=activity_type,
                    activity_source='aster_service',
                    summary=f"Opened {action.lower()} {symbol} at ${entry_price:,.2f}",
                    details={
                        'symbol': symbol,
                        'side': action.lower(),
                        'entry_price': entry_price,
                        'quantity': quantity,
                        'size_usd': notional_value,
                        'leverage': leverage,
                        'stop_loss_price': stop_loss,
                        'take_profit_price': take_profit,
                        'stop_loss_order_id': sl_order_id,
                        'take_profit_order_id': tp_order_id,
                        'confidence': confidence
                    },
                    trade_id=None,  # AsterDEX uses numeric order IDs, not UUIDs
                    trade_type='aster',
                    related_symbol=symbol,
                    importance=9
                )
                self._log.info(f"Activity logged for trade {order_id}")
            except Exception as e:
                self._log.warning(f"Failed to log activity (non-critical): {e}")

            # Get current account balance for response
            account_data = await self._get_account_balance()
            current_balance = 0.0
            if account_data:
                # Use totalMarginBalance (wallet + unrealized PnL)
                current_balance = float(account_data.get('totalMarginBalance', 0))

            return {
                "status": "executed",
                "trade_id": order_id,  # Use order_id as trade_id
                "symbol": symbol,  # Universal format (BTC/USDT)
                "side": action.lower(),  # "long" or "short"
                "entry_price": entry_price,
                "size_usd": notional_value,
                "size_contracts": quantity,
                "fees": 0.0,  # Aster doesn't provide immediate fee info
                "confidence_score": confidence,
                "stop_loss": stop_loss,  # Price, not order ID
                "take_profit": take_profit,  # Price, not order ID
                "account_balance": current_balance,
                "batch_id": order_id,  # Keep for backward compat
                "stop_loss_order_id": sl_order_id,
                "take_profit_order_id": tp_order_id
            }

        except Exception as e:
            self._log.error(f"Error executing AsterDEX trade: {e}", exc_info=True)
            return {
                "status": "failed",
                "reason": str(e),
                "batch_id": None
            }

    async def _place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        leverage: int
    ) -> Optional[Dict[str, Any]]:
        """Place market order on AsterDEX v3."""
        nonce = math.trunc(time.time() * 1000000)

        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
            "leverage": leverage,
            "positionSide": "BOTH"
        }

        # Generate signature (adds user, signer, nonce, signature, timestamp, recvWindow)
        signed_params = self._generate_signature(params, nonce)

        url = f"{self.base_url}/fapi/v3/order"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ggbots/1.0"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=signed_params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self._log.info(f"Market order successful: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        self._log.error(f"Market order failed: {response.status} - {error_text}")
                        return None
        except Exception as e:
            self._log.error(f"Exception placing market order: {e}")
            return None

    async def _place_stop_loss_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float
    ) -> Optional[Dict[str, Any]]:
        """Place stop-loss order (STOP_MARKET)."""
        nonce = math.trunc(time.time() * 1000000)

        params = {
            "symbol": symbol,
            "side": side,
            "type": "STOP_MARKET",
            "quantity": quantity,
            "stopPrice": stop_price,
            "positionSide": "BOTH"
        }

        signed_params = self._generate_signature(params, nonce)

        url = f"{self.base_url}/fapi/v3/order"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ggbots/1.0"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=signed_params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self._log.error(f"Stop-loss order failed: {response.status} - {await response.text()}")
                        return None
        except Exception as e:
            self._log.error(f"Exception placing stop-loss: {e}")
            return None

    async def _place_take_profit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float
    ) -> Optional[Dict[str, Any]]:
        """Place take-profit order (TAKE_PROFIT_MARKET)."""
        nonce = math.trunc(time.time() * 1000000)

        params = {
            "symbol": symbol,
            "side": side,
            "type": "TAKE_PROFIT_MARKET",
            "quantity": quantity,
            "stopPrice": stop_price,
            "positionSide": "BOTH"
        }

        signed_params = self._generate_signature(params, nonce)

        url = f"{self.base_url}/fapi/v3/order"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ggbots/1.0"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=signed_params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self._log.error(f"Take-profit order failed: {response.status} - {await response.text()}")
                        return None
        except Exception as e:
            self._log.error(f"Exception placing take-profit: {e}")
            return None

    async def _save_live_trade_record(
        self,
        batch_id: str,
        config_id: str,
        decision_id: Optional[str],
        sl_order_id: Optional[str],
        tp_order_id: Optional[str],
        symbol: str
    ) -> None:
        """Save audit trail to live_trades table with provider='aster'."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO live_trades
                        (batch_id, config_id, decision_id, provider, stop_loss_order_id, take_profit_order_id, symbol, created_at)
                        VALUES (%s, %s, %s, 'aster', %s, %s, %s, NOW())
                    """, (batch_id, config_id, decision_id, sl_order_id, tp_order_id, symbol))
                    conn.commit()
                    self._log.info(f"Saved AsterDEX trade record: {batch_id} for {symbol}")
        except Exception as e:
            self._log.error(f"Error saving trade record: {e}")

    async def get_open_positions(self, config_id: str) -> List[Dict[str, Any]]:
        """Get open positions for a specific bot configuration."""
        try:
            positions_data = await self._get_position_risk()
            if not positions_data:
                return []

            # Get batch_ids from database by symbol
            batch_id_map = {}  # Map: symbol -> batch_id
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT symbol, batch_id
                            FROM live_trades
                            WHERE config_id = %s AND provider = 'aster' AND closed_at IS NULL
                        """, (config_id,))
                        for row in cur.fetchall():
                            symbol, batch_id = row
                            batch_id_map[symbol] = batch_id
            except Exception as e:
                self._log.error(f"Error querying batch_ids: {e}")

            open_positions = []
            for pos in positions_data:
                position_amt = float(pos.get("positionAmt", 0))
                if position_amt == 0:
                    continue

                aster_symbol = pos.get("symbol", "")
                universal_symbol = self._from_aster_symbol(aster_symbol)

                # Look up batch_id from database by symbol
                batch_id = batch_id_map.get(universal_symbol)

                open_positions.append({
                    "symbol": universal_symbol,
                    "side": "LONG" if position_amt > 0 else "SHORT",
                    "size": abs(position_amt),
                    "entry_price": float(pos.get("entryPrice", 0)),
                    "mark_price": float(pos.get("markPrice", 0)),
                    "unrealized_pnl": float(pos.get("unRealizedProfit", 0)),
                    "liquidation_price": float(pos.get("liquidationPrice", 0)),
                    "leverage": int(pos.get("leverage", 1)),
                    "margin_type": pos.get("marginType", "isolated"),
                    "batch_id": batch_id  # Include batch_id from database
                })

            self._log.info(f"Found {len(open_positions)} open positions")
            return open_positions

        except Exception as e:
            self._log.error(f"Error getting open positions: {e}", exc_info=True)
            return []

    async def _get_position_risk(self) -> Optional[List[Dict[str, Any]]]:
        """Query position risk via GET /fapi/v3/positionRisk."""
        nonce = math.trunc(time.time() * 1000000)
        params = {}

        signed_params = self._generate_signature(params, nonce)

        url = f"{self.base_url}/fapi/v3/positionRisk"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=signed_params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self._log.error(f"Position risk query failed: {response.status} - {error_text}")
                        return None
        except Exception as e:
            self._log.error(f"Exception querying position risk: {e}")
            return None

    async def close_position(self, batch_id: str, user_id: str) -> Dict[str, Any]:
        """Close an open position by batch_id."""
        try:
            # Get trade record
            trade_record = await self._get_trade_record(batch_id)
            if not trade_record:
                return {
                    "status": "failed",
                    "reason": f"Trade record not found for batch_id {batch_id}"
                }

            sl_order_id = trade_record.get("stop_loss_order_id")
            tp_order_id = trade_record.get("take_profit_order_id")

            # Query positions
            positions = await self._get_position_risk()
            if not positions:
                return {
                    "status": "failed",
                    "reason": "Could not query positions from AsterDEX"
                }

            # Find open position
            target_position = None
            for pos in positions:
                position_amt = float(pos.get("positionAmt", 0))
                if position_amt != 0:
                    target_position = pos
                    break

            if not target_position:
                return {
                    "status": "failed",
                    "reason": "No open position found to close"
                }

            symbol = target_position.get("symbol")
            position_amt = float(target_position.get("positionAmt", 0))
            close_side = "SELL" if position_amt > 0 else "BUY"
            close_quantity = abs(position_amt)

            self._log.info(f"Closing position: {symbol} {close_side} {close_quantity}")

            # Cancel SL/TP orders
            if sl_order_id:
                await self._cancel_order(symbol, sl_order_id)
            if tp_order_id:
                await self._cancel_order(symbol, tp_order_id)

            # Place close order
            close_result = await self._place_market_order(
                symbol=symbol,
                side=close_side,
                quantity=close_quantity,
                leverage=1
            )

            if not close_result or "orderId" not in close_result:
                return {
                    "status": "failed",
                    "reason": "Failed to place market close order"
                }

            close_order_id = str(close_result["orderId"])

            # Mark trade as closed
            await self._mark_trade_closed(batch_id)

            self._log.info(f"Position closed successfully: {close_order_id}")

            # Log activity to timeline
            try:
                # Fetch P&L from Aster API user trades
                user_trades = await self.get_user_trades(limit=100)
                matched_trade = next((t for t in (user_trades or []) if str(t.get('id', '')) == batch_id), None)

                pnl = 0.0
                pnl_pct = 0.0
                if matched_trade:
                    pnl = float(matched_trade.get('realizedPnl', 0))
                    # Calculate percentage if we have entry data
                    qty = float(matched_trade.get('qty', 0))
                    price = float(matched_trade.get('price', 0))
                    if qty > 0 and price > 0:
                        position_value = qty * price
                        pnl_pct = (pnl / position_value) * 100 if position_value > 0 else 0

                # Determine activity type based on P&L
                activity_type = 'trade_win' if pnl >= 0 else 'trade_loss'

                # Get config_id from trade record for activity log
                config_id = trade_record.get('config_id')

                log_activity_safe(
                    config_id=config_id,
                    user_id=user_id,
                    activity_type=activity_type,
                    activity_source='aster_service',
                    summary=f"Closed {symbol}: {'+' if pnl >= 0 else ''}{pnl:.2f} ({pnl_pct:.1f}%)",
                    details={
                        'symbol': symbol,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'quantity': close_quantity,
                        'close_reason': 'manual',
                        'close_order_id': close_order_id
                    },
                    trade_id=batch_id,
                    trade_type='aster',
                    related_symbol=symbol,
                    importance=9
                )
                self._log.info(f"Activity logged for close {batch_id}")
            except Exception as e:
                self._log.warning(f"Failed to log close activity (non-critical): {e}")

            return {
                "status": "success",
                "close_order_id": close_order_id,
                "symbol": symbol,
                "quantity": close_quantity
            }

        except Exception as e:
            self._log.error(f"Error closing position: {e}", exc_info=True)
            return {
                "status": "failed",
                "reason": str(e)
            }

    async def _get_trade_record(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get trade record from live_trades table."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT batch_id, config_id, decision_id, stop_loss_order_id, take_profit_order_id, created_at
                        FROM live_trades
                        WHERE batch_id = %s AND provider = 'aster'
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
                            "created_at": row[5]
                        }
                    return None
        except Exception as e:
            self._log.error(f"Error getting trade record: {e}")
            return None

    async def _get_order_status(self, symbol: str, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order status from Aster API.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            order_id: Order ID to query

        Returns:
            Order info dict with 'status' field: "NEW", "FILLED", "CANCELED", etc.
            None on error.
        """
        nonce = math.trunc(time.time() * 1000000)

        params = {
            "symbol": symbol,
            "orderId": order_id
        }

        signed_params = self._generate_signature(params, nonce)

        url = f"{self.base_url}/fapi/v3/order"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ggbots/1.0"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=signed_params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        order_info = await response.json()
                        return order_info
                    else:
                        error_text = await response.text()
                        self._log.warning(f"Failed to get order status {order_id}: {response.status} - {error_text}")
                        return None
        except Exception as e:
            self._log.error(f"Exception getting order status: {e}")
            return None

    async def _cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order by ID."""
        nonce = math.trunc(time.time() * 1000000)

        params = {
            "symbol": symbol,
            "orderId": order_id
        }

        signed_params = self._generate_signature(params, nonce)

        url = f"{self.base_url}/fapi/v3/order"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ggbots/1.0"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    url,
                    data=signed_params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        self._log.info(f"Canceled order {order_id}")
                        return True
                    else:
                        error_text = await response.text()
                        self._log.warning(f"Failed to cancel order {order_id}: {response.status} - {error_text}")
                        return False
        except Exception as e:
            self._log.error(f"Exception canceling order: {e}")
            return False

    async def _mark_trade_closed(self, batch_id: str) -> None:
        """Update live_trades record with closed_at timestamp."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE live_trades
                        SET closed_at = NOW()
                        WHERE batch_id = %s AND provider = 'aster'
                    """, (batch_id,))
                    conn.commit()
                    self._log.info(f"Marked trade {batch_id} as closed")
        except Exception as e:
            self._log.error(f"Error marking trade closed: {e}")

    async def get_account_metrics(self, config_id: str, user_id: str) -> Dict[str, Any]:
        """Get account metrics from AsterDEX."""
        try:
            account_data = await self._get_account_balance()
            if not account_data:
                return {
                    "status": "failed",
                    "reason": "Could not query account balance"
                }

            positions = await self.get_open_positions(config_id)
            total_unrealized_pnl = sum(pos.get("unrealized_pnl", 0) for pos in positions)

            # Extract account totals from /fapi/v3/account response
            available_balance = float(account_data.get("availableBalance", 0))
            position_margin = float(account_data.get("totalPositionInitialMargin", 0))
            total_equity = available_balance + position_margin

            return {
                "status": "success",
                "balance": total_equity,  # TOTAL EQUITY for charts (available + locked)
                "available_balance": available_balance,  # Free cash (for trading checks)
                "total_unrealized_pnl": total_unrealized_pnl,  # From positions endpoint
                "positions_count": len(positions),
                "positions": positions
            }

        except Exception as e:
            self._log.error(f"Error getting account metrics: {e}", exc_info=True)
            return {
                "status": "failed",
                "reason": str(e)
            }

    async def _get_account_balance(self) -> Optional[Dict[str, Any]]:
        """
        Query account info via GET /fapi/v3/account.

        Returns account object with:
        - totalWalletBalance: Total wallet balance across all assets (in USDT)
        - totalUnrealizedProfit: Total unrealized profit (in USDT)
        - totalMarginBalance: totalWalletBalance + totalUnrealizedProfit
        - availableBalance: Available balance for new orders
        - assets: Array of individual asset balances
        """
        nonce = math.trunc(time.time() * 1000000)
        params = {}

        signed_params = self._generate_signature(params, nonce)

        url = f"{self.base_url}/fapi/v3/account"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=signed_params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self._log.error(f"Account query failed: {response.status} - {error_text}")
                        return None
        except Exception as e:
            self._log.error(f"Exception querying account: {e}")
            return None

    async def get_user_trades(self, symbol: Optional[str] = None, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Query user trade history via GET /fapi/v3/userTrades.

        Returns trades with realized P&L for completed trades.
        Used by Activity Timeline to reconstruct cumulative P&L.

        Args:
            symbol: Optional symbol filter (e.g., "BTCUSDT")
            limit: Max trades to return (default 100, max 1000)

        Returns:
            List of trades with fields:
            - id: Trade ID
            - symbol: Trading pair
            - orderId: Order ID
            - side: BUY or SELL
            - price: Execution price
            - qty: Quantity
            - realizedPnl: Realized P&L for this trade
            - time: Execution timestamp (ms)
        """
        nonce = math.trunc(time.time() * 1000000)
        params = {'limit': str(min(limit, 1000))}
        if symbol:
            params['symbol'] = symbol

        signed_params = self._generate_signature(params, nonce)
        url = f"{self.base_url}/fapi/v3/userTrades"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=signed_params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self._log.error(f"User trades query failed: {response.status} - {error_text}")
                        return None
        except Exception as e:
            self._log.error(f"Exception querying user trades: {e}")
            return None

    async def get_income_history(
        self,
        income_type: str = "REALIZED_PNL",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get income history (realized P&L, funding fees, etc.) via GET /fapi/v3/income.

        This endpoint provides complete P&L history, unlike userTrades which only shows recent trades.
        Essential for accurate balance series reconstruction.

        Args:
            income_type: "REALIZED_PNL", "FUNDING_FEE", "COMMISSION", etc. (default: "REALIZED_PNL")
            start_time: Timestamp in ms to get funding from (INCLUSIVE)
            end_time: Timestamp in ms to get funding until (INCLUSIVE)
            limit: Max records (default 1000, max 1000)

        Returns:
            List of income records:
            - symbol: Trading symbol (e.g., "BTCUSDT")
            - incomeType: Type of income ("REALIZED_PNL", etc.)
            - income: Income amount (can be negative for losses)
            - asset: Asset symbol (e.g., "USDT")
            - time: Timestamp in ms
            - tranId: Transaction ID (unique per incomeType)
            - tradeId: Trade ID if applicable
        """
        nonce = math.trunc(time.time() * 1000000)
        params = {
            'incomeType': income_type,
            'limit': str(min(limit, 1000))
        }

        if start_time:
            params['startTime'] = str(start_time)
        if end_time:
            params['endTime'] = str(end_time)

        signed_params = self._generate_signature(params, nonce)
        url = f"{self.base_url}/fapi/v3/income"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=signed_params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self._log.error(f"Income history query failed: {response.status} - {error_text}")
                        return None
        except Exception as e:
            self._log.error(f"Exception querying income history: {e}")
            return None

    async def get_open_orders(self, symbol: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get all open orders for the account.

        Args:
            symbol: Optional symbol filter (e.g., "BTCUSDT")

        Returns:
            List of open orders with details:
            - orderId: Order ID
            - symbol: Trading pair
            - side: BUY or SELL
            - type: Order type (LIMIT, STOP_MARKET, TAKE_PROFIT_MARKET, etc.)
            - origQty: Original quantity
            - price: Limit price (for limit orders)
            - stopPrice: Trigger price (for stop orders)
            - time: Order creation timestamp (ms)
            - updateTime: Last update timestamp (ms)
        """
        nonce = math.trunc(time.time() * 1000000)
        params = {}
        if symbol:
            params['symbol'] = symbol

        signed_params = self._generate_signature(params, nonce)
        url = f"{self.base_url}/fapi/v3/openOrders"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=signed_params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self._log.error(f"Open orders query failed: {response.status} - {error_text}")
                        return None
        except Exception as e:
            self._log.error(f"Exception querying open orders: {e}")
            return None

    async def cancel_order(self, symbol: str, order_id: str, user_id: str, config_id: str) -> Dict[str, Any]:
        """
        Cancel a specific order (public method for agent/API use).

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            order_id: Order ID to cancel
            user_id: User ID for activity logging
            config_id: Config ID for activity logging

        Returns:
            Dict with status and details
        """
        success = await self._cancel_order(symbol, order_id)

        if success:
            # Log activity
            log_activity_safe(
                config_id=config_id,
                user_id=user_id,
                activity_type='order_cancelled',
                activity_source='aster_service',
                summary=f"Cancelled order {order_id} for {symbol}",
                details={
                    'symbol': symbol,
                    'order_id': order_id
                },
                trade_type='aster',
                related_symbol=symbol,
                importance=5
            )

            return {
                "status": "success",
                "message": f"Order {order_id} cancelled successfully"
            }
        else:
            return {
                "status": "failed",
                "message": f"Failed to cancel order {order_id}"
            }
