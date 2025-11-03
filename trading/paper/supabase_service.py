"""
Supabase Paper Trading Service

Core execution engine for paper trading using WebSocket live prices and Supabase for persistence.
Handles trade execution, position tracking, and portfolio management via Supabase REST API.
"""

import os
import uuid
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from dotenv import load_dotenv
from supabase import create_client, Client
from psycopg2.extras import execute_values

from core.common.logger import logger
from core.common.db import get_db_connection
from core.symbols.standardizer import UniversalSymbolStandardizer
from core.config import config_repo, BotConfig, PositionSizingMethod
from core.domain.models.account import Account
from core.domain.models.value_objects import Money, Symbol
from core.domain.repositories.supabase_account_repository import supabase_account_repo
from .types import MarketPrice
from .live_price_service import LivePriceService

# Load environment variables
load_dotenv()


class ErrorRateLimiter:
    """Simple rate limiter for error logging to prevent spam."""

    def __init__(self, interval_seconds: int = 60):
        self.interval = interval_seconds
        self.last_logged = {}

    def should_log(self, error_key: str) -> bool:
        """Check if error should be logged based on rate limit."""
        current_time = time.time()
        last_time = self.last_logged.get(error_key, 0)

        if current_time - last_time >= self.interval:
            self.last_logged[error_key] = current_time
            return True
        return False


class SupabasePaperTradingService:
    """
    Core paper trading execution service using Supabase.
    
    Handles trade execution from Decision Module intents, manages paper accounts,
    tracks positions with real-time P&L, and enforces risk management rules.
    """
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.price_service = LivePriceService()
        self.symbol_standardizer = UniversalSymbolStandardizer()
        self.account_repo = supabase_account_repo
        self.error_limiter = ErrorRateLimiter(interval_seconds=60)  # Rate limit errors to once per minute

        # Default configuration
        self.taker_fee = 0.0006  # 0.06% taker fee
    
    async def get_or_create_paper_account(self, config_id: str, user_id: str) -> Account:
        """
        Get existing paper account or create new one for config_id.
        
        Args:
            config_id: Configuration ID
            user_id: User ID
            
        Returns:
            Account domain model with current balance and statistics
        """
        return await self.account_repo.get_or_create(
            config_id=config_id, 
            user_id=user_id,
            initial_balance=Money(amount=Decimal("10000.00"), currency="USD")
        )
    
    def _calculate_position_size(self, config: BotConfig, confidence: float, account_balance: Union[float, Decimal]) -> float:
        """
        Calculate position size based on configuration, confidence score, and account balance.

        Position sizing settings represent margin/risk, which is multiplied by leverage
        to get the final position size.

        Args:
            config: Bot configuration with position sizing settings
            confidence: Confidence score from Decision Module (0.0-1.0)
            account_balance: Current account balance (float or Decimal)

        Returns:
            Position size in USD (already includes leverage)
        """
        # Convert Decimal to float for calculations
        balance = float(account_balance) if isinstance(account_balance, Decimal) else account_balance

        # Get position size (margin × leverage) from config
        position_size = config.get_position_size(confidence, balance)
        leverage = config.trading.leverage

        # Calculate the margin required for this position
        margin_required = position_size / leverage

        # Cap margin at 95% of balance (keep 5% buffer for fees)
        max_margin = balance * 0.95
        if margin_required > max_margin:
            margin_required = max_margin
            position_size = margin_required * leverage

        # Minimum position size of $10
        position_size = max(position_size, 10.0)

        sizing_method = config.trading.position_sizing.method.value
        logger.debug(f"Position sizing ({sizing_method}): confidence={confidence:.3f}, balance=${balance:,}, margin=${margin_required:.2f}, size=${position_size:.2f}, leverage={leverage}x")
        return position_size
    
    async def _check_position_limits(self, config: BotConfig, config_id: str, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if new position would exceed configured limits.
        
        Args:
            config: Bot configuration with risk management settings
            config_id: Configuration ID
            user_id: User ID
            
        Returns:
            (can_open_position, reason_if_not)
        """
        max_positions = config.trading.risk_management.max_positions
        
        try:
            # Count current open positions
            response = self.supabase.table('paper_trades').select("count", count="exact").eq('config_id', config_id).eq('user_id', user_id).eq('status', 'open').execute()
            
            open_positions = response.count or 0
            
            if open_positions >= max_positions:
                return False, f"Maximum positions limit reached ({open_positions}/{max_positions})"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to check position limits: {str(e)}")
            return False, f"Failed to check position limits: {str(e)}"
    
    def _apply_default_risk_levels(self, config: BotConfig, intent: Dict[str, Any], entry_price: float) -> Dict[str, Any]:
        """
        Apply default stop loss and take profit if not specified in intent.
        
        Args:
            config: Bot configuration with default risk levels
            intent: Trade intent (modified in place)
            entry_price: Entry price for the trade
            
        Returns:
            Modified intent with default risk levels applied
        """
        side = intent.get("action", "").lower()
        
        # Apply default stop loss if not provided
        if not intent.get("stop_loss_price") and config.trading.risk_management.default_stop_loss_percent:
            default_stop = config.get_default_stop_loss_price(entry_price, side)
            if default_stop:
                intent["stop_loss_price"] = default_stop
                logger.debug(f"Applied default stop loss: ${default_stop:.2f}")
        
        # Apply default take profit if not provided
        if not intent.get("take_profit_price") and config.trading.risk_management.default_take_profit_percent:
            default_tp = config.get_default_take_profit_price(entry_price, side)
            if default_tp:
                intent["take_profit_price"] = default_tp
                logger.debug(f"Applied default take profit: ${default_tp:.2f}")
        
        return intent
    
    def _calculate_fees(self, size_usd: float) -> float:
        """Calculate trading fees"""
        return size_usd * self.taker_fee

    def _calculate_liquidation_price(self, entry_price: float, side: str, margin_used: float, position_size_usd: float) -> float:
        """
        Calculate liquidation price based on margin and position size.

        Args:
            entry_price: Entry price of the position
            side: Trade side ('long' or 'short')
            margin_used: Total margin reserved (includes fees)
            position_size_usd: Total position size in USD

        Returns:
            Liquidation price
        """
        # Calculate the margin ratio (how much of position is margin)
        margin_ratio = margin_used / position_size_usd

        # For LONG: liquidation when price drops by margin_ratio
        # For SHORT: liquidation when price rises by margin_ratio
        if side == "long":
            liquidation_price = entry_price * (1 - margin_ratio)
        else:  # short
            liquidation_price = entry_price * (1 + margin_ratio)

        logger.debug(f"Calculated liquidation price for {side}: ${liquidation_price:.2f} (entry: ${entry_price:.2f}, margin ratio: {margin_ratio:.2%})")
        return liquidation_price
    
    async def execute_trade_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute paper trade from Decision Module intent.

        Args:
            intent: Trade intent from Decision Module with optional overrides:
                - config_id: Bot configuration ID
                - user_id: User ID
                - symbol: Trading symbol
                - action: "long" or "short"
                - confidence: 0.0-1.0
                - decision_id: Optional decision UUID
                - stop_loss_price: Optional stop loss price
                - take_profit_price: Optional take profit price
                - position_size_override: Optional position size in base asset
                - position_size_usd_override: Optional position size in USD notional
                - leverage_override: Optional leverage multiplier

        Returns:
            Execution result with trade details
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
            # Note: reasoning is tracked in decisions table, not in paper_trades
            
            logger.info(f"Executing paper trade intent: {action} {symbol} (confidence={confidence:.3f})")
            
            # Load configuration
            config = config_repo.get_config(config_id, user_id)
            if not config:
                return {
                    "status": "failed",
                    "reason": f"Configuration not found: {config_id}",
                    "trade_id": None
                }
            
            # Validate action
            if action not in ["long", "short"]:
                return {
                    "status": "rejected",
                    "reason": f"Invalid action: {action}. Must be 'long' or 'short'",
                    "trade_id": None
                }
            
            # Get or create paper account
            account = await self.get_or_create_paper_account(config_id, user_id)
            
            # Check if we have enough balance
            min_balance = Money(amount=Decimal("10.00"), currency="USD")
            if not account.can_afford_trade(min_balance):
                return {
                    "status": "rejected",
                    "reason": f"Insufficient balance: {account.current_balance}",
                    "trade_id": None
                }
            
            # Check position limits using config
            can_open, limit_reason = await self._check_position_limits(config, config_id, user_id)
            if not can_open:
                return {
                    "status": "rejected",
                    "reason": limit_reason,
                    "trade_id": None
                }
            
            # Get current market price
            try:
                market_price = await self.price_service.get_current_price(symbol)
                entry_price = market_price.mid
            except Exception as e:
                logger.error(f"Failed to get market price for {symbol}: {e}")
                return {
                    "status": "failed",
                    "reason": f"Price fetch failed: {str(e)}",
                    "trade_id": None
                }
            
            # Apply default risk levels if not provided
            intent = self._apply_default_risk_levels(config, intent, entry_price)
            stop_loss = intent.get("stop_loss_price")  # Updated with defaults
            take_profit = intent.get("take_profit_price")  # Updated with defaults

            # Calculate position size - with override support for agents
            if position_size_usd_override:
                # Direct USD override (e.g., agent says "trade $500 worth")
                position_size_usd = float(position_size_usd_override)
                logger.info(f"Using position size USD override: ${position_size_usd:.2f}")
            elif position_size_override:
                # Base asset quantity override (e.g., agent says "trade 0.005 BTC")
                # Convert to USD using current price
                position_size_usd = float(position_size_override) * entry_price
                logger.info(f"Using position size override: {position_size_override} * ${entry_price:.2f} = ${position_size_usd:.2f}")
            else:
                # Use config-based position sizing
                position_size_usd = self._calculate_position_size(config, confidence, float(account.current_balance.amount))

            # Get leverage - with override support
            if leverage_override:
                leverage = int(leverage_override)
                leverage = max(1, leverage)  # Minimum 1x
                logger.info(f"Using leverage override: {leverage}x")
            else:
                leverage = config.trading.leverage

            # Calculate margin required (position size / leverage)
            margin_required = position_size_usd / leverage

            # Calculate fees on the margin amount
            fees = self._calculate_fees(position_size_usd)

            # Total margin to reserve (margin + fees)
            margin_with_fees = margin_required + fees

            # Calculate liquidation price based on margin and leverage
            liquidation_price = self._calculate_liquidation_price(
                entry_price=entry_price,
                side=action,
                margin_used=margin_with_fees,
                position_size_usd=position_size_usd
            )

            # Reserve balance for the trade (margin + fees, not full position size)
            trade_cost = Money(amount=Decimal(str(margin_with_fees)), currency="USD")
            try:
                account.reserve_balance(trade_cost)
                account.update_position_count(1)  # Open new position
            except ValueError as e:
                return {
                    "status": "rejected",
                    "reason": f"Cannot reserve balance: {str(e)}",
                    "trade_id": None
                }
            
            # Calculate position size in contracts for order tracking
            # Note: paper_trades table only stores size_usd, not size_contracts
            size_contracts = position_size_usd / entry_price
            
            # Create trade record
            trade_id = str(uuid.uuid4())
            
            try:
                # Insert trade record into Supabase
                trade_data = {
                    'trade_id': trade_id,
                    'account_id': str(account.account_id),
                    'config_id': config_id,
                    'user_id': user_id,
                    'decision_id': decision_id,
                    'symbol': symbol,
                    'side': action,
                    'entry_price': entry_price,
                    'current_price': entry_price,
                    'size_usd': position_size_usd,
                    # Note: size_contracts not in schema - using size_usd/entry_price calculation
                    'leverage': leverage,
                    'margin_used': margin_with_fees,  # Store actual reserved amount for later release
                    'unrealized_pnl': 0.0,
                    'status': 'open',
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'liquidation_price': liquidation_price,
                    'confidence_score': confidence
                    # Note: reasoning field not in schema, will track separately if needed
                }
                
                response = self.supabase.table('paper_trades').insert(trade_data).execute()
                if not response.data:
                    raise Exception("Failed to insert trade record")
                
                # Create entry order record
                order_data = {
                    'trade_id': trade_id,
                    'user_id': user_id,
                    'order_type': 'market',
                    'side': 'buy' if action == 'long' else 'sell',
                    'filled_price': entry_price,
                    'size': size_contracts,  # This should match schema
                    'fees': fees
                }
                
                response = self.supabase.table('paper_orders').insert(order_data).execute()
                if not response.data:
                    logger.warning(f"Failed to create order record for trade {trade_id}")
                
            except Exception as e:
                logger.error(f"Failed to save trade records: {str(e)}")
                # Rollback account changes
                account.release_balance(trade_cost)
                account.update_position_count(-1)
                return {
                    "status": "failed",
                    "reason": f"Failed to save trade: {str(e)}",
                    "trade_id": None
                }
            
            # Save updated account state after successful database operations
            await self.account_repo.save(account)
            
            logger.info(
                f"Paper trade executed: {trade_id} - {action} {symbol} @ ${entry_price:.2f} "
                f"(${position_size_usd:.2f}) - Account balance: {account.current_balance}"
            )
            
            return {
                "status": "executed",
                "trade_id": trade_id,
                "symbol": symbol,
                "side": action,
                "entry_price": entry_price,
                "size_usd": position_size_usd,
                "size_contracts": size_contracts,
                "fees": fees,
                "confidence_score": confidence,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "account_balance": float(account.current_balance.amount)
            }
            
        except Exception as e:
            logger.error(f"Failed to execute paper trade: {e}")
            return {
                "status": "failed",
                "reason": str(e),
                "trade_id": None
            }
    
    async def close_position(self, trade_id: str, reason: str = "manual", close_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Close paper trading position.
        
        Args:
            trade_id: Trade ID to close
            reason: Reason for closure ('manual', 'stop_loss', 'take_profit')
            close_price: Override close price (uses current market price if None)
            
        Returns:
            Closure result with P&L information
        """
        try:
            # Get trade details
            response = self.supabase.table('paper_trades').select("*").eq('trade_id', trade_id).eq('status', 'open').execute()
            
            if not response.data:
                return {
                    "status": "failed",
                    "reason": "Trade not found or already closed"
                }
            
            trade = response.data[0]
            
            # Get current price if not provided
            if close_price is None:
                market_price = await self.price_service.get_current_price(trade["symbol"])
                close_price = market_price.mid
            
            # Calculate P&L
            entry_price = float(trade["entry_price"])
            size_usd = float(trade["size_usd"])
            side = trade["side"]
            leverage = int(trade.get("leverage", 1))  # Get leverage from trade

            # Calculate size in contracts from USD size
            size_contracts = size_usd / entry_price

            # Calculate P&L (size_usd is already the full leveraged position)
            if side == "long":
                pnl = (close_price - entry_price) * size_contracts
            else:  # short
                pnl = (entry_price - close_price) * size_contracts
            
            # Calculate close fees
            close_size_usd = close_price * size_contracts
            close_fees = self._calculate_fees(close_size_usd)
            
            # Get existing fees from paper_orders (entry fees)
            orders_response = self.supabase.table('paper_orders').select("fees").eq('trade_id', trade_id).execute()
            entry_fees = sum(float(order.get('fees', 0)) for order in orders_response.data)
            
            total_fees = entry_fees + close_fees
            
            # Net P&L after fees
            net_pnl = pnl - close_fees
            
            # Update trade record
            update_data = {
                'status': 'closed',
                'current_price': close_price,
                'realized_pnl': net_pnl,
                'closed_at': datetime.now(timezone.utc).isoformat(),
                'close_reason': reason
            }
            
            response = self.supabase.table('paper_trades').update(update_data).eq('trade_id', trade_id).execute()
            if not response.data:
                raise Exception("Failed to update trade record")
            
            # Create close order record
            order_data = {
                'trade_id': trade_id,
                'user_id': trade['user_id'],
                'order_type': reason if reason in ["stop_loss", "take_profit"] else "market",
                'side': 'sell' if side == 'long' else 'buy',
                'filled_price': close_price,
                'size': size_contracts,
                'fees': close_fees
            }
            
            response = self.supabase.table('paper_orders').insert(order_data).execute()
            if not response.data:
                logger.warning(f"Failed to create close order record for trade {trade_id}")
            
            # Update account using domain model
            account = await self.account_repo.get_by_config_id(
                config_id=str(trade["config_id"]), 
                user_id=str(trade["user_id"])
            )
            
            if account:
                # Return margin that was reserved (not full position size)
                margin_reserved = float(trade.get("margin_used", trade["size_usd"]))  # Fallback to size_usd for old trades
                account.release_balance(Money(amount=Decimal(str(margin_reserved)), currency="USD"))
                
                # Realize P&L and update statistics
                # Money class now properly handles negative amounts
                pnl_money = Money(amount=Decimal(str(net_pnl)), currency="USD")
                is_win = net_pnl > 0
                account.realize_pnl(pnl_money, is_win)
                
                # Update position count
                account.update_position_count(-1)
                
                # Save updated account
                await self.account_repo.save(account)
            else:
                logger.error(f"Account not found for trade {trade_id}")
            
            logger.info(f"Paper position closed: {trade_id} - {reason} @ ${close_price:.2f} (P&L: ${net_pnl:.2f})")
            
            return {
                "status": "closed",
                "trade_id": trade_id,
                "close_price": close_price,
                "realized_pnl": net_pnl,
                "fees": total_fees
            }
            
        except Exception as e:
            logger.error(f"Failed to close position {trade_id}: {e}")
            return {
                "status": "failed",
                "reason": str(e)
            }

    async def reset_account(self, config_id: str, user_id: str) -> Dict[str, Any]:
        """
        Reset paper trading account to initial state.

        Closes all open positions, resets balance to $10k, clears stats,
        but preserves trade history for analysis.

        Args:
            config_id: Configuration ID
            user_id: User ID

        Returns:
            Reset result with summary of changes
        """
        try:
            # Get all open positions
            open_positions = await self.get_open_positions(config_id)

            # Close all open positions with 'account_reset' reason
            closed_count = 0
            failed_closes = []
            for position in open_positions:
                result = await self.close_position(
                    trade_id=position['trade_id'],
                    reason='account_reset'
                )
                if result['status'] == 'closed':
                    closed_count += 1
                else:
                    failed_closes.append(position['trade_id'])

            if failed_closes:
                logger.warning(f"Failed to close {len(failed_closes)} positions during reset: {failed_closes}")

            # Reset account stats using direct SQL update
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE paper_accounts
                        SET current_balance = 10000.00,
                            total_pnl = 0.00,
                            open_positions = 0,
                            total_trades = 0,
                            win_trades = 0,
                            loss_trades = 0,
                            last_reset_at = NOW(),
                            updated_at = NOW()
                        WHERE config_id = %s AND user_id = %s
                        RETURNING account_id, current_balance, last_reset_at;
                    """, (config_id, user_id))

                    result = cur.fetchone()
                    conn.commit()

                    if not result:
                        raise Exception("Account not found or update failed")

                    account_id, new_balance, reset_at = result

            logger.info(f"Account reset successful for config_id={config_id}, closed {closed_count} positions")

            return {
                "status": "success",
                "config_id": config_id,
                "positions_closed": closed_count,
                "new_balance": float(new_balance),
                "reset_at": reset_at.isoformat() if reset_at else None,
                "message": f"Account reset to $10,000. Closed {closed_count} positions."
            }

        except Exception as e:
            logger.error(f"Failed to reset account {config_id}: {e}")
            return {
                "status": "failed",
                "reason": str(e)
            }

    async def get_open_positions(self, config_id: str) -> List[Dict[str, Any]]:
        """Get all open positions for a config_id"""
        try:
            response = self.supabase.table('paper_trades').select("*").eq('config_id', config_id).eq('status', 'open').order('opened_at', desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get open positions: {str(e)}")
            return []
    
    async def get_account_summary(self, config_id: str) -> Dict[str, Any]:
        """Get paper account summary with performance stats"""
        try:
            response = self.supabase.table('paper_accounts').select("*").eq('config_id', config_id).execute()
            
            if response.data:
                account_data = response.data[0]
                
                # Add computed fields
                win_rate = 0
                if account_data['total_trades'] > 0:
                    win_rate = (account_data['win_trades'] / account_data['total_trades']) * 100
                
                return {
                    **account_data,
                    'win_rate': win_rate,
                    'loss_rate': 100 - win_rate if account_data['total_trades'] > 0 else 0
                }
            else:
                return {"error": "Account not found"}
        except Exception as e:
            logger.error(f"Failed to get account summary: {str(e)}")
            return {"error": str(e)}
    
    async def _batch_update_positions_sql(self, updates: List[Dict[str, Any]]) -> int:
        """
        Batch update position prices using raw SQL for efficiency.

        Args:
            updates: List of dicts with trade_id, current_price, unrealized_pnl

        Returns:
            Number of positions updated
        """
        if not updates:
            return 0

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Use PostgreSQL UPDATE FROM VALUES for true batch update
                    sql = """
                    UPDATE paper_trades SET
                        current_price = v.price::numeric,
                        unrealized_pnl = v.pnl::numeric
                    FROM (VALUES %s) AS v(trade_id, price, pnl)
                    WHERE paper_trades.trade_id = v.trade_id::uuid
                    """

                    # Prepare values for execute_values
                    values = [
                        (update['trade_id'], update['current_price'], update['unrealized_pnl'])
                        for update in updates
                    ]

                    # Execute batch update (single query for all positions)
                    execute_values(cur, sql, values, template=None, page_size=100)
                    conn.commit()

                    logger.debug(f"✅ Batch updated {len(updates)} positions via raw SQL")
                    return len(updates)

        except Exception as e:
            logger.error(f"❌ Batch SQL update failed: {e}")
            raise  # Re-raise to allow fallback handling

    async def _fallback_individual_updates(self, updates: List[Dict[str, Any]]) -> int:
        """
        Fallback to individual Supabase updates if batch fails.

        Args:
            updates: List of dicts with trade_id, current_price, unrealized_pnl

        Returns:
            Number of positions successfully updated
        """
        successful_updates = 0

        for update in updates:
            try:
                self.supabase.table('paper_trades').update({
                    'current_price': update['current_price'],
                    'unrealized_pnl': update['unrealized_pnl']
                }).eq('trade_id', update['trade_id']).execute()
                successful_updates += 1
            except Exception as e:
                # Rate limit individual failures to prevent log spam
                error_key = f"individual_update_{update['trade_id']}"
                if self.error_limiter.should_log(error_key):
                    logger.warning(f"Individual update failed for {update['trade_id']}: {e}")

        logger.info(f"🔄 Fallback: {successful_updates}/{len(updates)} positions updated individually")
        return successful_updates

    async def update_position_prices(self, config_id: Optional[str] = None) -> int:
        """
        Update current prices and unrealized P&L for open positions.

        Args:
            config_id: Update positions for specific config (all if None)

        Returns:
            Number of positions updated
        """
        try:
            # Get ALL open positions (batch optimization)
            if config_id:
                response = self.supabase.table('paper_trades').select("trade_id, symbol, side, entry_price, size_usd, stop_loss, take_profit, liquidation_price").eq('config_id', config_id).eq('status', 'open').execute()
            else:
                response = self.supabase.table('paper_trades').select("trade_id, symbol, side, entry_price, size_usd, stop_loss, take_profit, liquidation_price").eq('status', 'open').execute()

            positions = response.data
            if not positions:
                return 0

            # Get unique symbols for batch price fetch
            symbols = list(set(pos["symbol"] for pos in positions))
            prices = await self.price_service.get_multiple_prices(symbols)

            batch_updates = []
            positions_to_close = []

            # Process each position and collect batch updates
            for pos in positions:
                symbol = pos["symbol"]
                if symbol not in prices:
                    logger.warning(f"No price data for {symbol}, skipping update")
                    continue

                current_price = prices[symbol].mid

                # Calculate unrealized P&L
                entry_price = float(pos["entry_price"])
                size_usd = float(pos["size_usd"])
                side = pos["side"]
                leverage = int(pos.get("leverage", 1))  # Default to 1x if not set

                # Calculate size in contracts
                size_contracts = size_usd / entry_price

                # Calculate P&L (size_usd is already the full leveraged position)
                if side == "long":
                    unrealized_pnl = (current_price - entry_price) * size_contracts
                else:  # short
                    unrealized_pnl = (entry_price - current_price) * size_contracts

                # Check for liquidation/stop loss/take profit triggers
                # CRITICAL: Check liquidation FIRST - it overrides SL/TP in real trading
                should_close = None
                if pos.get("liquidation_price") and ((side == "long" and current_price <= pos["liquidation_price"]) or
                                                     (side == "short" and current_price >= pos["liquidation_price"])):
                    should_close = "liquidation"
                    logger.warning(f"⚠️ LIQUIDATION triggered for {symbol} {side} position: price ${current_price:.2f} hit liquidation ${pos['liquidation_price']:.2f}")
                elif pos["stop_loss"] and ((side == "long" and current_price <= pos["stop_loss"]) or
                                          (side == "short" and current_price >= pos["stop_loss"])):
                    should_close = "stop_loss"
                elif pos["take_profit"] and ((side == "long" and current_price >= pos["take_profit"]) or
                                            (side == "short" and current_price <= pos["take_profit"])):
                    should_close = "take_profit"

                if should_close:
                    positions_to_close.append((pos["trade_id"], should_close, current_price))
                else:
                    # Collect update for batch processing
                    batch_updates.append({
                        'trade_id': pos['trade_id'],
                        'current_price': current_price,
                        'unrealized_pnl': unrealized_pnl
                    })

            # CRITICAL: Always close triggered positions first (trading safety)
            for trade_id, reason, close_price in positions_to_close:
                await self.close_position(trade_id, reason, close_price)
                logger.info(f"Auto-closed position {trade_id} due to {reason} trigger")

            # Then batch update remaining positions (performance optimization)
            updated_count = 0
            if batch_updates:
                try:
                    # Try batch SQL update first (single query for all positions)
                    updated_count = await self._batch_update_positions_sql(batch_updates)
                except Exception as e:
                    logger.warning(f"Batch update failed, falling back to individual updates: {e}")
                    # Fallback to individual Supabase updates if batch fails
                    updated_count = await self._fallback_individual_updates(batch_updates)

            if updated_count > 0:
                logger.debug(f"Updated {updated_count} paper positions, closed {len(positions_to_close)} triggered positions")

            return updated_count
                    
        except Exception as e:
            # Rate limit connection errors to prevent log spam
            error_key = f"update_position_prices_{type(e).__name__}"
            if self.error_limiter.should_log(error_key):
                logger.error(f"Failed to update position prices: {e}")
            return 0
    
    async def get_trade_history(self, config_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history for config_id"""
        try:
            response = self.supabase.table('paper_trades').select("*").eq('config_id', config_id).order('opened_at', desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get trade history: {str(e)}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        health = {
            "service": "supabase_paper_trading",
            "status": "unknown",
            "market_data": "unknown",
            "database": "unknown",
            "errors": []
        }
        
        try:
            # Check market data adapter
            md_health = await self.price_service.health_check()
            health["market_data"] = md_health["status"]
            if md_health["errors"]:
                health["errors"].extend(md_health["errors"])
            
            # Check Supabase database
            response = self.supabase.table('paper_accounts').select("count", count="exact").execute()
            account_count = response.count or 0
            health["database"] = "healthy"
            health["stats"] = {
                "total_accounts": account_count
            }
            
            # Overall status
            if health["market_data"] == "healthy" and health["database"] == "healthy":
                health["status"] = "healthy"
            else:
                health["status"] = "degraded"
                
        except Exception as e:
            health["status"] = "failed"
            health["database"] = "failed"
            health["errors"].append(f"Health check failed: {str(e)}")
        
        return health


# Convenience functions
async def execute_paper_trade(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Quick paper trade execution"""
    service = SupabasePaperTradingService()
    return await service.execute_trade_intent(intent)


async def get_paper_account_summary(config_id: str) -> Dict[str, Any]:
    """Quick account summary lookup"""
    service = SupabasePaperTradingService()
    return await service.get_account_summary(config_id)