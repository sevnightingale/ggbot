"""
OpenAI LLM Provider Implementation.

This module implements the LLMProvider interface for OpenAI's API.
Supports GPT-4, GPT-3.5, and other OpenAI models.
"""

import aiohttp
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from core.common.logger import logger
from decision.interfaces.llm_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """
    OpenAI implementation of the LLMProvider interface.
    
    Uses OpenAI's chat completions API for generating trading decisions.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key (str): OpenAI API key
            model (str): Model to use (default: 'gpt-4o-mini')
            **kwargs: Additional settings like base_url, organization, timeout, etc.
        """
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://api.openai.com/v1')
        self.organization = kwargs.get('organization', None)
        self.timeout = kwargs.get('timeout', 30)
        self.max_retries = kwargs.get('max_retries', 3)
        
        logger.bind(module="decision.openai").info(
            f"Initialized OpenAI provider with model: {self.model}"
        )
    
    async def generate_response(self, 
                              prompt: str,
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              temperature: float = 0.7) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a response from OpenAI.
        
        Args:
            prompt (str): The prompt to send
            conversation_history (Optional[List[Dict[str, str]]]): Previous messages
            temperature (float): Response randomness (0.0-1.0)
            
        Returns:
            Tuple[str, Dict[str, Any]]: Response text and metadata
        """
        messages = self._prepare_messages(prompt, conversation_history)
        
        # Add system message at the beginning if not present
        if not messages or messages[0].get('role') != 'system':
            system_prompt = (
                "You are an expert cryptocurrency trader analyzing market data and making trading decisions. "
                "Provide clear, reasoned responses about trading actions. "
                "Format your response with clear sections for Decision, Confidence, and Reasoning."
            )
            messages.insert(0, {"role": "system", "content": system_prompt})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1500,
            "stream": False
        }
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract response content
                            content = data['choices'][0]['message']['content']
                            
                            # Build metadata
                            metadata = {
                                "model": data.get('model', self.model),
                                "usage": data.get('usage', {}),
                                "latency": time.time() - start_time,
                                "temperature": temperature,
                                "finish_reason": data['choices'][0].get('finish_reason', 'unknown')
                            }
                            
                            logger.bind(module="decision.openai").info(
                                f"Generated response in {metadata['latency']:.2f}s, "
                                f"tokens: {metadata['usage'].get('total_tokens', 'unknown')}"
                            )
                            
                            return content, metadata
                        
                        elif response.status == 429:  # Rate limit
                            wait_time = min(2 ** attempt, 10)
                            logger.bind(module="decision.openai").warning(
                                f"Rate limited, waiting {wait_time}s before retry"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        
                        else:
                            error_text = await response.text()
                            logger.bind(module="decision.openai").error(
                                f"API error {response.status}: {error_text}"
                            )
                            
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(1)
                                continue
                            else:
                                raise Exception(f"OpenAI API error: {error_text}")
            
            except asyncio.TimeoutError:
                logger.bind(module="decision.openai").error(
                    f"Request timeout on attempt {attempt + 1}"
                )
                if attempt < self.max_retries - 1:
                    continue
                else:
                    raise
            
            except Exception as e:
                logger.bind(module="decision.openai").error(
                    f"Unexpected error on attempt {attempt + 1}: {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise
        
        raise Exception("Failed to get response from OpenAI after all retries")
    
    async def health_check(self) -> bool:
        """
        Check if the OpenAI API is accessible.
        
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
            logger.bind(module="decision.openai").error(
                f"Health check failed: {str(e)}"
            )
            return False