"""
Decision Domain Model

Unified decision model replacing StrategyRun and ggshot_filter tables.
Represents all AI decision-making in the system with complete audit trail.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import uuid
from decimal import Decimal

from .models.value_objects import Symbol, Confidence


class DecisionAction(Enum):
    """Core decision actions that can be taken."""
    ENTER = "enter"  # Enter a new position (BUY signal)
    EXIT = "exit"    # Exit current position (SELL signal) 
    WAIT = "wait"    # No action, wait for better conditions


class DecisionStatus(Enum):
    """Decision validation status (primarily for signal validation)."""
    APPROVED = "approved"  # Decision validated and approved
    REJECTED = "rejected"  # Decision rejected/filtered out


@dataclass(frozen=True)
class DecisionData:
    """Flexible decision context storage (replaces decision_data JSONB field)."""
    
    # Trading-specific data
    trade_id: Optional[str] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    position_size: Optional[float] = None
    entry_price: Optional[float] = None
    
    # Signal validation data
    signal_source: Optional[str] = None
    signal_quality: Optional[float] = None
    validation_criteria: Optional[Dict[str, Any]] = None
    
    # Position management data
    current_pnl: Optional[float] = None
    position_duration: Optional[int] = None  # seconds
    risk_metrics: Optional[Dict[str, Any]] = None
    
    # Additional flexible context
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSONB storage."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]] = None) -> 'DecisionData':
        """Create from dictionary loaded from JSONB."""
        if not data:
            return cls()
        
        return cls(
            trade_id=data.get('trade_id'),
            stop_loss_price=data.get('stop_loss_price'),
            take_profit_price=data.get('take_profit_price'),
            position_size=data.get('position_size'),
            entry_price=data.get('entry_price'),
            signal_source=data.get('signal_source'),
            signal_quality=data.get('signal_quality'),
            validation_criteria=data.get('validation_criteria'),
            current_pnl=data.get('current_pnl'),
            position_duration=data.get('position_duration'),
            risk_metrics=data.get('risk_metrics'),
            metadata=data.get('metadata')
        )


@dataclass
class Decision:
    """
    Unified decision entity representing all AI decision-making in the system.
    
    Replaces both StrategyRun and ggshot_filter with a single audit trail.
    Captures complete decision context including prompts, market data, and reasoning.
    """
    
    decision_id: str
    user_id: str
    symbol: Symbol
    action: DecisionAction
    confidence: Confidence
    reasoning: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    # Optional fields
    config_id: Optional[str] = None  # NULL for ggShot signals (no user config)
    status: Optional[DecisionStatus] = None  # Primarily for signal validation
    
    # Audit trail fields
    prompt: Optional[str] = None  # Complete LLM prompt sent for decision
    market_data: Optional[Dict[str, Any]] = None  # Raw indicator values used
    
    # Flexible context storage
    decision_data: DecisionData = field(default_factory=DecisionData)
    
    # Decision linking
    parent_decision_id: Optional[str] = None  # Links related decisions (entry → management → exit)
    
    def __post_init__(self):
        """Validate decision after initialization."""
        if not self.decision_id:
            self.decision_id = str(uuid.uuid4())
        
        # Ensure confidence is in valid range
        if not (0.0 <= self.confidence.value <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence.value}")
    
    @property
    def is_actionable(self) -> bool:
        """Check if this decision represents an actionable trade signal."""
        return self.action in [DecisionAction.ENTER, DecisionAction.EXIT]
    
    @property
    def is_entry_signal(self) -> bool:
        """Check if this is an entry signal (BUY)."""
        return self.action == DecisionAction.ENTER
    
    @property
    def is_exit_signal(self) -> bool:
        """Check if this is an exit signal (SELL)."""
        return self.action == DecisionAction.EXIT
    
    @property
    def is_wait_signal(self) -> bool:
        """Check if this is a wait decision."""
        return self.action == DecisionAction.WAIT
    
    @property
    def is_approved(self) -> bool:
        """Check if decision was approved (for signal validation)."""
        return self.status == DecisionStatus.APPROVED
    
    @property
    def is_rejected(self) -> bool:
        """Check if decision was rejected."""
        return self.status == DecisionStatus.REJECTED
    
    @property
    def has_parent(self) -> bool:
        """Check if this decision is linked to a parent decision."""
        return self.parent_decision_id is not None
    
    @property
    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """Check if decision meets high confidence threshold."""
        return self.confidence.value >= threshold
    
    @property
    def is_user_config_based(self) -> bool:
        """Check if decision is based on user configuration (vs. system signals)."""
        return self.config_id is not None
    
    @property
    def is_system_signal(self) -> bool:
        """Check if decision is from system signals (e.g., ggShot)."""
        return self.config_id is None
    
    def get_trading_direction(self) -> Optional[str]:
        """Get human-readable trading direction."""
        if self.action == DecisionAction.ENTER:
            return "BUY"
        elif self.action == DecisionAction.EXIT:
            return "SELL"
        else:
            return None
    
    def get_risk_levels(self) -> tuple[Optional[float], Optional[float]]:
        """Get stop loss and take profit levels if available."""
        return (self.decision_data.stop_loss_price, self.decision_data.take_profit_price)
    
    def add_trading_context(
        self,
        trade_id: str,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None,
        position_size: Optional[float] = None,
        entry_price: Optional[float] = None
    ) -> None:
        """Add trading context to decision data."""
        self.decision_data = DecisionData(
            trade_id=trade_id,
            stop_loss_price=stop_loss_price or self.decision_data.stop_loss_price,
            take_profit_price=take_profit_price or self.decision_data.take_profit_price,
            position_size=position_size or self.decision_data.position_size,
            entry_price=entry_price or self.decision_data.entry_price,
            # Preserve other data
            signal_source=self.decision_data.signal_source,
            signal_quality=self.decision_data.signal_quality,
            validation_criteria=self.decision_data.validation_criteria,
            current_pnl=self.decision_data.current_pnl,
            position_duration=self.decision_data.position_duration,
            risk_metrics=self.decision_data.risk_metrics,
            metadata=self.decision_data.metadata
        )
    
    def add_signal_context(
        self,
        signal_source: str,
        signal_quality: Optional[float] = None,
        validation_criteria: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add signal validation context to decision data."""
        self.decision_data = DecisionData(
            signal_source=signal_source,
            signal_quality=signal_quality or self.decision_data.signal_quality,
            validation_criteria=validation_criteria or self.decision_data.validation_criteria,
            # Preserve other data
            trade_id=self.decision_data.trade_id,
            stop_loss_price=self.decision_data.stop_loss_price,
            take_profit_price=self.decision_data.take_profit_price,
            position_size=self.decision_data.position_size,
            entry_price=self.decision_data.entry_price,
            current_pnl=self.decision_data.current_pnl,
            position_duration=self.decision_data.position_duration,
            risk_metrics=self.decision_data.risk_metrics,
            metadata=self.decision_data.metadata
        )
    
    @classmethod
    def create_opportunity_analysis(
        cls,
        user_id: str,
        config_id: str,
        symbol: Symbol,
        action: DecisionAction,
        confidence: Confidence,
        reasoning: str,
        prompt: Optional[str] = None,
        market_data: Optional[Dict[str, Any]] = None,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> 'Decision':
        """Factory method for opportunity analysis decisions."""
        decision = cls(
            decision_id=str(uuid.uuid4()),
            user_id=user_id,
            config_id=config_id,
            symbol=symbol,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            prompt=prompt,
            market_data=market_data,
            created_at=datetime.now()
        )
        
        if stop_loss_price or take_profit_price:
            decision.add_trading_context(
                trade_id=None,  # Will be set when trade is created
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price
            )
        
        return decision
    
    @classmethod
    def create_position_management(
        cls,
        user_id: str,
        config_id: str,
        symbol: Symbol,
        action: DecisionAction,
        confidence: Confidence,
        reasoning: str,
        trade_id: str,
        parent_decision_id: str,
        prompt: Optional[str] = None,
        market_data: Optional[Dict[str, Any]] = None,
        current_pnl: Optional[float] = None
    ) -> 'Decision':
        """Factory method for position management decisions."""
        decision = cls(
            decision_id=str(uuid.uuid4()),
            user_id=user_id,
            config_id=config_id,
            symbol=symbol,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            parent_decision_id=parent_decision_id,
            prompt=prompt,
            market_data=market_data,
            created_at=datetime.now()
        )
        
        decision.add_trading_context(trade_id=trade_id)
        if current_pnl is not None:
            decision.decision_data = DecisionData(
                **decision.decision_data.to_dict(),
                current_pnl=current_pnl
            )
        
        return decision
    
    @classmethod
    def create_signal_validation(
        cls,
        user_id: str,
        symbol: Symbol,
        action: DecisionAction,
        confidence: Confidence,
        reasoning: str,
        signal_source: str,
        status: DecisionStatus,
        config_id: Optional[str] = None,  # NULL for system signals like ggShot
        prompt: Optional[str] = None,
        market_data: Optional[Dict[str, Any]] = None,
        signal_quality: Optional[float] = None,
        validation_criteria: Optional[Dict[str, Any]] = None
    ) -> 'Decision':
        """Factory method for signal validation decisions."""
        decision = cls(
            decision_id=str(uuid.uuid4()),
            user_id=user_id,
            config_id=config_id,  # NULL for ggShot signals
            symbol=symbol,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            status=status,
            prompt=prompt,
            market_data=market_data,
            created_at=datetime.now()
        )
        
        decision.add_signal_context(
            signal_source=signal_source,
            signal_quality=signal_quality,
            validation_criteria=validation_criteria
        )
        
        return decision


# Type aliases for backward compatibility
StrategyRun = Decision  # For gradual migration
DecisionRecord = Decision  # Alternative naming