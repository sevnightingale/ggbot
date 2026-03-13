Common mistakes when writing ggbots strategies:

1. Assuming indicators exist as JSON fields: They often arrive as text inside technical_analysis
2. Forgetting runtime validation: Always check: missing fields, stale data, numeric sanity
3. Not handling missing position state: Default to FLAT
4. Emitting inconsistent output: Always return one deterministic JSON object
5. Writing strategies like documentation: ggbots needs explicit decision logic
For example, use this master prompt when asking the strategy advisor LLM to generate a ggbots-ready trading strategy:

Write a trading strategy specification designed to run inside the GGbots runtime.

Important constraints:

1. Runtime data structure

Market data arrives as a JSON payload where indicators appear inside:

data.details.formatted_data.technical_analysis

This field is freeform text, not structured JSON.

Indicators must be parsed from text sections like:

=== 30M ===
=== 1H ===
=== 4H ===

Do NOT assume structured indicator fields exist.

2. Strategy must contain these sections

- Strategy Idea
- Required Runtime Inputs
- Parsing Expectations
- Validation Rules
- Entry Logic
- Position Management Logic

Output JSON Specification

3. Runtime safety rules

- Validate all required inputs before using them
- Handle missing fields gracefully
- Handle stale market data
- Assume FLAT position if no position state is present
- Only require position-management fields when state is LONG

4. Decision output

The strategy must output exactly one deterministic JSON object with:

action: ENTER_LONG | CLOSE | HOLD | PASS
reason: reason code
confidence: numeric value
margin_pct: numeric value
sl: numeric or null
tp1: numeric or null
tp2: numeric or null
notes: array of strings

5. Execution guarantees

- JSON output must contain no prose or markdown
- Numeric fields must be numbers, not strings
- Every decision branch must end in a valid JSON output
- Strategy must not rely on unavailable historical state

6. Logic clarity

Keep logic deterministic and easy to audit.

Prefer:

- Simple thresholds
- Explicit validation
- Clear exit conditions

Avoid:

- Implicit assumptions
- Undefined states
- Complex hidden dependencies
♟️

How are you doing sir
Hey @sevnightingale @sebastiansidoh @sebastian_sidoh_bot 👋 quick tech question about strategy runtime.

I'm running a text-runtime strategy that parses indicators from formatted_data.technical_analysis.

Two things seem off:

1) The bot output still shows
mode = 30M_BB_MEAN_REVERSION_LONG_ONLY
which comes from an earlier deployed version. Even though the deployed strategy should return
30M_BB_LITE_TEXT_RUNTIME_COMPAT_LONG_ONLY
(now changed to 30M_BB_LITE_TEXT_RUNTIME_COMPAT_LONG_ONLY_V2A for the next test).

So it looks like the old strategy might still be executing (possible caching?).

2) My strategy expects adx: ADX=... inside the === 30M === section, but the runtime payload doesn't seem to include ADX even though it's enabled in indicators (see screenshot).

There's other evidence too, on both.

Questions:

- Is there any strategy caching after updating config?

- Does technical_analysis actually include ADX values for custom timeframes?

Trying to confirm whether the issue is deployment or indicator formatting. Thanks!


The current GGBots architecture is excellent for stateless signal bots.
The next evolution could be enabling stateful execution strategies.
Without persistent state, strategies must be simplified to:
● Indicator thresholds
● Stateless signals
● One-shot decisions
This works for basic strategies but removes many advanced techniques. With richer state
support, ggbots could support:
● Structure-aware strategies
● Scaling systems
● Regime-based trading
● Complex position management
These are the types of strategies commonly used by experienced systematic traders.
Below are ggbots platform improvements that would enable more advanced strategies:
1. Persistent strategy state
Many strategies maintain custom structures across bars. Example:
● Arrays of support/resistance zones
● Order block lists
● Regime classification memory
● Last swing high / low
● Volatility state
Currently scheduled bots cannot safely maintain this kind of state.
Proposed capability
Allow each bot to maintain a persistent key-value state store:
bot_state = {
regime: "mean_reversion",
last_entry_price: 2050,
swing_low: 2015,
order_blocks: [...]
}
Features needed:
● Persistent storage between executions
● Mutation per bar
● Optional reset when strategy version changes
This would unlock many structure-based strategies.
2. Native position state contract
Strategies often depend on detailed information about the current position.
Important fields include:
● Position side
● Position size
● Average entry price
● Entry timestamp
● Bars since entry
● Unrealized PnL
● Realized PnL
Currently some of these must be treated as optional inputs with fallbacks.
Proposed capability
Guarantee a standard position state object on every cycle:
position = {
side: "LONG",
size: 1.25,
avg_price: 2030,
entry_bar: 43822,
bars_since_entry: 12,
unrealized_pnl: 0.032
}
This removes the need for defensive logic and improves reliability.
3. Multi-tranche / Pyramiding state
Many real strategies add to positions gradually. Example:
● DCA entries
● Scaling into momentum
● Martingale layers
● Volatility averaging
These require knowledge of previous entries.
Proposed capability
Expose a tranche ledger:
tranches = [
{price: 2040, size: 0.5},
{price: 2020, size: 0.5},
{price: 2005, size: 0.75}
]
This allows strategies to calculate:
● Weighted average price
● Distance between entries
● Dynamic DCA sizing
● Exposure management
Without this, many scaling strategies must be disabled.
4. Historical candle access
A lot of advanced strategies rely heavily on historical context. Examples:
● Pivot confirmation
● Swing detection
● Rolling volatility
● Multi-bar breakout confirmation
Typical constructs:
close[1]
close[2]
ta.pivothigh(...)
ta.pivotlow(...)
Proposed capability
Expose historical bars inside the payload:
ohlcv_history = {
30m: [... last 200 bars ...]
}
This enables:
● Pivot detection
● Regime classification
● Pattern detection
● Structure-aware trading
5. Deterministic bar-close execution
Many strategies assume evaluation occurs exactly on bar close. Scheduled execution can
sometimes introduce:
● Partial bars
● Stale payloads
● Duplicate evaluations
Proposed capability
Expose clear execution semantics:
bar = {
timeframe: "30m",
index: 84231,
closed_at: timestamp,
is_new_bar: true
}
Guaranteeing bar-close evaluation prevents subtle logic errors.
6. Canonical indicator schema
During experimentation, a common friction point was indicator naming differences.
Examples:
● BB
● BBW
● bollinger_bands
● upper_band
Strategies become fragile if indicator names change.
Proposed capability
Standardized indicator fields:
indicators = {
rsi_30m
ema_30m_50
atr_30m_14
bb_upper_30m
bb_lower_30m
bb_mid_30m
}
A stable schema would dramatically simplify strategy design.
7. Macro series support
Some strategies rely on macro indicators such as:
● USDT dominance
● DXY
● VIX
● MOVE index
These often require historical values to compute moving averages.
Proposed capability
Provide normalized macro series:
macro = {
usdt_dom: {
value: 6.1,
ema50_daily: 5.8
}
}
This enables regime filters and panic detection.
8. Strategy event journal
A useful addition would be a structured history of recent actions.
Example:
recent_events = [
{type: "entry", reason: "RSI_OVERSOLD"},
{type: "exit", reason: "TP"},
{type: "pass", reason: "NO_SETUP"}
]
This allows strategies to implement logic like:
● Cooldown after losses
● Regime switching
● Adaptive risk controls