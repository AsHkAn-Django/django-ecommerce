from . import views
from django.urls import path


app_name = "order"

urlpatterns = [
    path("create/", views.order_create, name="order_create"),
    path("my-order-list/", views.my_orders_list, name="my_orders_list"),
]
