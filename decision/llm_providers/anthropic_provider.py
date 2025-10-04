"""
Anthropic LLM Provider Implementation.

This module implements the LLMProvider interface for Anthropic's Claude API.
Supports Claude Opus 4.1 and other Claude models for trading decisions.
"""

import aiohttp
import asyncio
import time
import json
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from core.common.logger import logger
from decision.llm_providers.base import LLMProvider


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class AnthropicProvider(LLMProvider):
    """
    Anthropic implementation of the LLMProvider interface.

    Uses Anthropic's Claude API for generating trading decisions with
    advanced reasoning capabilities.
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-1-20250805", **kwargs):
        """
        Initialize the Anthropic provider.

        Args:
            api_key (str): Anthropic API key
            model (str): Model to use (default: 'claude-opus-4-1-20250805')
            **kwargs: Additional settings like base_url, timeout, etc.
        """
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://api.anthropic.com/v1')
        self.timeout = kwargs.get('timeout', 200)  # Extended for quality reasoning
        self.max_retries = kwargs.get('max_retries', 3)
        self.anthropic_version = kwargs.get('anthropic_version', '2023-06-01')

        logger.bind(module="decision.anthropic").info(
            f"Initialized Anthropic provider with model: {self.model}"
        )

    async def generate_response(self,
                              prompt: str,
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              temperature: float = 0.7,
                              custom_mode: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a response from Anthropic Claude.

        Args:
            prompt (str): The prompt to send
            conversation_history (Optional[List[Dict[str, str]]]): Previous messages
            temperature (float): Response randomness (0.0-1.0)
            custom_mode (Optional[str]): Custom mode for specialized system prompts

        Returns:
            Tuple[str, Dict[str, Any]]: Response text and metadata
        """
        messages = self._prepare_messages(prompt, conversation_history)

        # Extract system message if present
        system_prompt = None
        if messages and messages[0].get('role') == 'system':
            system_prompt = messages[0]['content']
            messages = messages[1:]  # Remove system message from messages list

        # Add system message based on custom mode if no system prompt exists
        if not system_prompt:
            system_prompt = self._get_system_prompt(custom_mode)

            # DEBUG: Log the system prompt
            logger.bind(module="decision.anthropic").info(
                f"📋 DECISION LLM SYSTEM PROMPT ({custom_mode or 'standard'}):\n{system_prompt}"
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "anthropic-version": self.anthropic_version
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "system": system_prompt,
            "temperature": temperature,
            "max_tokens": 16384,  # Maximum for quality reasoning
            "stream": False
        }

        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    # Serialize payload with custom encoder to handle Decimal types
                    json_payload = json.dumps(payload, cls=DecimalEncoder)
                    async with session.post(
                        f"{self.base_url}/messages",
                        headers=headers,
                        data=json_payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            # Extract response content from Claude's format
                            content = data['content'][0]['text']

                            # Build metadata
                            metadata = {
                                "model": data.get('model', self.model),
                                "usage": data.get('usage', {}),
                                "latency": time.time() - start_time,
                                "temperature": temperature,
                                "finish_reason": data.get('stop_reason', 'unknown')
                            }

                            logger.bind(module="decision.anthropic").info(
                                f"Generated response in {metadata['latency']:.2f}s, "
                                f"tokens: {metadata['usage'].get('output_tokens', 'unknown')}"
                            )

                            return content, metadata

                        elif response.status == 429:  # Rate limit
                            wait_time = min(2 ** attempt, 10)
                            logger.bind(module="decision.anthropic").warning(
                                f"Rate limited, waiting {wait_time}s before retry"
                            )
                            await asyncio.sleep(wait_time)
                            continue

                        else:
                            error_text = await response.text()
                            logger.bind(module="decision.anthropic").error(
                                f"API error {response.status}: {error_text}"
                            )

                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(1)
                                continue
                            else:
                                raise Exception(f"Anthropic API error: {error_text}")

            except asyncio.TimeoutError:
                logger.bind(module="decision.anthropic").error(
                    f"Request timeout on attempt {attempt + 1}"
                )
                if attempt < self.max_retries - 1:
                    continue
                else:
                    raise

            except Exception as e:
                logger.bind(module="decision.anthropic").error(
                    f"Unexpected error on attempt {attempt + 1}: {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise

        raise Exception("Failed to get response from Anthropic after all retries")

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
        Check if the Anthropic API is accessible.

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
            logger.bind(module="decision.anthropic").error(
                f"Health check failed: {str(e)}"
            )
            return False