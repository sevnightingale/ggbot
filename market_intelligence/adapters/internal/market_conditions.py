"""
Market Conditions Adapter

Reads the latest daily market conditions report from Supabase.
Reports are produced by Sebastian (AI research agent) via the
POST /api/v2/market-conditions endpoint and stored in the
market_conditions table.

This adapter reads from Redis cache first (written by the API endpoint
on POST), falling back to a direct DB query if cache is empty.
"""

import json
from datetime import datetime, timezone, timedelta

from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse, AdapterError


class MarketConditionsAdapter(DataAdapter):
    """
    Adapter for Sebastian's daily market conditions reports.

    Reads pre-produced market intelligence from Redis cache (set on POST)
    or falls back to Supabase query. Reports are global (not symbol-specific)
    and refreshed daily.
    """

    name = "market_conditions"
    data_type = "market_conditions"

    REDIS_KEY = "market_conditions:latest"
    MAX_AGE_HOURS = 48  # Serve stale data up to 48h, warn after 26h

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Read the latest market conditions report.

        Checks Redis cache first, falls back to DB query.
        Returns the synthesis + regime + domains + narratives
        formatted for LLM consumption.
        """
        try:
            import asyncio
            data = self._read_from_redis()
            if not data:
                data = await asyncio.to_thread(self._read_from_db)

            if not data:
                raise AdapterError("No market conditions report available. Sebastian may not have run yet.")

            # Check freshness
            generated_at = data.get('generated_at', '')
            if generated_at:
                try:
                    gen_time = datetime.fromisoformat(generated_at)
                    if gen_time.tzinfo is None:
                        gen_time = gen_time.replace(tzinfo=timezone.utc)
                    age_hours = (datetime.now(timezone.utc) - gen_time).total_seconds() / 3600

                    if age_hours > self.MAX_AGE_HOURS:
                        raise AdapterError(f"Market conditions report is {age_hours:.0f}h old (max {self.MAX_AGE_HOURS}h)")

                    if age_hours > 26:
                        self._log.warning(f"Market conditions report is {age_hours:.1f}h old — may be stale")
                except (ValueError, TypeError):
                    pass

            # Format for LLM consumption
            formatted = self._format_for_llm(data)

            return AdapterResponse(
                data=formatted,
                metadata=self.build_metadata(
                    source='sebastian',
                    generated_at=generated_at,
                    schema_version=data.get('schema_version', 'unknown'),
                ),
                confidence=self._calculate_data_confidence(data),
            )

        except AdapterError:
            raise
        except Exception as e:
            self._log.error(f"Failed to read market conditions: {e}")
            raise AdapterError(f"Market conditions fetch failed: {e}")

    def _read_from_redis(self) -> dict | None:
        """Read cached report from Redis."""
        try:
            import redis as sync_redis
            r = sync_redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            cached = r.get(self.REDIS_KEY)
            r.close()

            if cached:
                self._log.debug("Market conditions from Redis cache")
                return json.loads(cached)
        except Exception as e:
            self._log.debug(f"Redis read failed, falling back to DB: {e}")
        return None

    def _read_from_db(self) -> dict | None:
        """Read latest report from Supabase."""
        try:
            from core.common.db import get_db_connection

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT generated_at, schema_version, regime, domains,
                               narratives, synthesis, data_quality, raw_tables
                        FROM market_conditions
                        ORDER BY generated_at DESC
                        LIMIT 1
                    """)
                    row = cur.fetchone()
                    if not row:
                        return None

                    data = {
                        'generated_at': row[0].isoformat() if row[0] else None,
                        'schema_version': row[1],
                        'regime': row[2],
                        'domains': row[3],
                        'narratives': row[4],
                        'synthesis': row[5],
                        'data_quality': row[6],
                        'raw_tables': row[7],
                    }

                    # Cache in Redis for subsequent reads (1 hour TTL)
                    try:
                        import redis as sync_redis
                        r = sync_redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                        r.set(self.REDIS_KEY, json.dumps(data, default=str), ex=3600)
                        r.close()
                    except Exception:
                        pass

                    self._log.debug("Market conditions from DB (cached to Redis)")
                    return data

        except Exception as e:
            self._log.error(f"DB read failed for market conditions: {e}")
            return None

    def _format_for_llm(self, data: dict) -> dict:
        """
        Format market conditions for injection into LLM decision prompt.

        Produces a structured summary that the decision engine can consume.
        """
        regime = data.get('regime', {})
        domains = data.get('domains', {})
        narratives = data.get('narratives', [])
        synthesis = data.get('synthesis', '')

        # Build domain summaries
        domain_lines = []
        for domain_name, domain_data in domains.items():
            if isinstance(domain_data, dict):
                label = domain_name.upper().replace('_', ' ')
                trend = domain_data.get('trend', 'unknown')
                signal = domain_data.get('signal', 'unknown')
                summary = domain_data.get('summary', '')
                domain_lines.append(f"{label}: {trend} ({signal}) — {summary}")

        # Build narrative summaries
        narrative_lines = []
        for n in narratives:
            if isinstance(n, dict):
                name = n.get('name', 'Unknown')
                strength = n.get('strength', 'unknown')
                direction = n.get('direction', 'unknown')
                implication = n.get('implication', '')
                narrative_lines.append(f"• {name} [{strength}, {direction}]: {implication}")

        return {
            'regime': regime.get('overall', 'unknown'),
            'regime_confidence': regime.get('confidence', 'unknown'),
            'regime_driver': regime.get('primary_driver', 'unknown'),
            'domains': domain_lines,
            'narratives': narrative_lines,
            'synthesis': synthesis,
            'generated_at': data.get('generated_at', 'unknown'),
        }

    def _calculate_data_confidence(self, data: dict) -> float:
        """Calculate confidence based on data quality and freshness."""
        confidence = 0.85  # Base confidence for Sebastian's research

        # Freshness penalty
        generated_at = data.get('generated_at', '')
        if generated_at:
            try:
                gen_time = datetime.fromisoformat(generated_at)
                if gen_time.tzinfo is None:
                    gen_time = gen_time.replace(tzinfo=timezone.utc)
                age_hours = (datetime.now(timezone.utc) - gen_time).total_seconds() / 3600

                if age_hours > 24:
                    confidence *= 0.7
                elif age_hours > 12:
                    confidence *= 0.85
            except (ValueError, TypeError):
                confidence *= 0.6

        return max(0.0, min(1.0, confidence))
