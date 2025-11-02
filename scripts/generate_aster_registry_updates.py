#!/usr/bin/env python3
"""
Generate registry updates for Aster-compatible symbols.

This script generates Python code to add 'aster_compatible' flags
to the symbol registry based on cross-reference results.
"""

import sys
import os

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from core.symbols.registry import SYMBOL_REGISTRY

# Compatible symbols from cross-reference (TRADING status only)
ASTER_COMPATIBLE_SYMBOLS = [
    'AAVEUSDT', 'ADAUSDT', 'APEUSDT', 'APTUSDT', 'ARBUSDT', 'ATOMUSDT',
    'AVAXUSDT', 'BCHUSDT', 'BNBUSDT', 'BTCUSDT', 'CAKEUSDT', 'CRVUSDT',
    'DASHUSDT', 'DOGEUSDT', 'DOTUSDT', 'DYDXUSDT', 'ENAUSDT', 'ETCUSDT',
    'ETHUSDT', 'GALAUSDT', 'INJUSDT', 'LINKUSDT', 'LTCUSDT', 'NEARUSDT',
    'ONDOUSDT', 'OPUSDT', 'PYTHUSDT', 'SEIUSDT', 'SOLUSDT', 'SUIUSDT',
    'TRXUSDT', 'WLDUSDT', 'XRPUSDT'
]

def generate_registry_updates():
    """Generate Python code to update registry with aster_compatible flags."""

    print("="*80)
    print("ASTER-COMPATIBLE SYMBOL REGISTRY UPDATES")
    print("="*80)
    print()
    print(f"Found {len(ASTER_COMPATIBLE_SYMBOLS)} Aster-compatible symbols")
    print()

    # Find symbol keys for compatible symbols
    updates = []

    for aster_symbol in sorted(ASTER_COMPATIBLE_SYMBOLS):
        # Find the registry key
        symbol_key = None
        for key, data in SYMBOL_REGISTRY.items():
            if data.get('ggshot') == aster_symbol:
                symbol_key = key
                break

        if symbol_key:
            base = SYMBOL_REGISTRY[symbol_key].get('base')
            quote = SYMBOL_REGISTRY[symbol_key].get('quote')
            symphony = SYMBOL_REGISTRY[symbol_key].get('symphony_compatible', False)

            updates.append({
                'key': symbol_key,
                'symbol': aster_symbol,
                'base': base,
                'quote': quote,
                'symphony': symphony
            })

    # Generate Python code
    print("="*80)
    print("COPY AND PASTE THIS INTO core/symbols/registry.py")
    print("="*80)
    print()
    print("# Add these lines to each compatible symbol's dict:")
    print()

    for update in updates:
        symphony_mark = "✓" if update['symphony'] else "✗"
        print(f'    # {update["symbol"]:15} ({update["base"]:>4}/{update["quote"]:<4}) Symphony: {symphony_mark}')
        print(f'    "{update["key"]}": {{')
        print(f'        ...')
        print(f'        "aster_compatible": True,')
        print(f'    }},')
        print()

    # Generate summary
    print("="*80)
    print("MANUAL UPDATE INSTRUCTIONS")
    print("="*80)
    print()
    print("1. Open: core/symbols/registry.py")
    print("2. For EACH of the 33 symbols above:")
    print("   - Find the symbol's entry (e.g., \"aave\", \"btc\", etc.)")
    print("   - Add this line: \"aster_compatible\": True,")
    print("   - Place it after \"symphony_compatible\" line")
    print()
    print("3. For ALL other symbols (109 incompatible):")
    print("   - Add this line: \"aster_compatible\": False,")
    print()
    print("Example before:")
    print("    \"aave\": {")
    print("        \"base\": \"AAVE\",")
    print("        \"quote\": \"USDT\",")
    print("        \"ggshot\": \"AAVEUSDT\",")
    print("        \"ccxt\": \"AAVE/USDT\",")
    print("        \"hummingbot\": \"AAVE-USDT\",")
    print("        \"platform\": \"AAVE-USDT\",")
    print("        \"coingecko_id\": \"aave\",")
    print("        \"symphony\": \"AAVE\",")
    print("        \"symphony_compatible\": True,")
    print("        \"websocket_cached\": True")
    print("    },")
    print()
    print("Example after:")
    print("    \"aave\": {")
    print("        \"base\": \"AAVE\",")
    print("        \"quote\": \"USDT\",")
    print("        \"ggshot\": \"AAVEUSDT\",")
    print("        \"ccxt\": \"AAVE/USDT\",")
    print("        \"hummingbot\": \"AAVE-USDT\",")
    print("        \"platform\": \"AAVE-USDT\",")
    print("        \"coingecko_id\": \"aave\",")
    print("        \"symphony\": \"AAVE\",")
    print("        \"symphony_compatible\": True,")
    print("        \"aster_compatible\": True,  # <-- NEW LINE")
    print("        \"websocket_cached\": True")
    print("    },")
    print()

    # Show multi-exchange symbols
    multi_exchange = [u for u in updates if u['symphony']]
    print("="*80)
    print(f"MULTI-EXCHANGE SYMBOLS: {len(multi_exchange)} available on BOTH Symphony AND Aster")
    print("="*80)
    print()
    for update in multi_exchange:
        print(f"  {update['symbol']:15} {update['base']:>4}/{update['quote']:<4}")
    print()

    # Show Aster-only symbols
    aster_only = [u for u in updates if not u['symphony']]
    print("="*80)
    print(f"ASTER-ONLY SYMBOLS: {len(aster_only)} available ONLY on Aster (not Symphony)")
    print("="*80)
    print()
    for update in aster_only:
        print(f"  {update['symbol']:15} {update['base']:>4}/{update['quote']:<4}")
    print()


if __name__ == '__main__':
    generate_registry_updates()
