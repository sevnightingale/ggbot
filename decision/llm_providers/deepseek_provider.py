"""
DeepSeek LLM Provider Implementation.

This module implements the LLMProvider interface for DeepSeek's API.
DeepSeek provides powerful reasoning capabilities ideal for trading decisions.
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


class DeepSeekProvider(LLMProvider):
    """
    DeepSeek implementation of the LLMProvider interface.
    
    Uses DeepSeek's chat API for generating trading decisions with
    strong reasoning capabilities.
    """
    
    def __init__(self, api_key: str, model: str = "deepseek-reasoner", **kwargs):
        """
        Initialize the DeepSeek provider.
        
        Args:
            api_key (str): DeepSeek API key
            model (str): Model to use (default: 'deepseek-reasoner')
            **kwargs: Additional settings like base_url, timeout, etc.
        """
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://api.deepseek.com/v1')
        self.timeout = kwargs.get('timeout', 200)  # Extended timeout for reasoning model
        self.max_retries = kwargs.get('max_retries', 3)
        
        logger.bind(module="decision.deepseek").info(
            f"Initialized DeepSeek provider with model: {self.model}"
        )
    
    async def generate_response(self, 
                              prompt: str,
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              temperature: float = 0.7,
                              custom_mode: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a response from DeepSeek.
        
        Args:
            prompt (str): The prompt to send
            conversation_history (Optional[List[Dict[str, str]]]): Previous messages
            temperature (float): Response randomness (0.0-1.0)
            custom_mode (Optional[str]): Custom mode for specialized system prompts
            
        Returns:
            Tuple[str, Dict[str, Any]]: Response text and metadata
        """
        messages = self._prepare_messages(prompt, conversation_history)
        
        # Add system message at the beginning if not present
        if not messages or messages[0].get('role') != 'system':
            system_prompt = self._get_system_prompt(custom_mode)
            messages.insert(0, {"role": "system", "content": system_prompt})
            
            # DEBUG: Log the system prompt
            logger.bind(module="decision.deepseek").info(
                f"📋 DECISION LLM SYSTEM PROMPT ({custom_mode or 'standard'}):\n{system_prompt}"
            )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 8192,
            "stream": False
        }
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    # Serialize payload with custom encoder to handle Decimal types
                    json_payload = json.dumps(payload, cls=DecimalEncoder)
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        data=json_payload,
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
                            
                            logger.bind(module="decision.deepseek").info(
                                f"Generated response in {metadata['latency']:.2f}s, "
                                f"tokens: {metadata['usage'].get('total_tokens', 'unknown')}"
                            )
                            
                            return content, metadata
                        
                        elif response.status == 429:  # Rate limit
                            wait_time = min(2 ** attempt, 10)
                            logger.bind(module="decision.deepseek").warning(
                                f"Rate limited, waiting {wait_time}s before retry"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        
                        else:
                            error_text = await response.text()
                            logger.bind(module="decision.deepseek").error(
                                f"API error {response.status}: {error_text}"
                            )
                            
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(1)
                                continue
                            else:
                                raise Exception(f"DeepSeek API error: {error_text}")
            
            except asyncio.TimeoutError:
                logger.bind(module="decision.deepseek").error(
                    f"Request timeout on attempt {attempt + 1}"
                )
                if attempt < self.max_retries - 1:
                    continue
                else:
                    raise
            
            except Exception as e:
                logger.bind(module="decision.deepseek").error(
                    f"Unexpected error on attempt {attempt + 1}: {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise
        
        raise Exception("Failed to get response from DeepSeek after all retries")
    
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
        Check if the DeepSeek API is accessible.
        
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
            logger.bind(module="decision.deepseek").error(
                f"Health check failed: {str(e)}"
            )
            return False
