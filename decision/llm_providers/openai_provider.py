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
from decision.llm_providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """
    OpenAI implementation of the LLMProvider interface.
    
    Uses OpenAI's chat completions API for generating trading decisions.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-5", **kwargs):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key (str): OpenAI API key
            model (str): Model to use (default: 'gpt-5')
            **kwargs: Additional settings like base_url, organization, timeout, etc.
        """
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://api.openai.com/v1')
        self.organization = kwargs.get('organization', None)
        self.timeout = kwargs.get('timeout', 300)  # Extended for quality reasoning with multi-timeframe data
        self.max_retries = kwargs.get('max_retries', 3)
        
        logger.bind(module="decision.openai").info(
            f"Initialized OpenAI provider with model: {self.model}"
        )
    
    async def generate_response(self,
                              prompt: str,
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              temperature: float = 0.7,
                              custom_mode: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a response from OpenAI using GPT-5 Responses API.

        Args:
            prompt (str): The prompt to send
            conversation_history (Optional[List[Dict[str, str]]]): Previous messages (for CoT passing)
            temperature (float): Response randomness (0.0-1.0)
            custom_mode (Optional[str]): Custom mode for specialized system prompts

        Returns:
            Tuple[str, Dict[str, Any]]: Response text and metadata
        """
        # Prepend system prompt to input for GPT-5 Responses API
        system_prompt = self._get_system_prompt(custom_mode)
        full_input = f"{system_prompt}\n\n{prompt}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if self.organization:
            headers["OpenAI-Organization"] = self.organization

        # GPT-5 Responses API format
        payload = {
            "model": self.model,
            "input": full_input,
            "reasoning": {
                "effort": "high"  # Maximum reasoning quality for trading decisions
            },
            "text": {
                "verbosity": "medium"  # Balanced output length
            }
        }

        # If conversation history contains a previous response ID, use it for CoT passing
        if conversation_history and len(conversation_history) > 0:
            last_message = conversation_history[-1]
            if 'response_id' in last_message:
                payload["previous_response_id"] = last_message['response_id']

        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/responses",  # New Responses API endpoint
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            # GPT-5 Responses API can return dict with 'output' or direct list
                            content = ''
                            response_id = None
                            reasoning_summary = []
                            usage = {}

                            # Extract the output list from response
                            output_list = data.get('output') if isinstance(data, dict) else data if isinstance(data, list) else None

                            if output_list and isinstance(output_list, list):
                                # Extract response_id and usage from top-level if dict format
                                if isinstance(data, dict):
                                    response_id = data.get('id')
                                    usage = data.get('usage', {})

                                # Extract reasoning item (optional)
                                reasoning_item = next((item for item in output_list if item.get('type') == 'reasoning'), None)
                                if reasoning_item:
                                    reasoning_summary = reasoning_item.get('summary', [])
                                    if not response_id:  # Fallback to reasoning ID if no top-level ID
                                        response_id = reasoning_item.get('id')

                                # Extract message item (contains actual output)
                                message_item = next((item for item in output_list if item.get('type') == 'message'), None)
                                if message_item and 'content' in message_item:
                                    # Find output_text in content array
                                    for content_block in message_item['content']:
                                        if content_block.get('type') == 'output_text':
                                            content = content_block.get('text', '')
                                            break
                            else:
                                # Unexpected format
                                logger.bind(module="decision.openai").error(
                                    f"Could not parse GPT-5 response format: {type(data)}"
                                )
                                content = ''

                            # Build metadata including response_id for future CoT passing
                            metadata = {
                                "model": data.get('model', self.model) if isinstance(data, dict) else self.model,
                                "usage": usage,
                                "latency": time.time() - start_time,
                                "reasoning_effort": "high",
                                "verbosity": "medium",
                                "response_id": response_id,
                                "reasoning_summary": reasoning_summary,
                                "finish_reason": data.get('status', 'completed') if isinstance(data, dict) else 'completed'
                            }

                            logger.bind(module="decision.openai").info(
                                f"Generated GPT-5 response in {metadata['latency']:.2f}s, "
                                f"content_length: {len(content)}, "
                                f"reasoning_tokens: {usage.get('output_tokens_details', {}).get('reasoning_tokens', 0)}, "
                                f"total_tokens: {usage.get('total_tokens', 0)}"
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