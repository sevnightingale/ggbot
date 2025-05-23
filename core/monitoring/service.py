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
from decimal import Decimal

from core.common.logger import logger
from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
import psycopg2
from psycopg2.extras import RealDictCursor
from .adapters import create_exchange_adapter, ExchangeAdapter


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
        """Fetch and store current account state."""
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
        
        # Calculate metrics
        metrics = self._calculate_metrics(normalized_balance, normalized_positions)
        
        # Store in database
        await self._store_account_state(
            balance_data=normalized_balance,
            position_data=normalized_positions,
            metrics=metrics,
            timestamp=timestamp
        )
        
        logger.info(
            f"Updated account state: "
            f"BTC={normalized_balance['total_btc']:.8f}, "
            f"Positions={len(normalized_positions)}, "
            f"Equity={metrics['equity_btc']:.8f}"
        )
    
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