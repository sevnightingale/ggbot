"""
Market Data Adapter for Paper Trading

Integrates with Hummingbot API to fetch real-time market data for paper trade execution.
Handles symbol conversion, price caching, and trading rules lookup.
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import aiohttp
import json
from dataclasses import dataclass

from core.common.logger import logger
from core.symbols.standardizer import UniversalSymbolStandardizer


@dataclass
class MarketPrice:
    """Market price data structure"""
    symbol: str
    bid: float
    ask: float
    last: float
    mid: float
    timestamp: float
    
    def __post_init__(self):
        if self.mid is None:
            self.mid = (self.bid + self.ask) / 2
    

@dataclass
class TradingRules:
    """Trading rules data structure"""
    symbol: str
    min_order_size: float
    max_order_size: float
    price_step: float
    size_step: float
    min_notional: float
    

class MarketDataAdapter:
    """
    Adapter for Hummingbot API market data integration.
    
    Provides real-time price data, order book information, and trading rules
    for paper trading execution with proper symbol conversion.
    """
    
    def __init__(self):
        self.hummingbot_url = "http://localhost:8888"
        self.connector = "kucoin"  # Primary exchange for all 141 pairs
        self.symbol_standardizer = UniversalSymbolStandardizer()
        
        # Caching
        self.price_cache: Dict[str, MarketPrice] = {}
        self.rules_cache: Dict[str, TradingRules] = {}
        self.price_cache_ttl = 30  # 30 seconds
        self.rules_cache_ttl = 3600  # 1 hour
        
        # Authentication
        self.username = os.getenv('HBOT_USERNAME', '').strip('"')
        self.password = os.getenv('HBOT_PASSWORD', '').strip('"')
        
        if not self.username or not self.password:
            logger.warning("Hummingbot API credentials not found in environment")
    
    
    def _convert_symbol_to_hummingbot(self, symbol: str) -> str:
        """Convert internal symbol format to Hummingbot format"""
        # Internal: BTC/USDT -> Hummingbot: BTC-USDT
        hb_symbol = self.symbol_standardizer.normalize(symbol, "ccxt", "hummingbot")
        if not hb_symbol:
            logger.warning(f"Failed to convert symbol {symbol} to Hummingbot format")
            # Fallback: simple replacement
            return symbol.replace("/", "-")
        return hb_symbol
    
    def _is_price_cache_valid(self, symbol: str) -> bool:
        """Check if cached price is still valid"""
        if symbol not in self.price_cache:
            return False
        
        cached_price = self.price_cache[symbol]
        age = time.time() - cached_price.timestamp
        return age < self.price_cache_ttl
    
    def _is_rules_cache_valid(self, symbol: str) -> bool:
        """Check if cached trading rules are still valid"""
        if symbol not in self.rules_cache:
            return False
        
        # For simplicity, assume rules don't have timestamps
        # In production, you might want to add timestamp tracking
        return True  # Rules cache doesn't expire for now
    
    async def _call_hummingbot_api(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated API call to Hummingbot"""
        url = f"{self.hummingbot_url}{endpoint}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            # Create BasicAuth explicitly with proper credentials
            auth = aiohttp.BasicAuth(self.username, self.password)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if method.upper() == "POST":
                    async with session.post(url, json=data, auth=auth) as response:
                        response.raise_for_status()
                        return await response.json()
                else:
                    async with session.get(url, auth=auth) as response:
                        response.raise_for_status()
                        return await response.json()
                        
        except aiohttp.ClientError as e:
            logger.error(f"Hummingbot API call failed: {method} {endpoint} - {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Hummingbot API: {e}")
            raise
    
    async def get_current_price(self, symbol: str) -> MarketPrice:
        """
        Get current market price for symbol.
        
        Args:
            symbol: Symbol in internal format (e.g., 'BTC/USDT')
            
        Returns:
            MarketPrice with bid, ask, last, and calculated mid price
        """
        # Check cache first
        if self._is_price_cache_valid(symbol):
            logger.debug(f"Using cached price for {symbol}")
            return self.price_cache[symbol]
        
        # Convert symbol to Hummingbot format
        hb_symbol = self._convert_symbol_to_hummingbot(symbol)
        
        try:
            # Call Hummingbot API for price data
            response = await self._call_hummingbot_api(
                "POST", 
                "/market-data/prices",
                {
                    "connector_name": self.connector,
                    "trading_pairs": [hb_symbol]
                }
            )
            
            # Handle the actual Hummingbot API response format
            if "prices" not in response or hb_symbol not in response["prices"]:
                raise ValueError(f"No price data returned for {hb_symbol}")
            
            # Get the price (Hummingbot API returns single price, not bid/ask)
            price = float(response["prices"][hb_symbol])
            
            # Create MarketPrice object with realistic spread simulation
            # For paper trading, we simulate a small spread around the price
            spread_pct = 0.0005  # 0.05% spread
            spread_amount = price * spread_pct
            
            market_price = MarketPrice(
                symbol=symbol,
                bid=price - spread_amount,
                ask=price + spread_amount,
                last=price,
                mid=None,  # Will be calculated as (bid + ask) / 2
                timestamp=time.time()
            )
            
            # Cache the result
            self.price_cache[symbol] = market_price
            
            logger.debug(f"Fetched price for {symbol}: mid=${market_price.mid:.2f}")
            return market_price
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise

    async def get_current_price_with_fallback(self, symbol: str) -> MarketPrice:
        """
        Get current market price with automatic exchange fallback.

        Tries multiple exchanges in priority order until one succeeds.

        Args:
            symbol: Symbol in internal format (e.g., 'BTC/USDT')

        Returns:
            MarketPrice with bid, ask, last, and calculated mid price

        Raises:
            Exception: If symbol price is not available on any exchange
        """
        exchanges = ["kucoin", "binance", "okx", "gate_io", "ascend_ex"]
        original_connector = self.connector

        logger.debug(f"Attempting to fetch {symbol} price from {len(exchanges)} exchanges")

        for i, exchange in enumerate(exchanges):
            try:
                logger.debug(f"Trying {symbol} price on {exchange} (attempt {i+1}/{len(exchanges)})")

                # Temporarily set connector for this attempt
                self.connector = exchange

                price = await self.get_current_price(symbol)

                if price is not None:
                    if i > 0:  # Only log fallback if not first exchange
                        logger.info(f"✅ Price fallback success: {symbol} retrieved from {exchange}")
                    else:
                        logger.info(f"✅ {symbol} price retrieved from {exchange}")

                    return price

            except Exception as e:
                error_msg = str(e).strip()
                logger.debug(f"❌ {symbol} price failed on {exchange}: {error_msg}")

                # Continue to next exchange
                continue

            finally:
                # Always restore original connector
                self.connector = original_connector

        # All exchanges failed
        self.connector = original_connector  # Ensure it's restored
        raise Exception(f"Price for {symbol} not available on any of {len(exchanges)} exchanges: {exchanges}")

    async def get_order_book(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get order book data for symbol.
        
        Args:
            symbol: Symbol in internal format
            depth: Number of levels to fetch
            
        Returns:
            Order book with bids and asks
        """
        hb_symbol = self._convert_symbol_to_hummingbot(symbol)
        
        try:
            response = await self._call_hummingbot_api(
                "POST",
                "/market-data/order-book",
                {
                    "connector_name": self.connector,
                    "trading_pair": hb_symbol
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            raise
    
    async def get_trading_rules(self, symbol: str) -> TradingRules:
        """
        Get trading rules for symbol (min order size, tick size, etc.)
        
        Args:
            symbol: Symbol in internal format
            
        Returns:
            TradingRules with constraints and specifications
        """
        # Check cache first
        if self._is_rules_cache_valid(symbol):
            logger.debug(f"Using cached trading rules for {symbol}")
            return self.rules_cache[symbol]
        
        hb_symbol = self._convert_symbol_to_hummingbot(symbol)
        
        try:
            # Call Hummingbot API for trading rules
            response = await self._call_hummingbot_api(
                "GET",
                f"/connectors/{self.connector}/trading-rules?trading_pairs={hb_symbol}"
            )
            
            if hb_symbol not in response:
                raise ValueError(f"No trading rules returned for {hb_symbol}")
            
            rules_data = response[hb_symbol]
            
            # Create TradingRules object
            trading_rules = TradingRules(
                symbol=symbol,
                min_order_size=float(rules_data.get("min_order_size", 0.00001)),
                max_order_size=float(rules_data.get("max_order_size", 1000000)),
                price_step=float(rules_data.get("price_step", 0.01)),
                size_step=float(rules_data.get("size_step", 0.00001)),
                min_notional=float(rules_data.get("min_notional", 1.0))
            )
            
            # Cache the result
            self.rules_cache[symbol] = trading_rules
            
            logger.debug(f"Fetched trading rules for {symbol}: min_size={trading_rules.min_order_size}")
            return trading_rules
            
        except Exception as e:
            logger.error(f"Failed to get trading rules for {symbol}: {e}")
            raise
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, MarketPrice]:
        """
        Get prices for multiple symbols efficiently.
        
        Args:
            symbols: List of symbols in internal format
            
        Returns:
            Dictionary mapping symbols to MarketPrice objects
        """
        results = {}
        
        # Separate cached and non-cached symbols
        cached_symbols = [s for s in symbols if self._is_price_cache_valid(s)]
        fetch_symbols = [s for s in symbols if not self._is_price_cache_valid(s)]
        
        # Use cached data
        for symbol in cached_symbols:
            results[symbol] = self.price_cache[symbol]
        
        # Fetch non-cached symbols
        if fetch_symbols:
            # Convert to Hummingbot format
            hb_symbols = [self._convert_symbol_to_hummingbot(s) for s in fetch_symbols]
            
            try:
                response = await self._call_hummingbot_api(
                    "POST",
                    "/market-data/prices", 
                    {
                        "connector_name": self.connector,
                        "trading_pairs": hb_symbols
                    }
                )
                
                # Process results
                for i, symbol in enumerate(fetch_symbols):
                    hb_symbol = hb_symbols[i]
                    if "prices" in response and hb_symbol in response["prices"]:
                        price = float(response["prices"][hb_symbol])
                        
                        # Simulate realistic spread
                        spread_pct = 0.0005  # 0.05% spread
                        spread_amount = price * spread_pct
                        
                        market_price = MarketPrice(
                            symbol=symbol,
                            bid=price - spread_amount,
                            ask=price + spread_amount,
                            last=price,
                            mid=None,
                            timestamp=time.time()
                        )
                        
                        # Cache and store
                        self.price_cache[symbol] = market_price
                        results[symbol] = market_price
                    else:
                        logger.warning(f"No price data returned for {symbol} ({hb_symbol})")
                        
            except Exception as e:
                logger.error(f"Failed to fetch multiple prices: {e}")
                # Continue with what we have
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of market data service.
        
        Returns:
            Health status and diagnostic information
        """
        health_status = {
            "service": "market_data_adapter",
            "status": "unknown",
            "hummingbot_api": "unknown",
            "connector": self.connector,
            "cache_stats": {
                "price_cache_size": len(self.price_cache),
                "rules_cache_size": len(self.rules_cache)
            },
            "errors": []
        }
        
        try:
            # Test basic API connectivity
            connectors = await self._call_hummingbot_api("GET", "/connectors/")
            
            if self.connector in connectors:
                health_status["hummingbot_api"] = "healthy"
            else:
                health_status["hummingbot_api"] = "connector_not_found"
                health_status["errors"].append(f"Connector {self.connector} not available")
            
            # Test price fetching with a common pair
            try:
                await self.get_current_price("BTC/USDT")
                health_status["status"] = "healthy"
            except Exception as e:
                health_status["status"] = "degraded"
                health_status["errors"].append(f"Price fetch test failed: {str(e)}")
                
        except Exception as e:
            health_status["hummingbot_api"] = "failed"
            health_status["status"] = "failed"
            health_status["errors"].append(f"API connectivity failed: {str(e)}")
        
        return health_status
    
    def clear_cache(self):
        """Clear all cached data"""
        self.price_cache.clear()
        self.rules_cache.clear()
        logger.info("Market data cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "price_cache_entries": len(self.price_cache),
            "rules_cache_entries": len(self.rules_cache),
            "price_cache_ttl": self.price_cache_ttl,
            "rules_cache_ttl": self.rules_cache_ttl
        }


# Convenience functions for common operations
async def get_price(symbol: str) -> MarketPrice:
    """Quick price lookup"""
    adapter = MarketDataAdapter()
    return await adapter.get_current_price(symbol)


async def get_mid_price(symbol: str) -> float:
    """Get just the mid price for a symbol"""
    price = await get_price(symbol)
    return price.mid


async def validate_symbol(symbol: str) -> bool:
    """Check if symbol is supported by the exchange"""
    try:
        adapter = MarketDataAdapter()
        await adapter.get_trading_rules(symbol)
        return True
    except Exception:
        return False