'use client';

import React, { useEffect, useState, useRef } from 'react';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, LineData, Time, SeriesMarker } from 'lightweight-charts';

// Dark theme colors (arena is always dark)
const VIBE = {
  obsidian: '#0B0B0C',
  carbon: '#141416',
  ivory: '#EDEBE7',
  hair: 'rgba(237,235,231,0.16)',
  brass: '#C1A87D',
  signal: '#3CA6E0',
  ember: '#D74A1F',
};

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

interface ArenaTimelineProps {
  configId: string;
  height?: number;
}

export default function ArenaTimeline({ configId, height = 350 }: ArenaTimelineProps) {
  const [chartContainer, setChartContainer] = useState<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const lineSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);

  // Map to lookup activities by timestamp
  const activitiesMapRef = useRef<Map<number, Activity[]>>(new Map());

  // Chart creation and data fetching
  useEffect(() => {
    if (!configId || !chartContainer) return;

    // Clean up existing chart
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
      lineSeriesRef.current = null;
    }

    const containerWidth = chartContainer.clientWidth;
    const containerHeight = height;

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
        priceFormatter: (price: number) => {
          if (price == null || isNaN(price)) return '$—';
          return `$${price.toFixed(0)}`;
        },
      },
    });

    chartRef.current = chart;

    const lineSeries = chart.addLineSeries({
      color: VIBE.brass,
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      lastValueVisible: true,
      priceLineVisible: false,
    });

    lineSeriesRef.current = lineSeries;

    // Crosshair move handler
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.point) {
        setSelectedActivity(null);
        return;
      }

      const timestamp = typeof param.time === 'number' ? param.time : parseFloat(param.time as string);
      const activities = activitiesMapRef.current.get(timestamp);

      if (activities && activities.length > 0) {
        setSelectedActivity(activities[0]);
      } else {
        setSelectedActivity(null);
      }
    });

    const handleResize = () => {
      if (chartContainer && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainer.clientWidth,
          height: height,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Fetch data from public endpoints
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [balanceRes, activitiesRes] = await Promise.all([
          fetch(`/api/v2/public/arena/${configId}/balance-series`),
          fetch(`/api/v2/public/arena/${configId}/activities`),
        ]);

        if (!balanceRes.ok || !activitiesRes.ok) {
          throw new Error('Failed to fetch timeline data');
        }

        const balanceData = await balanceRes.json();
        const activitiesData = await activitiesRes.json();

        if (balanceData.status === 'error' || activitiesData.status === 'error') {
          throw new Error('Bot not available');
        }

        const equitySeries = balanceData.equity_series || [];
        const activities: Activity[] = activitiesData.activities || [];

        // Convert to chart data
        const chartData: LineData[] = equitySeries
          .filter((point: { timestamp: string; total_equity: number }) =>
            point.timestamp && point.total_equity != null
          )
          .map((point: { timestamp: string; total_equity: number }) => ({
            time: Math.floor(new Date(point.timestamp).getTime() / 1000) as Time,
            value: point.total_equity
          }))
          .sort((a: LineData, b: LineData) => {
            const timeA = typeof a.time === 'number' ? a.time : parseFloat(a.time as string);
            const timeB = typeof b.time === 'number' ? b.time : parseFloat(b.time as string);
            return timeA - timeB;
          });

        if (lineSeriesRef.current && chartData.length > 0) {
          lineSeriesRef.current.setData(chartData);

          // Build activities lookup map
          activitiesMapRef.current.clear();
          const groupedByTimestamp = new Map<number, Activity[]>();

          activities.forEach((activity) => {
            const timestamp = Math.floor(new Date(activity.timestamp).getTime() / 1000);
            if (!groupedByTimestamp.has(timestamp)) {
              groupedByTimestamp.set(timestamp, []);
            }
            groupedByTimestamp.get(timestamp)!.push(activity);
          });

          activitiesMapRef.current = groupedByTimestamp;

          // Create chart data timestamp set for marker validation
          const validTimestamps = new Set(chartData.map(point => point.time as number));

          // Create markers for activities
          const markers: SeriesMarker<Time>[] = [];

          groupedByTimestamp.forEach((activitiesAtTime, timestamp) => {
            // Skip markers for timestamps not in chart data
            if (!validTimestamps.has(timestamp)) return;

            const hasTradeLong = activitiesAtTime.some(a =>
              a.type === 'trade_entry' && a.data?.details?.side === 'long'
            );
            const hasTradeShort = activitiesAtTime.some(a =>
              a.type === 'trade_entry' && a.data?.details?.side === 'short'
            );
            const tradeExitActivity = activitiesAtTime.find(a => a.type === 'trade_exit');
            const hasLLMThought = activitiesAtTime.some(a => a.type === 'llm_thought');
            const hasMarketQuery = activitiesAtTime.some(a => a.type === 'market_query');

            if (hasTradeLong) {
              markers.push({
                time: timestamp as Time,
                position: 'belowBar',
                color: '#16a34a',
                shape: 'arrowUp',
                size: 2,
              });
            } else if (hasTradeShort) {
              markers.push({
                time: timestamp as Time,
                position: 'aboveBar',
                color: '#dc2626',
                shape: 'arrowDown',
                size: 2,
              });
            } else if (tradeExitActivity) {
              const pnl = Number(tradeExitActivity.data?.details?.pnl || 0);
              const isProfit = pnl > 0;
              markers.push({
                time: timestamp as Time,
                position: isProfit ? 'aboveBar' : 'belowBar',
                color: isProfit ? '#16a34a' : '#dc2626',
                shape: 'circle',
                size: 0.75,
                text: `${isProfit ? '+' : ''}$${pnl.toFixed(0)}`,
              });
            } else if (hasLLMThought) {
              markers.push({
                time: timestamp as Time,
                position: 'inBar',
                color: VIBE.brass,
                shape: 'circle',
                size: 1,
              });
            } else if (hasMarketQuery) {
              markers.push({
                time: timestamp as Time,
                position: 'inBar',
                color: VIBE.signal,
                shape: 'circle',
                size: 1,
              });
            }
          });

          if (markers.length > 0) {
            const sortedMarkers = markers.sort((a, b) => {
              const timeA = typeof a.time === 'number' ? a.time : parseFloat(a.time as string);
              const timeB = typeof b.time === 'number' ? b.time : parseFloat(b.time as string);
              return timeA - timeB;
            });
            lineSeriesRef.current.setMarkers(sortedMarkers);
          }

          chartRef.current?.timeScale().fitContent();
        }

        setLoading(false);
      } catch (err) {
        console.error('ArenaTimeline fetch error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load timeline');
        setLoading(false);
      }
    };

    fetchData();

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
        lineSeriesRef.current = null;
      }
    };
  }, [configId, chartContainer, height]);

  return (
    <div className="relative w-full rounded-lg overflow-hidden" style={{ backgroundColor: VIBE.carbon, height }}>
      {/* Chart */}
      <div ref={setChartContainer} style={{ width: '100%', height: '100%' }} />

      {/* Activity hover tooltip */}
      {selectedActivity && (
        <div
          className="absolute bottom-3 left-3 rounded-lg border px-3 py-2 pointer-events-none"
          style={{
            backgroundColor: VIBE.carbon,
            borderColor: VIBE.brass,
            borderWidth: '1px',
            maxWidth: '280px',
            zIndex: 10
          }}
        >
          <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: VIBE.brass }}>
            {selectedActivity.type === 'trade_entry' && selectedActivity.data?.details?.side === 'long' && 'Long Entry'}
            {selectedActivity.type === 'trade_entry' && selectedActivity.data?.details?.side === 'short' && 'Short Entry'}
            {selectedActivity.type === 'trade_exit' && 'Position Closed'}
            {selectedActivity.type === 'market_query' && 'Market Query'}
            {selectedActivity.type === 'llm_thought' && 'Analysis'}
            {selectedActivity.type === 'agent_wait' && 'Waiting'}
          </div>
          {selectedActivity.data.summary && (
            <div className="text-xs mb-1 line-clamp-2" style={{ color: VIBE.ivory }}>
              {selectedActivity.data.summary.length > 80
                ? selectedActivity.data.summary.slice(0, 80) + '...'
                : selectedActivity.data.summary}
            </div>
          )}
          <div className="text-[10px]" style={{ color: 'rgba(237,235,231,0.5)' }}>
            {new Date(selectedActivity.timestamp).toLocaleString()}
          </div>
        </div>
      )}

      {/* Loading overlay */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center" style={{ backgroundColor: 'rgba(11,11,12,0.8)' }}>
          <div className="text-sm" style={{ color: VIBE.ivory }}>Loading timeline...</div>
        </div>
      )}

      {/* Error overlay */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center" style={{ backgroundColor: 'rgba(11,11,12,0.8)' }}>
          <div className="text-sm" style={{ color: VIBE.ember }}>{error}</div>
        </div>
      )}
    </div>
  );
}
