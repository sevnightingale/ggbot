'use client';

import React, { useEffect, useState, useRef } from 'react';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, LineData, Time, SeriesMarker } from 'lightweight-charts';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import type { Session } from '@supabase/supabase-js';
import ActivityModal from './activity-modal';
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

interface BalancePoint {
  timestamp: string;
  total_equity?: number;  // New API key
  balance?: number;       // Legacy API key (deprecated)
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
    platform_cost_usd?: number;
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

type ChartMode = 'activity' | 'performance';
type Timeframe = '5m' | '1h' | '4h' | '1d';

// Aggregate 5-minute data points into higher timeframes
function aggregateToTimeframe(dataPoints: BalancePoint[], timeframe: Timeframe): BalancePoint[] {
  if (timeframe === '5m' || dataPoints.length === 0) {
    return dataPoints; // No aggregation needed
  }

  // Calculate period size in minutes
  const periodMinutes = {
    '1h': 60,
    '4h': 240,
    '1d': 1440
  }[timeframe];

  const aggregated: BalancePoint[] = [];
  let currentPeriodStart: Date | null = null;
  let currentPeriodPoints: BalancePoint[] = [];

  dataPoints.forEach((point) => {
    const timestamp = new Date(point.timestamp);

    if (!currentPeriodStart) {
      // Start first period
      currentPeriodStart = new Date(timestamp);
      currentPeriodStart.setMinutes(0, 0, 0); // Round down to hour
      currentPeriodPoints = [point];
    } else {
      // Check if we're still in the same period
      const minutesSinceStart = (timestamp.getTime() - currentPeriodStart.getTime()) / (1000 * 60);

      if (minutesSinceStart < periodMinutes) {
        // Still in same period
        currentPeriodPoints.push(point);
      } else {
        // Period ended, aggregate and start new period
        if (currentPeriodPoints.length > 0) {
          // Use the LAST value in the period (most accurate for equity)
          const lastPoint = currentPeriodPoints[currentPeriodPoints.length - 1];
          aggregated.push(lastPoint);
        }

        // Start new period
        currentPeriodStart = new Date(timestamp);
        currentPeriodStart.setMinutes(
          Math.floor(timestamp.getMinutes() / periodMinutes) * periodMinutes,
          0,
          0
        );
        currentPeriodPoints = [point];
      }
    }
  });

  // Add final period
  if (currentPeriodPoints.length > 0) {
    const lastPoint = currentPeriodPoints[currentPeriodPoints.length - 1];
    aggregated.push(lastPoint);
  }

  return aggregated;
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
  const [currentActivityIndex, setCurrentActivityIndex] = useState<number>(0);
  const [crosshairPosition, setCrosshairPosition] = useState<{ x: number; y: number } | null>(null);
  const [latestActivity, setLatestActivity] = useState<Activity | null>(null);
  const [statusText, setStatusText] = useState<string>('');

  // Chart mode and timeframe state
  const [chartMode, setChartMode] = useState<ChartMode>('activity');
  const [timeframe, setTimeframe] = useState<Timeframe>('5m');

  // Map to lookup activities by timestamp (can have multiple activities at same time)
  const activitiesMapRef = useRef<Map<number, Activity[]>>(new Map());
  // All activities sorted chronologically for modal navigation
  const allActivitiesSortedRef = useRef<Activity[]>([]);

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
        // Open modal with all activities, starting at the clicked one
        const allSorted = allActivitiesSortedRef.current;
        const clickedActivity = activities[0]; // Primary activity at this timestamp
        const startIndex = allSorted.findIndex(a => a.id === clickedActivity.id);
        setDetailActivities(allSorted);
        setCurrentActivityIndex(startIndex >= 0 ? startIndex : 0);
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

        console.log('Fetching from API...', { mode: chartMode, timeframe });

        // Choose endpoint based on chart mode
        const seriesEndpoint = chartMode === 'activity'
          ? `/api/v2/snapshots/${configId}/balance-series`
          : `/api/v2/snapshots/${configId}/performance-series`;

        // Fetch data (activities only needed for activity mode)
        const fetchPromises = [
          fetch(seriesEndpoint, { headers, signal: abortController.signal }),
          fetch(`/api/v2/activities/${configId}/metadata`, { headers, signal: abortController.signal }),
        ];

        // Only fetch activities for activity mode (needed for markers/details)
        if (chartMode === 'activity') {
          fetchPromises.push(
            fetch(`/api/v2/activities/${configId}`, { headers, signal: abortController.signal })
          );
        }

        const responses = await Promise.all(fetchPromises);
        const [balanceSeriesRes, metadataRes, activitiesRes] = responses;

        console.log('API responses:', {
          balanceOk: balanceSeriesRes.ok,
          balanceStatus: balanceSeriesRes.status,
          activitiesOk: activitiesRes?.ok,
          activitiesStatus: activitiesRes?.status,
          metadataOk: metadataRes.ok,
          metadataStatus: metadataRes.status
        });

        // Check required responses
        if (!balanceSeriesRes.ok || !metadataRes.ok || (chartMode === 'activity' && activitiesRes && !activitiesRes.ok)) {
          const balanceError = await balanceSeriesRes.text();
          const metadataError = await metadataRes.text();
          const activitiesError = activitiesRes ? await activitiesRes.text() : 'N/A';
          console.error('API errors:', { balanceError, activitiesError, metadataError });
          throw new Error(`Failed to fetch timeline data`);
        }

        // Parse responses
        const balanceSeries = await balanceSeriesRes.json();
        const metadataData = await metadataRes.json();
        const activitiesData = activitiesRes ? await activitiesRes.json() : null;

        // Get balance points and apply aggregation for performance mode
        let balancePoints: BalancePoint[] = balanceSeries.equity_series || balanceSeries.balance_series || [];

        // Apply timeframe aggregation for performance mode
        if (chartMode === 'performance' && timeframe !== '5m') {
          console.log(`Aggregating ${balancePoints.length} points to ${timeframe} timeframe...`);
          balancePoints = aggregateToTimeframe(balancePoints, timeframe);
          console.log(`After aggregation: ${balancePoints.length} points`);
        }

        const activities: Activity[] = activitiesData?.activities || [];

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
        // Just convert timestamps and use equity values directly
        const chartData: LineData[] = balancePoints
          .filter(point => {
            const equity = point.total_equity ?? point.balance;  // Use new key with fallback to legacy
            return point.timestamp && equity != null;
          })
          .map(point => ({
            time: Math.floor(new Date(point.timestamp).getTime() / 1000) as Time,
            value: point.total_equity ?? point.balance ?? 0  // Use new key with fallback to legacy
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

          // Build activities lookup map and markers - ONLY for activity mode
          if (chartMode === 'activity') {
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

            // Store all activities sorted chronologically (oldest first) for modal navigation
            allActivitiesSortedRef.current = [...activities].sort((a, b) =>
              new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
            );

            // Update latest activity for status display (most recent first)
            const sortedActivitiesDesc = [...activities].sort((a, b) =>
              new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
            );
            if (sortedActivitiesDesc.length > 0) {
              setLatestActivity(sortedActivitiesDesc[0]);
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
            const hasStrategyUpdated = activitiesAtTime.some(a => a.type === 'strategy_updated');

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
            } else if (hasStrategyUpdated) {
              markers.push({
                time: timestamp as Time,
                position: 'aboveBar',
                color: '#3CA6E0', // signal blue — config change
                shape: 'square',
                size: 1,
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
          } else {
            // Performance mode - clear markers and activities
            activitiesMapRef.current.clear();
            if (lineSeriesRef.current) {
              lineSeriesRef.current.setMarkers([]);
            }
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
  }, [configId, chartContainer, chartMode, timeframe]); // NOTE: session and theme NOT in dependencies
  // - session: prevents double render, fetchData reads current value via ref
  // - theme: separate effect handles color updates dynamically
  // - chartMode and timeframe: trigger data refetch when changed

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
        <div className="rounded-xl border p-4 relative flex flex-col" style={{ backgroundColor: VIBE.carbon, borderColor: VIBE.hair, height: variant === 'embedded' ? '600px' : 'calc(100vh - 280px)', minHeight: '400px' }}>

          {/* Chart Mode and Timeframe Controls - Centered above chart */}
          <div className="flex justify-center gap-2 mb-3 flex-shrink-0">
            {/* Mode Toggle */}
            <div className="flex gap-1 p-1 rounded-lg" style={{ backgroundColor: VIBE.obsidian }}>
              <button
                onClick={() => setChartMode('activity')}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                  chartMode === 'activity'
                    ? 'shadow-sm'
                    : 'hover:bg-opacity-50'
                }`}
                style={{
                  backgroundColor: chartMode === 'activity' ? VIBE.brass : 'transparent',
                  color: chartMode === 'activity' ? VIBE.obsidian : VIBE.ivory
                }}
              >
                Activity Timeline
              </button>
              <button
                onClick={() => setChartMode('performance')}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                  chartMode === 'performance'
                    ? 'shadow-sm'
                    : 'hover:bg-opacity-50'
                }`}
                style={{
                  backgroundColor: chartMode === 'performance' ? VIBE.brass : 'transparent',
                  color: chartMode === 'performance' ? VIBE.obsidian : VIBE.ivory
                }}
              >
                Performance Chart
              </button>
            </div>

            {/* Timeframe Selector (Performance mode only) */}
            {chartMode === 'performance' && (
              <div className="flex gap-1 p-1 rounded-lg" style={{ backgroundColor: VIBE.obsidian }}>
                {(['5m', '1h', '4h', '1d'] as Timeframe[]).map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setTimeframe(tf)}
                    className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                      timeframe === tf
                        ? 'shadow-sm'
                        : 'hover:bg-opacity-50'
                    }`}
                    style={{
                      backgroundColor: timeframe === tf ? VIBE.signal : 'transparent',
                      color: timeframe === tf ? VIBE.obsidian : VIBE.ivory
                    }}
                  >
                    {tf.toUpperCase()}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Chart - takes remaining space */}
          <div ref={setChartContainer} className="flex-1" />

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
                  // Open modal with all activities, starting at the hovered one
                  const allSorted = allActivitiesSortedRef.current;
                  const startIndex = allSorted.findIndex(a => a.id === selectedActivity.id);
                  setDetailActivities(allSorted);
                  setCurrentActivityIndex(startIndex >= 0 ? startIndex : 0);
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

      {/* Activity Detail Modal */}
      <ActivityModal
        isOpen={detailActivities.length > 0}
        activities={detailActivities}
        currentIndex={currentActivityIndex}
        onClose={() => setDetailActivities([])}
        onNavigate={(index) => setCurrentActivityIndex(index)}
      />
    </div>
  );
}
