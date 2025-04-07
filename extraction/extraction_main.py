"""
Main extraction module that manages data sources and indicators.

This module provides the main functionality for extracting market data from
various sources, computing technical indicators, and storing the data in the
database for use by the decision module.

It supports two types of data sources:
1. Standard sources that implement the DataSource interface (like YFinanceDataSource)
2. Specialized sources with their own extraction scripts (like TradingView)
"""
import os
import sys
import time
import json
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

from common.logger import logger
from common.config import DEFAULT_USER_ID

from extraction.sources import YFinanceDataSource
from extraction.indicators import PandasTAIndicators
from extraction.utils import store_market_data_entries


class ExtractionManager:
    """
    Manages the extraction of market data from various sources.
    
    This class coordinates between data sources, indicator computers, and the
    database to ensure that up-to-date market data is available for trading
    decisions.
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        """
        Initialize the ExtractionManager.
        
        Args:
            user_id: User ID to associate with the extracted data
        """
        self.user_id = user_id
        self.data_sources = {}
        self.indicator_computers = {}
        
        # Register default implementations
        self.register_data_source('yfinance', YFinanceDataSource())
        self.register_indicator_computer('pandas_ta', PandasTAIndicators())
    
    def register_data_source(self, name: str, data_source) -> None:
        """
        Register a data source.
        
        Args:
            name: Name to register the data source under
            data_source: DataSource implementation to register
        """
        self.data_sources[name] = data_source
        logger.bind(user_id=self.user_id).info(f"Registered data source: {name}")
    
    def register_indicator_computer(self, name: str, indicator_computer) -> None:
        """
        Register an indicator computer.
        
        Args:
            name: Name to register the indicator computer under
            indicator_computer: IndicatorComputer implementation to register
        """
        self.indicator_computers[name] = indicator_computer
        logger.bind(user_id=self.user_id).info(f"Registered indicator computer: {name}")
    
    def extract_market_data(
        self,
        symbol: str,
        timeframe: str,
        data_source_name: str = 'yfinance',
        indicator_computer_name: str = 'pandas_ta',
        days_of_history: int = 60,
        store_in_db: bool = True
    ) -> List[Dict]:
        """
        Extract market data for a specific symbol and timeframe.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USD')
            timeframe: Timeframe (e.g., '15m', '1h', '4h', '1d')
            data_source_name: Name of the data source to use
            indicator_computer_name: Name of the indicator computer to use
            days_of_history: Number of days of historical data to fetch
            store_in_db: Whether to store the data in the database
            
        Returns:
            List of dictionaries containing the market data
        """
        # Special handling for tradingview source
        if data_source_name == 'tradingview':
            return self.extract_from_tradingview(symbol, timeframe, store_in_db)
        
        # Get the data source and indicator computer
        data_source = self.data_sources.get(data_source_name)
        if not data_source:
            logger.bind(user_id=self.user_id).error(f"Data source not found: {data_source_name}")
            return []
        
        indicator_computer = self.indicator_computers.get(indicator_computer_name)
        if not indicator_computer:
            logger.bind(user_id=self.user_id).error(f"Indicator computer not found: {indicator_computer_name}")
            return []
        
        try:
            # Fetch historical data
            logger.bind(user_id=self.user_id).info(
                f"Extracting {days_of_history} days of {symbol} {timeframe} data from {data_source_name}"
            )
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_of_history)
            
            df = data_source.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                logger.bind(user_id=self.user_id).warning(
                    f"No data found for {symbol} {timeframe} from {data_source_name}"
                )
                return []
            
            # Compute indicators
            logger.bind(user_id=self.user_id).info(
                f"Computing indicators for {symbol} {timeframe} using {indicator_computer_name}"
            )
            
            df_with_indicators = indicator_computer.compute_indicators(df)
            
            # Convert to database format
            data_entries = data_source.to_database_format(
                df=df_with_indicators,
                symbol=symbol,
                timeframe=timeframe,
                user_id=self.user_id
            )
            
            data_entries = indicator_computer.to_database_format(
                df=df_with_indicators,
                data_entries=data_entries
            )
            
            # Store in database if requested
            if store_in_db:
                stored_count = store_market_data_entries(data_entries)
                logger.bind(user_id=self.user_id).info(
                    f"Stored {stored_count} {symbol} {timeframe} data entries in database"
                )
            
            return data_entries
            
        except Exception as e:
            logger.bind(user_id=self.user_id).error(
                f"Error extracting market data for {symbol} {timeframe}: {str(e)}"
            )
            return []
    
    def extract_from_tradingview(self, symbol: str, timeframe: str, store_in_db: bool = True) -> List[Dict]:
        """
        Extract market data from TradingView using the specialized script.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSD')
            timeframe: Timeframe (e.g., '15m', '1h', '4h', '1d')
            store_in_db: Whether to store the data in the database
            
        Returns:
            List of dictionaries containing the market data
        """
        logger.bind(user_id=self.user_id).info(
            f"Running TradingView extraction script for {symbol} {timeframe}"
        )
        
        try:
            # Run the TradingView extraction script as a subprocess
            script_path = os.path.join(
                os.path.dirname(__file__), 
                'sources', 'tradingview', 'run_extraction.py'
            )
            
            # Execute the script with symbol and timeframe as arguments
            process = subprocess.run(
                [sys.executable, script_path, symbol, timeframe],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check the output file for results
            output_file = os.path.join(
                os.path.dirname(__file__), 
                'sources', 'tradingview', f'ggshot_{timeframe}_summary.txt'
            )
            
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    report_text = f.read()
                
                # Create a data entry in our standard format
                data_entry = {
                    'user_id': self.user_id,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'source': 'tradingview',
                    'data_type': 'report',
                    'raw_data': {},
                    'indicators': {'report': report_text},
                    'updated_at': datetime.now()
                }
                
                data_entries = [data_entry]
                
                # Store in database if requested
                if store_in_db:
                    stored_count = store_market_data_entries(data_entries)
                    logger.bind(user_id=self.user_id).info(
                        f"Stored {stored_count} TradingView reports in database"
                    )
                
                return data_entries
            else:
                logger.bind(user_id=self.user_id).error(
                    f"TradingView extraction output file not found: {output_file}"
                )
                return []
        
        except subprocess.CalledProcessError as e:
            logger.bind(user_id=self.user_id).error(
                f"Error running TradingView extraction script: {e.stderr}"
            )
            return []
        
        except Exception as e:
            logger.bind(user_id=self.user_id).error(
                f"Error extracting data from TradingView: {str(e)}"
            )
            return []
    
    def extract_multiple(
        self,
        symbols: List[str],
        timeframes: List[str],
        data_source_name: str = 'yfinance',
        indicator_computer_name: str = 'pandas_ta',
        days_of_history: int = 60,
        store_in_db: bool = True
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Extract market data for multiple symbols and timeframes.
        
        Args:
            symbols: List of trading pair symbols (e.g., ['BTC-USD', 'ETH-USD'])
            timeframes: List of timeframes (e.g., ['15m', '1h', '4h', '1d'])
            data_source_name: Name of the data source to use
            indicator_computer_name: Name of the indicator computer to use
            days_of_history: Number of days of historical data to fetch
            store_in_db: Whether to store the data in the database
            
        Returns:
            Dictionary of symbols to timeframes to market data entries
        """
        results = {}
        
        for symbol in symbols:
            results[symbol] = {}
            
            for timeframe in timeframes:
                logger.bind(user_id=self.user_id).info(
                    f"Extracting {symbol} {timeframe} data..."
                )
                
                data_entries = self.extract_market_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    data_source_name=data_source_name,
                    indicator_computer_name=indicator_computer_name,
                    days_of_history=days_of_history,
                    store_in_db=store_in_db
                )
                
                results[symbol][timeframe] = data_entries
                
                # Add a small delay to avoid rate limiting
                time.sleep(1)
        
        return results
    
    def scheduled_extraction(
        self,
        symbols: List[str],
        timeframes: List[str],
        data_sources: List[str] = ['yfinance'],
        indicator_computer_name: str = 'pandas_ta',
        days_of_history: Optional[int] = None
    ) -> None:
        """
        Run scheduled extraction for all specified symbols, timeframes, and data sources.
        
        Args:
            symbols: List of trading pair symbols (e.g., ['BTC-USD', 'ETH-USD'])
            timeframes: List of timeframes (e.g., ['15m', '1h', '4h', '1d'])
            data_sources: List of data source names to use
            indicator_computer_name: Name of the indicator computer to use
            days_of_history: Number of days of historical data to fetch (if None, uses timeframe-specific defaults)
        """
        logger.bind(user_id=self.user_id).info(
            f"Running scheduled extraction for symbols={symbols}, "
            f"timeframes={timeframes}, sources={data_sources}"
        )
        
        # Configure days of history per timeframe based on yfinance limitations
        timeframe_config = {
            '1d': 730,   # 2 years for daily data
            '4h': 730,   # 2 years for 4h data
            '1h': 730,   # 2 years for hourly data
            '15m': 60    # 60 days for 15-min data (yfinance limit)
        }
        
        for data_source_name in data_sources:
            try:
                if days_of_history is not None:
                    # Use the provided days_of_history for all timeframes
                    results = self.extract_multiple(
                        symbols=symbols,
                        timeframes=timeframes,
                        data_source_name=data_source_name,
                        indicator_computer_name=indicator_computer_name,
                        days_of_history=days_of_history,
                        store_in_db=True
                    )
                else:
                    # Process each timeframe with its specific history limit
                    results = {}
                    for symbol in symbols:
                        results[symbol] = {}
                        
                        for timeframe in timeframes:
                            # Get appropriate history length for this timeframe
                            days = timeframe_config.get(timeframe, 60)  # Default to 60 days if unknown timeframe
                            
                            logger.bind(user_id=self.user_id).info(
                                f"Extracting {symbol} {timeframe} with {days} days of history..."
                            )
                            
                            data_entries = self.extract_market_data(
                                symbol=symbol,
                                timeframe=timeframe,
                                data_source_name=data_source_name,
                                indicator_computer_name=indicator_computer_name,
                                days_of_history=days,
                                store_in_db=True
                            )
                            
                            results[symbol][timeframe] = data_entries
                            
                            # Add a small delay to avoid rate limiting
                            time.sleep(1)
                
                # Log the results
                for symbol, timeframe_data in results.items():
                    for timeframe, data_entries in timeframe_data.items():
                        logger.bind(user_id=self.user_id).info(
                            f"Extracted {len(data_entries)} {symbol} {timeframe} "
                            f"data entries from {data_source_name}"
                        )
            
            except Exception as e:
                logger.bind(user_id=self.user_id).error(
                    f"Error in scheduled extraction for {data_source_name}: {str(e)}"
                )


def main():
    """Main function to run the extraction process."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Run market data extraction')
    parser.add_argument('--symbols', type=str, nargs='+', default=['BTC-USD'],
                        help='Trading pair symbols to extract data for')
    parser.add_argument('--timeframes', type=str, nargs='+', default=['1d', '4h', '1h', '15m'],
                        help='Timeframes to extract data for')
    parser.add_argument('--sources', type=str, nargs='+', default=['yfinance'],
                        help='Data sources to use')
    parser.add_argument('--days', type=int, default=None,
                        help='Number of days of historical data to fetch (overrides timeframe defaults)')
    parser.add_argument('--user-id', type=str, default=DEFAULT_USER_ID,
                        help='User ID to associate with the extracted data')
    parser.add_argument('--indicators', action='store_true',
                        help='Calculate indicators after extraction')
    
    args = parser.parse_args()
    
    # Create an extraction manager
    manager = ExtractionManager(user_id=args.user_id)
    
    # Run the extraction
    manager.scheduled_extraction(
        symbols=args.symbols,
        timeframes=args.timeframes,
        data_sources=args.sources,
        days_of_history=args.days  # Will be None by default, triggering timeframe-specific limits
    )
    
    # Calculate indicators if requested
    if args.indicators:
        logger.bind(user_id=args.user_id).info("Calculating indicators on all stored data")
        
        # Import here to avoid circular import
        from extraction.scheduled_extraction import run_indicator_calculation
        run_indicator_calculation()
    
    logger.bind(user_id=args.user_id).info("Extraction complete")


if __name__ == "__main__":
    main()