import asyncio
import logging
import subprocess  # Already added, ensuring no NameError
from playwright.async_api import async_playwright, Playwright
import os
import json
from dotenv import load_dotenv
from dateutil import parser

# Load environment variables for credentials
load_dotenv()

# Specific chart URL for BTCUSD on Coinbase
CHART_URL = "https://www.tradingview.com/chart/HiWAe2vQ/?symbol=COINBASE%3ABTCUSD"

# TradingView login page URL
LOGIN_URL = "https://www.tradingview.com/accounts/signin/"

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def load_cookies(context, cookie_file):
    with open(cookie_file, 'r') as f:
        raw_content = f.read()
    logger.debug(f"Raw content of {cookie_file}: {raw_content}")
    
    cookies = json.loads(raw_content)
    processed_cookies = []
    for cookie in cookies:
        logger.debug(f"Original cookie: {json.dumps(cookie, indent=2)}")
        new_cookie = {"name": cookie["name"], "value": cookie["value"]}
        
        if "domain" not in cookie:
            logger.warning(f"Cookie {cookie.get('name', 'unknown')} missing domain, skipping")
            continue
        new_cookie["domain"] = cookie["domain"]
        
        if "path" not in cookie:
            new_cookie["path"] = "/"
        else:
            new_cookie["path"] = cookie["path"]
        
        if "expires" in cookie and isinstance(cookie["expires"], (int, float)):
            new_cookie["expires"] = cookie["expires"]
        if "secure" in cookie:
            new_cookie["secure"] = cookie["secure"]
        
        processed_cookies.append(new_cookie)
        logger.debug(f"Processed cookie: {json.dumps(new_cookie, indent=2)}")
    
    logger.debug(f"Processed cookies list: {json.dumps(processed_cookies, indent=2)}")
    try:
        await context.add_cookies(processed_cookies)
        logger.info("Cookies successfully added to the browser context.")
    except Exception as e:
        logger.error(f"Failed to add cookies: {str(e)}")
        raise

async def save_cookies(context, cookie_file):
    """Save cookies from the browser context to a JSON file."""
    cookies = await context.cookies()
    with open(cookie_file, 'w') as f:
        json.dump(cookies, f)

async def check_session(playwright: Playwright):
    """Check if the session is valid by accessing the chart URL."""
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    
    # Load the manually saved cookies
    await load_cookies(context, "tv_cookies.json")
    page = await context.new_page()
    
    # Navigate to the chart URL
    await page.goto(CHART_URL)
    content = await page.content()
    
    # Check for session expiration
    if "this chart layout isn't available" in content.lower():
        logger.info("Session expired. Initiating re-login...")
        await re_login(playwright, context, page)
    else:
        logger.info("Session is valid. Proceeding to extraction...")
        await trigger_extraction()
    
    await browser.close()

async def re_login(playwright: Playwright, context, page):
    """Handle re-login using credentials from .env."""
    await page.goto(LOGIN_URL)
    
    # Wait for and click the "Email" button
    email_button = await page.wait_for_selector('text=Email', timeout=10000)
    await email_button.click()
    
    # Wait for the login form to appear
    await page.wait_for_selector('input[name="username"]', timeout=10000)
    await page.fill('input[name="username"]', os.getenv("TVIEW_USERNAME"))
    await page.wait_for_selector('input[name="password"]', timeout=10000)
    await page.fill('input[name="password"]', os.getenv("TVIEW_PASSWORD"))
    await page.click('button[type="submit"]')
    
    # Wait for navigation after login
    await page.wait_for_load_state("networkidle")
    
    # Verify login success by checking the chart URL again
    await page.goto(CHART_URL)
    content = await page.content()
    if "this chart layout isn't available" not in content.lower():
        logger.info("Re-login successful. Saving new cookies...")
        await save_cookies(context, "tv_cookies.json")
    else:
        logger.error("Re-login failed. Manual intervention may be required.")

from extraction_main import run_extraction

async def trigger_extraction():
    """Trigger the extraction process by calling the extraction function directly."""
    try:
        await run_extraction()
        logger.info("Extraction process triggered successfully.")
    except Exception as e:
        logger.error(f"Error triggering extraction: {e}")

async def main():
    async with async_playwright() as playwright:
        await check_session(playwright)

if __name__ == "__main__":
    asyncio.run(main())