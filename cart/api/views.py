from .serializers import CartSerializer, CartItemSerializer
from cart.models import Cart, CartItem
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status



class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = cart.items.all()
        # We send request here to serializer for finding the user and his favorites
        serialized_items = CartItemSerializer(cart_items, many=True, context={'request': request})
        return Response(serialized_items.data, status=status.HTTP_200_OK)