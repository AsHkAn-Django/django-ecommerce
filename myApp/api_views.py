from rest_framework import viewsets
from .models import Book, Rating, Favorite, CartItem
from .serializers import BookSerializer


class BookViewset(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
