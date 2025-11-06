'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import BalanceChartRecharts from './BalanceChartRecharts';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import type { Session } from '@supabase/supabase-js';

// =====================================================
// ActivityTimelineViewer — Trade37 Hardwired Palette
// Flat icons, mobile-friendly, NO dependency on app CSS vars.
// Colors match the screenshot/vibe: obsidian, carbon, ivory, brass, signal.
// =====================================================

// Trade37 palette (hardwired)
const VIBE = {
  obsidian: '#0B0B0C',   // page background
  carbon: '#141416',     // card surface
  ivory: '#EDEBE7',      // main text
  hair: 'rgba(237,235,231,0.16)', // hairline borders
  brass: '#C1A87D',      // accent / primary (buttons)
  signal: '#3CA6E0',     // equity line, data highlights
  ember: '#D74A1F',      // negative
  lilac: '#8B7CF2',      // thoughts
} as const;

// TypeScript Types
type Priority = 1 | 2;

type ActivityType =
  | 'trade_entry_long'
  | 'trade_entry_short'
  | 'trade_win'
  | 'trade_loss'
  | 'strategy_updated'
  | 'market_query'
  | 'agent_wait'
  | 'observation_recorded'
  | 'analysis'
  | 'reasoning'
  | 'plan';

type GlyphId = 'long' | 'short' | 'win' | 'loss' | 'strategy' | 'query' | 'wait' | 'note' | 'think' | 'plan';

interface ActivityDefinition {
  type: ActivityType;
  priority: Priority;
  color: string;
  label: string;
  description: string;
}

interface ActivityItem {
  id: string;
  timestamp: string;
  type: ActivityType;
  priority: number;
  data: Record<string, unknown>;
}

interface BalancePoint {
  timestamp: string;
  balance: number;
}

interface ActivityMetadata {
  botName: string;
  startingBalance: number;
  currentBalance: number;
  totalTrades: number;
  winRate: number;
  performance: number;
}

interface ActivityLog {
  activities: ActivityItem[];
  balanceTimeseries: BalancePoint[];
  metadata: ActivityMetadata;
}

interface TimelineProps {
  configId: string;
  title?: string;
}

interface SvgIconProps {
  className?: string;
  style?: React.CSSProperties;
}

interface VisibleTypes {
  [key: string]: boolean;
}

// React SVG counterparts for panel & buttons
const Svg = {
  Long: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M12 4l-9 16h18z" fill="currentColor" />
    </svg>
  ),
  Short: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M12 20l9-16H3z" fill="currentColor" />
    </svg>
  ),
  Up: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M11 21h2V8l4.5 4.5L19 11l-7-7-7 7 1.5 1.5L11 8z" fill="currentColor" />
    </svg>
  ),
  Down: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M13 3h-2v13l-4.5-4.5L5 13l7 7 7-7-1.5-1.5L13 16z" fill="currentColor" />
    </svg>
  ),
  Wrench: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M14.7 6.3a5 5 0 01-6.4 6.4L3 18l3 3 5.3-5.3a5 5 0 006.4-6.4l-3-3z" fill="currentColor" />
    </svg>
  ),
  Bars: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M4 20h4V8H4v12zm6 0h4V12h-4v8zm6 0h4V4h-4v16z" fill="currentColor" />
    </svg>
  ),
  Clock: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm1 10V6h-2v8h6v-2h-4z" fill="currentColor" />
    </svg>
  ),
  Note: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M6 2h9l5 5v13a2 2 0 01-2 2H6a2 2 0 01-2-2V4a2 2 0 012-2zm8 1.5V8h4.5L14 3.5z" fill="currentColor" />
    </svg>
  ),
  Bubble: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M4 4h16v12H8l-4 4V4z" fill="currentColor" />
    </svg>
  ),
  X: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" />
    </svg>
  ),
  Gear: (p: SvgIconProps) => (
    <svg viewBox="0 0 24 24" aria-hidden className={p.className} style={p.style}>
      <path d="M12 8a4 4 0 100 8 4 4 0 000-8zm9 4l-2.2.6a7.9 7.9 0 01-.9 2.1l1.3 1.9-2 2-1.9-1.3a7.9 7.9 0 01-2.1.9L12 21l-.6-2.2a7.9 7.9 0 01-2.1-.9L7.4 19.2l-2-2 1.3-1.9a7.9 7.9 0 01-.9-2.1L3 12l2.2-.6c.2-.7.5-1.4.9-2.1L4.8 7.4l2-2 1.9 1.3c.7-.4 1.4-.7 2.1-.9L12 3l.6 2.2c.7.2 1.4.5 2.1.9L16.6 5.4l2 2-1.3 1.9c.4.7.7 1.4.9 2.1L21 12z" fill="currentColor" />
    </svg>
  ),
};

// Activity definitions (hardwired colors)
const ACTIVITY_DEFS: Record<ActivityType, ActivityDefinition> = {
  trade_entry_long: { type: 'trade_entry_long', priority: 1, color: VIBE.signal, label: 'Long Entry', description: 'Opened a long position.' },
  trade_entry_short: { type: 'trade_entry_short', priority: 1, color: VIBE.ember, label: 'Short Entry', description: 'Opened a short position.' },
  trade_win: { type: 'trade_win', priority: 1, color: VIBE.signal, label: 'Trade Win', description: 'Closed with profit.' },
  trade_loss: { type: 'trade_loss', priority: 1, color: VIBE.ember, label: 'Trade Loss', description: 'Closed with loss.' },
  strategy_updated: { type: 'strategy_updated', priority: 1, color: VIBE.brass, label: 'Strategy Update', description: 'Strategy modified.' },
  market_query: { type: 'market_query', priority: 2, color: VIBE.signal, label: 'Data Query', description: 'Fetched market data.' },
  agent_wait: { type: 'agent_wait', priority: 2, color: VIBE.hair, label: 'Waiting', description: 'Agent paused.' },
  observation_recorded: { type: 'observation_recorded', priority: 2, color: VIBE.hair, label: 'Observation', description: 'Recorded observation.' },
  analysis: { type: 'analysis', priority: 2, color: VIBE.lilac, label: 'Agent Thoughts', description: 'Analysis.' },
  reasoning: { type: 'reasoning', priority: 2, color: VIBE.lilac, label: 'Agent Thoughts', description: 'Reasoning.' },
  plan: { type: 'plan', priority: 2, color: VIBE.lilac, label: 'Agent Thoughts', description: 'Plan.' },
};

function glyphIdFor(t: ActivityType): GlyphId {
  switch (t) {
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

export default function Timeline({ configId, title }: TimelineProps) {
  const theme = VIBE;

  const [log, setLog] = useState<ActivityLog | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [strategy, setStrategy] = useState<string | null>(null);
  const [showStrategy, setShowStrategy] = useState<boolean>(false);
  const [selected, setSelected] = useState<ActivityItem[] | null>(null);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState<boolean>(false);
  const [visibleTypes, setVisibleTypes] = useState<VisibleTypes>(() => {
    // Try to load from localStorage first
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('timeline-filters');
      if (saved) {
        try {
          return JSON.parse(saved) as VisibleTypes;
        } catch (e) {
          console.error('Failed to parse saved filters:', e);
        }
      }
    }
    // Default: all visible
    const defaultVisibleTypes: VisibleTypes = {};
    Object.keys(ACTIVITY_DEFS).forEach((k) => {
      defaultVisibleTypes[k] = true;
    });
    return defaultVisibleTypes;
  });

  // Save to localStorage whenever visibleTypes changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('timeline-filters', JSON.stringify(visibleTypes));
    }
  }, [visibleTypes]);

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
        const headers: HeadersInit = session?.access_token
          ? { Authorization: `Bearer ${session.access_token}` }
          : {};

        // Fetch all endpoints in parallel
        // Use pnl mode for cumulative P&L chart (starts at $0, shows gains/losses)
        const [activitiesRes, balanceSeriesRes, metadataRes, strategyRes] = await Promise.all([
          fetch(`/api/v2/activities/${configId}`, { headers }),
          fetch(`/api/v2/activities/${configId}/balance-series?mode=pnl`, { headers }),
          fetch(`/api/v2/activities/${configId}/metadata`, { headers }),
          fetch(`/api/v2/activities/${configId}/strategy`, { headers }).catch(() => null),
        ]);

        if (!activitiesRes.ok || !balanceSeriesRes.ok || !metadataRes.ok) {
          throw new Error('Failed to fetch activity data');
        }

        const [activities, balanceSeries, metadata, strategyData] = await Promise.all([
          activitiesRes.json(),
          balanceSeriesRes.json(),
          metadataRes.json(),
          strategyRes?.ok ? strategyRes.json() : null,
        ]);

        setLog({
          activities: activities.activities || [],
          balanceTimeseries: balanceSeries.balance_series || [],
          metadata: {
            botName: metadata.metadata?.botName || metadata.bot_name || metadata.botName || 'Unknown Bot',
            startingBalance: metadata.metadata?.startingBalance || metadata.startingBalance || metadata.starting_balance || 0,
            currentBalance: metadata.metadata?.currentBalance || metadata.currentBalance || metadata.current_balance || 0,
            totalTrades: metadata.metadata?.totalTrades || metadata.totalTrades || metadata.total_trades || 0,
            winRate: metadata.metadata?.winRate || metadata.winRate || metadata.win_rate || 0,
            performance: metadata.metadata?.performance || metadata.performance || 0,
          },
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

    // Initial fetch
    fetchData();

    // Set up polling interval (10 seconds)
    const intervalId = setInterval(fetchData, 10000);

    // Cleanup on unmount
    return () => clearInterval(intervalId);
  }, [configId, session]);

  const info = log?.metadata;
  const isEmpty = !log || (log.activities?.length ?? 0) === 0 || (log.balanceTimeseries?.length ?? 0) === 0;

  // Helper to get icon component for glyph
  const getIconComponent = (glyph: GlyphId) => {
    switch (glyph) {
      case 'long': return Svg.Long;
      case 'short': return Svg.Short;
      case 'win': return Svg.Up;
      case 'loss': return Svg.Down;
      case 'strategy': return Svg.Wrench;
      case 'query': return Svg.Bars;
      case 'wait': return Svg.Clock;
      case 'note': return Svg.Note;
      default: return Svg.Bubble;
    }
  };

  // Filter list UI (shared)
  function FiltersList() {
    const entries = Object.keys(ACTIVITY_DEFS).map((k) => {
      const activityType = k as ActivityType;
      const def = ACTIVITY_DEFS[activityType];
      const on = visibleTypes[k];
      const glyph = glyphIdFor(activityType);
      const Icon = getIconComponent(glyph);

      return (
        <button
          key={k}
          onClick={() => setVisibleTypes((prev) => ({ ...prev, [k]: !on }))}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${on ? '' : 'hover:bg-white/5'}`}
          style={{
            color: on ? theme.ivory : 'rgba(237,235,231,0.6)',
            borderColor: theme.hair,
            backgroundColor: on ? 'rgba(255,255,255,0.04)' : 'transparent',
          }}
        >
          <Icon className="w-4 h-4" style={{ color: def.color }} />
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
          <div className="text-sm" style={{ color: 'rgba(237,235,231,0.6)' }}>
            Fetching activity data
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="w-full h-screen flex items-center justify-center" style={{ backgroundColor: theme.obsidian, color: theme.ivory }}>
        <div className="max-w-md mx-auto text-center">
          <div className="text-xl mb-2" style={{ color: theme.ember }}>
            Failed to Load Timeline
          </div>
          <div className="text-sm" style={{ color: 'rgba(237,235,231,0.6)' }}>
            {error}
          </div>
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
                {title ?? info?.botName ?? 'Activity Timeline'}
              </h1>
              <p className="font-mono text-xs sm:text-sm" style={{ color: 'rgba(237,235,231,0.7)' }}>
                ARENA STATUS • {new Date().toUTCString().slice(5, 16).toUpperCase()} UTC
              </p>
            </div>
            <div className="flex items-center flex-wrap gap-2">
              {/* View Configuration */}
              {strategy && (
                <button
                  onClick={() => setShowStrategy(true)}
                  className="inline-flex items-center gap-2 px-3 py-1.5 text-xs sm:text-sm rounded-lg border"
                  style={{ borderColor: theme.hair, backgroundColor: 'transparent', color: theme.ivory }}
                >
                  <Svg.Gear className="w-4 h-4" />
                  <span>View Configuration</span>
                </button>
              )}
              {/* Mobile Filters toggle */}
              <button
                onClick={() => setMobileFiltersOpen(true)}
                className="md:hidden px-3 py-1.5 text-xs sm:text-sm rounded-lg border"
                style={{ borderColor: theme.hair }}
              >
                Filters
              </button>
            </div>
          </div>

          {/* KPI Row */}
          {info && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 sm:gap-3 mt-4">
              {[
                { k: 'Balance', v: `$${Math.round(info.currentBalance).toLocaleString()}` },
                { k: 'P/L', v: `${info.currentBalance - info.startingBalance >= 0 ? '+' : ''}${Math.round(info.currentBalance - info.startingBalance).toLocaleString()}` },
                { k: 'Trades', v: String(info.totalTrades) },
                { k: 'Win Rate', v: `${Math.round(info.winRate)}%` },
                { k: 'Perf', v: `${typeof info.performance === 'number' ? info.performance.toFixed(2) : info.performance}%` },
              ].map((d, i) => (
                <div key={i} className="border rounded-lg px-3 py-2" style={{ borderColor: theme.hair }}>
                  <div className="text-[10px] uppercase tracking-[0.18em]" style={{ color: 'rgba(237,235,231,0.6)' }}>
                    {d.k}
                  </div>
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
              <div className="text-sm" style={{ color: 'rgba(237,235,231,0.7)' }}>
                Activity Types
              </div>
              <FiltersList />
              <button
                onClick={() => {
                  const allOn = Object.values(visibleTypes).every((v) => v);
                  const next: VisibleTypes = {};
                  Object.keys(ACTIVITY_DEFS).forEach((k) => (next[k] = !allOn));
                  setVisibleTypes(next);
                }}
                className="w-full mt-3 text-xs px-3 py-1.5 rounded-lg border"
                style={{ borderColor: theme.hair, color: 'rgba(237,235,231,0.85)' }}
              >
                Toggle All
              </button>
              <div className="font-mono text-[11px] mt-3" style={{ color: 'rgba(237,235,231,0.6)' }}>
                Click markers to view details • Scroll to zoom • Drag to pan
              </div>
            </div>
          </aside>

          {/* RIGHT – Chart */}
          <div className="col-span-12 md:col-span-9 min-h-[360px] sm:min-h-[420px]">
            <div className="rounded-xl border h-full relative overflow-hidden" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
              <div className="absolute inset-0">
                {log?.balanceTimeseries && log?.activities ? (
                  <BalanceChartRecharts
                    balanceData={log.balanceTimeseries}
                    activities={log.activities}
                    onActivityClick={(activity) => setSelected([activity])}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full" style={{ color: theme.hair }}>
                    <div className="text-center">
                      <p className="text-sm">No chart data available</p>
                      <p className="text-xs mt-2">Waiting for trades...</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* MOBILE FILTERS SHEET */}
      <AnimatePresence>
        {mobileFiltersOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-40">
            <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.5)' }} onClick={() => setMobileFiltersOpen(false)} />
            <motion.div
              initial={{ y: 480 }}
              animate={{ y: 0 }}
              exit={{ y: 480 }}
              transition={{ type: 'tween', duration: 0.25 }}
              className="absolute bottom-0 left-0 right-0 rounded-t-2xl border p-4"
              style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium">Filters</div>
                <button onClick={() => setMobileFiltersOpen(false)} className="p-2 rounded-md" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}>
                  <Svg.X className="w-4 h-4" />
                </button>
              </div>
              <FiltersList />
              <button
                onClick={() => {
                  const allOn = Object.values(visibleTypes).every((v) => v);
                  const next: VisibleTypes = {};
                  Object.keys(ACTIVITY_DEFS).forEach((k) => (next[k] = !allOn));
                  setVisibleTypes(next);
                }}
                className="w-full mt-3 text-xs px-3 py-2 rounded-lg border"
                style={{ borderColor: theme.hair, color: 'rgba(237,235,231,0.9)' }}
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
          <motion.aside
            initial={{ x: 560, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 560, opacity: 0 }}
            transition={{ type: 'tween', duration: 0.25 }}
            className="fixed top-0 right-0 h-full w-full sm:w-[560px] z-40"
          >
            <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.4)' }} onClick={() => setSelected(null)} />
            <div className="relative ml-auto h-full w-full sm:w-[560px] rounded-l-xl border overflow-hidden" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
              <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: `1px solid ${theme.hair}` }}>
                <div className="text-lg font-medium">Activity Details</div>
                <button onClick={() => setSelected(null)} style={{ color: 'rgba(237,235,231,0.8)' }}>
                  <Svg.X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-5 space-y-3 overflow-y-auto h-[calc(100%-64px)]">
                {selected.map((a) => {
                  const def = ACTIVITY_DEFS[a.type];
                  const glyph = glyphIdFor(a.type);
                  const Glyph = (() => {
                    switch (glyph) {
                      case 'long': return Svg.Long;
                      case 'short': return Svg.Short;
                      case 'win': return Svg.Up;
                      case 'loss': return Svg.Down;
                      case 'strategy': return Svg.Wrench;
                      case 'query': return Svg.Bars;
                      case 'wait': return Svg.Clock;
                      case 'note': return Svg.Note;
                      default: return Svg.Bubble;
                    }
                  })();
                  return (
                    <div key={a.id} className="border rounded-lg p-4" style={{ borderColor: theme.hair }}>
                      <div className="flex items-center gap-2 text-sm">
                        <Glyph className="w-4 h-4" style={{ color: def.color }} />
                        <span className="font-semibold">{def.label}</span>
                        <span className="font-mono text-[11px]" style={{ color: 'rgba(237,235,231,0.6)' }}>
                          {new Date(a.timestamp).toLocaleString('en-US', { timeZone: 'UTC' })} UTC
                        </span>
                      </div>
                      <div className="text-sm mt-2" style={{ color: 'rgba(237,235,231,0.85)' }}>
                        {def.description}
                      </div>
                      {a.data && (
                        <pre className="mt-3 text-[12px] leading-relaxed font-mono whitespace-pre-wrap" style={{ color: 'rgba(237,235,231,0.85)' }}>
                          {JSON.stringify(a.data, null, 2)}
                        </pre>
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
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="max-w-3xl mx-auto mt-10">
            <div className="rounded-xl border p-8 text-center" style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}>
              <div className="text-2xl mb-2">Timeline</div>
              <div className="text-2xl">No Activity Yet</div>
              <p className="mt-2" style={{ color: 'rgba(237,235,231,0.7)' }}>
                When trades begin, events will plot here.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* STRATEGY MODAL */}
      <AnimatePresence>
        {showStrategy && strategy && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.6)' }} onClick={() => setShowStrategy(false)} />
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="relative w-full max-w-3xl max-h-[80vh] rounded-xl border overflow-hidden"
              style={{ backgroundColor: theme.carbon, borderColor: theme.hair }}
            >
              <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: `1px solid ${theme.hair}` }}>
                <div className="text-xl font-semibold">Agent Configuration</div>
                <button onClick={() => setShowStrategy(false)} style={{ color: 'rgba(237,235,231,0.8)' }}>
                  <Svg.X className="w-6 h-6" />
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[calc(80vh-5rem)]">
                <pre className="whitespace-pre-wrap text-sm leading-relaxed font-mono" style={{ color: 'rgba(237,235,231,0.9)' }}>
                  {strategy}
                </pre>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
