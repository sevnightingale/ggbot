"use client"

import React, {useEffect, useMemo, useRef, useState} from "react";
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

/**
 * Activity Timeline Viewer – Canvas v3 (Unicode-safe)
 * Integrated for ggbots - Public view for competition submission
 *
 * Features:
 * - Locked-lens scroll-through-time with zoom tiers (1h/4h/1d/1w/All)
 * - Activity icons with rail stacking to prevent overlap
 * - Click icons to see details in side panel
 * - Hover glow effects
 * - Pulsing "now" indicator with current state pill
 * - Smooth drag panning with inertia
 * - Wheel scroll through time, Shift+wheel to change zoom
 */

// --------- Types ---------

type Priority = 1 | 2;

type ActivityType =
  | "trade_entry_long"
  | "trade_entry_short"
  | "trade_win"
  | "trade_loss"
  | "strategy_updated"
  | "market_query"
  | "agent_wait"
  | "observation_recorded"
  | "analysis"
  | "reasoning"
  | "plan";

interface ActivityDefinition {
  type: ActivityType;
  priority: Priority;
  icon: string;
  color: string;
  label: string;
  description: string;
}

interface ActivityItem {
  id: string;
  timestamp: string; // ISO
  type: ActivityType;
  priority: Priority;
  data: Record<string, unknown>;
}

interface Position {
  symbol: string;
  side: 'long' | 'short';
  entry_price: number;
  current_price: number;
  size: number;
  unrealized_pnl: number;
  unrealized_pnl_percentage: number;
  opened_at: string;
}

interface BalancePoint { timestamp: string; balance: number; }

interface MockActivityLog {
  activities: ActivityItem[];
  balanceTimeseries: BalancePoint[];
  metadata: {
    botName: string; startingBalance: number; currentBalance: number; totalTrades: number; winRate: number; performance: number;
  };
}

// --------- Unicode-safe icon constants (emoji via escapes) ---------

const ICONS = {
  robot: "\uD83E\uDD16",             // 🤖 U+1F916
  greenCircle: "\uD83D\uDFE2",       // 🟢 U+1F7E2
  redCircle: "\uD83D\uDD34",         // 🔴 U+1F534
  chartUp: "\uD83D\uDCC8",           // 📈 U+1F4C8 (trending up)
  chartDown: "\uD83D\uDCC9",         // 📉 U+1F4C9 (trending down)
  thoughtBalloon: "\uD83D\uDCAD",     // 💭 U+1F4AD
  barChart: "\uD83D\uDCCA",          // 📊 U+1F4CA
  stopwatch: "\u23F1\uFE0F",          // ⏱️ U+23F1 U+FE0F
  memo: "\uD83D\uDCDD",               // 📝 U+1F4DD
  wrench: "\uD83D\uDD27",             // 🔧 U+1F527
  close: "\u2715",                    // ✕ U+2715
} as const;

// --------- Theme (ggbots colors) ---------

const COLORS = {
  bg: "#161618",        // charcoal-900
  grid: "rgba(255,255,255,0.06)",
  text: "#e3e5e6",      // bone-200
  positive: "#10b981",  // emerald-400
  negative: "#f43f5e",  // rose-400
  lineGlow: "rgba(16,185,129,0.28)",
  iconBg: "rgba(8,10,14,0.90)",
  iconRing: "rgba(255,255,255,0.34)",
  hoverGlow: "rgba(255,255,255,0.22)",
  pillBg: "rgba(255,255,255,0.08)",
  pillBorder: "rgba(255,255,255,0.18)",
};

const ACTIVITY_DEFS: Record<ActivityType, ActivityDefinition> = {
  trade_entry_long:  { type: "trade_entry_long",  priority: 1, icon: ICONS.greenCircle,   color: "#10b981", label: "Long Entry",    description: "Opened a long position." },
  trade_entry_short: { type: "trade_entry_short", priority: 1, icon: ICONS.redCircle,     color: "#f43f5e", label: "Short Entry",   description: "Opened a short position." },
  trade_win:         { type: "trade_win",         priority: 1, icon: ICONS.chartUp,       color: "#10b981", label: "Trade Win",     description: "Closed position with profit." },
  trade_loss:        { type: "trade_loss",        priority: 1, icon: ICONS.chartDown,     color: "#f43f5e", label: "Trade Loss",    description: "Closed position with loss." },
  strategy_updated:  { type: "strategy_updated",  priority: 1, icon: ICONS.wrench,        color: "#a855f7", label: "Strategy Update", description: "Strategy modified." },
  market_query:      { type: "market_query",      priority: 2, icon: ICONS.barChart,      color: "#3b82f6", label: "Data Query",    description: "Fetched market data." },
  agent_wait:        { type: "agent_wait",        priority: 2, icon: ICONS.stopwatch,     color: "#64748b", label: "Waiting",       description: "Agent paused." },
  observation_recorded: { type: "observation_recorded", priority: 2, icon: ICONS.memo,    color: "#94a3b8", label: "Observation",   description: "Recorded trade observation." },
  analysis:          { type: "analysis",          priority: 2, icon: ICONS.thoughtBalloon, color: "#8b5cf6", label: "Agent Thoughts", description: "Agent analysis or reasoning." },
  reasoning:         { type: "reasoning",         priority: 2, icon: ICONS.thoughtBalloon, color: "#8b5cf6", label: "Agent Thoughts", description: "Agent analysis or reasoning." },
  plan:              { type: "plan",              priority: 2, icon: ICONS.thoughtBalloon, color: "#8b5cf6", label: "Agent Thoughts", description: "Agent analysis or reasoning." },
};

// --------- Utils ---------

function clamp(n: number, a: number, b: number) { return Math.max(a, Math.min(b, n)); }

function niceTicks(min: number, max: number, target = 5) {
  const span = max - min; if (span <= 0) return [] as number[];
  const step = Math.pow(10, Math.floor(Math.log10(span/target)));
  const err = (target*span)/(step*10);
  const steps = err >= 7.5 ? 10 : err >= 3 ? 5 : err >= 1.5 ? 2 : 1;
  const niceStep = steps*step;
  const ticks: number[] = [];
  const start = Math.ceil(min/niceStep)*niceStep;
  for (let v=start; v<=max; v+=niceStep) ticks.push(v);
  return ticks;
}

function linearInterpolateAt(ms: number, xs: number[], ys: number[]) {
  const n = xs.length;
  if (ms <= xs[0]) return ys[0];
  if (ms >= xs[n-1]) return ys[n-1];
  let lo=0, hi=n-1;
  while (hi-lo>1) {
    const mid=(lo+hi)>>1;
    if (xs[mid] <= ms) lo=mid;
    else hi=mid;
  }
  const t0=xs[lo], t1=xs[hi], v0=ys[lo], v1=ys[hi];
  const a=(ms-t0)/(t1-t0);
  return v0 + (v1-v0)*a;
}

function roundRect(ctx: CanvasRenderingContext2D, x:number,y:number,w:number,h:number,r:number) {
  const rr = Math.min(r, w/2, h/2);
  ctx.beginPath();
  ctx.moveTo(x+rr,y);
  ctx.arcTo(x+w,y,x+w,y+h,rr);
  ctx.arcTo(x+w,y+h,x,y+h,rr);
  ctx.arcTo(x,y+h,x,y,rr);
  ctx.arcTo(x,y,x+w,y,rr);
  ctx.closePath();
}

// --------- Zoom tiers ---------

const ZOOMS = ["1h","4h","1d","1w","All"] as const;
type ZoomTier = typeof ZOOMS[number];
const FUTURE_PAD_RATIO = 0.08; // 8% of span beyond now

const ZOOM_RULES: Record<ZoomTier, {
  spanMs: number | "all";
  bucketMs: number;
  iconPx: number;
  minSpacingPx: number;
  railGap: number;
}> = {
  "1h":  { spanMs: 60*60*1000,        bucketMs: 60*1000,     iconPx: 22, minSpacingPx: 18, railGap: 28 },
  "4h":  { spanMs: 4*60*60*1000,      bucketMs: 10*60*1000,  iconPx: 20, minSpacingPx: 18, railGap: 28 },
  "1d":  { spanMs: 24*60*60*1000,     bucketMs: 60*60*1000,  iconPx: 18, minSpacingPx: 20, railGap: 26 },
  "1w":  { spanMs: 7*24*60*60*1000,   bucketMs: 4*60*60*1000, iconPx: 16, minSpacingPx: 22, railGap: 24 },
  "All": { spanMs: "all",            bucketMs: 24*60*60*1000, iconPx: 14, minSpacingPx: 28, railGap: 24 },
};

// --------- Component ---------

interface ActivityTimelineViewerProps {
  configId: string; // For future API integration
}

export default function ActivityTimelineViewer({ configId }: ActivityTimelineViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);

  // API data state
  const [log, setLog] = useState<MockActivityLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<{ access_token?: string } | null>(null);
  const [zoom, setZoom] = useState<ZoomTier>("4h");
  const [domain, setDomain] = useState<{left: number; right: number}>({ left: Date.now() - 4*60*60*1000, right: Date.now() });
  const [selected, setSelected] = useState<ActivityItem[] | null>(null);
  const [showStrategy, setShowStrategy] = useState(false);
  const [strategy, setStrategy] = useState<string | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [visibleTypes, setVisibleTypes] = useState<Record<ActivityType, boolean>>(() => {
    const o: Record<string, boolean> = {};
    (Object.keys(ACTIVITY_DEFS) as ActivityType[]).forEach(k => o[k] = true);
    return o as Record<ActivityType, boolean>;
  });
  const [size, setSize] = useState({ w: 1200, h: 460 });

  // Get session for auth
  useEffect(() => {
    const supabase = createClientComponentClient()
    const getSession = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      setSession(session)
    }
    getSession()
  }, []);

  // Fetch activity data from API
  useEffect(() => {
    if (!configId || !session?.access_token) return;

    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch all three endpoints in parallel
        const [activitiesRes, balanceSeriesRes, metadataRes] = await Promise.all([
          fetch(`/api/v2/activities/${configId}`, {
            headers: { 'Authorization': `Bearer ${session.access_token}` }
          }),
          fetch(`/api/v2/activities/${configId}/balance-series`, {
            headers: { 'Authorization': `Bearer ${session.access_token}` }
          }),
          fetch(`/api/v2/activities/${configId}/metadata`, {
            headers: { 'Authorization': `Bearer ${session.access_token}` }
          })
        ]);

        if (!activitiesRes.ok || !balanceSeriesRes.ok || !metadataRes.ok) {
          throw new Error('Failed to fetch activity data');
        }

        const activities = await activitiesRes.json();
        const balanceSeries = await balanceSeriesRes.json();
        const metadata = await metadataRes.json();

        if (activities.status !== 'success' || balanceSeries.status !== 'success' || metadata.status !== 'success') {
          throw new Error('API returned error status');
        }

        // Transform API response to match MockActivityLog interface
        setLog({
          activities: activities.activities,
          balanceTimeseries: balanceSeries.balance_series,
          metadata: metadata.metadata
        });

        setError(null);
      } catch (err) {
        console.error('Failed to fetch activity data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load activity timeline');
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Poll for updates every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [configId, session]);

  // Fetch strategy
  useEffect(() => {
    if (!configId || !session?.access_token) return;

    const fetchStrategy = async () => {
      try {
        const response = await fetch(`/api/v2/config/${configId}`, {
          headers: { 'Authorization': `Bearer ${session.access_token}` }
        });
        const data = await response.json();
        if (data.config?.agent_strategy?.content) {
          setStrategy(data.config.agent_strategy.content);
        }
      } catch (err) {
        console.error('Failed to fetch strategy:', err);
      }
    };

    fetchStrategy();
  }, [configId, session]);

  // Fetch positions
  useEffect(() => {
    if (!configId || !session?.access_token) return;

    const fetchPositions = async () => {
      try {
        const response = await fetch(`/api/v2/paper-trading/${configId}/positions`, {
          headers: { 'Authorization': `Bearer ${session.access_token}` }
        });
        const data = await response.json();
        if (data.positions) {
          setPositions(data.positions);
        }
      } catch (err) {
        console.error('Failed to fetch positions:', err);
      }
    };

    fetchPositions();
    // Poll for position updates every 5 seconds
    const interval = setInterval(fetchPositions, 5000);
    return () => clearInterval(interval);
  }, [configId, session]);

  // Derived data (safe to compute even if log is null)
  const seriesMs = useMemo(() => {
    const points = log?.balanceTimeseries?.map(p => new Date(p.timestamp).getTime()) || [];
    // If no trades yet, create synthetic baseline spanning activities
    if (points.length === 0 && log?.activities && log.activities.length > 0) {
      const activityTimes = log.activities.map(a => new Date(a.timestamp).getTime());
      const earliest = Math.min(...activityTimes);
      const latest = Math.max(...activityTimes, Date.now());
      return [earliest, latest];
    }
    return points;
  }, [log]);

  const seriesVal = useMemo(() => {
    const balances = log?.balanceTimeseries?.map(p => p.balance) || [];
    // If no trades yet, create $0 baseline
    if (balances.length === 0 && log?.activities && log.activities.length > 0) {
      return [0, 0]; // Flat line at $0
    }
    return balances;
  }, [log]);

  const dataFirst = seriesMs[0] || Date.now() - 24*60*60*1000;
  const dataLast = seriesMs[seriesMs.length - 1] || Date.now();

  const rules = ZOOM_RULES[zoom];

  const rightBound = useMemo(() => {
    if (rules.spanMs === "all") return dataLast;
    return dataLast + Math.round((rules.spanMs as number) * FUTURE_PAD_RATIO);
  }, [rules, dataLast]);

  // Recompute domain when zoom changes
  useEffect(() => {
    if (rules.spanMs === "all") { setDomain({ left: dataFirst, right: dataLast }); return; }
    const span = rules.spanMs as number;
    const pad = Math.round(span * FUTURE_PAD_RATIO);
    const desiredSpan = span + pad;
    const center = (domain.left + domain.right) / 2;
    let left = Math.round(center - (span));
    let right = left + desiredSpan;
    const maxRight = rightBound;
    if (right > maxRight) { right = maxRight; left = right - desiredSpan; }
    if (left < dataFirst) { left = dataFirst; right = left + desiredSpan; }
    setDomain({ left, right });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoom]);

  // Resize
  useEffect(() => {
    const obs = new ResizeObserver(() => {
      const el = containerRef.current;
      if (!el) return;
      setSize({ w: el.clientWidth, h: el.clientHeight });
    });
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  // Series slice (safe with optional chaining)
  const inDomainSeries = useMemo(() => {
    const { left, right } = domain;
    const pad = (right - left) * 0.5;

    // If we have real balance data, use it
    if (log?.balanceTimeseries && log.balanceTimeseries.length > 0) {
      return log.balanceTimeseries.filter(p => {
        const t = new Date(p.timestamp).getTime();
        return t >= left - pad && t <= right + pad;
      });
    }

    // Otherwise create synthetic $0 baseline for activities to anchor to
    if (log?.activities && log.activities.length > 0 && seriesMs.length === 2) {
      return [
        { timestamp: new Date(seriesMs[0]).toISOString(), balance: 0 },
        { timestamp: new Date(seriesMs[1]).toISOString(), balance: 0 }
      ];
    }

    return [];
  }, [log, domain, seriesMs]);

  // Scales
  const padL = 56, padR = 16, padT = 24, padB = 28;
  const chartW = Math.max(10, size.w - padL - padR);
  const chartH = Math.max(10, size.h - padT - padB);

  function xScale(ms: number) {
    const t = (ms - domain.left) / (domain.right - domain.left);
    return padL + t * chartW;
  }

  const yExtent = useMemo(() => {
    let min = Infinity, max = -Infinity;
    for (const p of inDomainSeries) {
      min = Math.min(min, p.balance);
      max = Math.max(max, p.balance);
    }
    if (!isFinite(min)||!isFinite(max)) { min=0; max=1; }
    const span = max - min;
    const pad = span*0.1 + 1;
    return { min: min - pad, max: max + pad };
  }, [inDomainSeries]);

  function yScale(v: number) {
    const t = (v - yExtent.min) / (yExtent.max - yExtent.min);
    return padT + chartH - t * chartH;
  }

  // Bucketing (safe with optional chaining)
  const bucketed = useMemo(() => {
    if (!log?.activities) return [];
    const ms = rules.bucketMs;
    const { left, right } = domain;
    const pad = (right - left) * 0.25;

    // Filter by time and type visibility only (all priorities visible)
    const acts = log.activities.filter(a => {
      const t = new Date(a.timestamp).getTime();
      return t >= left - pad && t <= right + pad && visibleTypes[a.type];
    });

    // Group activities by time + type (priority 2) or time + id (priority 1)
    const map = new Map<string, ActivityItem[]>();
    for (const a of acts) {
      const t = new Date(a.timestamp).getTime();
      const b = Math.floor(t / ms) * ms;

      // Create composite bucket key based on priority
      let bucketKey: string;
      if (a.priority === 1) {
        // Priority 1 (trades): Never group - each activity gets unique key
        bucketKey = `${b}:${a.id}`;
      } else {
        // Priority 2 (queries, decisions, etc.): Group by type within time bucket
        bucketKey = `${b}:${a.type}`;
      }

      const arr = map.get(bucketKey) || [];
      arr.push(a);
      map.set(bucketKey, arr);
    }

    // Convert map to groups array
    const groups = Array.from(map.entries()).map(([bucketKey, items]) => {
      // Extract bucketTs from composite key (format: "timestamp:type" or "timestamp:id")
      const bucketTs = parseInt(bucketKey.split(':')[0]);

      // Sort items within group by timestamp
      items.sort((a,b)=> new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

      // Representative is always the first item (or prioritize priority 1 if mixed)
      const rep = items.find(x=>x.priority===1) || items[0];

      return { bucketTs, items, rep };
    }).sort((a,b)=> a.bucketTs - b.bucketTs);

    return groups;
  }, [log, rules, domain, visibleTypes]);

  // Hit boxes
  const hitBoxesRef = useRef<{x:number;y:number;w:number;h:number; cx:number; cy:number; R:number; color:string; icon:string; group: ActivityItem[]}[]>([]);

  // Base draw (chart + icons)
  useEffect(() => {
    const canvas = canvasRef.current;
    const overlay = overlayRef.current;
    if (!canvas || !overlay) return;

    const dpr = window.devicePixelRatio || 1;
    for (const c of [canvas, overlay]) {
      c.width = Math.floor(size.w*dpr);
      c.height = Math.floor(size.h*dpr);
      c.style.width = `${size.w}px`;
      c.style.height = `${size.h}px`;
    }

    const ctx = canvas.getContext("2d")!;
    const octx = overlay.getContext("2d")!;
    ctx.setTransform(dpr,0,0,dpr,0,0);
    octx.setTransform(dpr,0,0,dpr,0,0);

    // BG
    ctx.fillStyle = COLORS.bg;
    ctx.fillRect(0,0,size.w,size.h);

    // Grid
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i=0;i<=5;i++){
      const x=padL+(chartW/5)*i;
      ctx.moveTo(x,padT);
      ctx.lineTo(x,padT+chartH);
    }
    const ys = niceTicks(yExtent.min,yExtent.max,5);
    for (const v of ys){
      const y=Math.round(yScale(v))+0.5;
      ctx.moveTo(padL,y);
      ctx.lineTo(padL+chartW,y);
    }
    ctx.stroke();

    // Y labels
    ctx.fillStyle=COLORS.text;
    ctx.font="12px ui-sans-serif, system-ui, -apple-system";
    ctx.textAlign="right";
    ctx.textBaseline="middle";
    for (const v of ys){
      const y=yScale(v);
      ctx.fillText(`$${Math.round(v).toLocaleString()}`, padL-8, y);
    }

    // Equity line
    ctx.save();
    ctx.beginPath();
    let first=true;
    for (const p of inDomainSeries){
      const x=xScale(new Date(p.timestamp).getTime());
      const y=yScale(p.balance);
      if(first){ctx.moveTo(x,y); first=false;}
      else {ctx.lineTo(x,y);}
    }
    ctx.shadowColor=COLORS.lineGlow;
    ctx.shadowBlur=16;
    ctx.strokeStyle=COLORS.positive;
    ctx.lineWidth=2;
    ctx.stroke();
    ctx.restore();

    // X labels
    ctx.textAlign="center";
    ctx.textBaseline="top";
    const spanMs = domain.right-domain.left;
    const xTicks=[domain.left, domain.left+spanMs/2, domain.right];
    for (const t of xTicks){
      const d=new Date(t);
      const label = spanMs <= 24*60*60*1000 ? d.toUTCString().slice(17,22)+" UTC" : d.toUTCString().slice(5,16);
      ctx.fillText(label, xScale(t), padT+chartH+6);
    }

    // Activities – rails + stems + icons
    hitBoxesRef.current = [];
    const colW = rules.minSpacingPx;
    const cols = Math.ceil(chartW/colW);
    const railHeights=[rules.railGap, rules.railGap*2, rules.railGap*3];
    const occupancy = new Array(cols).fill(0);

    for (const g of bucketed){
      const px = xScale(g.bucketTs);
      if (px < padL || px > padL+chartW) continue;

      const col = Math.floor((px - padL)/colW);
      let row = occupancy[col] || 0;
      if (row>2) row=2;
      occupancy[col]=row+1;

      const anchorBal = linearInterpolateAt(g.bucketTs, seriesMs, seriesVal);
      let anchorY=yScale(anchorBal);
      anchorY=clamp(anchorY, padT, padT+chartH);

      const upwards = anchorY - padT > padB + 80;
      const offset = railHeights[row];
      const py = upwards ? (anchorY - offset) : (anchorY + offset);
      const def = ACTIVITY_DEFS[g.rep.type];
      const R = rules.iconPx;
      const icon = def.icon;

      // Stem
      const stemColor = def.color + "80";
      ctx.strokeStyle = stemColor;
      ctx.lineWidth=2;
      ctx.beginPath();
      ctx.moveTo(px, anchorY);
      const ctrlY = upwards? anchorY - offset*0.6 : anchorY + offset*0.6;
      ctx.bezierCurveTo(px, ctrlY, px, ctrlY, px, py);
      ctx.stroke();

      // Anchor dot
      ctx.beginPath();
      ctx.fillStyle = def.color;
      ctx.arc(px, anchorY, 3, 0, Math.PI*2);
      ctx.fill();

      // Icon disc + ring
      ctx.beginPath();
      ctx.fillStyle = COLORS.iconBg;
      ctx.arc(px, py, R, 0, Math.PI*2);
      ctx.fill();
      ctx.beginPath();
      ctx.strokeStyle = COLORS.iconRing;
      ctx.lineWidth=1.5;
      ctx.arc(px, py, R-0.5, 0, Math.PI*2);
      ctx.stroke();

      // Emoji
      ctx.font = `${Math.max(14,R)}px "Apple Color Emoji","Segoe UI Emoji", system-ui`;
      ctx.textAlign="center";
      ctx.textBaseline="middle";
      ctx.fillText(icon, px, py+0.5);

      // Count badge
      if (g.items.length>1){
        const r=8, bx=px+R-4, by=py-R+4;
        ctx.beginPath();
        ctx.fillStyle = def.color;
        ctx.arc(bx,by,r,0,Math.PI*2);
        ctx.fill();
        ctx.fillStyle="#0b0d12";
        ctx.font="10px ui-sans-serif";
        ctx.fillText(String(g.items.length), bx, by+0.5);
      }

      // Hitbox
      hitBoxesRef.current.push({
        x: px-R, y: py-R, w: R*2, h: R*2,
        cx: px, cy: py, R,
        color: def.color, icon, group: g.items
      });
    }

    // Clear overlay
    octx.clearRect(0,0,size.w,size.h);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [size, domain, inDomainSeries, bucketed, yExtent, zoom, seriesMs, seriesVal, rules]);

  // Animation loop for overlay (hover + pulsing now)
  useEffect(() => {
    const overlay = overlayRef.current;
    if (!overlay) return;
    const ctx = overlay.getContext("2d")!;
    let raf: number | null = null;

    const draw = (t: number) => {
      const dpr = window.devicePixelRatio || 1;
      ctx.setTransform(dpr,0,0,dpr,0,0);
      ctx.clearRect(0,0,overlay.width/dpr, overlay.height/dpr);

      // Pulsing "now" dot
      const latestMs = dataLast;
      if (latestMs >= domain.left && latestMs <= domain.right) {
        const nowX = xScale(latestMs);
        const nowY = yScale(linearInterpolateAt(latestMs, seriesMs, seriesVal));

        // Determine pulse color based on current state
        const latestActivity = log?.activities ? [...log.activities].sort((a,b)=> new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0] : null;
        let pulseColor = COLORS.positive; // default green
        let pulseRgb = "16,185,129"; // emerald-500

        if (latestActivity && log?.activities) {
          const lastEntry = [...log.activities]
            .filter(a => a.type === 'trade_entry_long' || a.type === 'trade_entry_short')
            .sort((a,b)=> new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];
          const lastExit = [...log.activities]
            .filter(a => a.type === 'trade_win' || a.type === 'trade_loss')
            .sort((a,b)=> new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];
          const inPosition = lastEntry && (!lastExit || new Date(lastEntry.timestamp) > new Date(lastExit.timestamp));

          if (inPosition) {
            pulseColor = lastEntry.type === 'trade_entry_long' ? COLORS.positive : COLORS.negative;
            pulseRgb = lastEntry.type === 'trade_entry_long' ? "16,185,129" : "244,63,94";
          } else if (latestActivity.type === 'agent_wait') {
            pulseRgb = "100,116,139"; // gray
          } else if (latestActivity.type === 'market_query') {
            pulseRgb = "59,130,246"; // blue
          } else if (['analysis', 'reasoning', 'plan'].includes(latestActivity.type)) {
            pulseRgb = "139,92,246"; // purple
          }
        }

        // Pulse rings
        const tt = (t/1000) % 1.5;
        const r1 = 4 + tt*10;
        const a1 = 0.4 - tt*0.3;
        const r2 = 4 + ((tt+0.5)%1.5)*10;
        const a2 = 0.3 - ((tt+0.5)%1.5)*0.25;

        ctx.save();
        ctx.beginPath();
        ctx.arc(nowX, nowY, r1, 0, Math.PI*2);
        ctx.strokeStyle = `rgba(${pulseRgb},${Math.max(0,a1)})`;
        ctx.lineWidth = 2.5;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(nowX, nowY, r2, 0, Math.PI*2);
        ctx.strokeStyle = `rgba(${pulseRgb},${Math.max(0,a2)})`;
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Center dot with glow
        ctx.shadowColor = pulseColor;
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.fillStyle = pulseColor;
        ctx.arc(nowX, nowY, 4, 0, Math.PI*2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // Current state pill - intelligent status
        let statusText = "Idle";
        let statusColor = pulseColor; // Use same color as pulse dot

        if (latestActivity) {
          const timeSince = Date.now() - new Date(latestActivity.timestamp).getTime();
          const minutesAgo = Math.floor(timeSince / 60000);

          // Reuse position check from above
          const lastEntry = log?.activities ? [...log.activities]
            .filter(a => a.type === 'trade_entry_long' || a.type === 'trade_entry_short')
            .sort((a,b)=> new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0] : null;
          const lastExit = log?.activities ? [...log.activities]
            .filter(a => a.type === 'trade_win' || a.type === 'trade_loss')
            .sort((a,b)=> new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0] : null;
          const inPosition = lastEntry && (!lastExit || new Date(lastEntry.timestamp) > new Date(lastExit.timestamp));

          if (inPosition) {
            const side = lastEntry.type === 'trade_entry_long' ? 'Long' : 'Short';
            const symbol = lastEntry.data.symbol || 'position';
            statusText = `🟢 In ${side}: ${symbol}`;
            statusColor = lastEntry.type === 'trade_entry_long' ? COLORS.positive : COLORS.negative;
          } else if (latestActivity.type === 'agent_wait') {
            // Extract wait duration if available
            const details = latestActivity.data.details as unknown as {duration_minutes?: number};
            if (details && details.duration_minutes) {
              const elapsed = minutesAgo;
              const remaining = Math.max(0, details.duration_minutes - elapsed);
              statusText = remaining > 0 ? `⏱️ Waiting ${remaining}m` : `👁️ Monitoring`;
              statusColor = "#64748b";
            } else {
              statusText = `⏱️ Waiting`;
              statusColor = "#64748b";
            }
          } else if (latestActivity.type === 'market_query') {
            const symbol = latestActivity.data.symbol || 'markets';
            statusText = `📊 Analyzing ${symbol}`;
            statusColor = "#3b82f6";
          } else if (['analysis', 'reasoning', 'plan'].includes(latestActivity.type)) {
            statusText = `💭 Thinking...`;
            statusColor = "#8b5cf6";
          } else if (latestActivity.type === 'trade_win' || latestActivity.type === 'trade_loss') {
            if (minutesAgo < 5) {
              const pnl = (latestActivity.data.details as unknown as {pnl?: number})?.pnl || 0;
              statusText = latestActivity.type === 'trade_win'
                ? `📈 Won +$${Math.abs(pnl).toFixed(2)}`
                : `📉 Lost -$${Math.abs(pnl).toFixed(2)}`;
              statusColor = latestActivity.type === 'trade_win' ? COLORS.positive : COLORS.negative;
            } else {
              statusText = `👁️ Monitoring`;
              statusColor = "#6b7280";
            }
          } else if (minutesAgo > 30) {
            statusText = "😴 Idle";
            statusColor = "#64748b";
          } else {
            const def = ACTIVITY_DEFS[latestActivity.type];
            statusText = `${def.icon} ${def.label}`;
            statusColor = def.color;
          }
        }

        ctx.font = "500 13px ui-sans-serif, system-ui";
        const metrics = ctx.measureText(statusText);
        const pw = Math.ceil(metrics.width) + 20;
        const ph = 26;
        const maxW = (overlay.width/dpr) - 56 - 16;
        const maxH = (overlay.height/dpr) - 24 - 28;
        const px = Math.min(Math.max(nowX + 14, 56), 56 + Math.max(10, maxW - pw));
        const py = Math.max(24, Math.min(nowY - ph - 10, 24 + Math.max(10, maxH - ph)));

        ctx.save();
        roundRect(ctx, px, py, pw, ph, 10);
        ctx.fillStyle = "rgba(8,10,14,0.92)";
        ctx.fill();
        ctx.strokeStyle = statusColor + "50";
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.fillStyle = statusColor;
        ctx.textBaseline = "middle";
        ctx.textAlign = "left";
        ctx.fillText(statusText, px + 10, py + ph/2 + 1);
        ctx.restore();
      }

      raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);
    return () => { if (raf) cancelAnimationFrame(raf); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [domain, dataLast, seriesMs, seriesVal, log]);

  // Interactions
  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;
    let isDragging = false;
    let dragStartX = 0;
    let lastX = 0;
    let v = 0;
    let raf: number | null = null;

    const span = () => (domain.right - domain.left);
    const applyPan = (dtMs: number) => {
      const left = domain.left + dtMs;
      const right = domain.right + dtMs;
      const clamped = clampDomain(left, right);
      setDomain(clamped);
    };

    const onDown = (e: PointerEvent) => {
      isDragging = true;
      dragStartX = e.clientX;
      lastX = e.clientX;
      v = 0;
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
    };

    const onMove = (e: PointerEvent) => {
      // Show pointer cursor on hover
      const rect = c.getBoundingClientRect();
      const x = (e.clientX - rect.left);
      const y = (e.clientY - rect.top);
      const hit = hitBoxesRef.current.find(b => x>=b.x && x<=b.x+b.w && y>=b.y && y<=b.y+b.h);
      c.style.cursor = hit ? "pointer" : "default";

      if (!isDragging) return;
      const dx = e.clientX - lastX;
      lastX = e.clientX;
      v = dx;
      const msPerPx = span() / (Math.max(1, (c.clientWidth) - 56 - 16));
      applyPan(-dx * msPerPx);
    };

    const onUp = (e: PointerEvent) => {
      if (!isDragging) return;
      isDragging = false;
      (e.target as HTMLElement).releasePointerCapture(e.pointerId);

      // Only trigger click if we didn't drag much
      const dragDistance = Math.abs(e.clientX - dragStartX);
      if (dragDistance < 5) {
        // This was a click, not a drag
        const rect = c.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const hit = hitBoxesRef.current.find(b => x>=b.x && x<=b.x+b.w && y>=b.y && y<=b.y+b.h);
        if (hit) setSelected(hit.group);
      } else {
        // This was a drag, apply inertia
        const decay = 0.92;
        let vel = v;
        const step = () => {
          if (Math.abs(vel) < 0.2) {
            if (raf) cancelAnimationFrame(raf);
            raf = null;
            return;
          }
          const msPerPx = span() / (Math.max(1, (c.clientWidth) - 56 - 16));
          applyPan(-vel * msPerPx);
          vel *= decay;
          raf = requestAnimationFrame(step);
        };
        if (!raf) raf = requestAnimationFrame(step);
      }
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      if (rules.spanMs === "all") return;
      if (e.shiftKey) {
        const idx = ZOOMS.indexOf(zoom);
        const next = e.deltaY < 0 ? clamp(idx-1, 0, ZOOMS.length-1) : clamp(idx+1, 0, ZOOMS.length-1);
        if (next !== idx) setZoom(ZOOMS[next]);
        return;
      }
      const step = (domain.right - domain.left) * 0.15;
      const dir = e.deltaY < 0 ? -1 : 1;
      applyPan(dir * step);
    };

    c.addEventListener("pointerdown", onDown);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    c.addEventListener("wheel", onWheel, { passive: false });

    return () => {
      c.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      c.removeEventListener("wheel", onWheel);
      if (raf) cancelAnimationFrame(raf);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoom, domain, rules]);

  // Helper function for domain clamping
  function clampDomain(left: number, right: number) {
    if (rules.spanMs === "all") return { left: dataFirst, right: dataLast };
    const span = right - left;
    const maxRight = rightBound;
    const minLeft = dataFirst;
    if (right > maxRight) { right = maxRight; left = right - span; }
    if (left < minLeft) { left = minLeft; right = left + span; }
    return { left, right };
  }

  // Loading state
  if (loading && !log) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-charcoal-900">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500" />
          <span className="text-bone-200">Loading activity timeline...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-charcoal-900">
        <div className="text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <div className="text-xl text-bone-200 mb-2">Failed to Load Timeline</div>
          <div className="text-bone-400">{error}</div>
        </div>
      </div>
    );
  }

  // Empty state
  if (!log || log.activities.length === 0) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-charcoal-900">
        <div className="text-center">
          <div className="text-4xl mb-4">📊</div>
          <div className="text-xl text-bone-200 mb-2">No Activity Yet</div>
          <div className="text-bone-400">Activities will appear here once the bot starts trading</div>
        </div>
      </div>
    );
  }

  // Jump to Now
  const jumpToNow = () => {
    if (rules.spanMs === "all") {
      setDomain({ left: dataFirst, right: dataLast });
      return;
    }
    const span = (rules.spanMs as number);
    const pad = Math.round(span * FUTURE_PAD_RATIO);
    setDomain({ left: dataLast - span, right: dataLast + pad });
  };

  const info = log?.metadata;

  return (
    <div className="w-full h-full min-h-screen bg-[#0b0d12] text-white">
      <div className="max-w-7xl mx-auto px-6 py-6 space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/20 grid place-items-center">{ICONS.robot}</div>
          <div className="text-lg font-semibold">{info.botName}</div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {ZOOMS.map(z => (
            <button
              key={z}
              className={`px-3 py-1 rounded-xl border text-sm ${z===zoom?"bg-white text-black":"border-white/20 text-white/80 hover:bg-white/10"}`}
              onClick={()=>setZoom(z)}
            >
              {z}
            </button>
          ))}
          <div className="flex-1" />
          {strategy && (
            <button
              className="px-3 py-1 rounded-xl border border-white/20 text-white/80 hover:bg-white/10"
              onClick={()=>setShowStrategy(true)}
            >
              📋 View Strategy
            </button>
          )}
          <button
            className="px-3 py-1 rounded-xl border border-white/20 text-white/80 hover:bg-white/10"
            onClick={jumpToNow}
          >
            Jump to Now
          </button>
        </div>

        {/* Chart area with left sidebar legend */}
        <div className="flex gap-4 h-[calc(100vh-220px)] min-h-[500px]">
          {/* Legend / Activity Filters - Left Sidebar */}
          <div className="w-48 space-y-3 flex-shrink-0">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-white/70">Activity Types</h3>
            </div>

            <div className="flex flex-col gap-2">
              {(() => {
                // Deduplicate: analysis/reasoning/plan all show as one "Agent Thoughts" button
                const seen = new Set<string>();
                const legendItems: { key: string; def: ActivityDefinition; types: ActivityType[] }[] = [];

                (Object.keys(ACTIVITY_DEFS) as ActivityType[]).forEach(k => {
                  const def = ACTIVITY_DEFS[k];
                  const label = def.label;

                  if (!seen.has(label)) {
                    seen.add(label);
                    // Find all types with same label
                    const relatedTypes = (Object.keys(ACTIVITY_DEFS) as ActivityType[])
                      .filter(t => ACTIVITY_DEFS[t].label === label);
                    legendItems.push({ key: k, def, types: relatedTypes });
                  }
                });

                return legendItems.map(({ key, def, types }) => {
                  // Button is "on" if ANY of the related types are visible
                  const on = types.some(t => visibleTypes[t]);

                  return (
                    <button
                      key={key}
                      onClick={() => {
                        // Toggle all related types together
                        setVisibleTypes(v => {
                          const newState = { ...v };
                          types.forEach(t => { newState[t] = !on; });
                          return newState;
                        });
                      }}
                      className={`px-3 py-2 rounded-xl text-sm border transition-all ${
                        on
                          ? "bg-white/10 border-white/30 text-white"
                          : "border-white/10 text-white/40 hover:border-white/20 hover:text-white/60"
                      }`}
                      title={def.description}
                    >
                      <span className="text-base mr-1.5">{def.icon}</span>
                      {def.label}
                    </button>
                  );
                });
              })()}
            </div>

            <button
              onClick={() => {
                const allOn = Object.values(visibleTypes).every(v => v);
                setVisibleTypes(
                  Object.fromEntries(
                    (Object.keys(ACTIVITY_DEFS) as ActivityType[]).map(k => [k, !allOn])
                  ) as Record<ActivityType, boolean>
                );
              }}
              className="w-full text-xs text-white/50 hover:text-white/80 py-1 border border-white/10 rounded-lg hover:bg-white/5"
            >
              Toggle All
            </button>

            {/* Navigation hint */}
            <div className="text-xs text-white/40 pt-2">
              💡 <span className="text-white/50">Wheel to scroll • Shift+Wheel to zoom • Drag to pan</span>
            </div>
          </div>

          {/* Chart area */}
          <div
            ref={containerRef}
            className="relative flex-1 rounded-2xl overflow-hidden ring-1 ring-white/10"
            style={{background: COLORS.bg}}
          >
            <canvas ref={canvasRef} className="absolute inset-0 w-full h-full"/>
            <canvas ref={overlayRef} className="absolute inset-0 w-full h-full pointer-events-none"/>
          </div>
        </div>
      </div>

      {/* Active Positions Section */}
      {positions.length > 0 && (
        <div className="max-w-7xl mx-auto px-6 pb-6">
          <div className="bg-[#12151c] rounded-2xl border border-white/10 overflow-hidden">
            <div className="px-6 py-4 border-b border-white/10">
              <h3 className="text-lg font-semibold">Active Positions</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-white/70 border-b border-white/10">
                    <th className="px-6 py-3">Symbol</th>
                    <th className="px-6 py-3">Side</th>
                    <th className="px-6 py-3">Entry Price</th>
                    <th className="px-6 py-3">Current Price</th>
                    <th className="px-6 py-3">Size</th>
                    <th className="px-6 py-3">P&L</th>
                    <th className="px-6 py-3">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos: Position, idx: number) => {
                    const pnl = pos.unrealized_pnl || 0;
                    const pnlColor = pnl >= 0 ? 'text-emerald-400' : 'text-red-400';
                    return (
                      <tr key={idx} className="border-b border-white/5 hover:bg-white/5">
                        <td className="px-6 py-4 font-medium">{pos.symbol}</td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded text-xs ${pos.side === 'long' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                            {pos.side?.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-mono text-sm">${pos.entry_price?.toFixed(2)}</td>
                        <td className="px-6 py-4 font-mono text-sm">${pos.current_price?.toFixed(2)}</td>
                        <td className="px-6 py-4 font-mono text-sm">{pos.size?.toFixed(4)}</td>
                        <td className={`px-6 py-4 font-mono text-sm font-semibold ${pnlColor}`}>
                          {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)} ({pos.unrealized_pnl_percentage?.toFixed(2)}%)
                        </td>
                        <td className="px-6 py-4 text-sm text-white/60">
                          {pos.opened_at ? new Date(pos.opened_at).toLocaleString() : 'N/A'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Strategy Modal */}
      {showStrategy && strategy && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-8" onClick={()=>setShowStrategy(false)}>
          <div className="bg-[#12151c] rounded-2xl border border-white/10 max-w-3xl w-full max-h-[80vh] overflow-hidden shadow-2xl" onClick={(e)=>e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Agent Strategy</h2>
              <button onClick={()=>setShowStrategy(false)} className="text-white/70 hover:text-white text-2xl">{ICONS.close}</button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-5rem)]">
              <pre className="whitespace-pre-wrap text-sm text-white/90 font-mono leading-relaxed">{strategy}</pre>
            </div>
          </div>
        </div>
      )}

      {/* Side panel */}
      <SidePanel selected={selected} onClose={()=>setSelected(null)} />
    </div>
  );
}

// --------- Side Panel Component ---------

function SidePanel({ selected, onClose }: { selected: ActivityItem[] | null; onClose: ()=>void }) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Click outside to close
  useEffect(() => {
    if (!selected) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    // Add slight delay to prevent immediate close on same click that opened
    const timeoutId = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 100);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [selected, onClose]);

  return (
    <>
      {/* Backdrop */}
      {selected && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm transition-opacity duration-300 z-40" onClick={onClose} />
      )}

      {/* Panel */}
      <div
        ref={panelRef}
        className={`fixed top-0 right-0 h-full w-[560px] bg-[#12151c] shadow-2xl border-l border-white/10 transition-transform duration-300 z-50 ${selected?"translate-x-0":"translate-x-full"}`}
      >
        <div className="h-14 flex items-center justify-between px-6 border-b border-white/10">
          <div className="font-semibold text-lg">
            {selected ? (selected.length>1 ? `${selected.length} Activities` : ACTIVITY_DEFS[selected[0].type].label) : ""}
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white text-xl">{ICONS.close}</button>
        </div>
        <div className="p-6 space-y-4 overflow-y-auto h-[calc(100%-3.5rem)]">
          {!selected && (
            <div className="text-white/50 text-sm">Click any icon on the chart to see full context.</div>
          )}
          {selected && selected
            .slice()
            .sort((a,b)=> (a.priority-b.priority)|| (new Date(a.timestamp).getTime()-new Date(b.timestamp).getTime()))
            .map(item => {
              const def = ACTIVITY_DEFS[item.type];
              const t = new Date(item.timestamp);
              return (
                <div key={item.id} className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">{def.icon}</div>
                    <div>
                      <div className="font-medium text-base">{def.label}</div>
                      <div className="text-xs text-white/60">{t.toUTCString()}</div>
                    </div>
                  </div>
                  <div className="space-y-2 text-sm">
                    {Object.entries(item.data).filter(([k]) => k !== 'details' && k !== 'reasoning' && k !== 'summary').map(([k, v]) => (
                      <div key={k} className="flex items-start justify-between gap-4 py-1">
                        <span className="text-white/50 min-w-[100px]">{k}:</span>
                        <span className="font-mono text-white/90 text-right flex-1">{typeof v === 'number' ? v.toLocaleString() : String(v)}</span>
                      </div>
                    ))}
                  </div>
                  {/* Display agent thought content */}
                  {(() => {
                    const details = item.data.details;
                    if (details && typeof details === 'object' && 'thought' in details) {
                      const thought = (details as { thought: unknown }).thought;
                      if (typeof thought === 'string') {
                        return (
                          <div className="mt-3 pt-3 border-t border-white/10 text-sm text-white/80 whitespace-pre-wrap leading-relaxed">
                            {thought}
                          </div>
                        );
                      }
                    }
                    return null;
                  })()}
                  {/* Fallback for reasoning field */}
                  {typeof item.data.reasoning === 'string' && (
                    <div className="mt-3 pt-3 border-t border-white/10 text-sm text-white/80 whitespace-pre-wrap">{item.data.reasoning}</div>
                  )}
                </div>
              );
            })}
        </div>
      </div>
    </>
  );
}
