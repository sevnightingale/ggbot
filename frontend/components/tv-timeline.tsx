'use client';

import React, { useEffect, useState, useRef } from 'react';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, LineData, Time, SeriesMarker } from 'lightweight-charts';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import type { Session } from '@supabase/supabase-js';
import BottomSheet from './bottom-sheet';

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

interface BalancePoint {
  timestamp: string;
  balance: number;
}

interface Activity {
  id: string;
  timestamp: string;
  type: string;
  priority: number;
  data: {
    summary?: string;
    details?: Record<string, unknown>;
    symbol?: string;
    importance?: number;
    trade_id?: string;
    trade_type?: string;
  };
}

interface ActivityMetadata {
  botName: string;
  startingBalance: number;
  currentBalance: number;
  totalTrades: number;
  winRate: number;
  performance: number;
}

interface TimelineProps {
  configId: string;
  title?: string;
}

export default function TVTimeline({ configId, title }: TimelineProps) {
  const [chartContainer, setChartContainer] = useState<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const lineSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const isFirstLoadRef = useRef<boolean>(true);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [metadata, setMetadata] = useState<ActivityMetadata | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);
  const [detailActivity, setDetailActivity] = useState<Activity | null>(null);
  const [crosshairPosition, setCrosshairPosition] = useState<{ x: number; y: number } | null>(null);

  // Map to lookup activities by timestamp
  const activitiesMapRef = useRef<Map<number, Activity>>(new Map());

  // Get session for auth
  useEffect(() => {
    const supabase = createClientComponentClient();
    const getSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setSession(session);
    };
    getSession();
  }, []);

  // Fetch data and initialize chart
  useEffect(() => {
    console.log('useEffect running', { configId, hasContainer: !!chartContainer, hasSession: !!session });

    if (!configId || !chartContainer) {
      console.log('Early return - missing configId or container');
      return;
    }

    // Create chart if it doesn't exist
    if (!chartRef.current) {
      const containerWidth = chartContainer.clientWidth;
      const containerHeight = chartContainer.clientHeight;

      console.log('Creating chart with dimensions:', { width: containerWidth, height: containerHeight });

      // Reset first load flag when creating new chart
      isFirstLoadRef.current = true;

      const chart = createChart(chartContainer, {
        width: containerWidth,
        height: containerHeight,
        layout: {
          background: { type: ColorType.Solid, color: VIBE.carbon },
          textColor: VIBE.hair,
        },
        grid: {
          vertLines: { color: VIBE.hair, style: LineStyle.Dotted },
          horzLines: { color: VIBE.hair, style: LineStyle.Dotted },
        },
        rightPriceScale: {
          borderColor: VIBE.hair,
        },
        timeScale: {
          borderColor: VIBE.hair,
          timeVisible: true,
          secondsVisible: false,
        },
        crosshair: {
          mode: 1,
          vertLine: {
            color: VIBE.brass,
            width: 1,
            style: LineStyle.Dashed,
          },
          horzLine: {
            color: VIBE.brass,
            width: 1,
            style: LineStyle.Dashed,
          },
        },
      });

      chartRef.current = chart;
      console.log('Chart created:', !!chart);

      const lineSeries = chart.addLineSeries({
        color: VIBE.signal,
        lineWidth: 2,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 4,
        lastValueVisible: true,
        priceLineVisible: true,
      });

      lineSeriesRef.current = lineSeries;
      console.log('Line series created:', !!lineSeries);

      // Crosshair move handler - highlight activity when crosshair snaps to it
      chart.subscribeCrosshairMove((param) => {
        if (!param.time || !param.point) {
          setSelectedActivity(null);
          setCrosshairPosition(null);
          return;
        }

        const timestamp = typeof param.time === 'number' ? param.time : parseFloat(param.time as string);
        const activity = activitiesMapRef.current.get(timestamp);

        if (activity && (activity.type === 'trade_entry_long' || activity.type === 'trade_entry_short')) {
          // Only highlight trade entries for now
          setSelectedActivity(activity);
          setCrosshairPosition({ x: param.point.x, y: param.point.y });
        } else {
          setSelectedActivity(null);
          setCrosshairPosition(null);
        }
      });

      // Click handler - open activity detail when clicking on a point
      chart.subscribeClick((param) => {
        if (!param.time) return;

        const timestamp = typeof param.time === 'number' ? param.time : parseFloat(param.time as string);
        const activity = activitiesMapRef.current.get(timestamp);

        if (activity && (activity.type === 'trade_entry_long' || activity.type === 'trade_entry_short')) {
          console.log('Clicked activity:', activity);
          setDetailActivity(activity);
        }
      });

      const handleResize = () => {
        if (chartContainer && chartRef.current) {
          chartRef.current.applyOptions({
            width: chartContainer.clientWidth,
            height: chartContainer.clientHeight,
          });
        }
      };

      window.addEventListener('resize', handleResize);
    }

    const fetchData = async () => {
      try {
        console.log('fetchData starting...', { configId, hasSession: !!session });
        setLoading(true);
        setError(null);

        const headers: HeadersInit = session?.access_token
          ? { Authorization: `Bearer ${session.access_token}` }
          : {};

        console.log('Fetching from API...');
        const [balanceSeriesRes, activitiesRes, metadataRes] = await Promise.all([
          fetch(`/api/v2/activities/${configId}/balance-series?mode=pnl`, { headers }),
          fetch(`/api/v2/activities/${configId}`, { headers }),
          fetch(`/api/v2/activities/${configId}/metadata`, { headers }),
        ]);

        console.log('API responses:', {
          balanceOk: balanceSeriesRes.ok,
          balanceStatus: balanceSeriesRes.status,
          activitiesOk: activitiesRes.ok,
          activitiesStatus: activitiesRes.status,
          metadataOk: metadataRes.ok,
          metadataStatus: metadataRes.status
        });

        if (!balanceSeriesRes.ok || !activitiesRes.ok || !metadataRes.ok) {
          const balanceError = await balanceSeriesRes.text();
          const activitiesError = await activitiesRes.text();
          const metadataError = await metadataRes.text();
          console.error('API errors:', { balanceError, activitiesError, metadataError });
          throw new Error(`Failed to fetch timeline data`);
        }

        const [balanceSeries, activitiesData, metadataData] = await Promise.all([
          balanceSeriesRes.json(),
          activitiesRes.json(),
          metadataRes.json(),
        ]);

        const balancePoints: BalancePoint[] = balanceSeries.balance_series || [];
        const activities: Activity[] = activitiesData.activities || [];

        console.log('Raw balance points:', balancePoints.length);
        console.log('Raw activities:', activities.length);

        setMetadata({
          botName: metadataData.metadata?.botName || metadataData.bot_name || metadataData.botName || 'Unknown Bot',
          startingBalance: metadataData.metadata?.startingBalance || metadataData.startingBalance || metadataData.starting_balance || 0,
          currentBalance: metadataData.metadata?.currentBalance || metadataData.currentBalance || metadataData.current_balance || 0,
          totalTrades: metadataData.metadata?.totalTrades || metadataData.totalTrades || metadataData.total_trades || 0,
          winRate: metadataData.metadata?.winRate || metadataData.winRate || metadataData.win_rate || 0,
          performance: metadataData.metadata?.performance || metadataData.performance || 0,
        });

        // Step 1: Create timeline events from both balance points and activities
        interface TimelineEvent {
          timestamp: number; // unix seconds
          type: 'balance' | 'activity';
          value?: number; // P&L value (only for balance events)
        }

        const timelineEvents: TimelineEvent[] = [];

        // Add balance points
        balancePoints.forEach((point) => {
          timelineEvents.push({
            timestamp: Math.floor(new Date(point.timestamp).getTime() / 1000),
            type: 'balance',
            value: point.balance,
          });
        });

        // Add activities
        activities.forEach((activity) => {
          timelineEvents.push({
            timestamp: Math.floor(new Date(activity.timestamp).getTime() / 1000),
            type: 'activity',
          });
        });

        // Step 2: Sort all events chronologically
        timelineEvents.sort((a, b) => a.timestamp - b.timestamp);

        console.log('Timeline events (balance + activities):', timelineEvents.length);

        // Step 3: Walk through events, update P&L when we hit balance points
        let currentPnl = 0.0;
        const mergedData: LineData[] = [];
        const seenTimestamps = new Set<number>();

        timelineEvents.forEach((event) => {
          // Update P&L if this is a balance event
          if (event.type === 'balance' && event.value !== undefined) {
            currentPnl = event.value;
            console.log(`P&L update at ${new Date(event.timestamp * 1000).toISOString()}: $${currentPnl}`);
          }

          // Add point to chart (dedupe by timestamp)
          if (!seenTimestamps.has(event.timestamp)) {
            mergedData.push({
              time: event.timestamp as Time,
              value: currentPnl,
            });
            seenTimestamps.add(event.timestamp);
          }
        });

        // Data is already sorted and deduped
        const chartData = mergedData;

        console.log('Final chart data:', chartData.length, 'points');
        console.log('First 3 points:', chartData.slice(0, 3));
        console.log('Last 3 points:', chartData.slice(-3));

        // Debug time spacing
        if (chartData.length >= 3) {
          const t0 = typeof chartData[0].time === 'number' ? chartData[0].time : parseFloat(chartData[0].time as string);
          const t1 = typeof chartData[1].time === 'number' ? chartData[1].time : parseFloat(chartData[1].time as string);
          const t2 = typeof chartData[2].time === 'number' ? chartData[2].time : parseFloat(chartData[2].time as string);
          console.log('Time spacing (first 3 points):');
          console.log(`  Point 0 to 1: ${t1 - t0} seconds (${(t1 - t0) / 3600} hours)`);
          console.log(`  Point 1 to 2: ${t2 - t1} seconds (${(t2 - t1) / 3600} hours)`);
          console.log(`  Point 0 date: ${new Date(t0 * 1000).toISOString()}`);
          console.log(`  Point 1 date: ${new Date(t1 * 1000).toISOString()}`);
        }

        console.log('Line series ref exists:', !!lineSeriesRef.current);

        if (lineSeriesRef.current && chartData.length > 0) {
          console.log('Setting data on chart...');
          lineSeriesRef.current.setData(chartData);

          // Build activities lookup map and create markers for trade entries
          activitiesMapRef.current.clear();
          const tradeMarkers: SeriesMarker<Time>[] = [];

          activities.forEach((activity) => {
            const timestamp = Math.floor(new Date(activity.timestamp).getTime() / 1000);
            activitiesMapRef.current.set(timestamp, activity);

            // Only create markers for trade entries
            if (activity.type === 'trade_entry_long') {
              tradeMarkers.push({
                time: timestamp as Time,
                position: 'belowBar',
                color: '#16a34a', // green-600
                shape: 'arrowUp',
                text: 'LONG',
              });
            } else if (activity.type === 'trade_entry_short') {
              tradeMarkers.push({
                time: timestamp as Time,
                position: 'aboveBar',
                color: '#dc2626', // red-600
                shape: 'arrowDown',
                text: 'SHORT',
              });
            }
          });

          // Set markers on the line series
          if (tradeMarkers.length > 0) {
            // CRITICAL: Markers must be sorted by time in ascending order
            const sortedMarkers = tradeMarkers.sort((a, b) => {
              const timeA = typeof a.time === 'number' ? a.time : parseFloat(a.time as string);
              const timeB = typeof b.time === 'number' ? b.time : parseFloat(b.time as string);
              return timeA - timeB;
            });
            lineSeriesRef.current.setMarkers(sortedMarkers);
            console.log('Trade markers added:', sortedMarkers.length);
          }

          // Only fit content on first load, preserve user zoom/pan on subsequent updates
          if (isFirstLoadRef.current) {
            chartRef.current?.timeScale().fitContent();
            isFirstLoadRef.current = false;
            console.log('Data set successfully (initial load, fitted content)');
          } else {
            console.log('Data set successfully (update, preserved zoom/pan)');
          }
        } else {
          console.warn('Cannot set data:', {
            hasLineSeries: !!lineSeriesRef.current,
            dataLength: chartData.length
          });
        }

        setLoading(false);
      } catch (err) {
        console.error('Error fetching timeline data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setLoading(false);
      }
    };

    console.log('About to call fetchData...');
    fetchData();

    console.log('Setting up polling interval...');
    const intervalId = setInterval(fetchData, 10000);

    return () => {
      clearInterval(intervalId);
      if (chartRef.current) {
        window.removeEventListener('resize', () => {});
        chartRef.current.remove();
        chartRef.current = null;
        lineSeriesRef.current = null;
      }
    };
  }, [configId, session, chartContainer]);

  const info = metadata;

  return (
    <div className="relative w-full min-h-screen font-sans" style={{ backgroundColor: VIBE.obsidian, color: VIBE.ivory }}>
      <style>{`
        @keyframes markerPulse {
          0%, 100% {
            opacity: 1;
            filter: drop-shadow(0 0 8px currentColor);
          }
          50% {
            opacity: 0.8;
            filter: drop-shadow(0 0 16px currentColor);
          }
        }
      `}</style>
      {/* HEADER */}
      <section className="max-w-7xl mx-auto px-4 sm:px-5 pt-5 pb-4">
        <div className="rounded-xl border p-4 sm:p-6" style={{ backgroundColor: VIBE.carbon, borderColor: VIBE.hair }}>
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3 sm:gap-6">
            <div className="flex-1 min-w-0">
              <h1 className="text-xl sm:text-2xl md:text-3xl leading-tight tracking-tight">
                {title ?? info?.botName ?? 'Activity Timeline'}
              </h1>
              <p className="font-mono text-xs sm:text-sm" style={{ color: 'rgba(237,235,231,0.7)' }}>
                ARENA STATUS • {new Date().toUTCString().slice(5, 16).toUpperCase()} UTC
              </p>
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
                <div key={i} className="border rounded-lg px-3 py-2" style={{ borderColor: VIBE.hair }}>
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

      {/* CHART */}
      <section className="max-w-7xl mx-auto px-4 sm:px-5 pb-5">
        <div className="rounded-xl border overflow-hidden relative" style={{ backgroundColor: VIBE.carbon, borderColor: VIBE.hair, height: 'calc(100vh - 280px)', minHeight: '400px' }}>
          <div ref={setChartContainer} style={{ width: '100%', height: '100%' }} />

          {/* Activity hover tooltip */}
          {selectedActivity && (
            <>
              {/* Tooltip card */}
              <div
                className="absolute top-4 left-4 rounded-lg border px-4 py-3 pointer-events-none"
                style={{
                  backgroundColor: VIBE.carbon,
                  borderColor: VIBE.brass,
                  borderWidth: '2px',
                  maxWidth: '300px',
                  zIndex: 10
                }}
              >
                <div className="text-xs uppercase tracking-wider mb-1" style={{ color: VIBE.brass }}>
                  {selectedActivity.type === 'trade_entry_long' ? '↑ LONG ENTRY' : '↓ SHORT ENTRY'}
                </div>
                <div className="text-sm mb-1">{selectedActivity.data.summary || 'Trade entry'}</div>
                <div className="text-xs" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  {new Date(selectedActivity.timestamp).toLocaleString()}
                </div>
                {selectedActivity.data.symbol && (
                  <div className="text-xs mt-2" style={{ color: VIBE.signal }}>
                    {selectedActivity.data.symbol}
                  </div>
                )}
              </div>

              {/* Highlighted marker overlay - shows larger version at crosshair position */}
              {crosshairPosition && (
                <div
                  className="absolute pointer-events-none"
                  style={{
                    left: `${crosshairPosition.x}px`,
                    top: `${crosshairPosition.y}px`,
                    transform: 'translate(-50%, -50%)',
                    zIndex: 5
                  }}
                >
                  <div
                    style={{
                      fontSize: '40px',
                      color: selectedActivity.type === 'trade_entry_long' ? '#16a34a' : '#dc2626',
                      lineHeight: 1,
                      animation: 'markerPulse 1.5s ease-in-out infinite'
                    }}
                  >
                    {selectedActivity.type === 'trade_entry_long' ? '▲' : '▼'}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Loading overlay */}
          {loading && !metadata && (
            <div className="absolute inset-0 flex items-center justify-center" style={{ backgroundColor: 'rgba(11,11,12,0.8)' }}>
              <div className="text-center">
                <div className="text-xl mb-2">Loading Timeline...</div>
                <div className="text-sm" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  Fetching activity data
                </div>
              </div>
            </div>
          )}

          {/* Error overlay */}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center" style={{ backgroundColor: 'rgba(11,11,12,0.8)' }}>
              <div className="max-w-md mx-auto text-center">
                <div className="text-xl mb-2" style={{ color: VIBE.ember }}>
                  Failed to Load Timeline
                </div>
                <div className="text-sm" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  {error}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Activity Detail Bottom Sheet */}
      <BottomSheet
        isOpen={!!detailActivity}
        onClose={() => setDetailActivity(null)}
        title={detailActivity?.type === 'trade_entry_long' ? 'Long Entry' : detailActivity?.type === 'trade_entry_short' ? 'Short Entry' : 'Activity'}
      >
        {detailActivity && (
          <div className="px-6 py-4 space-y-4">
            {/* Activity Type Badge */}
            <div className="inline-block px-3 py-1 rounded-lg text-xs uppercase tracking-wider font-semibold" style={{
              backgroundColor: detailActivity.type === 'trade_entry_long' ? '#16a34a' : '#dc2626',
              color: VIBE.ivory
            }}>
              {detailActivity.type === 'trade_entry_long' ? '↑ Long Entry' : '↓ Short Entry'}
            </div>

            {/* Timestamp */}
            <div>
              <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                Timestamp
              </div>
              <div className="text-sm font-mono">
                {new Date(detailActivity.timestamp).toLocaleString('en-US', {
                  dateStyle: 'medium',
                  timeStyle: 'medium'
                })}
              </div>
            </div>

            {/* Symbol */}
            {detailActivity.data.symbol && (
              <div>
                <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  Symbol
                </div>
                <div className="text-lg font-semibold" style={{ color: VIBE.signal }}>
                  {detailActivity.data.symbol}
                </div>
              </div>
            )}

            {/* Summary */}
            {detailActivity.data.summary && (
              <div>
                <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  Summary
                </div>
                <div className="text-sm leading-relaxed">
                  {detailActivity.data.summary}
                </div>
              </div>
            )}

            {/* Trade ID */}
            {detailActivity.data.trade_id && (
              <div>
                <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  Trade ID
                </div>
                <div className="text-sm font-mono" style={{ color: VIBE.brass }}>
                  {detailActivity.data.trade_id}
                </div>
              </div>
            )}

            {/* Details (if present) */}
            {detailActivity.data.details && Object.keys(detailActivity.data.details).length > 0 && (
              <div>
                <div className="text-xs uppercase tracking-wider mb-2" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  Details
                </div>
                <div className="bg-black bg-opacity-30 rounded-lg p-3 overflow-auto">
                  <pre className="text-xs font-mono" style={{ color: VIBE.ivory }}>
                    {JSON.stringify(detailActivity.data.details, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Importance Level */}
            {detailActivity.data.importance !== undefined && (
              <div>
                <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  Importance
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <div
                        key={level}
                        className="w-8 h-2 rounded"
                        style={{
                          backgroundColor: level <= (detailActivity.data.importance || 0) ? VIBE.brass : 'rgba(237,235,231,0.2)'
                        }}
                      />
                    ))}
                  </div>
                  <span className="text-sm">{detailActivity.data.importance}/5</span>
                </div>
              </div>
            )}
          </div>
        )}
      </BottomSheet>
    </div>
  );
}
