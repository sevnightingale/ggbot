"use client";

import { useEffect, useRef } from 'react';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  LineData,
  SeriesMarker,
  Time,
  ColorType,
  LineSeries,
  createSeriesMarkers
} from 'lightweight-charts';

// Trade37 Palette
const VIBE = {
  obsidian: "#0B0B0C",
  carbon: "#141416",
  ivory: "#EDEBE7",
  hair: "rgba(237,235,231,0.16)",
  brass: "#C1A87D",
  signal: "#3CA6E0",
  ember: "#D74A1F",
  lilac: "#8B7CF2",
};

// Activity types
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

interface Activity {
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

interface BalanceChartTVProps {
  balanceData: BalancePoint[];
  activities: Activity[];
  onActivityClick?: (activity: Activity) => void;
}

export default function BalanceChartTV({
  balanceData,
  activities,
  onActivityClick
}: BalanceChartTVProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Ensure container has valid dimensions
    const containerWidth = chartContainerRef.current.clientWidth;
    const containerHeight = chartContainerRef.current.clientHeight;

    console.log('[BalanceChartTV] Container dimensions:', { containerWidth, containerHeight });

    if (containerWidth === 0 || containerHeight === 0) {
      console.error('[BalanceChartTV] Container has zero dimensions, cannot create chart');
      return;
    }

    // Log data for debugging
    console.log('[BalanceChartTV] Received data:', {
      balanceDataLength: balanceData?.length,
      activitiesLength: activities?.length,
      firstBalance: balanceData?.[0],
      firstActivity: activities?.[0]
    });

    // Create chart with Trade37 styling
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: {
        background: { type: ColorType.Solid, color: VIBE.carbon },
        textColor: VIBE.ivory,
      },
      grid: {
        vertLines: { color: VIBE.hair },
        horzLines: { color: VIBE.hair },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: VIBE.hair,
      },
      rightPriceScale: {
        borderColor: VIBE.hair,
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      crosshair: {
        vertLine: {
          color: VIBE.brass,
          width: 1,
          style: 2,
          labelBackgroundColor: VIBE.brass,
        },
        horzLine: {
          color: VIBE.brass,
          width: 1,
          style: 2,
          labelBackgroundColor: VIBE.brass,
        },
      },
    });

    // Add line series for account balance
    const lineSeries = chart.addSeries(LineSeries, {
      color: VIBE.signal,
      lineWidth: 2,
      lastValueVisible: true,
      priceLineVisible: true,
      priceFormat: {
        type: 'price',
        precision: 2,
        minMove: 0.01,
      },
    });

    // Convert balance data (timestamp in SECONDS for TradingView)
    // Filter out null/invalid values and sort by time
    const chartData: LineData[] = balanceData
      .filter(point => {
        if (!point || point.balance == null || !point.timestamp) return false;
        const time = new Date(point.timestamp).getTime();
        return !isNaN(time) && isFinite(point.balance);
      })
      .map(point => {
        const time = Math.floor(new Date(point.timestamp).getTime() / 1000);
        const value = Number(point.balance);
        return { time: time as Time, value };
      })
      .filter(point => {
        // Double-check: ensure no null/NaN values after mapping
        return point.value != null && !isNaN(point.value) && isFinite(point.value);
      })
      .sort((a, b) => (a.time as number) - (b.time as number));

    console.log('[BalanceChartTV] Processed chart data:', {
      originalLength: balanceData.length,
      filteredLength: chartData.length,
      firstThree: chartData.slice(0, 3),
      allData: chartData  // Log ALL points to see where null is
    });

    // Don't render if no valid data
    if (chartData.length === 0) {
      console.error('[BalanceChartTV] No valid chart data after filtering');
      chart.remove();
      return;
    }

    lineSeries.setData(chartData);

    // Create markers from activities
    // Filter out invalid activities and sort by time
    const markers: SeriesMarker<Time>[] = activities
      .filter(activity => {
        // Filter out null/invalid activities
        if (!activity || !activity.timestamp || !activity.type || activity.priority > 2) return false;
        const time = new Date(activity.timestamp).getTime();
        return !isNaN(time);
      })
      .map(activity => {
        const markerConfig = getMarkerConfig(activity.type);

        const markerTime = Math.floor(new Date(activity.timestamp).getTime() / 1000);

        return {
          time: markerTime as Time,
          position: markerConfig.position,
          color: markerConfig.color,
          shape: markerConfig.shape,
          text: markerConfig.text,
        };
      })
      .filter(marker => {
        // Ensure all marker fields are valid
        return marker.time != null &&
               marker.position != null &&
               marker.color != null &&
               marker.shape != null &&
               marker.text != null;
      })
      .sort((a, b) => (a.time as number) - (b.time as number));

    console.log('[BalanceChartTV] Processed markers:', {
      originalLength: activities.length,
      filteredLength: markers.length,
      firstThree: markers.slice(0, 3),
      allMarkers: markers  // Log all markers
    });

    // Add markers using v5 plugin API
    try {
      if (markers.length > 0) {
        console.log('[BalanceChartTV] Adding markers to chart...');
        createSeriesMarkers(lineSeries, markers);
        console.log('[BalanceChartTV] Markers added successfully');
      }
    } catch (error) {
      console.error('[BalanceChartTV] Error adding markers:', error);
      // Continue without markers rather than crash
    }

    chart.timeScale().fitContent();

    chartRef.current = chart;
    seriesRef.current = lineSeries;

    // Handle clicks on markers
    chart.subscribeClick((param) => {
      if (!param.time || !onActivityClick) return;

      // Find activity at clicked time
      const clickedTime = param.time as number;
      const clickedActivity = activities.find(activity => {
        const activityTime = Math.floor(new Date(activity.timestamp).getTime() / 1000);
        return Math.abs(activityTime - clickedTime) < 60; // Within 1 minute tolerance
      });

      if (clickedActivity) {
        onActivityClick(clickedActivity);
      }
    });

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [balanceData, activities, onActivityClick]);

  return (
    <div
      ref={chartContainerRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative'
      }}
    />
  );
}

// Map activity types to marker configurations
function getMarkerConfig(activityType: ActivityType) {
  const configs: Record<ActivityType, {
    position: 'aboveBar' | 'belowBar' | 'inBar';
    color: string;
    shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown';
    text: string;
  }> = {
    trade_entry_long: {
      position: 'belowBar',
      color: VIBE.signal,
      shape: 'arrowUp',
      text: 'L',
    },
    trade_entry_short: {
      position: 'aboveBar',
      color: VIBE.ember,
      shape: 'arrowDown',
      text: 'S',
    },
    trade_win: {
      position: 'aboveBar',
      color: VIBE.signal,
      shape: 'arrowUp',
      text: 'W',
    },
    trade_loss: {
      position: 'belowBar',
      color: VIBE.ember,
      shape: 'arrowDown',
      text: 'L',
    },
    strategy_updated: {
      position: 'aboveBar',
      color: VIBE.brass,
      shape: 'square',
      text: 'S',
    },
    market_query: {
      position: 'inBar',
      color: VIBE.lilac,
      shape: 'circle',
      text: 'Q',
    },
    agent_wait: {
      position: 'inBar',
      color: VIBE.hair,
      shape: 'circle',
      text: 'W',
    },
    observation_recorded: {
      position: 'inBar',
      color: VIBE.hair,
      shape: 'circle',
      text: 'O',
    },
    analysis: {
      position: 'inBar',
      color: VIBE.lilac,
      shape: 'circle',
      text: 'A',
    },
    reasoning: {
      position: 'inBar',
      color: VIBE.lilac,
      shape: 'circle',
      text: 'R',
    },
    plan: {
      position: 'inBar',
      color: VIBE.lilac,
      shape: 'circle',
      text: 'P',
    },
  };

  return configs[activityType] || {
    position: 'inBar' as const,
    color: VIBE.ivory,
    shape: 'circle' as const,
    text: '?',
  };
}
