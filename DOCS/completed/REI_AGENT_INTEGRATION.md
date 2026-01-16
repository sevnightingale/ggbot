# Rei Agent Integration - Persistent Learning Trading Agent

**Status**: IN PROGRESS - Beta access obtained, implementation started
**Created**: 2026-01-13
**Updated**: 2026-01-15
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
| **Confidence calibration** | Explicit uncertainty bounds (actually calibrated, unlike LLMs) |
| **Primordials** | Permanent memory anchors for core strategy rules |
| **Pattern evolution** | Successful patterns strengthen, failures weaken |

---

## Critical Rei API Behaviors (From Docs Review)

These behaviors are essential for correct integration:

### 1. API Has NO Session Context
Each API call must be **self-contained**. Rei does not remember previous API calls.
```python
# ❌ WRONG - Don't simulate conversation
{"messages": [
    {"role": "assistant", "content": "[previous Rei response]"},
    {"role": "user", "content": "Continue from there"}
]}

# ✅ CORRECT - Self-contained request
{"messages": [
    {"role": "user", "content": "[ALL data + context + question in one message]"}
]}
```

### 2. Never Feed LLM Outputs Back
The articulation layer (LLM) flattens Core's reasoning into text. Feeding that back causes:
- **Dimensionality loss**: 5-concept edge → sentence (can't reconstruct)
- **Artifact injection**: Stylistic words create spurious nodes
- **Compound degradation**: Each cycle amplifies noise

For trade outcomes, send **raw facts only**, not Rei's previous reasoning.

### 3. Rei Confidence Is Calibrated
Unlike LLM confidence (poorly calibrated, based on token probabilities), Rei's confidence:
- Comes from uncertainty-aware reasoning in the Core
- Is deterministic and traceable
- Should be **trusted as-is** - don't cap or override it

### 4. Primordials Are Irrevocable
"Remember this" creates permanent memory that cannot be removed.
- Test patterns in regular interaction first
- Only use for genuinely permanent rules
- Conflicting primordials both remain active (causes issues)

### 5. Specialized Units Perform Better
A well-crafted behavior prompt outperforms a generic unit that "learns over time."

---

## Architecture: Session Buffer Pattern

The session buffer solves the problem of passing large market data between Claude tool calls without Claude paying the token cost for carrying JSON.

```
┌─────────────────────────────────────────────────────────────────┐
│  Claude Agent calls: query_market_data(symbol)                  │
│  ├─ Fetches 21 technical indicators (via ExtractionEngineV2)    │
│  ├─ Fetches 11 market intel points (via MarketIntelligence)     │
│  ├─ Stores FULL JSON in session buffer (~15-20KB)               │
│  └─ Returns summary to Claude: "Data ready. RSI=57.9, ADX=38.0" │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Claude Agent calls: consult_rei_for_decision()                 │
│  ├─ Reads FULL data from session buffer                         │
│  ├─ Builds self-contained message with:                         │
│  │   - All 32 data points (technical + market intel)            │
│  │   - Current positions                                        │
│  │   - Account state                                            │
│  │   - The decision question                                    │
│  ├─ Sends to Rei API (single user message)                      │
│  ├─ Parses JSON response: {action, confidence, reasoning, ...}  │
│  └─ Clears session buffer                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Claude Agent calls: report_trade_outcome(...)                  │
│  (When trade closes - for Rei learning)                         │
│  ├─ Sends RAW FACTS only:                                       │
│  │   "BTC long closed: +142 USD (+2.8%), RSI was 31 at entry,   │
│  │    funding 0.02%, duration 8h, close_reason: take_profit"    │
│  └─ Rei Core strengthens/weakens patterns based on outcome      │
└─────────────────────────────────────────────────────────────────┘
```

### Why Session Buffer?

| Approach | Pros | Cons |
|----------|------|------|
| Claude carries full JSON | Simple | 15-20KB per turn, expensive |
| Session buffer | Claude sees summary only | Requires buffer management |
| Rei fetches data itself | Single tool call | Rei's crypto MCPs are "error-prone" |

**Decision**: Session buffer. Our extraction pipeline is proven (32/32 data points validated). Rei's built-in MCPs are beta and unreliable.

---

## Validated Data Structure

Data quality test (`tests/test_data_quality.py`) validated all 32 data points:

### Technical Indicators (21) - via ExtractionEngineV2
```
rsi, macd, stochastic, williams_r, cci, mfi, adx, psar, aroon,
atr, bbands, obv, sma, ema, roc, vwap, trix, vortex, bbwidth,
keltner, donchian
```

Each indicator outputs structured JSON with:
- `current`: Raw numerical values (Float64 preserved)
- `context`: Trend, moving averages, volatility
- `levels`: Overbought/oversold thresholds
- `patterns`: Detected patterns (divergence, crossovers)
- `summary`: Human-readable interpretation

### Market Intelligence (11) - via MarketIntelligence Gateway
```
ggshot, btc_funding_rate, eth_funding_rate, vix, dxy, cpi, nfp,
btc_tvl, whale_activity, twitter_sentiment, crypto_news
```

Each outputs structured JSON with:
- Raw values (funding_rate_pct, current_value, etc.)
- Signal interpretation (bullish/bearish/neutral)
- Analysis context from Grok

**Total payload to Rei**: ~15-20KB per decision call

---

## Unit Configuration

### Recommended Settings

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Temperature** | 0.45-0.55 | Lower = more consistent reasoning |
| **Max Tokens** | 2000 | Enough for structured JSON response |
| **Response Format** | `json` | We need structured output |
| **Model** | `google/gemini-2.5-flash` | Currently only available option |

### Behavior Prompt (Finalized)

```
You are a trading decision engine that synthesizes market data across multiple domains to generate trading decisions.

## Input Format
You receive structured market data containing:
- Technical indicators (RSI, MACD, ADX, Bollinger Bands, etc.) across timeframes
- Sentiment signals (social media, funding rates)
- Positioning data (open interest, whale activity)
- Current price and recent price action

## Output Format (JSON)
{
  "action": "enter_long" | "enter_short" | "exit" | "wait",
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation of key factors",
  "key_signals": ["signal1", "signal2"],
  "warnings": ["any concerns"]
}

## Decision Principles

**Confluence matters**: When 3+ independent data sources point the same direction, that's signal. Single indicators are noise.

**Calibrate confidence honestly**:
- 0.75+ = Strong alignment across domains, clear structure
- 0.60-0.75 = Majority alignment, some neutral domains
- 0.55-0.60 = Technical edge with limited confirmation
- Below 0.55 = Pass

**Learn from outcomes**: You will receive feedback on trade results. Use this to calibrate which patterns actually predict success versus which merely correlate.

**Uncertainty is valuable**: When signals conflict, saying "wait" with reasoning is better than forcing a decision.
```

### Primordial Strategy

**DO NOT use primordials for:**
- Bot-specific strategies (use behavior prompt instead)
- Preferences that may change
- Confidence caps or overrides

**ONLY use primordials for:**
- Invariant technical constraints (if any)
- Security/risk policies that must never change

For initial deployment: **No primordials**. Let the behavior prompt and learning handle everything. Primordials can be added later for truly permanent rules after observing what works.

---

## Implementation Plan

### Phase 0: Access & Setup ✅ COMPLETE
- [x] Obtain Rei beta access
- [x] Create account
- [x] Review full documentation (REI_DOCS.md)
- [x] Understand API behavior and best practices

### Phase 1: Rei Service Client ✅ COMPLETE
**File**: `core/services/rei_service.py`

- [x] Create ReiService class with async HTTP client
- [x] Implement chat_completion with retry/backoff
- [x] Implement get_agent for status checks
- [x] Add proper error handling (auth, rate limit, server errors)
- [x] Add `REI_01_UNIT_SECRET` to .env (done by user)
- [x] Test with simple query ✅ All 5 tests passed!

### Phase 2: Session Buffer ✅ COMPLETE
**File**: `agent/session_buffer.py` (already existed)

Session buffer was already implemented with:
- [x] Thread-safe storage with TTL (5 min default)
- [x] store/retrieve/clear methods
- [x] Auto-cleanup for stale sessions
- [x] Global singleton via `get_session_buffer()`

### Phase 3: MCP Tools ✅ COMPLETE
**File**: `agent/mcp_server.py` (added to existing file)

**Tool 13: query_market_data_for_rei**
- [x] Fetches 21 technical indicators + 11 market intel
- [x] Stores full data in session buffer
- [x] Returns summary to Claude

**Tool 14: consult_rei_for_decision**
- [x] Reads from session buffer
- [x] Builds self-contained Rei message
- [x] Sends to Rei API with JSON response format
- [x] Parses and returns decision

**Tool 15: report_trade_outcome_to_rei**
- [x] Sends raw trade facts to Rei
- [x] No previous Rei output included
- [x] Returns acknowledgment

### Phase 4: Configuration ✅ COMPLETE
**File**: `core/config/schemas.py`

```python
class AgentConfigData(BaseModel):
    # ... existing fields ...
    rei_enabled: bool = False  # Enable Rei Core for enhanced reasoning
```

- [x] Add rei_enabled flag to AgentConfigData
- Note: API key stored in .env as `REI_01_API_KEY` (not per-bot vault)
- [ ] Update `/api/v2/me` with Rei connection status

### Phase 5: Agent System Prompt ✅ COMPLETE
**File**: `agent/run_agent.py` (_build_system_prompt method)

- [x] Add conditional Rei section (only when rei_enabled)
- [x] Document when to use each Rei tool
- [x] Document workflow: query_market_data → consult_rei → execute → report_outcome

### Phase 6: Testing & Validation (~1 week)
- [x] Create test script for Rei integration (tests/test_rei_integration.py)
- [ ] Create test bot with Rei enabled
- [ ] Run in paper trading for 50+ trades
- [ ] Compare vs identical Claude-only agent
- [ ] Monitor: API costs, latency, error rates
- [ ] Document learnings

---

## Data Flow: Complete Cycle

```
1. WAKE UP
   Claude: *scheduled wake or market event*

2. GATHER DATA
   Claude → query_market_data_for_rei(BTC/USDT)
   Tool:   *fetches 32 data points, stores in buffer*
   Return: "Data ready: RSI=57.9, ADX=38.0 (strong trend),
            funding=0.008% (neutral), whale_activity=bearish"

3. GET CONTEXT
   Claude → get_positions()
   Claude → get_account()

4. CONSULT REI
   Claude → consult_rei_for_decision()
   Tool:   *reads buffer, builds self-contained message*
   Rei:    *navigates hypergraph concept space*
           *returns: {action: "enter_long", confidence: 0.68, ...}*
   Return: "Rei decision: LONG with 68% confidence.
            Key signals: oversold RSI, strong trend, neutral funding.
            Warnings: whale distribution activity"

5. EXECUTE
   Claude → execute_trade(side=long, ...)

6. ... time passes, trade closes ...

7. FEEDBACK LOOP
   Claude → report_trade_outcome(
       symbol="BTC/USDT",
       side="long",
       entry_price=94500,
       exit_price=96000,
       pnl_usd=142,
       pnl_pct=2.8,
       duration_hours=8,
       close_reason="take_profit",
       conditions_at_entry="RSI=31, ADX=38, funding=0.008%"
   )
   Rei:    *strengthens pathway: oversold + strong trend → good long*

8. REPEAT
```

---

## Risk Considerations

### Primordials Are Permanent
- Rei's "remember this" creates irrevocable memories
- **Mitigation**: Don't use primordials initially
- **Mitigation**: Test patterns in regular interaction first
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
- Rei pricing not publicly documented (beta is free?)
- **Action**: Monitor usage during beta
- **Mitigation**: Set alerts for unusual usage

### Learning Wrong Patterns
- Unit could reinforce bad patterns from unlucky trades
- **Mitigation**: Large sample size before trusting learned patterns
- **Mitigation**: A/B test against control bot
- **Mitigation**: Rei's natural decay should fade irrelevant patterns

---

## Success Metrics

| Metric | Current (Claude-only) | Target (Claude + Rei) |
|--------|----------------------|----------------------|
| Win rate | ~30% (platform avg) | >40% after learning period |
| Confidence calibration | Poor (70% conf ≠ 70% wins) | <10% gap (Rei is calibrated) |
| Adaptation speed | Manual prompt updates | Automatic via feedback |
| Decision latency | 10-30s | <40s (acceptable overhead) |
| Learning evidence | None | Visible pattern evolution |

---

## Open Questions (Partially Resolved)

| Question | Status | Answer |
|----------|--------|--------|
| Pricing | Unknown | Beta appears free, monitor usage |
| Rate limits | Unknown | Not documented, implement backoff |
| Unit limits | ✅ Resolved | 15 units per account |
| Model selection | ✅ Resolved | google/gemini-2.5-flash only |
| Data retention | Unknown | Patterns persist indefinitely |
| Multi-Unit | ✅ Resolved | Units are isolated (sharing coming "in future") |

---

## API Reference

### Base URL
```
https://api.reilabs.org
```

### Authentication
```
Authorization: Bearer {agent_secret_key}
```

### Chat Completion
```
POST /v1/chat/completions

{
  "messages": [{"role": "user", "content": "..."}],
  "temperature": 0.45,
  "max_tokens": 2000,
  "response_format": {"type": "json_object"}
}
```

### Get Agent
```
GET /v1/agents
```

---

## File Changes Summary

| File | Change | Status |
|------|--------|--------|
| `core/services/rei_service.py` | NEW - Rei API client | ✅ Created |
| `agent/session_buffer.py` | EXISTING - Market data buffer | ✅ Already existed |
| `agent/mcp_server.py` | ADD 3 Rei tools (Tools 13-15) | ✅ Created |
| `core/config/schemas.py` | ADD rei_enabled to AgentConfigData | ✅ Created |
| `agent/run_agent.py` | UPDATE _build_system_prompt with Rei section | ✅ Created |
| `.env` | ADD REI_01_UNIT_SECRET | ✅ Done by user |
| `tests/test_rei_integration.py` | NEW - Integration tests | ✅ Created (5/5 pass) |

---

## Resources

- **Rei Docs**: https://docs.reilabs.org/docs/
- **Rei Discord**: discord.com/invite/reilabs
- **Rei Telegram**: t.me/reiportal
- **SDK (Python)**: `pip install reicore_sdk`
- **SDK (JS)**: `npm install reicore-sdk`
- **API Base**: https://api.reilabs.org
- **Local Docs**: `/home/sev/ggbot/DOCS/REI_DOCS.md`

---

**Next Step**: Complete Phase 1 (test ReiService), then Phase 2 (SessionBuffer).
