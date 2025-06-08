#!/usr/bin/env python3
"""
Hybrid Account Monitoring Service

Combines scheduled monitoring with triggered updates for immediate trade confirmation.
This allows both regular account state updates and on-demand updates after trade execution.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from core.common.logger import logger
from core.common.db import get_db_connection
from core.common.config import DEFAULT_USER_ID
from core.monitoring.service import AccountMonitoringService


class HybridMonitoringService:
    """
    Hybrid monitoring service that supports both scheduled and triggered updates.
    """
    
    def __init__(
        self,
        user_id: str = DEFAULT_USER_ID,
        config_id: str = None,
        exchange_name: str = "bitmex",
        credentials: Dict[str, str] = None,
        testnet: bool = True
    ):
        """
        Initialize the hybrid monitoring service.
        
        Args:
            user_id: User ID to monitor
            config_id: Configuration ID (optional, will query from DB if not provided)
            exchange_name: Exchange name (default: bitmex)
            credentials: Exchange credentials (optional, will query from env if not provided)
            testnet: Use testnet mode (default: True)
        """
        self.user_id = user_id
        self.config_id = config_id
        self.exchange_name = exchange_name
        self.testnet = testnet
        self.logger = logger.bind(user_id=user_id, service="hybrid_monitoring")
        
        # Get credentials if not provided
        if credentials is None:
            credentials = self._get_credentials()
        
        # Get config_id if not provided
        if config_id is None:
            config_id = self._get_config_id()
        
        self.monitoring_service = AccountMonitoringService(
            user_id=user_id,
            config_id=config_id,
            exchange_name=exchange_name,
            credentials=credentials,
            testnet=testnet
        )
        
        # Scheduled monitoring state
        self.scheduled_task: Optional[asyncio.Task] = None
        self.scheduled_interval = 30  # Default 30 seconds
        self.is_running = False
        
        # Triggered update tracking
        self.last_triggered_update = None
        self.triggered_callbacks: List[Callable] = []
        
    def _get_credentials(self) -> Dict[str, str]:
        """Get exchange credentials from environment."""
        import os
        return {
            'apiKey': os.getenv('EXCHANGE_API', ''),
            'secret': os.getenv('EXCHANGE_SECRET', '')
        }
    
    def _get_config_id(self) -> str:
        """Get config ID from database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT config_id FROM configurations 
                        WHERE user_id = %s AND config_name = 'default'
                        LIMIT 1
                    """, (self.user_id,))
                    result = cursor.fetchone()
                    return result[0] if result else "a93de31b-9b8a-42e3-827d-c31e580f5f36"
        except Exception as e:
            self.logger.warning(f"Could not get config_id from DB: {e}")
            return "a93de31b-9b8a-42e3-827d-c31e580f5f36"  # Fallback
        
    async def start_scheduled_monitoring(self, interval: int = 30):
        """
        Start the scheduled monitoring task.
        
        Args:
            interval: Update interval in seconds
        """
        if self.scheduled_task and not self.scheduled_task.done():
            self.logger.warning("Scheduled monitoring already running")
            return
            
        self.scheduled_interval = interval
        self.is_running = True
        self.scheduled_task = asyncio.create_task(self._scheduled_monitoring_loop())
        self.logger.info(f"Started scheduled monitoring with {interval}s interval")
        
    async def stop_scheduled_monitoring(self):
        """Stop the scheduled monitoring task."""
        self.is_running = False
        
        if self.scheduled_task:
            self.scheduled_task.cancel()
            try:
                await self.scheduled_task
            except asyncio.CancelledError:
                pass
            self.logger.info("Stopped scheduled monitoring")
            
    async def _scheduled_monitoring_loop(self):
        """Main loop for scheduled monitoring."""
        while self.is_running:
            try:
                # Update account state
                await self.monitoring_service.update_account_state()
                
                # Wait for next interval
                await asyncio.sleep(self.scheduled_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in scheduled monitoring: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
                
    async def trigger_update(self, delay: float = 10.0, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Trigger an immediate account state update after a delay.
        Useful for confirming trade execution.
        
        Args:
            delay: Seconds to wait before updating (allows exchange to process)
            callback: Optional callback function to call with results
            
        Returns:
            Updated account state
        """
        self.logger.info(f"Triggered update requested with {delay}s delay")
        
        # Wait for exchange to process
        if delay > 0:
            await asyncio.sleep(delay)
            
        # Update account state
        try:
            await self.monitoring_service.update_account_state()
            
            # Get the latest state
            account_state = await self.get_latest_account_state()
            
            self.last_triggered_update = {
                'timestamp': datetime.now(timezone.utc),
                'account_state': account_state,
                'success': True
            }
            
            # Call callback if provided
            if callback:
                await callback(account_state)
                
            self.logger.info("Triggered update completed successfully")
            return account_state
            
        except Exception as e:
            self.logger.error(f"Triggered update failed: {e}")
            self.last_triggered_update = {
                'timestamp': datetime.now(timezone.utc),
                'error': str(e),
                'success': False
            }
            raise
            
    async def get_latest_account_state(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest account state from the database.
        
        Returns:
            Latest account state or None if not found
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT balance_data, position_data, equity,
                           available_margin, used_margin, updated_at
                    FROM account_states
                    WHERE user_id = %s AND exchange = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                """
                
                cursor.execute(query, (self.user_id, 'bitmex'))
                row = cursor.fetchone()
                
                if row:
                    balance_data, position_data, equity, available_margin, used_margin, updated_at = row
                    
                    return {
                        'balance_data': balance_data,
                        'position_data': position_data,
                        'equity': float(equity) if equity is not None else 0,
                        'available_margin': float(available_margin) if available_margin is not None else 0,
                        'used_margin': float(used_margin) if used_margin is not None else 0,
                        'updated_at': updated_at,
                        'positions': position_data if isinstance(position_data, list) else []
                    }
        
        return None
        
    async def wait_for_position_change(self, timeout: float = 30.0, poll_interval: float = 2.0) -> bool:
        """
        Wait for a position change to be reflected in the account state.
        
        Args:
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check for changes
            
        Returns:
            True if position changed, False if timeout
        """
        start_time = time.time()
        initial_state = await self.get_latest_account_state()
        initial_positions = len(initial_state.get('positions', [])) if initial_state else 0
        
        while time.time() - start_time < timeout:
            # Trigger an update
            await self.monitoring_service.update_account_state()
            
            # Check for changes
            current_state = await self.get_latest_account_state()
            current_positions = len(current_state.get('positions', [])) if current_state else 0
            
            if current_positions != initial_positions:
                self.logger.info(f"Position change detected: {initial_positions} -> {current_positions}")
                return True
                
            await asyncio.sleep(poll_interval)
            
        self.logger.warning(f"No position change detected after {timeout}s")
        return False
        
    async def verify_trade_execution(self, expected_symbol: str, expected_side: str, 
                                   timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """
        Verify that a specific trade was executed.
        
        Args:
            expected_symbol: Expected trading symbol
            expected_side: Expected position side ('long' or 'short')
            timeout: Maximum time to wait
            
        Returns:
            Position details if found, None otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Update and get latest state
            await self.monitoring_service.update_account_state()
            state = await self.get_latest_account_state()
            
            if state and state.get('positions'):
                for position in state['positions']:
                    symbol = position.get('symbol', '')
                    side = position.get('side', '').lower()
                    
                    # Check if this matches our expected trade
                    if (symbol == expected_symbol or symbol.startswith(expected_symbol.split('/')[0])):
                        if (side == expected_side or 
                            (expected_side == 'long' and side == 'buy') or
                            (expected_side == 'short' and side == 'sell')):
                            self.logger.info(f"Trade verified: {symbol} {side} position found")
                            return position
                            
            await asyncio.sleep(2)
            
        self.logger.warning(f"Could not verify trade execution for {expected_symbol} {expected_side}")
        return None


# Convenience functions for integration
async def create_hybrid_monitor(user_id: str = DEFAULT_USER_ID) -> HybridMonitoringService:
    """Create and start a hybrid monitoring service."""
    service = HybridMonitoringService(user_id)
    await service.start_scheduled_monitoring()
    return service


async def verify_trade_with_monitoring(user_id: str, expected_symbol: str, 
                                     expected_side: str, delay: float = 10.0) -> bool:
    """
    Verify trade execution using triggered monitoring.
    
    Args:
        user_id: User ID
        expected_symbol: Expected symbol
        expected_side: Expected side
        delay: Initial delay before checking
        
    Returns:
        True if trade verified, False otherwise
    """
    service = HybridMonitoringService(user_id)
    
    try:
        # Wait for initial delay
        if delay > 0:
            logger.info(f"Waiting {delay}s for trade to settle...")
            await asyncio.sleep(delay)
            
        # Verify the trade
        position = await service.verify_trade_execution(expected_symbol, expected_side)
        return position is not None
        
    except Exception as e:
        logger.error(f"Error verifying trade: {e}")
        return False