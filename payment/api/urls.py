from . import views
from django.urls import path


app_name = "payment"

urlpatterns = [
    path("payment-api/", views.CompeletedAPIView.as_view(), name="completed_api"),
    path("payment-api/cancel/", views.CanceledAPIView.as_view(), name="canceled_api"),
]
