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
        charcoal: {
          900: '#161618',
          800: '#1a1a1c',
          700: '#1e1e20',
          600: '#222224',
          500: '#4a4a50',
        },
        bone: {
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#e3e5e6',
          300: '#d0d2d3',
          400: '#a8abac',
          500: '#6b6f71',
        },
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
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Kanit', 'system-ui', 'sans-serif'],
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