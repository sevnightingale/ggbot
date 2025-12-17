"""
Account Snapshot Domain Model

Represents a point-in-time snapshot of an account's state across all trading modes.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from .metrics_calculator import AccountMetricsCalculator


@dataclass
class AccountSnapshot:
    """
    Unified account state snapshot for all trading modes.

    Represents the account balance, P&L, and performance metrics at a specific point in time.
    Works for paper, Symphony, and AsterDEX trading modes.
    """
    # Identity
    snapshot_id: Optional[str]
    config_id: str
    user_id: str
    trading_mode: str  # 'paper', 'symphony', 'aster'
    timestamp: datetime

    # Balance (current_balance may be None for Symphony)
    current_balance: Optional[Decimal]
    available_balance: Optional[Decimal]
    margin_used: Optional[Decimal]

    # P&L
    total_pnl: Decimal
    realized_pnl: Optional[Decimal]
    unrealized_pnl: Optional[Decimal]

    # Performance
    total_trades: int
    win_trades: int
    loss_trades: int
    win_rate: Optional[Decimal]

    # Positions
    open_positions: int
    position_value: Optional[Decimal]
    total_exposure: Optional[Decimal]

    # Advanced metrics (optional)
    avg_win: Optional[Decimal] = None
    avg_loss: Optional[Decimal] = None
    largest_win: Optional[Decimal] = None
    largest_loss: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None

    # Metadata
    raw_data: Optional[Dict[str, Any]] = None
    balance_change_pct: Optional[Decimal] = None
    is_heartbeat: bool = False

    @property
    def has_balance(self) -> bool:
        """Check if this snapshot includes balance data."""
        return self.current_balance is not None

    @property
    def has_open_positions(self) -> bool:
        """Check if account has open positions."""
        return self.open_positions > 0

    @property
    def total_equity(self) -> Optional[Decimal]:
        """
        Calculate Total Equity - the true net worth of the account.

        This represents what the AI "sees" at this moment in time.

        For paper mode:
            Total Equity = current_balance + unrealized_pnl

            Note: current_balance already includes margin_used
            (current_balance = available_balance + margin_used)

        For live modes (Symphony/Aster):
            Total Equity = total_pnl
            (already includes realized + unrealized P&L)

        Returns:
            Decimal representing total account equity, or None if insufficient data
        """
        if self.trading_mode == 'paper':
            # Paper trading: use centralized calculator
            if self.current_balance is None:
                return None

            return AccountMetricsCalculator.calculate_total_equity(
                self.current_balance,
                self.unrealized_pnl
            )

        else:
            # Live modes (symphony/aster): total_pnl already includes everything
            return self.total_pnl

    @property
    def return_pct(self) -> Optional[Decimal]:
        """
        Calculate return percentage from initial equity.

        Formula: ((current_equity - initial_equity) / initial_equity) * 100

        Where initial_equity is calculated as: total_equity - total_pnl

        This gives the performance percentage since account inception.
        """
        equity = self.total_equity
        if equity is None:
            return None

        # Calculate initial equity by subtracting all accumulated P&L
        initial_equity = AccountMetricsCalculator.calculate_initial_equity_from_current(
            equity,
            self.total_pnl
        )

        if initial_equity <= 0:
            return None

        return AccountMetricsCalculator.calculate_performance_percent(
            equity,
            initial_equity
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'snapshot_id': self.snapshot_id,
            'config_id': self.config_id,
            'user_id': self.user_id,
            'trading_mode': self.trading_mode,
            'timestamp': self.timestamp.isoformat(),
            'current_balance': float(self.current_balance) if self.current_balance else None,
            'available_balance': float(self.available_balance) if self.available_balance else None,
            'margin_used': float(self.margin_used) if self.margin_used else None,
            'total_pnl': float(self.total_pnl),
            'realized_pnl': float(self.realized_pnl) if self.realized_pnl else None,
            'unrealized_pnl': float(self.unrealized_pnl) if self.unrealized_pnl else None,
            'total_trades': self.total_trades,
            'win_trades': self.win_trades,
            'loss_trades': self.loss_trades,
            'win_rate': float(self.win_rate) if self.win_rate else None,
            'open_positions': self.open_positions,
            'position_value': float(self.position_value) if self.position_value else None,
            'total_exposure': float(self.total_exposure) if self.total_exposure else None,
            'avg_win': float(self.avg_win) if self.avg_win else None,
            'avg_loss': float(self.avg_loss) if self.avg_loss else None,
            'largest_win': float(self.largest_win) if self.largest_win else None,
            'largest_loss': float(self.largest_loss) if self.largest_loss else None,
            'sharpe_ratio': float(self.sharpe_ratio) if self.sharpe_ratio else None,
            'max_drawdown': float(self.max_drawdown) if self.max_drawdown else None,
            'is_heartbeat': self.is_heartbeat,
            'return_pct': float(self.return_pct) if self.return_pct else None
        }


class AccountAdapter(ABC):
    """
    Abstract adapter interface for fetching account state from different trading modes.

    Implementations:
    - PaperAccountAdapter: Queries paper_accounts and paper_trades tables
    - SymphonyAccountAdapter: Calls Symphony API
    - AsterAccountAdapter: Calls AsterDEX API
    """

    @abstractmethod
    async def get_current_snapshot(self, config_id: str) -> Optional[AccountSnapshot]:
        """
        Get current account state as a snapshot.

        Args:
            config_id: Configuration ID

        Returns:
            AccountSnapshot if successful, None otherwise
        """
        pass

    @abstractmethod
    async def supports_balance(self) -> bool:
        """
        Check if this adapter can provide balance data.

        Returns:
            True if balance is available, False otherwise (e.g., Symphony currently doesn't provide balance)
        """
        pass
