"""
Binance Funding Rate Adapter

Fetches perpetual futures funding rates from Binance Futures API.
Funding rates indicate long/short leverage positioning in the market.
"""

from datetime import datetime, timezone
from typing import Dict, Any
import aiohttp

from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse, AdapterError


class BinanceFundingAdapter(DataAdapter):
    """
    Adapter for Binance perpetual futures funding rates.

    Funding rates show leverage positioning:
    - Positive rate: Longs pay shorts (long-heavy market)
    - Negative rate: Shorts pay longs (short-heavy market)
    - Extreme rates (>±1%) indicate overleveraged positioning
    """

    name = "binance_funding"
    data_type = "funding_rate"

    # Binance Futures API endpoint
    FUTURES_API_BASE = "https://fapi.binance.com"

    # Longer timeout - Binance API is fast but event loop can be blocked during bot execution
    REQUEST_TIMEOUT = 60  # seconds (default is 30)

    # Funding rate interpretation thresholds
    THRESHOLDS = {
        'extreme_positive': 0.01,      # >1% = extremely overleveraged longs
        'high_positive': 0.005,         # >0.5% = high long leverage
        'neutral_high': 0.001,          # >0.1% = slight long bias
        'neutral_low': -0.001,          # <-0.1% = slight short bias
        'high_negative': -0.005,        # <-0.5% = high short leverage
        'extreme_negative': -0.01       # <-1% = extremely overleveraged shorts
    }

    def _interpret_funding_rate(self, rate: float) -> Dict[str, Any]:
        """
        Interpret funding rate value with trading implications.

        Args:
            rate: Funding rate as decimal (e.g., 0.0001 = 0.01%)

        Returns:
            Dict with interpretation, risk level, and trading implications
        """
        rate_pct = rate * 100  # Convert to percentage for display

        if rate >= self.THRESHOLDS['extreme_positive']:
            return {
                'level': 'extreme_long_leverage',
                'risk': 'high',
                'interpretation': f'Extremely overleveraged longs ({rate_pct:.3f}%)',
                'trading_implication': 'High risk of long liquidation cascade - avoid longs, consider shorts',
                'color': 'red'
            }
        elif rate >= self.THRESHOLDS['high_positive']:
            return {
                'level': 'high_long_leverage',
                'risk': 'medium',
                'interpretation': f'High long leverage ({rate_pct:.3f}%)',
                'trading_implication': 'Crowded long positioning - exercise caution on longs',
                'color': 'orange'
            }
        elif rate >= self.THRESHOLDS['neutral_high']:
            return {
                'level': 'slight_long_bias',
                'risk': 'low',
                'interpretation': f'Slight long bias ({rate_pct:.3f}%)',
                'trading_implication': 'Normal market conditions with mild long preference',
                'color': 'yellow'
            }
        elif rate >= self.THRESHOLDS['neutral_low']:
            return {
                'level': 'neutral',
                'risk': 'minimal',
                'interpretation': f'Balanced positioning ({rate_pct:.3f}%)',
                'trading_implication': 'Neutral funding - no leverage warning signals',
                'color': 'green'
            }
        elif rate >= self.THRESHOLDS['high_negative']:
            return {
                'level': 'slight_short_bias',
                'risk': 'low',
                'interpretation': f'Slight short bias ({rate_pct:.3f}%)',
                'trading_implication': 'Normal market conditions with mild short preference',
                'color': 'yellow'
            }
        elif rate >= self.THRESHOLDS['extreme_negative']:
            return {
                'level': 'high_short_leverage',
                'risk': 'medium',
                'interpretation': f'High short leverage ({rate_pct:.3f}%)',
                'trading_implication': 'Crowded short positioning - exercise caution on shorts',
                'color': 'orange'
            }
        else:
            return {
                'level': 'extreme_short_leverage',
                'risk': 'high',
                'interpretation': f'Extremely overleveraged shorts ({rate_pct:.3f}%)',
                'trading_implication': 'High risk of short squeeze - avoid shorts, consider longs',
                'color': 'red'
            }

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Fetch funding rate from Binance Futures API.

        Args:
            params: Must contain 'symbol' (e.g., 'BTC/USDT')
                   Optional: 'include_mark_price' (boolean) to include mark price data

        Returns:
            AdapterResponse with funding rate data and interpretation
        """
        symbol = params.get('symbol')
        if not symbol:
            raise AdapterError("symbol parameter is required")

        include_mark_price = params.get('include_mark_price', False)

        # Convert symbol format: BTC/USDT -> BTCUSDT
        binance_symbol = symbol.replace('/', '')

        try:
            # Build API URL
            url = f"{self.FUTURES_API_BASE}/fapi/v1/premiumIndex"
            query_params = {'symbol': binance_symbol}

            # Fetch from Binance Futures API with extended timeout
            timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=query_params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AdapterError(
                            f"Binance API returned {response.status}: {error_text}"
                        )
                    data = await response.json()

            # Extract funding rate data
            # Binance response: {"symbol": "BTCUSDT", "markPrice": "...", "lastFundingRate": "0.00010000", ...}
            funding_rate = float(data.get('lastFundingRate', 0))
            next_funding_time = int(data.get('nextFundingTime', 0))

            # Convert timestamp to datetime
            next_funding_dt = datetime.fromtimestamp(
                next_funding_time / 1000,
                tz=timezone.utc
            ) if next_funding_time else None

            # Interpret funding rate
            interpretation = self._interpret_funding_rate(funding_rate)

            # Build response data
            response_data = {
                'symbol': symbol,
                'funding_rate': funding_rate,
                'funding_rate_pct': funding_rate * 100,  # As percentage
                'next_funding_time': next_funding_dt.isoformat() if next_funding_dt else None,
                'interpretation': interpretation,
                'fetched_at': datetime.now(timezone.utc).isoformat()
            }

            # Optionally include mark price data
            if include_mark_price:
                response_data['mark_price'] = float(data.get('markPrice', 0))
                response_data['index_price'] = float(data.get('indexPrice', 0))

            # Calculate confidence based on data quality
            # Funding rates are very reliable from Binance, so high confidence
            confidence = 0.95

            self._log.info(
                f"Fetched funding rate for {symbol}: {funding_rate:.6f} "
                f"({interpretation['level']}, {interpretation['risk']} risk)"
            )

            return AdapterResponse(
                data=response_data,
                metadata=self.build_metadata(
                    source='binance_futures',
                    symbol=binance_symbol,
                    api_endpoint='/fapi/v1/premiumIndex',
                    risk_level=interpretation['risk']
                ),
                confidence=confidence,
                related_queries=[
                    f"Check open interest for {symbol}",
                    f"Query liquidation levels for {symbol}",
                    f"Compare with historical funding rates"
                ]
            )

        except AdapterError:
            raise
        except Exception as e:
            self._log.error(f"Error fetching funding rate for {symbol}: {type(e).__name__}: {e}")
            raise AdapterError(f"Failed to fetch funding rate: {type(e).__name__}: {e}")
