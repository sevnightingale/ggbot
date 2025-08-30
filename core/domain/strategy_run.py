"""
StrategyRun Domain Model

Represents a decision execution record with context preservation for position management.
Strategy runs capture the full decision-making context including market conditions,
reasoning, and confidence levels for audit trails and position management context.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
import uuid

from .models.value_objects import Symbol, Confidence


class DecisionScenario(Enum):
    """Types of decision scenarios that can be recorded."""
    OPPORTUNITY_ANALYSIS = "OPPORTUNITY_ANALYSIS"
    POSITION_MANAGEMENT = "POSITION_MANAGEMENT"
    SIGNAL_VALIDATION = "SIGNAL_VALIDATION"
    
    
class DecisionOutcome(Enum):
    """Possible outcomes from a decision."""
    ENTER_LONG = "ENTER_LONG"
    ENTER_SHORT = "ENTER_SHORT"
    HOLD_POSITION = "HOLD_POSITION"
    CLOSE_POSITION = "CLOSE_POSITION"
    ADJUST_POSITION = "ADJUST_POSITION"
    NO_ACTION = "NO_ACTION"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    VALIDATION_FAILED = "VALIDATION_FAILED"


@dataclass(frozen=True)
class DecisionContext:
    """Value object containing the full decision context."""
    market_data: Dict[str, Any]
    current_price: float
    strategy_template: str
    llm_reasoning: str
    confidence_factors: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSONB storage."""
        return {
            'market_data': self.market_data,
            'current_price': self.current_price,
            'strategy_template': self.strategy_template,
            'llm_reasoning': self.llm_reasoning,
            'confidence_factors': self.confidence_factors,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionContext':
        """Create from dictionary loaded from JSONB."""
        return cls(
            market_data=data.get('market_data', {}),
            current_price=data.get('current_price', 0.0),
            strategy_template=data.get('strategy_template', ''),
            llm_reasoning=data.get('llm_reasoning', ''),
            confidence_factors=data.get('confidence_factors', {}),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        )


@dataclass
class StrategyRun:
    """
    Entity representing a single strategy execution record.
    
    Contains complete decision context for audit trails and position management.
    Each strategy run represents one decision made by the system with full context.
    """
    strategy_run_id: str
    trade_id: Optional[str]
    config_id: str
    scenario: DecisionScenario
    outcome: DecisionOutcome
    confidence: Confidence
    symbol: Symbol
    reasoning_log: str
    decision_context: DecisionContext
    created_at: datetime
    # Risk management levels parsed from LLM response
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    
    def __post_init__(self):
        """Validate strategy run after initialization."""
        if not self.strategy_run_id:
            self.strategy_run_id = str(uuid.uuid4())
        
        # Validate scenario-outcome combinations
        if self.scenario == DecisionScenario.SIGNAL_VALIDATION:
            if self.outcome not in [DecisionOutcome.VALIDATION_PASSED, DecisionOutcome.VALIDATION_FAILED]:
                raise ValueError(f"Invalid outcome {self.outcome} for scenario {self.scenario}")
        
        if self.scenario == DecisionScenario.OPPORTUNITY_ANALYSIS:
            if self.outcome not in [DecisionOutcome.ENTER_LONG, DecisionOutcome.ENTER_SHORT, DecisionOutcome.NO_ACTION]:
                raise ValueError(f"Invalid outcome {self.outcome} for scenario {self.scenario}")
        
        if self.scenario == DecisionScenario.POSITION_MANAGEMENT:
            if self.outcome not in [DecisionOutcome.HOLD_POSITION, DecisionOutcome.CLOSE_POSITION, 
                                  DecisionOutcome.ADJUST_POSITION]:
                raise ValueError(f"Invalid outcome {self.outcome} for scenario {self.scenario}")
    
    @property
    def is_entry_decision(self) -> bool:
        """Check if this was an entry decision that created a trade."""
        return (self.scenario == DecisionScenario.OPPORTUNITY_ANALYSIS and 
                self.outcome in [DecisionOutcome.ENTER_LONG, DecisionOutcome.ENTER_SHORT])
    
    @property
    def is_position_management(self) -> bool:
        """Check if this was a position management decision."""
        return self.scenario == DecisionScenario.POSITION_MANAGEMENT
    
    @property
    def is_signal_validation(self) -> bool:
        """Check if this was a signal validation."""
        return self.scenario == DecisionScenario.SIGNAL_VALIDATION
    
    def get_entry_direction(self) -> Optional[str]:
        """Get the entry direction if this was an entry decision."""
        if not self.is_entry_decision:
            return None
        return "long" if self.outcome == DecisionOutcome.ENTER_LONG else "short"
    
    def was_successful_validation(self) -> bool:
        """Check if signal validation was successful."""
        return (self.is_signal_validation and 
                self.outcome == DecisionOutcome.VALIDATION_PASSED and
                self.confidence.value >= 0.7)  # High confidence threshold for validation
    
    @classmethod
    def create_opportunity_analysis(
        cls,
        config_id: str,
        symbol: Symbol,
        outcome: DecisionOutcome,
        confidence: Confidence,
        reasoning: str,
        context: DecisionContext,
        trade_id: Optional[str] = None,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> 'StrategyRun':
        """Factory method for opportunity analysis decisions."""
        return cls(
            strategy_run_id=str(uuid.uuid4()),
            trade_id=trade_id,
            config_id=config_id,
            scenario=DecisionScenario.OPPORTUNITY_ANALYSIS,
            outcome=outcome,
            confidence=confidence,
            symbol=symbol,
            reasoning_log=reasoning,
            decision_context=context,
            created_at=datetime.now(),
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price
        )
    
    @classmethod
    def create_position_management(
        cls,
        trade_id: str,
        config_id: str,
        symbol: Symbol,
        outcome: DecisionOutcome,
        confidence: Confidence,
        reasoning: str,
        context: DecisionContext,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> 'StrategyRun':
        """Factory method for position management decisions."""
        return cls(
            strategy_run_id=str(uuid.uuid4()),
            trade_id=trade_id,
            config_id=config_id,
            scenario=DecisionScenario.POSITION_MANAGEMENT,
            outcome=outcome,
            confidence=confidence,
            symbol=symbol,
            reasoning_log=reasoning,
            decision_context=context,
            created_at=datetime.now(),
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price
        )
    
    @classmethod
    def create_signal_validation(
        cls,
        config_id: str,
        symbol: Symbol,
        outcome: DecisionOutcome,
        confidence: Confidence,
        reasoning: str,
        context: DecisionContext,
        trade_id: Optional[str] = None,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> 'StrategyRun':
        """Factory method for signal validation decisions."""
        return cls(
            strategy_run_id=str(uuid.uuid4()),
            trade_id=trade_id,
            config_id=config_id,
            scenario=DecisionScenario.SIGNAL_VALIDATION,
            outcome=outcome,
            confidence=confidence,
            symbol=symbol,
            reasoning_log=reasoning,
            decision_context=context,
            created_at=datetime.now(),
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price
        )