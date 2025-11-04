"use client";
import React, {useEffect, useMemo, useRef, useState} from "react";
import { motion, AnimatePresence } from "framer-motion";
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

// =====================================================
// ActivityTimelineViewer — Trade37 Hardwired Palette
// Flat icons, mobile-friendly, NO dependency on app CSS vars.
// Colors match the screenshot/vibe: obsidian, carbon, ivory, brass, signal.
// =====================================================

// -----------------------------
// Trade37 palette (hardwired)
// -----------------------------
const VIBE = {
  obsidian: "#0B0B0C",   // page background
  carbon:   "#141416",   // card surface
  ivory:    "#EDEBE7",   // main text
  hair:     "rgba(237,235,231,0.16)", // hairline borders
  brass:    "#C1A87D",   // accent / primary (buttons)
  signal:   "#3CA6E0",   // equity line, data highlights
  ember:    "#D74A1F",   // negative
  lilac:    "#8B7CF2",   // thoughts
};

// -----------------------------
// Types
// -----------------------------
 type Priority = 1 | 2;
 export type ActivityType =
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

 interface ActivityDefinition { type: ActivityType; priority: Priority; color: string; label: string; description: string; }
 export interface ActivityItem { id: string; timestamp: string; type: ActivityType; priority: Priority; data: Record<string, any>; }
 export interface BalancePoint { timestamp: string; balance: number; }
 export interface ActivityLog {
  activities: ActivityItem[];
  balanceTimeseries: BalancePoint[];
  metadata: { botName: string; startingBalance: number; currentBalance: number; totalTrades: number; winRate: number; performance: number; };
 }

// -----------------------------
// Utility
// -----------------------------
const clamp = (n:number,a:number,b:number)=> Math.max(a, Math.min(b,n));
function niceTicks(min:number, max:number, target=5){
  const span=max-min; if(span<=0) return [] as number[];
  const step=Math.pow(10,Math.floor(Math.log10(span/target)));
  const err=(target*span)/(step*10);
  const steps= err>=7.5?10: err>=3?5: err>=1.5?2:1;
  const s=steps*step; const ticks:number[]=[]; const start=Math.ceil(min/s)*s; for(let v=start; v<=max; v+=s) ticks.push(v); return ticks;
}
function lerpAt(ms:number, xs:number[], ys:number[]){
  const n=xs.length; if(!n) return 0; if(ms<=xs[0]) return ys[0]; if(ms>=xs[n-1]) return ys[n-1];
  let lo=0, hi=n-1; while(hi-lo>1){ const mid=(lo+hi)>>1; if(xs[mid]<=ms) lo=mid; else hi=mid; }
  const t0=xs[lo], t1=xs[hi], v0=ys[lo], v1=ys[hi]; const a=(ms-t0)/(t1-t0); return v0+(v1-v0)*a;
}

// -----------------------------
// Zoom rules
// -----------------------------
const ZOOMS = ["1h","4h","1d","1w","All"] as const;
 type ZoomTier = typeof ZOOMS[number];
 const FUTURE_PAD_RATIO = 0.25;
 const ZOOM_RULES: Record<ZoomTier, { spanMs: number|"all"; bucketMs:number; iconPx:number; minSpacingPx:number; railGap:number; }>= {
  "1h":  { spanMs: 60*60*1000,        bucketMs: 60*1000,      iconPx:22, minSpacingPx:18, railGap:28 },
  "4h":  { spanMs: 4*60*60*1000,      bucketMs: 10*60*1000,   iconPx:20, minSpacingPx:18, railGap:28 },
  "1d":  { spanMs: 24*60*60*1000,     bucketMs: 60*60*1000,   iconPx:18, minSpacingPx:20, railGap:26 },
  "1w":  { spanMs: 7*24*60*60*1000,   bucketMs: 4*60*60*1000, iconPx:16, minSpacingPx:22, railGap:24 },
  "All": { spanMs: "all",            bucketMs: 24*60*60*1000,iconPx:14, minSpacingPx:28, railGap:24 },
 };

// -----------------------------
// Flat glyphs (canvas + React SVG)
// -----------------------------
 type GlyphId =
  | 'long' | 'short' | 'win' | 'loss'
  | 'strategy' | 'query' | 'wait' | 'note'
  | 'think' | 'plan' | 'close' | 'gear';

 function drawGlyph(ctx:CanvasRenderingContext2D, id:GlyphId, cx:number, cy:number, r:number, color:string){
  ctx.save();
  ctx.fillStyle = color;
  const s=r*0.9; // glyph box
  switch(id){
    case 'long': { // triangle up
      ctx.beginPath(); ctx.moveTo(cx, cy - s*0.8); ctx.lineTo(cx - s*0.7, cy + s*0.6); ctx.lineTo(cx + s*0.7, cy + s*0.6); ctx.closePath(); ctx.fill();
      break; }
    case 'short': { // triangle down
      ctx.beginPath(); ctx.moveTo(cx, cy + s*0.8); ctx.lineTo(cx - s*0.7, cy - s*0.6); ctx.lineTo(cx + s*0.7, cy - s*0.6); ctx.closePath(); ctx.fill();
      break; }
    case 'win': { // up arrow
      ctx.beginPath(); ctx.moveTo(cx, cy - s*0.8); ctx.lineTo(cx - s*0.5, cy - s*0.2); ctx.lineTo(cx - s*0.15, cy - s*0.2); ctx.lineTo(cx - s*0.15, cy + s*0.8); ctx.lineTo(cx + s*0.15, cy + s*0.8); ctx.lineTo(cx + s*0.15, cy - s*0.2); ctx.lineTo(cx + s*0.5, cy - s*0.2); ctx.closePath(); ctx.fill();
      break; }
    case 'loss': { // down arrow
      ctx.beginPath(); ctx.moveTo(cx, cy + s*0.8); ctx.lineTo(cx - s*0.5, cy + s*0.2); ctx.lineTo(cx - s*0.15, cy + s*0.2); ctx.lineTo(cx - s*0.15, cy - s*0.8); ctx.lineTo(cx + s*0.15, cy - s*0.8); ctx.lineTo(cx + s*0.15, cy + s*0.2); ctx.lineTo(cx + s*0.5, cy + s*0.2); ctx.closePath(); ctx.fill();
      break; }
    case 'strategy': { // wrench-ish
      ctx.beginPath();
      ctx.arc(cx - s*0.2, cy - s*0.2, s*0.35, Math.PI*0.1, Math.PI*1.2);
      ctx.lineTo(cx + s*0.5, cy + s*0.5);
      ctx.arc(cx + s*0.5, cy + s*0.5, s*0.12, 0, Math.PI*2);
      ctx.closePath(); ctx.fill();
      break; }
    case 'query': { // bar chart
      const w=s*0.25; ctx.fillRect(cx - s*0.5, cy + s*0.2, w, -s*0.6); ctx.fillRect(cx - w/2, cy + s*0.2, w, -s*0.35); ctx.fillRect(cx + s*0.25, cy + s*0.2, w, -s*0.8);
      break; }
    case 'wait': { // clock
      ctx.beginPath(); ctx.arc(cx, cy, s*0.75, 0, Math.PI*2); ctx.fill(); ctx.fillStyle = '#000000'; ctx.globalAlpha = 0.18; ctx.beginPath(); ctx.arc(cx, cy, s*0.55, 0, Math.PI*2); ctx.fill(); ctx.globalAlpha = 1; ctx.fillStyle = '#fff'; ctx.fillRect(cx-1, cy - s*0.35, 2, s*0.35); ctx.fillRect(cx, cy-1, s*0.28, 2); break; }
    case 'note': { // note with dog-ear
      const w=s*1.1, h=s*1.1; const x=cx-w/2, y=cy-h/2; ctx.fillRect(x, y, w, h); ctx.fillStyle='#000000'; ctx.globalAlpha=0.18; ctx.fillRect(x + w*0.1, y + h*0.25, w*0.8, 2); ctx.fillRect(x + w*0.1, y + h*0.5, w*0.6, 2); ctx.globalAlpha=1; break; }
    case 'think':
    case 'plan': { // speech bubble
      const w=s*1.15, h=s*0.8; const x=cx-w/2, y=cy-h/2; const r=6; ctx.beginPath(); ctx.moveTo(x+r, y); ctx.arcTo(x+w, y, x+w, y+h, r); ctx.arcTo(x+w, y+h, x, y+h, r); ctx.arcTo(x, y+h, x, y, r); ctx.arcTo(x, y, x+w, y, r); ctx.closePath(); ctx.fill(); ctx.beginPath(); ctx.moveTo(cx - w*0.2, y+h); ctx.lineTo(cx - w*0.05, y+h + h*0.25); ctx.lineTo(cx + w*0.05, y+h); ctx.closePath(); ctx.fill(); break; }
    case 'close': { // X
      const t=s*0.2; ctx.fillRect(cx-t, cy- s*0.8, 2*t, 2*t); break; }
    case 'gear': { // simple gear disc with teeth blocks
      ctx.beginPath(); ctx.arc(cx,cy,s*0.7,0,Math.PI*2); ctx.fill(); const teeth=6; const tr=s*0.95; const tw=s*0.12; for(let i=0;i<teeth;i++){ const a=(i/teeth)*Math.PI*2; const x=cx+Math.cos(a)*tr; const y=cy+Math.sin(a)*tr; ctx.save(); ctx.translate(x,y); ctx.rotate(a); ctx.fillRect(-tw/2,-tw/2,tw,tw); ctx.restore(); } break; }
  }
  ctx.restore();
 }

 // React SVG counterparts for panel & buttons
 const Svg = {
  Long:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M12 4l-9 16h18z" fill="currentColor"/></svg>),
  Short:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M12 20l9-16H3z" fill="currentColor"/></svg>),
  Up:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M11 21h2V8l4.5 4.5L19 11l-7-7-7 7 1.5 1.5L11 8z" fill="currentColor"/></svg>),
  Down:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M13 3h-2v13l-4.5-4.5L5 13l7 7 7-7-1.5-1.5L13 16z" fill="currentColor"/></svg>),
  Wrench:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M14.7 6.3a5 5 0 01-6.4 6.4L3 18l3 3 5.3-5.3a5 5 0 006.4-6.4l-3-3z" fill="currentColor"/></svg>),
  Bars:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M4 20h4V8H4v12zm6 0h4V12h-4v8zm6 0h4V4h-4v16z" fill="currentColor"/></svg>),
  Clock:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M12 2a10 10 0 100 20 10 10 0 000-20zm1 10V6h-2v8h6v-2h-4z" fill="currentColor"/></svg>),
  Note:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M6 2h9l5 5v13a2 2 0 01-2 2H6a2 2 0 01-2-2V4a2 2 0 012-2zm8 1.5V8h4.5L14 3.5z" fill="currentColor"/></svg>),
  Bubble:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M4 4h16v12H8l-4 4V4z" fill="currentColor"/></svg>),
  X:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2"/></svg>),
  Gear:(p:any)=> (<svg viewBox="0 0 24 24" aria-hidden className={p.className}><path d="M12 8a4 4 0 100 8 4 4 0 000-8zm9 4l-2.2.6a7.9 7.9 0 01-.9 2.1l1.3 1.9-2 2-1.9-1.3a7.9 7.9 0 01-2.1.9L12 21l-.6-2.2a7.9 7.9 0 01-2.1-.9L7.4 19.2l-2-2 1.3-1.9a7.9 7.9 0 01-.9-2.1L3 12l2.2-.6c.2-.7.5-1.4.9-2.1L4.8 7.4l2-2 1.9 1.3c.7-.4 1.4-.7 2.1-.9L12 3l.6 2.2c.7.2 1.4.5 2.1.9L16.6 5.4l2 2-1.3 1.9c.4.7.7 1.4.9 2.1L21 12z" fill="currentColor"/></svg>),
 } as const;

// -----------------------------
// Activity definitions (hardwired colors)
// -----------------------------
const ACTIVITY_DEFS: Record<ActivityType, ActivityDefinition> = {
  trade_entry_long:  { type:"trade_entry_long",  priority:1, color:VIBE.signal, label:"Long Entry", description:"Opened a long position." },
  trade_entry_short: { type:"trade_entry_short", priority:1, color:VIBE.ember,  label:"Short Entry", description:"Opened a short position." },
  trade_win:         { type:"trade_win",         priority:1, color:VIBE.signal, label:"Trade Win",   description:"Closed with profit." },
  trade_loss:        { type:"trade_loss",        priority:1, color:VIBE.ember,  label:"Trade Loss",  description:"Closed with loss." },
  strategy_updated:  { type:"strategy_updated",  priority:1, color:VIBE.brass,  label:"Strategy Update", description:"Strategy modified." },
  market_query:      { type:"market_query",      priority:2, color:VIBE.signal, label:"Data Query",   description:"Fetched market data." },
  agent_wait:        { type:"agent_wait",        priority:2, color:VIBE.hair,   label:"Waiting",      description:"Agent paused." },
  observation_recorded: { type:"observation_recorded", priority:2, color:VIBE.hair, label:"Observation", description:"Recorded observation." },
  analysis:          { type:"analysis",          priority:2, color:VIBE.lilac,  label:"Agent Thoughts", description:"Analysis." },
  reasoning:         { type:"reasoning",         priority:2, color:VIBE.lilac,  label:"Agent Thoughts", description:"Reasoning." },
  plan:              { type:"plan",              priority:2, color:VIBE.lilac,  label:"Agent Thoughts", description:"Plan." },
};

function glyphIdFor(t: ActivityType): GlyphId{
  switch(t){
    case 'trade_entry_long': return 'long';
    case 'trade_entry_short': return 'short';
    case 'trade_win': return 'win';
    case 'trade_loss': return 'loss';
    case 'strategy_updated': return 'strategy';
    case 'market_query': return 'query';
    case 'agent_wait': return 'wait';
    case 'observation_recorded': return 'note';
    case 'analysis': return 'think';
    case 'reasoning': return 'think';
    case 'plan': return 'plan';
  }
}

// -----------------------------
// Component
// -----------------------------
export interface ActivityTimelineViewerProps {
  configId: string;
  title?: string;
  initialZoom?: ZoomTier;
}

export default function Timeline({ configId, title, initialZoom = '4h' }: ActivityTimelineViewerProps){
  // No theme lookup: fixed palette
  const theme = VIBE;

  const [log, setLog] = useState<ActivityLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<any>(null);
  const [strategy, setStrategy] = useState<string | null>(null);
  const [showStrategy, setShowStrategy] = useState(false);
  const [zoom, setZoom] = useState<ZoomTier>(initialZoom);
  const [domain, setDomain] = useState(()=>({left: Date.now()-24*60*60*1000, right: Date.now()}));
  const [selected, setSelected] = useState<ActivityItem[] | null>(null);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [visibleTypes, setVisibleTypes] = useState<Record<ActivityType, boolean>>(()=>{
    const o:Record<ActivityType,boolean> = (Object.keys(ACTIVITY_DEFS) as ActivityType[]).reduce((acc:any,k)=>{acc[k]=true; return acc;},{} as any);
    return o;
  });

  // Get session for auth
  useEffect(() => {
    const supabase = createClientComponentClient();
    const getSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setSession(session);
    };
    getSession();
  }, []);

  // Fetch activity data from API
  useEffect(() => {
    if (!configId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Build headers - include auth if session exists
        const headers = session?.access_token
          ? { 'Authorization': `Bearer ${session.access_token}` }
          : {};

        // Fetch all endpoints in parallel
        const [activitiesRes, balanceSeriesRes, metadataRes, strategyRes] = await Promise.all([
          fetch(`/api/v2/activities/${configId}`, { headers }),
          fetch(`/api/v2/activities/${configId}/balance-series`, { headers }),
          fetch(`/api/v2/activities/${configId}/metadata`, { headers }),
          fetch(`/api/v2/configs/${configId}/strategy`, { headers }).catch(() => null)
        ]);

        if (!activitiesRes.ok || !balanceSeriesRes.ok || !metadataRes.ok) {
          throw new Error('Failed to fetch activity data');
        }

        const [activities, balanceSeries, metadata, strategyData] = await Promise.all([
          activitiesRes.json(),
          balanceSeriesRes.json(),
          metadataRes.json(),
          strategyRes?.ok ? strategyRes.json() : null
        ]);

        setLog({
          activities: activities.activities || [],
          balanceTimeseries: balanceSeries.balance_series || [],
          metadata: {
            botName: metadata.bot_name || 'Unknown Bot',
            startingBalance: metadata.starting_balance || 0,
            currentBalance: metadata.current_balance || 0,
            totalTrades: metadata.total_trades || 0,
            winRate: metadata.win_rate || 0,
            performance: metadata.performance || 0
          }
        });

        if (strategyData?.strategy) {
          setStrategy(strategyData.strategy);
        }

        setLoading(false);
      } catch (err) {
        console.error('Error fetching activity data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setLoading(false);
      }
    };

    fetchData();
  }, [configId, session]);

  // ---- Sizing (mobile-friendly)
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const [size, setSize] = useState({w:1200,h:480});
  useEffect(()=>{
    const obs=new ResizeObserver(()=>{ const el=containerRef.current; if(!el) return; setSize({w: el.clientWidth, h: el.clientHeight}); });
    if(containerRef.current) obs.observe(containerRef.current);
    return ()=>obs.disconnect();
  },[]);

  // ---- Derived series
  const seriesMs = useMemo(()=> log?.balanceTimeseries?.map(p=> new Date(p.timestamp).getTime()) ?? [], [log]);
  const seriesVal = useMemo(()=> log?.balanceTimeseries?.map(p=> p.balance) ?? [], [log]);
  const dataFirst = useMemo(()=> seriesMs[0] ?? Date.now()-24*60*60*1000, [seriesMs]);
  const dataLast  = useMemo(()=> seriesMs[seriesMs.length-1] ?? Date.now(), [seriesMs]);
  const rules = ZOOM_RULES[zoom];
  const rightBound = useMemo(()=> { const span=(dataLast - dataFirst); const buffer=Math.round(span*FUTURE_PAD_RATIO); return dataLast + buffer; }, [dataFirst, dataLast]);

  // initialize domain on zoom change
  useEffect(()=>{
    if(rules.spanMs === "all") return setDomain({left:dataFirst, right:rightBound});
    const span = rules.spanMs as number; const now = Date.now();
    let right = Math.min(now, rightBound); let left = right - span;
    if(left < dataFirst){ left = dataFirst; right = Math.min(left+span, rightBound); }
    setDomain({left,right});
  },[zoom, rules, dataFirst, rightBound]);

  // ---- Slice series into domain (+guards for continuity)
  const inDomainSeries = useMemo(()=>{
    if(!log?.balanceTimeseries?.length) return [] as BalancePoint[];
    const {left,right}=domain; const src=log.balanceTimeseries; const out:BalancePoint[]=[];
    for(let i=0;i<src.length;i++){
      const t=new Date(src[i].timestamp).getTime();
      if(t>=left && t<=right) out.push(src[i]);
      else if(i<src.length-1){ const tNext=new Date(src[i+1].timestamp).getTime(); if(tNext>=left && tNext<=right && out.length===0) out.push(src[i]); }
    }
    if(out.length===0 && src.length>=2) return [src[0], src[src.length-1]]; return out.length?out:src;
  },[log, domain]);

  // ---- Scales
  const padL=64, padR=16, padT=20, padB=32; const chartW=Math.max(10, size.w - padL - padR); const chartH=Math.max(10, size.h - padT - padB);
  const xScale = (ms:number)=> padL + ((ms-domain.left)/(domain.right-domain.left))*chartW;
  const yExtent = useMemo(()=>{
    let min=Infinity, max=-Infinity; for(const p of inDomainSeries){ min=Math.min(min,p.balance); max=Math.max(max,p.balance); }
    if(!isFinite(min)||!isFinite(max)) { min=0; max=100; }
    const span=max-min; const minRange=120; if(span<minRange){ const c=(min+max)/2; return {min:c-minRange/2, max:c+minRange/2}; }
    const pad=span*0.1; return {min:min-pad, max:max+pad};
  },[inDomainSeries]);
  const yScale = (v:number)=> padT + chartH - ((v-yExtent.min)/(yExtent.max-yExtent.min))*chartH;

  // ---- Bucket activities
  const bucketed = useMemo(()=>{
    if(!log?.activities) return [] as {bucketTs:number; items:ActivityItem[]; rep:ActivityItem}[];
    const ms = rules.bucketMs; const {left,right}=domain; const pad=(right-left)*0.25; const acts = log.activities.filter(a=>{
      const t=new Date(a.timestamp).getTime(); return t>=left-pad && t<=right+pad && visibleTypes[a.type];
    });
    const map = new Map<string, ActivityItem[]>();
    for(const a of acts){ const t=new Date(a.timestamp).getTime(); const b=Math.floor(t/ms)*ms; const key = a.priority===1? `${b}:${a.id}` : `${b}:${a.type}`; const arr = map.get(key) || []; arr.push(a); map.set(key, arr); }
    return Array.from(map.entries()).map(([k,items])=>{ const bucketTs=parseInt(k.split(":")[0]); items.sort((a,b)=> new Date(a.timestamp).getTime()-new Date(b.timestamp).getTime()); const rep= items.find(x=>x.priority===1) || items[0]; return {bucketTs, items, rep}; }).sort((a,b)=> a.bucketTs-b.bucketTs);
  },[log, rules, domain, visibleTypes]);

  // ---- Canvas draw
  const hitBoxesRef = useRef<{x:number;y:number;w:number;h:number; cx:number; cy:number; R:number; color:string; glyph:GlyphId; group: ActivityItem[]}[]>([]);
  const hoverRef = useRef<{cx:number; cy:number; R:number; color:string; glyph:GlyphId} | null>(null);

  useEffect(()=>{
    const c=canvasRef.current, o=overlayRef.current; if(!c||!o) return; const dpr=window.devicePixelRatio||1;
    for(const el of [c,o]){ el.width=Math.floor(size.w*dpr); el.height=Math.floor(size.h*dpr); el.style.width=`${size.w}px`; el.style.height=`${size.h}px`; }
    const ctx=c.getContext("2d")!; const octx=o.getContext("2d")!; ctx.setTransform(dpr,0,0,dpr,0,0); octx.setTransform(dpr,0,0,dpr,0,0);

    // Surface
    ctx.fillStyle = theme.carbon; ctx.fillRect(0,0,size.w,size.h);

    // Grid
    ctx.strokeStyle = VIBE.hair; ctx.globalAlpha = 1; ctx.lineWidth=1; ctx.beginPath();
    for(let i=0;i<=6;i++){ const x=padL+(chartW/6)*i; ctx.moveTo(x,padT); ctx.lineTo(x,padT+chartH);} const ys=niceTicks(yExtent.min,yExtent.max,5); for(const v of ys){ const y=Math.round(yScale(v))+0.5; ctx.moveTo(padL,y); ctx.lineTo(padL+chartW,y);} ctx.stroke();

    // Y labels
    ctx.fillStyle = theme.ivory; ctx.font = "12px var(--font-sans, ui-sans-serif)"; ctx.textAlign="right"; ctx.textBaseline="middle";
    for(const v of ys){ const y=yScale(v); ctx.fillText(`$${Math.round(v).toLocaleString()}`, padL-10, y); }

    // Equity line
    ctx.save(); ctx.beginPath(); let first=true; for(const p of inDomainSeries){ const x=xScale(new Date(p.timestamp).getTime()); const y=yScale(p.balance); if(first){ctx.moveTo(x,y); first=false;} else ctx.lineTo(x,y);} ctx.shadowColor=`${theme.signal}`; ctx.shadowBlur=10; ctx.strokeStyle=theme.signal; ctx.lineWidth=2; ctx.stroke(); ctx.restore();

    // X labels
    ctx.textAlign="center"; ctx.textBaseline="top"; const spanMs=domain.right-domain.left; const xTicks=[domain.left, domain.left+spanMs/2, domain.right];
    for(const t of xTicks){ const d=new Date(t); const label= spanMs<=24*60*60*1000 ? d.toUTCString().slice(17,22)+" UTC" : d.toUTCString().slice(5,16); ctx.fillText(label, xScale(t), padT+chartH+8); }

    // Activities
    hitBoxesRef.current = [];
    const colW = rules.minSpacingPx; const cols=Math.ceil(chartW/colW); const railHeights=[rules.railGap, rules.railGap*2, rules.railGap*3]; const occupancy=new Array(cols).fill(0);
    for(const g of bucketed){ const px=xScale(g.bucketTs); if(px<padL||px>padL+chartW) continue; const col=Math.floor((px-padL)/colW); let row=occupancy[col]||0; if(row>2) row=2; occupancy[col]=row+1;
      const anchorBal = lerpAt(g.bucketTs, seriesMs, seriesVal); let ay=yScale(anchorBal); ay=clamp(ay,padT,padT+chartH);
      const upwards = ay - padT > padB + 80; const offset=railHeights[row]; const py = upwards ? (ay - offset) : (ay + offset);
      const def = ACTIVITY_DEFS[g.rep.type]; const R=ZOOM_RULES[zoom].iconPx; const stem=`${def.color}`;
      // stem
      ctx.strokeStyle = stem; ctx.globalAlpha=0.55; ctx.lineWidth=2; ctx.beginPath(); ctx.moveTo(px,ay); const ctrlY = upwards? ay-offset*0.6 : ay+offset*0.6; ctx.bezierCurveTo(px,ctrlY,px,ctrlY,px,py); ctx.stroke(); ctx.globalAlpha=1;
      // anchor dot
      ctx.beginPath(); ctx.fillStyle=def.color; ctx.arc(px, ay, 3,0,Math.PI*2); ctx.fill();
      // icon disc
      ctx.beginPath(); ctx.fillStyle = theme.obsidian; ctx.globalAlpha=0.9; ctx.arc(px,py,R,0,Math.PI*2); ctx.fill(); ctx.globalAlpha=1;
      // ring
      ctx.beginPath(); ctx.strokeStyle = VIBE.hair; ctx.lineWidth=1.25; ctx.arc(px,py,R-0.5,0,Math.PI*2); ctx.stroke();
      // glyph (solid flat)
      drawGlyph(ctx, glyphIdFor(g.rep.type), px, py, R*0.72, def.color);
      // badge
      if(g.items.length>1){ const r=8, bx=px+R-4, by=py-R+4; ctx.beginPath(); ctx.fillStyle=def.color; ctx.arc(bx,by,r,0,Math.PI*2); ctx.fill(); ctx.fillStyle=theme.obsidian; ctx.font="10px ui-sans-serif"; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(String(g.items.length), bx, by+0.5); }
      // hitbox
      hitBoxesRef.current.push({x:px-R,y:py-R,w:R*2,h:R*2,cx:px,cy:py,R,color:def.color,glyph:glyphIdFor(g.rep.type),group:g.items});
    }

    // clear overlay
    octx.clearRect(0,0,size.w,size.h);
  },[size, domain, inDomainSeries, bucketed, yExtent, zoom, seriesMs, seriesVal, theme]);

  // ---- Overlay (hover + now pulse)
  useEffect(()=>{
    const o=overlayRef.current; if(!o) return; const ctx=o.getContext("2d")!; let raf:number|undefined;
    const draw=(t:number)=>{
      const dpr=window.devicePixelRatio||1; ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,o.width/dpr,o.height/dpr);
      const h=hoverRef.current; if(h){ ctx.save(); ctx.beginPath(); ctx.arc(h.cx,h.cy,h.R+6,0,Math.PI*2); ctx.fillStyle=VIBE.hair; ctx.fill(); drawGlyph(ctx,h.glyph,h.cx,h.cy,h.R*0.72,h.color); ctx.restore(); }
      // now pulse
      const latestMs = dataLast; if(latestMs>=domain.left && latestMs<=domain.right){
        const nowX = xScale(latestMs); const nowY = yScale(lerpAt(latestMs, seriesMs, seriesVal));
        const tt=(t/1000)%1.6; const r1=4+tt*10, a1=.35-tt*.25; const r2=4+((tt+.6)%1.6)*10, a2=.28-((tt+.6)%1.6)*.2;
        ctx.save(); ctx.beginPath(); ctx.arc(nowX,nowY,r1,0,Math.PI*2); ctx.strokeStyle=theme.signal; ctx.globalAlpha=Math.max(0,a1); ctx.lineWidth=2.5; ctx.stroke();
        ctx.beginPath(); ctx.arc(nowX,nowY,r2,0,Math.PI*2); ctx.globalAlpha=Math.max(0,a2); ctx.lineWidth=2.5; ctx.stroke(); ctx.globalAlpha=1;
        ctx.shadowColor=theme.signal; ctx.shadowBlur=8; ctx.beginPath(); ctx.fillStyle=theme.signal; ctx.arc(nowX,nowY,4,0,Math.PI*2); ctx.fill(); ctx.restore();
      }
      raf=requestAnimationFrame(draw);
    };
    raf=requestAnimationFrame(draw); return ()=>{ if(raf) cancelAnimationFrame(raf); };
  },[domain, dataLast, seriesMs, seriesVal, theme]);

  // ---- Interaction
  const domainRef = useRef(domain); const rulesRef = useRef(rules); const dataFirstRef=useRef(dataFirst); const rightBoundRef=useRef(rightBound);
  useEffect(()=>{ domainRef.current=domain; rulesRef.current=rules; dataFirstRef.current=dataFirst; rightBoundRef.current=rightBound; },[domain,rules,dataFirst,rightBound]);
  useEffect(()=>{
    const c=canvasRef.current; if(!c) return; let isDragging=false; let dragStartX=0; let lastX=0; let v=0; let raf:number|undefined;
    const clampDom=(left:number,right:number)=>{ if(rulesRef.current.spanMs==="all") return {left:dataFirstRef.current,right:rightBoundRef.current}; const span=right-left; const maxR=rightBoundRef.current; const minL=dataFirstRef.current; if(right>maxR){ right=maxR; left=right-span; } if(left<minL){ left=minL; right=Math.min(left+span,maxR); } return {left,right}; };
    const span=()=> (domainRef.current.right - domainRef.current.left);
    const applyPan=(dtMs:number)=>{ const left=domainRef.current.left + dtMs; const right=domainRef.current.right + dtMs; setDomain(clampDom(left,right)); };

    const onDown=(e:PointerEvent)=>{ isDragging=true; dragStartX=e.clientX; lastX=e.clientX; v=0; (e.target as HTMLElement).setPointerCapture(e.pointerId); };
    const onMove=(e:PointerEvent)=>{ const rect=c.getBoundingClientRect(); const x=(e.clientX-rect.left); const y=(e.clientY-rect.top); const hit=hitBoxesRef.current.find(b=> x>=b.x && x<=b.x+b.w && y>=b.y && y<=b.y+b.h); (c as any).style.cursor = hit? "pointer" : "default"; hoverRef.current = hit? {cx:hit.cx, cy:hit.cy, R:hit.R, color:hit.color, glyph:hit.glyph}: null; if(!isDragging) return; const dx=e.clientX - lastX; lastX=e.clientX; v=dx; const msPerPx = span() / Math.max(1, (c.clientWidth) - padL - padR); applyPan(-dx*msPerPx); };
    const onUp=(e:PointerEvent)=>{ if(!isDragging) return; isDragging=false; (e.target as HTMLElement).releasePointerCapture(e.pointerId); const dragDist=Math.abs(e.clientX-dragStartX); if(dragDist<5){ const rect=c.getBoundingClientRect(); const x=e.clientX-rect.left; const y=e.clientY-rect.top; const hit=hitBoxesRef.current.find(b=> x>=b.x && x<=b.x+b.w && y>=b.y && y<=b.y+b.h); if(hit) setSelected(hit.group); }
      else{ let vel=v; const decay=.92; const step=()=>{ if(Math.abs(vel)<.2){ if(raf) cancelAnimationFrame(raf); raf=undefined; return; } const msPerPx = span() / Math.max(1,(c.clientWidth)-padL-padR); applyPan(-vel*msPerPx); vel*=decay; raf=requestAnimationFrame(step); }; if(!raf) raf=requestAnimationFrame(step); }
    };
    const onWheel=(e:WheelEvent)=>{ e.preventDefault(); if(rulesRef.current.spanMs==="all") return; if(e.shiftKey){ const idx=ZOOMS.indexOf(zoom); const next = e.deltaY < 0 ? clamp(idx-1,0,ZOOMS.length-1) : clamp(idx+1,0,ZOOMS.length-1); if(next!==idx) setZoom(ZOOMS[next]); return; } const step=(domainRef.current.right-domainRef.current.left)*0.15; const dir=e.deltaY<0? -1: 1; applyPan(dir*step); };

    c.addEventListener("pointerdown", onDown); window.addEventListener("pointermove", onMove); window.addEventListener("pointerup", onUp); c.addEventListener("wheel", onWheel, {passive:false});
    return ()=>{ c.removeEventListener("pointerdown", onDown); window.removeEventListener("pointermove", onMove); window.removeEventListener("pointerup", onUp); c.removeEventListener("wheel", onWheel); if(raf) cancelAnimationFrame(raf); };
  },[zoom]);

  // ---- Helpers
  const jumpToNow = ()=>{ if(rules.spanMs==="all") return setDomain({left:dataFirst,right:rightBound}); const span = rules.spanMs as number; const now=Date.now(); let right=Math.min(now,rightBound); let left=right-span; if(left<dataFirst){ left=dataFirst; right=Math.min(left+span,rightBound);} setDomain({left,right}); };

  const info = log?.metadata; const isEmpty = !log || (log.activities?.length ?? 0)===0 || (log.balanceTimeseries?.length ?? 0)===0;

  // ---- Filter list UI (shared)
  function FiltersList(){
    const entries = (Object.keys(ACTIVITY_DEFS) as ActivityType[]).map(k=>{
      const def=ACTIVITY_DEFS[k]; const on=visibleTypes[k]; const glyph=glyphIdFor(k);
      const Icon = (():React.FC<any>=>{
        switch(glyph){
          case 'long': return (p:any)=> <Svg.Long {...p}/>;
          case 'short': return (p:any)=> <Svg.Short {...p}/>;
          case 'win': return (p:any)=> <Svg.Up {...p}/>;
          case 'loss': return (p:any)=> <Svg.Down {...p}/>;
          case 'strategy': return (p:any)=> <Svg.Wrench {...p}/>;
          case 'query': return (p:any)=> <Svg.Bars {...p}/>;
          case 'wait': return (p:any)=> <Svg.Clock {...p}/>;
          case 'note': return (p:any)=> <Svg.Note {...p}/>;
          default: return (p:any)=> <Svg.Bubble {...p}/>;
        }
      })();
      return (
        <button key={k}
          onClick={()=> setVisibleTypes(prev=>({...prev,[k]:!on}))}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${on? '' : 'hover:bg-white/5'}`}
          style={{ color: on? theme.ivory : 'rgba(237,235,231,0.6)', borderColor: theme.hair, backgroundColor: on? 'rgba(255,255,255,0.04)' : 'transparent' }}
        >
          <Icon className="w-4 h-4" style={{color: def.color}}/>
          <span className="text-sm">{def.label}</span>
        </button>
      );
    });
    return <div className="flex flex-col gap-2">{entries}</div>;
  }

  // Loading state
  if (loading && !log) {
    return (
      <div className="w-full h-screen flex items-center justify-center" style={{ backgroundColor: theme.obsidian, color: theme.ivory }}>
        <div className="text-center">
          <div className="text-xl mb-2">Loading Timeline...</div>
          <div className="text-sm" style={{ color: 'rgba(237,235,231,0.6)' }}>Fetching activity data</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="w-full h-screen flex items-center justify-center" style={{ backgroundColor: theme.obsidian, color: theme.ivory }}>
        <div className="max-w-md mx-auto text-center">
          <div className="text-xl mb-2" style={{ color: theme.ember }}>Failed to Load Timeline</div>
          <div className="text-sm" style={{ color: 'rgba(237,235,231,0.6)' }}>{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full min-h-[520px] sm:min-h-[600px] h-[70vh] sm:h-[78vh] font-sans" style={{ backgroundColor: theme.obsidian, color: theme.ivory }}>
      {/* HEADER */}
      <section className="max-w-7xl mx-auto px-4 sm:px-5 pt-5 pb-4">
        <div className="rounded-xl border p-4 sm:p-6" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3 sm:gap-6">
            <div className="flex-1 min-w-0">
              <h1 className="text-xl sm:text-2xl md:text-3xl leading-tight tracking-tight">
                {title ?? info?.botName ?? "Activity Timeline"}
              </h1>
              <p className="font-mono text-xs sm:text-sm" style={{ color: 'rgba(237,235,231,0.7)' }}>
                ARENA STATUS • {new Date().toUTCString().slice(5,16).toUpperCase()}
              </p>
            </div>
            <div className="flex items-center flex-wrap gap-2">
              {/* View Configuration (to the LEFT of timeframe buttons) */}
              {strategy && (
                <button
                  onClick={()=> setShowStrategy(true)}
                  className="inline-flex items-center gap-2 px-3 py-1.5 text-xs sm:text-sm rounded-lg border"
                  style={{ borderColor: theme.hair, backgroundColor: 'transparent', color: theme.ivory }}
                >
                  <Svg.Gear className="w-4 h-4"/>
                  <span>View Configuration</span>
                </button>
              )}
              <div className="inline-flex rounded-lg overflow-hidden border" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
                {ZOOMS.map(z=> (
                  <button key={z} onClick={()=>setZoom(z)}
                    className={`px-3 py-1.5 text-xs sm:text-sm transition-colors`}
                    style={ z===zoom ? { backgroundColor: theme.brass, color: '#0B0B0C' } : { color: theme.ivory } }
                  >
                    {z}
                  </button>
                ))}
              </div>
              <button onClick={jumpToNow} className="px-3 py-1.5 text-xs sm:text-sm rounded-lg border"
                style={{ borderColor: theme.hair, color: theme.ivory }}
              >
                Jump to Now
              </button>
              {/* Mobile Filters toggle */}
              <button onClick={()=> setMobileFiltersOpen(true)} className="md:hidden px-3 py-1.5 text-xs sm:text-sm rounded-lg border" style={{ borderColor: theme.hair }}>
                Filters
              </button>
            </div>
          </div>

          {/* KPI Row */}
          {info && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 sm:gap-3 mt-4">
              {[
                {k:"Balance", v:`$${Math.round(info.currentBalance).toLocaleString()}`},
                {k:"P/L", v:`${(info.currentBalance-info.startingBalance>=0?'+':'')}${Math.round(info.currentBalance-info.startingBalance).toLocaleString()}`},
                {k:"Trades", v:String(info.totalTrades)},
                {k:"Win Rate", v:`${Math.round(info.winRate)}%`},
                {k:"Perf", v:`${info.performance.toFixed?.(2) ?? info.performance}%`},
              ].map((d,i)=> (
                <div key={i} className="border rounded-lg px-3 py-2" style={{ borderColor: theme.hair }}>
                  <div className="text-[10px] uppercase tracking-[0.18em]" style={{ color: 'rgba(237,235,231,0.6)' }}>{d.k}</div>
                  <div className="text-lg sm:text-xl leading-snug">{d.v}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* BODY */}
      <section className="max-w-7xl mx-auto px-4 sm:px-5">
        <div className="grid grid-cols-12 gap-4 sm:gap-5 items-stretch">
          {/* LEFT – Filters */}
          <aside className="hidden md:block col-span-3">
            <div className="rounded-xl border p-4" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
              <div className="text-sm" style={{ color: 'rgba(237,235,231,0.7)' }}>Activity Types</div>
              <FiltersList/>
              <button onClick={()=>{ const allOn=Object.values(visibleTypes).every(v=>v); const next: any={}; (Object.keys(ACTIVITY_DEFS) as ActivityType[]).forEach(k=> next[k]=!allOn); setVisibleTypes(next); }}
                className="w-full mt-3 text-xs px-3 py-1.5 rounded-lg border"
                style={{ borderColor: theme.hair, color: 'rgba(237,235,231,0.85)' }}
              >
                Toggle All
              </button>
              <div className="font-mono text-[11px] mt-3" style={{ color: 'rgba(237,235,231,0.6)' }}>Wheel = scroll • Shift+Wheel = zoom • Drag = pan</div>
            </div>
          </aside>

          {/* RIGHT – Chart */}
          <div className="col-span-12 md:col-span-9 min-h-[360px] sm:min-h-[420px]">
            <div className="rounded-xl border h-full relative overflow-hidden" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
              <div ref={containerRef} className="absolute inset-0">
                <canvas ref={canvasRef} className="absolute inset-0 w-full h-full"/>
                <canvas ref={overlayRef} className="absolute inset-0 w-full h-full pointer-events-none"/>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* MOBILE FILTERS SHEET */}
      <AnimatePresence>
        {mobileFiltersOpen && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="fixed inset-0 z-40">
            <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.5)' }} onClick={()=> setMobileFiltersOpen(false)} />
            <motion.div initial={{y: 480}} animate={{y:0}} exit={{y:480}} transition={{type:'tween', duration:.25}} className="absolute bottom-0 left-0 right-0 rounded-t-2xl border p-4" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium">Filters</div>
                <button onClick={()=> setMobileFiltersOpen(false)} className="p-2 rounded-md" style={{ backgroundColor:'rgba(255,255,255,0.06)' }}>
                  <Svg.X className="w-4 h-4"/>
                </button>
              </div>
              <FiltersList/>
              <button onClick={()=>{ const allOn=Object.values(visibleTypes).every(v=>v); const next: any={}; (Object.keys(ACTIVITY_DEFS) as ActivityType[]).forEach(k=> next[k]=!allOn); setVisibleTypes(next); }}
                className="w-full mt-3 text-xs px-3 py-2 rounded-lg border"
                style={{ borderColor: theme.hair, color:'rgba(237,235,231,0.9)' }}
              >
                Toggle All
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* SIDE PANEL – Activity details */}
      <AnimatePresence>
        {selected && (
          <motion.aside initial={{x: 560, opacity:0}} animate={{x:0, opacity:1}} exit={{x:560, opacity:0}} transition={{type:"tween", duration:.25}} className="fixed top-0 right-0 h-full w-full sm:w-[560px] z-40">
            <div className="absolute inset-0" style={{ background:'rgba(0,0,0,0.4)' }} onClick={()=>setSelected(null)} />
            <div className="relative ml-auto h-full w-full sm:w-[560px] rounded-l-xl border overflow-hidden" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
              <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom:`1px solid ${theme.hair}` }}>
                <div className="text-lg font-medium">Activity Details</div>
                <button onClick={()=>setSelected(null)} style={{ color:'rgba(237,235,231,0.8)' }}>
                  <Svg.X className="w-5 h-5"/>
                </button>
              </div>
              <div className="p-5 space-y-3 overflow-y-auto h-[calc(100%-64px)]">
                {selected.map((a)=>{
                  const def=ACTIVITY_DEFS[a.type];
                  const Glyph = (()=>{ const g=glyphIdFor(a.type); switch(g){ case 'long': return Svg.Long; case 'short': return Svg.Short; case 'win': return Svg.Up; case 'loss': return Svg.Down; case 'strategy': return Svg.Wrench; case 'query': return Svg.Bars; case 'wait': return Svg.Clock; case 'note': return Svg.Note; default: return Svg.Bubble; } })();
                  return (
                    <div key={a.id} className="border rounded-lg p-4" style={{ borderColor: theme.hair }}>
                      <div className="flex items-center gap-2 text-sm">
                        <Glyph className="w-4 h-4" style={{color:def.color}}/>
                        <span className="font-semibold">{def.label}</span>
                        <span className="font-mono text-[11px]" style={{ color:'rgba(237,235,231,0.6)' }}>{new Date(a.timestamp).toLocaleString()}</span>
                      </div>
                      <div className="text-sm mt-2" style={{ color:'rgba(237,235,231,0.85)' }}>{def.description}</div>
                      {a.data && (
                        <pre className="mt-3 text-[12px] leading-relaxed font-mono whitespace-pre-wrap" style={{ color:'rgba(237,235,231,0.85)' }}>{JSON.stringify(a.data, null, 2)}</pre>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* EMPTY STATE */}
      <AnimatePresence>
        {isEmpty && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="max-w-3xl mx-auto mt-10">
            <div className="rounded-xl border p-8 text-center" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
              <div className="text-2xl mb-2">Timeline</div>
              <div className="text-2xl">No Activity Yet</div>
              <p className="mt-2" style={{ color:'rgba(237,235,231,0.7)' }}>When trades begin, events will plot here.</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* STRATEGY MODAL */}
      <AnimatePresence>
        {showStrategy && strategy && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.6)' }} onClick={()=>setShowStrategy(false)} />
            <motion.div initial={{scale:0.95}} animate={{scale:1}} exit={{scale:0.95}} className="relative w-full max-w-3xl max-h-[80vh] rounded-xl border overflow-hidden" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
              <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom:`1px solid ${theme.hair}` }}>
                <div className="text-xl font-semibold">Agent Configuration</div>
                <button onClick={()=>setShowStrategy(false)} style={{ color:'rgba(237,235,231,0.8)' }}>
                  <Svg.X className="w-6 h-6"/>
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[calc(80vh-5rem)]">
                <pre className="whitespace-pre-wrap text-sm leading-relaxed font-mono" style={{ color:'rgba(237,235,231,0.9)' }}>{strategy}</pre>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
