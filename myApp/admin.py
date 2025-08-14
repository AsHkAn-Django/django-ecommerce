from django.contrib import admin
from .models import Book, Rating, Favorite
from order.models import Order, OrderItem


admin.site.register(Book)
admin.site.register(Rating)
admin.site.register(Favorite)
admin.site.register(Order)
admin.site.register(OrderItem)
