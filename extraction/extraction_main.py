import asyncio
from browser_use import Browser, BrowserConfig, BrowserContextConfig, Agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Path to the saved cookies file (shared with session_check_login.py)
COOKIE_FILE = "/root/ggbot/extraction/tv_cookies.json"

# Chart URL for BTCUSD on Coinbase
CHART_URL = "https://www.tradingview.com/chart/HiWAe2vQ/?symbol=COINBASE%3ABTCUSD"

async def run_extraction():
    """
    Extract ggShot indicator data from TradingView using browser-use with vision.
    Returns data in the format: {'trend': 'buy/sell', 'take_profit': price, 'stop_loss': price}.
    """
    # Set the DISPLAY environment variable for Xvfb
    os.environ['DISPLAY'] = ':99'

    # Retrieve the API key from environment variables
    api_key = os.getenv("EXTRACTION_LLM_API_KEY")
    if not api_key:
        logger.error("EXTRACTION_LLM_API_KEY is not set in the environment.")
        raise ValueError("Missing EXTRACTION_LLM_API_KEY in environment variables.")
    logger.debug(f"API key loaded: {api_key[:4]}... (censored)")

    # Check if the cookies file exists
    if not os.path.exists(COOKIE_FILE):
        logger.error(f"Cookies file not found at {COOKIE_FILE}.")
        raise FileNotFoundError(f"Cookies file missing: {COOKIE_FILE}")

    # Configure the browser context to use saved cookies
    ctx_config = BrowserContextConfig(cookies_file=COOKIE_FILE)
    browser_config = BrowserConfig(
        headless=False,  # Headful mode for development/debugging
        new_context_config=ctx_config,
    )

    # Initialize the browser
    browser = Browser(config=browser_config)

    # Initialize the LLM with vision capability
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0, api_key=api_key)

    # Define the extraction task
    task = (
        "Navigate to https://www.tradingview.com/chart/HiWAe2vQ/?symbol=COINBASE%3ABTCUSD "
        "and extract the ggShot indicator data from the chart. Identify the trend signals "
        "(buy or sell), take-profit levels, and stop-loss levels using vision. Return the "
        "data in a structured format like: {'trend': 'buy/sell', 'take_profit': price, 'stop_loss': price}."
    )

    # Create the Agent with vision enabled
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        use_vision=True,  # Enable vision for chart analysis
    )

    # Execute the extraction
    try:
        logger.info("Starting extraction process...")
        result = await agent.run()
        logger.info(f"Extraction Result: {result}")
        print(f"Extracted ggShot Data: {result}")
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        print(f"Error: {e}")
    finally:
        # Ensure the browser closes properly
        await browser.close()
        logger.info("Browser closed.")

if __name__ == "__main__":
    asyncio.run(run_extraction())