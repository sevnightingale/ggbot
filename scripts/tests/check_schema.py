#!/usr/bin/env python3
"""
Check actual Supabase schema for paper trading tables
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def check_table_schema():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Check what columns actually exist by trying to insert minimal data
    tables = ['paper_accounts', 'paper_trades', 'paper_orders']
    
    for table_name in tables:
        print(f"\n🔍 Checking {table_name} table schema...")
        
        try:
            # Try to select with limit 0 to see what columns exist
            response = supabase.table(table_name).select("*").limit(0).execute()
            print(f"   ✅ {table_name} table accessible")
            
            # Try to get one record to see column structure
            response = supabase.table(table_name).select("*").limit(1).execute()
            if response.data:
                print(f"   📋 Sample record structure:")
                for key, value in response.data[0].items():
                    print(f"      - {key}: {type(value).__name__}")
            else:
                print(f"   📋 No records in {table_name} to show structure")
                
        except Exception as e:
            print(f"   ❌ Error accessing {table_name}: {e}")

if __name__ == "__main__":
    check_table_schema()