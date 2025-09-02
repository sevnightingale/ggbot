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
            timeout = aiohttp.ClientTimeout(total=30)
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
                
                # Convert to pandas DataFrame
                df = pd.DataFrame({
                    'timestamp': pd.to_datetime(data['timestamp'], unit='ms'),
                    'open': data['open'],
                    'high': data['high'], 
                    'low': data['low'],
                    'close': data['close'],
                    'volume': data['volume']
                })
                
                # Sort by timestamp (oldest first)
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                self._log.info(f"✅ Retrieved {len(df)} candles for {symbol}")
                return df
                
        except Exception as e:
            self._log.error(f"Error fetching candles for {symbol}: {str(e)}")
            raise
    
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
        return ["kucoin", "binance", "gate_io", "ascend_ex", "okx"]
    
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