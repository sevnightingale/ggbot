export type IndicatorCategory = 'momentum' | 'trend' | 'volatility' | 'volume' | 'premium'

export interface Indicator {
  name: string
  label: string
  description: string
  category: IndicatorCategory
  defaultTimeframes: string[]
  isPremium?: boolean
}

export const AVAILABLE_TIMEFRAMES = [
  { value: '15m', label: '15m' },
  { value: '1h', label: '1h' },
  { value: '4h', label: '4h' },
  { value: '1d', label: '1d' }
]

export const INDICATORS: Indicator[] = [
  // Premium
  {
    name: 'ggshot',
    label: 'ggShot',
    description: 'AI-powered high-confidence trading signals',
    category: 'premium',
    defaultTimeframes: ['15m', '1h'],
    isPremium: true
  },
  
  // Momentum Indicators
  {
    name: 'rsi',
    label: 'RSI',
    description: 'Relative Strength Index - Identifies overbought/oversold conditions',
    category: 'momentum',
    defaultTimeframes: ['15m', '1h']
  },
  {
    name: 'stochastic',
    label: 'Stochastic',
    description: 'Momentum indicator comparing closing price to price range',
    category: 'momentum',
    defaultTimeframes: ['15m', '1h']
  },
  {
    name: 'williams_r',
    label: 'Williams %R',
    description: 'Momentum indicator showing overbought/oversold levels',
    category: 'momentum',
    defaultTimeframes: ['15m', '1h']
  },
  {
    name: 'roc',
    label: 'ROC',
    description: 'Rate of Change - Measures momentum as percentage change',
    category: 'momentum',
    defaultTimeframes: ['1h', '4h']
  },
  {
    name: 'cci',
    label: 'CCI',
    description: 'Commodity Channel Index - Identifies cyclical trends',
    category: 'momentum',
    defaultTimeframes: ['1h', '4h']
  },
  
  // Trend Indicators
  {
    name: 'macd',
    label: 'MACD',
    description: 'Moving Average Convergence Divergence - Trend following momentum',
    category: 'trend',
    defaultTimeframes: ['1h', '4h']
  },
  {
    name: 'ema',
    label: 'EMA',
    description: 'Exponential Moving Average - Weighted trend indicator',
    category: 'trend',
    defaultTimeframes: ['1h', '4h']
  },
  {
    name: 'adx',
    label: 'ADX',
    description: 'Average Directional Index - Measures trend strength',
    category: 'trend',
    defaultTimeframes: ['4h', '1d']
  },
  {
    name: 'aroon',
    label: 'Aroon',
    description: 'Identifies trend changes and strength',
    category: 'trend',
    defaultTimeframes: ['4h', '1d']
  },
  {
    name: 'parabolic_sar',
    label: 'Parabolic SAR',
    description: 'Stop and Reverse - Trend following indicator',
    category: 'trend',
    defaultTimeframes: ['1h', '4h']
  },
  {
    name: 'vortex',
    label: 'Vortex',
    description: 'Identifies trend direction and reversals',
    category: 'trend',
    defaultTimeframes: ['1h', '4h']
  },
  {
    name: 'trix',
    label: 'TRIX',
    description: 'Triple Exponential Average - Filters market noise',
    category: 'trend',
    defaultTimeframes: ['4h', '1d']
  },
  
  // Volatility Indicators
  {
    name: 'bollinger_bands',
    label: 'Bollinger Bands',
    description: 'Volatility bands around moving average',
    category: 'volatility',
    defaultTimeframes: ['1h', '4h']
  },
  {
    name: 'bollinger_bands_width',
    label: 'BB Width',
    description: 'Bollinger Bands Width - Measures volatility',
    category: 'volatility',
    defaultTimeframes: ['1h', '4h']
  },
  {
    name: 'atr',
    label: 'ATR',
    description: 'Average True Range - Measures market volatility',
    category: 'volatility',
    defaultTimeframes: ['1h', '4h']
  },
  {
    name: 'keltner_channel',
    label: 'Keltner Channel',
    description: 'Volatility-based envelope indicator',
    category: 'volatility',
    defaultTimeframes: ['4h', '1d']
  },
  {
    name: 'donchian_channel',
    label: 'Donchian Channel',
    description: 'Shows highest high and lowest low over period',
    category: 'volatility',
    defaultTimeframes: ['4h', '1d']
  },
  
  // Volume Indicators
  {
    name: 'obv',
    label: 'OBV',
    description: 'On-Balance Volume - Volume momentum indicator',
    category: 'volume',
    defaultTimeframes: ['1h', '4h']
  },
  {
    name: 'mfi',
    label: 'MFI',
    description: 'Money Flow Index - Volume-weighted momentum',
    category: 'volume',
    defaultTimeframes: ['1h', '4h']
  },
  {
    name: 'vwap',
    label: 'VWAP',
    description: 'Volume Weighted Average Price',
    category: 'volume',
    defaultTimeframes: ['15m', '1h']
  }
]

export const CATEGORY_COLORS = {
  premium: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/40',
  momentum: 'text-blue-400 bg-blue-400/10 border-blue-400/40',
  trend: 'text-green-400 bg-green-400/10 border-green-400/40',
  volatility: 'text-orange-400 bg-orange-400/10 border-orange-400/40',
  volume: 'text-purple-400 bg-purple-400/10 border-purple-400/40'
}

export const CATEGORY_LABELS = {
  premium: 'Premium',
  momentum: 'Momentum',
  trend: 'Trend',
  volatility: 'Volatility',
  volume: 'Volume'
}