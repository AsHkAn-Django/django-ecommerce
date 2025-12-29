from rest_framework import serializers
from cart.models import Cart, CartItem
from myApp.models import Book
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404


class UserSerializer(serializers.ModelSerializer):
    """A serializer for showing user data."""

    class Meta:
        model = get_user_model()
        fields = ["id", "email", "full_name", "date_joined"]


class MiniBookSerializer(serializers.ModelSerializer):
    """A short version of book serializer."""

    class Meta:
        model = Book
        fields = ["id", "title", "price"]


class CartSerializer(serializers.ModelSerializer):
    """A GET method version serializer for Cart."""

    user = UserSerializer()

    class Meta:
        model = Cart
        fields = ["id", "user"]
        read_only_fields = ["id", "user"]


class CartItemSerializer(serializers.ModelSerializer):
    """A GET method version serializer for Cart Item."""

    cart = CartSerializer()
    book = MiniBookSerializer()

    class Meta:
        model = CartItem
        fields = ["id", "cart", "book", "quantity", "created_at", "updated_at"]
        read_only_fields = ["id", "cart", "created_at", "updated_at"]


class CreateCartSerializer(serializers.ModelSerializer):
    """A POST method version serializer for Cart."""

    class Meta:
        model = Cart
        fields = []

    def validate(self, attrs):
        user = self.context["request"].user
        if Cart.objects.filter(user=user).exists():
            raise serializers.ValidationError("User already has a cart.")
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CreateCartItemSerializer(serializers.ModelSerializer):
    """A POST method version serializer for Cart Item."""

    class Meta:
        model = CartItem
        fields = ["book", "quantity"]

    def validate(self, attrs):
        user = self.context["request"].user
        cart = get_object_or_404(Cart, user=user)
        book = attrs["book"]
        new_quantity = attrs["quantity"]

        # check if item already exists in cart
        existing_item = CartItem.objects.filter(cart=cart, book=book).first()
        total_quantity = new_quantity + (existing_item.quantity if existing_item else 0)
        try:
            book.quantity_stock_check(total_quantity)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        cart = get_object_or_404(Cart, user=user)
        book = validated_data["book"]
        quantity = validated_data["quantity"]

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, book=book, defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return cart_item
