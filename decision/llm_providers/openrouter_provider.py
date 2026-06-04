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

    # Model + Reasoning Tier → OpenRouter model ID
    # Tiers: economy (cheap/fast), standard (balanced), premium (best quality)
    MODEL_TIER_MAP = {
        # Grok (xAI) - Updated 2026-06-04: grok-3-mini/grok-4-fast/grok-4.20-beta all
        # delisted from OpenRouter. Economy = 4.3 with no reasoning effort (tier
        # differentiated by effort, same pattern as Kimi/Gemini).
        ('grok', 'economy'): 'x-ai/grok-4.3',
        ('grok', 'standard'): 'x-ai/grok-4.3',
        ('grok', 'premium'): 'x-ai/grok-4.20',

        # DeepSeek
        ('deepseek', 'economy'): 'deepseek/deepseek-chat',
        ('deepseek', 'standard'): 'deepseek/deepseek-v3.2',
        ('deepseek', 'premium'): 'deepseek/deepseek-r1',

        # Gemini (Google)
        ('gemini', 'economy'): 'google/gemini-2.0-flash-001',
        ('gemini', 'standard'): 'google/gemini-2.5-pro',
        ('gemini', 'premium'): 'google/gemini-3-pro-preview',

        # Claude (Anthropic) - Updated 2026-03-26: standard → sonnet-4.6, premium → opus-4.6
        ('claude', 'economy'): 'anthropic/claude-haiku-4.5',
        ('claude', 'standard'): 'anthropic/claude-sonnet-4.6',
        ('claude', 'premium'): 'anthropic/claude-opus-4.6',

        # GPT (OpenAI)
        ('gpt', 'economy'): 'openai/gpt-4.1-mini',
        ('gpt', 'standard'): 'openai/gpt-5',
        ('gpt', 'premium'): 'openai/gpt-5-pro',

        # Kimi (MoonshotAI) - Updated 2026-01-27: standard/premium → K2.5
        ('kimi', 'economy'): 'moonshotai/kimi-k2',
        ('kimi', 'standard'): 'moonshotai/kimi-k2.5',
        ('kimi', 'premium'): 'moonshotai/kimi-k2.5',

        # Qwen
        ('qwen', 'economy'): 'qwen/qwen-turbo',
        ('qwen', 'standard'): 'qwen/qwen-plus',
        ('qwen', 'premium'): 'qwen/qwen3-max',
    }

    # Legacy MODEL_MAP for backward compatibility (maps to standard tier)
    MODEL_MAP = {
        'grok': 'x-ai/grok-4.3',
        'claude': 'anthropic/claude-sonnet-4.6',
        'gemini': 'google/gemini-2.5-pro',
        'deepseek': 'deepseek/deepseek-v3.2',
        'gpt': 'openai/gpt-5',
        'kimi': 'moonshotai/kimi-k2.5',
        'qwen': 'qwen/qwen-plus',
        'default': 'x-ai/grok-4.3'
    }

    # All OpenRouter model IDs that support reasoning parameter
    REASONING_SUPPORTED = {
        # Grok
        'x-ai/grok-4.3',
        'x-ai/grok-4.20',
        # DeepSeek
        'deepseek/deepseek-chat',
        'deepseek/deepseek-v3.2',
        'deepseek/deepseek-r1',
        # Gemini
        'google/gemini-2.0-flash-001',
        'google/gemini-2.5-pro',
        'google/gemini-3-pro-preview',
        # Claude
        'anthropic/claude-haiku-4.5',
        'anthropic/claude-sonnet-4.6',
        'anthropic/claude-opus-4.6',
        # GPT
        'openai/gpt-4.1-mini',
        'openai/gpt-5',
        'openai/gpt-5-pro',
        # Kimi
        'moonshotai/kimi-k2',
        'moonshotai/kimi-k2.5',
        # Qwen - does NOT support reasoning
    }

    # Models that support temperature parameter
    TEMPERATURE_SUPPORTED = {
        # Grok
        'x-ai/grok-4.3',
        'x-ai/grok-4.20',
        # DeepSeek
        'deepseek/deepseek-chat',
        'deepseek/deepseek-v3.2',
        'deepseek/deepseek-r1',
        # Gemini
        'google/gemini-2.0-flash-001',
        'google/gemini-2.5-pro',
        'google/gemini-3-pro-preview',
        # Claude
        'anthropic/claude-haiku-4.5',
        'anthropic/claude-sonnet-4.6',
        'anthropic/claude-opus-4.6',
        # Kimi
        'moonshotai/kimi-k2',
        'moonshotai/kimi-k2.5',
        # Qwen
        'qwen/qwen-turbo',
        'qwen/qwen-plus',
        'qwen/qwen3-max',
        # GPT - does NOT support temperature
    }

    def __init__(self, api_key: str, model: str = "grok", **kwargs):
        """
        Initialize the OpenRouter provider.

        Args:
            api_key (str): OpenRouter API key
            model (str): Internal model name (grok, claude, gemini, deepseek, gpt, kimi, qwen)
            **kwargs: Additional settings like timeout, max_retries, reasoning_tier, etc.
        """
        super().__init__(api_key, model, **kwargs)

        self.timeout = kwargs.get('timeout', 200)
        self.max_retries = kwargs.get('max_retries', 3)
        self._api_key = api_key  # Store for client recreation on connection errors

        # Initialize OpenAI client with OpenRouter base URL
        self.client = self._create_client()

        # Get reasoning tier (economy, standard, premium)
        # Support both new reasoning_tier and legacy thinking_mode
        self.reasoning_tier = kwargs.get('reasoning_tier', None)
        if self.reasoning_tier is None:
            # Backward compatibility: thinking_mode maps to tiers
            thinking_mode = kwargs.get('thinking', False)
            self.reasoning_tier = 'premium' if thinking_mode else 'standard'

        # Get OpenRouter model ID using tier-based lookup
        tier_key = (self.model, self.reasoning_tier)
        if tier_key in self.MODEL_TIER_MAP:
            self.openrouter_model = self.MODEL_TIER_MAP[tier_key]
        else:
            # Fallback to legacy MODEL_MAP
            self.openrouter_model = self.MODEL_MAP.get(self.model, self.MODEL_MAP['default'])

        # For backward compatibility, set thinking_mode based on tier
        self.thinking_mode = self.reasoning_tier == 'premium'

        logger.bind(module="decision.openrouter").info(
            f"Initialized OpenRouter provider - model: {self.model}, tier: {self.reasoning_tier} → {self.openrouter_model}"
        )

    def _create_client(self) -> AsyncOpenAI:
        """Create a fresh AsyncOpenAI client with a new connection pool."""
        return AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self._api_key,
            timeout=self.timeout,
            max_retries=0,  # We handle retries ourselves with client recreation
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
        # Validate prompt is not empty (prevents "Input must have at least 1 token" API errors)
        if not prompt or not prompt.strip():
            logger.bind(module="decision.openrouter").error(
                f"Empty prompt received! custom_mode={custom_mode}, "
                f"conversation_history_len={len(conversation_history) if conversation_history else 0}"
            )
            raise ValueError("Cannot send empty prompt to LLM API")

        # Log prompt info for debugging (truncated for brevity)
        logger.bind(module="decision.openrouter").debug(
            f"Prompt received: {len(prompt)} chars, first 100: {prompt[:100]!r}..."
        )

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
                # Determine max_tokens based on reasoning tier
                if self.reasoning_tier == 'premium':
                    max_tokens = 8192  # Premium: extended reasoning
                elif self.reasoning_tier == 'standard':
                    max_tokens = 4096  # Standard: balanced
                else:
                    max_tokens = 2048  # Economy: fast/cheap

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

                # Add reasoning based on tier (if model supports it)
                if self.openrouter_model in self.REASONING_SUPPORTED:
                    if self.reasoning_tier == 'premium':
                        request_params["extra_body"] = {"reasoning": {"effort": "high"}}
                    elif self.reasoning_tier == 'standard':
                        request_params["extra_body"] = {"reasoning": {"effort": "medium"}}
                    # economy: no reasoning parameter

                # Call OpenRouter via OpenAI SDK
                response = await self.client.chat.completions.create(**request_params)

                # Validate response structure before accessing
                if not response.choices:
                    raise ValueError(
                        f"OpenRouter returned empty choices array - "
                        f"model: {self.openrouter_model}, response: {response}"
                    )

                # Extract response content
                message = response.choices[0].message
                content = message.content
                finish_reason = response.choices[0].finish_reason

                # For thinking models (Kimi K2, DeepSeek R1), response may be in 'reasoning' field
                if (not content or content.strip() == "") and hasattr(message, 'reasoning') and message.reasoning:
                    logger.bind(module="decision.openrouter").info(
                        f"Content empty, using reasoning field from thinking model (length: {len(message.reasoning)})"
                    )
                    content = message.reasoning

                # Validate response content is not blank
                if not content or content.strip() == "":
                    error_msg = (
                        f"OpenRouter returned blank/empty content - "
                        f"finish_reason: {finish_reason}, "
                        f"model: {self.openrouter_model}, "
                        f"thinking_mode: {self.thinking_mode}, "
                        f"prompt_tokens: {response.usage.prompt_tokens}, "
                        f"completion_tokens: {response.usage.completion_tokens}, "
                        f"has_reasoning: {hasattr(message, 'reasoning')}"
                    )
                    logger.bind(module="decision.openrouter").error(error_msg)
                    # Log the full response for debugging
                    logger.bind(module="decision.openrouter").error(f"Full response object: {response}")
                    raise ValueError(error_msg)

                # Build standardized metadata
                usage = response.usage
                metadata = {
                    "model": self.model,  # Return internal model name
                    "openrouter_model": self.openrouter_model,  # Actual OpenRouter model ID
                    "reasoning_tier": self.reasoning_tier,
                    "thinking_mode": self.thinking_mode,  # Backward compatibility
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
                error_type = type(e).__name__
                logger.bind(module="decision.openrouter").error(
                    f"Error on attempt {attempt + 1}/{self.max_retries} ({error_type}): {error_msg}"
                )

                # Check if it's a rate limit error
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    wait_time = min(2 ** attempt, 10)
                    logger.bind(module="decision.openrouter").warning(
                        f"Rate limited, waiting {wait_time}s before retry"
                    )
                    try:
                        await self.client.close()
                    except Exception:
                        pass
                    self.client = self._create_client()
                    await asyncio.sleep(wait_time)
                    continue

                # Connection error: stale pool — recreate client with fresh connections
                if 'connection error' in error_msg.lower() or 'connect' in error_type.lower():
                    logger.bind(module="decision.openrouter").warning(
                        f"Connection error detected, recreating HTTP client for retry"
                    )
                    try:
                        await self.client.close()
                    except Exception:
                        pass
                    self.client = self._create_client()

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
