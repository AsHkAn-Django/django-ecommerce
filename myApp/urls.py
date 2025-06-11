from django.urls import path
from . import views

app_name = 'myApp'

urlpatterns = [
    path('delete_item/<int:pk>/', views.delete_item, name='delete_item'),
    path('purchase/<int:pk>/', views.purchase, name='purchase'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('session_cart/', views.SessionCartView.as_view(), name='session_cart'),
    path('update_book/<int:pk>/', views.BookUpdateView.as_view(), name='update_book'),
    path('shopping/', views.ShoppingListView.as_view(), name='shopping'),
    path('', views.IndexView.as_view(), name='home'),
]
