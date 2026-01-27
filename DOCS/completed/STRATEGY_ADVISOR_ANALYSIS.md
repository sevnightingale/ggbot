# Strategy Advisor Analysis Feature

**Status**: PLANNING
**Created**: 2025-12-28
**Complexity**: Medium-High (~8-12 hours)

---

## Problem Statement

Users have no automated way to understand why their bot is winning or losing. Currently:
- Must manually browse activities to understand bot behavior
- No statistical analysis of what patterns work
- No correlation between market data and outcomes
- No actionable recommendations

## Solution Overview

Enhance Strategy Advisor with:
1. **Button prompts** instead of empty textbox ("Create Strategy" | "Analyze Performance" | "Improve Config")
2. **Automated performance analysis** that queries trade history, correlates with market data, and produces actionable insights
3. **AI synthesis** that turns statistics into recommendations

---

## Analysis Framework

Based on our Technician analysis, the automated analysis should cover:

### 1. Basic Statistics
```python
{
    "total_trades": 97,
    "wins": 28,
    "losses": 69,
    "win_rate": 0.289,
    "total_pnl": -660.17,
    "avg_win": 10.22,
    "avg_loss": 13.58,
    "risk_reward_ratio": 0.75,
    "breakeven_winrate_needed": 1.33  # Impossible!
}
```

### 2. Direction Analysis
```python
{
    "longs": {"trades": 57, "wins": 21, "win_rate": 0.37, "pnl": -410.21},
    "shorts": {"trades": 40, "wins": 7, "win_rate": 0.18, "pnl": -249.96}
}
```

### 3. Market Data Correlation
```python
{
    "patterns": [
        {
            "name": "1H MACD Rising + Long",
            "trades": 35,
            "win_rate": 0.429,
            "pnl": -356.86,
            "is_best": True
        },
        {
            "name": "1H MACD Falling + Short",
            "trades": 28,
            "win_rate": 0.179,
            "pnl": -197.57,
            "is_worst": True
        }
    ]
}
```

### 4. Duration & Big Loss Analysis
```python
{
    "avg_win_duration_min": 43.8,
    "avg_loss_duration_min": 37.6,
    "big_losses": [
        {"pnl": -133.95, "duration_min": 115, "side": "long", "confidence": 0.60}
    ],
    "big_loss_total": -403.0,
    "big_loss_pct_of_losses": 0.61
}
```

### 5. Confidence Calibration
```python
{
    "buckets": [
        {"range": "55-60%", "trades": 45, "actual_win_rate": 0.27},
        {"range": "60-65%", "trades": 40, "actual_win_rate": 0.30},
        {"range": "65-70%", "trades": 12, "actual_win_rate": 0.33}
    ],
    "calibration_gap": 0.35  # Bot says 60% but wins 29%
}
```

### 6. AI-Generated Recommendations
```python
{
    "critical": [
        {
            "issue": "Risk/Reward Inverted",
            "detail": "Avg win $10.22 vs avg loss $13.58 = 0.75:1 R:R",
            "recommendation": "Tighter stop loss (2-3%) or trailing TP",
            "expected_impact": "Break-even becomes achievable"
        },
        {
            "issue": "Shorts Underperforming",
            "detail": "18% win rate vs 37% for longs",
            "recommendation": "Add 'only take long positions' to strategy",
            "expected_impact": "+$250 saved, WR improves to ~37%"
        }
    ],
    "moderate": [...],
    "minor": [...]
}
```

---

## Technical Architecture

### Backend Analysis Service

**New File**: `core/services/performance_analyzer.py`

```python
class PerformanceAnalyzer:
    """Analyzes bot trading performance and generates insights."""

    def __init__(self, config_id: str):
        self.config_id = config_id

    async def analyze(self) -> PerformanceReport:
        """Run full analysis and return structured report."""
        trades = await self._get_trades()
        activities = await self._get_market_queries()

        return PerformanceReport(
            basic_stats=self._calculate_basic_stats(trades),
            direction_analysis=self._analyze_direction(trades),
            market_correlation=self._correlate_market_data(trades, activities),
            duration_analysis=self._analyze_duration(trades),
            confidence_calibration=self._calibrate_confidence(trades),
            recommendations=await self._generate_recommendations(...)
        )

    def _correlate_market_data(self, trades, activities):
        """Match trades to preceding market_query and extract patterns."""
        # For each trade, find the market_query that preceded it
        # Parse indicator values from technical_analysis text
        # Aggregate by pattern (e.g., "1H MACD rising + long")
        # Compare win rates across patterns
        pass

    async def _generate_recommendations(self, stats, patterns, ...):
        """Use LLM to synthesize findings into actionable recommendations."""
        # Build prompt with all statistical findings
        # Ask LLM to prioritize issues and suggest fixes
        # Return structured recommendations
        pass
```

### API Endpoint

**File**: `api/assistant.py` (extend existing)

```python
@router.post("/api/v2/assistant/analyze/{config_id}")
async def analyze_performance(config_id: str, user_id: str = Depends(get_user_id)):
    """Run performance analysis for a bot."""

    # Verify ownership
    config = await config_service.get_config(config_id)
    if config.user_id != user_id:
        raise HTTPException(403, "Not authorized")

    # Check minimum trades
    trade_count = await get_trade_count(config_id)
    if trade_count < 20:
        return {"error": "Need at least 20 trades for meaningful analysis"}

    # Run analysis
    analyzer = PerformanceAnalyzer(config_id)
    report = await analyzer.analyze()

    return report.to_dict()
```

### Frontend Strategy Advisor Enhancement

**File**: `frontend/components/StrategyAdvisorPanel.tsx`

```tsx
// Current: Empty textbox
// Proposed: Button prompts + textbox

<div className="strategy-advisor">
  {!hasStartedChat && (
    <div className="prompt-buttons">
      <button onClick={() => startChat("create")}>
        Create Strategy
      </button>
      <button onClick={() => startChat("analyze")}>
        Analyze Performance
      </button>
      <button onClick={() => startChat("improve")}>
        Improve Config
      </button>
    </div>
  )}

  <ChatMessages messages={messages} />
  <ChatInput ... />
</div>
```

**"Analyze Performance" Flow**:
1. User clicks "Analyze Performance"
2. Show loading state: "Analyzing 97 trades..."
3. Call `/api/v2/assistant/analyze/{config_id}`
4. Display formatted report in chat
5. User can ask follow-up questions

---

## Implementation Phases

### Phase 1: Analysis Service (~4 hours)
- [ ] Create `core/services/performance_analyzer.py`
- [ ] Implement `_get_trades()` - fetch all closed trades
- [ ] Implement `_get_market_queries()` - fetch market_query activities
- [ ] Implement `_calculate_basic_stats()` - trades, wins, P&L, R:R
- [ ] Implement `_analyze_direction()` - long vs short breakdown
- [ ] Implement `_correlate_market_data()` - parse indicators, match to trades
- [ ] Implement `_analyze_duration()` - hold times, big losses
- [ ] Implement `_calibrate_confidence()` - bucket by confidence, compare to outcome
- [ ] Create `PerformanceReport` dataclass with all sections

### Phase 2: Recommendation Engine (~2 hours)
- [ ] Create prompt template for analysis synthesis
- [ ] Implement `_generate_recommendations()` using Claude Haiku
- [ ] Structure output as critical/moderate/minor issues
- [ ] Include specific actionable suggestions
- [ ] Add expected impact estimates

### Phase 3: API Endpoint (~1 hour)
- [ ] Add `/api/v2/assistant/analyze/{config_id}` endpoint
- [ ] Add ownership verification
- [ ] Add minimum trades check
- [ ] Return structured JSON report
- [ ] Add to ACTIVE.md API documentation

### Phase 4: Frontend Button Prompts (~2 hours)
- [ ] Redesign StrategyAdvisorPanel with button prompts
- [ ] Create button grid: "Create Strategy" | "Analyze Performance" | "Improve Config"
- [ ] Hide buttons after first interaction (show chat)
- [ ] Style buttons per VIBE.md

### Phase 5: Analysis Display (~2 hours)
- [ ] Create `AnalysisReport` component for formatted display
- [ ] Render critical issues with red/yellow/green indicators
- [ ] Collapsible sections for detailed stats
- [ ] Action items with "Apply to Config" buttons (future)
- [ ] Handle loading state during analysis

### Phase 6: Testing & Polish (~1 hour)
- [ ] Test with bots that have various trade counts
- [ ] Test with bots that have different issues
- [ ] Verify correlation logic is accurate
- [ ] Handle edge cases (no trades, no market queries, etc.)

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `core/services/performance_analyzer.py` | NEW - Analysis service |
| `core/domain/performance_report.py` | NEW - Report dataclass |
| `api/assistant.py` | Add /analyze endpoint |
| `frontend/components/StrategyAdvisorPanel.tsx` | Button prompts, analysis display |
| `frontend/components/AnalysisReport.tsx` | NEW - Formatted report component |
| `ACTIVE.md` | Document new endpoint |

---

## Data Sources

### Trades Table (`paper_trades`)
- side, realized_pnl, confidence_score
- opened_at, closed_at (for duration)
- close_reason

### Activities Table (`activities`)
- activity_type = 'market_query'
- details->'formatted_data'->'technical_analysis'
- details->'formatted_data'->'volume_confirmation'
- created_at (to match with trade opened_at)

### Correlation Logic
```sql
-- Match each trade to its preceding market_query
WITH trade_entries AS (
    SELECT trade_id, side, realized_pnl, opened_at, ...
    FROM paper_trades WHERE config_id = ? AND status = 'closed'
),
market_queries AS (
    SELECT created_at, details->'formatted_data' as data
    FROM activities WHERE config_id = ? AND activity_type = 'market_query'
)
SELECT te.*, mq.data
FROM trade_entries te
CROSS JOIN LATERAL (
    SELECT * FROM market_queries mq
    WHERE mq.created_at <= te.opened_at
    ORDER BY mq.created_at DESC
    LIMIT 1
) mq
```

---

## Indicator Parsing

The technical_analysis is a formatted string. Need to parse:

```python
def parse_timeframe_section(tech_text: str, timeframe: str) -> str:
    """Extract a specific timeframe section."""
    pattern = rf'=== {timeframe} ===(.*?)(?==== \d|$)'
    match = re.search(pattern, tech_text, re.DOTALL | re.IGNORECASE)
    return match.group(1) if match else ""

def extract_indicators(section: str) -> dict:
    """Extract key indicators from a timeframe section."""
    indicators = {}

    # RSI
    rsi_match = re.search(r'RSI at ([\d.]+)', section)
    if rsi_match:
        indicators['rsi'] = float(rsi_match.group(1))

    # MACD trend
    if 'MACD rising' in section:
        indicators['macd'] = 'rising'
    elif 'MACD falling' in section:
        indicators['macd'] = 'falling'

    # Aroon
    aroon_match = re.search(r'Aroon Up: ([\d.]+)', section)
    if aroon_match:
        indicators['aroon_up'] = float(aroon_match.group(1))

    # ... more indicators
    return indicators
```

---

## Recommendation Prompt Template

```
You are analyzing trading bot performance. Based on the following statistics,
identify the most critical issues and provide specific, actionable recommendations.

## STATISTICS
{json.dumps(stats, indent=2)}

## MARKET DATA PATTERNS
{json.dumps(patterns, indent=2)}

## INSTRUCTIONS
1. Identify the 2-3 most critical issues hurting performance
2. For each issue, provide:
   - Clear description of the problem
   - Specific recommendation to fix it
   - Expected impact if fixed
3. Prioritize by potential P&L impact
4. Be specific - reference actual numbers from the data

## OUTPUT FORMAT
Return JSON:
{
  "critical": [{"issue": "...", "detail": "...", "recommendation": "...", "impact": "..."}],
  "moderate": [...],
  "minor": [...]
}
```

---

## Success Criteria

1. Analysis runs in <10 seconds for 100 trades
2. Correctly identifies direction bias (long vs short)
3. Correctly calculates risk/reward ratio
4. Market data correlation produces actionable patterns
5. Recommendations are specific and actionable
6. Users report finding insights they didn't know

---

## Future Enhancements

1. **"Apply to Config" buttons** - One-click apply recommendation
2. **Backtesting** - "What if you only took longs?" simulation
3. **Alerts** - Notify when R:R ratio inverts
4. **Comparison** - Compare two bots' performance
5. **Time-based analysis** - Performance by hour/day of week

---

## Open Questions

1. How many trades minimum for meaningful analysis? (Proposed: 20)
2. Should analysis be cached? (Probably yes, with TTL)
3. Should we show raw data or just insights?
4. Cost: LLM call for recommendations (~$0.01-0.02 per analysis)

---

## Related Work

- Existing Strategy Advisor: `api/assistant.py`, `frontend/components/StrategyAdvisorPanel.tsx`
- Activity logging: `core/common/activity_logger.py`
- Trade data: `trading/paper/supabase_service.py`
