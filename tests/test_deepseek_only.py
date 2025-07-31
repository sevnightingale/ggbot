#!/usr/bin/env python3
"""
Test DeepSeek parsing issue in isolation
"""

import asyncio
from ggshot.test_llm_providers import get_llm_provider, parse_llm_response

async def test_deepseek_parsing():
    """Test DeepSeek API call and response parsing"""
    
    # Sample response with the formatting issue
    sample_response = """### FINAL OUTPUT
**ACTION:** validate
**CONFIDENCE:** 0.170
**STOP_LOSS:** 0.5620
**TAKE_PROFIT:** 0.4480

### REASONING
This is a test response."""
    
    print("Testing response parsing...")
    result = parse_llm_response(sample_response)
    print(f"Parsed confidence: {result['confidence']}")
    print(f"Expected: 0.170")
    print(f"Match: {result['confidence'] == 0.170}")
    
    # Test actual API call
    print("\nTesting DeepSeek API call...")
    try:
        provider = get_llm_provider("deepseek", "deepseek-reasoner")
        response = await provider.generate_response("Say 'Hello' and give CONFIDENCE: 0.123")
        print(f"API Response: {response['content'][:200]}...")
        
        parsed = parse_llm_response(response['content'])
        print(f"Parsed result: {parsed}")
        
    except Exception as e:
        print(f"DeepSeek API Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_deepseek_parsing())