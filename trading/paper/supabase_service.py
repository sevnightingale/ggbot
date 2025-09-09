"""
Supabase Paper Trading Service

Core execution engine for paper trading using Hummingbot API market data and Supabase for persistence.
Handles trade execution, position tracking, and portfolio management via Supabase REST API.
"""

import os
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from dotenv import load_dotenv
from supabase import create_client, Client

from core.common.logger import logger
from core.symbols.standardizer import UniversalSymbolStandardizer
from core.config import config_repo, BotConfig, PositionSizingMethod
from core.domain.models.account import Account
from core.domain.models.value_objects import Money, Symbol
from core.domain.repositories.supabase_account_repository import supabase_account_repo
from .market_data import MarketDataAdapter, MarketPrice

# Load environment variables
load_dotenv()


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
        self.market_data = MarketDataAdapter()
        self.symbol_standardizer = UniversalSymbolStandardizer()
        self.account_repo = supabase_account_repo
        
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
        
        Args:
            config: Bot configuration with position sizing settings
            confidence: Confidence score from Decision Module (0.0-1.0)
            account_balance: Current account balance (float or Decimal)
            
        Returns:
            Position size in USD
        """
        # Convert Decimal to float for calculations
        balance = float(account_balance) if isinstance(account_balance, Decimal) else account_balance
        
        # Use config-based position sizing
        position_size = config.get_position_size(confidence, balance)
        
        # Minimum position size of $10
        position_size = max(position_size, 10.0)
        
        # Don't exceed available balance
        position_size = min(position_size, balance * 0.95)  # Keep 5% buffer
        
        sizing_method = config.trading.position_sizing.method.value
        logger.debug(f"Position sizing ({sizing_method}): confidence={confidence:.3f}, balance=${balance:,}, size=${position_size:.2f}")
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
    
    async def execute_trade_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute paper trade from Decision Module intent.
        
        Args:
            intent: Trade intent from Decision Module
            
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
                market_price = await self.market_data.get_current_price(symbol)
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
            
            # Calculate position size using configuration
            position_size_usd = self._calculate_position_size(config, confidence, float(account.current_balance.amount))
            
            # Calculate fees
            fees = self._calculate_fees(position_size_usd)
            
            # Reserve balance for the trade (includes fees)
            trade_cost = Money(amount=Decimal(str(position_size_usd + fees)), currency="USD")
            try:
                account.reserve_balance(trade_cost)
                account.update_position_count(1)  # Open new position
            except ValueError as e:
                return {
                    "status": "rejected",
                    "reason": f"Cannot reserve balance: {str(e)}",
                    "trade_id": None
                }
            
            # Get leverage from config
            leverage = config.trading.leverage
            
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
                    'unrealized_pnl': 0.0,
                    'status': 'open',
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
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
                market_price = await self.market_data.get_current_price(trade["symbol"])
                close_price = market_price.mid
            
            # Calculate P&L
            entry_price = float(trade["entry_price"])
            size_usd = float(trade["size_usd"])
            side = trade["side"]
            
            # Calculate size in contracts from USD size
            size_contracts = size_usd / entry_price
            
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
                'closed_at': datetime.now(timezone.utc).isoformat()
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
                # Return original position size to balance
                original_size_usd = float(trade["size_usd"])
                account.release_balance(Money(amount=Decimal(str(original_size_usd)), currency="USD"))
                
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
    
    async def update_position_prices(self, config_id: Optional[str] = None) -> int:
        """
        Update current prices and unrealized P&L for open positions.
        
        Args:
            config_id: Update positions for specific config (all if None)
            
        Returns:
            Number of positions updated
        """
        try:
            # Get open positions
            if config_id:
                response = self.supabase.table('paper_trades').select("trade_id, symbol, side, entry_price, size_usd, stop_loss, take_profit").eq('config_id', config_id).eq('status', 'open').execute()
            else:
                response = self.supabase.table('paper_trades').select("trade_id, symbol, side, entry_price, size_usd, stop_loss, take_profit").eq('status', 'open').execute()
            
            positions = response.data
            if not positions:
                return 0
            
            # Get unique symbols for batch price fetch
            symbols = list(set(pos["symbol"] for pos in positions))
            prices = await self.market_data.get_multiple_prices(symbols)
            
            updated_count = 0
            positions_to_close = []
            
            # Update each position
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
                
                # Calculate size in contracts
                size_contracts = size_usd / entry_price
                
                if side == "long":
                    unrealized_pnl = (current_price - entry_price) * size_contracts
                else:  # short
                    unrealized_pnl = (entry_price - current_price) * size_contracts
                
                # Check for stop loss/take profit triggers
                should_close = None
                if pos["stop_loss"] and ((side == "long" and current_price <= pos["stop_loss"]) or 
                                        (side == "short" and current_price >= pos["stop_loss"])):
                    should_close = "stop_loss"
                elif pos["take_profit"] and ((side == "long" and current_price >= pos["take_profit"]) or
                                            (side == "short" and current_price <= pos["take_profit"])):
                    should_close = "take_profit"
                
                if should_close:
                    positions_to_close.append((pos["trade_id"], should_close, current_price))
                else:
                    # Update position with current price and P&L
                    update_data = {
                        'current_price': current_price,
                        'unrealized_pnl': unrealized_pnl
                    }
                    
                    self.supabase.table('paper_trades').update(update_data).eq('trade_id', pos['trade_id']).execute()
                
                updated_count += 1
            
            # Close triggered positions
            for trade_id, reason, close_price in positions_to_close:
                await self.close_position(trade_id, reason, close_price)
                logger.info(f"Auto-closed position {trade_id} due to {reason} trigger")
            
            if updated_count > 0:
                logger.debug(f"Updated {updated_count} paper positions, closed {len(positions_to_close)} triggered positions")
            
            return updated_count
                    
        except Exception as e:
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
            md_health = await self.market_data.health_check()
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