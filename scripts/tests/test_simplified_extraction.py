#!/usr/bin/env python
"""
Test script for the simplified extraction module.

This verifies that the MCP-only extraction works correctly after
removing deprecated YFinance and TradingView code.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.extraction_main import extract_mcp_indicators


async def test_extraction():
    """Test the simplified MCP extraction."""
    print("=== Testing Simplified Extraction Module ===\n")
    
    # Check for required environment variable
    if not os.environ.get("TRADING_LLM_API_KEY"):
        print("❌ Error: TRADING_LLM_API_KEY environment variable not set")
        print("   Please set: export TRADING_LLM_API_KEY=your_openai_api_key")
        return False
    
    # Test parameters
    symbols = ["BTC/USDT"]
    timeframes = ["1h"]
    
    print(f"Testing extraction for {symbols} on {timeframes}...")
    
    try:
        # Run the extraction
        results = await extract_mcp_indicators(
            symbols=symbols,
            timeframes=timeframes,
            use_llm=True,
            llm_model="gpt-4o-mini"
        )
        
        # Check results
        if "error" in results:
            print(f"❌ Extraction failed: {results['error']}")
            return False
        
        # Verify structure
        for symbol in symbols:
            if symbol not in results:
                print(f"❌ Missing results for {symbol}")
                return False
            
            for timeframe in timeframes:
                if timeframe not in results[symbol]:
                    print(f"❌ Missing results for {symbol} {timeframe}")
                    return False
                
                result = results[symbol][timeframe]
                if result.get("status") != "success":
                    print(f"❌ Extraction failed for {symbol} {timeframe}: {result.get('error')}")
                    return False
                
                # Check for expected fields
                if "indicators" not in result:
                    print(f"❌ Missing indicators for {symbol} {timeframe}")
                    return False
                
                if "interpretation" not in result:
                    print(f"❌ Missing interpretation for {symbol} {timeframe}")
                    return False
                
                interpretation = result["interpretation"]
                print(f"\n✓ {symbol} {timeframe}:")
                print(f"  Sentiment: {interpretation.get('sentiment', 'N/A')}")
                print(f"  Strength: {interpretation.get('strength', 'N/A')}")
                print(f"  Risk Level: {interpretation.get('risk_level', 'N/A')}")
                print(f"  Confidence: {interpretation.get('confidence', 0):.2f}")
                print(f"  Indicators calculated: {len(result['indicators'])}")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """Test that deprecated imports have been removed."""
    print("Testing that deprecated imports are removed...")
    
    try:
        # This should fail now
        from extraction.sources import YFinanceDataSource
        print("❌ YFinanceDataSource import should have been removed!")
        return False
    except ImportError:
        print("✓ YFinanceDataSource import correctly removed")
    
    try:
        # This should fail now
        from extraction.indicators import PandasTAIndicators
        print("❌ PandasTAIndicators import should have been removed!")
        return False
    except ImportError:
        print("✓ PandasTAIndicators import correctly removed")
    
    # Test that extraction_main only has the MCP function
    from extraction import extraction_main
    
    if hasattr(extraction_main, 'ExtractionManager'):
        print("❌ ExtractionManager class should have been removed!")
        return False
    else:
        print("✓ ExtractionManager class correctly removed")
    
    if not hasattr(extraction_main, 'extract_mcp_indicators'):
        print("❌ extract_mcp_indicators function is missing!")
        return False
    else:
        print("✓ extract_mcp_indicators function exists")
    
    return True


async def main():
    """Run all tests."""
    print("=== Simplified Extraction Module Test Suite ===\n")
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import tests failed!")
        return
    
    print("\n" + "="*50 + "\n")
    
    # Test extraction functionality
    success = await test_extraction()
    
    if success:
        print("\n=== All tests completed successfully! ===")
    else:
        print("\n=== Some tests failed! ===")


if __name__ == "__main__":
    asyncio.run(main())