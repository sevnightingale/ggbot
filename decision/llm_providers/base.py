"""
LLM Provider Interface for the Decision Module.

This module defines the abstract base class that all LLM providers must implement.
LLM providers handle communication with different LLM APIs and process their responses.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple


class LLMProvider(ABC):
    """
    Abstract base class for all LLM (Large Language Model) providers.
    
    This interface abstracts the communication with different LLM APIs
    (DeepSeek, OpenAI, Anthropic, etc.) and provides a standardized way
    to send prompts and receive responses for trading decisions.
    """
    
    def __init__(self, api_key: str, model: str = None, **kwargs):
        """
        Initialize the LLM provider with necessary credentials and settings.
        
        Args:
            api_key (str): API key for authentication with the LLM service
            model (str): Model name to use (e.g., 'gpt-4', 'deepseek-chat')
            **kwargs: Additional provider-specific settings
        """
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs
    
    @abstractmethod
    async def generate_response(self, 
                              prompt: str,
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              temperature: float = 0.7,
                              custom_mode: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Send a prompt to the LLM and get a response.
        
        Args:
            prompt (str): The complete prompt containing all context and instructions
            conversation_history (Optional[List[Dict[str, str]]]): Previous conversation
                messages for maintaining context. Each message should have 'role' and 'content' keys.
            temperature (float): Controls randomness (0.0 = deterministic, 1.0 = creative)
            custom_mode (Optional[str]): Custom mode for specialized system prompts (e.g., 'ggshot')
        
        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - The raw text response from the LLM
                - Metadata about the request/response (tokens used, latency, model, etc.)
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM API is accessible and functioning.
        
        This method should make a minimal API call to verify connectivity
        and authentication without consuming significant resources.
        
        Returns:
            bool: True if the API is accessible, False otherwise
        """
        pass
    
    def _prepare_messages(self, prompt: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """
        Helper method to prepare messages in the format expected by most LLM APIs.
        
        Args:
            prompt (str): The current prompt
            conversation_history (Optional[List[Dict[str, str]]]): Previous messages
            
        Returns:
            List[Dict[str, str]]: Formatted messages list
        """
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current prompt as user message
        messages.append({"role": "user", "content": prompt})
        
        return messages