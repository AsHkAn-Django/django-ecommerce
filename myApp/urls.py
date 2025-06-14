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
    path('rating/<int:pk>/', views.RatingFormView.as_view(), name='rating'),
    path('add_to_favorite/<int:pk>/', views.add_to_favorite_toggle, name='add_to_favorite'),
    path('book/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('', views.IndexView.as_view(), name='home'),
]
