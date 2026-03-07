"""
CoinGecko Global Adapter - USDT Dominance and Global Crypto Market Metrics

Fetches global crypto market data from CoinGecko's free /global endpoint.
Primary use case: USDT dominance as a risk-on/risk-off indicator.

Rising USDT dominance = money flowing into stables = risk-off (bearish for crypto)
Falling USDT dominance = money leaving stables for risk assets = risk-on (bullish)

Cost: $0/query (free tier, ~10-30 calls/min limit)
"""

from datetime import datetime, timezone
from typing import Dict, Any
import aiohttp

from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse, AdapterError


class CoinGeckoGlobalAdapter(DataAdapter):
    """
    Adapter for CoinGecko global crypto market data.

    Primary metric: USDT dominance (market_cap_percentage.usdt)
    Also captures: total market cap, 24h change
    """

    name = "coingecko_global"
    data_type = "coingecko_global"

    API_URL = "https://api.coingecko.com/api/v3/global"
    REQUEST_TIMEOUT = 30  # seconds

    # USDT dominance interpretation thresholds
    THRESHOLDS = {
        'high': 10.0,    # >10% = high stablecoin dominance, risk-off
        'low': 6.0,      # <6% = low stablecoin allocation, risk-on
    }

    def _interpret_usdt_dominance(self, value: float) -> Dict[str, Any]:
        """Interpret USDT dominance percentage for crypto trading context."""
        if value > self.THRESHOLDS['high']:
            return {
                'signal': 'bearish',
                'crypto_regime': 'risk_off',
                'interpretation': (
                    f"USDT dominance at {value:.2f}% — high stablecoin allocation. "
                    f"Capital parked in stables suggests risk-off sentiment, bearish for crypto."
                ),
            }
        elif value < self.THRESHOLDS['low']:
            return {
                'signal': 'bullish',
                'crypto_regime': 'risk_on',
                'interpretation': (
                    f"USDT dominance at {value:.2f}% — low stablecoin allocation. "
                    f"Capital deployed into risk assets, bullish for crypto."
                ),
            }
        else:
            return {
                'signal': 'neutral',
                'crypto_regime': 'neutral',
                'interpretation': (
                    f"USDT dominance at {value:.2f}% — normal range (6-10%). "
                    f"Balanced allocation between stables and risk assets."
                ),
            }

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Fetch global crypto market data from CoinGecko.

        Args:
            params: Must contain 'query_type' (currently only 'usdt_dominance')

        Returns:
            AdapterResponse with USDT dominance data and interpretation
        """
        query_type = params.get('query_type')
        if query_type != 'usdt_dominance':
            raise AdapterError(f"Unsupported query_type: {query_type}. Available: usdt_dominance")

        try:
            timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.API_URL) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AdapterError(
                            f"CoinGecko API returned {response.status}: {error_text}"
                        )
                    raw = await response.json()

            data = raw.get('data', {})
            market_cap_pct = data.get('market_cap_percentage', {})
            usdt_dominance = market_cap_pct.get('usdt', 0.0)
            total_market_cap = data.get('total_market_cap', {}).get('usd', 0)
            market_cap_change_24h = data.get('market_cap_change_percentage_24h_usd', 0.0)

            interpretation = self._interpret_usdt_dominance(usdt_dominance)

            response_data = {
                'value': round(usdt_dominance, 2),
                'total_crypto_market_cap_usd': total_market_cap,
                'market_cap_change_24h_pct': round(market_cap_change_24h, 2),
                **interpretation,
                'fetched_at': datetime.now(timezone.utc).isoformat(),
            }

            self._log.info(
                f"USDT dominance: {usdt_dominance:.2f}% — {interpretation['signal']} "
                f"({interpretation['crypto_regime']})"
            )

            return AdapterResponse(
                data=response_data,
                metadata=self.build_metadata(
                    source='coingecko',
                    api_endpoint='/api/v3/global',
                    query_type=query_type,
                ),
                confidence=0.95,
            )

        except AdapterError:
            raise
        except Exception as e:
            self._log.error(f"Error fetching CoinGecko global data: {type(e).__name__}: {e}")
            raise AdapterError(f"Failed to fetch CoinGecko global data: {type(e).__name__}: {e}")
