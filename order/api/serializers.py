from rest_framework import serializers
from order.models import Order, OrderItem
from cart.models import Cart
from cart.api.serializers import MiniBookSerializer
from django.db import transaction



class OrderItemSerializer(serializers.ModelSerializer):
    book = MiniBookSerializer()

    class Meta:
        model = OrderItem
        fields = ['id', 'book', 'price', 'quantity']




class OrderSerializer(serializers.ModelSerializer):
    total_cost = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'first_name', 'last_name', 'email', 'created_at',
            'updated_at', 'total_quantity', 'total_cost', 'items'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'total_quantity', 'total_cost'
        ]

    def get_total_cost(self, obj):
        return obj.get_total_cost()

    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items.all())


class CreateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email']

    def validate(self, attrs):
        user = self.context['request'].user

        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Your cart is empty!")

        for item in cart.items.all():
            if item.quantity > item.book.stock:
                raise serializers.ValidationError(
                    f"Not enough stock for {item.book.title}. "
                    f"Only {item.book.stock} left."
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        # retrieve the cart and lock it until transaction finishes
        cart = Cart.objects.select_for_update().get(user=user)

        # create the order
        order = Order.objects.create(user=user, **validated_data)

        # Move cart items into order
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,book=item.book,quantity=item.quantity, price=item.book.price
            )

        return order


