"""
LLM Service for V2 Orchestrator

Subscription-aware LLM client factory that handles API key management
based on user subscription tier and Supabase Vault integration.
"""

import os
from typing import Optional, Dict, Any, Protocol
from abc import ABC, abstractmethod
import openai
from core.common.logger import logger
from core.auth.vault_utils import VaultManager
from core.services.user_service import UserService
from core.domain import SubscriptionTier


class LLMClient(Protocol):
    """Protocol for LLM client implementations."""
    
    async def generate_completion(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion from LLM."""
        ...


class OpenAIClient:
    """OpenAI API client implementation."""
    
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self._log = logger.bind(component="openai_client")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using OpenAI API."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return {
                "status": "success",
                "content": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            self._log.error(f"OpenAI API error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "model": model
            }


class DeepSeekClient:
    """DeepSeek API client implementation."""
    
    def __init__(self, api_key: str):
        # DeepSeek uses OpenAI-compatible API
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self._log = logger.bind(component="deepseek_client")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using DeepSeek API."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return {
                "status": "success",
                "content": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            self._log.error(f"DeepSeek API error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "model": model
            }


class AnthropicClient:
    """Anthropic API client implementation."""
    
    def __init__(self, api_key: str):
        # Note: This would need the anthropic library installed
        self.api_key = api_key
        self._log = logger.bind(component="anthropic_client")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using Anthropic API."""
        # For now, return error as anthropic library not installed
        return {
            "status": "error",
            "error": "Anthropic client not yet implemented",
            "model": model
        }


class LLMService:
    """Service for managing LLM clients based on subscription tiers."""
    
    def __init__(self):
        self._log = logger.bind(component="llm_service")
        self.user_service = UserService()
        self.vault_manager = VaultManager()
        
        # Hosted LLM keys for premium users
        self.hosted_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "deepseek": os.getenv("DEEPSEEK_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY")
        }
    
    async def get_llm_client(
        self,
        user_id: str,
        config_id: str,
        preferred_provider: str = "openai"
    ) -> Optional[LLMClient]:
        """
        Get LLM client based on user subscription and configuration.
        
        Args:
            user_id: User ID
            config_id: Configuration ID 
            preferred_provider: Preferred LLM provider
            
        Returns:
            LLM client instance or None if unavailable
        """
        try:
            # Get user profile to check subscription tier
            profile = await self.user_service.get_profile(user_id)
            if not profile:
                self._log.error(f"User profile not found: {user_id}")
                return None
            
            # Get config to check for LLM credential preference
            from core.services.config_service import config_service
            config = await config_service.get_config(config_id, user_id)
            
            if profile.subscription_tier == SubscriptionTier.FREE:
                # Free tier: must use user's own API keys from Vault
                return await self._get_user_llm_client(user_id, config, preferred_provider)
            
            elif profile.subscription_tier == SubscriptionTier.GGBASE:
                # GGBase tier: use our hosted API keys
                return await self._get_hosted_llm_client(preferred_provider)
            
            else:
                self._log.warning(f"Unknown subscription tier: {profile.subscription_tier}")
                return None
                
        except Exception as e:
            self._log.error(f"Failed to get LLM client: {e}")
            return None
    
    async def _get_user_llm_client(
        self,
        user_id: str,
        config: Optional[Any],
        preferred_provider: str
    ) -> Optional[LLMClient]:
        """Get LLM client using user's stored credentials."""
        try:
            # Determine credential name from config or use default
            credential_name = "Default"  # Default credential name
            if config and hasattr(config, 'decision'):
                credential_name = config.decision.get("llm_credential_name", "Default")
            
            # Get user's credential from Vault
            credential = await self.vault_manager.get_user_credential(user_id, credential_name)
            if not credential:
                self._log.error(f"No LLM credential found for user {user_id}, name: {credential_name}")
                return None
            
            provider = credential.get("provider", preferred_provider)
            api_key = credential.get("api_key")
            
            if not api_key:
                self._log.error(f"No API key in credential for user {user_id}")
                return None
            
            # Create client based on provider
            return self._create_client(provider, api_key)
            
        except Exception as e:
            self._log.error(f"Failed to get user LLM client: {e}")
            return None
    
    async def _get_hosted_llm_client(self, provider: str) -> Optional[LLMClient]:
        """Get LLM client using hosted API keys."""
        try:
            api_key = self.hosted_keys.get(provider)
            if not api_key:
                self._log.error(f"No hosted API key for provider: {provider}")
                return None
            
            return self._create_client(provider, api_key)
            
        except Exception as e:
            self._log.error(f"Failed to get hosted LLM client: {e}")
            return None
    
    def _create_client(self, provider: str, api_key: str) -> Optional[LLMClient]:
        """Create LLM client instance."""
        try:
            if provider == "openai":
                return OpenAIClient(api_key)
            elif provider == "deepseek":
                return DeepSeekClient(api_key)
            elif provider == "anthropic":
                return AnthropicClient(api_key)
            else:
                self._log.error(f"Unsupported LLM provider: {provider}")
                return None
                
        except Exception as e:
            self._log.error(f"Failed to create {provider} client: {e}")
            return None
    
    async def test_client(self, client: LLMClient) -> Dict[str, Any]:
        """Test an LLM client with a simple prompt."""
        try:
            response = await client.generate_completion(
                prompt="Say 'Hello from GGBot V2' in exactly 4 words.",
                system_prompt="You are a helpful assistant.",
                max_tokens=50,
                temperature=0.1
            )
            
            return {
                "status": "success",
                "test_response": response
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Convenience instance
llm_service = LLMService()