import asyncio
from browser_use import Browser, BrowserConfig, BrowserContextConfig, Agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import logging

# Load environment variables for credentials
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def run_extraction():
    """Run the browser-use extraction process in headful mode (placeholder)."""
    logger.info("Starting extraction process with browser-use...")
    
    # Load cookies from the session check
    ctx_config = BrowserContextConfig(cookies_file="/root/ggbot/extraction/tv_cookies.json")
    browser_config = BrowserConfig(headless=False)  # Headful mode for visual debugging
    browser = Browser(config=browser_config)
    
    # Initialize ChatGPT 4o for vision-based extraction
    llm = ChatOpenAI(model="gpt-4o")
    agent = Agent(
        task="Navigate to the BTCUSD chart on TradingView and extract ggShot indicator data using vision",
        llm=llm,
        browser=browser
    )
    
    try:
        result = await agent.run()
        logger.info(f"Extraction result: {result}")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_extraction())