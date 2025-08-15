from . import views
from django.urls import path


app_name = 'cart'

urlpatterns = [
    path('cart/', views.CartView.as_view(), name='cart_list'),
    path('cart/add-item/', views.CartItemView.as_view(), name='add_item'),
]