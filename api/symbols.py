#!/usr/bin/env python3
"""
Symbols API endpoint for frontend symbol selection.
"""

from fastapi import APIRouter
from typing import List, Dict, Any
import sys
import os

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from core.symbols.standardizer import UniversalSymbolStandardizer

router = APIRouter(prefix="/api/symbols", tags=["symbols"])


@router.get("/supported")
async def get_supported_symbols() -> Dict[str, List[str]]:
    """Get all 141 supported trading symbols in various formats."""
    try:
        standardizer = UniversalSymbolStandardizer()

        # Get symbols in different formats for frontend use
        platform_symbols = standardizer.get_supported_symbols("platform")  # BTC-USDT format
        ccxt_symbols = standardizer.get_supported_symbols("ccxt")          # BTC/USDT format

        return {
            "platform": sorted(platform_symbols),  # For internal use
            "display": sorted(ccxt_symbols),       # For UI display (BTC/USDT looks better)
            "count": len(platform_symbols)
        }

    except Exception as e:
        return {
            "platform": [],
            "display": [],
            "count": 0,
            "error": str(e)
        }


@router.get("/search/{query}")
async def search_symbols(query: str) -> Dict[str, Any]:
    """Search symbols by base currency, symbol name, or partial match."""
    try:
        standardizer = UniversalSymbolStandardizer()
        platform_symbols = standardizer.get_supported_symbols("platform")
        ccxt_symbols = standardizer.get_supported_symbols("ccxt")

        query = query.upper().strip()

        # Search logic
        platform_matches = []
        display_matches = []

        for platform_symbol, ccxt_symbol in zip(platform_symbols, ccxt_symbols):
            # Match base currency (BTC from BTC-USDT)
            base_currency = platform_symbol.split('-')[0]

            # Check if query matches base currency or symbol
            if (query in platform_symbol or
                query in base_currency or
                query in ccxt_symbol):
                platform_matches.append(platform_symbol)
                display_matches.append(ccxt_symbol)

        return {
            "query": query,
            "platform": platform_matches[:20],  # Limit results
            "display": display_matches[:20],
            "count": len(platform_matches)
        }

    except Exception as e:
        return {
            "query": query,
            "platform": [],
            "display": [],
            "count": 0,
            "error": str(e)
        }


@router.get("/validate/{symbol}")
async def validate_symbol(symbol: str) -> Dict[str, Any]:
    """Validate if a symbol is supported and get all its format variations."""
    try:
        standardizer = UniversalSymbolStandardizer()

        # Try to detect format and validate
        symbol = symbol.upper().strip()

        # Check different formats
        formats_to_check = ["platform", "ccxt", "ggshot", "hummingbot"]

        for format_type in formats_to_check:
            if standardizer.is_supported(symbol, format_type):
                # Get all format variations
                all_formats = standardizer.get_all_formats(symbol, format_type)
                return {
                    "valid": True,
                    "symbol": symbol,
                    "detected_format": format_type,
                    "formats": all_formats
                }

        return {
            "valid": False,
            "symbol": symbol,
            "error": f"Symbol '{symbol}' is not supported"
        }

    except Exception as e:
        return {
            "valid": False,
            "symbol": symbol,
            "error": str(e)
        }