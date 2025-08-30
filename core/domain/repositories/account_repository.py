"""
Account Repository - Unified access to paper and live trading accounts.

Provides clean abstraction over:
- Paper accounts: Direct database access via paper_accounts table
- Live accounts: Future Hummingbot API integration
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
import psycopg2
from psycopg2.extras import RealDictCursor

from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
from core.common.logger import logger
from core.domain.models.account import Account, AccountType, AccountStatistics
from core.domain.models.value_objects import Money


class AccountRepository:
    """
    Repository for Account domain model operations.
    
    Handles both paper trading accounts (database) and live trading accounts
    (future Hummingbot API integration).
    """
    
    def __init__(self):
        """Initialize the repository"""
        logger.debug("Initialized AccountRepository")
    
    def _get_db_connection(self):
        """Get database connection for paper account operations"""
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
    
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
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM paper_accounts 
                        WHERE config_id = %s AND user_id = %s
                    """, (config_id, user_id))
                    
                    row = cur.fetchone()
                    
                    if not row:
                        logger.debug(f"No account found for config_id={config_id}, user_id={user_id}")
                        return None
                    
                    return self._row_to_domain_model(row)
                    
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
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Insert new paper account
                    cur.execute("""
                        INSERT INTO paper_accounts 
                        (config_id, user_id, initial_balance, current_balance, total_pnl, 
                         open_positions, total_trades, win_trades, loss_trades)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING *
                    """, (
                        config_id, user_id, 
                        float(initial_balance.amount), float(initial_balance.amount), 0.00,
                        0, 0, 0, 0
                    ))
                    
                    row = cur.fetchone()
                    conn.commit()
                    
                    account = self._row_to_domain_model(row)
                    logger.info(f"Created new paper account {account.account_id} for config {config_id}")
                    return account
                    
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
        """Save paper account to database"""
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE paper_accounts 
                        SET current_balance = %s,
                            total_pnl = %s,
                            open_positions = %s,
                            total_trades = %s,
                            win_trades = %s,
                            loss_trades = %s,
                            updated_at = %s
                        WHERE account_id = %s
                    """, (
                        float(account.current_balance.amount),
                        float(account.total_pnl.amount),
                        account.statistics.open_positions,
                        account.statistics.total_trades,
                        account.statistics.win_trades,
                        account.statistics.loss_trades,
                        account.updated_at,
                        str(account.account_id)
                    ))
                    
                    if cur.rowcount == 0:
                        logger.warning(f"No rows updated for account {account.account_id}")
                        return False
                    
                    conn.commit()
                    logger.debug(f"Saved paper account {account.account_id}")
                    return True
                    
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
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM paper_accounts 
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                    """, (user_id,))
                    
                    rows = cur.fetchall()
                    
                    for row in rows:
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
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Note: This will cascade delete related paper_trades due to FK constraint
                    cur.execute("""
                        DELETE FROM paper_accounts 
                        WHERE account_id = %s
                    """, (account_id,))
                    
                    if cur.rowcount == 0:
                        logger.warning(f"No account found to delete: {account_id}")
                        return False
                    
                    conn.commit()
                    logger.info(f"Deleted paper account {account_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to delete account {account_id}: {str(e)}")
            return False
    
    def _row_to_domain_model(self, row: Dict[str, Any]) -> Account:
        """
        Convert database row to Account domain model.
        
        Args:
            row: Database row from paper_accounts table
            
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
            created_at=row['created_at'].replace(tzinfo=timezone.utc) if row.get('created_at') else datetime.now(timezone.utc),
            updated_at=row['updated_at'].replace(tzinfo=timezone.utc) if row.get('updated_at') else datetime.now(timezone.utc)
        )


# Create singleton instance
account_repo = AccountRepository()