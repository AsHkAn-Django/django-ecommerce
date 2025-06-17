from rest_framework import viewsets
from rest_framework.response import Response
from .models import Book, Rating, Favorite, CartItem
from .serializers import BookSerializer
from .permissions import IsAdminOrReadOnly



class BookViewset(viewsets.ModelViewSet):
    """
    A viewset with search and ordering.
    """
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrReadOnly,)


    def get_queryset(self):
        title = self.request.query_params.get('title')
        qs = Book.objects.all()
        if title:
            qs = qs.filter(title__icontains=title)

        ordering = self.request.query_params.get('ordering')
        if ordering:
            qs = qs.order_by(ordering)
        return qs


# TODO: We can also do the filtering part with DRF built-in
# from rest_framework import filters

# class BookViewset(viewsets.ModelViewSet):
#     serializer_class = BookSerializer
#     queryset = Book.objects.all()
#     filter_backends = [filters.SearchFilter, filters.OrderingFilter]
#     search_fields = ['title']
#     ordering_fields = ['price', 'title', 'author']