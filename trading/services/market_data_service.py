"""
Market Data Service for Hummingbot Integration

Provides market data for ggShot trading pairs using the Hummingbot API.
Focuses on the top 20 pairs by trading volume.
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from decimal import Decimal

from hummingbot_api_client import Client
from hummingbot_api_client.api.market_data import (
    get_prices_market_data_prices_post,
    get_order_book_market_data_order_book_post,
    get_candles_market_data_candles_post
)
from hummingbot_api_client.models import (
    PriceRequest,
    OrderBookRequest,
    CandlesConfigRequest
)

from core.common.logger import logger


class MarketDataService:
    """Service for fetching market data from Hummingbot API."""
    
    # Top 20 ggShot pairs by typical volume (can be updated based on actual data)
    TOP_20_PAIRS = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT',
        'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT', 'LINKUSDT',
        'LTCUSDT', 'ATOMUSDT', 'NEARUSDT', 'ARBUSDT', 'OPUSDT',
        'INJUSDT', 'SUIUSDT', 'APTUSDT', 'FETUSDT', 'WLDUSDT'
    ]
    
    def __init__(self, api_url: str = None, 
                 username: str = "admin", password: str = "admin",
                 connector: Optional[str] = None):
        """
        Initialize MarketDataService with Hummingbot API credentials.
        
        Args:
            api_url: Hummingbot API URL (defaults to env var or service name)
            username: API username
            password: API password
            connector: Optional connector name. Defaults to binance_perpetual_testnet
        """
        import base64
        
        # Determine API URL - use environment variable or default
        if api_url is None:
            api_url = os.getenv("HUMMINGBOT_API_HOST", "http://localhost:15888")
        
        # Create authenticated client
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.client = Client(
            base_url=api_url,
            headers={"Authorization": f"Basic {encoded_credentials}"}
        )
        
        # Default connector for paper trading - use testnet
        self.connector = connector or "binance_perpetual_testnet"
        
        logger.bind(service="market_data").info(
            f"MarketDataService initialized with API at {api_url}"
        )
    
    async def get_current_prices(self, symbols: Optional[List[str]] = None) -> Dict[str, Decimal]:
        """
        Get current prices for specified symbols or top 20 pairs.
        
        Args:
            symbols: List of symbols to get prices for. If None, uses TOP_20_PAIRS
            
        Returns:
            Dict mapping symbol to current price
        """
        if symbols is None:
            symbols = self.TOP_20_PAIRS
            
        try:
            # Create request for multiple trading pairs
            trading_pairs = [self._format_trading_pair(symbol) for symbol in symbols]
            
            request = PriceRequest(
                connector_name=self.connector,
                trading_pairs=trading_pairs
            )
            
            response = await get_prices_market_data_prices_post.asyncio_detailed(
                client=self.client,
                body=request
            )
            
            if response.status_code == 200:
                data = json.loads(response.content.decode())
                prices = {}
                
                # Extract prices from response
                if 'prices' in data:
                    for pair, price_data in data['prices'].items():
                        # Convert back to our symbol format
                        symbol = pair.replace('-', '')
                        if isinstance(price_data, dict) and 'price' in price_data:
                            prices[symbol] = Decimal(str(price_data['price']))
                        elif isinstance(price_data, (int, float, str)):
                            prices[symbol] = Decimal(str(price_data))
                
                logger.bind(service="market_data").info(
                    f"Retrieved prices for {len(prices)} symbols"
                )
                return prices
            else:
                logger.error(f"Failed to get prices: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return {}
    
    async def get_order_book(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get order book data for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            depth: Number of price levels to retrieve
            
        Returns:
            Dict with 'bids' and 'asks' lists
        """
        try:
            trading_pair = self._format_trading_pair(symbol)
            
            request = OrderBookRequest(
                connector_name=self.connector,
                trading_pair=trading_pair,
                depth=depth
            )
            
            response = await get_order_book_market_data_order_book_post.asyncio_detailed(
                client=self.client,
                body=request
            )
            
            if response.status_code == 200:
                data = json.loads(response.content.decode())
                return {
                    'bids': data.get('bids', []),
                    'asks': data.get('asks', []),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            else:
                logger.error(f"Failed to get order book: {response.status_code}")
                return {'bids': [], 'asks': []}
                
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return {'bids': [], 'asks': []}
    
    async def get_candles(self, symbol: str, interval: str = "15m", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get candlestick data for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Candle interval (e.g., '1m', '15m', '1h')
            limit: Number of candles to retrieve
            
        Returns:
            List of candle data dicts
        """
        try:
            trading_pair = self._format_trading_pair(symbol)
            
            request = CandlesConfigRequest(
                connector_name=self.connector,
                trading_pair=trading_pair,
                interval=interval,  # Pass interval as string directly
                max_records=limit
            )
            
            response = await get_candles_market_data_candles_post.asyncio_detailed(
                client=self.client,
                body=request
            )
            
            if response.status_code == 200:
                data = json.loads(response.content.decode())
                candles = []
                
                # Process candle data
                for candle in data.get('candles', []):
                    candles.append({
                        'timestamp': candle.get('timestamp'),
                        'open': Decimal(str(candle.get('open', 0))),
                        'high': Decimal(str(candle.get('high', 0))),
                        'low': Decimal(str(candle.get('low', 0))),
                        'close': Decimal(str(candle.get('close', 0))),
                        'volume': Decimal(str(candle.get('volume', 0)))
                    })
                
                return candles
            else:
                logger.error(f"Failed to get candles: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching candles for {symbol}: {e}")
            return []
    
    async def get_volume_rankings(self) -> List[tuple[str, Decimal]]:
        """
        Get trading volume rankings for all ggShot symbols.
        
        Returns:
            List of (symbol, 24h_volume) tuples sorted by volume descending
        """
        # For now, return predefined top 20
        # In production, this would fetch actual 24h volume data
        return [(symbol, Decimal('0')) for symbol in self.TOP_20_PAIRS]
    
    def _format_trading_pair(self, symbol: str) -> str:
        """Convert symbol format from 'BTCUSDT' to 'BTC-USDT'."""
        # Handle common patterns
        if symbol.endswith('USDT'):
            base = symbol[:-4]
            return f"{base}-USDT"
        elif symbol.endswith('USD'):
            base = symbol[:-3]
            return f"{base}-USD"
        elif symbol.endswith('BTC'):
            base = symbol[:-3]
            return f"{base}-BTC"
        elif symbol.endswith('ETH'):
            base = symbol[:-3]
            return f"{base}-ETH"
        else:
            # Default: assume last 3-4 chars are quote currency
            if len(symbol) > 6:
                return f"{symbol[:-4]}-{symbol[-4:]}"
            else:
                return symbol


async def test_market_data_service():
    """Test the MarketDataService functionality."""
    service = MarketDataService()
    
    # Test getting prices
    print("\n=== Testing Current Prices ===")
    prices = await service.get_current_prices(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
    for symbol, price in prices.items():
        print(f"{symbol}: ${price}")
    
    # Test getting order book
    print("\n=== Testing Order Book ===")
    order_book = await service.get_order_book('BTCUSDT', depth=5)
    print(f"Top 5 Bids: {order_book['bids'][:5]}")
    print(f"Top 5 Asks: {order_book['asks'][:5]}")
    
    # Test getting candles
    print("\n=== Testing Candles ===")
    candles = await service.get_candles('BTCUSDT', interval='15m', limit=5)
    for candle in candles[:5]:
        print(f"Time: {candle['timestamp']}, Close: {candle['close']}")


if __name__ == "__main__":
    asyncio.run(test_market_data_service())