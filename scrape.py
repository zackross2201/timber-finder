import asyncio
import json
import urllib.parse
from playwright.async_api import async_playwright

SEARCH_TERMS = ["shed"]

async def scrape_term(page, term):
    encoded = urllib.parse.quote(term)
    url = f"https://www.facebook.com/marketplace/search/?query={encoded}&sortBy=creation_time_descend"
    
    print(f"Opening URL: {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(5000)

    print(f"Final URL landed on: {page.url}")
    print(f"Page Title: {await page.title()}")

    # Save a screenshot to inspect what the runner actually sees
    await page.screenshot(path="debug_facebook.png", full_page=True)

    cards = await page.locator('a[href*="/marketplace/item/"]').all()
    print(f"Found {len(cards)} cards for {term}")

    # Check for login prompts
    login_form = await page.locator('form#login_form, input[name="email"]').count()
    if login_form > 0:
        print("DETECTED: Full Facebook Login Wall triggered.")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-GB",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        for term in SEARCH_TERMS:
            await scrape_term(page, term)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
