"""
OpenRouter LLM Provider Implementation.

This module implements the LLMProvider interface for OpenRouter's unified API.
OpenRouter provides access to 200+ models from multiple providers through a single API.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
from core.common.logger import logger
from decision.llm_providers.base import LLMProvider


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter implementation of the LLMProvider interface.

    Uses OpenRouter's unified API to access multiple LLM providers (OpenAI, Anthropic,
    DeepSeek, xAI) through a single standardized interface with consistent token tracking.
    """

    # Model name mapping: user-friendly name → OpenRouter model ID
    MODEL_MAP = {
        'grok': 'x-ai/grok-4-fast',
        'claude': 'anthropic/claude-sonnet-4.5',
        'gemini': 'google/gemini-2.5-pro',
        'deepseek': 'deepseek/deepseek-chat-v3.1',
        'gpt': 'openai/gpt-5',
        'kimi': 'moonshotai/kimi-k2-thinking',
        'qwen': 'qwen/qwen3-max',

        # Legacy names for backward compatibility
        'grok-4-fast': 'x-ai/grok-4-fast',
        'claude-sonnet-4.5': 'anthropic/claude-sonnet-4.5',
        'gpt-5': 'openai/gpt-5',
        'deepseek-chat': 'deepseek/deepseek-chat-v3.1',

        # Default
        'default': 'x-ai/grok-4-fast'
    }

    # Models that support reasoning parameter
    REASONING_SUPPORTED = {
        'x-ai/grok-4-fast',
        'anthropic/claude-sonnet-4.5',
        'google/gemini-2.5-pro',
        'deepseek/deepseek-chat-v3.1',
        'openai/gpt-5',
        'moonshotai/kimi-k2-thinking'
        # Note: qwen/qwen3-max does NOT support reasoning
    }

    # Models that support temperature parameter
    TEMPERATURE_SUPPORTED = {
        'x-ai/grok-4-fast',
        'anthropic/claude-sonnet-4.5',
        'google/gemini-2.5-pro',
        'deepseek/deepseek-chat-v3.1',
        'moonshotai/kimi-k2-thinking',
        'qwen/qwen3-max'
        # Note: openai/gpt-5 does NOT support temperature
    }

    def __init__(self, api_key: str, model: str = "gpt-5", **kwargs):
        """
        Initialize the OpenRouter provider.

        Args:
            api_key (str): OpenRouter API key
            model (str): Internal model name (will be mapped to preset)
            **kwargs: Additional settings like timeout, max_retries, etc.
        """
        super().__init__(api_key, model, **kwargs)

        # Initialize OpenAI client with OpenRouter base URL
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

        self.timeout = kwargs.get('timeout', 200)
        self.max_retries = kwargs.get('max_retries', 3)

        # Get OpenRouter model ID for internal model name
        self.openrouter_model = self.MODEL_MAP.get(self.model, self.MODEL_MAP['default'])

        # Get thinking mode flag (enables reasoning + higher token limits)
        self.thinking_mode = kwargs.get('thinking', False)

        logger.bind(module="decision.openrouter").info(
            f"Initialized OpenRouter provider - model: {self.model} → {self.openrouter_model}, thinking: {self.thinking_mode}"
        )

    async def generate_response(self,
                              prompt: str,
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              temperature: float = 0.7,
                              custom_mode: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a response from OpenRouter.

        Args:
            prompt (str): The prompt to send
            conversation_history (Optional[List[Dict[str, str]]]): Previous messages
            temperature (float): Response randomness (0.0-1.0)
            custom_mode (Optional[str]): Custom mode for specialized system prompts

        Returns:
            Tuple[str, Dict[str, Any]]: Response text and standardized metadata
        """
        messages = []

        # Add system prompt if custom mode is specified
        if custom_mode:
            system_prompt = self._get_system_prompt(custom_mode)
            messages.append({"role": "system", "content": system_prompt})

            # DEBUG: Log the system prompt
            logger.bind(module="decision.openrouter").info(
                f"📋 DECISION LLM SYSTEM PROMPT ({custom_mode}):\n{system_prompt}"
            )

        # Add conversation history and current prompt
        messages.extend(self._prepare_messages(prompt, conversation_history))

        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                # Determine max_tokens based on thinking mode
                if self.thinking_mode:
                    # Thinking mode: higher token limits for extended reasoning
                    if self.openrouter_model == 'qwen/qwen3-max':
                        max_tokens = 4096  # Qwen thinking mode
                    else:
                        max_tokens = 8192  # Standard thinking mode
                else:
                    # Standard mode: balanced performance
                    max_tokens = 2048

                # Build request parameters
                request_params = {
                    "model": self.openrouter_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "timeout": self.timeout
                }

                # Add temperature if model supports it
                if self.openrouter_model in self.TEMPERATURE_SUPPORTED:
                    request_params["temperature"] = temperature

                # Add reasoning if thinking mode enabled and model supports it
                if self.thinking_mode and self.openrouter_model in self.REASONING_SUPPORTED:
                    request_params["extra_body"] = {"reasoning": {"effort": "high"}}

                # Call OpenRouter via OpenAI SDK
                response = await self.client.chat.completions.create(**request_params)

                # Extract response content
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason

                # Build standardized metadata
                usage = response.usage
                metadata = {
                    "model": self.model,  # Return internal model name
                    "openrouter_model": self.openrouter_model,  # Actual OpenRouter model ID
                    "thinking_mode": self.thinking_mode,
                    "max_tokens": max_tokens,
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens
                    },
                    "latency": time.time() - start_time,
                    "temperature": temperature if self.openrouter_model in self.TEMPERATURE_SUPPORTED else None,
                    "finish_reason": finish_reason
                }

                # Add reasoning tokens if available (GPT-5, DeepSeek R1)
                if hasattr(usage, 'completion_tokens_details') and usage.completion_tokens_details:
                    details = usage.completion_tokens_details
                    if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens:
                        metadata['usage']['reasoning_tokens'] = details.reasoning_tokens

                # Add cost if available (OpenRouter may include this)
                if hasattr(usage, 'cost') and usage.cost:
                    metadata['usage']['cost'] = usage.cost

                logger.bind(module="decision.openrouter").info(
                    f"Generated response in {metadata['latency']:.2f}s, "
                    f"tokens: {metadata['usage']['total_tokens']}"
                )

                return content, metadata

            except Exception as e:
                error_msg = str(e)
                logger.bind(module="decision.openrouter").error(
                    f"Error on attempt {attempt + 1}/{self.max_retries}: {error_msg}"
                )

                # Check if it's a rate limit error
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    wait_time = min(2 ** attempt, 10)
                    logger.bind(module="decision.openrouter").warning(
                        f"Rate limited, waiting {wait_time}s before retry"
                    )
                    await self.client._client.aclose()  # Close connection
                    await asyncio.sleep(wait_time)
                    continue

                # Retry on other errors
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"OpenRouter API error after {self.max_retries} retries: {error_msg}")

        raise Exception("Failed to get response from OpenRouter after all retries")

    def _get_system_prompt(self, custom_mode: Optional[str] = None) -> str:
        """
        Get the appropriate system prompt based on the custom mode.

        Args:
            custom_mode (Optional[str]): The custom mode (ggshot, trade_management, etc.)

        Returns:
            str: The system prompt for the given mode
        """
        if custom_mode == "ggshot":
            return (
                "You are a quantitative trading analyst executing the Four-Pillar Validation Framework. "
                "PHASE 1 (Pillar-scoring judgment): Choose values strictly within each pillar's numeric range. "
                "PHASE 2 (Math): Sum the scores. If total <0.05 set to 0.05; if >0.95 set to 0.95. "
                "NO further edits, rescaling, or overrides after Phase 2. If you attempt to alter the post-clamp value, output 'ERROR'. "
                "Focus on identifying clean technical setups and avoiding the rationalization of conflicting signals."
            )
        elif custom_mode == "trade_management":
            return (
                "You are an expert cryptocurrency trader managing active positions. Your role is to "
                "analyze current market conditions and make decisions about existing trades: hold, "
                "adjust, or close positions. You must be precise and disciplined in your analysis, "
                "considering market changes, risk management, and profit optimization. Provide clear "
                "reasoning for your decisions based on current market data and trade performance."
            )
        else:
            # Standard/default system prompt
            return (
                "You are an expert cryptocurrency trader analyzing market data and making trading decisions. "
                "Provide clear, reasoned responses about trading actions."
            )

    async def health_check(self) -> bool:
        """
        Check if the OpenRouter API is accessible.

        Returns:
            bool: True if API is accessible, False otherwise
        """
        try:
            # Make a minimal API call
            response, _ = await self.generate_response(
                "Say 'OK' if you can read this.",
                temperature=0.0
            )

            return 'OK' in response or 'ok' in response.lower()

        except Exception as e:
            logger.bind(module="decision.openrouter").error(
                f"Health check failed: {str(e)}"
            )
            return False
