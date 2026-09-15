import asyncio
import json
import os
import urllib.parse
from playwright.async_api import async_playwright

SEARCH_TERMS = ["shed"]

async def main():
    raw_cookies = os.environ.get("FB_COOKIES", "")
    if not raw_cookies:
        print("ERROR: No FB_COOKIES secret found!")
        return

    try:
        cookies = json.loads(raw_cookies)
    except Exception as e:
        print(f"Failed to parse FB_COOKIES: {e}")
        return

    formatted_cookies = []
    for c in cookies:
        formatted_cookies.append({
            "name": c.get("name"),
            "value": c.get("value"),
            "domain": c.get("domain", ".facebook.com"),
            "path": c.get("path", "/"),
            "secure": c.get("secure", True)
        })

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-GB",
            viewport={"width": 1280, "height": 900}
        )
        await context.add_cookies(formatted_cookies)
        page = await context.new_page()

        encoded = urllib.parse.quote("shed")
        url = f"https://www.facebook.com/marketplace/search/?query={encoded}&sortBy=creation_time_descend"
        
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)

        print(f"Landed URL: {page.url}")
        print(f"Page Title: {await page.title()}")

        # Take screenshot of what the authenticated page actually looks like
        await page.screenshot(path="debug_facebook.png", full_page=True)

        # Print all anchor hrefs to see what links exist
        links = await page.locator("a").evaluate_all("els => els.map(e => e.href)")
        item_links = [l for l in links if "marketplace" in l or "item" in l]
        print(f"Total links found: {len(links)}")
        print(f"Marketplace-related links: {len(item_links)}")
        if item_links:
            print("Sample link:", item_links[0])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
