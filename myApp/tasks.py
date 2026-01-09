import re
import requests
from celery import shared_task
from playwright.sync_api import sync_playwright
from django.core.files.base import ContentFile
from .models import Book
from django.utils.text import slugify


@shared_task
def scrape_amazon_product(url):
    print(f"celery_worker: 🕵️‍♂️ Starting robust scrape for: {url}")
    scraped_data = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"  # noqa
        page = browser.new_page(user_agent=user_agent)

        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # --- 1. TITLE ---
            title = page.locator("#productTitle").first.inner_text().strip()

            # --- 2. AUTHOR (Improved Cleaning) ---
            author = "Unknown"
            author_selectors = ["#bylineInfo", "#author_name", ".contributorNameID"]
            for selector in author_selectors:
                if page.locator(selector).count() > 0:
                    raw_author = page.locator(selector).first.inner_text().strip()
                    # Clean "by Stephen Covey (Author) Format:..." -> "Stephen Covey"
                    clean_author = re.sub(
                        r"(?i)(by |Visit the | Store|Brand: |\s*\(Author\)|\s*Format:.*)",  # noqa
                        "",
                        raw_author,
                    )
                    author = clean_author.strip()
                    break

            # --- 3. PRICE (Fallback Strategy) ---
            price = 0.00
            # Order of preference: Discounted Apex -> Whole/Fraction -> Offscreen text
            price_selectors = [
                ".a-price.aok-align-center",  # The div you found
                "#price_inside_buybox",
                "#kindle-price",
                ".a-price",
            ]

            for selector in price_selectors:
                loc = page.locator(selector).first
                if loc.count() > 0:
                    text = loc.inner_text()
                    # Find any pattern like 11.99 or 11,99
                    found = re.findall(r"\d+[.,]\d{2}", text)
                    if found:
                        price = float(found[0].replace(",", "."))
                        break

            # Final fallback: Check the specific "aok-offscreen" you mentioned
            if price == 0.00 and page.locator(".aok-offscreen").count() > 0:
                offscreen_text = page.locator(".aok-offscreen").first.inner_text()
                found = re.findall(r"\$\s*(\d+\.\d{2})", offscreen_text)
                if found:
                    price = float(found[0])

            # --- 4. IMAGE (Fallback Strategy) ---
            image_url = ""
            img_selectors = [
                "#landingImage",
                "#imgBlkFront",
                "#main-image",
                "#ebooksImgBlkFront",
            ]
            for selector in img_selectors:
                if page.locator(selector).count() > 0:
                    image_url = page.locator(selector).first.get_attribute("src")
                    if image_url:
                        break

            scraped_data = {
                "title": title,
                "author": author,
                "price": price,
                "image_url": image_url,
                "user_agent": user_agent,
            }
            print(
                f"celery_worker: ✅ Scraped: {title[:20]} | ${price} | Author: {author}"
            )

        except Exception as e:
            print(f"celery_worker: ❌ Error: {e}")
        finally:
            browser.close()

    # --- SAVING PHASE ---
    if scraped_data:
        book, created = Book.objects.get_or_create(
            title=scraped_data["title"],
            defaults={
                "author": scraped_data["author"],
                "price": scraped_data["price"],
                "description": "Imported via AI Scraper.",
                "stock": 10,
            },
        )

        # Always update price even if not created
        if not created:
            book.price = scraped_data["price"]
            book.save()

        if scraped_data["image_url"]:
            print("celery_worker: 📸 Downloading image...")
            try:
                # Use headers to avoid 403 Forbidden on image download
                res = requests.get(
                    scraped_data["image_url"],
                    headers={"User-Agent": scraped_data["user_agent"]},
                )
                if res.status_code == 200:
                    filename = f"{slugify(book.title)[:20]}.jpg"
                    book.image.save(filename, ContentFile(res.content), save=True)
            except Exception as e:
                print(f"celery_worker: ⚠️ Image Error: {e}")

        return f"Done: {book.title}"
