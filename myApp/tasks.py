import re
import requests
from celery import shared_task
from playwright.sync_api import sync_playwright
from django.core.files.base import ContentFile
from .models import Book


@shared_task
def scrape_amazon_product(url):
    print(f"celery_worker: 🕵️‍♂️ Starting background scrape for: {url}")

    scraped_data = None

    # --- 1. SCRAPING PHASE ---
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"  # noqa
        page = browser.new_page(user_agent=user_agent)

        try:
            page.goto(url, timeout=60000)

            # Title
            title = page.locator("#productTitle").first.inner_text().strip()

            # Price
            price_text = "0.00"
            if page.locator(".a-price-whole").count() > 0:
                whole = page.locator(".a-price-whole").first.inner_text().strip()
                fraction = page.locator(".a-price-fraction").first.inner_text().strip()
                whole = whole.replace(".", "")
                price_text = f"{whole}.{fraction}"

            price = float(re.sub(r"[^\d.]", "", price_text))

            # Image URL
            image_url = ""
            if page.locator("#landingImage").count() > 0:
                image_url = page.locator("#landingImage").first.get_attribute("src")

            scraped_data = {
                "title": title,
                "price": price,
                "image_url": image_url,
                "user_agent": user_agent,
            }
            print(f"celery_worker: ✅ Scraped: {title[:30]}...")

        except Exception as e:
            print(f"celery_worker: ❌ Scraping Error: {e}")
        finally:
            browser.close()

    # --- 2. SAVING PHASE ---
    if scraped_data:
        # We MUST provide an 'author' because your model requires it.
        # We use 'Amazon Product' as a placeholder.
        book, created = Book.objects.get_or_create(
            title=scraped_data["title"],
            defaults={
                "author": "Amazon Product",  # <--- FIXED: Added required field
                "price": scraped_data["price"],
                "description": "Imported from Amazon.",
                "stock": 10,
            },
        )

        # --- 3. IMAGE DOWNLOAD PHASE ---
        if scraped_data["image_url"]:
            print("celery_worker: 📸 Downloading image...")
            try:
                headers = {"User-Agent": scraped_data["user_agent"]}
                response = requests.get(scraped_data["image_url"], headers=headers)

                if response.status_code == 200:
                    # Create a filename based on the title (e.g., "amd-ryzen.jpg")
                    filename = (
                        f"{scraped_data['title'][:20].replace(' ', '-').lower()}.jpg"
                    )

                    # This .save() triggers your 'book_image_upload_path' automatically!
                    book.image.save(filename, ContentFile(response.content), save=True)

                    print("celery_worker: 💾 Image saved to uploads folder!")
                else:
                    print(f"celery_worker: ⚠️ Download failed: {response.status_code}")
            except Exception as e:
                print(f"celery_worker: ⚠️ Image Error: {e}")

        return f"Finished: {book.title}"

    return "Failed to scrape"
