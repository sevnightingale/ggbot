"""
ggShot Signals Adapter

Fetches latest ggShot trading signals for a symbol across all timeframes.
Queries the market_data table where signals are stored by the listener service.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any

from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse, AdapterError
from core.common.db import get_db_connection


class GGShotAdapter(DataAdapter):
    """
    Adapter for ggShot trading signals.

    Fetches the latest signal for each timeframe for a given symbol
    from the market_data table.
    """

    name = "ggshot_adapter"
    data_type = "ggshot_signals"

    def __init__(self):
        """Initialize adapter."""
        super().__init__()
        self._signals_source_id = None

    def _get_signals_source_id(self) -> str:
        """Get UUID of 'trading_signals' data source."""
        if self._signals_source_id:
            return self._signals_source_id

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT source_id FROM data_sources
                    WHERE name = 'trading_signals'
                """)
                result = cur.fetchone()
                if not result:
                    raise AdapterError("trading_signals data source not found in database. Make sure signals are seeded.")
                self._signals_source_id = str(result[0])
                return self._signals_source_id

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Fetch latest ggShot signals for a symbol across all timeframes.

        Args:
            params: Must contain 'symbol' (e.g., 'BTC/USDT')
                   Optional: 'include_raw' (boolean) to include raw Telegram messages

        Returns:
            AdapterResponse with signals organized by timeframe
        """
        symbol = params.get('symbol')
        if not symbol:
            raise AdapterError("symbol parameter is required")

        include_raw = params.get('include_raw', False)

        try:
            # Get data source ID
            signals_source_id = self._get_signals_source_id()

            # Query for latest signal per timeframe
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Use DISTINCT ON to get latest signal per timeframe
                    cur.execute("""
                        SELECT DISTINCT ON (timeframe)
                            timeframe,
                            data_points,
                            raw_data,
                            updated_at
                        FROM market_data
                        WHERE symbol = %s
                          AND data_source = %s
                        ORDER BY timeframe, updated_at DESC
                    """, (symbol, signals_source_id))

                    rows = cur.fetchall()

            if not rows:
                self._log.info(f"No ggShot signals found for {symbol}")
                return AdapterResponse(
                    data={
                        'signals': {},
                        'metadata': {
                            'symbol': symbol,
                            'timeframes_found': [],
                            'latest_signal_age': None,
                            'query_timestamp': datetime.now(timezone.utc).isoformat()
                        }
                    },
                    metadata={'source': 'ggshot', 'symbol': symbol, 'row_count': 0},
                    confidence=0.5,  # Lower confidence when no signals
                    related_queries=[
                        f"Check if ggShot has any signals for {symbol}",
                        "Query technical indicators as alternative"
                    ]
                )

            # Parse signals into structured format
            signals_by_timeframe = {}
            timeframes_found = []
            latest_timestamp = None

            for row in rows:
                timeframe, data_points_json, raw_data_json, updated_at = row

                # Parse data_points JSONB
                data_points = json.loads(data_points_json) if isinstance(data_points_json, str) else data_points_json
                ggshot_signal = data_points.get('ggshot_signal', {})

                # Parse raw_data JSONB (optional)
                raw_data = json.loads(raw_data_json) if isinstance(raw_data_json, str) else raw_data_json

                # Build signal object
                signal = {
                    'direction': ggshot_signal.get('direction'),
                    'entry_zone': ggshot_signal.get('entry_zone'),
                    'stop_loss': ggshot_signal.get('stop_loss'),
                    'take_profit': ggshot_signal.get('take_profit'),
                    'targets': ggshot_signal.get('targets', []),
                    'confidence': ggshot_signal.get('confidence'),
                    'strategy_accuracy': ggshot_signal.get('strategy_accuracy'),
                    'trend_line': ggshot_signal.get('trend_line'),
                    'timestamp': updated_at.isoformat() if updated_at else None
                }

                # Include raw message if requested
                if include_raw and raw_data:
                    signal['raw_message'] = raw_data.get('telegram_message')

                signals_by_timeframe[timeframe] = signal
                timeframes_found.append(timeframe)

                # Track latest timestamp
                if not latest_timestamp or updated_at > latest_timestamp:
                    latest_timestamp = updated_at

            # Calculate age of latest signal
            if latest_timestamp:
                age_seconds = (datetime.now(timezone.utc) - latest_timestamp.replace(tzinfo=timezone.utc)).total_seconds()
                if age_seconds < 3600:
                    age_str = f"{int(age_seconds / 60)} minutes ago"
                elif age_seconds < 86400:
                    age_str = f"{int(age_seconds / 3600)} hours ago"
                else:
                    age_str = f"{int(age_seconds / 86400)} days ago"
            else:
                age_str = "unknown"

            # Calculate confidence based on signal age
            if age_seconds < 3600:  # Less than 1 hour
                confidence = 1.0
            elif age_seconds < 86400:  # Less than 1 day
                confidence = 0.9
            elif age_seconds < 86400 * 3:  # Less than 3 days
                confidence = 0.7
            else:
                confidence = 0.5

            response_data = {
                'signals': signals_by_timeframe,
                'metadata': {
                    'symbol': symbol,
                    'timeframes_found': timeframes_found,
                    'latest_signal_age': age_str,
                    'query_timestamp': datetime.now(timezone.utc).isoformat()
                }
            }

            self._log.info(f"Fetched {len(timeframes_found)} ggShot signals for {symbol}: {timeframes_found}")

            return AdapterResponse(
                data=response_data,
                metadata={
                    'source': 'ggshot',
                    'symbol': symbol,
                    'row_count': len(rows),
                    'timeframes': timeframes_found,
                    'latest_signal_timestamp': latest_timestamp.isoformat() if latest_timestamp else None
                },
                confidence=confidence,
                related_queries=[
                    f"Query technical indicators for {symbol} to compare",
                    f"Check news for {symbol} to validate signal context"
                ]
            )

        except Exception as e:
            self._log.error(f"Error fetching ggShot signals for {symbol}: {e}")
            raise AdapterError(f"Failed to fetch ggShot signals: {str(e)}")


# Module-level alias for dynamic loading by gateway (must match catalog YAML adapter name)
ggshot_adapter = GGShotAdapter
