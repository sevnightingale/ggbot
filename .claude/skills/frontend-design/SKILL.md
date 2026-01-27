# Frontend Design Skill

**Source**: [Anthropic Claude Code Frontend Design Skill](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md)

Creates distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Generates creative, polished, working code with exceptional attention to aesthetic details.

---

## ggbots Platform Aesthetic

**IMPORTANT**: This project has an established design system. Follow it.

### Tone: Ceremonial Brutalism / Guild Hall

### Colors (CSS Variables)
```css
--bg-primary: #0b0b0c      /* Obsidian - main background */
--bg-secondary: #141416    /* Slightly lighter */
--bg-tertiary: #1a1a1d     /* Card backgrounds */
--text-primary: #edebe7    /* Ivory - main text */
--text-secondary: #d6d3ce  /* Muted text */
--text-muted: #8a8781      /* Subtle text */
--accent: #c1a87d          /* Brass - CTAs, highlights */
--accent-hover: #d4bc91    /* Brass hover state */
--border: #2a2a2d          /* Subtle borders */
--ember: #e05c4d           /* Error/danger */
```

### Typography
- **Display**: Bodoni Moda (dramatic headers)
- **Body**: Space Grotesk (clean, readable)
- **Mono**: IBM Plex Mono (code, numbers, data)

### Philosophy
- Border-based cards, **no shadows**
- Intentional restraint over decoration
- Brass accents used sparingly for emphasis
- Dark mode first (obsidian background)

---

## Design Thinking Framework

Before coding, establish a **BOLD aesthetic direction**:

### 1. Purpose
- What problem does this interface solve?
- Who uses it?

### 2. Tone (ggbots uses Ceremonial Brutalism)
Other options for reference:
- Brutally minimal
- Maximalist chaos
- Retro-futuristic
- Organic/natural
- Luxury/refined
- Playful/toy-like
- Editorial/magazine
- Brutalist/raw
- Art deco/geometric

### 3. Constraints
- Technical requirements (framework, performance, accessibility)

### 4. Differentiation
- What makes this UNFORGETTABLE?
- What's the one thing someone will remember?

**CRITICAL:** Choose intentionality over intensity. Bold maximalism and refined minimalism both work—the key is execution precision.

---

## Frontend Aesthetics Guidelines

### Typography
- Choose beautiful, unique, and **interesting fonts**
- Avoid generic choices (Arial, Inter, Roboto, system fonts)
- **For ggbots**: Use Bodoni Moda for headers, Space Grotesk for body
- Unexpected typography elevates the entire aesthetic

### Color & Theme
- Commit to a cohesive aesthetic
- Use **CSS variables** for consistency
- **Dominant colors with sharp accents** outperform timid, evenly-distributed palettes
- **For ggbots**: Obsidian base, brass accents, ivory text

### Motion & Animation
- Use animations for effects and micro-interactions
- **CSS-only solutions** for HTML
- **Framer Motion** for React when available
- **High-impact orchestration:** One well-orchestrated page load with staggered reveals (via `animation-delay`) creates more delight than scattered micro-interactions
- Leverage scroll-triggering and hover states that surprise
- **For ggbots**: Subtle, purposeful animations only

### Spatial Composition
- Unexpected layouts
- Asymmetry and overlap
- Diagonal flow
- Grid-breaking elements
- Generous negative space OR controlled density

### Backgrounds & Visual Details
Create atmosphere and depth rather than solid colors:
- Gradient meshes
- Noise textures
- Geometric patterns
- Layered transparencies
- Dramatic shadows (but NOT for ggbots - use borders instead)
- Decorative borders
- Grain overlays
- Context-specific visual effects

---

## What to AVOID

**NEVER use:**
- Generic AI-generated aesthetics
- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (purple gradients on white)
- Predictable layouts and component patterns
- Cookie-cutter design lacking context-specific character
- Shadows for ggbots (use borders instead)

**DO:** Match the existing ggbots aesthetic. Don't introduce new patterns without reason.

---

## Implementation Requirements

Code must be:
- ✅ **Production-grade and functional**
- ✅ **Visually striking and memorable**
- ✅ **Cohesive with ggbots aesthetic**
- ✅ **Meticulously refined in every detail**

---

## ggbots-Specific Patterns

### Modal Component
Use the existing `<Modal>` from `frontend/components/ui/modal.tsx`:
```tsx
import { Modal, ModalHeader, ModalBody, ModalFooter } from '@/components/ui/modal'

<Modal open={isOpen} onOpenChange={setIsOpen} size="md">
  <ModalHeader>
    <ModalTitle>Title Here</ModalTitle>
  </ModalHeader>
  <ModalBody>
    {/* Content */}
  </ModalBody>
  <ModalFooter>
    {/* Actions */}
  </ModalFooter>
</Modal>
```

### Button Patterns
```tsx
// Primary CTA (brass)
<button className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)]">
  <Icon className="h-4 w-4" />
  Action
</button>

// Secondary (border)
<button className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-colors border border-[var(--border)] hover:border-[var(--accent)] text-[var(--text-primary)]">
  Secondary
</button>
```

### Card Patterns
```tsx
<div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
  {/* No shadows - border-based */}
</div>
```

### Input Patterns
```tsx
<input
  className="w-full rounded-xl border border-[var(--border)] bg-[var(--bg-primary)] px-4 py-3 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-[var(--accent)] focus:outline-none"
/>
```

---

## Key Principle

**Match implementation complexity to aesthetic vision:**
- **Maximalist designs** = Elaborate code with extensive animations and effects
- **Minimalist/refined designs** = Restraint, precision, careful spacing, subtle details

For ggbots: **Refined minimalism with brass accents**. Elegance comes from executing your vision *well*, not from complexity alone.

---

## Final Directive

*Claude is capable of extraordinary creative work. For ggbots, channel that creativity within the established Ceremonial Brutalism aesthetic. Don't deviate—elevate.*
