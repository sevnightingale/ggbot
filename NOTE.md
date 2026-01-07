# CC Instance B - Polish & Navigation Tasks

Another CC instance is working on the Arena page and registration endpoint. You are handling polish and navigation tasks that don't conflict with those files.

## Context
We're launching ggArena Season 1. Launch tweet goes out tomorrow (Jan 8), competition starts Jan 21. See `TODO.md` for full context - you should have read it via GO.md.

## Your Tasks (DO NOT touch arena/page.tsx or ggbot.py - other CC is working on those)

### 1. Add ggArena to Navbar + Banner
- Add "Arena" link to main navigation
- Add a banner/announcement about Season 1 launching Jan 21st
- Make it mobile-friendly
- Look at existing nav components to understand the pattern

### 2. Remove "Free" Labels from Bot Creation Modal
- Find the bot creation modal component
- Remove any "free" text after options (we're usage-based now, it's confusing)
- File is likely in `frontend/components/` - search for "BotCreationModal" or "CreateBot"

### 3. Fix Light Mode Theme Issues
- Strategy Advisor buttons have miscolored text in light mode
- Image upload icon in ActivationBar not responsive to theme
- Check `frontend/app/forge/components/monitor/ActivationBar.tsx`
- Check `frontend/components/StrategyAdvisorPanel.tsx` or similar
- Use CSS variables like `var(--text-primary)` instead of hardcoded colors

### 4. Fix "Setting up your ggbot" Message
- When user has no bots, message shows "Setting up your ggbot... Please wait while we create your bot"
- But we're NOT auto-creating a bot anymore
- Find where this message is displayed and update copy to something like "Create your first ggbot to get started"
- Likely in dashboard or main app page

### 5. Remove Floating Question Mark Helper Icon
- There's a floating help icon in bottom right corner
- Remove it
- Instead, add social links to footer or navbar (Twitter/X, Telegram, Discord)

## Files You Can Safely Edit
- `frontend/components/nav/*`
- `frontend/components/BotCreationModal.tsx` (or similar)
- `frontend/components/StrategyAdvisorPanel.tsx`
- `frontend/app/forge/components/monitor/ActivationBar.tsx`
- `frontend/components/ui/*`
- `frontend/app/page.tsx` or dashboard components

## Files to AVOID (Other CC is editing these)
- `frontend/app/arena/page.tsx` - DO NOT TOUCH
- `frontend/app/arena/layout.tsx` - DO NOT TOUCH
- `ggbot.py` - DO NOT TOUCH

## How to Proceed
1. Start with the navbar + banner (highest visibility)
2. Then fix the "free" labels
3. Then light mode issues
4. Then the "setting up" message
5. Finally the helper icon removal

Check off items in TODO.md as you complete them. Ask the user if you have questions about the design or approach.
