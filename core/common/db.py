# common/db.py
import json
import psycopg2
from psycopg2 import pool
from decimal import Decimal
from contextlib import contextmanager
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global connection pool (initialized on first use)
_connection_pool = None


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that preserves Decimal precision as strings."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to string to preserve precision
        return super(DecimalEncoder, self).default(obj)

def get_database_url():
    """Get database connection URL, preferring Supabase over legacy config."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if supabase_url and supabase_key:
        # Parse Supabase URL to get database connection details
        # Supabase URL format: https://project-ref.supabase.co
        # Database URL format: postgresql://postgres:[password]@db.project-ref.supabase.co:5432/postgres
        parsed = urlparse(supabase_url)
        project_ref = parsed.netloc.split('.')[0]

        # Get database password from service key (you'll need to set this in .env)
        db_password = os.getenv("SUPABASE_DB_PASSWORD")
        if not db_password:
            raise ValueError("SUPABASE_DB_PASSWORD environment variable required for database connection")

        # Use transaction pooler for IPv4 compatibility (direct db only has IPv6)
        return f"postgresql://postgres.{project_ref}:{db_password}@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
    else:
        # Fallback to legacy config
        from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
        return f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def _get_connection_pool():
    """Get or create the global connection pool."""
    global _connection_pool

    if _connection_pool is None:
        database_url = get_database_url()
        # Create a connection pool with min 5, max 20 connections
        # This reduces SSL connection churn dramatically
        _connection_pool = pool.ThreadedConnectionPool(
            minconn=5,   # Keep 5 connections alive at all times
            maxconn=20,  # Allow up to 20 concurrent connections
            dsn=database_url
        )

    return _connection_pool

@contextmanager
def get_db_connection():
    """
    Context manager to safely handle database connections using connection pooling.
    Automatically uses Supabase if configured, otherwise falls back to legacy config.

    Connection pool reduces SSL connection churn from hundreds/minute to ~5-20 persistent connections.

    Usage:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM some_table")
            results = cur.fetchall()
    """
    pool = _get_connection_pool()
    conn = pool.getconn()  # Get connection from pool (reuses existing SSL connection)
    try:
        yield conn
    finally:
        pool.putconn(conn)  # Return connection to pool (keeps SSL connection alive)

def upsert_market_data(user_id, symbol, config_id, data_dict, data_type=None, source=None, timeframe='mixed'):
    """
    Inserts or updates market data for a specific user using config_id pattern.
    
    Args:
        user_id: UUID of the user
        symbol: Trading pair symbol (e.g., 'BTC/USD')
        config_id: Configuration ID for the extraction
        data_dict: Dictionary containing the data to store
        data_type: Type of data (e.g., 'indicator_values', 'report', 'sentiment')
        source: Data source (e.g., 'tradingview', 'yfinance')
        timeframe: Chart timeframe (default 'mixed' for new system)
        
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
                # Convert Python dictionary to JSON format (preserving Decimal precision)
                json_data = json.dumps(data_dict, cls=DecimalEncoder)

                # Insert or update the row using config_id pattern
                cur.execute("""
                    INSERT INTO market_data (user_id, symbol, config_id, timeframe, indicators, source, data_type, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (user_id, symbol, timeframe, config_id)
                    DO UPDATE SET indicators = EXCLUDED.indicators,
                                source = EXCLUDED.source,
                                data_type = EXCLUDED.data_type,
                                updated_at = NOW();
                """, (user_id, symbol, config_id, timeframe, json_data, source, data_type))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error in upsert_market_data: {e}")
            return False

# get_configuration function removed - use core.config.config_main.get_configuration instead

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
                # Convert config_data to JSON if it's not already a string (preserving Decimal precision)
                if not isinstance(config_data, str):
                    config_data = json.dumps(config_data, cls=DecimalEncoder)
                
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
                        (config_id, user_id, config_type, config_name, config_data, initial_equity, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, 10000.00, NOW(), NOW())
                    """, (config_id, user_id, config_type, config_name, config_data))
                
                conn.commit()
                return config_id
        except Exception as e:
            conn.rollback()
            print(f"Error in save_configuration: {e}")
            return None