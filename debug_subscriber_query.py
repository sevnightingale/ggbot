#!/usr/bin/env python3

import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.common.db import get_db_connection

def test_subscriber_query():
    """Test the subscriber query to see what's wrong."""
    signal_source = "ggshot"
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Debug: First check what configs exist at all
            print("=== DEBUG: All signal_validation configs ===")
            cur.execute("""
                SELECT c.config_id, c.config_type, c.state, 
                       up.subscription_tier, up.subscription_status, up.paid_data_points,
                       c.config_data->'extraction'->'selected_data_sources'->'signals_group_chats'->'data_points' as signal_data_points,
                       c.config_data->'extraction'->'selected_data_sources' ? 'signals_group_chats' as has_signals_section,
                       c.config_data->'config_data'->'extraction'->'selected_data_sources'->'signals_group_chats'->'data_points' as nested_signal_points
                FROM configurations c
                JOIN user_profiles up ON c.user_id = up.user_id
                WHERE c.config_type = 'signal_validation'
            """)
            
            debug_results = cur.fetchall()
            print(f"Found {len(debug_results)} signal_validation configs:")
            for row in debug_results:
                print(f"   Config {row[0]}: type={row[1]}, state={row[2]}, tier={row[3]}, status={row[4]}")
                print(f"      paid_points={row[5]}")
                print(f"      signal_data_points={row[6]}")  
                print(f"      has_signals_section={row[7]}")
                print(f"      nested_signal_points={row[8]}")
            
            print(f"\n=== DEBUG: Testing different query approaches for signal_source='{signal_source}' ===")
            
            # Test 1: Original query with ANY() - this is probably broken
            print("\n1. Original query with ANY():")
            try:
                cur.execute("""
                    SELECT DISTINCT c.config_id, c.user_id
                    FROM configurations c
                    JOIN user_profiles up ON c.user_id = up.user_id
                    WHERE c.config_type = 'signal_validation'
                      AND c.state = 'active'
                      AND c.config_data->'extraction'->'selected_data_sources' ? 'signals_group_chats'
                      AND %s = ANY(up.paid_data_points)
                      AND up.subscription_tier = 'ggBase'
                      AND up.subscription_status = 'active'
                """, (signal_source,))
                
                results = cur.fetchall()
                print(f"   ANY() query returned {len(results)} results")
                for row in results:
                    print(f"      {row[0]} - {row[1]}")
            except Exception as e:
                print(f"   ANY() query failed: {e}")
            
            # Test 2: Correct ANY() for text[] type
            print("\n2. Correct ANY() for text[] type:")
            try:
                cur.execute("""
                    SELECT DISTINCT c.config_id, c.user_id
                    FROM configurations c
                    JOIN user_profiles up ON c.user_id = up.user_id
                    WHERE c.config_type = 'signal_validation'
                      AND c.state = 'active'
                      AND c.config_data->'extraction'->'selected_data_sources' ? 'signals_group_chats'
                      AND %s = ANY(up.paid_data_points)
                      AND up.subscription_tier = 'ggBase'
                      AND up.subscription_status = 'active'
                """, (signal_source,))
                
                results = cur.fetchall()
                print(f"   Correct ANY() query returned {len(results)} results")
                for row in results:
                    print(f"      {row[0]} - {row[1]}")
            except Exception as e:
                print(f"   Correct ANY() query failed: {e}")
                
            # Test 3: Without state check to see if that's the issue
            print("\n3. Without state check:")
            try:
                cur.execute("""
                    SELECT DISTINCT c.config_id, c.user_id, c.state
                    FROM configurations c
                    JOIN user_profiles up ON c.user_id = up.user_id
                    WHERE c.config_type = 'signal_validation'
                      AND c.config_data->'extraction'->'selected_data_sources' ? 'signals_group_chats'
                      AND %s = ANY(up.paid_data_points)
                      AND up.subscription_tier = 'ggBase'
                      AND up.subscription_status = 'active'
                """, (signal_source,))
                
                results = cur.fetchall()
                print(f"   No state check query returned {len(results)} results")
                for row in results:
                    print(f"      {row[0]} - {row[1]} - state: {row[2]}")
            except Exception as e:
                print(f"   No state check query failed: {e}")

if __name__ == "__main__":
    test_subscriber_query()