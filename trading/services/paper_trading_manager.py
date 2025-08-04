"""
Paper Trading Manager

Manages isolated paper trading accounts per config_id for strategy testing.
Integrates with Hummingbot's paper trading infrastructure.
"""

import os
from decimal import Decimal
from typing import Dict, Optional
from core.common.logger import logger
from .instance_manager import HummingbotInstanceManager


class PaperTradingManager:
    """
    Manage isolated paper trading accounts per config_id.
    
    Each configuration gets:
    - $10,000 USDT starting balance
    - Isolated paper trading account
    - Independent performance tracking
    - Account reset capabilities
    """
    
    INITIAL_BALANCE = Decimal("10000.0")  # $10,000 USDT per config
    
    def __init__(self, hummingbot_api_url: str = None):
        """Initialize paper trading manager."""
        self.api_url = hummingbot_api_url or os.getenv("HUMMINGBOT_API_HOST", "http://localhost:15888")
        self.instance_manager = HummingbotInstanceManager()
        
        logger.bind(service="paper_trading_manager").info(
            f"PaperTradingManager initialized with API: {self.api_url}"
        )
    
    async def initialize_paper_account(self, account_name: str, config_id: str) -> bool:
        """
        Initialize paper trading account in Hummingbot.
        
        This would normally create account_state and token_state entries
        in Hummingbot's database, but for now we'll rely on Hummingbot's
        built-in paper trading initialization.
        
        Args:
            account_name: Paper account name (e.g., "paper_ggbot_user123_conf456")
            config_id: Configuration UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.bind(service="paper_trading_manager").info(
                f"Initializing paper account {account_name} for config {config_id}"
            )
            
            # For Phase 1, we rely on Hummingbot's built-in paper trading
            # The Position Executor will automatically create paper accounts
            # when deployed with paper_trade_enabled: true
            
            # Future enhancement: Create explicit account entries in Hummingbot DB
            # via direct database connection to ensure $10k starting balance
            
            logger.bind(service="paper_trading_manager").info(
                f"Paper account {account_name} initialized with ${self.INITIAL_BALANCE} balance"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize paper account {account_name}: {e}")
            return False
    
    async def reset_paper_account(self, config_id: str) -> bool:
        """
        Reset paper account balance to initial amount.
        
        Args:
            config_id: Configuration UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            mapping = await self.instance_manager.get_mapping(config_id)
            if not mapping:
                logger.error(f"No instance mapping found for config {config_id}")
                return False
            
            account_name = mapping['hummingbot_account']
            
            logger.bind(service="paper_trading_manager").info(
                f"Resetting paper account {account_name} to ${self.INITIAL_BALANCE}"
            )
            
            # Re-initialize the account (this would reset balances)
            success = await self.initialize_paper_account(account_name, config_id)
            
            if success:
                logger.bind(service="paper_trading_manager").info(
                    f"Successfully reset paper account {account_name}"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reset paper account for config {config_id}: {e}")
            return False
    
    async def get_account_balance(self, config_id: str) -> Dict[str, float]:
        """
        Get current paper trading balance for a config.
        
        Args:
            config_id: Configuration UUID
            
        Returns:
            Dict with balance information
        """
        try:
            mapping = await self.instance_manager.get_mapping(config_id)
            if not mapping:
                logger.warning(f"No instance mapping found for config {config_id}")
                return {
                    'token': 'USDT',
                    'units': 0.0,
                    'available_units': 0.0,
                    'value': 0.0
                }
            
            account_name = mapping['hummingbot_account']
            
            # For Phase 1, return default balance
            # Future enhancement: Query Hummingbot's token_states table
            default_balance = {
                'token': 'USDT',
                'units': float(self.INITIAL_BALANCE),
                'available_units': float(self.INITIAL_BALANCE),
                'value': float(self.INITIAL_BALANCE)
            }
            
            logger.bind(service="paper_trading_manager").debug(
                f"Retrieved balance for {account_name}: ${default_balance['value']}"
            )
            
            return default_balance
            
        except Exception as e:
            logger.error(f"Failed to get account balance for config {config_id}: {e}")
            return {
                'token': 'USDT',
                'units': 0.0,
                'available_units': 0.0,
                'value': 0.0
            }
    
    async def get_account_performance(self, config_id: str) -> Dict[str, any]:
        """
        Get performance metrics for a paper trading account.
        
        Args:
            config_id: Configuration UUID
            
        Returns:
            Dict with performance metrics
        """
        try:
            mapping = await self.instance_manager.get_mapping(config_id)
            if not mapping:
                return {
                    'account_name': None,
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'current_balance': float(self.INITIAL_BALANCE)
                }
            
            account_name = mapping['hummingbot_account']
            balance = await self.get_account_balance(config_id)
            
            # Future enhancement: Query Hummingbot's orders/trades tables
            # for actual performance metrics
            
            performance = {
                'account_name': account_name,
                'instance_name': mapping['instance_name'],
                'total_trades': 0,  # TODO: Query from Hummingbot DB
                'win_rate': 0.0,    # TODO: Calculate from trade history
                'total_pnl': 0.0,   # TODO: Sum from position_snapshots
                'current_balance': balance['value'],
                'initial_balance': float(self.INITIAL_BALANCE)
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"Failed to get performance for config {config_id}: {e}")
            return {
                'account_name': None,
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'current_balance': float(self.INITIAL_BALANCE)
            }
    
    async def list_all_accounts(self, user_id: Optional[str] = None) -> list:
        """
        List all paper trading accounts.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            List of account information
        """
        try:
            mappings = await self.instance_manager.list_active_mappings(user_id)
            accounts = []
            
            for mapping in mappings:
                performance = await self.get_account_performance(mapping['config_id'])
                
                account_info = {
                    'config_id': mapping['config_id'],
                    'config_name': mapping.get('config_name', 'Unnamed Config'),
                    'instance_name': mapping['instance_name'],
                    'account_name': mapping['hummingbot_account'],
                    'balance': performance['current_balance'],
                    'total_trades': performance['total_trades'],
                    'pnl': performance['total_pnl'],
                    'status': mapping['status']
                }
                
                accounts.append(account_info)
            
            return accounts
            
        except Exception as e:
            logger.error(f"Failed to list accounts: {e}")
            return []


# Utility functions for integration with HummingbotExecutionAdapter

async def ensure_paper_account_ready(config_id: str, user_id: str) -> str:
    """
    Ensure paper trading account is ready for a config.
    
    Args:
        config_id: Configuration UUID
        user_id: User UUID
        
    Returns:
        Account name for the paper trading account
    """
    manager = PaperTradingManager()
    instance_manager = HummingbotInstanceManager()
    
    # Ensure instance mapping exists
    mapping = await instance_manager.ensure_mapping(user_id, config_id)
    account_name = mapping['hummingbot_account']
    
    # Initialize paper account
    await manager.initialize_paper_account(account_name, config_id)
    
    return account_name