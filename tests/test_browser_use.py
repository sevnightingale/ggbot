import asyncio
import json
import os
from browser_use import Agent, Browser, BrowserContextConfig
from langchain_openai import ChatOpenAI  # Adjust if using a different LLM
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File paths for cookies
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
    logger.info("Starting Browser-use test script...")

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

    # Configure browser context with cookies
    context_config = BrowserContextConfig(
        cookies_file=cookies_file_path,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        wait_for_network_idle_page_load_time=5.0,
        browser_window_size={'width': 1280, 'height': 1100},
        locale='en-US'
    )

    # Initialize Browser-use with a local Chromium instance
    browser = Browser()  # No cdp_url, uses local browser
    context = await browser.new_context(config=context_config)
    logger.info("Browser context created with cookies loaded.")

    # Set up a simple LLM (replace with your actual LLM)
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=os.getenv("EXTRACTION_LLM_API_KEY")  # Ensure this is set in your environment
    )

    # Define a basic task for the agent
    task = "Navigate to the TradingView chart at https://www.tradingview.com/chart/HiWAe2vQ/?symbol=COINBASE%3ABTCUSD and Visually inspect the GG-Shot indicator overlaid on the chart, and take note of any signals, trendlines, or other relevant indicators visible on the chart"

    # Initialize and run the agent
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        browser_context=context
    )

    try:
        logger.info("Running the agent...")
        history = await agent.run(max_steps=10)  # Limit steps for simplicity
        logger.info(f"Task Result: {history}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        await browser.close()
        logger.info("Browser closed. Test complete.")

if __name__ == "__main__":
    asyncio.run(main())