# New ggbots Landing Page - Complete Redesign

## Overview
Complete redesign of the ggbots landing page with focus on conversion optimization, interactive demo, and clear user journey. Moving away from abstract three-agent explanation to practical, results-driven approach.

## Design Philosophy
- **Conversion-first**: Every section drives toward CTA
- **Show, don't tell**: Interactive demo upfront
- **Personal credibility**: Sev's story for trust building  
- **Clear value prop**: Immediate understanding of benefits
- **Consistent styling**: Follow VIBE.md brutalist command center aesthetic

---

## Page Structure & Sections

### 1. Header/Navigation
**Layout**: Clean header with logo, hamburger menu, and primary CTA
- **Logo**: ggbots.ai logo (left) - using `ggbots_logo.png`
- **Navigation**: Hamburger menu (center) - jumps to page sections
  - Hero/Demo section
  - Process section  
  - Features section
  - Pricing section
- **Primary CTA**: "Launch App" (right)

**Styling**:
- Background: charcoal-900 (#161618)
- Text: bone-200 (#e3e5e6)
- CTA button: agent-extraction (#38a1c7) with neumorphic styling

---

### 2. Hero Section
**Layout**: Clean, minimal hero with clear value proposition

**Primary Headline**:
```
One liner- what is it who is it for?
```

**Sub-headline**:
```
sub one liner what does it do?
```

**Visual Elements**:
- Minimal background textures from VIBE.md
- Subtle animated elements (optional)
- Focus on typography hierarchy

**CTA**: "Create a ggbot now" button (agent colors)

**Styling**:
- Background: charcoal-900 with subtle textures
- Headers: font-display (Kanit)
- Body text: font-sans (Inter)
- Color scheme: bone-200/300 text on charcoal background

---

### 3. Interactive Demo Section
**Layout**: Full-width container for Arcade embed

**Content**:
- **Placeholder text**: "Demo Space (Arcade)"
- **Container styling**: Prepared for iframe/embed
- **Dimensions**: Responsive, likely 16:9 or custom aspect ratio

**Purpose**: 
- Show ggbot creation process
- Dashboard walkthrough
- Live trades and performance
- User interaction simulation

**Implementation**:
- Responsive container ready for Arcade embed
- Proper spacing and visual integration
- Loading states consideration

---

### 4. Process Section - "3 Easy Steps"
**Layout**: Horizontal three-column layout

**Headline**: "Automate you trading in 3 easy steps"

**Steps**:
1. **Configure your agents**
   - Brief description of customization
2. **Set your guardrails** 
   - Risk management configuration
3. **Launch your ai bot**
   - Deploy and monitor

**CTA**: "Launch App" button

**Styling**:
- Three equal-width cards
- Corner bracket styling from VIBE.md
- Agent colors for step indicators
- Clean typography hierarchy

---

### 5. Personal Story Section - Sev's Letter
**Layout**: Single column, letter-style format with personal touch

**Content Structure**:
```
Dear trader,
I'm sev

I've been a crypto day trader for the last 5 years. I've tried many bots, lost $1,500 in 
experimenting with them, and ultimately found they created more work for me.

the problem with bots are
1. They don't adapt to changing market conditions  
2. They follow rigid rules with zero reasoning
3. They can't think beyond the data you hardcode in

This is what drove me to build ggbots, an AI first trading bot that...

1. Can predict and adapt market changes
2. Follows a trading strategy without being stuck to a rigid set of rules  
3. Can think, rationalize and recalculate like I would

I'm building with the input of x number of traders come join our journey (link)
```

**Visual Elements**:
- **Profile photo**: Circular placeholder for Sev's photo
- **Social link**: Twitter/X icon and link
- **Letter styling**: Personal, conversational formatting

**Styling**:
- Letter-style formatting with personal touch
- Highlight key pain points and solutions  
- Profile photo integration
- Social proof elements

---

### 6. Features Section
**Layout**: 2x2 grid of feature cards

**Feature Cards** (4 total):
- **Customized Indicators**
  - Short description w/ link to live demo
  - Video walkthrough of feature/screen recording
- **Feature 2** (TBD)
  - Short description w/ link to live demo  
  - Video walkthrough of feature/screen recording
- **Feature 3** (TBD)
  - Short description w/ link to live demo
  - Video walkthrough of feature/screen recording  
- **Feature 4** (TBD)
  - Short description w/ link to live demo
  - Video walkthrough of feature/screen recording

**Styling**:
- Sharp geometric containers from VIBE.md
- Corner bracket system
- Agent color accents
- Embedded video players or mockup screens

---

### 7. Video Section - Talking Head
**Layout**: Large video container with minimal surrounding content

**Content**:
- **Placeholder**: "Talking head style video walk through"
- Personal explanation from Sev
- Product demonstration
- Trust building content

**CTA**: "Create your AI trading agent now"

**Implementation**:
- YouTube embed container
- Responsive video scaling  
- Placeholder for video ID
- Loading states and error handling

---

### 8. FAQ Section
**Layout**: Expandable accordion-style questions

**Content Structure**:
- FAQ header
- 5 common questions (placeholders)
- Expandable answers
- Clean, scannable format

**Questions** (placeholders for now):
1. Question 1
2. Question 2  
3. Question 3
4. Question 4
5. Question 5

**Styling**:
- Accordion functionality
- neumorphic button styling from VIBE.md
- Smooth expand/collapse animations
- Consistent spacing and typography

---

### 9. Pricing Section
**Layout**: Three-tier pricing table

**Pricing Tiers**:

**Free Plan**
- Paper Trading
- User API LLM

**Base Plan** 
- No API LLM
- Telegram Signals
- Cornix integration
- Bot filter thing like what you did for ggshot

**Premium Plan**
- Full Automation
- Plus paper trading
- [Additional features TBD]

**Implementation**:
- Clean pricing table
- "Sign up" CTAs for each tier
- Clear feature differentiation
- Highlight recommended plan (optional)
- Placeholder pricing until Stripe integration complete

---

## Domain Architecture & Routing

### Current Setup
Your middleware (`middleware.ts:24-26`) already handles domain routing:
- **Main domain** (`ggbots.ai`) → `/landing` page  
- **App subdomain** (`app.ggbots.ai`) → `/dashboard` page
- Auth pages (`/login`, `/signup`) work on app subdomain

### Target Domain Structure

**Production Domains**:
- **`ggbots.ai`** (main domain) → New landing page
- **`app.ggbots.ai`** (app subdomain) → Dashboard/application

### User Journey Flow
```
ggbots.ai (landing) 
    ↓ [Click "Launch App" / "Create ggbot now"]
app.ggbots.ai (dashboard/application)
```

### Implementation Plan
1. **Development Phase**: Build new landing at `/new-landing` route
2. **Testing Phase**: Test new landing page functionality  
3. **Migration Phase**: Update middleware to serve new landing:
   ```typescript
   // Update middleware.ts line 25:
   return NextResponse.rewrite(new URL('/new-landing', request.url))
   ```
4. **CTA Links**: All "Launch App" buttons redirect to `app.ggbots.ai`

### CTA Button Configuration
All call-to-action buttons should redirect to app subdomain:
- **"Launch App"** → `https://app.ggbots.ai` 
- **"Create ggbot now"** → `https://app.ggbots.ai`
- **"Sign up"** buttons → `https://app.ggbots.ai/signup`

This maintains clear separation between marketing (main domain) and application (app subdomain).

---

## Technical Implementation Plan

### New Route Structure
- Create `/app/new-landing/` directory
- New page component: `page.tsx`
- New layout if needed: `layout.tsx`
- Import and apply VIBE.md styling standards

### Component Architecture
- Modular section components
- Reusable CTA buttons with variations
- Responsive design patterns
- Clean component separation

### Styling Approach  
- Extend existing Tailwind config
- Use VIBE.md color palette and patterns
- Maintain brutalist command center aesthetic
- Ensure responsive behavior

### Content Strategy
- **Placeholder copy**: Descriptive sentences explaining what type of content goes in each section
- **Asset placeholders**: Spots for icons, images, and other visual elements
- **Logo integration**: Use `ggbots_logo.png` throughout
- **Profile elements**: Circular photo placeholder + social links for Sev
- **Video integration**: YouTube embed ready for future content

### Asset Requirements  
- **Logo**: ✅ `ggbots_logo.png` (uploaded)
- **Profile photo**: 📋 Circular photo of Sev (pending)
- **Section icons**: 📋 Various icons for features/process (pending)
- **Video content**: 📋 YouTube video (pending)

---

## Success Metrics & Goals

### Primary Goals
1. **Increased Conversion**: Clear CTAs and value proposition
2. **User Understanding**: Interactive demo shows actual product
3. **Trust Building**: Personal story and social proof
4. **Reduced Bounce Rate**: Engaging, scannable content

### Secondary Goals
1. **SEO Optimization**: Proper meta tags and content structure
2. **Mobile Experience**: Fully responsive design
3. **Loading Performance**: Optimized assets and code splitting
4. **Analytics Integration**: Track user behavior and conversion funnels

---

## Next Steps

1. **Build page structure** with placeholder content
2. **Implement responsive design** following VIBE.md standards  
3. **Add interactive elements** (accordions, hover effects)
4. **Prepare Arcade demo container** for future integration
5. **Test and iterate** based on user feedback
6. **Content refinement** with actual copy and assets
7. **Pricing integration** when Stripe plans are finalized

This approach provides a solid foundation for a high-converting landing page while maintaining flexibility for future enhancements and content updates.