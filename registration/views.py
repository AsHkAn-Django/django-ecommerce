from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm



class SignUpView(generic.CreateView):
    model = User
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('registration:login')
    template_name = "registration/sign_up.html"


