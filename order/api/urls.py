from . import views
from django.urls import path


app_name = 'order'

urlpatterns = [
    path('order/', views.OrderView.as_view(), name='order'),
]