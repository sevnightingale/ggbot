#!/usr/bin/env python3
"""
Quick test script to verify Supabase connection and migration.
Run from ggbot directory: python test_supabase_connection.py
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

def test_environment_variables():
    """Test that required environment variables are set."""
    print("🔍 Testing environment variables...")
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY", 
        "SUPABASE_ANON_KEY",
        "SUPABASE_DB_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 20)}...")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All environment variables are set")
    return True

def test_database_connection():
    """Test database connection using the updated db.py"""
    print("\n🔍 Testing database connection...")
    
    try:
        from core.common.db import get_db_connection, get_database_url
        
        # Show which database URL is being used
        db_url = get_database_url()
        if "supabase" in db_url:
            print("✅ Using Supabase database")
        else:
            print("⚠️  Using legacy database (fallback)")
        
        # Test connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"✅ Database connection successful")
                print(f"   PostgreSQL version: {version}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_tables_exist():
    """Test that migrated tables exist."""
    print("\n🔍 Testing migrated tables...")
    
    expected_tables = [
        'configurations',
        'decisions', 
        'market_data',
        'paper_accounts',
        'paper_trades',
        'paper_orders',
        'logs'
    ]
    
    try:
        from core.common.db import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get list of tables
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                
                existing_tables = [row[0] for row in cur.fetchall()]
                print(f"📋 Found {len(existing_tables)} tables in database")
                
                missing_tables = []
                for table in expected_tables:
                    if table in existing_tables:
                        print(f"✅ {table}")
                    else:
                        print(f"❌ {table} - MISSING")
                        missing_tables.append(table)
                
                if missing_tables:
                    print(f"\n❌ Missing tables: {', '.join(missing_tables)}")
                    print("💡 Run the supabase_migration.sql script in your Supabase dashboard")
                    return False
                
                print("✅ All expected tables exist")
                return True
                
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False

def test_rls_policies():
    """Test that Row Level Security is enabled."""
    print("\n🔍 Testing Row Level Security...")
    
    try:
        from core.common.db import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check RLS status for key tables
                cur.execute("""
                    SELECT schemaname, tablename, rowsecurity 
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename IN ('configurations', 'decisions', 'market_data', 'paper_accounts')
                    ORDER BY tablename;
                """)
                
                rls_status = cur.fetchall()
                all_enabled = True
                
                for schema, table, rls_enabled in rls_status:
                    if rls_enabled:
                        print(f"✅ {table}: RLS enabled")
                    else:
                        print(f"❌ {table}: RLS disabled")
                        all_enabled = False
                
                if all_enabled:
                    print("✅ Row Level Security is properly configured")
                    return True
                else:
                    print("❌ Some tables missing RLS - check migration script")
                    return False
                    
    except Exception as e:
        print(f"❌ RLS check failed: {e}")
        return False

def test_auth_utilities():
    """Test auth utilities can be imported."""
    print("\n🔍 Testing auth utilities...")
    
    try:
        from core.auth import get_current_user_id, verify_jwt_token, create_supabase_client
        print("✅ Auth utilities imported successfully")
        
        # Test Supabase client creation
        client = create_supabase_client()
        print("✅ Supabase client created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Auth utilities test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 GGBot Supabase Integration Test\n")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Database Connection", test_database_connection),
        ("Migrated Tables", test_tables_exist),
        ("Row Level Security", test_rls_policies),
        ("Auth Utilities", test_auth_utilities)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Supabase integration is ready.")
        print("\n📝 Next steps:")
        print("   1. Proceed to Phase 2: Extraction Accuracy Testing")
        print("   2. Install pandas-ta: pip install pandas-ta")
    else:
        print("🔧 Some tests failed. Please fix issues before proceeding.")
        print("\n💡 Common fixes:")
        print("   1. Check .env file has all required variables")
        print("   2. Run supabase_migration.sql in Supabase dashboard")
        print("   3. Verify database password is correct")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)