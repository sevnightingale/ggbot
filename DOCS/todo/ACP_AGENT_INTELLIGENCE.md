# ACP Agent Intelligence Integration

**Status**: In Progress — Market Conditions data source shipped (2026-03-21), ACP integration next
**Created**: 2026-03-20
**Context**: $GG token graduation requires ACP transaction volume. ggbots becomes a distribution platform for Virtuals ACP agents — consuming agent intelligence as a new market data category.

---

## Strategic Context

$GG is on the Virtuals bonding curve (~12K/42K VIRTUAL for graduation). ACP revenue triggers buyback-and-burn on $GG. The strategy:

1. **ggbots as ACP buyer** — bots consume intelligence from curated Virtuals agents
2. **"Agent Intelligence" data source** — new MI category alongside macro, sentiment, on-chain
3. **Our own ACP agent** (Phase 2, separate scope) — deployed on Virtuals, consumed through the same pipeline
4. **Volume generation** — 36 active bots × N cycles/day × curated agents = real on-chain ACP commerce

ggbots is a distribution layer for Virtuals agents. Every bot cycle with Agent Intelligence enabled generates ACP transactions for the ecosystem.

---

## Architecture: How It Fits

The MI pipeline already supports arbitrary data sources via the adapter pattern:

```
User toggles data point → orchestrator.py → catalog_mapping.py → gateway.py → adapter.fetch() → result
```

Adding ACP agents follows the exact same path as Grok, CoinGecko, or AccountPerformance:

```
('agent_intelligence', 'agent_name') → 'acp_agent' data_type → ACPAgentAdapter.fetch() → ACP job lifecycle → result
```

### Existing Patterns We Follow

| Pattern | Existing Example | ACP Equivalent |
|---------|-----------------|----------------|
| Adapter | `GrokAgenticAdapter` | `ACPAgentAdapter` |
| Catalog YAML | `grok_agentic.yaml` | `acp_agent.yaml` |
| Catalog mapping | `('macro_economics', 'vix')` | `('agent_intelligence', 'market_regime')` |
| DB seed | `data_sources` + `data_points` rows | Same — new category + agent rows |
| Cache | Redis with TTL per data point | Same — `intel:acp:{agent}:{params}` |
| Frontend | Auto-populates from DB | Same — shows up in bot builder automatically |

---

## Technical Design

### New Files

1. **`market_intelligence/adapters/acp/acp_agent_adapter.py`** — ACP buyer adapter
2. **`market_intelligence/catalog/data_types/agentic_intelligence/acp_agent.yaml`** — Catalog entry
3. **`core/services/acp_client.py`** — ACP client wrapper (wallet, job lifecycle, error handling)

### Modified Files

4. **`market_intelligence/catalog_mapping.py`** — Add `('agent_intelligence', ...)` entries
5. **`market_intelligence/gateway.py`** — Add `'acp'` adapter routing (if needed, may auto-discover)
6. **DB seed** — `data_sources` + `data_points` rows for curated agents

### ACPAgentAdapter Design

```python
class ACPAgentAdapter(DataAdapter):
    """
    ACP agent intelligence adapter.

    Initiates ACP jobs to curated Virtuals agents, handles the full
    job lifecycle (initiate → pay → receive → evaluate), and returns
    structured market intelligence.
    """

    name = "acp_agent_adapter"
    data_type = "acp_agent"

    async def fetch(self, params: QueryParams) -> AdapterResponse:
        """
        Fetch intelligence from an ACP agent.

        Params:
            agent_id: str — ACP entity ID or agent identifier
            offering_name: str — Which offering to request
            service_requirement: dict — What to ask for (symbol, timeframe, etc.)
        """
        # 1. Get or create ACP client (singleton per process)
        # 2. Find agent's offering
        # 3. Initiate job with service_requirement
        # 4. Pay for job (x402 gasless USDC)
        # 5. Poll for delivery (with timeout)
        # 6. Self-evaluate (accept delivery)
        # 7. Parse deliverable → AdapterResponse
```

### ACP Client Wrapper (`core/services/acp_client.py`)

Singleton that manages:
- Smart wallet connection (env vars: `ACP_WALLET_ADDRESS`, `ACP_WALLET_PRIVATE_KEY`, `ACP_ENTITY_ID`)
- USDC balance monitoring
- Job lifecycle (initiate → pay → poll → evaluate)
- Error handling (timeout, rejection, insufficient funds)
- Agent discovery cache (browse_agents results cached in Redis)

**Polling vs WebSocket**: Use polling mode (`skip_socket_connection=True`). Fits the existing bot cycle model — adapter calls ACP, waits for delivery, returns result. No persistent Socket.IO connection needed.

### Catalog Mapping Pattern

```python
# Each curated agent gets a mapping entry
('agent_intelligence', 'market_regime_synopsis'): {
    'data_type': 'acp_agent',
    'params_template': {
        'agent_address': '0x...',        # ACP smart wallet address
        'offering_name': 'Market Regime Synopsis',
        'service_requirement': {
            'symbol': '{symbol}',
            'request_type': 'regime_analysis'
        }
    },
    'cache_ttl': 3600,  # 1 hour — ACP results are higher-order analysis
    'global': True,      # If agent provides symbol-agnostic analysis
},
```

### Cost Model

ACP costs are a **platform expense**, same as Grok API costs:
- Platform pays ACP agents in USDC (from platform wallet on Base)
- Cost tracked per bot cycle in `activities.platform_cost_usd`
- Billed to users via existing metered billing at 1.7x markup
- No user wallet setup needed — invisible to end users

### Job Lifecycle Timing

ACP jobs have variable completion time (depends on provider agent SLA). Strategies:

1. **Synchronous with timeout** — Adapter polls for delivery with configurable timeout (e.g., 60s). If provider doesn't deliver, return cached result or skip gracefully. Simple, fits current pipeline.

2. **Pre-fetch on schedule** — Separate cron fetches ACP results into Redis cache. Bot cycle reads from cache. Decouples ACP latency from bot cycle. More complex but eliminates latency risk.

**Recommendation**: Start with (1) — synchronous with generous cache TTL (1hr+). ACP results are higher-order analysis, not real-time data. A 1-hour cache means at most 1 ACP call per hour per agent per symbol, regardless of how many bots use it. If `global: True`, one call serves all bots.

### Failure Handling

| Failure Mode | Handling |
|---|---|
| ACP agent offline | Return `AdapterError`, gateway skips this data point, bot continues with other MI data |
| Job timeout (SLA exceeded) | Cancel job, return cached result if available, else skip |
| Insufficient USDC | Log error, alert admin, skip ACP data points |
| Bad deliverable (unparseable) | Self-evaluate as rejected, log, return `AdapterError` |
| Network/Base chain issues | Retry once, then skip gracefully |

Same pattern as Grok failures — bot never blocks on a single MI source.

---

## Completed: Market Conditions Data Source (2026-03-21)

Sebastian AI research agent produces daily cross-market intelligence reports. This is the product foundation for our ACP provider agent.

- [x] `market_conditions` Supabase table (regime, domains, narratives, synthesis, data_quality, raw_tables)
- [x] `GET /POST /api/v2/market-conditions` endpoints with `SEBASTIAN_API_KEY` auth
- [x] `MarketConditionsAdapter` in MI pipeline (Redis cache → Supabase fallback)
- [x] Catalog YAML + mapping + DB seed (auto-populates in frontend bot builder)
- [x] Sebastian daily research pass operational — first report: Iran war / energy crisis

---

## Completed: Marketplace Exploration + Registration (2026-03-21)

### Agent Registered
- **Name**: Sebastian by ggbots.ai (Hybrid — buyer + provider)
- **Entity ID**: 29537
- **Smart Wallet**: `0xDAD5606b4f049591859DF0f352Cc703881422612`
- **EOA (whitelisted)**: `0xFF0ab2acF9b81DDd2cf16ad955a8Aaa0A4619bbD`
- **Offering**: marketBrief ($0.01 USDC, 10min SLA)
- **SDK**: `virtuals-acp` installed

### Curated Third-Party Agents (from Butler survey)

| Agent | Offering | Price | SLA | Jobs | Why |
|---|---|---|---|---|---|
| **Otto AI** | Crypto News | $0.01 | 30m | 55,251 (83%) | Replaces/supplements Grok crypto_news |
| **Wolfpack Intelligence** | Composite Risk Score | $0.05 | 30m | 2,646 (78%) | Risk scoring we don't have |
| **BlackSwan** | Prediction Market Monitor | $0.01 | 20m | 1,270 (96%) | Anomaly detection, unique |

**Rejected**: Elfa AI ($1.50/query too expensive), Loky ($5/query), Ask Caesar (45min SLA, 68% success rate)

**Daily cost estimate**: 3 agents × ~6 calls/day (4hr cache) × avg $0.02 = ~$0.36/day. Billed to users at 1.7x = ~$0.61/day.

---

## Environment Variables

```bash
# ACP Agent (Sebastian by ggbots.ai) — all set in .env
ACP_WALLET_ADDRESS=0xDAD5606b4f049591859DF0f352Cc703881422612
ACP_WALLET_PRIVATE_KEY=<set>   # EOA private key (no 0x prefix)
ACP_EOA_ADDRESS=0xFF0ab2acF9b81DDd2cf16ad955a8Aaa0A4619bbD
ACP_ENTITY_ID=29537
```

No user-facing wallet setup. Platform manages a single buyer/provider wallet.

---

## Remaining Prerequisites

- [x] ~~Register agent at app.virtuals.io/acp/join~~
- [x] ~~Create smart wallet + whitelist EOA~~
- [x] ~~Install `virtuals-acp` SDK~~
- [x] ~~Explore marketplace for curated agents~~
- [ ] Fund smart wallet with USDC on Base (test: $5-10)

---

## Scope Estimate

| Component | Effort | New/Modified |
|---|---|---|
| `acp_client.py` (ACP wrapper) | Medium | New |
| `acp_agent_adapter.py` | Medium | New |
| Catalog YAML | Low | New |
| `catalog_mapping.py` entries | Low | Modified |
| `gateway.py` routing | Low | Modified (if needed) |
| DB seed (data_sources + data_points) | Low | SQL |
| Frontend | None | Auto-populates |
| **Total** | **~2-3 days** | **2-3 new, 2-3 modified** |

---

## Dependencies

- `virtuals-acp>=0.3.23` (PyPI)
- USDC on Base (platform wallet)
- ACP agent registration (app.virtuals.io)
- At least 1 curated ACP agent to consume (our own or third-party)

---

## Workstream 2: Deploy Market Conditions as ACP Provider

Wrap Sebastian's daily market conditions output as an ACP offering. Other Virtuals agents buy cross-market intelligence from ggbots.

### Registration
- [ ] Register provider agent at app.virtuals.io/acp/join (separate smart wallet from buyer)
- [ ] Define offering: "Daily Market Conditions Brief"
  - `price`: $0.01-0.03 USDC (near-zero marginal cost — report is pre-produced)
  - `price_type`: FIXED
  - `required_funds`: false (Service-Only, not Fund-Transfer)
  - `sla_minutes`: 2 (read from DB, near-instant)
  - `requirement` schema: `{"symbol": "optional string", "request_type": "regime_analysis"}`
  - `deliverable` description: "Structured JSON: market regime, domain summaries, narratives, synthesis"

### Provider Service
- [ ] New PM2 service: `acp-provider` (or fold into ggbot-scheduler)
- [ ] `on_new_task` callback: read latest `market_conditions` from Supabase → format as deliverable → `job.deliver()`
- [ ] Polling mode (`skip_socket_connection=True`) — check for new jobs every 30s
- [ ] Self-evaluate buyer jobs as accepted (when we're also the buyer)
- [ ] Handle rejection gracefully (refund if post-payment)

### Self-Consumption
- [ ] Add our provider agent to the Agent Intelligence category as a data point
- [ ] Our bots buy from our own agent via ACP → generates on-chain volume
- [ ] Same cached result serves all bots (`global: True`, 1hr+ TTL)

### Graduation
- [ ] Implement Notification Memos (graduation requirement)
- [ ] Implement Resource endpoints (graduation requirement)
- [ ] Submit for graduation review (7 working days)

### Economics
- Report produced once daily by Sebastian (cost: ~$0 marginal, web search only)
- ACP job: $0.01 USDC, 80/20 split → we keep $0.008/job
- 36 bots × 24 cycles × $0.008 = $6.91/day from self-consumption alone
- External buyers are pure upside

---

## What This Does NOT Include

- **Per-user ACP wallets** — platform wallet only
- **Fund-Transfer jobs** — Service-Only jobs only (Phase 2 vault strategy is separate)
- **Frontend ACP marketplace UI** — agents appear as standard MI data points, no custom UI
- **Strategy Vaults** — separate scope, requires fund-transfer job type + custody design

---

## Reference

- ACP Whitepaper: https://whitepaper.virtuals.io/about-virtuals/agent-commerce-protocol-acp
- ACP v2: https://whitepaper.virtuals.io/acp-product-resources/introducing-acp-v2
- Python SDK: https://github.com/Virtual-Protocol/acp-python
- Registration: https://app.virtuals.io/acp/join
- NOTE.md: Strategic context and Phase 2 vault vision
