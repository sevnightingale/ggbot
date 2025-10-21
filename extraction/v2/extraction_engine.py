"""
V2 Extraction Engine - Clean Python-native technical analysis system.

This module provides the main extraction engine that coordinates data fetching
from Hummingbot API and technical analysis using pandas-ta.
"""

import asyncio
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from core.config.config_main import get_configuration

from .universal_data_client import UniversalDataClient
from .indicators import TechnicalIndicators
from .file_storage import FileStorage
from .supabase_storage import SupabaseStorage
from .smart_limits import get_batch_limit, get_efficiency_report


class ExtractionEngineV2:
    """
    Clean, Python-native extraction engine.
    
    Coordinates data fetching from Hummingbot API and technical analysis
    using pandas-ta with simple analytical preprocessing.
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID, use_advanced_preprocessing: bool = True, use_database_storage: bool = True, use_file_storage: bool = False):
        """
        Initialize extraction engine with configurable storage options.
        
        Args:
            user_id: User ID for configuration and logging
            use_advanced_preprocessing: Enable sophisticated analysis preprocessing
            use_database_storage: Store results to Supabase database
            use_file_storage: Store results to local files (useful for debugging, disable for production)
        """
        self.user_id = user_id
        self.use_database_storage = use_database_storage
        self.use_file_storage = use_file_storage

        # Core components - Using Universal Data Layer
        self.data_client = UniversalDataClient()  # Drop-in replacement for HummingbotDataClient
        self.indicators = TechnicalIndicators(use_advanced_preprocessing=use_advanced_preprocessing)
        
        # Configurable storage system
        self.file_storage = FileStorage(base_dir=f"extraction_results/{user_id}") if use_file_storage else None
        self.supabase_storage = SupabaseStorage() if use_database_storage else None
        
        self._log = logger.bind(user_id=user_id, component="extraction_v2")
        mode = "advanced" if use_advanced_preprocessing else "simple"
        
        # Determine storage description
        storage_parts = []
        if use_database_storage:
            storage_parts.append("database")
        if use_file_storage:
            storage_parts.append("files")
        if not storage_parts:
            storage_parts.append("none")
        storage = " + ".join(storage_parts)
        
        self._log.info(f"Initialized ExtractionEngineV2 with {mode} preprocessing, {storage} storage")

    async def cleanup(self):
        """Cleanup resources when engine is destroyed or no longer needed."""
        if self.data_client:
            await self.data_client.disconnect()
            self._log.info("ExtractionEngineV2 cleanup completed")

    async def extract_for_symbol(
        self,
        symbol: str,
        indicators: List[str],
        timeframe: str = "1h",
        limit: int = 200,
        connector: str = "kucoin",
        config_id: Optional[str] = None,
        **indicator_params
    ) -> Dict[str, Any]:
        """
        Extract technical indicators for a single symbol.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            indicators: List of indicators to calculate
            timeframe: Candle timeframe
            limit: Number of candles to fetch
            connector: Exchange connector
            config_id: Configuration ID (optional)
            **indicator_params: Custom indicator parameters
            
        Returns:
            Dictionary with extraction results
        """
        # Use smart limit if not explicitly provided
        smart_limit = get_batch_limit(indicators, timeframe)
        if smart_limit != 200:  # Only log if different from default
            efficiency = get_efficiency_report(indicators, timeframe)
            self._log.info(f"Smart limits: using {smart_limit} candles (vs 200 static), saving {efficiency['percent_reduction']}%")

        actual_limit = limit if limit != 200 else smart_limit
        self._log.info(f"Extracting {len(indicators)} indicators for {symbol} ({timeframe}) with {actual_limit} candles")

        try:
            # Step 1: Fetch OHLCV data from Hummingbot with multi-exchange fallback
            # Use ensure_connected() instead of context manager to avoid race conditions in parallel execution
            await self.data_client.ensure_connected()
            df = await self.data_client.get_candles_with_fallback(symbol, timeframe, actual_limit)
            
            if df.empty:
                raise ValueError(f"No data received for {symbol}")
            
            self._log.info(f"✅ Fetched {len(df)} candles for {symbol}")
            
            # Step 2: Calculate technical indicators
            indicator_results = self.indicators.calculate_multiple(df, indicators, **indicator_params)
            
            # Step 3: Add metadata
            extraction_result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "connector": connector,
                "data_points": len(df),
                "limit_used": actual_limit,
                "timestamp": datetime.utcnow().isoformat(),
                "indicators": indicator_results,
                "config_id": config_id,
                "ohlcv_summary": {
                    "latest_price": float(df['close'].iloc[-1]),
                    "price_change_24h": float((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100) if len(df) >= 24 else None,
                    "volume_24h": float(df['volume'].iloc[-24:].sum()) if len(df) >= 24 else None,
                    "date_range": {
                        "start": df['timestamp'].iloc[0].isoformat(),
                        "end": df['timestamp'].iloc[-1].isoformat()
                    }
                }
            }
            
            # Step 4: Store results (dual storage)
            storage_results = {}
            
            # File storage (optional)
            if self.use_file_storage and self.file_storage:
                stored_path = self.file_storage.save_extraction_result(extraction_result, "single")
                storage_results["file"] = {
                    "status": "success" if stored_path else "error",
                    "path": stored_path
                }
            else:
                storage_results["file"] = {
                    "status": "disabled",
                    "path": None
                }
            
            # Database storage (if enabled)
            if self.supabase_storage:
                db_result = await self.supabase_storage.store_extraction_result(
                    user_id=self.user_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    raw_candles=df,  # Pass the raw DataFrame
                    technical_analysis=indicator_results,
                    config_id=config_id
                )
                storage_results["database"] = db_result
            
            extraction_result["storage"] = storage_results
            
            self._log.info(f"✅ Extraction complete for {symbol} (stored to {len(storage_results)} systems)")
            return {
                "status": "success",
                "result": extraction_result
            }
            
        except Exception as e:
            self._log.error(f"❌ Extraction failed for {symbol}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "symbol": symbol,
                "timeframe": timeframe
            }
    
    async def extract_for_config(self, config_id: str) -> Dict[str, Any]:
        """
        Extract indicators based on user configuration.
        
        Args:
            config_id: Configuration ID to load settings from
            
        Returns:
            Dictionary with extraction results for all configured symbols
        """
        self._log.info(f"Starting extraction for config_id: {config_id}")
        
        try:
            # Load configuration
            config = get_configuration(user_id=self.user_id, config_id=config_id)
            if not config:
                raise ValueError(f"Configuration not found for config_id: {config_id}")
            
            extraction_config = config.get('extraction', {})
            
            # Extract configuration parameters
            symbols = extraction_config.get('symbols', ['BTC/USDT'])
            timeframe = extraction_config.get('timeframe', '1h')
            indicators = extraction_config.get('indicators', ['RSI'])
            connector = extraction_config.get('connector', 'kucoin')
            limit = extraction_config.get('limit', 200)
            
            self._log.info(f"Config loaded: {len(symbols)} symbols, {len(indicators)} indicators")
            
            # Extract for all symbols
            results = {}
            for symbol in symbols:
                result = await self.extract_for_symbol(
                    symbol=symbol,
                    indicators=indicators,
                    timeframe=timeframe,
                    limit=limit,
                    connector=connector,
                    config_id=config_id
                )
                results[symbol] = result
            
            # Summary statistics
            successful_extractions = sum(1 for r in results.values() if r["status"] == "success")
            
            # Store batch results to file
            batch_result = {
                "status": "success",
                "config_id": config_id,
                "results": results,
                "summary": {
                    "total_symbols": len(symbols),
                    "successful_extractions": successful_extractions,
                    "failed_extractions": len(symbols) - successful_extractions
                }
            }
            
            if self.use_file_storage and self.file_storage:
                batch_path = self.file_storage.save_extraction_result(batch_result, "config")
                batch_result["file_path"] = batch_path
            else:
                batch_result["file_path"] = None
            
            return batch_result
            
        except Exception as e:
            self._log.error(f"❌ Config extraction failed for {config_id}: {str(e)}")
            return {
                "status": "error",
                "config_id": config_id,
                "error": str(e)
            }
    
    async def extract_multiple_symbols(
        self,
        symbols: List[str],
        indicators: List[str],
        timeframe: str = "1h",
        limit: int = 200,
        connector: str = "kucoin",
        config_id: Optional[str] = None,
        **indicator_params
    ) -> Dict[str, Any]:
        """
        Extract indicators for multiple symbols efficiently.
        
        Args:
            symbols: List of trading pairs
            indicators: List of indicators to calculate
            timeframe: Candle timeframe
            limit: Number of candles to fetch
            connector: Exchange connector
            config_id: Configuration ID (optional)
            **indicator_params: Custom indicator parameters
            
        Returns:
            Dictionary with results for all symbols
        """
        self._log.info(f"Extracting for {len(symbols)} symbols: {symbols}")
        
        # Extract for all symbols concurrently
        tasks = []
        for symbol in symbols:
            task = self.extract_for_symbol(
                symbol=symbol,
                indicators=indicators,
                timeframe=timeframe,
                limit=limit,
                connector=connector,
                config_id=config_id,
                **indicator_params
            )
            tasks.append(task)
        
        # Execute all extractions concurrently
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results by symbol
        results = {}
        for i, symbol in enumerate(symbols):
            result = results_list[i]
            if isinstance(result, Exception):
                results[symbol] = {
                    "status": "error",
                    "error": str(result),
                    "symbol": symbol
                }
            else:
                results[symbol] = result
        
        # Summary statistics
        successful = sum(1 for r in results.values() if r.get("status") == "success")
        
        # Store batch results  
        batch_result = {
            "status": "success",
            "results": results,
            "summary": {
                "total_symbols": len(symbols),
                "successful_extractions": successful,
                "failed_extractions": len(symbols) - successful
            }
        }
        
        if self.use_file_storage and self.file_storage:
            batch_path = self.file_storage.save_multiple_results(results, f"{len(symbols)}_symbols")
            batch_result["file_path"] = batch_path
        else:
            batch_result["file_path"] = None
        
        return batch_result
    
    
    async def test_system(self) -> Dict[str, Any]:
        """
        Test the entire V2 extraction system.
        
        Returns:
            Dictionary with test results
        """
        self._log.info("Testing V2 extraction system...")
        
        test_results = {}
        
        # Test 1: Data client connection
        try:
            await self.data_client.ensure_connected()
            connection_test = await self.data_client.test_connection()
            test_results["data_client"] = connection_test
        except Exception as e:
            test_results["data_client"] = {"status": "error", "error": str(e)}
        
        # Test 2: Supabase connection (if enabled)
        if self.supabase_storage:
            try:
                supabase_test = await self.supabase_storage.test_connection()
                test_results["supabase"] = supabase_test
            except Exception as e:
                test_results["supabase"] = {"status": "error", "error": str(e)}
        else:
            test_results["supabase"] = {"status": "skipped", "reason": "database storage disabled"}
        
        # Test 3: Simple extraction
        try:
            result = await self.extract_for_symbol(
                symbol="BTC/USDT",
                indicators=["rsi", "sma"],
                timeframe="1h",
                limit=50
            )
            test_results["extraction"] = {"status": result["status"]}
            if result["status"] == "success":
                test_results["extraction"]["indicators_calculated"] = len(result["result"]["indicators"])
                test_results["extraction"]["data_points"] = result["result"]["data_points"]
        except Exception as e:
            test_results["extraction"] = {"status": "error", "error": str(e)}
        
        # Test 4: Indicator calculations
        try:
            available = self.indicators.get_available_indicators()
            test_results["indicators"] = {
                "status": "success",
                "available_count": len(available),
                "available_indicators": available
            }
        except Exception as e:
            test_results["indicators"] = {"status": "error", "error": str(e)}
        
        overall_status = "success" if all(
            test.get("status") == "success" for test in test_results.values()
        ) else "partial_success"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "tests": test_results
        }


# Convenience functions for direct usage
async def extract_indicators(
    symbol: str,
    indicators: List[str],
    timeframe: str = "1h",
    limit: int = 200,
    user_id: str = DEFAULT_USER_ID,
    use_advanced_preprocessing: bool = True
) -> Dict[str, Any]:
    """
    Convenience function for quick indicator extraction.
    
    Args:
        symbol: Trading pair (e.g., "BTC/USDT")
        indicators: List of indicators to calculate
        timeframe: Candle timeframe
        limit: Number of candles to fetch
        user_id: User ID for logging
        use_advanced_preprocessing: Enable sophisticated analysis
        
    Returns:
        Extraction results
    """
    engine = ExtractionEngineV2(user_id, use_advanced_preprocessing)
    return await engine.extract_for_symbol(symbol, indicators, timeframe, limit)


async def test_v2_system(user_id: str = DEFAULT_USER_ID, advanced: bool = True) -> Dict[str, Any]:
    """
    Convenience function to test the V2 extraction system.
    
    Args:
        user_id: User ID for testing
        advanced: Use advanced preprocessing
        
    Returns:
        Test results
    """
    engine = ExtractionEngineV2(user_id, use_advanced_preprocessing=advanced)
    return await engine.test_system()