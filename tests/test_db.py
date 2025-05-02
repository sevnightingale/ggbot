import uuid
import psycopg2
import os
from core.common.db import upsert_market_data
from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, DEFAULT_USER_ID

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )

# Ensure the default user exists in the users table
def ensure_default_user():
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (user_id, username)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) DO NOTHING;
                """, (DEFAULT_USER_ID, "default_user"))
    finally:
        conn.close()

# Ensure default user is present
ensure_default_user()

# Example market data
symbol = "BTC/USD"
timeframe = "4h"
data = {
    "ggShot": {
        "signal": "LONG",
        "take_profits": [{"tp1": 87500.0}],
        "trailing_stop_loss": 85500.0
    },
    "rsi": 42.5,
    "macd": {"macd_line": 1.07, "signal_line": 0.95, "histogram": 0.12},
    "bollinger": {"upper": 87000.0, "middle": 86000.0, "lower": 85000.0},
    "price_context": {
        "recent_high": 88000.0,
        "recent_low": 85000.0,
        "moving_average_20": 86500.0,
        "momentum": 2.5,
        "volatility": 1500.0
    },
    "real_time_price": 86350.0
}

# Insert market data
upsert_market_data(DEFAULT_USER_ID, symbol, timeframe, data)

print(f"Market data inserted/updated for user: {DEFAULT_USER_ID}")
