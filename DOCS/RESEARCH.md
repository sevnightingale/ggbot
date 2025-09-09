Here’s the blunt take: your template is a solid “container,” but it’s not production-ready for autonomous use. Three critical gaps:

1. It’s unstructured. Inputs are free-text blobs; output isn’t machine-robust.
2. It’s ambiguous. “hold” vs “wait”; no explicit entry/position sizing hooks though your goal says the strategy defines them.
3. It lacks guardrails. No staleness checks, missing-indicator handling, or “don’t hallucinate metrics not in data.”

Below is a tighter, drop-in replacement that keeps your “user supplies the strategy” philosophy while making it reliable for an execution pipeline.

---

# What to fix (strongly recommended)

* **JSON-only output** with a strict schema; reject anything else.
* **Single neutral no-trade state** (“WAIT”), not “hold” vs “wait.”
* **Guardrails:** If required indicators are missing or data is stale, return `WAIT` with `data_status.complete=false`.
* **Evidence not chain-of-thought:** cite specific indicator values + timeframe (structured), no long prose.
* **Numeric types:** prices/confidence are numbers, not strings; fixed precision.
* **Strategy-driven fields:** allow the user’s strategy to define timeframe priority, entry logic, and position sizing; the template should just surface those.
* **Action set control:** allow caller to pass `allowed_actions` (e.g., disallow SHORT if the venue can’t short).
* **Signal freshness:** include `as_of` and `valid_until`.
* **RR/Risk sanity check:** if R\:R < strategy minimum (e.g., 1.5), force `WAIT`.

---

# Improved prompt template (drop-in)

```python
def build_opportunity_analysis_prompt(
    symbol: str,
    current_price: float,
    market_data_json: str,      # JSON string: per-timeframe indicators (see schema note)
    volume_analysis_json: str,  # JSON string: volume/OBV/VPVR, etc.
    user_strategy: str,         # Free text OR JSON; user defines how to trade
    as_of_iso: str,             # ISO8601 timestamp for the data snapshot
    allowed_actions: str = "LONG,SHORT,WAIT",  # comma-separated
    stale_minutes: int = 5
) -> str:
    """
    Build an opportunity-analysis prompt that treats the user_strategy as the ONLY source of trading logic.
    This template enforces structured I/O and guardrails for autonomous use.
    """

    return f"""
You are an execution-grade crypto opportunity evaluator. You DO NOT invent strategy rules.
You strictly apply the user's strategy to the supplied, structured market data.

## CONTEXT
- Instrument: {symbol}
- Current Price: {current_price}
- Data As-Of: {as_of_iso}
- Allowed Actions: {allowed_actions}
- Stale Threshold (minutes): {stale_minutes}

## MARKET DATA (STRUCTURED, DO NOT REINTERPRET SHAPE)
market_data_json:
{market_data_json}

volume_analysis_json:
{volume_analysis_json}

## USER STRATEGY (SOURCE OF TRUTH)
The user defines how to trade (timeframe priority, entry rules, stop/TP rules, position sizing).
Use ONLY these rules. If rules are ambiguous or required indicators are missing, return WAIT with rationale.
user_strategy:
{user_strategy}

## RULES YOU MUST FOLLOW
1) Do not use indicators or timeframes not present in market_data_json/volume_analysis_json.
2) If any indicator required by the user strategy is missing OR data is older than {stale_minutes} minutes from {as_of_iso}, set action=WAIT and data_status.complete=false.
3) Respect Allowed Actions: if SHORT not allowed, you cannot output SHORT.
4) If the user strategy specifies timeframe precedence (e.g., 4h > 1h > 15m), follow it strictly.
5) Confidence is a real number in [0,1], calibrated by the user strategy’s confluence rules. If the strategy doesn’t define calibration, keep confidence ≤ 0.6.
6) Only propose trades with a strategy-compliant stop and target; if R:R below the strategy minimum, output WAIT.
7) Output STRICT JSON only. No extra text.

## OUTPUT JSON SCHEMA (STRICT)
Return exactly this shape and nothing else:

{{
  "action": "LONG" | "SHORT" | "WAIT",
  "confidence": number,                         # 0.000–1.000
  "entry": {{
    "type": "MARKET" | "LIMIT" | "STOP" | null,
    "price": number | null,
    "valid_until": "ISO8601" | null
  }},
  "stop_loss": number | null,
  "take_profit": [number, ...] | null,          # allow multiple targets if the strategy uses scales
  "position_size": {{
    "units": number | null,
    "notional": number | null
  }} | null,
  "evidence": [                                  # cite exact evidence, not chain-of-thought
    {{
      "timeframe": "5m|15m|30m|1h|4h|1d|1w",
      "indicator": "RSI|MACD|EMA50|... (as in data)",
      "value": number,
      "rule_evaluated": "e.g., RSI>70",
      "status": "met|not_met"
    }}
  ],
  "risk_reward": {{
    "rr": number | null,
    "atr": number | null
  }},
  "data_status": {{
    "as_of": "{as_of_iso}",
    "complete": true | false,
    "missing_indicators": [ "..." ]
  }}
}}

## EVALUATION INSTRUCTIONS
- Apply the user_strategy exactly. If it specifies entries/position sizing, populate those fields. If it says the executor determines size elsewhere, set position_size to null.
- If the strategy uses fixed offsets (e.g., SL = entry - 1.5 * ATR(14)), compute them from provided data.
- Keep numbers to sensible precision for {symbol}. Do NOT round away risk controls.
- If signals conflict per the strategy’s precedence rules, prefer higher-priority timeframe; otherwise WAIT.

Return STRICT JSON only.
"""
```

---

# Minimal market\_data schema (example your data pipeline should supply)

Keep your inputs structured so the LLM can’t misread them:

```json
{
  "5m": {"price": 123.45, "rsi": 73.2, "macd": {"line": 0.004, "signal": 0.001, "hist": 0.003}, "ema": {"20": 122.8, "50": 121.9}, "atr": 0.9, "volume": 1_234_567},
  "15m": {...},
  "1h": {...},
  "4h": {...},
  "1d": {...}
}
```

And volume:

```json
{
  "obv": 1234567,
  "vpvr": [{"price": 120.0, "volume": 2_000_000}, {"price": 124.0, "volume": 1_100_000}],
  "delta": {"buy": 600000, "sell": 500000}
}
```

---

# Optional: suggest a structured strategy format (users can still paste prose)

If you want to make strategy entry painless but unambiguous, support a JSON shape like:

```json
{
  "timeframe_priority": ["4h", "1h", "15m"],
  "rules": [
    {"timeframe": "4h", "indicator": "MACD", "op": "crossover", "direction": "bullish"},
    {"timeframe": "15m", "indicator": "RSI", "op": ">", "threshold": 70}
  ],
  "risk": {"min_rr": 1.8, "sl_via": "ATR", "atr_mult": 1.5},
  "entry": {"type": "LIMIT", "source": "prev_high_break + tick"},
  "position_sizing": {"method": "fixed_risk", "risk_pct": 0.5}
}
```

---

## Verdict

* **Concept:** Good bones. Clear separation of “strategy (user)” vs “container (template)”.
* **Blocking issues for autonomy:** unstructured I/O, ambiguous actions, no guardrails.
* **After these fixes:** You’ll have an execution-grade container where the user only drops in a strategy and data, and the LLM outputs deterministic, parseable decisions—no extra prompt-engineering required.
