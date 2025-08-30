Verdict

Architecture direction: good. Clean interfaces, domain models, repo pattern, mode-aware routing.
Production readiness: not yet. Several correctness/consistency gaps that will bite you.

High-severity issues (fix first)

Legacy mode field
You’re branching on self.config.config_type. That’s the legacy field you’re removing. Use config.mode: Literal["autonomous_trading","signal_validation"] (Enum), or this engine will break the moment you accept D2.

Timeframe blindness
Every market decision is timeframe-bound. _get_fresh_market_data(symbol) and the entire flow don’t accept/propagate a timeframe. Your universal cache design requires keys like (symbol, timeframe, candle_close, version). Add timeframe everywhere (engine ctor or method arg) and pass it to repos.

Freshness path is a dead end
_get_fresh_market_data returns None and the caller just errors. This must trigger extraction and await, with concurrency protection:

Check cache; if stale, acquire per-symbol lock, enqueue extraction, await result (with timeout/backoff).

Never return None unless you’ve tried extraction.

SL/TP lost in transit
_parse_llm_response extracts stop_loss_price and take_profit_price, but _create_strategy_run throws them away. Later _create_trading_intent tries to read them from decision_context.confidence_factors (where they don’t exist), so they’re always None. Persist them in StrategyRun (or in DecisionContext) and pass through.

Async/sync mismatch
You call config_repo.get_config, position_repo.get_active_positions, market_data_repo.get_fresh_data, strategy_run_repo.save without await. If these hit DB/network they should be async. Pick a style and enforce it (prefer async IO; otherwise make them clearly sync repos).

LLM client usage + naming
Docstrings and method name say GPT-5; code uses "gpt-4". Call it _call_llm, make model configurable in BotConfig, and handle provider errors with retries/jitter + idempotency token for decisions.

Medium-severity issues

Single-symbol assumption
self.config.selected_pair suggests one symbol; your product wants multi-symbol/multi-timeframe. Decide now: engine scoped to (config_id, symbol, timeframe) or accept arrays and loop. Don’t hide this in a field named “selected_pair”.

Position management takes first only
active_positions[0] drops other positions. Either iterate and emit intents per position or push PM orchestration to the scheduler (per-position jobs).

Prompt system coupling
Direct .format on self.config.decision.system_prompt/user_prompt assumes those keys exist and strings won’t break. Move to a prompt composer that:

Validates template variables,

Adds standardized headers (symbol, timeframe, candle timestamps),

Injects explicit indicator summaries (with units) not free-form strings.

Price source & symbol format
_get_current_price mocks CCXT format like "BTC/USDT" while Symbol.internal_format may be Hummingbot (BTC-USDT). Standardize via Symbol value object and adapters; never key maps by free strings.

Error handling pattern
Returning {'action':'error'} mixes control and domain. Raise a typed DecisionError and let the orchestrator turn that into retries/circuit-breakers/alerts.

Timestamps
Use datetime.now(timezone.utc) and ISO8601 with “Z”. Don’t put naive datetimes in DB/logs.

Logging
Include config_id, symbol, timeframe, scenario, strategy_run_id in every log as structured fields.

Low-severity / polish

Remove unused imports (asyncio, DataFreshness).

Pull regex compilation out of the loop in _parse_llm_response.

Confidence threshold 0.7 → config-driven.

Rename decision_type vs scenario to avoid redundancy.

Minimal concrete changes (illustrative)
# 1) Mode field
if self.config.mode == "signal_validation":
    ...
elif self.config.mode == "autonomous_trading":
    ...

# 2) Timeframe propagation (method signatures)
async def make_decision(self, symbol: Optional[str]=None, timeframe: str="1h", signal_data: Optional[Dict]=None): ...
market_data = await self._get_fresh_market_data(symbol_obj, timeframe)

# 3) Freshness + extraction trigger
async def _get_fresh_market_data(self, symbol: Symbol, timeframe: str, max_age_seconds: int = 30):
    snapshot = await market_data_repo.get_fresh_data(symbol, timeframe, max_age_seconds)
    if snapshot: return snapshot
    async with extraction_locks.per_symbol(symbol, timeframe):
        # double-check after acquiring lock
        snapshot = await market_data_repo.get_fresh_data(symbol, timeframe, max_age_seconds)
        if snapshot: return snapshot
        await extraction_service.extract_all(symbol, timeframe)  # await result or set a short timeout
        return await market_data_repo.get_fresh_data(symbol, timeframe, max_age_seconds)

# 4) Preserve SL/TP
decision_data = self._parse_llm_response(llm_response)
...
strategy_run = StrategyRun.create_opportunity_analysis(...,
    stop_loss=decision_data.get("stop_loss_price"),
    take_profit=decision_data.get("take_profit_price"),
)

Alignment with your refactor plan

✅ Service layer + domain models: you’re on track.

❌ Still tied to config_type: switch to mode now.

❌ Not compatible yet with universal extraction’s timeframe/candle-aware cache.

⚠️ Prompt system needs the modular composer.

⚠️ Multi-position and multi-symbol scheduling decisions are still implicit; make them explicit in the orchestrator, not ad-hoc in this class.

Final take

Good skeleton; wrong assumptions around mode field, timeframe, and freshness. Fix those three, preserve SL/TP, make repos consistently async, and this becomes a solid DecisionEngine v2 foundation.

You said:
1) no we actually decided to keep config_type and repurpose it. originally it was to separate the 3 agent configs, then we consolidated to only 1 config with the agents nested so it was legacy, but then we decided it could be repurposed for modes. So config_type = 'autonomous trading' or 'signal validation' modes. 
2) explain the use of timeframe in the current code more, and what you're proposing, explain more and in simple terms, idk what you're talking about. 
3) ok. 
4) good catch.
5) yeah good catch.
6) agreed. 
ChatGPT said:

Got it. Here’s a crisp update addressing each point.

1) config_type

Keeping and repurposing config_type for modes is fine. My only asks:

Make it an Enum ({"autonomous_trading","signal_validation"}), validate at API boundary.

Document it as “mode,” not “type,” in code/docs to prevent old mental models from leaking in.

Add config_version so future mode additions (e.g., “paper_review”) don’t surprise old configs.

2) Timeframe — what’s missing and what I propose (plain English)

What your code does now:

It asks for “fresh market data” without saying which timeframe (1m, 5m, 15m, 1h, 4h…).

Indicators and strategies depend on timeframe (RSI(14) on 1h ≠ RSI(14) on 5m).

Your universal cache idea also depends on timeframe (cache must be keyed by it).

Simple mental model:

Think of each (symbol, timeframe) as a separate “data stream.”

Decisions should run per (symbol, timeframe), and on candle close for that timeframe.

Concretely add:

In config:

primary_timeframe: str (e.g., "15m").

analysis_timeframes: List[str] (optional, for multi-TF inputs like ["15m","1h","4h"]).

In engine signatures (minimal):

make_decision(symbol: Optional[str], timeframe: Optional[str]=None, ...)

If timeframe not provided, use config.primary_timeframe.

In repositories & cache:

market_data_repo.get_fresh_data(symbol, timeframe, ...)

Cache key: (symbol, timeframe, candle_close_ts, feature_version).

In scheduler:

Jobs are per (config_id, symbol, timeframe) and fire on candle close for that timeframe.

No arbitrary “every 30s” polling—tie execution to candle boundaries (with tiny jitter).

For multi-timeframe strategies:

Fetch the primary timeframe as the decision anchor.

Optionally enrich the prompt with higher TF context (e.g., trend from 4h, confirmation from 1h).

Make this explicit in config: mtf_context: {"include": true, "timeframes": ["1h","4h"]}.

The decision context must record exactly which timeframes were used.

3) Freshness/extraction (we agree)

Implement the per-(symbol,timeframe) lock + extraction trigger path. Never return None without attempting extraction and double-checking the cache after the lock.

4) SL/TP propagation (fix)

Parse → include stop_loss/take_profit in StrategyRun (and/or DecisionContext).

Surface them in the trading intent from the stored fields (not confidence_factors).

5) Async consistency (fix)

Pick async for repos or make them explicitly sync—don’t mix. Given DB/IO, go async:

await config_repo.get_config(...)

await position_repo.get_active_positions(...)

await market_data_repo.get_fresh_data(...)

await strategy_run_repo.save(...)

6) LLM client/model (fix)

Rename to _call_llm, model comes from config (and provider in the future).

Add retries with jitter and an idempotency key (config_id + symbol + timeframe + candle_close_ts).

Use UTC timestamps in ISO8601 with Z.

Minimal deltas you can apply now

Add primary_timeframe to BotConfig; pass timeframe through make_decision → _get_fresh_market_data → repos.

Change scheduler to run per (config_id, symbol, timeframe) on candle close.

Promote SL/TP to first-class fields in StrategyRun and trading intents.

Flip repos to async and validate config_type Enum at the API boundary.

Do that, and the engine aligns with your universal extraction + mode-aware orchestration—without a rewrite.