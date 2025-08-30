"""
Account domain model for GGBot trading platform.

Provides unified abstraction over paper trading accounts and live trading
accounts (Hummingbot integration). Handles account lifecycle, balance tracking,
and performance statistics.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from .value_objects import Money


class AccountType(str, Enum):
    """Account execution type enumeration."""
    PAPER = "paper"
    LIVE = "live"


class AccountStatistics(BaseModel):
    """Account performance statistics."""
    total_trades: int = Field(default=0, ge=0, description="Total number of trades executed")
    win_trades: int = Field(default=0, ge=0, description="Number of profitable trades")
    loss_trades: int = Field(default=0, ge=0, description="Number of losing trades")
    open_positions: int = Field(default=0, ge=0, description="Current number of open positions")
    
    @field_validator('win_trades', 'loss_trades')
    @classmethod
    def validate_trade_counts(cls, v, info):
        """Ensure win + loss trades doesn't exceed total trades"""
        if info.data.get('total_trades', 0) > 0:
            win_trades = info.data.get('win_trades', 0) if info.field_name == 'loss_trades' else v
            loss_trades = info.data.get('loss_trades', 0) if info.field_name == 'win_trades' else v
            total_trades = info.data.get('total_trades', 0)
            
            if win_trades + loss_trades > total_trades:
                raise ValueError("Win trades + loss trades cannot exceed total trades")
        
        return v
    
    @property
    def win_rate(self) -> Optional[Decimal]:
        """Calculate win rate percentage (0-100)"""
        if self.total_trades == 0:
            return None
        return Decimal(str(self.win_trades / self.total_trades * 100)).quantize(Decimal('0.1'))
    
    @property
    def completed_trades(self) -> int:
        """Get number of completed trades (win + loss)"""
        return self.win_trades + self.loss_trades


class Account(BaseModel):
    """
    Unified account abstraction for paper and live trading.
    
    Provides consistent interface over:
    - Paper trading: Uses paper_accounts database table
    - Live trading: Future integration with Hummingbot account API
    """
    
    # Core Identity
    account_id: UUID = Field(..., description="Unique account identifier")
    config_id: UUID = Field(..., description="Configuration this account belongs to")
    user_id: UUID = Field(..., description="User who owns this account")
    account_type: AccountType = Field(..., description="Paper or live trading account")
    
    # Financial State
    initial_balance: Money = Field(..., description="Starting account balance")
    current_balance: Money = Field(..., description="Available balance for new trades")
    total_pnl: Money = Field(default_factory=lambda: Money(amount=Decimal("0.00")), 
                           description="Cumulative realized P&L")
    
    # Performance Statistics
    statistics: AccountStatistics = Field(default_factory=AccountStatistics, 
                                        description="Account performance metrics")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), 
                               description="Account creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), 
                               description="Last update timestamp")
    
    @field_validator('current_balance', 'total_pnl')
    @classmethod
    def validate_currency_consistency(cls, v, info):
        """Ensure all money amounts use same currency as initial_balance"""
        initial_balance = info.data.get('initial_balance')
        if initial_balance and v.currency != initial_balance.currency:
            raise ValueError(f"Currency mismatch: {v.currency} != {initial_balance.currency}")
        return v
    
    @property
    def total_return(self) -> Decimal:
        """Calculate total return percentage from initial balance"""
        if self.initial_balance.amount == 0:
            return Decimal('0.00')
        
        total_value = self.current_balance.amount + self.total_pnl.amount
        return ((total_value - self.initial_balance.amount) / self.initial_balance.amount * 100).quantize(Decimal('0.01'))
    
    @property
    def account_equity(self) -> Money:
        """Calculate total account equity (balance + unrealized P&L would be added by caller)"""
        return Money(
            amount=self.current_balance.amount + self.total_pnl.amount,
            currency=self.current_balance.currency
        )
    
    @property
    def is_paper_account(self) -> bool:
        """True if this is a paper trading account"""
        return self.account_type == AccountType.PAPER
    
    @property
    def is_live_account(self) -> bool:
        """True if this is a live trading account"""
        return self.account_type == AccountType.LIVE
    
    def can_afford_trade(self, trade_size: Money) -> bool:
        """
        Check if account has sufficient balance for a trade.
        
        Args:
            trade_size: Required trade size in account currency
            
        Returns:
            True if account can afford the trade
        """
        if trade_size.currency != self.current_balance.currency:
            raise ValueError(f"Currency mismatch: {trade_size.currency} != {self.current_balance.currency}")
        
        return self.current_balance.amount >= trade_size.amount
    
    def reserve_balance(self, amount: Money) -> Money:
        """
        Reserve balance for a trade (reduces available balance).
        
        Args:
            amount: Amount to reserve
            
        Returns:
            New current balance after reservation
            
        Raises:
            ValueError: If insufficient balance or currency mismatch
        """
        if amount.currency != self.current_balance.currency:
            raise ValueError(f"Currency mismatch: {amount.currency} != {self.current_balance.currency}")
        
        if not self.can_afford_trade(amount):
            raise ValueError(f"Insufficient balance: {self.current_balance} < {amount}")
        
        self.current_balance = self.current_balance.subtract(amount)
        self.updated_at = datetime.now(timezone.utc)
        return self.current_balance
    
    def release_balance(self, amount: Money) -> Money:
        """
        Release reserved balance back to available (e.g., after trade closes).
        
        Args:
            amount: Amount to release back to balance
            
        Returns:
            New current balance after release
        """
        if amount.currency != self.current_balance.currency:
            raise ValueError(f"Currency mismatch: {amount.currency} != {self.current_balance.currency}")
        
        self.current_balance = self.current_balance.add(amount)
        self.updated_at = datetime.now(timezone.utc)
        return self.current_balance
    
    def realize_pnl(self, pnl: Money, is_win: bool) -> None:
        """
        Realize profit/loss from a closed trade.
        
        Args:
            pnl: Realized P&L amount (positive for profit, negative for loss)
            is_win: True if trade was profitable
        """
        if pnl.currency != self.current_balance.currency:
            raise ValueError(f"Currency mismatch: {pnl.currency} != {self.current_balance.currency}")
        
        # Update financial state
        self.current_balance = self.current_balance.add(pnl)
        self.total_pnl = self.total_pnl.add(pnl)
        
        # Update statistics
        self.statistics.total_trades += 1
        if is_win:
            self.statistics.win_trades += 1
        else:
            self.statistics.loss_trades += 1
        
        self.updated_at = datetime.now(timezone.utc)
    
    def update_position_count(self, delta: int) -> int:
        """
        Update open position count.
        
        Args:
            delta: Change in position count (+1 for open, -1 for close)
            
        Returns:
            New position count
        """
        self.statistics.open_positions = max(0, self.statistics.open_positions + delta)
        self.updated_at = datetime.now(timezone.utc)
        return self.statistics.open_positions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage or API responses"""
        return {
            'account_id': str(self.account_id),
            'config_id': str(self.config_id),
            'user_id': str(self.user_id),
            'account_type': self.account_type.value,
            'initial_balance': float(self.initial_balance.amount),
            'current_balance': float(self.current_balance.amount),
            'total_pnl': float(self.total_pnl.amount),
            'currency': self.current_balance.currency,
            'open_positions': self.statistics.open_positions,
            'total_trades': self.statistics.total_trades,
            'win_trades': self.statistics.win_trades,
            'loss_trades': self.statistics.loss_trades,
            'win_rate': float(self.statistics.win_rate) if self.statistics.win_rate else None,
            'total_return_pct': float(self.total_return),
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    class Config:
        """Pydantic model configuration"""
        validate_assignment = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: str
        }