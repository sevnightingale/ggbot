"""
Base adapter class for all data sources.

All adapters must inherit from DataAdapter and implement the fetch() method.
The framework handles everything else (caching, validation, routing, formatting).
"""

from abc import ABC, abstractmethod
from typing import Optional
import aiohttp
import asyncio
from datetime import datetime, timezone

from market_intelligence.types import QueryParams, AdapterResponse, AdapterError
from core.common.logger import logger


class DataAdapter(ABC):
    """
    Abstract base class for all data adapters.

    Adapters must implement a single method: fetch(params) -> AdapterResponse
    Everything else is handled by the framework.
    """

    # Adapter metadata (optional - catalog is source of truth)
    name: Optional[str] = None
    data_type: Optional[str] = None

    def __init__(self):
        """Initialize adapter with common utilities."""
        self._http_client: Optional[aiohttp.ClientSession] = None
        self._log = logger.bind(adapter=self.__class__.__name__)

    @abstractmethod
    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Fetch data from source.

        This is the ONLY method adapters must implement.

        Args:
            params: Validated query parameters

        Returns:
            AdapterResponse with data, metadata, and confidence

        Raises:
            AdapterError: If fetch fails
        """
        pass

    async def get_http_client(self) -> aiohttp.ClientSession:
        """
        Get or create HTTP client with sensible defaults.

        Returns:
            Shared aiohttp session for this adapter
        """
        if not self._http_client:
            timeout = aiohttp.ClientTimeout(total=30)
            self._http_client = aiohttp.ClientSession(timeout=timeout)

        return self._http_client

    async def close(self):
        """Clean up resources."""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None

    async def fetch_with_retry(
        self,
        url: str,
        method: str = "GET",
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Fetch with exponential backoff retry logic.

        Args:
            url: URL to fetch
            method: HTTP method
            max_retries: Maximum retry attempts
            backoff_factor: Backoff multiplier (2.0 = double each time)
            **kwargs: Additional arguments for aiohttp request

        Returns:
            Response object

        Raises:
            AdapterError: If all retries fail
        """
        client = await self.get_http_client()
        last_error = None

        for attempt in range(max_retries):
            try:
                async with client.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return response
                    elif response.status == 429:  # Rate limit
                        wait_time = (backoff_factor ** attempt)
                        self._log.warning(f"Rate limited, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        response.raise_for_status()

            except aiohttp.ClientError as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = (backoff_factor ** attempt)
                    self._log.warning(f"Request failed (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break

        raise AdapterError(f"Failed after {max_retries} retries: {last_error}")

    def calculate_confidence(
        self,
        sample_size: Optional[int] = None,
        freshness_seconds: Optional[float] = None,
        error_rate: Optional[float] = None
    ) -> float:
        """
        Calculate data quality confidence score.

        Combines multiple factors to produce a 0.0-1.0 confidence score.

        Args:
            sample_size: Number of data points (more = higher confidence)
            freshness_seconds: Age of data (newer = higher confidence)
            error_rate: Percentage of errors (lower = higher confidence)

        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 1.0

        # Sample size penalty
        if sample_size is not None:
            if sample_size < 10:
                confidence *= 0.3
            elif sample_size < 50:
                confidence *= 0.6
            elif sample_size < 200:
                confidence *= 0.8

        # Freshness penalty
        if freshness_seconds is not None:
            if freshness_seconds > 3600:  # >1 hour
                confidence *= 0.6
            elif freshness_seconds > 600:  # >10 minutes
                confidence *= 0.8
            elif freshness_seconds > 60:  # >1 minute
                confidence *= 0.9

        # Error rate penalty
        if error_rate is not None:
            confidence *= (1.0 - error_rate)

        return max(0.0, min(1.0, confidence))

    def build_metadata(self, **kwargs) -> dict:
        """
        Build standard metadata dict with common fields.

        Args:
            **kwargs: Custom metadata fields

        Returns:
            Metadata dict with standard fields + custom fields
        """
        return {
            'adapter': self.__class__.__name__,
            'fetched_at': datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
