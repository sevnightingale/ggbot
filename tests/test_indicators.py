#!/usr/bin/env python3
"""
Extract indicator values from the database and save them as a JSON file.
This helps validate that the calculated indicators make sense and are useful
for the decision module.
"""
import json
from datetime import datetime
from common.db import get_db_connection

def extract_indicator_test_data():
    """Extract recent indicators for multiple timeframes and save as JSON."""
    data = []
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Query recent data with non-empty indicators for each timeframe
            timeframes = ['15m', '1h', '4h', '1d']
            
            for timeframe in timeframes:
                cur.execute("""
                    SELECT symbol, timeframe, updated_at, raw_data, indicators 
                    FROM market_data 
                    WHERE symbol = %s 
                    AND source = %s 
                    AND timeframe = %s 
                    AND indicators != '{}'::jsonb
                    ORDER BY updated_at DESC 
                    LIMIT 5
                """, ('BTC-USD', 'yfinance', timeframe))
                
                rows = cur.fetchall()
                print(f"Found {len(rows)} records for {timeframe} timeframe")
                
                for row in rows:
                    symbol, tf, timestamp, raw_data, indicators = row
                    
                    # Convert to serializable format
                    record = {
                        'symbol': symbol,
                        'timeframe': tf,
                        'timestamp': timestamp.isoformat(),
                        'price_data': {
                            'open': raw_data.get('open'),
                            'high': raw_data.get('high'),
                            'low': raw_data.get('low'),
                            'close': raw_data.get('close'),
                            'volume': raw_data.get('volume')
                        },
                        'indicators': indicators
                    }
                    data.append(record)
    
    # Save to a test file
    filename = f"indicator_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved {len(data)} records to {filename}")
    return filename

if __name__ == "__main__":
    extract_indicator_test_data()