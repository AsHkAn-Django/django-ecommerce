from django.urls import path
from . import views

app_name = 'registration'
urlpatterns = [
    path('sign_up/', views.SignUpView.as_view(), name='sign_up'),
]
