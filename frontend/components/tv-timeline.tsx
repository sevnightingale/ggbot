'use client';

import React, { useEffect, useState, useRef } from 'react';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, LineData, Time, SeriesMarker } from 'lightweight-charts';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import type { Session } from '@supabase/supabase-js';
import BottomSheet from './bottom-sheet';
import ReactMarkdown from 'react-markdown';
import { useTheme } from '@/lib/theme';

// Theme-aware color palette
const getThemeColors = (isDark: boolean) => ({
  // Dark mode colors
  dark: {
    obsidian: '#0B0B0C',   // page background
    carbon: '#141416',     // card surface
    ivory: '#EDEBE7',      // main text
    hair: 'rgba(237,235,231,0.16)', // hairline borders
    brass: '#C1A87D',      // accent / primary (buttons)
    signal: '#3CA6E0',     // equity line, data highlights
    ember: '#D74A1F',      // negative
    lilac: '#8B7CF2',      // thoughts
  },
  // Light mode colors
  light: {
    obsidian: '#f8f7f4',   // page background (warm parchment)
    carbon: '#edebe7',     // card surface (ivory)
    ivory: '#1a1816',      // main text (near-black)
    hair: 'rgba(26,24,22,0.16)', // hairline borders (inverted)
    brass: '#C1A87D',      // accent (same as dark)
    signal: '#3CA6E0',     // equity line (same as dark)
    ember: '#D74A1F',      // negative (same as dark)
    lilac: '#8B7CF2',      // thoughts (same as dark)
  }
})[isDark ? 'dark' : 'light'];

// Formatting helpers for activity data (handles null/undefined gracefully)
const formatActivityPrice = (price: number | null | undefined): string => {
  if (price == null) return '—';
  return `$${price.toFixed(2)}`;
};

const formatActivityPercent = (value: number | null | undefined): string => {
  if (value == null) return 'N/A';
  return `${(value * 100).toFixed(1)}%`;
};

const formatActivityUSD = (value: number | null | undefined): string => {
  if (value == null) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}$${value.toFixed(2)}`;
};

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
  const { theme } = useTheme();
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

  // Refs to avoid stale closures and enable cross-effect communication
  const sessionRef = useRef<Session | null>(null);
  const fetchDataRef = useRef<(() => Promise<void>) | null>(null);
  const fetchAbortControllerRef = useRef<AbortController | null>(null);

  // Fast-click detection: track mousedown time to distinguish quick clicks from drag/pan
  const mouseDownTimeRef = useRef<number>(0);
  const FAST_CLICK_THRESHOLD_MS = 200;

  // Get theme colors
  const VIBE = getThemeColors(theme === 'dark');

  // Get session for auth
  useEffect(() => {
    const supabase = createClientComponentClient();
    const getSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setSession(session);
      sessionRef.current = session; // Keep ref in sync
    };
    getSession();
  }, []);

  // Keep session ref up to date when session changes
  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  // Update chart colors when theme changes
  useEffect(() => {
    if (!chartRef.current) return;

    const colors = getThemeColors(theme === 'dark');

    // Update chart layout colors
    chartRef.current.applyOptions({
      layout: {
        background: { type: ColorType.Solid, color: colors.carbon },
        textColor: colors.hair,
      },
      grid: {
        vertLines: { color: colors.hair },
        horzLines: { color: colors.hair },
      },
      rightPriceScale: {
        borderColor: colors.hair,
      },
      timeScale: {
        borderColor: colors.hair,
      },
      crosshair: {
        vertLine: {
          color: colors.brass,
        },
        horzLine: {
          color: colors.brass,
        },
      },
    });

    // Update line series color
    if (lineSeriesRef.current) {
      lineSeriesRef.current.applyOptions({
        color: colors.brass,
      });
    }
  }, [theme]);

  // Chart creation and data polling - only recreates when switching bots or container changes
  // NOTE: session is NOT a dependency - fetchData reads current session via ref
  useEffect(() => {
    console.log('Chart creation effect:', { configId, hasContainer: !!chartContainer });

    if (!configId || !chartContainer) {
      console.log('Early return - missing configId or container');
      return;
    }

    // Clean up existing chart when switching bots
    if (chartRef.current) {
      console.log('Cleaning up existing chart (switching bots)');
      chartRef.current.remove();
      chartRef.current = null;
      lineSeriesRef.current = null;
    }

    const containerWidth = chartContainer.clientWidth;
    const containerHeight = chartContainer.clientHeight;

    console.log('Creating chart with dimensions:', { width: containerWidth, height: containerHeight });

    // Reset first load flag when creating new chart
    isFirstLoadRef.current = true;

    // Ensure all color values are valid (not null/undefined)
    const colors = getThemeColors(theme === 'dark');
    const carbonColor = colors.carbon || '#141416';
    const hairColor = colors.hair || 'rgba(237,235,231,0.16)';
    const brassColor = colors.brass || '#C1A87D';

    const chart = createChart(chartContainer, {
      width: containerWidth,
      height: containerHeight,
      layout: {
        background: { type: ColorType.Solid, color: carbonColor },
        textColor: hairColor,
      },
      grid: {
        vertLines: { color: hairColor, style: LineStyle.Dotted },
        horzLines: { color: hairColor, style: LineStyle.Dotted },
      },
      rightPriceScale: {
        borderColor: hairColor,
      },
      timeScale: {
        borderColor: hairColor,
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: brassColor,
          width: 1,
          style: LineStyle.Dashed,
        },
        horzLine: {
          color: brassColor,
          width: 1,
          style: LineStyle.Dashed,
        },
      },
      localization: {
        priceFormatter: (price: number) => {
          if (price == null || isNaN(price)) return '$—';
          return `$${price.toFixed(2)}`;
        },
      },
    });

    chartRef.current = chart;
    console.log('Chart created:', !!chart);

    const lineSeries = chart.addLineSeries({
      color: brassColor,
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      lastValueVisible: true,
      priceLineVisible: false,
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

    // Track mousedown time for fast-click detection
    const handleMouseDown = () => {
      mouseDownTimeRef.current = Date.now();
    };
    chartContainer.addEventListener('mousedown', handleMouseDown);
    chartContainer.addEventListener('touchstart', handleMouseDown);

    // Click handler - open activity detail only on fast clicks (< 200ms)
    // This prevents accidental opens when panning/dragging the chart
    chart.subscribeClick((param) => {
      if (!param.time) return;

      // Check if this was a fast click (not a drag/pan)
      const clickDuration = Date.now() - mouseDownTimeRef.current;
      if (clickDuration > FAST_CLICK_THRESHOLD_MS) {
        console.log('Slow click ignored (drag/pan):', clickDuration, 'ms');
        return;
      }

      const timestamp = typeof param.time === 'number' ? param.time : parseFloat(param.time as string);
      const activities = activitiesMapRef.current.get(timestamp);

      if (activities && activities.length > 0) {
        console.log('Fast click on activities:', activities, 'duration:', clickDuration, 'ms');
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

    const fetchData = async () => {
      try {
        // Guard: Don't fetch if component is unmounted or chart destroyed
        if (!chartRef.current || !lineSeriesRef.current) {
          console.log('fetchData skipped - chart or line series destroyed');
          return;
        }

        // CRITICAL: Abort any previous in-flight fetchData call
        if (fetchAbortControllerRef.current) {
          console.log('Aborting previous fetchData call');
          fetchAbortControllerRef.current.abort();
        }

        // Create new AbortController for THIS fetch
        const abortController = new AbortController();
        fetchAbortControllerRef.current = abortController;

        console.log('fetchData starting...', { configId, hasAuth: !!sessionRef.current });
        setLoading(true);
        setError(null);

        // Read current session from ref (not stale closure)
        const headers: HeadersInit = sessionRef.current?.access_token
          ? { Authorization: `Bearer ${sessionRef.current.access_token}` }
          : {};

        console.log('Fetching from API...');
        const [balanceSeriesRes, activitiesRes, metadataRes] = await Promise.all([
          fetch(`/api/v2/snapshots/${configId}/balance-series`, {
            headers,
            signal: abortController.signal
          }),
          fetch(`/api/v2/activities/${configId}`, {
            headers,
            signal: abortController.signal
          }),
          fetch(`/api/v2/activities/${configId}/metadata`, {
            headers,
            signal: abortController.signal
          }),
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

        // Simplified: Backend already merges snapshots + activities
        // Just convert timestamps and use balance values directly
        const chartData: LineData[] = balancePoints
          .filter(point => point.timestamp && point.balance != null)  // Filter null/invalid points
          .map(point => ({
            time: Math.floor(new Date(point.timestamp).getTime() / 1000) as Time,
            value: point.balance
          }))
          .filter(point => !isNaN(point.time as number) && point.value != null)  // Extra safety check
          .sort((a, b) => {
            const timeA = typeof a.time === 'number' ? a.time : parseFloat(a.time as string);
            const timeB = typeof b.time === 'number' ? b.time : parseFloat(b.time as string);
            return timeA - timeB;
          });

        console.log('Chart data points (snapshots + activities):', chartData.length);

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

          // Defensive validation before passing to TradingView
          const invalidPoints = chartData.filter(p =>
            p.time == null ||
            p.value == null ||
            typeof p.time !== 'number' ||
            typeof p.value !== 'number' ||
            isNaN(p.time) ||
            isNaN(p.value) ||
            !isFinite(p.time) ||  // Catch Infinity/-Infinity
            !isFinite(p.value)     // Catch Infinity/-Infinity
          );

          if (invalidPoints.length > 0) {
            console.error('❌ INVALID CHART DATA POINTS (found Infinity, NaN, or null):', invalidPoints);
            throw new Error(`Found ${invalidPoints.length} invalid chart data points`);
          }

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

          // Create a Set of valid timestamps from chartData for marker validation
          const validTimestamps = new Set(chartData.map(point => point.time as number));

          groupedByTimestamp.forEach((activitiesAtTime, timestamp) => {
            // Skip markers for timestamps not in the chart data (prevents TradingView errors)
            if (!validTimestamps.has(timestamp)) {
              return;
            }
            // Determine marker type based on priority (NEW: AI consciousness markers)
            // Trade events = arrows above/below line (vertical movement)
            // Observation events = circles on the line (neutral position)

            const hasTradeLong = activitiesAtTime.some(a =>
              a.type === 'trade_entry' && a.data?.details?.side === 'long'
            );
            const hasTradeShort = activitiesAtTime.some(a =>
              a.type === 'trade_entry' && a.data?.details?.side === 'short'
            );
            const tradeExitActivity = activitiesAtTime.find(a => a.type === 'trade_exit');
            const hasLLMThought = activitiesAtTime.some(a => a.type === 'llm_thought');
            const hasMarketQuery = activitiesAtTime.some(a => a.type === 'market_query');
            const hasAgentWait = activitiesAtTime.some(a => a.type === 'agent_wait');
            const hasBotCreated = activitiesAtTime.some(a => a.type === 'bot_created');

            // TRADE EVENTS (arrows, above/below line)
            if (hasTradeLong) {
              markers.push({
                time: timestamp as Time,
                position: 'belowBar',
                color: '#16a34a', // solid green
                shape: 'arrowUp',
                size: 2,
              });
            } else if (hasTradeShort) {
              markers.push({
                time: timestamp as Time,
                position: 'aboveBar',
                color: '#dc2626', // solid red
                shape: 'arrowDown',
                size: 2,
              });
            } else if (tradeExitActivity) {
              // Determine profit/loss from P&L
              const pnl = Number(tradeExitActivity.data?.details?.pnl || 0);
              const isProfit = pnl > 0;

              markers.push({
                time: timestamp as Time,
                position: isProfit ? 'aboveBar' : 'belowBar', // Profit up, loss down
                color: isProfit ? '#16a34a' : '#dc2626', // green for profit, red for loss
                shape: 'circle',
                size: 0.75, // Small circles with text labels
                text: `${isProfit ? '+' : ''}$${pnl.toFixed(2)}`, // Show P&L amount
              });
            }
            // OBSERVATION EVENTS (circles, on the line)
            else if (hasLLMThought) {
              markers.push({
                time: timestamp as Time,
                position: 'inBar',
                color: '#C1A87D', // solid brass (matching line)
                shape: 'circle',
                size: 1, // standard circle size
              });
            } else if (hasMarketQuery) {
              markers.push({
                time: timestamp as Time,
                position: 'inBar',
                color: '#3CA6E0', // solid signal blue
                shape: 'circle',
                size: 1, // standard circle size
              });
            } else if (hasAgentWait) {
              markers.push({
                time: timestamp as Time,
                position: 'inBar',
                color: '#9ca3af', // solid gray
                shape: 'circle',
                size: 1, // standard circle size
              });
            } else if (hasBotCreated) {
              markers.push({
                time: timestamp as Time,
                position: 'inBar',
                color: '#16a34a', // green for new creation
                shape: 'circle',
                size: 1.5, // slightly larger for lifecycle event
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

            // Defensive validation before passing to TradingView
            const invalidMarkers = sortedMarkers.filter(m =>
              m.time == null ||
              m.position == null ||
              m.color == null ||
              m.shape == null ||
              m.size == null ||
              typeof m.time !== 'number' ||
              isNaN(m.time) ||
              !isFinite(m.time)  // Catch Infinity/-Infinity
            );

            if (invalidMarkers.length > 0) {
              console.error('❌ INVALID MARKERS (found Infinity, NaN, or null):', invalidMarkers);
              throw new Error(`Found ${invalidMarkers.length} invalid markers`);
            }

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
        // Ignore AbortError - it's expected when component unmounts or chart changes
        if (err instanceof Error && err.name === 'AbortError') {
          console.log('fetchData aborted (chart cleanup)');
          return;
        }
        console.error('Error fetching timeline data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setLoading(false);
      }
    };

    // Store fetchData in ref so session effect can call it
    fetchDataRef.current = fetchData;

    console.log('About to call fetchData...');
    fetchData();

    console.log('Setting up polling interval...');
    const intervalId = setInterval(fetchData, 10000);

    return () => {
      console.log('Cleanup: Aborting fetches and removing chart');
      // Abort any in-flight fetchData call
      if (fetchAbortControllerRef.current) {
        fetchAbortControllerRef.current.abort();
        fetchAbortControllerRef.current = null;
      }
      clearInterval(intervalId);
      // Clean up mousedown listeners
      chartContainer.removeEventListener('mousedown', handleMouseDown);
      chartContainer.removeEventListener('touchstart', handleMouseDown);
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
        lineSeriesRef.current = null;
      }
      fetchDataRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [configId, chartContainer]); // NOTE: session and theme NOT in dependencies
  // - session: prevents double render, fetchData reads current value via ref
  // - theme: separate effect handles color updates dynamically

  // Refetch data when session loads (for RLS auth) - without recreating chart
  useEffect(() => {
    if (session && chartRef.current && lineSeriesRef.current && fetchDataRef.current) {
      console.log('Session loaded, refetching data with auth');
      fetchDataRef.current();
    }
  }, [session]);

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

      // NEW: unified activity type detection
      const isLongEntry = latestActivity.type === 'trade_entry' && latestActivity.data?.details?.side === 'long';
      const isShortEntry = latestActivity.type === 'trade_entry' && latestActivity.data?.details?.side === 'short';

      if (isLongEntry) {
        icon = '↑';
        label = 'LONG ENTERED';
      } else if (isShortEntry) {
        icon = '↓';
        label = 'SHORT ENTERED';
      } else if (latestActivity.type === 'trade_exit') {
        icon = '⨯';
        label = 'POSITION CLOSED';
      } else if (latestActivity.type === 'market_query') {
        icon = '📊';
        label = 'QUERIED MARKET';
      } else if (latestActivity.type === 'llm_thought') {
        icon = '💭';
        label = 'ANALYZING';
      } else if (latestActivity.type === 'price_check') {
        icon = '💱';
        label = 'PRICE CHECK';
      } else if (latestActivity.type === 'observation_recorded') {
        icon = '📝';
        label = 'RECORDED';
      } else if (latestActivity.type === 'strategy_updated') {
        icon = '⚙️';
        label = 'CONFIG UPDATED';
      } else if (latestActivity.type === 'signal_received') {
        icon = '📡';
        label = 'SIGNAL';
      } else if (latestActivity.type === 'bot_created') {
        icon = '🤖';
        label = 'BOT CREATED';
      }

      const timeAgo = diffMins > 0 ? `${diffMins}m ago` : `${diffSecs}s ago`;
      setStatusText(`${icon} ${label} • ${timeAgo}`);
    };

    updateStatus();
    const interval = setInterval(updateStatus, 1000);
    return () => clearInterval(interval);
  }, [latestActivity]);

  const info = metadata;

  // Get status color based on activity type (NEW: unified types)
  const getStatusColor = () => {
    if (!latestActivity) return VIBE.brass;

    const isLongEntry = latestActivity.type === 'trade_entry' && latestActivity.data?.details?.side === 'long';
    const isShortEntry = latestActivity.type === 'trade_entry' && latestActivity.data?.details?.side === 'short';

    if (isLongEntry) return '#16a34a';
    if (isShortEntry) return '#dc2626';
    if (latestActivity.type === 'trade_exit') return '#9ca3af'; // gray-400
    if (latestActivity.type === 'market_query') return VIBE.signal;
    if (latestActivity.type === 'llm_thought') return VIBE.brass;
    if (latestActivity.type === 'agent_wait') return VIBE.ivory;
    if (latestActivity.type === 'price_check') return VIBE.signal;
    if (latestActivity.type === 'observation_recorded') return VIBE.brass;
    if (latestActivity.type === 'strategy_updated') return VIBE.signal;
    if (latestActivity.type === 'signal_received') return VIBE.signal;
    if (latestActivity.type === 'bot_created') return '#16a34a'; // green for creation
    return VIBE.brass;
  };

  return (
    <div className={`relative w-full font-sans ${variant === 'standalone' ? 'min-h-screen' : ''}`} style={{ backgroundColor: VIBE.obsidian, color: VIBE.ivory }}>
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
      {/* HEADER - Only shown in standalone mode, hidden in embedded mode (KPIs shown in ActivationBar) */}
      {variant === 'standalone' && (
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
                  { k: 'Perf', v: typeof info.performance === 'number' && info.performance != null ? `${info.performance.toFixed(2)}%` : 'N/A' },
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
      )}

      {/* CHART */}
      <section className="max-w-7xl mx-auto">
        <div className="rounded-xl border p-4 relative" style={{ backgroundColor: VIBE.carbon, borderColor: VIBE.hair, height: variant === 'embedded' ? '600px' : 'calc(100vh - 280px)', minHeight: '400px' }}>
          <div ref={setChartContainer} style={{ width: '100%', height: '100%' }} />

          {/* Activity hover tooltip */}
          {selectedActivity && (
            <>
              {/* Tooltip card - clickable to open details */}
              <div
                className="absolute bottom-4 left-4 rounded-lg border px-4 py-3 cursor-pointer transition-all hover:scale-[1.02]"
                style={{
                  backgroundColor: VIBE.carbon,
                  borderColor: VIBE.brass,
                  borderWidth: '2px',
                  maxWidth: '300px',
                  zIndex: 10
                }}
                onClick={() => {
                  // Get all activities at this timestamp and open bottom sheet
                  const timestamp = Math.floor(new Date(selectedActivity.timestamp).getTime() / 1000);
                  const activities = activitiesMapRef.current.get(timestamp);
                  if (activities && activities.length > 0) {
                    setDetailActivities(activities);
                  } else {
                    setDetailActivities([selectedActivity]);
                  }
                }}
              >
                <div className="text-xs uppercase tracking-wider mb-1" style={{ color: VIBE.brass }}>
                  {selectedActivity.type === 'trade_entry' && selectedActivity.data?.details?.side === 'long' && '↑ LONG ENTRY'}
                  {selectedActivity.type === 'trade_entry' && selectedActivity.data?.details?.side === 'short' && '↓ SHORT ENTRY'}
                  {selectedActivity.type === 'trade_exit' && '⨯ POSITION CLOSED'}
                  {selectedActivity.type === 'market_query' && '📊 MARKET QUERY'}
                  {selectedActivity.type === 'llm_thought' && '💭 AGENT THOUGHT'}
                  {selectedActivity.type === 'price_check' && '💱 PRICE CHECK'}
                  {selectedActivity.type === 'agent_wait' && '⏸ WAITING'}
                  {selectedActivity.type === 'observation_recorded' && '📝 OBSERVATION'}
                  {selectedActivity.type === 'strategy_updated' && '⚙️ STRATEGY UPDATE'}
                  {selectedActivity.type === 'signal_received' && '📡 SIGNAL RECEIVED'}
                  {selectedActivity.type === 'bot_created' && '🤖 BOT CREATED'}
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
                  <div className="text-xs mt-1" style={{ color: VIBE.signal }}>
                    {selectedActivity.data.symbol}
                  </div>
                )}
                {/* View Details hint */}
                <div className="text-xs mt-2 pt-2 border-t flex items-center gap-1" style={{ borderColor: VIBE.hair, color: VIBE.brass }}>
                  <span>Click to view details</span>
                  <span>→</span>
                </div>
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
                      fontSize: selectedActivity.type === 'trade_entry' ? '40px' : '20px',
                      color: selectedActivity.type === 'trade_entry' && selectedActivity.data?.details?.side === 'long' ? '#16a34a' :
                             selectedActivity.type === 'trade_entry' && selectedActivity.data?.details?.side === 'short' ? '#dc2626' :
                             selectedActivity.type === 'trade_exit' ? '#9ca3af' :
                             selectedActivity.type === 'market_query' ? VIBE.signal :
                             selectedActivity.type === 'llm_thought' ? VIBE.brass : VIBE.ivory,
                      lineHeight: 1,
                      animation: 'markerPulse 1.5s ease-in-out infinite'
                    }}
                  >
                    {selectedActivity.type === 'trade_entry' && selectedActivity.data?.details?.side === 'long' && '▲'}
                    {selectedActivity.type === 'trade_entry' && selectedActivity.data?.details?.side === 'short' && '▼'}
                    {selectedActivity.type === 'trade_exit' && '⨯'}
                    {(selectedActivity.type === 'market_query' ||
                      selectedActivity.type === 'llm_thought' ||
                      selectedActivity.type === 'price_check' ||
                      selectedActivity.type === 'agent_wait' ||
                      selectedActivity.type === 'observation_recorded' ||
                      selectedActivity.type === 'strategy_updated' ||
                      selectedActivity.type === 'signal_received') && '●'}
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
            ? detailActivities[0].type === 'trade_entry' && detailActivities[0].data?.details?.side === 'long' ? 'Long Entry' :
              detailActivities[0].type === 'trade_entry' && detailActivities[0].data?.details?.side === 'short' ? 'Short Entry' :
              detailActivities[0].type === 'trade_exit' ? 'Position Closed' :
              detailActivities[0].type === 'market_query' ? 'Market Query' :
              detailActivities[0].type === 'llm_thought' ? 'Agent Thought' :
              detailActivities[0].type === 'price_check' ? 'Price Check' :
              detailActivities[0].type === 'agent_wait' ? 'Agent Waiting' :
              detailActivities[0].type === 'observation_recorded' ? 'Observation' :
              detailActivities[0].type === 'strategy_updated' ? 'Strategy Update' :
              detailActivities[0].type === 'signal_received' ? 'Signal Received' :
              detailActivities[0].type === 'bot_created' ? 'Bot Created' :
              'Activity'
            : `${detailActivities.length} Activities`
        }
      >
        {detailActivities.length > 0 && (
          <div className="px-6 py-4 space-y-6">
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
                    detailActivity.type === 'trade_entry' && detailActivity.data?.details?.side === 'long' ? '#16a34a' :
                    detailActivity.type === 'trade_entry' && detailActivity.data?.details?.side === 'short' ? '#dc2626' :
                    detailActivity.type === 'trade_exit' ? '#9ca3af' :
                    detailActivity.type === 'market_query' ? VIBE.signal :
                    detailActivity.type === 'llm_thought' ? VIBE.brass :
                    detailActivity.type === 'agent_wait' ? VIBE.ivory :
                    detailActivity.type === 'bot_created' ? '#16a34a' : VIBE.brass,
                  color: detailActivity.type === 'agent_wait' ? VIBE.obsidian : VIBE.ivory
                }}>
                  {detailActivity.type === 'trade_entry' && detailActivity.data?.details?.side === 'long' && '↑ Long Entry'}
                  {detailActivity.type === 'trade_entry' && detailActivity.data?.details?.side === 'short' && '↓ Short Entry'}
                  {detailActivity.type === 'trade_exit' && '⨯ Position Closed'}
                  {detailActivity.type === 'market_query' && '📊 Market Query'}
                  {detailActivity.type === 'llm_thought' && '💭 Agent Thought'}
                  {detailActivity.type === 'price_check' && '💱 Price Check'}
                  {detailActivity.type === 'agent_wait' && '⏸ Waiting'}
                  {detailActivity.type === 'observation_recorded' && '📝 Observation'}
                  {detailActivity.type === 'strategy_updated' && '⚙️ Strategy Update'}
                  {detailActivity.type === 'signal_received' && '📡 Signal Received'}
                  {detailActivity.type === 'bot_created' && '🤖 Bot Created'}
                </div>

                {/* Type-specific content */}
                <div className="space-y-4">

            {/* TRADE ENTRY/EXIT SPECIFIC FIELDS */}
            {(detailActivity.type === 'trade_entry' || detailActivity.type === 'trade_exit') ? (
              <>
                {/* Confidence */}
                {detailActivity.data.details?.confidence != null ? (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Confidence
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-black bg-opacity-30 rounded-full h-2 overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${(Number(detailActivity.data.details.confidence) || 0) * 100}%`,
                            backgroundColor: VIBE.signal
                          }}
                        />
                      </div>
                      <span className="text-sm font-semibold">{formatActivityPercent(Number(detailActivity.data.details.confidence))}</span>
                    </div>
                  </div>
                 ) : null}

                {/* Leverage */}
                {detailActivity.data.details?.leverage != null ? (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Leverage
                    </div>
                    <div className="text-lg font-semibold">{String(detailActivity.data.details.leverage)}x</div>
                  </div>
                 ) : null}

                {/* Entry Price */}
                {detailActivity.data.details?.entry_price != null ? (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Entry Price
                    </div>
                    <div className="text-lg font-mono">{formatActivityPrice(Number(detailActivity.data.details.entry_price))}</div>
                  </div>
                 ) : null}

                {/* Exit Price (for trade_exit) */}
                {detailActivity.data.details?.exit_price != null ? (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Exit Price
                    </div>
                    <div className="text-lg font-mono">{formatActivityPrice(Number(detailActivity.data.details.exit_price))}</div>
                  </div>
                 ) : null}

                {/* P&L (for trade_exit) */}
                {detailActivity.data.details?.pnl != null ? (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      P&L
                    </div>
                    <div className="text-lg font-semibold" style={{ color: Number(detailActivity.data.details.pnl) >= 0 ? VIBE.signal : VIBE.ember }}>
                      {formatActivityUSD(Number(detailActivity.data.details.pnl))}
                    </div>
                  </div>
                 ) : null}

                {/* Size USD */}
                {detailActivity.data.details?.size_usd != null ? (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Position Size
                    </div>
                    <div className="text-lg font-mono">{formatActivityPrice(Number(detailActivity.data.details.size_usd))}</div>
                  </div>
                 ) : null}

                {/* Stop Loss / Take Profit Grid */}
                <div className="grid grid-cols-2 gap-4">
                  {detailActivity.data.details?.stop_loss != null ? (
                    <div>
                      <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                        Stop Loss
                      </div>
                      <div className="text-sm font-mono" style={{ color: VIBE.ember }}>
                        {formatActivityPrice(Number(detailActivity.data.details.stop_loss))}
                      </div>
                    </div>
                  ) : null}

                  {detailActivity.data.details?.take_profit != null ? (
                    <div>
                      <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                        Take Profit
                      </div>
                      <div className="text-sm font-mono" style={{ color: VIBE.signal }}>
                        {formatActivityPrice(Number(detailActivity.data.details.take_profit))}
                      </div>
                    </div>
                  ) : null}
                </div>
              </>
            ) : null}

            {/* MARKET QUERY SPECIFIC FIELDS */}
            {detailActivity.type === 'market_query' && detailActivity.data.details ? (
              <>
                {/* Query Mode Badge */}
                {Boolean((detailActivity.data.details as Record<string, unknown>).query_mode) && (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Query Mode
                    </div>
                    <div className="inline-block px-3 py-1 rounded-lg text-xs uppercase tracking-wider font-semibold" style={{
                      backgroundColor: 'rgba(60, 166, 224, 0.2)',
                      color: VIBE.signal
                    }}>
                      {String((detailActivity.data.details as Record<string, unknown>).query_mode).replace(/_/g, ' ')}
                    </div>
                  </div>
                )}

                {/* Current Price & Data Age */}
                <div className="grid grid-cols-2 gap-4">
                  {Boolean((detailActivity.data.details as Record<string, unknown>).current_price) && (
                    <div>
                      <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                        Price at Query
                      </div>
                      <div className="text-lg font-mono">${Number((detailActivity.data.details as Record<string, unknown>).current_price).toFixed(2)}</div>
                    </div>
                  )}
                  {(detailActivity.data.details as Record<string, unknown>).data_age_seconds != null && (
                    <div>
                      <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                        Data Age
                      </div>
                      <div className="text-sm">{Math.floor(Number((detailActivity.data.details as Record<string, unknown>).data_age_seconds) / 60)}m {Number((detailActivity.data.details as Record<string, unknown>).data_age_seconds) % 60}s</div>
                    </div>
                  )}
                </div>

                {/* Metadata Summary */}
                {Boolean((detailActivity.data.details as Record<string, unknown>).metadata) && (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-2" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Query Summary
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {Boolean(((detailActivity.data.details as Record<string, unknown>).metadata as Record<string, unknown>).timeframes_analyzed) && (
                        <div>
                          <span className="text-xs" style={{ color: 'rgba(237,235,231,0.6)' }}>Timeframes:</span> {(((detailActivity.data.details as Record<string, unknown>).metadata as Record<string, unknown>).timeframes_analyzed as string[]).length}
                        </div>
                      )}
                      {Boolean(((detailActivity.data.details as Record<string, unknown>).metadata as Record<string, unknown>).indicators_count) && (
                        <div>
                          <span className="text-xs" style={{ color: 'rgba(237,235,231,0.6)' }}>Indicators:</span> {String(((detailActivity.data.details as Record<string, unknown>).metadata as Record<string, unknown>).indicators_count)}
                        </div>
                      )}
                      {Boolean(((detailActivity.data.details as Record<string, unknown>).metadata as Record<string, unknown>).total_prompt_tokens) && (
                        <div>
                          <span className="text-xs" style={{ color: 'rgba(237,235,231,0.6)' }}>Tokens:</span> {Number(((detailActivity.data.details as Record<string, unknown>).metadata as Record<string, unknown>).total_prompt_tokens).toLocaleString()}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Formatted Data Sections (Collapsible) */}
                {Boolean((detailActivity.data.details as Record<string, unknown>).formatted_data) && (
                  <div className="space-y-3">
                    <div className="text-xs uppercase tracking-wider" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Data Sent to LLM
                    </div>
                    {Object.entries((detailActivity.data.details as Record<string, unknown>).formatted_data as Record<string, unknown>).map(([sectionName, sectionText]) => {
                      if (!sectionText) return null;
                      const metadata = (detailActivity.data.details as Record<string, unknown>).metadata as Record<string, unknown>;
                      const breakdown = metadata?.breakdown as Record<string, unknown>;
                      const tokens = breakdown?.[`${sectionName}_tokens`] || 0;
                      return (
                        <details key={sectionName} className="rounded-lg border" style={{ borderColor: VIBE.hair, backgroundColor: 'rgba(193, 168, 125, 0.05)' }}>
                          <summary className="cursor-pointer px-4 py-3 font-semibold text-sm flex items-center justify-between" style={{ color: VIBE.brass }}>
                            <span>{sectionName.replace(/_/g, ' ').toUpperCase()}</span>
                            {Number(tokens) > 0 && (
                              <span className="text-xs font-mono px-2 py-1 rounded" style={{ backgroundColor: 'rgba(193, 168, 125, 0.2)' }}>
                                {Number(tokens).toLocaleString()} tokens
                              </span>
                            )}
                          </summary>
                          <div className="px-4 pb-4 max-h-96 overflow-y-auto">
                            <pre className="text-xs font-mono whitespace-pre-wrap" style={{ color: VIBE.ivory }}>
                              {String(sectionText)}
                            </pre>
                          </div>
                        </details>
                      );
                    })}
                  </div>
                )}
              </>
            ) : null}

            {/* LLM THOUGHT SPECIFIC FIELDS */}
            {detailActivity.type === 'llm_thought' && detailActivity.data.details && ((detailActivity.data.details as Record<string, unknown>).thought || (detailActivity.data.details as Record<string, unknown>).reasoning) ? (
              <div>
                <div className="text-xs uppercase tracking-wider mb-2" style={{ color: 'rgba(237,235,231,0.6)' }}>
                  Agent Thought
                </div>
                <div
                  className="prose prose-invert prose-sm max-w-none"
                  style={{ color: VIBE.ivory }}
                >
                  <ReactMarkdown>{String((detailActivity.data.details as Record<string, unknown>).thought || (detailActivity.data.details as Record<string, unknown>).reasoning)}</ReactMarkdown>
                </div>

                {detailActivity.data.details.balance != null && typeof detailActivity.data.details.balance === 'number' ? (
                  <div className="mt-4 p-3 rounded-lg" style={{ backgroundColor: 'rgba(0, 217, 255, 0.1)' }}>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Balance at Time
                    </div>
                    <div className="text-lg font-semibold" style={{ color: VIBE.signal }}>
                      {formatActivityPrice(detailActivity.data.details.balance)}
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

            {/* BOT CREATED SPECIFIC FIELDS */}
            {detailActivity.type === 'bot_created' && detailActivity.data.details ? (
              <div className="grid grid-cols-2 gap-4">
                {/* Trading Mode */}
                {Boolean((detailActivity.data.details as Record<string, unknown>).trading_mode) && (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Trading Mode
                    </div>
                    <div className="text-lg font-semibold" style={{ color: '#16a34a' }}>
                      {String((detailActivity.data.details as Record<string, unknown>).trading_mode).toUpperCase()}
                    </div>
                  </div>
                )}

                {/* Config Type */}
                {Boolean((detailActivity.data.details as Record<string, unknown>).config_type) && (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Bot Type
                    </div>
                    <div className="text-sm">
                      {String((detailActivity.data.details as Record<string, unknown>).config_type).replace(/_/g, ' ')}
                    </div>
                  </div>
                )}

                {/* Selected Pair */}
                {Boolean((detailActivity.data.details as Record<string, unknown>).selected_pair) && (
                  <div>
                    <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'rgba(237,235,231,0.6)' }}>
                      Trading Pair
                    </div>
                    <div className="text-sm font-mono" style={{ color: VIBE.signal }}>
                      {String((detailActivity.data.details as Record<string, unknown>).selected_pair)}
                    </div>
                  </div>
                )}
              </div>
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
