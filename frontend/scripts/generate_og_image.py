#!/usr/bin/env python3
"""
Generate OG images by rendering HTML templates with Playwright.

Usage:
    python generate_og_image.py [template] [output]

Example:
    python generate_og_image.py og-image-template.html ../app/opengraph-image.png
"""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def generate_og_image(
    template_path: str = "og-image-template.html",
    output_path: str = "../app/opengraph-image.png",
    width: int = 1200,
    height: int = 630
):
    """Render HTML template and screenshot at OG image dimensions."""

    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    template_file = script_dir / template_path
    output_file = script_dir / output_path

    if not template_file.exists():
        print(f"Error: Template not found: {template_file}")
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Create page with exact OG image dimensions
        page = await browser.new_page(viewport={"width": width, "height": height})

        # Load the HTML template
        file_url = f"file://{template_file.absolute()}"
        print(f"Loading template: {file_url}")
        await page.goto(file_url, wait_until="networkidle")

        # Wait for fonts to load
        await page.wait_for_timeout(1000)

        # Screenshot at exact dimensions (no full_page to get exact viewport)
        print(f"Generating {width}x{height} image...")
        await page.screenshot(path=str(output_file), full_page=False)

        print(f"✓ Saved to: {output_file}")
        await browser.close()


async def main():
    template = sys.argv[1] if len(sys.argv) > 1 else "og-image-template.html"
    output = sys.argv[2] if len(sys.argv) > 2 else "../app/opengraph-image.png"

    await generate_og_image(template, output)


if __name__ == "__main__":
    asyncio.run(main())
