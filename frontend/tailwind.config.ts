import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Legacy charcoal colors (keep for backwards compatibility)
        charcoal: {
          900: '#161618',
          800: '#1a1a1c',
          700: '#1e1e20',
          600: '#222224',
          500: '#4a4a50',
        },
        // Legacy bone colors (keep for backwards compatibility)
        bone: {
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#e3e5e6',
          300: '#d0d2d3',
          400: '#a8abac',
          500: '#6b6f71',
        },
        // New ceremonial brutalism palette (trade37 inspired)
        obsidian: '#0b0b0c',
        carbon: '#141416',
        ivory: '#edebe7',
        alloy: '#8a8781',
        brass: {
          DEFAULT: '#c1a87d',     // Dark mode accent
          light: '#d4bc91',       // Hover state
          dark: '#8a7859',        // Light mode accent
        },
        signal: '#3ca6e0',
        ember: '#d74a1f',
        // Legacy agent colors (deprecated - use brass instead)
        agents: {
          extraction: '#38a1c7',
          decision: '#2cbe77',
          trading: '#be6a47',
        },
        status: {
          success: '#2cbe77',
          warning: '#f59e0b',
          error: '#ef4444',
        }
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'flow': 'flow 3s linear infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { 
            opacity: '0.8',
            transform: 'scale(1)',
          },
          '50%': { 
            opacity: '1',
            transform: 'scale(1.02)',
          },
        },
        'flow': {
          'to': {
            'stroke-dashoffset': '-15',
          },
        },
      },
      backgroundImage: {
        'grid-pattern': 'linear-gradient(to right, rgba(227, 229, 230, 0.1) 1px, transparent 1px), linear-gradient(to bottom, rgba(227, 229, 230, 0.1) 1px, transparent 1px)',
      },
      backgroundSize: {
        'grid': '20px 20px',
      },
    },
  },
  plugins: [],
}

export default config