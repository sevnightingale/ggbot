# FRONTEND_ARCHITECTURE.md

## 🧠 Overview

This document outlines the architecture, tooling, and component structure for the **ggbots** frontend—a high-performance, agent-based trading dashboard designed for clarity, speed, and precision.

Our goal is simple: build a lightweight, modular interface for managing and monitoring autonomous trading bots—without over-engineering or visual excess.

---

## 🚀 Tech Stack

### Framework
- **Next.js 14+ (App Router)** – File-based routing, great DX
- **TypeScript** – Safer code, better autocompletion
- **Tailwind CSS** – Utility-first styling, no CSS bloat

### State Management
- **Zustand** – Minimal global store for UI and bot states
- **Native fetch + polling** – Polling every 30–60s (no WebSockets in v1)

---

## 🧱 Project Structure

ggbot-frontend/
├── app/ # App Router pages
│ ├── layout.tsx # Global layout/providers
│ ├── page.tsx # Bot overview (default route)
│ └── bot/
│ └── [id]/page.tsx # Individual bot detail
├── components/
│ ├── ui/ # Buttons, inputs, modals
│ ├── bot/ # Agent layout, ggbot controls
│ ├── trades/ # Trade log components
│ └── charts/ # Performance chart components
├── lib/
│ ├── api/ # Typed API functions
│ ├── hooks/ # React + Zustand hooks
│ └── utils/ # Generic helpers
├── public/ # Assets
├── store/ # Zustand stores
├── types/ # TypeScript interfaces
└── styles/ # Tailwind config / base styles

yaml
Copy
Edit

---

## 🎨 Styling & Tokens

Tailwind config with custom tokens:

```ts
theme: {
  colors: {
    charcoal: {
      900: '#161618',
      800: '#1a1a1c',
    },
    bone: {
      200: '#e3e5e6',
      300: '#d0d2d3',
    },
    agents: {
      extraction: '#38a1c7',
      decision: '#2cbe77',
      trading: '#be6a47',
    }
  }
}
Use Tailwind for layout and styling

Simple CSS animations for visual effects (no complex libraries)

Native CSS transitions and keyframes only

## 🔧 Key Components

### components/bot/
- **AgentCircle.tsx** – Clickable agent node with glow animations
- **AgentFlowVisualization.tsx** – SVG container for agent layout + flow lines
- **BotControlPanel.tsx** – Start/stop/test UI
- **AgentConfigModal.tsx** – Tabbed agent configuration interface

### Animation Components:
- **FlowLine.tsx** – Animated SVG path showing data flow
- **GlowEffect.tsx** – Reusable glow animation wrapper

components/ui/
Button.tsx, Modal.tsx, Input.tsx – Basic primitives

TopNav.tsx – Minimal top navbar w/ hamburger menu

components/trades/
TradeTable.tsx – Tabular trade history

TradeDetailModal.tsx – Simple insight display

components/charts/
PerformanceChart.tsx – Recharts line chart for PnL

🧠 Zustand Store
ts
Copy
Edit
// store/bot.ts
import { create } from 'zustand'

export const useBotStore = create((set) => ({
  bots: [],
  currentBot: null,
  isConfigModalOpen: false,
  setBots: (bots) => set({ bots }),
  setCurrentBot: (bot) => set({ currentBot: bot }),
  toggleConfigModal: () =>
    set((s) => ({ isConfigModalOpen: !s.isConfigModalOpen })),
}))
📡 API Client
ts
Copy
Edit
const API_URL = process.env.NEXT_PUBLIC_API_URL
const USER_ID = process.env.NEXT_PUBLIC_USER_ID

export const api = {
  async getConfig(module: string) {
    return fetch(`${API_URL}/agent/api/config/${USER_ID}/${module}`).then(res => res.json())
  },
  async updateConfig(module: string, config: any) {
    return fetch(`${API_URL}/agent/api/config/${USER_ID}/${module}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config }),
    }).then(res => res.json())
  },
  async startScheduler() {
    return fetch(`${API_URL}/agent/api/scheduler/start`, { method: 'POST' }).then(res => res.json())
  },
  async stopScheduler() {
    return fetch(`${API_URL}/agent/api/scheduler/stop`, { method: 'POST' }).then(res => res.json())
  },
  async getTrades() {
    return fetch(`${API_URL}/dashboard/api/dashboard/${USER_ID}/trades`).then(res => res.json())
  },
  async getPerformance(period = '7d') {
    return fetch(`${API_URL}/dashboard/api/dashboard/${USER_ID}/performance?period=${period}`).then(res => res.json())
  }
}
🌐 Routing
Pages:

/ – Bot list + create

/bot/[id] – Configuration + live performance

/settings – API key setup (later)

Future: /discover, /subscribe

Nav:

Top-right hamburger icon

Expands to basic links (simple overlay panel)

📊 Charting
Library: Recharts

Charts: Line for PnL, bar/pie optional later

Interaction: Hover only, no animations

Responsiveness: Full container width/height

🐳 Deployment
Primary: Vercel (CI/CD, previews, CDN, env management)

Vercel PR previews auto-deploy

Main → production

🧰 Key Libraries
Purpose	Library
Routing	Next.js App Router
State	Zustand
Styling	Tailwind CSS
Forms	React Hook Form + Zod
Charts	Recharts
Icons	Lucide React
Dates	date-fns

## 🎨 Animation Guidelines

### CSS-Only Visual Effects:
```css
/* Agent glow effect */
.agent-circle {
  transition: all 0.3s ease;
}

.agent-circle.configured {
  animation: pulse-glow 2s ease-in-out infinite;
  box-shadow: 0 0 20px var(--agent-color);
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.8; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.02); }
}

/* Flow line animation */
.flow-line {
  stroke-dasharray: 5 10;
  animation: flow 3s linear infinite;
}

@keyframes flow {
  to { stroke-dashoffset: -15; }
}
```

### Implementation Notes:
- Use CSS custom properties for agent colors
- GPU-accelerated transforms only
- Subtle effects (2-3s duration, minimal movement)
- Disable animations based on prefers-reduced-motion

## ✅ Principles
Build for function first – No fluff

Validate as you go – Feedback before features

Simple, performant animations that enhance understanding

Use your own product—hard

This is ggbots:
Clean. Fast. Trader-first.
Built to think like you.
