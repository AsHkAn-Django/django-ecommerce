from django.core.management.base import BaseCommand
from myApp.tasks import scrape_amazon_product


class Command(BaseCommand):
    help = "Triggers a Celery task to scrape Amazon"

    def add_arguments(self, parser):
        parser.add_argument("url", type=str, help="The Amazon Product URL")

    def handle(self, *args, **options):
        url = options["url"]

        # PRO MOVE: We use .delay() to send it to Redis
        scrape_amazon_product.delay(url)

        self.stdout.write(
            self.style.SUCCESS(f"🚀 Task sent to Celery! processing: {url}")
        )
