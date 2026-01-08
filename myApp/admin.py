from order.models import Order, OrderItem
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Book, Rating, Favorite

from .tasks import scrape_amazon_product


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "stock", "author")

    # 1. Point to a custom template that we will create soon
    change_list_template = "admin/book_changelist.html"

    # 2. Add a custom URL for our import page
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-amazon/",
                self.admin_site.admin_view(self.import_amazon_view),
                name="book-import-amazon",
            ),
        ]
        return custom_urls + urls

    # 3. The View: Handles the Form and Triggers Celery
    def import_amazon_view(self, request):
        if request.method == "POST":
            url = request.POST.get("amazon_url")
            if url:
                # Trigger the background task!
                scrape_amazon_product.delay(url)

                self.message_user(
                    request,
                    "🚀 Task started! The book will appear shortly.",
                    level=messages.SUCCESS,
                )
                return redirect(
                    "admin:myApp_book_changelist"
                )  # Ensure 'myApp' matches your actual app name

        context = dict(
            self.admin_site.each_context(request),  # Include admin navigation/branding
            title="Import from Amazon",
        )
        return render(request, "admin/import_amazon_form.html", context)


admin.site.register(Rating)
admin.site.register(Favorite)
admin.site.register(Order)
admin.site.register(OrderItem)
