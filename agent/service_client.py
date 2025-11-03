"""
Agent Service Client

HTTP client for agent to call ggbot API endpoints.
Provides clean interface for MCP tools to interact with backend services.

NOTE: Uses HTTP API calls (no direct imports from main ggbot codebase).
Agent service runs in separate venv (.venv-agent).
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from loguru import logger
import httpx


class GGBotAPIClient:
    """
    HTTP client for agent to call ggbot API.

    Handles authentication, retries, and error handling.
    """

    def __init__(self, user_id: str):
        """
        Initialize API client with service-to-service authentication.

        Args:
            user_id: User ID for API calls (passed as query param)
        """
        self.base_url = os.getenv("API_BASE_URL", "https://ggbots-api.nightingale.business")
        self.user_id = user_id
        self.timeout = httpx.Timeout(100.0, connect=10.0)  # Increased to 100s for slow Grok queries

        # Service authentication (like signal-listener)
        service_key = os.getenv("SUPABASE_SERVICE_KEY")
        if not service_key:
            raise ValueError("SUPABASE_SERVICE_KEY environment variable required for agent authentication")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {service_key}",
                "X-Service-Auth": "agent-runner",
                "Content-Type": "application/json"
            }
        )
        logger.info(f"Initialized GGBotAPIClient for user {user_id}, base_url: {self.base_url}")

    async def close(self):
        """Close HTTP client connection"""
        await self.client.aclose()

    async def _retry_request(
        self,
        method: str,
        endpoint: str,
        max_retries: int = 3,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            max_retries: Maximum number of retries
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.debug(f"Request: {method} {endpoint}, kwargs: {kwargs}")
                response = await self.client.request(method, endpoint, **kwargs)
                logger.debug(f"Response URL: {response.url}")
                logger.debug(f"Response status: {response.status_code}")

                # Log response body for debugging
                try:
                    response_data = response.json()
                    logger.debug(f"Response data: {response_data}")
                except Exception:
                    logger.debug(f"Response text: {response.text[:500]}")

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                # Don't retry 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    logger.error(f"Client error {e.response.status_code}: {e}")
                    raise
                last_error = e

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e

            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

        # All retries failed
        logger.error(f"Request failed after {max_retries} attempts: {last_error}")
        raise last_error

    # ========================================================================
    # MARKET DATA
    # ========================================================================

    async def query_market_data(
        self,
        config_id: str,
        symbol: str,
        indicators: Optional[List[str]] = None,
        data_sources: Optional[Dict[str, List[str]]] = None,
        timeframe: str = "1h"
    ) -> Dict[str, Any]:
        """
        Query market data (technical indicators + market intelligence).

        Args:
            config_id: Configuration ID
            symbol: Trading symbol (e.g., "BTCUSDT")
            indicators: Optional list of technical indicators
            data_sources: Optional dict of market intelligence sources
            timeframe: Candle timeframe

        Returns:
            Market data response with technicals and/or intelligence
        """
        payload = {
            "config_id": config_id,
            "symbol": symbol,
            "timeframe": timeframe
        }
        if indicators:
            payload["indicators"] = indicators
        if data_sources:
            payload["data_sources"] = data_sources

        response = await self._retry_request(
            "POST",
            "/api/v2/agent/query-market-data",
            params={"user_id": self.user_id},
            json=payload
        )
        return response.json()

    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price for a symbol (lightweight, fast).

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")

        Returns:
            Current price response with symbol, price, volume, and change
        """
        response = await self._retry_request(
            "GET",
            f"/api/v2/agent/current-price/{symbol}",
            params={"user_id": self.user_id}
        )
        return response.json()

    # ========================================================================
    # TRADING
    # ========================================================================

    async def execute_trade(
        self,
        config_id: str,
        symbol: str,
        side: str,
        confidence: float = 0.7,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None,
        decision_id: Optional[str] = None,
        size_usd: Optional[float] = None,
        leverage: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a trade directly with optional position sizing overrides.

        Args:
            config_id: Configuration ID
            symbol: Trading symbol
            side: "long" or "short"
            confidence: Confidence score (0-1)
            stop_loss_price: Optional stop loss price
            take_profit_price: Optional take profit price
            decision_id: Optional decision ID to link
            size_usd: Optional position size in USD (NOTIONAL, not margin - overrides config)
                      Example: 1000 with 10x leverage = $1000 position using $100 margin
            leverage: Optional leverage multiplier (overrides config)

        Note:
            size_usd is the TOTAL POSITION SIZE (notional), not the margin/collateral.
            Actual capital at risk = size_usd / leverage

        Returns:
            Trade execution result
        """
        payload = {
            "config_id": config_id,
            "symbol": symbol,
            "side": side,
            "confidence": confidence
        }
        if stop_loss_price:
            payload["stop_loss_price"] = stop_loss_price
        if take_profit_price:
            payload["take_profit_price"] = take_profit_price
        if decision_id:
            payload["decision_id"] = decision_id
        if size_usd:
            payload["position_size_usd_override"] = size_usd
        if leverage:
            payload["leverage_override"] = leverage

        response = await self._retry_request(
            "POST",
            "/api/v2/agent/execute-trade",
            params={"user_id": self.user_id},
            json=payload
        )
        return response.json()

    async def get_positions(self, config_id: str) -> Dict[str, Any]:
        """
        Get open positions for config.

        Args:
            config_id: Configuration ID

        Returns:
            List of open positions
        """
        response = await self._retry_request(
            "GET",
            f"/api/v2/agent/positions/{config_id}",
            params={"user_id": self.user_id}
        )
        return response.json()

    async def get_account_status(self, config_id: str) -> Dict[str, Any]:
        """
        Get account summary with performance metrics.

        Args:
            config_id: Configuration ID

        Returns:
            Account status and metrics
        """
        response = await self._retry_request(
            "GET",
            f"/api/v2/agent/account/{config_id}",
            params={"user_id": self.user_id}
        )
        return response.json()

    async def close_position(
        self,
        config_id: str,
        trade_id: str
    ) -> Dict[str, Any]:
        """
        Close an open position.

        Args:
            config_id: Configuration ID
            trade_id: Trade ID to close

        Returns:
            Close result
        """
        response = await self._retry_request(
            "POST",
            f"/api/v2/agent/positions/{trade_id}/close",
            params={"user_id": self.user_id},
            json={"config_id": config_id}
        )
        return response.json()

    # ========================================================================
    # CONFIGURATION & STRATEGY
    # ========================================================================

    async def update_strategy(
        self,
        config_id: str,
        strategy_content: str,
        updated_by: str = "agent"
    ) -> Dict[str, Any]:
        """
        Update agent strategy.

        Args:
            config_id: Configuration ID
            strategy_content: New strategy text
            updated_by: "agent" or "user"

        Returns:
            Updated strategy with version
        """
        payload = {
            "strategy_content": strategy_content,
            "updated_by": updated_by
        }

        response = await self._retry_request(
            "PATCH",
            f"/api/v2/agent/config/{config_id}/strategy",
            params={"user_id": self.user_id},
            json=payload
        )
        return response.json()

    # ========================================================================
    # TRADE OBSERVATIONS
    # ========================================================================

    async def record_trade_observation(
        self,
        config_id: str,
        trade_id: str,
        observation_type: str,
        what_went_well: Optional[str] = None,
        what_went_wrong: Optional[str] = None,
        predictive_data_points: Optional[Dict[str, str]] = None,
        decision_review: Optional[str] = None,
        importance: int = 5
    ) -> Dict[str, Any]:
        """
        Record post-trade reflection.

        Args:
            config_id: Configuration ID
            trade_id: Closed trade ID
            observation_type: "win_analysis" or "loss_analysis"
            what_went_well: What worked in this trade
            what_went_wrong: What didn't work
            predictive_data_points: Which data points were most useful
            decision_review: Review of original entry decision
            importance: 1-10 importance score

        Returns:
            Created observation record
        """
        payload = {
            "config_id": config_id,
            "trade_id": trade_id,
            "observation_type": observation_type,
            "what_went_well": what_went_well,
            "what_went_wrong": what_went_wrong,
            "predictive_data_points": predictive_data_points,
            "decision_review": decision_review,
            "importance": importance
        }

        response = await self._retry_request(
            "POST",
            "/api/v2/agent/trade-observations",
            params={"user_id": self.user_id},
            json=payload
        )
        return response.json()

    async def query_trade_observations(
        self,
        config_id: str,
        symbol: Optional[str] = None,
        observation_type: Optional[str] = None,
        min_importance: Optional[int] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query trade observations for learning.

        Args:
            config_id: Configuration ID
            symbol: Filter by symbol (optional)
            observation_type: "win_analysis" or "loss_analysis" (optional)
            min_importance: Minimum importance threshold (optional)
            limit: Maximum results to return

        Returns:
            List of observations with trade context
        """
        payload = {
            "config_id": config_id,
            "symbol": symbol,
            "observation_type": observation_type,
            "min_importance": min_importance,
            "limit": limit
        }

        response = await self._retry_request(
            "POST",
            "/api/v2/agent/trade-observations/query",
            params={"user_id": self.user_id},
            json=payload
        )
        return response.json()


# Convenience function for agent context pattern
async def create_api_client(user_id: str) -> GGBotAPIClient:
    """
    Factory function to create API client.

    Args:
        user_id: User ID for authentication

    Returns:
        Initialized API client
    """
    return GGBotAPIClient(user_id=user_id)
