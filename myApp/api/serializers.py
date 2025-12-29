from rest_framework import serializers
from myApp.models import Book


class BookSerializer(serializers.ModelSerializer):
    average_rate = serializers.SerializerMethodField()
    rate_numbers = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "stock",
            "price",
            "image",
            "description",
            "average_rate",
            "rate_numbers",
            "is_favorite",
        )
        read_only_fields = (
            "author",
            "stock",
        )

    def get_average_rate(self, obj):
        return obj.get_average_rating()

    def get_rate_numbers(self, obj):
        return obj.get_rates_number()

    def get_is_favorite(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.book_favorites.filter(user=user).exists()
        return False
