"""
Binance REST API Adapter for OHLCV data.

Fetches historical OHLCV data directly from Binance REST API as fallback
when WebSocket cache doesn't have the data.
"""

import pandas as pd
from binance import AsyncClient
from typing import Optional

from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse, AdapterError


class BinanceRestAdapter(DataAdapter):
    """
    Adapter for fetching OHLCV from Binance REST API.

    Used as fallback when Redis WebSocket cache doesn't have the data.
    """

    name = "binance_rest"
    data_type = "ohlcv"

    # Timeframe mapping (ggbots format -> Binance format)
    TIMEFRAME_MAP = {
        "5m": AsyncClient.KLINE_INTERVAL_5MINUTE,
        "15m": AsyncClient.KLINE_INTERVAL_15MINUTE,
        "30m": AsyncClient.KLINE_INTERVAL_30MINUTE,
        "1h": AsyncClient.KLINE_INTERVAL_1HOUR,
        "4h": AsyncClient.KLINE_INTERVAL_4HOUR,
        "1d": AsyncClient.KLINE_INTERVAL_1DAY,
        "1w": AsyncClient.KLINE_INTERVAL_1WEEK,
    }

    def __init__(self):
        """Initialize Binance REST adapter."""
        super().__init__()
        self.client: Optional[AsyncClient] = None

    async def _get_client(self) -> AsyncClient:
        """Get or create Binance async client."""
        if not self.client:
            # Create client without API key (public endpoints only)
            self.client = await AsyncClient.create()
        return self.client

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Fetch OHLCV data from Binance REST API.

        Args:
            params: Query parameters with symbol, timeframe, limit

        Returns:
            AdapterResponse with DataFrame

        Raises:
            AdapterError: If fetch fails
        """
        symbol = params.symbol
        timeframe = params.timeframe
        limit = params.get('limit', 200)

        # Convert symbol format: BTC/USDT -> BTCUSDT
        binance_symbol = symbol.replace('/', '')

        # Convert timeframe to Binance format
        binance_interval = self.TIMEFRAME_MAP.get(timeframe)
        if not binance_interval:
            raise AdapterError(
                f"Unsupported timeframe: {timeframe}. "
                f"Supported: {list(self.TIMEFRAME_MAP.keys())}"
            )

        self._log.info(f"Fetching {limit} {timeframe} candles for {symbol} from Binance REST")

        try:
            client = await self._get_client()

            # Fetch klines from Binance
            klines = await client.get_klines(
                symbol=binance_symbol,
                interval=binance_interval,
                limit=limit
            )

            if not klines:
                raise AdapterError(f"No data returned from Binance for {symbol}")

            # Convert to DataFrame
            # Binance kline format: [timestamp, open, high, low, close, volume, ...]
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Keep only OHLCV columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)

            # Sort by timestamp (oldest first)
            df = df.sort_values('timestamp').reset_index(drop=True)

            self._log.info(f"✅ Retrieved {len(df)} candles from Binance REST API")

            # Calculate confidence (REST API is reliable but not real-time)
            confidence = self.calculate_confidence(sample_size=len(df))

            return AdapterResponse(
                data=df,
                metadata=self.build_metadata(
                    source="binance_rest",
                    symbol=binance_symbol,
                    interval=binance_interval,
                    candle_count=len(df)
                ),
                confidence=confidence,
                related_queries=self._suggest_related_queries(symbol, timeframe)
            )

        except AdapterError:
            raise
        except Exception as e:
            error_msg = str(e) if str(e) else repr(e)
            self._log.error(f"Binance REST API error for {symbol}: {type(e).__name__}: {error_msg}")
            raise AdapterError(f"Failed to fetch from Binance REST API: {type(e).__name__}: {error_msg}")

    def _suggest_related_queries(self, symbol: str, timeframe: str) -> list:
        """Suggest related queries."""
        other_timeframes = ["5m", "15m", "1h", "4h", "1d"]
        related = []

        for tf in other_timeframes:
            if tf != timeframe:
                related.append(f"ohlcv:{symbol}:{tf}")
                if len(related) >= 3:
                    break

        return related

    async def close(self):
        """Close Binance client."""
        if self.client:
            await self.client.close_connection()
            self.client = None
        await super().close()
