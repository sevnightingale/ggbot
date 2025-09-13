# ggbots Forge — Phase 2 UI/UX Spec (v1)

Senior UI/UX guidance focused on a professional, real‑time trading experience with low cognitive load and high trust.

---

## 0) Product Principles (non‑negotiable)

* **Two clear modes per bot:** *Monitor* vs *Configure*. Never mix. Default to **Monitor** for safety.
* **Multi‑bot is first‑class:** switching is instant, stateful per bot, and never loses context.
* **Trust by design:** explicit environment (Paper/Live), live heartbeat, last update timestamps, auditability.
* **Progressive disclosure:** start simple; reveal complexity on demand.
* **Optimistic but verifiable:** actions feel instant; confirmations appear as SSE events.

---

## 1) Information Architecture & Navigation

**Global frame**

* **Left Rail (Bots):** persistent list of user bots with compact status chips and inline actions.
* **Primary Tabs (per bot):** **Monitor** | **Configure**. Persist user’s last tab *per bot*.
* **Secondary Tabs:** context-specific within each mode.

**URL model**

* `/forge?bot=<configId>&mode=monitor&view=overview`
* Deep-linkable subviews for support/debugging.

---

## 2) Layout Template (per bot)

**Persistent Status Bar (top of content)**

* **Pipeline indicator:** Extraction → Decision → Trading → Idle, with stage animation and timestamps.
* **Next run:** countdown pill + schedule tooltip.
* **Connectivity:** SSE heartbeat (Connected/Retrying), Exchange health, API key validity.
* **Environment:** Paper/Live pill; **Start/Stop** button (guarded when Live).
* **Last update:** time‑ago with absolute time on hover.

**12‑column grid**

* **Monitor ▸ Overview**

  * **\[8 cols]** Equity Curve (area), P\&L by day (bars), Drawdown (line) — compact stacked cards with shared timeframe picker.
  * **\[8 cols]** Open Positions table (sticky header, compact rows, inline Close/Adjust TP/SL).
  * **\[4 cols]** Decision Feed (LLM reasoning summaries with confidence), Alerts/Errors, Upcoming schedule.
* **Configure** surfaces a form scaffold (see §4) with sticky Save/Publish bar.

**Empty / Loading / Error states**

* Empty: guidance, links to Templates; Loading: skeletons; Error: retry with diagnostics.

---

## 3) Multi‑Bot Management

**Left Rail (Bots List)**

* Row: Bot name • status chip • P\&L 24h • env pill. Hover: quick actions (Start/Stop, Duplicate, Delete).
* **Create Bot** button at top; opens template gallery.

**Fast switching**

* Switch maintains per‑bot view preferences. Abort SSE for prior bot; subscribe to new bot immediately.
* **⌘/Ctrl+K** Command Palette with fuzzy search across bots.

**Compare mode (optional v2)**

* Checkbox to select up to 2 bots → overlays key metrics & charts with color‑safe differentiation.

---

## 4) Configuration Editing (progressive, safe)

**Model: Draft → Publish**

* Autosave drafts; **Publish** required to take effect. Prompt to **Test‑run** on publish.
* **Diff viewer** (Draft vs Published). Version history with revert.

**Sections (secondary tabs under Configure)**

1. **Strategy**

   * Templates: *Scalper*, *Trend*, *Mean‑reversion*, *Arbitrage (beta)* with descriptions.
   * Parameters surface only those relevant to the selected template.
2. **Market Data Sources**

   * **Matrix view**: Categories (Technical, Signals, Sentiment, News, Influencers, On‑chain, Fundamental) × Data points.
   * Controls: toggle include, weight slider (0–1), timeframe chips (5m, 1h, 1d; allow multi‑select), lookback window.
   * Cost/latency est. badges where applicable; backfill toggle.
3. **AI Decision Logic**

   * System/User prompt editors with tokenized variables (e.g., {{symbol}}, {{timeframe}}, {{risk\_budget}}).
   * **Frequency**: simple presets (Every 5m/15m/1h) + **Advanced** (cron).
   * **Test Decision**: run on historical snapshot; preview reasoning & action.
4. **Risk Management**

   * Position sizing (fixed %, Kelly cap), **Max concurrent positions**, Daily loss cap, SL/TP %, trailing stop.
   * **Risk preview**: simulated max drawdown band vs balance.
5. **LLM Configuration**

   * Provider select (OpenAI, DeepSeek…), Model select, token & context limits, **cost estimator**.
   * API keys (masked, scoped) + **Test connection**.
6. **Trading Setup**

   * Exchange selection & account link. **Mode**: Paper vs Live (default Paper).
   * Live guard: confirm modal summarizing current risk settings + recent performance.
7. **Advanced / JSON**

   * Monaco editor with schema validation; **Format** & **Validate** buttons; import/export.

**Validation & Feedback**

* Inline validation with side summary; sticky bar shows errors count and **Publish** disabled until resolved.

---

## 5) Real‑Time Monitoring (trust & clarity)

**Key cards (top row)**

* Balance • Equity • Unrealized P\&L • Realized P\&L (day) • Win rate (30d). Tooltips with definitions.

**Charts**

* Equity curve, Daily P\&L, Drawdown. Timeframe: 1D/7D/30D/All.

**Open Positions**

* Columns: Symbol, Side, Size, Entry, Mark, P\&L, SL/TP, Age, Status.
* Row actions: Close, Adjust SL/TP (sheet), View on exchange. Confirmations when Live.

**Decision Feed**

* For each run: summary sentence, confidence chip (0–100), time, link to full reasoning (sheet), inputs snapshot (selected data points & weights used).

**Pipeline Timeline**

* Last N runs with per‑stage durations, errors (click to details). Trend of cycle time.

**Countdown & Schedule**

* Primary countdown; “Run now” (respects throttles). Snooze 1 cycle.

**Alerts & Health**

* SSE: Connected/Retrying/Offline; last event age. Exchange latency, rate limit state, key expiry.
* Notifications center with severity levels; audit trail.

---

## 6) Visual System

**Color tokens** (Tailwind)

* Base neutral: slate/stone for surfaces. Accent: indigo/cyan for interactive.
* Profit/Loss: accessible pairs (e.g., **emerald** for profit, **rose** for loss) with iconography; never color‑only.

**Density & Type**

* Compact tables; 12–14px for dense rows; headings at 18–24px. Numeric monospace where helpful.

**Motion**

* Framer Motion micro‑interactions: pipeline stage progress, streaming message reveal; prefer 150–200ms ease‑out.

---

## 7) Components (React/Tailwind contracts)

> Names/props are illustrative to guide build; compose locally, no global stores required.

* `<BotRail bots: BotSummary[] onSelect(id) selectedId />`
* `<StatusBar botId startStop() env status sse={connected:boolean, lastEventTs} nextRunTs />`
* `<PipelineIndicator stage: "extraction"|"decision"|"trading"|"idle" durations {...} />`
* `<SSEBadge connected lastEventTs />`
* `<Countdown targetTs onRunNow onSnooze />`
* `<MetricsBar metrics={[{label, value, delta}]} timeframe />`
* `<EquityChart data timeframe />` • `<PLChart data timeframe />` • `<DDChart data timeframe />`
* `<PositionsTable rows onClose(row) onAdjust(row) />`
* `<DecisionFeed items onOpenDetail(itemId) />`
* `<ConfigTabs sections=[Strategy, Data, Logic, Risk, LLM, Trading, Advanced] />`
* `<DataSourcesMatrix sources weights timeframes onChange />`
* `<PromptEditor system user tokens onTest />`
* `<RiskControls {...} preview />`
* `<LLMProviderSelect provider model costEstimator onTest />`
* `<ExchangeConnect exchange account onTest />`
* `<DiffDrawer draft published onRevert onPublish />`
* `<ConfirmLiveModal summary onConfirm />`
* `<Toast/>` and `<InlineValidationSummary/>`

---

## 8) Interaction Patterns

* **Optimistic actions** with rollback on SSE confirmation.
* **Sticky Save/Publish bar** shows draft status, errors, and CTA.
* **Toasts** for success/fail; **inline** for field‑level errors.
* **Keyboard**: ⌘/Ctrl+K (bot switch), `g m` (Monitor), `g c` (Configure), `.` (Run now), `/` (search bots).
* **Tooltips** with concise definitions for metrics.

---

## 9) Edge Cases & Guardrails

* **SSE drop:** show Retrying with exponential backoff; disable Run now; keep stale data labeled.
* **Missing API keys:** banner with link to LLM/Trading config.
* **Live mode risk:** require typed confirm if risk limits are weak; show recent drawdown snapshot.
* **Partial pipeline failure:** isolate failing stage; allow retry of that stage only.

---

## 10) Responsive Strategy

* **Mobile:** bottom tab bar (Bots ▸ Monitor ▸ Configure ▸ Alerts). Status Bar collapses to a single line.
* **Table → Cards** transformation for Positions; swipe actions for Close/Adjust.

---

## 11) Implementation Notes (to accelerate build)

* **State:** `selectedConfigId` from URL; local component state per section; unmount cleans SSE.
* **SSE:** one EventSource per active bot; heartbeat event every \~10s sets freshness badge.
* **Formatting:** central number/time utilities; compact & locale‑aware.
* **Accessibility:** focus order, ARIA for live regions (SSE badges, toasts), min 4.5:1 contrast.

---

## 12) What ships first (sequenced)

1. Frame: Left Rail + Monitor/Configure tabs + Status Bar with heartbeat & Start/Stop.
2. Monitor Overview: Metrics, Charts, Positions, Decision Feed, Countdown.
3. Configure: Strategy, Risk, Trading; then Data Sources, Decision Logic, LLM; finally Advanced/JSON + Diff.
4. Versioning & Publish flow; Test‑run.
5. Compare mode (optional v2).

---

## 13) Success Criteria

* Switch between 5 bots in <300ms perceived (optimistic) with accurate SSE freshness.
* Configure → Publish → Test‑run in <3 clicks, with zero confusion about Paper vs Live.
* Users can answer “what is the bot doing and why?” within 5s on Monitor.



Sev: "is this the most elegant design? clean, simple, elegant? intutive? 

Let's walk through the user journey. User lands on the landing page, they hit launch app, they get taken to the create acc page, they create an acc and login, they land in this page, we create a new default settings ggbot for the user right away so they start with one ggbot, that's inactive, btw the start/stop button, I think we should rephrase to activate/deactivate, that's more what it actually is. So the user lands in, they get a very basic ggbot with 'factory settings'. They need to know where to go, what to do intuitively. There are two types of ggbots, autonomous_trading and signal_validation. The default is autonomous trading, which has an 'analysis frequency' basically how often the bot completes the pipeline, we'll set the default to 5 minutes. So the user can 'activate' their default ggbot, which will start the timer to the next run. But we should also have a way for them to get immediate satisfaction, by clicking a manual trigger button, to force a ggbot execution run immediately, overriding the schedule. Then they see things happening, the status that gets pulled in for the ggbot can be used to display cycling messages, we want them to feel like this bot is really alive, going through the 3 processes, extraction, decision and (if the decision is to enter a trade, which for the default bot always will be) trading. Then they need to see the decision, the AI will have 'reasoning' for it's decision, every time a ggbot executes it makes a decision, but it doesn't always make a trade, a lot of the time it will just 'wait', especially when it's monitoring an active trade. So the user needs to see these decisions, that's the first thing they'll be able to really see value in is how the AI used data and a strategy to reason about the market. Then, since the default ggbot has a very simple strategy (if RSI is below 50 enter long, if above 50 enter short) it will always enter a trade on the first go, whether the user manually tiriggers that or waits the 5 minutes for it to run scheduled. so then we need to see the trade, we want a notification the trade was entered, and we always want to be able to see active trades to see how they're doing. The are active trades should be in is maybe 1-10 trades. For autonomous_trading mode it will always be max one trade for now, but for signal validation mode it might be many trades. Ok so that's the onboarding and immediate dopamine hit of seeing a ggbot work, but this will not be a successfuly ggbot, so the next thing a user needs to do is start configuring their ggbot, it needs to be intuitive for how they edit it. THere's 3 main things they can edit. 1) Extraction, aka Market Data, the data sources and data points that get fed to the decision LLM. 2) Decision - the trading strategy, we have uneditable prompt structuring that gives the LLM general instructions and provides current prices, and a 'market data' section that includes all the selected datapoints that a user configures in the extraction section, so all the user has to do is add their trading strategy. The default strategy is what I described, simply to enter a trade based on RSI being above or below 50. So they will see that in the default trading strategy. So they need to understand that this is what really makes all the difference, a ggbots success or failure is based on the data points you give it and the strategy you give it for how to interpret those data points, the decision LLM will always output an ACTION, REASONING, and CONFIDENCE. user can't change that output instruction section either. So the system prompt, general instructions, market data, and output instructions are all set for the user and uneditable, then they just add the strategy section to customize behavior. So this needs to be prominent and clear. Finally the trading settings are like position sizing, exchange connections, and telegram publishing settings. I think the biggest challenge will be how to display market data options. Right now our system is extremely basic, we only have 20 data points, which are techincal indicators inside the techincal analysis data source. but this will grow fast. We'll be quickly adding 5-10 data sources, and idk what the data points for each of those will look like yet, but they could have all sorts of options. So how to not overwelm, make those selections feel easy. idk how exactly.... oh and then comes performance, we really just need to track account balance, and a chart with change over time, profit and loss, trade statstics and such.. but pretty minimal. Ultimately people just care about whether their ggbot is making money or not. OH and right now the MVP we're laucnhing will be paper trading ONLY. So we should have an exchange connection settings area set up, with a place to add API keys and such, but it will be turned off/hidden/unclickable or something for now. All ggbots get a paper trading account with $10k immediately. so showing the ggbot's balance is also a great thing to show. 

Ultimately I want this to be clean, elegant, minalist, taking what would normally be a very complex thing of building and deploying an AI trading agent, and just making it feel effortless."

ChatGPT said:"
Thought for 25s

Short answer: yes—this can be clean and elegant, but only if we ruthlessly script the first-run journey and keep a single, obvious CTA on every screen. You’re right to rename Start/Stop → Activate/Deactivate. Below is the opinionated, end-to-end flow with precise UI states and copy so it feels effortless and alive.

First-Run Journey (opinionated, minimal, dopamine-forward)
0) Landing → Create account → Launch app

Keep this boring and fast. One CTA: Launch Forge.

1) First time in Forge (default bot auto-created)

Surface shown: Monitor mode, with a single Activation Bar (sticky) and three empty blocks below.

Activation Bar (hero, single primary CTA)

Left: Bot name (Default ggbot) • Type chip: Autonomous trading • Env chip: Paper ($10,000) • Next run: every 5m

Center: Activate (primary) • Run once (secondary) • Countdown (disabled until active)

Right: SSE badge: ● Connected • “Last update: just now”

Below (empty states that guide action):

Decision Feed (empty) — “No decisions yet. Press Run once to see your bot think.”

Active Trade (empty) — “No trade yet. Your default strategy will open a position on first decision.”

Performance (empty) — sparkline placeholder + “Starts tracking after your first trade.”

Key: You’re giving the user exactly two choices, both safe in paper: Activate (sets the 5-minute rhythm) or Run once (instant gratification).

2) Immediate satisfaction (manual trigger)

User hits Run once (or Activate → countdown → Run). The Pipeline Ticker animates in the Activation Bar:

▸ Extracting market data… (2–5s)

▸ Reasoning (LLM)…

▸ Trading decision…

✓ Cycle complete at 10:42:13

A toast pops: Decision made — “Action: ENTER LONG BTC • Confidence 78”.
Secondary toast (if a trade placed): Trade opened — “BTCUSD, size 0.10, avg price 62,345.” (link: View trade)

What updates on page, above the fold:

Decision Feed: newest card slides in at top:

“Cycle #1 • Confidence 78 • 10:42:13”

Summary: “RSI(1h)=36 rising; basic strategy: below 50 → long.”

Pill buttons: Why? (drawer) • Inputs used (badge “2/20”)

Active Trade: one row table appears with live P&L and age.

Performance: balance card becomes $10,000 → $10,000 (unrealized P&L separate). Chart draws first point.

Copy is crisp, deterministic, and celebratory but not gimmicky. Micro-animation comes from the ticker and card slide-ins only.

3) Make the bot feel “alive”

Keep the Pipeline Ticker visible always. When idle, it shows “Idle • next in 04:59” with a ticking countdown.

Each stage lights up (Extraction → Decision → Trading). If the action is WAIT, the Decision Feed still logs it with a gray “No trade” badge—this is important to show thinking even without execution.

4) Clarify the two bot types (without cognitive cost)

In the Activation Bar, the Type chip is clickable only in Configure. Default shows Autonomous trading.

If user later switches to Signal validation, the Active Trade block morphs into Signal Stream (potentially many rows). Same layout, different label—no new concept load on day one.

5) Nudge into configuration (after first run)

Above the Decision Feed, show a subtle callout card:

“Want better results? Your bot uses a simple RSI rule. Edit strategy (2–3 mins).”

CTA routes to Configure ▸ Decision with a guided highlight.

Configure (crystal-clear, progressive)
A) Structure and copy (no ambiguity)

Top sticky Publish Bar:

“Draft saved • 0 errors” — Actions: Validate, Test-run, Publish.

Important: Activate/Deactivate stays in Monitor only. Configure is for thinking, Monitor for doing.

Tabs (left to right, increasing complexity):

Decision (first)

Market Data

Risk

Trading

LLM

Advanced / JSON

Opinion: Put Decision first. It’s the “aha.” Users believe strategy > everything. You already lock system prompt, general instructions, market data container, and output schema. Great—make that visually explicit.

Decision (first-run content)

Read-only blocks (faint border, lock icon):

System instructions (collapsed by default)

Market data (auto-injected) — “Based on your selections in Market Data.”

Output format: ACTION / REASONING / CONFIDENCE

Editable block (prominent): Your Strategy

Pre-filled with: “If RSI < 50 then LONG, else SHORT.”

Microcopy: “Only edit the strategy. Everything else is handled for you.”

Actions: Test decision (runs on latest snapshot → shows a one-off decision card right here)

Market Data (scales without overwhelm)

Default today: 1 source (Technical Analysis) with ~20 indicators.

Design for growth now:

Facet panel (left): Categories (Technical, Signals, Sentiment, News, On-chain, Fundamental).

Main list (right): Search + small cards per datapoint:

Name (RSI), short desc, toggle, timeframe chips (5m, 1h, 1d), optional weight.

“Add to strategy” simply means “include in inputs.” Weight shows influence hints later in Decision details.

Presets row at the top: “Momentum basics”, “Mean reversion”, “Trend following” — clicking toggles a curated set. Users can tweak after.

Selection summary drawer (right): “You’ve selected 7 datapoints” with a Validate inputs button (warns about cost/latency if/when that matters).

Don’t over-rank yet: keep weights optional; default equal. Avoid sliders everywhere—only show a weight control on hover or when toggled on.

Risk

Minimal, opinionated defaults: fixed % sizing = 2%, SL 1.0%, TP 1.5%, max concurrent = 1.

Show a tiny “risk preview” sparkline (simulated DD range) under the controls.

Trading

Read-only state for MVP (Paper only):

“Paper account: $10,000 (auto-provisioned)”

Exchange connections (disabled): card with lock and “Live trading coming soon.”

Telegram publishing (optional): allow enabling now if you want early delight; else show as “Coming soon”.

LLM

Provider select, Test connection button.

Keep cost/latency hints subtle; don’t drown first-run.

Advanced / JSON

Monaco editor with schema validation and Revert.

B) Publish flow (fast and safe)

Validate (1s) → Test-run (optional) → Publish.

On publish, a compact summary modal: “You changed 1) Strategy, 2) Added 3 datapoints. Ready?”

After publish, toast: “Published v4. Switch to Monitor to see it in action.” Add Run once inline button in the toast for the dopamine loop.

Performance (minimal, money-first)

Top of Monitor (second row, always visible):

Balance (Paper), Unrealized P&L, Realized P&L (Today), Win rate (30d).

Below: Equity curve and Daily P&L only. Nothing else until you have history.

Micro-interactions that sell the magic

Pipeline Ticker with stage badges and a subtle progress shimmer.

Decision cards slide in; confidence chip animates 0→value.

Trade toast with a gentle count-up of P&L for 2 seconds (then settles).

All timestamps show “2m ago” with absolute on hover.

Copy & labels (lock them in)

Primary CTA in Monitor: Activate (then becomes Deactivate when running) • Secondary: Run once.

Decision card: “Why?” (opens drawer with reasoning + inputs snapshot).

Type: Autonomous trading | Signal validation (read-only chip in Monitor; editable in Configure).

Environment: Paper (solid, friendly) — Live is hidden/disabled until future.

Why this is elegant

One primary choice per screen → Activate in Monitor, Publish in Configure.

Immediate payoff → Run once + ticker + decision card + trade toast.

Complexity kept behind glass → locked system prompt, output schema, and connection cards make it feel safe.

Scalable data UI → facets, search, presets, optional weights; no overwhelming matrix.

If you want, I’ll drop a “First-Run Overlay” and the Activation Bar into real React/Tailwind components next, exactly as specified (including the ticker, Run once, chips, and empty states)."







# Forge MVP — Implementation Plan & Acceptance Criteria (v1)

Opinionated build plan for shipping the demo’d experience to production (paper-only).

---

## 1) Scope (MVP)

* **Environment**: Paper only. Auto-provision \$10,000.
* **Bots**: Auto-create one default bot on first login (type: `autonomous_trading`, inactive). Support `signal_validation` selection in Configure.
* **Monitor**: Activation Bar (Activate/Deactivate, Run once, countdown), Pipeline Ticker (Extraction → Decision → Trading → Idle), Decision Feed, Active Trades (max 1 in autonomous; many in signal validation), KPIs (Balance, Unrealized, Realized Today, Win rate), Health panel.
* **Configure**: Tabs — Decision (first), Market Data, Risk (minimal), Trading (read-only; live disabled), LLM (basic), Advanced/JSON (schema-validated). Draft→Publish flow: Validate, Test-run (optional), Publish.
* **Charts**: Placeholder spark/area initially; wire real data later.
* **SSE**: Single EventSource per selected bot; heartbeat; reconnect; staleness badge.

---

## 2) Routes & URL Model

* `/forge?bot=<configId>&mode=monitor|configure&view=overview`
* Persist last tab per bot in URL or localStorage.

---

## 3) Component Inventory (contracts)

* **ActivationBar**: `{ botName, type, env, balance, activated, countdown, onToggle, onRunOnce }`
* **PipelineTicker**: `{ stage: 'idle'|'extraction'|'decision'|'trading' }`
* **MetricsBar**: `{ unrealized, realizedToday, winRate, statusText }`
* **PositionsTable**: `{ rows: TradeRow[], onClose(row) }`
* **DecisionFeed**: `{ items: DecisionItem[], onOpenDetail(id) }`
* **DecisionCard**: `{ item: DecisionItem }`
* **HealthPanel**: `{ sseConnected, latency, env }`
* **ConfigTabs**: `{ active, onChange }`
* **DecisionEditor**: `{ strategy, onChange, lockedSectionsMeta }`
* **MarketDataSelector**: `{ categories, points, selected, onToggle, onWeightChange }`
* **PublishBar**: `{ draftStatus, errorsCount, onValidate, onTestRun, onPublish }`
* **BotRail**: `{ bots: BotSummary[], selectedId, onSelect, onNew }`
* **Toast**: `{ type, title, body }`

---

## 4) Data Models (TS)

```ts
export type BotType = 'autonomous_trading' | 'signal_validation';
export type Stage = 'idle' | 'extraction' | 'decision' | 'trading';

export interface BotSummary { id: string; name: string; type: BotType; env: 'paper'; pnl24h: number; active: boolean; }
export interface DecisionItem { id: string; time: string; confidence: number; summary: string; action: 'ENTER LONG'|'ENTER SHORT'|'EXIT'|'WAIT'; symbol: string; inputsUsed: string[]; details: string; }
export interface TradeRow { id: string; symbol: string; side: 'LONG'|'SHORT'; size: number; entry: number; mark: number; sl?: number; tp?: number; openedAt: string; }
```

---

## 5) SSE Event Schema (JSON)

* `heartbeat`: `{ ts }`
* `stage_update`: `{ stage: Stage, ts }`
* `decision`: `{ id, time, confidence, summary, action, symbol, inputsUsed, details }`
* `trade_opened`: `{ id, symbol, side, size, entry, sl?, tp?, openedAt }`
* `mark_price`: `{ tradeId, mark }` (per second throttled)
* `trade_closed`: `{ id, mark, pnl }`
* `schedule`: `{ nextRunTs }`
* `error`: `{ code, message, stage }`

**Reconnect/backoff**: 1s → 2s → 5s → 10s (cap); show “Reconnecting…” badge after 2s.

---

## 6) Actions & Copy (lock this)

* Monitor primary: **Activate** / **Deactivate** (secondary: **Run once**).
* Decision card: **Why?** opens detail drawer (Reasoning + Inputs snapshot + Output schema note).
* Toasts:

  * **Decision made** — `Action: <ACTION> • Confidence <N>`
  * **Trade opened** — `<SYMBOL>, size <X>, avg <PRICE>`
  * **Trade closed** — `P&L <+$N / -$N>`
* Configure primary: **Publish** (with **Validate**, **Test-run** apart). Copy on Decision tab: “Only edit **Your Strategy**. System prompt, market data injection, and output schema are fixed.”

---

## 7) Empty/Loading/Error States

* **No decisions**: “Click **Run once** to see your bot think.”
* **No trades**: “No active trades. The default strategy will open a position on first decision.”
* **SSE offline**: banner and badge; disable Run once if backend unreachable; keep stale labels.
* **Configure errors**: show inline per field + summary count in PublishBar.

---

## 8) Acceptance Criteria (Monitor)

* [ ] Activate toggles state immediately; countdown appears (5m real, 15s demo).
* [ ] **Run once** executes full pipeline: Extraction → Decision → Trading → Idle; stage chips animate.
* [ ] Decision Feed shows newest first with time, confidence, summary, action badge, inputs list, Why? drawer.
* [ ] Autonomous: max 1 active trade; additional signals either WAIT or replace with close+open sequence.
* [ ] Signal validation: allow 1–10 concurrent trades.
* [ ] KPIs update: Unrealized from mark ticks; Realized increments on close; Balance = \$10,000 + net P\&L.
* [ ] SSE reconnect shows “Reconnecting…” within 2s and recovers without hard refresh.

## 9) Acceptance Criteria (Configure)

* [ ] Decision tab first; locked sections visually distinct (icon + muted).
* [ ] Strategy editor saves draft on change; Test-run produces inline decision preview.
* [ ] Market Data scales: facet list (left), searchable cards (right), toggle + timeframe chips; selection summary.
* [ ] Publish disabled if errors > 0; Validate populates summary; Publish shows summary modal then success toast.
* [ ] Trading tab shows Paper account and disabled live connections.

---

## 10) Design Tokens (Tailwind)

* Surface: `bg-slate-950 / 900`, Border: `border-slate-800`, Text: `slate-100/300/400/500`.
* Accent: cyan for active/process; emerald for profit; rose for loss; amber for warnings.
* Radius: `rounded-2xl`; Shadow subtle; Motion: 150–200ms ease-out.

---

## 11) Analytics & Audit (nice-to-have)

* Events: `activate_click`, `run_once_click`, `decision_why_open`, `trade_close_click`, `publish_click`.
* Audit log (server): decisions, trades, config versions.

---

## 12) Ticket Breakdown (suggested)

1. Frame + BotRail + URL state
2. ActivationBar + PipelineTicker + SSE wiring
3. DecisionFeed + DecisionCard (+drawer)
4. PositionsTable + close action
5. KPIs + placeholders for charts
6. Configure: Decision (locked + editor + test-run)
7. Configure: Market Data (searchable cards)
8. Configure: PublishBar (validate/test/publish flow)
9. Trading (paper-only) + LLM basic + Advanced/JSON
10. Error/empty states + reconnect logic

---

## 13) QA Scenarios

* Activate → wait countdown → auto-run triggers correctly.
* Rapid Run once clicks are debounced (single in-flight run).
* SSE drop mid-stage shows partial progress then resumes.
* Switching bot types updates Monitor (max trades vs many) without reload.
* Large decisions list remains performant (virtualized if needed).

---

**Definition of Done**: All acceptance criteria pass; onboarding from first login to first trade takes ≤ 60 seconds with zero confusion about Paper vs Live; a user can explain “what the bot is doing and why” within 5 seconds on Monitor.

"
  2. UI Components (❌ Over-complex)
  - Left rail with multiple bots - Your current Forge is single-bot focused
  - Command palette (⌘K) - Nice-to-have but not MVP essential
  - "Compare mode" - Definitely not MVP
" - actually this is like the bot selector, this this rail would be like how you slect which bot you're on which would effect everything else... it did have the perforamnce of each bot showing which might not be possible, but actually I did like that a lot because being able to see how all your bots are doing (very basic percentage profit/loss up or down) at a glance is really ncie, but also might be out of scope for us right now. 

1) i don't think we need to add SSE staus in the header, but we probably do wnat a profile ? rn there's no user profile component in our plans, we probably want that for logout and basic settings, email and password changes, subscription management, stuff like that, and the little profile icon be where that stuff lives, inside the header.
2) can just remove healthpanel.tsx
3) publisher bar - i think the test run and validate options here are unecessary, it's simple save changes or don't, and it shows changes not saved, no saving drafts, if you don't save the settings and you refresh the page they won't save. publish feels wierd word to use here, how about SaveConfig.tsx instead. 