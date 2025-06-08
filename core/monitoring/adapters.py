"""
Exchange-specific adapters for normalizing data formats.

Each exchange has its own quirks in how it returns balance and position data.
These adapters convert exchange-specific formats to a standardized format
that can be stored consistently in the database.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
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
    
    def normalize_position_for_lifecycle(self, raw_position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert exchange-specific position format to enhanced dictionary for trade lifecycle.
        
        Args:
            raw_position: Raw position data from exchange
            
        Returns:
            Enhanced position dictionary or None if position has zero size
        """
        # Default implementation - subclasses should override
        raise NotImplementedError("Subclasses must implement normalize_position_for_lifecycle")
    
    async def get_positions_for_lifecycle(self, exchange_client) -> List[Dict[str, Any]]:
        """
        Get all active positions from the exchange for trade lifecycle.
        
        This is a helper method that uses the monitoring service's exchange client.
        
        Args:
            exchange_client: CCXT exchange client from monitoring service
            
        Returns:
            List of enhanced position dictionaries
        """
        raw_positions = await exchange_client.fetch_positions()
        normalized_positions = []
        
        for raw_pos in raw_positions:
            normalized = self.normalize_position_for_lifecycle(raw_pos)
            if normalized:  # Skip None (e.g., 0-contract positions)
                normalized_positions.append(normalized)
        
        return normalized_positions
    
    def get_position_key(self, position: Dict[str, Any]) -> Tuple[str, ...]:
        """
        Generate position key for database uniqueness.
        
        Args:
            position: Enhanced position dictionary
            
        Returns:
            Tuple representing unique position key
        """
        # Default implementation - subclasses should override
        raise NotImplementedError("Subclasses must implement get_position_key")
    
    @abstractmethod
    def get_symbol_format(self, symbol: str) -> str:
        """Convert standard symbol format to exchange-specific format."""
        pass
    
    @abstractmethod
    def get_exchange_config(self) -> Dict[str, Any]:
        """Return exchange-specific configuration."""
        pass
    
    def normalize_open_orders(self, raw_orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert exchange-specific open orders to standardized format for TP/SL tracking.
        
        Args:
            raw_orders: List of raw order data from exchange
            
        Returns:
            List of normalized order dictionaries with risk classification
        """
        normalized_orders = []
        
        for raw_order in raw_orders:
            normalized = self.normalize_single_order(raw_order)
            if normalized:
                normalized_orders.append(normalized)
        
        return normalized_orders
    
    @abstractmethod
    def normalize_single_order(self, raw_order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a single exchange-specific order to standardized format.
        
        Returns:
            {
                "exchange_order_id": str,
                "symbol": str,  # Standardized symbol
                "side": str,    # "buy" or "sell"
                "order_type": str,  # "market", "limit", "stop"
                "price": float,
                "trigger_price": float,  # For stop orders
                "size": float,
                "status": str,  # "open", "filled", "canceled"
                "is_risk_order": bool,  # True for reduce-only orders
                "risk_type": str,  # "TP", "SL", or None
                "timestamp": int  # Unix timestamp in milliseconds
            }
        """
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
    
    def normalize_position_for_lifecycle(self, raw_position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize BitMEX position data to enhanced dictionary for trade lifecycle."""
        # Include ALL positions for lifecycle (including 0-contract positions)
        # The lifecycle manager needs to see 0-contract positions to close database trades
        contracts = raw_position.get('contracts', 0)
        
        # Standardize symbol (remove :BTC suffix if present)
        symbol = raw_position.get('symbol', '')
        if ':' in symbol:
            symbol = symbol.split(':')[0]
        
        return {
            "exchange": "bitmex",
            "account_id": "main",  # BitMEX doesn't have sub-accounts in this context
            "symbol": symbol,
            "side": None,  # BitMEX uses net positioning
            "size_contracts": float(contracts) if contracts is not None else 0,
            "mark_price": float(raw_position.get('markPrice', 0)) if raw_position.get('markPrice') is not None else 0,
            "entry_price": float(raw_position.get('entryPrice', 0)) if raw_position.get('entryPrice') is not None else 0,
            "unrealized_pnl": float(raw_position.get('unrealizedPnl', 0)) if raw_position.get('unrealizedPnl') is not None else 0,
            "leverage": float(raw_position.get('leverage', 1)) if raw_position.get('leverage') else None,
            "liquidation_price": float(raw_position.get('liquidationPrice', 0)) if raw_position.get('liquidationPrice') else None,
            "margin_mode": raw_position.get('marginMode', 'cross'),
            "timestamp": datetime.now().timestamp() * 1000  # Unix timestamp in milliseconds
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
    
    
    def get_position_key(self, position: Dict[str, Any]) -> Tuple[str, ...]:
        """BitMEX uses net positioning - no side in key."""
        return (position["account_id"], position["exchange"], position["symbol"])
    
    def normalize_single_order(self, raw_order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a single BitMEX order for risk order tracking."""
        # Skip orders that don't have an ID
        order_id = raw_order.get('id')
        if not order_id:
            return None
        
        # Extract basic order information
        symbol = raw_order.get('symbol', '')
        
        # Standardize symbol (remove :BTC suffix if present)
        if ':' in symbol:
            symbol = symbol.split(':')[0]
        
        # Get order details
        order_type = raw_order.get('type', '').lower()
        side = raw_order.get('side', '').lower()
        price = raw_order.get('price')
        amount = raw_order.get('amount', 0)
        status = raw_order.get('status', '').lower()
        timestamp = raw_order.get('timestamp') or raw_order.get('datetime')
        
        # Extract trigger price for stop orders
        trigger_price = (
            raw_order.get('triggerPrice') or 
            raw_order.get('stopPrice') or 
            raw_order.get('info', {}).get('stopPx')
        )
        
        # Check if this is a reduce-only order (TP/SL)
        is_reduce_only = self._is_reduce_only_order(raw_order)
        
        # Determine risk type if it's a reduce-only order
        risk_type = None
        if is_reduce_only:
            risk_type = self._classify_risk_order_type(raw_order, price, trigger_price)
        
        return {
            "exchange_order_id": str(order_id),
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "price": float(price) if price is not None else None,
            "trigger_price": float(trigger_price) if trigger_price is not None else None,
            "size": float(amount) if amount is not None else 0,
            "status": status,
            "is_risk_order": is_reduce_only,
            "risk_type": risk_type,
            "timestamp": timestamp if isinstance(timestamp, (int, float)) else datetime.now().timestamp() * 1000
        }
    
    def _is_reduce_only_order(self, raw_order: Dict[str, Any]) -> bool:
        """Check if an order is reduce-only (TP/SL order)."""
        # Check direct reduceOnly field
        if raw_order.get('reduceOnly') is True:
            return True
        
        # Check in info object for BitMEX-specific field
        info = raw_order.get('info', {})
        if info.get('reduceOnly') is True:
            return True
        
        # Check execInst for "Close" instruction
        exec_inst = info.get('execInst', '')
        if 'Close' in exec_inst:
            return True
        
        # Check if it's a stop order with trigger price (likely TP/SL)
        order_type = raw_order.get('type', '').lower()
        has_trigger = (
            raw_order.get('triggerPrice') is not None or 
            raw_order.get('stopPrice') is not None or
            info.get('stopPx') is not None
        )
        
        if order_type == 'stop' and has_trigger:
            return True
        
        return False
    
    def _classify_risk_order_type(self, raw_order: Dict[str, Any], price: Optional[float], trigger_price: Optional[float]) -> Optional[str]:
        """Classify a reduce-only order as TP or SL."""
        # If we have explicit TP/SL fields
        if raw_order.get('takeProfitPrice') is not None:
            return 'TP'
        if raw_order.get('stopLossPrice') is not None:
            return 'SL'
        
        # For BitMEX, we need to analyze the order characteristics
        order_type = raw_order.get('type', '').lower()
        
        # Stop orders are typically stop-loss
        if order_type == 'stop':
            return 'SL'
        
        # Check for BitMEX-specific indicators
        info = raw_order.get('info', {})
        
        # Orders with stopPx (stop price) are stop-loss orders
        if info.get('stopPx') is not None:
            return 'SL'
        
        # Orders with execInst "Close" and trigger prices are typically stop-loss
        exec_inst = info.get('execInst', '')
        if 'Close' in exec_inst and trigger_price is not None:
            return 'SL'
        
        # Limit orders without stop characteristics are typically take-profit
        if order_type == 'limit':
            return 'TP'
        
        # Default to SL for unknown reduce-only orders
        return 'SL'


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
    
    def normalize_position_for_lifecycle(self, raw_position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize Binance position data to enhanced dictionary for trade lifecycle."""
        # Binance only returns active positions
        contracts = raw_position.get('contracts', 0)
        if contracts == 0:
            return None
        
        return {
            "exchange": "binance",
            "account_id": "main",
            "symbol": raw_position.get('symbol', ''),
            "side": raw_position.get('side'),  # Binance supports hedge mode
            "size_contracts": float(contracts) if contracts is not None else 0,
            "mark_price": float(raw_position.get('markPrice', 0)) if raw_position.get('markPrice') is not None else 0,
            "entry_price": float(raw_position.get('entryPrice', 0)) if raw_position.get('entryPrice') is not None else 0,
            "unrealized_pnl": float(raw_position.get('unrealizedPnl', 0)) if raw_position.get('unrealizedPnl') is not None else 0,
            "leverage": float(raw_position.get('leverage', 1)) if raw_position.get('leverage') else None,
            "liquidation_price": float(raw_position.get('liquidationPrice', 0)) if raw_position.get('liquidationPrice') else None,
            "margin_mode": raw_position.get('marginMode', 'cross'),
            "timestamp": datetime.now().timestamp() * 1000  # Unix timestamp in milliseconds
        }
    
    def get_symbol_format(self, symbol: str) -> str:
        """Convert standard symbol to Binance format."""
        # Binance uses BTCUSDT format
        return symbol.replace('/', '')
    
    
    def get_position_key(self, position: Dict[str, Any]) -> Tuple[str, ...]:
        """Binance supports hedge mode - side included in key when present."""
        if position.get("side"):
            return (position["account_id"], position["exchange"], position["symbol"], position["side"])
        else:
            return (position["account_id"], position["exchange"], position["symbol"])
    
    def normalize_single_order(self, raw_order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a single Binance order for risk order tracking."""
        # Skip orders that don't have an ID
        order_id = raw_order.get('id')
        if not order_id:
            return None
        
        # Extract basic order information
        symbol = raw_order.get('symbol', '')
        order_type = raw_order.get('type', '').lower()
        side = raw_order.get('side', '').lower()
        price = raw_order.get('price')
        amount = raw_order.get('amount', 0)
        status = raw_order.get('status', '').lower()
        timestamp = raw_order.get('timestamp') or raw_order.get('datetime')
        
        # Extract trigger price for stop orders
        trigger_price = (
            raw_order.get('triggerPrice') or 
            raw_order.get('stopPrice')
        )
        
        # Check if this is a reduce-only order (TP/SL)
        is_reduce_only = self._is_binance_reduce_only_order(raw_order)
        
        # Determine risk type if it's a reduce-only order
        risk_type = None
        if is_reduce_only:
            risk_type = self._classify_binance_risk_order_type(raw_order, price, trigger_price)
        
        return {
            "exchange_order_id": str(order_id),
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "price": float(price) if price is not None else None,
            "trigger_price": float(trigger_price) if trigger_price is not None else None,
            "size": float(amount) if amount is not None else 0,
            "status": status,
            "is_risk_order": is_reduce_only,
            "risk_type": risk_type,
            "timestamp": timestamp if isinstance(timestamp, (int, float)) else datetime.now().timestamp() * 1000
        }
    
    def _is_binance_reduce_only_order(self, raw_order: Dict[str, Any]) -> bool:
        """Check if a Binance order is reduce-only (TP/SL order)."""
        # Check direct reduceOnly field
        if raw_order.get('reduceOnly') is True:
            return True
        
        # Check in info object for Binance-specific field
        info = raw_order.get('info', {})
        if info.get('reduceOnly') is True:
            return True
        
        # Binance uses specific order types for TP/SL
        order_type = raw_order.get('type', '').lower()
        if order_type in ['take_profit', 'take_profit_market', 'stop', 'stop_market']:
            return True
        
        return False
    
    def _classify_binance_risk_order_type(self, raw_order: Dict[str, Any], price: Optional[float], trigger_price: Optional[float]) -> Optional[str]:
        """Classify a Binance reduce-only order as TP or SL."""
        # If we have explicit TP/SL fields
        if raw_order.get('takeProfitPrice') is not None:
            return 'TP'
        if raw_order.get('stopLossPrice') is not None:
            return 'SL'
        
        # Check order type
        order_type = raw_order.get('type', '').lower()
        
        if 'take_profit' in order_type:
            return 'TP'
        elif 'stop' in order_type:
            return 'SL'
        
        # Default classification
        return 'SL'


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