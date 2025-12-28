# Strategy Advisor Unification & Agent Cleanup

**Created**: 2025-12-04
**Completed**: 2025-12-04
**Status**: COMPLETE
**TODO Section**: Strategy Advisor Unification & Agent Cleanup

---

## Overview

Unify the configuration experience across all bot types by leveraging the existing Strategy Advisor API. Remove the old PM2-based `strategy_definition` mode and consolidate duplicate strategy fields.

## Background

### Current State (Technical Debt)

**Two Configuration Systems:**
1. **Strategy Advisor** (API-based, simple)
   - Backend: `api/assistant.py`
   - Frontend: `StrategyAdvisorPanel.tsx`
   - Used by: `scheduled_trading` and `signal_validation` bots
   - How it works: Claude Haiku with function calling, instant responses

2. **Agent Configurator** (PM2-based, complex)
   - Backend: `agent/run_agent.py` in `strategy_definition` mode
   - Frontend: `AgentConfigurator.tsx`
   - Used by: `agent` bots only
   - How it works: Spawns PM2 process, Redis queues for messaging

**The Problem:**
- Strategy Advisor already supports ALL bot types (including agent)
- Agent bots get a worse UX (must click "Start Strategy Builder", wait for PM2)
- Duplicate code paths for the same functionality
- Two strategy fields: `agent_strategy.content` vs `decision.user_prompt`

### Target State

**Single Configuration System:**
- All bot types use `StrategyAdvisorPanel` for AI-assisted configuration
- Single strategy field: `decision.user_prompt`
- Agent PM2 process ONLY for autonomous trading execution
- No `strategy_definition` mode - agent only runs in `autonomous` mode

---

## Architecture Decisions

### 1. Strategy Field Consolidation

**Decision**: Use `decision.user_prompt` as THE strategy field for all bot types.

| Field | Keep/Remove | Reason |
|-------|-------------|--------|
| `decision.user_prompt` | KEEP | Universal strategy field |
| `decision.system_prompt` | KEEP (hidden) | LLM instructions, advanced setting |
| `agent_strategy.content` | DEPRECATE | Redundant with user_prompt |
| `agent_strategy.*` | DEPRECATE | Version tracking not needed |

**Migration**: Existing agent bots with `agent_strategy.content` will need strategy copied to `decision.user_prompt`. Can be done lazily (on next config save).

### 2. Agent Mode UI

**Decision**: Agent config shows ONLY StrategyAdvisorPanel + strategy textarea.

Why hide other options for agents:
- Agents don't need `analysis_frequency` (they decide when to trade)
- Agents don't need `extraction.indicators` preset (they query dynamically)
- Agents don't need complex trade settings (they manage risk autonomously)

What agents see:
```
+----------------------------------+
| Strategy Advisor Panel           |
| [Chat interface - always visible]|
+----------------------------------+
| Trading Strategy                 |
| [Large textarea for strategy]    |
+----------------------------------+
```

### 3. Backend Agent Mode

**Decision**: Remove `strategy_definition` mode entirely.

Current modes:
- `strategy_definition` - Chat with agent to build strategy (REMOVE)
- `autonomous` - Agent trades autonomously (KEEP)

After cleanup:
- Agent start endpoint only accepts autonomous mode (or no mode param)
- Redis message/poll endpoints can be simplified or removed

---

## Implementation Plan

### Phase 1: Frontend Unification

**ConfigureLayout.tsx Changes:**
```typescript
// Add agent mode detection
const isAgentMode = botType === 'agent'

// Conditional rendering
return (
  <div>
    <StrategyAdvisorPanel ... />

    {isAgentMode ? (
      // Agent mode: just strategy textarea
      <AgentStrategySection configData={configData} onUpdate={onUpdateConfig} />
    ) : (
      // Normal mode: full config tabs
      <>
        <ConfigTabs ... />
        {/* tab content */}
      </>
    )}
  </div>
)
```

**page.tsx Changes:**
- Remove: `agentMessages`, `agentInputValue`, `isWaitingForAgent`, `agentStarted` state
- Remove: `handleSendAgentMessage`, `handleStartStrategyBuilder` handlers
- Remove: Redis polling useEffect
- Remove: Special routing to `AgentConfigurator`
- Change: Route agent config_type to `ConfigureLayout`

**Delete:**
- `frontend/app/forge/components/configure/AgentConfigurator.tsx`

### Phase 2: Strategy Field Consolidation

**api/assistant.py Changes:**

Current `update_full_config` tool:
```python
# Updates any field including agent_strategy and decision.system_prompt
```

After:
```python
# Only updates decision.user_prompt for strategy changes
# Ignores system_prompt updates from AI
# Removes agent_strategy handling
```

**StrategyEditor.tsx:**
- Already uses `decision.user_prompt` - verify it works for agent mode
- Add agent-specific placeholder if needed

### Phase 3: Backend Cleanup

**api/agent.py Changes:**

Remove from `start_agent`:
```python
mode: str = Query(..., description="strategy_definition | autonomous")
```

Change to:
```python
# No mode param needed, always autonomous
```

Remove or simplify:
- `/message` endpoint (only used for strategy_definition)
- `/poll-response` endpoint (only used for strategy_definition)
- Keep `/conversation-history` if autonomous mode uses it

**agent/run_agent.py Changes:**

Remove `strategy_definition` mode branch:
```python
# Before
if mode == "strategy_definition":
    # Complex Redis message handling
elif mode == "autonomous":
    # Trading loop

# After
# Only autonomous trading loop
```

### Phase 4: Documentation

**agent/README.md Updates:**
- Remove strategy_definition mode documentation
- Document new architecture:
  - Strategy Advisor (API) handles configuration
  - Agent (PM2) handles autonomous execution only
- Update diagrams if any

---

## File Changes Summary

| File | Changes |
|------|---------|
| `frontend/app/forge/components/configure/ConfigureLayout.tsx` | Add `isAgentMode` conditional, render strategy-only UI for agents |
| `frontend/app/forge/page.tsx` | Remove AgentConfigurator routing, remove agent state, clean up handlers |
| `frontend/app/forge/components/configure/AgentConfigurator.tsx` | DELETE |
| `frontend/app/forge/components/configure/StrategyEditor.tsx` | Verify works for agent mode |
| `api/assistant.py` | Only update decision.user_prompt, remove agent_strategy refs |
| `api/agent.py` | Remove strategy_definition mode, simplify endpoints |
| `agent/run_agent.py` | Remove strategy_definition branch |
| `agent/README.md` | Update documentation |

---

## Testing Checklist

- [x] Agent bot: Can chat with Strategy Advisor (UI integration complete)
- [x] Agent bot: Strategy saves to `decision.user_prompt` (api/assistant.py updated)
- [x] Agent bot: Can start autonomous trading (api/agent.py updated)
- [x] Agent bot: ConfigTabs are hidden (ConfigureLayout.tsx updated)
- [x] Scheduled bot: Configuration works unchanged (no changes to scheduled flow)
- [x] Signal bot: Configuration works unchanged (no changes to signal flow)
- [x] Strategy Advisor: Only updates user_prompt, not system_prompt (verified)
- [x] Build passes (TypeScript, ESLint) - verified 2025-12-04

**Production testing still needed** - requires deployment and manual verification

---

## Rollback Plan

If issues arise:
1. Frontend: Revert ConfigureLayout and page.tsx changes
2. Keep AgentConfigurator.tsx (don't delete until verified)
3. Backend: Keep strategy_definition mode in api/agent.py

Low risk since:
- Strategy Advisor API already works for all bot types
- No database schema changes required
- Existing bots continue to work (just different UI)

---

## Future Considerations

After this cleanup:
- Consider removing `agent_strategy` column from configurations table entirely
- Consider adding strategy version tracking to `decision` if needed
- Consider adding "advanced settings" accordion for system_prompt access
