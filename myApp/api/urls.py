from . import views
from rest_framework.routers import SimpleRouter, DefaultRouter
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


app_name = "myApp"

router = DefaultRouter()
router.register(r"books", views.BookViewset, basename="books")

urlpatterns = [
    path("", include(router.urls)),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
