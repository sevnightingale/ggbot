"""
Grok Agentic Adapter - Universal Market Intelligence via XAI's Agentic API

This adapter uses Grok's autonomous agentic capabilities (web search, X search, code execution)
to gather and interpret market intelligence from any source accessible via the internet.

Instead of building 50+ individual adapters, this ONE adapter handles:
- VIX Index (web search)
- DXY Dollar Index (web search)
- Twitter/X Sentiment (X search + analysis)
- Crypto News (web + X search)
- Whale Activity (web search on-chain data)
- Macro indicators (CPI, NFP, etc.)
- And potentially 100+ more data sources

Cost: ~$0.05-0.15 per query (with caching, effectively $0.01-0.03 per query)
Latency: 5-15 seconds (autonomous research takes time, but worth it)
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse, AdapterError
from core.common.logger import logger


class GrokAgenticAdapter(DataAdapter):
    """
    Universal market intelligence adapter using Grok's agentic API.

    Grok autonomously:
    - Searches the web
    - Searches X (Twitter)
    - Executes Python code for analysis
    - Interprets and structures data
    - Provides citations

    All in one API call!
    """

    name = "grok_agentic_adapter"
    data_type = "grok_agentic"

    # Prompt templates for different query types
    PROMPT_TEMPLATES = {
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
- Strong jobs (+300k+): Fed may stay hawkish, bearish for crypto
- Weak jobs (<100k): Fed may pivot dovish, bullish for crypto
- Moderate (100-250k): Goldilocks scenario, neutral

Return ONLY the JSON object, no markdown formatting.""",

        'twitter_sentiment': """Analyze current Twitter/X sentiment for {symbol} cryptocurrency over the last 24 hours.

Search recent X posts about {symbol} and perform sentiment analysis.

Tasks:
1. Search for recent posts mentioning {symbol} (last 24h)
2. Analyze sentiment of these posts (bullish/bearish/neutral)
3. Identify key themes and narratives
4. Note any influential accounts discussing {symbol}
5. Calculate overall sentiment score

Return a JSON object with this EXACT structure:
{{
    "symbol": "{symbol}",
    "sentiment_score": <number from -1.0 (very bearish) to 1.0 (very bullish)>,
    "sample_size": <number of posts analyzed>,
    "bullish_ratio": <number 0-1>,
    "bearish_ratio": <number 0-1>,
    "neutral_ratio": <number 0-1>,
    "key_themes": [<list of strings>],
    "influencer_sentiment": "<bullish|bearish|neutral|mixed>",
    "interpretation": "<brief analysis>",
    "signal": "<bullish|bearish|neutral>",
    "confidence": "<high|medium|low>"
}}

Sentiment scoring:
- > 0.5: Very bullish
- 0.2 to 0.5: Moderately bullish
- -0.2 to 0.2: Neutral
- -0.5 to -0.2: Moderately bearish
- < -0.5: Very bearish

Return ONLY the JSON object, no markdown formatting.""",

        'crypto_news': """Find recent breaking crypto news for {symbol} in the last 6 hours.

Search crypto news sites and X for important headlines about {symbol}.

Tasks:
1. Search for recent news (last 6h)
2. Identify most important/market-moving headlines
3. Classify each by sentiment and importance
4. Categorize news types

Return a JSON object with this EXACT structure:
{{
    "symbol": "{symbol}",
    "headlines": [
        {{
            "title": "<headline>",
            "source": "<source name>",
            "url": "<URL>",
            "published": "<ISO 8601 datetime>",
            "sentiment": "<bullish|bearish|neutral>",
            "importance": "<high|medium|low>",
            "category": "<regulation|technology|adoption|market|partnership|other>"
        }}
    ],
    "overall_sentiment": "<bullish|bearish|neutral|mixed>",
    "high_importance_count": <number>,
    "interpretation": "<brief summary of news impact>",
    "signal": "<bullish|bearish|neutral>"
}}

Return top 5 most important headlines only.
Return ONLY the JSON object, no markdown formatting.""",

        'btc_tvl': """Get the current Total Value Locked (TVL) for Bitcoin in DeFi protocols.

Search on-chain data sources (DefiLlama, Dune Analytics, etc.) for BTC TVL.

Return a JSON object with this EXACT structure:
{{
    "tvl_usd": <number>,
    "timestamp": "<ISO 8601 datetime>",
    "change_24h_pct": <number or null>,
    "change_7d_pct": <number or null>,
    "interpretation": "<brief analysis of TVL trend>",
    "signal": "<bullish|bearish|neutral>",
    "trend": "<increasing|stable|decreasing>"
}}

Interpretation guidelines:
- Rising TVL: More BTC locked in DeFi, bullish (reduced sell pressure)
- Falling TVL: BTC being withdrawn, bearish (potential selling)
- Significant changes (>10%): Strong signal

Return ONLY the JSON object, no markdown formatting.""",

        'whale_activity': """Analyze recent whale activity for {symbol} in the last 24 hours.

Search whale alert services, on-chain analytics, and crypto news for large transactions.

Tasks:
1. Find large transfers (>$1M) to/from exchanges
2. Identify accumulation vs distribution patterns
3. Note any significant wallet movements

Return a JSON object with this EXACT structure:
{{
    "symbol": "{symbol}",
    "large_transfers_count": <number>,
    "exchange_inflows_usd": <number or null>,
    "exchange_outflows_usd": <number or null>,
    "net_flow_usd": <number (positive = accumulation, negative = distribution)>,
    "interpretation": "<analysis of whale behavior>",
    "signal": "<bullish|bearish|neutral>",
    "confidence": "<high|medium|low>"
}}

Interpretation:
- Net outflows (positive): Whales withdrawing to cold storage = accumulation = bullish
- Net inflows (negative): Whales sending to exchanges = distribution = bearish
- Large magnitude (>$50M): High confidence signal

Return ONLY the JSON object, no markdown formatting.""",
    }

    def __init__(self):
        """Initialize Grok agentic adapter."""
        super().__init__()
        self.api_key = os.getenv('XAI_API_KEY')
        if not self.api_key:
            raise AdapterError("XAI_API_KEY environment variable not set")

        self._log = logger.bind(adapter="grok_agentic")

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Fetch market intelligence using Grok's agentic API.

        Args:
            params: Must contain 'query_type' (e.g., 'vix_index', 'twitter_sentiment')
                   Optional: 'symbol' for symbol-specific queries

        Returns:
            AdapterResponse with structured data + Grok metadata
        """
        query_type = params.get('query_type')
        if not query_type:
            raise AdapterError("query_type parameter required")

        if query_type not in self.PROMPT_TEMPLATES:
            raise AdapterError(f"Unknown query_type: {query_type}. Available: {list(self.PROMPT_TEMPLATES.keys())}")

        symbol = params.get('symbol', 'BTC')

        # Get prompt template and format with symbol
        prompt = self.PROMPT_TEMPLATES[query_type].format(symbol=symbol)

        self._log.info(f"Querying Grok for {query_type}" + (f" ({symbol})" if symbol else ""))

        try:
            # Call Grok agentic API with streaming
            response_data, metadata = await self._call_grok_agentic(prompt, query_type)

            # Add query metadata
            response_data['_meta'] = {
                'query_type': query_type,
                'symbol': symbol if symbol else None,
                'timestamp': datetime.utcnow().isoformat(),
                **metadata
            }

            self._log.info(
                f"✅ Grok {query_type} complete: "
                f"{metadata.get('tool_calls_count', 0)} tool calls, "
                f"{metadata.get('reasoning_tokens', 0)} reasoning tokens, "
                f"${metadata.get('estimated_cost', 0):.4f} cost"
            )

            return AdapterResponse(
                data=response_data,
                metadata=metadata,
                confidence=0.9  # Grok's reasoning is highly reliable
            )

        except Exception as e:
            self._log.error(f"Grok agentic query failed for {query_type}: {e}")
            raise AdapterError(f"Grok query failed: {e}")

    async def _call_grok_agentic(self, prompt: str, query_type: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Call Grok's agentic API with streaming support.

        Returns:
            Tuple of (parsed_response_data, metadata)
        """
        try:
            from xai_sdk import Client
            from xai_sdk.chat import user
            from xai_sdk.tools import web_search, x_search, code_execution

        except ImportError:
            raise AdapterError("xai-sdk not installed. Run: pip install xai-sdk>=1.3.1")

        # Query-specific timeouts (in seconds)
        # NFP queries require extended time due to complex government data source searches
        query_timeouts = {
            'nfp_jobs': 300.0,  # 5 minutes - complex BLS.gov/Bloomberg/Reuters searches
            'cpi_inflation': 180.0,  # 3 minutes - government data
            'dxy_index': 120.0,  # 2 minutes - financial indices
            'vix_index': 120.0,  # 2 minutes - financial indices
            'btc_tvl': 180.0,  # 3 minutes - DeFi protocol aggregation
            'whale_activity': 180.0,  # 3 minutes - blockchain analysis
            'twitter_sentiment': 180.0,  # 3 minutes - X search + sentiment analysis + code execution
            'crypto_news': 120.0,  # 2 minutes - news aggregation
        }
        timeout = query_timeouts.get(query_type, 180.0)  # Default 3 minutes

        self._log.debug(f"Using {timeout}s timeout for {query_type}")
        client = Client(api_key=self.api_key, timeout=timeout)

        # Determine which tools to enable based on query type
        tools = []
        if 'twitter' in query_type or 'whale' in query_type or 'news' in query_type:
            tools.append(x_search())  # X search for social/news

        # Always enable web search for most queries
        if query_type not in ['twitter_sentiment']:  # Twitter uses X search primarily
            tools.append(web_search())

        # Enable code execution for complex analysis
        if query_type in ['twitter_sentiment', 'whale_activity']:
            tools.append(code_execution())

        # Create chat with tools
        chat = client.chat.create(
            model="grok-4-1-fast",  # Optimized for agentic tool calling
            tools=tools if tools else [web_search()]  # Fallback to web search
        )

        # Add user query
        chat.append(user(prompt))

        # Stream response and collect metadata
        tool_calls_made = []
        citations = []
        reasoning_tokens = 0
        final_response = None
        final_content = ""

        try:
            self._log.debug(f"Streaming Grok response for {query_type}...")

            for response, chunk in chat.stream():
                # Track tool calls in real-time
                if chunk.tool_calls:
                    for tool_call in chunk.tool_calls:
                        # Convert to dict for Redis serialization (avoid protobuf objects)
                        tool_info = {
                            'tool': str(tool_call.function.name),
                            'args': str(tool_call.function.arguments) if tool_call.function.arguments else None
                        }
                        tool_calls_made.append(tool_info)
                        self._log.debug(f"  Tool: {tool_call.function.name}")

                # Track reasoning tokens
                if hasattr(response.usage, 'reasoning_tokens') and response.usage.reasoning_tokens:
                    reasoning_tokens = response.usage.reasoning_tokens

                # Collect content
                if chunk.content:
                    final_content += chunk.content

                # Store final response
                final_response = response

            # Get citations (convert protobuf to list for Redis serialization)
            if hasattr(final_response, 'citations') and final_response.citations:
                citations = list(final_response.citations)

            # Parse JSON response
            parsed_data = self._parse_grok_response(final_content, query_type)

            # Calculate cost estimate
            usage = final_response.usage if final_response else None
            estimated_cost = self._estimate_cost(usage) if usage else 0.0

            # Build metadata
            metadata = {
                'tool_calls': tool_calls_made,
                'tool_calls_count': len(tool_calls_made),
                'citations': citations,
                'citations_count': len(citations),
                'reasoning_tokens': reasoning_tokens,
                'total_tokens': usage.total_tokens if usage else 0,
                'estimated_cost': estimated_cost,
                'model': 'grok-4-1-fast',
                'tools_used': list(set(tc['tool'] for tc in tool_calls_made))
            }

            return parsed_data, metadata

        except Exception as e:
            # Extract detailed error information from gRPC exceptions
            error_msg = str(e)
            error_details = error_msg

            # Try to get gRPC details if available
            if hasattr(e, 'code'):
                error_details = f"gRPC code: {e.code()}, details: {e.details()}"
            elif hasattr(e, '_state'):
                error_details = f"gRPC state: {e._state}"

            # Check for resource exhaustion (out of credits)
            if "RESOURCE_EXHAUSTED" in error_msg or "credits" in error_msg.lower():
                self._log.error(
                    f"🚨 XAI/Grok API credits exhausted for {query_type}. "
                    f"Add credits at https://console.x.ai/team/settings/billing or increase spending limit. "
                    f"Error: {error_details}"
                )
                raise AdapterError(f"XAI API credits exhausted - add funds to continue using Grok market intelligence")

            # Check for timeout errors
            if "DEADLINE_EXCEEDED" in error_msg or "timeout" in error_msg.lower():
                self._log.error(
                    f"Grok query timed out after {timeout}s for {query_type}. "
                    f"This query may be too complex or data source unavailable. "
                    f"Error: {error_details}"
                )
                raise AdapterError(f"Grok query timeout (>{timeout}s) for {query_type}: Data source may be slow or unavailable")

            self._log.error(f"Grok streaming failed for {query_type}: {error_details}")
            raise

    def _parse_grok_response(self, content: str, query_type: str) -> Dict[str, Any]:
        """
        Parse Grok's response, expecting JSON.

        Grok should return pure JSON, but may include markdown formatting.
        This method extracts and validates the JSON.
        """
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]  # Remove ```json
        if content.startswith('```'):
            content = content[3:]  # Remove ```
        if content.endswith('```'):
            content = content[:-3]

        content = content.strip()

        try:
            data = json.loads(content)

            # Validate required fields based on query type
            self._validate_response(data, query_type)

            return data

        except json.JSONDecodeError as e:
            self._log.error(f"Failed to parse Grok JSON response: {e}\nContent: {content[:500]}")
            # Return error response
            return {
                'error': 'Failed to parse Grok response',
                'raw_content': content[:500],
                'query_type': query_type
            }

    def _validate_response(self, data: Dict[str, Any], query_type: str):
        """Validate that response has expected structure."""
        # Basic validation - just check it's a dict
        if not isinstance(data, dict):
            raise ValueError(f"Response must be a JSON object, got {type(data)}")

        # Query-type specific validation
        required_fields = {
            'vix_index': ['value'],
            'dxy_index': ['value'],
            'cpi_inflation': ['value'],
            'nfp_jobs': ['value'],
            'twitter_sentiment': ['sentiment_score', 'sample_size'],
            'crypto_news': ['headlines'],
            'btc_tvl': ['tvl_usd'],
            'whale_activity': ['large_transfers_count']
        }

        if query_type in required_fields:
            for field in required_fields[query_type]:
                if field not in data:
                    self._log.warning(f"Missing expected field '{field}' in {query_type} response")

    def _estimate_cost(self, usage) -> float:
        """
        Estimate query cost based on token usage.

        grok-4-1-fast pricing (2026):
        - Input: $0.20 / 1M tokens
        - Output: $0.50 / 1M tokens
        - Live Search: $25.00 / 1K sources = $0.025 per source

        Note: Each source type (web, X) counts as one source regardless of citations.
        """
        if not usage:
            return 0.0

        # Token costs (updated pricing)
        prompt_cost = (usage.prompt_tokens / 1_000_000) * 0.20
        completion_cost = (usage.completion_tokens / 1_000_000) * 0.50

        # Live Search costs: $25/1K sources = $0.025 per source
        # Each source type (web_search, x_search) = 1 source
        source_cost = 0.0
        if hasattr(usage, 'server_side_tool_usage'):
            tool_usage = usage.server_side_tool_usage or {}
            for tool_type, count in tool_usage.items():
                if 'WEB_SEARCH' in tool_type.upper():
                    source_cost += 0.025  # 1 web source = $0.025
                elif 'X_SEARCH' in tool_type.upper():
                    source_cost += 0.025  # 1 X source = $0.025
                # Code execution is free (no additional cost)

        total = prompt_cost + completion_cost + source_cost
        return total
