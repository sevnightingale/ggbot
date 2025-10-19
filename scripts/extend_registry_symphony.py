"""
Extend Symbol Registry with Symphony Format Support

This script adds two new fields to each symbol in the registry:
1. "symphony": The base currency (e.g., "BTC" for BTC-USDT) - for Symphony API calls
2. "symphony_compatible": Boolean indicating if symbol is supported by Symphony.io

The 100 Symphony-compatible symbols are sourced from:
core/services/websocket_market_data_service.py::SYMBOLS

Usage:
    python scripts/extend_registry_symphony.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.symbols.registry import SYMBOL_REGISTRY

# 100 Symphony-compatible symbols (from WebSocket service)
SYMPHONY_COMPATIBLE_SYMBOLS = [
    '1INCHUSDT', 'AAVEUSDT', 'ADAUSDT', 'ALGOUSDT', 'ALICEUSDT', 'ALTUSDT', 'ANKRUSDT', 'APEUSDT', 'API3USDT', 'APTUSDT',
    'ARUSDT', 'ARBUSDT', 'ARKMUSDT', 'ASTRUSDT', 'ATOMUSDT', 'AUCTIONUSDT', 'AVAXUSDT', 'BATUSDT', 'BCHUSDT', 'BNBUSDT',
    'BOMEUSDT', 'BTCUSDT', 'CAKEUSDT', 'CFXUSDT', 'COMPUSDT', 'DASHUSDT', 'DOGEUSDT', 'DOTUSDT', 'DYDXUSDT', 'EGLDUSDT',
    'ENAUSDT', 'ENSUSDT', 'ETCUSDT', 'ETHUSDT', 'ETHFIUSDT', 'FETUSDT', 'FILUSDT', 'FLOWUSDT', 'GALAUSDT', 'GMTUSDT',
    'GMXUSDT', 'GRTUSDT', 'HBARUSDT', 'ICPUSDT', 'INJUSDT', 'IOTXUSDT', 'JASMYUSDT', 'JTOUSDT', 'JUPUSDT', 'KSMUSDT',
    'LDOUSDT', 'LINKUSDT', 'LRCUSDT', 'LTCUSDT', 'MAGICUSDT', 'MANAUSDT', 'MASKUSDT', 'NEARUSDT', 'NEOUSDT', 'NMRUSDT',
    'NOTUSDT', 'NTRNUSDT', 'ONDOUSDT', 'OPUSDT', 'ORDIUSDT', 'PENDLEUSDT', 'PEOPLEUSDT', 'PYTHUSDT', 'QTUMUSDT', 'RAREUSDT',
    'RENDERUSDT', 'ROSEUSDT', 'RSRUSDT', 'RVNUSDT', 'SUSDT', 'SANDUSDT', 'SEIUSDT', 'SKLUSDT', 'SNXUSDT', 'SOLUSDT',
    'STORJUSDT', 'STRKUSDT', 'STXUSDT', 'TAOUSDT', 'THETAUSDT', 'TIAUSDT', 'TRBUSDT', 'TRXUSDT', 'TURBOUSDT', 'TWTUSDT',
    'VETUSDT', 'WUSDT', 'WIFUSDT', 'WLDUSDT', 'WOOUSDT', 'XRPUSDT', 'YFIUSDT', 'ZILUSDT', 'ZROUSDT', 'ZRXUSDT'
]


def extend_registry():
    """Add Symphony fields to all symbols in registry."""

    print("🔧 Extending Symbol Registry with Symphony Format Support\n")

    # Convert ggShot list to set for faster lookup
    compatible_set = set(SYMPHONY_COMPATIBLE_SYMBOLS)

    compatible_count = 0
    incompatible_count = 0

    # Process each symbol
    for symbol_key, symbol_data in SYMBOL_REGISTRY.items():
        ggshot_format = symbol_data.get("ggshot")
        base_currency = symbol_data.get("base")

        if not ggshot_format or not base_currency:
            print(f"⚠️  Warning: Symbol '{symbol_key}' missing ggshot or base field, skipping")
            continue

        # Check if this symbol is Symphony-compatible
        is_compatible = ggshot_format in compatible_set

        if is_compatible:
            # Add Symphony format (base currency only)
            symbol_data["symphony"] = base_currency
            symbol_data["symphony_compatible"] = True
            compatible_count += 1
            print(f"✅ {ggshot_format:15} → Symphony: {base_currency:10} (compatible)")
        else:
            # Mark as incompatible (no Symphony trading)
            symbol_data["symphony"] = None
            symbol_data["symphony_compatible"] = False
            incompatible_count += 1

    print(f"\n📊 Summary:")
    print(f"   Symphony-compatible symbols: {compatible_count}")
    print(f"   Incompatible symbols: {incompatible_count}")
    print(f"   Total symbols: {len(SYMBOL_REGISTRY)}")

    return compatible_count, incompatible_count


def generate_updated_registry_code():
    """Generate the updated registry.py file content."""

    print("\n🔨 Generating updated registry.py code...\n")

    # Read current registry.py
    registry_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'symbols', 'registry.py')

    with open(registry_path, 'r') as f:
        lines = f.readlines()

    # Find where to insert new fields (after each symbol's existing fields)
    output_lines = []
    in_symbol_block = False
    current_indent = ""

    for line in lines:
        output_lines.append(line)

        # Detect symbol block start
        if '": {' in line and not line.strip().startswith('#'):
            in_symbol_block = True
            # Detect indentation
            current_indent = line[:len(line) - len(line.lstrip())]
            continue

        # Detect coingecko_id line (last field before closing brace)
        if in_symbol_block and '"coingecko_id":' in line:
            # Get the symbol key from a few lines back
            symbol_key = None
            for prev_line in reversed(output_lines[-10:]):
                if '": {' in prev_line:
                    symbol_key = prev_line.split('"')[1]
                    break

            if symbol_key and symbol_key in SYMBOL_REGISTRY:
                symbol_data = SYMBOL_REGISTRY[symbol_key]

                # Add comma to coingecko_id line (since we're adding more fields)
                output_lines[-1] = line.rstrip().rstrip(',') + ',\n'

                # Add Symphony fields
                symphony_value = symbol_data.get("symphony")
                symphony_compatible = symbol_data.get("symphony_compatible", False)

                if symphony_value:
                    output_lines.append(f'{current_indent}    "symphony": "{symphony_value}",\n')
                else:
                    output_lines.append(f'{current_indent}    "symphony": None,\n')

                output_lines.append(f'{current_indent}    "symphony_compatible": {symphony_compatible}\n')

        # Detect symbol block end
        if in_symbol_block and line.strip() == '},':
            in_symbol_block = False

    return ''.join(output_lines)


def write_updated_registry(content):
    """Write the updated registry.py file."""

    registry_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'symbols', 'registry.py')
    backup_path = registry_path + '.backup'

    # Create backup
    print(f"💾 Creating backup at {backup_path}")
    with open(registry_path, 'r') as f:
        backup_content = f.read()
    with open(backup_path, 'w') as f:
        f.write(backup_content)

    # Write updated file
    print(f"✍️  Writing updated registry.py")
    with open(registry_path, 'w') as f:
        f.write(content)

    print(f"✅ Registry updated successfully!\n")
    print(f"   Original backed up to: {backup_path}")
    print(f"   Updated file: {registry_path}")


def main():
    """Main execution."""

    print("="*60)
    print("Symphony Registry Extension")
    print("="*60 + "\n")

    # Step 1: Extend in-memory registry
    compatible, incompatible = extend_registry()

    # Step 2: Generate updated code
    updated_content = generate_updated_registry_code()

    # Step 3: Write to file
    write_updated_registry(updated_content)

    print("\n" + "="*60)
    print("✅ COMPLETE")
    print("="*60)
    print(f"\nNext steps:")
    print(f"1. Review the changes in core/symbols/registry.py")
    print(f"2. Test symbol lookups with UniversalSymbolStandardizer")
    print(f"3. Add to_symphony() and from_symphony() methods to standardizer.py")
    print(f"4. If something went wrong, restore from registry.py.backup")


if __name__ == "__main__":
    main()
