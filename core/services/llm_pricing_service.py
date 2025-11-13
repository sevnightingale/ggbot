"""
LLM Pricing Service - Calculate LLM costs with 70% markup for metered billing

This service queries the llm_models table for pricing and calculates both
provider costs and platform costs (with 70% markup) for token usage.
"""

from typing import Optional, Tuple
from decimal import Decimal
from core.common.db import get_db_connection
from core.common.logger import logger


class LLMPricingService:
    """Service for calculating LLM costs based on token usage."""

    # Markup percentage (70% = 1.70x multiplier)
    MARKUP_PERCENTAGE = Decimal("0.70")
    MARKUP_MULTIPLIER = Decimal("1.70")

    @classmethod
    def get_model_pricing(
        cls,
        provider: str,
        model: str,
        thinking_mode: bool = False
    ) -> Optional[Tuple[Decimal, Decimal]]:
        """
        Get pricing for a specific model from llm_models table.

        Args:
            provider: LLM provider ('openrouter', 'openai', 'anthropic', etc.)
            model: Model identifier ('grok', 'claude', 'gpt-5', etc.)
            thinking_mode: Whether thinking mode is enabled (affects pricing)

        Returns:
            Tuple of (input_price_per_1m, output_price_per_1m) or None if not found
            Prices are in USD per 1M tokens

        Example:
            >>> pricing = LLMPricingService.get_model_pricing('openrouter', 'grok', False)
            >>> if pricing:
            ...     input_price, output_price = pricing
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Try exact match first (model_id + provider)
                    cur.execute("""
                        SELECT
                            CASE WHEN %s THEN pricing_input_per_1m_thinking ELSE pricing_input_per_1m END,
                            CASE WHEN %s THEN pricing_output_per_1m_thinking ELSE pricing_output_per_1m END
                        FROM llm_models
                        WHERE model_id = %s AND enabled = TRUE
                    """, (thinking_mode, thinking_mode, model))

                    result = cur.fetchone()

                    if result and result[0] is not None and result[1] is not None:
                        return (Decimal(str(result[0])), Decimal(str(result[1])))

                    # Fallback: If not found, log warning and return None
                    logger.warning(
                        f"Pricing not found for model: {provider}/{model} (thinking_mode={thinking_mode})"
                    )
                    return None

        except Exception as e:
            logger.error(f"Failed to query model pricing: {e}")
            return None

    @classmethod
    def calculate_cost(
        cls,
        input_tokens: int,
        output_tokens: int,
        provider: str,
        model: str,
        thinking_mode: bool = False
    ) -> Tuple[float, float]:
        """
        Calculate provider cost and platform cost for token usage.

        Args:
            input_tokens: Number of input tokens consumed
            output_tokens: Number of output tokens consumed
            provider: LLM provider
            model: Model identifier
            thinking_mode: Whether thinking mode was enabled

        Returns:
            Tuple of (provider_cost_usd, platform_cost_usd)
            provider_cost_usd: Raw cost from provider
            platform_cost_usd: Cost with 70% markup (billed to user)

        Example:
            >>> provider_cost, platform_cost = LLMPricingService.calculate_cost(
            ...     input_tokens=2500,
            ...     output_tokens=150,
            ...     provider='openrouter',
            ...     model='grok',
            ...     thinking_mode=False
            ... )
            >>> print(f"Provider: ${provider_cost:.4f}, Platform: ${platform_cost:.4f}")
        """
        # Get pricing from database
        pricing = cls.get_model_pricing(provider, model, thinking_mode)

        if pricing is None:
            # Fallback to conservative estimate if pricing not found
            logger.warning(
                f"Using fallback pricing for {provider}/{model} (thinking_mode={thinking_mode})"
            )
            # Conservative estimate: $0.01 per 1M input, $0.03 per 1M output
            input_price_per_1m = Decimal("0.01")
            output_price_per_1m = Decimal("0.03")
        else:
            input_price_per_1m, output_price_per_1m = pricing

        # Calculate provider cost
        # Price is per 1M tokens, so divide token count by 1M
        input_cost = (Decimal(str(input_tokens)) / Decimal("1000000")) * input_price_per_1m
        output_cost = (Decimal(str(output_tokens)) / Decimal("1000000")) * output_price_per_1m
        provider_cost = input_cost + output_cost

        # Calculate platform cost with 70% markup
        platform_cost = provider_cost * cls.MARKUP_MULTIPLIER

        # Convert to float for database storage (NUMERIC can handle this precision)
        return (float(provider_cost), float(platform_cost))

    @classmethod
    def calculate_cost_from_response(
        cls,
        llm_response: dict,
        provider: str,
        model: str,
        thinking_mode: bool = False
    ) -> Tuple[float, float]:
        """
        Calculate costs from LLM response object (convenience method).

        Args:
            llm_response: LLM response dict with 'usage' key
            provider: LLM provider
            model: Model identifier
            thinking_mode: Whether thinking mode was enabled

        Returns:
            Tuple of (provider_cost_usd, platform_cost_usd)

        Example:
            >>> response = await llm_provider.generate(prompt)
            >>> provider_cost, platform_cost = LLMPricingService.calculate_cost_from_response(
            ...     llm_response=response,
            ...     provider='openrouter',
            ...     model='grok'
            ... )
        """
        usage = llm_response.get('usage', {})
        input_tokens = usage.get('input_tokens', 0) or usage.get('prompt_tokens', 0)
        output_tokens = usage.get('output_tokens', 0) or usage.get('completion_tokens', 0)

        return cls.calculate_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider=provider,
            model=model,
            thinking_mode=thinking_mode
        )


# Singleton instance for convenience
llm_pricing_service = LLMPricingService()
