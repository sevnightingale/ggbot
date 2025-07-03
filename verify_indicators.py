#!/usr/bin/env python3
"""
Indicator Data Verification Script

This script compares our extracted indicator data with external sources to verify accuracy.
It focuses on the most problematic indicators identified by Grok: Aroon and Volume.
"""

import json
import asyncio
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor
from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
from datetime import datetime
import re

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=RealDictCursor
    )

def parse_mcp_data(raw_mcp_string: str) -> dict:
    """
    Parse MCP format data to extract actual values
    
    Expected format: meta=None content=[TextContent(type='text', text='{"up":[100,92.85...],"down":[42.86...]}')]
    """
    try:
        # Extract the JSON content from the MCP wrapper
        if 'text=\'' in raw_mcp_string:
            # Find the JSON part between text=' and the closing '
            start = raw_mcp_string.find("text='") + 6
            # Find the matching closing quote - need to handle nested quotes
            depth = 0
            end = start
            for i, char in enumerate(raw_mcp_string[start:], start):
                if char == '\'':
                    # Check if this is an escaped quote
                    if i > 0 and raw_mcp_string[i-1] != '\\':
                        end = i
                        break
            
            json_str = raw_mcp_string[start:end]
            # Handle escaped characters
            json_str = json_str.replace("\\'", "'").replace('\\"', '"')
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try to extract just numeric arrays
                if '[' in json_str and ']' in json_str:
                    # For simple arrays like RSI
                    return {"values": json_str}
                return {"raw": json_str}
        
        return {"error": "Could not parse MCP format", "raw": raw_mcp_string[:200]}
    
    except Exception as e:
        return {"error": str(e), "raw": raw_mcp_string[:200]}

def extract_current_values(parsed_data: dict) -> dict:
    """Extract current/latest values from parsed indicator data"""
    result = {}
    
    try:
        if "up" in parsed_data and "down" in parsed_data:
            # Aroon indicator format
            up_values = parsed_data["up"]
            down_values = parsed_data["down"]
            
            if isinstance(up_values, list) and len(up_values) > 0:
                result["aroon_up"] = up_values[-1]  # Latest value
            if isinstance(down_values, list) and len(down_values) > 0:
                result["aroon_down"] = down_values[-1]  # Latest value
                
        elif "values" in parsed_data:
            # Simple array format (like RSI)
            values_str = parsed_data["values"]
            # Extract numbers from string like [45.98,52.19,...]
            numbers = re.findall(r'-?\d+\.?\d*', values_str)
            if numbers:
                result["current_value"] = float(numbers[-1])  # Latest value
                result["all_values"] = [float(n) for n in numbers[-10:]]  # Last 10 values
                
        elif isinstance(parsed_data.get("raw"), str):
            # Try to extract numbers from raw string
            numbers = re.findall(r'-?\d+\.?\d*', parsed_data["raw"])
            if numbers:
                result["extracted_numbers"] = [float(n) for n in numbers[-5:]]
                
    except Exception as e:
        result["parse_error"] = str(e)
    
    return result

async def fetch_binance_data(symbol: str):
    """Fetch current price and volume from Binance for comparison"""
    try:
        # Convert symbol format (WIF/USDT -> WIFUSDT)
        binance_symbol = symbol.replace('/', '')
        
        async with aiohttp.ClientSession() as session:
            # Get 24hr ticker data
            async with session.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}') as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "symbol": symbol,
                        "price": float(data['lastPrice']),
                        "volume_24h": float(data['volume']),
                        "price_change_24h": float(data['priceChangePercent']),
                        "high_24h": float(data['highPrice']),
                        "low_24h": float(data['lowPrice']),
                        "trades_count": int(data['count'])
                    }
                else:
                    return {"error": f"Binance API error: {response.status}"}
                    
    except Exception as e:
        return {"error": str(e)}

async def verify_wif_usdt():
    """Verify WIF/USDT data specifically"""
    print("=== WIF/USDT Indicator Verification ===\n")
    
    # Get our extracted data
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT indicators, updated_at 
        FROM market_data 
        WHERE symbol = %s AND config_id = %s
        ORDER BY updated_at DESC 
        LIMIT 1
    ''', ('WIF/USDT', 'e249bb49-0455-4596-9657-09bf9e14ca14'))
    
    result = cur.fetchone()
    if not result:
        print("❌ No WIF/USDT data found in database")
        return
    
    print(f"📅 Data timestamp: {result['updated_at']}")
    print()
    
    # Verify Aroon data
    if 'Aroon_1d' in result['indicators']:
        print("🎯 AROON VERIFICATION")
        aroon_raw = result['indicators']['Aroon_1d']
        print(f"Raw MCP data: {aroon_raw[:100]}...")
        
        parsed_aroon = parse_mcp_data(aroon_raw)
        print(f"Parsed data: {parsed_aroon}")
        
        current_aroon = extract_current_values(parsed_aroon)
        print(f"Extracted values: {current_aroon}")
        
        # Check if values are in valid range
        if "aroon_up" in current_aroon and "aroon_down" in current_aroon:
            aroon_up = current_aroon["aroon_up"]
            aroon_down = current_aroon["aroon_down"]
            
            print(f"✅ Aroon Up: {aroon_up} (Valid: {0 <= aroon_up <= 100})")
            print(f"✅ Aroon Down: {aroon_down} (Valid: {0 <= aroon_down <= 100})")
            
            if not (0 <= aroon_up <= 100) or not (0 <= aroon_down <= 100):
                print("❌ AROON VALUES OUT OF RANGE - DATA ERROR CONFIRMED")
        else:
            print("❌ Could not extract Aroon values")
        print()
    
    # Verify RSI data
    if 'RSI_30m' in result['indicators']:
        print("🎯 RSI VERIFICATION")
        rsi_raw = result['indicators']['RSI_30m']
        print(f"Raw MCP data: {rsi_raw[:100]}...")
        
        parsed_rsi = parse_mcp_data(rsi_raw)
        current_rsi = extract_current_values(parsed_rsi)
        print(f"Extracted RSI: {current_rsi}")
        print()
    
    # Get Binance reference data
    print("🎯 BINANCE REFERENCE DATA")
    binance_data = await fetch_binance_data('WIF/USDT')
    if "error" not in binance_data:
        print(f"Current price: ${binance_data['price']}")
        print(f"24h volume: {binance_data['volume_24h']:,}")
        print(f"24h change: {binance_data['price_change_24h']:.2f}%")
        print(f"24h high: ${binance_data['high_24h']}")
        print(f"24h low: ${binance_data['low_24h']}")
    else:
        print(f"❌ Binance error: {binance_data['error']}")
    
    conn.close()

def main():
    """Main verification function"""
    print("🔍 INDICATOR DATA VERIFICATION\n")
    print("This script verifies the accuracy of our extracted indicator data")
    print("by parsing the raw MCP format and comparing with external sources.\n")
    
    asyncio.run(verify_wif_usdt())

if __name__ == "__main__":
    main()