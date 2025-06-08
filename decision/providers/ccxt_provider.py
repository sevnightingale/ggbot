"""
CCXT Price Provider for the Decision Module.

This provider fetches current market prices from liquid cryptocurrency exchanges 
using the CCXT library. It tries multiple exchanges for reliability.
"""

import ccxt.async_support as ccxt
from typing import Optional, List
from core.common.logger import logger
from decision.interfaces.price_provider import PriceProvider


class CCXTPriceProvider(PriceProvider):
    """
    Price provider implementation using CCXT library.
    
    This provider fetches prices from multiple liquid exchanges (NOT testnets)
    to ensure accurate real market pricing. It tries exchanges in order of 
    preference until it gets a successful response.
    """
    
    # Ordered list of exchanges to try (most liquid/reliable first)
    EXCHANGE_PRIORITY = ['binance', 'coinbase', 'kraken', 'okx', 'bybit']
    
    # Symbol mappings for different exchanges
    EXCHANGE_SYMBOL_MAPS = {
        'binance': {
            'BTC/USD': 'BTC/USDT',  # Binance doesn't have true USD pairs
            'BTC/USDT': 'BTC/USDT',
            'ETH/USD': 'ETH/USDT',
            'ETH/USDT': 'ETH/USDT',
            'BNB/USD': 'BNB/USDT',
            'BNB/USDT': 'BNB/USDT',
            'XRP/USD': 'XRP/USDT',
            'XRP/USDT': 'XRP/USDT',
            'ADA/USD': 'ADA/USDT',
            'ADA/USDT': 'ADA/USDT',
            'SOL/USD': 'SOL/USDT',
            'SOL/USDT': 'SOL/USDT',
            'DOGE/USD': 'DOGE/USDT',
            'DOGE/USDT': 'DOGE/USDT',
        },
        'coinbase': {
            'BTC/USD': 'BTC/USD',
            'BTC/USDT': 'BTC/USD',  # Use USD equivalent
            'ETH/USD': 'ETH/USD',
            'ETH/USDT': 'ETH/USD',
            'SOL/USD': 'SOL/USD',
            'SOL/USDT': 'SOL/USD',
        },
        'kraken': {
            'BTC/USD': 'BTC/USD',
            'BTC/USDT': 'BTC/USDT',
            'ETH/USD': 'ETH/USD',
            'ETH/USDT': 'ETH/USDT',
            'XRP/USD': 'XRP/USD',
            'XRP/USDT': 'XRP/USDT',
            'ADA/USD': 'ADA/USD',
            'ADA/USDT': 'ADA/USDT',
            'SOL/USD': 'SOL/USD',
            'SOL/USDT': 'SOL/USDT',
            'DOGE/USD': 'DOGE/USD',
            'DOGE/USDT': 'DOGE/USDT',
        },
        'okx': {
            'BTC/USD': 'BTC/USDT',  # OKX uses USDT
            'BTC/USDT': 'BTC/USDT',
            'ETH/USD': 'ETH/USDT',
            'ETH/USDT': 'ETH/USDT',
            'BNB/USD': 'BNB/USDT',
            'BNB/USDT': 'BNB/USDT',
            'XRP/USD': 'XRP/USDT',
            'XRP/USDT': 'XRP/USDT',
            'ADA/USD': 'ADA/USDT',
            'ADA/USDT': 'ADA/USDT',
            'SOL/USD': 'SOL/USDT',
            'SOL/USDT': 'SOL/USDT',
            'DOGE/USD': 'DOGE/USDT',
            'DOGE/USDT': 'DOGE/USDT',
        },
        'bybit': {
            'BTC/USD': 'BTC/USDT',
            'BTC/USDT': 'BTC/USDT',
            'ETH/USD': 'ETH/USDT',
            'ETH/USDT': 'ETH/USDT',
            'SOL/USD': 'SOL/USDT',
            'SOL/USDT': 'SOL/USDT',
        }
    }
    
    def __init__(self, **kwargs):
        """Initialize CCXT price provider."""
        super().__init__(**kwargs)
        self._log = logger.bind(provider="ccxt")
        self._exchange_clients = {}  # Cache for exchange clients
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price from CCXT exchanges.
        
        Args:
            symbol: Standard trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            Current price as float, or None if unable to fetch
        """
        for exchange_name in self.EXCHANGE_PRIORITY:
            try:
                price = await self._get_price_from_exchange(exchange_name, symbol)
                if price:
                    self._log.info(f"CCXT price for {symbol} from {exchange_name}: ${price:,.2f}")
                    return price
                    
            except Exception as e:
                self._log.warning(f"Failed to get price from {exchange_name}: {e}")
                continue
        
        self._log.error(f"Failed to get price for {symbol} from all CCXT exchanges")
        return None
    
    async def _get_price_from_exchange(self, exchange_name: str, symbol: str) -> Optional[float]:
        """
        Get price from a specific exchange.
        
        Args:
            exchange_name: Name of the exchange (e.g., 'binance')
            symbol: Standard trading symbol
            
        Returns:
            Price as float or None if failed
        """
        try:
            # Get or create exchange client
            exchange = await self._get_exchange_client(exchange_name)
            if not exchange:
                return None
            
            # Map symbol to exchange-specific format
            exchange_symbol = self._map_symbol_for_exchange(exchange_name, symbol)
            if not exchange_symbol:
                self._log.debug(f"Symbol {symbol} not supported on {exchange_name}")
                return None
            
            # Load markets if not already loaded
            if not hasattr(exchange, 'markets') or not exchange.markets:
                await exchange.load_markets()
            
            # Check if symbol exists
            if exchange_symbol not in exchange.markets:
                self._log.debug(f"Symbol {exchange_symbol} not found in {exchange_name} markets")
                return None
            
            # Fetch ticker
            ticker = await exchange.fetch_ticker(exchange_symbol)
            
            # Get last price
            price = ticker.get('last')
            if price and price > 0:
                return float(price)
            
            self._log.warning(f"Invalid price from {exchange_name} for {exchange_symbol}: {price}")
            return None
            
        except Exception as e:
            self._log.error(f"Error fetching from {exchange_name}: {e}")
            return None
        finally:
            # Always close the exchange connection
            if exchange_name in self._exchange_clients:
                try:
                    await self._exchange_clients[exchange_name].close()
                    del self._exchange_clients[exchange_name]
                except:
                    pass
    
    async def _get_exchange_client(self, exchange_name: str):
        """
        Get or create exchange client.
        
        Args:
            exchange_name: Name of the exchange
            
        Returns:
            Exchange client or None if not available
        """
        try:
            # Create new client (don't cache to avoid connection issues)
            if hasattr(ccxt, exchange_name):
                exchange_class = getattr(ccxt, exchange_name)
                exchange = exchange_class({
                    'enableRateLimit': True,
                    'timeout': 10000,  # 10 second timeout
                })
                self._exchange_clients[exchange_name] = exchange
                return exchange
            else:
                self._log.warning(f"Exchange {exchange_name} not available in CCXT")
                return None
                
        except Exception as e:
            self._log.error(f"Failed to create {exchange_name} client: {e}")
            return None
    
    def _map_symbol_for_exchange(self, exchange_name: str, symbol: str) -> Optional[str]:
        """
        Map standard symbol to exchange-specific format.
        
        Args:
            exchange_name: Name of the exchange
            symbol: Standard symbol format
            
        Returns:
            Exchange-specific symbol or None if not supported
        """
        exchange_map = self.EXCHANGE_SYMBOL_MAPS.get(exchange_name, {})
        return exchange_map.get(symbol)
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of symbols supported by CCXT provider."""
        # Collect all unique symbols from all exchange mappings
        symbols = set()
        for exchange_map in self.EXCHANGE_SYMBOL_MAPS.values():
            symbols.update(exchange_map.keys())
        return list(symbols)
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return 'ccxt'
    
    async def health_check(self) -> bool:
        """
        Check if CCXT exchanges are accessible.
        
        Returns:
            True if can fetch a price from any exchange, False otherwise
        """
        try:
            # Test with BTC/USDT as it's widely available
            test_symbol = 'BTC/USDT'
            
            for exchange_name in self.EXCHANGE_PRIORITY[:2]:  # Test first 2 exchanges
                try:
                    price = await self._get_price_from_exchange(exchange_name, test_symbol)
                    if price and price > 0:
                        self._log.debug(f"CCXT health check passed via {exchange_name}")
                        return True
                except:
                    continue
            
            self._log.warning("CCXT health check failed - no exchanges accessible")
            return False
            
        except Exception as e:
            self._log.error(f"CCXT health check failed: {e}")
            return False
    
    async def cleanup(self):
        """Clean up all exchange connections."""
        for exchange_name, exchange in self._exchange_clients.items():
            try:
                await exchange.close()
            except:
                pass
        self._exchange_clients.clear()