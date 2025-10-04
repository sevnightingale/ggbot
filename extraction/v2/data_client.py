"""
Hummingbot Data Client for V2 extraction system.

Provides clean interface to Hummingbot API for OHLCV data retrieval.
"""

import os
import aiohttp
import asyncio
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import base64

from core.common.logger import logger


class HummingbotDataClient:
    """
    Clean interface to Hummingbot API for market data retrieval.
    
    This client handles authentication, rate limiting, and data formatting
    to provide pandas-ready OHLCV data.
    """
    
    def __init__(self, base_url: str = None, username: str = None, password: str = None):
        """
        Initialize Hummingbot data client.
        
        Args:
            base_url: Hummingbot API base URL (default: http://localhost:8888)
            username: API username (default: from HBOT_USERNAME env var)
            password: API password (default: from HBOT_PASSWORD env var)
        """
        self.base_url = base_url or os.environ.get("HUMMINGBOT_API_URL", "http://localhost:8888")
        self.username = username or os.environ.get("HBOT_USERNAME")
        self.password = password or os.environ.get("HBOT_PASSWORD")
        
        if not self.username or not self.password:
            raise ValueError("Hummingbot credentials required. Set HBOT_USERNAME and HBOT_PASSWORD env vars.")
        
        # Create auth headers
        credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._log = logger.bind(component="hummingbot_client")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Establish connection to Hummingbot API."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=10)  # Balanced timeout for reliability under load
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )
            self._log.info("Connected to Hummingbot API")
    
    async def disconnect(self):
        """Close connection to Hummingbot API."""
        if self.session:
            await self.session.close()
            self.session = None
            self._log.info("Disconnected from Hummingbot API")

    async def ensure_connected(self):
        """Ensure connection is established (idempotent)."""
        if not self.session:
            await self.connect()
    
    async def get_candles(
        self, 
        symbol: str, 
        timeframe: str = "1h", 
        limit: int = 100,
        connector: str = "kucoin"
    ) -> pd.DataFrame:
        """
        Get OHLCV candle data from Hummingbot API.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")  
            timeframe: Candle timeframe (e.g., "1h", "15m", "1d")
            limit: Number of candles to retrieve
            connector: Exchange connector name (default: "kucoin")
            
        Returns:
            pandas DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if not self.session:
            await self.connect()
        
        # Convert symbol format for Hummingbot (BTC/USDT -> BTC-USDT)
        hbot_symbol = symbol.replace("/", "-")
        
        url = f"{self.base_url}/market-data/candles"
        payload = {
            "connector_name": connector,
            "trading_pair": hbot_symbol,
            "interval": timeframe,
            "max_records": limit
        }
        
        self._log.info(f"Fetching {limit} {timeframe} candles for {symbol} from {connector}")
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Hummingbot API error {response.status}: {error_text}")
                
                data = await response.json()

                # Handle error responses that are dicts (API returns errors with status 200 sometimes)
                if isinstance(data, dict):
                    if "error" in data:
                        raise Exception(f"API error: {data['error']}")
                    else:
                        raise Exception(f"Expected list of candles, got dict: {data}")

                # API returns list of dicts: [{'timestamp': 1756843200.0, 'open': 110805.6, ...}, ...]
                if not isinstance(data, list):
                    raise Exception(f"Expected list of candles, got: {type(data)}")

                if not data:
                    raise Exception("No candle data returned")
                
                # Convert to pandas DataFrame
                df = pd.DataFrame(data)
                
                # Convert timestamp from seconds to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                
                # Sort by timestamp (oldest first)
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                self._log.info(f"✅ Retrieved {len(df)} candles for {symbol}")
                return df

        except Exception as e:
            # Handle empty error messages from aiohttp exceptions
            error_msg = str(e) or repr(e) or type(e).__name__
            self._log.error(f"Error fetching candles for {symbol}: {error_msg}")
            raise

    async def get_candles_with_fallback(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get OHLCV candle data with automatic exchange fallback.

        Tries multiple exchanges in priority order until one succeeds.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Candle timeframe (e.g., "1h", "15m", "1d")
            limit: Number of candles to retrieve

        Returns:
            pandas DataFrame with columns: timestamp, open, high, low, close, volume

        Raises:
            Exception: If symbol is not available on any exchange
        """
        exchanges = self.get_supported_connectors()

        self._log.info(f"Attempting to fetch {symbol} from {len(exchanges)} exchanges")

        for i, exchange in enumerate(exchanges):
            try:
                self._log.debug(f"Trying {symbol} on {exchange} (attempt {i+1}/{len(exchanges)})")

                df = await self.get_candles(symbol, timeframe, limit, exchange)

                if df is not None and len(df) > 0:
                    if i > 0:  # Only log fallback if not first exchange
                        self._log.info(f"✅ Fallback success: {symbol} retrieved from {exchange}")
                    else:
                        self._log.info(f"✅ {symbol} retrieved from {exchange}")
                    return df

            except Exception as e:
                error_msg = str(e).strip()
                self._log.debug(f"❌ {symbol} failed on {exchange}: {error_msg}")

                # Continue to next exchange
                continue

        # All exchanges failed
        raise Exception(f"Symbol {symbol} not available on any of {len(exchanges)} exchanges: {exchanges}")

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Hummingbot API.
        
        Returns:
            Dictionary with connection status and API info
        """
        if not self.session:
            await self.connect()
        
        try:
            # Test with a simple API call
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    return {
                        "status": "connected",
                        "base_url": self.base_url,
                        "api_status": response.status
                    }
                else:
                    return {
                        "status": "error",
                        "base_url": self.base_url,
                        "api_status": response.status,
                        "error": await response.text()
                    }
        except Exception as e:
            return {
                "status": "connection_failed",
                "base_url": self.base_url,
                "error": str(e)
            }
    
    def get_supported_timeframes(self) -> List[str]:
        """
        Get list of supported timeframes.
        
        Returns:
            List of supported timeframe strings
        """
        return ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]
    
    def get_supported_connectors(self) -> List[str]:
        """
        Get list of supported exchange connectors.
        
        Returns:
            List of supported connector names
        """
        return ["binance", "kucoin", "gate_io", "ascend_ex", "okx"]
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol format for consistency.
        
        Args:
            symbol: Trading pair in any format
            
        Returns:
            Normalized symbol in "BASE/QUOTE" format
        """
        # Handle different formats: BTC-USDT, BTC_USDT, BTCUSDT -> BTC/USDT
        if "/" in symbol:
            return symbol.upper()
        elif "-" in symbol:
            return symbol.replace("-", "/").upper()
        elif "_" in symbol:
            return symbol.replace("_", "/").upper()
        else:
            # Handle concatenated format like BTCUSDT -> BTC/USDT
            # This is more complex and may need symbol-specific logic
            # For now, assume it's already in the right format
            return symbol.upper()


# Convenience function for quick usage
async def get_market_data(
    symbol: str,
    timeframe: str = "1h", 
    limit: int = 100,
    connector: str = "kucoin"
) -> pd.DataFrame:
    """
    Convenience function to quickly get market data.
    
    Args:
        symbol: Trading pair (e.g., "BTC/USDT")
        timeframe: Candle timeframe (e.g., "1h", "15m", "1d") 
        limit: Number of candles to retrieve
        connector: Exchange connector name
        
    Returns:
        pandas DataFrame with OHLCV data
    """
    async with HummingbotDataClient() as client:
        return await client.get_candles(symbol, timeframe, limit, connector)