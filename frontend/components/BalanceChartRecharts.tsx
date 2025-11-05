'use client';

import { useState } from 'react';
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

// Activity types
type ActivityType =
  | 'trade_entry_long'
  | 'trade_entry_short'
  | 'trade_win'
  | 'trade_loss'
  | 'trade_exit'
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

interface ActivityMarker extends Activity {
  time: number;
  balance: number;
  color: string;
  humanTime: string;
}

export default function BalanceChartRecharts({
  balanceData,
  activities,
  onActivityClick,
}: BalanceChartRechartsProps) {
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);

  // Convert balance data to chart format
  const chartData: ChartDataPoint[] = balanceData
    .map((point) => {
      const time = new Date(point.timestamp).getTime();
      return {
        time,
        balance: point.balance,
        humanTime: new Date(point.timestamp).toLocaleString(),
      };
    })
    .sort((a, b) => a.time - b.time);

  // Create activity markers aligned with balance line
  const activityMarkers: ActivityMarker[] = activities
    .map((activity) => {
      const time = new Date(activity.timestamp).getTime();

      // Find closest balance point to this activity
      const closestBalance = chartData.reduce((prev, curr) =>
        Math.abs(curr.time - time) < Math.abs(prev.time - time) ? curr : prev
      );

      return {
        ...activity,
        time,
        balance: closestBalance?.balance || 0,
        color: getActivityColor(activity.type),
        humanTime: new Date(activity.timestamp).toLocaleString(),
      };
    })
    .sort((a, b) => a.time - b.time);

  const startingBalance = chartData[0]?.balance || 0;

  const formatPrice = (value: number) => {
    return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const handleActivityClick = (marker: ActivityMarker) => {
    setSelectedActivity(marker);
    if (onActivityClick) {
      onActivityClick(marker);
    }
  };

  if (chartData.length === 0) {
    return (
      <div
        className="flex items-center justify-center h-full"
        style={{ color: VIBE.hair }}
      >
        <div className="text-center">
          <p className="text-sm">No chart data available</p>
          <p className="text-xs mt-2">Waiting for trades...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
          <defs>
            <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={VIBE.signal} stopOpacity={0.3} />
              <stop offset="95%" stopColor={VIBE.signal} stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke={VIBE.hair} opacity={0.3} />

          <XAxis
            dataKey="time"
            type="number"
            domain={['dataMin', 'dataMax']}
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
            opacity={0.5}
            label={{
              value: 'Start',
              fill: VIBE.hair,
              fontSize: 10,
              position: 'right',
            }}
          />

          {/* Balance line */}
          <Line
            data={chartData}
            type="monotone"
            dataKey="balance"
            stroke={VIBE.signal}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
            fill="url(#balanceGradient)"
          />

          {/* Activity markers */}
          <Scatter
            data={activityMarkers}
            dataKey="balance"
            shape={(props: unknown) => {
              const { cx, cy, payload } = props as {
                cx?: number;
                cy?: number;
                payload?: ActivityMarker;
              };
              if (!cx || !cy || !payload) return <g />;

              return (
                <circle
                  cx={cx}
                  cy={cy}
                  r={5}
                  fill={payload.color}
                  stroke={VIBE.carbon}
                  strokeWidth={1}
                  className="cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => handleActivityClick(payload)}
                  style={{ cursor: 'pointer' }}
                />
              );
            }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Activity detail tooltip on the side */}
      {selectedActivity && (
        <div
          className="absolute top-4 right-4 rounded-lg border p-3 shadow-lg max-w-xs"
          style={{
            backgroundColor: VIBE.carbon,
            borderColor: VIBE.hair,
            color: VIBE.ivory,
          }}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wide">
              {selectedActivity.type.replace(/_/g, ' ')}
            </span>
            <button
              onClick={() => setSelectedActivity(null)}
              className="text-xs hover:opacity-70"
              style={{ color: VIBE.hair }}
            >
              ✕
            </button>
          </div>
          <div className="text-xs space-y-1" style={{ color: VIBE.hair }}>
            <p>{(selectedActivity.data.summary as string) || 'No details'}</p>
            <p className="text-[10px]">
              {new Date(selectedActivity.timestamp).toLocaleString()}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// Custom tooltip component
interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: ChartDataPoint | ActivityMarker;
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
        {data.humanTime}
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
    trade_exit: VIBE.brass,
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
