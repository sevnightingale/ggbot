"""
Supabase Account Repository - Unified access to paper and live trading accounts via Supabase REST API.

Provides clean abstraction over:
- Paper accounts: Supabase REST API via supabase-py client
- Live accounts: Future Hummingbot API integration
"""

import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from dotenv import load_dotenv
from supabase import create_client, Client

from core.common.logger import logger
from core.domain.models.account import Account, AccountType, AccountStatistics
from core.domain.models.value_objects import Money

# Load environment variables
load_dotenv()


class SupabaseAccountRepository:
    """
    Repository for Account domain model operations using Supabase.
    
    Handles both paper trading accounts (Supabase) and live trading accounts
    (future Hummingbot API integration).
    """
    
    def __init__(self):
        """Initialize the repository with Supabase client"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.debug("Initialized SupabaseAccountRepository")
    
    async def get_by_config_id(self, config_id: str, user_id: str) -> Optional[Account]:
        """
        Get account by configuration ID.
        
        Args:
            config_id: Configuration UUID
            user_id: User UUID
            
        Returns:
            Account domain model or None if not found
        """
        try:
            response = self.supabase.table('paper_accounts').select("*").eq('config_id', config_id).eq('user_id', user_id).execute()
            
            if not response.data:
                logger.debug(f"No account found for config_id={config_id}, user_id={user_id}")
                return None
            
            return self._row_to_domain_model(response.data[0])
                    
        except Exception as e:
            logger.error(f"Failed to get account for config {config_id}: {str(e)}")
            return None
    
    async def get_or_create(self, config_id: str, user_id: str, 
                           initial_balance: Money = None) -> Account:
        """
        Get existing account or create new one for config_id.
        
        Args:
            config_id: Configuration UUID
            user_id: User UUID
            initial_balance: Starting balance (defaults to $10,000 USD)
            
        Returns:
            Account domain model (existing or newly created)
        """
        # Try to get existing account first
        account = await self.get_by_config_id(config_id, user_id)
        if account:
            logger.debug(f"Found existing account for config {config_id}")
            return account
        
        # Create new account
        if initial_balance is None:
            initial_balance = Money(amount=Decimal("10000.00"), currency="USD")
        
        logger.info(f"Creating new paper account for config {config_id} with balance {initial_balance}")
        
        try:
            account_data = {
                'config_id': config_id,
                'user_id': user_id,
                'initial_balance': float(initial_balance.amount),
                'current_balance': float(initial_balance.amount),
                'total_pnl': 0.00,
                'open_positions': 0,
                'total_trades': 0,
                'win_trades': 0,
                'loss_trades': 0
            }
            
            response = self.supabase.table('paper_accounts').insert(account_data).execute()
            
            if response.data:
                account = self._row_to_domain_model(response.data[0])
                logger.info(f"Created new paper account {account.account_id} for config {config_id}")
                return account
            else:
                raise Exception("No data returned from insert operation")
                    
        except Exception as e:
            logger.error(f"Failed to create account for config {config_id}: {str(e)}")
            raise
    
    async def save(self, account: Account) -> bool:
        """
        Save account changes to persistence layer.
        
        Args:
            account: Account domain model to save
            
        Returns:
            True if save was successful
        """
        if account.account_type == AccountType.PAPER:
            return await self._save_paper_account(account)
        elif account.account_type == AccountType.LIVE:
            return await self._save_live_account(account)
        else:
            logger.error(f"Unknown account type: {account.account_type}")
            return False
    
    async def _save_paper_account(self, account: Account) -> bool:
        """Save paper account to Supabase"""
        try:
            update_data = {
                'current_balance': float(account.current_balance.amount),
                'total_pnl': float(account.total_pnl.amount),
                'open_positions': account.statistics.open_positions,
                'total_trades': account.statistics.total_trades,
                'win_trades': account.statistics.win_trades,
                'loss_trades': account.statistics.loss_trades,
                'updated_at': account.updated_at.isoformat()
            }
            
            response = self.supabase.table('paper_accounts').update(update_data).eq('account_id', str(account.account_id)).execute()
            
            if response.data:
                logger.debug(f"Saved paper account {account.account_id}")
                return True
            else:
                logger.warning(f"No rows updated for account {account.account_id}")
                return False
                    
        except Exception as e:
            logger.error(f"Failed to save paper account {account.account_id}: {str(e)}")
            return False
    
    async def _save_live_account(self, account: Account) -> bool:
        """Save live account via Hummingbot API (future implementation)"""
        # TODO: Implement Hummingbot API integration
        logger.warning("Live account save not implemented yet - requires Hummingbot integration")
        return False
    
    async def get_all_for_user(self, user_id: str) -> List[Account]:
        """
        Get all accounts for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of account domain models
        """
        accounts = []
        
        try:
            response = self.supabase.table('paper_accounts').select("*").eq('user_id', user_id).order('created_at', desc=True).execute()
            
            for row in response.data:
                accounts.append(self._row_to_domain_model(row))
                        
        except Exception as e:
            logger.error(f"Failed to get accounts for user {user_id}: {str(e)}")
        
        return accounts
    
    async def delete(self, account_id: str) -> bool:
        """
        Delete an account.
        
        Args:
            account_id: Account UUID to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            response = self.supabase.table('paper_accounts').delete().eq('account_id', account_id).execute()
            
            if response.data:
                logger.info(f"Deleted paper account {account_id}")
                return True
            else:
                logger.warning(f"No account found to delete: {account_id}")
                return False
                    
        except Exception as e:
            logger.error(f"Failed to delete account {account_id}: {str(e)}")
            return False
    
    def _row_to_domain_model(self, row: Dict[str, Any]) -> Account:
        """
        Convert Supabase row to Account domain model.
        
        Args:
            row: Row from paper_accounts table
            
        Returns:
            Account domain model
        """
        # Extract currency from initial balance (assume USD for paper accounts)
        currency = "USD"  # Paper accounts are always USD initially
        
        return Account(
            account_id=UUID(str(row['account_id'])),
            config_id=UUID(str(row['config_id'])),
            user_id=UUID(str(row['user_id'])),
            account_type=AccountType.PAPER,
            initial_balance=Money(amount=Decimal(str(row['initial_balance'])), currency=currency),
            current_balance=Money(amount=Decimal(str(row['current_balance'])), currency=currency),
            total_pnl=Money(amount=Decimal(str(row['total_pnl'])), currency=currency),
            statistics=AccountStatistics(
                open_positions=row['open_positions'],
                total_trades=row['total_trades'],
                win_trades=row['win_trades'],
                loss_trades=row['loss_trades']
            ),
            created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if row.get('created_at') else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')) if row.get('updated_at') else datetime.now(timezone.utc)
        )


# Create singleton instance
supabase_account_repo = SupabaseAccountRepository()