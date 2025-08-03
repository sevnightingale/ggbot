"""
Trade Lifecycle Manager for position-based trade tracking.

This module manages the lifecycle of trades based on exchange positions:
- Creates trades when new positions appear
- Updates trades when positions change  
- Closes trades when positions disappear

Core principle: Exchange positions drive trade state, not the other way around.
"""

import uuid
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from psycopg2.extras import RealDictCursor

from core.common.logger import logger
from core.common.db import get_db_connection


class TradeLifecycleManager:
    """
    Simple position-based trade lifecycle management.
    
    This manager syncs database trades with actual exchange positions.
    """
    
    def __init__(self, user_id: str, exchange: str, config_id: Optional[str] = None):
        """
        Initialize the lifecycle manager.
        
        Args:
            user_id: User ID for database operations
            exchange: Exchange name (e.g., 'bitmex')
            config_id: Configuration ID for trade association (optional for backward compatibility)
        """
        self.user_id = user_id
        self.exchange = exchange
        self.config_id = config_id
        
        logger.info(f"Initialized TradeLifecycleManager for {exchange} (user: {user_id}, config: {config_id})")
    
    async def sync_positions_to_trades(self, positions: List[Dict[str, Any]], adapter) -> Dict[str, Any]:
        """
        Main sync method: update database trades to match exchange positions.
        
        Args:
            positions: List of enhanced position dictionaries from adapter
            adapter: Exchange adapter for position key generation
            
        Returns:
            Dictionary with sync results
        """
        results = {
            'trades_opened': 0,
            'trades_updated': 0, 
            'trades_closed': 0,
            'errors': []
        }
        
        try:
            # Process each position
            for position in positions:
                try:
                    await self._sync_single_position(position, adapter, results)
                except Exception as e:
                    error_msg = f"Error syncing position {position.get('symbol', 'unknown')}: {e}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Close trades for positions that no longer exist
            await self._close_missing_positions(positions, adapter, results)
            
            logger.info(f"Position sync completed: {results['trades_opened']} opened, {results['trades_updated']} updated, {results['trades_closed']} closed")
            
        except Exception as e:
            error_msg = f"Error during position sync: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    async def sync_tp_sl_orders(self) -> Dict[str, Any]:
        """
        Check TP/SL order status and update trades when orders are filled.
        
        This method:
        1. Finds active trades with open TP/SL orders
        2. Checks if any orders have been filled
        3. Updates trade exit prices and closes trades when TP/SL hits
        
        Returns:
            Dictionary with sync results
        """
        results = {
            'orders_checked': 0,
            'trades_closed_by_tp': 0,
            'trades_closed_by_sl': 0,
            'errors': []
        }
        
        try:
            # Get all active trades with TP/SL orders
            trades_with_orders = await self._get_trades_with_tp_sl_orders()
            
            for trade_info in trades_with_orders:
                try:
                    await self._check_trade_tp_sl_status(trade_info, results)
                    results['orders_checked'] += 1
                except Exception as e:
                    error_msg = f"Error checking TP/SL for trade {trade_info.get('trade_id', 'unknown')}: {e}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            if results['trades_closed_by_tp'] > 0 or results['trades_closed_by_sl'] > 0:
                logger.info(f"TP/SL sync completed: {results['trades_closed_by_tp']} TP closures, {results['trades_closed_by_sl']} SL closures")
            else:
                logger.debug(f"TP/SL sync completed: {results['orders_checked']} orders checked, no closures")
                
        except Exception as e:
            error_msg = f"Error during TP/SL sync: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    async def _sync_single_position(self, position: Dict[str, Any], adapter, results: Dict):
        """Sync a single position to database trade."""
        
        # Generate position key for database lookup
        position_key = adapter.get_position_key(position)
        
        # Find existing trade
        existing_trade = await self._find_active_trade(position_key)
        
        # Check position size
        size_contracts = position.get('size_contracts', 0)
        
        if size_contracts == 0:
            # Position closed
            if existing_trade:
                await self._close_trade(existing_trade, position)
                results['trades_closed'] += 1
        else:
            # Position active
            if existing_trade:
                await self._update_trade(existing_trade, position)
                results['trades_updated'] += 1
            else:
                await self._open_trade(position)
                results['trades_opened'] += 1
    
    async def _find_active_trade(self, position_key: tuple) -> Optional[Dict]:
        """Find active trade matching the position key."""
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build query based on position key length
            if len(position_key) == 3:
                # Net positioning (BitMEX): (account_id, exchange, symbol)
                query = """
                    SELECT trade_id, symbol, size_contracts, entry_price 
                    FROM trades 
                    WHERE user_id = %s AND account_id = %s AND exchange = %s AND symbol = %s 
                    AND side IS NULL AND trade_status = 'open'
                """
                cursor.execute(query, (self.user_id, position_key[0], position_key[1], position_key[2]))
            else:
                # Hedge positioning (Binance): (account_id, exchange, symbol, side)
                query = """
                    SELECT trade_id, symbol, side, size_contracts, entry_price 
                    FROM trades 
                    WHERE user_id = %s AND account_id = %s AND exchange = %s AND symbol = %s 
                    AND side = %s AND trade_status = 'open'
                """
                cursor.execute(query, (self.user_id, position_key[0], position_key[1], position_key[2], position_key[3]))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None
    
    async def _open_trade(self, position: Dict[str, Any]) -> str:
        """Create new trade record for position."""
        
        trade_id = str(uuid.uuid4())
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                INSERT INTO trades (
                    trade_id, user_id, account_id, exchange, symbol, side,
                    size_contracts, entry_price, mark_price, unrealized_pnl,
                    opened_at, last_updated, config_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                trade_id,
                self.user_id,
                position['account_id'],
                position['exchange'],
                position['symbol'],
                position.get('side'),
                position['size_contracts'],
                position['entry_price'],
                position['mark_price'],
                position['unrealized_pnl'],
                datetime.now(),
                datetime.now(),
                self.config_id
            )
            
            cursor.execute(query, values)
            conn.commit()
            
            logger.info(f"Opened trade {trade_id} for {position['symbol']} ({position['size_contracts']} contracts)")
            return trade_id
    
    async def _update_trade(self, trade: Dict, position: Dict[str, Any]):
        """Update existing trade with new position data."""
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                UPDATE trades SET
                    size_contracts = %s,
                    entry_price = %s,
                    mark_price = %s,
                    unrealized_pnl = %s,
                    last_updated = %s
                WHERE trade_id = %s
            """
            
            values = (
                position['size_contracts'],
                position['entry_price'],
                position['mark_price'],
                position['unrealized_pnl'],
                datetime.now(),
                trade['trade_id']
            )
            
            cursor.execute(query, values)
            conn.commit()
            
            logger.debug(f"Updated trade {trade['trade_id']} for {position['symbol']}")
    
    async def _close_trade(self, trade: Dict, final_position: Dict[str, Any]):
        """Close trade when position disappears."""
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                UPDATE trades SET
                    trade_status = 'closed',
                    closed_at = %s,
                    last_updated = %s
                WHERE trade_id = %s
            """
            
            values = (
                datetime.now(),
                datetime.now(),
                trade['trade_id']
            )
            
            cursor.execute(query, values)
            conn.commit()
            
            logger.info(f"Closed trade {trade['trade_id']} for {final_position['symbol']}")
    
    async def _close_missing_positions(self, current_positions: List[Dict], adapter, results: Dict):
        """Close trades for positions that no longer exist on exchange."""
        
        # Get all active trades for this user/exchange
        active_trades = await self._get_active_trades()
        
        # Create set of current position keys
        current_keys = set()
        for position in current_positions:
            key = adapter.get_position_key(position)
            current_keys.add(key)
        
        # Check each active trade
        for trade in active_trades:
            # Reconstruct position key from trade
            if trade.get('side'):
                trade_key = (trade['account_id'], trade['exchange'], trade['symbol'], trade['side'])
            else:
                trade_key = (trade['account_id'], trade['exchange'], trade['symbol'])
            
            # If trade key not in current positions, close it
            if trade_key not in current_keys:
                await self._close_trade(trade, {'symbol': trade['symbol']})
                results['trades_closed'] += 1
    
    async def _get_active_trades(self) -> List[Dict]:
        """Get all active trades for this user/exchange."""
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT trade_id, account_id, exchange, symbol, side, size_contracts
                FROM trades 
                WHERE user_id = %s AND exchange = %s AND trade_status = 'open'
            """
            
            cursor.execute(query, (self.user_id, self.exchange))
            return [dict(row) for row in cursor.fetchall()]
    
    async def _get_trades_with_tp_sl_orders(self) -> List[Dict]:
        """Get all active trades that have open TP/SL orders."""
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT DISTINCT 
                    t.trade_id, t.symbol, t.exchange, t.size_contracts, t.entry_price,
                    COUNT(CASE WHEN to_ord.risk_type = 'TP' THEN 1 END) as tp_orders,
                    COUNT(CASE WHEN to_ord.risk_type = 'SL' THEN 1 END) as sl_orders
                FROM trades t
                INNER JOIN trade_orders to_ord ON t.trade_id = to_ord.trade_id
                WHERE t.user_id = %s 
                    AND t.exchange = %s 
                    AND t.trade_status = 'open'
                    AND to_ord.is_risk_order = true
                    AND to_ord.status IN ('open', 'pending')
                GROUP BY t.trade_id, t.symbol, t.exchange, t.size_contracts, t.entry_price
                HAVING COUNT(*) > 0
            """
            
            cursor.execute(query, (self.user_id, self.exchange))
            return [dict(row) for row in cursor.fetchall()]
    
    async def _check_trade_tp_sl_status(self, trade_info: Dict, results: Dict):
        """Check if TP/SL orders for a specific trade have been filled."""
        
        trade_id = trade_info['trade_id']
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check for filled TP/SL orders
            query = """
                SELECT exchange_order_id, risk_type, price, size, status, filled_at
                FROM trade_orders 
                WHERE trade_id = %s 
                    AND is_risk_order = true 
                    AND status = 'filled'
                    AND filled_at IS NOT NULL
                ORDER BY filled_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (trade_id,))
            filled_order = cursor.fetchone()
            
            if filled_order:
                filled_order_dict = dict(filled_order)
                await self._close_trade_by_tp_sl(trade_id, trade_info, filled_order_dict, results)
    
    async def _close_trade_by_tp_sl(self, trade_id: str, trade_info: Dict, filled_order: Dict, results: Dict):
        """Close a trade when its TP/SL order is filled."""
        
        risk_type = filled_order['risk_type']
        exit_price = filled_order['price']
        exit_time = filled_order['filled_at']
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Calculate realized P&L if possible
            entry_price = trade_info.get('entry_price')
            size_contracts = trade_info.get('size_contracts', 0)
            realized_pnl = None
            
            if entry_price and exit_price and size_contracts:
                # Simple P&L calculation (this could be enhanced for different contract types)
                realized_pnl = (exit_price - entry_price) * size_contracts
            
            # Update trade with exit information
            query = """
                UPDATE trades SET
                    trade_status = 'closed',
                    exit_price = %s,
                    exit_reason = %s,
                    realized_pnl = %s,
                    closed_at = %s,
                    last_updated = %s
                WHERE trade_id = %s
            """
            
            exit_reason = f"{'Take Profit' if risk_type == 'TP' else 'Stop Loss'} hit"
            
            values = (
                exit_price,
                exit_reason,
                realized_pnl,
                exit_time,
                datetime.now(),
                trade_id
            )
            
            cursor.execute(query, values)
            conn.commit()
            
            # Update results counter
            if risk_type == 'TP':
                results['trades_closed_by_tp'] += 1
            else:
                results['trades_closed_by_sl'] += 1
            
            logger.info(f"Closed trade {trade_id} by {risk_type} at price {exit_price} (realized P&L: {realized_pnl})")
    
    async def update_order_status(self, exchange_order_id: str, new_status: str, filled_price: Optional[float] = None):
        """
        Update the status of a specific order.
        
        This method is called when order status changes are detected.
        
        Args:
            exchange_order_id: The exchange's order ID
            new_status: New order status ('filled', 'canceled', etc.)
            filled_price: Execution price if order was filled
        """
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Prepare update query
            if new_status == 'filled' and filled_price is not None:
                query = """
                    UPDATE trade_orders SET
                        status = %s,
                        price = %s,
                        filled_at = %s
                    WHERE exchange_order_id = %s AND exchange = %s
                    RETURNING trade_id, is_risk_order, risk_type
                """
                values = (new_status, filled_price, datetime.now(), exchange_order_id, self.exchange)
            else:
                query = """
                    UPDATE trade_orders SET
                        status = %s
                    WHERE exchange_order_id = %s AND exchange = %s
                    RETURNING trade_id, is_risk_order, risk_type
                """
                values = (new_status, exchange_order_id, self.exchange)
            
            cursor.execute(query, values)
            result = cursor.fetchone()
            conn.commit()
            
            if result:
                trade_id, is_risk_order, risk_type = result
                
                if is_risk_order and new_status == 'filled':
                    logger.info(f"Risk order {exchange_order_id} ({risk_type}) filled for trade {trade_id}")
                    # The next sync_tp_sl_orders() call will handle closing the trade
                else:
                    logger.debug(f"Updated order {exchange_order_id} status to {new_status}")
            else:
                logger.warning(f"Order {exchange_order_id} not found for status update")
    
    async def get_trade_orders_summary(self, trade_id: str) -> Dict[str, Any]:
        """Get a summary of all orders associated with a trade."""
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN is_risk_order = true THEN 1 END) as risk_orders,
                    COUNT(CASE WHEN risk_type = 'TP' THEN 1 END) as tp_orders,
                    COUNT(CASE WHEN risk_type = 'SL' THEN 1 END) as sl_orders,
                    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_orders,
                    COUNT(CASE WHEN status = 'filled' THEN 1 END) as filled_orders
                FROM trade_orders
                WHERE trade_id = %s
            """
            
            cursor.execute(query, (trade_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            else:
                return {
                    'total_orders': 0,
                    'risk_orders': 0,
                    'tp_orders': 0,
                    'sl_orders': 0,
                    'open_orders': 0,
                    'filled_orders': 0
                }