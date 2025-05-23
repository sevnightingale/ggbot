"""
Exchange-specific adapters for normalizing data formats.

Each exchange has its own quirks in how it returns balance and position data.
These adapters convert exchange-specific formats to a standardized format
that can be stored consistently in the database.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class ExchangeAdapter(ABC):
    """Abstract base class for exchange-specific data normalization."""
    
    @abstractmethod
    def normalize_balance(self, raw_balance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert exchange-specific balance format to standard format.
        
        Returns:
            {
                "total_btc": float,
                "available_btc": float,
                "used_btc": float,
                "total_usd_value": float (if available),
                "currencies": {
                    "BTC": {"total": float, "free": float, "used": float},
                    "USDT": {"total": float, "free": float, "used": float},
                    ...
                }
            }
        """
        pass
    
    @abstractmethod
    def normalize_position(self, raw_position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert exchange-specific position format to standard format.
        
        Returns:
            {
                "symbol": str,  # Standardized symbol
                "side": str,    # "long" or "short"
                "contracts": float,
                "size": float,  # Position size in base currency
                "entry_price": float,
                "mark_price": float,
                "liquidation_price": float,
                "unrealized_pnl": float,
                "unrealized_pnl_pct": float,
                "margin_mode": str,  # "cross" or "isolated"
                "leverage": float
            }
        """
        pass
    
    @abstractmethod
    def get_symbol_format(self, symbol: str) -> str:
        """Convert standard symbol format to exchange-specific format."""
        pass
    
    @abstractmethod
    def get_exchange_config(self) -> Dict[str, Any]:
        """Return exchange-specific configuration."""
        pass


class BitMEXAdapter(ExchangeAdapter):
    """BitMEX-specific data adapter."""
    
    def get_exchange_config(self) -> Dict[str, Any]:
        return {
            "btc_key": "XBt",
            "btc_divisor": 100000000,  # Satoshis to BTC
            "has_testnet": True,
            "position_always_returned": True,
            "unrealized_pnl_type": "string",
            "margin_currency": "BTC"
        }
    
    def normalize_balance(self, raw_balance: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize BitMEX balance data."""
        result = {
            "total_btc": 0.0,
            "available_btc": 0.0,
            "used_btc": 0.0,
            "total_usd_value": None,
            "currencies": {}
        }
        
        # BitMEX stores detailed info in the 'info' array
        if isinstance(raw_balance.get('info'), list):
            for currency_info in raw_balance['info']:
                currency = currency_info.get('currency', '')
                
                if currency == 'XBt':
                    # Convert satoshis to BTC
                    divisor = 100000000
                    result['total_btc'] = currency_info.get('walletBalance', 0) / divisor
                    result['available_btc'] = currency_info.get('availableMargin', 0) / divisor
                    result['used_btc'] = (currency_info.get('walletBalance', 0) - 
                                         currency_info.get('availableMargin', 0)) / divisor
                    
                    result['currencies']['BTC'] = {
                        'total': result['total_btc'],
                        'free': result['available_btc'],
                        'used': result['used_btc'],
                        'unrealized_pnl': currency_info.get('unrealisedPnl', 0) / divisor,
                        'margin_balance': currency_info.get('marginBalance', 0) / divisor,
                        'margin_used_pct': currency_info.get('marginUsedPcnt', 0)
                    }
                
                elif currency in ['USDt', 'USDT']:
                    # USDT values are in micro-USDT (1e-6)
                    divisor = 1000000
                    result['currencies']['USDT'] = {
                        'total': currency_info.get('walletBalance', 0) / divisor,
                        'free': currency_info.get('availableMargin', 0) / divisor,
                        'used': (currency_info.get('walletBalance', 0) - 
                                currency_info.get('availableMargin', 0)) / divisor
                    }
                    result['total_usd_value'] = result['currencies']['USDT']['total']
        
        # Also check the standard balance format
        if 'BTC' in raw_balance:
            btc_balance = raw_balance['BTC']
            # Sometimes BitMEX returns negative 'used' values
            result['currencies']['BTC'].update({
                'free': btc_balance.get('free', 0),
                'used': abs(btc_balance.get('used', 0)),
                'total': btc_balance.get('total', 0) or btc_balance.get('free', 0)
            })
        
        return result
    
    def normalize_position(self, raw_position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize BitMEX position data."""
        # Skip positions with 0 contracts (BitMEX returns these)
        contracts = raw_position.get('contracts', 0)
        if contracts == 0:
            return None
        
        # Convert unrealized PNL from string to float if needed
        unrealized_pnl = raw_position.get('unrealizedPnl', 0)
        if isinstance(unrealized_pnl, str):
            try:
                unrealized_pnl = float(unrealized_pnl)
            except (ValueError, TypeError):
                unrealized_pnl = 0.0
        
        # Standardize symbol (remove :BTC suffix)
        symbol = raw_position.get('symbol', '')
        if ':' in symbol:
            symbol = symbol.split(':')[0]
        
        return {
            "symbol": symbol,
            "side": raw_position.get('side', 'unknown'),
            "contracts": contracts,
            "size": raw_position.get('notional', 0),  # USD value
            "entry_price": raw_position.get('entryPrice'),
            "mark_price": raw_position.get('markPrice'),
            "liquidation_price": raw_position.get('liquidationPrice'),
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": raw_position.get('percentage', 0),
            "margin_mode": raw_position.get('marginMode', 'cross'),
            "leverage": raw_position.get('leverage', 1),
            "timestamp": raw_position.get('timestamp', datetime.now().timestamp() * 1000)
        }
    
    def get_symbol_format(self, symbol: str) -> str:
        """Convert standard symbol to BitMEX format."""
        # BitMEX uses BTC/USD:BTC format for perpetuals
        if symbol == 'BTC/USD':
            return 'BTC/USD:BTC'
        elif symbol == 'ETH/USD':
            return 'ETH/USD:BTC'
        # Add more mappings as needed
        return symbol


class BinanceAdapter(ExchangeAdapter):
    """Binance-specific data adapter."""
    
    def get_exchange_config(self) -> Dict[str, Any]:
        return {
            "btc_key": "BTC",
            "btc_divisor": 1,  # Already in BTC
            "has_testnet": True,
            "position_always_returned": False,
            "unrealized_pnl_type": "float",
            "margin_currency": "USDT"
        }
    
    def normalize_balance(self, raw_balance: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Binance balance data."""
        result = {
            "total_btc": 0.0,
            "available_btc": 0.0,
            "used_btc": 0.0,
            "total_usd_value": None,
            "currencies": {}
        }
        
        # Binance uses direct currency keys
        if 'BTC' in raw_balance:
            btc = raw_balance['BTC']
            result['total_btc'] = btc.get('total', 0)
            result['available_btc'] = btc.get('free', 0)
            result['used_btc'] = btc.get('used', 0)
            
            result['currencies']['BTC'] = {
                'total': result['total_btc'],
                'free': result['available_btc'],
                'used': result['used_btc']
            }
        
        if 'USDT' in raw_balance:
            usdt = raw_balance['USDT']
            result['currencies']['USDT'] = {
                'total': usdt.get('total', 0),
                'free': usdt.get('free', 0),
                'used': usdt.get('used', 0)
            }
            result['total_usd_value'] = result['currencies']['USDT']['total']
        
        return result
    
    def normalize_position(self, raw_position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize Binance position data."""
        # Binance only returns active positions
        contracts = raw_position.get('contracts', 0)
        if contracts == 0:
            return None
        
        return {
            "symbol": raw_position.get('symbol', ''),
            "side": raw_position.get('side', 'unknown'),
            "contracts": contracts,
            "size": raw_position.get('notional', 0),
            "entry_price": raw_position.get('entryPrice'),
            "mark_price": raw_position.get('markPrice'),
            "liquidation_price": raw_position.get('liquidationPrice'),
            "unrealized_pnl": raw_position.get('unrealizedPnl', 0),
            "unrealized_pnl_pct": raw_position.get('percentage', 0),
            "margin_mode": raw_position.get('marginMode', 'cross'),
            "leverage": raw_position.get('leverage', 1),
            "timestamp": raw_position.get('timestamp', datetime.now().timestamp() * 1000)
        }
    
    def get_symbol_format(self, symbol: str) -> str:
        """Convert standard symbol to Binance format."""
        # Binance uses BTCUSDT format
        return symbol.replace('/', '')


# Factory function
def create_exchange_adapter(exchange_name: str) -> ExchangeAdapter:
    """Create appropriate adapter for the given exchange."""
    adapters = {
        'bitmex': BitMEXAdapter,
        'binance': BinanceAdapter,
        # Add more exchanges as needed
    }
    
    adapter_class = adapters.get(exchange_name.lower())
    if not adapter_class:
        raise ValueError(f"No adapter available for exchange: {exchange_name}")
    
    return adapter_class()