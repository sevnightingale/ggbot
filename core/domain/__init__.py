"""
Core Domain Models

This module contains the domain models and value objects for the GGBot platform.
Domain models represent business entities and their behavior, independent of 
infrastructure concerns like databases or APIs.

V1 Schema Update: Added unified decision model, user profiles, and dynamic indicators.
"""

from .models.account import Account
from .repositories.account_repository import AccountRepository, account_repo  
from .models.value_objects import Money, Symbol, Confidence, Timeframe

# Decision tracking (unified model replacing StrategyRun)
from .decision import (
    Decision,
    DecisionAction,
    DecisionStatus, 
    DecisionData
)

# Legacy strategy run model (for backward compatibility during migration)
from .strategy_run import (
    StrategyRun,
    DecisionScenario,
    DecisionOutcome,
    DecisionContext
)

# User management and business model
from .user_profile import (
    UserProfile,
    SubscriptionTier,
    SubscriptionStatus
)

# Dynamic indicator management
from .indicator import (
    Indicator,
    DataSource,
    IndicatorCategory,
    IndicatorStatus,
    UserIndicatorAccess
)

# Position and trading
from .position import (
    Position, 
    PositionStatus, 
    PositionSide, 
    PositionMetrics,
    PriceLevel
)
from .position_repository import PositionRepository, position_repo

# Market data and extraction
from .market_data import (
    MarketDataSnapshot,
    DataFreshness,
    PriceData,
    VolumeData
)
from .market_data_repository import MarketDataRepository, market_data_repo

__all__ = [
    # Core domain
    'Account',
    'AccountRepository', 
    'account_repo',
    'Money',
    'Symbol', 
    'Confidence',
    'Timeframe',
    
    # Decision tracking (V1 unified model)
    'Decision',
    'DecisionAction',
    'DecisionStatus',
    'DecisionData',
    
    # Legacy strategy tracking (backward compatibility)
    'StrategyRun',
    'DecisionScenario',
    'DecisionOutcome',
    'DecisionContext',
    
    # User management and business model
    'UserProfile',
    'SubscriptionTier',
    'SubscriptionStatus',
    
    # Dynamic indicator management
    'Indicator',
    'DataSource',
    'IndicatorCategory',
    'IndicatorStatus',
    'UserIndicatorAccess',
    
    # Position management
    'Position',
    'PositionStatus',
    'PositionSide',
    'PositionMetrics', 
    'PriceLevel',
    'PositionRepository',
    'position_repo',
    
    # Market data
    'MarketDataSnapshot',
    'DataFreshness', 
    'PriceData',
    'VolumeData',
    'MarketDataRepository',
    'market_data_repo'
]