from . import views
from django.urls import path


app_name = "cart"

urlpatterns = [
    path("cart/", views.CartAPIView.as_view(), name="cart_list_api"),
    path("cart/add-item/", views.CartItemAPIView.as_view(), name="add_item_api"),
]
