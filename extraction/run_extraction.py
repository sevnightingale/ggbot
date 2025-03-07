# ggbot/extraction/run_extraction.py
import asyncio
import json
import os
import sys
from dotenv import load_dotenv
from browser_use import Agent, Browser, BrowserConfig, BrowserContextConfig
from langchain_openai import ChatOpenAI

# Add parent directory to sys.path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.logger import logger
from prompts import TEST_TASK

# Bind logger with user_id
logger = logger.bind(user_id="test_user")

# Define cookie file paths
COOKIES_FILE = "extraction/cookies.json"
TEMP_COOKIES_FILE = "extraction/temp_cookies.json"

def preprocess_cookies(cookies):
    """Preprocess cookies to ensure 'sameSite' values are compatible with Playwright."""
    processed_cookies = []
    for cookie in cookies:
        processed_cookie = cookie.copy()
        same_site = processed_cookie.get("sameSite", "").lower()
        if same_site == "no_restriction":
            processed_cookie["sameSite"] = "None"
        elif same_site == "lax":
            processed_cookie["sameSite"] = "Lax"
        elif same_site == "strict":
            processed_cookie["sameSite"] = "Strict"
        else:
            processed_cookie["sameSite"] = "Lax"  # Default fallback
        processed_cookies.append(processed_cookie)
    return processed_cookies

async def main():
    logger.info("Starting extraction script...")

    # Load and preprocess cookies
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
        processed_cookies = preprocess_cookies(cookies)
        with open(TEMP_COOKIES_FILE, "w") as f:
            json.dump(processed_cookies, f)
        cookies_file_path = TEMP_COOKIES_FILE
        logger.info(f"Preprocessed cookies saved to {cookies_file_path}")
    else:
        logger.warning("Cookies file not found at extraction/cookies.json. Proceeding without cookies.")
        cookies_file_path = None

    # Configure browser context
    context_config = BrowserContextConfig(
        cookies_file=cookies_file_path,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        wait_for_network_idle_page_load_time=5.0,
        browser_window_size={'width': 1280, 'height': 1100},
        locale='en-US'
    )

    # Initialize local browser
    browser = Browser()  # Uses local browser, headless by default
    context = await browser.new_context(config=context_config)
    logger.info("Browser context created with cookies loaded.")

    # Set up ChatOpenAI
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=os.getenv("EXTRACTION_LLM_API_KEY")
    )

    # Use TEST_TASK from prompts.py
    task = TEST_TASK

    # Initialize and run the agent
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        browser_context=context,
        use_vision=True,  # Added for visual inspection of GG-Shot indicator
        save_conversation_path="/root/ggbot/logs/extraction_conversation.json",  # For debugging
    )

    try:
        logger.info("Running the agent...")
        history = await agent.run(max_steps=7)
        logger.info(f"Task Result: {history}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        await browser.close()
        logger.info("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())