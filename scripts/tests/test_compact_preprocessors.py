#!/usr/bin/env python3
"""
Test script for validating compact preprocessor implementations.

Run after implementing each preprocessor's to_compact() method:
    python scripts/tests/test_compact_preprocessors.py

Validates:
1. All preprocessors have to_compact() method (at least fallback)
2. Output matches universal schema
3. All values are JSON-serializable
4. Size is reasonable (<600 bytes per indicator)
5. Pattern codes are from approved list
"""

import json
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

# Add project root to path
sys.path.insert(0, '/home/sev/ggbot')

from extraction.v2.preprocessors import get_preprocessor, list_available_preprocessors
from extraction.v2.preprocessors.compact_config import PATTERN_CODES, REI_INDICATOR_TIMEFRAMES


# =============================================================================
# TEST DATA GENERATORS
# =============================================================================

def create_test_series(length: int = 100, base: float = 50, volatility: float = 5) -> pd.Series:
    """Create a random test series."""
    np.random.seed(42)
    values = [base]
    for _ in range(length - 1):
        change = np.random.normal(0, volatility)
        values.append(values[-1] + change)
    return pd.Series(values)


def create_price_series(length: int = 100) -> pd.Series:
    """Create a test price series."""
    np.random.seed(42)
    prices = [100000]  # BTC-like price
    for _ in range(length - 1):
        change = np.random.normal(0, 500)
        prices.append(prices[-1] + change)
    return pd.Series(prices)


def create_indicator_test_data(indicator_name: str) -> Dict[str, Any]:
    """Create appropriate test data for each indicator type."""
    prices = create_price_series()

    if indicator_name in ['rsi', 'cci', 'mfi', 'williams_r']:
        # Bounded oscillators
        return {
            'primary': create_test_series(base=50, volatility=10),
            'prices': prices
        }
    elif indicator_name == 'stochastic':
        return {
            'k_percent': create_test_series(base=50, volatility=15),
            'd_percent': create_test_series(base=50, volatility=10),
            'prices': prices
        }
    elif indicator_name == 'macd':
        return {
            'macd_line': create_test_series(base=100, volatility=50),
            'signal_line': create_test_series(base=80, volatility=40),
            'histogram': create_test_series(base=20, volatility=30),
            'prices': prices
        }
    elif indicator_name in ['bbands', 'keltner', 'donchian']:
        return {
            'upper': create_test_series(base=102000, volatility=500),
            'middle': create_test_series(base=100000, volatility=400),
            'lower': create_test_series(base=98000, volatility=500),
            'prices': prices
        }
    elif indicator_name == 'adx':
        return {
            'adx': create_test_series(base=25, volatility=5),
            'plus_di': create_test_series(base=25, volatility=5),
            'minus_di': create_test_series(base=20, volatility=5),
            'prices': prices
        }
    elif indicator_name == 'aroon':
        return {
            'aroon_up': create_test_series(base=60, volatility=20),
            'aroon_down': create_test_series(base=40, volatility=20),
            'prices': prices
        }
    elif indicator_name == 'vortex':
        return {
            'vi_plus': create_test_series(base=1.1, volatility=0.1),
            'vi_minus': create_test_series(base=0.9, volatility=0.1),
            'prices': prices
        }
    elif indicator_name in ['obv']:
        return {
            'obv': create_test_series(base=1000000, volatility=50000),
            'prices': prices,
            'volumes': create_test_series(base=10000, volatility=2000)
        }
    elif indicator_name == 'vwap':
        return {
            'vwap': create_test_series(base=100000, volatility=200),
            'prices': prices,
            'volumes': create_test_series(base=10000, volatility=2000)
        }
    else:
        # Default for simple indicators (ATR, EMA, SMA, ROC, TRIX, etc.)
        return {
            'primary': create_test_series(base=100, volatility=10),
            'prices': prices
        }


# =============================================================================
# SCHEMA VALIDATION
# =============================================================================

REQUIRED_FIELDS = {
    'indicator': str,
    'timeframe': str,
    'timestamp': (str, type(None)),
    'value': (float, int, type(None)),
    'value_secondary': (float, int, type(None)),
    'value_tertiary': (float, int, type(None)),
    'velocity': (float, int),
    'rank': (float, int),
    'zone': str,
    'zone_periods': (int, type(None)),
    'trend': str,
    'crossover_type': (str, type(None)),
    'crossover_periods_ago': (int, type(None)),
    'patterns': list,
    'analysis': str,
}


def validate_schema(compact_output: Dict[str, Any], indicator_name: str) -> List[str]:
    """Validate compact output matches universal schema."""
    errors = []

    # Check required fields
    for field, expected_types in REQUIRED_FIELDS.items():
        if field not in compact_output:
            errors.append(f"Missing required field: {field}")
            continue

        value = compact_output[field]
        if not isinstance(value, expected_types):
            errors.append(f"Field '{field}' has wrong type: expected {expected_types}, got {type(value)}")

    # Check indicator name matches
    if compact_output.get('indicator', '').lower() != indicator_name.lower():
        errors.append(f"Indicator name mismatch: expected '{indicator_name}', got '{compact_output.get('indicator')}'")

    # Check patterns are valid codes
    patterns = compact_output.get('patterns', [])
    for pattern in patterns:
        if pattern not in PATTERN_CODES:
            errors.append(f"Unknown pattern code: '{pattern}'")

    return errors


def validate_json_serializable(compact_output: Dict[str, Any]) -> List[str]:
    """Ensure output is JSON serializable (no numpy types)."""
    errors = []
    try:
        json.dumps(compact_output, default=str)
    except Exception as e:
        errors.append(f"JSON serialization failed: {e}")

    # Check for numpy types explicitly
    def check_numpy(obj, path=""):
        if isinstance(obj, (np.integer, np.floating, np.ndarray)):
            errors.append(f"Numpy type found at {path}: {type(obj)}")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                check_numpy(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                check_numpy(v, f"{path}[{i}]")

    check_numpy(compact_output)
    return errors


def validate_size(compact_output: Dict[str, Any], max_bytes: int = 600) -> List[str]:
    """Ensure compact output is reasonably sized."""
    errors = []
    size = len(json.dumps(compact_output, default=str))
    if size > max_bytes:
        errors.append(f"Output too large: {size} bytes (max {max_bytes})")
    return errors


# =============================================================================
# PREPROCESSOR TESTING
# =============================================================================

def test_preprocessor(indicator_name: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Test a single preprocessor's to_compact() implementation.

    Returns:
        (success, errors, compact_output)
    """
    errors = []
    compact_output = None

    try:
        # Get preprocessor
        preprocessor = get_preprocessor(indicator_name)
        if preprocessor is None:
            return False, [f"Preprocessor not found: {indicator_name}"], None

        # Check for to_compact method
        if not hasattr(preprocessor, 'to_compact'):
            return False, [f"No to_compact() method found"], None

        # Get test data
        test_data = create_indicator_test_data(indicator_name)

        # Generate full output based on indicator type
        if indicator_name in ['rsi', 'cci', 'mfi', 'williams_r']:
            full_output = preprocessor.preprocess(
                test_data['primary'],
                test_data['prices']
            )
        elif indicator_name == 'stochastic':
            full_output = preprocessor.preprocess(
                test_data['k_percent'],
                test_data['d_percent'],
                test_data['prices']
            )
        elif indicator_name == 'macd':
            full_output = preprocessor.preprocess(
                test_data['macd_line'],
                test_data['signal_line'],
                test_data['histogram'],
                test_data['prices']
            )
        elif indicator_name in ['bbands', 'keltner', 'donchian']:
            full_output = preprocessor.preprocess(
                test_data['upper'],
                test_data['middle'],
                test_data['lower'],
                test_data['prices']
            )
        elif indicator_name == 'adx':
            full_output = preprocessor.preprocess(
                test_data['adx'],
                test_data['plus_di'],
                test_data['minus_di'],
                test_data['prices']
            )
        elif indicator_name == 'aroon':
            full_output = preprocessor.preprocess(
                test_data['aroon_up'],
                test_data['aroon_down'],
                test_data['prices']
            )
        elif indicator_name == 'vortex':
            full_output = preprocessor.preprocess(
                test_data['vi_plus'],
                test_data['vi_minus'],
                test_data['prices']
            )
        elif indicator_name == 'obv':
            full_output = preprocessor.preprocess(
                test_data['obv'],
                test_data['prices'],
                test_data['volumes']
            )
        elif indicator_name == 'vwap':
            full_output = preprocessor.preprocess(
                test_data['vwap'],
                test_data['prices'],
                test_data['volumes']
            )
        else:
            # Default single-series indicators
            full_output = preprocessor.preprocess(
                test_data['primary'],
                test_data['prices']
            )

        if 'error' in full_output:
            return False, [f"Preprocessor returned error: {full_output['error']}"], None

        # Convert to compact
        compact_output = preprocessor.to_compact(full_output, "1h")

        # Validate schema
        schema_errors = validate_schema(compact_output, indicator_name)
        errors.extend(schema_errors)

        # Validate JSON serializable
        json_errors = validate_json_serializable(compact_output)
        errors.extend(json_errors)

        # Validate size
        size_errors = validate_size(compact_output)
        errors.extend(size_errors)

    except Exception as e:
        import traceback
        errors.append(f"Exception: {e}\n{traceback.format_exc()}")

    success = len(errors) == 0
    return success, errors, compact_output


def run_all_tests():
    """Run tests for all available preprocessors."""
    print("=" * 70)
    print("COMPACT PREPROCESSOR VALIDATION")
    print("=" * 70)
    print()

    available = list_available_preprocessors()
    print(f"Found {len(available)} preprocessors: {', '.join(available)}")
    print()

    results = {
        'passed': [],
        'failed': [],
        'fallback': [],  # Using base class fallback
    }

    for indicator in sorted(available):
        success, errors, compact = test_preprocessor(indicator)

        # Check if using fallback (base class to_compact)
        preprocessor = get_preprocessor(indicator)
        is_fallback = not hasattr(preprocessor.__class__, 'to_compact') or \
                      preprocessor.__class__.to_compact == preprocessor.__class__.__bases__[0].to_compact

        if success:
            if is_fallback:
                status = "⚠️  FALLBACK"
                results['fallback'].append(indicator)
            else:
                status = "✅ PASS"
                results['passed'].append(indicator)

            size = len(json.dumps(compact, default=str)) if compact else 0
            print(f"{status:12} {indicator:15} ({size} bytes)")
        else:
            status = "❌ FAIL"
            results['failed'].append(indicator)
            print(f"{status:12} {indicator:15}")
            for error in errors[:3]:  # Show first 3 errors
                print(f"             └─ {error}")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Implemented:  {len(results['passed'])} ({', '.join(results['passed']) or 'none'})")
    print(f"⚠️  Fallback:     {len(results['fallback'])} ({', '.join(results['fallback']) or 'none'})")
    print(f"❌ Failed:       {len(results['failed'])} ({', '.join(results['failed']) or 'none'})")
    print()

    # Calculate payload estimate
    total_combos = 0
    for indicator in available:
        tfs = REI_INDICATOR_TIMEFRAMES.get(indicator, ['1h', '4h'])
        total_combos += len(tfs)

    estimated_size = total_combos * 450  # Average ~450 bytes
    print(f"Estimated Rei payload: {total_combos} indicator-timeframes × ~450 bytes = ~{estimated_size/1024:.1f}KB")
    print(f"Rei limit: 30KB → {'✅ FITS' if estimated_size < 30000 else '❌ TOO BIG'}")

    return len(results['failed']) == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
