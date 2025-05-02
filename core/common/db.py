# common/db.py
import json
import psycopg2
from contextlib import contextmanager
from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

@contextmanager
def get_db_connection():
    """
    Context manager to safely handle database connections.
    
    Usage:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM some_table")
            results = cur.fetchall()
    """
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    try:
        yield conn
    finally:
        conn.close()

def upsert_market_data(user_id, symbol, timeframe, data_dict, data_type=None, source=None):
    """
    Inserts or updates market data for a specific user, ensuring one row per user-symbol-timeframe.
    
    Args:
        user_id: UUID of the user
        symbol: Trading pair symbol (e.g., 'BTC/USD')
        timeframe: Chart timeframe (e.g., '15m', '1h', '4h')
        data_dict: Dictionary containing the data to store
        data_type: Type of data (e.g., 'indicator_values', 'report', 'sentiment')
        source: Data source (e.g., 'tradingview', 'yfinance')
        
    Returns:
        Boolean indicating success
    """
    # Default source to 'unknown' if not provided
    source = source or 'unknown'
    
    # Determine data_type if not provided
    if data_type is None:
        # Simple heuristic to guess data_type
        if 'report' in data_dict:
            data_type = 'report'
        elif any(key in data_dict for key in ['RSI', 'MACD', 'EMA']):
            data_type = 'indicator_values'
        else:
            data_type = 'mixed'

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                # Convert Python dictionary to JSON format
                json_data = json.dumps(data_dict)

                # Insert or update the row based on (user_id, symbol, timeframe)
                cur.execute("""
                    INSERT INTO market_data (user_id, symbol, timeframe, indicators, source, data_type, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (user_id, symbol, timeframe)
                    DO UPDATE SET indicators = EXCLUDED.indicators,
                                source = EXCLUDED.source,
                                data_type = EXCLUDED.data_type,
                                updated_at = NOW();
                """, (user_id, symbol, timeframe, json_data, source, data_type))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error in upsert_market_data: {e}")
            return False

def get_configuration(user_id, config_type, config_name=None):
    """
    Retrieve a configuration from the database.
    
    Args:
        user_id: UUID of the user
        config_type: Type of configuration (e.g., 'extraction', 'decision')
        config_name: Optional name of the configuration
        
    Returns:
        Dictionary containing the configuration data or None if not found
    """
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                if config_name:
                    cur.execute("""
                        SELECT config_data FROM configurations 
                        WHERE user_id = %s AND config_type = %s AND config_name = %s
                    """, (user_id, config_type, config_name))
                else:
                    cur.execute("""
                        SELECT config_data FROM configurations 
                        WHERE user_id = %s AND config_type = %s
                    """, (user_id, config_type))
                
                result = cur.fetchone()
                if result:
                    return result[0]
                return None
        except Exception as e:
            print(f"Error in get_configuration: {e}")
            return None

def save_configuration(user_id, config_type, config_data, config_name=None):
    """
    Save a configuration to the database.
    
    Args:
        user_id: UUID of the user
        config_type: Type of configuration (e.g., 'extraction', 'decision')
        config_data: Dictionary containing the configuration data
        config_name: Optional name for the configuration
        
    Returns:
        UUID of the configuration or None if failed
    """
    import uuid
    
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                # Convert config_data to JSON if it's not already a string
                if not isinstance(config_data, str):
                    config_data = json.dumps(config_data)
                
                # Check if configuration already exists
                if config_name:
                    cur.execute("""
                        SELECT config_id FROM configurations 
                        WHERE user_id = %s AND config_type = %s AND config_name = %s
                    """, (user_id, config_type, config_name))
                else:
                    cur.execute("""
                        SELECT config_id FROM configurations 
                        WHERE user_id = %s AND config_type = %s AND config_name IS NULL
                    """, (user_id, config_type))
                
                result = cur.fetchone()
                
                if result:
                    # Update existing configuration
                    config_id = result[0]
                    cur.execute("""
                        UPDATE configurations 
                        SET config_data = %s, updated_at = NOW() 
                        WHERE config_id = %s
                    """, (config_data, config_id))
                else:
                    # Insert new configuration
                    config_id = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO configurations 
                        (config_id, user_id, config_type, config_name, config_data, created_at, updated_at) 
                        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """, (config_id, user_id, config_type, config_name, config_data))
                
                conn.commit()
                return config_id
        except Exception as e:
            conn.rollback()
            print(f"Error in save_configuration: {e}")
            return None