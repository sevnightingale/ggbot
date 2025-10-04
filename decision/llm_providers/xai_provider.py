"""
XAI LLM Provider Implementation.

This module implements the LLMProvider interface for XAI's Grok API.
Supports Grok models including grok-4-fast-non-reasoning, grok-4, and grok-code-fast-1.
"""

import json
import asyncio
import aiohttp
import time
from typing import Optional, Dict, Any, List
from core.common.logger import logger
from decision.interfaces.llm_provider import LLMProvider


class XAIProvider(LLMProvider):
    """
    XAI implementation of the LLMProvider interface.

    Uses XAI's Grok API for generating trading decisions with
    fast and efficient reasoning capabilities.
    """

    def __init__(self, api_key: str, model: str = "grok-4-fast-non-reasoning", **kwargs):
        """
        Initialize the XAI provider.

        Args:
            api_key (str): XAI API key
            model (str): Model to use (default: 'grok-4-fast-non-reasoning')
            **kwargs: Additional provider-specific settings
        """
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://api.x.ai/v1')
        self.timeout = kwargs.get('timeout', 200)  # Extended for quality reasoning

        logger.bind(module="decision.xai").info(
            f"Initialized XAI provider with model: {self.model}"
        )

    async def generate_response(self,
                              prompt: str,
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              temperature: float = 0.7,
                              custom_mode: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """
        Generate a response from XAI Grok.

        Args:
            prompt (str): The complete prompt containing all context and instructions
            conversation_history (Optional[List[Dict[str, str]]]): Previous conversation messages
            temperature (float): Controls randomness (0.0 = deterministic, 1.0 = creative)
            custom_mode (Optional[str]): Custom mode for specialized system prompts

        Returns:
            tuple[str, Dict[str, Any]]: Response text and metadata

        Raises:
            Exception: If API call fails after retries
        """
        # Convert prompt to messages format using helper method
        messages = self._prepare_messages(prompt, conversation_history)

        # Add system message at the beginning if not present
        if not messages or messages[0].get('role') != 'system':
            system_prompt = self._get_system_prompt(custom_mode)
            messages.insert(0, {"role": "system", "content": system_prompt})

        url = f"{self.base_url}/chat/completions"

        # Build request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 16384,  # Maximum for quality reasoning
            "temperature": temperature,  # Use parameter value
            "top_p": 0.9,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Retry logic with exponential backoff
        max_retries = 3
        base_delay = 1

        for attempt in range(max_retries):
            try:
                logger.bind(module="decision.xai").info(
                    f"Sending request to XAI (attempt {attempt + 1})"
                )

                start_time = time.time()
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            end_time = time.time()
                            latency = end_time - start_time

                            # Extract response content
                            if 'choices' in data and len(data['choices']) > 0:
                                content = data['choices'][0]['message']['content']

                                # Prepare metadata
                                metadata = {
                                    'model': self.model,
                                    'latency': latency,
                                    'usage': data.get('usage', {}),
                                    'status': 'success'
                                }

                                logger.bind(module="decision.xai").info(
                                    f"Successfully received response from XAI (latency: {latency:.2f}s)"
                                )
                                return content, metadata
                            else:
                                logger.bind(module="decision.xai").warning(
                                    "Unexpected response format from XAI"
                                )
                        else:
                            error_text = await response.text()
                            logger.bind(module="decision.xai").error(
                                f"XAI API error {response.status}: {error_text}"
                            )
                            if response.status >= 500:
                                # Server error, retry
                                if attempt < max_retries - 1:
                                    delay = base_delay * (2 ** attempt)
                                    await asyncio.sleep(delay)
                                    continue
                            else:
                                raise Exception(f"XAI API error: {error_text}")

            except asyncio.TimeoutError:
                logger.bind(module="decision.xai").error(
                    f"Request timeout on attempt {attempt + 1}"
                )
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
            except Exception as e:
                logger.bind(module="decision.xai").error(
                    f"Request failed on attempt {attempt + 1}: {str(e)}"
                )
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                raise

        raise Exception("Failed to get response from XAI after all retries")

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
        Check if the XAI API is accessible.

        Returns:
            bool: True if API is accessible, False otherwise
        """
        try:
            url = f"{self.base_url}/language-models"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200

        except Exception as e:
            logger.bind(module="decision.xai").error(
                f"Health check failed: {str(e)}"
            )
            return False