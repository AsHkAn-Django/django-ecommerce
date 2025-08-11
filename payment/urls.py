from . import views
from django.urls import path


app_name = 'payment'

urlpatterns = [
    path('process/<int:order_id>/', views.payment_process, name='process'),
    path('completed/', views.process_completed, name='completed'),
    path('canceled/', views.process_canceled, name='canceled'),

]