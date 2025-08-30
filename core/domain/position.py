"""
Position Domain Model

Represents a trading position with complete lifecycle management.
Handles position states, P&L calculations, and risk management.
Integrates with paper trading and live trading systems.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from decimal import Decimal
import uuid

from .models.value_objects import Symbol, Money, Confidence


class PositionStatus(Enum):
    """Possible states of a trading position."""
    PENDING = "pending"          # Order placed but not filled
    OPEN = "open"               # Position is active
    CLOSED = "closed"           # Position closed normally
    LIQUIDATED = "liquidated"   # Position force-closed by exchange
    CANCELLED = "cancelled"     # Order cancelled before fill


class PositionSide(Enum):
    """Direction of the position."""
    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class PriceLevel:
    """Value object representing a price level with timestamp."""
    price: Decimal
    timestamp: datetime
    
    def __post_init__(self):
        if self.price <= 0:
            raise ValueError("Price must be positive")
    
    @property
    def age_seconds(self) -> float:
        """Get age of this price level in seconds."""
        return (datetime.now() - self.timestamp).total_seconds()
    
    def is_stale(self, max_age_seconds: int = 300) -> bool:
        """Check if price level is stale (default 5 minutes)."""
        return self.age_seconds > max_age_seconds


@dataclass(frozen=True)
class PositionMetrics:
    """Value object containing position performance metrics."""
    unrealized_pnl: Money
    unrealized_pnl_pct: Decimal
    realized_pnl: Money
    total_pnl: Money
    max_profit: Money
    max_loss: Money
    current_risk_reward_ratio: Optional[Decimal]
    time_in_position_hours: float
    
    @property
    def is_profitable(self) -> bool:
        """Check if position is currently profitable."""
        return self.unrealized_pnl.amount > 0
    
    @property
    def is_losing(self) -> bool:
        """Check if position is currently losing money."""
        return self.unrealized_pnl.amount < 0
    
    def hit_stop_loss(self, stop_loss_pct: Decimal) -> bool:
        """Check if position has hit stop loss threshold."""
        return self.unrealized_pnl_pct <= -abs(stop_loss_pct)
    
    def hit_take_profit(self, take_profit_pct: Decimal) -> bool:
        """Check if position has hit take profit threshold.""" 
        return self.unrealized_pnl_pct >= take_profit_pct


@dataclass
class Position:
    """
    Entity representing a trading position with full lifecycle management.
    
    Handles both paper trading and live trading positions with unified interface.
    Provides risk management, P&L tracking, and position lifecycle methods.
    """
    trade_id: str
    config_id: str  # Links to bot configuration
    symbol: Symbol
    side: PositionSide
    status: PositionStatus
    
    # Position sizing
    size_usd: Money
    leverage: Decimal
    collateral_amount: Money
    
    # Price levels
    entry_price: PriceLevel
    current_price: Optional[PriceLevel] = None
    stop_loss_price: Optional[PriceLevel] = None
    take_profit_price: Optional[PriceLevel] = None
    
    # Execution details
    exchange: str = "paper"  # paper, bitmex, binance, etc.
    order_id: Optional[str] = None
    execution_details: dict = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Strategy context
    entry_confidence: Optional[Confidence] = None
    entry_reasoning: str = ""
    
    def __post_init__(self):
        """Validate position after initialization."""
        if not self.trade_id:
            self.trade_id = str(uuid.uuid4())
        
        # Validate size and collateral
        if self.size_usd.amount <= 0:
            raise ValueError("Position size must be positive")
        
        if self.leverage < 1:
            raise ValueError("Leverage must be at least 1x")
        
        # Validate price levels
        if self.stop_loss_price and self.take_profit_price:
            if self.side == PositionSide.LONG:
                if self.stop_loss_price.price >= self.entry_price.price:
                    raise ValueError("Long stop loss must be below entry price")
                if self.take_profit_price.price <= self.entry_price.price:
                    raise ValueError("Long take profit must be above entry price")
            else:  # SHORT
                if self.stop_loss_price.price <= self.entry_price.price:
                    raise ValueError("Short stop loss must be above entry price") 
                if self.take_profit_price.price >= self.entry_price.price:
                    raise ValueError("Short take profit must be below entry price")
    
    @property
    def is_active(self) -> bool:
        """Check if position is currently active."""
        return self.status == PositionStatus.OPEN
    
    @property
    def is_pending(self) -> bool:
        """Check if position is pending execution."""
        return self.status == PositionStatus.PENDING
    
    @property
    def is_closed(self) -> bool:
        """Check if position has been closed."""
        return self.status in [PositionStatus.CLOSED, PositionStatus.LIQUIDATED]
    
    @property
    def time_in_position(self) -> timedelta:
        """Get time spent in position."""
        if not self.opened_at:
            return timedelta(0)
        end_time = self.closed_at or datetime.now()
        return end_time - self.opened_at
    
    def calculate_metrics(self) -> Optional[PositionMetrics]:
        """Calculate current position metrics."""
        if not self.current_price or not self.is_active:
            return None
        
        # Calculate P&L based on position side
        price_diff = self.current_price.price - self.entry_price.price
        if self.side == PositionSide.SHORT:
            price_diff = -price_diff  # Invert for short positions
        
        # Calculate unrealized P&L
        position_size_base = self.size_usd.amount / self.entry_price.price
        unrealized_pnl_amount = price_diff * position_size_base
        unrealized_pnl = Money(unrealized_pnl_amount, self.size_usd.currency)
        
        # Calculate percentage
        unrealized_pnl_pct = (price_diff / self.entry_price.price) * 100
        
        # For now, no realized P&L (position still open)
        realized_pnl = Money(Decimal('0'), self.size_usd.currency)
        total_pnl = unrealized_pnl
        
        # Calculate risk/reward ratio if we have stop loss and take profit
        current_risk_reward = None
        if self.stop_loss_price and self.take_profit_price:
            risk = abs(self.entry_price.price - self.stop_loss_price.price)
            reward = abs(self.take_profit_price.price - self.entry_price.price)
            if risk > 0:
                current_risk_reward = reward / risk
        
        # TODO: Track max profit/loss over time (would need historical data)
        max_profit = unrealized_pnl if unrealized_pnl.amount > 0 else Money(Decimal('0'), self.size_usd.currency)
        max_loss = unrealized_pnl if unrealized_pnl.amount < 0 else Money(Decimal('0'), self.size_usd.currency)
        
        return PositionMetrics(
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            realized_pnl=realized_pnl,
            total_pnl=total_pnl,
            max_profit=max_profit,
            max_loss=max_loss,
            current_risk_reward_ratio=current_risk_reward,
            time_in_position_hours=self.time_in_position.total_seconds() / 3600
        )
    
    def update_current_price(self, new_price: Decimal) -> None:
        """Update the current market price."""
        self.current_price = PriceLevel(new_price, datetime.now())
    
    def should_close_on_stop_loss(self) -> bool:
        """Check if position should be closed due to stop loss."""
        if not self.stop_loss_price or not self.current_price:
            return False
        
        if self.side == PositionSide.LONG:
            return self.current_price.price <= self.stop_loss_price.price
        else:  # SHORT
            return self.current_price.price >= self.stop_loss_price.price
    
    def should_close_on_take_profit(self) -> bool:
        """Check if position should be closed due to take profit."""
        if not self.take_profit_price or not self.current_price:
            return False
        
        if self.side == PositionSide.LONG:
            return self.current_price.price >= self.take_profit_price.price
        else:  # SHORT
            return self.current_price.price <= self.take_profit_price.price
    
    def close_position(self, close_price: Decimal, reason: str = "manual") -> None:
        """Close the position with final price."""
        if self.is_closed:
            raise ValueError("Position is already closed")
        
        self.current_price = PriceLevel(close_price, datetime.now())
        self.closed_at = datetime.now()
        
        # Update status based on reason
        if reason == "liquidated":
            self.status = PositionStatus.LIQUIDATED
        else:
            self.status = PositionStatus.CLOSED
        
        # Store close reason in execution details
        self.execution_details.update({
            'close_reason': reason,
            'close_price': float(close_price),
            'close_timestamp': self.closed_at.isoformat()
        })
    
    def update_stop_loss(self, new_stop_loss: Decimal) -> None:
        """Update stop loss price (for trailing stops, etc.)."""
        self.stop_loss_price = PriceLevel(new_stop_loss, datetime.now())
        self.execution_details.update({
            'stop_loss_updates': self.execution_details.get('stop_loss_updates', []) + [
                {
                    'price': float(new_stop_loss),
                    'timestamp': datetime.now().isoformat()
                }
            ]
        })
    
    def update_take_profit(self, new_take_profit: Decimal) -> None:
        """Update take profit price."""
        self.take_profit_price = PriceLevel(new_take_profit, datetime.now())
        self.execution_details.update({
            'take_profit_updates': self.execution_details.get('take_profit_updates', []) + [
                {
                    'price': float(new_take_profit),
                    'timestamp': datetime.now().isoformat()
                }
            ]
        })
    
    @classmethod
    def create_paper_position(
        cls,
        config_id: str,
        symbol: Symbol,
        side: PositionSide,
        size_usd: Money,
        entry_price: Decimal,
        leverage: Decimal = Decimal('1'),
        stop_loss_price: Optional[Decimal] = None,
        take_profit_price: Optional[Decimal] = None,
        entry_confidence: Optional[Confidence] = None,
        entry_reasoning: str = ""
    ) -> 'Position':
        """Factory method for creating paper trading positions."""
        entry_price_level = PriceLevel(entry_price, datetime.now())
        collateral = Money(size_usd.amount / leverage, size_usd.currency)
        
        return cls(
            trade_id=str(uuid.uuid4()),
            config_id=config_id,
            symbol=symbol,
            side=side,
            status=PositionStatus.OPEN,
            size_usd=size_usd,
            leverage=leverage,
            collateral_amount=collateral,
            entry_price=entry_price_level,
            stop_loss_price=PriceLevel(stop_loss_price, datetime.now()) if stop_loss_price else None,
            take_profit_price=PriceLevel(take_profit_price, datetime.now()) if take_profit_price else None,
            exchange="paper",
            opened_at=datetime.now(),
            entry_confidence=entry_confidence,
            entry_reasoning=entry_reasoning
        )