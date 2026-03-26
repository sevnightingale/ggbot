"""
ACP Agent Adapter — Market Intelligence from Virtuals ACP agents.

Generic adapter that works with ANY ACP agent. Parameterized via
params_template in catalog_mapping.py. Each curated agent gets a
mapping entry, but they all route through this single adapter.

Cache-first design: never blocks on ACP. On cache miss, enqueues
a job request for the sebastian-virtuals background service and
raises AdapterError (gateway skips gracefully).

Cache keys: acp:{agent_name}:{param_hash}
Job queue: acp:job_queue (Redis list, FIFO)
Dedup: acp:pending:{agent_name}:{param_hash} (SET NX, 600s TTL)
"""

import json
import hashlib
from datetime import datetime, timezone

import redis

from market_intelligence.adapters.base import DataAdapter
from market_intelligence.types import QueryParams, AdapterResponse, AdapterError


class ACPAgentAdapter(DataAdapter):
    """
    MI adapter for ACP agent intelligence.

    Reads cached deliverables from Redis. On cache miss, enqueues
    a job request for the background service and skips gracefully.
    """

    name = "acp_agent_adapter"
    data_type = "acp_agent"

    def __init__(self):
        super().__init__()
        self._redis = redis.Redis(
            host='localhost', port=6379, db=0, decode_responses=True
        )

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Fetch intelligence from an ACP agent.

        Params (from catalog_mapping params_template):
            agent_name: str — identifier (e.g., 'otto_ai', 'ggbots')
            agent_address: str — ACP smart wallet address
            offering_name: str — job offering name
            service_requirement: dict — what to ask for
        """
        p = params if isinstance(params, dict) else params.params
        agent_name = p.get('agent_name', 'unknown')
        agent_address = p.get('agent_address', '')
        offering_name = p.get('offering_name', '')
        service_requirement = p.get('service_requirement', {})

        if not agent_address:
            raise AdapterError(f"No agent_address for ACP agent '{agent_name}'")

        # Build cache and dedup keys
        param_hash = self._hash_params(service_requirement)
        cache_key = f"acp:{agent_name}:{param_hash}"
        pending_key = f"acp:pending:{agent_name}:{param_hash}"

        # 1. Check Redis cache
        try:
            cached = self._redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                self._log.debug(f"ACP cache hit: {agent_name}")
                return AdapterResponse(
                    data=data.get('deliverable', data),
                    metadata=self.build_metadata(
                        source=f'acp:{agent_name}',
                        cached=True,
                        agent_address=agent_address,
                        offering=offering_name,
                    ),
                    confidence=0.8,
                )
        except Exception as e:
            self._log.debug(f"Redis read failed for {cache_key}: {e}")

        # 2. Cache miss — check if job already pending
        try:
            already_pending = self._redis.get(pending_key)
            if already_pending:
                self._log.debug(f"ACP job already pending for {agent_name}, skipping enqueue")
                raise AdapterError(
                    f"ACP data for {agent_name} pending (job in progress)"
                )
        except AdapterError:
            raise
        except Exception:
            pass

        # 3. Enqueue job request for background service
        try:
            job_request = json.dumps({
                'agent_name': agent_name,
                'agent_address': agent_address,
                'offering_name': offering_name,
                'service_requirement': service_requirement,
                'cache_key': cache_key,
                'requested_at': datetime.now(timezone.utc).isoformat(),
            })
            self._redis.lpush('acp:job_queue', job_request)

            # Set dedup marker (atomic, 10min TTL)
            self._redis.set(pending_key, '1', ex=600, nx=True)

            self._log.info(f"ACP job enqueued for {agent_name} ({offering_name})")

        except Exception as e:
            self._log.warning(f"Failed to enqueue ACP job for {agent_name}: {e}")

        # 4. Skip this data point for this cycle
        raise AdapterError(
            f"ACP data for {agent_name} not cached yet, job enqueued"
        )

    @staticmethod
    def _hash_params(params: dict) -> str:
        """
        Short deterministic hash of service requirement params.

        Used for cache key uniqueness — different params = different cache.
        """
        raw = json.dumps(params, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()[:12]
