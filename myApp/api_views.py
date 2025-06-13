from rest_framework import viewsets
from rest_framework.response import Response
from .models import Book, Rating, Favorite, CartItem
from .serializers import BookSerializer
from rest_framework.decorators import action


class BookViewset(viewsets.ModelViewSet):
    serializer_class = BookSerializer

    def get_queryset(self):
        title = self.request.query_params.get('title')
        qs = Book.objects.all()
        if title:
            qs = qs.filter(title__icontains=title)
        return qs