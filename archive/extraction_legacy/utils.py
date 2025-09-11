"""
Extraction module utilities.

This module provides utility functions for the extraction module, including
database operations for storing and retrieving market data.
"""
import json
from typing import Dict, List, Optional, Any

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.common.db import get_db_connection


def store_market_data_entries(data_entries: List[Dict], replace_existing: bool = False) -> int:
    """
    Store multiple market data entries in the database.
    
    Args:
        data_entries: List of dictionaries, each representing a market data entry
                     (as returned by DataSource.to_database_format and updated by
                      IndicatorComputer.to_database_format)
        replace_existing: Whether to replace existing entries or update them
                         (default: False - update existing entries)
        
    Returns:
        Number of successfully stored entries
    """
    if not data_entries:
        logger.bind(user_id=DEFAULT_USER_ID).warning("No market data entries to store")
        return 0
    
    success_count = 0
    
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                for entry in data_entries:
                    # Extract the required fields from the entry
                    user_id = entry.get('user_id', DEFAULT_USER_ID)
                    source = entry.get('source', 'unknown')
                    symbol = entry.get('symbol', '')
                    timeframe = entry.get('timeframe', '')
                    data_type = entry.get('data_type', 'price_data')
                    raw_data = entry.get('raw_data', {})
                    indicators = entry.get('indicators', {})
                    updated_at = entry.get('updated_at')
                    config_id = entry.get('config_id')  # NEW FIELD
                    
                    # Skip entries without required fields
                    if not symbol or not timeframe:
                        logger.bind(user_id=user_id).warning(
                            f"Skipping entry with missing symbol or timeframe: {entry}"
                        )
                        continue
                    
                    # Convert Python dictionaries to JSON strings
                    raw_data_json = json.dumps(raw_data) if isinstance(raw_data, dict) else raw_data
                    indicators_json = json.dumps(indicators) if isinstance(indicators, dict) else indicators
                    
                    if replace_existing:
                        # Delete existing entry only if it has the same timestamp
                        # This ensures we don't delete historical data when updating
                        cur.execute("""
                            DELETE FROM market_data
                            WHERE user_id = %s AND symbol = %s AND timeframe = %s AND source = %s AND updated_at = %s
                        """, (user_id, symbol, timeframe, source, updated_at))
                    
                    # Insert the data into the market_data table with the updated schema
                    cur.execute("""
                        INSERT INTO market_data 
                        (user_id, symbol, timeframe, source, data_type, raw_data, indicators, updated_at, config_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, symbol, timeframe, updated_at)
                        DO UPDATE SET 
                            raw_data = EXCLUDED.raw_data,
                            indicators = EXCLUDED.indicators,
                            source = EXCLUDED.source,
                            data_type = EXCLUDED.data_type,
                            config_id = EXCLUDED.config_id
                        RETURNING id
                    """, (
                        user_id, symbol, timeframe, source, data_type, 
                        raw_data_json, indicators_json, updated_at, config_id
                    ))
                    
                    # Get the ID of the inserted/updated row
                    result = cur.fetchone()
                    if result:
                        success_count += 1
                    
                # Commit the transaction
                conn.commit()
                
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"Successfully stored {success_count} of {len(data_entries)} market data entries"
                )
                
                return success_count
                
        except Exception as e:
            conn.rollback()
            logger.bind(user_id=DEFAULT_USER_ID).error(f"Error storing market data: {str(e)}")
            return 0


def get_latest_market_data(
    symbol: str, 
    config_id: str,
    user_id: str = DEFAULT_USER_ID,
    source: Optional[str] = None,
    timeframe: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get the latest market data for a specific symbol and config.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC-USD')
        config_id: Configuration ID for the extraction
        user_id: User ID to retrieve data for (default: DEFAULT_USER_ID)
        source: Optional source to filter by (e.g., 'yfinance', 'tradingview')
        timeframe: Optional timeframe filter (for backwards compatibility)
        
    Returns:
        Dictionary containing the market data or None if not found
    """
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                if source:
                    cur.execute("""
                        SELECT id, source, data_type, raw_data, indicators, updated_at
                        FROM market_data
                        WHERE user_id = %s AND symbol = %s AND config_id = %s AND source = %s
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """, (user_id, symbol, config_id, source))
                else:
                    cur.execute("""
                        SELECT id, source, data_type, raw_data, indicators, updated_at
                        FROM market_data
                        WHERE user_id = %s AND symbol = %s AND config_id = %s
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """, (user_id, symbol, config_id))
                
                result = cur.fetchone()
                if not result:
                    return None
                
                # Parse the result into a dictionary
                id, src, data_type, raw_data, indicators, updated_at = result
                
                return {
                    'id': id,
                    'user_id': user_id,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'source': src,
                    'data_type': data_type,
                    'raw_data': raw_data,
                    'indicators': indicators,
                    'updated_at': updated_at
                }
                
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Error retrieving market data: {str(e)}")
            return None


def get_market_data_history(
    symbol: str,
    config_id: str,
    limit: int = 100,
    user_id: str = DEFAULT_USER_ID,
    source: Optional[str] = None,
    timeframe: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get historical market data for a specific symbol and config.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC-USD')
        config_id: Configuration ID for the extraction
        limit: Maximum number of records to retrieve (default: 100)
        user_id: User ID to retrieve data for (default: DEFAULT_USER_ID)
        source: Optional source to filter by (e.g., 'yfinance', 'tradingview')
        timeframe: Optional timeframe filter (for backwards compatibility)
        
    Returns:
        List of dictionaries containing the market data, ordered by updated_at DESC
    """
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                if source:
                    cur.execute("""
                        SELECT id, source, data_type, raw_data, indicators, updated_at
                        FROM market_data
                        WHERE user_id = %s AND symbol = %s AND config_id = %s AND source = %s
                        ORDER BY updated_at DESC
                        LIMIT %s
                    """, (user_id, symbol, config_id, source, limit))
                else:
                    cur.execute("""
                        SELECT id, source, data_type, raw_data, indicators, updated_at
                        FROM market_data
                        WHERE user_id = %s AND symbol = %s AND config_id = %s
                        ORDER BY updated_at DESC
                        LIMIT %s
                    """, (user_id, symbol, config_id, limit))
                
                results = cur.fetchall()
                if not results:
                    return []
                
                # Parse the results into a list of dictionaries  
                history = []
                for row in results:
                    id, src, data_type, raw_data, indicators, updated_at = row
                    
                    history.append({
                        'id': id,
                        'user_id': user_id,
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'source': src,
                        'data_type': data_type,
                        'raw_data': raw_data,
                        'indicators': indicators,
                        'updated_at': updated_at
                    })
                
                return history
                
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Error retrieving market data history: {str(e)}")
            return []