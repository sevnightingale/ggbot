Below is a fast-read briefing that answers the five open questions, with a focus on whether take-profit/stop-loss (TP/SL) information can be queried through CCXT across different exchanges.

🔑 One-paragraph take-away
Most futures venues expose TP/SL as ordinary “reduce-only” or strategy orders, so you can fetch them via CCXT’s fetch_open_orders()/watchOrders() as long as you know the exchange-specific flags (e.g., reduceOnly on BitMEX, closePosition=true on Binance). Spot exchanges are spottier—many force you to emulate TP/SL locally. Given the schema break, ship a compatibility SQL VIEW first to keep the decision engine alive, then refactor it to the new position-centric model once tests are green. Treat leverage, stops and config links as strategy-metadata, not trade columns: store them in a separate strategy_runs table and join on trade_id.

1 Can we query TP/SL from exchanges?
Venue	How TP/SL are represented	CCXT / API access
BitMEX	Separate limit/market orders with ordType='Stop' or ordType='TakeProfit'; flagged reduceOnly	Returned by fetch_open_orders(); flags visible in info blob 
blog.bitmex.com
bitmex.com
Binance Futures	“Strategy orders” (OTOCO) with closePosition=true and reduceOnly; also surfaced on the User-Data WebSocket stream	Fetchable with fetch_open_orders(); real-time via watchOrders() in CCXT Pro 
binance.com
dev.binance.vision
stackoverflow.com
Bybit / OKX / KuCoin Futures	TP/SL are paired conditional orders; require symbol-side filtering	Visible as separate orders; some endpoints need the category=futures param 
github.com
Spot venues (Binance spot, Kraken, Coinbase)	Native TP/SL not supported; must be emulated client-side	CCXT can’t fetch what isn’t there 
github.com
Edge cases	Some exchanges don’t include TP/SL in fetch_positions(); you must poll orders	Design your bot so that position sync ≠ risk-order sync

Bottom line: Futures exchanges: yes; spot: usually no. Your new trade_orders table already captures everything you need—just insert any order where reduceOnly=true OR closePosition=true and tag it tp_sl=true.

2 Where should TP/SL logic live?
Option A — Exchange-native
Place linked TP/SL orders when a position opens.
Pros: exchange closes you even when your server is down; no latency.
Cons: not portable to spot venues; some APIs (e.g., Bitget) hide filled TP/SL orders until they trigger. 
github.com

Option B — Local watcher
Store desired TP/SL in DB, monitor mark price, fire a market order when hit.
Pros: works everywhere, one code path.
Cons: depends on your latency; can slip in fast moves.

Recommendation: Hybrid—use native TP/SL on futures, local watcher as a fallback for spot.

3 Decision engine: refactor vs. compatibility layer
Path	Speed to green	Long-term tech-debt
SQL VIEW compatibility layer (CREATE VIEW legacy_trades AS …)	🟢 Hours – map symbol→pair, hard-code leverage=NULL, stop_loss=NULL	Adds one view to maintain, minimal code churn 
stackoverflow.com
Full decision-engine rewrite	🔴 Days-to-weeks	Clean future, but blocks pipeline

Do the view first so tests pass, then schedule the refactor. That matches Gartner “rehost → refactor later” guidance. 
netapp.com
valuecoders.com

4 How to handle config_id, leverage and other per-strategy settings
Treat them as strategy metadata, not trade columns:

text
Copy
Edit
strategy_runs
-------------
strategy_run_id  PK
config_id        FK configs(id)
trade_id         FK trades(trade_id)
leverage         DECIMAL
stop_loss        DECIMAL
take_profit      DECIMAL
decision_json    JSONB   -- confidence, reasoning, etc.
This keeps the trades table lean and lets one position feed multiple analytics views.

5 Migration reality check
You already nuked legacy rows, so no historical migration headache. From here:

Add the compatibility view to unblock decision-engine tests.

Augment adapters to tag TP/SL orders (is_risk_order) and store them in trade_orders.

Extend lifecycle manager to pull realised P&L from those fills.

Create strategy metadata table and wire new trades to the current config.

Once tests pass, flip the feature flag and retire the view.

6 Priority call
Day 0: Ship the SQL VIEW so CI goes green.

Day 1–2: Patch adapters to capture TP/SL orders on BitMEX & Binance futures.

Day 3+: Begin decision-engine refactor to native schema; remove VIEW once parity reports <0.1 % P&L delta.

Do that and the pipeline breathes again without rolling back your hard-won lifecycle upgrade.







Sources






You said:
we will always be doing futures so spot doesn't matter


ChatGPT said:

Thought for 10 seconds
Got it — if you’re futures-only you can ignore the spot caveats and lean fully on the exchanges’ native risk-order facilities.

1 TP/SL on the big futures venues (all CCXT-supported)
Exchange	How to place the order	How CCXT exposes it	Flag(s) to test for in info
BitMEX	send ordType='Stop' or TakeProfit' + reduceOnly=true	fetch_open_orders() / watchOrders() returns them as standalone orders	reduceOnly, ordType, execInst='Close,LastPrice'
Binance Futures (USDT & COIN-M)	use “strategy order”: closePosition=true and either stopPrice (SL) or price (TP)	shows up as a normal LIMIT/MARKET order, reduceOnly=true, closePosition=true	closePosition, reduceOnly, workingType
Bybit	conditional order with reduce_only=1	returned in fetch_open_orders(); WebSocket stream sends orderType='TakeProfitMarket', etc.	reduce_only, tp_sl_mode
OKX	“algo order” with tpTriggerPx / slTriggerPx	fetch_orders() with algo=true	algoClOrdId, tpTriggerPx, tpOrdPx
KuCoin Futures	“stop” order with stop='down'/'up' + reduceOnly=true	visible in both fetch and WS	reduceOnly, stop
Deribit	separate TP/SL orders with reduce=true	same pattern	reduce, order_type

Reality check: every major futures venue surfaces these as ordinary orders tagged with a reduce-only/close flag. So:

Storage rule: insert any order whose info blob has reduceOnly=true OR closePosition=true OR order_type ∈ {TakeProfit*,Stop*} and tag it is_risk_order=true.

Lifecycle rule: when one of these fills, decrement size_contracts; if that brings the position to zero, the lifecycle manager closes the trade.

No need for a price-watcher fallback.

2 Schema tweaks specific to futures
Add is_risk_order BOOL to trade_orders.

Optional but handy: risk_type ENUM('TP','SL').

That lets you reconstruct which exit leg closed the trade and what portion was partial.

3 Decision-module compatibility
Because you’re futures-only, the legacy fields the decision engine cares about boil down to:

pair → symbol

leverage → can be fetched from leverage in NormalizedPosition or stored in new strategy_runs table.

stop_loss, take_profit → derive from most recent TP/SL orders linked to the trade.

config_id → store in strategy_runs.

Thus a SQL VIEW can still bridge the gap quickly:

sql
Copy
Edit
CREATE OR REPLACE VIEW legacy_trades AS
SELECT
    t.trade_id,
    t.symbol          AS pair,
    sr.leverage,
    sr.stop_loss,
    sr.take_profit,
    sr.config_id,
    t.entry_price,
    t.size_contracts AS collateral_amount,  -- if they used it that way
    t.status         AS trade_status,
    t.opened_at      AS created_at,
    '{}'::jsonb      AS execution_details   -- stub
FROM trades t
LEFT JOIN strategy_runs sr USING (trade_id)
WHERE t.status = 'open';
That keeps the decision engine alive while you refactor it to call the new schema directly.

4 Risk-management data flow
Trade opens

store strategy_run with desired leverage, tp_price, sl_price.

Order placement

engine submits entry + TP/SL orders (native reduce-only).

store those order IDs in trade_orders (is_risk_order=true).

Lifecycle manager

on each WS/REST update, adjust position size.

When size hits 0, mark trade closed and read realised P&L from fills (fees already attached).

5 Execution priorities
Day	Action
0	Add is_risk_order column; create the legacy_trades view; tests green.
1	Patch adapters to flag TP/SL orders; update lifecycle manager to recognise is_risk_order.
2	Populate strategy_runs on trade open; legacy view now returns leverage/TP/SL.
3-4	Begin deprecating decision-engine’s legacy query path, swapping to the new tables.

Ship the view first, then clean up—your futures-only scope means zero spot edge-cases and no need for local stop logic.