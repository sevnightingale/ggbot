 Based on the available documentation, here's what I can share about long-running Claude Agent SDK applications:

## Compaction and Context Management

The SDK provides automatic compaction when context limits approach[(1)](https://docs.claude.com/en/api/agent-sdk/slash-commands#common-slash-commands). You can detect when compaction occurs by listening for system messages with `subtype === "compact_boundary"`[(1)](https://docs.claude.com/en/api/agent-sdk/slash-commands#common-slash-commands):

```typescript
for await (const message of query({
  prompt: "/compact",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "compact_boundary") {
    console.log("Compaction completed");
    console.log("Pre-compaction tokens:", message.compact_metadata.pre_tokens);
    console.log("Trigger:", message.compact_metadata.trigger);
  }
}
```
[(1)](https://docs.claude.com/en/api/agent-sdk/slash-commands#common-slash-commands)

Compaction automatically summarizes older messages while preserving important context[(1)](https://docs.claude.com/en/api/agent-sdk/slash-commands#common-slash-commands). This is built on Claude Code's compact slash command[(2)](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk).

## Session Management for Persistence

The SDK supports session resumption, which is key for maintaining state[(3)](https://docs.claude.com/en/api/agent-sdk/sessions#resuming-sessions). When you start a query, capture the session ID from the initial system message[(3)](https://docs.claude.com/en/api/agent-sdk/sessions#resuming-sessions):

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    session_id = None
    
    response = query(
        prompt="Help me build a web application",
        options=ClaudeAgentOptions(model="claude-sonnet-4-5")
    )
    
    async for message in response:
        if message.type == 'system' and message.subtype == 'init':
            session_id = message.session_id
            print(f"Session started with ID: {session_id}")
            # Save this ID for later resumption
```
[(3)](https://docs.claude.com/en/api/agent-sdk/sessions#resuming-sessions)

You can resume sessions later using the saved session ID[(3)](https://docs.claude.com/en/api/agent-sdk/sessions#resuming-sessions):

```python
if session_id:
    resumed_response = query(
        prompt="Continue where we left off",
        options=ClaudeAgentOptions(
            resume=session_id
        )
    )
```
[(3)](https://docs.claude.com/en/api/agent-sdk/sessions#resuming-sessions)

The SDK automatically handles loading conversation history and context when resuming[(3)](https://docs.claude.com/en/api/agent-sdk/sessions#resuming-sessions).

## Deployment Patterns for Long-Running Agents

The documentation outlines several production deployment patterns[(4)](https://docs.claude.com/en/api/agent-sdk/hosting):

**Pattern 2: Long-Running Sessions** - Maintain persistent container instances for long-running tasks, often running multiple Claude Agent processes inside the container based on demand[(4)](https://docs.claude.com/en/api/agent-sdk/hosting). This is best for proactive agents that take action without user input, agents that serve content, or agents that process high amounts of messages[(4)](https://docs.claude.com/en/api/agent-sdk/hosting).

**Pattern 3: Hybrid Sessions** - Ephemeral containers hydrated with history and state, possibly from a database or from the SDK's session resumption features[(4)](https://docs.claude.com/en/api/agent-sdk/hosting). Best for containers with intermittent interaction that kicks off work and spins down when completed but can be continued[(4)](https://docs.claude.com/en/api/agent-sdk/hosting).

## What's Not Explicitly Documented

The documentation doesn't provide specific guidance on:
- Predicting exact timing of auto-compaction events
- Maximum recommended uptime before manual restarts
- Specific recovery patterns for unexpected stream termination
- Whether to implement custom state management vs. relying solely on built-in features

For 24/7 agents, the session resumption feature[(3)](https://docs.claude.com/en/api/agent-sdk/sessions#resuming-sessions) combined with the long-running session deployment pattern[(4)](https://docs.claude.com/en/api/agent-sdk/hosting) appear to be the recommended approach, but explicit best practices for state checkpointing beyond session IDs aren't detailed in the available sources.

Would you like me to provide a general answer based on common patterns for long-running agent systems, or would you prefer to reach out to support for more specific guidance?

Check out these potentially useful sources:
- [Session Management](https://docs.claude.com/en/api/agent-sdk/sessions#resuming-sessions)
- [Hosting the Agent SDK](https://docs.claude.com/en/api/agent-sdk/hosting)
- [Slash Commands in the SDK](https://docs.claude.com/en/api/agent-sdk/slash-commands#common-slash-commands)