import re
from celery import shared_task
from playwright.sync_api import sync_playwright
from .models import Book


@shared_task
def scrape_amazon_product(url):
    print(f"celery_worker: 🕵️‍♂️ Starting background scrape for: {url}")

    scraped_data = None

    # --- 1. THE SCRAPING PHASE ---
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"  # noqa
        )

        try:
            page.goto(url, timeout=60000)

            # Title
            title = page.locator("#productTitle").first.inner_text().strip()

            # Price Logic
            price_text = "0.00"
            if page.locator(".a-price-whole").count() > 0:
                whole = page.locator(".a-price-whole").first.inner_text().strip()
                fraction = page.locator(".a-price-fraction").first.inner_text().strip()
                whole = whole.replace(".", "")
                price_text = f"{whole}.{fraction}"

            # Image
            image_url = ""
            if page.locator("#landingImage").count() > 0:
                image_url = page.locator("#landingImage").first.get_attribute("src")

            price = float(re.sub(r"[^\d.]", "", price_text))

            scraped_data = {"title": title, "price": price, "image_url": image_url}
            print(f"celery_worker: ✅ Scraped: {title[:30]}...")

        except Exception as e:
            print(f"celery_worker: ❌ Error: {e}")
        finally:
            browser.close()

    # --- 2. THE SAVING PHASE ---
    if scraped_data:
        # Note: We don't need print() here as much, but we can log it
        product, _ = Book.objects.get_or_create(
            title=scraped_data["title"],
            defaults={
                "price": scraped_data["price"],
                "description": f"Imported from Amazon. Original Image: {scraped_data['image_url']}",  # noqa
                "stock": 10,
            },
        )
        return f"Saved: {product.title}"

    return "Failed to scrape"
