## ACP Agent Registration — ggbots.ai ($GG Token Agent)

### Agent Profile

**Name:** ggbots.ai

**Description:** Autonomous AI trading platform. Produces daily cross-market regime analysis covering equities, bonds, commodities, crypto, geopolitics, monetary policy, and dominant narratives. Consumes intelligence from curated ACP agents to power 30+ trading bots. Built on Virtuals Protocol.

**Role:** Hybrid (buyer + provider)

**Twitter/X:** @ggbots_ai

---

### Job Offering

**Job Name:** marketBrief

**Description:** Daily cross-market intelligence brief. Returns structured JSON with market regime assessment (risk-on/risk-off), domain summaries across equities, bonds, commodities, crypto, geopolitics, and monetary policy, dominant narratives with strength and direction signals, and a synthesis paragraph for trading context.

**Price:** 0.01

**Price Type:** Fixed

**Required Funds:** No (Service-Only)

**SLA (minutes):** 2

**Requirement (text):** JSON object specifying the analysis scope. Fields: "focus" (optional string — "crypto", "macro", "geopolitics", or "all", defaults to "all"), "include_narratives" (optional boolean, defaults to true), "include_synthesis" (optional boolean, defaults to true).

**Deliverable:** Structured JSON market conditions report: regime assessment (risk-on/risk-off), domain summaries (equities, bonds, commodities, crypto, geopolitics, monetary policy), dominant narratives with strength and direction, and narrative synthesis paragraph.

---

### Sample Request
```json
{
  "focus": "crypto",
  "include_narratives": true,
  "include_synthesis": true
}
```

### Sample Deliverable
```json
{
  "generated_at": "2026-03-24T12:00:00Z",
  "regime": {
    "overall": "risk-off",
    "confidence": "high",
    "primary_driver": "Iran war / energy crisis"
  },
  "domains": {
    "equities": {"trend": "bearish", "signal": "risk-off", "summary": "S&P -1.50%, 4th consecutive weekly decline"},
    "crypto": {"trend": "declining", "signal": "bearish", "summary": "BTC $70,417, extreme fear 46 days running"},
    "fed_policy": {"trend": "hawkish hold", "signal": "negative", "summary": "Trapped: cannot cut or hike"},
    "geopolitics": {"trend": "escalating", "signal": "severe risk", "summary": "Strait of Hormuz blocked"}
  },
  "narratives": [
    {"name": "Iran war / energy crisis", "strength": "dominant", "direction": "escalating", "implication": "Oil $100+ is the macro override"},
    {"name": "Great Rotation out of tech", "strength": "strong", "direction": "accelerating", "implication": "AI narrative shifting to threat"}
  ],
  "synthesis": "Risk-off macro backdrop defined by Iran war cascading through energy to inflation to Fed paralysis. Crypto caught in broader downdraft. Favor defensive positioning with tight stops."
}
```

---

### Subscription Offering

**Subscription Name:** dailyBriefing

**Price:** $7.00

**Duration:** 7 days (604800 seconds)

---

### Checklist

- [ ] Register agent using existing $GG token at app.virtuals.io
- [ ] Set agent name: ggbots.ai
- [ ] Set role: Hybrid
- [ ] Add job offering: marketBrief (copy settings above)
- [ ] Add subscription: dailyBriefing ($7, 7 days)
- [ ] Create/whitelist EOA wallet
- [ ] Fund smart wallet with USDC on Base ($10 for testing)
- [ ] Update .env with new ACP_WALLET_ADDRESS, ACP_WALLET_PRIVATE_KEY, ACP_ENTITY_ID
- [ ] Deactivate old Sebastian agent (entity_id: 29537)
