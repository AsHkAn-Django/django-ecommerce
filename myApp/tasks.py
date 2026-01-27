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
            # Go to page and give scripts a moment to hydrate
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # --- 0. BASIC BOT / INTERSTITIAL / CAPTCHA DETECTION ---
            # Some Amazon URLs first render a "Continue shopping" or captcha page with no product DOM.
            content_snapshot = page.content()

            # Captcha / bot challenge
            if page.locator(
                'input#captchacharacters, form[action*="validateCaptcha"]'
            ).count() > 0:
                raise Exception("Amazon captcha / bot challenge detected")

            # Interstitial / "Continue shopping" page with no product DOM
            if "Continue shopping" in content_snapshot and "productTitle" not in content_snapshot:
                raise Exception("Amazon interstitial / continue shopping page returned")

            # --- 1. TITLE ---
            title_loc = page.locator("#productTitle")
            if title_loc.count() == 0:
                raise Exception("Could not find product title (#productTitle missing)")
            title = title_loc.first.inner_text().strip()

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

            # --- 3. PRICE (Format-Aware Strategy) ---
            # Helper to extract float from any price-like text ("13.59", "13,59", "$13.59", "1,299.99", etc.)
            def _parse_price(text: str):
                if not text:
                    return None
                # Normalize non-breaking spaces
                text = text.replace("\u00a0", " ")

                # Match prices with optional thousands separators and 2 decimals, e.g. 1,299.99 or 1.299,99
                candidates = re.findall(
                    r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})", text
                )
                if not candidates:
                    # If we can’t find a decimal price, treat as not-a-price.
                    return None

                # Heuristic: use the last price-like token (often the final/discounted price)
                value_str = candidates[-1]

                # If both '.' and ',' appear, treat the last separator as decimal and all others as thousands
                if "," in value_str and "." in value_str:
                    last_sep = max(value_str.rfind(","), value_str.rfind("."))
                    int_part = re.sub(r"[.,]", "", value_str[:last_sep])
                    dec_part = value_str[last_sep + 1 :]
                    value_str = f"{int_part}.{dec_part}"
                else:
                    # Single separator type: assume it's the decimal separator
                    value_str = value_str.replace(",", ".")

                try:
                    return float(value_str)
                except ValueError:
                    return None

            # Helper to read the main price from core price containers
            def _extract_core_price():
                core_price_loc = page.locator(
                    "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen, "
                    "#corePriceDisplay_mobile_feature_div .a-price .a-offscreen, "
                    "#corePrice_feature_div .a-price .a-offscreen"
                )
                count = core_price_loc.count()
                for i in range(count):
                    raw_price = core_price_loc.nth(i).inner_text().strip()
                    parsed = _parse_price(raw_price)
                    if parsed is not None:
                        return parsed
                return None

            price = None

            # 3.1 Prefer specific book formats in order: Paperback > Hardcover > everything else.
            preferred_order = ["paperback", "hardcover"]

            # Many book pages have a "formats" section (e.g. #tmmSwatches li for each format).
            # Strategy: click the desired swatch (Paperback / Hardcover) and then read the main core price block.
            swatch_locator = page.locator("#tmmSwatches li")
            swatch_count = swatch_locator.count()
            if swatch_count == 0:
                # Fallback: some templates might still use .swatchElement
                swatch_locator = page.locator(".swatchElement")
                swatch_count = swatch_locator.count()

            if swatch_count > 0:
                # First, try strictly preferred formats (Paperback, then Hardcover)
                for target_format in preferred_order:
                    for i in range(swatch_count):
                        item = swatch_locator.nth(i)
                        label_text = item.inner_text().strip().lower()
                        if target_format not in label_text:
                            continue
                        try:
                            item.click(timeout=5000)
                            page.wait_for_timeout(800)
                        except Exception:
                            continue

                        core_parsed = _extract_core_price()
                        if core_parsed is not None:
                            price = core_parsed
                            break
                    if price is not None:
                        break

                # If still nothing, fall back to "any format" within the swatches:
                # click the first one and read the core price.
                if price is None:
                    try:
                        first_item = swatch_locator.first
                        first_item.click(timeout=5000)
                        page.wait_for_timeout(800)
                        core_parsed = _extract_core_price()
                        if core_parsed is not None:
                            price = core_parsed
                    except Exception:
                        pass

            # 3.2 If no price from the formats section, fall back to core price blocks
            if price is None:
                core_parsed = _extract_core_price()
                if core_parsed is not None:
                    price = core_parsed

            # 3.3 Last resort: scoped .a-offscreen search in key price containers
            if price is None:
                fallback_loc = page.locator(
                    "#corePriceDisplay_desktop_feature_div .a-offscreen, "
                    "#corePriceDisplay_mobile_feature_div .a-offscreen, "
                    "#apex_desktop .a-offscreen, "
                    "#buybox .a-offscreen"
                )
                for txt in fallback_loc.all_inner_texts():
                    parsed = _parse_price(txt.strip())
                    if parsed is not None:
                        price = parsed
                        break

            # If absolutely nothing matched, default to 0.00 so calling code won't explode
            if price is None:
                price = 0.00

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
