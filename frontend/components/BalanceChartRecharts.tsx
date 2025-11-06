'use client';

import React, { useMemo, useCallback } from 'react';
import {
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Brush,
} from 'recharts';

// Trade37 Palette
const VIBE = {
  obsidian: '#0B0B0C',
  carbon: '#141416',
  ivory: '#EDEBE7',
  hair: 'rgba(237,235,231,0.16)',
  brass: '#C1A87D',
  signal: '#3CA6E0',
  ember: '#D74A1F',
  lilac: '#8B7CF2',
};

// SVG Icons (from Timeline.jsx)
const Svg = {
  Long: (color: string) => (
    <svg viewBox="0 0 24 24" width="16" height="16">
      <path d="M12 4l-9 16h18z" fill={color} />
    </svg>
  ),
  Short: (color: string) => (
    <svg viewBox="0 0 24 24" width="16" height="16">
      <path d="M12 20l9-16H3z" fill={color} />
    </svg>
  ),
  Up: (color: string) => (
    <svg viewBox="0 0 24 24" width="16" height="16">
      <path d="M11 21h2V8l4.5 4.5L19 11l-7-7-7 7 1.5 1.5L11 8z" fill={color} />
    </svg>
  ),
  Down: (color: string) => (
    <svg viewBox="0 0 24 24" width="16" height="16">
      <path d="M13 3h-2v13l-4.5-4.5L5 13l7 7 7-7-1.5-1.5L13 16z" fill={color} />
    </svg>
  ),
  Wrench: (color: string) => (
    <svg viewBox="0 0 24 24" width="16" height="16">
      <path d="M14.7 6.3a5 5 0 01-6.4 6.4L3 18l3 3 5.3-5.3a5 5 0 006.4-6.4l-3-3z" fill={color} />
    </svg>
  ),
  Bars: (color: string) => (
    <svg viewBox="0 0 24 24" width="16" height="16">
      <path d="M4 20h4V8H4v12zm6 0h4V12h-4v8zm6 0h4V4h-4v16z" fill={color} />
    </svg>
  ),
  Clock: (color: string) => (
    <svg viewBox="0 0 24 24" width="16" height="16">
      <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm1 10V6h-2v8h6v-2h-4z" fill={color} />
    </svg>
  ),
  Note: (color: string) => (
    <svg viewBox="0 0 24 24" width="16" height="16">
      <path d="M6 2h9l5 5v13a2 2 0 01-2 2H6a2 2 0 01-2-2V4a2 2 0 012-2zm8 1.5V8h4.5L14 3.5z" fill={color} />
    </svg>
  ),
  Bubble: (color: string) => (
    <svg viewBox="0 0 24 24" width="16" height="16">
      <path d="M4 4h16v12H8l-4 4V4z" fill={color} />
    </svg>
  ),
  Gear: (color: string) => (
    <svg viewBox="0 0 24 24" width="16" height="16">
      <path d="M12 8a4 4 0 100 8 4 4 0 000-8zm9 4l-2.2.6a7.9 7.9 0 01-.9 2.1l1.3 1.9-2 2-1.9-1.3a7.9 7.9 0 01-2.1.9L12 21l-.6-2.2a7.9 7.9 0 01-2.1-.9L7.4 19.2l-2-2 1.3-1.9a7.9 7.9 0 01-.9-2.1L3 12l2.2-.6c.2-.7.5-1.4.9-2.1L4.8 7.4l2-2 1.9 1.3c.7-.4 1.4-.7 2.1-.9L12 3l.6 2.2c.7.2 1.4.5 2.1.9L16.6 5.4l2 2-1.3 1.9c.4.7.7 1.4.9 2.1L21 12z" fill={color} />
    </svg>
  ),
};

// Get icon for activity type
function getActivityIcon(type: ActivityType, color: string): React.ReactElement {
  switch (type) {
    case 'trade_entry_long':
      return Svg.Long(color);
    case 'trade_entry_short':
      return Svg.Short(color);
    case 'trade_win':
      return Svg.Up(color);
    case 'trade_loss':
      return Svg.Down(color);
    case 'strategy_updated':
      return Svg.Wrench(color);
    case 'market_query':
      return Svg.Bars(color);
    case 'agent_wait':
      return Svg.Clock(color);
    case 'observation_recorded':
      return Svg.Note(color);
    case 'analysis':
    case 'reasoning':
      return Svg.Bubble(color);
    case 'plan':
      return Svg.Gear(color);
    default:
      return Svg.Note(color);
  }
}

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

interface BalanceChartRechartsProps {
  balanceData: BalancePoint[];
  activities: Activity[];
  onActivityClick?: (activity: Activity) => void;
}

interface ChartDataPoint {
  time: number;
  balance: number;
  humanTime: string;
}

interface ClusteredMarker {
  time: number;
  balance: number;
  activities: Activity[];
  color: string;
  count: number;
  icon: React.ReactElement;
  activityType: ActivityType;
}

export default function BalanceChartRecharts({
  balanceData,
  activities,
  onActivityClick,
}: BalanceChartRechartsProps) {
  // Convert balance data to chart format - show ALL data
  const chartData: ChartDataPoint[] = useMemo(
    () =>
      balanceData
        .map((point) => {
          const time = new Date(point.timestamp).getTime();
          return {
            time,
            balance: point.balance,
            humanTime: new Date(point.timestamp).toLocaleString('en-US', { timeZone: 'UTC' }) + ' UTC',
          };
        })
        .sort((a, b) => a.time - b.time),
    [balanceData]
  );

  // Calculate time domain from all data
  const timeDomain = useMemo(() => {
    if (chartData.length === 0) return [0, 0];
    return [chartData[0].time, chartData[chartData.length - 1].time];
  }, [chartData]);

  // Interpolate balance at a given timestamp using STEP function (P&L is flat between trades)
  const interpolateBalance = useCallback((timestamp: number): number => {
    if (chartData.length === 0) return 0;
    if (chartData.length === 1) return chartData[0].balance;

    // Find the most recent balance point before or at this timestamp
    let beforeIdx = -1;
    for (let i = chartData.length - 1; i >= 0; i--) {
      if (chartData[i].time <= timestamp) {
        beforeIdx = i;
        break;
      }
    }

    // If timestamp is before all data, use first point
    if (beforeIdx === -1) return chartData[0].balance;

    // Step interpolation: use the balance from the most recent point
    return chartData[beforeIdx].balance;
  }, [chartData]);

  // Cluster activities by time window AND activity type (adaptive based on data span)
  const clusteredMarkers: ClusteredMarker[] = useMemo(() => {
    if (chartData.length === 0 || activities.length === 0) return [];

    // Calculate adaptive cluster window based on total time span
    const timeSpan = timeDomain[1] - timeDomain[0];
    // Aim for roughly 50-100 potential clusters across the entire span
    const clusterWindow = Math.max(
      5 * 60 * 1000,  // Minimum 5 minutes
      timeSpan / 50   // Or 1/50th of the total span
    );

    // Group by BOTH time bucket AND activity type
    const clusters: Map<string, Activity[]> = new Map();

    activities.forEach((activity) => {
      const time = new Date(activity.timestamp).getTime();
      const bucket = Math.floor(time / clusterWindow) * clusterWindow;

      // Create composite key: timeBucket_activityType
      const clusterKey = `${bucket}_${activity.type}`;

      if (!clusters.has(clusterKey)) {
        clusters.set(clusterKey, []);
      }
      clusters.get(clusterKey)!.push(activity);
    });

    // Create clustered markers (one per time+type combination)
    return Array.from(clusters.entries()).map(([, acts]) => {
      // Use the average timestamp of all activities in this cluster
      const avgTime = acts.reduce((sum, a) => sum + new Date(a.timestamp).getTime(), 0) / acts.length;

      // All activities in this cluster have the same type now
      const activityType = acts[0].type;
      const color = getActivityColor(activityType);
      const icon = getActivityIcon(activityType, color);

      return {
        time: avgTime,
        balance: interpolateBalance(avgTime),
        activities: acts,
        color,
        count: acts.length,
        icon,
        activityType,
      };
    }).sort((a, b) => a.time - b.time);
  }, [activities, chartData, timeDomain, interpolateBalance]);

  const startingBalance = chartData[0]?.balance || 0;

  const formatPrice = (value: number) => {
    return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC'
    });
  };

  const handleMarkerClick = (marker: ClusteredMarker) => {
    if (onActivityClick && marker.activities[0]) {
      onActivityClick(marker.activities[0]);
    }
  };

  if (chartData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full" style={{ color: VIBE.hair }}>
        <div className="text-center">
          <p className="text-sm">No chart data available</p>
          <p className="text-xs mt-2">Waiting for trades...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col">
      {/* Chart */}
      <div className="flex-1 relative">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart margin={{ top: 20, right: 40, left: 10, bottom: 20 }}>
            <defs>
              <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={VIBE.signal} stopOpacity={0.2} />
                <stop offset="95%" stopColor={VIBE.signal} stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke={VIBE.hair} opacity={0.2} />

            <XAxis
              dataKey="time"
              type="number"
              domain={timeDomain}
              tickFormatter={formatDate}
              tick={{ fill: VIBE.hair, fontSize: 11 }}
              stroke={VIBE.hair}
            />

            <YAxis
              orientation="right"
              tickFormatter={formatPrice}
              tick={{ fill: VIBE.hair, fontSize: 11 }}
              stroke={VIBE.hair}
              domain={['auto', 'auto']}
            />

            <Tooltip
              content={<CustomTooltip />}
              cursor={{ stroke: VIBE.brass, strokeWidth: 1, strokeDasharray: '5 5' }}
            />

            <ReferenceLine
              y={startingBalance}
              stroke={VIBE.hair}
              strokeDasharray="5 5"
              opacity={0.4}
            />

            {/* Balance line */}
            <Line
              data={chartData}
              type="monotone"
              dataKey="balance"
              stroke={VIBE.signal}
              strokeWidth={2.5}
              dot={false}
              isAnimationActive={false}
              fill="url(#balanceGradient)"
            />

            {/* Activity markers */}
            <Scatter
              data={clusteredMarkers}
              dataKey="balance"
              shape={(props: unknown) => {
                const { cx, cy, payload } = props as {
                  cx?: number;
                  cy?: number;
                  payload?: ClusteredMarker;
                };
                if (!cx || !cy || !payload) return <g />;

                const size = 24;
                const halfSize = size / 2;

                return (
                  <g
                    onClick={() => handleMarkerClick(payload)}
                    style={{ cursor: 'pointer' }}
                    className="hover:opacity-80 transition-opacity"
                  >
                    {/* Background circle */}
                    <circle
                      cx={cx}
                      cy={cy}
                      r={halfSize}
                      fill={VIBE.carbon}
                      stroke={payload.color}
                      strokeWidth={2}
                    />
                    {/* Icon */}
                    <foreignObject
                      x={cx - halfSize / 2}
                      y={cy - halfSize / 2}
                      width={halfSize}
                      height={halfSize}
                      style={{ pointerEvents: 'none' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
                        {getActivityIcon(payload.activityType, payload.color)}
                      </div>
                    </foreignObject>
                    {/* Count badge */}
                    {payload.count > 1 && (
                      <>
                        <circle
                          cx={cx + halfSize - 2}
                          cy={cy - halfSize + 2}
                          r={8}
                          fill={VIBE.brass}
                          stroke={VIBE.carbon}
                          strokeWidth={1.5}
                        />
                        <text
                          x={cx + halfSize - 2}
                          y={cy - halfSize + 2}
                          textAnchor="middle"
                          dominantBaseline="middle"
                          fill={VIBE.obsidian}
                          fontSize={9}
                          fontWeight="bold"
                          pointerEvents="none"
                        >
                          {payload.count}
                        </text>
                      </>
                    )}
                  </g>
                );
              }}
            />

            {/* Brush for pan/zoom */}
            <Brush
              dataKey="time"
              height={30}
              stroke={VIBE.brass}
              fill={VIBE.carbon}
              tickFormatter={formatDate}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Custom tooltip component
interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: ChartDataPoint | ClusteredMarker;
    dataKey?: string;
  }>;
}

function CustomTooltip({ active, payload }: TooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const data = payload[0].payload;

  return (
    <div
      className="rounded-lg border px-3 py-2 shadow-lg"
      style={{
        backgroundColor: VIBE.carbon,
        borderColor: VIBE.hair,
        color: VIBE.ivory,
      }}
    >
      <div className="text-xs font-semibold" style={{ color: VIBE.ivory }}>
        {formatPrice(data.balance)}
      </div>
      <div className="text-[10px]" style={{ color: VIBE.hair }}>
        {'humanTime' in data
          ? data.humanTime
          : new Date(data.time).toLocaleString('en-US', { timeZone: 'UTC' })} UTC
      </div>
    </div>
  );
}

function formatPrice(value: number) {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

// Get color for activity type
function getActivityColor(type: ActivityType): string {
  const colors: Record<ActivityType, string> = {
    trade_entry_long: VIBE.signal,
    trade_entry_short: VIBE.ember,
    trade_win: VIBE.signal,
    trade_loss: VIBE.ember,
    strategy_updated: VIBE.brass,
    market_query: VIBE.lilac,
    agent_wait: VIBE.hair,
    observation_recorded: VIBE.hair,
    analysis: VIBE.lilac,
    reasoning: VIBE.lilac,
    plan: VIBE.lilac,
  };

  return colors[type] || VIBE.ivory;
}
