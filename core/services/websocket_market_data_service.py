"""
WebSocket Market Data Service

Real-time market data streaming service using Binance WebSocket API.
Fetches historical candles on startup, then maintains 200-candle windows
via real-time WebSocket updates.

This replaces polling-based approaches with push-based streaming for:
- Zero latency (sub-100ms updates)
- No rate limits
- No timeouts
- Always-fresh data
"""

import asyncio
import os
import pickle
import time
from datetime import datetime
from typing import List, Dict, Any
from binance import AsyncClient, BinanceSocketManager
import redis.asyncio as redis
from dotenv import load_dotenv

from core.common.logger import logger

load_dotenv()


class WebSocketMarketDataService:
    """
    Real-time market data service using Binance WebSocket streams.

    Architecture:
    1. Startup: Fetch 200 historical candles via REST (one-time)
    2. Runtime: Subscribe to WebSocket streams for real-time updates
    3. Storage: Maintain 200-candle rolling windows in Redis
    """

    # 100 overlapping symbols (ggbots + Symphony compatible)
    # Expanded from 20 → 100 for comprehensive market coverage
    SYMBOLS = [
        '1INCHUSDT', 'AAVEUSDT', 'ADAUSDT', 'ALGOUSDT', 'ALICEUSDT', 'ALTUSDT', 'ANKRUSDT', 'APEUSDT', 'API3USDT', 'APTUSDT',
        'ARUSDT', 'ARBUSDT', 'ARKMUSDT', 'ASTRUSDT', 'ATOMUSDT', 'AUCTIONUSDT', 'AVAXUSDT', 'BATUSDT', 'BCHUSDT', 'BNBUSDT',
        'BOMEUSDT', 'BTCUSDT', 'CAKEUSDT', 'CFXUSDT', 'COMPUSDT', 'DASHUSDT', 'DOGEUSDT', 'DOTUSDT', 'DYDXUSDT', 'EGLDUSDT',
        'ENAUSDT', 'ENSUSDT', 'ETCUSDT', 'ETHUSDT', 'ETHFIUSDT', 'FETUSDT', 'FILUSDT', 'FLOWUSDT', 'GALAUSDT', 'GMTUSDT',
        'GMXUSDT', 'GRTUSDT', 'HBARUSDT', 'ICPUSDT', 'INJUSDT', 'IOTXUSDT', 'JASMYUSDT', 'JTOUSDT', 'JUPUSDT', 'KSMUSDT',
        'LDOUSDT', 'LINKUSDT', 'LRCUSDT', 'LTCUSDT', 'MAGICUSDT', 'MANAUSDT', 'MASKUSDT', 'NEARUSDT', 'NEOUSDT', 'NMRUSDT',
        'NOTUSDT', 'NTRNUSDT', 'ONDOUSDT', 'OPUSDT', 'ORDIUSDT', 'PENDLEUSDT', 'PEOPLEUSDT', 'PYTHUSDT', 'QTUMUSDT', 'RAREUSDT',
        'RENDERUSDT', 'ROSEUSDT', 'RSRUSDT', 'RVNUSDT', 'SUSDT', 'SANDUSDT', 'SEIUSDT', 'SKLUSDT', 'SNXUSDT', 'SOLUSDT',
        'STORJUSDT', 'STRKUSDT', 'STXUSDT', 'TAOUSDT', 'THETAUSDT', 'TIAUSDT', 'TRBUSDT', 'TRXUSDT', 'TURBOUSDT', 'TWTUSDT',
        'VETUSDT', 'WUSDT', 'WIFUSDT', 'WLDUSDT', 'WOOUSDT', 'XRPUSDT', 'YFIUSDT', 'ZILUSDT', 'ZROUSDT', 'ZRXUSDT'
    ]

    # Timeframes to track (all 7 used by scheduler)
    TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h', '1d', '1w']

    # Binance WebSocket timeframe mapping
    BINANCE_TF_MAP = {
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '4h': '4h',
        '1d': '1d',
        '1w': '1w'
    }

    # Binance REST API timeframe mapping (uses different format)
    BINANCE_REST_TF_MAP = {
        '5m': AsyncClient.KLINE_INTERVAL_5MINUTE,
        '15m': AsyncClient.KLINE_INTERVAL_15MINUTE,
        '30m': AsyncClient.KLINE_INTERVAL_30MINUTE,
        '1h': AsyncClient.KLINE_INTERVAL_1HOUR,
        '4h': AsyncClient.KLINE_INTERVAL_4HOUR,
        '1d': AsyncClient.KLINE_INTERVAL_1DAY,
        '1w': AsyncClient.KLINE_INTERVAL_1WEEK
    }

    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.binance_client = None
        self.socket_manager = None
        self._log = logger.bind(service="websocket_market_data")

        # Stats
        self.candles_received = 0
        self.candles_stored = 0
        self.live_candles_stored = 0
        self.errors = 0

    async def start(self):
        """Start the WebSocket market data service."""
        self._log.info("🚀 Starting WebSocket Market Data Service")

        try:
            # Initialize connections
            await self._initialize()

            # Phase 1: Fetch historical data (one-time)
            await self._fetch_historical_candles()

            # Phase 2: Start WebSocket streams (forever)
            await self._start_websocket_streams()

        except Exception as e:
            self._log.error(f"Service failed: {e}")
            raise
        finally:
            await self._cleanup()

    async def _initialize(self):
        """Initialize Redis and Binance connections."""
        self._log.info("Initializing connections...")

        # Connect to Redis
        self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
        await self.redis_client.ping()
        self._log.info("✅ Redis connected")

        # Connect to Binance
        self.binance_client = await AsyncClient.create()
        self._log.info("✅ Binance client created")

    async def _fetch_historical_candles(self):
        """Fetch 200 historical candles for all symbols/timeframes via REST API."""
        self._log.info(f"📥 Fetching historical candles for {len(self.SYMBOLS)} symbols × {len(self.TIMEFRAMES)} timeframes...")

        start_time = datetime.now()
        tasks = []

        for symbol in self.SYMBOLS:
            for timeframe in self.TIMEFRAMES:
                task = self._fetch_and_store_historical(symbol, timeframe)
                tasks.append(task)

        # Fetch all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes/failures
        successes = sum(1 for r in results if not isinstance(r, Exception))
        failures = sum(1 for r in results if isinstance(r, Exception))

        elapsed = (datetime.now() - start_time).total_seconds()
        self._log.info(f"✅ Historical fetch complete: {successes} success, {failures} failed in {elapsed:.1f}s")

    async def _fetch_and_store_historical(self, symbol: str, timeframe: str):
        """Fetch and store 200 historical candles for one symbol/timeframe."""
        try:
            # Get Binance REST API timeframe format
            binance_tf = self.BINANCE_REST_TF_MAP.get(timeframe)
            if not binance_tf:
                self._log.warning(f"Unsupported timeframe: {timeframe}")
                return

            # Fetch 200 historical candles
            klines = await self.binance_client.get_klines(
                symbol=symbol,
                interval=binance_tf,
                limit=200
            )

            if not klines:
                self._log.warning(f"No historical data for {symbol} {timeframe}")
                return

            # Convert to our format
            candles = []
            for kline in klines:
                candle = {
                    'timestamp': int(kline[0]),  # Open time
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                }
                candles.append(candle)

            # Store in Redis with slash format for consistency
            symbol_slash = f"{symbol[:-4]}/{symbol[-4:]}"  # BTCUSDT -> BTC/USDT
            key = f"ws:candles:{symbol_slash}:{timeframe}:200"  # ws: prefix to avoid collision

            await self.redis_client.setex(
                key,
                3600,  # 1 hour TTL
                pickle.dumps(candles)
            )

            self._log.debug(f"✅ Stored {len(candles)} historical candles for {symbol_slash} {timeframe}")

        except Exception as e:
            self._log.error(f"Failed to fetch historical for {symbol} {timeframe}: {e}")
            raise

    async def _start_websocket_streams(self):
        """
        Start WebSocket streams with automatic reconnection and health monitoring.

        Features:
        - Automatic reconnection on disconnect
        - Exponential backoff retry logic
        - Connection health monitoring
        - Silence detection (reconnect if no messages for 2 minutes)
        """
        self._log.info(f"🌐 Starting WebSocket streams for {len(self.SYMBOLS)} symbols × {len(self.TIMEFRAMES)} timeframes...")

        # Build stream names (do this once, reuse on reconnect)
        streams = []
        for symbol in self.SYMBOLS:
            for timeframe in self.TIMEFRAMES:
                binance_tf = self.BINANCE_TF_MAP.get(timeframe)
                if binance_tf:
                    stream_name = f"{symbol.lower()}@kline_{binance_tf}"
                    streams.append(stream_name)

        self._log.info(f"📡 Will subscribe to {len(streams)} streams...")

        # Connection retry configuration
        retry_count = 0
        max_retries = 100  # Essentially unlimited retries
        base_delay = 1
        max_delay = 300  # Max 5 minutes between retries

        # Health monitoring configuration
        silence_threshold = 60  # Reconnect if no messages for 60 seconds
        recv_timeout = 30  # Timeout for individual recv() calls
        proactive_reconnect_interval = 900  # Proactive reconnect every 15 minutes (900s)

        # Outer reconnection loop
        while retry_count < max_retries:
            try:
                self._log.info(f"🔌 Connecting to Binance WebSocket (attempt {retry_count + 1})...")

                # Create socket manager (fresh connection)
                self.socket_manager = BinanceSocketManager(self.binance_client)
                multiplex_socket = self.socket_manager.multiplex_socket(streams)

                last_message_time = time.time()
                connection_start_time = time.time()

                async with multiplex_socket as stream:
                    self._log.info("✅ WebSocket streams active - receiving real-time data")

                    # Refetch historical candles after reconnection to rebuild cache
                    if retry_count > 0:  # Only on reconnection, not first connection
                        self._log.info("🔄 Refetching historical candles after reconnection...")
                        await self._fetch_historical_candles()
                        self._log.info("✅ Historical candles refetched - cache rebuilt")

                    retry_count = 0  # Reset retry count on successful connection

                    # Inner message processing loop
                    while True:
                        try:
                            # Receive with timeout to prevent infinite blocking
                            msg = await asyncio.wait_for(stream.recv(), timeout=recv_timeout)
                            last_message_time = time.time()
                            await self._handle_kline_message(msg)

                        except asyncio.TimeoutError:
                            # No message received within timeout - check for prolonged silence
                            silence_duration = time.time() - last_message_time
                            connection_uptime = time.time() - connection_start_time

                            # Proactive reconnect: Refresh connection every 15 minutes
                            if connection_uptime > proactive_reconnect_interval:
                                self._log.info(
                                    f"🔄 Proactive reconnect after {connection_uptime/60:.1f}min "
                                    f"(prevents Binance disconnect) - reconnecting"
                                )
                                break  # Exit inner loop to reconnect

                            # Reactive reconnect: Connection is silent/dead
                            if silence_duration > silence_threshold:
                                # No messages for too long - connection likely dead
                                self._log.error(
                                    f"⚠️ Connection silent for {silence_duration:.0f}s "
                                    f"(uptime: {connection_uptime/60:.1f}min) - reconnecting"
                                )
                                break  # Exit inner loop to reconnect

                            # Still within threshold - just log debug message
                            if silence_duration > 30:  # Log if silent for > 30 seconds
                                self._log.warning(
                                    f"No messages for {silence_duration:.0f}s "
                                    f"(threshold: {silence_threshold}s)"
                                )

                        except Exception as e:
                            # Error processing message - log but continue
                            self._log.error(f"Error processing message: {e}")
                            self.errors += 1

                            # Log stats every 100 errors
                            if self.errors % 100 == 0:
                                self._log.warning(
                                    f"Stats: {self.candles_received} received, "
                                    f"{self.candles_stored} stored, {self.errors} errors"
                                )

            except Exception as e:
                # Connection failed or inner loop exited - reconnect
                retry_count += 1
                delay = min(base_delay * (2 ** retry_count), max_delay)

                self._log.error(
                    f"❌ WebSocket connection failed: {e} "
                    f"(retry {retry_count}/{max_retries} in {delay}s)"
                )

                await asyncio.sleep(delay)
                continue

        # If we get here, we've exceeded max retries
        raise Exception(f"WebSocket service failed after {max_retries} reconnection attempts")

    async def _handle_kline_message(self, msg: Dict[str, Any]):
        """Handle incoming kline (candle) message from WebSocket."""
        try:
            # Extract data from message
            if 'data' not in msg:
                return

            data = msg['data']
            if 'k' not in data:
                return

            kline = data['k']

            # Extract candle data
            symbol = kline['s']  # BTCUSDT
            timeframe = kline['i']  # 1h

            candle = {
                'timestamp': int(kline['t']),  # Open time
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c']),
                'volume': float(kline['v'])
            }

            # Convert symbol to slash format
            symbol_slash = f"{symbol[:-4]}/{symbol[-4:]}"  # BTCUSDT -> BTC/USDT

            # Store live candle for current price (updates every ~1 second)
            if not kline['x']:  # x = is candle closed (False = live/current candle)
                await self._store_live_candle(symbol_slash, timeframe, candle)
                return

            # Closed candle - store in 200-candle window
            self.candles_received += 1

            # Update rolling 200-candle window
            await self._update_candle_window(symbol_slash, timeframe, candle)

            self.candles_stored += 1

            # Log every 100 candles
            if self.candles_stored % 100 == 0:
                self._log.info(f"📊 Stats: {self.candles_received} received, {self.candles_stored} stored, {self.errors} errors")

        except Exception as e:
            self._log.error(f"Failed to handle kline message: {e}")
            self.errors += 1

    async def _update_candle_window(self, symbol: str, timeframe: str, new_candle: Dict[str, Any]):
        """Update 200-candle rolling window in Redis."""
        try:
            key = f"ws:candles:{symbol}:{timeframe}:200"  # ws: prefix to avoid collision with extraction cache

            # Get existing candles
            existing_data = await self.redis_client.get(key)

            if existing_data:
                candles = pickle.loads(existing_data)
            else:
                candles = []

            # Append new candle
            candles.append(new_candle)

            # Keep only last 200
            candles = candles[-200:]

            # Store back to Redis
            await self.redis_client.setex(
                key,
                3600,  # 1 hour TTL
                pickle.dumps(candles)
            )

            self._log.debug(f"✅ Updated {symbol} {timeframe} (now {len(candles)} candles)")

        except Exception as e:
            self._log.error(f"Failed to update candle window for {symbol} {timeframe}: {e}")
            raise

    async def _store_live_candle(self, symbol: str, timeframe: str, candle: Dict[str, Any]):
        """
        Store the current (unclosed) candle for live price data.

        This provides real-time price updates (~1 second granularity) by storing
        the current candle as it updates. The 'close' price represents the most
        recent trade price.

        Args:
            symbol: Trading pair in slash format (e.g., BTC/USDT)
            timeframe: Candle timeframe (e.g., 1h, 5m)
            candle: Current candle data dict
        """
        try:
            # Store one live candle per symbol (timeframe-agnostic for simplicity)
            # We use the 5m timeframe as it updates most frequently
            if timeframe == '5m':
                key = f"price:live:{symbol}"

                await self.redis_client.setex(
                    key,
                    60,  # 60 second TTL (refreshed on every update)
                    pickle.dumps(candle)
                )

                self.live_candles_stored += 1

                # Log every 100 live candles to see activity
                if self.live_candles_stored % 100 == 0:
                    self._log.info(f"📍 Live candles: {self.live_candles_stored} stored")

        except Exception as e:
            self._log.error(f"Failed to store live candle for {symbol}: {e}")
            # Don't raise - this is a nice-to-have feature, don't break the main flow

    async def _cleanup(self):
        """Clean up connections."""
        self._log.info("🔄 Cleaning up connections...")

        if self.binance_client:
            await self.binance_client.close_connection()
            self._log.info("✅ Binance client closed")

        if self.redis_client:
            await self.redis_client.close()
            self._log.info("✅ Redis client closed")


async def main():
    """Main entry point for the service."""
    service = WebSocketMarketDataService()

    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service crashed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
