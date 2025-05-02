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
        pass