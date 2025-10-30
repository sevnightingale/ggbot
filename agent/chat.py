#!/usr/bin/env python3
"""
Chat CLI for interacting with trading agent via Redis queues.

Usage:
    python agent/chat.py --config-id <config_id>
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
import redis.asyncio as redis
import aioconsole


async def response_monitor(redis_client: redis.Redis, config_id: str, stop_event: asyncio.Event):
    """Background task that continuously monitors for agent responses."""
    while not stop_event.is_set():
        try:
            response_data = await redis_client.blpop(
                f"agent:{config_id}:responses",
                timeout=1  # Short timeout to check stop_event frequently
            )

            if response_data:
                try:
                    response = json.loads(response_data[1])
                    response_text = response.get("text", str(response))
                    print(f"\n\nAgent: {response_text}\n")
                    print("You: ", end="", flush=True)  # Restore prompt
                except json.JSONDecodeError:
                    print(f"\n\nAgent: {response_data[1].decode()}\n")
                    print("You: ", end="", flush=True)

        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f"\nError monitoring responses: {e}")
            await asyncio.sleep(1)


async def input_handler(redis_client: redis.Redis, config_id: str, stop_event: asyncio.Event):
    """Handle user input and send to agent."""
    print("Chat CLI started. Type 'exit' to quit.\n")

    while not stop_event.is_set():
        try:
            # Non-blocking input using aioconsole
            user_input = await aioconsole.ainput("You: ")
            user_input = user_input.strip()

            if not user_input:
                continue

            if user_input.lower() == 'exit':
                print("Goodbye!")
                stop_event.set()
                break

            # Send message to agent
            message_data = json.dumps({
                "type": "user_message",
                "text": user_input,
                "timestamp": datetime.utcnow().isoformat()
            })
            await redis_client.rpush(f"agent:{config_id}:messages", message_data)

        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            stop_event.set()
            break
        except Exception as e:
            print(f"Error: {e}")


async def chat_loop(config_id: str, redis_url: str):
    """Main chat loop with concurrent response monitoring and input handling."""
    redis_client = await redis.from_url(redis_url)
    stop_event = asyncio.Event()

    try:
        # Run response monitor and input handler concurrently
        await asyncio.gather(
            response_monitor(redis_client, config_id, stop_event),
            input_handler(redis_client, config_id, stop_event)
        )
    finally:
        await redis_client.aclose()


def main():
    parser = argparse.ArgumentParser(description="Chat with trading agent via Redis")
    parser.add_argument(
        "--config-id",
        required=True,
        help="Agent configuration ID"
    )
    parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL", "redis://localhost:6379"),
        help="Redis connection URL (default: redis://localhost:6379)"
    )

    args = parser.parse_args()

    try:
        asyncio.run(chat_loop(args.config_id, args.redis_url))
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
