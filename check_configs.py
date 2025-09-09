#!/usr/bin/env python3
"""
Check existing configurations in Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def check_configs():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    user_id = os.getenv("DEFAULT_USER_ID")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Check configurations
        response = supabase.table('configurations').select("*").eq('user_id', user_id).execute()
        
        print(f"Total configurations for user {user_id}: {len(response.data)}")
        
        for config in response.data:
            print(f"  - Config ID: {config['config_id']}")
            print(f"    Name: {config.get('config_name', 'Unnamed')}")
            print(f"    Type: {config.get('config_type', 'Unknown')}")
            print(f"    Created: {config.get('created_at', 'Unknown')}")
            print()
            
        if len(response.data) == 0:
            print("No configurations found. Creating a test configuration...")
            
            # Create a test configuration
            test_config = {
                'user_id': user_id,
                'config_type': 'test',
                'config_name': 'Paper Trading Test Config',
                'config_data': {'test': True, 'trading': {'execution_mode': 'paper'}}
            }
            
            result = supabase.table('configurations').insert(test_config).execute()
            if result.data:
                print(f"✅ Created test configuration: {result.data[0]['config_id']}")
                return result.data[0]['config_id']
            else:
                print("❌ Failed to create test configuration")
                
    except Exception as e:
        print(f"Error checking configurations: {e}")
        
    return None

if __name__ == "__main__":
    check_configs()