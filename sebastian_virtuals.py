"""
Sebastian Virtuals — ACP Background Service

PM2 service handling all ACP operations for ggbots.ai:
  A) PROVIDER: Poll for incoming jobs → deliver market conditions from DB
  B) BUYER QUEUE: Process job requests from MI adapter → initiate ACP jobs
  C) BUYER MONITOR: Poll active jobs → pay/collect/cache deliverables

Run with: python sebastian_virtuals.py
PM2:      pm2 start ecosystem.config.js --only sebastian-virtuals
"""

import asyncio
import json
import signal
import sys
from datetime import datetime, timezone

import redis

from core.common.logger import logger as base_logger
from core.services.acp_client import get_acp_client, ACPClientError

logger = base_logger.bind(service="sebastian_virtuals")

# Redis connection
_redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

POLL_INTERVAL = 30  # seconds between cycles


# =============================================================================
# A) PROVIDER — Serve incoming ACP jobs
# =============================================================================

def handle_provider_jobs(acp_client):
    """
    Check for incoming jobs where we are the provider.
    Accept and deliver market conditions report from DB.
    """
    try:
        jobs = acp_client.get_pending_provider_jobs()
    except ACPClientError as e:
        logger.warning(f"Provider job fetch failed: {e}")
        return

    if not jobs:
        return

    logger.info(f"Processing {len(jobs)} incoming provider jobs")

    from virtuals_acp.models import ACPJobPhase

    for job in jobs:
        try:
            phase = ACPJobPhase(job.phase) if isinstance(job.phase, int) else job.phase

            if phase == ACPJobPhase.REQUEST:
                # Step 1: Accept the job (creates TRANSACTION memo for buyer to pay)
                acp_client.accept_job(job)
                logger.info(f"Provider job {job.id} accepted, waiting for buyer payment")

            elif phase == ACPJobPhase.TRANSACTION:
                # Step 2: Buyer has paid — deliver the report
                report = _get_market_conditions_report()
                if not report:
                    logger.warning(f"No market conditions report available, skipping job {job.id}")
                    continue

                acp_client.deliver_job(job, report)
                logger.info(f"Provider job {job.id} delivered successfully")
                _log_provider_activity(job)

            else:
                logger.debug(f"Provider job {job.id} in phase {phase}, no action needed")

        except ACPClientError as e:
            logger.error(f"Failed to handle provider job {job.id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error on provider job {job.id}: {e}")


def _get_market_conditions_report() -> dict | None:
    """Read latest market conditions from Redis cache or DB."""
    # Try Redis first
    try:
        cached = _redis.get("market_conditions:latest")
        if cached:
            data = json.loads(cached)
            logger.debug("Market conditions from Redis cache")
            return data
    except Exception:
        pass

    # Fallback to DB
    try:
        from core.common.db import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT generated_at, schema_version, regime, domains,
                           narratives, synthesis, data_quality
                    FROM market_conditions
                    ORDER BY generated_at DESC
                    LIMIT 1
                """)
                row = cur.fetchone()
                if not row:
                    return None

                return {
                    'generated_at': row[0].isoformat() if row[0] else None,
                    'schema_version': row[1],
                    'regime': row[2],
                    'domains': row[3],
                    'narratives': row[4],
                    'synthesis': row[5],
                    'data_quality': row[6],
                }
    except Exception as e:
        logger.error(f"Failed to read market conditions from DB: {e}")
        return None


def _log_provider_activity(job):
    """Log provider revenue as an activity."""
    try:
        from core.common.activity_logger import log_llm_activity

        log_llm_activity(
            config_id=None,
            user_id=None,
            summary=f"ACP provider: delivered marketBrief (job {job.id})",
            details={
                'acp_job_id': job.id,
                'client_address': job.client_address,
                'price': job.price,
                'role': 'provider',
            },
            provider='acp',
            model='ggbots_provider',
            input_tokens=0,
            output_tokens=0,
            provider_cost_usd=0.0,  # We earned, not spent
            platform_cost_usd=0.0,
            importance=3,
        )
    except Exception as e:
        logger.debug(f"Failed to log provider activity: {e}")


# =============================================================================
# B) BUYER QUEUE — Process job requests from adapter
# =============================================================================

def process_buyer_queue(acp_client):
    """
    Pop job requests from acp:job_queue and initiate ACP jobs.
    """
    # Process up to 5 jobs per cycle to avoid blocking
    for _ in range(5):
        try:
            raw = _redis.rpop('acp:job_queue')
            if not raw:
                return  # Queue empty

            request = json.loads(raw)
            agent_name = request['agent_name']
            agent_address = request['agent_address']
            offering_name = request['offering_name']
            service_requirement = request.get('service_requirement', {})
            cache_key = request.get('cache_key', f"acp:{agent_name}:default")

            # Check dedup — skip if active job already exists
            active_key = f"acp:active_job:{agent_name}:{_hash_requirement(service_requirement)}"
            if _redis.exists(active_key):
                logger.debug(f"Active job already exists for {agent_name}, skipping")
                continue

            # Initiate ACP job
            logger.info(f"Initiating ACP buy: {agent_name} / {offering_name}")
            job_id = acp_client.buy_from_offering(
                agent_address, offering_name, service_requirement
            )

            # Track active job
            _redis.set(active_key, json.dumps({
                'job_id': job_id,
                'agent_name': agent_name,
                'cache_key': cache_key,
                'created_at': datetime.now(timezone.utc).isoformat(),
            }), ex=3600)  # 1hr TTL

            logger.info(f"ACP job {job_id} initiated for {agent_name}")

        except ACPClientError as e:
            logger.error(f"Failed to initiate ACP job: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing buyer queue: {e}")


# =============================================================================
# C) BUYER MONITOR — Poll active jobs for completion
# =============================================================================

def monitor_active_jobs(acp_client):
    """
    Scan active outgoing jobs and advance their lifecycle:
    - NEGOTIATION: provider accepted → pay
    - TRANSACTION: waiting for delivery → skip
    - EVALUATION: delivery ready → collect + cache
    - COMPLETED: already done → cache if needed + cleanup
    - REJECTED/EXPIRED: log + cleanup
    """
    from virtuals_acp.models import ACPJobPhase

    # Scan for active job keys
    try:
        keys = list(_redis.scan_iter(match='acp:active_job:*', count=50))
    except Exception as e:
        logger.warning(f"Failed to scan active jobs: {e}")
        return

    if not keys:
        return

    for key in keys:
        try:
            raw = _redis.get(key)
            if not raw:
                continue

            tracking = json.loads(raw)
            job_id = tracking['job_id']
            agent_name = tracking['agent_name']
            cache_key = tracking['cache_key']

            # Fetch current job state
            try:
                job = acp_client.get_job(job_id)
            except ACPClientError:
                logger.warning(f"Failed to fetch job {job_id}, will retry next cycle")
                continue

            phase = ACPJobPhase(job.phase) if isinstance(job.phase, int) else job.phase

            if phase == ACPJobPhase.NEGOTIATION:
                # Provider accepted — pay and advance
                logger.info(f"Job {job_id} ({agent_name}): provider accepted, paying...")
                try:
                    acp_client.pay_job(job)
                except ACPClientError as e:
                    logger.error(f"Payment failed for job {job_id}: {e}")
                    # Don't cleanup — retry next cycle

            elif phase == ACPJobPhase.TRANSACTION:
                # Waiting for delivery — skip
                logger.debug(f"Job {job_id} ({agent_name}): waiting for delivery")

            elif phase in (ACPJobPhase.EVALUATION, ACPJobPhase.COMPLETED):
                # Delivery ready — collect and cache
                logger.info(f"Job {job_id} ({agent_name}): collecting deliverable")
                try:
                    deliverable = acp_client.get_deliverable(job)

                    if deliverable:
                        # Cache the result
                        cache_data = json.dumps({
                            'deliverable': deliverable,
                            'agent_name': agent_name,
                            'job_id': job_id,
                            'cached_at': datetime.now(timezone.utc).isoformat(),
                        }, default=str)
                        _redis.set(cache_key, cache_data, ex=3600)

                        logger.info(
                            f"Job {job_id} ({agent_name}): deliverable cached at {cache_key}"
                        )

                        # Log buyer activity for billing
                        _log_buyer_activity(job, agent_name)

                    # Cleanup
                    _redis.delete(key)
                    _cleanup_pending_marker(agent_name, tracking)

                except ACPClientError as e:
                    logger.error(f"Failed to collect deliverable for job {job_id}: {e}")

            elif phase in (ACPJobPhase.REJECTED, ACPJobPhase.EXPIRED):
                # Failed — log and cleanup
                reason = ""
                if phase == ACPJobPhase.REJECTED:
                    reason = getattr(job, 'rejection_reason', '') or 'unknown'
                logger.warning(
                    f"Job {job_id} ({agent_name}): {phase.name} — {reason}"
                )
                _redis.delete(key)
                _cleanup_pending_marker(agent_name, tracking)

            else:
                logger.debug(f"Job {job_id} ({agent_name}): phase={phase}, waiting")

        except Exception as e:
            logger.error(f"Error monitoring job from {key}: {e}")


def _log_buyer_activity(job, agent_name: str):
    """Log buyer cost as an activity."""
    try:
        from core.common.activity_logger import log_llm_activity

        log_llm_activity(
            config_id=None,
            user_id=None,
            summary=f"ACP buyer: received {agent_name} intelligence (job {job.id})",
            details={
                'acp_job_id': job.id,
                'agent_name': agent_name,
                'provider_address': job.provider_address,
                'price': job.price,
                'role': 'buyer',
            },
            provider='acp',
            model=agent_name,
            input_tokens=0,
            output_tokens=0,
            provider_cost_usd=job.price,
            platform_cost_usd=0.0,  # Free to users initially
            importance=3,
        )
    except Exception as e:
        logger.debug(f"Failed to log buyer activity: {e}")


def _cleanup_pending_marker(agent_name: str, tracking: dict):
    """Remove the pending/dedup marker so adapter can enqueue new requests."""
    try:
        # Reconstruct the pending key from the cache key
        cache_key = tracking.get('cache_key', '')
        # cache_key format: "acp:{agent_name}:{hash}"
        parts = cache_key.split(':')
        if len(parts) >= 3:
            param_hash = parts[2]
            pending_key = f"acp:pending:{agent_name}:{param_hash}"
            _redis.delete(pending_key)
    except Exception:
        pass


def _hash_requirement(params: dict) -> str:
    """Short hash of service requirement for dedup keys."""
    import hashlib
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# =============================================================================
# D) ARENA TRADES — Mirror bot decisions to DGClaw
# =============================================================================

def process_arena_trades(dgclaw_service):
    """
    Process arena trade queue from orchestrator.

    Pops trade intents from arena:trade_queue and executes them
    on DGClaw via ACP. Each trade runs the full ACP lifecycle
    synchronously (~20-50s).
    """
    from core.symbols.standardizer import UniversalSymbolStandardizer
    standardizer = UniversalSymbolStandardizer()

    for _ in range(3):  # Max 3 trades per cycle to avoid blocking
        try:
            raw = _redis.rpop('arena:trade_queue')
            if not raw:
                return  # Queue empty

            intent = json.loads(raw)
            action = intent.get('action', '')
            symbol = intent.get('symbol', '')
            config_id = intent.get('config_id', 'unknown')

            logger.info(
                f"Arena trade: {action.upper()} {symbol} "
                f"(config={config_id[:8]}, confidence={intent.get('confidence', 0):.2f})"
            )

            if action in ('long', 'short', 'enter', 'enter_long', 'enter_short'):
                result = dgclaw_service.execute_arena_trade(intent)

            elif action in ('close', 'exit'):
                # Convert symbol to HL bare pair name for close
                pair = _symbol_to_pair(symbol, standardizer)
                if pair:
                    result = dgclaw_service.close_arena_position(pair)
                else:
                    logger.error(f"Cannot convert symbol for arena close: {symbol}")
                    continue

            else:
                logger.warning(f"Unknown arena action: {action}")
                continue

            status = result.get('status', 'unknown')
            job_id = result.get('job_id', 'n/a')
            logger.info(f"Arena trade result: {status} (job={job_id})")

        except Exception as e:
            logger.error(f"Arena trade processing failed: {e}")


def _symbol_to_pair(symbol: str, standardizer) -> str | None:
    """Convert any symbol format to HL bare name (e.g., 'ETH')."""
    formats = ["ccxt", "platform", "ggshot", "hyperliquid"]
    for fmt in formats:
        if standardizer.is_supported(symbol, fmt):
            hl = standardizer.to_hyperliquid(symbol, fmt)
            if hl:
                return hl
    # Fallback for bare names
    if symbol.isalpha() and len(symbol) <= 6:
        return symbol.upper()
    return None


# =============================================================================
# Main Loop
# =============================================================================

async def main():
    logger.info("Starting Sebastian Virtuals ACP service")
    logger.info(f"Poll interval: {POLL_INTERVAL}s")

    acp_client = get_acp_client()

    # Verify ACP client can initialize (fail fast)
    try:
        acp_client.get_client()
        logger.info("ACP client initialized successfully")
    except ACPClientError as e:
        logger.error(f"ACP client failed to initialize: {e}")
        logger.error("Check ACP_WALLET_ADDRESS, ACP_WALLET_PRIVATE_KEY, ACP_ENTITY_ID env vars")
        sys.exit(1)

    # Initialize DGClaw arena service (lazy — only creates objects, no network calls)
    dgclaw_service = None
    try:
        from trading.virtuals.dgclaw_service import DGClawArenaService
        dgclaw_service = DGClawArenaService()
        logger.info("DGClaw arena service initialized")
    except Exception as e:
        logger.warning(f"DGClaw arena service not available: {e}")

    while True:
        try:
            # A) Provider: handle incoming jobs
            await asyncio.to_thread(handle_provider_jobs, acp_client)

            # B) Buyer: process job queue from adapter
            await asyncio.to_thread(process_buyer_queue, acp_client)

            # C) Buyer: monitor active outgoing jobs
            await asyncio.to_thread(monitor_active_jobs, acp_client)

            # D) Arena: process trade queue from orchestrator
            if dgclaw_service:
                await asyncio.to_thread(process_arena_trades, dgclaw_service)

        except Exception as e:
            logger.error(f"ACP service loop error: {e}")

        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Sebastian Virtuals stopped by user")
        sys.exit(0)
