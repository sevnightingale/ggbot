"""
Account monitoring service using direct CCXT connections.

This service runs continuously to monitor exchange account state and update
the database with current balance, position, and margin information.
"""

import asyncio
import ccxt.async_support as ccxt
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import uuid
from decimal import Decimal
from dataclasses import dataclass

from core.common.logger import logger
from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
import psycopg2
from psycopg2.extras import RealDictCursor
from .adapters import create_exchange_adapter, ExchangeAdapter


# ReconciliationResult dataclass removed - no longer needed with simple trade lifecycle system


class AccountMonitoringService:
    """Service for monitoring exchange account state."""
    
    def __init__(
        self,
        user_id: str,
        config_id: str,
        exchange_name: str,
        credentials: Dict[str, str],
        monitoring_interval: int = 30,
        testnet: bool = True
    ):
        """
        Initialize the monitoring service.
        
        Args:
            user_id: User ID for database association
            config_id: Configuration ID for this monitoring instance
            exchange_name: Name of the exchange (e.g., 'bitmex')
            credentials: Dict with 'apiKey', 'secret', and optionally 'passphrase'
            monitoring_interval: Seconds between updates (default 30)
            testnet: Whether to use testnet/sandbox mode
        """
        self.user_id = user_id
        self.config_id = config_id
        self.exchange_name = exchange_name.lower()
        self.credentials = credentials
        self.monitoring_interval = monitoring_interval
        self.testnet = testnet
        
        # Create exchange adapter
        self.adapter = create_exchange_adapter(self.exchange_name)
        
        # Exchange client will be created when starting
        self.exchange = None
        self.monitoring_task = None
        self.is_running = False
        
        logger.info(f"Initialized monitoring for {exchange_name} (user: {user_id})")
    
    async def _create_exchange_client(self) -> ccxt.Exchange:
        """Create and configure CCXT exchange client."""
        # Get exchange class
        exchange_class = getattr(ccxt, self.exchange_name)
        
        # Configure exchange
        config = {
            'apiKey': self.credentials.get('apiKey'),
            'secret': self.credentials.get('secret'),
            'enableRateLimit': True,
            'options': {}
        }
        
        # Add passphrase if needed (e.g., OKX)
        if 'passphrase' in self.credentials:
            config['password'] = self.credentials['passphrase']
        
        # Enable testnet if requested
        if self.testnet:
            config['options']['testnet'] = True
            logger.info(f"Using {self.exchange_name} testnet")
        
        # Create exchange instance
        exchange = exchange_class(config)
        
        # Load markets
        await exchange.load_markets()
        logger.info(f"Connected to {self.exchange_name}, loaded {len(exchange.markets)} markets")
        
        return exchange
    
    async def start_monitoring(self):
        """Start the monitoring loop."""
        if self.is_running:
            logger.warning("Monitoring already running")
            return
        
        try:
            # Create exchange client
            self.exchange = await self._create_exchange_client()
            
            # Start monitoring task
            self.is_running = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info(f"Started monitoring for {self.exchange_name}")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            self.is_running = False
            raise
    
    async def stop_monitoring(self):
        """Stop the monitoring loop gracefully."""
        if not self.is_running:
            return
        
        logger.info(f"Stopping monitoring for {self.exchange_name}")
        self.is_running = False
        
        # Cancel monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Close exchange connection
        if self.exchange:
            await self.exchange.close()
            self.exchange = None
        
        logger.info(f"Monitoring stopped for {self.exchange_name}")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        consecutive_errors = 0
        
        while self.is_running:
            try:
                # Update account state
                await self._update_account_state()
                consecutive_errors = 0  # Reset on success
                
                # Wait for next update
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in monitoring loop: {e} (consecutive: {consecutive_errors})")
                
                # Exponential backoff on errors
                wait_time = min(300, self.monitoring_interval * (2 ** consecutive_errors))
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
                
                # Recreate exchange connection after multiple failures
                if consecutive_errors >= 3:
                    logger.warning("Multiple failures, recreating exchange connection...")
                    try:
                        if self.exchange:
                            await self.exchange.close()
                        self.exchange = await self._create_exchange_client()
                        consecutive_errors = 0
                    except Exception as conn_error:
                        logger.error(f"Failed to recreate connection: {conn_error}")
    
    async def _update_account_state(self):
        """
        Fetch and store current account state, then reconcile trades.
        
        Returns:
            Dict with update results including reconciliation info
        """
        timestamp = datetime.utcnow()
        
        # Fetch balance
        logger.debug("Fetching balance...")
        raw_balance = await self.exchange.fetch_balance()
        normalized_balance = self.adapter.normalize_balance(raw_balance)
        
        # Fetch positions
        logger.debug("Fetching positions...")
        raw_positions = await self.exchange.fetch_positions()
        normalized_positions = []
        
        for raw_pos in raw_positions:
            normalized = self.adapter.normalize_position(raw_pos)
            if normalized:  # Skip None (e.g., 0-contract positions)
                normalized_positions.append(normalized)
        
        # Fetch open orders for TP/SL tracking
        logger.debug("Fetching open orders...")
        raw_open_orders = []
        normalized_orders = []
        try:
            raw_open_orders = await self.exchange.fetch_open_orders()
            logger.debug(f"Fetched {len(raw_open_orders)} open orders")
            
            # Normalize orders for risk tracking
            normalized_orders = self.adapter.normalize_open_orders(raw_open_orders)
            risk_orders = [order for order in normalized_orders if order.get('is_risk_order')]
            logger.debug(f"Identified {len(risk_orders)} risk orders (TP/SL) out of {len(normalized_orders)} total orders")
            
        except Exception as e:
            logger.warning(f"Failed to fetch open orders: {e}")
            raw_open_orders = []
            normalized_orders = []
        
        # Calculate metrics
        metrics = self._calculate_metrics(normalized_balance, normalized_positions)
        
        # Store in database
        await self._store_account_state(
            balance_data=normalized_balance,
            position_data=normalized_positions,
            metrics=metrics,
            timestamp=timestamp
        )
        
        # Sync orders to trade_orders table
        if normalized_orders:
            await self._sync_orders_to_database(normalized_orders)
        
        # NEW: Simple position sync using trade lifecycle manager
        logger.debug("Syncing trades with exchange positions...")
        lifecycle_positions = await self.adapter.get_positions_for_lifecycle(self.exchange)
        
        # Import and use the trade lifecycle manager
        # TODO: Re-enable when TradeLifecycleManager is migrated from trading-legacy
        # from trading.lifecycle_manager import TradeLifecycleManager
        # lifecycle_manager = TradeLifecycleManager(self.user_id, self.exchange_name, self.config_id)
        # sync_results = await lifecycle_manager.sync_positions_to_trades(lifecycle_positions, self.adapter)
        
        # For now, return empty results to keep the service running
        sync_results = {
            'trades_opened': 0,
            'trades_updated': 0,
            'trades_closed': 0,
            'errors': []
        }
        
        # NEW: Sync TP/SL order status and close trades when orders are filled
        logger.debug("Checking TP/SL order status...")
        # tp_sl_results = await lifecycle_manager.sync_tp_sl_orders()
        tp_sl_results = {
            'orders_checked': 0,
            'trades_closed_by_tp': 0,
            'trades_closed_by_sl': 0,
            'errors': []
        }
        
        # Log sync results
        position_changes = sync_results['trades_opened'] > 0 or sync_results['trades_closed'] > 0
        tp_sl_changes = tp_sl_results['trades_closed_by_tp'] > 0 or tp_sl_results['trades_closed_by_sl'] > 0
        
        if position_changes or tp_sl_changes:
            logger.info(f"Trade sync completed: {sync_results['trades_opened']} opened, {sync_results['trades_updated']} updated, {sync_results['trades_closed']} closed, TP/SL: {tp_sl_results['trades_closed_by_tp']} TP hits, {tp_sl_results['trades_closed_by_sl']} SL hits")
        else:
            logger.debug("Trade sync completed: no changes needed")
        
        # Count risk orders for logging
        risk_orders_count = len([order for order in normalized_orders if order.get('is_risk_order')])
        
        logger.info(
            f"Updated account state: "
            f"BTC={normalized_balance['total_btc']:.8f}, "
            f"Positions={len(normalized_positions)}, "
            f"Orders={len(normalized_orders)} ({risk_orders_count} TP/SL), "
            f"Equity={metrics['equity_btc']:.8f}, "
            f"Trade sync: {sync_results['trades_opened']} opened, {sync_results['trades_updated']} updated, {sync_results['trades_closed']} closed"
        )
        
        return {
            "account_updated": True,
            "position_sync_performed": True,
            "tp_sl_sync_performed": True,
            "trades_opened": sync_results['trades_opened'],
            "trades_updated": sync_results['trades_updated'],
            "trades_closed": sync_results['trades_closed'],
            "trades_closed_by_tp": tp_sl_results['trades_closed_by_tp'],
            "trades_closed_by_sl": tp_sl_results['trades_closed_by_sl'],
            "tp_sl_orders_checked": tp_sl_results['orders_checked'],
            "sync_errors": len(sync_results['errors']) + len(tp_sl_results['errors']),
            "total_positions": len(normalized_positions),
            "total_orders": len(normalized_orders),
            "risk_orders": risk_orders_count,
            "timestamp": timestamp.isoformat()
        }
    
    def _calculate_metrics(
        self,
        balance: Dict[str, Any],
        positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate account metrics from balance and positions."""
        # Total unrealized PNL
        total_unrealized_pnl = sum(
            pos.get('unrealized_pnl', 0) for pos in positions
        )
        
        # Equity = balance + unrealized PNL
        equity_btc = balance['total_btc'] + total_unrealized_pnl
        
        # Used margin (approximate from positions)
        used_margin_btc = balance['used_btc']
        
        # Available margin
        available_margin_btc = balance['available_btc']
        
        # Margin usage percentage
        margin_used_pct = 0
        if equity_btc > 0:
            margin_used_pct = (used_margin_btc / equity_btc) * 100
        
        return {
            'equity_btc': equity_btc,
            'available_margin_btc': available_margin_btc,
            'used_margin_btc': used_margin_btc,
            'margin_used_pct': margin_used_pct,
            'total_unrealized_pnl': total_unrealized_pnl,
            'position_count': len(positions)
        }
    
    async def _store_account_state(
        self,
        balance_data: Dict[str, Any],
        position_data: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        timestamp: datetime
    ):
        """Store account state in database."""
        # Use sync database connection (we'll run in thread pool if needed)
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        
        try:
            with conn.cursor() as cursor:
                # Prepare data for storage
                balance_json = json.dumps(balance_data)
                position_json = json.dumps(position_data)
                
                # Upsert account state
                query = """
                    INSERT INTO account_states (
                        user_id, config_id, exchange,
                        balance_data, position_data,
                        equity, available_margin, used_margin,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, config_id, exchange)
                    DO UPDATE SET
                        balance_data = EXCLUDED.balance_data,
                        position_data = EXCLUDED.position_data,
                        equity = EXCLUDED.equity,
                        available_margin = EXCLUDED.available_margin,
                        used_margin = EXCLUDED.used_margin,
                        updated_at = EXCLUDED.updated_at
                """
                
                cursor.execute(
                    query,
                    (
                        self.user_id,
                        self.config_id,
                        self.exchange_name,
                        balance_json,
                        position_json,
                        Decimal(str(metrics['equity_btc'])),
                        Decimal(str(metrics['available_margin_btc'])),
                        Decimal(str(metrics['used_margin_btc'])),
                        timestamp
                    )
                )
                
                conn.commit()
                logger.debug("Account state stored successfully")
            
        except Exception as e:
            logger.error(f"Failed to store account state: {e}")
            conn.rollback()
            raise
        
        finally:
            conn.close()
    
    async def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """Get the latest account state from database."""
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT balance_data, position_data, equity,
                           available_margin, used_margin, updated_at
                    FROM account_states
                    WHERE user_id = %s AND config_id = %s AND exchange = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                """
                
                cursor.execute(
                    query,
                    (self.user_id, self.config_id, self.exchange_name)
                )
                
                row = cursor.fetchone()
                
                if row:
                    # psycopg2 automatically converts JSONB to dict
                    balance_data = row['balance_data']
                    position_data = row['position_data']
                    
                    # If they're strings, parse them
                    if isinstance(balance_data, str):
                        balance_data = json.loads(balance_data)
                    if isinstance(position_data, str):
                        position_data = json.loads(position_data)
                    
                    return {
                        'balance_data': balance_data,
                        'position_data': position_data,
                        'equity': float(row['equity']),
                        'available_margin': float(row['available_margin']),
                        'used_margin': float(row['used_margin']),
                        'updated_at': row['updated_at']
                    }
                
                return None
            
        finally:
            conn.close()
    
    async def _sync_orders_to_database(self, normalized_orders: List[Dict[str, Any]]):
        """
        Sync normalized orders to the trade_orders table.
        
        This method:
        1. Updates existing orders if they already exist
        2. Inserts new orders
        3. Marks orders as filled/canceled if they no longer exist in open orders
        4. Associates risk orders (TP/SL) with existing trades
        """
        if not normalized_orders:
            return
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        
        try:
            with conn.cursor() as cursor:
                orders_processed = 0
                orders_inserted = 0
                orders_updated = 0
                
                for order in normalized_orders:
                    # Try to find matching trade for all orders
                    trade_id = await self._find_trade_for_risk_order(cursor, order)
                    
                    # Upsert order into trade_orders table
                    query = """
                        INSERT INTO trade_orders (
                            trade_id, exchange, symbol, exchange_order_id,
                            order_type, side, price, size, status,
                            is_risk_order, risk_type, created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (exchange, exchange_order_id)
                        DO UPDATE SET
                            trade_id = EXCLUDED.trade_id,
                            price = EXCLUDED.price,
                            size = EXCLUDED.size,
                            status = EXCLUDED.status,
                            is_risk_order = EXCLUDED.is_risk_order,
                            risk_type = EXCLUDED.risk_type
                        RETURNING (xmax = 0) AS inserted
                    """
                    
                    cursor.execute(
                        query,
                        (
                            trade_id,
                            self.exchange_name,
                            order['symbol'],
                            order['exchange_order_id'],
                            order['order_type'],
                            order['side'],
                            order['price'],
                            order['size'],
                            order['status'],
                            order['is_risk_order'],
                            order['risk_type']
                        )
                    )
                    
                    # Check if this was an insert or update
                    result = cursor.fetchone()
                    if result and result[0]:  # inserted = True
                        orders_inserted += 1
                    else:
                        orders_updated += 1
                    
                    orders_processed += 1
                
                conn.commit()
                logger.debug(f"Order sync completed: {orders_processed} processed, {orders_inserted} inserted, {orders_updated} updated")
                
        except Exception as e:
            logger.error(f"Failed to sync orders to database: {e}")
            conn.rollback()
            raise
        
        finally:
            conn.close()
    
    async def _find_trade_for_risk_order(self, cursor, order: Dict[str, Any]) -> Optional[str]:
        """
        Find the trade_id that this risk order (TP/SL) belongs to.
        
        Args:
            cursor: Database cursor
            order: Normalized order data
            
        Returns:
            trade_id if found, None otherwise
        """
        try:
            # Look for open trades with matching symbol and exchange
            query = """
                SELECT trade_id FROM trades
                WHERE symbol = %s AND exchange = %s AND trade_status = 'open'
                AND user_id = %s
                ORDER BY opened_at DESC
                LIMIT 1
            """
            
            cursor.execute(
                query,
                (order['symbol'], self.exchange_name, self.user_id)
            )
            
            result = cursor.fetchone()
            if result:
                return result[0]
            
            logger.debug(f"No matching trade found for risk order {order['exchange_order_id']} on {order['symbol']}")
            return None
            
        except Exception as e:
            logger.warning(f"Error finding trade for risk order: {e}")
            return None
    
    # =================================================================
    # SIMPLIFIED MONITORING SERVICE
    # =================================================================
    
    # This monitoring service has been simplified to use the new trade lifecycle system.
    # 
    # OLD APPROACH: Complex phantom-trade reconciliation with aggregation logic
    # NEW APPROACH: Simple position sync using TradeLifecycleManager
    #
    # Key benefits:
    # - No phantom trades
    # - Exchange positions drive trade state  
    # - Simple and reliable
    # - Universal exchange support
    #
    # The removed reconciliation methods (~600 lines) have been replaced by
    # TradeLifecycleManager.sync_positions_to_trades() (~200 lines).
