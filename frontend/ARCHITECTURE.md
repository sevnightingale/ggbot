# FRONTEND_ARCHITECTURE.md

## 🧠 Overview

This document outlines the architecture, tooling, and component structure of the **ggbots** frontend. The goal is a performant, immersive, single-screen trading agent dashboard built with modern best practices and a cinematic UX flow.

---

## 🚀 Tech Stack

### Framework
- **Next.js 14+ (App Router)** – App-centric, file-based routing
- **TypeScript** – Full static typing and API contract safety
- **Tailwind CSS** – Utility-first styling with design tokens
- **CSS Modules** – Scoped styles for complex animations
- **Framer Motion** – UI animation (carousel, agent glow, transitions)

### State Management
- **Zustand** – Global UI state (active bot, modal, etc.)
- **TanStack Query** – Server state (fetching, caching, real-time)
- **WebSocket** – Live trade updates and bot feedback

---

## 🧱 Project Structure

ggbot-frontend/
├── app/ # Next.js App Router
│ ├── layout.tsx # Global layout with providers
│ ├── page.tsx # Landing page (static)
│ ├── app/ # Main ggbot interface (default route)
│ │ ├── page.tsx # ggbot Dashboard (single-screen)
│ │ └── components/ # Dashboard-specific components
│ ├── auth/ # Login/register (future)
│ └── api/ # Optional proxy routes (if needed)
├── components/ # Shared components
│ ├── ui/ # Buttons, modals, typography, etc.
│ ├── agents/ # ggbot visual interface components
│ ├── trades/ # Trade log table + viewer
│ ├── charts/ # Performance visualizations
├── lib/
│ ├── api/ # API clients (typed fetch functions)
│ ├── hooks/ # Reusable logic + Zustand hooks
│ ├── utils/ # Helper logic
│ ├── constants/ # App-wide values and color maps
│ └── schema/ # zod validation schemas
├── public/ # Static assets
├── styles/ # Tailwind config and globals
├── store/ # Zustand global store
└── types/ # TypeScript types and interfaces

yaml
Copy
Edit

---

## 🎨 Styling

### Tailwind Theme Tokens (tailwind.config.js)
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
  },
}
Usage
Use Tailwind for layout, typography, base UI

Use CSS Modules for orbiting agent animation, pulsing glows, line transitions

📦 Key Components
/components/agents/
GGBotCore.tsx – Central ggbot orb + config status

AgentNode.tsx – Extraction / Evaluation / Execution agent buttons

AgentLines.tsx – SVG-based link lines between agents

GGBotCarousel.tsx – Bot selector with arrow controls and + button

ConfigureAgentModal.tsx – Agent config modals (one per agent type)

/components/ui/
MenuOverlay.tsx – Slide-out top-right nav

DeployButton.tsx – Appears once all agents configured

Button.tsx, Modal.tsx, Tooltip.tsx, etc.

/components/trades/
TradeTable.tsx – Trade log (live + closed)

TradeDetailModal.tsx – Expanded trade view (LLM reasoning, data)

/components/charts/
PerformanceChart.tsx – PnL over time

WinLossChart.tsx – Win rate breakdown

🔗 Zustand Store Example
ts
Copy
Edit
// store/ggbot.ts
import { create } from 'zustand'

export const useGGBotStore = create((set) => ({
  activeBotIndex: 0,
  bots: [], // [{ id, config: {}, status }]
  selectedTrade: null,
  setBotConfig: (id, agent, config) => { /* update logic */ },
  addNewBot: () => { /* create new ggbot */ },
  setActiveBot: (index) => set({ activeBotIndex: index }),
}))
📡 API Client
ts
Copy
Edit
// lib/api/client.ts
export class GGBotAPI {
  async getConfig(module: AgentModule) {
    return fetch(`${API_URL}/agent/api/config/${userId}/${module}`)
  }

  async startScheduler() {
    return fetch(`${API_URL}/agent/api/scheduler/start`, {
      method: 'POST'
    })
  }
}
🌐 Navigation System
Minimal top-right menu (hamburger)

Expands to reveal:

My ggbots

Discover (soon)

Analytics (future)

Settings

Profile / Logout

No sidebar. Entire UI lives within one immersive scene.

📊 Charting & Visuals
Recharts → Simple, React-native performance charts for P&L and metrics

Framer Motion → agent activation animations, carousel, modals

SVG Lines → animate agent connections + “power on” effects

🐳 Deployment
Vercel (primary)
One-click preview deploys

Global CDN, auto environment management

Docker (optional)
Dockerfile
Copy
Edit
FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm ci && npm run build
CMD ["npm", "start"]
🧪 Development Workflow
bash
Copy
Edit
# Local dev
npm run dev
# API runs on localhost:8000
PRs auto-deploy to Vercel

Staging connects to staging API

Main branch deploys to production

📚 Libraries
Purpose	Library
Routing / SSR	Next.js
State	Zustand + TanStack Query
Styling	Tailwind CSS + CSS Modules
Forms	React Hook Form + Zod
Animations	Framer Motion
Charts	Recharts
Icons	Lucide React
Dates	date-fns

✅ Summary
This frontend is designed for focus and flow—a control panel for live trading agents, not a noisy admin dashboard. Every layer supports an immersive, performant, visual-first experience.

Keep it minimal. Keep it responsive.
Make it glow when it thinks.

— ggbots