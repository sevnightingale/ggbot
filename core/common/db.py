# common/db.py
import asyncio
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
    """Build the application database DSN (local PostgreSQL).

    Precedence:
      1. DATABASE_URL — full DSN (canonical pointer to the local Postgres)
      2. DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASS parts

    Fails loud if neither is configured — no silent fallback (per migration off
    Supabase: the app DB is now local Postgres; auth + vault are app-managed).
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
    if DB_HOST and DB_NAME and DB_USER and DB_PASS:
        return f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    raise ValueError(
        "No database configuration found: set DATABASE_URL (preferred) or the "
        "DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASS set in .env"
    )

def _get_connection_pool():
    """Get or create the global connection pool."""
    global _connection_pool

    if _connection_pool is None:
        database_url = get_database_url()
        # Log resolved host (not credentials) so a misconfigured DSN is obvious at startup.
        try:
            _host = urlparse(database_url).hostname
        except Exception:
            _host = "?"
        print(f"[db] connection pool -> host={_host}")
        # Connection pool: min 5 idle, max 30 concurrent per process.
        # 3 pool-owning processes (api, scheduler, account-monitor) x 30 = 90 < max_connections=100.
        # connect_timeout=5 prevents permanent deadlock if pool exhausted in async context.
        _connection_pool = pool.ThreadedConnectionPool(
            minconn=5,
            maxconn=30,
            dsn=database_url,
            connect_timeout=5,
            # TCP keepalives: harmless on local PG; survive any idle-close on the wire.
            keepalives=1,
            keepalives_idle=30,     # seconds before first probe
            keepalives_interval=10, # seconds between probes
            keepalives_count=3      # failed probes before closing
        )

    return _connection_pool


def _reset_connection_pool():
    """Discard the global pool so the next call rebuilds fresh connections.
    Called when a pooled connection is found broken (e.g. local Postgres restarted)."""
    global _connection_pool
    if _connection_pool is not None:
        try:
            _connection_pool.closeall()
        except Exception:
            pass
        _connection_pool = None

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
    pool_ = _get_connection_pool()
    conn = pool_.getconn()  # Get connection from pool (reuses existing connection)
    try:
        yield conn
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        # Connection broke mid-use (e.g. local Postgres restarted / OOM-killed).
        # Discard this connection and reset the pool so the next caller rebuilds.
        try:
            pool_.putconn(conn, close=True)
        except Exception:
            pass
        conn = None
        _reset_connection_pool()
        raise
    finally:
        if conn is not None:
            pool_.putconn(conn)  # Return healthy connection to pool

# ---------------------------------------------------------------------------
# Async-safe DB helpers — run sync psycopg2 queries in a thread pool so they
# never block the asyncio event loop.  Used by the scheduler process where
# 30+ bot coroutines share a single event loop thread.
# ---------------------------------------------------------------------------

async def db_fetch_one(sql, params=None):
    """Execute SELECT returning one row, in a thread pool."""
    def _run():
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone()
    return await asyncio.to_thread(_run)


async def db_fetch_all(sql, params=None):
    """Execute SELECT returning all rows, in a thread pool."""
    def _run():
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()
    return await asyncio.to_thread(_run)


async def db_execute(sql, params=None):
    """Execute INSERT/UPDATE/DELETE with commit, in a thread pool."""
    def _run():
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                conn.commit()
                return cur.rowcount
    return await asyncio.to_thread(_run)


async def db_execute_returning(sql, params=None):
    """Execute INSERT ... RETURNING with commit, in a thread pool."""
    def _run():
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                result = cur.fetchone()
                conn.commit()
                return result
    return await asyncio.to_thread(_run)


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