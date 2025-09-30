#!/usr/bin/env python3
"""
Test script for the Decision Module.

This script tests the decision-making process using real market data
from the database.
"""

import asyncio
import sys
sys.path.append('/home/sev/ggbot')

from core.common.config import DEFAULT_USER_ID
from core.common.logger import logger
from decision import run_decision_process


async def test_decision_module():
    """Test the decision module with real data."""
    
    print("=== Testing Decision Module ===\n")
    
    # Test parameters
    user_id = DEFAULT_USER_ID
    config_name = 'default'
    symbol = 'BTC/USD'
    timeframes = ['15m', '1h', '4h']
    
    print(f"User ID: {user_id}")
    print(f"Config Name: {config_name}")
    print(f"Symbol: {symbol}")
    print(f"Timeframes: {timeframes}")
    print("\nRunning decision process...\n")
    
    try:
        # Run the decision process
        intent = await run_decision_process(
            user_id=user_id,
            config_name=config_name,
            symbol=symbol,
            timeframes=timeframes
        )
        
        # Display results
        print("=== Decision Result ===")
        print(f"Action: {intent.get('action')}")
        print(f"Confidence: {intent.get('confidence')}")
        
        if intent.get('action') == 'error':
            print(f"Error: {intent.get('error')}")
        else:
            if intent.get('action') == 'open_position':
                print(f"Side: {intent.get('side')}")
                print(f"Position Size: {intent.get('position_size', 0) * 100:.1f}%")
                print(f"Leverage: {intent.get('leverage')}x")
                print(f"Stop Loss: {intent.get('stop_loss', 'Not set')}")
                print(f"Take Profit: {intent.get('take_profit', 'Not set')}")
            elif intent.get('action') in ['close_position', 'adjust_position']:
                print(f"Trade ID: {intent.get('trade_id')}")
                if intent.get('adjustments'):
                    print(f"Adjustments: {intent.get('adjustments')}")
            
            print(f"\nReasoning: {intent.get('reasoning', 'No reasoning provided')[:300]}...")
            
            if intent.get('metadata'):
                print(f"\nMetadata:")
                print(f"- Model: {intent['metadata'].get('model', 'Unknown')}")
                print(f"- Latency: {intent['metadata'].get('latency', 0):.2f}s")
                print(f"- Tokens: {intent['metadata'].get('usage', {}).get('total_tokens', 'Unknown')}")
        
        print("\n=== Test Complete ===")
        return intent
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\nTest failed with error: {str(e)}")
        return None


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_decision_module())
    
    # Exit with appropriate code
    if result and result.get('action') != 'error':
        sys.exit(0)
    else:
        sys.exit(1)