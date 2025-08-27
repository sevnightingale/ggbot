"""
Paper Trading Service

Core execution engine for paper trading using Hummingbot API market data.
Handles trade execution, position tracking, and portfolio management.
"""

import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
from core.common.logger import logger
from core.symbols.standardizer import UniversalSymbolStandardizer
from .market_data import MarketDataAdapter, MarketPrice


class PaperTradingService:
    """
    Core paper trading execution service.
    
    Handles trade execution from Decision Module intents, manages paper accounts,
    tracks positions with real-time P&L, and enforces risk management rules.
    """
    
    def __init__(self):
        self.market_data = MarketDataAdapter()
        self.symbol_standardizer = UniversalSymbolStandardizer()
        
        # Configuration (could be moved to env vars)
        self.initial_balance = 10000.00
        self.max_position_pct = 0.10  # 10% of balance per trade
        self.taker_fee = 0.0006  # 0.06% taker fee
        self.max_leverage = 10
        self.max_positions = 5
    
    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
    
    async def get_or_create_paper_account(self, config_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get existing paper account or create new one for config_id.
        
        Args:
            config_id: Configuration ID
            user_id: User ID
            
        Returns:
            Paper account data with current balance and statistics
        """
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if account exists
                cur.execute("""
                    SELECT * FROM paper_accounts 
                    WHERE config_id = %s AND user_id = %s
                """, (config_id, user_id))
                
                account = cur.fetchone()
                
                if account:
                    logger.debug(f"Found existing paper account for config {config_id}")
                    return dict(account)
                
                # Create new account
                cur.execute("""
                    INSERT INTO paper_accounts 
                    (config_id, user_id, initial_balance, current_balance, total_pnl, 
                     open_positions, total_trades, win_trades, loss_trades)
                    VALUES (%s, %s, %s, %s, 0, 0, 0, 0, 0)
                    RETURNING *
                """, (config_id, user_id, self.initial_balance, self.initial_balance))
                
                new_account = cur.fetchone()
                conn.commit()
                
                logger.info(f"Created new paper account for config {config_id} with ${self.initial_balance:,} starting balance")
                return dict(new_account)
    
    def _calculate_position_size(self, confidence: float, account_balance: Union[float, Decimal]) -> float:
        """
        Calculate position size based on confidence score and account balance.
        
        Args:
            confidence: Confidence score from Decision Module (0.0-1.0)
            account_balance: Current account balance (float or Decimal)
            
        Returns:
            Position size in USD
        """
        # Convert Decimal to float for calculations
        balance = float(account_balance) if isinstance(account_balance, Decimal) else account_balance
        max_position_usd = balance * self.max_position_pct
        position_size = confidence * max_position_usd
        
        # Minimum position size of $10
        position_size = max(position_size, 10.0)
        
        logger.debug(f"Position sizing: confidence={confidence:.3f}, balance=${balance:,}, size=${position_size:.2f}")
        return position_size
    
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
            reasoning = intent.get("reasoning", "")
            
            logger.info(f"Executing paper trade intent: {action} {symbol} (confidence={confidence:.3f})")
            
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
            if account["current_balance"] < 10:
                return {
                    "status": "rejected",
                    "reason": f"Insufficient balance: ${account['current_balance']:.2f}",
                    "trade_id": None
                }
            
            # Check position limits
            if account["open_positions"] >= self.max_positions:
                return {
                    "status": "rejected",
                    "reason": f"Maximum positions reached: {self.max_positions}",
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
            
            # Calculate position size
            position_size_usd = self._calculate_position_size(confidence, account["current_balance"])
            
            # Calculate fees
            fees = self._calculate_fees(position_size_usd)
            
            # Calculate position size in contracts (for crypto, this is the same as USD size)
            size_contracts = position_size_usd / entry_price
            
            # Create trade record
            trade_id = str(uuid.uuid4())
            
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Insert trade record
                    cur.execute("""
                        INSERT INTO paper_trades 
                        (trade_id, account_id, config_id, user_id, decision_id, symbol, side, 
                         entry_price, current_price, size_usd, size_contracts, leverage,
                         unrealized_pnl, fees, status, stop_loss, take_profit, 
                         confidence_score, reasoning)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        trade_id, account["account_id"], config_id, user_id, decision_id, 
                        symbol, action, entry_price, entry_price, position_size_usd, 
                        size_contracts, 1, 0.0, fees, "open", stop_loss, take_profit, 
                        confidence, reasoning
                    ))
                    
                    # Create entry order record
                    cur.execute("""
                        INSERT INTO paper_orders
                        (trade_id, order_type, side, filled_price, size, fees)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        trade_id, "market", "buy" if action == "long" else "sell",
                        entry_price, size_contracts, fees
                    ))
                    
                    # Update account balance and stats
                    cur.execute("""
                        UPDATE paper_accounts 
                        SET current_balance = current_balance - %s,
                            open_positions = open_positions + 1,
                            total_trades = total_trades + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE account_id = %s
                    """, (position_size_usd + fees, account["account_id"]))
                    
                    conn.commit()
            
            logger.info(f"Paper trade executed: {trade_id} - {action} {symbol} @ ${entry_price:.2f} (${position_size_usd:.2f})")
            
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
                "account_balance": float(account["current_balance"]) - position_size_usd - fees
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
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get trade details
                    cur.execute("""
                        SELECT * FROM paper_trades 
                        WHERE trade_id = %s AND status = 'open'
                    """, (trade_id,))
                    
                    trade = cur.fetchone()
                    if not trade:
                        return {
                            "status": "failed",
                            "reason": "Trade not found or already closed"
                        }
                    
                    # Get current price if not provided
                    if close_price is None:
                        market_price = await self.market_data.get_current_price(trade["symbol"])
                        close_price = market_price.mid
                    
                    # Calculate P&L
                    entry_price = float(trade["entry_price"])
                    size_contracts = float(trade["size_contracts"])
                    side = trade["side"]
                    
                    if side == "long":
                        pnl = (close_price - entry_price) * size_contracts
                    else:  # short
                        pnl = (entry_price - close_price) * size_contracts
                    
                    # Calculate close fees
                    close_size_usd = close_price * size_contracts
                    close_fees = self._calculate_fees(close_size_usd)
                    total_fees = float(trade["fees"]) + close_fees
                    
                    # Net P&L after fees
                    net_pnl = pnl - close_fees
                    
                    # Update trade record
                    cur.execute("""
                        UPDATE paper_trades 
                        SET status = 'closed', 
                            current_price = %s,
                            realized_pnl = %s,
                            fees = %s,
                            close_reason = %s,
                            closed_at = CURRENT_TIMESTAMP
                        WHERE trade_id = %s
                    """, (close_price, net_pnl, total_fees, reason, trade_id))
                    
                    # Create close order record
                    cur.execute("""
                        INSERT INTO paper_orders
                        (trade_id, order_type, side, filled_price, size, fees)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        trade_id, reason if reason in ["stop_loss", "take_profit"] else "market",
                        "sell" if side == "long" else "buy", close_price, size_contracts, close_fees
                    ))
                    
                    # Update account balance and stats
                    original_size_usd = float(trade["size_usd"])
                    balance_return = original_size_usd + net_pnl  # Original position + P&L
                    
                    win_increment = 1 if net_pnl > 0 else 0
                    loss_increment = 1 if net_pnl <= 0 else 0
                    
                    cur.execute("""
                        UPDATE paper_accounts 
                        SET current_balance = current_balance + %s,
                            total_pnl = total_pnl + %s,
                            open_positions = open_positions - 1,
                            win_trades = win_trades + %s,
                            loss_trades = loss_trades + %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE account_id = %s
                    """, (balance_return, net_pnl, win_increment, loss_increment, trade["account_id"]))
                    
                    conn.commit()
            
            logger.info(f"Paper position closed: {trade_id} - {reason} @ ${close_price:.2f} (P&L: ${net_pnl:.2f})")
            
            return {
                "status": "closed",
                "trade_id": trade_id,
                "close_price": close_price,
                "realized_pnl": net_pnl,
                "close_reason": reason,
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
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM paper_trades 
                    WHERE config_id = %s AND status = 'open'
                    ORDER BY opened_at DESC
                """, (config_id,))
                
                return [dict(row) for row in cur.fetchall()]
    
    async def get_account_summary(self, config_id: str) -> Dict[str, Any]:
        """Get paper account summary with performance stats"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM paper_trading_summary 
                    WHERE config_id = %s
                """, (config_id,))
                
                summary = cur.fetchone()
                if summary:
                    return dict(summary)
                else:
                    return {"error": "Account not found"}
    
    async def update_position_prices(self, config_id: Optional[str] = None) -> int:
        """
        Update current prices and unrealized P&L for open positions.
        
        Args:
            config_id: Update positions for specific config (all if None)
            
        Returns:
            Number of positions updated
        """
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get open positions
                    if config_id:
                        cur.execute("""
                            SELECT trade_id, symbol, side, entry_price, size_contracts, stop_loss, take_profit
                            FROM paper_trades 
                            WHERE config_id = %s AND status = 'open'
                        """, (config_id,))
                    else:
                        cur.execute("""
                            SELECT trade_id, symbol, side, entry_price, size_contracts, stop_loss, take_profit
                            FROM paper_trades 
                            WHERE status = 'open'
                        """)
                    
                    positions = cur.fetchall()
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
                        size_contracts = float(pos["size_contracts"])
                        side = pos["side"]
                        
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
                            cur.execute("""
                                UPDATE paper_trades 
                                SET current_price = %s, 
                                    unrealized_pnl = %s,
                                    last_updated = CURRENT_TIMESTAMP
                                WHERE trade_id = %s
                            """, (current_price, unrealized_pnl, pos["trade_id"]))
                        
                        updated_count += 1
                    
                    conn.commit()
                    
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
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM paper_trades 
                    WHERE config_id = %s 
                    ORDER BY opened_at DESC 
                    LIMIT %s
                """, (config_id, limit))
                
                return [dict(row) for row in cur.fetchall()]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        health = {
            "service": "paper_trading",
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
            
            # Check database
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM paper_accounts")
                    account_count = cur.fetchone()[0]
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
    service = PaperTradingService()
    return await service.execute_trade_intent(intent)


async def get_paper_account_summary(config_id: str) -> Dict[str, Any]:
    """Quick account summary lookup"""
    service = PaperTradingService()
    return await service.get_account_summary(config_id)