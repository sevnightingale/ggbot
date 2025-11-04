"""
Supabase Storage Module for V2 Extraction System

Provides Supabase database storage for market data and technical analysis results.
Integrates with the new schema: data_source UUID, data_points JSONB, raw_data JSONB.
"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from supabase import create_client, Client

from core.common.logger import logger
from core.domain.market_data import DataSource


class SupabaseStorage:
    """
    Supabase storage handler for V2 extraction system.
    
    Stores market data and technical analysis results using the new schema:
    - data_source: UUID reference to data_sources table
    - data_points: JSONB with preprocessor analysis results  
    - raw_data: JSONB with OHLCV candles
    """
    
    def __init__(self):
        """Initialize Supabase client with service key for full access."""
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")

        if not self.url or not self.service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")

        self.client: Client = create_client(self.url, self.service_key)
        self._log = logger.bind(component="supabase_storage")

        # Technical Analysis data source UUID from Supabase
        self.TECHNICAL_ANALYSIS_SOURCE_ID = "75f6030b-117e-4178-9bfc-5d1c244ccb96"
    
    def _make_serializable(self, data: Any) -> Any:
        """
        Convert pandas, numpy, and UUID objects to JSON-serializable format.
        """
        import uuid
        
        if isinstance(data, dict):
            return {key: self._make_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        elif isinstance(data, uuid.UUID):
            return str(data)
        elif isinstance(data, pd.Timestamp):
            return data.isoformat()
        elif isinstance(data, pd.Series):
            return data.to_list()
        elif isinstance(data, pd.DataFrame):
            return data.to_dict('records')
        elif hasattr(data, 'item'):  # numpy types
            return data.item()
        elif hasattr(data, '__float__'):
            return float(data)
        elif hasattr(data, '__int__'):
            return int(data)
        else:
            return data
    
    async def store_extraction_result(
        self,
        user_id: str,
        symbol: str,
        timeframe: str,
        raw_candles: pd.DataFrame,
        technical_analysis: Dict[str, Any],
        config_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store extraction results to Supabase market_data table.
        
        Args:
            user_id: User ID
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Timeframe (e.g., "5m", "1h") 
            raw_candles: OHLCV DataFrame from Hummingbot
            technical_analysis: Analysis results from all 21 preprocessors
            config_id: Optional configuration ID
            
        Returns:
            Storage result with status and metadata
        """
        try:
            # Prepare raw OHLCV data
            raw_data = self._make_serializable({
                "candles": raw_candles.to_dict('records'),
                "metadata": {
                    "total_candles": len(raw_candles),
                    "date_range": {
                        "start": raw_candles['timestamp'].iloc[0].isoformat() if not raw_candles.empty else None,
                        "end": raw_candles['timestamp'].iloc[-1].isoformat() if not raw_candles.empty else None
                    },
                    "latest_price": float(raw_candles['close'].iloc[-1]) if not raw_candles.empty else None
                }
            })
            
            # Prepare technical analysis data points
            data_points = self._make_serializable({
                "indicators": technical_analysis,
                "extraction_metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_indicators": len(technical_analysis),
                    "advanced_preprocessing": True,
                    "system_version": "v2"
                }
            })
            
            # Prepare record for insertion
            record = {
                "user_id": user_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "data_source": self.TECHNICAL_ANALYSIS_SOURCE_ID,
                "data_points": data_points,
                "raw_data": raw_data,
                "config_id": config_id,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert record to prevent duplicates (overwrites based on user_id,symbol,timeframe,config_id)
            # on_conflict parameter specifies which constraint to use for upsert
            result = self.client.table('market_data').upsert(
                record,
                on_conflict='user_id,config_id,symbol,timeframe'
            ).execute()
            
            if result.data:
                record_id = result.data[0]['id']
                self._log.info(f"✅ Stored market data for {symbol} ({timeframe}) - Record ID: {record_id}")
                
                return {
                    "status": "success",
                    "record_id": record_id,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "indicators_stored": len(technical_analysis),
                    "candles_stored": len(raw_candles),
                    "storage_timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise Exception("No data returned from upsert operation")
                
        except Exception as e:
            self._log.error(f"❌ Failed to store market data for {symbol}: {str(e)}")
            return {
                "status": "error", 
                "error": str(e),
                "symbol": symbol,
                "timeframe": timeframe
            }
    
    async def get_latest_market_data(
        self,
        user_id: str,
        symbol: str,
        timeframe: str,
        max_age_minutes: int = 60
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve latest market data for a symbol within specified age limit.
        
        Args:
            user_id: User ID
            symbol: Trading pair
            timeframe: Timeframe
            max_age_minutes: Maximum age in minutes
            
        Returns:
            Latest market data or None if not found/too old
        """
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow().replace(microsecond=0)
            cutoff_time = (cutoff_time - pd.Timedelta(minutes=max_age_minutes))
            
            result = self.client.table('market_data').select('id,symbol,timeframe,data_points,updated_at').eq(
                'user_id', user_id
            ).eq(
                'symbol', symbol  
            ).eq(
                'timeframe', timeframe
            ).eq(
                'data_source', self.TECHNICAL_ANALYSIS_SOURCE_ID
            ).gte(
                'updated_at', cutoff_time.isoformat()
            ).order(
                'updated_at', desc=True
            ).limit(1).execute()
            
            if result.data:
                record = result.data[0]
                self._log.info(f"✅ Retrieved market data for {symbol} ({timeframe})")
                return record
            else:
                self._log.info(f"No recent market data found for {symbol} ({timeframe})")
                return None
                
        except Exception as e:
            self._log.error(f"❌ Failed to retrieve market data for {symbol}: {str(e)}")
            return None
    
    async def store_multiple_extractions(
        self,
        extraction_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Store multiple extraction results in batch.
        
        Args:
            extraction_results: List of extraction results to store
            
        Returns:
            Batch storage results
        """
        try:
            successful_stores = 0
            failed_stores = 0
            store_results = []
            
            for result in extraction_results:
                if result.get("status") == "success":
                    extraction_data = result["result"]
                    
                    store_result = await self.store_extraction_result(
                        user_id=result.get("user_id", "default"),
                        symbol=extraction_data["symbol"],
                        timeframe=extraction_data["timeframe"],
                        raw_candles=result.get("raw_candles"),  # This would need to be passed
                        technical_analysis=extraction_data["indicators"],
                        config_id=extraction_data.get("config_id")
                    )
                    
                    if store_result["status"] == "success":
                        successful_stores += 1
                    else:
                        failed_stores += 1
                    
                    store_results.append(store_result)
                else:
                    failed_stores += 1
                    store_results.append({
                        "status": "skipped",
                        "reason": "extraction_failed",
                        "symbol": result.get("symbol", "unknown")
                    })
            
            return {
                "status": "success",
                "total_processed": len(extraction_results),
                "successful_stores": successful_stores,
                "failed_stores": failed_stores,
                "results": store_results
            }
            
        except Exception as e:
            self._log.error(f"❌ Batch storage failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "total_processed": len(extraction_results)
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Supabase connection and table access.
        
        Returns:
            Connection test results
        """
        try:
            # Test basic connection
            result = self.client.table('market_data').select('id').limit(1).execute()
            
            # Test data_sources table access
            sources_result = self.client.table('data_sources').select(
                'source_id, display_name, enabled'
            ).execute()
            
            return {
                "status": "success",
                "market_data_accessible": True,
                "data_sources_count": len(sources_result.data),
                "technical_analysis_source": self.TECHNICAL_ANALYSIS_SOURCE_ID,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }