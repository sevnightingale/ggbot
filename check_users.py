#!/usr/bin/env python3
"""
Check existing users in Supabase auth system
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def check_users():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Try to list users (this requires service role)
        response = supabase.auth.admin.list_users()
        print(f"Total users in auth.users: {len(response)}")
        
        for user in response:
            print(f"  - User ID: {user.id}")
            print(f"    Email: {user.email}")
            print(f"    Created: {user.created_at}")
            print()
            
    except Exception as e:
        print(f"Error listing users: {e}")
        
        # Try alternative approach - check auth.users via direct SQL
        try:
            # Note: This won't work due to RLS, but let's try
            result = supabase.rpc('get_auth_users').execute()
            print("RPC result:", result)
        except Exception as e2:
            print(f"RPC also failed: {e2}")

if __name__ == "__main__":
    check_users()