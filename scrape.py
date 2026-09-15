import asyncio
import json
import os
import urllib.parse
from playwright.async_api import async_playwright

SEARCH_TERMS = ["shed", "wardrobe", "timber", "pallets"]

async def scrape_term(page, term):
    encoded = urllib.parse.quote(term)
    # Target Marketplace sorted by newest
    url = f"https://www.facebook.com/marketplace/search/?query={encoded}&sortBy=creation_time_descend"
    
    print(f"--- Checking: {term} ---")
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(4000)

    # Dismiss any leftover modals/dialogs
    try:
        close_btn = page.locator('div[role="dialog"] [aria-label="Close"]')
        if await close_btn.count() > 0:
            await close_btn.first.click()
    except Exception:
        pass

    # Scroll down to load initial cards
    await page.mouse.wheel(0, 1500)
    await page.wait_for_timeout(2500)

    # Grab Marketplace listing anchor tags
    cards = await page.locator('a[href*="/marketplace/item/"]').all()
    print(f"Found {len(cards)} cards for '{term}'")
    results = []

    for card in cards[:12]:
        href = await card.get_attribute("href")
        if not href:
            continue
            
        full_link = href if href.startswith("http") else f"https://www.facebook.com{href.split('?')[0]}"
        raw_text = (await card.inner_text()).strip().split("\n")
        raw_text = [t.strip() for t in raw_text if t.strip()]

        if not raw_text:
            continue

        price = raw_text[0] if len(raw_text) > 0 else "Free / Check"
        title = raw_text[1] if len(raw_text) > 1 else term
        location = raw_text[2] if len(raw_text) > 2 else "Local"

        img = card.locator("img")
        img_src = await img.first.get_attribute("src") if await img.count() > 0 else ""

        results.append({
            "id": full_link,
            "term": term,
            "title": title,
            "price": price,
            "location": location,
            "image": img_src,
            "url": full_link
        })

    return results

async def main():
    raw_cookies = os.environ.get("FB_COOKIES", "")
    if not raw_cookies:
        print("ERROR: No FB_COOKIES secret found in environment!")
        return

    try:
        cookies = json.loads(raw_cookies)
    except Exception as e:
        print(f"ERROR: Failed to parse FB_COOKIES JSON: {e}")
        return

    # Clean cookies format for Playwright
    formatted_cookies = []
    for c in cookies:
        cookie_dict = {
            "name": c.get("name"),
            "value": c.get("value"),
            "domain": c.get("domain", ".facebook.com"),
            "path": c.get("path", "/"),
            "secure": c.get("secure", True)
        }
        formatted_cookies.append(cookie_dict)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-GB",
            viewport={"width": 1280, "height": 800}
        )
        
        # Inject logged-in session cookies
        await context.add_cookies(formatted_cookies)
        page = await context.new_page()

        all_items = {}
        for term in SEARCH_TERMS:
            try:
                items = await scrape_term(page, term)
                for item in items:
                    all_items[item["id"]] = item
            except Exception as e:
                print(f"Error on {term}: {e}")

        await browser.close()
        print(f"Total listings collected: {len(all_items)}")

        with open("listings.json", "w") as f:
            json.dump({"items": list(all_items.values())}, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
