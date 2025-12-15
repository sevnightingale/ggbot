"""
OpenRouter-based market intelligence adapter using Perplexity models with web search.

Uses OpenRouter API with Perplexity Sonar models that have built-in web search capabilities.
"""

import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from loguru import logger

from market_intelligence.types import AdapterResponse, AdapterError


class OpenRouterMarketAdapter:
    """
    Market intelligence adapter using OpenRouter + Perplexity models.

    Perplexity models have built-in web search, making them perfect for
    real-time market data queries (VIX, DXY, CPI, NFP, etc.)
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with OpenRouter API key from environment."""
        import os
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        # Initialize OpenAI client pointing to OpenRouter
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        self._log = logger.bind(adapter="openrouter_market")

        # Use Perplexity Sonar Pro for web search capabilities
        self.model = "perplexity/sonar-pro"

        # Same prompts as Grok adapter
        self.PROMPT_TEMPLATES = self._load_prompts()

    def _load_prompts(self) -> Dict[str, str]:
        """Load prompt templates for market data queries."""
        return {
            'vix_index': """Get the current VIX (CBOE Volatility Index) value.

Search reliable financial data sources (CBOE, Bloomberg, Yahoo Finance, etc.) for the most recent VIX value.

Return a JSON object with this EXACT structure:
{{
    "value": <number>,
    "timestamp": "<ISO 8601 datetime>",
    "interpretation": "<brief interpretation for crypto traders>",
    "signal": "<bullish|bearish|neutral>",
    "risk_regime": "<low_volatility|moderate|high_volatility|extreme>"
}}

Interpretation guidelines:
- VIX < 15: Low volatility, risk-on environment (bullish for crypto)
- VIX 15-20: Moderate volatility (neutral)
- VIX 20-30: Elevated volatility (cautious)
- VIX > 30: High fear, risk-off (bearish for crypto)

Return ONLY the JSON object, no markdown formatting.""",

            'dxy_index': """Get the current DXY (US Dollar Index) value.

Search financial data sources for the most recent DXY value and its recent trend.

Return a JSON object with this EXACT structure:
{{
    "value": <number>,
    "timestamp": "<ISO 8601 datetime>",
    "change_24h": <number or null>,
    "interpretation": "<brief interpretation for crypto traders>",
    "signal": "<bullish|bearish|neutral>",
    "crypto_impact": "<how dollar strength affects crypto>"
}}

Interpretation guidelines:
- DXY rising: Dollar strength, typically bearish for crypto (inverse correlation)
- DXY falling: Dollar weakness, typically bullish for crypto
- Strong moves (>1%): Significant crypto impact
- DXY > 105: Strong dollar pressure on crypto

Return ONLY the JSON object, no markdown formatting.""",

            'cpi_inflation': """Get the most recent CPI (Consumer Price Index) inflation reading for the United States.

Search for the latest CPI data from official sources (BLS, Fed, financial news).

Return a JSON object with this EXACT structure:
{{
    "value": <number (percent)>,
    "release_date": "<ISO 8601 date>",
    "previous_value": <number or null>,
    "interpretation": "<brief interpretation for crypto and Fed policy>",
    "signal": "<bullish|bearish|neutral>",
    "fed_implications": "<how this affects Fed rate policy>"
}}

Interpretation guidelines:
- High inflation (>4%): Fed hawkish, bearish for crypto
- Declining inflation: Fed dovish pivot possible, bullish for crypto
- Target range (2-3%): Neutral, Fed on hold

Return ONLY the JSON object, no markdown formatting.""",

            'nfp_jobs': """Get the most recent NFP (Nonfarm Payrolls) jobs report for the United States.

Search for the latest NFP data from official sources (BLS, Fed, financial news).

Return a JSON object with this EXACT structure:
{{
    "value": <number (thousands of jobs added)>,
    "release_date": "<ISO 8601 date>",
    "previous_value": <number or null>,
    "unemployment_rate": <number (percent) or null>,
    "interpretation": "<brief interpretation for crypto markets>",
    "signal": "<bullish|bearish|neutral>",
    "economic_health": "<strong|moderate|weak>"
}}

Interpretation guidelines:
- Strong jobs (>200k): Strong economy, possible Fed hawkish, mixed for crypto
- Weak jobs (<100k): Economic weakness, Fed dovish, bullish for crypto
- Goldilocks (150-200k): Balanced growth, neutral

Return ONLY the JSON object, no markdown formatting.""",

            'btc_tvl': """Get the current Total Value Locked (TVL) in Bitcoin DeFi protocols.

Search crypto analytics sources (DeFi Llama, Dune Analytics, The Block) for Bitcoin TVL data.

Return a JSON object with this EXACT structure:
{{
    "value": <number (USD)>,
    "timestamp": "<ISO 8601 datetime>",
    "change_7d": <number or null (percent)>,
    "interpretation": "<brief interpretation>",
    "signal": "<bullish|bearish|neutral>",
    "trend": "<growing|stable|declining>"
}}

Interpretation guidelines:
- Rising TVL: Increasing Bitcoin DeFi adoption (bullish)
- Falling TVL: Capital flight or deleveraging (bearish)
- Major protocols: Lightning Network, Stacks, RSK

Return ONLY the JSON object, no markdown formatting.""",

            'whale_activity': """Analyze recent whale activity for {symbol}.

Search on-chain analytics for large transactions and whale wallet movements.

Return a JSON object with this EXACT structure:
{{
    "large_txs_24h": <number>,
    "net_flow": "<inflow|outflow|neutral>",
    "timestamp": "<ISO 8601 datetime>",
    "interpretation": "<brief interpretation>",
    "signal": "<bullish|bearish|neutral>",
    "accumulation_score": "<high|moderate|low>"
}}

Interpretation guidelines:
- Exchange inflows: Potential selling pressure (bearish)
- Exchange outflows: Accumulation/hodling (bullish)
- Large on-chain volumes: Increased activity

Return ONLY the JSON object, no markdown formatting.""",

            'twitter_sentiment': """Analyze current Twitter/X sentiment for {symbol} and crypto markets.

Search recent Twitter data for sentiment indicators and trending topics.

Return a JSON object with this EXACT structure:
{{
    "sentiment_score": <number -1 to 1>,
    "timestamp": "<ISO 8601 datetime>",
    "trending_topics": ["<topic1>", "<topic2>"],
    "interpretation": "<brief interpretation>",
    "signal": "<bullish|bearish|neutral>",
    "volume": "<high|moderate|low>"
}}

Interpretation guidelines:
- Sentiment > 0.5: Very bullish social sentiment
- Sentiment < -0.5: Very bearish social sentiment
- High volume + positive: Strong bullish momentum
- High volume + negative: Fear/panic

Return ONLY the JSON object, no markdown formatting.""",

            'crypto_news': """Get the latest significant cryptocurrency news and headlines.

Search crypto news sources for major developments, regulatory news, institutional moves.

Return a JSON object with this EXACT structure:
{{
    "headlines": ["<headline1>", "<headline2>", "<headline3>"],
    "timestamp": "<ISO 8601 datetime>",
    "overall_sentiment": "<bullish|bearish|neutral>",
    "interpretation": "<brief synthesis>",
    "signal": "<bullish|bearish|neutral>",
    "key_themes": ["<theme1>", "<theme2>"]
}}

Interpretation guidelines:
- Institutional adoption news: Bullish
- Regulatory crackdowns: Bearish
- Technical developments: Context-dependent
- Major hacks/exploits: Bearish

Return ONLY the JSON object, no markdown formatting."""
        }

    async def fetch(self, params: Dict[str, Any]) -> AdapterResponse:
        """
        Fetch market intelligence using OpenRouter + Perplexity.

        Args:
            params: Must contain 'query_type' (e.g., 'vix_index', 'twitter_sentiment')
                   Optional: 'symbol' for symbol-specific queries

        Returns:
            AdapterResponse with structured data
        """
        query_type = params.get('query_type')
        if not query_type:
            raise AdapterError("query_type parameter required")

        if query_type not in self.PROMPT_TEMPLATES:
            raise AdapterError(f"Unknown query_type: {query_type}. Available: {list(self.PROMPT_TEMPLATES.keys())}")

        symbol = params.get('symbol', 'BTC')

        # Get prompt template and format with symbol
        prompt = self.PROMPT_TEMPLATES[query_type].format(symbol=symbol)

        self._log.info(f"Querying OpenRouter/Perplexity for {query_type}" + (f" ({symbol})" if symbol else ""))

        try:
            # Call OpenRouter with Perplexity model
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for factual queries
                max_tokens=1024
            )

            content = response.choices[0].message.content

            # Parse JSON response
            parsed_data = self._parse_response(content, query_type)

            # Build metadata
            metadata = {
                'model': self.model,
                'input_tokens': response.usage.prompt_tokens if response.usage else 0,
                'output_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0,
                'provider': 'openrouter/perplexity'
            }

            # Add query metadata
            parsed_data['_meta'] = {
                **metadata,
                'query_type': query_type,
                'symbol': symbol if symbol else None
            }

            return AdapterResponse(
                data=parsed_data,
                metadata=metadata,
                confidence=0.9  # Perplexity web search is highly reliable
            )

        except Exception as e:
            self._log.error(f"OpenRouter query failed for {query_type}: {e}")
            raise AdapterError(f"OpenRouter query failed: {e}")

    def _parse_response(self, content: str, query_type: str) -> Dict[str, Any]:
        """Parse response, extracting JSON from markdown if needed."""
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith('```'):
            # Extract content between ```json and ```
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1])

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self._log.error(f"Failed to parse JSON for {query_type}: {e}\nContent: {content}")
            raise AdapterError(f"Invalid JSON response for {query_type}")
