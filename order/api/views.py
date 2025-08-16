from .serializers import OrderSerializer, CreateOrderSerializer
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


class CreateOrderAPIView(APIView):
    """A view for posting an order request."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """A post request to create an order"""
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(
            {
                'success': 'Your order has been created.'
                ' Click here for payment: '
            },
            status=status.HTTP_200_OK
        )

