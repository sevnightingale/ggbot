#!/usr/bin/env python3
"""
Unified Position Manager Service

Single source of truth for position state across all modules.
Aggregates data from account monitoring and trading engine to provide
consistent position information to decision module and other consumers.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from core.common.logger import logger
from core.common.db import get_db_connection
from core.monitoring.service import AccountMonitoringService


class PositionStatus(Enum):
    """Position status enumeration."""
    ACTIVE = "active"
    CLOSED = "closed"
    PENDING = "pending"
    ERROR = "error"


@dataclass
class UnifiedPosition:
    """Unified position representation combining exchange and database data."""
    symbol: str
    side: str  # 'long' or 'short'
    size: float
    entry_price: float
    current_price: Optional[float]
    unrealized_pnl: Optional[float]
    
    # Database trade information
    trade_id: Optional[str]
    confidence_score: Optional[float]
    created_at: Optional[datetime]
    leverage: Optional[int]
    
    # Exchange information
    exchange_position_id: Optional[str]
    margin_used: Optional[float]
    liquidation_price: Optional[float]
    
    # Status and metadata
    status: PositionStatus
    last_sync_at: datetime
    sync_source: str  # 'exchange', 'database', 'reconciled'


@dataclass
class PositionSummary:
    """Summary of all positions for a user."""
    user_id: str
    total_positions: int
    active_positions: int
    total_unrealized_pnl: float
    total_margin_used: float
    positions: List[UnifiedPosition]
    last_updated: datetime
    data_sources: Dict[str, datetime]  # Track when each source was last updated


class UnifiedPositionManager:
    """
    Unified position manager that combines data from multiple sources
    to provide a single source of truth for position state.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize the position manager.
        
        Args:
            user_id: User ID to manage positions for
        """
        self.user_id = user_id
        self.logger = logger.bind(user_id=user_id, service="position_manager")
        
        # Cache for position data
        self._position_cache: Dict[str, UnifiedPosition] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=30)  # 30 second cache TTL
        
        # Services - reconciliation is now handled by AccountMonitoringService
        
    async def get_user_positions(
        self, 
        force_refresh: bool = False
    ) -> PositionSummary:
        """
        Get unified position summary for the user.
        
        Args:
            force_refresh: Force refresh from all data sources
            
        Returns:
            PositionSummary with all position information
        """
        # Check cache
        if not force_refresh and self._is_cache_valid():
            self.logger.debug("Returning cached position data")
            return self._build_summary_from_cache()
        
        self.logger.info("Refreshing position data from all sources")
        
        # Get data from all sources
        exchange_positions = await self._get_exchange_positions()
        database_trades = self._get_database_trades()
        
        # Merge and reconcile the data
        unified_positions = await self._merge_position_data(
            exchange_positions, 
            database_trades
        )
        
        # Update cache
        self._update_cache(unified_positions)
        
        # Build summary
        summary = PositionSummary(
            user_id=self.user_id,
            total_positions=len(unified_positions),
            active_positions=len([p for p in unified_positions if p.status == PositionStatus.ACTIVE]),
            total_unrealized_pnl=sum(p.unrealized_pnl or 0 for p in unified_positions),
            total_margin_used=sum(p.margin_used or 0 for p in unified_positions),
            positions=unified_positions,
            last_updated=datetime.utcnow(),
            data_sources={
                'exchange': datetime.utcnow(),
                'database': datetime.utcnow(),
                'cache': self._cache_timestamp or datetime.utcnow()
            }
        )
        
        self.logger.info(
            f"Position summary: {summary.active_positions}/{summary.total_positions} active, "
            f"PnL: {summary.total_unrealized_pnl:.2f}"
        )
        
        return summary
    
    async def get_position_by_symbol(self, symbol: str) -> Optional[UnifiedPosition]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol: Trading symbol to get position for
            
        Returns:
            UnifiedPosition if found, None otherwise
        """
        summary = await self.get_user_positions()
        
        for position in summary.positions:
            if position.symbol == symbol:
                return position
        
        return None
    
    async def sync_trade_with_exchange(self, trade_id: str) -> Dict[str, Any]:
        """
        Sync a specific trade with exchange state.
        Note: Individual trade sync is now handled by triggering full account reconciliation.
        
        Args:
            trade_id: Trade ID to sync
            
        Returns:
            Dictionary with sync results
        """
        self.logger.info(f"Syncing trade {trade_id} with exchange via account monitoring")
        
        # Trigger full account reconciliation via monitoring service
        # This is more efficient as it syncs all trades at once
        monitoring_service = AccountMonitoringService(
            user_id=self.user_id,
            config_id="a93de31b-9b8a-42e3-827d-c31e580f5f36",  # Default config
            exchange_name="bitmex",
            credentials={},  # Will be loaded from config
            testnet=True
        )
        
        try:
            # Create exchange connection and update account state (includes reconciliation)
            monitoring_service.exchange = await monitoring_service._create_exchange_client()
            result = await monitoring_service.update_account_state_on_demand()
            
            # Invalidate cache to force refresh
            self._invalidate_cache()
            
            return {
                'trade_id': trade_id,
                'action_taken': 'reconciliation_triggered',
                'phantom_trades_closed': result.get('phantom_trades_closed', 0),
                'trades_validated': result.get('trades_validated', 0),
                'reconciliation_performed': result.get('reconciliation_performed', False)
            }
        
        finally:
            if hasattr(monitoring_service, 'exchange') and monitoring_service.exchange:
                await monitoring_service.exchange.close()
    
    async def reconcile_all_positions(self) -> Dict[str, Any]:
        """
        Reconcile all positions with exchange state via account monitoring service.
        
        Returns:
            Dictionary with reconciliation results
        """
        self.logger.info("Starting full position reconciliation via account monitoring")
        
        # Use account monitoring service which now includes reconciliation
        monitoring_service = AccountMonitoringService(
            user_id=self.user_id,
            config_id="a93de31b-9b8a-42e3-827d-c31e580f5f36",  # Default config
            exchange_name="bitmex", 
            credentials={},  # Will be loaded from config
            testnet=True
        )
        
        try:
            # Create exchange connection and update account state (includes reconciliation)
            monitoring_service.exchange = await monitoring_service._create_exchange_client()
            result = await monitoring_service.update_account_state_on_demand()
            
            # Invalidate cache to force refresh
            self._invalidate_cache()
            
            return {
                'timestamp': result.get('timestamp'),
                'trades_processed': result.get('trades_validated', 0) + result.get('phantom_trades_closed', 0),
                'trades_updated': result.get('phantom_trades_closed', 0),
                'errors': result.get('reconciliation_errors', 0),
                'phantom_trades_closed': result.get('phantom_trades_closed', 0),
                'trades_validated': result.get('trades_validated', 0),
                'reconciliation_performed': result.get('reconciliation_performed', False)
            }
        
        finally:
            if hasattr(monitoring_service, 'exchange') and monitoring_service.exchange:
                await monitoring_service.exchange.close()
    
    def _is_cache_valid(self) -> bool:
        """Check if the position cache is still valid."""
        if not self._cache_timestamp:
            return False
        
        return datetime.utcnow() - self._cache_timestamp < self._cache_ttl
    
    def _invalidate_cache(self):
        """Invalidate the position cache."""
        self._cache_timestamp = None
        self._position_cache.clear()
    
    def _update_cache(self, positions: List[UnifiedPosition]):
        """Update the position cache."""
        self._position_cache = {pos.symbol: pos for pos in positions}
        self._cache_timestamp = datetime.utcnow()
    
    def _build_summary_from_cache(self) -> PositionSummary:
        """Build position summary from cached data."""
        positions = list(self._position_cache.values())
        
        return PositionSummary(
            user_id=self.user_id,
            total_positions=len(positions),
            active_positions=len([p for p in positions if p.status == PositionStatus.ACTIVE]),
            total_unrealized_pnl=sum(p.unrealized_pnl or 0 for p in positions),
            total_margin_used=sum(p.margin_used or 0 for p in positions),
            positions=positions,
            last_updated=self._cache_timestamp,
            data_sources={'cache': self._cache_timestamp}
        )
    
    async def _get_exchange_positions(self) -> List[Dict[str, Any]]:
        """Get current positions from exchange via account monitoring."""
        try:
            # Get the latest account state from database (updated by monitoring service)
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT position_data, updated_at
                        FROM account_states
                        WHERE user_id = %s
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """, (self.user_id,))
                    
                    result = cursor.fetchone()
                    if result:
                        position_data, updated_at = result
                        self.logger.debug(f"Retrieved {len(position_data)} positions from account_states")
                        return position_data or []
                    else:
                        self.logger.warning("No account state found in database")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Failed to get exchange positions: {e}")
            return []
    
    def _get_database_trades(self) -> List[Dict[str, Any]]:
        """Get active trades from database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            trade_id, pair, trade_status, created_at,
                            collateral_amount, leverage, entry_price,
                            confidence_score, last_sync_at
                        FROM trades
                        WHERE user_id = %s 
                        AND trade_status IN ('open', 'active', 'pending')
                        ORDER BY created_at DESC
                    """, (self.user_id,))
                    
                    columns = [desc[0] for desc in cursor.description]
                    trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    
                    self.logger.debug(f"Retrieved {len(trades)} active trades from database")
                    return trades
                    
        except Exception as e:
            self.logger.error(f"Failed to get database trades: {e}")
            return []
    
    async def _merge_position_data(
        self,
        exchange_positions: List[Dict[str, Any]],
        database_trades: List[Dict[str, Any]]
    ) -> List[UnifiedPosition]:
        """
        Merge position data from exchange and database.
        
        Args:
            exchange_positions: Positions from exchange
            database_trades: Trades from database
            
        Returns:
            List of unified positions
        """
        unified_positions = []
        
        # Track which symbols we've processed
        processed_symbols = set()
        
        # Process exchange positions first
        for ex_pos in exchange_positions:
            symbol = ex_pos.get('symbol', '')
            if not symbol:
                continue
                
            # Find matching database trade
            matching_trade = None
            for trade in database_trades:
                if self._symbols_match(trade.get('pair', ''), symbol):
                    matching_trade = trade
                    break
            
            # Create unified position
            unified_pos = self._create_unified_position(
                exchange_position=ex_pos,
                database_trade=matching_trade,
                sync_source='exchange'
            )
            
            unified_positions.append(unified_pos)
            processed_symbols.add(symbol)
        
        # Process remaining database trades (not matched with exchange positions)
        for trade in database_trades:
            symbol = trade.get('pair', '')
            if symbol and symbol not in processed_symbols:
                # Database trade without exchange position - likely needs reconciliation
                unified_pos = self._create_unified_position(
                    exchange_position=None,
                    database_trade=trade,
                    sync_source='database'
                )
                
                unified_positions.append(unified_pos)
        
        return unified_positions
    
    def _create_unified_position(
        self,
        exchange_position: Optional[Dict[str, Any]],
        database_trade: Optional[Dict[str, Any]],
        sync_source: str
    ) -> UnifiedPosition:
        """Create a unified position from exchange and/or database data."""
        
        # Determine primary symbol and data source
        if exchange_position:
            symbol = exchange_position.get('symbol', '')
            size = abs(float(exchange_position.get('contracts', 0)))
            side = 'long' if exchange_position.get('side') == 'long' else 'short'
            current_price = exchange_position.get('markPrice')
            unrealized_pnl = exchange_position.get('unrealizedPnl')
            margin_used = exchange_position.get('initialMargin')
            liquidation_price = exchange_position.get('liquidationPrice')
            exchange_position_id = exchange_position.get('info', {}).get('account')
            status = PositionStatus.ACTIVE
        else:
            symbol = database_trade.get('pair', '') if database_trade else ''
            size = float(database_trade.get('collateral_amount', 0)) if database_trade else 0
            side = 'long'  # Default, could be determined from trade direction
            current_price = None
            unrealized_pnl = None
            margin_used = None
            liquidation_price = None
            exchange_position_id = None
            status = PositionStatus.PENDING  # No exchange position found
        
        # Get database trade information
        if database_trade:
            trade_id = database_trade.get('trade_id')
            confidence_score = float(database_trade.get('confidence_score', 0)) if database_trade.get('confidence_score') else None
            created_at = database_trade.get('created_at')
            leverage = database_trade.get('leverage')
            entry_price = float(database_trade.get('entry_price', 0)) if database_trade.get('entry_price') else None
            last_sync_at = database_trade.get('last_sync_at') or datetime.utcnow()
        else:
            trade_id = None
            confidence_score = None
            created_at = None
            leverage = None
            entry_price = None
            last_sync_at = datetime.utcnow()
        
        return UnifiedPosition(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price or 0,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            trade_id=trade_id,
            confidence_score=confidence_score,
            created_at=created_at,
            leverage=leverage,
            exchange_position_id=exchange_position_id,
            margin_used=margin_used,
            liquidation_price=liquidation_price,
            status=status,
            last_sync_at=last_sync_at,
            sync_source=sync_source
        )
    
    def _symbols_match(self, trade_symbol: str, exchange_symbol: str) -> bool:
        """Check if trade symbol matches exchange symbol."""
        # Handle BitMEX symbol format conversion
        if trade_symbol == "BTC/USD" and exchange_symbol in ["BTC/USD:BTC", "XBTUSD"]:
            return True
        # Add more symbol mappings as needed
        return trade_symbol == exchange_symbol


# Standalone functions for external use
async def get_user_positions(user_id: str) -> PositionSummary:
    """Get positions for a user (convenience function)."""
    manager = UnifiedPositionManager(user_id)
    return await manager.get_user_positions()


async def reconcile_user_positions(user_id: str) -> Dict[str, Any]:
    """Reconcile positions for a user (convenience function)."""
    manager = UnifiedPositionManager(user_id)
    return await manager.reconcile_all_positions()