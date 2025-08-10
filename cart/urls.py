from django.urls import path
from . import views


app_name = 'cart'

urlpatterns = [
    path('delete_item/<int:pk>/', views.delete_item, name='delete_item'),
    path('purchase/<int:pk>/', views.purchase, name='purchase'),
    path('session_cart/', views.SessionCartView.as_view(), name='session_cart'),
    path('cart-add/<int:pk>/', views.cart_add, name='cart_add'),
    path('cart-list/', views.cart_list, name='cart_list'),
]