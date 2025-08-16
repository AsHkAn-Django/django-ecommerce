from . import views
from django.urls import path


app_name = 'order'

urlpatterns = [
    path('order/', views.OrderListAPIView.as_view(), name='order'),
    path('order/create/', views.CreateOrderAPIView.as_view(), name='order_create'),
]