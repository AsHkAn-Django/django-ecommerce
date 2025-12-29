from .serializers import OrderSerializer, CreateOrderSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from order.models import Order
from django.urls import reverse
from decimal import Decimal
import stripe


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
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        success_url = request.build_absolute_uri(reverse("payment_api:completed_api"))
        cancel_url = request.build_absolute_uri(reverse("payment_api:canceled_api"))
        session_data = {
            "mode": "payment",
            "client_reference_id": order.id,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items": [],
        }

        for item in order.items.all():
            session_data["line_items"].append(
                {
                    "price_data": {
                        "unit_amount": int(item.price * Decimal("100")),
                        "currency": "usd",
                        "product_data": {"name": item.book.title},
                    },
                    "quantity": item.quantity,
                }
            )

        session = stripe.checkout.Session.create(**session_data)

        return Response(
            {
                "success": "Your order has been created.",
                "order_id": order.id,
                "stripe_url": session.url,
            },
            status=status.HTTP_201_CREATED,
        )
