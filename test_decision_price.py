#!/usr/bin/env python
"""
Test the decision engine with the new PriceService.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from decision.engine import DecisionEngine
from core.common.logging_config import setup_logging, logger

async def test_decision_price():
    """Test the decision engine price fetching."""
    print("🚀 Testing DecisionEngine with new PriceService...")
    
    # Use test user and config
    user_id = "00000000-0000-0000-0000-000000000001"
    config_id = "a93de31b-9b8a-42e3-827d-c31e580f5f36"
    
    try:
        # Create decision engine
        engine = DecisionEngine(user_id, config_id)
        
        # Override config for testing with single source fallback
        await engine.initialize()
        
        # Allow single source for testing (YFinance is rate limited)
        engine.price_service.allow_single_source = True
        print(f"✓ Enabled single-source fallback (YFinance rate limited)")
        
        print(f"\n💰 Testing price fetching with new PriceService...")
        
        # Test current price fetch (this was broken before)
        symbol = "BTC/USDT"
        price = await engine._fetch_current_price(symbol)
        print(f"✅ Current {symbol} price: ${price:,.2f}")
        
        # Compare with the old broken testnet price of ~$95k
        if price > 100000:
            print(f"🎉 SUCCESS! Real market price ${price:,.2f} vs broken testnet ~$95k")
        else:
            print(f"⚠️ Price seems low: ${price:,.2f}")
        
        print(f"\n✅ DecisionEngine price test completed!")
        
    except Exception as e:
        print(f"❌ DecisionEngine test failed: {e}")
        raise

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    
    # Run the test
    asyncio.run(test_decision_price())