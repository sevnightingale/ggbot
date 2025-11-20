"""
Base exchange adapter interface.

All exchange adapters should implement this interface.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class OrderResponse:
    """Response from placing an order."""
    order_id: str
    status: str  # "open", "filled", "cancelled", "rejected"
    filled_size: Decimal = Decimal("0")
    filled_price: Optional[Decimal] = None
    error_message: Optional[str] = None


@dataclass
class Fill:
    """A fill notification from the exchange."""
    order_id: str
    filled_size: Decimal
    filled_price: Decimal
    side: str  # "buy" or "sell"
    timestamp: float
    fee: Decimal = Decimal("0")


class ExchangeAdapter(ABC):
    """
    Abstract base class for exchange adapters.

    All exchanges should implement these methods to be compatible
    with the market maker engine.
    """

    @abstractmethod
    def get_orderbook(self, symbol: str, depth: int = 10):
        """
        Fetch current orderbook for a trading pair.

        Args:
            symbol: Trading pair (e.g., "CHOG/USDC")
            depth: Number of levels to fetch per side

        Returns:
            Orderbook instance
        """
        pass

    @abstractmethod
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        price: Decimal,
        size: Decimal
    ) -> OrderResponse:
        """
        Place a limit order.

        Args:
            symbol: Trading pair
            side: "buy" or "sell"
            price: Limit price
            size: Order size in base currency

        Returns:
            OrderResponse with order_id and status
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a single order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled successfully
        """
        pass

    @abstractmethod
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """
        Cancel all open orders (optionally filtered by symbol).

        Args:
            symbol: Optional symbol filter

        Returns:
            Number of orders cancelled
        """
        pass

    @abstractmethod
    def get_balances(self) -> Dict[str, Decimal]:
        """
        Get current account balances.

        Returns:
            Dict mapping currency to balance
            Example: {"CHOG": Decimal("5000000"), "USDC": Decimal("5000")}
        """
        pass

    @abstractmethod
    def get_fills(self, since: Optional[float] = None) -> List[Fill]:
        """
        Get recent fills (executed orders).

        Args:
            since: Unix timestamp to fetch fills after (optional)

        Returns:
            List of Fill objects
        """
        pass

    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get all open orders.

        Args:
            symbol: Optional symbol filter

        Returns:
            List of open orders
        """
        pass
