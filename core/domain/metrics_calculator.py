"""
Centralized account metrics calculator for GGBot trading platform.

Provides standardized formulas for calculating account performance metrics.
All metric calculations should use these functions to ensure consistency
across the platform (domain models, APIs, monitoring, frontend).

Eliminates formula duplication and ensures single source of truth for
metric definitions.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple


class AccountMetricsCalculator:
    """
    Centralized calculator for account performance metrics.

    All methods are static and stateless - no instance needed.
    Use these methods instead of duplicating formulas across codebase.
    """

    @staticmethod
    def calculate_total_equity(
        current_balance: Decimal,
        unrealized_pnl: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate total account equity.

        Formula: total_equity = current_balance + unrealized_pnl

        For paper trading:
            - current_balance includes margin_used
            - unrealized_pnl is sum of all open positions' P&L

        For live trading (Symphony/Aster):
            - total_pnl already includes everything
            - use total_pnl directly as equity

        Args:
            current_balance: Account balance including reserved margin
            unrealized_pnl: Unrealized P&L from open positions (None = 0)

        Returns:
            Total equity value
        """
        if unrealized_pnl is None:
            unrealized_pnl = Decimal('0')
        return current_balance + unrealized_pnl

    @staticmethod
    def calculate_available_balance(
        current_balance: Decimal,
        margin_used: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate available balance for new trades.

        Formula: available_balance = current_balance - margin_used

        Args:
            current_balance: Total account balance
            margin_used: Balance reserved for open positions (None = 0)

        Returns:
            Available balance for new trades
        """
        if margin_used is None:
            margin_used = Decimal('0')
        return current_balance - margin_used

    @staticmethod
    def calculate_performance_percent(
        current_equity: Decimal,
        initial_equity: Decimal
    ) -> Optional[Decimal]:
        """
        Calculate performance percentage from initial equity.

        Formula: performance_pct = ((current_equity - initial_equity) / initial_equity) * 100

        Returns value in percentage format (e.g., 15.25 = +15.25%, -5.00 = -5.00%)

        Args:
            current_equity: Current total equity
            initial_equity: Starting equity (initial balance)

        Returns:
            Performance percentage, or None if initial_equity is zero
        """
        if initial_equity == 0:
            return None

        return ((current_equity - initial_equity) / initial_equity * 100).quantize(
            Decimal('0.01')
        )

    @staticmethod
    def calculate_return_on_investment(
        total_pnl: Decimal,
        initial_equity: Decimal
    ) -> Optional[Decimal]:
        """
        Calculate ROI percentage based on realized+unrealized P&L.

        Formula: roi_pct = (total_pnl / initial_equity) * 100

        This is equivalent to performance_percent when:
            current_equity = initial_equity + total_pnl

        Args:
            total_pnl: Total P&L (realized + unrealized)
            initial_equity: Starting equity (initial balance)

        Returns:
            ROI percentage, or None if initial_equity is zero
        """
        if initial_equity == 0:
            return None

        return (total_pnl / initial_equity * 100).quantize(Decimal('0.01'))

    @staticmethod
    def calculate_win_rate_percent(
        win_trades: int,
        total_trades: int
    ) -> Optional[Decimal]:
        """
        Calculate win rate as percentage.

        Formula: win_rate_pct = (win_trades / total_trades) * 100

        Returns value in percentage format (0-100), not decimal (0-1).

        Args:
            win_trades: Number of winning trades
            total_trades: Total number of trades

        Returns:
            Win rate percentage (0-100), or None if no trades
        """
        if total_trades == 0:
            return None

        return (Decimal(win_trades) / Decimal(total_trades) * 100).quantize(
            Decimal('0.1')
        )

    @staticmethod
    def calculate_win_rate_decimal(
        win_trades: int,
        total_trades: int
    ) -> Optional[Decimal]:
        """
        Calculate win rate as decimal.

        Formula: win_rate = win_trades / total_trades

        Returns value in decimal format (0-1), not percentage (0-100).

        Args:
            win_trades: Number of winning trades
            total_trades: Total number of trades

        Returns:
            Win rate decimal (0-1), or None if no trades
        """
        if total_trades == 0:
            return None

        return (Decimal(win_trades) / Decimal(total_trades)).quantize(
            Decimal('0.001')
        )

    @staticmethod
    def calculate_realized_pnl(
        total_pnl: Decimal,
        unrealized_pnl: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate realized P&L only (excluding unrealized).

        Formula: realized_pnl = total_pnl - unrealized_pnl

        Args:
            total_pnl: Total P&L (realized + unrealized)
            unrealized_pnl: Unrealized P&L from open positions (None = 0)

        Returns:
            Realized P&L only
        """
        if unrealized_pnl is None:
            unrealized_pnl = Decimal('0')
        return total_pnl - unrealized_pnl

    @staticmethod
    def calculate_initial_equity_from_current(
        current_balance: Decimal,
        total_pnl: Decimal
    ) -> Decimal:
        """
        Reverse-calculate initial equity from current state.

        Formula: initial_equity = current_balance - total_pnl

        This assumes current_balance represents total equity that has
        changed only due to P&L (no deposits/withdrawals).

        Args:
            current_balance: Current account balance
            total_pnl: Total P&L accumulated

        Returns:
            Calculated initial equity
        """
        return current_balance - total_pnl

    @staticmethod
    def calculate_twr(
        equity_points: List[Tuple[datetime, float]],
        flows: List[Tuple[datetime, float]]
    ) -> List[Tuple[datetime, float]]:
        """
        Compute time-weighted return series.

        TWR eliminates the impact of deposits/withdrawals by chaining
        sub-period returns around each cash flow event. A deposit of $500
        won't inflate the return — only actual trading performance counts.

        Args:
            equity_points: [(timestamp, equity_value), ...] sorted by time
            flows: [(timestamp, signed_amount), ...] sorted by time.
                   Deposits are positive, withdrawals are negative.

        Returns:
            [(timestamp, pct_return), ...] where pct_return is cumulative
            TWR percentage (e.g., 5.0 = +5%).
        """
        if not equity_points:
            return []

        if len(equity_points) == 1:
            return [(equity_points[0][0], 0.0)]

        # Sort flows by time for sequential processing
        sorted_flows = sorted(flows, key=lambda f: f[0])
        flow_idx = 0

        cumulative_twr = 1.0
        period_start_equity = equity_points[0][1]
        result = [(equity_points[0][0], 0.0)]

        for i in range(1, len(equity_points)):
            current_time = equity_points[i][0]
            current_equity = equity_points[i][1]
            prev_equity = equity_points[i - 1][1]

            # Process any flows that occurred between previous and current snapshot
            while flow_idx < len(sorted_flows) and sorted_flows[flow_idx][0] <= current_time:
                flow_time, flow_amount = sorted_flows[flow_idx]

                # Only process flows that are after the previous equity point
                if flow_time > equity_points[i - 1][0]:
                    # Close the sub-period at the pre-flow equity
                    if period_start_equity != 0:
                        period_return = prev_equity / period_start_equity
                        cumulative_twr *= period_return

                    # New period starts after the flow
                    period_start_equity = prev_equity + flow_amount

                flow_idx += 1

            # Current TWR value
            if period_start_equity != 0:
                twr_value = (cumulative_twr * (current_equity / period_start_equity)) - 1.0
            else:
                twr_value = 0.0

            result.append((current_time, round(twr_value * 100, 4)))

        return result
