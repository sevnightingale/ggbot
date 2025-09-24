"""
MarketData Repository

Provides data access for market data with universal extraction support.
Handles freshness checking, caching, and serves data to multiple users.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from core.common.db import get_db_connection
from core.common.logger import logger
from .market_data import MarketDataSnapshot, DataSource, DataFreshness, Indicator, PriceData, VolumeData
from .models.value_objects import Symbol
from decimal import Decimal


class MarketDataRepository:
    """Repository for market data access with universal extraction support."""
    
    def save_snapshot(self, snapshot: MarketDataSnapshot) -> None:
        """Save a market data snapshot to the database."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Build indicators JSONB
                indicators_json = {}
                for key, indicator in snapshot.indicators.items():
                    indicators_json[key] = {
                        'name': indicator.name,
                        'timeframe': indicator.timeframe,
                        'value': indicator.value,
                        'calculation_time': indicator.calculation_time.isoformat(),
                        'metadata': indicator.metadata
                    }
                
                # Build raw_data JSONB
                raw_data = {
                    'price_data': None,
                    'volume_data': None,
                    'extraction_metadata': {
                        'processing_time_ms': snapshot.processing_time_ms,
                        'extraction_config': snapshot.extraction_config
                    }
                }
                
                if snapshot.price_data:
                    raw_data['price_data'] = {
                        'price': float(snapshot.price_data.price),
                        'timestamp': snapshot.price_data.timestamp.isoformat(),
                        'source': snapshot.price_data.source.value,
                        'bid': float(snapshot.price_data.bid) if snapshot.price_data.bid else None,
                        'ask': float(snapshot.price_data.ask) if snapshot.price_data.ask else None,
                        'volume_24h': float(snapshot.price_data.volume_24h) if snapshot.price_data.volume_24h else None
                    }
                
                if snapshot.volume_data:
                    raw_data['volume_data'] = {
                        'current_volume': float(snapshot.volume_data.current_volume),
                        'average_volume': float(snapshot.volume_data.average_volume),
                        'volume_ratio': float(snapshot.volume_data.volume_ratio),
                        'timeframe': snapshot.volume_data.timeframe,
                        'period_used': snapshot.volume_data.period_used,
                        'timestamp': snapshot.volume_data.timestamp.isoformat(),
                        'confidence_level': snapshot.volume_data.confidence_level
                    }
                
                # Insert or update market data
                cur.execute("""
                    INSERT INTO market_data (
                        user_id, symbol, timeframe, source, data_type,
                        indicators, raw_data, updated_at, config_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, symbol, timeframe, config_id)
                    DO UPDATE SET
                        indicators = EXCLUDED.indicators,
                        raw_data = EXCLUDED.raw_data,
                        source = EXCLUDED.source,
                        data_type = EXCLUDED.data_type,
                        updated_at = EXCLUDED.updated_at
                """, (
                    "universal",  # Universal data for all users
                    snapshot.symbol.internal_format,
                    "mixed",  # Mixed timeframes in one snapshot
                    snapshot.data_source.value,
                    snapshot.data_type.value,
                    json.dumps(indicators_json),
                    json.dumps(raw_data),
                    snapshot.extracted_at,
                    None  # No specific config_id for universal data
                ))
                
                conn.commit()
        
        logger.info(f"Saved market data snapshot for {snapshot.symbol.internal_format} with {len(snapshot.indicators)} indicators")
    
    def get_latest_snapshot(self, symbol: Symbol, 
                          max_age_seconds: int = 30) -> Optional[MarketDataSnapshot]:
        """Get the latest market data snapshot for a symbol."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, symbol, source, data_type, indicators, raw_data, updated_at
                    FROM market_data
                    WHERE symbol = %s 
                    AND updated_at >= %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (symbol.internal_format, datetime.now() - timedelta(seconds=max_age_seconds)))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                return self._row_to_snapshot(row)
    
    def get_fresh_data(self, symbol: Symbol, 
                      required_indicators: List[str] = None) -> Optional[MarketDataSnapshot]:
        """Get fresh market data, checking 30-second freshness requirement."""
        snapshot = self.get_latest_snapshot(symbol, max_age_seconds=30)
        
        if not snapshot:
            logger.info(f"No fresh data for {symbol.internal_format}, extraction needed")
            return None
        
        # Check if we have required indicators
        if required_indicators:
            available_indicators = set(snapshot.indicators.keys())
            required_set = set(required_indicators)
            
            if not required_set.issubset(available_indicators):
                missing = required_set - available_indicators
                logger.info(f"Missing required indicators for {symbol.internal_format}: {missing}")
                return None
        
        logger.info(f"Using fresh cached data for {symbol.internal_format} (age: {snapshot.age_seconds:.1f}s)")
        return snapshot
    
    async def get_fresh_data_for_config(self, symbol: Symbol, config_id: str, 
                                       user_id: Optional[str] = None) -> Optional[MarketDataSnapshot]:
        """
        Get fresh market data for a specific config.
        
        In the current config-driven system, market data is stored per config/user,
        not universally. This method gets data that was extracted for this specific config.
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Query for data that was extracted for this config
                # Current schema uses user_id + config_id combination
                cur.execute("""
                    SELECT id, symbol, source, data_type, indicators, raw_data, updated_at
                    FROM market_data
                    WHERE symbol = %s 
                    AND config_id = %s
                    AND updated_at >= %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (
                    symbol.internal_format, 
                    config_id,
                    datetime.now() - timedelta(seconds=30)  # 30-second freshness
                ))
                
                row = cur.fetchone()
                if not row:
                    logger.info(f"No fresh config-specific data for {symbol.internal_format} (config: {config_id})")
                    return None
                
                snapshot = self._row_to_snapshot(row)
                logger.info(f"Using config-specific fresh data for {symbol.internal_format} (config: {config_id}, age: {snapshot.age_seconds:.1f}s)")
                return snapshot
    
    def needs_extraction(self, symbol: Symbol, 
                        required_indicators: List[str] = None) -> bool:
        """Check if symbol needs fresh data extraction."""
        snapshot = self.get_fresh_data(symbol, required_indicators)
        return snapshot is None
    
    def get_data_freshness(self, symbol: Symbol) -> DataFreshness:
        """Get freshness level of data for a symbol."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT updated_at FROM market_data
                    WHERE symbol = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (symbol.internal_format,))
                
                row = cur.fetchone()
                if not row:
                    return DataFreshness.EXPIRED
                
                age_seconds = (datetime.now() - row[0]).total_seconds()
                
                if age_seconds <= 30:
                    return DataFreshness.FRESH
                elif age_seconds <= 60:
                    return DataFreshness.ACCEPTABLE
                elif age_seconds <= 300:
                    return DataFreshness.STALE
                else:
                    return DataFreshness.EXPIRED
    
    def get_available_symbols(self, min_freshness: DataFreshness = DataFreshness.STALE) -> List[Symbol]:
        """Get symbols with data fresher than minimum requirement."""
        max_age_map = {
            DataFreshness.FRESH: 30,
            DataFreshness.ACCEPTABLE: 60,
            DataFreshness.STALE: 300,
            DataFreshness.EXPIRED: float('inf')
        }
        
        max_age_seconds = max_age_map.get(min_freshness, 300)
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT symbol FROM market_data
                    WHERE updated_at >= %s
                """, (datetime.now() - timedelta(seconds=max_age_seconds),))
                
                return [Symbol.from_string(row[0]) for row in cur.fetchall()]
    
    def cleanup_stale_data(self, older_than_hours: int = 24) -> int:
        """Clean up stale market data older than specified hours."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
                
                cur.execute("""
                    DELETE FROM market_data
                    WHERE updated_at < %s
                """, (cutoff_time,))
                
                deleted_count = cur.rowcount
                conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} stale market data records")
        return deleted_count
    
    def get_extraction_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get extraction statistics for monitoring."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                # Get extraction counts by symbol
                cur.execute("""
                    SELECT 
                        symbol,
                        COUNT(*) as extractions,
                        MAX(updated_at) as last_extraction,
                        AVG(EXTRACT(EPOCH FROM (NOW() - updated_at))) as avg_age_seconds
                    FROM market_data
                    WHERE updated_at >= %s
                    GROUP BY symbol
                    ORDER BY extractions DESC
                """, (cutoff_time,))
                
                symbol_stats = []
                for row in cur.fetchall():
                    symbol_stats.append({
                        'symbol': row[0],
                        'extractions': row[1],
                        'last_extraction': row[2],
                        'avg_age_seconds': float(row[3]) if row[3] else 0
                    })
                
                # Get total stats
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_extractions,
                        COUNT(DISTINCT symbol) as unique_symbols,
                        MIN(updated_at) as earliest_extraction,
                        MAX(updated_at) as latest_extraction
                    FROM market_data
                    WHERE updated_at >= %s
                """, (cutoff_time,))
                
                totals_row = cur.fetchone()
                
                return {
                    'time_period_hours': hours,
                    'total_extractions': totals_row[0] if totals_row[0] else 0,
                    'unique_symbols': totals_row[1] if totals_row[1] else 0,
                    'earliest_extraction': totals_row[2],
                    'latest_extraction': totals_row[3],
                    'symbol_breakdown': symbol_stats
                }
    
    def get_indicator_coverage(self, symbol: Symbol) -> Dict[str, List[str]]:
        """Get available indicators grouped by timeframe for a symbol."""
        snapshot = self.get_latest_snapshot(symbol, max_age_seconds=3600)  # Allow up to 1 hour old
        if not snapshot:
            return {}
        
        coverage = {}
        for indicator_key, indicator in snapshot.indicators.items():
            timeframe = indicator.timeframe
            if timeframe not in coverage:
                coverage[timeframe] = []
            coverage[timeframe].append(indicator.name)
        
        return coverage
    
    async def check_indicators_freshness(self, symbol: Symbol, config_id: str,
                                       required_indicators: List[str], 
                                       max_age_seconds: int = 30) -> Dict[str, bool]:
        """
        Check freshness of specific indicator+timeframe combinations for a config.
        
        Args:
            symbol: Symbol to check
            config_id: Configuration ID  
            required_indicators: List of indicator keys like ["RSI_1h", "MACD_4h", "EMA_15m"]
            max_age_seconds: Maximum age in seconds to consider fresh
            
        Returns:
            Dictionary mapping indicator keys to boolean freshness status
        """
        freshness_status = {}
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get the latest market data for this config
                cur.execute("""
                    SELECT indicators, updated_at
                    FROM market_data 
                    WHERE symbol = %s 
                    AND config_id = %s
                    AND updated_at >= %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (
                    symbol.internal_format,
                    config_id,
                    datetime.now() - timedelta(seconds=max_age_seconds)
                ))
                
                row = cur.fetchone()
                
                if not row:
                    # No fresh data at all - all indicators are stale
                    return {indicator: False for indicator in required_indicators}
                
                indicators_data, updated_at = row
                
                # Check each required indicator
                for indicator_key in required_indicators:
                    # Parse indicator_key (e.g., "RSI_1h" -> indicator="RSI", timeframe="1h")
                    if '_' in indicator_key:
                        indicator_type, timeframe = indicator_key.rsplit('_', 1)
                        
                        # Check if this specific indicator+timeframe exists in the data
                        has_indicator = False
                        if indicators_data:
                            # Look for the indicator in the JSONB data
                            # The key might be stored as "RSI_1h" directly or nested by timeframe
                            if indicator_key in indicators_data:
                                has_indicator = True
                            elif indicator_type in indicators_data:
                                # Check if it's nested by timeframe
                                indicator_data = indicators_data[indicator_type]
                                if isinstance(indicator_data, dict) and timeframe in indicator_data:
                                    has_indicator = True
                        
                        freshness_status[indicator_key] = has_indicator
                    else:
                        # Malformed indicator key
                        freshness_status[indicator_key] = False
        
        return freshness_status
    
    async def get_multi_timeframe_data(self, symbol: Symbol, config_id: str,
                                     max_age_seconds: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get market data across all timeframes for a config, organized by timeframe.
        
        This method supports the new V2 multi-timeframe architecture where data is stored
        separately per timeframe but needs to be consolidated for decision making.
        
        Args:
            symbol: Symbol to query
            config_id: Configuration ID
            max_age_seconds: Maximum age in seconds to consider fresh
            
        Returns:
            Dictionary organized by timeframe with indicators and metadata, or None if no fresh data
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get all fresh market data for this config and symbol across timeframes
                cur.execute("""
                    SELECT timeframe, data_points, raw_data, updated_at 
                    FROM market_data 
                    WHERE symbol = %s 
                    AND config_id = %s
                    AND updated_at >= %s
                    ORDER BY timeframe ASC, updated_at DESC
                """, (
                    symbol.internal_format,
                    config_id,
                    datetime.now() - timedelta(seconds=max_age_seconds)
                ))
                
                rows = cur.fetchall()
                if not rows:
                    logger.info(f"No fresh multi-timeframe data for {symbol.internal_format} (config: {config_id})")
                    return None
                
                # Group by timeframe, taking most recent entry for each
                timeframe_data = {}
                latest_price = None
                oldest_update = None
                
                for timeframe, data_points, raw_data, updated_at in rows:
                    # Only take the first (most recent) entry for each timeframe
                    if timeframe not in timeframe_data:
                        indicators = data_points.get("indicators", {}) if data_points else {}
                        raw_summary = raw_data.get("metadata", {}) if raw_data else {}
                        
                        timeframe_data[timeframe] = {
                            "indicators": indicators,
                            "raw_summary": raw_summary,
                            "updated_at": updated_at
                        }
                        
                        # Extract latest price from first timeframe processed
                        if latest_price is None and raw_summary:
                            latest_price = raw_summary.get("latest_price")
                        
                        # Track oldest update for age calculation
                        if oldest_update is None or updated_at < oldest_update:
                            oldest_update = updated_at
                
                # Calculate data age
                age_seconds = (datetime.now() - oldest_update).total_seconds() if oldest_update else 0
                
                # Prepare consolidated response
                result = {
                    "symbol": symbol.internal_format,
                    "timeframes": timeframe_data,
                    "latest_price": latest_price or 0.0,
                    "data_age_seconds": age_seconds,
                    "timeframes_available": list(timeframe_data.keys())
                }
                
                logger.info(f"Retrieved multi-timeframe data for {symbol.internal_format} "
                           f"(config: {config_id}, {len(timeframe_data)} timeframes, age: {age_seconds:.1f}s)")
                
                return result
    
    def _row_to_snapshot(self, row) -> MarketDataSnapshot:
        """Convert database row to MarketDataSnapshot."""
        record_id, symbol, source, data_type, indicators_json, raw_data_json, updated_at = row
        
        # Parse indicators
        indicators = {}
        if indicators_json:
            for key, indicator_data in indicators_json.items():
                indicator = Indicator(
                    name=indicator_data['name'],
                    timeframe=indicator_data['timeframe'],
                    value=indicator_data['value'],
                    calculation_time=datetime.fromisoformat(indicator_data['calculation_time']),
                    metadata=indicator_data.get('metadata', {})
                )
                indicators[key] = indicator
        
        # Parse price data
        price_data = None
        if raw_data_json and 'price_data' in raw_data_json and raw_data_json['price_data']:
            price_info = raw_data_json['price_data']
            price_data = PriceData(
                symbol=Symbol.from_string(symbol),
                price=Decimal(str(price_info['price'])),
                timestamp=datetime.fromisoformat(price_info['timestamp']),
                source=DataSource(price_info['source']),
                bid=Decimal(str(price_info['bid'])) if price_info['bid'] else None,
                ask=Decimal(str(price_info['ask'])) if price_info['ask'] else None,
                volume_24h=Decimal(str(price_info['volume_24h'])) if price_info['volume_24h'] else None
            )
        
        # Parse volume data
        volume_data = None
        if raw_data_json and 'volume_data' in raw_data_json and raw_data_json['volume_data']:
            volume_info = raw_data_json['volume_data']
            volume_data = VolumeData(
                current_volume=Decimal(str(volume_info['current_volume'])),
                average_volume=Decimal(str(volume_info['average_volume'])),
                volume_ratio=Decimal(str(volume_info['volume_ratio'])),
                timeframe=volume_info['timeframe'],
                period_used=volume_info['period_used'],
                timestamp=datetime.fromisoformat(volume_info['timestamp'])
            )
        
        # Create snapshot
        snapshot = MarketDataSnapshot(
            id=str(record_id),
            symbol=Symbol.from_string(symbol),
            data_source=DataSource(source),
            extracted_at=updated_at,
            indicators=indicators,
            price_data=price_data,
            volume_data=volume_data
        )
        
        # Add extraction metadata
        if raw_data_json and 'extraction_metadata' in raw_data_json:
            metadata = raw_data_json['extraction_metadata']
            snapshot.processing_time_ms = metadata.get('processing_time_ms')
            snapshot.extraction_config = metadata.get('extraction_config', {})
        
        return snapshot


# Global repository instance
market_data_repo = MarketDataRepository()