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

            # 1. Title
            title = page.locator("#productTitle").first.inner_text().strip()

            # 2. Author / Brand (NEW LOGIC)
            author = "Unknown Brand"
            if page.locator("#bylineInfo").count() > 0:
                raw_author = page.locator("#bylineInfo").first.inner_text().strip()
                # Clean up "Visit the Apple Store" -> "Apple"
                # Remove "Visit the", "Store", "Brand:" (case insensitive)
                author = re.sub(
                    r"(?i)(Visit the | Store|Brand: )", "", raw_author
                ).strip()

            # 3. Price
            price_text = "0.00"
            if page.locator(".a-price-whole").count() > 0:
                whole = page.locator(".a-price-whole").first.inner_text().strip()
                fraction = page.locator(".a-price-fraction").first.inner_text().strip()
                whole = whole.replace(".", "")
                price_text = f"{whole}.{fraction}"

            price = float(re.sub(r"[^\d.]", "", price_text))

            # 4. Image URL
            image_url = ""
            if page.locator("#landingImage").count() > 0:
                image_url = page.locator("#landingImage").first.get_attribute("src")

            scraped_data = {
                "title": title,
                "author": author,  # <--- Saving the real author
                "price": price,
                "image_url": image_url,
                "user_agent": user_agent,
            }
            print(f"celery_worker: ✅ Scraped: {title[:20]}... by {author}")

        except Exception as e:
            print(f"celery_worker: ❌ Scraping Error: {e}")
        finally:
            browser.close()

    # --- 2. SAVING PHASE ---
    if scraped_data:
        book, created = Book.objects.get_or_create(
            title=scraped_data["title"],
            defaults={
                "author": scraped_data["author"],  # <--- Using the real author
                "price": scraped_data["price"],
                "description": "Imported from Amazon.",
                "stock": 10,
            },
        )

        # --- 3. IMAGE DOWNLOAD PHASE ---
        if scraped_data["image_url"]:
            # Check if image is missing OR if we just created the book
            if not book.image or created:
                print("celery_worker: 📸 Downloading image...")
                try:
                    headers = {"User-Agent": scraped_data["user_agent"]}
                    response = requests.get(scraped_data["image_url"], headers=headers)

                    if response.status_code == 200:
                        filename = f"{scraped_data['title'][:20].replace(' ', '-').lower()}.jpg"  # noqa
                        book.image.save(
                            filename, ContentFile(response.content), save=True
                        )
                        print("celery_worker: 💾 Image saved!")
                except Exception as e:
                    print(f"celery_worker: ⚠️ Image Error: {e}")

        return f"Finished: {book.title}"

    return "Failed to scrape"
