#!/usr/bin/env python3
"""
Get the full BollingerBandsWidth error message.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parents[1]))

from core.mcp.indicators import IndicatorsMCPClient

async def get_full_bbw_error():
    """Get the complete error message for BollingerBandsWidth."""
    
    mcp_client = IndicatorsMCPClient()
    
    try:
        await mcp_client.connect()
        
        # Call the failing tool
        result = await mcp_client.session.call_tool('calculate_bollinger_bands_width', {
            "symbol": "BTC/USDT",
            "timeframe": "1h"
        })
        
        print("Full BollingerBandsWidth result:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        # Try to extract the error text
        if hasattr(result, 'content') and result.content:
            for content in result.content:
                if hasattr(content, 'text'):
                    print(f"\nError text: {content.text}")
                    
    except Exception as e:
        print(f"Exception: {str(e)}")
        
    finally:
        await mcp_client.disconnect()

if __name__ == "__main__":
    asyncio.run(get_full_bbw_error())