from rest_framework import serializers
from order.models import Order, OrderItem
from cart.api.serializers import MiniBookSerializer



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


