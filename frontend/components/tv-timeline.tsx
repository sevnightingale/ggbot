'use client';

import React, { useEffect, useState, useRef } from 'react';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, LineData, Time, SeriesMarker } from 'lightweight-charts';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import type { Session } from '@supabase/supabase-js';
import BottomSheet from './bottom-sheet';
import ReactMarkdown from 'react-markdown';

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
    confidence?: number;
    leverage?: number;
    entry_price?: number;
    stop_loss_price?: number;
    take_profit_price?: number;
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
  variant?: 'standalone' | 'embedded';
}

export default function TVTimeline({ configId, title, variant = 'standalone' }: TimelineProps) {
  const [chartContainer, setChartContainer] = useState<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const lineSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const isFirstLoadRef = useRef<boolean>(true);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [metadata, setMetadata] = useState<ActivityMetadata | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);
  const [detailActivities, setDetailActivities] = useState<Activity[]>([]);
  const [crosshairPosition, setCrosshairPosition] = useState<{ x: number; y: number } | null>(null);
  const [latestActivity, setLatestActivity] = useState<Activity | null>(null);
  const [statusText, setStatusText] = useState<string>('');

  // Map to lookup activities by timestamp (can have multiple activities at same time)
  const activitiesMapRef = useRef<Map<number, Activity[]>>(new Map());

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
        localization: {
          priceFormatter: (price: number) => `$${price.toFixed(2)}`,
        },
      });

      chartRef.current = chart;
      console.log('Chart created:', !!chart);

      const lineSeries = chart.addLineSeries({
        color: VIBE.brass,  // Changed from signal (blue) to brass
        lineWidth: 2,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 4,
        lastValueVisible: true,
        priceLineVisible: false,  // Remove the dashed price line
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
        const activities = activitiesMapRef.current.get(timestamp);

        if (activities && activities.length > 0) {
          // For tooltip, show the first/primary activity
          setSelectedActivity(activities[0]);
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
        const activities = activitiesMapRef.current.get(timestamp);

        if (activities && activities.length > 0) {
          console.log('Clicked activities:', activities);
          setDetailActivities(activities);
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

          // Build activities lookup map - group by timestamp
          activitiesMapRef.current.clear();
          const groupedByTimestamp = new Map<number, Activity[]>();

          activities.forEach((activity) => {
            const timestamp = Math.floor(new Date(activity.timestamp).getTime() / 1000);
            if (!groupedByTimestamp.has(timestamp)) {
              groupedByTimestamp.set(timestamp, []);
            }
            groupedByTimestamp.get(timestamp)!.push(activity);
          });

          // Set the grouped activities in the ref
          activitiesMapRef.current = groupedByTimestamp;

          // Update latest activity for status display
          const sortedActivities = activities.sort((a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
          );
          if (sortedActivities.length > 0) {
            setLatestActivity(sortedActivities[0]);
          }

          // Create one marker per timestamp based on priority
          const markers: SeriesMarker<Time>[] = [];

          groupedByTimestamp.forEach((activitiesAtTime, timestamp) => {
            // Determine marker type based on priority
            const hasTradeLong = activitiesAtTime.some(a => a.type === 'trade_entry_long');
            const hasTradeShort = activitiesAtTime.some(a => a.type === 'trade_entry_short');
            const hasAnalysis = activitiesAtTime.some(a => a.type === 'analysis');
            const hasMarketQuery = activitiesAtTime.some(a => a.type === 'market_query');
            const hasAgentWait = activitiesAtTime.some(a => a.type === 'agent_wait');

            if (hasTradeLong) {
              markers.push({
                time: timestamp as Time,
                position: 'belowBar',
                color: '#16a34a', // green-600
                shape: 'arrowUp',
                size: 2, // Make arrows bigger
              });
            } else if (hasTradeShort) {
              markers.push({
                time: timestamp as Time,
                position: 'aboveBar',
                color: '#dc2626', // red-600
                shape: 'arrowDown',
                size: 2, // Make arrows bigger
              });
            } else if (hasAnalysis) {
              markers.push({
                time: timestamp as Time,
                position: 'aboveBar',
                color: 'rgba(193, 168, 125, 0.6)', // brass with transparency
                shape: 'circle',
                size: 0.5, // Smaller circles
              });
            } else if (hasMarketQuery) {
              markers.push({
                time: timestamp as Time,
                position: 'belowBar',
                color: 'rgba(60, 166, 224, 0.5)', // signal blue with transparency
                shape: 'circle',
                size: 0.5, // Smaller circles
              });
            } else if (hasAgentWait) {
              markers.push({
                time: timestamp as Time,
                position: 'belowBar',
                color: 'rgba(237, 235, 231, 0.4)', // ivory with transparency
                shape: 'circle',
                size: 0.5, // Smaller circles
              });
            }
          });

          // Set markers on the line series
          if (markers.length > 0) {
            // CRITICAL: Markers must be sorted by time in ascending order
            const sortedMarkers = markers.sort((a, b) => {
              const timeA = typeof a.time === 'number' ? a.time : parseFloat(a.time as string);
              const timeB = typeof b.time === 'number' ? b.time : parseFloat(b.time as string);
              return timeA - timeB;
            });
            lineSeriesRef.current.setMarkers(sortedMarkers);
            console.log('Markers added:', sortedMarkers.length, {
              trade_entries: sortedMarkers.filter(m => m.shape === 'arrowUp' || m.shape === 'arrowDown').length,
              circles: sortedMarkers.filter(m => m.shape === 'circle').length,
            });
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

  // Track latest activity and update status text
  useEffect(() => {
    // Find the most recent activity
    const sortedActivities = Array.from(activitiesMapRef.current.values())
      .flat()
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    if (sortedActivities.length > 0) {
      setLatestActivity(sortedActivities[0]);
    }
  }, []);

  // Update status text every second
  useEffect(() => {
    if (!latestActivity) return;

    const updateStatus = () => {
      const now = new Date();
      const activityTime = new Date(latestActivity.timestamp);
      const diffMs = now.getTime() - activityTime.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffSecs = Math.floor((diffMs % 60000) / 1000);

      // For agent_wait, show countdown to next check
      if (latestActivity.type === 'agent_wait' && latestActivity.data.details) {
        const details = latestActivity.data.details as Record<string, unknown>;
        if (details.next_check_at) {
          const nextCheck = new Date(String(details.next_check_at));
          const remainingMs = nextCheck.getTime() - now.getTime();

          if (remainingMs > 0) {
            const mins = Math.floor(remainingMs / 60000);
            const secs = Math.floor((remainingMs % 60000) / 1000);
            setStatusText(`⏸ WAITING • Next check in ${mins}m ${secs}s`);
            return;
          } else {
            setStatusText('⏸ WAITING • Check imminent');
            return;
          }
        }
      }

      // For other activity types, show time since
      let icon = '●';
      let label = 'ACTIVE';

      if (latestActivity.type === 'trade_entry_long') {
        icon = '↑';
        label = 'LONG ENTERED';
      } else if (latestActivity.type === 'trade_entry_short') {
        icon = '↓';
        label = 'SHORT ENTERED';
      } else if (latestActivity.type === 'market_query') {
        icon = '📊';
        label = 'QUERIED MARKET';
      } else if (latestActivity.type === 'analysis') {
        icon = '💭';
        label = 'ANALYZING';
      }

      const timeAgo = diffMins > 0 ? `${diffMins}m ago` : `${diffSecs}s ago`;
      setStatusText(`${icon} ${label} • ${timeAgo}`);
    };

    updateStatus();
    const interval = setInterval(updateStatus, 1000);
    return () => clearInterval(interval);
  }, [latestActivity]);

  const info = metadata;

  // Get status color based on activity type
  const getStatusColor = () => {
    if (!latestActivity) return VIBE.brass;
    if (latestActivity.type === 'trade_entry_long') return '#16a34a';
    if (latestActivity.type === 'trade_entry_short') return '#dc2626';
    if (latestActivity.type === 'market_query') return VIBE.signal;
    if (latestActivity.type === 'analysis') return VIBE.brass;
    if (latestActivity.type === 'agent_wait') return VIBE.ivory;
    return VIBE.brass;
  };

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
        @keyframes statusPulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.6;
            transform: scale(1.2);
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
              <div className="flex items-center gap-2 font-mono text-xs sm:text-sm" style={{ color: 'rgba(237,235,231,0.7)' }}>
                <div
                  className="w-2 h-2 rounded-full"
                  style={{
                    backgroundColor: getStatusColor(),
                    animation: 'statusPulse 2s ease-in-out infinite'
                  }}
                />
                <span>{statusText || 'ARENA STATUS'}</span>
              </div>
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
        <div className="rounded-xl border overflow-hidden relative" style={{ backgroundColor: VIBE.carbon, borderColor: VIBE.hair, height: variant === 'embedded' ? '600px' : 'calc(100vh - 280px)', minHeight: '400px' }}>
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
                  {selectedActivity.type === 'trade_entry_long' && '↑ LONG ENTRY'}
                  {selectedActivity.type === 'trade_entry_short' && '↓ SHORT ENTRY'}
                  {selectedActivity.type === 'market_query' && '📊 MARKET QUERY'}
                  {selectedActivity.type === 'analysis' && '💭 AGENT THOUGHT'}
                  {selectedActivity.type === 'agent_wait' && '⏸ WAITING'}
                </div>
                {selectedActivity.data.summary && (
                  <div className="text-sm mb-1 prose prose-invert prose-sm max-w-none" style={{ color: VIBE.ivory }}>
                    <ReactMarkdown>
                      {selectedActivity.data.summary.length > 100
                        ? selectedActivity.data.summary.slice(0, 100) + '...'
                        : selectedActivity.data.summary}
                    </ReactMarkdown>
                  </div>
                )}
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
                      fontSize: selectedActivity.type.includes('trade_entry') ? '40px' : '20px',
                      color: selectedActivity.type === 'trade_entry_long' ? '#16a34a' :
                             selectedActivity.type === 'trade_entry_short' ? '#dc2626' :
                             selectedActivity.type === 'market_query' ? VIBE.signal :
                             selectedActivity.type === 'analysis' ? VIBE.brass : VIBE.ivory,
                      lineHeight: 1,
                      animation: 'markerPulse 1.5s ease-in-out infinite'
                    }}
                  >
                    {selectedActivity.type === 'trade_entry_long' && '▲'}
                    {selectedActivity.type === 'trade_entry_short' && '▼'}
                    {(selectedActivity.type === 'market_query' ||
                      selectedActivity.type === 'analysis' ||
                      selectedActivity.type === 'agent_wait') && '●'}
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
        isOpen={detailActivities.length > 0}
        onClose={() => setDetailActivities([])}
        title={
          detailActivities.length === 1
            ? detailActivities[0].type === 'trade_entry_long' ? 'Long Entry' :
              detailActivities[0].type === 'trade_entry_short' ? 'Short Entry' :
              detailActivities[0].type === 'market_query' ? 'Market Query' :
              detailActivities[0].type === 'analysis' ? 'Agent Thought' :
              detailActivities[0].type === 'agent_wait' ? 'Agent Waiting' :
              'Activity'
            : `${detailActivities.length} Activities`
        }
      >
        {detailActivities.length > 0 && (
          <div className="px-6 py-4 space-y-6 max-h-[calc(80vh-120px)] overflow-y-auto">
            {/* Show timestamp once at top if all activities share same timestamp */}
            <div>
              <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                Timestamp
              </div>
              <div className="text-sm font-mono">
                {new Date(detailActivities[0].timestamp).toLocaleString('en-US', {
                  dateStyle: 'medium',
                  timeStyle: 'medium'
                })}
              </div>
            </div>

            {/* Loop through all activities */}
            {detailActivities.map((detailActivity, index) => (
              <div key={detailActivity.id || index} className="pb-6 border-b last:border-b-0" style={{ borderColor: VIBE.hair }}>
                {/* Activity Type Badge */}
                <div className="inline-block px-3 py-1 rounded-lg text-xs uppercase tracking-wider font-semibold mb-4" style={{
                  backgroundColor:
                    detailActivity.type === 'trade_entry_long' ? '#16a34a' :
                    detailActivity.type === 'trade_entry_short' ? '#dc2626' :
                    detailActivity.type === 'market_query' ? VIBE.signal :
                    detailActivity.type === 'analysis' ? VIBE.brass :
                    detailActivity.type === 'agent_wait' ? VIBE.ivory : VIBE.brass,
                  color: detailActivity.type === 'agent_wait' ? VIBE.obsidian : VIBE.ivory
                }}>
                  {detailActivity.type === 'trade_entry_long' && '↑ Long Entry'}
                  {detailActivity.type === 'trade_entry_short' && '↓ Short Entry'}
                  {detailActivity.type === 'market_query' && '📊 Market Query'}
                  {detailActivity.type === 'analysis' && '💭 Agent Thought'}
                  {detailActivity.type === 'agent_wait' && '⏸ Waiting'}
                </div>

                {/* Type-specific content */}
                <div className="space-y-4">

            {/* TRADE ENTRY SPECIFIC FIELDS */}
            {(detailActivity.type === 'trade_entry_long' || detailActivity.type === 'trade_entry_short') ? (
              <>
                {detailActivity.data.confidence !== undefined ? (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Confidence
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-black bg-opacity-30 rounded-full h-2 overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${(detailActivity.data.confidence || 0) * 100}%`,
                            backgroundColor: VIBE.signal
                          }}
                        />
                      </div>
                      <span className="text-sm font-semibold">{Math.round((detailActivity.data.confidence || 0) * 100)}%</span>
                    </div>
                  </div>
                 ) : null}

                {detailActivity.data.leverage ? (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Leverage
                    </div>
                    <div className="text-lg font-semibold">{detailActivity.data.leverage}x</div>
                  </div>
                 ) : null}

                {detailActivity.data.entry_price ? (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Entry Price
                    </div>
                    <div className="text-lg font-mono">${detailActivity.data.entry_price.toLocaleString()}</div>
                  </div>
                 ) : null}

                <div className="grid grid-cols-2 gap-4">
                  {detailActivity.data.stop_loss_price ? (
                    <div>
                      <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                        Stop Loss
                      </div>
                      <div className="text-sm font-mono" style={{ color: VIBE.ember }}>
                        ${detailActivity.data.stop_loss_price.toLocaleString()}
                      </div>
                    </div>
                  ) : null}

                  {detailActivity.data.take_profit_price ? (
                    <div>
                      <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                        Take Profit
                      </div>
                      <div className="text-sm font-mono" style={{ color: VIBE.signal }}>
                        ${detailActivity.data.take_profit_price.toLocaleString()}
                      </div>
                    </div>
                  ) : null}
                </div>
              </>
            ) : null}

            {/* MARKET QUERY SPECIFIC FIELDS */}
            {detailActivity.type === 'market_query' && detailActivity.data.details ? (
              <>
                {detailActivity.data.details.timeframe && (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Timeframe
                    </div>
                    <div className="text-sm">{String(detailActivity.data.details.timeframe)}</div>
                  </div>
                 )}

                {detailActivity.data.details.categories && typeof detailActivity.data.details.categories === 'object' && (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-2" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Data Requested
                    </div>
                    {Object.entries(detailActivity.data.details.categories).map(([category, indicators]) => (
                      <div key={category} className="mb-2">
                        <div className="text-xs font-semibold mb-1" style={{ color: VIBE.signal }}>
                          {category}:
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {Array.isArray(indicators) && indicators.map((ind: unknown, i: number) => (
                            <span
                              key={i}
                              className="px-2 py-1 rounded text-xs"
                              style={{ backgroundColor: 'rgba(0, 217, 255, 0.2)', color: VIBE.signal }}
                            >
                              {String(ind)}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                 )}

                {/* Display actual market data received */}
                {detailActivity.data.details && (detailActivity.data.details as Record<string, unknown>).market_data && (
                  <div className="mt-4">
                    <div className="text-xs uppercase tracking-wider mb-2" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Market Data Received
                    </div>

                    {/* Technical Indicators */}
                    {((detailActivity.data.details as Record<string, unknown>).market_data as Record<string, unknown>)?.technicals &&
                     (((detailActivity.data.details as Record<string, unknown>).market_data as Record<string, unknown>).technicals as Record<string, unknown>)?.indicators ? (
                      <div className="mb-4">
                        <div className="text-xs font-semibold mb-2" style={{ color: VIBE.brass }}>
                          Technical Indicators:
                        </div>
                        {Object.entries((((detailActivity.data.details as Record<string, unknown>).market_data as Record<string, unknown>).technicals as Record<string, unknown>).indicators as Record<string, unknown>).map(([indName, indData]: [string, unknown]) => {
                          const indicator = indData as Record<string, unknown>;
                          return (
                          <div key={indName} className="mb-3 p-3 rounded-lg" style={{ backgroundColor: 'rgba(193, 168, 125, 0.1)' }}>
                            <div className="font-semibold mb-1" style={{ color: VIBE.brass }}>{indName}</div>

                            {/* Current Value */}
                            {indicator.current ? (
                              <div className="text-sm mb-1">
                                Value: <span className="font-mono">{typeof indicator.current === 'object' ? JSON.stringify((indicator.current as Record<string, unknown>).value || indicator.current) : String(indicator.current)}</span>
                              </div>
                            ) : null}

                            {/* Trend */}
                            {indicator.context && typeof indicator.context === 'object' && (indicator.context as Record<string, unknown>).trend ? (
                              <div className="text-sm mb-1">
                                Trend: <span className="font-mono">{String(((indicator.context as Record<string, unknown>).trend as Record<string, unknown>).direction)}</span>
                                {((indicator.context as Record<string, unknown>).trend as Record<string, unknown>).strength ? <span className="ml-2">({(Number(((indicator.context as Record<string, unknown>).trend as Record<string, unknown>).strength) * 100).toFixed(1)}%)</span> : null}
                              </div>
                            ) : null}

                            {/* Patterns */}
                            {indicator.patterns && typeof indicator.patterns === 'object' && Object.keys(indicator.patterns as Record<string, unknown>).length > 0 ? (
                              <div className="text-sm">
                                Patterns: {Object.keys(indicator.patterns as Record<string, unknown>).map(p => (
                                  <span key={p} className="inline-block px-2 py-0.5 mr-1 rounded text-xs" style={{ backgroundColor: 'rgba(193, 168, 125, 0.3)' }}>
                                    {p}
                                  </span>
                                ))}
                              </div>
                            ) : null}
                          </div>
                        );
                        })}
                      </div>
                    ) : null}

                    {/* Market Intelligence */}
                    {(((detailActivity.data.details as Record<string, unknown>).market_data as Record<string, unknown>)?.market_intelligence) ? (
                      <div>
                        <div className="text-xs font-semibold mb-2" style={{ color: VIBE.signal }}>
                          Market Intelligence:
                        </div>
                        {Object.entries(((detailActivity.data.details as Record<string, unknown>).market_data as Record<string, unknown>).market_intelligence as Record<string, unknown>).map(([source, data]: [string, unknown]) => (
                          <div key={source} className="mb-2 p-3 rounded-lg" style={{ backgroundColor: 'rgba(60, 166, 224, 0.1)' }}>
                            <div className="font-semibold mb-1 text-sm" style={{ color: VIBE.signal }}>
                              {source.replace(/_/g, ' ').toUpperCase()}
                            </div>
                            <pre className="text-xs font-mono overflow-x-auto" style={{ color: VIBE.ivory }}>
                              {JSON.stringify(data, null, 2)}
                            </pre>
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                )}
              </>
            ) : null}

            {/* ANALYSIS SPECIFIC FIELDS */}
            {detailActivity.type === 'analysis' && detailActivity.data.details?.thought ? (
              <div>
                <div className="text-xs uppercase tracking-wider mb-2" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  Agent Thought
                </div>
                <div
                  className="prose prose-invert prose-sm max-w-none"
                  style={{ color: VIBE.ivory }}
                >
                  <ReactMarkdown>{String(detailActivity.data.details.thought)}</ReactMarkdown>
                </div>

                {detailActivity.data.details.balance && typeof detailActivity.data.details.balance === 'number' ? (
                  <div className="mt-4 p-3 rounded-lg" style={{ backgroundColor: 'rgba(0, 217, 255, 0.1)' }}>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Balance at Time
                    </div>
                    <div className="text-lg font-semibold" style={{ color: VIBE.signal }}>
                      ${detailActivity.data.details.balance.toFixed(2)}
                    </div>
                  </div>
                 ) : null}
              </div>
            ) : null}

            {/* AGENT WAIT SPECIFIC FIELDS */}
            {detailActivity.type === 'agent_wait' && detailActivity.data.details ? (
              <>
                {detailActivity.data.details.duration_minutes && typeof detailActivity.data.details.duration_minutes === 'number' && (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Wait Duration
                    </div>
                    <div className="text-lg font-semibold">{detailActivity.data.details.duration_minutes} minutes</div>
                  </div>
                 )}

                {detailActivity.data.details.next_check_at && (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Next Check
                    </div>
                    <div className="text-sm font-mono">
                      {new Date(String(detailActivity.data.details.next_check_at)).toLocaleString('en-US', {
                        dateStyle: 'medium',
                        timeStyle: 'medium'
                      })}
                    </div>
                  </div>
                 )}

                {detailActivity.data.details.reason && (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-2" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Reason
                    </div>
                    <div
                      className="prose prose-invert prose-sm max-w-none"
                      style={{ color: VIBE.ivory }}
                    >
                      <ReactMarkdown>{String(detailActivity.data.details.reason)}</ReactMarkdown>
                    </div>
                  </div>
                 )}
              </>
            ) : null}

            {/* Summary (for all types that have it) */}
            {detailActivity.data.summary ? (
              <div>
                <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  Summary
                </div>
                <div className="prose prose-invert prose-sm max-w-none" style={{ color: VIBE.ivory }}>
                  <ReactMarkdown>{detailActivity.data.summary}</ReactMarkdown>
                </div>
              </div>
            ) : null}
                </div>
              </div>
            ))}
          </div>
        )}
      </BottomSheet>
    </div>
  );
}
