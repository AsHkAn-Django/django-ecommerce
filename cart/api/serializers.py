from rest_framework import serializers
from cart.models import Cart, CartItem
from myApp.models import Book
from django.contrib.auth import get_user_model



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields =['id', 'email', 'full_name', 'date_joined']


class MiniBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'price']


class CartSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Cart
        fields = ['id', 'user']
        read_only_fields = ['id', 'user']


class CartItemSerializer(serializers.ModelSerializer):
    cart = CartSerializer()
    book = MiniBookSerializer()

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'book', 'quantity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'cart', 'created_at', 'updated_at']
