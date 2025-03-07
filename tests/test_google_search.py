import asyncio
import os
from dotenv import load_dotenv
from browser_use import Agent, Browser, BrowserConfig, BrowserContextConfig
from langchain_openai import ChatOpenAI

# Load environment variables (e.g., API keys)
load_dotenv()

async def main():
    # Configure the browser context (optional but recommended)
    context_config = BrowserContextConfig(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        wait_for_network_idle_page_load_time=3.0,  # Time to wait for page load
        browser_window_size={'width': 1280, 'height': 1100},
        locale='en-US'
    )

    # Configure Browser-use to connect to Browserless via CDP
    browser_config = BrowserConfig(
        cdp_url="ws://localhost:3000",  # Browserless WebSocket URL
        headless=True,                  # Run in headless mode
        new_context_config=context_config
    )
    browser = Browser(config=browser_config)

    # Create a new browser context
    context = await browser.new_context()

    # Set up the language model (e.g., GPT-4o)
    model = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=os.getenv("EXTRACTION_LLM_API_KEY")
    )

    # Define the task
    task = "Go to google.com and search for 'browser automation'."

    # Initialize the agent with the Browserless-connected browser
    agent = Agent(
        task=task,
        llm=model,
        browser=browser,
        browser_context=context,
        use_vision=True,  # Enable vision if needed
        save_conversation_path="logs/google_search_conversation.json"  # For debugging
    )

    try:
        # Run the agent
        history = await agent.run(max_steps=50)
        print(f"Result: {history}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())