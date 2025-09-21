"""
LLM Provider Factory.

This module provides a factory function to create LLM provider instances
based on the provider name specified in configuration.
"""

from typing import Optional
from core.common.logger import logger
from decision.llm_providers.base import LLMProvider
from decision.llm_providers.deepseek_provider import DeepSeekProvider
from decision.llm_providers.openai_provider import OpenAIProvider
from decision.llm_providers.anthropic_provider import AnthropicProvider
from decision.llm_providers.xai_provider import XAIProvider


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

    # Handle default provider mapping to XAI/Grok
    if provider_name == 'default':
        return XAIProvider(
            api_key=api_key,
            model=model or 'grok-4-fast-non-reasoning',
            **kwargs
        )

    elif provider_name == 'deepseek':
        return DeepSeekProvider(
            api_key=api_key,
            model=model or 'deepseek-reasoner',
            **kwargs
        )

    elif provider_name in ['openai', 'gpt', 'gpt4', 'gpt5']:
        return OpenAIProvider(
            api_key=api_key,
            model=model or 'gpt-5',
            **kwargs
        )

    elif provider_name in ['anthropic', 'claude']:
        return AnthropicProvider(
            api_key=api_key,
            model=model or 'claude-opus-4-1-20250805',
            **kwargs
        )

    elif provider_name in ['xai', 'grok']:
        return XAIProvider(
            api_key=api_key,
            model=model or 'grok-4-fast-non-reasoning',
            **kwargs
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Supported providers: deepseek, openai, anthropic, xai"
        )


def get_available_providers() -> list[str]:
    """
    Get a list of available LLM provider names.

    Returns:
        list[str]: List of provider names that can be used with get_llm_provider
    """
    return ['default', 'deepseek', 'openai', 'anthropic', 'xai']