"""
Core Domain Models

This module contains the domain models and value objects for the GGBot platform.
Domain models represent business entities and their behavior, independent of 
infrastructure concerns like databases or APIs.
"""

from .models.account import Account
from .repositories.account_repository import AccountRepository, account_repo  
from .models.value_objects import Money, Symbol, Confidence, Timeframe

# Strategy and decision tracking
from .strategy_run import (
    StrategyRun, 
    DecisionScenario, 
    DecisionOutcome, 
    DecisionContext
)
from .strategy_run_repository import StrategyRunRepository, strategy_run_repo

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
    DataSource,
    DataType, 
    DataFreshness,
    Indicator,
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
    
    # Strategy tracking
    'StrategyRun',
    'DecisionScenario',
    'DecisionOutcome', 
    'DecisionContext',
    'StrategyRunRepository',
    'strategy_run_repo',
    
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
    'DataSource',
    'DataType',
    'DataFreshness', 
    'Indicator',
    'PriceData',
    'VolumeData',
    'MarketDataRepository',
    'market_data_repo'
]