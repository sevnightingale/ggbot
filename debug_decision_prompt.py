#!/usr/bin/env python3
"""
Debug script to see exactly what prompt is being sent to the decision LLM
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from decision.engine import DecisionEngine
from core.common.logger import logger

async def debug_decision_prompt():
    """Debug what prompt is being sent to the LLM"""
    
    user_id = "00000000-0000-0000-0000-000000000001"
    
    try:
        # Get config_id like the API does
        from decision.utils import get_config_id_by_name
        config_id = get_config_id_by_name(user_id, "default")
        
        # Initialize decision engine like the API does
        engine = DecisionEngine(user_id=user_id, config_id=config_id)
        
        # Load configuration (the engine needs this for prompts)
        engine._load_configuration()
        
        # Fetch market data the same way the engine does
        symbol = "BTC/USDT"
        timeframes = ["15m", "1h"]
        
        market_data = engine._fetch_market_data(symbol, timeframes)
        account_state = engine._fetch_account_state()
        
        print("=== MARKET DATA STRUCTURE ===")
        for timeframe, data in market_data.items():
            print(f"\n{timeframe} timeframe:")
            print(f"  indicators: {data['indicators']}")
            print(f"  signals: {data['signals']}")
            print(f"  raw_data: {data.get('raw_data', {})}")
        
        print("\n=== ACCOUNT STATE ===")
        print(account_state)
        
        # Generate the actual prompt that would be sent to LLM
        prompt = engine._format_prompt_new_trade(market_data, account_state, symbol)
        
        print("\n=== FULL PROMPT SENT TO LLM ===")
        print(prompt)
        print("\n=== END PROMPT ===")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_decision_prompt())