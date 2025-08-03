"""
BitMEX Testnet Exchange Guide

This module provides exchange-specific guidance for BitMEX testnet to help the LLM
generate better tool calls. This guide is based on real metadata extracted from
BitMEX testnet via CCXT on 2025-01-22.

The information here supplements the MCP tool schema with exchange-specific
requirements, limits, and conventions that the LLM should follow.
"""

from typing import Dict, List, Optional

# Exchange identification
EXCHANGE_ID = "bitmex"
ENVIRONMENT = "testnet"
EXCHANGE_NAME = "BitMEX Testnet"

def get_exchange_guide_text(symbol: Optional[str] = None) -> str:
    """
    Get formatted exchange guide text for inclusion in LLM prompts.
    
    Args:
        symbol: Optional specific symbol to get targeted guidance for
        
    Returns:
        Formatted guide text string for LLM consumption
    """
    
    # Determine minimum amount for the specific symbol
    min_amount_note = ""
    if symbol:
        if symbol.upper() in ["BTC/USD", "BTC"]:
            min_amount_note = f"\n- {symbol}: 100 contract minimum (BTC exception)"
        else:
            min_amount_note = f"\n- {symbol}: 1 contract minimum (standard)"
    
    guide_text = f"""
=== BitMEX Testnet Trading Guide ===

ACCOUNT BALANCE STRUCTURE:
- Available Margin: Your actual usable balance for trading (use this for position sizing)
- Equity: May show small/weird values due to BitMEX's calculation method
- Position Sizing: Base position sizes on AVAILABLE MARGIN, not equity
- Risk Management: The system will auto-adjust positions to stay within 5% of available margin

MINIMUM ORDER SIZES:
- Default: 1 contract for most symbols
- Exception: BTC/USD requires 100 contract minimum due to precision settings{min_amount_note}
- Decimal amounts: Automatically rounded down to nearest whole contract

SUPPORTED ORDER TYPES AND TOOLS:
- market: Immediate execution at current market price
  → Use create_market_buy_order or create_market_sell_order
  → NEVER use create_limit_order with null/empty price
- limit: Orders at specific price levels  
  → Use create_limit_order with valid price parameter
- stop: Stop orders - use create_limit_order with params={{"stopPx": trigger_price, "execInst": "Close"}}
  → Use create_limit_order with both price and stopPx parameters
- Note: stopLimit orders are NOT supported
- Note: reduce_only orders use regular orders with params={{"reduceOnly": true}}
- IMPORTANT: Do NOT use create_stop_order - it's not properly implemented in the MCP

REQUIRED PARAMETERS:
- stop_orders: Use create_limit_order with price=stop_price and params={{"stopPx": stop_price, "execInst": "Close", "triggerDirection": "below"}}
  Example: Stop-loss sell at 100000: create_limit_order(side="sell", price=100000, params={{"stopPx": 100000, "execInst": "Close", "triggerDirection": "below"}})
- leverage: Must be an integer between 1-100 (no decimals) - but see "TESTNET LIMITATIONS" below
- symbols: Use standard format (BTC/USD) - system maps to BitMEX format automatically

PRICE HANDLING:
- Prices automatically rounded to exchange tick size (0.5 for BTC, 0.05 for ETH)
- Very high buy prices execute as market orders immediately
- Very low buy prices require sufficient margin to place order

EXCHANGE CHARACTERISTICS:
- Contract types: Perpetual swaps (no expiry)
- Settlement: BTC-settled for most USD pairs, USDT-settled for USDT pairs
- Margin: Cross margin mode (enforced for multi-asset accounts)
- Leverage range: 1-100x (integers only)
- Rate limit: 100ms minimum between requests

TESTNET LIMITATIONS:
- Isolated margin not supported for multi-asset accounts
- set_leverage may fail with "Isolated margin not supported" error
- Account balances are test funds only

TOOL SELECTION RULES:
1. For MARKET ORDERS (immediate execution):
   - Buy position: Use create_market_buy_order  
   - Sell position: Use create_market_sell_order
   - NEVER use create_limit_order with price=null/empty
2. For LIMIT ORDERS (specific price):
   - Use create_limit_order with valid price parameter
3. For STOP ORDERS (triggered orders):
   - Use create_limit_order with both price and stopPx parameters

COMMON PATTERNS:
1. For new positions: Skip set_leverage call - testnet uses cross margin at 100x by default
2. For stop losses: Use create_limit_order with price=stop_price and params={{"stopPx": stop_price, "execInst": "Close", "triggerDirection": "below"}}
3. Position closing: Use create_market_sell_order with params={{"reduceOnly": true}}
4. Contract sizing: All amounts are in contracts, not USD values
5. Position sizing with leverage intent:
   - Use 'position_size_usd' directly from intent for contract calculation
   - For BTC/USD: contracts = position_size_usd (since 1 contract = $1)
   - Formula: BTC/USD contracts = position_size_usd value

ERROR HANDLING:
- "amount...must be greater than minimum": Increase to minimum (100 for BTC, 1 for others)
- "insufficient Available Balance": Reduce position size or adjust price
- "Isolated margin not supported": Ignore - testnet uses cross margin by default
- "Field required": Check that all required parameters are included
"""
    
    return guide_text.strip()

def get_minimum_amount(symbol: str) -> int:
    """
    Get the minimum order amount for a specific symbol.
    
    Args:
        symbol: Trading symbol in standard format (e.g., 'BTC/USD')
        
    Returns:
        Minimum contract amount for the symbol
    """
    # Based on precision.amount from BitMEX testnet metadata
    if symbol.upper() in ["BTC/USD", "BTC"]:
        return 100  # BTC requires 100 contract minimum
    else:
        return 1    # Most other symbols require 1 contract minimum

def get_supported_order_types() -> List[str]:
    """
    Get list of order types supported by BitMEX testnet.
    
    Returns:
        List of supported order type strings
    """
    # Based on 'has' capabilities from exchange.describe()
    return [
        "market",
        "limit", 
        "stop",
        # Note: "stopLimit" is NOT supported
    ]

def get_required_credentials() -> List[str]:
    """
    Get list of required credentials for BitMEX testnet.
    
    Returns:
        List of required credential field names
    """
    # Based on requiredCredentials from exchange.describe()
    return ["apiKey", "secret"]

def get_leverage_limits() -> Dict[str, int]:
    """
    Get leverage limits for BitMEX testnet.
    
    Returns:
        Dictionary with min and max leverage values
    """
    # Based on limits.leverage from fetch_markets() data
    return {
        "min": 1,
        "max": 100
    }

def get_rate_limit_ms() -> int:
    """
    Get the minimum time between requests in milliseconds.
    
    Returns:
        Rate limit in milliseconds
    """
    # Based on rateLimit from exchange.describe()
    return 100

def validate_symbol_minimum(symbol: str, amount: float) -> bool:
    """
    Check if an order amount meets the minimum requirement for a symbol.
    
    Args:
        symbol: Trading symbol in standard format
        amount: Order amount in contracts
        
    Returns:
        True if amount meets minimum, False otherwise
    """
    min_amount = get_minimum_amount(symbol)
    return amount >= min_amount

# Metadata for programmatic access
EXCHANGE_METADATA = {
    "exchange_id": EXCHANGE_ID,
    "environment": ENVIRONMENT,
    "name": EXCHANGE_NAME,
    "minimum_amounts": {
        "BTC/USD": 100,
        "default": 1
    },
    "supported_order_types": get_supported_order_types(),
    "required_credentials": get_required_credentials(),
    "leverage_limits": get_leverage_limits(),
    "rate_limit_ms": get_rate_limit_ms(),
    "special_notes": [
        "BTC/USD requires 100 contract minimum due to precision settings",
        "Stop orders require BOTH price and stopPrice parameters",
        "Leverage must be an integer (no decimals)",
        "Cross margin mode is enforced for multi-asset accounts",
        "Contract-based sizing, not USD amounts",
        "Decimal amounts are automatically rounded down",
        "create_reduce_only_order tool has parameter naming issues - use regular orders with reduceOnly param instead"
    ]
}