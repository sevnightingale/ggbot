"""
XAI LLM Provider Implementation.

This module implements the LLMProvider interface for XAI's Grok API.
Supports Grok models including grok-4-fast-non-reasoning, grok-4, and grok-code-fast-1.
"""

import json
import asyncio
import aiohttp
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
        self.timeout = kwargs.get('timeout', 120)  # XAI models can be fast

        logger.bind(module="decision.xai").info(
            f"Initialized XAI provider with model: {self.model}"
        )

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response from XAI Grok.

        Args:
            messages: List of message objects with 'role' and 'content'
            **kwargs: Additional generation parameters

        Returns:
            str: Generated response content

        Raises:
            Exception: If API call fails after retries
        """
        url = f"{self.base_url}/chat/completions"

        # Build request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', 4000),
            "temperature": kwargs.get('temperature', 0.1),
            "top_p": kwargs.get('top_p', 0.9),
        }

        # Add optional parameters if supported by model
        if 'seed' in kwargs:
            payload['seed'] = kwargs['seed']

        # Note: grok-4 and grok-4-fast models don't support presencePenalty, frequencyPenalty, stop
        if not self.model.startswith('grok-4'):
            if 'presence_penalty' in kwargs:
                payload['presence_penalty'] = kwargs['presence_penalty']
            if 'frequency_penalty' in kwargs:
                payload['frequency_penalty'] = kwargs['frequency_penalty']
            if 'stop' in kwargs:
                payload['stop'] = kwargs['stop']

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

                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()

                            # Extract response content
                            if 'choices' in data and len(data['choices']) > 0:
                                content = data['choices'][0]['message']['content']
                                logger.bind(module="decision.xai").info(
                                    "Successfully received response from XAI"
                                )
                                return content
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