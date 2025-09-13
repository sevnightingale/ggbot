import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Square,
  Zap,
  Activity,
  Clock,
  Server,
  ChevronRight,
  CheckCircle2,
  Circle,
  CircleDot,
  TrendingUp,
  TrendingDown,
  PauseCircle,
  Cog,
  Bot,
  Layers,
  BarChart3,
} from "lucide-react";

// Tailwind is available. This is a self-contained interactive mock for Forge.
// Goals:
// - Show Monitor vs Configure tabs (minimal Configure)
// - Activation Bar with Activate/Deactivate + Run once
// - Pipeline ticker (Extraction → Decision → Trading → Idle)
// - Decision Feed
// - Active Trade (max 1 for autonomous_trading; many for signal_validation)
// - Minimal performance cards
// - Paper-only, $10k starting balance

// --- Types ---
type BotType = "autonomous_trading" | "signal_validation";
type Stage = "idle" | "extraction" | "decision" | "trading";

interface DecisionItem {
  id: string;
  time: string;
  confidence: number; // 0-100
  summary: string;
  action: "ENTER LONG" | "ENTER SHORT" | "EXIT" | "WAIT";
  symbol: string;
  inputsUsed: string[];
  details?: string;
}

interface TradeRow {
  id: string;
  symbol: string;
  side: "LONG" | "SHORT";
  size: number; // lots/shares
  entry: number; // price
  mark: number; // current price
  sl?: number;
  tp?: number;
  openedAt: string;
}

// --- Helpers ---
function fmt(n: number, opts: Intl.NumberFormatOptions = {}) {
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
    ...opts,
  }).format(n);
}

function nowTime() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour12: false });
}

function randBetween(min: number, max: number) {
  return Math.random() * (max - min) + min;
}

function id(prefix = "id") {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}`;
}

// Demo constants
const DEMO_COUNTDOWN_SECONDS = 15; // visual demo pace (instead of 5m)
const START_BALANCE = 10000;

// --- Main Component ---
export default function ForgePreview() {
  // Core state
  const [activated, setActivated] = useState(false);
  const [stage, setStage] = useState<Stage>("idle");
  const [countdown, setCountdown] = useState<number>(DEMO_COUNTDOWN_SECONDS);
  const [sseConnected, setSseConnected] = useState(true);
  const [botType, setBotType] = useState<BotType>("autonomous_trading");
  const [tab, setTab] = useState<"monitor" | "configure">("monitor");

  // Data
  const [decisions, setDecisions] = useState<DecisionItem[]>([]);
  const [trades, setTrades] = useState<TradeRow[]>([]);
  const [balance, setBalance] = useState<number>(START_BALANCE);
  const [realizedToday, setRealizedToday] = useState<number>(0);

  // Derived
  const unrealized = useMemo(() => {
    return trades.reduce((acc, t) => {
      const pnl = t.side === "LONG" ? (t.mark - t.entry) * t.size : (t.entry - t.mark) * t.size;
      return acc + pnl;
    }, 0);
  }, [trades]);

  const winRate = useMemo(() => {
    // Demo: infer from decisions with EXIT tagged in details
    const exits = decisions.filter((d) => d.action === "EXIT");
    if (!exits.length) return 0;
    const wins = exits.filter((d) => d.details?.includes("WIN")).length;
    return Math.round((wins / exits.length) * 100);
  }, [decisions]);

  // Countdown timer (when activated)
  useEffect(() => {
    if (!activated) return;
    setCountdown((c) => (c <= 0 ? DEMO_COUNTDOWN_SECONDS : c));
    const iv = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          // Fire scheduled run
          runCycle();
          return DEMO_COUNTDOWN_SECONDS;
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(iv);
  }, [activated]);

  // Mark price ticker for live trades
  useEffect(() => {
    if (!trades.length) return;
    const iv = setInterval(() => {
      setTrades((rows) =>
        rows.map((t) => ({
          ...t,
          mark: +(t.mark * (1 + randBetween(-0.001, 0.001))).toFixed(2),
        }))
      );
    }, 1000);
    return () => clearInterval(iv);
  }, [trades.length]);

  // Simulate occasional SSE reconnect blip
  useEffect(() => {
    const iv = setInterval(() => {
      if (Math.random() < 0.06) {
        setSseConnected(false);
        setTimeout(() => setSseConnected(true), 1500);
      }
    }, 8000);
    return () => clearInterval(iv);
  }, []);

  // First run hint: auto-select Monitor tab and idle stage
  useEffect(() => {
    setTab("monitor");
    setStage("idle");
  }, []);

  // Cycle runner
  const runCycle = () => {
    // Pipeline animation
    setStage("extraction");
    setTimeout(() => setStage("decision"), 1100);

    setTimeout(() => {
      // Decide action
      const madeTradeAlready = trades.length > 0 && botType === "autonomous_trading";
      let action: DecisionItem["action"] = "WAIT";
      let symbol = "BTCUSD";
      let summary = "";
      let side: TradeRow["side"] = "LONG";
      const conf = Math.round(randBetween(65, 92));

      if (botType === "autonomous_trading") {
        if (!madeTradeAlready) {
          // First run: always trade per product brief
          action = Math.random() < 0.5 ? "ENTER LONG" : "ENTER SHORT";
        } else {
          // When a trade exists, often wait
          if (Math.random() < 0.7) action = "WAIT"; else action = Math.random() < 0.5 ? "ENTER LONG" : "ENTER SHORT";
        }
      } else {
        // signal_validation can fan out
        action = Math.random() < 0.6 ? "ENTER LONG" : Math.random() < 0.5 ? "ENTER SHORT" : "WAIT";
      }

      side = action === "ENTER SHORT" ? "SHORT" : "LONG";
      const rsi = Math.round(randBetween(30, 70));
      summary = action === "WAIT"
        ? `Hold position; RSI(1h)=${rsi} neutral; monitoring.`
        : `${action.includes("LONG") ? "RSI<50 → long bias" : "RSI>50 → short bias"}.`;

      const decision: DecisionItem = {
        id: id("dec"),
        time: nowTime(),
        confidence: conf,
        summary,
        action,
        symbol,
        inputsUsed: ["RSI(1h)", "PriceMomentum"],
        details: `Reasoning: rules-based with RSI=${rsi}.`,
      };

      // Possibly open trades
      let newTrades: TradeRow[] = [];
      if (action !== "WAIT") {
        if (botType === "autonomous_trading") {
          if (trades.length === 0) {
            newTrades.push(makeTrade(symbol, side));
          } else {
            // optional: replace existing trade if signal flips
            if (Math.random() < 0.2) {
              // close the old one, realize P&L
              closeAllTrades(true);
              newTrades.push(makeTrade(symbol, side));
            }
          }
        } else {
          const count = Math.ceil(randBetween(1, 3));
          newTrades = Array.from({ length: count }).map(() => makeTrade(symbol, side));
        }
      }

      // Commit data
      setDecisions((d) => [decision, ...d].slice(0, 20));
      if (newTrades.length) setTrades((rows) => [...rows, ...newTrades].slice(-10));

      setStage("trading");
      setTimeout(() => setStage("idle"), 900);
    }, 2200);
  };

  function makeTrade(symbol: string, side: TradeRow["side"]): TradeRow {
    const entry = +(randBetween(60000, 65000)).toFixed(2);
    return {
      id: id("tr"),
      symbol,
      side,
      size: +(randBetween(0.05, 0.2)).toFixed(2),
      entry,
      mark: entry,
      sl: +(side === "LONG" ? entry * 0.99 : entry * 1.01).toFixed(2),
      tp: +(side === "LONG" ? entry * 1.015 : entry * 0.985).toFixed(2),
      openedAt: nowTime(),
    };
  }

  function closeTrade(row: TradeRow) {
    const pnl = row.side === "LONG" ? (row.mark - row.entry) * row.size : (row.entry - row.mark) * row.size;
    setTrades((rows) => rows.filter((t) => t.id !== row.id));
    setRealizedToday((r) => r + pnl);
    setBalance((b) => b + pnl);
    setDecisions((d) => [
      {
        id: id("dec"),
        time: nowTime(),
        confidence: 100,
        summary: `Closed ${row.symbol} ${row.side} @ ${fmt(row.mark)} (entry ${fmt(row.entry)})`,
        action: "EXIT",
        symbol: row.symbol,
        inputsUsed: ["Risk/TP/SL"],
        details: `Result: ${pnl >= 0 ? "WIN" : "LOSS"} • P&L ${fmt(pnl)}`,
      },
      ...d,
    ]);
  }

  function closeAllTrades(openReplacement = false) {
    trades.forEach((t) => closeTrade(t));
    if (!openReplacement) setTrades([]);
  }

  const stageOrder: Stage[] = ["extraction", "decision", "trading", "idle"];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-cyan-400" />
            <span className="font-semibold tracking-wide">ggbots • Forge</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Server className="h-4 w-4" />
            <span className={sseConnected ? "text-emerald-400" : "text-amber-400"}>
              {sseConnected ? "SSE Connected" : "Reconnecting…"}
            </span>
          </div>
        </div>
      </header>

      {/* Body */}
      <div className="mx-auto grid max-w-7xl grid-cols-12 gap-4 px-4 py-4">
        {/* Left rail (bots) */}
        <aside className="col-span-12 hidden md:col-span-3 md:block">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-3">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2 font-medium">
                <Layers className="h-4 w-4" /> Bots
              </div>
              <button className="rounded-xl border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800">
                + New
              </button>
            </div>
            <div className="space-y-2">
              <BotRow active name="Default ggbot" pnl={realizedToday + unrealized} env="Paper" />
              <BotRow name="Momentum scout" pnl={0} env="Paper" />
              <BotRow name="Signal lab" pnl={0} env="Paper" />
            </div>
          </div>
        </aside>

        {/* Main column */}
        <main className="col-span-12 md:col-span-9">
          {/* Activation Bar */}
          <div className="sticky top-[52px] z-30 rounded-2xl border border-slate-800 bg-slate-900/70 p-4 backdrop-blur">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-400">Bot:</span>
                <span className="font-medium">Default ggbot</span>
                <span className="rounded-full border border-slate-700 px-2 py-0.5 text-xs text-slate-300">
                  {botType === "autonomous_trading" ? "Autonomous trading" : "Signal validation"}
                </span>
                <span className="rounded-full bg-cyan-500/10 px-2 py-0.5 text-xs text-cyan-300 border border-cyan-700/30">
                  Paper • ${fmt(balance)}
                </span>
                <span className="text-xs text-slate-400">Every 5m</span>
              </div>

              <div className="flex items-center gap-2 ml-auto">
                <PipelineTicker stage={stage} />
                <div className="mx-2 h-5 w-px bg-slate-700" />
                <button
                  onClick={() => (activated ? setActivated(false) : setActivated(true))}
                  className={`inline-flex items-center gap-2 rounded-xl px-3 py-1.5 text-sm font-medium shadow-sm ring-1 ring-inset transition
                    ${activated ? "bg-rose-600/90 hover:bg-rose-600 ring-rose-500" : "bg-emerald-600/90 hover:bg-emerald-600 ring-emerald-500"}`}
                >
                  {activated ? (
                    <>
                      <PauseCircle className="h-4 w-4" /> Deactivate
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" /> Activate
                    </>
                  )}
                </button>
                <button
                  onClick={runCycle}
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-3 py-1.5 text-sm hover:bg-slate-800"
                >
                  <Zap className="h-4 w-4" /> Run once
                </button>
                <div className="ml-2 flex items-center gap-1 text-xs text-slate-400">
                  <Clock className="h-4 w-4" /> Next in {countdown}s
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="mt-4 flex items-center gap-2">
            <button
              onClick={() => setTab("monitor")}
              className={`rounded-xl px-3 py-1.5 text-sm ${tab === "monitor" ? "bg-slate-800 text-slate-100" : "text-slate-400 hover:bg-slate-900"}`}
            >
              Monitor
            </button>
            <button
              onClick={() => setTab("configure")}
              className={`rounded-xl px-3 py-1.5 text-sm ${tab === "configure" ? "bg-slate-800 text-slate-100" : "text-slate-400 hover:bg-slate-900"}`}
            >
              Configure
            </button>
          </div>

          {tab === "monitor" ? (
            <MonitorView
              trades={trades}
              decisions={decisions}
              unrealized={unrealized}
              realizedToday={realizedToday}
              winRate={winRate}
              closeTrade={closeTrade}
              activated={activated}
              countdown={countdown}
              sseConnected={sseConnected}
            />
          ) : (
            <ConfigureView botType={botType} setBotType={setBotType} />
          )}
        </main>
      </div>
    </div>
  );
}

function BotRow({ name, pnl, env = "Paper", active = false }: { name: string; pnl: number; env?: string; active?: boolean }) {
  const positive = pnl >= 0;
  return (
    <div className={`flex items-center justify-between rounded-xl px-3 py-2 ${active ? "bg-slate-800/60" : "hover:bg-slate-900"}`}>
      <div className="flex items-center gap-2">
        <CircleDot className={`h-4 w-4 ${active ? "text-emerald-400" : "text-slate-500"}`} />
        <div className="text-sm">{name}</div>
      </div>
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <span className="rounded-full border border-slate-700 px-2 py-0.5">{env}</span>
        <span className={positive ? "text-emerald-400" : "text-rose-400"}>
          {positive ? <TrendingUp className="mr-1 inline h-3 w-3" /> : <TrendingDown className="mr-1 inline h-3 w-3" />} {fmt(pnl)}
        </span>
      </div>
    </div>
  );
}

function PipelineTicker({ stage }: { stage: Stage }) {
  const stages: { key: Stage; label: string }[] = [
    { key: "extraction", label: "Extraction" },
    { key: "decision", label: "Decision" },
    { key: "trading", label: "Trading" },
    { key: "idle", label: "Idle" },
  ];
  return (
    <div className="flex items-center gap-2 text-xs">
      {stages.map((s, i) => {
        const active = stage === s.key;
        return (
          <div className="flex items-center" key={s.key}>
            <div className={`flex items-center gap-1 rounded-full px-2 py-1 ${active ? "bg-slate-800" : "bg-slate-900 border border-slate-800"}`}>
              {active ? <Activity className="h-3.5 w-3.5 text-cyan-300" /> : <Circle className="h-3.5 w-3.5 text-slate-600" />}
              <span className={active ? "text-slate-100" : "text-slate-400"}>{s.label}</span>
            </div>
            {i < stages.length - 1 && <ChevronRight className="mx-1 h-3.5 w-3.5 text-slate-600" />}
          </div>
        );
      })}
    </div>
  );
}

function KPI({ label, value, delta }: { label: string; value: string; delta?: number }) {
  const pos = (delta ?? 0) >= 0;
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="mt-1 text-xl font-semibold tracking-tight">{value}</div>
      {delta !== undefined && (
        <div className={`mt-1 text-xs ${pos ? "text-emerald-400" : "text-rose-400"}`}>
          {pos ? <TrendingUp className="mr-1 inline h-3 w-3" /> : <TrendingDown className="mr-1 inline h-3 w-3" />} {fmt(Math.abs(delta))}
        </div>
      )}
    </div>
  );
}

function MonitorView({
  trades,
  decisions,
  unrealized,
  realizedToday,
  winRate,
  closeTrade,
  activated,
  countdown,
  sseConnected,
}: {
  trades: TradeRow[];
  decisions: DecisionItem[];
  unrealized: number;
  realizedToday: number;
  winRate: number;
  closeTrade: (row: TradeRow) => void;
  activated: boolean;
  countdown: number;
  sseConnected: boolean;
}) {
  return (
    <div className="mt-4 space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KPI label="Unrealized P&L" value={(unrealized >= 0 ? "+" : "-") + "$" + fmt(Math.abs(unrealized))} delta={unrealized} />
        <KPI label="Realized P&L (Today)" value={(realizedToday >= 0 ? "+" : "-") + "$" + fmt(Math.abs(realizedToday))} delta={realizedToday} />
        <KPI label="Win rate (30d)" value={`${winRate}%`} />
        <KPI label="Status" value={activated ? `Active • next in ${countdown}s` : "Inactive"} />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {/* Left: charts placeholder + positions */}
        <div className="md:col-span-2 space-y-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
            <div className="mb-2 flex items-center justify-between">
              <div className="text-sm text-slate-300">Equity / P&L / Drawdown (placeholder)</div>
              <div className="text-xs text-slate-500">1D • 7D • 30D • All</div>
            </div>
            <div className="h-28 w-full rounded-lg bg-slate-800/60" />
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/50">
            <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
              <div className="text-sm text-slate-300">Active trades</div>
              <div className="text-xs text-slate-500">{trades.length || 0}</div>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="text-left text-slate-400">
                  <tr className="border-b border-slate-800">
                    <th className="px-4 py-2">Symbol</th>
                    <th className="px-4 py-2">Side</th>
                    <th className="px-4 py-2">Size</th>
                    <th className="px-4 py-2">Entry</th>
                    <th className="px-4 py-2">Mark</th>
                    <th className="px-4 py-2">P&L</th>
                    <th className="px-4 py-2">SL / TP</th>
                    <th className="px-4 py-2">Age</th>
                    <th className="px-4 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.length === 0 ? (
                    <tr>
                      <td className="px-4 py-6 text-slate-500" colSpan={9}>
                        No active trades. Run once to see your bot act.
                      </td>
                    </tr>
                  ) : (
                    trades.map((t) => {
                      const pnl = t.side === "LONG" ? (t.mark - t.entry) * t.size : (t.entry - t.mark) * t.size;
                      const pos = pnl >= 0;
                      return (
                        <tr key={t.id} className="border-t border-slate-800">
                          <td className="px-4 py-2">{t.symbol}</td>
                          <td className="px-4 py-2">{t.side}</td>
                          <td className="px-4 py-2">{fmt(t.size, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                          <td className="px-4 py-2">${fmt(t.entry)}</td>
                          <td className="px-4 py-2">${fmt(t.mark)}</td>
                          <td className={`px-4 py-2 ${pos ? "text-emerald-400" : "text-rose-400"}`}>{pos ? "+" : "-"}${fmt(Math.abs(pnl))}</td>
                          <td className="px-4 py-2">${fmt(t.sl ?? 0)} / ${fmt(t.tp ?? 0)}</td>
                          <td className="px-4 py-2">{t.openedAt}</td>
                          <td className="px-4 py-2">
                            <button onClick={() => closeTrade(t)} className="rounded-lg border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800">
                              Close
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right: Decision feed + health */}
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50">
            <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
              <div className="text-sm text-slate-300">Decision feed</div>
              <div className="text-xs text-slate-500">{decisions.length || 0}</div>
            </div>
            <div className="divide-y divide-slate-800">
              <AnimatePresence initial={false}>
                {decisions.length === 0 ? (
                  <div className="p-4 text-sm text-slate-500">No decisions yet. Click <span className="font-medium text-slate-300">Run once</span> to see your bot think.</div>
                ) : (
                  decisions.map((d) => <DecisionCard key={d.id} d={d} />)
                )}
              </AnimatePresence>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm text-slate-300">
              <BarChart3 className="h-4 w-4" /> Health & schedule
            </div>
            <div className="space-y-1 text-xs text-slate-400">
              <div>
                SSE: <span className={sseConnected ? "text-emerald-400" : "text-amber-400"}>{sseConnected ? "Connected" : "Retrying"}</span>
              </div>
              <div>Exchange latency: 120–180ms</div>
              <div>Next run: countdown updates above</div>
              <div>Env: Paper (live connections disabled)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DecisionCard({ d }: { d: DecisionItem }) {
  const [open, setOpen] = useState(false);
  const trade = d.action !== "WAIT" && d.action !== "EXIT";
  const badgeClass = trade
    ? "bg-emerald-500/10 text-emerald-300 border border-emerald-700/30"
    : d.action === "EXIT"
    ? "bg-cyan-500/10 text-cyan-300 border border-cyan-700/30"
    : "bg-slate-700/30 text-slate-300 border border-slate-700/50";

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      className="px-4 py-3"
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs text-slate-500">{d.time} • Confidence {d.confidence}</div>
          <div className="mt-0.5 text-sm text-slate-200">{d.summary}</div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
            <span className={`rounded-full px-2 py-0.5 ${badgeClass}`}>{d.action}</span>
            <span className="rounded-full border border-slate-700 px-2 py-0.5 text-slate-300">{d.symbol}</span>
            <span className="text-slate-500">Inputs: {d.inputsUsed.join(", ")}</span>
          </div>
        </div>
        <button onClick={() => setOpen((v) => !v)} className="ml-2 rounded-lg border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800">
          {open ? "Hide" : "Why?"}
        </button>
      </div>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="mt-2 overflow-hidden rounded-xl border border-slate-800 bg-slate-900/70 p-3 text-xs text-slate-300">
            <div className="mb-1 font-medium text-slate-200">Reasoning</div>
            <p className="leading-relaxed">{d.details}</p>
            <div className="mt-2 text-slate-400">Output schema: ACTION • REASONING • CONFIDENCE</div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function ConfigureView({ botType, setBotType }: { botType: BotType; setBotType: (t: BotType) => void }) {
  const [strategy, setStrategy] = useState<string>(
    "If RSI < 50 then ENTER LONG. If RSI > 50 then ENTER SHORT."
  );
  const [selected, setSelected] = useState<string[]>(["RSI(1h)", "PriceMomentum"]);
  const [errors, setErrors] = useState<number>(0);

  return (
    <div className="mt-4 space-y-4">
      {/* Publish bar */}
      <div className="sticky top-[116px] z-20 flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-900/80 p-3 text-sm">
        <div className="text-slate-400">Draft saved • {errors} errors</div>
        <div className="flex items-center gap-2">
          <button className="rounded-xl border border-slate-700 px-3 py-1.5 hover:bg-slate-800">Validate</button>
          <button className="rounded-xl border border-slate-700 px-3 py-1.5 hover:bg-slate-800">Test-run</button>
          <button className="rounded-xl bg-slate-100 px-3 py-1.5 font-medium text-slate-900 hover:bg-white disabled:opacity-50" disabled={errors > 0}>
            Publish
          </button>
        </div>
      </div>

      {/* Decision first */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="text-sm font-medium">Decision</div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Cog className="h-4 w-4" /> Only edit <span className="text-slate-200">Your Strategy</span> — system prompt, market data injection, and output schema are fixed.
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs text-slate-400">System instructions (locked)</label>
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-3 text-xs text-slate-400">General instructions, price context, output schema (ACTION/REASONING/CONFIDENCE).</div>

            <label className="text-xs text-slate-400">Market data (auto-injected)</label>
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-3 text-xs text-slate-400">Selected datapoints appear in the prompt automatically.</div>
          </div>
          <div className="space-y-2">
            <label className="text-xs text-slate-300">Your Strategy (editable)</label>
            <textarea value={strategy} onChange={(e) => setStrategy(e.target.value)} rows={6} className="w-full rounded-xl border border-slate-700 bg-slate-900 p-3 text-sm outline-none focus:ring-2 focus:ring-cyan-600" />
          </div>
        </div>
      </section>

      {/* Market Data */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="text-sm font-medium">Market Data</div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="rounded-full border border-slate-700 px-2 py-0.5">Technical</span>
            <span className="rounded-full border border-slate-700 px-2 py-0.5">More sources soon</span>
          </div>
        </div>
        <div className="mb-3 flex items-center gap-2">
          <input placeholder="Search datapoints…" className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-cyan-600" />
        </div>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
          {["RSI(5m)", "RSI(1h)", "RSI(1d)", "MACD(1h)", "Bollinger(1h)", "Momentum(1h)", "ATR(1h)", "Stoch(1h)", "EMA(1h)"].map((k) => (
            <label key={k} className="flex cursor-pointer items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm hover:bg-slate-900">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selected.includes(k)}
                  onChange={(e) => setSelected((arr) => (e.target.checked ? [...arr, k] : arr.filter((x) => x !== k)))}
                  className="h-4 w-4 accent-cyan-600"
                />
                <span>{k}</span>
              </div>
              <span className="text-xs text-slate-500">TF preset</span>
            </label>
          ))}
        </div>
      </section>

      {/* Trading & Bot Type */}
      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
          <div className="mb-2 text-sm font-medium">Trading</div>
          <div className="space-y-2 text-sm text-slate-400">
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-3">Environment: <span className="text-slate-200">Paper ($10,000)</span></div>
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-3 opacity-60">
              Exchange connections (Live) — coming soon
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
          <div className="mb-2 text-sm font-medium">Bot Type</div>
          <div className="flex items-center gap-2 text-sm">
            <button onClick={() => setBotType("autonomous_trading")} className={`rounded-xl px-3 py-1.5 ${botType === "autonomous_trading" ? "bg-slate-800" : "border border-slate-700 hover:bg-slate-900"}`}>Autonomous trading</button>
            <button onClick={() => setBotType("signal_validation")} className={`rounded-xl px-3 py-1.5 ${botType === "signal_validation" ? "bg-slate-800" : "border border-slate-700 hover:bg-slate-900"}`}>Signal validation</button>
          </div>
          <div className="mt-2 text-xs text-slate-400">Autonomous: max 1 active trade (for now). Signal validation: may open many.</div>
        </div>
      </section>
    </div>
  );
}
