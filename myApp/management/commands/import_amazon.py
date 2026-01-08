import re
from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright

from myApp.models import Book


class Command(BaseCommand):
    help = 'Scrapes Amazon and adds a product to the DB'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='The Amazon Product URL')

    def handle(self, *args, **options):
        url = options['url']
        self.stdout.write(f"🕵️‍♂️ Starting scraper for: {url}")

        with sync_playwright() as p:
            # Launch browser (headless=True means no UI, faster for server)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )

            try:
                page.goto(url, timeout=60000) # 60s timeout

                # --- SCRAPING LOGIC ---
                # 1. Title
                title = page.locator("#productTitle").first.inner_text().strip()

                # 2. Price (Try multiple selectors because Amazon is tricky)
                price_text = "0.00"
                if page.locator(".a-price-whole").count() > 0:
                    whole = page.locator(".a-price-whole").first.inner_text().strip()
                    fraction = page.locator(".a-price-fraction").first.inner_text().strip()
                    price_text = f"{whole}.{fraction}"

                # Clean price string (remove currency symbols)
                price = float(re.sub(r'[^\d.]', '', price_text))

                # 3. Image
                image_url = ""
                if page.locator("#landingImage").count() > 0:
                    image_url = page.locator("#landingImage").first.get_attribute("src")

                self.stdout.write(f"✅ Found: {title[:50]}... | ${price}")

                # --- SAVE TO DB ---
                # This is where the magic happens. We save directly to your E-commerce DB.
                product, created = Book.objects.get_or_create(
                    title=title,
                    defaults={
                        'price': price,
                        'description': f"Imported from Amazon. Original Image: {image_url}",
                        # Add other required fields here with dummy data if needed
                        'stock': 10,
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"🎉 Created new product: {product.title}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Product already exists. Updated price."))
                    product.price = price
                    product.save()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            finally:
                browser.close()