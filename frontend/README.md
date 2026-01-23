# ggbots Frontend - Forge Architecture

**Next.js 15 + TypeScript + Tailwind CSS + Supabase + Real-time SSE**

---

## 🚀 Current Status: PRODUCTION READY - FORGE ARCHITECTURE

### **✅ FORGE - COMPLETE AUTONOMOUS TRADING PLATFORM**
- **Architecture**: Clean local-state design with SSE real-time updates
- **Multi-Bot Management**: Native support for unlimited trading agents per user
- **Configuration System**: Complete sandboxed editing with premium feature gating
- **Authentication**: Full Supabase integration with permission-based access control
- **Real-time Data**: Live positions, decisions, and account tracking via Server-Sent Events
- **Permission System**: Comprehensive premium feature gatekeeping for monetization

### **✅ AUTHENTICATION & LANDING SYSTEM**
- **Landing Pages**: Modern marketing site with new-landing ready for deployment
- **Auth Flow**: Email/password signup → verification → dashboard access
- **Protected Routes**: Server-side session guards with automatic redirects
- **Permission Gates**: Subscription tier-based feature access control

---

## 🏗 Architecture Overview

### **Current Page Structure**
```
Production Pages:
├── /forge                    # Main application (Forge architecture)
├── /arena                   # ggArena competition page
├── /new-landing             # Modern landing page (ready to replace /landing)
├── /login                   # Supabase authentication (login)
├── /signup                  # Supabase authentication (signup)
├── /auth/callback           # Email verification handler
├── /success                 # Subscription success page
└── /credits/success         # Credit purchase success page

Legacy/Archive (Moved to /archive/):
├── frontend-dashboard       # Deprecated WebSocket-based dashboard
├── frontend-landing-components # Old landing page components
└── frontend-store          # Archived Zustand botStore complexity
```

### **Forge Architecture (Production)**
```
/forge/components/
├── layout/                  # Application shell
│   ├── Header.tsx          # Branding, theme toggle, user profile
│   ├── BotRail.tsx         # Multi-bot sidebar with management
│   ├── TabNavigation.tsx   # Monitor/Configure tab switching
│   ├── MobileNav.tsx       # Mobile responsive navigation
│   └── UserProfile.tsx     # Profile dropdown with subscription status + usage display
│
├── monitor/                 # Real-time operational dashboard
│   ├── ActivationBar.tsx   # Bot status/control with daily cost display
│   └── PositionsTable.tsx  # Live trading positions with real-time P&L
│
├── configure/               # Bot configuration system (auto-save)
│   ├── ConfigureLayout.tsx # Main layout with Strategy Advisor panel + SaveStatusContext
│   ├── ConfigTabs.tsx      # Sub-navigation (Strategy | Market Data | Trade Settings | Signals)
│   ├── StrategyEditor.tsx  # AI prompt editing with LLM provider selection (auto-saves)
│   ├── MarketDataSelector.tsx # Technical indicator selection with premium gates (auto-saves)
│   ├── TradeSettings.tsx   # Position sizing, risk management, Telegram integration (auto-saves)
│   └── SignalsConfiguration.tsx # External signal sources (ggShot) (auto-saves)
│
└── shared/                  # Reusable components
    ├── ThemeToggle.tsx     # Dark/light mode switching
    ├── EmptyState.tsx      # Guidance for empty states
    └── LoadingSkeleton.tsx # Loading placeholders

/components/                 # Global components
├── tv-timeline.tsx         # AI consciousness timeline - bot's subjective awareness moments with equity chart
├── bottom-sheet.tsx        # Framer Motion slide-up drawer (centered on desktop) for activity details
├── StrategyAdvisorPanel.tsx # Inline AI chat for bot configuration (500px fixed, markdown rendering)
│                           #   Buttons: "Explain Strategy" (understand), "Update Strategy" (iterate), "Analyze Performance" (after trades)
├── OnboardingTour.tsx      # First-time user tutorial overlay - spotlight + tooltip, localStorage persistence, keyboard nav
├── SaveStatusIndicator.tsx # Global operation status (Saving/Saved/Error) with custom message support
├── BotImageUpload.tsx      # Bot profile image uploader - drag-drop, auto-resize to 1024×1024, Supabase Storage
├── HelpWidget.tsx          # Floating help widget with Telegram community invite
├── SymbolSelector.tsx      # Symbol dropdown with search (141 validated pairs)
├── UpgradeModal.tsx        # Payment chooser: "Pay as you go" vs "Prepay credits" with Stripe checkout
├── CreditPicker.tsx        # Credit amount selector ($10-$100) with Card/Crypto payment toggle
├── AddCreditsModal.tsx     # Modal wrapper for CreditPicker (for existing subscribers)
└── ValidationMessage.tsx   # Error/warning message component with icons

/components/ui/              # UI components
├── modal.tsx               # Unified modal system - Framer Motion animations, responsive sizes (sm/md/lg/xl/full),
│                           #   focus trap, portal rendering, full-screen mobile. Exports: Modal, ModalHeader,
│                           #   ModalBody, ModalFooter, ModalTitle, ModalDescription. Use for ALL modals.
├── dialog.tsx              # Radix UI Dialog wrapper (DEPRECATED - use modal.tsx instead)
├── button.tsx              # Button component with variants
├── card.tsx                # Card layout component
├── badge.tsx               # Badge/pill component
└── input.tsx               # Input field component

/forge/components/modals/    # Bot management modals
├── BotCreationModal.tsx    # 5-step typeform-style onboarding (Name→Mode→Symbol→Strategy→Model)

/lib/                        # Core utilities
├── archetypes.ts           # Trading archetype templates (Contrarian, Compass, Arbiter)
├── permissions.tsx         # Permission context with subscription checks
├── permission-gate.tsx     # Component for gating premium features
├── useTradeValidation.ts   # Trading settings validation hook
├── hooks/
│   ├── useBatchedConfigSave.ts  # Unified batched config save with dirty tracking (2025-12-04)
│   └── useAutoSave.ts      # Legacy: Debounced auto-save (deprecated, use useBatchedConfigSave)
├── contexts/
│   └── SaveStatusContext.tsx # Global operation status (supports custom messages for bot operations)
├── api.ts                  # API client with Stripe methods
├── theme.tsx               # Dark/light theme provider
└── supabase.ts             # Supabase client setup
```

---

## 🎯 Forge Architecture Highlights

### **Local State Design**
- **No Global Store**: Direct API types, no transformation layers
- **Multi-Bot Native**: `selectedConfigId` pattern with seamless switching
- **SSE Real-time**: Server-Sent Events replace complex WebSocket patterns
- **Unified Batched Save**: Single hook manages all config saves with 5s debounce + dirty field tracking (2025-12-04)
- **Optimistic Updates**: Bot operations (delete/duplicate/rename/reset) update UI immediately, rollback on error (2026-01-13)
- **AI-First Configuration**: Strategy Advisor inline chat panel for collaborative bot setup

### **Real-time Data Flow**
```typescript
// SSE connection with filtered data streams
const eventSource = new EventSource(`${apiUrl}/api/v2/dashboard/stream?user_id=${userId}`)

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data)

  // Filter for currently selected bot
  if (data.config_id === selectedConfigIdRef.current) {
    setPositions(data.positions)
    setAccounts(data.accounts)
    setExecutionStatus(data.execution_status)
  }
}
```

### **Configuration Architecture** (Unified Batched Save - 2025-12-04)

All configuration components are now **controlled components** that call `onUpdate()` - no direct API calls.
The parent `page.tsx` owns all state and save logic via `useBatchedConfigSave` hook.

```
┌─────────────────────────────────────────────────────────────────┐
│                         page.tsx                                 │
│                                                                  │
│   useBatchedConfigSave({ delay: 5000 })                         │
│         │                                                        │
│         ├── Accumulates all changes into queue                   │
│         ├── Tracks dirty fields                                  │
│         ├── 5 second debounce                                    │
│         └── Single batched API call                              │
│                                                                  │
│   SSE Handler                                                    │
│         └── Updates only non-dirty fields                        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
   StrategyEditor     TradeSettings    MarketDataSelector
   (controlled)       (controlled)     (controlled)

   All components just call onUpdate() - no direct API calls
```

```typescript
// Unified batched config save with dirty field tracking (page.tsx)
const { queueChange, isFieldDirty } = useBatchedConfigSave({
  configId: selectedConfigId,
  configName: editingTableFields?.config_name,
  configType: editingTableFields?.config_type,
  delay: 5000,  // 5s batch window
  enabled: activeTab === 'configure',
})

// Unified config change handler - used by ALL config components
const handleConfigChange = useCallback((updates: Partial<ConfigData>) => {
  // 1. Update local state immediately (optimistic UI)
  setEditingConfigData(prev => deepMerge(prev, updates))
  // 2. Queue for batched save
  queueConfigChange(updates)
}, [queueConfigChange])

// SSE handler with dirty field protection
// User wins for fields they're editing, SSE updates non-dirty fields
if (!isFieldDirty('decision')) {
  merged.decision = serverConfig.decision  // Safe to update
}
```

**Conflict Resolution**: When AI edits (via SSE) and user edits simultaneously:
- **Dirty fields** (user editing): User wins, preserved
- **Non-dirty fields**: Updated from SSE
- **After save completes**: Dirty tracking clears

### **Optimistic Update Pattern** (2026-01-13)

Bot operations use optimistic updates - UI changes immediately, API runs async, rollback on error:

```typescript
// Pattern: Capture → Update → API → Rollback on error
const handleDeleteBot = async (configId: string) => {
  // 1. Capture previous state for rollback
  const previousBots = allBots

  // 2. Optimistic update - IMMEDIATE
  setAllBots(prev => prev.filter(bot => bot.config_id !== configId))

  // 3. API call (async, user already sees result)
  try {
    await apiClient.deleteConfig(configId)
  } catch (error) {
    // 4. Rollback on failure + show error
    setAllBots(previousBots)
    failSave('delete-bot', new Error('Failed to delete bot'))
  }
}
```

**Applies to**: `handleDeleteBot`, `handleDuplicateBot`, `handleRenameBot`, `handleResetAccount`

**Feedback**: Uses `useSaveStatus()` from SaveStatusContext for error display. Reset shows "Resetting..." → "Account reset".

---

## 📐 Forge Page Layout Architecture

### **Container Hierarchy**

```
<div className="min-h-screen bg-[var(--bg-primary)]">
  <Header />  // Fixed height: ~64px

  {/* 12-column grid container */}
  <div className="grid max-w-7xl grid-cols-12 gap-4 px-4 py-4 min-h-[calc(100vh-64px)]">

    {/* BotRail - LEFT COLUMN (25% width on desktop) */}
    <BotRail className="col-span-12 hidden md:col-span-3 md:block" />

    {/* Main Content - RIGHT COLUMN (75% width on desktop) */}
    <main className="col-span-12 md:col-span-9 flex flex-col pb-16 md:pb-0">
      <ActivationBar />        // Height: ~80-120px (dynamic), padding: p-4 (16px)
      <TabNavigation />        // Height: ~48px, spacing: my-3 (12px)

      {/* Tab Content Area */}
      <div className="flex-1 pb-8">
        {activeTab === 'monitor' ? (
          <div className="space-y-3">  // 12px vertical gaps
            <TVTimeline variant="embedded" />  // Height: 600px fixed, padding: p-4
            <PositionsTable />                 // Height: Variable, padding: p-4
          </div>
        ) : (
          <ConfigureLayout />  // Height: Variable (scrollable), all sections: p-4
        )}
      </div>
    </main>
  </div>

  <MobileNav className="md:hidden" />  // Fixed at bottom on mobile
</div>
```

### **Spacing & Padding Standards** (2025-11-23)
- **Component padding**: All components use `p-4` (16px) uniformly
- **Vertical gaps**: 12px (`space-y-3`, `my-3`) between major sections
- **Configure sections**: 24px gaps (`space-y-6`) between config blocks
- **Batched save pattern**: All config saves go through `useBatchedConfigSave` hook in page.tsx
```typescript
// Config components just call onUpdate - no direct API calls
onUpdate?.({ decision: { user_prompt: newValue } })
```

### **Width & Spacing Constraints**

```typescript
// Container widths
max-w-7xl          // 1280px maximum container width
px-4               // 16px horizontal padding (mobile)
gap-4              // 16px grid gap between columns

// Column distribution (desktop)
BotRail:    col-span-3 (3/12 = 25%)  // ~320px @ 1280px container
Main:       col-span-9 (9/12 = 75%)  // ~960px @ 1280px container

// Timeline in main content
- Full width of main column: 960px available
- Embedded height: 600px fixed
- Enough space for readable TradingView chart
```

### **Height Constraints**

```typescript
// Viewport calculations
min-h-screen                     // 100vh (full viewport)
Header:                          // ~64px
Grid container:                  // min-h-[calc(100vh-64px)]

// Main content area
pb-32                            // 128px bottom padding (for readability)
Available for content:           // ~calc(100vh - 64px - 128px - 48px)
                                 // = ~calc(100vh - 240px) accounting for tabs

// Component heights
ActivationBar:      ~80-120px (dynamic)
TabNavigation:      ~48px
TVTimeline:         600px (embedded mode)
PositionsTable:     Variable (auto, based on open positions)
```

### **Responsive Breakpoints**

```typescript
// Tailwind breakpoints
sm:   640px   // Small devices
md:   768px   // Tablets (BotRail shows, grid activates)
lg:   1024px  // Desktops
xl:   1280px  // Large desktops
2xl:  1536px  // Extra large

// Layout behavior by breakpoint
Mobile (<md):
  - BotRail: hidden (shows as bottom drawer via MobileNav)
  - Main: col-span-12 (100% width)
  - Grid: Single column, vertical stacking
  - Timeline: 600px height maintained, responsive width

Tablet (md):
  - BotRail: col-span-3 (25%, shows sidebar)
  - Main: col-span-9 (75%)
  - Grid: 12-column activated
  - Timeline: 600px height, ~75% container width

Desktop (lg+):
  - Same as tablet
  - More horizontal space for chart readability
  - Timeline benefits from wider viewport
```

### **Component Spacing Pattern**

```typescript
// Vertical rhythm
space-y-4          // 16px vertical gap between major sections (Timeline, Positions)
mt-4               // 16px margin-top for tab content
pb-32              // 128px bottom padding for scroll-past readability

// Example: Monitor tab vertical spacing
<div className="space-y-4">
  <TVTimeline />     // 600px height
  {/* 16px gap */}
  <PositionsTable /> // Variable height
  {/* 128px bottom padding for scrolling past */}
</div>
```

### **Why pb-32 Bottom Padding?**

The 128px (`pb-32`) bottom padding on the main content area is intentional for **readability**:
- Allows users to scroll content past the viewport bottom
- Prevents PositionsTable from being cut off at screen edge
- Provides comfortable reading position for bottom content
- Mobile nav drawer (fixed position) doesn't overlap content

### **Mobile-Specific Behavior**

```typescript
// Mobile navigation drawer
<MobileNav className="md:hidden" />  // Only visible on mobile
- Fixed at bottom of viewport
- 70% width slide-in drawer for bot switching
- Touch gestures for closing (swipe right)
- Bottom tab triggers for opening

// Main content on mobile
- Full width (100%)
- Vertical stacking of all components
- Timeline maintains 600px height
- Responsive KPI grid (2 cols → 3 cols → 5 cols based on width)
```

---

## 🔐 Permission System & Monetization

### **Subscription Tier Architecture**
```typescript
// /lib/permissions.tsx - Complete permission context
interface PermissionContextType {
  userProfile: UserProfile | null
  loading: boolean
  canAccess: (feature: string) => boolean
  hasSubscription: (tier: 'usage_based' | 'pro') => boolean
  hasPaidDataPoint: (dataPoint: string) => boolean
}

// Permission gates in components
const { canAccess } = usePermissions()

// Premium LLM models
const isLocked = !canAccess('premium_llms')
<button disabled={isLocked} className={isLocked ? 'opacity-60 cursor-not-allowed' : ''}>
  {isLocked && <LockIcon />} OpenAI GPT-4
</button>

// ggShot signals
const canUseSignals = canAccess('ggshot')
<Toggle enabled={canUseSignals && isGgShotEnabled} />
```

### **Upgrade Flow (Stripe Integration)**
```typescript
// ActivationBar passes bot config to UpgradeModal for cost estimate
<UpgradeModal
  open={upgradeModalOpen}
  onOpenChange={setUpgradeModalOpen}
  botConfig={selectedBot}  // Bot-specific cost estimate
/>

// Modal shows:
// - Bot name ("Activate The Technician")
// - Value prop ("trade 24/7 while you sleep")
// - Cost estimate based on model + tier + frequency (~$X-Y/mo)
// - Trust bullets (pay only for AI decisions, no base fee, etc.)
// - Redirects to Stripe Checkout on confirm
```

### **Feature Gatekeeping**
All features available with usage-based subscription:
- **Unlimited Bots**: No bot count limits
- **Any Frequency**: 5-minute to weekly analysis
- **All 7 AI Models**: GPT, Claude, Grok, Gemini, DeepSeek, Kimi, Qwen
- **All Reasoning Tiers**: Economy/Standard/Premium
- **ggShot Signals**: Available with usage-based subscription
- **Telegram Publishing**: Available with usage-based subscription
- **Live Trading**: Symphony.io and AsterDEX integrations

### **Stripe Integration**
```typescript
// API methods in /lib/api.ts
apiClient.createCheckoutSession({ plan: 'usage' })
apiClient.createPortalSession() // For subscription management
```

**Usage-Based Pricing**: $0 base fee, pay per AI decision
- Budget: <$2/month (hourly checks, economy reasoning)
- Active: $10-35/month (15-30min frequency, standard reasoning)
- Power: $50-150/month (5-15min frequency, premium reasoning)

---

## 💰 Usage & Billing Display (2026-01-16)

### **UserProfile Dropdown**

Adaptive display based on billing model:

```typescript
// Credit pack users (credits > 0): Full breakdown
🪙 Credits    $50.00
   Used       -$12.34
   ─────────────────
   Balance    $37.66  // amber if < $5

// Metered users (credits = 0): Simple usage
🪙 This week  $12.34
```

**Implementation** (`UserProfile.tsx`):
```typescript
// Fetch usage summary on mount
const [usageSummary, setUsageSummary] = useState<{
  usage_usd: number
  credits_usd: number | null
  net_balance_usd: number | null
} | null>(null)

useEffect(() => {
  if (userProfile?.subscription_tier === 'usage_based') {
    const summary = await apiClient.getUsageSummary()
    setUsageSummary(summary)
  }
}, [userProfile?.subscription_tier])

// Adaptive display
{usageSummary.credits_usd > 0 ? (
  // Credit pack user - show full breakdown
) : (
  // Metered user - show just weekly usage
)}
```

### **ActivationBar Daily Cost**

Shows average daily LLM cost per bot:

```typescript
// Day 1 of month:
🪙 $0.89 today

// Day 2+:
🪙 ~$0.35/day  // period_usage / days_elapsed
```

**Implementation** (`ActivationBar.tsx`):
```typescript
// Fetch on mount + 5-minute refresh
useEffect(() => {
  const fetchConfigUsage = async () => {
    const usage = await apiClient.getConfigUsage(selectedBot.config_id)
    setConfigUsage(usage)
  }
  fetchConfigUsage()
  const interval = setInterval(fetchConfigUsage, 5 * 60 * 1000)
  return () => clearInterval(interval)
}, [selectedBot.config_id])

// Calculate average
const dayOfMonth = new Date().getDate()
const avgDaily = configUsage.period_usage_usd / dayOfMonth
```

### **API Methods** (`lib/api.ts`)

```typescript
// User-level usage summary (for UserProfile)
getUsageSummary(): Promise<{
  period: string           // "2026-01"
  usage_usd: number        // Total usage this period
  credits_usd: number | null  // Credit balance (null if metered)
  net_balance_usd: number | null  // credits - usage
  cached: boolean          // True if from 5-min cache
}>

// Per-bot usage (for ActivationBar)
getConfigUsage(configId: string): Promise<{
  config_id: string
  config_name: string
  period: string           // "2026-01"
  period_usage_usd: number // Total this month
  today_usage_usd: number  // Just today
}>
```

---

## 💻 Development & Deployment

### **Environment Setup**
```bash
# Development
cd /home/sev/ggbot/frontend
npm install
npm run dev          # http://localhost:3000

# Production Build
npm run build        # Test compilation
npm run lint         # Code quality check
```

### **Environment Variables**
```bash
# Supabase Authentication
NEXT_PUBLIC_SUPABASE_URL=https://ciinauxtnkweyebyhucl.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# V2 Backend API
NEXT_PUBLIC_V2_API_URL=https://ggbots-api.nightingale.business

# Domain Configuration
# ggbots.ai → Landing page
# app.ggbots.ai → Forge application
```

### **Deployment**
```bash
# Automatic deployment via Vercel + GitHub
git push origin main

# Vercel automatically deploys:
# - Frontend: https://ggbot-app.vercel.app
# - Production: https://app.ggbots.ai
```

---

## 🗂 Legacy Components (Archived)

### **Moved to Main Archive** (`/archive/`)
- **`frontend-dashboard/`** - WebSocket-based dashboard with Zustand complexity
- **`frontend-store/`** - Global botStore with 600+ lines and transformation layers
- **`frontend-landing-components/`** - Original landing page components

### **Unused Directories** (Consider for cleanup)
```
/components/
├── /ui/                     # Generic UI components (potentially useful)
├── /auth/                   # Authentication components (check if used)
├── /trades/                 # Trading-specific components (may overlap with Forge)
├── /charts/                 # Chart components (future integration)
└── /bot/                    # Bot-specific components (likely superseded by Forge)

/emails/                     # Email templates (keep for notifications)
/types/                      # TypeScript definitions (may have useful types)
/hooks/                      # Custom hooks (check for Forge overlap)
```

### **Cleanup Recommendations**
1. **Audit `/components/ui/`** - May contain reusable components for Forge
2. **Review `/components/auth/`** - Check if used by login/signup pages
3. **Evaluate `/components/trades/` and `/components/charts/`** - Potential future integration
4. **Check `/hooks/`** - May contain useful hooks not implemented in Forge
5. **Review `/types/`** - Consolidate with Forge type definitions

---

## 🎨 Design System

**Ceremonial Brutalism** - Inspired by trade37, creating a premium, sophisticated trading environment with unified brass accents.

### **Theme Architecture**
```typescript
// /lib/theme.tsx - Complete dark/light mode system
const [theme, setTheme] = useState<'light' | 'dark'>('dark')

// CSS Variables - Ceremonial Brutalism Palette
[data-theme="dark"] {
  --bg-primary: #0b0b0c;       /* obsidian - deep black */
  --bg-secondary: #141416;     /* carbon */
  --text-primary: #edebe7;     /* ivory - warm off-white */
  --accent: #c1a87d;           /* brass - primary accent */
  --border: #2a2a2d;           /* subtle borders */
}

[data-theme="light"] {
  --bg-primary: #f8f7f4;       /* warm parchment */
  --bg-secondary: #edebe7;     /* ivory background */
  --text-primary: #1a1816;     /* near-black with warmth */
  --accent: #8a7859;           /* dark brass accent */
  --border: #c8c4bc;           /* warm gray borders */
}
```

### **Typography** (2025-11-06 Update)
```typescript
// Premium editorial fonts
Display: Bodoni Moda serif      // Headlines, dramatic impact
Sans: Space Grotesk             // Body text, geometric clarity
Mono: IBM Plex Mono            // Technical data, code
```

### **Brass Pipeline System**
```css
:root {
  --agent-extraction: #d4bc91;  /* Light brass - extraction phase */
  --agent-decision: #c1a87d;    /* Medium brass - decision phase */
  --agent-trading: #a89168;     /* Dark brass - trading phase */
  --signal: #3ca6e0;            /* Signal blue */
  --ember: #d74a1f;             /* Ember red */
  --success: #10b981;           /* Profit/success (semantic) */
  --danger: #ef4444;            /* Loss/error (semantic) */
}
```

### **Icon System** (2025-11-06 Update)
All UI uses **Lucide React** icons (56 emojis replaced):
- Professional, scalable, stroke-based icons
- Tree-shakeable (only bundles used icons)
- Customizable size, color, stroke-width
- Brass accent coloring for active/selected states

**Example:**
```tsx
import { Bot, Settings, BarChart3 } from 'lucide-react'

<Bot className="h-5 w-5 text-[var(--accent)]" />
```

### **Design Philosophy**
- **Dark Mode:** "Obsidian and metal" - deep blacks with warm brass highlights
- **Light Mode:** "Parchment and stone" - aged paper warmth with rich dark brass
- **Unified Brand:** Consistent with trade37 championship platform
- **Premium Feel:** Editorial typography + ceremonial color palette

---

## 🚀 Production Features

### **Multi-Bot Management**
- **Unlimited Bots**: Create, duplicate, rename, delete trading agents
- **Bot Switching**: Seamless switching with isolated operational data
- **Real-time Status**: Live execution status with agent pipeline visualization
- **Account Isolation**: $10k paper trading accounts per bot configuration

### **Bot Profile Images** (2025-12-18)
- **Custom Avatars**: Upload bot profile images via drag-drop or click interface
- **Auto-Processing**: Images automatically resized to 1024×1024 with center-crop and aspect ratio preservation
- **Storage**: Supabase Storage bucket (`bot-avatars/{user_id}/{config_id}.jpg`) with RLS policies
- **Display**: 48px circular avatars with brass border in ActivationBar next to bot name
- **Upload UX**: Progress spinner during upload, hover-to-remove button, graceful fallback to Upload icon placeholder
- **Specs**: 5MB max file size, supports JPG/PNG/WebP, JPEG output at 90% quality
- **Integration**: `BotImageUpload` component with `profile_image_url` field on configurations table

### **Onboarding System** (2026-01-23)

#### **First-Time User Tour**
Tutorial overlay that highlights key features after first bot creation:

**Component**: `OnboardingTour.tsx`
```typescript
interface TourStep {
  target: string      // CSS selector (e.g., '[data-tour="activity-timeline"]')
  title: string       // Step heading
  content: string     // Explanation text
  onEnter?: () => void // Called when entering step (for navigation)
}
```

**Tour Steps** (5-step flow with auto-navigation):
| Step | Tab | Target | Title |
|------|-----|--------|-------|
| 1 | Monitor | Activity Timeline | "Your Bot's Activity" |
| 2 | Monitor | Configure Tab | "Customize Your Bot" |
| 3 | Configure | Strategy Advisor | "Strategy Advisor" |
| 4 | Configure | Config Tabs | "Manual Configuration" |
| 5 | Monitor | Activity Timeline | "You're All Set!" |

**Features**:
- Border highlight only (no darkening overlay) - brass border via CSS
- Pointer-events pass-through (clicks reach page, only tooltip captures)
- "Skip tutorial" link at bottom of each tooltip
- Keyboard navigation: ←/→ arrows, Escape to skip
- localStorage persistence (`ggbots-onboarding-complete`)
- Automatic scroll-into-view for each step
- `onEnter` callbacks enable tab switching between steps

**Trigger**: 1.5s after first bot creation completes:
```typescript
// In page.tsx handleCreateNewBot()
const isFirstBot = allBots.length === 0
if (isFirstBot) {
  setTimeout(() => setShowOnboardingTour(true), 1500)
}
```

**Data Attributes**: Target elements use `data-tour` for selection:
- `data-tour="activity-timeline"` - TVTimeline wrapper (Monitor tab)
- `data-tour="configure-tab"` - Configure tab button (TabNavigation)
- `data-tour="strategy-advisor"` - StrategyAdvisorPanel root (Configure tab)
- `data-tour="config-tabs"` - ConfigTabs wrapper (Configure tab)

#### **Strategy Advisor Buttons**
Post-creation context-aware buttons in `StrategyAdvisorPanel.tsx`:

| Button | Icon | When Shown | Action |
|--------|------|------------|--------|
| Explain Strategy | MessageCircle | Always | Sends prompt asking AI to explain current strategy |
| Update Strategy | Wand2 | Always | Sends prompt to modify strategy |
| Analyze Performance | BarChart3 | After trades | Fetches performance analysis report |

**Empty State Text**: Changes based on trade history:
- No trades: "What would you like to know about your bot?"
- Has trades: "How can I help you improve your bot?"

#### **Bot Creation Modal Improvements**
- **Better Placeholder**: Description field shows bullet-point examples
- **Visual Separator**: "or choose a proven strategy" divider between custom description and archetypes
- **Frequency Hint**: Explains what analysis frequency means

### **Configuration System** (Unified Batched Save - 2025-12-04)
- **Strategy Advisor**: Inline AI chat panel (500px fixed) with Claude Haiku, markdown rendering, real-time config updates
- **Unified Batched Save**: All config changes batched over 5s, single API call, dirty field tracking prevents SSE overwrites
- **Controlled Components**: StrategyEditor, TradeSettings, MarketDataSelector, SignalsConfiguration - all just call `onUpdate()`
- **SSE Conflict Resolution**: User wins for dirty fields, SSE updates non-dirty fields, clears after save
- **Market Data**: 21+ technical indicators with premium feature gating
- **Signal Sources**: ggShot integration with subscription gatekeeping
- **Strategy Editor**: AI prompt editing with LLM provider selection, thinking mode toggle
- **Trading Settings**: Symbol selection (141 pairs), position sizing, risk management, Telegram integration

### **Real-time Monitoring**
- **AI Consciousness Timeline**: Chart shows bot's subjective awareness - each point = moment AI observed account state (not objective reality)
- **Equity-Only Chart**: Activities-only (no snapshots), Redis-cached total equity, time spacing irrelevant (sequence of observations)
- **Trade Markers**: Green/red arrows (entries), green/red circles with P&L text (exits), brass/blue/gray circles (observations)
- **Live Status**: Pulsing colored dot showing current agent state with countdown timers ("⏸ WAITING • Next check in 2m 15s")
- **KPI Header**: Real-time Balance, P&L, Trades, Win Rate metrics integrated into timeline view
- **Bottom Sheet**: Framer Motion drawer (centered on desktop) with comprehensive activity details, preprocessed market data
- **Live Positions**: Real-time P&L updates with color-coded performance in positions table
- **Execution Pipeline**: Visual extraction → decision → trading status tracking in activation bar

### **Trading Settings Validation**
```typescript
// Real-time validation with error/warning states
import { useFieldValidation, ValidationRules } from '@/lib/useTradeValidation'
import { ValidationMessage } from '@/components/ValidationMessage'

const leverageValidation = useFieldValidation(leverage, ValidationRules.leverage)

<input
  value={leverage}
  className={leverageValidation.error ? 'border-red-500' : 'border-gray-300'}
/>
<ValidationMessage error={leverageValidation.error} warning={leverageValidation.warning} />
```

**Validated Fields**:
- **Leverage**: 1-100 (⚠️ warning if >20x)
- **Stop Loss**: 1-50%
- **Take Profit**: 1-500%
- **Position Size (%)**: 0.1-100% (⚠️ warning if >50%)
- **Position Size (USD)**: 10 - account balance
- **Max Positions**: 1-50 (⚠️ warning if >10)

**Validation Behavior**:
- 🔴 **Errors**: Red borders + error message + blocks save
- 🟡 **Warnings**: Yellow borders + warning message + allows save
- ✅ **Valid**: Normal borders + no message

---

## ✅ Production Readiness Checklist

### **Core Architecture**
- [x] Forge architecture with local state design
- [x] Multi-bot management with seamless switching
- [x] Real-time SSE data streams with proper filtering
- [x] Sandboxed configuration editing with change detection
- [x] Permission system with subscription tier gatekeeping

### **Authentication & Security**
- [x] Supabase authentication with email verification
- [x] Protected routes with server-side session guards
- [x] Permission-based feature access control
- [x] API client with JWT token authentication

### **User Experience**
- [x] Responsive design with mobile navigation
- [x] Dark/light theme system with localStorage persistence
- [x] Loading states, empty states, and error boundaries
- [x] Professional design system with agent color scheme
- [x] Trading settings validation with error/warning feedback
- [x] Real-time input validation preventing invalid configurations
- [x] First-time user onboarding tour with spotlight highlighting (2026-01-23)
- [x] Context-aware Strategy Advisor buttons (Explain/Update/Analyze)

### **Monetization & Subscriptions**
- [x] Stripe integration (checkout, webhooks, billing portal)
- [x] Usage-based pricing with transparent cost estimates
- [x] UpgradeModal with reasoning tier examples
- [x] Subscription status display in UserProfile
- [x] Permission gates triggering upgrade flow
- [x] Metered billing system (pay-per-decision)
- [x] Real-time usage display in UserProfile (credit pack & metered billing)
- [x] Per-bot daily cost in ActivationBar

### **Integration & Deployment**
- [x] V2 backend API integration with real-time data
- [x] Vercel deployment with custom domain routing
- [x] Environment variable configuration
- [x] Production build optimization

---

## 📊 CodeScout Analysis & Recommendations

### **✅ Production Status: GOOD**
**Overall Rating**: 🟢 Production-ready with clean Forge architecture

**Recent Fixes Applied:**
- ✅ **Unified Config Saving** (2025-12-04): Batched saves with 5s debounce, dirty field tracking, SSE conflict resolution - reduced 40+ API calls to 1
- ✅ **Activity Timeline Integration** (2025-11-08): Replaced DecisionFeed + PerformanceChart with full-width TVTimeline in Monitor tab
- ✅ **Critical routing fix**: Updated middleware to redirect `app.ggbots.ai` to `/forge` instead of non-existent `/dashboard`
- ✅ **Legacy API cleanup**: Removed duplicate API client, single authenticated client architecture
- ✅ **Complete component cleanup**: All unused legacy components archived to `/archive/frontend-*`
- ✅ **Symbol validation system**: 141 supported trading pairs with dropdown + search functionality
- ✅ **Help widget integration**: Floating community support with Telegram group access
- ✅ **UX improvements**: Symbol selection moved from locked exchange section to accessible location
- ✅ **Stripe subscription system**: Usage-based metered billing, checkout flow, webhooks, billing portal
- ✅ **Trading settings validation**: Real-time error/warning feedback for 6 critical trading parameters

### **🔴 Critical Issues (RESOLVED)**
- **Routing Architecture**: ✅ Fixed middleware redirecting to non-existent dashboard route
- **Duplicate API Clients**: ✅ Archived legacy client, clean single API architecture
- **Legacy References**: ✅ No WebSocket, botStore, or legacy component imports remain

### **🟡 Code Quality Improvements (Medium Priority)**

#### **Component Architecture**
- **Large Component Refactoring**: Break down 970-line ForgeApp component into smaller hooks:
  ```typescript
  hooks/
    ├── useAuth.ts           // Authentication state management
    ├── useBotManagement.ts  // Bot CRUD operations and switching
    ├── useConfigEditing.ts  // Sandboxed configuration editing
    └── useRealTimeData.ts   // SSE connection and data streaming
  ```

#### **React Hook Dependencies**
- **Fix useEffect warnings**: Add missing dependencies in `/app/forge/page.tsx:414`
- **Use useCallback**: For stable function references in effect dependencies
- **Dependency optimization**: Review all useEffect hooks for proper dependency arrays

#### **Code Cleanup**
- **Test page cleanup**: Remove commented code in `/app/test/page.tsx`
- **Unused imports**: Audit for any remaining unused import statements
- **Type safety**: Add more specific types for API responses and component props

### **🟢 Code Quality Improvements (Low Priority)**

#### **Error Handling & Resilience**
- **Error boundaries**: Add React error boundaries around major components
- **SSE reconnection**: Implement automatic reconnection logic for Server-Sent Events
- **API error handling**: Enhanced error handling with user-friendly messages

#### **Performance Optimizations**
- **Component memoization**: Add React.memo for expensive components
- **API response caching**: Implement intelligent caching for configuration data
- **Bundle optimization**: Code splitting for new-landing components

#### **Developer Experience**
- **Type definitions**: More specific TypeScript interfaces for complex data structures
- **Component documentation**: JSDoc comments for complex component props
- **Testing setup**: Unit tests for critical Forge components

### **🎯 Implementation Priorities**

#### **High Priority (Week 1)**
1. **Component refactoring** - Extract hooks from large ForgeApp component
2. **useEffect dependencies** - Fix React hook warnings
3. **Error boundaries** - Add resilience to component failures

#### **Medium Priority (Week 2-3)**
1. **SSE improvements** - Reconnection logic and error handling
2. **Type safety** - Enhanced TypeScript coverage
3. **Performance optimization** - Component memoization and caching

#### **Low Priority (Month 2)**
1. **Advanced charts** - TradingView integration for performance visualization
2. **Mobile UX polish** - Complete mobile drawer behavior for bot switching
3. **Analytics integration** - User behavior tracking and conversion optimization
4. **Notification system** - Email/SMS alerts for bot events and performance

### **🔒 Security & Compliance Status**
- ✅ **No hardcoded secrets** - All credentials use environment variables
- ✅ **Proper authentication** - Supabase session management implemented correctly
- ✅ **API security** - Bearer token authentication with JWT validation
- ✅ **Permission gates** - Subscription-based feature access control

---

## 📊 TradingView Activity Timeline

### **Overview**

Dual-mode equity chart using TradingView Lightweight Charts v4.2.0. Users can toggle between Activity Timeline (AI consciousness) and Performance Chart (objective tracking) with timeframe aggregation.

**Dual Chart Modes** (2025-12-17):
- **Activity Timeline**: Bot's subjective awareness - irregular intervals when AI acts (activities.total_equity from Redis cache)
- **Performance Chart**: Objective 5-minute tracking - regular snapshots regardless of activity (account_snapshots table)
  - **Timeframe Aggregation**: 5M (base), 1H, 4H, 1D views for higher-level performance analysis
  - **Smart Aggregation**: Uses LAST value in each period (most accurate for equity)

**Mode Toggle UI**: Brass-colored toggle buttons in header with conditional timeframe selector (performance mode only)

**Component Variants**:
- **Standalone**: `aster.ggbots.ai` → `/view/{config_id}` (full viewport, 100vh - 280px)
- **Embedded**: `/forge` Monitor tab (fixed 600px height, full width)

**Integration** (2025-11-08): Timeline replaced DecisionFeed + PerformanceChart in Forge Monitor tab, consolidating KPIs, equity chart, and activity history into single comprehensive view.

### **Architecture**

```typescript
/components/
├── tv-timeline.tsx          # Main timeline component (870 lines)
│                            # - variant prop: 'standalone' | 'embedded'
│                            # - Self-contained: own data fetching, polling
└── bottom-sheet.tsx         # Activity detail drawer (100 lines)

/app/view/[config_id]/       # Standalone route
└── page.tsx                 # <TVTimeline variant="standalone" />

/app/forge/page.tsx          # Embedded in Monitor tab
└── Monitor tab              # <TVTimeline variant="embedded" />
```

### **Key Features**

#### **1. TradingView Chart Integration**
- **Library**: TradingView Lightweight Charts v4.2.0 (NOT v5 - API breaking changes)
- **Chart Type**: Line series with brass color (#C1A87D), 2px stroke width
- **Data**: Activities-only (no snapshots), total equity from Redis cache (current_balance + margin_used + unrealized_pnl)
- **Y-Axis**: Formatted with `$` symbol, automatic scaling
- **X-Axis**: Activity timestamps (time spacing = sequence of AI observations, not clock time)
- **Interaction**: Crosshair mode with dashed brass lines

**Chart Configuration**:
```typescript
const chart = createChart(container, {
  layout: {
    background: { type: ColorType.Solid, color: '#1A1D23' }, // VIBE.carbon
    textColor: '#3a3a3c', // VIBE.hair
  },
  rightPriceScale: { borderColor: '#3a3a3c' },
  timeScale: { borderColor: '#3a3a3c', timeVisible: true, secondsVisible: false },
  localization: {
    priceFormatter: (price: number) => `$${price.toFixed(2)}`,
  },
  crosshair: {
    mode: 1, // Magnet to data points
    vertLine: { color: '#C9A962', width: 1, style: LineStyle.Dashed },
    horzLine: { color: '#C9A962', width: 1, style: LineStyle.Dashed },
  },
})

const lineSeries = chart.addLineSeries({
  color: '#C9A962', // VIBE.brass
  lineWidth: 2,
  priceLineVisible: false, // Hide dashed price line
})
```

#### **2. Activity Markers** (2025-11-20 Update)

**Trade Events** (arrows, above/below line - vertical movement):
- **Long Entry**: Green arrow up (▲, #16a34a, belowBar, size: 2)
- **Short Entry**: Red arrow down (▼, #dc2626, aboveBar, size: 2)
- **Exit (Profit)**: Green circle with P&L text (●, #16a34a, aboveBar, size: 1.5, text: "+$5.23")
- **Exit (Loss)**: Red circle with P&L text (●, #dc2626, belowBar, size: 1.5, text: "-$2.10")

**Observation Events** (circles, on the line - neutral position):
- **LLM Thought**: Brass circle (●, #C1A87D, inBar, size: 1)
- **Market Query**: Signal blue circle (●, #3CA6E0, inBar, size: 1)
- **Agent Wait**: Gray circle (●, #9ca3af, inBar, size: 1)

**Priority System**: When multiple activities occur at same timestamp, show single marker by priority:
1. Trade entries (long/short)
2. Trade exits
3. LLM thoughts
4. Market queries
5. Agent waits

**Critical Implementation Detail**: Markers must be sorted by time in ascending order or they disappear on zoom:
```typescript
markers.sort((a, b) => (a.time as number) - (b.time as number))
lineSeries.setMarkers(markers)
```

#### **3. Live Status Indicator**

Replaces static "ARENA STATUS • DATE" line with real-time agent status.

**Display Format**:
```
[Pulsing Dot] STATUS TEXT
```

**Status Types**:
- `⏸ WAITING • Next check in 2m 15s` (ivory dot) - countdown to next check
- `↑ LONG ENTERED • 3m ago` (green dot) - time since trade entry
- `↓ SHORT ENTERED • 1m ago` (red dot) - time since trade entry
- `📊 QUERIED MARKET • 5m ago` (blue dot) - time since query
- `💭 ANALYZING • 30s ago` (brass dot) - time since thought

**Implementation**:
```typescript
// Track latest activity
const [latestActivity, setLatestActivity] = useState<Activity | null>(null)
const [statusText, setStatusText] = useState<string>('')

// Update every second
useEffect(() => {
  if (!latestActivity) return

  const updateStatus = () => {
    const now = new Date()
    const activityTime = new Date(latestActivity.timestamp)

    // For agent_wait, show countdown
    if (latestActivity.type === 'agent_wait' && latestActivity.data.details?.next_check_at) {
      const nextCheck = new Date(String(details.next_check_at))
      const remainingMs = nextCheck.getTime() - now.getTime()
      const mins = Math.floor(remainingMs / 60000)
      const secs = Math.floor((remainingMs % 60000) / 1000)
      setStatusText(`⏸ WAITING • Next check in ${mins}m ${secs}s`)
    } else {
      // For others, show time ago
      const diffMs = now.getTime() - activityTime.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffSecs = Math.floor((diffMs % 60000) / 1000)
      const timeAgo = diffMins > 0 ? `${diffMins}m ago` : `${diffSecs}s ago`
      setStatusText(`${icon} ${label} • ${timeAgo}`)
    }
  }

  updateStatus()
  const interval = setInterval(updateStatus, 1000)
  return () => clearInterval(interval)
}, [latestActivity])
```

**CSS Animation**:
```css
@keyframes statusPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}
```

#### **4. Interactive Hover Tooltips**

**Crosshair Detection**: Using `subscribeCrosshairMove()` to detect when user hovers near markers:
```typescript
chart.subscribeCrosshairMove((param) => {
  if (!param.time || !param.point) {
    setSelectedActivity(null)
    return
  }

  const timestamp = typeof param.time === 'number' ? param.time : parseFloat(param.time as string)
  const activities = activitiesMapRef.current.get(timestamp)

  if (activities && activities.length > 0) {
    setSelectedActivity(activities[0]) // Show first activity for tooltip
    setCrosshairPosition({ x: param.point.x, y: param.point.y })
  }
})
```

**Tooltip Content** (positioned at crosshair):
- Activity type badge with color
- Summary text (truncated to 100 chars for market queries)
- Symbol if available
- Markdown rendering for analysis/thoughts

#### **5. Bottom Sheet Detail View**

**Trigger**: Click on any marker opens bottom sheet with full details.

**Implementation**: Framer Motion slide-up drawer
```typescript
<BottomSheet
  isOpen={detailActivities.length > 0}
  onClose={() => setDetailActivities([])}
  title={detailActivities.length === 1 ? 'Activity Type' : `${detailActivities.length} Activities`}
>
  {/* Scrollable content with type-specific rendering */}
</BottomSheet>
```

**Features**:
- Drag handle at top (swipe down to dismiss on mobile)
- Max height: 80vh with overflow scroll
- Multiple activities shown as list when grouped
- Type-specific field rendering:
  - **Trade entries**: Symbol, side, entry price, leverage, confidence, SL/TP
  - **Market queries**: Timeframe, categories list, **preprocessed market data**
  - **Agent thoughts**: Markdown-rendered thought content
  - **Agent waits**: Wait duration, next check time, reason

**Market Data Display** (NEW - 2025-11-07):

Market queries now display the actual preprocessed data that agents receive:

```typescript
// Technical Indicators (brass boxes)
{details.market_data.technicals?.indicators &&
  Object.entries(indicators).map(([name, data]) => (
    <div className="p-3 rounded-lg bg-brass-10">
      <div className="font-semibold">{name}</div>
      <div>Value: {data.current.value}</div>
      <div>Trend: {data.context.trend.direction} ({data.context.trend.strength * 100}%)</div>
      <div>Patterns: {Object.keys(data.patterns).map(p => <Badge>{p}</Badge>)}</div>
    </div>
  ))
}

// Market Intelligence (blue boxes)
{details.market_data.market_intelligence &&
  Object.entries(intelligence).map(([source, data]) => (
    <div className="p-3 rounded-lg bg-signal-10">
      <div className="font-semibold">{source.toUpperCase()}</div>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  ))
}
```

This shows the **200-500 analytical fields** (trend strength, divergence patterns, momentum velocity, etc.) that influence agent decisions.

#### **6. Data Fetching & Management** (2025-12-17 Update)

**API Endpoints** (Dual-Mode Architecture):
```typescript
// ACTIVITY MODE: AI consciousness timeline (activities-only, Redis-cached equity)
// Returns activities with total_equity from Redis cache (updated every 5s by account monitor)
// Irregular intervals - pure activity stream representing AI's awareness moments
GET /api/v2/snapshots/{config_id}/balance-series

// PERFORMANCE MODE: Objective performance tracking (account_snapshots, regular 5-min intervals)
// Returns snapshots with total_equity calculated from current_balance + unrealized_pnl
// Regular 5-minute intervals regardless of bot activity
GET /api/v2/snapshots/{config_id}/performance-series

// All activities (trades, queries, thoughts, waits) - ACTIVITY MODE ONLY
// Used for markers, hover tooltips, and click details
GET /api/v2/activities/{config_id}

// Bot metadata (name, balance, win rate, performance) - BOTH MODES
// Paper: Calculated from paper_trades (per-bot)
// Symphony: Queries Symphony API get_account_metrics() (account-wide)
// Aster: Queries Aster API balance + trades (account-wide)
GET /api/v2/activities/{config_id}/metadata
```

**Conditional Fetching** (2025-12-17):
```typescript
// Choose endpoint based on chart mode
const seriesEndpoint = chartMode === 'activity'
  ? `/api/v2/snapshots/${configId}/balance-series`   // activities.total_equity
  : `/api/v2/snapshots/${configId}/performance-series` // account_snapshots

// Activity mode: Fetch activities for markers
// Performance mode: Skip activities fetch (no markers needed)
const fetchPromises = [
  fetch(seriesEndpoint),
  fetch(`/api/v2/activities/${configId}/metadata`),
]
if (chartMode === 'activity') {
  fetchPromises.push(fetch(`/api/v2/activities/${configId}`))
}

// Apply timeframe aggregation for performance mode
if (chartMode === 'performance' && timeframe !== '5m') {
  balancePoints = aggregateToTimeframe(balancePoints, timeframe)
}
```

**Redis Equity Caching Architecture** (2025-11-20):
```
Account Monitor (every 5s):
  → Calculate total_equity (current_balance + margin_used + unrealized_pnl)
  → Cache in Redis: equity:{config_id} (TTL: 30s)

Activity Logger (on every activity):
  → Read from Redis cache (tier 1)
  → Fallback to database snapshots (tier 2)
  → Fallback to account table query (tier 3)
  → Store total_equity in activities.account_balance

Chart API:
  → Query activities table only
  → Each activity has total_equity from moment it was logged
  → Chart displays AI's discrete observations (not continuous snapshots)
```

**Multi-Mode Architecture** (2025-11-13):
All three trading modes (paper, Symphony, Aster) fully supported with smart backend routing:
- **Paper Trading**: Per-bot isolated metrics from `paper_trades` table
- **Symphony Live**: Account-wide metrics from Symphony API (shared wallet design)
- **AsterDEX Live**: Account-wide metrics from Aster API (shared wallet design)

**Data Transformation**:
1. Fetch balance series (P&L snapshots)
2. Fetch all activities (500+ items)
3. Sort activities chronologically
4. Merge with carry-forward P&L:
   ```typescript
   const chartPoints = []
   let currentPnl = 0.0

   for (const activity of sortedActivities) {
     // Update P&L if this activity has a balance point
     if (balanceMap.has(activity.timestamp)) {
       currentPnl = balanceMap.get(activity.timestamp)
     }

     chartPoints.push({
       time: timestamp,
       value: currentPnl, // Carry forward P&L
     })
   }
   ```

**Activity Grouping** (by timestamp):
```typescript
const activitiesMapRef = useRef<Map<number, Activity[]>>(new Map())

// Group activities by timestamp
const groupedByTimestamp = new Map<number, Activity[]>()
activities.forEach(activity => {
  const timestamp = Math.floor(new Date(activity.timestamp).getTime() / 1000)
  if (!groupedByTimestamp.has(timestamp)) {
    groupedByTimestamp.set(timestamp, [])
  }
  groupedByTimestamp.get(timestamp).push(activity)
})

// Create one marker per timestamp
groupedByTimestamp.forEach((activitiesAtTime, timestamp) => {
  // Priority: trades > thoughts > queries > waits
  const hasTradeLong = activitiesAtTime.some(a => a.type === 'trade_entry_long')
  if (hasTradeLong) {
    markers.push({ time: timestamp, shape: 'arrowUp', color: '#16a34a', size: 2 })
  }
  // ... etc
})
```

### **Integration with Backend**

#### **Enhanced Activity Logging** (2025-11-07)

Market query activities now capture the full preprocessed data:

**Backend** (`agent/mcp_server.py:220-234`):
```python
# Extract market data for activity logging
market_data = {}
if result.get('data', {}).get('technicals'):
    market_data['technicals'] = result['data']['technicals']
if result.get('data', {}).get('market_intelligence'):
    market_data['market_intelligence'] = result['data']['market_intelligence']

log_activity_safe(
    config_id=agent_context.config_id,
    user_id=agent_context.user_id,
    activity_type='market_query',
    details={
        'symbol': symbol,
        'categories': categories,
        'timeframe': timeframe,
        'market_data': market_data  # NEW: Full preprocessed data (200-500 fields)
    },
    related_symbol=symbol,
)
```

This enables complete transparency into agent decision-making by showing the exact data that influenced each trade.

### **Performance Considerations**

1. **Chart Initialization**: Heavy operation, only run once in useEffect
2. **Marker Updates**: Batch updates instead of individual calls
3. **Activity Grouping**: Pre-compute timestamp → activities map
4. **Memory**: Store only necessary data in refs, avoid duplicating chart data
5. **Rendering**: Use React.memo for BottomSheet to prevent unnecessary re-renders

### **Common Issues & Solutions**

**Issue**: Markers disappear when zooming in
**Solution**: Markers must be sorted by time in ascending order before calling `setMarkers()`

**Issue**: TypeScript errors with conditional rendering
**Solution**: Use ternary operators `? :` instead of `&&` for JSX conditionals to avoid `unknown` type

**Issue**: Chart doesn't resize on window change
**Solution**: Use ResizeObserver to detect container size changes and call `chart.applyOptions({ width, height })`

**Issue**: Bottom sheet not scrollable
**Solution**: Set `overflow-y-auto` on content div with max-height constraint

### **Future Enhancements**

- **Zoom to activity**: Double-click marker to zoom timeline to that time range
- **Filter by type**: Toggle visibility of different activity markers
- **Export data**: Download P&L chart as CSV or PNG
- **Annotations**: Add manual notes/markers to timeline
- **Comparison mode**: Overlay multiple bot timelines for performance comparison

---

**The Forge architecture represents a complete, production-ready autonomous trading platform with elegant local state management, comprehensive real-time features, and sophisticated permission-based monetization capabilities.** 🚀