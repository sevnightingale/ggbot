"""
Price Service for the Decision Module.

This service orchestrates multiple price providers to fetch reliable, 
current market prices with validation and consensus logic.
"""

import asyncio
from decimal import Decimal
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone

from core.common.logger import logger
from decision.providers.yfinance_provider import YFinancePriceProvider
from decision.providers.ccxt_provider import CCXTPriceProvider


class PriceService:
    """
    Service that orchestrates multiple price providers for reliable pricing.
    
    This service:
    1. Fetches prices from multiple sources simultaneously
    2. Validates price consistency between sources
    3. Returns consensus price or fails if sources disagree significantly
    4. Provides no fallback values - real data or error
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the price service with multiple providers.
        
        Args:
            config: Optional configuration for price tolerance and providers
        """
        self.config = config or {}
        
        # Price validation settings
        self.price_tolerance = self.config.get('price_tolerance', 0.05)  # 5% max difference
        self.timeout_seconds = self.config.get('timeout_seconds', 10)    # 10 second timeout
        self.allow_single_source = self.config.get('allow_single_source', True)   # Fallback to single source (default enabled)
        
        # Initialize providers
        self.yfinance_provider = YFinancePriceProvider()
        self.ccxt_provider = CCXTPriceProvider()
        
        self._log = logger.bind(service="price_service")
        
        self._log.info(
            f"Initialized PriceService with {self.price_tolerance*100:.1f}% tolerance, "
            f"{self.timeout_seconds}s timeout"
        )
    
    async def get_current_price(self, symbol: str) -> Union[float, Decimal]:
        """
        Get current market price with dual-source validation.
        
        Args:
            symbol: Standard trading symbol (e.g., 'BTC/USDT', 'ETH/USD')
            
        Returns:
            Union[float, Decimal]: Consensus current market price
            
        Raises:
            ValueError: If either source fails or prices disagree significantly
            TimeoutError: If price fetching times out
        """
        self._log.info(f"Fetching current price for {symbol}")
        
        try:
            # Fetch from both sources simultaneously with timeout
            yf_task = asyncio.create_task(
                self.yfinance_provider.get_current_price(symbol)
            )
            ccxt_task = asyncio.create_task(
                self.ccxt_provider.get_current_price(symbol)
            )
            
            # Wait for both with timeout
            yf_price, ccxt_price = await asyncio.wait_for(
                asyncio.gather(yf_task, ccxt_task, return_exceptions=True),
                timeout=self.timeout_seconds
            )
            
            # Check for exceptions
            if isinstance(yf_price, Exception):
                raise ValueError(f"YFinance provider failed: {yf_price}")
            if isinstance(ccxt_price, Exception):
                raise ValueError(f"CCXT provider failed: {ccxt_price}")
            
            # Handle single source fallback if enabled
            if self.allow_single_source:
                # If only one source succeeded, use it
                if yf_price and not ccxt_price:
                    self._log.warning(f"Using YFinance only for {symbol} (CCXT failed)")
                    return yf_price  # Keep original type (float from YFinance)
                elif ccxt_price and not yf_price:
                    self._log.warning(f"Using CCXT only for {symbol} (YFinance failed)")
                    return ccxt_price  # Keep original type (Decimal from CCXT)
            
            # Check for None results (strict dual-source mode)
            if yf_price is None:
                raise ValueError(f"YFinance provider returned None for {symbol}")
            if ccxt_price is None:
                raise ValueError(f"CCXT provider returned None for {symbol}")
            
            # Validate prices are reasonable (> 0)
            if yf_price <= 0:
                raise ValueError(f"YFinance returned invalid price: {yf_price}")
            if ccxt_price <= 0:
                raise ValueError(f"CCXT returned invalid price: {ccxt_price}")
            
            # Convert both to Decimal for precise calculations
            yf_decimal = Decimal(str(yf_price)) if not isinstance(yf_price, Decimal) else yf_price
            ccxt_decimal = Decimal(str(ccxt_price)) if not isinstance(ccxt_price, Decimal) else ccxt_price
            
            # Calculate price difference percentage using Decimals
            price_diff = abs(yf_decimal - ccxt_decimal)
            min_price = min(yf_decimal, ccxt_decimal)
            price_diff_pct = float(price_diff / min_price)
            
            # Check if prices agree within tolerance
            if price_diff_pct > self.price_tolerance:
                raise ValueError(
                    f"Price mismatch for {symbol}: "
                    f"YFinance=${yf_price}, CCXT=${ccxt_price} "
                    f"({price_diff_pct*100:.1f}% difference, max allowed: {self.price_tolerance*100:.1f}%)"
                )
            
            # Calculate consensus price (average) - prefer Decimal precision
            consensus_price = (yf_decimal + ccxt_decimal) / Decimal('2')
            
            self._log.info(
                f"Price consensus for {symbol}: ${consensus_price} "
                f"(YF: ${yf_price}, CCXT: ${ccxt_price}, "
                f"diff: {price_diff_pct*100:.1f}%)"
            )
            
            return consensus_price
            
        except asyncio.TimeoutError:
            error_msg = f"Price fetch timeout for {symbol} after {self.timeout_seconds}s"
            self._log.error(error_msg)
            raise TimeoutError(error_msg)
        
        except Exception as e:
            self._log.error(f"Failed to get price for {symbol}: {e}")
            raise
        
        finally:
            # Clean up CCXT connections
            await self.ccxt_provider.cleanup()
    
    async def get_price_breakdown(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed price breakdown from all sources for debugging.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dict with prices from each source and metadata
        """
        self._log.debug(f"Getting price breakdown for {symbol}")
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'providers': {},
            'consensus': None,
            'validation': {}
        }
        
        try:
            # Fetch from both sources
            yf_task = asyncio.create_task(
                self.yfinance_provider.get_current_price(symbol)
            )
            ccxt_task = asyncio.create_task(
                self.ccxt_provider.get_current_price(symbol)
            )
            
            yf_price, ccxt_price = await asyncio.gather(
                yf_task, ccxt_task, return_exceptions=True
            )
            
            # Record results from each provider
            result['providers']['yfinance'] = {
                'price': yf_price if not isinstance(yf_price, Exception) else None,
                'error': str(yf_price) if isinstance(yf_price, Exception) else None,
                'status': 'success' if not isinstance(yf_price, Exception) and yf_price else 'failed'
            }
            
            result['providers']['ccxt'] = {
                'price': ccxt_price if not isinstance(ccxt_price, Exception) else None,
                'error': str(ccxt_price) if isinstance(ccxt_price, Exception) else None,
                'status': 'success' if not isinstance(ccxt_price, Exception) and ccxt_price else 'failed'
            }
            
            # Calculate consensus if both succeeded
            if (not isinstance(yf_price, Exception) and yf_price and 
                not isinstance(ccxt_price, Exception) and ccxt_price):
                
                # Convert to Decimal for precise calculations
                yf_decimal = Decimal(str(yf_price)) if not isinstance(yf_price, Decimal) else yf_price
                ccxt_decimal = Decimal(str(ccxt_price)) if not isinstance(ccxt_price, Decimal) else ccxt_price
                
                price_diff = abs(yf_decimal - ccxt_decimal)
                min_price = min(yf_decimal, ccxt_decimal)
                price_diff_pct = float(price_diff / min_price)
                consensus_price = (yf_decimal + ccxt_decimal) / Decimal('2')
                
                result['consensus'] = consensus_price
                result['validation'] = {
                    'price_difference_pct': price_diff_pct * 100,
                    'tolerance_pct': self.price_tolerance * 100,
                    'within_tolerance': price_diff_pct <= self.price_tolerance,
                    'status': 'valid' if price_diff_pct <= self.price_tolerance else 'invalid'
                }
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
        
        finally:
            await self.ccxt_provider.cleanup()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all price providers.
        
        Returns:
            Dict with health status of each provider
        """
        self._log.debug("Running price service health check")
        
        result = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'providers': {},
            'overall_status': 'unknown'
        }
        
        try:
            # Check YFinance health
            yf_healthy = await self.yfinance_provider.health_check()
            result['providers']['yfinance'] = {
                'status': 'healthy' if yf_healthy else 'unhealthy',
                'provider_name': self.yfinance_provider.get_provider_name()
            }
            
            # Check CCXT health
            ccxt_healthy = await self.ccxt_provider.health_check()
            result['providers']['ccxt'] = {
                'status': 'healthy' if ccxt_healthy else 'unhealthy',
                'provider_name': self.ccxt_provider.get_provider_name()
            }
            
            # Overall status
            if yf_healthy and ccxt_healthy:
                result['overall_status'] = 'healthy'
            elif yf_healthy or ccxt_healthy:
                result['overall_status'] = 'degraded'
            else:
                result['overall_status'] = 'unhealthy'
            
            self._log.info(f"Price service health check: {result['overall_status']}")
            return result
            
        except Exception as e:
            result['error'] = str(e)
            result['overall_status'] = 'error'
            self._log.error(f"Price service health check failed: {e}")
            return result
        
        finally:
            await self.ccxt_provider.cleanup()
    
    def get_supported_symbols(self) -> List[str]:
        """
        Get list of symbols supported by all providers.
        
        Returns:
            List of symbols supported by both YFinance and CCXT
        """
        yf_symbols = set(self.yfinance_provider.get_supported_symbols())
        ccxt_symbols = set(self.ccxt_provider.get_supported_symbols())
        
        # Return intersection (symbols supported by both)
        supported = list(yf_symbols.intersection(ccxt_symbols))
        supported.sort()
        
        self._log.debug(f"Supported symbols: {len(supported)} symbols")
        return supported