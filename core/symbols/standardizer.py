"""
Universal Symbol Standardizer for ggbots Platform

This module provides centralized symbol conversion between different trading systems:
- ggShot: BTCUSDT (no separator)
- CCXT: BTC/USDT (slash separator) 
- Hummingbot: BTC-USDT (dash separator)
- Platform: BTC-USDT (standardized format)

Usage:
    from core.symbols import UniversalSymbolStandardizer
    
    standardizer = UniversalSymbolStandardizer()
    
    # Convert ggShot signal to Hummingbot format
    hb_symbol = standardizer.from_ggshot("BTCUSDT")  # → "BTC-USDT"
    
    # Convert platform format to CCXT format
    ccxt_symbol = standardizer.to_ccxt("BTC-USDT")  # → "BTC/USDT"
    
    # Validate symbol support
    is_valid = standardizer.is_supported("BTC-USDT")  # → True
"""

from typing import Dict, List, Optional, Union
from .registry import SYMBOL_REGISTRY, find_symbol_by_format, get_symbol_data


class UniversalSymbolStandardizer:
    """Universal symbol conversion service for all ggbots platform components"""
    
    def __init__(self):
        self.registry = SYMBOL_REGISTRY
    
    def normalize(self, symbol: str, source_format: str, target_format: str) -> Optional[str]:
        """
        Convert symbol between any supported formats
        
        Args:
            symbol: Input symbol in source format
            source_format: Source format (ggshot, ccxt, hummingbot, platform)
            target_format: Target format (ggshot, ccxt, hummingbot, platform)
            
        Returns:
            Converted symbol in target format, or None if not found
        """
        # Find symbol key by source format
        symbol_key = find_symbol_by_format(symbol, source_format)
        if not symbol_key:
            return None
            
        # Get symbol data and return target format
        symbol_data = get_symbol_data(symbol_key)
        if not symbol_data:
            return None
            
        return symbol_data.get(target_format)
    
    def from_ggshot(self, ggshot_symbol: str) -> Optional[str]:
        """Convert ggShot format (BTCUSDT) to Hummingbot format (BTC-USDT)"""
        return self.normalize(ggshot_symbol, "ggshot", "hummingbot")
    
    def to_ggshot(self, platform_symbol: str) -> Optional[str]:
        """Convert platform format (BTC-USDT) to ggShot format (BTCUSDT)"""
        return self.normalize(platform_symbol, "platform", "ggshot")
    
    def to_ccxt(self, platform_symbol: str) -> Optional[str]:
        """Convert platform format (BTC-USDT) to CCXT format (BTC/USDT)"""
        return self.normalize(platform_symbol, "platform", "ccxt")
    
    def from_ccxt(self, ccxt_symbol: str) -> Optional[str]:
        """Convert CCXT format (BTC/USDT) to platform format (BTC-USDT)"""
        return self.normalize(ccxt_symbol, "ccxt", "platform")
    
    def to_hummingbot(self, platform_symbol: str) -> Optional[str]:
        """Convert platform format to Hummingbot format (same for now)"""
        return self.normalize(platform_symbol, "platform", "hummingbot")
    
    def from_hummingbot(self, hummingbot_symbol: str) -> Optional[str]:
        """Convert Hummingbot format to platform format (same for now)"""
        return self.normalize(hummingbot_symbol, "hummingbot", "platform")

    def to_symphony(self, platform_symbol: str) -> Optional[str]:
        """Convert platform format (BTC-USDT) to Symphony format (BTC)"""
        return self.normalize(platform_symbol, "platform", "symphony")

    def from_symphony(self, symphony_symbol: str) -> Optional[str]:
        """Convert Symphony format (BTC) to platform format (BTC-USDT)"""
        return self.normalize(symphony_symbol, "symphony", "platform")

    def is_symphony_compatible(self, symbol: str, format_type: str = "platform") -> bool:
        """Check if symbol is compatible with Symphony.io live trading"""
        symbol_data = self.get_all_formats(symbol, format_type)
        if not symbol_data:
            return False
        return symbol_data.get("symphony_compatible", False)

    def is_aster_compatible(self, symbol: str, format_type: str = "platform") -> bool:
        """Check if symbol is compatible with AsterDEX live trading"""
        symbol_data = self.get_all_formats(symbol, format_type)
        if not symbol_data:
            return False
        return symbol_data.get("aster_compatible", False)

    def to_aster(self, platform_symbol: str) -> Optional[str]:
        """Convert platform format (BTC-USDT) to AsterDEX format (BTCUSDT)"""
        # AsterDEX uses same format as ggshot (no separator)
        return self.normalize(platform_symbol, "platform", "ggshot")

    def from_aster(self, aster_symbol: str) -> Optional[str]:
        """Convert AsterDEX format (BTCUSDT) to platform format (BTC-USDT)"""
        return self.normalize(aster_symbol, "ggshot", "platform")

    def is_supported(self, symbol: str, format_type: str = "platform") -> bool:
        """Check if symbol is supported in given format"""
        symbol_key = find_symbol_by_format(symbol, format_type)
        return symbol_key is not None
    
    def get_all_formats(self, symbol: str, format_type: str = "platform") -> Optional[Dict[str, str]]:
        """
        Get symbol in all supported formats
        
        Args:
            symbol: Input symbol
            format_type: Format of input symbol
            
        Returns:
            Dict with all format versions, or None if not supported
        """
        symbol_key = find_symbol_by_format(symbol, format_type)
        if not symbol_key:
            return None
            
        return get_symbol_data(symbol_key)
    
    def get_base_quote(self, symbol: str, format_type: str = "platform") -> Optional[tuple[str, str]]:
        """
        Extract base and quote currencies
        
        Returns:
            (base, quote) tuple, e.g., ("BTC", "USDT")
        """
        symbol_data = self.get_all_formats(symbol, format_type)
        if not symbol_data:
            return None
            
        return (symbol_data.get("base"), symbol_data.get("quote"))
    
    def get_coingecko_id(self, symbol: str, format_type: str = "platform") -> Optional[str]:
        """Get CoinGecko ID for a symbol"""
        symbol_data = self.get_all_formats(symbol, format_type)
        if not symbol_data:
            return None
            
        return symbol_data.get("coingecko_id")
    
    def get_supported_symbols(self, format_type: str = "platform") -> List[str]:
        """Get all supported symbols in specified format"""
        symbols = []
        for symbol_data in SYMBOL_REGISTRY.values():
            format_symbol = symbol_data.get(format_type)
            if format_symbol:
                symbols.append(format_symbol)
        return sorted(symbols)
    
    def get_stats(self) -> Dict[str, int]:
        """Get standardizer statistics"""
        return {
            "total_symbols": len(SYMBOL_REGISTRY),
            "ggshot_symbols": len([s for s in SYMBOL_REGISTRY.values() if s.get("ggshot")]),
            "ccxt_symbols": len([s for s in SYMBOL_REGISTRY.values() if s.get("ccxt")]),
            "hummingbot_symbols": len([s for s in SYMBOL_REGISTRY.values() if s.get("hummingbot")]),
            "platform_symbols": len([s for s in SYMBOL_REGISTRY.values() if s.get("platform")]),
            "symphony_symbols": len([s for s in SYMBOL_REGISTRY.values() if s.get("symphony")]),
            "symphony_compatible": len([s for s in SYMBOL_REGISTRY.values() if s.get("symphony_compatible")]),
            "aster_compatible": len([s for s in SYMBOL_REGISTRY.values() if s.get("aster_compatible")])
        }
    
    def validate_symbol(self, symbol: str, format_type: str = "platform", strict: bool = True) -> Dict[str, Union[bool, str, None]]:
        """
        Comprehensive symbol validation
        
        Returns:
            Dict with validation results and suggestions
        """
        result = {
            "is_valid": False,
            "symbol_key": None,
            "all_formats": None,
            "suggestion": None
        }
        
        # Direct lookup
        symbol_key = find_symbol_by_format(symbol, format_type)
        if symbol_key:
            result.update({
                "is_valid": True,
                "symbol_key": symbol_key,
                "all_formats": get_symbol_data(symbol_key)
            })
            return result
        
        if not strict:
            # Try fuzzy matching for common mistakes
            symbol_upper = symbol.upper()
            
            # Common format conversions for suggestions
            if format_type == "ggshot" and "/" in symbol:
                # User passed BTC/USDT instead of BTCUSDT
                suggested = symbol.replace("/", "").upper()
                if find_symbol_by_format(suggested, "ggshot"):
                    result["suggestion"] = f"Did you mean '{suggested}'? Use ggShot format without separators."
            
            elif format_type == "hummingbot" and "/" in symbol:
                # User passed BTC/USDT instead of BTC-USDT
                suggested = symbol.replace("/", "-").upper()
                if find_symbol_by_format(suggested, "hummingbot"):
                    result["suggestion"] = f"Did you mean '{suggested}'? Hummingbot uses dash separators."
            
            elif format_type == "ccxt" and "-" in symbol:
                # User passed BTC-USDT instead of BTC/USDT
                suggested = symbol.replace("-", "/").upper()
                if find_symbol_by_format(suggested, "ccxt"):
                    result["suggestion"] = f"Did you mean '{suggested}'? CCXT uses slash separators."
        
        return result


# Convenience functions for common operations
def ggshot_to_hummingbot(ggshot_symbol: str) -> Optional[str]:
    """Quick conversion from ggShot to Hummingbot format"""
    standardizer = UniversalSymbolStandardizer()
    return standardizer.from_ggshot(ggshot_symbol)

def hummingbot_to_ccxt(hummingbot_symbol: str) -> Optional[str]:
    """Quick conversion from Hummingbot to CCXT format"""
    standardizer = UniversalSymbolStandardizer() 
    return standardizer.normalize(hummingbot_symbol, "hummingbot", "ccxt")

def validate_symbol_quick(symbol: str, format_type: str = "platform") -> bool:
    """Quick symbol validation"""
    standardizer = UniversalSymbolStandardizer()
    return standardizer.is_supported(symbol, format_type)