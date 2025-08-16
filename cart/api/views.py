from .serializers import (CartItemSerializer, CreateCartSerializer,
                          CreateCartItemSerializer)
from cart.models import Cart, CartItem
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status



class CartAPIView(APIView):
    """
    A View for getting the nested serializer of existed cart and
    cart items and also for creating a cart for user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Only for getting the list of the items in the cart with detail."""
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = cart.items.all()
        serialized_items = CartItemSerializer(cart_items, many=True,
                                              context={'request': request})
        return Response(serialized_items.data, status=status.HTTP_200_OK)

    def post(self, request):
        """For sending a post request to create a cart for user."""
        # We send request here to serializer for assigning the user 
        serializer = CreateCartSerializer(data=request.data,
                                          context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': 'The cart has been created. Now you can add '
                         'an item to your cart.'},
                        status=status.HTTP_201_CREATED)


class CartItemAPIView(APIView):
    """
    A View for adding books to your cart.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """A post method to add an item to cart."""
        serializer = CreateCartItemSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save()
        return Response(
            {
                'success': f'{cart_item.book.title} has been added to your cart. '
                           f'Quantity: {cart_item.quantity}'
            },
            status=status.HTTP_200_OK
        )
