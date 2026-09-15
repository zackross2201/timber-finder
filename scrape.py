import asyncio
import json
import urllib.parse
from playwright.async_api import async_playwright

SEARCH_TERMS = ["shed", "wardrobe", "timber", "pallets"]

async def scrape_term(page, term):
    encoded = urllib.parse.quote(term)
    url = f"https://www.facebook.com/marketplace/search/?query={encoded}&sortBy=creation_time_descend"
    
    print(f"Checking: {term}")
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(4000)

    # Scroll once to let items render
    await page.mouse.wheel(0, 1500)
    await page.wait_for_timeout(2000)

    cards = await page.locator('a[href*="/marketplace/item/"]').all()
    results = []

    for card in cards[:15]:
        href = await card.get_attribute("href")
        if not href:
            continue
            
        full_link = f"https://www.facebook.com{href.split('?')[0]}"
        text = (await card.inner_text()).split("\n")
        
        price = text[0] if len(text) > 0 else "Free / Check listing"
        title = text[1] if len(text) > 1 else term
        location = text[2] if len(text) > 2 else "Local area"

        img = card.locator("img")
        img_src = await img.first.get_attribute("src") if await img.count() > 0 else ""

        results.append({
            "id": href.split("/item/")[1].split("/")[0] if "/item/" in href else full_link,
            "term": term,
            "title": title,
            "price": price,
            "location": location,
            "image": img_src,
            "url": full_link
        })

    return results

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-GB"
        )
        page = await context.new_page()

        all_items = {}
        for term in SEARCH_TERMS:
            try:
                items = await scrape_term(page, term)
                for item in items:
                    all_items[item["id"]] = item
            except Exception as e:
                print(f"Failed on {term}: {e}")

        await browser.close()

        with open("listings.json", "w") as f:
            json.dump({"items": list(all_items.values())}, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
