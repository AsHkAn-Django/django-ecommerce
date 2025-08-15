from rest_framework import serializers
from cart.models import Cart, CartItem
from myApp.models import Book
from django.contrib.auth import get_user_model



class UserSerializer(serializers.ModelSerializer):
    """A serializer for showing user data."""
    class Meta:
        model = get_user_model()
        fields =['id', 'email', 'full_name', 'date_joined']


class MiniBookSerializer(serializers.ModelSerializer):
    """A short version of book serializer."""
    class Meta:
        model = Book
        fields = ['id', 'title', 'price']


class CartSerializer(serializers.ModelSerializer):
    """A GET method version serializer for Cart."""
    user = UserSerializer()

    class Meta:
        model = Cart
        fields = ['id', 'user']
        read_only_fields = ['id', 'user']


class CartItemSerializer(serializers.ModelSerializer):
    """A GET method version serializer for Cart Item."""
    cart = CartSerializer()
    book = MiniBookSerializer()

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'book', 'quantity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'cart', 'created_at', 'updated_at']


class CreateCartSerializer(serializers.ModelSerializer):
    """A POST method version serializer for Cart."""
    class Meta:
        model = Cart
        fields = []

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate(self, attrs):
        user = self.context['request'].user
        if Cart.objects.filter(user=user).exists():
            raise serializers.ValidationError("User already has a cart.")
        return attrs



class CreateCartItemSerializer(serializers.ModelSerializer):
    """A POST method version serializer for Cart Item."""
    pass
