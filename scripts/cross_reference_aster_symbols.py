#!/usr/bin/env python3
"""
Cross-reference ggbot symbols with AsterDEX symbols.

This script:
1. Parses AsterDEX symbols from the test log
2. Loads ggbot's symbol registry (141 symbols)
3. Cross-references to find compatible symbols
4. Shows which ggbot symbols are available on AsterDEX
5. Shows which Aster symbols we don't support yet
"""

import json
import re
import sys
import os

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from core.symbols.registry import SYMBOL_REGISTRY


def parse_aster_symbols_from_log(log_path: str) -> dict:
    """
    Parse all symbols from AsterDEX API test log.

    Returns:
        Dict of symbol -> symbol_data from exchangeInfo
    """
    print(f"📖 Reading AsterDEX log: {log_path}")

    with open(log_path, 'r') as f:
        content = f.read()

    # Find the exchangeInfo JSON block
    # The log format is:
    # ================================================================================
    # Test: exchange_info
    # Timestamp: 2025-11-02T17:05:22.544066
    # ================================================================================
    # {
    #   "timezone": "UTC",
    #   ...
    # }
    #
    # Find the start of JSON (first { after "Test: exchange_info")
    start_marker = content.find("Test: exchange_info")
    if start_marker == -1:
        raise ValueError("Could not find 'Test: exchange_info' in log file")

    json_start = content.find("{", start_marker)
    if json_start == -1:
        raise ValueError("Could not find JSON start after 'Test: exchange_info'")

    # Find the next test separator or end of file
    next_test = content.find("\n================================================================================\nTest:", json_start)
    if next_test == -1:
        # This is the last test, use end of file
        json_str = content[json_start:]
    else:
        json_str = content[json_start:next_test]

    # Parse JSON
    data = json.loads(json_str.strip())

    # Extract symbols
    if 'symbols' not in data:
        raise ValueError("No 'symbols' field in exchangeInfo response")

    symbols = {}
    for symbol_data in data['symbols']:
        symbol = symbol_data.get('symbol')
        status = symbol_data.get('status')

        # Store all data, we'll filter later
        symbols[symbol] = {
            'symbol': symbol,
            'status': status,
            'contractType': symbol_data.get('contractType'),
            'baseAsset': symbol_data.get('baseAsset'),
            'quoteAsset': symbol_data.get('quoteAsset'),
            'marginAsset': symbol_data.get('marginAsset'),
            'pricePrecision': symbol_data.get('pricePrecision'),
            'quantityPrecision': symbol_data.get('quantityPrecision'),
            'baseAssetPrecision': symbol_data.get('baseAssetPrecision'),
            'quotePrecision': symbol_data.get('quotePrecision'),
            'filters': symbol_data.get('filters', [])
        }

    print(f"✅ Found {len(symbols)} total AsterDEX symbols")

    # Filter to TRADING status only
    trading_symbols = {k: v for k, v in symbols.items() if v['status'] == 'TRADING'}
    settling_symbols = {k: v for k, v in symbols.items() if v['status'] == 'SETTLING'}

    print(f"   - {len(trading_symbols)} TRADING")
    print(f"   - {len(settling_symbols)} SETTLING (being delisted - avoid)")

    return symbols, trading_symbols, settling_symbols


def cross_reference_symbols():
    """Cross-reference ggbot symbols with AsterDEX symbols."""

    print("\n" + "="*80)
    print("ASTER SYMBOL CROSS-REFERENCE")
    print("="*80 + "\n")

    # Parse AsterDEX symbols
    log_path = '/home/sev/ggbot/aster_api_test_20251102_170522.log'
    all_aster_symbols, trading_aster_symbols, settling_aster_symbols = parse_aster_symbols_from_log(log_path)

    # Get ggbot symbols (141 total)
    ggbot_symbols = {}
    for symbol_key, symbol_data in SYMBOL_REGISTRY.items():
        ggshot_format = symbol_data.get('ggshot')  # BTCUSDT format
        if ggshot_format:
            ggbot_symbols[ggshot_format] = {
                'key': symbol_key,
                'base': symbol_data.get('base'),
                'quote': symbol_data.get('quote'),
                'platform': symbol_data.get('platform'),
                'symphony_compatible': symbol_data.get('symphony_compatible', False),
                'websocket_cached': symbol_data.get('websocket_cached', False)
            }

    print(f"📊 ggbot registry: {len(ggbot_symbols)} symbols")
    print(f"📊 AsterDEX total: {len(all_aster_symbols)} symbols")
    print(f"📊 AsterDEX TRADING: {len(trading_aster_symbols)} symbols\n")

    # Find matches
    compatible_symbols = []
    incompatible_symbols = []

    for ggbot_symbol, ggbot_data in sorted(ggbot_symbols.items()):
        if ggbot_symbol in trading_aster_symbols:
            compatible_symbols.append({
                'symbol': ggbot_symbol,
                'ggbot_data': ggbot_data,
                'aster_data': trading_aster_symbols[ggbot_symbol]
            })
        else:
            incompatible_symbols.append({
                'symbol': ggbot_symbol,
                'ggbot_data': ggbot_data
            })

    # Results
    print("="*80)
    print(f"✅ COMPATIBLE SYMBOLS: {len(compatible_symbols)}/{len(ggbot_symbols)}")
    print("="*80 + "\n")

    # Show compatible symbols
    print("Symbol          Base/Quote   Symphony   WebSocket   Aster Status")
    print("-" * 80)
    for item in compatible_symbols:
        symbol = item['symbol']
        ggbot = item['ggbot_data']
        aster = item['aster_data']

        symphony_mark = "✓" if ggbot['symphony_compatible'] else "✗"
        websocket_mark = "✓" if ggbot['websocket_cached'] else "✗"

        print(f"{symbol:15} {ggbot['base']:>4}/{ggbot['quote']:<4}   "
              f"{symphony_mark:^9}   {websocket_mark:^10}   {aster['status']}")

    print(f"\n{'='*80}")
    print(f"❌ INCOMPATIBLE SYMBOLS: {len(incompatible_symbols)}/{len(ggbot_symbols)}")
    print("="*80 + "\n")

    # Show first 20 incompatible symbols
    print("These ggbot symbols are NOT available on AsterDEX:")
    print("-" * 80)
    for item in incompatible_symbols[:20]:
        symbol = item['symbol']
        ggbot = item['ggbot_data']
        symphony_mark = "✓" if ggbot['symphony_compatible'] else "✗"

        print(f"{symbol:15} {ggbot['base']:>4}/{ggbot['quote']:<4}   Symphony: {symphony_mark}")

    if len(incompatible_symbols) > 20:
        print(f"\n... and {len(incompatible_symbols) - 20} more")

    # Show Aster-only symbols (symbols on Aster that we don't support)
    aster_only_symbols = []
    for aster_symbol in trading_aster_symbols:
        if aster_symbol not in ggbot_symbols:
            aster_only_symbols.append(aster_symbol)

    print(f"\n{'='*80}")
    print(f"📊 ASTER-ONLY SYMBOLS: {len(aster_only_symbols)} (not in ggbot registry)")
    print("="*80 + "\n")

    print("These AsterDEX symbols are available but NOT in ggbot registry:")
    print("-" * 80)
    for symbol in sorted(aster_only_symbols[:30]):
        aster_data = trading_aster_symbols[symbol]
        print(f"{symbol:20} {aster_data['baseAsset']:>6}/{aster_data['quoteAsset']:<6} "
              f"({aster_data['contractType']})")

    if len(aster_only_symbols) > 30:
        print(f"\n... and {len(aster_only_symbols) - 30} more")

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print("="*80)
    print(f"ggbot symbols:          {len(ggbot_symbols)}")
    print(f"Aster TRADING symbols:  {len(trading_aster_symbols)}")
    print(f"Compatible symbols:     {len(compatible_symbols)} ({len(compatible_symbols)/len(ggbot_symbols)*100:.1f}% of ggbot)")
    print(f"Incompatible symbols:   {len(incompatible_symbols)} ({len(incompatible_symbols)/len(ggbot_symbols)*100:.1f}% of ggbot)")
    print(f"Aster-only symbols:     {len(aster_only_symbols)}")
    print()

    # Check how many Symphony symbols are Aster compatible
    symphony_symbols = [s for s in compatible_symbols if s['ggbot_data']['symphony_compatible']]
    print(f"Symphony + Aster:       {len(symphony_symbols)} symbols available on BOTH exchanges")
    print()

    # Show SETTLING symbols to avoid
    print(f"\n{'='*80}")
    print(f"⚠️  SETTLING SYMBOLS (BEING DELISTED - AVOID): {len(settling_aster_symbols)}")
    print("="*80)
    for symbol in sorted(settling_aster_symbols.keys())[:20]:
        print(f"  - {symbol}")
    if len(settling_aster_symbols) > 20:
        print(f"  ... and {len(settling_aster_symbols) - 20} more")

    print("\n")

    # Return for further processing
    return {
        'compatible': compatible_symbols,
        'incompatible': incompatible_symbols,
        'aster_only': aster_only_symbols,
        'settling': list(settling_aster_symbols.keys())
    }


if __name__ == '__main__':
    results = cross_reference_symbols()

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Update core/symbols/registry.py with 'aster_compatible' flag")
    print("2. Update aster_service_v3.py to validate symbols before trading")
    print("3. Add AsterDEX symbols to market data websocket (if needed)")
    print("4. Frontend: Show Aster badge on compatible symbols")
    print()
