from . import api_views
from rest_framework.routers import SimpleRouter, DefaultRouter
from django.urls import path, include


app_name = 'api'

router = DefaultRouter()
router.register(r'books', api_views.BookViewset, basename='books')

urlpatterns = [
    path('', include(router.urls)),
]