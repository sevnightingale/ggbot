#!/usr/bin/env python3
"""
Debug what's happening with config loading
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from core.common.logger import logger

load_dotenv()

def debug_config_loading():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    user_id = "00000000-0000-0000-0000-000000000000"
    config_id = "04b4a272-8303-4770-a536-6d210b9defba"
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Get the raw config from database
    response = supabase.table('configurations').select("*").eq('config_id', config_id).eq('user_id', user_id).execute()
    
    if response.data:
        config_row = response.data[0]
        print("🔍 Full configuration row from database:")
        for key, value in config_row.items():
            if key == 'config_data':
                print(f"  {key}: {type(value)} with keys: {list(value.keys()) if isinstance(value, dict) else 'not dict'}")
                if isinstance(value, dict):
                    for sub_key in value.keys():
                        print(f"    - {sub_key}")
            else:
                print(f"  {key}: {value}")
        
        print(f"\n🔍 config_data contents:")
        config_data = config_row['config_data']
        if isinstance(config_data, dict):
            for key, value in config_data.items():
                print(f"  {key}: {type(value)}")
                if key == 'config_data' and isinstance(value, dict):
                    print(f"    Inner config_data keys: {list(value.keys())}")
                    # Check if config_type is in the inner config_data
                    if 'config_type' in value:
                        print(f"    ❌ PROBLEM: config_type in inner config_data: {value['config_type']}")
        else:
            print(f"  config_data is not dict: {type(config_data)}")
            
        # Check if config_type is in config_data
        if isinstance(config_data, dict) and 'config_type' in config_data:
            print(f"\n❌ PROBLEM: config_type is inside config_data JSONB!")
            print(f"  config_data['config_type'] = {config_data['config_type']}")
        else:
            print(f"\n✅ config_type is properly in table metadata, not in config_data JSONB")
            
    else:
        print("❌ No config found")

if __name__ == "__main__":
    debug_config_loading()