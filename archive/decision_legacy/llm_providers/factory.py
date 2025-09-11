"""
LLM Provider Factory.

This module provides a factory function to create LLM provider instances
based on the provider name specified in configuration.
"""

from typing import Optional
from core.common.logger import logger
from decision.interfaces.llm_provider import LLMProvider
from decision.llm_providers.deepseek_provider import DeepSeekProvider
from decision.llm_providers.openai_provider import OpenAIProvider


def get_llm_provider(
    provider_name: str,
    api_key: str,
    model: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Factory function to create an LLM provider instance.
    
    Args:
        provider_name (str): Name of the provider ('deepseek', 'openai', etc.)
        api_key (str): API key for the provider
        model (Optional[str]): Model to use (provider-specific default if None)
        **kwargs: Additional provider-specific settings
        
    Returns:
        LLMProvider: An instance of the requested LLM provider
        
    Raises:
        ValueError: If the provider name is not supported
    """
    provider_name = provider_name.lower()
    
    if provider_name == 'deepseek':
        return DeepSeekProvider(
            api_key=api_key,
            model=model or 'deepseek-chat',
            **kwargs
        )
    
    elif provider_name in ['openai', 'gpt', 'gpt4']:
        return OpenAIProvider(
            api_key=api_key,
            model=model or 'gpt-4o-mini',
            **kwargs
        )
    
    # Future providers can be added here
    # elif provider_name == 'anthropic':
    #     return AnthropicProvider(api_key, model or 'claude-3-opus', **kwargs)
    
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Supported providers: deepseek, openai"
        )


def get_available_providers() -> list[str]:
    """
    Get a list of available LLM provider names.
    
    Returns:
        list[str]: List of provider names that can be used with get_llm_provider
    """
    return ['deepseek', 'openai']