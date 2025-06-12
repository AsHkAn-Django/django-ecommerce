from django.contrib import admin
from .models import Book, CartItem, Rating, Favorite


admin.site.register(Book)
admin.site.register(CartItem)
admin.site.register(Rating)
admin.site.register(Favorite)
