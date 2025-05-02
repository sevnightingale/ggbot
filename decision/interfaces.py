"""
LLM Provider Interface for the Decision Module.

This module defines the abstract base class that all LLM providers must implement.
LLM providers handle communication with different LLM APIs and process their responses.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union


class LLMProvider(ABC):
    """
    Abstract base class for all LLM (Large Language Model) providers.
    
    This interface abstracts the communication with different LLM APIs
    (DeepSeek, OpenAI, Anthropic, etc.) and provides a standardized way
    to send prompts and receive responses for trading decisions.
    """
    
    @abstractmethod
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize the LLM provider with necessary credentials and settings.
        
        Args:
            api_key (str): API key for authentication with the LLM service
            **kwargs: Additional provider-specific settings
        """
        pass
    
    @abstractmethod
    def generate_response(self, 
                         system_prompt: str,
                         user_prompt: str,
                         conversation_history: Optional[List[Dict[str, str]]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Send a prompt to the LLM and get a response.
        
        The system_prompt should include instructions for the LLM to format its 
        response in a semi-structured format like:
        
        Decision: buy
        Confidence: 0.85
        Position Size: 0.05
        Stop Loss: 74200
        Take Profit: 76500
        Reasoning: RSI is oversold and MACD shows bullish crossover...
        
        This minimal structure ensures consistency while allowing free-form reasoning.
        The raw response will be passed to the Structuring Module for further processing.
        
        Args:
            system_prompt (str): Initial system instructions to guide the LLM's behavior
                and establish the expected response format
            user_prompt (str): The main prompt containing market data and questions
            conversation_history (Optional[List[Dict[str, str]]]): Previous conversation
                messages for maintaining context, especially for active trade management.
                Each message should have 'role' and 'content' keys.
        
        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - The raw text response from the LLM (semi-structured)
                - Metadata about the request/response (tokens used, latency, etc.)
        """
        pass
    
    @abstractmethod
    def format_market_data(self, 
                          market_data: Dict[str, Dict[str, Any]], 
                          live_price: Union[float, Dict[str, float]],
                          symbol: str = "BTC-USD",
                          active_trade: Optional[Dict[str, Any]] = None) -> str:
        """
        Format market data into a prompt that the LLM can process effectively.
        
        Args:
            market_data (Dict[str, Dict[str, Any]]): Market data by timeframe
            live_price (Union[float, Dict[str, float]]): Current price(s)
            symbol (str): The trading symbol/pair
            active_trade (Optional[Dict[str, Any]]): Information about any active trade
            
        Returns:
            str: A formatted prompt string ready to send to the LLM
        """
        pass
    
    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """
        Get the maximum context length in tokens that this LLM supports.
        
        Returns:
            int: Maximum number of tokens the LLM can process in one request
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the LLM API is accessible and functioning.
        
        This method should make a minimal API call to verify connectivity
        and authentication without consuming significant resources.
        
        Returns:
            bool: True if the API is accessible, False otherwise
        """
        pass"""
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