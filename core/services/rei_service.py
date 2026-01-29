"""
Rei Core Service - API client for Reilabs' Rei reasoning engine.

This service handles communication with the Rei API for inference-time learning
trading decisions. Rei provides persistent memory, numerical precision (Float64),
and pattern evolution that improves over time.

Key API behaviors (from Rei docs):
- API has NO session context - each call must be self-contained
- Never feed LLM outputs back (causes reasoning corruption)
- Float64 numerical precision is preserved
- Response format can be JSON for structured output

Usage:
    rei = ReiService(agent_secret_key="...")
    response = await rei.chat_completion(messages=[...])
"""

import os
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from core.common.logger import logger


@dataclass
class ReiResponse:
    """Structured response from Rei API."""
    content: str
    raw_response: Dict[str, Any]
    model: str
    usage: Optional[Dict[str, int]] = None
    tool_calls: Optional[List[Dict]] = None


class ReiServiceError(Exception):
    """Base exception for Rei service errors."""
    pass


class ReiAuthenticationError(ReiServiceError):
    """Raised when authentication fails (401)."""
    pass


class ReiRateLimitError(ReiServiceError):
    """Raised when rate limited (429)."""
    pass


class ReiAPIError(ReiServiceError):
    """Raised for general API errors."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ReiService:
    """
    Client for Rei Core API.

    Handles chat completions with retry logic, structured JSON responses,
    and proper error handling for the Rei reasoning engine.
    """

    BASE_URL = "https://api.reilabs.org"
    DEFAULT_TIMEOUT = 60.0  # Rei can take time for complex reasoning
    MAX_RETRIES = 5  # Increased for rate limit handling
    RETRY_DELAY = 2.0  # Base delay in seconds (increased for rate limits)

    def __init__(
        self,
        agent_secret_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize Rei service.

        Args:
            agent_secret_key: Rei Unit secret key. Falls back to REI_01_UNIT_SECRET env var.
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for transient failures
        """
        self.agent_secret_key = agent_secret_key or os.getenv("REI_01_UNIT_SECRET")

        if not self.agent_secret_key:
            raise ValueError(
                "Rei agent secret key required. "
                "Pass agent_secret_key or set REI_01_UNIT_SECRET env var."
            )

        self.timeout = timeout
        self.max_retries = max_retries
        self._log = logger.bind(component="rei_service")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.agent_secret_key}",
                    "Content-Type": "application/json"
                }
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def get_agent(self) -> Dict[str, Any]:
        """
        Retrieve agent details and configuration.

        Returns:
            Dict with agent info: id, name, model, temperature, max_tokens, etc.

        Raises:
            ReiAuthenticationError: If authentication fails
            ReiAPIError: For other API errors
        """
        client = await self._get_client()

        try:
            response = await client.get("/v1/agents")

            if response.status_code == 401:
                raise ReiAuthenticationError("Invalid agent secret key")

            if response.status_code == 404:
                raise ReiAPIError("Agent not found", status_code=404)

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise ReiAPIError(
                f"Failed to get agent: {e}",
                status_code=e.response.status_code
            )

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None
    ) -> ReiResponse:
        """
        Send messages to Rei and get a completion.

        IMPORTANT: Each call must be self-contained. Rei API has no session context.
        Never include previous Rei responses in messages (causes reasoning corruption).

        Args:
            messages: List of message dicts with 'role' and 'content'
                      Role can be: 'user', 'system', 'tool'
                      Content should contain ALL context needed for the decision
            temperature: Override unit's default temperature (0-2, lower = more consistent)
            max_tokens: Override unit's default max tokens
            response_format: {"type": "json_object"} for structured JSON output
            tools: List of tool schemas (function calling)
            tool_choice: "none", "auto", or specific tool

        Returns:
            ReiResponse with content, raw response, and metadata

        Raises:
            ReiAuthenticationError: If authentication fails
            ReiRateLimitError: If rate limited
            ReiAPIError: For other API errors
        """
        payload = {"messages": messages}

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_format is not None:
            payload["response_format"] = response_format
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice

        return await self._request_with_retry(payload)

    async def _request_with_retry(self, payload: Dict[str, Any]) -> ReiResponse:
        """
        Make API request with exponential backoff retry.

        Args:
            payload: Request payload for chat completion

        Returns:
            ReiResponse
        """
        client = await self._get_client()
        last_error = None

        for attempt in range(self.max_retries):
            try:
                self._log.debug(f"Rei API request attempt {attempt + 1}/{self.max_retries}")

                response = await client.post("/v1/chat/completions", json=payload)

                # Handle specific status codes
                if response.status_code == 401:
                    raise ReiAuthenticationError("Invalid agent secret key")

                if response.status_code == 429:
                    # Rate limited - exponential backoff
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    self._log.warning(f"Rei rate limited, waiting {delay}s before retry")
                    await asyncio.sleep(delay)
                    continue

                if response.status_code == 404:
                    raise ReiAPIError("Agent not found", status_code=404)

                response.raise_for_status()

                data = response.json()
                return self._parse_response(data)

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                delay = self.RETRY_DELAY * (2 ** attempt)
                self._log.warning(f"Rei connection error: {e}, retrying in {delay}s")
                await asyncio.sleep(delay)

            except ReiAuthenticationError:
                # Don't retry auth errors
                raise

            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    # Server error - retry
                    last_error = e
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    self._log.warning(f"Rei server error: {e}, retrying in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    # Client error - check if it's a wrapped rate limit
                    error_detail = None
                    try:
                        error_detail = e.response.json() if e.response.content else None
                    except Exception:
                        error_detail = e.response.text[:500] if e.response.text else None

                    # Check if this is a 400 wrapping a 429 rate limit (Rei API quirk)
                    is_wrapped_rate_limit = (
                        isinstance(error_detail, dict) and
                        '429' in str(error_detail.get('details', ''))
                    )

                    if is_wrapped_rate_limit:
                        # Treat as rate limit - retry with backoff
                        delay = self.RETRY_DELAY * (2 ** attempt) * 2  # Longer delay for rate limits
                        self._log.warning(f"Rei rate limited (wrapped in 400), waiting {delay}s before retry")
                        await asyncio.sleep(delay)
                        continue

                    self._log.error(f"Rei API client error {e.response.status_code}: {error_detail}")
                    raise ReiAPIError(
                        f"Rei API error: {e}",
                        status_code=e.response.status_code,
                        response=error_detail
                    )

        # All retries exhausted
        raise ReiAPIError(f"Rei API request failed after {self.max_retries} attempts: {last_error}")

    def _parse_response(self, data: Dict[str, Any]) -> ReiResponse:
        """
        Parse Rei API response into structured format.

        Args:
            data: Raw API response JSON

        Returns:
            ReiResponse object
        """
        choices = data.get("choices", [])
        if not choices:
            raise ReiAPIError("No choices in Rei response", response=data)

        message = choices[0].get("message", {})
        content = message.get("content", "")
        tool_calls = message.get("tool_calls")

        return ReiResponse(
            content=content,
            raw_response=data,
            model=data.get("model", "unknown"),
            usage=data.get("usage"),
            tool_calls=tool_calls
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience function for one-off usage
async def query_rei(
    messages: List[Dict[str, Any]],
    agent_secret_key: Optional[str] = None,
    response_format: Optional[Dict[str, str]] = None,
    temperature: float = 0.45
) -> ReiResponse:
    """
    Convenience function for single Rei query.

    Args:
        messages: List of message dicts
        agent_secret_key: Rei Unit secret key (or use env var)
        response_format: {"type": "json_object"} for JSON
        temperature: Temperature for response (default 0.45 for consistent reasoning)

    Returns:
        ReiResponse

    Example:
        response = await query_rei(
            messages=[{"role": "user", "content": "Analyze BTC: RSI=31, ADX=38"}],
            response_format={"type": "json_object"}
        )
        print(response.content)
    """
    async with ReiService(agent_secret_key=agent_secret_key) as rei:
        return await rei.chat_completion(
            messages=messages,
            response_format=response_format,
            temperature=temperature
        )
