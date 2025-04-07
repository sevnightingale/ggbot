"""
Scheduled extraction script for regularly updating market data.

This script is designed to be run by a scheduler (cron) to regularly
update market data for various symbols and timeframes.

It has three modes:
1. Initialization mode: Fetches maximum historical data for all timeframes
2. Update mode: Only fetches new data since the last update
3. Indicator calculation mode: Recalculates indicators on all stored data
"""
import sys
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from common.logger import logger
from common.config import DEFAULT_USER_ID
from common.db import get_db_connection
from extraction.extraction_main import ExtractionManager
from extraction.utils import get_latest_market_data, store_market_data_entries


def get_last_update_time(symbol: str, timeframe: str, source: str = 'yfinance') -> Optional[datetime]:
    """
    Get the timestamp of the most recent data for a symbol and timeframe.
    
    Args:
        symbol: The trading pair symbol (e.g., 'BTC-USD')
        timeframe: The timeframe (e.g., '1d', '4h', '1h', '15m')
        source: The data source name
        
    Returns:
        The timestamp of the most recent data or None if no data exists
    """
    data = get_latest_market_data(symbol, timeframe, DEFAULT_USER_ID, source)
    if data and 'updated_at' in data:
        return data['updated_at']
    return None


def run_initialization(force: bool = False):
    """
    Initialize the database with historical data for all symbols and timeframes.
    
    Args:
        force: Whether to force initialization even if data exists
    """
    manager = ExtractionManager()
    
    # Define symbols and timeframes with appropriate history lengths for each
    symbols = ['BTC-USD']
    
    # Configure days of history per timeframe based on yfinance limitations
    # 1d, 1w, 1mo: up to 10+ years
    # 1h, 4h: up to 730 days (2 years)
    # 15m, 30m: up to 60 days
    # 1m: up to 7 days
    timeframe_config = {
        '1d': {'days': 730},   # 2 years for daily data
        '4h': {'days': 730},   # 2 years for 4h data
        '1h': {'days': 730},   # 2 years for hourly data
        '15m': {'days': 60}    # 60 days for 15-min data (yfinance limit)
    }
    
    # Process each symbol
    for symbol in symbols:
        # Process each timeframe with appropriate history length
        for timeframe, config in timeframe_config.items():
            # Check if we already have data for this symbol and timeframe
            if not force:
                last_update = get_last_update_time(symbol, timeframe)
                if last_update:
                    logger.bind(user_id=DEFAULT_USER_ID).info(
                        f"Data already exists for {symbol} {timeframe}, last updated at {last_update}. "
                        f"Skipping initialization. Use --force to override."
                    )
                    continue
            
            days = config['days']
            
            logger.bind(user_id=DEFAULT_USER_ID).info(
                f"Initializing {symbol} {timeframe} with {days} days of history..."
            )
            
            # Calculate appropriate dates
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            try:
                # Get the data source
                data_source = manager.data_sources.get('yfinance')
                if not data_source:
                    logger.bind(user_id=DEFAULT_USER_ID).error("YFinance data source not found!")
                    continue
                
                # Fetch historical data
                df = data_source.get_historical_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df.empty:
                    logger.bind(user_id=DEFAULT_USER_ID).warning(
                        f"No data found for {symbol} {timeframe}"
                    )
                    continue
                
                # Convert to database format without computing indicators
                # We'll just store the raw data
                data_entries = data_source.to_database_format(
                    df=df,
                    symbol=symbol,
                    timeframe=timeframe,
                    user_id=DEFAULT_USER_ID
                )
                
                # Set empty indicators object for now
                for entry in data_entries:
                    entry['indicators'] = {}
                
                # Store in database
                stored_count = store_market_data_entries(data_entries)
                
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"Initialized {stored_count} {symbol} {timeframe} data entries in database"
                )
                
                # Add a small delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.bind(user_id=DEFAULT_USER_ID).error(
                    f"Error initializing {symbol} {timeframe}: {str(e)}"
                )
    
    logger.bind(user_id=DEFAULT_USER_ID).info("Initialization complete!")


def run_update():
    """
    Update the database with only new data since the last update.
    """
    manager = ExtractionManager()
    
    # Define symbols and timeframes to update
    symbols = ['BTC-USD']
    timeframes = ['1d', '4h', '1h', '15m']
    
    update_count = 0
    
    # Process each symbol
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                # Get the latest data timestamp
                last_update = get_last_update_time(symbol, timeframe)
                
                if not last_update:
                    logger.bind(user_id=DEFAULT_USER_ID).info(
                        f"No existing data for {symbol} {timeframe}. Run initialization first."
                    )
                    continue
                
                # Add a small buffer to avoid missing data due to timing issues
                # For example, if the last candle closed at exactly the same time as the last update
                buffer_minutes = 5
                start_date = last_update - timedelta(minutes=buffer_minutes)
                end_date = datetime.now()
                
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"Updating {symbol} {timeframe} data from {start_date} to {end_date}..."
                )
                
                # Get the data source
                data_source = manager.data_sources.get('yfinance')
                if not data_source:
                    logger.bind(user_id=DEFAULT_USER_ID).error("YFinance data source not found!")
                    continue
                
                # Fetch only new data
                df = data_source.get_historical_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df.empty:
                    logger.bind(user_id=DEFAULT_USER_ID).info(
                        f"No new data for {symbol} {timeframe} since {last_update}"
                    )
                    continue
                
                # Convert to database format without computing indicators
                # We'll just store the raw data
                data_entries = data_source.to_database_format(
                    df=df,
                    symbol=symbol,
                    timeframe=timeframe,
                    user_id=DEFAULT_USER_ID
                )
                
                # Set empty indicators object for now
                for entry in data_entries:
                    entry['indicators'] = {}
                
                # Store in database - use replace_existing=True to update any overlapping data
                stored_count = store_market_data_entries(data_entries, replace_existing=True)
                update_count += stored_count
                
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"Updated {stored_count} {symbol} {timeframe} data entries in database"
                )
                
                # Add a small delay to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.bind(user_id=DEFAULT_USER_ID).error(
                    f"Error updating {symbol} {timeframe}: {str(e)}"
                )
    
    if update_count > 0:
        logger.bind(user_id=DEFAULT_USER_ID).info(f"Updated {update_count} data entries in total")
    else:
        logger.bind(user_id=DEFAULT_USER_ID).info("No new data to update")


def compute_indicators_from_stored_data(symbol, timeframe):
    """
    Compute indicators using all stored historical data for a symbol and timeframe.
    
    This function:
    1. Retrieves all stored raw data for a symbol and timeframe
    2. Converts it to a DataFrame
    3. Computes indicators on the complete dataset
    4. Updates the database with the calculated indicators
    
    Args:
        symbol: The trading pair symbol (e.g., 'BTC-USD')
        timeframe: The timeframe (e.g., '1d', '4h', '1h', '15m')
    """
    logger.bind(user_id=DEFAULT_USER_ID).info(
        f"Computing indicators for all stored {symbol} {timeframe} data..."
    )
    
    try:
        # Get all stored data for this symbol and timeframe
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, raw_data, updated_at
                    FROM market_data
                    WHERE user_id = %s AND symbol = %s AND timeframe = %s AND source = 'yfinance'
                    ORDER BY updated_at ASC
                """, (DEFAULT_USER_ID, symbol, timeframe))
                
                records = cur.fetchall()
                
                # Log how many records we found
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"Found {len(records)} records for {symbol} {timeframe}"
                )
                
                if not records:
                    logger.bind(user_id=DEFAULT_USER_ID).warning(
                        f"No stored data found for {symbol} {timeframe}"
                    )
                    return
                
                # Convert records to DataFrame
                data_points = []
                record_ids = []
                
                for record_id, raw_data, timestamp in records:
                    record_ids.append(record_id)
                    
                    # Extract OHLCV data
                    try:
                        # Handle different raw_data formats from the database
                        if isinstance(raw_data, str):
                            try:
                                raw_data = json.loads(raw_data)
                            except json.JSONDecodeError:
                                logger.bind(user_id=DEFAULT_USER_ID).warning(
                                    f"Failed to parse raw_data as JSON: {raw_data[:100]}..."
                                )
                                continue
                        elif isinstance(raw_data, dict):
                            # Already a dictionary, use as is
                            pass
                        else:
                            logger.bind(user_id=DEFAULT_USER_ID).warning(
                                f"Unexpected raw_data type: {type(raw_data)}, value: {str(raw_data)[:100]}..."
                            )
                            continue
                        
                        # Now access the data
                        data_point = {
                            'Open': float(raw_data.get('open', 0)),
                            'High': float(raw_data.get('high', 0)),
                            'Low': float(raw_data.get('low', 0)),
                            'Close': float(raw_data.get('close', 0)),
                            'Volume': float(raw_data.get('volume', 0)),
                            'timestamp': timestamp
                        }
                        
                        # Validate the data point to ensure we have valid values
                        if (data_point['Open'] <= 0 or data_point['High'] <= 0 or
                            data_point['Low'] <= 0 or data_point['Close'] <= 0):
                            logger.bind(user_id=DEFAULT_USER_ID).warning(
                                f"Skipping record with invalid price values: {data_point}"
                            )
                            continue
                            
                    except Exception as e:
                        logger.bind(user_id=DEFAULT_USER_ID).warning(
                            f"Error processing data point: {str(e)}"
                        )
                        continue
                    data_points.append(data_point)
                
                # Create DataFrame
                df = pd.DataFrame(data_points)
                
                # Log the shape of the DataFrame before setting index
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"DataFrame shape before setting index: {df.shape}"
                )
                
                # Convert timestamp to datetime if it's not already
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                
                # Log the shape after setting index
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"DataFrame shape after setting index: {df.shape}"
                )
                
                # Log all unique timestamps to debug
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"Unique timestamps count: {df.index.nunique()}"
                )
                
                if df.empty:
                    logger.bind(user_id=DEFAULT_USER_ID).warning(
                        f"Empty DataFrame created for {symbol} {timeframe}"
                    )
                    return
                
                # Compute indicators
                manager = ExtractionManager()
                indicator_computer = manager.indicator_computers.get('pandas_ta')
                
                if not indicator_computer:
                    logger.bind(user_id=DEFAULT_USER_ID).error("PandasTA indicator computer not found!")
                    return
                
                df_with_indicators = indicator_computer.compute_indicators(df)
                
                # Extract indicators for each record and update database
                indicators_by_timestamp = {}
                ohlcv_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
                indicator_columns = [col for col in df_with_indicators.columns if col not in ohlcv_columns]
                
                for timestamp, row in df_with_indicators.iterrows():
                    indicators = {}
                    
                    for col in indicator_columns:
                        if pd.notnull(row[col]):
                            indicators[col] = float(row[col])
                    
                    indicators_by_timestamp[timestamp] = indicators
                
                # Update each record in the database
                update_count = 0
                
                for record_id, _, timestamp in records:
                    # Handle the timestamp correctly for lookup
                    if isinstance(timestamp, datetime):
                        timestamp_key = timestamp
                    else:
                        timestamp_key = pd.to_datetime(timestamp)
                    
                    # Try to get indicators for this timestamp
                    indicators = indicators_by_timestamp.get(timestamp_key, {})
                    
                    if not indicators and timestamp_key in df_with_indicators.index:
                        # Try direct lookup in DataFrame if the dictionary lookup failed
                        row = df_with_indicators.loc[timestamp_key]
                        indicators = {}
                        
                        for col in indicator_columns:
                            if col in row and pd.notnull(row[col]):
                                indicators[col] = float(row[col])
                    
                    if indicators:
                        indicators_json = json.dumps(indicators)
                        
                        cur.execute("""
                            UPDATE market_data
                            SET indicators = %s
                            WHERE id = %s
                        """, (indicators_json, record_id))
                        
                        update_count += 1
                
                conn.commit()
                
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"Updated indicators for {update_count} {symbol} {timeframe} records"
                )
    
    except Exception as e:
        logger.bind(user_id=DEFAULT_USER_ID).error(
            f"Error computing indicators for {symbol} {timeframe}: {str(e)}"
        )


def check_database_structure():
    """
    Check the database structure to understand what data we have.
    """
    logger.bind(user_id=DEFAULT_USER_ID).info("Checking database structure")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check the total rows
            cur.execute("SELECT COUNT(*) FROM market_data")
            total_rows = cur.fetchone()[0]
            logger.bind(user_id=DEFAULT_USER_ID).info(f"Total rows in market_data: {total_rows}")
            
            # Check rows by symbol and timeframe
            cur.execute("""
                SELECT symbol, timeframe, COUNT(*) 
                FROM market_data 
                GROUP BY symbol, timeframe
                ORDER BY symbol, timeframe
            """)
            results = cur.fetchall()
            for symbol, timeframe, count in results:
                logger.bind(user_id=DEFAULT_USER_ID).info(f"Symbol: {symbol}, Timeframe: {timeframe}, Count: {count}")
            
            # Check a few rows to understand the data structure
            cur.execute("""
                SELECT id, symbol, timeframe, raw_data, updated_at
                FROM market_data
                LIMIT 5
            """)
            samples = cur.fetchall()
            
            for id, symbol, timeframe, raw_data, updated_at in samples:
                raw_data_type = type(raw_data).__name__
                raw_data_preview = str(raw_data)[:100] if raw_data else "None"
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"Sample row: id={id}, symbol={symbol}, timeframe={timeframe}, "
                    f"updated_at={updated_at}, raw_data type={raw_data_type}, "
                    f"preview={raw_data_preview}..."
                )
            
            # Check table schema and constraints
            logger.bind(user_id=DEFAULT_USER_ID).info("Checking table schema and constraints")
            
            # Get table schema
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'market_data'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            logger.bind(user_id=DEFAULT_USER_ID).info("Table schema:")
            for column_name, data_type, is_nullable in columns:
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"  {column_name}: {data_type}, nullable: {is_nullable}"
                )
            
            # Get constraints
            cur.execute("""
                SELECT conname, contype, pg_get_constraintdef(c.oid)
                FROM pg_constraint c
                JOIN pg_class t ON c.conrelid = t.oid
                WHERE t.relname = 'market_data'
            """)
            constraints = cur.fetchall()
            
            logger.bind(user_id=DEFAULT_USER_ID).info("Table constraints:")
            for conname, contype, condef in constraints:
                constraint_type = {
                    'p': 'PRIMARY KEY',
                    'u': 'UNIQUE',
                    'f': 'FOREIGN KEY',
                    'c': 'CHECK'
                }.get(contype, contype)
                
                logger.bind(user_id=DEFAULT_USER_ID).info(
                    f"  {conname} ({constraint_type}): {condef}"
                )


def run_indicator_calculation():
    """
    Calculate indicators for all symbols and timeframes with stored data.
    """
    logger.bind(user_id=DEFAULT_USER_ID).info("Running indicator calculation for all stored data")
    
    # First check the database structure to understand our data
    check_database_structure()
    
    symbols = ['BTC-USD']
    timeframes = ['1d', '4h', '1h', '15m']
    
    for symbol in symbols:
        for timeframe in timeframes:
            compute_indicators_from_stored_data(symbol, timeframe)
    
    logger.bind(user_id=DEFAULT_USER_ID).info("Indicator calculation complete")


def run_scheduled_extraction():
    """Run scheduled extraction for standard timeframes and symbols."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run market data extraction')
    parser.add_argument('--init', action='store_true', help='Initialize historical data')
    parser.add_argument('--force', action='store_true', help='Force initialization even if data exists')
    parser.add_argument('--update', action='store_true', help='Update with only new data')
    parser.add_argument('--indicators', action='store_true', help='Calculate indicators on all stored data')
    parser.add_argument('--check-db', action='store_true', help='Only check database structure')
    
    args = parser.parse_args()
    
    # If no arguments provided, default to update mode
    if not (args.init or args.update or args.indicators or args.check_db):
        args.update = True
    
    if args.check_db:
        # Just check the database structure
        check_database_structure()
        return
    
    if args.init:
        run_initialization(force=args.force)
    
    if args.update:
        run_update()
    
    if args.indicators or args.init or args.update:
        # Always run indicator calculation after init or update
        run_indicator_calculation()


if __name__ == "__main__":
    run_scheduled_extraction()