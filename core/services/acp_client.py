"""
ACP Client — Singleton wrapper for Virtuals Agent Commerce Protocol.

Handles both buyer (consuming intelligence from ACP agents) and provider
(serving our market conditions report) operations. All methods are
synchronous (matching the SDK). Callers use asyncio.to_thread().

Usage:
    from core.services.acp_client import get_acp_client

    client = get_acp_client()  # Lazy singleton
    job_id = client.buy_from_offering(agent_address, "marketBrief", {"focus": "crypto"})
"""

import os
import json
import time
from typing import Optional, Dict, Any, List

import redis

from core.common.logger import logger

_log = logger.bind(component="acp_client")

# Module-level singleton
_acp_client: Optional['ACPClient'] = None


class ACPClientError(Exception):
    """Wrapper for all ACP SDK exceptions."""
    pass


class ACPClient:
    """
    Singleton ACP client for buyer + provider operations.

    Wraps VirtualsACP + ACPContractClientV2 with clean methods
    for job lifecycle management and Redis-based agent caching.
    """

    # Sebastian's wallet — used as provider for self-consumption
    # (SDK blocks buying from yourself, so we use two wallets)
    SEBASTIAN_WALLET = "0xDAD5606b4f049591859DF0f352Cc703881422612"

    def __init__(self):
        self._acp = None  # VirtualsACP instance (buyer), lazy-init
        self._provider_acp = None  # VirtualsACP instance (provider/Sebastian), lazy-init
        self._redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self._wallet_address = os.getenv('ACP_WALLET_ADDRESS')
        self._private_key = os.getenv('ACP_WALLET_PRIVATE_KEY')
        self._entity_id = int(os.getenv('ACP_ENTITY_ID', '0'))

        if not all([self._wallet_address, self._private_key, self._entity_id]):
            _log.warning("ACP env vars not fully set (ACP_WALLET_ADDRESS, ACP_WALLET_PRIVATE_KEY, ACP_ENTITY_ID)")

    def get_client(self):
        """
        Get or create the VirtualsACP singleton.

        Lazy initialization — only connects to ACP on first use.
        This makes RPC calls to read contract addresses, so it can
        take a few seconds on first call.
        """
        if self._acp is not None:
            return self._acp

        try:
            from virtuals_acp.contract_clients.contract_client_v2 import ACPContractClientV2
            from virtuals_acp.client import VirtualsACP

            _log.info("Initializing ACP client...")

            contract_client = ACPContractClientV2(
                agent_wallet_address=self._wallet_address,
                wallet_private_key=self._private_key,
                entity_id=self._entity_id,
            )

            self._acp = VirtualsACP(
                contract_client,
                skip_socket_connection=True,
            )

            _log.info(
                f"ACP client initialized — wallet={self._wallet_address[:10]}..., "
                f"entity_id={self._entity_id}"
            )
            return self._acp

        except Exception as e:
            _log.error(f"Failed to initialize ACP client: {e}")
            raise ACPClientError(f"ACP initialization failed: {e}") from e

    def get_provider_client(self):
        """
        Get or create a separate VirtualsACP instance for Sebastian (provider role).

        Uses Sebastian's smart wallet address but same EOA/entity_id.
        Needed because the SDK blocks buying from yourself (same wallet),
        so we use two wallets: ggbots.ai as buyer, Sebastian as provider.
        """
        if self._provider_acp is not None:
            return self._provider_acp

        try:
            from virtuals_acp.contract_clients.contract_client_v2 import ACPContractClientV2
            from virtuals_acp.client import VirtualsACP

            _log.info("Initializing ACP provider client (Sebastian)...")

            contract_client = ACPContractClientV2(
                agent_wallet_address=self.SEBASTIAN_WALLET,
                wallet_private_key=self._private_key,
                entity_id=self._entity_id,
            )

            self._provider_acp = VirtualsACP(
                contract_client,
                skip_socket_connection=True,
            )

            _log.info(
                f"ACP provider client initialized — wallet={self.SEBASTIAN_WALLET[:10]}..."
            )
            return self._provider_acp

        except Exception as e:
            _log.error(f"Failed to initialize ACP provider client: {e}")
            raise ACPClientError(f"Provider client initialization failed: {e}") from e

    # =========================================================================
    # Agent Discovery (cached)
    # =========================================================================

    def get_cached_agent(self, wallet_address: str):
        """
        Get agent by wallet address with Redis caching (1hr TTL).

        Returns IACPAgent or None.
        """
        cache_key = f"acp:agent:{wallet_address}"

        # Check cache
        try:
            cached = self._redis.get(cache_key)
            if cached:
                _log.debug(f"Agent cache hit: {wallet_address[:10]}...")
                # Can't cache the full IACPAgent (has methods), so we re-fetch
                # but use the cache as a "known good" signal
        except Exception:
            pass

        # Fetch from API
        try:
            acp = self.get_client()
            agent = acp.get_agent(wallet_address)

            if agent:
                # Cache the wallet address as "known good" for 1hr
                try:
                    self._redis.set(cache_key, wallet_address, ex=3600)
                except Exception:
                    pass

            return agent

        except Exception as e:
            _log.error(f"Failed to get agent {wallet_address[:10]}...: {e}")
            raise ACPClientError(f"Agent lookup failed: {e}") from e

    def browse_agents(self, keyword: str, top_k: int = 5):
        """Search for agents by keyword."""
        try:
            acp = self.get_client()
            return acp.browse_agents(keyword=keyword, top_k=top_k)
        except Exception as e:
            _log.error(f"Failed to browse agents for '{keyword}': {e}")
            raise ACPClientError(f"Agent search failed: {e}") from e

    # =========================================================================
    # Buyer Operations
    # =========================================================================

    def buy_from_offering(
        self,
        agent_address: str,
        offering_name: str,
        service_requirement: Dict[str, Any],
    ) -> int:
        """
        Initiate an ACP job by finding an agent's offering and calling initiate_job().

        Args:
            agent_address: Provider agent's smart wallet address
            offering_name: Name of the job offering (e.g., "marketBrief")
            service_requirement: Dict to send as the service requirement

        Returns:
            job_id (int) — on-chain job ID

        Raises:
            ACPClientError on any failure
        """
        try:
            agent = self.get_cached_agent(agent_address)
            if not agent:
                raise ACPClientError(f"Agent not found: {agent_address}")

            # Find offering by name
            offering = None
            for o in agent.job_offerings:
                if o.name == offering_name:
                    offering = o
                    break

            if not offering:
                available = [o.name for o in agent.job_offerings]
                raise ACPClientError(
                    f"Offering '{offering_name}' not found on agent. "
                    f"Available: {available}"
                )

            _log.info(
                f"Initiating ACP job: agent={agent.name}, "
                f"offering={offering_name}, price=${offering.price}"
            )

            job_id = offering.initiate_job(service_requirement)
            _log.info(f"ACP job initiated: job_id={job_id}")
            return job_id

        except ACPClientError:
            raise
        except Exception as e:
            _log.error(f"Failed to initiate ACP job: {e}")
            raise ACPClientError(f"Job initiation failed: {e}") from e

    def get_job(self, job_id: int):
        """
        Fetch job by on-chain ID.

        Returns ACPJob.
        """
        try:
            acp = self.get_client()
            return acp.get_job_by_onchain_id(job_id)
        except Exception as e:
            _log.error(f"Failed to get job {job_id}: {e}")
            raise ACPClientError(f"Job fetch failed: {e}") from e

    def pay_job(self, job) -> Optional[str]:
        """
        Pay for a job and accept the requirement.

        Call this when job phase is NEGOTIATION (provider accepted).
        Returns transaction hash.
        """
        try:
            _log.info(f"Paying for ACP job {job.id}...")
            txn_hash = job.pay_and_accept_requirement("Payment from ggbots.ai")
            _log.info(f"ACP job {job.id} paid: txn={txn_hash}")
            return txn_hash
        except Exception as e:
            _log.error(f"Failed to pay for job {job.id}: {e}")
            raise ACPClientError(f"Job payment failed: {e}") from e

    def get_deliverable(self, job) -> Optional[Any]:
        """
        Get the deliverable from a completed job and evaluate it.

        Call this when job phase is EVALUATION or COMPLETED.
        Calls job.evaluate(True) to accept the delivery.
        Returns the deliverable payload (dict or str).
        """
        try:
            deliverable = job.get_deliverable()

            # Accept the delivery
            try:
                job.evaluate(True, "Accepted by ggbots.ai")
                _log.info(f"ACP job {job.id} evaluated: accepted")
            except Exception as eval_err:
                # Non-fatal — deliverable was received even if evaluate fails
                _log.warning(f"Failed to evaluate job {job.id} (non-fatal): {eval_err}")

            return deliverable

        except Exception as e:
            _log.error(f"Failed to get deliverable for job {job.id}: {e}")
            raise ACPClientError(f"Deliverable fetch failed: {e}") from e

    # =========================================================================
    # Provider Operations
    # =========================================================================

    def get_pending_provider_jobs(self) -> List:
        """
        Get jobs where Sebastian is the provider and action is needed.

        Uses the provider client (Sebastian's wallet) to find incoming jobs.
        Returns list of ACPJob objects.
        """
        try:
            acp = self.get_provider_client()
            jobs = acp.get_pending_memo_jobs(page=1, page_size=20)

            # Filter for jobs where Sebastian is the provider
            sebastian_address = self.SEBASTIAN_WALLET.lower()
            provider_jobs = [
                j for j in jobs
                if j.provider_address.lower() == sebastian_address
            ]

            if provider_jobs:
                _log.debug(f"Found {len(provider_jobs)} pending provider jobs")

            return provider_jobs

        except Exception as e:
            _log.error(f"Failed to get pending provider jobs: {e}")
            raise ACPClientError(f"Provider job fetch failed: {e}") from e

    def accept_job(self, job) -> Optional[str]:
        """
        Accept an incoming job request (REQUEST phase).

        Calls job.respond(True) which:
        1. Signs the negotiation memo (accept)
        2. Creates a TRANSACTION memo (so buyer can pay)
        """
        from virtuals_acp.models import ACPJobPhase

        try:
            phase = ACPJobPhase(job.phase) if isinstance(job.phase, int) else job.phase

            if phase != ACPJobPhase.REQUEST:
                _log.debug(f"Job {job.id} not in REQUEST phase ({phase}), skipping accept")
                return None

            _log.info(f"Accepting provider job {job.id}...")
            txn_hash = job.respond(True, "Accepted by ggbots.ai")
            _log.info(f"Job {job.id} accepted, TRANSACTION memo created")
            return txn_hash

        except Exception as e:
            _log.error(f"Failed to accept job {job.id}: {e}")
            raise ACPClientError(f"Job accept failed: {e}") from e

    def deliver_job(self, job, deliverable: Dict[str, Any]) -> Optional[str]:
        """
        Deliver result for a job in TRANSACTION phase.

        Call this after the buyer has paid (phase = TRANSACTION).
        """
        from virtuals_acp.models import ACPJobPhase

        try:
            phase = ACPJobPhase(job.phase) if isinstance(job.phase, int) else job.phase

            if phase != ACPJobPhase.TRANSACTION:
                _log.debug(
                    f"Job {job.id} not in TRANSACTION phase ({phase}), can't deliver yet"
                )
                return None

            _log.info(f"Delivering to job {job.id}...")
            txn_hash = job.deliver(deliverable)
            _log.info(f"ACP job {job.id} delivered: txn={txn_hash}")
            return txn_hash

        except Exception as e:
            _log.error(f"Failed to deliver job {job.id}: {e}")
            raise ACPClientError(f"Provider delivery failed: {e}") from e


def get_acp_client() -> ACPClient:
    """Get or create the module-level ACPClient singleton."""
    global _acp_client
    if _acp_client is None:
        _acp_client = ACPClient()
    return _acp_client
