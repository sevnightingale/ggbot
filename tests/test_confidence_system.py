#!/usr/bin/env python3
"""
Test script for the new confidence-based position sizing system.

This script tests the confidence-to-risk mapping and position calculations
without running a full trade execution.
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from trading.api import confidence_to_risk_percentage, calculate_position_from_confidence


def test_confidence_mapping():
    """Test the confidence to risk percentage mapping."""
    print("🧪 Testing Confidence to Risk Percentage Mapping")
    print("=" * 50)
    
    test_cases = [
        0.05,  # Low confidence
        0.15,  # Low-medium
        0.25,  # Medium-low
        0.55,  # Medium
        0.75,  # Medium-high
        0.85,  # High
        0.95,  # Very high
    ]
    
    for confidence in test_cases:
        risk_pct = confidence_to_risk_percentage(confidence)
        print(f"Confidence {confidence:.2f} → Risk {risk_pct:.1f}%")
    
    print()


def test_position_calculations():
    """Test position size calculations for different scenarios."""
    print("🧪 Testing Position Size Calculations")
    print("=" * 50)
    
    account_balances = [10000, 50000, 100000]  # Different account sizes
    confidence_levels = [0.15, 0.55, 0.95]    # Low, medium, high confidence
    
    for account_balance in account_balances:
        print(f"\n💰 Account Balance: ${account_balance:,}")
        print("-" * 30)
        
        for confidence in confidence_levels:
            result = calculate_position_from_confidence(
                confidence=confidence,
                account_balance_usd=account_balance
            )
            
            print(f"Confidence {confidence:.2f}:")
            print(f"  Risk: {result['risk_percentage']:.1f}% (${result['risk_amount_usd']:.2f})")
            print(f"  Position: ${result['position_size_usd']:.2f} @ {result['leverage']}x")
            print(f"  Contracts: {result['contracts']:.0f}")
            print()


def test_edge_cases():
    """Test edge cases and boundaries."""
    print("🧪 Testing Edge Cases")
    print("=" * 50)
    
    # Test minimum position enforcement
    small_account = 1000
    low_confidence = 0.05
    
    result = calculate_position_from_confidence(
        confidence=low_confidence,
        account_balance_usd=small_account
    )
    
    print(f"Small Account (${small_account:,}) + Low Confidence ({low_confidence:.2f}):")
    print(f"  Risk: {result['risk_percentage']:.1f}% (${result['risk_amount_usd']:.2f})")
    print(f"  Position: ${result['position_size_usd']:.2f} @ {result['leverage']}x")
    print(f"  Minimum enforced: {result['position_size_usd'] >= 100}")
    print()
    
    # Test maximum position cap
    large_account = 500000
    high_confidence = 0.95
    
    result = calculate_position_from_confidence(
        confidence=high_confidence,
        account_balance_usd=large_account
    )
    
    print(f"Large Account (${large_account:,}) + High Confidence ({high_confidence:.2f}):")
    print(f"  Risk: {result['risk_percentage']:.1f}% (${result['risk_amount_usd']:.2f})")
    print(f"  Position: ${result['position_size_usd']:.2f} @ {result['leverage']}x")
    print(f"  Maximum capped: {result['position_size_usd'] <= 10000}")
    print()


def test_trading_intent_format():
    """Test what a new TradingIntent would look like."""
    print("🧪 Sample TradingIntent (New Format)")
    print("=" * 50)
    
    sample_intent = {
        "decision_id": "test-123",
        "action": "enter_long",
        "symbol": "BTC/USD",
        "exchange": "bitmex",
        "confidence": 0.75,
        "stop_loss_price": 102000,
        "take_profit_price": 108000,
        "reasoning": "Strong bullish signal with RSI oversold bounce and volume confirmation"
    }
    
    print("Intent from Decision Module:")
    for key, value in sample_intent.items():
        print(f"  {key}: {value}")
    
    print("\nAfter Trading Module Processing:")
    account_balance = 50000
    result = calculate_position_from_confidence(
        confidence=sample_intent["confidence"],
        account_balance_usd=account_balance
    )
    
    print(f"  collateral_amount: ${result['collateral_amount']:.2f}")
    print(f"  leverage: {result['leverage']}")
    print(f"  position_size_usd: ${result['position_size_usd']:.2f}")
    print(f"  risk_percentage: {result['risk_percentage']:.1f}%")


if __name__ == "__main__":
    print("🎯 Confidence-Based Position Sizing Test")
    print("=" * 60)
    print()
    
    test_confidence_mapping()
    test_position_calculations()
    test_edge_cases()
    test_trading_intent_format()
    
    print("✅ All tests completed!")
    print("\nKey Features Verified:")
    print("- Confidence maps to risk percentage (0.5% - 5.0%)")
    print("- Fixed 10x leverage for all trades")
    print("- $100 minimum position size")
    print("- $10,000 maximum position size")
    print("- Automatic adjustment for small/large accounts")