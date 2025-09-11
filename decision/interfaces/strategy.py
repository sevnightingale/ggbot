"""
Strategy Interface for the Decision Module.

This module defines the abstract base class that all trading strategies must implement.
Strategies take market data as input and produce trading decisions as output.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Any, Optional, Literal, Union


class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    A strategy analyzes market data and produces a trading decision with
    confidence score and reasoning. Strategies can be rule-based, LLM-based,
    or use any other approach as long as they implement this interface.
    """
    
    # Define decision types for new trade evaluation vs. active trade management
    DecisionType = Literal["buy", "sell", "hold", "adjust", "close"]
    
    @abstractmethod
    def make_decision(self, 
                     market_data: Dict[str, Dict[str, Any]], 
                     live_price: Union[float, Dict[str, float]],
                     symbol: str = "BTC-USD",
                     active_trade: Optional[Dict[str, Any]] = None) -> Tuple[DecisionType, float, Dict[str, Any], str]:
        """
        Analyze market data and produce a trading decision.
        
        Args:
            market_data (Dict[str, Dict[str, Any]]): Market data organized by timeframe,
                containing raw_data and indicators for each timeframe.
                Example: {'15m': {'raw_data': {...}, 'indicators': {...}}, '1h': {...}}
            live_price (Union[float, Dict[str, float]]): The current live price of the asset(s).
                Can be a single float (for single-pair trading) or a dict mapping
                symbols to prices (for multi-pair trading).
            symbol (str): The trading symbol/pair being evaluated (default: "BTC-USD").
            active_trade (Optional[Dict[str, Any]]): Information about any active trade,
                including entry price, position size, direction, etc. None if no active trade.
                
        Returns:
            Tuple[DecisionType, float, Dict[str, Any], str]: A tuple containing:
                - decision (str): One of:
                  - For new trades: 'buy', 'sell', or 'hold'
                  - For active trades: 'adjust', 'close', or 'hold'
                - confidence (float): Confidence score between 0.0 and 1.0
                - params (Dict[str, Any]): Additional parameters for the decision, such as:
                  - position_size: Size as percentage of capital (0.01 = 1%)
                  - stop_loss: Price level for stop loss
                  - take_profit: Price level for take profit
                  - leverage: Desired leverage (if applicable)
                  For 'adjust' decisions, include what's being adjusted
                - reasoning (str): Explanation of the decision
        """
        pass
    
    @abstractmethod
    def apply_risk_management(self, 
                             decision: DecisionType, 
                             confidence: float,
                             params: Dict[str, Any],
                             reasoning: str,
                             config: Dict[str, Any]) -> Tuple[DecisionType, float, Dict[str, Any], str]:
        """
        Apply risk management rules to a decision.
        
        This method applies configured risk parameters to ensure the strategy
        does not exceed risk tolerance. Risk caps are applied after the raw
        decision is made but before it's executed.
        
        Suggested risk management guidelines (for TestStrategy implementation):
        - Max position size based on confidence:
          - confidence > 0.8: 5% of capital
          - confidence 0.5-0.8: 2% of capital
          - confidence < 0.5: 1% of capital or no trade
        - Maximum leverage limit (e.g., 10x)
        - Minimum stop-loss distance (e.g., 2% from entry)
        - Daily trade frequency limit
        
        Args:
            decision (DecisionType): The initial decision ('buy', 'sell', 'hold', etc.)
            confidence (float): The confidence score (0.0 to 1.0)
            params (Dict[str, Any]): Decision parameters (position_size, etc.)
            reasoning (str): The original decision reasoning
            config (Dict[str, Any]): Strategy configuration parameters
            
        Returns:
            Tuple[DecisionType, float, Dict[str, Any], str]: The potentially modified decision tuple
                with the same structure as make_decision's return value.
        """
        pass