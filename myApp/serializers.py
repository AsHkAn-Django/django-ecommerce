from rest_framework import serializers
from .models import Book, Rating, Favorite, CartItem


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'stock', 'price', 'image', 'description')
        read_only_fields = ('author', 'stock',)