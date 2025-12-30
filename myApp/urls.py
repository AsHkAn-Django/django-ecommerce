from django.urls import path
from . import views

app_name = "myApp"

urlpatterns = [
    path("update_book/<int:pk>/", views.BookUpdateView.as_view(), name="update_book"),
    path("shopping/", views.ShoppingListView.as_view(), name="shopping"),
    path("rating/<int:pk>/", views.RatingFormView.as_view(), name="rating"),
    path(
        "add_to_favorite/<int:pk>/",
        views.add_to_favorite_toggle,
        name="add_to_favorite",
    ),
    path("book/<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
    path("favorites/", views.FavoriteListView.as_view(), name="favorite_list"),
    path("", views.IndexView.as_view(), name="home"),
]
