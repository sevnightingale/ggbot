# Rei Agent Integration - Persistent Learning Trading Agent

**Status**: PLANNING - Awaiting beta access
**Created**: 2026-01-13
**TODO Section**: Rei Agent Integration

---

## Executive Summary

Integrate Reilabs' Rei Core reasoning engine with ggbots' existing Claude SDK agent to create a **hybrid architecture** where:
- **Claude Agent** = Orchestrator (execution, timing, tool use, error recovery)
- **Rei Unit** = Brain (reasoning, learning, memory, pattern recognition)

This enables **persistent learning at inference time** - the agent genuinely improves from experience rather than relying solely on prompt engineering.

---

## Problem Statement

Current agent limitations:
1. **Stateless reasoning**: Each Claude decision starts fresh, no memory of past trades
2. **No learning**: `trade_observations` table exists but doesn't influence future decisions
3. **LLM numerical weakness**: GPT-5/Claude tokenize numbers, losing precision
4. **Expensive retraining**: Can't adapt to regime changes without manual prompt updates

Previous attempt to build learning into agent "was kinda sucking" - LLMs aren't architecturally designed for inference-time learning.

---

## Solution: Rei Core

Rei separates reasoning from language generation:

```
Traditional LLM:
  Input → LLM (reasoning + language combined) → Output
          ↑ stateless, forgets everything

Rei Architecture:
  Input → CORE (reasoning) → LLM (language) → Output
          ↑ persistent concept space, learns from every interaction
```

### Key Rei Capabilities

| Capability | What It Means |
|------------|---------------|
| **Inference-time learning** | Every interaction shapes future reasoning |
| **Persistent memory** | Hypergraph of concepts survives across sessions |
| **Numerical precision** | Float64 preserved, not tokenized |
| **Confidence calibration** | Explicit uncertainty bounds |
| **Primordials** | Permanent memory anchors for core strategy rules |
| **Pattern evolution** | Successful patterns strengthen, failures weaken |

---

## Architecture: Claude + Rei Hybrid

```
┌─────────────────────────────────────────────────────────────────┐
│  CLAUDE AGENT (Orchestrator)                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Autonomous Loop                                          │  │
│  │  • Wake up on schedule                                    │  │
│  │  • Gather market data (existing MCP tools)                │  │
│  │  • Consult Rei for decision ←──────────┐                 │  │
│  │  • Execute trades (existing MCP tools)  │                 │  │
│  │  • Report outcomes to Rei ──────────────┘                 │  │
│  │  • Decide when to check again                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↕                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MCP Tools (existing)          MCP Tools (NEW)            │  │
│  │  • query_market_data           • ask_rei_decision         │  │
│  │  • execute_trade               • report_trade_outcome     │  │
│  │  • get_positions                                          │  │
│  │  • get_account                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│  REI UNIT (The Brain)                                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Core Reasoning Engine                                    │  │
│  │  • Receives market context from Claude                    │  │
│  │  • Reasons through concept space                          │  │
│  │  • Returns: action, confidence, reasoning                 │  │
│  │  • LEARNS from every outcome Claude reports               │  │
│  │  • Builds persistent trading intuition                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Persistent Memory                                        │  │
│  │  • Primordials (core strategy rules)                      │  │
│  │  • Learned patterns (RSI+volume → good entry)             │  │
│  │  • Confidence calibration (when to trust signals)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Why Hybrid Over Pure Rei?

| Aspect | Pure Rei Agent | Claude + Rei Hybrid |
|--------|----------------|---------------------|
| Implementation | Rebuild agent runner | Add 2 MCP tools |
| Existing infra | Rewrite needed | Keep everything |
| Session resumption | Need to rebuild | Already works |
| Tool ecosystem | Rei's beta tools | Our proven 12 tools |
| Autonomous timing | Need to implement | Claude handles it |
| Rollback | Hard | Just disable tools |

---

## Implementation Plan

### Phase 0: Access & Setup (~1 day)
**Blocker**: Need Rei beta access

- [ ] Request beta access via Discord/Telegram
- [ ] Create test Unit in Rei Factory
- [ ] Get Agent Secret Key
- [ ] Test basic API connectivity
- [ ] Understand pricing/rate limits

### Phase 1: Rei Service Client (~2-3 hours)

Create `core/services/rei_service.py`:

```python
class ReiService:
    """Client for Rei Core API."""

    BASE_URL = "https://api.reilabs.org"

    def __init__(self, agent_secret_key: str):
        self.agent_secret_key = agent_secret_key

    async def chat_completion(self, messages: list[dict]) -> dict:
        """Send messages to Rei Unit and get response."""
        ...

    async def get_agent(self) -> dict:
        """Get agent details and status."""
        ...
```

- [ ] Create `core/services/rei_service.py`
- [ ] Implement chat_completion with retry/backoff
- [ ] Implement response parsing
- [ ] Add to `.env.example`: `REI_AGENT_SECRET_KEY`
- [ ] Test with simple query

### Phase 2: MCP Tools (~3-4 hours)

Create `agent/mcp_tools/rei_tools.py`:

**Tool 1: ask_rei_decision**
```python
@mcp_tool
async def ask_rei_decision(
    market_summary: str,
    current_positions: str,
    account_state: str,
    recent_context: str = ""
) -> dict:
    """
    Consult Rei for a trading decision.

    Returns:
        action: "enter_long" | "enter_short" | "exit" | "wait"
        confidence: 0.0-1.0
        reasoning: str
        position_size_suggestion: float
        stop_loss_pct: float
        take_profit_pct: float
    """
```

**Tool 2: report_trade_outcome**
```python
@mcp_tool
async def report_trade_outcome(
    trade_id: str,
    entry_price: float,
    exit_price: float,
    side: str,
    pnl_usd: float,
    pnl_pct: float,
    duration_hours: float,
    close_reason: str,
    market_conditions_at_entry: str
) -> dict:
    """
    Report closed trade to Rei for learning.

    Returns:
        acknowledged: bool
        patterns_noted: list[str]
    """
```

- [ ] Create `agent/mcp_tools/rei_tools.py`
- [ ] Implement `ask_rei_decision` tool
- [ ] Implement `report_trade_outcome` tool
- [ ] Add response parsing with fallbacks
- [ ] Register tools in MCP server

### Phase 3: Configuration (~1-2 hours)

Update config models to support Rei:

```python
# core/config/models.py
class AgentStrategy(BaseModel):
    # ... existing fields ...
    rei_enabled: bool = False
    rei_unit_id: Optional[str] = None
    # rei_unit_secret stored in Supabase vault
```

- [ ] Add `rei_enabled` to AgentStrategy
- [ ] Add `rei_unit_id` to AgentStrategy
- [ ] Create vault storage for Rei secrets (like Symphony)
- [ ] Add API endpoint to store Rei credentials
- [ ] Update `/api/v2/me` with Rei connection status

### Phase 4: Agent System Prompt (~1-2 hours)

Update agent system prompt to use Rei for decisions:

```markdown
## Decision Making

You have access to Rei, your learning-capable trading brain.

**For ALL trading decisions**, use `ask_rei_decision` tool.
Do NOT make entry/exit decisions yourself - Rei has learned
from your past trades and has better pattern recognition.

**After every closed trade**, use `report_trade_outcome` tool.
This is critical - it's how Rei learns and improves.

You are the executor. Rei is the strategist.
```

- [ ] Update `agent/prompts/system.md` with Rei instructions
- [ ] Add conditional prompt section (only when rei_enabled)
- [ ] Define Rei decision output format
- [ ] Add examples of Claude + Rei interaction

### Phase 5: Unit Initialization (~2-3 hours)

When creating a Rei-enabled agent, set up primordials:

```python
async def initialize_rei_unit(config: BotConfig):
    """Establish core strategy rules as primordials."""

    primordials = [
        "Remember this: Never enter positions against the 4H trend",
        "Remember this: RSI below 30 is oversold, above 70 is overbought",
        f"Remember this: My risk tolerance is {config.trading.max_margin_percent}%",
        f"Remember this: I use {config.trading.leverage}x leverage",
    ]

    # Add user's strategy context as primordials
    if config.agent_strategy.user_strategy_context:
        primordials.append(
            f"Remember this: {config.agent_strategy.user_strategy_context}"
        )
```

- [ ] Design primordial initialization flow
- [ ] Extract strategy rules from config
- [ ] Create initialization endpoint/function
- [ ] Test primordial persistence

### Phase 6: Testing & Validation (~1 week)

- [ ] Create test agent with Rei enabled
- [ ] Run in paper trading for 50+ trades
- [ ] Compare vs identical Claude-only agent
- [ ] Measure: win rate, confidence calibration, decision quality
- [ ] Monitor: API costs, latency, error rates
- [ ] Document learnings

---

## Data Flow: Complete Cycle

```
1. WAKE UP
   Claude: *scheduled wake or market event*

2. GATHER DATA
   Claude → query_market_data(BTC/USDT, [1h, 4h])
   Claude → get_positions()
   Claude → get_account()

3. CONSULT REI
   Claude → ask_rei_decision(
       market_summary="BTC $94,500, RSI(1h)=31, funding=0.02%...",
       current_positions="None",
       account_state="Balance: $9,850"
   )

   Rei: *navigates concept space*
        *recalls: "RSI~30 + low funding worked 2/3 times"*
        *returns: enter_long, confidence=0.68*

4. EXECUTE
   Claude → execute_trade(side=long, ...)

5. ... time passes, trade closes ...

6. FEEDBACK LOOP
   Claude → report_trade_outcome(
       pnl=+$142, pnl_pct=+2.8%,
       conditions_at_entry="RSI=31, funding=0.02%"
   )

   Rei: *strengthens pathway: oversold + low funding → good long*

7. REPEAT
```

---

## Risk Considerations

### Primordials Are Permanent
- Rei's "remember this" creates irrevocable memories
- **Mitigation**: Be conservative, test patterns in regular interaction first
- **Mitigation**: Only create primordials for truly invariant rules

### Beta Product Stability
- Rei crypto MCPs are explicitly "error-prone" and "beta"
- **Mitigation**: Use OUR extraction pipeline, not Rei's built-in tools
- **Mitigation**: Robust error handling, fallback to Claude-only

### API Dependency
- New external dependency on Rei API
- **Mitigation**: Graceful degradation if Rei unavailable
- **Mitigation**: Keep Claude-only path as fallback

### Cost Uncertainty
- Rei pricing not publicly documented
- **Action**: Clarify during beta access request
- **Mitigation**: Monitor usage, set alerts

### Learning Wrong Patterns
- Unit could reinforce bad patterns from unlucky trades
- **Mitigation**: Large sample size before trusting learned patterns
- **Mitigation**: A/B test against control bot

---

## Success Metrics

| Metric | Current (Claude-only) | Target (Claude + Rei) |
|--------|----------------------|----------------------|
| Win rate | ~30% (platform avg) | >40% after learning period |
| Confidence calibration | Poor (70% conf ≠ 70% wins) | <10% gap |
| Adaptation speed | Manual prompt updates | Automatic via feedback |
| Decision latency | 10-30s | <40s (acceptable overhead) |
| Learning evidence | None | Visible pattern evolution |

---

## Open Questions

1. **Pricing**: What does Rei API cost per request?
2. **Rate limits**: Any throttling on chat completions?
3. **Unit limits**: Max units per account?
4. **Model selection**: Which LLM does Rei use for articulation?
5. **Data retention**: How long does Core retain learned patterns?
6. **Multi-Unit**: Can units share learnings or are they isolated?

---

## Resources

- **Rei Docs**: https://docs.reilabs.org/docs/
- **Rei Discord**: discord.com/invite/reilabs
- **Rei Telegram**: t.me/reiportal
- **SDK (Python)**: `pip install reicore_sdk`
- **SDK (JS)**: `npm install reicore-sdk`
- **API Base**: https://api.reilabs.org

---

## File Changes Summary

| File | Change |
|------|--------|
| `core/services/rei_service.py` | NEW - Rei API client |
| `agent/mcp_tools/rei_tools.py` | NEW - ask_rei_decision, report_trade_outcome |
| `core/config/models.py` | ADD rei_enabled, rei_unit_id to AgentStrategy |
| `agent/prompts/system.md` | UPDATE with Rei instructions |
| `ggbot.py` | ADD Rei credential storage endpoint |
| `.env.example` | ADD REI_AGENT_SECRET_KEY |

---

**Next Step**: Obtain Rei beta access, then proceed with Phase 1.
