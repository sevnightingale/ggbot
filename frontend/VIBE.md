# GGBot Frontend Design System & Visual Standards

## Core Design Philosophy

**Brutalist Command Center Aesthetic** - A sophisticated, industrial interface that conveys precision, control, and advanced technical capabilities. Think mission control meets high-end trading terminal.

## Color Palette

### Primary Colors
- **Charcoal-900** (`#161618`) - Primary background, deepest dark
- **Charcoal-800** (`#1f1f23`) - Secondary backgrounds, cards
- **Charcoal-700** (`#2a2a30`) - Borders, dividers
- **Charcoal-600** (`#36363d`) - Interactive element borders

### Text Colors
- **Bone-200** (`#e3e5e6`) - Primary text, headers
- **Bone-100** (`#f0f2f3`) - Emphasized text, hover states
- **Bone-300** (`#d6d8da`) - Secondary text
- **Gray-400/500** (`#9ca3af`, `#6b7280`) - Muted text, placeholders
- **Gray-600** (`#4b5563`) - Disabled text

### Agent Colors (Status & Accents)
- **Agent-Extraction** (`#38a1c7`) - Blue, data extraction
- **Agent-Decision** (`#2cbe77`) - Green, AI decision making  
- **Agent-Trading** (`#be6a47`) - Orange, trade execution

### Status Colors
- **Green-400** (`#10b981`) - Profit, success, active
- **Red-400** (`#ef4444`) - Loss, error, inactive
- **Orange-400** (`#f97316`) - Warning, pending
- **Yellow-400** (`#eab308`) - Caution, neutral

## Typography Scale

### Font Sizes (Tailwind Classes)
- **Headers**: `text-subheader` - Section titles, bot names
- **Body**: `text-footnote` - Primary text, descriptions
- **Small**: `text-xs` - Meta info, labels, secondary text
- **Tiny**: `text-[10px]` - Timestamps, fine details

### Font Weights
- **Medium** (`font-medium`) - Headers, emphasized text
- **Normal** (`font-normal`) - Body text, descriptions

## Layout System

### Grid Structure
```css
/* 3-Column Dashboard Layout */
grid-cols-[1fr_400px_1fr]  /* Left data | Center bot | Right data */

/* Responsive Breakpoints */
hidden lg:block  /* Hide on mobile, show on large screens */
max-w-[1680px]   /* Maximum container width */
```

### Spacing Standards
- **Component Padding**: `p-3` (12px), `p-6` (24px), `p-8` (32px)
- **Section Gaps**: `gap-6` (24px), `gap-8` (32px)
- **Element Margins**: `mb-4` (16px), `mb-6` (24px), `mb-8` (32px)

## Component Design Patterns

### 1. Neumorphic Interactive Elements

**GGBot Circle** - Central bot selector with depth and dimensionality:
```css
.ggbot-circle {
  /* Dual-shadow neumorphic effect */
  box-shadow: 
    8px 8px 16px rgba(0, 0, 0, 0.9),      /* Dark shadow (bottom-right) */
    -8px -8px 16px rgba(255, 255, 255, 0.08); /* Light shadow (top-left) */
  
  /* 4-quadrant gradient borders */
  background: radial-gradient(circle at 30% 30%, rgba(227, 229, 230, 0.15), transparent 50%);
}
```

**Floating Action Buttons** - Circular controls with hover states:
```css
.floating-action-btn {
  /* Matching neumorphic shadows */
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.9),
    -4px -4px 8px rgba(255, 255, 255, 0.08);
  
  /* Agent-specific hover colors */
  &:hover { background-color: rgba(56, 161, 199, 0.1); } /* extraction blue */
}
```

### 2. Sharp Geometric Containers

**Dashboard Cards** - Angular containers with corner brackets:
```css
.corner-top-left {
  position: relative;
  background: #1f1f23; /* charcoal-800 */
}

.corner-top-left::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 70%; height: 70%;
  background: 
    linear-gradient(to right, #e3e5e6 0%, #e3e5e6 30%, transparent 100%) top/100% 2px no-repeat,
    linear-gradient(to bottom, #e3e5e6 0%, #e3e5e6 30%, transparent 100%) left/2px 100% no-repeat;
}
```

**Sharp Dividers** - Gradient separators:
```css
.gradient-divider {
  height: 1px;
  background: linear-gradient(to right, transparent 0%, #e3e5e6 20%, #e3e5e6 80%, transparent 100%);
  opacity: 0.6;
}
```

### 3. Accordion/Collapsible Sections

**Agent Configuration Panels** - Expandable sections with neumorphic styling:
```css
.ggbot-accordion-btn {
  /* Interactive neumorphic styling */
  box-shadow: 
    8px 8px 16px rgba(0, 0, 0, 0.9),
    -8px -8px 16px rgba(255, 255, 255, 0.08);
  
  /* Corner bracket system for visual hierarchy */
  &::before { /* Top-left corner bracket */ }
  &::after  { /* Bottom-right corner bracket */ }
}

.ggbot-accordion-expanded {
  /* Flat styling for expanded content */
  background: #161618; /* charcoal-900 */
  border: 1px solid #36363d; /* charcoal-600 */
}
```

### 4. Form Controls & Inputs

**Search/Input Fields**:
```css
input[type="text"] {
  background: #1f1f23;      /* charcoal-800 */
  border: 1px solid #36363d; /* charcoal-600 */
  color: #e3e5e6;           /* bone-200 */
  
  &:focus {
    border-color: #38a1c7;   /* agent-extraction */
    transition: border-color 0.2s;
  }
}
```

**Checkbox/Selection Controls**:
```css
.selection-checkbox {
  width: 16px; height: 16px;
  border: 2px solid #6b7280;  /* gray-600 */
  border-radius: 2px;
  
  &.selected {
    background: #38a1c7;      /* agent-extraction */
    border-color: #38a1c7;
  }
}
```

### 5. Data Display Components

**Trade Tables**:
```css
.trade-table {
  /* Alternating row backgrounds */
  tr:nth-child(even) {
    background: rgba(128, 128, 128, 0.3);
  }
  
  /* Color-coded data */
  .profit { color: #10b981; }  /* green-400 */
  .loss   { color: #ef4444; }  /* red-400 */
  .neutral { color: #e3e5e6; } /* bone-200 */
}
```

**Status Indicators**:
```css
.status-indicator {
  /* Colored dots with glow effect */
  &.active   { color: #10b981; text-shadow: 0 0 4px rgba(16, 185, 129, 0.5); }
  &.warning  { color: #f97316; text-shadow: 0 0 4px rgba(249, 115, 22, 0.5); }
  &.error    { color: #ef4444; text-shadow: 0 0 4px rgba(239, 68, 68, 0.5); }
  &.inactive { color: #6b7280; }
}
```

## Animation Standards

### Micro-Interactions
```css
/* Standard transition timing */
transition: all 0.2s ease;

/* Hover states */
&:hover {
  transform: translateY(-1px);
  transition-duration: 0.15s;
}

/* Loading spinners */
.spinner {
  animation: spin 1s linear infinite;
}
```

### Modal/Sheet Transitions
```css
/* Bottom sheet slide animation */
.sheet-enter {
  transform: translateY(100%);
  transition: transform 500ms ease-out;
}

.sheet-enter-active {
  transform: translateY(0);
}
```

## Visual Hierarchy Rules

### 1. Element Classification

**Interactive Elements** (clickable):
- Use neumorphic styling with dual shadows
- Apply hover effects and transitions
- Examples: GGBot circle, floating buttons, accordions

**Display Elements** (informational):
- Use corner bracket styling
- Minimal shadows, focus on content
- Examples: Dashboard cards, data tables

### 2. Color Usage Priority

1. **Agent colors** for primary actions and status
2. **Status colors** for data states (profit/loss, active/inactive)
3. **Bone colors** for text hierarchy
4. **Gray colors** for secondary information

### 3. Spacing Consistency

- **Large gaps** (32px) between major sections
- **Medium gaps** (24px) between related components  
- **Small gaps** (16px) within component groups
- **Micro gaps** (8px, 12px) for fine adjustments

## Component Relationships

### Layout Nesting Patterns
```
Dashboard Container (charcoal-900)
├── Section Cards (charcoal-800 + corner brackets)
│   ├── Headers (bone-200, text-subheader)
│   ├── Dividers (gradient-divider)
│   └── Content (text-footnote, bone-200)
└── Interactive Overlays (neumorphic styling)
    ├── GGBot Circle (central focal point)
    ├── Floating Buttons (contextual actions)
    └── Modal Sheets (configuration panels)
```

### State Communication
- **Visual feedback** through color changes
- **Depth changes** via shadow intensity
- **Border highlights** for focus states
- **Subtle animations** for state transitions

## Responsive Design

### Breakpoint Strategy
- **Mobile-first** approach with progressive enhancement
- **Hide complex elements** on small screens (`hidden lg:block`)
- **Maintain core functionality** across all device sizes
- **Preserve visual hierarchy** at different scales

### Content Prioritization
1. **Central bot display** always visible
2. **Critical controls** accessible on mobile
3. **Data tables** become scrollable
4. **Secondary information** hidden on small screens

This design system creates a cohesive, professional interface that conveys the sophisticated nature of AI-powered trading while maintaining excellent usability and visual appeal.