from rest_framework import serializers
from order.models import Order, OrderItem
from cart.api.serializers import UserSerializer, MiniBookSerializer



class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    total_cost = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'first_name', 'last_name', 'email',
            'total_quantity', 'total_cost', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at', 'total_quantity',
            'total_cost'
        ]

    def get_total_cost(self, obj):
        return obj.get_total_cost()

    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items.all())


class OrderItemSerializer(serializers.ModelSerializer):
    book = MiniBookSerializer()

    class Meta:
        model = OrderItem
        fields = ['id', 'book', 'price', 'quantity']
