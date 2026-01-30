#!/usr/bin/env python3
"""
Screenshot a URL using Playwright.

Usage:
    python screenshot_url.py <url> [output_path]

Example:
    python screenshot_url.py https://ggbots.ai/landing landing.png
"""

import sys
import asyncio
from playwright.async_api import async_playwright


async def screenshot_url(url: str, output_path: str = "screenshot.png", full_page: bool = True):
    """Take a screenshot of a URL."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")

        print(f"Taking screenshot...")
        await page.screenshot(path=output_path, full_page=full_page)

        print(f"Screenshot saved to {output_path}")
        await browser.close()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python screenshot_url.py <url> [output_path]")
        sys.exit(1)

    url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "screenshot.png"

    await screenshot_url(url, output_path)


if __name__ == "__main__":
    asyncio.run(main())
