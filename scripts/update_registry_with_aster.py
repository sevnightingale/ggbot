#!/usr/bin/env python3
"""
Automatically update registry.py with aster_compatible flags.

This script programmatically adds 'aster_compatible' field to all symbols
in the registry based on cross-reference results.
"""

import re
import sys
import os

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

# Compatible symbols from cross-reference (TRADING status only on AsterDEX)
ASTER_COMPATIBLE_SYMBOLS = {
    'AAVEUSDT', 'ADAUSDT', 'APEUSDT', 'APTUSDT', 'ARBUSDT', 'ATOMUSDT',
    'AVAXUSDT', 'BCHUSDT', 'BNBUSDT', 'BTCUSDT', 'CAKEUSDT', 'CRVUSDT',
    'DASHUSDT', 'DOGEUSDT', 'DOTUSDT', 'DYDXUSDT', 'ENAUSDT', 'ETCUSDT',
    'ETHUSDT', 'GALAUSDT', 'INJUSDT', 'LINKUSDT', 'LTCUSDT', 'NEARUSDT',
    'ONDOUSDT', 'OPUSDT', 'PYTHUSDT', 'SEIUSDT', 'SOLUSDT', 'SUIUSDT',
    'TRXUSDT', 'WLDUSDT', 'XRPUSDT'
}

def update_registry():
    """Update registry.py with aster_compatible flags."""

    registry_path = os.path.join(PROJECT_DIR, 'core/symbols/registry.py')

    print(f"📖 Reading: {registry_path}")

    with open(registry_path, 'r') as f:
        content = f.read()

    print(f"✅ Loaded {len(content)} characters")

    # Strategy: Add "aster_compatible": True/False after each "symphony_compatible" line
    # Pattern: Find lines like: "symphony_compatible": True,
    # Then check if next line already has aster_compatible

    lines = content.split('\n')
    updated_lines = []
    added_count = 0
    skipped_count = 0

    # Track current symbol being processed
    current_symbol = None
    current_ggshot = None

    for i, line in enumerate(lines):
        updated_lines.append(line)

        # Detect symbol entries: look for "ggshot": "XXXUSDT"
        ggshot_match = re.search(r'"ggshot":\s*"([A-Z0-9]+USDT)"', line)
        if ggshot_match:
            current_ggshot = ggshot_match.group(1)

        # Find symphony_compatible lines
        if '"symphony_compatible":' in line:
            # Check if next line already has aster_compatible
            next_line = lines[i + 1] if i + 1 < len(lines) else ""

            if '"aster_compatible":' in next_line:
                # Already has the field, skip
                skipped_count += 1
                continue

            # Add aster_compatible field
            # Determine value based on current_ggshot
            is_compatible = current_ggshot in ASTER_COMPATIBLE_SYMBOLS

            # Match indentation from current line
            indent_match = re.match(r'^(\s*)', line)
            indent = indent_match.group(1) if indent_match else "        "

            # Python dict syntax needs True/False (capital), not "true"/"false"
            aster_line = f'{indent}"aster_compatible": {is_compatible},'

            updated_lines.append(aster_line)
            added_count += 1

    # Join back together
    updated_content = '\n'.join(updated_lines)

    # Write to file
    print(f"\n📝 Writing updates...")
    print(f"   - Added {added_count} aster_compatible flags")
    print(f"   - Skipped {skipped_count} (already present)")

    with open(registry_path, 'w') as f:
        f.write(updated_content)

    print(f"✅ Updated: {registry_path}")

    # Verify by importing
    print(f"\n🔍 Verifying import...")
    try:
        # Clear module cache
        if 'core.symbols.registry' in sys.modules:
            del sys.modules['core.symbols.registry']

        from core.symbols.registry import SYMBOL_REGISTRY

        aster_compatible_count = sum(
            1 for s in SYMBOL_REGISTRY.values()
            if s.get('aster_compatible', False)
        )

        print(f"✅ Registry loaded successfully")
        print(f"   - Total symbols: {len(SYMBOL_REGISTRY)}")
        print(f"   - Aster compatible: {aster_compatible_count}")

        # Show some examples
        print(f"\n📊 Sample Aster-compatible symbols:")
        for key, data in list(SYMBOL_REGISTRY.items())[:5]:
            if data.get('aster_compatible'):
                print(f"   - {data['ggshot']:15} aster_compatible={data.get('aster_compatible')}")

    except Exception as e:
        print(f"❌ Error importing registry: {e}")
        print(f"   You may need to manually check the file for syntax errors")


if __name__ == '__main__':
    print("="*80)
    print("UPDATE REGISTRY WITH ASTER COMPATIBILITY FLAGS")
    print("="*80)
    print()

    response = input(f"This will modify core/symbols/registry.py. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        sys.exit(0)

    update_registry()

    print("\n" + "="*80)
    print("✅ DONE")
    print("="*80)
    print()
    print("Next steps:")
    print("1. Review the changes: git diff core/symbols/registry.py")
    print("2. Update aster_service_v3.py to check aster_compatible")
    print("3. Test with: python scripts/cross_reference_aster_symbols.py")
    print()
