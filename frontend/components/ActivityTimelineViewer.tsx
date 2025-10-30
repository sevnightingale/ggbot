"use client"

import React, {useEffect, useMemo, useRef, useState} from "react";

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

type Priority = 1 | 2 | 3;

type ActivityType =
  | "trade_entry_long"
  | "trade_entry_short"
  | "trade_exit"
  | "position_adjusted"
  | "decision_made"
  | "market_query"
  | "agent_wait"
  | "observation_recorded"
  | "strategy_updated"
  | "agent_reasoning";

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
  data: Record<string, string | number>;
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
  blackSquare: "\u2B1B",              // ⬛ U+2B1B
  counterClockwise: "\uD83D\uDD01",   // 🔄 U+1F501
  thoughtBalloon: "\uD83D\uDCAD",     // 💭 U+1F4AD
  barChart: "\uD83D\uDCCA",          // 📊 U+1F4CA
  stopwatch: "\u23F1\uFE0F",          // ⏱️ U+23F1 U+FE0F
  memo: "\uD83D\uDCDD",               // 📝 U+1F4DD
  wrench: "\uD83D\uDD27",             // 🔧 U+1F527
  lightBulb: "\uD83D\uDCA1",          // 💡 U+1F4A1
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
  trade_entry_long: { type: "trade_entry_long", priority: 1, icon: ICONS.greenCircle, color: "#10b981", label: "Long Entry", description: "Bot opened a long position." },
  trade_entry_short:{ type: "trade_entry_short",priority: 1, icon: ICONS.redCircle,   color: "#f43f5e", label: "Short Entry", description: "Bot opened a short position." },
  trade_exit:        { type: "trade_exit",       priority: 1, icon: ICONS.blackSquare, color: "#6b7280", label: "Position Closed", description: "Bot closed a position." },
  position_adjusted: { type: "position_adjusted",priority: 1, icon: ICONS.counterClockwise, color: "#22c55e", label: "Position Adjusted", description: "Size/SL/TP modified." },
  decision_made:     { type: "decision_made",    priority: 2, icon: ICONS.thoughtBalloon, color: "#8b5cf6", label: "Decision", description: "Agent decision step." },
  market_query:      { type: "market_query",     priority: 2, icon: ICONS.barChart,       color: "#3b82f6", label: "Data Query", description: "Fetched market data." },
  agent_wait:        { type: "agent_wait",       priority: 2, icon: ICONS.stopwatch,      color: "#64748b", label: "Waiting", description: "Waiting for confirmation." },
  observation_recorded:{type:"observation_recorded",priority:3,icon: ICONS.memo,          color:"#94a3b8", label:"Note", description:"Recorded observation."},
  strategy_updated:  { type: "strategy_updated", priority: 3, icon: ICONS.wrench,         color: "#a855f7", label: "Strategy Update", description: "Strategy parameters changed." },
  agent_reasoning:   { type: "agent_reasoning",  priority: 3, icon: ICONS.lightBulb,      color: "#fde047", label: "Reasoning", description: "Internal chain-of-thought summary." },
};

// --------- Mock Data Generator ---------

function generateMockLog(): MockActivityLog {
  const now = Date.now();
  const begin = now - 3*24*60*60*1000; // 3 days ago
  const end = now;

  // Generate balance timeseries (every 5 minutes)
  const series: BalancePoint[] = [];
  let bal = 10000;
  for (let t = begin; t <= end; t += 5*60*1000) {
    const drift = Math.sin((t - begin) / (6*60*60*1000)) * 8;
    const noise = (Math.random()-0.5)*10;
    bal = Math.max(9000, bal + drift + noise);
    series.push({ timestamp: new Date(t).toISOString(), balance: Math.round(bal) });
  }

  // Generate activities
  const types: ActivityType[] = [
    "trade_entry_long","trade_entry_short","trade_exit","position_adjusted",
    "decision_made","market_query","agent_wait","observation_recorded",
    "strategy_updated","agent_reasoning"
  ];
  const activities: ActivityItem[] = [];

  for (let i=0;i<260;i++) {
    const tt = begin + Math.random()*(end-begin);
    const type = types[Math.floor(Math.random()*types.length)];
    const def = ACTIVITY_DEFS[type];

    activities.push({
      id: String(i),
      timestamp: new Date(tt).toISOString(),
      type,
      priority: def.priority,
      data: {
        symbol: "BTC/USDT",
        price: 42000 + Math.round(Math.random()*3000-1500),
        size: (Math.random()*5000+1000).toFixed(0),
        reasoning: "Mock rationale for action.",
        confidence: Math.round(50+Math.random()*50)
      }
    });
  }

  const metadata = {
    botName: "RSI Scalper v2",
    startingBalance: 10000,
    currentBalance: series.at(-1)!.balance,
    totalTrades: activities.filter(a=>a.type.includes("trade_"))?.length||0,
    winRate: 68,
    performance: ((series.at(-1)!.balance-10000)/10000)*100
  };

  return { activities, balanceTimeseries: series, metadata };
}

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
  visible: Priority[];
  iconPx: number;
  minSpacingPx: number;
  railGap: number;
}> = {
  "1h":  { spanMs: 60*60*1000,        bucketMs: 60*1000,     visible: [1,2,3], iconPx: 22, minSpacingPx: 18, railGap: 28 },
  "4h":  { spanMs: 4*60*60*1000,      bucketMs: 10*60*1000,  visible: [1,2],   iconPx: 20, minSpacingPx: 18, railGap: 28 },
  "1d":  { spanMs: 24*60*60*1000,     bucketMs: 60*60*1000,  visible: [1],     iconPx: 18, minSpacingPx: 20, railGap: 26 },
  "1w":  { spanMs: 7*24*60*60*1000,   bucketMs: 4*60*60*1000,visible: [1],     iconPx: 16, minSpacingPx: 22, railGap: 24 },
  "All": { spanMs: "all",            bucketMs: 24*60*60*1000,visible: [1],    iconPx: 14, minSpacingPx: 28, railGap: 24 },
};

// --------- Component ---------

interface ActivityTimelineViewerProps {
  configId: string; // For future API integration
}

export default function ActivityTimelineViewer({ configId: _configId }: ActivityTimelineViewerProps) {
  // _configId will be used when we connect to real API
  // For now using mock data
  void _configId; // Acknowledge unused param
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);

  const [log] = useState<MockActivityLog>(() => generateMockLog());
  const [zoom, setZoom] = useState<ZoomTier>("4h");

  const seriesMs = useMemo(() => log.balanceTimeseries.map(p => new Date(p.timestamp).getTime()), [log.balanceTimeseries]);
  const seriesVal = useMemo(() => log.balanceTimeseries.map(p => p.balance), [log.balanceTimeseries]);
  const dataFirst = seriesMs[0];
  const dataLast = seriesMs[seriesMs.length - 1];

  // Time domain (locked span per zoom, with future pad)
  const [domain, setDomain] = useState<{left: number; right: number}>(() => {
    const baseSpan = ZOOM_RULES["4h"].spanMs as number;
    const pad = Math.round(baseSpan * FUTURE_PAD_RATIO);
    return { left: dataLast - baseSpan, right: dataLast + pad };
  });

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

  function clampDomain(left: number, right: number) {
    if (rules.spanMs === "all") return { left: dataFirst, right: dataLast };
    const span = right - left;
    const maxRight = rightBound;
    const minLeft = dataFirst;
    if (right > maxRight) { right = maxRight; left = right - span; }
    if (left < minLeft) { left = minLeft; right = left + span; }
    return { left, right };
  }

  // Resize
  const [size, setSize] = useState({ w: 960, h: 460 });
  useEffect(() => {
    const obs = new ResizeObserver(() => {
      const el = containerRef.current;
      if (!el) return;
      setSize({ w: el.clientWidth, h: el.clientHeight });
    });
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  // Selection + hover
  const [selected, setSelected] = useState<ActivityItem[] | null>(null);
  const hoverRef = useRef<{x:number;y:number;cx:number;cy:number;R:number;color:string;icon:string;group:ActivityItem[]} | null>(null);

  // Series slice
  const inDomainSeries = useMemo(() => {
    const { left, right } = domain;
    const pad = (right - left) * 0.5;
    return log.balanceTimeseries.filter(p => {
      const t = new Date(p.timestamp).getTime();
      return t >= left - pad && t <= right + pad;
    });
  }, [log.balanceTimeseries, domain]);

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

  // Visibility + bucketing
  const [visibleTypes, setVisibleTypes] = useState<Record<ActivityType, boolean>>(() => {
    const o: Record<string, boolean> = {};
    (Object.keys(ACTIVITY_DEFS) as ActivityType[]).forEach(k => o[k] = true);
    return o as Record<ActivityType, boolean>;
  });

  const bucketed = useMemo(() => {
    const ms = rules.bucketMs;
    const visibleP = new Set(rules.visible);
    const { left, right } = domain;
    const pad = (right - left) * 0.25;

    const acts = log.activities.filter(a => {
      const t = new Date(a.timestamp).getTime();
      return t >= left - pad && t <= right + pad && visibleP.has(a.priority) && visibleTypes[a.type];
    });

    const map = new Map<number, ActivityItem[]>();
    for (const a of acts) {
      const t = new Date(a.timestamp).getTime();
      const b = Math.floor(t / ms) * ms;
      const arr = map.get(b) || [];
      arr.push(a);
      map.set(b, arr);
    }

    const groups = Array.from(map.entries()).map(([bucketTs, items]) => {
      items.sort((a,b)=> (a.priority-b.priority) || (new Date(a.timestamp).getTime()-new Date(b.timestamp).getTime()));
      const rep = items.find(x=>x.priority===1) || items[0];
      return { bucketTs, items, rep };
    }).sort((a,b)=> a.bucketTs - b.bucketTs);

    return groups;
  }, [log.activities, rules, domain, visibleTypes]);

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

      // Hover effect
      const h = hoverRef.current;
      if (h) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(h.cx, h.cy, h.R+6, 0, Math.PI*2);
        ctx.fillStyle = COLORS.hoverGlow;
        ctx.fill();
        ctx.beginPath();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = h.color;
        ctx.arc(h.cx, h.cy, h.R-0.5, 0, Math.PI*2);
        ctx.stroke();
        ctx.font = `${Math.max(14,h.R)}px "Apple Color Emoji","Segoe UI Emoji", system-ui`;
        ctx.textAlign="center";
        ctx.textBaseline="middle";
        ctx.fillText(h.icon, h.cx, h.cy+0.5);
        ctx.restore();
      }

      // Pulsing "now" dot
      const latestMs = dataLast;
      if (latestMs >= domain.left && latestMs <= domain.right) {
        const nowX = xScale(latestMs);
        const nowY = yScale(linearInterpolateAt(latestMs, seriesMs, seriesVal));

        // Pulse rings
        const tt = (t/1000) % 1.5;
        const r1 = 4 + tt*8;
        const a1 = 0.35 - tt*0.25;
        const r2 = 4 + ((tt+0.5)%1.5)*8;
        const a2 = 0.25 - ((tt+0.5)%1.5)*0.2;

        ctx.save();
        ctx.beginPath();
        ctx.arc(nowX, nowY, r1, 0, Math.PI*2);
        ctx.strokeStyle = `rgba(16,185,129,${Math.max(0,a1)})`;
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(nowX, nowY, r2, 0, Math.PI*2);
        ctx.strokeStyle = `rgba(16,185,129,${Math.max(0,a2)})`;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Center dot
        ctx.beginPath();
        ctx.fillStyle = COLORS.positive;
        ctx.arc(nowX, nowY, 3.5, 0, Math.PI*2);
        ctx.fill();

        // Current state pill
        const latestActivity = [...log.activities].sort((a,b)=> new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];
        const label = latestActivity ? ACTIVITY_DEFS[latestActivity.type].label : "Idle";
        const text = `Current: ${label}`;
        ctx.font = "12px ui-sans-serif";
        const metrics = ctx.measureText(text);
        const pw = Math.ceil(metrics.width) + 14;
        const ph = 20;
        const maxW = (overlay.width/dpr) - 56 - 16;
        const maxH = (overlay.height/dpr) - 24 - 28;
        const px = Math.min(Math.max(nowX + 10, 56), 56 + Math.max(10, maxW - pw));
        const py = Math.max(24, Math.min(nowY - ph - 8, 24 + Math.max(10, maxH - ph)));

        ctx.save();
        roundRect(ctx, px, py, pw, ph, 8);
        ctx.fillStyle = COLORS.pillBg;
        ctx.fill();
        ctx.strokeStyle = COLORS.pillBorder;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.fillStyle = COLORS.text;
        ctx.textBaseline = "middle";
        ctx.textAlign = "left";
        ctx.fillText(text, px + 7, py + ph/2 + 0.5);
        ctx.restore();
      }

      raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);
    return () => { if (raf) cancelAnimationFrame(raf); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [domain, dataLast, seriesMs, seriesVal, log.activities]);

  // Interactions
  useEffect(() => {
    const c = canvasRef.current!;
    let isDragging = false;
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

    const hitTest = (clientX:number, clientY:number) => {
      const rect = c.getBoundingClientRect();
      const x = (clientX - rect.left);
      const y = (clientY - rect.top);
      const hit = hitBoxesRef.current.find(b => x>=b.x && x<=b.x+b.w && y>=b.y && y<=b.y+b.h) || null;
      hoverRef.current = hit ? { x: hit.x, y: hit.y, cx: hit.cx, cy: hit.cy, R: hit.R, color: hit.color, icon: hit.icon, group: hit.group } : null;
      c.style.cursor = hit ? "pointer" : "default";
    };

    const onDown = (e: PointerEvent) => {
      isDragging = true;
      lastX = e.clientX;
      v = 0;
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
    };

    const onMove = (e: PointerEvent) => {
      hitTest(e.clientX, e.clientY);
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
    };

    const onClick = (e: MouseEvent) => {
      const rect = c.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const hit = hitBoxesRef.current.find(b => x>=b.x && x<=b.x+b.w && y>=b.y && y<=b.y+b.h);
      if (hit) setSelected(hit.group);
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
    c.addEventListener("click", onClick);
    c.addEventListener("wheel", onWheel, { passive: false });

    return () => {
      c.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      c.removeEventListener("click", onClick);
      c.removeEventListener("wheel", onWheel);
      if (raf) cancelAnimationFrame(raf);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoom, domain, rules]);

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

  const info = log.metadata;

  return (
    <div className="w-full h-full min-h-[560px] bg-[#0b0d12] text-white">
      <div className="max-w-6xl mx-auto p-4 space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-emerald-500/20 grid place-items-center">{ICONS.robot}</div>
            <div className="text-lg font-semibold">{info.botName}</div>
          </div>
          <div className="flex items-center gap-2 text-sm text-white/70">
            <div className="px-2 py-1 rounded-lg bg-white/5">Perf: {info.performance.toFixed(2)}%</div>
            <div className="px-2 py-1 rounded-lg bg-white/5">Trades: {info.totalTrades}</div>
            <div className="px-2 py-1 rounded-lg bg-white/5">Win: {info.winRate}%</div>
          </div>
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
          <button
            className="px-3 py-1 rounded-xl border border-white/20 text-white/80 hover:bg-white/10"
            onClick={jumpToNow}
          >
            Jump to Now
          </button>
        </div>

        {/* Chart area */}
        <div
          ref={containerRef}
          className="relative w-full h-[460px] rounded-2xl overflow-hidden ring-1 ring-white/10"
          style={{background: COLORS.bg}}
        >
          <canvas ref={canvasRef} className="absolute inset-0"/>
          <canvas ref={overlayRef} className="absolute inset-0 pointer-events-none"/>

          {/* Legend / filters */}
          <div className="absolute left-3 bottom-3 flex flex-wrap gap-2 max-w-[90%]">
            {(Object.keys(ACTIVITY_DEFS) as ActivityType[]).map(k => {
              const def = ACTIVITY_DEFS[k];
              const on = visibleTypes[k];
              return (
                <button
                  key={k}
                  onClick={() => setVisibleTypes(v => ({...v, [k]: !v[k]}))}
                  className={`px-2 py-1 rounded-xl text-xs border ${on?"bg-white/10 border-white/30":"border-white/10 text-white/50"}`}
                  title={def.description}
                >
                  {def.icon} {def.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Navigation hint */}
        <div className="text-xs text-white/50">
          Wheel: scroll through time (up = earlier, down = later). Shift+Wheel: change zoom tier. Drag: pan. Hover: glow. Click icons: details.
        </div>
      </div>

      {/* Side panel */}
      <SidePanel selected={selected} onClose={()=>setSelected(null)} />
    </div>
  );
}

// --------- Side Panel Component ---------

function SidePanel({ selected, onClose }: { selected: ActivityItem[] | null; onClose: ()=>void }) {
  return (
    <div className={`fixed top-0 right-0 h-full w-[420px] bg-[#12151c] shadow-2xl border-l border-white/10 transition-transform duration-300 ${selected?"translate-x-0":"translate-x-full"}`}>
      <div className="h-12 flex items-center justify-between px-4 border-b border-white/10">
        <div className="font-semibold">
          {selected ? (selected.length>1 ? `${selected.length} Activities` : ACTIVITY_DEFS[selected[0].type].label) : ""}
        </div>
        <button onClick={onClose} className="text-white/70 hover:text-white">{ICONS.close}</button>
      </div>
      <div className="p-3 space-y-3 overflow-y-auto h-[calc(100%-3rem)]">
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
              <div key={item.id} className="p-3 rounded-xl bg-white/5 border border-white/10">
                <div className="flex items-center gap-2">
                  <div className="text-xl">{def.icon}</div>
                  <div className="font-medium">{def.label}</div>
                  <div className="ml-auto text-xs text-white/60">{t.toUTCString()}</div>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-sm text-white/80">
                  {Object.entries(item.data).map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between gap-2">
                      <span className="text-white/50">{k}</span>
                      <span className="font-mono">{typeof v === 'number' ? v.toLocaleString() : String(v)}</span>
                    </div>
                  ))}
                </div>
                {item.data.reasoning && (
                  <div className="mt-2 text-sm text-white/80">{item.data.reasoning}</div>
                )}
              </div>
            );
          })}
      </div>
    </div>
  );
}
