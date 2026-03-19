# ACP Integration Scope for ggbots

*Written by Sebastian for Sev's ggbot repo session. March 17, 2026.*
*Context: After conversation with Big Wil (Virtuals KOL), priority is ACP integration + revenue generation to drive $GG toward 42K VIRTUAL LP graduation threshold (currently ~12K).*

---

## Strategic Context

$GG is stuck on the bonding curve. Two paths to graduation:
1. Virtuals team collaboration on their "degen arena" (Sev has reached out to scope)
2. ACP integration generating real revenue -- this is the path we control

ACP revenue triggers buyback-and-burn on $GG. Real on-chain commerce volume signals to the ecosystem that $GG is a functional, revenue-generating agent. This is what drives token attention in Virtuals -- not hype, revenue.

---

## Phase 1: "Agents" as a Market Data Source

### The Idea

Add ACP-powered agents as a new category of market data source in ggbots. Users already select data points (technical indicators, on-chain data, etc.) when building their bots. "Agent Intelligence" becomes another data source category -- market analysis, sentiment, on-chain flow, macro signals -- all sourced from ACP provider agents on Virtuals.

The user experience is seamless: toggle on the agents you want, costs come from existing usage credits. No wallet setup, no ACP knowledge needed. ggbots handles all the ACP plumbing invisibly.

### Why This Framing Matters

- **Not self-dealing**: Users' ggbots buy from third-party Virtuals agents. Legitimate commerce.
- **ggbots becomes a distribution layer for Virtuals agents**: Every ACP analysis agent has a reason to care about ggbots -- it puts their service in front of paying traders.
- **ggbots' own analysis agent competes on merit**: It's one option among several, not the only option.
- **Ecosystem pitch**: "ggbots is bringing ACP to 350 traders who've never heard of agent commerce. Every ggbot becomes an ACP buyer. First platform to make agent commerce invisible to end users."

### Architecture

```
User's ggbot (ACP Buyer, platform-managed wallet)
    |-- ggbots Market Analysis Agent (ACP Provider, our own)
    |-- [Third-party] Sentiment Agent (ACP Provider)
    |-- [Third-party] On-chain Flow Agent (ACP Provider)
    |-- [Third-party] Macro Signals Agent (ACP Provider)
         |
    Decision Agent receives enriched context
         |
    Trading Agent executes
```

### What Needs Building

1. **ggbots Market Analysis Agent (ACP Provider)**
   - Wrap existing extraction pipeline as an ACP provider
   - Register at app.virtuals.io/acp/join
   - Create job offering (e.g., "Enhanced Market Analysis" -- ~$0.05 USDC, SLA: 2 min)
   - Wire `on_new_task` callback to existing extraction pipeline
   - The analysis capability already exists -- this is mostly plumbing

2. **ACP Buyer Integration (platform side)**
   - Platform-managed ACP wallet (or per-user wallets) on Base
   - Usage credits -> USDC conversion for ACP payments
   - ACP job initiation added to pre-trade decision flow
   - Handle full lifecycle: initiate job -> pay -> receive analysis -> evaluate -> settle
   - Graceful failure handling (if ACP provider doesn't deliver, bot continues with standard data)

3. **Curated Agent Marketplace**
   - Browse ACP marketplace for quality analysis/signal agents
   - Vet and curate 2-3 third-party agents alongside our own
   - Present as selectable "enhancements" in bot builder UI
   - Each agent shows: name, description, cost per call, reliability score

4. **"Agent Intelligence" Data Source in Bot Builder**
   - New category in market data source selection
   - Users toggle on/off like any other data source
   - Cost displayed clearly (deducted from usage credits)
   - Analysis results injected into decision agent context alongside other data

### Python SDK Reference

```bash
pip install virtuals-acp
```

```python
from virtuals_acp.client import VirtualsACP
from virtuals_acp.env import EnvSettings
from virtuals_acp.contract_clients import ACPContractClientV2
from virtuals_acp.configs import BASE_MAINNET_ACP_X402_CONFIG_V2

env = EnvSettings()

# Initialize ACP client (buyer side)
acp_client = VirtualsACP(
    acp_contract_clients=ACPContractClientV2(
        wallet_private_key=env.WHITELISTED_WALLET_PRIVATE_KEY,
        agent_wallet_address=env.BUYER_AGENT_WALLET_ADDRESS,
        entity_id=env.BUYER_ENTITY_ID,
        config=BASE_MAINNET_ACP_X402_CONFIG_V2,
    ),
    on_new_task=on_new_task  # callback for incoming jobs (provider side)
)

# Browse available agents
agents = acp_client.browse_agents(
    keyword="market analysis",
    sort_by=[ACPAgentSort.SUCCESSFUL_JOB_COUNT],
    top_k=5,
    graduation_status=ACPGraduationStatus.ALL,
    online_status=ACPOnlineStatus.ALL,
)

# Initiate a job from a discovered offering
offering = agents[0].offerings[0]
job_id = offering.initiate_job(
    service_requirement="BTC/USDT 4h analysis with sentiment and key levels",
    evaluator_address="0x..."
)

# Pay for the job
acp_client.pay_job(job_id=job_id, amount=0.05, memo_id=memo_id, reason="Market analysis")

# Deliver (provider side callback)
acp_client.deliver_job(job_id=job_id, deliverable="structured_analysis_json")
```

### Environment Variables Needed

```
WHITELISTED_WALLET_PRIVATE_KEY=    # Developer wallet (whitelisted with Virtuals)
BUYER_AGENT_WALLET_ADDRESS=        # ggbots platform buyer wallet on Base
BUYER_ENTITY_ID=                   # From ACP registration
SELLER_AGENT_WALLET_ADDRESS=       # ggbots analysis agent wallet
SELLER_ENTITY_ID=                  # From ACP registration
```

### ACP Job Lifecycle

```
Request -> Negotiation -> Transaction (escrow) -> Evaluation -> Completed
```

- Each phase transition requires cryptographic signatures (memos)
- Funds held in smart contract escrow until work verified
- 80/20 fee split: 80% to provider, 20% to Virtuals protocol
- SDK handles all wallet/escrow/settlement -- gas is sponsored on Base
- Job types: Service-Only (analysis) or Fund-Transfer (vault, Phase 2)

### Registration Steps

1. Register at https://app.virtuals.io/acp/join
2. Create two agents: ggbots analysis agent (provider) + ggbots platform agent (buyer)
3. Whitelist developer wallet per ACP tech playbook
4. Fund buyer agent with USDC on Base
5. Create job offerings for the analysis agent

---

## Phase 2: Vault Strategy Integration (Future)

### The Idea

The Arbiter (or any high-performing ggbot) becomes an ACP Fund-Transfer provider. Other agents deposit capital, The Arbiter trades it, returns results. This is a managed trading vault on-chain.

### How It Works

- Job type: Fund-Transfer (`fundTransfer = true`)
- Buyer agent deposits principal funds + service fee
- The Arbiter manages those funds via Hyperliquid
- Requires: separate hot wallet per buyer, position tracking resource endpoints, proof-of-custody
- Performance fee model (e.g., 2/20 or flat service fee per trade cycle)

### Why Phase 2

- Higher complexity: custody, risk management, regulatory surface
- Higher visibility: revenue-generating vault is the strongest signal in Virtuals ecosystem
- Builds on Phase 1 infrastructure (ACP integration already in place)
- The Arbiter's track record (+34.59% Season 1) is the selling point

### Vault Job Offering Example

```
Service: Managed Trading (The Arbiter Strategy)
Service Fee: 10 USDC per trade cycle
Fund Transfer: Yes (minimum 100 USDC deposit)
SLA: 24 hours (one full trade cycle)
Deliverable: Trade execution report with P&L, positions, and next action
```

---

## Key Documentation

- ACP Whitepaper: https://whitepaper.virtuals.io/about-virtuals/agent-commerce-protocol-acp
- ACP Architecture: https://whitepaper.virtuals.io/acp-product-resources/acp-concepts-terminologies-and-architecture
- ACP v2: https://whitepaper.virtuals.io/acp-product-resources/introducing-acp-v2
- Python SDK: https://github.com/Virtual-Protocol/acp-python (PyPI: virtuals-acp)
- Node SDK: https://github.com/Virtual-Protocol/acp-node
- CLI Tool: https://github.com/Virtual-Protocol/openclaw-acp
- ACP Registration: https://app.virtuals.io/acp/join

---

## Current $GG Status

- Token: 0x0497F698CdB42984FFcfb509472a186F984673e2 (Base)
- LP: ~12K VIRTUAL (need 42K for Uniswap graduation)
- Day 8 of 60-day sprint
- MC: ~$79K
- ACP revenue -> buyback-and-burn on $GG -> LP growth -> graduation
