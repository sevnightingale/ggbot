import asyncio
import json
from playwright.async_api import async_playwright

# Path to your cookies file
COOKIES_FILE = "extraction/cookies.json"

def map_same_site(value):
    """Convert sameSite values to Playwright-compatible strings."""
    if value == "no_restriction":
        return "None"
    elif value and value.lower() == "lax":
        return "Lax"
    elif value and value.lower() == "strict":
        return "Strict"
    return "Lax"  # Default to "Lax" for any invalid or missing value

async def main():
    async with async_playwright() as p:
        # Launch a headless Chromium browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # Load and preprocess cookies with debugging
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
        print("Original cookies:", json.dumps(cookies, indent=2))

        processed_cookies = []
        for i, cookie in enumerate(cookies):
            processed_cookie = cookie.copy()
            original_same_site = processed_cookie.get("sameSite")
            processed_cookie["sameSite"] = map_same_site(original_same_site)
            print(f"Cookie {i}: sameSite '{original_same_site}' -> '{processed_cookie['sameSite']}'")
            processed_cookies.append(processed_cookie)
        print("Processed cookies:", json.dumps(processed_cookies, indent=2))

        # Add cookies to the browser context
        await context.add_cookies(processed_cookies)

        # Open a new page and navigate to TradingView chart
        page = await context.new_page()
        chart_url = "https://www.tradingview.com/chart/HiWAe2vQ/?symbol=COINBASE%3ABTCUSD"
        await page.goto(chart_url)

        # Check if the chart loads (indicating successful login)
        chart_element = await page.query_selector(".priceValue-KzMjFOA8")  # Price element class
        error_message = await page.query_selector("text='We can't open this chart layout for you'")

        if chart_element:
            print("Logged in successfully! Chart is visible.")
        elif error_message:
            print("Not logged in. Cookies failed: 'We can't open this chart layout for you' message displayed.")
        else:
            print("Unexpected result: Neither chart nor error message found. Check the page manually.")

        # Take a screenshot for manual verification
        await page.wait_for_timeout(2000)  # Wait 2 seconds
        await page.screenshot(path="tradingview_chart.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())