"""
Storage Module for V2 Extraction System

Provides local PostgreSQL storage for market data and technical analysis results.
Integrates with the schema: data_source UUID, data_points JSONB, raw_data JSONB.
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from psycopg2.extras import RealDictCursor

from core.common.db import (
    db_execute_returning,
    get_db_connection,
)
from core.common.logger import logger
from core.domain.market_data import DataSource


class SupabaseStorage:
    """
    Storage handler for V2 extraction system (local PostgreSQL).

    Stores market data and technical analysis results using the schema:
    - data_source: UUID reference to data_sources table
    - data_points: JSONB with preprocessor analysis results
    - raw_data: JSONB with OHLCV candles
    """

    def __init__(self):
        """Initialize storage handler against local PostgreSQL."""
        self._log = logger.bind(component="supabase_storage")

        # Technical Analysis data source UUID (known orphan: market_data.data_source
        # has no FK; this literal is preserved byte-for-byte and is not a valid
        # data_sources.source_id reference).
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
        Store extraction results to the market_data table.

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

            updated_at = datetime.utcnow().isoformat()

            # Upsert record to prevent duplicates. Conflict target matches the
            # UNIQUE constraint market_data_unique_per_config
            # (user_id, config_id, symbol, timeframe).
            row = await db_execute_returning(
                """
                INSERT INTO market_data
                    (user_id, symbol, timeframe, data_source, data_points, raw_data, config_id, updated_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, config_id, symbol, timeframe)
                DO UPDATE SET
                    data_source = EXCLUDED.data_source,
                    data_points = EXCLUDED.data_points,
                    raw_data    = EXCLUDED.raw_data,
                    updated_at  = EXCLUDED.updated_at
                RETURNING id
                """,
                (
                    user_id,
                    symbol,
                    timeframe,
                    self.TECHNICAL_ANALYSIS_SOURCE_ID,
                    json.dumps(data_points),
                    json.dumps(raw_data),
                    config_id,
                    updated_at,
                ),
            )

            if row:
                record_id = row[0]
                self._log.debug(f"Stored market data for {symbol} ({timeframe}) - Record ID: {record_id}")

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

            def _run():
                with get_db_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute(
                            """
                            SELECT id, symbol, timeframe, data_points, updated_at
                            FROM market_data
                            WHERE user_id = %s
                              AND symbol = %s
                              AND timeframe = %s
                              AND data_source = %s
                              AND updated_at >= %s
                            ORDER BY updated_at DESC
                            LIMIT 1
                            """,
                            (
                                user_id,
                                symbol,
                                timeframe,
                                self.TECHNICAL_ANALYSIS_SOURCE_ID,
                                cutoff_time.isoformat(),
                            ),
                        )
                        row = cur.fetchone()
                        # Return a plain dict so the shape matches PostgREST .data[0]
                        return dict(row) if row is not None else None

            import asyncio
            record = await asyncio.to_thread(_run)

            if record:
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
        Test database connection and table access.

        Returns:
            Connection test results
        """
        try:
            def _run():
                with get_db_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        # Test basic connection / market_data access
                        cur.execute("SELECT id FROM market_data LIMIT 1")
                        cur.fetchall()

                        # Test data_sources table access
                        cur.execute(
                            "SELECT source_id, display_name, enabled FROM data_sources"
                        )
                        return cur.fetchall()

            import asyncio
            sources_rows = await asyncio.to_thread(_run)

            return {
                "status": "success",
                "market_data_accessible": True,
                "data_sources_count": len(sources_rows),
                "technical_analysis_source": self.TECHNICAL_ANALYSIS_SOURCE_ID,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
