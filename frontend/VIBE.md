# ggbots Frontend Design System - Ceremonial Brutalism

**Last Updated:** 2025-11-06 (Rebrand Complete)

## Core Design Philosophy

**Ceremonial Brutalism** - A premium, sophisticated interface inspired by trade37 that merges the precision of brutalist design with the warmth of ceremonial brass accents. Think prestigious financial institutions meets modern trading terminal - elegant, authoritative, and technical.

**Design Principles:**
- Border-based architecture over shadows
- Unified brass accent system
- Professional Lucide icons throughout
- Premium editorial typography
- Dual theme support (dark/light)

---

## Color Palette

### Ceremonial Dark Mode: "Obsidian and Metal"
Deep blacks with warm brass highlights, creating a premium nighttime trading environment.

```css
[data-theme="dark"] {
  /* Backgrounds */
  --bg-primary: #0b0b0c;       /* obsidian - deepest black */
  --bg-secondary: #141416;     /* carbon - secondary surfaces */
  --bg-tertiary: #1a1a1c;      /* darker variations */

  /* Text */
  --text-primary: #edebe7;     /* ivory - warm off-white */
  --text-secondary: #d6d3ce;   /* muted ivory */
  --text-muted: #8a8781;       /* warm gray */

  /* Borders */
  --border: #2a2a2d;           /* subtle borders */
  --border-hover: #3a3a3d;     /* hover states */

  /* Accent - Brass */
  --accent: #c1a87d;           /* brass - primary accent */
  --accent-hover: #d4bc91;     /* lighter brass for hover */

  /* Status Colors */
  --signal: #3ca6e0;           /* signal blue */
  --ember: #d74a1f;            /* ember red */
}
```

### Ceremonial Light Mode: "Parchment and Stone"
Aged paper warmth with rich dark brass accents, evoking historical financial documents.

```css
[data-theme="light"] {
  /* Backgrounds */
  --bg-primary: #f8f7f4;       /* warm parchment */
  --bg-secondary: #edebe7;     /* ivory surfaces */
  --bg-tertiary: #e6e3de;      /* cream variations */

  /* Text */
  --text-primary: #1a1816;     /* near-black with warmth */
  --text-secondary: #3a3734;   /* medium brown-gray */
  --text-muted: #6b6661;       /* lighter brown */

  /* Borders */
  --border: #c8c4bc;           /* warm gray borders */
  --border-hover: #b5aea5;     /* darker hover */

  /* Accent - Dark Brass */
  --accent: #8a7859;           /* dark brass accent */
  --accent-hover: #9d8b6a;     /* lighter brass hover */

  /* Status Colors */
  --signal: #3ca6e0;           /* signal blue (same) */
  --ember: #d74a1f;            /* ember red (same) */
}
```

### Brass Pipeline System
The three-phase trading pipeline uses brass variants instead of multi-color agents:

```css
:root {
  /* Agent Pipeline - Brass Variants */
  --agent-extraction: #d4bc91;  /* Light brass - market data extraction */
  --agent-decision: #c1a87d;    /* Medium brass - AI decision making */
  --agent-trading: #a89168;     /* Dark brass - trade execution */

  /* Semantic Status Colors (Trading-specific) */
  --profit-color: #10b981;      /* green - profit, wins, long positions */
  --loss-color: #ef4444;        /* red - loss, losses, short positions */
  --neutral-color: #8a8781;     /* gray - neutral, no change */
}
```

**Usage:**
- Brass variants show the progression from data → decision → execution
- Keep profit/loss colors semantic (green/red) for trading clarity
- Use brass for all accent colors, highlights, CTAs, and active states

---

## Typography System

### Font Stack (Premium Editorial)
Replaced utilitarian fonts with sophisticated editorial typefaces:

```typescript
// Font Imports (app/layout.tsx)
import { Bodoni_Moda, Space_Grotesk, IBM_Plex_Mono } from 'next/font/google'

const bodoniModa = Bodoni_Moda({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
})

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-mono',
  display: 'swap',
})
```

### Typography Usage
- **Display (Headlines):** Bodoni Moda - Elegant serif for section titles, headlines, dramatic impact
- **Sans (Body):** Space Grotesk - Geometric sans for body text, navigation, clarity
- **Mono (Technical):** IBM Plex Mono - Monospace for code, data, technical precision

### Font Scale (Tailwind Classes)
- **Headers:** `text-lg`, `text-xl`, `text-2xl` with `font-display`
- **Body:** `text-sm`, `text-base` with `font-sans`
- **Small:** `text-xs`, `text-[10px]` for meta information
- **Mono:** `font-mono` for numeric data, timestamps, technical details

**Font Weights:**
- `font-semibold` (600) - Headlines, emphasized text
- `font-medium` (500) - Subheaders, labels
- `font-normal` (400) - Body text, descriptions

---

## Icon System

### Lucide React Integration
All 56 emojis replaced with professional Lucide icons (v0.513.0):

**Installation:**
```bash
npm install lucide-react
```

**Usage:**
```tsx
import { Bot, Settings, BarChart3, Clock, CheckSquare } from 'lucide-react'

// Standard icon with brass accent
<Bot className="h-5 w-5 text-[var(--accent)]" />

// Size variants
<Icon className="h-3.5 w-3.5" />  // Small (menu items)
<Icon className="h-4 w-4" />      // Standard (tabs, controls)
<Icon className="h-5 w-5" />      // Medium (headers)
<Icon className="h-16 w-16" />    // Large (empty states)

// With hover effect
<Icon className="h-4 w-4 text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors" />
```

### Common Icon Mappings
```tsx
// Bot Types
Clock        // Scheduled Trading (⏰ replaced)
CheckSquare  // Signal Validation (✓ replaced)
Bot          // Agent (🤖 replaced)

// Navigation & UI
BarChart3    // Market Data (📊 replaced)
Brain        // Strategy (🧠 replaced)
Settings     // Settings (⚙️ replaced)
Radio        // Signals (📡 replaced)

// Actions
Edit2        // Rename (✏️ replaced)
Copy         // Duplicate (📋 replaced)
Zap          // Deploy/Action (⚡ replaced)
RefreshCw    // Reset (🔄 replaced)
Check        // Confirm (✓ replaced)
Trash2       // Delete (🗑️ replaced)

// Status
Circle       // Active/Inactive indicator (●/○ replaced)
Loader2      // Loading state (⟳ replaced)
MoreHorizontal // Menu (⋯ replaced)

// Communication
MessageSquare // Chat (💬 replaced)
FileText      // Documents (📋 replaced)
```

**Benefits:**
- ✅ Scalable vector graphics (no pixelation)
- ✅ Tree-shakeable (optimized bundle size)
- ✅ Customizable (size, color, stroke-width)
- ✅ Consistent geometric style
- ✅ Better accessibility

---

## Layout System

### Grid Structure
```css
/* Forge App Layout */
.forge-container {
  display: grid;
  grid-template-columns: 280px 1fr;  /* Sidebar | Main content */
  gap: 24px;
}

/* Responsive breakpoints */
@media (max-width: 768px) {
  .forge-container {
    grid-template-columns: 1fr;  /* Stack on mobile */
  }
}
```

### Spacing Standards
```css
/* Component spacing */
--spacing-xs: 8px;     /* gap-2, p-2 */
--spacing-sm: 12px;    /* gap-3, p-3 */
--spacing-md: 16px;    /* gap-4, p-4 */
--spacing-lg: 24px;    /* gap-6, p-6 */
--spacing-xl: 32px;    /* gap-8, p-8 */

/* Border radius */
--radius-sm: 8px;      /* rounded-lg */
--radius-md: 12px;     /* rounded-xl */
--radius-lg: 16px;     /* rounded-2xl */
```

---

## Component Design Patterns

### 1. Border-Based Cards (Replacing Neumorphism)
Ceremonial brutalism uses clean borders instead of shadows:

```tsx
<div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
  {/* Card content */}
</div>
```

**Hover States:**
```tsx
<button className="border border-[var(--border)] hover:border-[var(--border-hover)] transition-colors">
  {/* Button content */}
</button>
```

### 2. Brass Accent Buttons
Primary action buttons use brass with obsidian text for contrast:

```tsx
// Primary action (brass)
<button className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-obsidian font-medium px-4 py-2 rounded-lg transition-colors">
  Activate
</button>

// Danger action (red)
<button className="bg-rose-600 hover:bg-rose-700 text-white px-4 py-2 rounded-lg">
  Stop
</button>

// Secondary action (border only)
<button className="border border-[var(--border)] hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] px-4 py-2 rounded-lg">
  Cancel
</button>
```

### 3. Glass Morphism Effects
Subtle backdrop blur for overlays:

```tsx
<div className="bg-[var(--bg-secondary)]/80 backdrop-blur-sm border border-[var(--border)]">
  {/* Header or overlay content */}
</div>
```

### 4. Active State Indicators
Brass-colored status dots and highlights:

```tsx
// Active bot indicator
<Circle className={`h-3 w-3 ${isActive ? 'text-[var(--accent)] fill-[var(--accent)]' : 'text-[var(--text-muted)]'}`} />

// Tab active state
<button className={`${isActive ? 'border-[var(--accent)] text-[var(--accent)]' : 'border-transparent text-[var(--text-muted)]'}`}>
  {/* Tab content */}
</button>
```

### 5. Form Controls
Clean, minimal inputs with brass focus states:

```tsx
<input
  type="text"
  className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-colors"
/>
```

### 6. Data Display Components

**Trade Tables with Semantic Colors:**
```tsx
<div className="rounded-xl border border-[var(--border)] overflow-hidden">
  <table>
    <tr>
      <td className={pnl > 0 ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}>
        {pnl > 0 ? '+' : ''}{pnl.toFixed(2)}%
      </td>
    </tr>
  </table>
</div>
```

**Status Badges:**
```tsx
// Success (brass)
<span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-[var(--accent)]/20 text-[var(--accent)] text-xs">
  <Check className="h-3 w-3" />
  Active
</span>

// Profit (green - semantic)
<span className="text-[var(--profit-color)]">
  +$234.56
</span>

// Loss (red - semantic)
<span className="text-[var(--loss-color)]">
  -$89.23
</span>
```

---

## Animation Standards

### Micro-Interactions
```css
/* Standard transitions */
transition: all 0.2s ease;

/* Hover effects */
&:hover {
  transform: scale(1.02);
  transition-duration: 0.15s;
}

/* Loading spinners */
.spinner {
  animation: spin 1s linear infinite;
}
```

### Lucide Icon Animations
```tsx
// Spinning loader
<Loader2 className="h-4 w-4 animate-spin" />

// Pulse effect
<Circle className="h-3 w-3 animate-pulse" />
```

---

## Visual Hierarchy Rules

### 1. Color Usage Priority
1. **Brass accent** - Primary actions, active states, highlights
2. **Semantic colors** - Profit/loss data (green/red), status indicators
3. **Text hierarchy** - Primary/secondary/muted text colors
4. **Borders** - Subtle definition without shadows

### 2. Element Classification

**Interactive Elements:**
- Use brass accent for active/hover states
- Apply smooth transitions
- Include Lucide icons for clarity
- Examples: Buttons, tabs, toggles

**Display Elements:**
- Use border-based styling
- Minimal effects, focus on content
- Examples: Cards, tables, data displays

### 3. Spacing Consistency
- **32px gaps** between major sections
- **24px gaps** between related components
- **16px gaps** within component groups
- **8-12px gaps** for fine adjustments

---

## Responsive Design

### Breakpoint Strategy
```css
/* Mobile-first approach */
sm: 640px   /* Small devices */
md: 768px   /* Medium devices */
lg: 1024px  /* Large screens */
xl: 1280px  /* Extra large */
```

### Mobile Adaptations
- **Hide sidebar** on small screens, show via drawer
- **Stack layouts** vertically
- **Maintain brass accents** for consistency
- **Preserve icon clarity** at all sizes

---

## Migration from Old System

### Deprecated Elements (2025-11-06)
❌ **Old Agent Colors:** Blue (#38a1c7), Green (#2cbe77), Orange (#be6a47)
❌ **Old Fonts:** Inter, Kanit
❌ **Emojis:** All 56 replaced with Lucide icons
❌ **Neumorphic shadows:** Replaced with border-based design
❌ **Multi-color system:** Unified to brass accent

### Current Standards (2025-11-06)
✅ **Brass variants:** Light/Medium/Dark brass for pipeline
✅ **Premium fonts:** Bodoni Moda, Space Grotesk, IBM Plex Mono
✅ **Lucide icons:** Professional, scalable, consistent
✅ **Border-based design:** Clean, brutalist aesthetic
✅ **Ceremonial palette:** Obsidian/ivory/brass

---

## Best Practices

### Do's ✅
- Use CSS variables for all colors
- Apply brass accent for primary actions
- Use Lucide icons consistently
- Maintain border-based design
- Keep profit/loss colors semantic (green/red)
- Use premium typography hierarchy
- Apply smooth transitions (0.2s ease)

### Don'ts ❌
- Don't use hardcoded color values
- Don't mix emojis with Lucide icons
- Don't use emerald/blue/orange for accents
- Don't add heavy shadows (use borders)
- Don't use Comic Sans (obviously)

---

## Related Documentation
- **Complete Rebrand Details:** `/DOCS/completed/REBRAND.md`
- **Frontend README:** `/frontend/README.md`
- **trade37 Design Reference:** `/home/sev/trade37/CLAUDE.md`
- **Main Changelog:** `/CHANGELOG.md`

---

This design system creates a cohesive, premium interface that conveys the prestigious nature of autonomous AI trading while maintaining excellent usability and professional appeal across all device sizes.
