'use client';

import React, { useEffect, useState, useRef } from 'react';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, LineData, Time } from 'lightweight-charts';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import type { Session } from '@supabase/supabase-js';

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

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [metadata, setMetadata] = useState<ActivityMetadata | null>(null);

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
        const [balanceSeriesRes, metadataRes] = await Promise.all([
          fetch(`/api/v2/activities/${configId}/balance-series?mode=pnl`, { headers }),
          fetch(`/api/v2/activities/${configId}/metadata`, { headers }),
        ]);

        console.log('API responses:', {
          balanceOk: balanceSeriesRes.ok,
          balanceStatus: balanceSeriesRes.status,
          metadataOk: metadataRes.ok,
          metadataStatus: metadataRes.status
        });

        if (!balanceSeriesRes.ok || !metadataRes.ok) {
          const balanceError = await balanceSeriesRes.text();
          const metadataError = await metadataRes.text();
          console.error('API errors:', { balanceError, metadataError });
          throw new Error(`Failed to fetch timeline data: ${balanceSeriesRes.status}, ${metadataRes.status}`);
        }

        const [balanceSeries, metadataData] = await Promise.all([
          balanceSeriesRes.json(),
          metadataRes.json(),
        ]);

        const balancePoints: BalancePoint[] = balanceSeries.balance_series || [];
        console.log('Raw balance points sample:', balancePoints.slice(0, 2));

        setMetadata({
          botName: metadataData.metadata?.botName || metadataData.bot_name || metadataData.botName || 'Unknown Bot',
          startingBalance: metadataData.metadata?.startingBalance || metadataData.startingBalance || metadataData.starting_balance || 0,
          currentBalance: metadataData.metadata?.currentBalance || metadataData.currentBalance || metadataData.current_balance || 0,
          totalTrades: metadataData.metadata?.totalTrades || metadataData.totalTrades || metadataData.total_trades || 0,
          winRate: metadataData.metadata?.winRate || metadataData.winRate || metadataData.win_rate || 0,
          performance: metadataData.metadata?.performance || metadataData.performance || 0,
        });

        // Transform and validate data
        const chartData: LineData[] = balancePoints
          .map((point) => {
            const timestamp = new Date(point.timestamp).getTime() / 1000;
            return {
              time: timestamp as Time,
              value: point.balance,
            };
          })
          .filter((point) => {
            // Filter out invalid data points
            const timeNum = typeof point.time === 'number' ? point.time : parseFloat(point.time as string);
            const isValid = !isNaN(timeNum) && point.value !== null && point.value !== undefined && !isNaN(point.value);
            if (!isValid) {
              console.warn('Filtered out invalid data point:', point);
            }
            return isValid;
          })
          .sort((a, b) => {
            const aTime = typeof a.time === 'number' ? a.time : parseFloat(a.time as string);
            const bTime = typeof b.time === 'number' ? b.time : parseFloat(b.time as string);
            return aTime - bTime;
          }); // TradingView requires sorted data

        console.log('Balance points:', balancePoints.length);
        console.log('Chart data after validation:', chartData.length);
        console.log('First 3 points:', chartData.slice(0, 3));
        console.log('Last 3 points:', chartData.slice(-3));
        console.log('Line series ref exists:', !!lineSeriesRef.current);

        if (lineSeriesRef.current && chartData.length > 0) {
          console.log('Setting data on chart...');
          lineSeriesRef.current.setData(chartData);
          chartRef.current?.timeScale().fitContent();
          console.log('Data set successfully');
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
    </div>
  );
}
