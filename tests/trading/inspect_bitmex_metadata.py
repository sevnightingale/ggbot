#!/usr/bin/env python
"""
BitMEX Metadata Inspector

This script extracts official exchange metadata from CCXT to understand
BitMEX's actual limits, precision requirements, and capabilities.

This will form the foundation for creating data-driven exchange guides
instead of guessing exchange rules.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from pprint import pprint

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set environment for testnet
os.environ["TESTNET"] = "1"
os.environ["EXCHANGE_NAME"] = "bitmex"

def inspect_bitmex_describe():
    """
    Inspect BitMEX exchange.describe() to get official metadata.
    """
    try:
        import ccxt
        
        # Create BitMEX exchange instance
        print("🔍 Creating BitMEX exchange instance...")
        bitmex = ccxt.bitmex()
        
        # Set sandbox mode for testnet
        bitmex.set_sandbox_mode(True)
        print("✅ BitMEX testnet mode enabled")
        
        # Get the describe() metadata
        print("\n📋 Getting exchange.describe() metadata...")
        describe_data = bitmex.describe()
        
        print("\n" + "="*60)
        print("BITMEX EXCHANGE METADATA FROM describe()")
        print("="*60)
        
        # Key sections to examine
        sections = {
            'id': 'Exchange ID',
            'name': 'Exchange Name',
            'countries': 'Supported Countries',
            'version': 'API Version',
            'rateLimit': 'Rate Limit (ms)',
            'has': 'Capabilities',
            'requiredCredentials': 'Required Credentials',
            'timeframes': 'Supported Timeframes',
            'urls': 'API URLs',
            'api': 'API Endpoints',
            'fees': 'Fee Structure',
            'precisionMode': 'Precision Mode',
            'precision': 'Default Precision',
            'limits': 'Default Limits',
            'options': 'Exchange Options',
            'exceptions': 'Error Code Mappings'
        }
        
        for key, description in sections.items():
            if key in describe_data:
                print(f"\n🔧 {description} ({key}):")
                if key == 'has':
                    # Special formatting for capabilities
                    capabilities = describe_data[key]
                    for cap, supported in capabilities.items():
                        status = "✅" if supported else "❌"
                        print(f"  {status} {cap}: {supported}")
                elif key == 'limits':
                    # Special formatting for limits
                    limits = describe_data[key]
                    for limit_type, limit_data in limits.items():
                        print(f"  📏 {limit_type}: {limit_data}")
                elif key == 'precision':
                    # Special formatting for precision
                    precision = describe_data[key]
                    for prec_type, prec_data in precision.items():
                        print(f"  🎯 {prec_type}: {prec_data}")
                elif key == 'requiredCredentials':
                    # Special formatting for credentials
                    creds = describe_data[key]
                    for cred, required in creds.items():
                        status = "✅ Required" if required else "❌ Optional"
                        print(f"  {status} {cred}")
                elif key == 'urls':
                    # Special formatting for URLs
                    urls = describe_data[key]
                    for url_type, url_data in urls.items():
                        if isinstance(url_data, dict):
                            print(f"  🌐 {url_type}:")
                            for sub_type, url in url_data.items():
                                print(f"    {sub_type}: {url}")
                        else:
                            print(f"  🌐 {url_type}: {url_data}")
                elif key in ['api', 'fees', 'exceptions']:
                    # These can be large, show summary
                    data = describe_data[key]
                    if isinstance(data, dict):
                        print(f"  📦 Contains {len(data)} entries")
                        # Show first few keys as example
                        for i, (sub_key, sub_data) in enumerate(data.items()):
                            if i >= 3:
                                print(f"  ... and {len(data) - 3} more")
                                break
                            print(f"    {sub_key}: {type(sub_data).__name__}")
                else:
                    # Default formatting
                    data = describe_data[key]
                    if isinstance(data, (dict, list)) and len(str(data)) > 200:
                        print(f"  📦 {type(data).__name__} with {len(data)} items")
                    else:
                        print(f"  {data}")
            else:
                print(f"\n❓ {description} ({key}): Not available")
        
        # Save full describe data to file for detailed analysis
        output_file = Path(__file__).parent / "bitmex_describe_output.json"
        with open(output_file, 'w') as f:
            json.dump(describe_data, f, indent=2, default=str)
        print(f"\n💾 Full describe() output saved to: {output_file}")
        
        return describe_data
        
    except ImportError:
        print("❌ CCXT library not found. Install with: pip install ccxt")
        return None
    except Exception as e:
        print(f"❌ Error inspecting BitMEX metadata: {e}")
        import traceback
        traceback.print_exc()
        return None

def inspect_bitmex_markets():
    """
    Inspect BitMEX fetch_markets() to get per-symbol metadata.
    """
    try:
        import ccxt
        
        # Create BitMEX exchange instance
        print("\n🔍 Getting BitMEX markets data...")
        bitmex = ccxt.bitmex()
        bitmex.set_sandbox_mode(True)
        
        # Get markets data
        markets = bitmex.fetch_markets()
        
        print(f"\n📊 Found {len(markets)} markets on BitMEX testnet")
        
        print("\n" + "="*60)
        print("BITMEX MARKETS METADATA FROM fetch_markets()")
        print("="*60)
        
        # Focus on key symbols for our trading
        key_symbols = ['BTC/USD:BTC', 'ETH/USD:BTC', 'XRP/USD:BTC']
        
        for market in markets:
            if market['symbol'] in key_symbols:
                print(f"\n🪙 {market['symbol']} ({market.get('type', 'unknown')} market)")
                
                # Key fields to examine
                fields = [
                    'active', 'base', 'quote', 'settle', 'baseId', 'quoteId', 'settleId',
                    'type', 'spot', 'margin', 'future', 'option', 'contract', 'linear', 'inverse',
                    'contractSize', 'expiry', 'expiryDatetime', 'strike', 'optionType',
                    'precision', 'limits', 'info'
                ]
                
                for field in fields:
                    if field in market and market[field] is not None:
                        value = market[field]
                        if field == 'precision':
                            print(f"  🎯 {field}:")
                            for prec_type, prec_val in value.items():
                                print(f"    {prec_type}: {prec_val}")
                        elif field == 'limits':
                            print(f"  📏 {field}:")
                            for limit_type, limit_data in value.items():
                                if isinstance(limit_data, dict):
                                    print(f"    {limit_type}:")
                                    for sub_type, sub_val in limit_data.items():
                                        print(f"      {sub_type}: {sub_val}")
                                else:
                                    print(f"    {limit_type}: {limit_data}")
                        elif field == 'info':
                            # Info can be large, show summary
                            print(f"  ℹ️  {field}: {len(value)} raw API fields")
                        else:
                            print(f"  📝 {field}: {value}")
        
        # Save markets data to file
        output_file = Path(__file__).parent / "bitmex_markets_output.json"
        with open(output_file, 'w') as f:
            json.dump(markets, f, indent=2, default=str)
        print(f"\n💾 Full markets data saved to: {output_file}")
        
        return markets
        
    except Exception as e:
        print(f"❌ Error getting BitMEX markets: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_key_insights(describe_data, markets_data):
    """
    Extract key insights for building exchange guides.
    """
    print("\n" + "="*60)
    print("KEY INSIGHTS FOR EXCHANGE GUIDE")
    print("="*60)
    
    insights = {}
    
    if describe_data:
        print("\n🎯 From exchange.describe():")
        
        # Capabilities
        has = describe_data.get('has', {})
        supported_features = [feature for feature, supported in has.items() if supported]
        print(f"  ✅ Supported features: {', '.join(supported_features[:10])}...")
        insights['supported_features'] = supported_features
        
        # Required credentials
        req_creds = describe_data.get('requiredCredentials', {})
        required = [cred for cred, needed in req_creds.items() if needed]
        print(f"  🔑 Required credentials: {', '.join(required)}")
        insights['required_credentials'] = required
        
        # Rate limits
        rate_limit = describe_data.get('rateLimit')
        if rate_limit:
            print(f"  ⏱️  Rate limit: {rate_limit}ms between requests")
            insights['rate_limit'] = rate_limit
        
        # Default limits
        limits = describe_data.get('limits', {})
        if limits:
            print(f"  📏 Default limits: {limits}")
            insights['default_limits'] = limits
            
        # Options
        options = describe_data.get('options', {})
        if options:
            print(f"  ⚙️  Exchange options: {list(options.keys())}")
            insights['options'] = options
    
    if markets_data:
        print(f"\n🪙 From fetch_markets() ({len(markets_data)} markets):")
        
        # Contract types
        contract_types = set()
        for market in markets_data:
            if market.get('type'):
                contract_types.add(market['type'])
        print(f"  📊 Contract types: {', '.join(contract_types)}")
        insights['contract_types'] = list(contract_types)
        
        # Check specific symbols we care about
        key_symbols = ['BTC/USD:BTC', 'ETH/USD:BTC']
        for symbol in key_symbols:
            market = next((m for m in markets_data if m['symbol'] == symbol), None)
            if market:
                min_amount = market.get('limits', {}).get('amount', {}).get('min')
                if min_amount:
                    print(f"  💰 {symbol} minimum amount: {min_amount}")
                    insights[f'{symbol}_min_amount'] = min_amount
    
    # Save insights
    output_file = Path(__file__).parent / "bitmex_insights.json"
    with open(output_file, 'w') as f:
        json.dump(insights, f, indent=2, default=str)
    print(f"\n💾 Key insights saved to: {output_file}")
    
    return insights

def main():
    """Main function to run the BitMEX metadata inspection."""
    print("🚀 BitMEX Metadata Inspector")
    print("="*60)
    print("Extracting official exchange metadata from CCXT...")
    
    # Phase 1: Get exchange.describe() metadata
    describe_data = inspect_bitmex_describe()
    
    # Phase 2: Get fetch_markets() metadata  
    markets_data = inspect_bitmex_markets()
    
    # Phase 3: Extract key insights
    if describe_data or markets_data:
        insights = extract_key_insights(describe_data, markets_data)
        
        print("\n✅ Metadata inspection complete!")
        print("📁 Output files created:")
        print("  - bitmex_describe_output.json (full describe() data)")
        print("  - bitmex_markets_output.json (full markets data)")  
        print("  - bitmex_insights.json (key insights summary)")
        print("\nNext step: Use this data to design empirical error testing!")
    else:
        print("\n❌ Failed to get metadata. Check CCXT installation and connection.")

if __name__ == "__main__":
    main()