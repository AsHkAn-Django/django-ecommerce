from .serializers import OrderSerializer, OrderItemSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from order.models import Order, OrderItem



class OrderListAPIView(APIView):
    """Get the list of your past orders."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Bring back all the past orders for this user."""
        order = Order.objects.filter(user=request.user)
        serialized_order = OrderSerializer(order, many=True)
        return Response(serialized_order.data, status=status.HTTP_200_OK)
