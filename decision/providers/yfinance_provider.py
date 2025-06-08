"""
YFinance Price Provider for the Decision Module.

This provider fetches current market prices from Yahoo Finance using the yfinance library.
"""

import yfinance as yf
import time
from typing import Optional
from core.common.logger import logger
from decision.interfaces.price_provider import PriceProvider


class YFinancePriceProvider(PriceProvider):
    """
    Price provider implementation using Yahoo Finance.
    
    This provider converts standard trading symbols to Yahoo Finance format
    and fetches real-time market prices.
    """
    
    # Mapping from standard symbols to Yahoo Finance format
    SYMBOL_MAP = {
        'BTC/USD': 'BTC-USD',
        'BTC/USDT': 'BTC-USD',  # Yahoo doesn't have USDT pairs, use USD
        'ETH/USD': 'ETH-USD', 
        'ETH/USDT': 'ETH-USD',
        'BNB/USD': 'BNB-USD',
        'BNB/USDT': 'BNB-USD',
        'XRP/USD': 'XRP-USD',
        'XRP/USDT': 'XRP-USD',
        'ADA/USD': 'ADA-USD',
        'ADA/USDT': 'ADA-USD',
        'SOL/USD': 'SOL-USD',
        'SOL/USDT': 'SOL-USD',
        'DOGE/USD': 'DOGE-USD',
        'DOGE/USDT': 'DOGE-USD',
        'MATIC/USD': 'MATIC-USD',
        'MATIC/USDT': 'MATIC-USD',
        'DOT/USD': 'DOT-USD',
        'DOT/USDT': 'DOT-USD',
        'AVAX/USD': 'AVAX-USD',
        'AVAX/USDT': 'AVAX-USD',
    }
    
    def __init__(self, **kwargs):
        """Initialize YFinance price provider."""
        super().__init__(**kwargs)
        self._log = logger.bind(provider="yfinance")
        self._last_request_time = 0
        self._request_delay = 2.0  # 2 second delay between requests
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._request_delay:
            sleep_time = self._request_delay - time_since_last
            self._log.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price from Yahoo Finance.
        
        Args:
            symbol: Standard trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            Current price as float, or None if unable to fetch
        """
        try:
            # Apply rate limiting
            self._apply_rate_limit()
            
            # Map to Yahoo Finance format
            yf_symbol = self._map_to_yf_symbol(symbol)
            if not yf_symbol:
                self._log.warning(f"Symbol {symbol} not supported by YFinance")
                return None
            
            self._log.debug(f"Fetching price for {symbol} -> {yf_symbol}")
            
            # Create ticker object
            ticker = yf.Ticker(yf_symbol)
            
            # Try to get current market price from info
            info = ticker.info
            current_price = info.get('regularMarketPrice')
            
            if current_price:
                price = float(current_price)
                self._log.info(f"YFinance price for {symbol}: ${price:,.2f}")
                return price
            
            # Fallback: get last closing price
            self._log.debug(f"No market price found, trying last close for {yf_symbol}")
            hist = ticker.history(period='1d', interval='1m')
            
            if not hist.empty:
                last_price = float(hist['Close'].iloc[-1])
                self._log.info(f"YFinance last price for {symbol}: ${last_price:,.2f}")
                return last_price
            
            self._log.warning(f"No price data available for {symbol} from YFinance")
            return None
            
        except Exception as e:
            self._log.error(f"Error fetching price for {symbol} from YFinance: {e}")
            return None
    
    def _map_to_yf_symbol(self, symbol: str) -> Optional[str]:
        """
        Map standard symbol to Yahoo Finance format.
        
        Args:
            symbol: Standard symbol (e.g., 'BTC/USDT')
            
        Returns:
            Yahoo Finance symbol (e.g., 'BTC-USD') or None if not supported
        """
        return self.SYMBOL_MAP.get(symbol)
    
    def get_supported_symbols(self) -> list[str]:
        """Get list of symbols supported by YFinance provider."""
        return list(self.SYMBOL_MAP.keys())
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return 'yfinance'
    
    async def health_check(self) -> bool:
        """
        Check if YFinance is accessible.
        
        Returns:
            True if can fetch a simple price, False otherwise
        """
        try:
            # Apply rate limiting
            self._apply_rate_limit()
            
            # Test with BTC-USD as it's very reliable
            ticker = yf.Ticker('BTC-USD')
            info = ticker.info
            price = info.get('regularMarketPrice')
            
            if price and price > 0:
                self._log.debug("YFinance health check passed")
                return True
            
            self._log.warning("YFinance health check failed - no price data")
            return False
            
        except Exception as e:
            self._log.error(f"YFinance health check failed: {e}")
            return False