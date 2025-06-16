from rest_framework import serializers
from .models import Book, Rating, Favorite, CartItem


class BookSerializer(serializers.ModelSerializer):
    average_rate = serializers.SerializerMethodField()
    rate_numbers = serializers.SerializerMethodField()


    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'stock', 'price', 'image', 'description', 'average_rate', 'rate_numbers')
        read_only_fields = ('author', 'stock',)

    def get_average_rate(self, obj):
        return obj.get_average_rating()

    def get_rate_numbers(self, obj):
        return obj.get_rates_number()
