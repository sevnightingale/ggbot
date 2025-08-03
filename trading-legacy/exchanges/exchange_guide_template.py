"""
Exchange Guide Template

This template provides a standardized structure for creating exchange-specific guides
that help the LLM generate better tool calls. Copy this file and customize it for
each exchange you want to support.

Usage:
1. Copy this file to: trading/exchanges/{exchange_name}/exchange_guide.py
2. Update all template values marked with {TEMPLATE_*}
3. Customize the guide text based on the exchange's specific requirements
4. Test the guide with the LLM to ensure it generates correct tool calls

The information here supplements the MCP tool schema with exchange-specific
requirements, limits, and conventions that the LLM should follow.
"""

from typing import Dict, List, Optional

# Exchange identification - CUSTOMIZE THESE
EXCHANGE_ID = "{TEMPLATE_EXCHANGE_ID}"  # e.g., "binance", "coinbase", "kraken"
ENVIRONMENT = "{TEMPLATE_ENVIRONMENT}"  # e.g., "mainnet", "testnet", "sandbox"
EXCHANGE_NAME = "{TEMPLATE_EXCHANGE_NAME}"  # e.g., "Binance Mainnet", "Coinbase Pro"

def get_exchange_guide_text(symbol: Optional[str] = None) -> str:
    """
    Get formatted exchange guide text for inclusion in LLM prompts.
    
    Args:
        symbol: Optional specific symbol to get targeted guidance for
        
    Returns:
        Formatted guide text string for LLM consumption
    """
    
    # Determine minimum amount for the specific symbol - CUSTOMIZE THIS LOGIC
    min_amount_note = ""
    if symbol:
        min_amount = get_minimum_amount(symbol)
        min_amount_note = f"\n- {symbol}: {min_amount} minimum"
    
    guide_text = f"""
=== {EXCHANGE_NAME} Trading Guide ===

ACCOUNT BALANCE STRUCTURE:
- {"{TEMPLATE_BALANCE_STRUCTURE}"}
- {"{TEMPLATE_MARGIN_EXPLANATION}"}
- {"{TEMPLATE_POSITION_SIZING_GUIDANCE}"}

MINIMUM ORDER SIZES:
- {"{TEMPLATE_DEFAULT_MINIMUM}"}{min_amount_note}
- {"{TEMPLATE_MINIMUM_NOTES}"}

SUPPORTED ORDER TYPES AND TOOLS:
- market: {"{TEMPLATE_MARKET_ORDER_GUIDANCE}"}
  → Use create_market_buy_order or create_market_sell_order
- limit: {"{TEMPLATE_LIMIT_ORDER_GUIDANCE}"}
  → Use create_limit_order with valid price parameter
- stop: {"{TEMPLATE_STOP_ORDER_GUIDANCE}"}
  → Use create_limit_order with both price and stopPx parameters
- Note: {"{TEMPLATE_UNSUPPORTED_TYPES}"}

REQUIRED PARAMETERS:
- {"{TEMPLATE_REQUIRED_PARAMS}"}
- symbols: Use standard format ({"{TEMPLATE_SYMBOL_FORMAT}"}) - system maps to exchange format automatically

PRICE HANDLING:
- {"{TEMPLATE_PRICE_ROUNDING}"}
- {"{TEMPLATE_PRICE_SPECIAL_CASES}"}

EXCHANGE CHARACTERISTICS:
- Contract types: {"{TEMPLATE_CONTRACT_TYPES}"}
- Settlement: {"{TEMPLATE_SETTLEMENT_INFO}"}
- Margin: {"{TEMPLATE_MARGIN_MODE}"}
- Leverage range: {"{TEMPLATE_LEVERAGE_RANGE}"}
- Rate limit: {"{TEMPLATE_RATE_LIMIT}"}

{"{TEMPLATE_ENVIRONMENT_UPPER}"} LIMITATIONS:
- {"{TEMPLATE_ENV_LIMITATIONS}"}

TOOL SELECTION RULES:
1. For MARKET ORDERS (immediate execution):
   - Buy position: Use create_market_buy_order  
   - Sell position: Use create_market_sell_order
2. For LIMIT ORDERS (specific price):
   - Use create_limit_order with valid price parameter
3. For STOP ORDERS (triggered orders):
   - Use create_limit_order with both price and stopPx parameters

COMMON PATTERNS:
1. {"{TEMPLATE_LEVERAGE_PATTERN}"}
2. {"{TEMPLATE_STOP_LOSS_PATTERN}"}
3. {"{TEMPLATE_POSITION_CLOSING_PATTERN}"}
4. Contract sizing: {"{TEMPLATE_CONTRACT_SIZING_INFO}"}
5. Position sizing with leverage intent:
   - Use 'position_size_usd' directly from intent for contract calculation
   - For {"{TEMPLATE_MAIN_SYMBOL}"}: contracts = position_size_usd × {"{TEMPLATE_CONTRACT_MULTIPLIER}"}
   - Formula: {"{TEMPLATE_MAIN_SYMBOL}"} contracts = position_size_usd × {"{TEMPLATE_CONTRACT_MULTIPLIER}"}

ERROR HANDLING:
- {"{TEMPLATE_ERROR_PATTERNS}"}
"""
    
    return guide_text.strip()

def get_minimum_amount(symbol: str) -> float:
    """
    Get the minimum order amount for a specific symbol.
    
    Args:
        symbol: Trading symbol in standard format (e.g., 'BTC/USDT')
        
    Returns:
        Minimum contract/share amount for the symbol
    """
    # CUSTOMIZE THIS BASED ON EXCHANGE REQUIREMENTS
    # Example logic:
    if symbol.upper() in ["{TEMPLATE_SPECIAL_SYMBOL_1}", "{TEMPLATE_SPECIAL_SYMBOL_2}"]:
        return float("{TEMPLATE_SPECIAL_MINIMUM}")  # Special symbols with higher minimums
    else:
        return float("{TEMPLATE_DEFAULT_MINIMUM_VALUE}")  # Standard minimum

def get_supported_order_types() -> List[str]:
    """
    Get list of order types supported by this exchange.
    
    Returns:
        List of supported order type strings
    """
    # CUSTOMIZE THIS BASED ON EXCHANGE CAPABILITIES
    return [
        "market",
        "limit", 
        "stop",
        # Add other supported types like "stopLimit", "oco", etc.
    ]

def get_required_credentials() -> List[str]:
    """
    Get list of required credentials for this exchange.
    
    Returns:
        List of required credential field names
    """
    # CUSTOMIZE THIS BASED ON EXCHANGE REQUIREMENTS
    return ["apiKey", "secret"]  # Most exchanges require these
    # Some may also require: "password", "sandbox", "uid", etc.

def get_leverage_limits() -> Dict[str, int]:
    """
    Get leverage limits for this exchange.
    
    Returns:
        Dictionary with min and max leverage values
    """
    # CUSTOMIZE THIS BASED ON EXCHANGE LIMITS
    return {
        "min": int("{TEMPLATE_MIN_LEVERAGE}"),
        "max": int("{TEMPLATE_MAX_LEVERAGE}")
    }

def get_rate_limit_ms() -> int:
    """
    Get the minimum time between requests in milliseconds.
    
    Returns:
        Rate limit in milliseconds
    """
    # CUSTOMIZE THIS BASED ON EXCHANGE RATE LIMITS
    return int("{TEMPLATE_RATE_LIMIT_MS}")

def validate_symbol_minimum(symbol: str, amount: float) -> bool:
    """
    Check if an order amount meets the minimum requirement for a symbol.
    
    Args:
        symbol: Trading symbol in standard format
        amount: Order amount in contracts/shares
        
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
        "{TEMPLATE_SPECIAL_SYMBOL_1}": float("{TEMPLATE_SPECIAL_MINIMUM}"),
        "default": float("{TEMPLATE_DEFAULT_MINIMUM_VALUE}")
    },
    "supported_order_types": get_supported_order_types(),
    "required_credentials": get_required_credentials(),
    "leverage_limits": get_leverage_limits(),
    "rate_limit_ms": get_rate_limit_ms(),
    "special_notes": [
        # CUSTOMIZE THESE BASED ON EXCHANGE QUIRKS
        "{TEMPLATE_SPECIAL_NOTE_1}",
        "{TEMPLATE_SPECIAL_NOTE_2}",
        "{TEMPLATE_SPECIAL_NOTE_3}",
        "Use 'position_size_usd' from intent for position sizing calculations",
        "Contract multipliers vary by symbol - check exchange documentation"
    ]
}

# Template customization guide
CUSTOMIZATION_GUIDE = """
To customize this template for a new exchange:

1. Replace all {TEMPLATE_*} placeholders with actual values
2. Update the guide text to reflect exchange-specific requirements
3. Implement exchange-specific logic in get_minimum_amount()
4. Add exchange-specific order types to get_supported_order_types()
5. Set correct rate limits and leverage limits
6. Add exchange-specific error patterns and handling notes
7. Test with real exchange data to ensure accuracy

Key areas to focus on:
- Position sizing formulas (especially contract multipliers)
- Order type support and parameters
- Error message patterns for troubleshooting
- Exchange-specific limitations and quirks
"""