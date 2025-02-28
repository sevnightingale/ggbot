# common/db.py
import json
import psycopg2
from common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

def upsert_market_data(user_id, symbol, timeframe, data_dict):
    """ Inserts or updates market data for a specific user, ensuring one row per user-symbol-timeframe. """

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    try:
        with conn:
            with conn.cursor() as cur:
                # Convert Python dictionary to JSON format
                json_data = json.dumps(data_dict)

                # Insert or update the row based on (user_id, symbol, timeframe)
                cur.execute("""
                    INSERT INTO market_data (user_id, symbol, timeframe, data)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id, symbol, timeframe)
                    DO UPDATE SET data = EXCLUDED.data,
                                  updated_at = NOW();
                """, (user_id, symbol, timeframe, json_data))
    finally:
        conn.close()
