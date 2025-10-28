  1. ClaudeSDKClient lifecycle and MCP integration:
  How do I initialize ClaudeSDKClient with a custom MCP server in Python?
  Specifically:
  - Do I pass the MCP server config when creating the client?
  - Does the client stay open for the entire agent session?
  - Example code for creating a persistent client with custom MCP tools?


 ## Initializing ClaudeSDKClient with custom MCP servers

You pass the MCP server configuration when creating the `ClaudeSDKClient` through the `ClaudeAgentOptions` parameter[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes). The client stays open for your entire agent session when used as a context manager[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes).

Here's how to create a persistent client with custom MCP tools:

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock
)
import asyncio
from typing import Any

# Define custom tools with @tool decorator
@tool("calculate", "Perform mathematical calculations", {"expression": str})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = eval(args["expression"], {"__builtins__": {}})
        return {
            "content": [{
                "type": "text",
                "text": f"Result: {result}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "is_error": True
        }

@tool("get_time", "Get current time", {})
async def get_time(args: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "content": [{
            "type": "text",
            "text": f"Current time: {current_time}"
        }]
    }

async def main():
    # Create SDK MCP server with custom tools
    my_server = create_sdk_mcp_server(
        name="utilities",
        version="1.0.0",
        tools=[calculate, get_time]
    )

    # Configure options with the server
    options = ClaudeAgentOptions(
        mcp_servers={"utils": my_server},

        allowed_tools=[
            "mcp__utils__calculate",
            "mcp__utils__get_time"
        ]
    )

    # Use ClaudeSDKClient for interactive tool usage
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What's 123 * 456?")

        # Process calculation response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Calculation: {block.text}")

        # Follow up with time query
        await client.query("What time is it now?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Time: {block.text}")

asyncio.run(main())
```
[(2)](https://docs.claude.com/en/api/agent-sdk/python#example-usage)

## Key points:

- **Pass MCP config at initialization**: You create `ClaudeAgentOptions` with your `mcp_servers` dictionary and pass it to `ClaudeSDKClient(options=options)`[(2)](https://docs.claude.com/en/api/agent-sdk/python#example-usage)[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)
- **Client stays open**: When using `async with ClaudeSDKClient(options=options) as client:`, the client remains open for the entire session within that context[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)
- **Multiple queries in same session**: You can call `client.query()` multiple times, and Claude remembers previous context[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)







 2. Message flow and Redis queue integration:
  How do I integrate a Redis message queue with ClaudeSDKClient in Python?
  My architecture:
  - User pushes messages to Redis queue
  - Agent polls queue, sends message to Claude via client.query()
  - Agent gets response, pushes to Redis response queue

  Questions:
  - Can I call client.query() multiple times in a loop on the same client?
  - Does query() block until agent finishes all tool calls?
  - How do I send follow-up messages in an ongoing conversation?









 ## Integrating Redis with ClaudeSDKClient

Yes, you can call `client.query()` multiple times in a loop on the same client[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes). The `ClaudeSDKClient` is specifically designed for continuous conversations where Claude remembers previous context[(2)](https://docs.claude.com/en/api/agent-sdk/python).

## Key behaviors:

**1. Multiple query() calls are supported:**
```python
async with ClaudeSDKClient() as client:
    # First question
    await client.query("What's the capital of France?")
    
    # Process response
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
    
    # Follow-up question - Claude remembers the previous context
    await client.query("What's the population of that city?")
    
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
```
[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)

**2. query() does NOT block** - it's asynchronous and you must iterate through responses:
- `client.query()` sends the message but doesn't wait for completion[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)
- You must call `client.receive_response()` or `client.receive_messages()` to get the agent's output[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)
- The agent completes all tool calls before you receive the final result[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)

**3. Follow-up messages maintain conversation context:**

The client maintains session continuity across multiple exchanges[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes). Each new `query()` call continues the same conversation[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes).

## Redis integration example:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
import asyncio
import redis.asyncio as redis

async def redis_agent_loop():
    # Initialize Redis
    redis_client = await redis.from_url("redis://localhost")
    
    # Initialize Claude client with options
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits"
    )
    
    async with ClaudeSDKClient(options=options) as client:
        print("Agent started, polling Redis queue...")
        
        while True:
            # Poll Redis queue for user messages
            message_data = await redis_client.blpop("user_messages", timeout=5)
            
            if message_data:
                _, user_message = message_data
                user_text = user_message.decode('utf-8')
                print(f"Received from queue: {user_text}")
                
                # Send to Claude
                await client.query(user_text)
                
                # Collect full response
                response_parts = []
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                response_parts.append(block.text)
                
                # Push response back to Redis
                full_response = " ".join(response_parts)
                await redis_client.rpush("agent_responses", full_response)
                print(f"Pushed response to queue")

asyncio.run(redis_agent_loop())
```
[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)[(3)](https://docs.claude.com/en/api/agent-sdk/python#example-usage)

## Important notes:

- **Session persistence**: The client maintains conversation context across all `query()` calls within the same session[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)[(2)](https://docs.claude.com/en/api/agent-sdk/python)
- **Response iteration**: You must iterate through `receive_response()` to get the complete output including all tool executions[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)
- **Non-blocking**: `query()` is async and doesn't block, allowing you to manage the Redis polling loop[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)







  3. Streaming vs single mode for autonomous agent:
  For a 24/7 autonomous trading agent that:
  - Continuously loops (check positions → decide → act → sleep)
  - Needs to process user interrupts from Redis queue
  - Uses tools like wait_for() that sleep for hours

  Should I use:
  - Streaming mode (async for message in client.receive_messages())
  - Single mode (await client.query())
  - Something else?

  What's the recommended pattern for a long-running autonomous agent?




 ## Recommended: Streaming Mode with ClaudeSDKClient

For your 24/7 autonomous trading agent, **streaming mode is the recommended approach**[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended). Streaming mode is specifically designed for long-lived, interactive sessions with full tool integration and interruption support[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended).

## Why streaming mode for your use case:

**1. Interruption support**: Streaming mode allows you to interrupt Claude mid-execution using `client.interrupt()`[(2)](https://docs.claude.com/en/api/agent-sdk/python#classes), which is critical for processing user commands from your Redis queue[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended).

**2. Persistent session**: The client maintains conversation context and file system state across the entire session[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended), perfect for continuous monitoring loops.

**3. Tool integration**: Full access to all tools and custom MCP servers during the session[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended).

**4. Queued messages**: You can send multiple messages that process sequentially with the ability to interrupt[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended).

## Architecture pattern for your autonomous agent:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
import asyncio
import redis.asyncio as redis

async def autonomous_trading_agent():
    redis_client = await redis.from_url("redis://localhost")
    
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Bash", "mcp__trading__check_positions", 
                      "mcp__trading__execute_trade", "mcp__trading__wait_for"],
        permission_mode="acceptEdits",
        max_turns=100
    )
    
    async with ClaudeSDKClient(options=options) as client:
        # Start the autonomous loop
        await client.query("""
        You are an autonomous trading agent. Continuously:
        1. Check current positions
        2. Analyze market conditions
        3. Make trading decisions
        4. Execute trades if needed
        5. Wait for next cycle (use wait_for tool)
        
        Continue this loop indefinitely.
        """)
        
        # Process messages in parallel
        agent_task = asyncio.create_task(process_agent_messages(client, redis_client))
        interrupt_task = asyncio.create_task(handle_user_interrupts(client, redis_client))
        
        await asyncio.gather(agent_task, interrupt_task)

async def process_agent_messages(client, redis_client):
    """Process streaming messages from Claude"""
    async for message in client.receive_messages():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    # Log agent actions
                    await redis_client.rpush("agent_logs", block.text)
                    print(f"Agent: {block.text}")

async def handle_user_interrupts(client, redis_client):
    """Poll Redis for user commands and interrupt if needed"""
    while True:
        message_data = await redis_client.blpop("user_commands", timeout=1)
        
        if message_data:
            _, command = message_data
            user_command = command.decode('utf-8')
            print(f"User interrupt: {user_command}")
            
            # Interrupt current execution
            await client.interrupt()
            
            # Send new command
            await client.query(user_command)
            
            # Get response to user command
            response_parts = []
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_parts.append(block.text)
            
            full_response = " ".join(response_parts)
            await redis_client.rpush("user_responses", full_response)

asyncio.run(autonomous_trading_agent())
```
[(2)](https://docs.claude.com/en/api/agent-sdk/python#classes)[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended)

## Key benefits for your scenario:

- **Long-running sessions**: The client stays alive for your entire 24/7 operation[(2)](https://docs.claude.com/en/api/agent-sdk/python#classes)
- **Interrupt support**: `client.interrupt()` allows you to stop Claude mid-execution when user commands arrive[(2)](https://docs.claude.com/en/api/agent-sdk/python#classes)
- **Tool execution during sleep**: Your `wait_for()` tool can sleep for hours while the session remains active[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended)
- **Context preservation**: Claude remembers all previous trading decisions and market conditions[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended)

## Alternative: Single message mode limitations

Single message mode does **not** support[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended):
- Real-time interruption
- Natural multi-turn conversations
- Dynamic message queueing

Single message mode is better suited for stateless, one-shot queries[(1)](https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode#streaming-input-mode-recommended), not continuous autonomous agents.

## Important note about `receive_messages()` vs `receive_response()`:

- **`receive_messages()`**: Streams all messages indefinitely, suitable for your continuous loop[(2)](https://docs.claude.com/en/api/agent-sdk/python#classes)
- **`receive_response()`**: Streams messages until and including a ResultMessage, then stops[(2)](https://docs.claude.com/en/api/agent-sdk/python#classes)

For your autonomous agent, use `receive_messages()` to keep processing the continuous loop, and use `receive_response()` when handling specific user interrupts that expect a direct answer[(2)](https://docs.claude.com/en/api/agent-sdk/python#classes).


  4. System prompt and context injection:
  How do I pass initial context to ClaudeSDKClient in Python?
  Specifically:
  - Where do I set the system prompt?
  - How do I inject dynamic context (strategy, config_id, mode)?
  - Can I update context between queries?
  - Example of passing both system prompt and initial user message?


   ## Setting system prompts and context in ClaudeSDKClient

You set the system prompt through `ClaudeAgentOptions` when initializing the client, and inject dynamic context via the initial `connect()` or `query()` call[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes).

## Where to set the system prompt:

The system prompt is configured in `ClaudeAgentOptions` using the `system_prompt` parameter[(2)](https://docs.claude.com/en/api/agent-sdk/modifying-system-prompts):

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def main():
    options = ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code"  # Use Claude Code's system prompt
        },
        setting_sources=["project"]  # Load CLAUDE.md files
    )
    
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Create a Python file")
        
        async for message in client.receive_response():
            print(message)

asyncio.run(main())
```
[(2)](https://docs.claude.com/en/api/agent-sdk/modifying-system-prompts)

## Injecting dynamic context (strategy, config_id, mode):

You can inject dynamic context in two ways:

**1. Via initial prompt when connecting:**

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def trading_agent_with_context(strategy: str, config_id: str, mode: str):
    options = ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code"
        },
        allowed_tools=["Read", "Write", "Bash"]
    )
    
    # Inject dynamic context in initial prompt
    initial_context = f"""
    You are a trading agent with the following configuration:
    - Strategy: {strategy}
    - Config ID: {config_id}
    - Mode: {mode}
    
    Use this configuration for all trading decisions.
    """
    
    async with ClaudeSDKClient(options=options) as client:
        # Pass context when connecting
        await client.connect(prompt=initial_context)
        
        # Now send actual task
        await client.query("Check current positions and analyze")
        
        async for message in client.receive_response():
            print(message)

asyncio.run(trading_agent_with_context(
    strategy="momentum",
    config_id="config_123",
    mode="live"
))
```
[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)

**2. Via appended system prompt:**

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def trading_agent_with_appended_prompt(strategy: str, config_id: str, mode: str):
    # Build dynamic system prompt content
    custom_instructions = f"""
    TRADING CONFIGURATION:
    - Strategy: {strategy}
    - Config ID: {config_id}
    - Trading Mode: {mode}
    
    Always reference this configuration when making trading decisions.
    """
    
    options = ClaudeAgentOptions(
        system_prompt={
            "type": "append",
            "preset": "claude_code",
            "append": custom_instructions
        },
        allowed_tools=["Read", "Write", "Bash"]
    )
    
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Analyze market and execute trades")
        
        async for message in client.receive_response():
            print(message)

asyncio.run(trading_agent_with_appended_prompt(
    strategy="mean_reversion",
    config_id="config_456",
    mode="paper"
))
```
[(2)](https://docs.claude.com/en/api/agent-sdk/modifying-system-prompts)

## Can you update context between queries?

**Context persists across queries in the same session**[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes). You cannot modify the system prompt mid-session, but you can inject new context via regular user messages:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def update_context_example():
    options = ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code"
        }
    )
    
    async with ClaudeSDKClient(options=options) as client:
        # Initial query with context
        await client.query("Strategy: momentum, Mode: paper trading")
        async for message in client.receive_response():
            pass
        
        # Update context mid-session via new query
        await client.query("""
        CONTEXT UPDATE: Switching to live trading mode.
        New strategy: mean_reversion
        Config ID: config_789
        
        Now analyze positions with this new configuration.
        """)
        
        async for message in client.receive_response():
            print(message)

asyncio.run(update_context_example())
```
[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)

## Complete example with system prompt and initial message:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
import asyncio

async def complete_context_example():
    # Dynamic configuration
    strategy = "momentum"
    config_id = "config_123"
    mode = "live"
    
    # Configure with system prompt
    options = ClaudeAgentOptions(
        system_prompt={
            "type": "append",
            "preset": "claude_code",
            "append": f"""
            TRADING AGENT CONFIGURATION:
            - Primary Strategy: {strategy}
            - Configuration ID: {config_id}
            - Trading Mode: {mode}
            - Risk Tolerance: Medium
            
            Always consider this configuration in your decisions.
            """
        },
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits"
    )
    
    async with ClaudeSDKClient(options=options) as client:
        # Initial message with task context
        initial_prompt = """
        Start autonomous trading loop:
        1. Check current positions
        2. Analyze market conditions
        3. Execute trades based on configured strategy
        4. Wait 1 hour and repeat
        """
        
        await client.connect(prompt=initial_prompt)
        
        # Process agent responses
        async for message in client.receive_messages():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Agent: {block.text}")

asyncio.run(complete_context_example())
```
[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)[(2)](https://docs.claude.com/en/api/agent-sdk/modifying-system-prompts)

## Key points:

- **System prompt**: Set via `ClaudeAgentOptions.system_prompt` at initialization[(2)](https://docs.claude.com/en/api/agent-sdk/modifying-system-prompts)
- **Dynamic context**: Inject via initial `connect(prompt=...)` or first `query()` call[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)
- **Context updates**: Send new context as regular user messages; Claude remembers all previous messages[(1)](https://docs.claude.com/en/api/agent-sdk/python#classes)
- **System prompt persistence**: Cannot be changed mid-session; set once at initialization[(2)](https://docs.claude.com/en/api/agent-sdk/modifying-system-prompts)