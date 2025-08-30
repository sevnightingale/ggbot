"""
Position Repository

Provides data access for trading positions using paper_trades table.
Handles position lifecycle queries and integrates with paper trading system.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from core.common.db import get_db_connection
from core.common.logger import logger
from .position import Position, PositionStatus, PositionSide, PriceLevel, PositionMetrics
from .models.value_objects import Symbol, Money, Confidence


class PositionRepository:
    """Repository for position data access using paper_trades table."""
    
    def save(self, position: Position) -> None:
        """Save a position to the paper_trades table."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if position already exists
                cur.execute("SELECT trade_id FROM paper_trades WHERE trade_id = %s", (position.trade_id,))
                exists = cur.fetchone()
                
                if exists:
                    self._update_position(cur, position)
                else:
                    self._insert_position(cur, position)
                
                conn.commit()
        
        logger.info(f"Saved position {position.trade_id} for {position.symbol.value}")
    
    def _insert_position(self, cur, position: Position) -> None:
        """Insert a new position."""
        cur.execute("""
            INSERT INTO paper_trades (
                trade_id, config_id, user_id, symbol, side, entry_price, 
                current_price, size_usd, size_contracts, leverage, 
                unrealized_pnl, realized_pnl, status, stop_loss, take_profit,
                confidence_score, reasoning, opened_at, closed_at,
                close_reason, last_updated
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            position.trade_id,
            position.config_id,
            self._get_user_id_from_config(position.config_id),  # Need to lookup user_id
            position.symbol.value,
            position.side.value,
            position.entry_price.price,
            position.current_price.price if position.current_price else None,
            position.size_usd.amount,
            self._calculate_size_contracts(position),
            position.leverage,
            0.0,  # Will be calculated
            0.0,  # Realized P&L starts at 0
            position.status.value,
            position.stop_loss_price.price if position.stop_loss_price else None,
            position.take_profit_price.price if position.take_profit_price else None,
            position.entry_confidence.value if position.entry_confidence else None,
            position.entry_reasoning,
            position.opened_at,
            position.closed_at,
            position.execution_details.get('close_reason'),
            datetime.now()
        ))
    
    def _update_position(self, cur, position: Position) -> None:
        """Update an existing position."""
        cur.execute("""
            UPDATE paper_trades SET
                current_price = %s,
                unrealized_pnl = %s,
                realized_pnl = %s,
                status = %s,
                stop_loss = %s,
                take_profit = %s,
                closed_at = %s,
                close_reason = %s,
                last_updated = %s
            WHERE trade_id = %s
        """, (
            position.current_price.price if position.current_price else None,
            self._calculate_unrealized_pnl(position),
            self._calculate_realized_pnl(position),
            position.status.value,
            position.stop_loss_price.price if position.stop_loss_price else None,
            position.take_profit_price.price if position.take_profit_price else None,
            position.closed_at,
            position.execution_details.get('close_reason'),
            datetime.now(),
            position.trade_id
        ))
    
    def get_by_id(self, trade_id: str) -> Optional[Position]:
        """Get a position by trade ID."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT trade_id, config_id, user_id, symbol, side, entry_price,
                           current_price, size_usd, size_contracts, leverage,
                           unrealized_pnl, realized_pnl, status, stop_loss, take_profit,
                           confidence_score, reasoning, opened_at, closed_at,
                           close_reason, last_updated
                    FROM paper_trades
                    WHERE trade_id = %s
                """, (trade_id,))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                return self._row_to_position(row)
    
    def get_active_positions(self, config_id: str) -> List[Position]:
        """Get all active positions for a config."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT trade_id, config_id, user_id, symbol, side, entry_price,
                           current_price, size_usd, size_contracts, leverage,
                           unrealized_pnl, realized_pnl, status, stop_loss, take_profit,
                           confidence_score, reasoning, opened_at, closed_at,
                           close_reason, last_updated
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'open'
                    ORDER BY opened_at DESC
                """, (config_id,))
                
                return [self._row_to_position(row) for row in cur.fetchall()]
    
    def get_positions_by_symbol(self, config_id: str, symbol: str) -> List[Position]:
        """Get all positions for a specific symbol."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT trade_id, config_id, user_id, symbol, side, entry_price,
                           current_price, size_usd, size_contracts, leverage,
                           unrealized_pnl, realized_pnl, status, stop_loss, take_profit,
                           confidence_score, reasoning, opened_at, closed_at,
                           close_reason, last_updated
                    FROM paper_trades
                    WHERE config_id = %s AND symbol = %s
                    ORDER BY opened_at DESC
                """, (config_id, symbol))
                
                return [self._row_to_position(row) for row in cur.fetchall()]
    
    def get_closed_positions(self, config_id: str, limit: int = 50) -> List[Position]:
        """Get recent closed positions."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT trade_id, config_id, user_id, symbol, side, entry_price,
                           current_price, size_usd, size_contracts, leverage,
                           unrealized_pnl, realized_pnl, status, stop_loss, take_profit,
                           confidence_score, reasoning, opened_at, closed_at,
                           close_reason, last_updated
                    FROM paper_trades
                    WHERE config_id = %s AND status IN ('closed', 'liquidated')
                    ORDER BY closed_at DESC
                    LIMIT %s
                """, (config_id, limit))
                
                return [self._row_to_position(row) for row in cur.fetchall()]
    
    def update_current_prices(self, config_id: str, symbol: str, 
                            current_price: Decimal) -> List[Position]:
        """Update current price for all active positions of a symbol."""
        positions = []
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get active positions for this symbol
                cur.execute("""
                    SELECT trade_id FROM paper_trades
                    WHERE config_id = %s AND symbol = %s AND status = 'open'
                """, (config_id, symbol))
                
                trade_ids = [row[0] for row in cur.fetchall()]
                
                # Update each position
                for trade_id in trade_ids:
                    position = self.get_by_id(trade_id)
                    if position:
                        position.update_current_price(current_price)
                        self.save(position)
                        positions.append(position)
        
        return positions
    
    def close_position(self, trade_id: str, close_price: Decimal, 
                      reason: str = "manual") -> Optional[Position]:
        """Close a position with final price."""
        position = self.get_by_id(trade_id)
        if not position or position.is_closed:
            return position
        
        position.close_position(close_price, reason)
        self.save(position)
        
        logger.info(f"Closed position {trade_id} at {close_price} (reason: {reason})")
        return position
    
    def get_portfolio_summary(self, config_id: str) -> Dict[str, Any]:
        """Get portfolio summary for a config."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get active positions summary
                cur.execute("""
                    SELECT 
                        COUNT(*) as active_positions,
                        COALESCE(SUM(size_usd), 0) as total_position_size,
                        COALESCE(SUM(unrealized_pnl), 0) as total_unrealized_pnl
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'open'
                """, (config_id,))
                
                active_row = cur.fetchone()
                
                # Get closed positions summary
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_trades,
                        COALESCE(SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END), 0) as winning_trades,
                        COALESCE(SUM(realized_pnl), 0) as total_realized_pnl,
                        COALESCE(AVG(realized_pnl), 0) as avg_pnl_per_trade
                    FROM paper_trades
                    WHERE config_id = %s AND status = 'closed'
                """, (config_id,))
                
                closed_row = cur.fetchone()
                
                total_trades = closed_row[0] if closed_row[0] else 0
                winning_trades = closed_row[1] if closed_row[1] else 0
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                return {
                    'active_positions': active_row[0] if active_row[0] else 0,
                    'total_position_size_usd': float(active_row[1] if active_row[1] else 0),
                    'total_unrealized_pnl': float(active_row[2] if active_row[2] else 0),
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': total_trades - winning_trades,
                    'win_rate_pct': win_rate,
                    'total_realized_pnl': float(closed_row[2] if closed_row[2] else 0),
                    'avg_pnl_per_trade': float(closed_row[3] if closed_row[3] else 0)
                }
    
    def _row_to_position(self, row) -> Position:
        """Convert database row to Position entity."""
        # Extract data from row
        trade_id, config_id, user_id, symbol, side, entry_price = row[:6]
        current_price, size_usd, size_contracts, leverage = row[6:10]
        unrealized_pnl, realized_pnl, status, stop_loss, take_profit = row[10:15]
        confidence_score, reasoning, opened_at, closed_at = row[15:19]
        close_reason, last_updated = row[19:21]
        
        # Create value objects
        symbol_obj = Symbol.from_string(symbol)
        side_obj = PositionSide(side)
        status_obj = PositionStatus(status)
        size_usd_obj = Money(Decimal(str(size_usd)), "USD")
        
        # Create price levels
        entry_price_level = PriceLevel(Decimal(str(entry_price)), opened_at or datetime.now())
        current_price_level = PriceLevel(Decimal(str(current_price)), last_updated) if current_price else None
        stop_loss_level = PriceLevel(Decimal(str(stop_loss)), opened_at or datetime.now()) if stop_loss else None
        take_profit_level = PriceLevel(Decimal(str(take_profit)), opened_at or datetime.now()) if take_profit else None
        
        # Create confidence
        confidence_obj = Confidence(float(confidence_score)) if confidence_score else None
        
        # Build execution details
        execution_details = {}
        if close_reason:
            execution_details['close_reason'] = close_reason
        
        return Position(
            trade_id=trade_id,
            config_id=config_id,
            symbol=symbol_obj,
            side=side_obj,
            status=status_obj,
            size_usd=size_usd_obj,
            leverage=Decimal(str(leverage)),
            collateral_amount=Money(size_usd_obj.amount / Decimal(str(leverage)), "USD"),
            entry_price=entry_price_level,
            current_price=current_price_level,
            stop_loss_price=stop_loss_level,
            take_profit_price=take_profit_level,
            exchange="paper",
            execution_details=execution_details,
            created_at=opened_at or datetime.now(),
            opened_at=opened_at,
            closed_at=closed_at,
            entry_confidence=confidence_obj,
            entry_reasoning=reasoning or ""
        )
    
    def _get_user_id_from_config(self, config_id: str) -> str:
        """Get user_id for a config_id."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id FROM configurations WHERE config_id = %s", (config_id,))
                result = cur.fetchone()
                return result[0] if result else "00000000-0000-0000-0000-000000000001"
    
    def _calculate_size_contracts(self, position: Position) -> Decimal:
        """Calculate size in contracts from USD size."""
        return position.size_usd.amount / position.entry_price.price
    
    def _calculate_unrealized_pnl(self, position: Position) -> Decimal:
        """Calculate current unrealized P&L."""
        if not position.current_price or not position.is_active:
            return Decimal('0')
        
        metrics = position.calculate_metrics()
        return metrics.unrealized_pnl.amount if metrics else Decimal('0')
    
    def _calculate_realized_pnl(self, position: Position) -> Decimal:
        """Calculate realized P&L for closed positions."""
        if not position.is_closed:
            return Decimal('0')
        
        metrics = position.calculate_metrics()
        return metrics.total_pnl.amount if metrics else Decimal('0')


# Global repository instance  
position_repo = PositionRepository()